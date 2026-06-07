from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import psycopg2
import bcrypt
import jwt
import datetime
import os
from pydantic import BaseModel
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "coderun-secret-key"
security = HTTPBearer()

def get_db():
    return psycopg2.connect(
        host="postgres",
        database="coderun",
        user="coderun",
        password="coderun123"
    )

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER REFERENCES users(id),
            total_jobs INTEGER DEFAULT 0,
            successful_jobs INTEGER DEFAULT 0,
            total_execution_time FLOAT DEFAULT 0,
            PRIMARY KEY (user_id)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

while True:
    try:
        init_db()
        print("Database initialized successfully!")
        break
    except Exception as e:
        print(f"Database not ready yet, retrying... {e}")
        time.sleep(3)

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/register")
def register(req: RegisterRequest):
    if not req.username.strip() or not req.password.strip():
        raise HTTPException(status_code=400, detail="Username and password required")
    try:
        conn = get_db()
        cur = conn.cursor()
        password_hash = bcrypt.hashpw(
            req.password.encode(), bcrypt.gensalt()
        ).decode()
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
            (req.username, password_hash)
        )
        user_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO user_stats (user_id) VALUES (%s)",
            (user_id,)
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"message": f"User {req.username} registered successfully"}
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

@app.post("/login")
def login(req: LoginRequest):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, password_hash FROM users WHERE username = %s",
            (req.username,)
        )
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not bcrypt.checkpw(req.password.encode(), user[1].encode()):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = jwt.encode({
            "user_id": user[0],
            "username": req.username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")

        return {"token": token, "username": req.username}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail="Auth service unavailable")

@app.get("/verify")
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=["HS256"]
        )
        return {"user_id": payload["user_id"], "username": payload["username"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")