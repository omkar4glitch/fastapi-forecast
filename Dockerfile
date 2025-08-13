FROM python:3.11-bullseye

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for Prophet + cmdstan
RUN apt-get update && apt-get install -y \
    build-essential \
    libatlas-base-dev \
    gcc \
    g++ \
    make \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Run API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
