from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from typing import Optional

from services.file_service import file_service
from core.database import get_database
from models.file import (
    FileUploadResponse,
    FileStatusResponse,
    FileStatusUpdateResponse,
    FileListResponse
)

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...), 
    session_id: str = Form(...),
    db: Session = Depends(get_database)
):
    """Upload a PDF file and save it to the shared storage directory"""
    return await file_service.upload_file(file, session_id, db)


@router.get("/{file_id}", response_model=FileStatusResponse)
async def get_file_status(file_id: str, db: Session = Depends(get_database)):
    """Get the status of a file by its ID"""
    return await file_service.get_file_status(file_id, db)


@router.put("/{file_id}/status", response_model=FileStatusUpdateResponse)
async def update_file_status(file_id: str, status: str, db: Session = Depends(get_database)):
    """Update the status of a file (pending, processing, processed, error)"""
    return await file_service.update_file_status(file_id, status, db)


@router.get("", response_model=FileListResponse)
async def list_files():
    """List all uploaded files in the shared storage directory"""
    return await file_service.list_files()
