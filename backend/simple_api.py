#!/usr/bin/env python3
"""
Simple FastAPI server for Personif.ai backend
Provides REST API endpoints for the simplified frontend
"""

import os
import logging
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Personif.ai API",
    description="Simple backend API for voice personification",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class PersonificationCreate(BaseModel):
    name: str
    content: str
    quotes: List[str] = []
    profilePic: Optional[str] = None
    elevenLabsId: Optional[str] = None
    status: str = "inactive"

class PersonificationUpdate(BaseModel):
    name: str
    content: str
    quotes: List[str] = []
    profilePic: Optional[str] = None
    elevenLabsId: Optional[str] = None
    status: str

class PersonificationResponse(BaseModel):
    id: str
    name: str
    content: str
    quotes: List[str] = []
    profilePic: Optional[str] = None
    elevenLabsId: Optional[str] = None
    status: str
    createdAt: str
    updatedAt: str

# In-memory storage for demo purposes
personifications_db: dict[str, PersonificationResponse] = {}

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "Personif.ai API is running"
    }

# Personification CRUD endpoints
@app.get("/api/personifications", response_model=List[PersonificationResponse])
async def get_personifications():
    """Get all personifications"""
    return list(personifications_db.values())

@app.get("/api/personifications/{personification_id}", response_model=PersonificationResponse)
async def get_personification(personification_id: str):
    """Get a specific personification"""
    if personification_id not in personifications_db:
        raise HTTPException(status_code=404, detail="Personification not found")
    return personifications_db[personification_id]

@app.post("/api/personifications", response_model=PersonificationResponse)
async def create_personification(personification: PersonificationCreate):
    """Create a new personification"""
    personification_id = str(uuid4())
    now = datetime.now().isoformat()
    
    new_personification = PersonificationResponse(
        id=personification_id,
        name=personification.name,
        content=personification.content,
        quotes=personification.quotes,
        profilePic=personification.profilePic,
        elevenLabsId=personification.elevenLabsId,
        status=personification.status,
        createdAt=now,
        updatedAt=now
    )
    
    personifications_db[personification_id] = new_personification
    logger.info(f"Created personification: {personification.name}")
    return new_personification

@app.put("/api/personifications/{personification_id}", response_model=PersonificationResponse)
async def update_personification(personification_id: str, personification: PersonificationUpdate):
    """Update a personification"""
    if personification_id not in personifications_db:
        raise HTTPException(status_code=404, detail="Personification not found")
    
    existing = personifications_db[personification_id]
    updated = PersonificationResponse(
        id=personification_id,
        name=personification.name,
        content=personification.content,
        quotes=personification.quotes,
        profilePic=personification.profilePic,
        elevenLabsId=personification.elevenLabsId,
        status=personification.status,
        createdAt=existing.createdAt,
        updatedAt=datetime.now().isoformat()
    )
    
    personifications_db[personification_id] = updated
    logger.info(f"Updated personification: {personification.name}")
    return updated

@app.delete("/api/personifications/{personification_id}")
async def delete_personification(personification_id: str):
    """Delete a personification"""
    if personification_id not in personifications_db:
        raise HTTPException(status_code=404, detail="Personification not found")
    
    deleted_name = personifications_db[personification_id].name
    del personifications_db[personification_id]
    logger.info(f"Deleted personification: {deleted_name}")
    return {
        "success": True,
        "message": f"Personification '{deleted_name}' deleted successfully"
    }

# Voice enrollment endpoint (simplified)
@app.post("/api/voice/enroll")
async def enroll_voice(
    audio: UploadFile = File(...),
    sampleRate: int = Form(16000)
):
    """Enroll user voice for speaker recognition"""
    try:
        # Read audio file
        audio_data = await audio.read()
        
        # Mock response - in production, integrate with actual voice enrollment
        logger.info(f"Voice enrollment request: {audio.filename}, sample rate: {sampleRate}")
        
        return {
            "success": True,
            "confidence": 0.95,
            "message": "Voice enrolled successfully"
        }
            
    except Exception as e:
        logger.error(f"Voice enrollment error: {e}")
        raise HTTPException(status_code=500, detail=f"Voice enrollment failed: {str(e)}")

# Statistics endpoint
@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    total = len(personifications_db)
    active = sum(1 for p in personifications_db.values() if p.status == "active")
    training = sum(1 for p in personifications_db.values() if p.status == "training")
    
    return {
        "total": total,
        "active": active,
        "training": training,
        "recentActivity": total
    }

# Initialize demo data
@app.on_event("startup")
async def startup_event():
    """Initialize demo data on startup"""
    logger.info("Initializing demo data...")
    
    # Create demo personifications
    demo_personifications = [
        PersonificationResponse(
            id="demo-1",
            name="Alex Johnson",
            content="Professional voice profile for client meetings. Professional and confident tone with clear articulation and moderate pace. You are Alex Johnson, a professional consultant specializing in business strategy and client relations. Respond as Alex Johnson would in a professional meeting setting, focusing on providing clear, actionable advice with a confident yet approachable tone.",
            quotes=[
                "Success is not final, failure is not fatal: it is the courage to continue that counts.",
                "The way to get started is to quit talking and begin doing.",
                "Don't be afraid to give up the good to go for the great."
            ],
            profilePic="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face",
            elevenLabsId="pNInz6obpgDQGcFmaJgB",
            status="active",
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat()
        ),
        PersonificationResponse(
            id="demo-2",
            name="Sarah Chen",
            content="Customer service representative voice. Warm and helpful with gentle pace and clear pronunciation. You are Sarah Chen, a customer service representative known for your patience and helpfulness. Respond as Sarah would when helping customers with their inquiries, always maintaining a positive, solution-oriented approach while being empathetic to customer concerns.",
            quotes=[
                "The customer's perception is your reality.",
                "A satisfied customer is the best business strategy of all.",
                "Service is the rent we pay for being on this earth."
            ],
            profilePic="https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150&h=150&fit=crop&crop=face",
            elevenLabsId="EXAVITQu4vr4xnSDxMaL",
            status="active",
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat()
        ),
        PersonificationResponse(
            id="demo-3",
            name="Michael Rodriguez",
            content="Training in progress - technical documentation. Technical and precise with slow, deliberate speech and clear enunciation. You are Michael Rodriguez, a technical writer specializing in software documentation. Explain technical concepts as Michael would in documentation, breaking down complex topics into clear, step-by-step explanations.",
            quotes=[
                "Code is like humor. When you have to explain it, it's bad.",
                "The best error message is the one that never shows up.",
                "First, solve the problem. Then, write the code."
            ],
            elevenLabsId="VR6AewLTigWG4xSOukaG",
            status="training",
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat()
        )
    ]
    
    for personification in demo_personifications:
        personifications_db[personification.id] = personification
    
    logger.info(f"Initialized {len(demo_personifications)} demo personifications")

if __name__ == "__main__":
    uvicorn.run(
        "simple_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
