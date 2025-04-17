# Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.12-slim-bookworm

# Update package lists and upgrade installed packages to get security updates
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Install build dependencies for numpy, pandas, matplotlib, etc., required during pip install
# Also install pkg-config needed by some packages
# Clean up apt lists afterwards to keep the image smaller
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libatlas-base-dev \
    gfortran \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Using --no-cache-dir reduces layer size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
# This includes your app/, config/, static/, templates/, run.py, etc.
COPY . .

# Vercel automatically exposes the container and sets the PORT environment variable.
# WARNING: The base image may contain high vulnerabilities. Consider using a more secure or updated base image if security is critical.
# Gunicorn will bind to this port. We don't strictly need EXPOSE here for Vercel,
# but it's good practice for documenting the intended port.
EXPOSE 8000

# Define environment variable for the default port if not set externally
ENV PORT=8000

# Run the application using Gunicorn when the container launches
# Bind to 0.0.0.0 to be accessible from outside the container.
# Use the PORT environment variable set by Vercel (or the default 8000).
# Assuming your Flask app instance is named 'app' in 'run.py'.
# Added --workers 1 for debugging

# --- TEMPORARY DEBUGGING CMD (Commented out) ---
# CMD ["python", "-c", "import sys; print('--- Directly executing Python in CMD ---', flush=True); sys.stdout.flush()"]

# --- ORIGINAL CMD ---
# Run the application using Gunicorn when the container launches
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "run:app"]
