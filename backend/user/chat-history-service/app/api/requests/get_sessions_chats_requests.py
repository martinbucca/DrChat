from pydantic import BaseModel

class GetSessionsChatsRequest(BaseModel):
    """
    Represents a request to get chat sessions and their associated chats for a user.

    Attributes:
        user_id (str): The identifier of the user whose chat sessions are to be retrieved.
    """
    user_id: str