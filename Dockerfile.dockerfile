# 1. Use a stable Python base image
FROM python:3.10-slim

# 2. Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

# 3. Set the working directory
WORKDIR /app

# 4. Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    libpq-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. Install 'uv' for fast, reliable dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 6. Copy dependency files first (for better caching)
COPY pyproject.toml uv.lock* requirements.txt ./

# 7. Install dependencies 
# This handles both your standard requirements and the new pyproject structure
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    uv pip install --system -e .

# 8. Copy the entire project
COPY . .

# 9. Set permissions (CRITICAL for Hugging Face Spaces)
RUN chmod -R 777 /app

# 10. Expose the mandatory Hugging Face port
EXPOSE 7860

# 11. Start the FastAPI server using the module path
# We use 'python -m server.app' because it's now a package
CMD ["python", "-m", "server.app"]