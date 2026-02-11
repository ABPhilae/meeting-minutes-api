# ========================================
# Dockerfile for Meeting Minutes API
# ========================================

# BASE IMAGE: python:3.11-slim
# Why 'slim'? It's ~150MB vs ~900MB for the full image.
# It has everything we need (pip, core libs) without extras.
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# ---- DEPENDENCY LAYER (cached) ----
# Copy ONLY requirements.txt first.
# Docker caches each layer. If requirements.txt hasn't changed,
# Docker skips the pip install step entirely.
# This saves 30-60 seconds on every build where only code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- APPLICATION LAYER ----
# Now copy everything else.
# This layer is rebuilt whenever your code changes,
# but dependencies stay cached from the layer above.
COPY . .

# Document which port the app uses
EXPOSE 8000

# Start the application
# --host 0.0.0.0 makes it accessible from outside the container
# Without this, the server only listens on localhost INSIDE
# the container, which is unreachable from your machine.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
