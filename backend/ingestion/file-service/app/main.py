from dotenv import load_dotenv
load_dotenv()  # Load variables from .env for local/dev runs

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from core.logging import setup_logging
from core.database import DataBase, engine
from api import router
from services import kafka_service

# Setup logging
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - Create database tables
    DataBase.metadata.create_all(bind=engine)
    yield
    # Shutdown
    kafka_service.close()

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
