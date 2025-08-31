"""LLM integration for meeting transcript analysis using Gemini 2.5."""

import os
import json
from typing import Dict, Any
import google.generativeai as genai

from models import Analysis


def init_gemini() -> None:
    """Initialize Gemini with API key from environment."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required")
    genai.configure(api_key=api_key)


def analyze_transcript(
    transcript: str,
    team: str,
    product: str,
    meeting_date: str
) -> Dict[str, Any]:
    """
    Analyze meeting transcript using Gemini to extract decisions and action items.
    
    Args:
        transcript: The meeting transcript text
        team: Team name for context
        product: Product name for context
        meeting_date: Meeting date in YYYY-MM-DD format
        
    Returns:
        Dictionary containing decisions and actions lists
    """
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Create the model
    model = genai.GenerativeModel(model_name=model_name)
    
    # JSON schema definition for the response
    json_schema = """
    {
        "decisions": [
            {
                "title": "string (required)",
                "owner": "string or null",
                "rationale": "string or null", 
                "effective_date": "YYYY-MM-DD or null"
            }
        ],
        "actions": [
            {
                "title": "string (required)",
                "assignee": "string or null",
                "due": "YYYY-MM-DD or null",
                "priority": "P0|P1|P2 or null",
                "notes": "string or null"
            }
        ]
    }
    """
    
    system_prompt = f"""You are an expert meeting analyst. Extract decisions and action items from the meeting transcript.

RULES:
- Extract only what is explicitly mentioned in the transcript
- If information is not available, use null values
- Do not hallucinate or infer information not present
- Be precise and factual
- Return ONLY valid JSON matching the exact schema below

CONTEXT:
- Team: {team}
- Product: {product}
- Meeting Date: {meeting_date}

JSON SCHEMA TO FOLLOW:
{json_schema}

For each DECISION, identify:
- title: The actual decision made
- owner: Person responsible (if mentioned)
- rationale: Reasoning provided (if mentioned)
- effective_date: When it takes effect (if mentioned, format YYYY-MM-DD)

For each ACTION ITEM, identify:
- title: What needs to be done
- assignee: Who is assigned (if mentioned)
- due: Due date (if mentioned, format YYYY-MM-DD)
- priority: Priority level if mentioned (P0/P1/P2 only)
- notes: Additional context (if any)

TRANSCRIPT:
{transcript}

Return only valid JSON matching the schema above. No explanations, just the JSON."""

    try:
        response = model.generate_content(system_prompt)
        response_text = response.text.strip()
        
        # Clean up the response to extract JSON
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        result = json.loads(response_text)
        
        # Validate the response matches our expected structure
        analysis = Analysis(**result)
        return analysis.model_dump()
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {str(e)}")
    except Exception as e:
        raise ValueError(f"Failed to analyze transcript: {str(e)}")
