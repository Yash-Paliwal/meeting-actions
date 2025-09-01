"""Audio/video transcription using OpenAI Whisper."""

import os
import tempfile
import aiofiles
from typing import Optional
import whisper
from fastapi import UploadFile, HTTPException


def init_whisper():
    """Initialize Whisper model."""
    # Load the Whisper model (will download on first use)
    # Using 'base' model for faster processing, can be changed to 'small', 'medium', 'large' for better accuracy
    return whisper.load_model("base")


async def save_upload_file(upload_file: UploadFile) -> str:
    """Save uploaded file to temporary location."""
    try:
        # Create temp file with original extension
        suffix = os.path.splitext(upload_file.filename)[1] if upload_file.filename else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await upload_file.read()
            temp_file.write(content)
            return temp_file.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


async def transcribe_audio_video(file_path: str, language: Optional[str] = None) -> str:
    """
    Transcribe audio/video file using OpenAI Whisper.
    
    Args:
        file_path: Path to the audio/video file
        language: Language code (optional, auto-detect if not provided)
        
    Returns:
        Transcribed text
    """
    try:
        # Initialize Whisper model
        model = init_whisper()
        
        # Set language for transcription
        if language and language != "auto-detect":
            # Map language codes to Whisper language codes
            language_map = {
                "en": "english",
                "es": "spanish", 
                "fr": "french",
                "de": "german",
                "it": "italian",
                "pt": "portuguese",
                "ru": "russian",
                "ja": "japanese",
                "ko": "korean",
                "zh": "chinese",
                "hi": "hindi"
            }
            whisper_language = language_map.get(language, language)
        else:
            whisper_language = None
        
        # Transcribe the audio/video file
        result = model.transcribe(
            file_path,
            language=whisper_language,
            verbose=False
        )
        
        # Clean up temp file
        os.unlink(file_path)
        
        # Return the transcribed text
        return result["text"].strip()
        
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(file_path):
            os.unlink(file_path)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


def get_supported_formats() -> dict:
    """Get supported audio/video formats."""
    return {
        "audio": [
            "mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"
        ],
        "video": [
            "mp4", "avi", "mov", "mkv", "webm", "flv", "wmv"
        ],
        "max_size_mb": 25  # Gemini file size limit
    }


def validate_file_format(filename: str) -> bool:
    """Validate if file format is supported."""
    if not filename:
        return False
    
    ext = filename.lower().split('.')[-1]
    supported_formats = get_supported_formats()
    
    return ext in supported_formats["audio"] or ext in supported_formats["video"]


def validate_file_size(file_size: int) -> bool:
    """Validate if file size is within limits."""
    max_size = get_supported_formats()["max_size_mb"] * 1024 * 1024  # Convert to bytes
    return file_size <= max_size
