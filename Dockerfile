# Use Python 3.11 as the runtime environment for the backend.
FROM python:3.11-slim

# Set the working directory inside the container.
WORKDIR /app

# Copy dependency definitions first to leverage Docker layer caching.
COPY backend/requirements.txt ./requirements.txt

# Install Python dependencies.
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the backend source code into the container.
COPY backend ./backend

# Expose the FastAPI port.
EXPOSE 8000

# Start the FastAPI application with Uvicorn.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
