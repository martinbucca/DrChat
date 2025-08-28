FROM python:3.13.2-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed for HuggingFace or Neo4j)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy files
COPY requirements.txt .
COPY .env /app/.env
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose FastAPI port
EXPOSE 5001

# Start the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5001"]
