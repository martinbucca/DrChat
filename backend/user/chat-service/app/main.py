import uvicorn
from app.services.driver import Neo4jDriver
from app.services.embedding import Embedding
from app.services.llm import LLM
from app.services.retriever import Retriever
from app.services.graph_rag import GraphRAGPipeline
from app.services.chat_history import ChatMessageHistory
from app.api.api import API
from app.api.answer_question_endpoint import AnswerQuestionEndpoint
from app.config import (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, VECTOR_INDEX_NAME)

llm_instance = LLM.get_instance()
llm = llm_instance.llm

driver_instance = Neo4jDriver.get_instance(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
driver = driver_instance.driver

embedding_instance = Embedding.get_instance()
embedder = embedding_instance.embedder

retriever_instance = Retriever.get_instance(driver, embedder, VECTOR_INDEX_NAME)
retriever = retriever_instance.retriever

chat_message_history = ChatMessageHistory.get_instance(driver)

graphrag = GraphRAGPipeline(
    llm=llm,
    retriever=retriever,
    history=chat_message_history
)

api_instance = API.get_instance()
app = api_instance.app

qa_endpoint = AnswerQuestionEndpoint(app, graphrag, chat_message_history)


@app.on_event("shutdown")
def shutdown_event():
    driver.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
