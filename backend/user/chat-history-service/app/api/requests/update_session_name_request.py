from pydantic import BaseModel

class UpdateSessionNameRequest(BaseModel):
    """
    Represents a request to update the name of a chat session.

    Attributes:
        user_id (str): The identifier of the user requesting the update.
        session_id (str): The identifier of the session to be updated.
        new_name (str): The new name for the session.
    """
    user_id: str
    session_id: str
    new_name: str