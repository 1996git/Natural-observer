"""SQLAlchemy による DB セッション管理"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import DATABASE_URL

# データベースエンジン作成
if DATABASE_URL.startswith("sqlite"):
    # SQLite の場合は check_same_thread を無効化
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

# セッションファクトリ
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI 依存性注入用のジェネレータ"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
