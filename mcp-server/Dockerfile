FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /usr/src/app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Copy the source code
COPY . .

# Install the package in development mode
RUN pip install -e .

# Create log directory
RUN mkdir -p /var/log

# Create directory for files
RUN mkdir -p /usr/src/app/local_files

# Set environment variables
ENV PYTHONPATH=/usr/src/app
ENV PYTHONUNBUFFERED=1

# Run the MCP server
CMD ["python", "-m", "minima.server"]
