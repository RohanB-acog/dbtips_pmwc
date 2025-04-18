from fastapi import FastAPI, Depends, HTTPException, status,Request
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from db.database import get_db, engine, Base
from db import models
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer


# OAuth2 scheme setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Secret and Algorithm
SECRET_KEY = "e3f3b0cdb413f37cb1b9e03f0b12b283e158a12993c9825e91b9b5a8a49072bb"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Helper to verify passwords
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Helper to authenticate users
def authenticate_user(db: Session, username: str, password: str):
    # Query the Admin table
    user = db.query(models.Admin).filter(models.Admin.username == username).first()
    if user and verify_password(password, user.password):
        return user
    return None

# JWT token generation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta if expires_delta else datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user_role(request: Request):
    token: Optional[str] = request.headers.get("Authorization")
    if token:
        try:
            # Remove the "Bearer " prefix from the token
            token = token.split(" ")[1]  # Assuming the format is "Bearer <token>"
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            role = payload.get("role")
            
            if role is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            return role
        except JWTError as e:
            if 'expired' in str(e):
                raise HTTPException(status_code=401, detail="Token has expired")
            else:
                raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    # If no token is provided, assume normal_user
    return "normal_user"