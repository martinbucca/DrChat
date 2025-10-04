from app.config.database import DataBase
from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Boolean, func


class Feedback(DataBase):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(BigInteger, nullable=False)
    is_liked = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
