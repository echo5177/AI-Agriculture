FROM python:3.9-slim

# Install system dependencies required for OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose port 7860 (default port for Hugging Face Spaces)
EXPOSE 7860

# Run the FastAPI app using uvicorn on port 7860
CMD ["uvicorn", "ai_engine.main:app", "--host", "0.0.0.0", "--port", "7860"]
