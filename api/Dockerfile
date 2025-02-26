# Use an official slim Python image as the base image
FROM python:3.9-slim

# Set environment variables to prevent Python from writing .pyc files and to buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if needed (e.g., gcc, libpq-dev for PostgreSQL connectivity)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Copy the entrypoint script into the image
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port 8000 to the host
EXPOSE 8000

# Set the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

# Command to run the application using Gunicorn with Uvicorn workers
# Adjust the number of workers as necessary for your environment
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--reload", "--timeout", "120"]
