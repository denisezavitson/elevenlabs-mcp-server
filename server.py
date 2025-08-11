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
async def root_post_simple():
    return {"status": "mcp-ready", "protocol": "ready"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# FULL MCP PROTOCOL IMPLEMENTATION
@app.post("/mcp/initialize")
async def mcp_initialize():
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {},
            "resources": {}
        },
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
                "description": "Start a conversation with an ElevenLabs agent",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "The ElevenLabs agent ID"
                        }
                    },
                    "required": ["agent_id"]
                }
            }
        ]
    }

@app.post("/mcp/tools/call")
async def call_tool(request: dict):
    tool_name = request.get("name")
    arguments = request.get("arguments", {})
    
    if tool_name == "start_conversation":
        agent_id = arguments.get("agent_id")
        
        if not agent_id:
            raise HTTPException(status_code=400, detail="agent_id is required")
        
        # Use the API key from environment (since ElevenLabs will handle auth)
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not configured")
        
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{ELEVENLABS_BASE_URL}/convai/agents/{agent_id}/conversations",
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = f"ElevenLabs API error: {response.status_code} - {response.text}"
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: {error_msg}"
                        }
                    ],
                    "isError": True
                }
            
            conversation_data = response.json()
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "conversation_id": conversation_data.get("conversation_id"),
                            "websocket_url": f"wss://api.elevenlabs.io/v1/convai/conversations/{conversation_data.get('conversation_id')}",
                            "status": "success",
                            "agent_id": agent_id
                        })
                    }
                ]
            }
            
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text", 
                        "text": f"Error: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

# Keep your existing endpoints for Base44 direct calls
@app.post("/start-conversation")
async def start_conversation(request: dict):
    agent_id = request.get("agent_id")
    api_key = request.get("api_key")
    
    if not agent_id or not api_key:
        raise HTTPException(status_code=400, detail="agent_id and api_key required")
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{ELEVENLABS_BASE_URL}/convai/agents/{agent_id}/conversations",
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"ElevenLabs API error: {response.text}")
        
        conversation_data = response.json()
        
        return {
            "conversation_id": conversation_data.get("conversation_id"),
            "websocket_url": f"wss://api.elevenlabs.io/v1/convai/conversations/{conversation_data.get('conversation_id')}",
            "status": "success",
            "agent_id": agent_id
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
