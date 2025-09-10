from pydantic import BaseModel

class DeleteSessionRequest(BaseModel):
    """
    Represents a request to delete a chat session.

    Attributes:
        user_id (str): The identifier of the user requesting the deletion.
        session_id (str): The identifier of the session to be deleted.
    """
    user_id: str
    session_id: str