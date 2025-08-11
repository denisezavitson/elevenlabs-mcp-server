from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

# Enable CORS for Base44 to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

@app.get("/")
async def root():
    return {"status": "ElevenLabs MCP Server Running", "service": "Base44 Integration"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "elevenlabs-mcp-server"}

@app.post("/agents")
async def create_agent(agent_config: dict):
    """Create a conversational AI agent"""
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{ELEVENLABS_BASE_URL}/conversational-ai/agents",
        headers=headers,
        json=agent_config
    )
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response.json()

@app.post("/agents/{agent_id}/conversations")
async def start_conversation(agent_id: str):
    """Start a conversation with an agent"""
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{ELEVENLABS_BASE_URL}/conversational-ai/agents/{agent_id}/conversations",
        headers=headers
    )
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
