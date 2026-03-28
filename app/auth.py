import os
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Header, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-for-dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def get_password_hash(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key:
        return None
    hashed = os.getenv("API_KEY_HASH")
    if not hashed or not bcrypt.checkpw(x_api_key.encode(), hashed.encode()):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return True

def get_current_user(token: str = Depends(oauth2_scheme), x_api_key: str = Header(None), db: Session = Depends(get_db)):
    # 1. Intentar con API Key (para pipelines)
    if x_api_key:
        if verify_api_key(x_api_key):
            return "api_user"
    
    # 2. Intentar con JWT (para la UI)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
