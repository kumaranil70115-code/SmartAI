# Smart AI - 24/7 Permanent Cloud Server Container
FROM python:3.12-slim

# Prevent python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SMARTAI_CLOUD_MODE=1
ENV PORT=8765

# Set work directory
WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Ensure permissions and uploads directory exists
RUN mkdir -p uploads web/.well-known

# Expose port (Render/Railway injects PORT dynamically)
EXPOSE 8765

# Healthcheck to verify 24/7 continuous uptime
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8765}/api/health || exit 1

# Start Smart AI 24/7 server
CMD ["python", "app.py"]
