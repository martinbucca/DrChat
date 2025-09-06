from dotenv import load_dotenv
load_dotenv()  # Load variables from .env for local/dev runs

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth
from .config.database import DataBase, engine

app = FastAPI(title="User Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    DataBase.metadata.create_all(bind=engine)


app.include_router(auth.router, prefix="/api", tags=["auth"])
