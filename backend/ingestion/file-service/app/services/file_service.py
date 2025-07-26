import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException
from pymongo.errors import PyMongoError

from core.config import settings
from core.database import database
from core.logging import logger as log
from models.file import (
    FileUploadResponse, 
    FileStatusResponse, 
    FileStatusUpdateResponse, 
    FileListResponse, 
    FileListItem
)


class FileService:
    def __init__(self):
        self.storage_dir = settings.STORAGE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.files_collection = database.get_files_collection()
    
    async def upload_file(self, file: UploadFile, chat_id: Optional[str] = None) -> FileUploadResponse:
        """Upload a PDF file and save it to storage"""
        log.info(f"Starting file upload: {file.filename}, chat_id: {chat_id}")
        
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
        file_record = {
            "file_id": file_id,
            "original_filename": file.filename,
            "saved_filename": unique_filename,
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "content_type": file.content_type,
            "chat_id": chat_id,
            "status": "pending",
            "upload_time": datetime.now(),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        log.info(f"Created file record with ID: {file_id}")
        
        # Prepare response record first (before MongoDB insertion)
        response_record = FileUploadResponse(
            message="File uploaded successfully",
            file_id=file_id,
            original_filename=file.filename,
            saved_filename=unique_filename,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            content_type=file.content_type,
            chat_id=chat_id,
            status="pending",
            upload_time=datetime.now().isoformat(),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Store in MongoDB
        if self.files_collection is not None:
            try:
                log.info("Saving file record to MongoDB...")
                result = self.files_collection.insert_one(file_record)
                log.info(f"File record saved to MongoDB with ID: {result.inserted_id}")
            except PyMongoError as e:
                log.error(f"Error saving to MongoDB: {e}")
                # Continue without failing the upload
        else:
            log.warning("MongoDB collection not available, skipping database save")
        
        # TODO: Publish to Kafka
        
        log.info(f"File upload completed successfully: {file_id}")
        return response_record
    
    async def get_file_status(self, file_id: str) -> FileStatusResponse:
        """Get file status by ID"""
        log.info(f"Getting file status for ID: {file_id}")
        
        if not database.is_connected():
            log.error("Database connection not available")
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        try:
            file_record = self.files_collection.find_one({"file_id": file_id})
            
            if file_record is None:
                log.warning(f"File not found: {file_id}")
                raise HTTPException(status_code=404, detail="File not found")
            
            log.info(f"File found: {file_id}, status: {file_record.get('status', 'unknown')}")
            
            # Convert ObjectId to string and datetime objects to ISO strings
            file_record["_id"] = str(file_record["_id"])
            if "upload_time" in file_record and isinstance(file_record["upload_time"], datetime):
                file_record["upload_time"] = file_record["upload_time"].isoformat()
            if "created_at" in file_record and isinstance(file_record["created_at"], datetime):
                file_record["created_at"] = file_record["created_at"].isoformat()
            if "updated_at" in file_record and isinstance(file_record["updated_at"], datetime):
                file_record["updated_at"] = file_record["updated_at"].isoformat()
            
            return FileStatusResponse(**file_record)
        
        except PyMongoError as e:
            log.error(f"Database error while getting file {file_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def update_file_status(self, file_id: str, status: str) -> FileStatusUpdateResponse:
        """Update file status"""
        log.info(f"Updating file status: {file_id} -> {status}")
        
        valid_statuses = ["pending", "processing", "processed", "error"]
        if status not in valid_statuses:
            log.warning(f"Invalid status attempted: {status} for file {file_id}")
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        if not database.is_connected():
            log.error("Database connection not available")
            raise HTTPException(status_code=503, detail="Database connection not available")
        
        try:
            # Update the file status in MongoDB
            result = self.files_collection.update_one(
                {"file_id": file_id},
                {
                    "$set": {
                        "status": status,
                        "updated_at": datetime.now()
                    }
                }
            )
            
            if result.matched_count == 0:
                log.warning(f"File not found for status update: {file_id}")
                raise HTTPException(status_code=404, detail="File not found")
            
            log.info(f"Status updated successfully: {file_id} -> {status}")
            
            return FileStatusUpdateResponse(
                file_id=file_id,
                status=status,
                updated_at=datetime.now().isoformat(),
                message="Status updated successfully"
            )
        
        except PyMongoError as e:
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
