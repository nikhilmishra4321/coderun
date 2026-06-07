FROM python:3.11

WORKDIR /app

COPY worker.py .
RUN pip install redis

ENV PYTHONUNBUFFERED=1

CMD ["python", "worker.py"]