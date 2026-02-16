# Airbnb MCP Server - Python FastMCP for Railway
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY server.py .

# Expose port for HTTP server
EXPOSE 8080

# Set environment variable for PORT (Railway will override this)
ENV PORT=8080

# Run the server
CMD ["python", "server.py"]
