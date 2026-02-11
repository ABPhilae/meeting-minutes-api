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
    # IMPORTANT: Swagger UI sends JSON, so newlines must be escaped as \n
    # in the example. Literal line breaks in the JSON body cause a 422 error.
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "raw_notes": "Meeting on Q4 Audit Planning - January 15, 2026\n\nPresent: Sarah Chen (Head of Audit), Jean-Pierre Dubois (Senior Auditor), Li Wei (Data Analytics Lead), Rahul Sharma (Risk Manager)\n\nSarah opened by reviewing the Q3 audit findings. She noted three critical issues were found in the APAC trade reconciliation system, specifically around timestamp mismatches between the Hong Kong and Singapore offices. She wants Q4 to focus on the same area with an expanded scope covering all five APAC offices.\n\nJean-Pierre suggested implementing automated data validation checks that could catch these discrepancies in real-time. He volunteered to draft a proposal for the automated checks by January 22nd. Sarah agreed this should be high priority.\n\nLi Wei demonstrated a prototype Power BI dashboard that could monitor reconciliation anomalies in real-time. The team was impressed with the demo. Li Wei will schedule a full walkthrough session for the broader audit team next Thursday at 2pm.\n\nRahul raised concerns about the regulatory deadline in March. The HKMA expects a comprehensive report on reconciliation controls by March 31. The team agreed this is the top priority and needs weekly status updates. Sarah will set up a recurring 30-minute weekly sync starting January 22.\n\nOther items discussed:\n- Budget approval for new audit tools is still pending with Finance\n- The annual audit methodology review will happen in February\n- Two new team members joining in February need onboarding plans\n\nRahul will prepare a risk assessment matrix for the APAC reconciliation issues by end of this week. Li Wei offered to provide data extracts to support Rahul's analysis.\n\nNext meeting: January 22, 2026 at 3pm HKT."
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

