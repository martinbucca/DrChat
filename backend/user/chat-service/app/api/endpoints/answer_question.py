from fastapi import HTTPException
from app.api.requests.query_request import QueryRequest
from app.services.chat_history import LLMMessage
import logging

logger = logging.getLogger(__name__)

class AnswerQuestionEndpoint:
    """
    Endpoint class for handling question-answering requests.
    This class registers a POST endpoint `/answer_question` on the provided FastAPI app.
    It receives a `QueryRequest` containing a user query and session ID, validates the input,
    and uses the provided `graphrag` object to search for an answer. The response includes
    the answer and retriever result. Handles invalid queries and internal errors with appropriate HTTP exceptions.
    Args:
        app: FastAPI application instance where the endpoint will be registered.
        graphrag: An object with a `search(query, session_id)` method to process the query.
    Methods:
        _register_endpoint():
            Registers the `/answer_question` POST endpoint.
    """
    def __init__(self, app, graphrag):
        self._app = app
        self._graphrag = graphrag
        self._register_endpoint()

    def _register_endpoint(self):
        @self._app.post("/answer_question")
        async def answer_question(request: QueryRequest):
            try:
                if not request.query or not request.query.strip():
                    raise HTTPException(status_code=400, detail="Consulta inválida")
                    
                session_id = request.session_id
                question = request.query
                created_at = request.created_at
                
                result = self._graphrag.search(question, session_id, created_at)
                answer = result.answer
                retriever_result = result.retriever_result
                
                answer_created_at = result.created_at
                retriever_nodes = []
                for item in retriever_result.items:
                    retriever_nodes.append(item.metadata)
                return {"answer": answer, "retriever_result": retriever_nodes, "answer_created_at": answer_created_at}
            except Exception as e:
                logger.error(f"Error processing question: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
