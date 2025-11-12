from datetime import datetime
from fastapi import HTTPException, Depends
from app.api.requests.feedback_request import FeedbackRequest
from sqlalchemy.orm import Session
from app.config.database import get_database
from app.models.feedback import Feedback

import logging
logger = logging.getLogger(__name__)

class FeedbackEndpoint:
    def __init__(self, app, driver):
        self._app = app
        self._driver = driver
        self._register_endpoint()

    def _register_endpoint(self):
        @self._app.post("/feedback")
        async def feedback(feedback: FeedbackRequest, db: Session = Depends(get_database)):
            try:
                session_id = feedback.session_id
                is_liked = feedback.like
                question = feedback.question
                response = feedback.response
                message_id = feedback.message_id

                with self._driver.session() as session:
                    result = session.run(
                        "MATCH (u:User)-[:HAS_SESSION]->(s:Session {id: $session_id}) "
                        "RETURN u.id AS user_id",
                        session_id=session_id
                    )
                    record = result.single()
                    user_id =  record["user_id"] if record else None

                new_feedback = Feedback(
                    session_id = session_id,
                    is_liked = is_liked,
                    question = question,
                    response = response,
                    user_id = user_id,
                    message_id = message_id,
                )
                db.add(new_feedback)
                db.commit()
                db.refresh(new_feedback)
                return {
                    "session_id": new_feedback.session_id,
                    "is_liked": new_feedback.is_liked,
                    "created_at": new_feedback.created_at,
                    "question": new_feedback.question,
                    "response": new_feedback.response,
                    "user_id": new_feedback.user_id,
                    "message_id": new_feedback.message_id,
                    "Score": "Feedback agregado exitosamente"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
            