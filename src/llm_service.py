"""
LLM Service - The single gateway to the OpenAI API.

WHY THIS FILE EXISTS:
- If we ever switch from OpenAI to Anthropic, we only change THIS file
- All error handling and retry logic is in ONE place
- We can easily add logging, cost tracking, caching later
- Testing: we can mock THIS service instead of mocking OpenAI everywhere
"""
from openai import OpenAI, APIError, RateLimitError, APIConnectionError
from src.config import settings
import logging
import time
import json

logger = logging.getLogger(__name__)


class LLMService:
    """
    Wrapper around the OpenAI API.

    This class handles:
    - Client initialization
    - Retry logic with exponential backoff
    - Error handling and logging
    - JSON response parsing
    """

    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. "
                "Please add it to your .env file."
            )
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.max_tokens
        logger.info(f"LLM Service initialized with model: {self.model}")

    def generate(
        self,
        prompt: str,
        system_message: str = "You are a helpful assistant.",
        temperature: float = 0.3,
        max_retries: int = 3,
    ) -> str:
        """
        Send a prompt to OpenAI and return the text response.

        Args:
            prompt: The user message (the question / task)
            system_message: Instructions for the AI behavior
            temperature: 0.0 = very focused, 1.0 = very creative
            max_retries: Number of retry attempts on failure

        Returns:
            The raw text response from the AI

        Raises:
            Exception: If all retries are exhausted
        """
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Calling OpenAI (attempt {attempt + 1}/{max_retries}, "
                    f"model={self.model}, temp={temperature})"
                )

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=self.max_tokens,
                )

                result = response.choices[0].message.content

                # Log token usage for cost monitoring
                usage = response.usage
                logger.info(
                    f"OpenAI response received: "
                    f"{usage.prompt_tokens} prompt tokens, "
                    f"{usage.completion_tokens} completion tokens, "
                    f"{usage.total_tokens} total tokens"
                )

                return result

            except RateLimitError:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(
                    f"Rate limited by OpenAI. "
                    f"Waiting {wait_time}s before retry..."
                )
                time.sleep(wait_time)

            except APIConnectionError as e:
                logger.error(f"Connection error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    raise

            except APIError as e:
                logger.error(f"OpenAI API error: {e}")
                raise  # Don't retry on other API errors

        raise Exception("All retry attempts exhausted")

    def generate_json(
        self,
        prompt: str,
        system_message: str = "You are a helpful assistant.",
        temperature: float = 0.3,
    ) -> dict:
        """
        Send a prompt and parse the response as JSON.

        This method handles the common pattern where we ask the AI
        to return JSON and need to parse it safely.
        """
        raw_response = self.generate(
            prompt=prompt,
            system_message=system_message,
            temperature=temperature,
        )

        # Clean up common AI quirks in JSON responses
        cleaned = raw_response.strip()

        # Sometimes AI wraps JSON in markdown code blocks
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]  # Remove ```json
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]  # Remove ```
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]  # Remove trailing ```

        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Raw response was: {raw_response[:500]}")
            raise ValueError(
                f"AI returned invalid JSON. This can happen occasionally. "
                f"Please try again. Error: {e}"
            )


# Create a single instance shared across the application
llm_service = LLMService()
