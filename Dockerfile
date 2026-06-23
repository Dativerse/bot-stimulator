FROM python:3.11-slim

# Prevent Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install system dependencies if any are needed (e.g., cron)
# RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set the default command to show help, users can override it to run `sync`, `fetch`, or `upload`
ENTRYPOINT ["python3", "main.py"]
CMD ["--help"]
