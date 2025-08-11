FROM python:3.11-slim

WORKDIR /app

# Install required packages
RUN pip install fastapi uvicorn requests

# Copy our custom server
COPY server.py .

# Expose port
EXPOSE 8080

# Start our custom server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
