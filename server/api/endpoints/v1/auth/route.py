# server/api/endpoints/v1/auth/route.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import os
import sqlite3
from dotenv import load_dotenv
import logging
import secrets
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
import uuid

load_dotenv()

router = APIRouter()

# but why did you pup these here? ENV FILE!! chill its fine for now
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

DB_PATH = "database/falcon_auth.db"

logging.basicConfig(filename='database/falcon_auth.log', level=logging.INFO)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        hashed_password TEXT NOT NULL,
        refresh_token TEXT,
        reset_token TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS nodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ip_address TEXT NOT NULL,
        port INTEGER NOT NULL,
        status TEXT NOT NULL,
        user_email TEXT,
        FOREIGN KEY (user_email) REFERENCES users(email)
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# we create this default user, but will chnage later on when i get the core features done
default_email = "admin@example.com"
default_password = "adminpassword"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
security = HTTPBearer()

class RateLimiter:
    def __init__(self, times: int, seconds: int):
        self.times = times
        self.seconds = seconds
        self.requests = {}

    async def __call__(self, request: Request):
        ip = request.client.host
        if ip in self.requests:
            if len(self.requests[ip]) >= self.times:
                if datetime.now() - self.requests[ip][0] < timedelta(seconds=self.seconds):
                    raise HTTPException(status_code=429, detail="Too many requests")
                self.requests[ip] = self.requests[ip][1:]
        else:
            self.requests[ip] = []
        self.requests[ip].append(datetime.now())

# creating our rate limiters lol
login_limiter = RateLimiter(times=5, seconds=60)
register_limiter = RateLimiter(times=3, seconds=60)

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class User(BaseModel):
    email: EmailStr

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(email: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(email=user[0])
    return None

def authenticate_user(email: str, password: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return False
    if not verify_password(password, user[1]):
        return False
    return User(email=user[0])

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(email: str):
    expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": email, "exp": expires}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = User(email=email)
    except JWTError:
        raise credentials_exception
    user = get_user(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

@router.post("/token", response_model=Token)
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    await login_limiter(request)
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(user.email)
    
    # we store the refresh token in the database for future use
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET refresh_token = ? WHERE email = ?", (refresh_token, user.email))
    conn.commit()
    conn.close()
    
    logging.info(f"User {user.email} logged in successfully")
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

@router.post("/refresh")
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    refresh_token = credentials.credentials
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=400, detail="Invalid refresh token")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT refresh_token FROM users WHERE email = ?", (email,))
        stored_refresh_token = cursor.fetchone()
        conn.close()
        
        if not stored_refresh_token or stored_refresh_token[0] != refresh_token:
            raise HTTPException(status_code=400, detail="Invalid refresh token")
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid refresh token")

@router.post("/register")
async def register(request: Request, email: EmailStr, password: str):
    await register_limiter(request)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(password)
    cursor.execute("INSERT INTO users (email, hashed_password) VALUES (?, ?)", (email, hashed_password))
    conn.commit()
    conn.close()
    logging.info(f"New user registered: {email}")
    return {"message": "User created successfully"}

@router.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

def create_default_user():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (default_email,))
    if not cursor.fetchone():
        hashed_password = get_password_hash(default_password)
        cursor.execute("INSERT INTO users (email, hashed_password) VALUES (?, ?)", (default_email, hashed_password))
        conn.commit()
        print(f"Default user created: {default_email}")
    conn.close()

create_default_user()

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

def generate_password_reset_token():
    return str(uuid.uuid4())

def store_password_reset_token(email: str, token: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET reset_token = ? WHERE email = ?", (token, email))
    conn.commit()
    conn.close()

def get_user_by_reset_token(token: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE reset_token = ?", (token,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(email=user[0])
    return None

def clear_reset_token(email: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET reset_token = NULL WHERE email = ?", (email,))
    conn.commit()
    conn.close()

@router.post("/password-reset-request")
async def request_password_reset(request: PasswordResetRequest, background_tasks: BackgroundTasks):
    user = get_user(request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    token = generate_password_reset_token()
    background_tasks.add_task(store_password_reset_token, request.email, token)
    
    # TODO: send these thur the client via reset password modal in settings.
    return {"message": "Password reset token generated", "token": token}

@router.post("/reset-password")
async def reset_password(reset: PasswordReset):
    user = get_user_by_reset_token(reset.token)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    hashed_password = get_password_hash(reset.new_password)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET hashed_password = ? WHERE email = ?", (hashed_password, user.email))
    conn.commit()
    conn.close()
    
    clear_reset_token(user.email)
    
    return {"message": "Password reset successful"}