# Use the official Python base image for version 3.11
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files to disk
# and to buffer output (useful for Docker logs)
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install system dependencies that might be required by yt-dlp and other libraries
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*  # Clean up to reduce image size

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose the port that Django will run on
EXPOSE 8000

# Set the default command to run the Django development server (use gunicorn in production)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]