from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main import MCP
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP API", description="API for Model Context Protocol with LangChain")
mcp = MCP()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production to specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserInput(BaseModel):
    text: str

class ContextOperation(BaseModel):
    filename: str = "context.json"

@app.get("/")
async def root():
    """Root endpoint to check if the API is running."""
    return {"message": "MCP API is running", "status": "online"}

@app.post("/interact")
async def interact(user_input: UserInput):
    """Process user input and return AI response."""
    try:
        if not user_input.text.strip():
            raise HTTPException(status_code=400, detail="Empty input. Please provide a valid query.")
        
        response = mcp.interact(user_input.text)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in /interact endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools")
async def get_tools():
    """Get available tools."""
    try:
        tools = mcp.get_available_tools()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Error in /tools endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/context/save")
async def save_context(operation: ContextOperation):
    """Save the current conversation context."""
    try:
        result = mcp.save_context(operation.filename)
        return {"message": result}
    except Exception as e:
        logger.error(f"Error in /context/save endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/context/load")
async def load_context(operation: ContextOperation):
    """Load a saved conversation context."""
    try:
        result = mcp.load_context(operation.filename)
        return {"message": result}
    except Exception as e:
        logger.error(f"Error in /context/load endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/context/clear")
async def clear_context():
    """Clear the current conversation context."""
    try:
        mcp.memory.clear()
        mcp.context_manager.clear_context()
        return {"message": "Context cleared successfully"}
    except Exception as e:
        logger.error(f"Error in /context/clear endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)