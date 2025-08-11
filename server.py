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
    return {"status": "ok", "service": "elevenlabs-mcp-server"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# NEW: Direct conversation endpoints for Base44
@app.post("/start-conversation")
async def start_conversation(request: dict):
    """Start a conversation with the configured agent"""
    agent_id = request.get("agent_id")
    
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{ELEVENLABS_BASE_URL}/conversational-ai/agents/{agent_id}/conversations",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        conversation_data = response.json()
        
        # Return the conversation data including WebSocket URL
        return {
            "conversation_id": conversation_data.get("conversation_id"),
            "websocket_url": f"wss://api.elevenlabs.io/v1/conversational-ai/conversations/{conversation_data.get('conversation_id')}",
            "status": "success",
            "agent_id": agent_id
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")

@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation details"""
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{ELEVENLABS_BASE_URL}/conversational-ai/conversations/{conversation_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")

# Keep existing MCP protocol endpoints for ElevenLabs integration
@app.post("/mcp/initialize")
async def mcp_initialize():
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}},
        "serverInfo": {
            "name": "Base44 ElevenLabs MCP Server",
            "version": "1.0.0"
        }
    }

@app.post("/mcp/tools/list")
async def list_tools():
    return {
        "tools": [
            {
                "name": "start_conversation",
                "description": "Start a conversation with an agent",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"}
                    }
                }
            }
        ]
    }

@app.post("/mcp/tools/call")
async def call_tool(request: dict):
    tool_name = request.get("name")
    arguments = request.get("arguments", {})
    
    if tool_name == "start_conversation":
        return await start_
