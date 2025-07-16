from backend.app.routes.api import documents, graph, qa
from fastapi import APIRouter


api_router = APIRouter()
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(graph.router, prefix="/graph", tags=["Graph"])
api_router.include_router(qa.router, prefix="/answer", tags=["Answer"])
