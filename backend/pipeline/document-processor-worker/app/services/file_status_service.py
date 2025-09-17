import httpx
import logging
from typing import Optional
from config import FILE_SERVICE_URL

logger = logging.getLogger(__name__)

class FileStatusService:
    """
    Service to communicate with file-service to update file processing status
    """
    
    _instance = None
    
    def __init__(self, file_service_url: str = None):
        self.file_service_url = file_service_url or FILE_SERVICE_URL
        self.client = httpx.Client(timeout=30.0)
    
    def update_file_status(self, file_id: str, status: str) -> bool:
        """
        Update the status of a file in the file-service
        
        Args:
            file_id: The ID of the file to update
            status: The new status (pending, processing, processed, error)
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            url = f"{self.file_service_url}/files/{file_id}/status"
            response = self.client.put(url, params={"status": status})
            
            if response.status_code == 200:
                logger.info(f"Successfully updated file {file_id} status to {status}")
                return True
            else:
                logger.error(f"Failed to update file {file_id} status: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating file {file_id} status to {status}: {str(e)}")
            return False
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()
    
    @classmethod
    def get_instance(cls, file_service_url: str = None):
        if cls._instance is None:
            cls._instance = cls(file_service_url)
        return cls._instance
