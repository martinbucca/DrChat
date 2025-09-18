from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlalchemy.orm import Session

from ..config.database import get_database
from app.models.user import User


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    profesion: str

    model_config = ConfigDict(from_attributes=True)


router = APIRouter()


@router.get("/users", response_model=List[UserOut])
def get_users(db: Session = Depends(get_database)):
    users = db.query(User).order_by(User.id.asc()).all()
    return users


@router.get("/users/{user_id}", response_model=UserOut)
def get_user_by_id(user_id: int, db: Session = Depends(get_database)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

