FROM python:3.11

WORKDIR /app

COPY main.py .
RUN pip install fastapi uvicorn psycopg2-binary bcrypt pyjwt
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]