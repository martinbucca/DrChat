import os
import re
import requests
import firebase_admin
from firebase_admin import auth as fb_auth, credentials
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from ..config.database import get_database
from app.models.user import User
from passlib.context import CryptContext
from typing import Optional


if not firebase_admin._apps:
    try:
        cred = credentials.ApplicationDefault()
        project_id = os.getenv("FIREBASE_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
        options = {"projectId": project_id} if project_id else None
        firebase_admin.initialize_app(cred, options)
    except Exception as e:
        pass

def _firebase_send_verification_email(email: str, raw_password: str):
    """
    Crea/sincroniza usuario en Firebase Auth con mismo email/password y pide a Firebase
    que envíe el correo de verificación (sendOobCode VERIFY_EMAIL).
    """
    # 1) Crear o asegurar usuario en Firebase Auth
    try:
        try:
            fb_user = fb_auth.get_user_by_email(email)
        except fb_auth.UserNotFoundError:
            fb_user = fb_auth.create_user(email=email, password=raw_password)
        # Si existe pero no tiene password válida, opcionalmente:
        # fb_auth.update_user(fb_user.uid, password=raw_password)
    except Exception as e:
        raise RuntimeError(f"No se pudo crear/sincronizar usuario en Firebase: {e}")

    api_key = os.getenv("FIREBASE_WEB_API_KEY")
    if not api_key:
        raise RuntimeError("Falta FIREBASE_WEB_API_KEY en el entorno")
    try:
        r = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
            json={"email": email, "password": raw_password, "returnSecureToken": True},
            timeout=10,
        )
        r.raise_for_status()
        id_token = r.json()["idToken"]
    except Exception as e:
        raise RuntimeError(f"Falló signInWithPassword para obtener idToken: {e}")

    # 3) Pedir a Firebase que ENVÍE el mail de verificación
    try:
        r = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}",
            json={"requestType": "VERIFY_EMAIL", "idToken": id_token},
            timeout=10,
        )
        r.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Falló sendOobCode (VERIFY_EMAIL): {e}")


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
    id: str
    name: Optional[str]
    email: EmailStr
    token: str

router = APIRouter()

def hash_password(pw: str) -> str:
    return pwd_context.hash(pw)

def verify_password(pw: str, hashed: str) -> bool:
    return pwd_context.verify(pw, hashed)

def _normalize_user_id(email: str) -> str:
    """
    Genera un user_id a partir de un email.

    Toma la parte local del email (antes de '@'), la pasa a minúsculas y elimina
    todos los caracteres que no sean alfanuméricos ASCII (a–z, 0–9). Si luego
    de sanearla queda vacía, devuelve el valor por defecto "user".
    """
    local_part = email.split("@", 1)[0].lower()
    sanitized = re.sub(r"[^a-z0-9]", "", local_part)
    return sanitized or "user"

@router.post("/register", response_model=AuthResponse)
def register(body: RegisterRequest, db: Session = Depends(get_database)):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        user_id=_normalize_user_id(body.email),
        name=body.name,
        email=body.email,
        password=hash_password(body.password),
        profesion=body.profesion or "N/A",
    )
    db.add(user)
    db.commit()
    try:
        _firebase_send_verification_email(email=body.email, raw_password=body.password)
    except Exception as e:
        
# raise HTTPException(status_code=500, detail=f"Error enviando verificación: {e}")
        # o loguear y seguir:
        print(f"[WARN] Verificación por Firebase no enviada: {e}")

    # Esto hay que mejorarlo si lo queremos serio, es un login muy de juguete
    token = f"token-{user.email}"
    return {"id": user.user_id, "name": user.name, "email": user.email, "token": token}

@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_database)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.email_verified:
        try:
            fb_user = fb_auth.get_user_by_email(body.email)
        except fb_auth.UserNotFoundError:
            raise HTTPException(
                status_code=403,
                detail="Email not verified. Please confirm the verification link sent to your inbox.",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Unable to validate email verification status: {exc}",
            )

        if not fb_user.email_verified:
            raise HTTPException(
                status_code=403,
                detail="Email not verified. Please confirm the verification link sent to your inbox.",
            )

        try:
            user.email_verified = True
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=503,
                detail="Unable to update verification status. Please try again later.",
            )

    token = f"token-{user.email}"
    return {"id": user.user_id, "name": user.name, "email": user.email, "token": token}
