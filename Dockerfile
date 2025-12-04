FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create outputs directory
RUN mkdir -p outputs

# Default command
CMD ["python", "src/engine/greedy_scheduler.py", "--inputs", "inputs/", "--output", "outputs/", "--config", "config.yaml"]
