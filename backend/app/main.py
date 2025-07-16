from fastapi import FastAPI
import uvicorn
from backend.app.routes.api.router import api_router

app = FastAPI(title="PDF Microservice API")
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
