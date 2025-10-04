from datetime import datetime
from fastapi import HTTPException, Depends
from app.api.requests.feedback_request import FeedbackRequest
from sqlalchemy.orm import Session
from app.config.database import get_database
from app.models.feedback import Feedback

import logging
logger = logging.getLogger(__name__)

class FeedbackEndpoint:
    def __init__(self, app):
        self.app = app
        self._register_endpoint()

    def _register_endpoint(self):
        @self.app.post("/feedback")
        async def feedback(feedback: FeedbackRequest, db: Session = Depends(get_database)):
            try:
                message_id = feedback.message_id
                is_liked = feedback.like

                new_feedback = Feedback(
                    message_id=message_id,
                    is_liked=is_liked,
                )
                logger.error(new_feedback)
                db.add(new_feedback)
                db.commit()
                logger.error("commited")
                db.refresh(new_feedback)
                return {
                    "message_id": new_feedback.message_id,
                    "is_liked": new_feedback.is_liked,
                    "created_at": new_feedback.created_at,
                    "message": "Feedback agregado exitosamente"
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
            