#!/usr/bin/env python3
"""
Insurance Bot API Server - REST API cho frontend app
"""

import os
import sys
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import json
import time

# Import bot
sys.path.append('..')
from insurance_bot_minirag import InsuranceBotMiniRAG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Insurance Bot API",
    description="API cho chatbot bảo hiểm FISS",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global bot instance
bot: Optional[InsuranceBotMiniRAG] = None

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: float
    session_id: Optional[str] = None
    processing_time: float

class HealthResponse(BaseModel):
    status: str
    timestamp: float
    bot_ready: bool
    version: str

@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup"""
    global bot
    try:
        logger.info("🚀 Initializing Insurance Bot...")
        bot = InsuranceBotMiniRAG()
        logger.info("✅ Insurance Bot ready!")
    except Exception as e:
        logger.error(f"❌ Failed to initialize bot: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global bot
    if bot:
        try:
            await bot.close()
            logger.info("👋 Bot closed")
        except Exception as e:
            logger.error(f"❌ Error closing bot: {e}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        bot_ready=bot is not None,
        version="1.0.0"
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    try:
        start_time = time.time()

        # Process message
        response = await bot.chat(request.message)

        processing_time = time.time() - start_time

        return ChatResponse(
            response=response,
            timestamp=time.time(),
            session_id=request.session_id,
            processing_time=processing_time
        )

    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """Streaming chat endpoint"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    async def generate_response():
        try:
            start_time = time.time()

            # For now, return full response (can implement streaming later)
            response = await bot.chat(request.message)

            processing_time = time.time() - start_time

            result = {
                "response": response,
                "timestamp": time.time(),
                "session_id": request.session_id,
                "processing_time": processing_time,
                "finished": True
            }

            yield f"data: {json.dumps(result)}\n\n"

        except Exception as e:
            logger.error(f"❌ Stream error: {e}")
            error_data = {
                "error": str(e),
                "timestamp": time.time(),
                "finished": True
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Insurance Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    # Run server
    uvicorn.run(
        "insurance_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
