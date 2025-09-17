FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY app/ .

# Command to run the Kafka consumer
CMD ["python", "main.py"]
