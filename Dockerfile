FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Fix apt-get update failures
RUN apt-get clean && rm -rf /var/lib/apt/lists/* \
    && apt-get update -o Acquire::CompressionTypes::Order::=gz \
    && apt-get install -y \
       build-essential \
       python3-dev \
       libatlas-base-dev \
       gcc \
       g++ \
       make \
       git \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
