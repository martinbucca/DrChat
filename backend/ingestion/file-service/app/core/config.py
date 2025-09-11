import os
from pathlib import Path


class Settings:
    # MongoDB configuration
    MONGO_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("MONGODB_DATABASE_NAME", "drchat")
    COLLECTION_NAME: str = "files"
    
    # Storage configuration
    STORAGE_DIR: Path = Path(os.getenv("STORAGE_DIR", "../../../storage"))
    
    # Kafka configuration
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_FILE_UPLOAD_TOPIC: str = os.getenv("KAFKA_FILE_UPLOAD_TOPIC", "file-upload-events")
    
    # API configuration
    API_TITLE: str = "File Service"
    API_DESCRIPTION: str = "A microservice for handling PDF file uploads and storage"
    API_VERSION: str = "1.0.0"
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "file_service.log"


settings = Settings()
