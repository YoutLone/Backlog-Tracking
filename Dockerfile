FROM python:3.11-slim

# System packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libargon2-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# App directory
WORKDIR /app

# Install dependencies before copying app code.
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

EXPOSE 8000

# Development server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
