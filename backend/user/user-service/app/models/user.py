from datetime import datetime

from app.config.database import DataBase
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class User(DataBase):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    profesion: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True, server_default="N/A"
    )
    password: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
