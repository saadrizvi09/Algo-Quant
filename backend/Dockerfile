# Use python 3.11 slim image
FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for scientific packages (numpy, hmmlearn, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Hugging Face Spaces specific port
EXPOSE 7860

# Run uvicorn on port 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]