from fastapi import FastAPI
from documents import router as documents_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="File Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, allow all. You can restrict it to ["http://localhost:3000"] later.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(documents_router,tags=["Documents"])
