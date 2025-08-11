# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv package manager
RUN pip install uv

# Install ElevenLabs MCP server
RUN uv pip install --system elevenlabs-mcp

# Expose port
EXPOSE 8080

# Start the MCP server
CMD ["python", "-m", "elevenlabs_mcp"]
