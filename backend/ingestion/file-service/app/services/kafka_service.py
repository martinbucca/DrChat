import json
from datetime import datetime
from typing import Optional, Dict, Any
from kafka import KafkaProducer
from kafka.errors import KafkaError

from core.config import settings
from core.logging import logger as log
from models.file import FileUploadEvent


class KafkaService:
    def __init__(self):
        self.producer: Optional[KafkaProducer] = None
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.file_upload_topic = settings.KAFKA_FILE_UPLOAD_TOPIC
        self._initialize_producer()
    
    def _initialize_producer(self):
        """Initialize Kafka producer with retry logic"""
        try:
            log.info(f"Initializing Kafka producer with servers: {self.bootstrap_servers}")
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retries=3,
                retry_backoff_ms=1000,
                request_timeout_ms=30000,
                api_version=(0, 10, 1)
            )
            log.info("Kafka producer initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize Kafka producer: {e}")
            self.producer = None
    
    def is_connected(self) -> bool:
        """Check if Kafka producer is connected"""
        return self.producer is not None
    
    async def publish_file_upload_event(self, file_data: Dict[str, Any]) -> bool:
        """
        Publish file upload event to Kafka topic
        
        Args:
            file_data: Dictionary containing file information
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not self.is_connected():
            log.warning("Kafka producer not available, skipping message publication")
            return False
        
        try:
            # Prepare the message using the FileUploadEvent model
            # Now we always receive strings for timestamps
            event = FileUploadEvent(
                event_type="file_uploaded",
                file_id=file_data.get("file_id"),
                original_filename=file_data.get("original_filename"),
                saved_filename=file_data.get("saved_filename"),
                file_path=file_data.get("file_path"),
                file_size=file_data.get("file_size"),
                content_type=file_data.get("content_type"),
                session_id=file_data.get("session_id"),
                status=file_data.get("status"),
                upload_time=file_data.get("upload_time"),
                timestamp=file_data.get("created_at")
            )
            
            # Convert to dict for JSON serialization
            message = event.model_dump()
            
            # Use file_id as the message key for partitioning
            key = file_data.get("file_id")
            
            log.info(f"Publishing file upload event to topic '{self.file_upload_topic}' for file: {file_data.get('file_id')}")
            
            # Send the message
            future = self.producer.send(
                topic=self.file_upload_topic,
                key=key,
                value=message
            )
            
            # Wait for the message to be sent (with timeout)
            record_metadata = future.get(timeout=10)
            
            log.info(f"Message sent successfully to topic '{record_metadata.topic}', "
                    f"partition {record_metadata.partition}, offset {record_metadata.offset}")
            
            return True
            
        except KafkaError as e:
            log.error(f"Kafka error while publishing file upload event: {e}")
            return False
        except Exception as e:
            log.error(f"Unexpected error while publishing file upload event: {e}")
            return False
    
    def close(self):
        """Close the Kafka producer"""
        if self.producer:
            try:
                log.info("Closing Kafka producer")
                self.producer.close()
                self.producer = None
                log.info("Kafka producer closed successfully")
            except Exception as e:
                log.error(f"Error closing Kafka producer: {e}")


# Global Kafka service instance
kafka_service = KafkaService()
