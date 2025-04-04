# Use the official Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system packages
RUN apt-get update && apt-get install -y gcc curl && apt-get clean

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Expose port for Cloud Run (functions_framework runs on 8080 by default)
EXPOSE 8080

# Set environment variable for functions framework
ENV PORT 8080

# Start the Cloud Function using functions_framework
CMD ["functions-framework", "--target=main", "--port=8080"]