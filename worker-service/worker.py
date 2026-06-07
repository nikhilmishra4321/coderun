import redis
import json
import subprocess
import time
import tempfile
import os
import urllib.request

print("Worker started, waiting for jobs...")

while True:
    try:
        r = redis.Redis(host="redis", port=6379)
        r.ping()
        print("Connected to Redis successfully!")
        break
    except Exception as e:
        print(f"Redis not ready yet, retrying... {e}")
        time.sleep(2)

def update_leaderboard(user_id, status, execution_time):
    try:
        data = json.dumps({
            "user_id": user_id,
            "status": status,
            "execution_time": execution_time
        }).encode()
        req = urllib.request.Request(
            "http://leaderboard-service:8003/update",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception as e:
        print(f"Leaderboard update failed: {e}")

while True:
    try:
        r = redis.Redis(host="redis", port=6379)
        job_data = r.brpop("jobs", timeout=5)

        if job_data is None:
            continue

        job = json.loads(job_data[1])
        job_id = job["job_id"]
        code = job["code"]
        language = job.get("language", "python")
        user_id = job.get("user_id", None)

        print(f"Picked up job: {job_id}")

        supported = ["python"]
        if language not in supported:
            result_data = {
                "job_id": job_id,
                "status": "error",
                "output": "",
                "error": f"Language '{language}' not supported.",
                "execution_time": 0,
                "user_id": user_id
            }
            r.set(f"result:{job_id}", json.dumps(result_data))
            continue

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as f:
                f.write(code)
                temp_path = f.name

            try:
                start_time = time.time()
                result = subprocess.run(
                    ["python", temp_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                execution_time = round(time.time() - start_time, 3)
                output = result.stdout
                error = result.stderr
                status = "success" if result.returncode == 0 else "error"

            except subprocess.TimeoutExpired:
                execution_time = 5.0
                output = ""
                error = "Time limit exceeded (5s)"
                status = "timeout"

            finally:
                os.unlink(temp_path)

        except Exception as e:
            execution_time = 0
            output = ""
            error = f"Execution failed: {str(e)}"
            status = "error"

        result_data = {
            "job_id": job_id,
            "status": status,
            "output": output,
            "error": error,
            "execution_time": execution_time,
            "user_id": user_id
        }
        r.set(f"result:{job_id}", json.dumps(result_data))
        print(f"Job {job_id} done — status: {status} — time: {execution_time}s")

        if user_id:
            update_leaderboard(user_id, status, execution_time)

    except Exception as e:
        print(f"Connection error: {e}, retrying in 2 seconds...")
        time.sleep(2)