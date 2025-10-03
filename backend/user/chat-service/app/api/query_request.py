from pydantic import BaseModel

class QueryRequest(BaseModel):
    """
    Represents a request to query the chat service.

    Attributes:
        query (str): The user's query string.
        session_id (str, optional): The session identifier. Defaults to None.
    """
    query: str
    session_id: str = None
    created_at: str = None