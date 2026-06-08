# CodeRun

A distributed code execution engine built with microservices. Submit code, run it safely in an isolated environment, get results instantly, and compete on a global leaderboard.

> Designed to scale — add languages, workers, or services independently without touching existing code.

---

## Architecture


                        ┌──────────────┐
                        │   Frontend   │
                        │  nginx:3000  │
                        └──────┬───────┘
                               │
                    ┌──────────▼──────────┐
                    │     API Service     │
                    │   FastAPI · 8000    │
                    │  JWT · Validation   │
                    └──────────┬──────────┘
                               │ push job
                               ▼
                    ┌──────────────────────┐
                    │        Redis         │
                    │   Job Queue · 6379   │
                    └──────┬───────────────┘
                           │ pop job
              ┌────────────▼────────────┐
              │      Worker Service     │
              │  Execute · Time · Stats │
              └────┬──────────┬─────────┘
                   │          │
         set result│          │ POST /update
                   ▼          ▼
              ┌────────┐  ┌────────────────────┐
              │ Redis  │  │ Leaderboard Service │
              │Results │  │  FastAPI · 8003     │
              └───┬────┘  │  PostgreSQL         │
                  │        └────────────────────┘
         GET result│
              ┌───▼────────────┐     ┌──────────────────┐
              │ Result Service │     │   Auth Service   │
              │ FastAPI · 8001 │     │  FastAPI · 8002  │
              └────────────────┘     │  JWT · bcrypt    │
                                     └──────────────────┘


---

## Services

| Service | Port | Tech | Responsibility |
|---|---|---|---|
| Frontend | 3000 | nginx + HTML | Editor UI, leaderboard, auth |
| API Service | 8000 | FastAPI | Accept submissions, validate JWT, queue jobs |
| Worker Service | — | Python | Execute code, enforce limits, update stats |
| Result Service | 8001 | FastAPI | Serve results by job ID |
| Auth Service | 8002 | FastAPI + bcrypt | Register, login, issue JWT tokens |
| Leaderboard | 8003 | FastAPI + PostgreSQL | Track and rank users |
| Redis | 6379 | Redis 7 | Job queue + result store |
| PostgreSQL | 5432 | Postgres 15 | Users, stats, leaderboard data |

---

## Tech Stack


Backend       Python 3.11 · FastAPI · Pydantic · Uvicorn
Queue         Redis (brpop/lpush producer-consumer pattern)
Database      PostgreSQL · psycopg2
Auth          JWT (PyJWT) · bcrypt · HTTPBearer
Containers    Docker · Docker Compose
Frontend      HTML · CSS · Vanilla JS · nginx


---

## Features

- *Async job queue* — submissions pushed to Redis, worker processes independently
- *Execution sandboxing* — code runs in isolated subprocess with 5s timeout
- *Code validation* — dangerous patterns blocked before execution reaches the worker
- *JWT authentication* — all submissions require a valid token
- *Real-time results* — poll /result/{job_id} for output, errors, execution time
- *Global leaderboard* — ranked by successful jobs and average execution time
- *Error handling* — syntax errors, runtime errors, TLE all return clean responses
- *Persistent data* — leaderboard and users survive container restarts via Docker volumes

---

## Getting Started

### Requirements

- Docker Desktop
- Git

### Run

bash
git clone https://github.com/yourusername/coderun.git
cd coderun
docker compose up --build


Open http://localhost:3000 — register, write code, run it.

### API Endpoints

| Method | URL | Auth | Description |
|---|---|---|---|
| POST | /submit | JWT | Submit code for execution |
| GET | /result/{job_id} | — | Get execution result |
| POST | /register | — | Create account |
| POST | /login | — | Get JWT token |
| GET | /leaderboard | — | Get global rankings |

---

## Multi-Language Support

Currently supports *Python 3.11*. The architecture is designed to support additional languages with no changes to existing services.

To add a new language:

*1. Add the language to the worker's supported list:*
python
SUPPORTED_LANGUAGES = ["python", "javascript", "go"]


*2. Add execution logic per language:*
python
if language == "python":
    cmd = ["python", temp_path]
elif language == "javascript":
    cmd = ["node", temp_path]
elif language == "go":
    cmd = ["go", "run", temp_path]


*3. Install the runtime in the worker Dockerfile:*
dockerfile
FROM python:3.11
RUN apt-get update && apt-get install -y nodejs golang


*4. Update the API validation:*
python
SUPPORTED_LANGUAGES = ["python", "javascript", "go"]


No other services need to change. The queue, result store, auth, and leaderboard are all language-agnostic.

---

## Scaling

*Scale workers horizontally* — zero code changes required:

bash
docker compose up --scale worker-service=5


Five workers now process jobs in parallel from the same Redis queue.

*In production* — replace Redis queue with Kafka or AWS SQS for persistence and guaranteed delivery. Replace subprocess sandboxing with Docker-in-Docker on a Linux host for full isolation.

---

## Project Structure


coderun/
├── api-services/
│   ├── main.py           # JWT validation, code validation, job queuing
│   └── Dockerfile
├── worker-service/
│   ├── worker.py         # Queue consumer, execution, timing, leaderboard update
│   └── Dockerfile
├── result-service/
│   ├── main.py           # Result retrieval by job ID
│   └── Dockerfile
├── auth-service/
│   ├── main.py           # Register, login, token verify, DB init
│   └── Dockerfile
├── leaderboard-service/
│   ├── main.py           # Stats update, rankings query
│   └── Dockerfile
├── frontend/
│   ├── index.html        # Single-page UI
│   └── Dockerfile
├── docker-compose.yml
└── README.md


---

## Skills Demonstrated

| Skill | Where |
|---|---|
| Microservices architecture | 6 independent services, each with single responsibility |
| Docker & Docker Compose | All services containerized, orchestrated with one command |
| Async queue pattern | Redis lpush/brpop producer-consumer between API and Worker |
| REST API design | FastAPI with Pydantic validation, proper HTTP status codes |
| Authentication | JWT tokens, bcrypt hashing, HTTPBearer middleware |
| Database design | PostgreSQL with relational schema (users → stats) |
| Error handling | Try/except across all services, clean HTTP error responses |
| Service resilience | Retry loops for Redis and PostgreSQL on startup |
| Security | Code validation, execution timeout, JWT-protected endpoints |
| Horizontal scaling | Stateless worker — scale with --scale flag |

---

## Known Limitations

| Limitation | Production Solution |
|---|---|
| Redis queue is in-memory | Replace with Kafka or AWS SQS |
| Subprocess sandboxing | Docker-in-Docker on Linux host |
| Single language (Python) | Add runtimes to worker Dockerfile |
| No rate limiting | Add per-user request throttling in API service |

---

## License

MIT