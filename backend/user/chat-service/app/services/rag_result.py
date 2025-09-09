from pydantic import BaseModel
from neo4j_graphrag.types import RetrieverResult
from typing import Optional

class RagResult(BaseModel):
    """
    Represents the result of a Retrieval-Augmented Generation (RAG) process.

    Attributes:
        answer (str): The generated answer from the RAG process.
        retriever_result (Optional[RetrieverResult]): The result returned by the retriever component, if available.
    """
    answer: str
    created_at: Optional[str] = None
    retriever_result: Optional[RetrieverResult] = None