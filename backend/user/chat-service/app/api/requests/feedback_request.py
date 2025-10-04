from pydantic import BaseModel

class FeedbackRequest(BaseModel):
    """
    Represents a feedback given to a response from the chatbot.

    Attributes:
        message_id (int): The message identifier..
        like (bool): True for positive feedback. False for negative feedback
    """
    message_id: int
    like: bool