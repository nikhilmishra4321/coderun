from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import redis
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/result/{job_id}")
def get_result(job_id: str):
    try:
        r = redis.Redis(host="redis", port=6379)
        data = r.get(f"result:{job_id}")

        if data is None:
            raise HTTPException(
                status_code=404,
                detail="Result not found. Job may still be processing."
            )

        return json.loads(data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="Result service unavailable, try again later"
        )