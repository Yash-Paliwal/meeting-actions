"""Notion synchronization with idempotency for decisions and action items."""

import os
import hashlib
from typing import Dict, List, Any, Optional
from datetime import date

from notion_client import Client
from models import Decision, ActionItem, Analysis


def init_notion() -> Client:
    """Initialize Notion client."""
    token = os.getenv("NOTION_TOKEN")
    if not token:
        raise ValueError("NOTION_TOKEN environment variable is required")
    return Client(auth=token)


def compute_external_id(meeting_url: Optional[str], title: str) -> str:
    """Compute external ID for idempotency using SHA256."""
    source = (meeting_url or '') + '|' + title.strip().lower()
    return hashlib.sha256(source.encode()).hexdigest()


def find_existing_page(
    notion: Client,
    database_id: str,
    external_id: str
) -> Optional[str]:
    """Find existing page by external ID."""
    try:
        response = notion.databases.query(
            database_id=database_id,
            filter={
                "property": "External ID",
                "rich_text": {
                    "equals": external_id
                }
            }
        )
        
        if response["results"]:
            return response["results"][0]["id"]
        return None
    except Exception:
        return None


def upsert_action_item(
    notion: Client,
    database_id: str,
    action: ActionItem,
    meeting_url: Optional[str]
) -> Dict[str, str]:
    """Upsert action item to Notion backlog database."""
    try:
        external_id = compute_external_id(meeting_url, action.title)
        existing_page_id = find_existing_page(notion, database_id, external_id)
        
        # Prepare basic properties that should always exist
        properties = {
            "Name": {
                "title": [{"text": {"content": action.title}}]
            },
            "External ID": {
                "rich_text": [{"text": {"content": external_id}}]
            }
        }
        
        # Add optional properties only if they exist in the database
        try:
            # Try to add Status - this might not exist in user's database
            properties["Status"] = {"select": {"name": "Todo"}}
        except:
            pass
            
        if action.priority:
            try:
                properties["Priority"] = {"select": {"name": action.priority}}
            except:
                pass
        
        if action.due:
            try:
                properties["Due"] = {"date": {"start": action.due.isoformat()}}
            except:
                pass
        
        if action.notes:
            try:
                properties["Notes"] = {
                    "rich_text": [{"text": {"content": action.notes}}]
                }
            except:
                pass
        
        if meeting_url:
            try:
                properties["Source"] = {"url": meeting_url}
            except:
                pass
        
        if existing_page_id:
            # Update existing page
            notion.pages.update(page_id=existing_page_id, properties=properties)
            return {"action": "updated", "page_id": existing_page_id}
        else:
            # Create new page
            response = notion.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            return {"action": "created", "page_id": response["id"]}
            
    except Exception as e:
        # More detailed error information
        error_msg = f"Database ID: {database_id}, Error: {str(e)}"
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                error_msg += f", Details: {error_detail}"
            except:
                error_msg += f", Status: {e.response.status_code}"
        raise Exception(error_msg)


def upsert_decision(
    notion: Client,
    database_id: str,
    decision: Decision,
    meeting_url: Optional[str]
) -> Dict[str, str]:
    """Upsert decision to Notion decisions database."""
    try:
        external_id = compute_external_id(meeting_url, decision.title)
        existing_page_id = find_existing_page(notion, database_id, external_id)
        
        # Prepare basic properties that should always exist
        properties = {
            "Name": {
                "title": [{"text": {"content": decision.title}}]
            },
            "External ID": {
                "rich_text": [{"text": {"content": external_id}}]
            }
        }
        
        # Add optional properties only if they exist in the database
        if decision.owner:
            try:
                properties["Owner"] = {
                    "rich_text": [{"text": {"content": decision.owner}}]
                }
            except:
                pass
        
        if decision.rationale:
            try:
                properties["Rationale"] = {
                    "rich_text": [{"text": {"content": decision.rationale}}]
                }
            except:
                pass
        
        if decision.effective_date:
            try:
                properties["Effective Date"] = {
                    "date": {"start": decision.effective_date.isoformat()}
                }
            except:
                pass
        
        if meeting_url:
            try:
                properties["Source"] = {"url": meeting_url}
            except:
                pass
        
        if existing_page_id:
            # Update existing page
            notion.pages.update(page_id=existing_page_id, properties=properties)
            return {"action": "updated", "page_id": existing_page_id}
        else:
            # Create new page
            response = notion.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            return {"action": "created", "page_id": response["id"]}
            
    except Exception as e:
        # More detailed error information
        error_msg = f"Database ID: {database_id}, Error: {str(e)}"
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                error_msg += f", Details: {error_detail}"
            except:
                error_msg += f", Status: {e.response.status_code}"
        raise Exception(error_msg)


def sync_to_notion(
    analysis_data: Dict[str, Any],
    meeting_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sync analysis results to Notion databases.
    
    Args:
        analysis_data: Analysis results with decisions and actions
        meeting_url: Optional meeting URL for source reference
        
    Returns:
        Dictionary with created and updated counts
    """
    notion = init_notion()
    
    backlog_db = os.getenv("NOTION_BACKLOG_DB")
    decisions_db = os.getenv("NOTION_DECISIONS_DB")
    
    if not backlog_db or not decisions_db:
        raise ValueError("NOTION_BACKLOG_DB and NOTION_DECISIONS_DB environment variables are required")
    
    # Parse analysis data
    analysis = Analysis(**analysis_data)
    
    results = {
        "created": {"actions": 0, "decisions": 0},
        "updated": {"actions": 0, "decisions": 0},
        "errors": []
    }
    
    # Sync action items
    for action in analysis.actions:
        try:
            result = upsert_action_item(notion, backlog_db, action, meeting_url)
            if result["action"] == "created":
                results["created"]["actions"] += 1
            else:
                results["updated"]["actions"] += 1
        except Exception as e:
            results["errors"].append(f"Action '{action.title}': {str(e)}")
    
    # Sync decisions
    for decision in analysis.decisions:
        try:
            result = upsert_decision(notion, decisions_db, decision, meeting_url)
            if result["action"] == "created":
                results["created"]["decisions"] += 1
            else:
                results["updated"]["decisions"] += 1
        except Exception as e:
            results["errors"].append(f"Decision '{decision.title}': {str(e)}")
    
    return results
