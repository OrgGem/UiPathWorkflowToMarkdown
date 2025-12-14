# ============================================
# Stage 1: Build the Vue.js Frontend
# ============================================
FROM node:20-alpine AS ui-builder

WORKDIR /ui

# Copy package files and install dependencies
COPY ui/package*.json ./
RUN npm ci

# Copy UI source code and build
COPY ui/ ./
RUN npm run build

# ============================================
# Stage 2: Python Backend + Built UI
# ============================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY app ./app

# Copy built UI from the builder stage
COPY --from=ui-builder /ui/dist ./ui/dist

# Copy additional files
COPY README.md ./

EXPOSE 8000

# Start the FastAPI server (which now serves both API and UI)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
