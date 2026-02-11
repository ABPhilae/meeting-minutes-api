"""
Data models for the Meeting Minutes API.

These Pydantic models serve three purposes:
1. INPUT VALIDATION: Automatically reject malformed requests
2. DOCUMENTATION: FastAPI uses these to generate Swagger docs
3. TYPE SAFETY: Your IDE can autocomplete field names
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


# ================================================================
# ENUMS - Predefined choices (like a dropdown menu on a form)
# ================================================================

class Priority(str, Enum):
    """Priority levels for action items."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ================================================================
# REQUEST MODELS - What the user sends to us
# ================================================================

class MeetingNotesRequest(BaseModel):
    """
    The raw meeting notes sent by the user.

    Example usage (what the user sends as JSON):
    {
        "raw_notes": "Meeting on Q4 planning... Sarah said...",
        "language": "en"
    }
    """
    raw_notes: str = Field(
        ...,  # ... means this field is REQUIRED
        min_length=50,  # At least 50 characters (reject tiny inputs)
        max_length=50000,  # At most 50k chars (prevent abuse)
        description="Raw meeting notes or transcript to process"
    )
    language: str = Field(
        default="en",
        description="Language of the meeting notes (ISO code: en, fr, zh, etc.)"
    )

    # This is a Pydantic v2 feature: example values for the docs
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "raw_notes": "Meeting on Q4 Audit Planning - Jan 15, 2026. Present: Sarah, Jean-Pierre, Li Wei. Sarah opened by noting Q3 findings..."
                }
            ]
        }
    }


# ================================================================
# RESPONSE MODELS - What we send back to the user
# ================================================================

class TopicDiscussed(BaseModel):
    """A single topic that was discussed in the meeting."""
    topic: str = Field(description="Name of the topic discussed")
    summary: str = Field(description="2-3 sentence summary")
    decisions: List[str] = Field(
        default_factory=list,
        description="Decisions made about this topic"
    )


class ActionItem(BaseModel):
    """A specific task assigned during the meeting."""
    task: str = Field(description="Description of what needs to be done")
    assignee: str = Field(description="Person responsible")
    deadline: Optional[str] = Field(
        default=None,
        description="Deadline if mentioned"
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Priority level"
    )


class MeetingMinutesResponse(BaseModel):
    """
    The complete, structured meeting minutes.
    This is what our API returns after processing.
    """
    title: str = Field(description="Meeting title inferred from the content")
    date: Optional[str] = Field(default=None, description="Meeting date if mentioned")
    attendees: List[str] = Field(description="List of people present")
    topics_discussed: List[TopicDiscussed] = Field(
        description="Topics covered, each with summary and decisions"
    )
    action_items: List[ActionItem] = Field(
        description="Tasks assigned with owners and deadlines"
    )
    next_meeting: Optional[str] = Field(
        default=None,
        description="Date/time of next meeting if mentioned"
    )


class MinutesWithMetadata(BaseModel):
    """Final response wrapping the minutes with processing info."""
    minutes: MeetingMinutesResponse
    processing_time_ms: float = Field(description="How long processing took")
    model_used: str = Field(description="Which AI model was used")
    input_character_count: int
    generated_at: str


class HealthResponse(BaseModel):
    """Response from the health check endpoint."""
    status: str = "healthy"
    version: str
    timestamp: str

