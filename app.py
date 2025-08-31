"""FastAPI application for meeting-actions web app."""

import os
import uuid
from datetime import date
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

from llm import init_gemini, analyze_transcript
from notion_sync import sync_to_notion


# Load environment variables
load_dotenv()

# In-memory storage for transcripts (use Redis/DB in production)
transcripts: Dict[str, str] = {}


class NotionSyncRequest(BaseModel):
    """Request model for Notion sync endpoint."""
    analysis: Dict[str, Any]
    meeting_url: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Initialize Gemini on startup
    try:
        init_gemini()
    except Exception as e:
        print(f"Warning: Failed to initialize Gemini: {e}")
    yield


# Create FastAPI app
app = FastAPI(
    title="Meeting Actions",
    description="Extract decisions and action items from meeting transcripts",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")


@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"ok": True}


@app.post("/ingest")
async def ingest_transcript(transcript: str = Form(...)):
    """
    Ingest a meeting transcript and return a transcript ID.
    
    Args:
        transcript: The meeting transcript text
        
    Returns:
        Dictionary with transcript_id
    """
    if not transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript cannot be empty")
    
    transcript_id = str(uuid.uuid4())
    transcripts[transcript_id] = transcript.strip()
    
    return {"transcript_id": transcript_id}


@app.post("/analyze")
async def analyze_meeting(
    transcript_id: str = Query(...),
    team: str = Query(...),
    product: str = Query(...),
    date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
):
    """
    Analyze a meeting transcript to extract decisions and action items.
    
    Args:
        transcript_id: ID of the ingested transcript
        team: Team name for context
        product: Product name for context
        date: Meeting date in YYYY-MM-DD format
        
    Returns:
        Analysis results with decisions and actions
    """
    if transcript_id not in transcripts:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    transcript = transcripts[transcript_id]
    
    try:
        # Validate date format  
        from datetime import date as date_cls
        date_obj = date_cls.fromisoformat(date)
        
        # Analyze transcript using Gemini
        analysis = analyze_transcript(transcript, team, product, date)
        return analysis
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/notion/sync")
async def sync_notion(request: NotionSyncRequest):
    """
    Sync analysis results to Notion databases.
    
    Args:
        request: Contains analysis data and optional meeting URL
        
    Returns:
        Sync results with created and updated counts
    """
    try:
        results = sync_to_notion(request.analysis, request.meeting_url)
        return results
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notion sync failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
