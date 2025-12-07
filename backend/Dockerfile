# Use official Python image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy project root files (for noco_wink_inventory_sync module)
COPY noco_wink_inventory_sync ./noco_wink_inventory_sync

# Copy backend code
COPY backend/ .

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn requests python-dotenv rich

# Expose port
EXPOSE 5000

# Run FastAPI server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
