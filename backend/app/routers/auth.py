"""
Authentication router - simplified version for testing
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
import hashlib
from typing import Optional
from pydantic import BaseModel

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str

def simple_hash(password: str) -> str:
    """Simple hash for testing (not for production)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return simple_hash(plain_password) == hashed_password

def get_user_by_username(db: Session, username: str):
    result = db.execute(
        text("SELECT * FROM users WHERE username = :username"), 
        {"username": username}
    ).fetchone()
    return result

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str) -> str:
    # Simple token for testing (not secure for production)
    return f"test_token_{username}"

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    # Extract username from simple token
    if token.startswith("test_token_"):
        username = token.replace("test_token_", "")
        user = get_user_by_username(db, username)
        if user:
            return UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=bool(user.is_active)
            )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )