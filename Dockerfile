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

# Expose port (7860 for Hugging Face, 10000 for Render)
EXPOSE 7860
EXPOSE 10000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV OMP_NUM_THREADS=2
ENV TOKENIZERS_PARALLELISM=false

# Run the application (uses PORT env var if set, defaults to 7860 for HF)
CMD ["python", "main.py"]
