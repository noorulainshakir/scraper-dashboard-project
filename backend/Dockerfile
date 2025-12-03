# Use official Python image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy backend code
COPY . .

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn

# Expose port
EXPOSE 5000

# Run FastAPI server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
