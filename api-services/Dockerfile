FROM python:3.11

# Set working directory inside container
WORKDIR /app

# Copy your code into the container
COPY main.py .

# Install FastAPI and uvicorn
RUN pip install fastapi uvicorn redis pyjwt

# Command to run when container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


