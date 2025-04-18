# Use a slim version of Python 3.12
FROM python:3.12.3-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only the requirements file to optimize cache usage
COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install dependencies using the requirements.txt file
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into the container
COPY . .

# Copy static folder to the container
COPY static /app/static

ENV PYTHONUNBUFFERED=1

# Expose port 8000 to communicate with the FastAPI app
EXPOSE 8000

# Run the FastAPI server using Uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
