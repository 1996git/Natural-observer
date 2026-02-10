# Backend API

FastAPI を使用した Natural Observer のバックエンド API です。

## セットアップ

```bash
# 依存パッケージをインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env

# サーバーを起動
python run.py
```

### 環境変数（必須）
- `S3_BUCKET_NAME`: 保存先バケット名（必須）
- `S3_REGION`: リージョン（例: ap-northeast-1）
- `S3_ENDPOINT_URL`: 任意。カスタムエンドポイント／MinIO 利用時に指定
- `S3_OBJECT_PREFIX`: 任意。オブジェクトキーの接頭辞（デフォルト: uploads/）

### 環境変数（OpenAI / GPT）
- `OPENAI_API_KEY`: ChatGPT へのリクエスト用 API キー（必須）
- `OPENAI_MODEL`: 使用モデル名（デフォルト: gpt-4o-mini）
- `OPENAI_BASE_URL`: 任意。OpenAI 互換エンドポイントを使う場合に指定

### 環境変数（データベース）
- `DATABASE_URL`: DB 接続文字列（デフォルト: sqlite:///./natural_observer.db）
  - PostgreSQL の場合: `postgresql://user:password@localhost/dbname`

## API エンドポイント

### POST /upload
画像ファイルをアップロードして S3（または互換ストレージ）に保存します。

**リクエスト:**
- Content-Type: multipart/form-data
- file: アップロードする画像ファイル（jpg, jpeg, png, gif, bmp）

**レスポンス:**
```json
{
  "status": "success",
  "message": "ファイルが正常に保存されました",
  "original_filename": "photo.jpg",
  "saved_filename": "20260124_120530_abc12345.jpg",
  "size": 1024000,
    "s3_object_key": "uploads/20260124_120530_abc12345.jpg",
    "s3_url": "https://your-bucket.s3.ap-northeast-1.amazonaws.com/uploads/20260124_120530_abc12345.jpg"
}
```

### GET /
API の基本情報を取得します。

### GET /health
ヘルスチェック用のエンドポイント。

### GET /analysis/{id}
DB に保存された特定の分析結果を ID で取得します。

**レスポンス(JSON):**
```json
{
  "status": "success",
  "id": 1,
  "original_filename": "photo.jpg",
  "s3_url": "https://your-bucket.s3.ap-northeast-1.amazonaws.com/uploads/20260124_120530_abc12345.jpg",
  "gpt_response": {
    "title": "○○",
    "summary": "○○",
    "tags": ["tag1", "tag2"]
  },
  "custom_instructions": null,
  "created_at": "2026-01-24T12:05:30.123456",
  "updated_at": "2026-01-24T12:05:30.123456"
}
```

### GET /analysis
DB に保存されたすべての分析結果をリスト表示します（ページング対応）。

**クエリパラメータ:**
- `skip`: スキップするレコード数（デフォルト: 0）
- `limit`: 取得する最大レコード数（デフォルト: 10）

**レスポンス(JSON):**
```json
{
  "status": "success",
  "total": 25,
  "skip": 0,
  "limit": 10,
  "items": [
    {
      "id": 1,
      "original_filename": "photo.jpg",
      "s3_url": "https://...",
      "created_at": "2026-01-24T12:05:30.123456"
    }
  ]
}
```

### POST /analyze
S3 に保存済みの画像 URL を GPT へ渡し、説明 JSON を返します。

**リクエスト(JSON):**
```json
{
  "s3_url": "https://your-bucket.s3.ap-northeast-1.amazonaws.com/uploads/20260124_120530_abc12345.jpg",
  "original_filename": "photo.jpg",
  "instructions": "任意の追加指示"
}
```

**レスポンス(JSON):**
```json
{
  "status": "success",
  "model": "gpt-4o-mini",
  "input": {
    "s3_url": "https://...",
    "original_filename": "photo.jpg"
  },
  "gpt_response": {
    "title": "○○",
    "summary": "○○",
    "tags": ["tag1", "tag2"]
  }
}
```

## ディレクトリ構成

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py       # 設定ファイル
│   ├── main.py         # FastAPI アプリケーション
│   ├── database.py     # DB セッション管理
│   └── models.py       # SQLAlchemy ORM モデル
├── uploads/            # アップロードされた画像の保存先（ローカル時）
├── natural_observer.db # SQLite DB ファイル（デフォルト）
├── run.py              # サーバー起動スクリプト
└── requirements.txt    # 依存パッケージ
```
