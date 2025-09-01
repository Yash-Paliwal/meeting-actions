"""FastAPI application for meeting-actions web app."""

import os
import uuid
from datetime import date
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, HTTPException, Query, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

from llm import init_gemini, analyze_transcript
from notion_sync import sync_to_notion
from transcription import (
    transcribe_audio_video, 
    save_upload_file, 
    validate_file_format, 
    validate_file_size,
    get_supported_formats
)
from database import (
    init_database, 
    TranscriptStorage, 
    AnalysisStorage, 
    SyncStorage,
    cleanup_old_data
)


# Load environment variables
load_dotenv()


class NotionSyncRequest(BaseModel):
    """Request model for Notion sync endpoint."""
    analysis: Dict[str, Any]
    analysis_id: Optional[str] = None
    meeting_url: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Initialize database and Gemini on startup
    try:
        init_database()
        init_gemini()  # This initializes Gemini for analysis
        # Clean up old data on startup (older than 30 days)
        cleanup_old_data(30)
    except Exception as e:
        print(f"Warning: Failed to initialize services: {e}")
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
    
    # Save transcript to database
    if not TranscriptStorage.save_transcript(transcript_id, transcript.strip()):
        raise HTTPException(status_code=500, detail="Failed to save transcript")
    
    return {"transcript_id": transcript_id}


@app.post("/upload")
async def upload_audio_video(
    file: UploadFile = File(...),
    language: str = Form(None)
):
    """
    Upload audio/video file and transcribe it automatically.
    
    Args:
        file: Audio/video file to transcribe
        language: Language code (optional, auto-detect if not provided)
        
    Returns:
        Dictionary with transcript_id and transcribed text
    """
    # Validate file format
    if not validate_file_format(file.filename):
        supported = get_supported_formats()
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format. Supported formats: {supported['audio'] + supported['video']}"
        )
    
    # Validate file size
    if not validate_file_size(file.size):
        max_size = get_supported_formats()["max_size_mb"]
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size: {max_size}MB"
        )
    
    try:
        # Save uploaded file
        file_path = await save_upload_file(file)
        
        # Transcribe audio/video
        transcript_text = await transcribe_audio_video(file_path, language)
        
        if not transcript_text.strip():
            raise HTTPException(status_code=400, detail="No speech detected in the file")
        
        # Generate transcript ID and save to database
        transcript_id = str(uuid.uuid4())
        if not TranscriptStorage.save_transcript(transcript_id, transcript_text.strip()):
            raise HTTPException(status_code=500, detail="Failed to save transcript")
        
        return {
            "transcript_id": transcript_id,
            "transcript": transcript_text.strip(),
            "filename": file.filename,
            "file_size_mb": round(file.size / (1024 * 1024), 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/formats")
async def get_supported_file_formats():
    """
    Get supported audio/video file formats.
    
    Returns:
        Dictionary with supported formats and size limits
    """
    return get_supported_formats()


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
        Analysis results with decisions and actions, plus analysis_id
    """
    # Check if transcript exists in database
    transcript = TranscriptStorage.get_transcript(transcript_id)
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    # Check if analysis already exists for this transcript
    existing_analysis = AnalysisStorage.get_analysis_by_transcript(transcript_id)
    if existing_analysis and (
        existing_analysis["team"] == team and 
        existing_analysis["product"] == product and 
        existing_analysis["meeting_date"] == date
    ):
        # Return existing analysis with its ID
        result = existing_analysis["analysis_data"].copy()
        result["analysis_id"] = existing_analysis["id"]
        return result
    
    try:
        # Validate date format  
        from datetime import date as date_cls
        date_obj = date_cls.fromisoformat(date)
        
        # Analyze transcript using Gemini
        analysis = analyze_transcript(transcript, team, product, date)
        
        # Save analysis to database
        analysis_id = str(uuid.uuid4())
        if not AnalysisStorage.save_analysis(
            analysis_id, transcript_id, team, product, date, analysis
        ):
            print("Warning: Failed to save analysis to database")
        
        # Add analysis_id to response
        result = analysis.copy()
        result["analysis_id"] = analysis_id
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/notion/sync")
async def sync_notion(request: NotionSyncRequest):
    """
    Sync analysis results to Notion databases.
    
    Args:
        request: Contains analysis data, analysis ID, and optional meeting URL
        
    Returns:
        Sync results with created and updated counts
    """
    try:
        # Check if already synced
        if request.analysis_id:
            existing_sync = SyncStorage.get_sync_status(request.analysis_id)
            if existing_sync and not existing_sync["sync_result"].get("errors"):
                # Return previous successful sync result
                return existing_sync["sync_result"]
        
        # Perform sync
        results = sync_to_notion(request.analysis, request.meeting_url)
        
        # Save sync result to database
        if request.analysis_id:
            SyncStorage.save_sync_result(
                request.analysis_id,
                request.meeting_url,
                results
            )
        
        return results
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notion sync failed: {str(e)}")


@app.get("/history/transcripts")
async def get_transcript_history(limit: int = Query(10, ge=1, le=50)):
    """
    Get recent transcript history.
    
    Args:
        limit: Number of recent transcripts to return (1-50)
        
    Returns:
        List of recent transcripts with metadata
    """
    try:
        transcripts = TranscriptStorage.get_recent_transcripts(limit)
        # Truncate content for preview
        for transcript in transcripts:
            if len(transcript["content"]) > 200:
                transcript["content_preview"] = transcript["content"][:200] + "..."
            else:
                transcript["content_preview"] = transcript["content"]
        return {"transcripts": transcripts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


@app.get("/history/analyses")
async def get_analysis_history(limit: int = Query(10, ge=1, le=50)):
    """
    Get recent analysis history.
    
    Args:
        limit: Number of recent analyses to return (1-50)
        
    Returns:
        List of recent analyses with metadata
    """
    try:
        analyses = AnalysisStorage.get_recent_analyses(limit)
        return {"analyses": analyses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analysis history: {str(e)}")


@app.get("/recovery/transcript/{transcript_id}")
async def recover_transcript(transcript_id: str):
    """
    Recover a transcript by ID for data recovery.
    
    Args:
        transcript_id: The transcript ID to recover
        
    Returns:
        Transcript content and any associated analysis
    """
    try:
        transcript = TranscriptStorage.get_transcript(transcript_id)
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        # Also get any existing analysis
        analysis = AnalysisStorage.get_analysis_by_transcript(transcript_id)
        
        return {
            "transcript_id": transcript_id,
            "content": transcript,
            "has_analysis": analysis is not None,
            "analysis": analysis
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recovery failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
