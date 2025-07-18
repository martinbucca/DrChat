from backend.app.services.qa_retriever import VectorRetriever
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.post("/answer_question")
async def answer_question(request: QueryRequest):
    print("SOLICITUD DE CHUNK")
    try:
        vector_retriever = VectorRetriever
        if request.query:
            answer = vector_retriever.answer_with_rag(request.query)
            return {"answer": answer}
        else:
            raise HTTPException(status_code=400, detail="No se ingresó una consulta válida.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo responder la consulta. Error: {e}")