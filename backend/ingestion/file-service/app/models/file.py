from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy import Integer, String, BigInteger, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from core.database import DataBase


# SQLAlchemy model for database
class FileModel(DataBase):
    __tablename__ = "files"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    saved_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    upload_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    notification_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# Pydantic models for API responses (unchanged)
class FileUploadResponse(BaseModel):
    message: str
    file_id: str
    original_filename: str
    saved_filename: str
    file_path: str
    file_size: int
    content_type: Optional[str]
    session_id: str
    status: str
    upload_time: str
    created_at: str
    updated_at: str


class FileStatusResponse(BaseModel):
    file_id: str
    original_filename: str
    saved_filename: str
    file_path: str
    file_size: int
    content_type: Optional[str]
    session_id: str
    status: str
    upload_time: str
    created_at: str
    updated_at: str
    _id: str


class FileStatusUpdateResponse(BaseModel):
    file_id: str
    status: str
    updated_at: str
    message: str


class FileUploadEvent(BaseModel):
    """Model for Kafka file upload event message"""
    event_type: str
    file_id: str
    original_filename: str
    saved_filename: str
    file_path: str
    file_size: int
    content_type: Optional[str]
    session_id: str  # Required session ID for chat isolation
    status: str
    upload_time: str
    timestamp: str


class FileListItem(BaseModel):
    filename: str
    size: int
    modified: str
    path: str


class FileListResponse(BaseModel):
    files: list[FileListItem]
    total_files: int
    storage_directory: str


class HealthCheckResponse(BaseModel):
    message: str
    timestamp: str
