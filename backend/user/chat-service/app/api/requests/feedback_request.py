from typing import Optional
from pydantic import BaseModel

class FeedbackRequest(BaseModel):
    """
    Represents feedback provided for a chatbot's response.

    Attributes:
        like (bool): True for positive feedback, False for negative feedback.
        session_id (str): Identifier for the session in which the feedback was given.
        question (Optional[str]): The question that was asked to the chatbot.
        response (Optional[str]): The response given by the chatbot.
    """
    like: bool
    session_id: str
    question: Optional[str] = None
    response: Optional[str] = None
