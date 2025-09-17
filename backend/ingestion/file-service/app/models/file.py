from pydantic import BaseModel
from typing import Optional
from datetime import datetime


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
