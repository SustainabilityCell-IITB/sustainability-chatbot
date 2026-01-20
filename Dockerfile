FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create cache directory
RUN mkdir -p cache

# Expose port
EXPOSE 10000

# Set environment variables for memory optimization
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:32
ENV OMP_NUM_THREADS=1
ENV TOKENIZERS_PARALLELISM=false

# Run the application
CMD ["python", "main.py"]
