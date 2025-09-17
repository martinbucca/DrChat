import logging
from .config import settings


def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(settings.LOG_FILE)
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()
