from backend.app.services.kg_builder import KnowledgeGraphBuilder
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/create_graph")
async def create_kg_from_documents():
    try:
        kg_builder = KnowledgeGraphBuilder()
        kg_builder.create_kg()
        return {"response": "Grafo creado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo crear el grafo a partir del documento. Error: {e}")