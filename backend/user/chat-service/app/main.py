import uvicorn
from app.services.driver import Neo4jDriver
from app.services.embedding import Embedding
from app.services.llm import LLM
from app.services.retriever import Retriever
from app.services.graph_rag import GraphRAGPipeline
from app.services.chat_history import ChatMessageHistory
from app.api.api import API
from app.api.answer_question_endpoint import AnswerQuestionEndpoint
from app.config import (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, VECTOR_INDEX_NAME, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

llm_instance = LLM.get_instance()
llm = llm_instance.llm

driver_instance = Neo4jDriver(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
driver = driver_instance.driver

driver_instance_messages = Neo4jDriver(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
driver_messages = driver_instance_messages.driver


embedding_instance = Embedding.get_instance()
embedder = embedding_instance.embedder

retriever_instance = Retriever.get_instance(driver, embedder, VECTOR_INDEX_NAME)
retriever = retriever_instance.retriever

chat_message_history = ChatMessageHistory.get_instance(driver_messages)

graphrag = GraphRAGPipeline(
    llm=llm,
    retriever=retriever,
    history=chat_message_history
)

api_instance = API.get_instance()
app = api_instance.app

qa_endpoint = AnswerQuestionEndpoint(app, graphrag)


@app.on_event("shutdown")
def shutdown_event():
    driver.close()
    driver_messages.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
