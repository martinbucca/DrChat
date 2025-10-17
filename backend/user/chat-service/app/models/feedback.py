from app.config.database import DataBase
from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

class Feedback(DataBase):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    message_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    question: Mapped[str | None] = mapped_column(String, nullable=True)
    response: Mapped[str | None] = mapped_column(String, nullable=True)
    is_liked: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    session_id: Mapped[str | None] = mapped_column(String, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)