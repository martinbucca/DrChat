from fastapi import FastAPI
from app.routes.api.router import api_router

app = FastAPI(title="PDF Microservice API")
app.include_router(api_router)
