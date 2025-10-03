import os
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



# --- NUEVO: inicialización Firebase Admin (una sola vez) ---
# Requiere GOOGLE_APPLICATION_CREDENTIALS apuntando al JSON del Service Account
if not firebase_admin._apps:
    try:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
    except Exception as e:
        # Si querés, podés loguear el error; no rompemos el arranque
        pass

# --- NUEVO: helper para pedir a Firebase que ENVÍE el mail de verificación ---
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
        # No interrumpimos el flujo principal, pero informamos si querés
        raise RuntimeError(f"No se pudo crear/sincronizar usuario en Firebase: {e}")

    # 2) Obtener ID token vía REST (signInWithPassword) para poder llamar sendOobCode
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

# ----------------- Tu código original -----------------
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

    # --- NUEVO: pedir a Firebase que envíe el mail de verificación ---
    try:
        _firebase_send_verification_email(email=body.email, raw_password=body.password)
    except Exception as e:
        
# raise HTTPException(status_code=500, detail=f"Error enviando verificación: {e}")
        # o loguear y seguir:
        print(f"[WARN] Verificación por Firebase no enviada: {e}")

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

