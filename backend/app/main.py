from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
from datetime import datetime
import uuid
import json
import asyncio
import boto3
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from botocore.exceptions import BotoCoreError, NoCredentialsError, ClientError
from openai import OpenAI

from app.config import (
    MAX_UPLOAD_SIZE,
    ALLOWED_EXTENSIONS,
    S3_BUCKET_NAME,
    S3_REGION,
    S3_ENDPOINT_URL,
    S3_OBJECT_PREFIX,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_BASE_URL,
    ALLOWED_ORIGINS,
)
from app.database import get_db, engine
from app.models import Base, ImageAnalysis

app = FastAPI(
    title="Natural Observer API",
    description="自然観察 × LLM Web API",
    version="0.1.0"
)

# CORS ミドルウェア設定（環境変数から許可オリジンを取得）
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB テーブルを初期化（存在しなければ作成）
Base.metadata.create_all(bind=engine)

# S3 クライアント（環境変数で資格情報を取得）
s3_client = boto3.client(
    "s3",
    region_name=S3_REGION,
    endpoint_url=S3_ENDPOINT_URL,
)


def get_openai_client() -> OpenAI:
    """OpenAI クライアントを生成する"""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY が設定されていません")
    return OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL or None,
    )


class AnalyzeRequest(BaseModel):
    """GPT に渡すペイロードの基本形"""

    s3_url: HttpUrl
    original_filename: str
    instructions: str | None = None


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Natural Observer API",
        "version": "0.1.0",
        "endpoints": {
            "POST /upload": "画像をアップロード",
            "POST /analyze": "S3 URL を GPT へ送信して説明を生成"
        }
    }


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    画像ファイルを S3 にアップロード
    
    - **file**: アップロードする画像ファイル
    
    Returns:
        - filename: 保存されたファイル名
        - size: ファイルサイズ（バイト）
        - s3_object_key: 保存先キー
        - s3_url: 参照用 URL
    """
    try:
        # S3 設定の確認
        if not S3_BUCKET_NAME:
            raise HTTPException(status_code=500, detail="S3_BUCKET_NAME が設定されていません")

        # ファイル検証
        if not file.filename:
            raise HTTPException(status_code=400, detail="ファイル名が空です")
        
        # ファイル拡張子の確認
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"許可されていないファイル形式です。対応形式: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # ファイルサイズのチェック
        file_content = await file.read()
        if len(file_content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"ファイルが大きすぎます。最大サイズ: {MAX_UPLOAD_SIZE / (1024*1024):.0f}MB"
            )
        
        # ユニークなファイル名を生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        saved_filename = f"{timestamp}_{unique_id}{file_ext}"
        object_key = f"{S3_OBJECT_PREFIX.rstrip('/')}/{saved_filename}"

        # S3 にアップロード
        content_type = file.content_type or "application/octet-stream"
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=object_key,
            Body=file_content,
            ContentType=content_type,
        )
        # S3 URL を組み立て（エンドポイント指定時はそちらを優先）
        if S3_ENDPOINT_URL:
            s3_url = f"{S3_ENDPOINT_URL.rstrip('/')}/{S3_BUCKET_NAME}/{object_key}"
        else:
            s3_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{object_key}"
        
        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "message": "ファイルが正常に保存されました",
                "original_filename": file.filename,
                "saved_filename": saved_filename,
                "size": len(file_content),
                "s3_object_key": object_key,
                "s3_url": s3_url,
            }
        )
    
    except HTTPException:
        raise
    except (NoCredentialsError, ClientError, BotoCoreError) as e:
        # 認証・接続系のエラーを補足
        raise HTTPException(status_code=502, detail=f"S3 へのアップロードに失敗しました: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ファイル保存エラー: {str(e)}")


async def call_chatgpt(payload: dict, instructions: str | None = None) -> dict:
    """JSON を GPT に送り、JSON で応答を受け取る"""

    system_prompt = (
        "You are a helpful assistant for Natural Observer. "
        "Summarize the provided image metadata and respond in concise Japanese JSON with keys: "
        "title (string), summary (string), tags (array of short strings)."
    )
    if instructions:
        system_prompt += f" Additional instructions: {instructions}"

    client = get_openai_client()

    # OpenAI クライアント呼び出しはブロッキングのためスレッドに逃がす
    def _call():
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return response

    response = await asyncio.to_thread(_call)
    message_content = response.choices[0].message.content
    try:
        return json.loads(message_content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="GPT からの応答 JSON を解釈できませんでした")


@app.post("/analyze")
async def analyze_with_gpt(body: AnalyzeRequest, db: Session = Depends(get_db)):
    """S3 URL を GPT に渡し、説明を返す。結果は DB に保存"""

    payload = {
        "s3_url": str(body.s3_url),
        "original_filename": body.original_filename,
    }
    gpt_response = await call_chatgpt(payload=payload, instructions=body.instructions)

    # DB に分析結果を保存
    analysis = ImageAnalysis(
        original_filename=body.original_filename,
        s3_object_key=payload["s3_url"],  # S3 URL をキーとして保存
        s3_url=payload["s3_url"],
        file_size=0,  # アップロード時の size を DB に保存していないため、ここでは 0 にセット（別途更新可能）
        gpt_response=gpt_response,
        custom_instructions=body.instructions,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return {
        "status": "success",
        "model": OPENAI_MODEL,
        "analysis_id": analysis.id,
        "input": payload,
        "gpt_response": gpt_response,
        "saved_at": analysis.created_at.isoformat(),
    }


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy"}


@app.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """DB に保存された分析結果を ID で取得"""

    analysis = db.query(ImageAnalysis).filter(ImageAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail=f"分析結果 ID {analysis_id} が見つかりません")

    return {
        "status": "success",
        "id": analysis.id,
        "original_filename": analysis.original_filename,
        "s3_url": analysis.s3_url,
        "gpt_response": analysis.gpt_response,
        "custom_instructions": analysis.custom_instructions,
        "created_at": analysis.created_at.isoformat(),
        "updated_at": analysis.updated_at.isoformat(),
    }


@app.get("/analysis")
async def list_analyses(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """DB に保存されたすべての分析結果をリスト表示（ページング対応）"""

    analyses = db.query(ImageAnalysis).offset(skip).limit(limit).all()
    total = db.query(ImageAnalysis).count()

    return {
        "status": "success",
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "id": a.id,
                "original_filename": a.original_filename,
                "s3_url": a.s3_url,
                "created_at": a.created_at.isoformat(),
            }
            for a in analyses
        ],
    }
