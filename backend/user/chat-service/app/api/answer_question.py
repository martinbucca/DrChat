from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.graph_rag import graphrag

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/answer_question")
async def answer_question(request: QueryRequest):
    try:
        if request.query.strip():
            result = graphrag.search(request.query)
            return {"answer": result.answer}
        else:
            raise HTTPException(status_code=400, detail="Consulta inválida")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {e}")
