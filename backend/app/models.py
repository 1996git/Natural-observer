"""SQLAlchemy ORM モデル定義"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ImageAnalysis(Base):
    """画像分析結果を格納するテーブル"""

    __tablename__ = "image_analysis"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String(255), nullable=False)
    s3_object_key = Column(String(1024), nullable=False, unique=True)
    s3_url = Column(String(2048), nullable=False)
    file_size = Column(Integer, nullable=False)
    gpt_response = Column(JSON, nullable=False)  # JSON 形式で保存
    custom_instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ImageAnalysis(id={self.id}, filename={self.original_filename})>"
