FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY src src
COPY .env .env

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8015", "--reload"]
