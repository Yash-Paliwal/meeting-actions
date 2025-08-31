"""Pydantic models for meeting analysis."""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field


class Decision(BaseModel):
    """A decision made during the meeting."""
    title: str = Field(..., description="The decision that was made")
    owner: Optional[str] = Field(None, description="Person responsible for the decision")
    rationale: Optional[str] = Field(None, description="Reasoning behind the decision")
    effective_date: Optional[date] = Field(None, description="When the decision takes effect (YYYY-MM-DD)")


class ActionItem(BaseModel):
    """An action item from the meeting."""
    title: str = Field(..., description="The action that needs to be taken")
    assignee: Optional[str] = Field(None, description="Person assigned to the action")
    due: Optional[date] = Field(None, description="Due date for the action (YYYY-MM-DD)")
    priority: Optional[str] = Field(None, pattern="^(P0|P1|P2)$", description="Priority level: P0, P1, or P2")
    notes: Optional[str] = Field(None, description="Additional notes about the action item")


class Analysis(BaseModel):
    """Complete analysis result from a meeting transcript."""
    decisions: List[Decision] = Field(default_factory=list, description="List of decisions made")
    actions: List[ActionItem] = Field(default_factory=list, description="List of action items")
