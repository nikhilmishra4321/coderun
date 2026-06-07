from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return psycopg2.connect(
        host="postgres",
        database="coderun",
        user="coderun",
        password="coderun123"
    )

class StatsUpdate(BaseModel):
    user_id: int
    status: str
    execution_time: float

@app.post("/update")
def update_stats(data: StatsUpdate):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE user_stats SET
                total_jobs = total_jobs + 1,
                successful_jobs = successful_jobs + CASE WHEN %s = 'success' THEN 1 ELSE 0 END,
                total_execution_time = total_execution_time + %s
            WHERE user_id = %s
        """, (data.status, data.execution_time, data.user_id))
        conn.commit()
        cur.close()
        conn.close()
        return {"message": "Stats updated"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Leaderboard service unavailable")

@app.get("/leaderboard")
def get_leaderboard():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT u.username, s.total_jobs, s.successful_jobs,
                   CASE WHEN s.successful_jobs > 0
                   THEN ROUND(CAST(s.total_execution_time / s.successful_jobs AS numeric), 3)
                   ELSE 0 END as avg_execution_time
            FROM users u
            JOIN user_stats s ON u.id = s.user_id
            WHERE s.total_jobs > 0
            ORDER BY s.successful_jobs DESC, avg_execution_time ASC
            LIMIT 20
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [
            {
                "rank": i + 1,
                "username": row[0],
                "total_jobs": row[1],
                "successful_jobs": row[2],
                "avg_execution_time": float(row[3])
            }
            for i, row in enumerate(rows)
        ]
    except Exception as e:
        raise HTTPException(status_code=503, detail="Leaderboard service unavailable")