FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --default-timeout=120 -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["python", "-m", "app.main"]
