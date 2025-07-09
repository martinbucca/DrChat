from fastapi import FastAPI, HTTPException, Request
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app import App
from create_knowledge_graph import KnowledgeGraphBuilder

chatbot = App()

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia esto para restringir los orígenes en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de datos para el request de /find_chunk
class QueryRequest(BaseModel):
    query: str


# Endpoint para recibir queries del frontend
@app.post("/find_chunk")
async def find_chunk_endpoint(request: QueryRequest):
    print("SOLICITUD DE CHUNK")
    try:
        if request.query:
            answer = chatbot.answer_query(request.query)
            return {"answer": answer}
        else:
            raise HTTPException(status_code=400, detail="No se ingresó una consulta válida.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo responder la consulta. Error: {e}")
    

# Endpoint para crear grafo
@app.post("/create_kg")
async def create_kg_endpoint():
    try:
        chatbot.create_knowledge_graph()
        return {"response": "Grafo creado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo crear el grafo a partir del documento. Error: {e}")
        

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
