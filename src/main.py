"""
Meeting Minutes API - Main Application.

This is the entry point of the API.
It defines all HTTP endpoints and wires them to the services.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import time
import logging

from src.config import settings
from src.models import (
    MeetingNotesRequest,
    MinutesWithMetadata,
    HealthResponse,
)
from src.minutes_service import minutes_service

# ================================================================
# LOGGING SETUP
# ================================================================
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ================================================================
# APP CREATION
# ================================================================
app = FastAPI(
    title=settings.app_name,
    description=(
        "An AI-powered API that converts raw meeting notes "
        "into structured, professional meeting minutes. "
        "Built with FastAPI and OpenAI."
    ),
    version=settings.app_version,
)

# CORS middleware - allows web browsers to call your API
# Without this, a React/Vue frontend cannot talk to your API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, list specific domains
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================
# ENDPOINTS
# ================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Every production API needs this. Monitoring tools (like Docker
    health checks, Kubernetes probes, or Uptime Robot) call this
    endpoint every 30 seconds to confirm the service is alive.
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow().isoformat(),
    )


@app.post("/generate-minutes", response_model=MinutesWithMetadata)
async def generate_minutes(request: MeetingNotesRequest):
    """
    Convert raw meeting notes into structured meeting minutes.

    Send your raw, unstructured meeting notes and receive back
    professionally structured minutes with topics, action items,
    and key decisions.
    """
    logger.info(
        f"Received meeting notes: {len(request.raw_notes)} chars, "
        f"language: {request.language}"
    )

    start_time = time.time()

    try:
        # Call the minutes service to process the notes
        minutes = minutes_service.generate_minutes(request.raw_notes)

        # Calculate processing time
        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        logger.info(f"Minutes generated in {elapsed_ms}ms")

        # Wrap the minutes with metadata and return
        return MinutesWithMetadata(
            minutes=minutes,
            processing_time_ms=elapsed_ms,
            model_used=settings.openai_model,
            input_character_count=len(request.raw_notes),
            generated_at=datetime.utcnow().isoformat(),
        )

    except ValueError as e:
        # This catches JSON parsing errors from the AI
        logger.error(f"Processing error: {e}")
        raise HTTPException(
            status_code=422,
            detail=str(e),
        )

    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=(
                "An unexpected error occurred while processing "
                "your meeting notes. Please try again."
            ),
        )


# ================================================================
# STARTUP EVENT
# ================================================================

@app.on_event("startup")
async def startup_event():
    """Runs when the server starts. Good for initialization checks."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Using model: {settings.openai_model}")
    if not settings.openai_api_key:
        logger.error("WARNING: OPENAI_API_KEY is not set!")
