from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

@app.get("/")
async def root():
    return {"status": "ok", "service": "elevenlabs-mcp-server", "endpoints": ["/start-conversation", "/health"]}

@app.post("/")
async def root_post(request: dict):
    """Handle POST requests to root - redirect to start-conversation"""
    print(f"📨 Received POST to root: {json.dumps(request, indent=2)}")
    return await start_conversation(request)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/start-conversation")
async def start_conversation(request: dict):
    """Start a conversation with the configured agent"""
    print(f"🚀 start_conversation called with: {json.dumps(request, indent=2)}")
    
    agent_id = request.get("agent_id")
    api_key = request.get("api_key")
    
    print(f"🎯 Agent ID: {agent_id}")
    print(f"🔑 API Key from Base44: {'Yes' if api_key else 'No'}")
    
    if not agent_id:
        print("❌ No agent_id provided")
        raise HTTPException(status_code=400, detail="agent_id is required")
    
    if not api_key:
        print("❌ No api_key provided")
        raise HTTPException(status_code=400, detail="api_key is required")
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        print(f"📡 Calling ElevenLabs API for agent: {agent_id}")
        response = requests.post(
    f"{ELEVENLABS_BASE_URL}/convai/agents/{agent_id}/conversations",
    headers=headers,
    timeout=30
)
        
        print(f"📈 ElevenLabs API response status: {response.status_code}")
        print(f"📄 ElevenLabs API response text: {response.text}")
        
        if response.status_code != 200:
            error_msg = f"ElevenLabs API error: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=response.status_code, detail=error_msg)
        
        conversation_data = response.json()
        print(f"✅ Conversation data: {json.dumps(conversation_data, indent=2)}")
        
        result = {
            "conversation_id": conversation_data.get("conversation_id"),
            "websocket_url": f"wss://api.elevenlabs.io/v1/conversational-ai/conversations/{conversation_data.get('conversation_id')}",
            "status": "success",
            "agent_id": agent_id
        }
        
        print(f"✅ Returning result: {json.dumps(result, indent=2)}")
        return result
        
    except requests.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
