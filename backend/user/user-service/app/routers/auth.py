from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from ..config.database import get_database
from app.models.user import User
from passlib.context import CryptContext
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    profesion: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    name: Optional[str]
    email: EmailStr
    token: str


router = APIRouter()


def hash_password(pw: str) -> str:
    return pwd_context.hash(pw)


def verify_password(pw: str, hashed: str) -> bool:
    return pwd_context.verify(pw, hashed)


@router.post("/register", response_model=AuthResponse)
def register(body: RegisterRequest, db: Session = Depends(get_database)):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        name=body.name,
        email=body.email,
        password=hash_password(body.password),
        profesion=body.profesion or "N/A",
    )
    db.add(user)
    db.commit()
    # Esto hay que mejorarlo si lo queremos serio, es un login muy de juguete
    token = f"token-{user.email}"
    return {"name": user.name, "email": user.email, "token": token}


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_database)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = f"token-{user.email}"
    return {"name": user.name, "email": user.email, "token": token}
