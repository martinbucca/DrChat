import os
from pathlib import Path


class Settings:
    # PostgreSQL configuration
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB")
    
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
