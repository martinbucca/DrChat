from pydantic import BaseModel, Field

class CreateSessionRequest(BaseModel):
    """
    Represents a request to create a new chat session for a user.

    Attributes:
        user_id (str): The identifier of the user for whom the session is to be created.
        session_id (str): The identifier of the new chat session.
        session_name (str): The name of the new chat session.
    """
    user_id: str
    session_id: str
    session_name: str