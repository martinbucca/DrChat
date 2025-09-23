import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from core.config import settings
from core.database import get_database
from core.logging import logger as log
from models.file import (
    FileModel,
    FileUploadResponse, 
    FileStatusResponse, 
    FileStatusUpdateResponse, 
    FileListResponse, 
    FileListItem
)
from .kafka_service import kafka_service


class FileService:
    def __init__(self):
        self.storage_dir = settings.STORAGE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(self, file: UploadFile, session_id: str, db: Session) -> FileUploadResponse:
        """Upload a PDF file and save it to storage"""
        log.info(f"Starting file upload: {file.filename}, session_id: {session_id}")
        
        # Validate file type (PDF only)
        if not file.filename.lower().endswith('.pdf'):
            log.warning(f"Invalid file type attempted: {file.filename}")
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Generate unique filename to avoid conflicts
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = self.storage_dir / unique_filename
        
        log.info(f"Saving file to: {file_path}")
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        log.info(f"File saved successfully: {unique_filename}")
        
        # Create file record
        file_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        # Create SQLAlchemy model instance
        file_record = FileModel(
            file_id=file_id,
            original_filename=file.filename,
            saved_filename=unique_filename,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            content_type=file.content_type,
            session_id=session_id,
            status="pending",
            upload_time=current_time,
            created_at=current_time,
            updated_at=current_time
        )
        
        log.info(f"Created file record with ID: {file_id}")
        
        # Prepare response record first (before database insertion)
        response_record = FileUploadResponse(
            message="File uploaded successfully",
            file_id=file_id,
            original_filename=file.filename,
            saved_filename=unique_filename,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            content_type=file.content_type,
            session_id=session_id,
            status="pending",
            upload_time=current_time.isoformat(),
            created_at=current_time.isoformat(),
            updated_at=current_time.isoformat()
        )
        
        # Store in PostgreSQL
        try:
            log.info("Saving file record to PostgreSQL...")
            db.add(file_record)
            db.commit()
            db.refresh(file_record)
            log.info(f"File record saved to PostgreSQL with ID: {file_record.id}")
        except SQLAlchemyError as e:
            db.rollback()
            log.error(f"Error saving to PostgreSQL: {e}")
            # Continue without failing the upload
        
        # Publish to Kafka
        kafka_success = False
        try:
            log.info(f"Publishing file upload event to Kafka for file: {file_id}")

            kafka_record = {
                "file_id": file_id,
                "original_filename": file.filename,
                "saved_filename": unique_filename,
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "content_type": file.content_type,
                "session_id": session_id,
                "status": "pending",
                "upload_time": current_time.isoformat(),
                "created_at": current_time.isoformat(),
                "updated_at": current_time.isoformat()
            }
            
            kafka_success = await kafka_service.publish_file_upload_event(kafka_record)
            if kafka_success:
                log.info(f"File upload event published successfully to Kafka for file: {file_id}")
            else:
                log.warning(f"Failed to publish file upload event to Kafka for file: {file_id}")
        except Exception as e:
            log.error(f"Error publishing to Kafka: {e}")
            kafka_success = False
        
        # Update status in PostgreSQL if Kafka publication failed
        if not kafka_success:
            try:
                log.info(f"Updating file status to 'notification_failed' for file: {file_id}")
                file_record.status = "notification_failed"
                file_record.notification_error = "Failed to publish file upload event to Kafka"
                file_record.updated_at = datetime.now()
                db.commit()
                log.info(f"File status updated to 'notification_failed' for file: {file_id}")
                
                # Also update the response record
                response_record.status = "notification_failed"
                
            except SQLAlchemyError as e:
                db.rollback()
                log.error(f"Error updating file status in PostgreSQL: {e}")
        
        log.info(f"File upload completed successfully: {file_id}")
        return response_record
    
    async def get_file_status(self, file_id: str, db: Session) -> FileStatusResponse:
        """Get file status by ID"""
        log.info(f"Getting file status for ID: {file_id}")
        
        try:
            file_record = db.query(FileModel).filter(FileModel.file_id == file_id).first()
            
            if file_record is None:
                log.warning(f"File not found: {file_id}")
                raise HTTPException(status_code=404, detail="File not found")
            
            log.info(f"File found: {file_id}, status: {file_record.status}")
            
            return FileStatusResponse(
                file_id=file_record.file_id,
                original_filename=file_record.original_filename,
                saved_filename=file_record.saved_filename,
                file_path=file_record.file_path,
                file_size=file_record.file_size,
                content_type=file_record.content_type,
                session_id=file_record.session_id,
                status=file_record.status,
                upload_time=file_record.upload_time.isoformat(),
                created_at=file_record.created_at.isoformat(),
                updated_at=file_record.updated_at.isoformat(),
                _id=str(file_record.id)  # For compatibility with existing API
            )
        
        except SQLAlchemyError as e:
            log.error(f"Database error while getting file {file_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def update_file_status(self, file_id: str, status: str, db: Session) -> FileStatusUpdateResponse:
        """Update file status"""
        log.info(f"Updating file status: {file_id} -> {status}")

        valid_statuses = ["pending", "processing", "processed", "error", "notification_failed"]
        if status not in valid_statuses:
            log.warning(f"Invalid status attempted: {status} for file {file_id}")
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

        try:
            # Update the file status in PostgreSQL
            file_record = db.query(FileModel).filter(FileModel.file_id == file_id).first()

            if file_record is None:
                log.warning(f"File not found for status update: {file_id}")
                raise HTTPException(status_code=404, detail="File not found")

            file_record.status = status
            file_record.updated_at = datetime.now()
            db.commit()

            log.info(f"Status updated successfully: {file_id} -> {status}")

            return FileStatusUpdateResponse(
                file_id=file_id,
                status=status,
                updated_at=datetime.now().isoformat(),
                message="Status updated successfully"
            )

        except SQLAlchemyError as e:
            db.rollback()
            log.error(f"Database error while updating status for {file_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def list_files(self) -> FileListResponse:
        """List all files in storage directory"""
        log.info(f"Listing files in storage directory: {self.storage_dir}")

        try:
            files = []
            for file_path in self.storage_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() == '.pdf':
                    files.append(FileListItem(
                        filename=file_path.name,
                        size=file_path.stat().st_size,
                        modified=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        path=str(file_path)
                    ))

            log.info(f"Found {len(files)} PDF files in storage")

            return FileListResponse(
                files=files,
                total_files=len(files),
                storage_directory=str(self.storage_dir)
            )

        except Exception as e:
            log.error(f"Error listing files: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


# Global file service instance
file_service = FileService()
