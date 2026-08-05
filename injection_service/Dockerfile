FROM python:3.11-slim

WORKDIR /app

COPY injection_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app/core ./app/core
COPY backend/app/retrieval ./app/retrieval
COPY injection_service/app/__init__.py ./app/__init__.py
COPY injection_service/app/main.py ./app/main.py

EXPOSE 8100

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
