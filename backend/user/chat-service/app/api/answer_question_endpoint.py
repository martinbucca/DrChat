from fastapi import HTTPException
from app.api.query_request import QueryRequest
from app.services.chat_history import LLMMessage

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
    def __init__(self, app, graphrag, chat_message_history):
        self._app = app
        self._graphrag = graphrag
        self._chat_message_history = chat_message_history
        self._register_endpoint()

    def _register_endpoint(self):
        @self._app.post("/answer_question")
        async def answer_question(request: QueryRequest):
            try:
                if not request.query or not request.query.strip():
                    raise HTTPException(status_code=400, detail="Consulta inválida")
                session_id = request.session_id
                question = request.query
                question_message = LLMMessage(role="user", content=question)
                self._chat_message_history.add_message(question_message, session_id)
                result = self._graphrag.search(question, session_id)
                answer = result.answer
                answer_message = LLMMessage(role="ai", content=answer)
                self._chat_message_history.add_message(answer_message, session_id)
                retriever_result = result.retriever_result
                retriever_nodes = []
                for item in retriever_result.items:
                    retriever_nodes.append(item.metadata)
                return {"answer": answer, "retriever_result": retriever_nodes}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
