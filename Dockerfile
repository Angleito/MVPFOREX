# Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py \
    FLASK_ENV=production

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . /app/

# Create non-root user
RUN useradd -m mvpforex && \
    chown -R mvpforex:mvpforex /app
USER mvpforex

# Create necessary directories
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Run the application using Gunicorn when the container launches
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--access-logfile", "-", "--error-logfile", "-", "run:app"]
