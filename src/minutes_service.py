"""
Meeting Minutes Service - The core AI logic.

This file contains the prompt engineering and business logic
for converting raw meeting notes into structured minutes.

ARCHITECTURE NOTE:
- llm_service.py handles HOW to talk to OpenAI (retries, errors)
- minutes_service.py handles WHAT to ask OpenAI (prompts, parsing)
- main.py handles WHO can ask (endpoints, HTTP, validation)
"""
from src.llm_service import llm_service
from src.models import (
    MeetingMinutesResponse,
    TopicDiscussed,
    ActionItem,
    Priority,
)
import logging

logger = logging.getLogger(__name__)


# ================================================================
# SYSTEM PROMPT
# ================================================================
# This is the most critical part of the entire application.
# The quality of your output depends 80% on this prompt.
# Notice how specific and structured it is - vague prompts
# produce vague results.

SYSTEM_PROMPT = """You are an expert meeting secretary working in a
professional financial services environment. Your job is to convert
raw meeting notes into perfectly structured meeting minutes.

INSTRUCTIONS:
1. Extract ALL attendees mentioned (by name or role)
2. Identify the main topics discussed and summarize each one
3. Capture every decision that was made
4. Extract EVERY action item with a clear owner
5. If a deadline is mentioned, include it
6. Mark items as high priority if urgent language was used
   (e.g., "critical", "ASAP", "by end of week", "blocker")
7. Infer the meeting title from the context

RESPONSE FORMAT:
Return ONLY a valid JSON object. No explanation, no markdown,
no text before or after the JSON. The JSON must have this structure:

{
  "title": "Short, descriptive meeting title",
  "date": "Date if mentioned, or null",
  "attendees": ["Name 1", "Name 2"],
  "topics_discussed": [
    {
      "topic": "Topic name",
      "summary": "2-3 sentence summary of the discussion",
      "decisions": ["Decision 1", "Decision 2"]
    }
  ],
  "action_items": [
    {
      "task": "Clear description of what needs to be done",
      "assignee": "Person responsible",
      "deadline": "Deadline or null",
      "priority": "high or medium or low"
    }
  ],
  "next_meeting": "Date/time or null"
}

RULES:
- Every action item MUST have an assignee
- If the assignee is unclear, use "Team" or "TBD"
- Decisions should be concrete, not vague
- Topic summaries should be 2-3 sentences, not one word
- Return valid JSON only - no trailing commas"""


class MinutesService:
    """Service for generating meeting minutes from raw notes."""

    def generate_minutes(self, raw_notes: str) -> MeetingMinutesResponse:
        """
        Process raw meeting notes and return structured minutes.

        Args:
            raw_notes: The unstructured meeting text

        Returns:
            MeetingMinutesResponse: Validated, structured minutes
        """
        logger.info(f"Processing meeting notes ({len(raw_notes)} chars)")

        # Build the prompt with the actual meeting notes
        prompt = (
            "Here are the raw meeting notes to process:\n\n"
            "--- START OF MEETING NOTES ---\n"
            f"{raw_notes}\n"
            "--- END OF MEETING NOTES ---\n\n"
            "Convert these notes into structured meeting minutes."
        )

        # Call the LLM and get parsed JSON
        data = llm_service.generate_json(
            prompt=prompt,
            system_message=SYSTEM_PROMPT,
            temperature=0.2,  # Low temp for factual, consistent output
        )

        # Convert the raw dict into validated Pydantic models
        # This is where Pydantic catches any issues in the AI output
        minutes = MeetingMinutesResponse(
            title=data.get("title", "Untitled Meeting"),
            date=data.get("date"),
            attendees=data.get("attendees", []),
            topics_discussed=[
                TopicDiscussed(
                    topic=t.get("topic", "Unknown Topic"),
                    summary=t.get("summary", ""),
                    decisions=t.get("decisions", []),
                )
                for t in data.get("topics_discussed", [])
            ],
            action_items=[
                ActionItem(
                    task=a.get("task", ""),
                    assignee=a.get("assignee", "TBD"),
                    deadline=a.get("deadline"),
                    priority=Priority(a.get("priority", "medium")),
                )
                for a in data.get("action_items", [])
            ],
            next_meeting=data.get("next_meeting"),
        )

        logger.info(
            f"Minutes generated: {len(minutes.topics_discussed)} topics, "
            f"{len(minutes.action_items)} action items"
        )

        return minutes


# Single shared instance
minutes_service = MinutesService()

