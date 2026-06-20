FROM python:3.12-slim

WORKDIR /app

# Copy dependency file and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY . .

# Ensure data files are writable
RUN mkdir -p /app/data && \
    chmod 777 /app/data

# Use the retry wrapper (handles 429 rate-limits gracefully)
CMD ["bash", "entrypoint.sh"]
