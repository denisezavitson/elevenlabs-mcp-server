import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
import aiohttp
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Base44 ElevenLabs MCP Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

class MCPServer:
    def __init__(self):
        self.server_info = {
            "name": "Base44 ElevenLabs MCP Server",
            "version": "1.0.0"
        }
        self.capabilities = {
            "tools": {},
            "resources": {}
        }
        
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP JSON-RPC requests"""
        try:
            method = request_data.get("method")
            params = request_data.get("params", {})
            request_id = request_data.get("id")
            
            logger.info(f"Handling MCP request: {method}")
            
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": self.capabilities,
                        "serverInfo": self.server_info
                    }
                }
            
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
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
                            },
                            {
                                "name": "list_agents",
                                "description": "List available ElevenLabs agents",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {},
                                    "required": []
                                }
                            }
                        ]
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name == "start_conversation":
                    result = await self.start_conversation(arguments.get("agent_id"))
                elif tool_name == "list_agents":
                    result = await self.list_agents()
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Tool not found: {tool_name}"
                        }
                    }
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            
            elif method == "notifications/initialized":
                # This is a notification, no response needed
                return None
                
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def start_conversation(self, agent_id: str) -> Dict[str, Any]:
        """Start a conversation with an ElevenLabs agent"""
        if not agent_id:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: agent_id is required"
                    }
                ],
                "isError": True
            }
        
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: ELEVENLABS_API_KEY not configured"
                    }
                ],
                "isError": True
            }
        
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ELEVENLABS_BASE_URL}/convai/agents/{agent_id}/conversations",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"ElevenLabs API error: {response.status} - {error_text}"
                                }
                            ],
                            "isError": True
                        }
                    
                    conversation_data = await response.json()
                    
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps({
                                    "conversation_id": conversation_data.get("conversation_id"),
                                    "websocket_url": f"wss://api.elevenlabs.io/v1/convai/conversations/{conversation_data.get('conversation_id')}",
                                    "status": "success",
                                    "agent_id": agent_id
                                }, indent=2)
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
    
    async def list_agents(self) -> Dict[str, Any]:
        """List available ElevenLabs agents"""
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: ELEVENLABS_API_KEY not configured"
                    }
                ],
                "isError": True
            }
        
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{ELEVENLABS_BASE_URL}/convai/agents",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"ElevenLabs API error: {response.status} - {error_text}"
                                }
                            ],
                            "isError": True
                        }
                    
                    agents_data = await response.json()
                    
                    return {
                        "content": [
                            {
                                "type": "text", 
                                "text": json.dumps(agents_data, indent=2)
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

# Initialize MCP server
mcp_server = MCPServer()

@app.get("/")
async def root():
    return {
        "status": "ok", 
        "service": "Base44 ElevenLabs MCP Server",
        "protocol": "MCP 2024-11-05",
        "transport": "HTTP"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

@app.post("/")
async def mcp_endpoint(request: Request):
    """Main MCP endpoint that handles JSON-RPC requests"""
    try:
        request_data = await request.json()
        logger.info(f"Received MCP request: {request_data}")
        
        # Handle single request
        if isinstance(request_data, dict):
            response_data = await mcp_server.handle_request(request_data)
            if response_data is None:
                # Notification, no response needed
                return Response(status_code=204)
            return response_data
        
        # Handle batch requests
        elif isinstance(request_data, list):
            responses = []
            for req in request_data:
                resp = await mcp_server.handle_request(req)
                if resp is not None:
                    responses.append(resp)
            return responses
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request"
                }
            }
            
    except json.JSONDecodeError:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": "Parse error"
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

# Keep your original endpoint for backwards compatibility
@app.post("/start-conversation")
async def start_conversation_legacy(request: dict):
    """Legacy endpoint for direct API calls"""
    agent_id = request.get("agent_id")
    api_key = request.get("api_key")
    
    if not agent_id or not api_key:
        return {"error": "agent_id and api_key required"}, 400
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{ELEVENLABS_BASE_URL}/convai/agents/{agent_id}/conversations",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    return {"error": f"ElevenLabs API error: {response.status} - {error_text}"}, response.status
                
                conversation_data = await response.json()
                
                return {
                    "conversation_id": conversation_data.get("conversation_id"),
                    "websocket_url": f"wss://api.elevenlabs.io/v1/convai/conversations/{conversation_data.get('conversation_id')}",
                    "status": "success",
                    "agent_id": agent_id
                }
                
    except Exception as e:
        return {"error": f"Request error: {str(e)}"}, 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
