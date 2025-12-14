# Minimal production image for UiPath Workflow to Markdown
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps (none required currently) and Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY frontend ./frontend
COPY README.md ./

EXPOSE 8000

# Default command to serve the API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
