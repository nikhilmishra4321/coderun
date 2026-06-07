from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis
import json
import uuid
import jwt
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "coderun-secret-key"
security = HTTPBearer()

DANGEROUS_PATTERNS = [
    "import os",
    "import sys",
    "import subprocess",
    "import socket",
    "open(",
    "_import_",
    "eval(",
    "exec(",
]

class JobRequest(BaseModel):
    code: str
    language: str = "python"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

def validate_code(code: str):
    for pattern in DANGEROUS_PATTERNS:
        if pattern in code:
            raise HTTPException(
                status_code=400,
                detail=f"Dangerous code detected: '{pattern}' is not allowed"
            )

SUPPORTED_LANGUAGES = ["python"]

@app.get("/")
def root():
    return {"message": "API Service is running"}

@app.post("/submit")
def submit_job(job: JobRequest, user=Depends(verify_token)):
    if not job.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    if job.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Language '{job.language}' not supported. Supported: {SUPPORTED_LANGUAGES}"
        )

    validate_code(job.code)

    try:
        r = redis.Redis(host="redis", port=6379)
        job_id = str(uuid.uuid4())
        job_data = {
            "job_id": job_id,
            "code": job.code,
            "language": job.language,
            "user_id": user["user_id"],
            "username": user["username"]
        }
        r.lpush("jobs", json.dumps(job_data))
        return {"job_id": job_id, "status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Queue unavailable, try again later")