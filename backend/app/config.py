import os
from pathlib import Path
from dotenv import load_dotenv

# .env ファイルを読み込み（存在する場合）
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# プロジェクトルートディレクトリ
BASE_DIR = Path(__file__).parent.parent

# アップロードディレクトリ（ローカル保存をする場合に使用）
UPLOAD_DIR = BASE_DIR / "uploads"

# サーバー設定
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# ファイルアップロード設定
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}

# S3 設定（環境変数から取得）
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
S3_REGION = os.getenv("S3_REGION", "ap-northeast-1")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")  # カスタムエンドポイント（例: MinIO）
S3_OBJECT_PREFIX = os.getenv("S3_OBJECT_PREFIX", "uploads/")

# OpenAI / GPT 設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # 互換エンドポイントを利用する場合に指定

# データベース設定
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./natural_observer.db")
# 例: PostgreSQL の場合は postgresql://user:password@localhost/dbname

# CORS 許可オリジン（環境変数から読み込み、カンマ区切り）
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

# セキュリティチェック: 本番環境で必須の環境変数が設定されているか確認
if not DEBUG:
    required_vars = ["S3_BUCKET_NAME", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise RuntimeError(f"本番環境で必須の環境変数が設定されていません: {', '.join(missing_vars)}")
