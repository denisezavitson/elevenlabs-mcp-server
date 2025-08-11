from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

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
    return {"status": "ok", "service": "elevenlabs-mcp-server", "endpoints": ["/start-conversation", "/health"]}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/start-conversation")
async def start_conversation(request: dict):
    """Start a conversation with the configured agent"""
    agent_id = request.get("agent_id")
    
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")
    
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not configured")
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Starting conversation for agent: {agent_id}")
        response = requests.post(
            f"{ELEVENLABS_BASE_URL}/conversational-ai/agents/{agent_id}/conversations",
            headers=headers
        )
        
        print(f"ElevenLabs API response status: {response.status_code}")
        print(f"ElevenLabs API response: {response.text}")
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"ElevenLabs API error: {response.text}")
        
        conversation_data = response.json()
        
        return {
            "conversation_id": conversation_data.get("conversation_id"),
            "websocket_url": f"wss://api.elevenlabs.io/v1/conversational-ai/conversations/{conversation_data.get('conversation_id')}",
            "status": "success",
            "agent_id": agent_id
        }
        
    except requests.RequestException as e:
        print(f"Request error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
