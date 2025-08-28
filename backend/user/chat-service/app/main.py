from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from app.api.answer_question import router

app = FastAPI(title="Chat Service API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/qa")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
