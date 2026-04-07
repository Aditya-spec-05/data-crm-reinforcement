# 1. Use a stable Python base image
FROM python:3.10-slim

# 2. Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 3. Set the working directory
WORKDIR /app

# 4. Install system dependencies
# Added libpq-dev for PostgreSQL (psycopg2) compatibility
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    libpq-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy requirements and install Python libraries
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copy the entire project into the container
COPY . .

# 7. Set permissions (CRITICAL for Hugging Face Spaces)
# We give full permissions so the app can create 'crm.db' at runtime
RUN chmod -R 777 /app

# 8. Expose the mandatory Hugging Face port
EXPOSE 7860

# 9. Start the FastAPI server
# Using 'python main.py' is fine as long as main.py calls uvicorn.run
CMD ["python", "main.py"]