"""LLM Client Service.

Provides a clean interface to the Anthropic Claude API with:
- Mock mode for testing without live credentials
- Exponential backoff retry for transient failures
- Token usage tracking
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-3-5-sonnet-latest"
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TEMPERATURE = 0.7

# Retry configuration (3 attempts: 30s, 1m, 2m)
RETRY_DELAYS = [30, 60, 120]
MAX_RETRIES = 3


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LLMResponse:
    """Response from an LLM API call."""

    content: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    is_mock: bool = False


@dataclass
class LLMError:
    """Error from an LLM API call."""

    error_type: str
    message: str
    status_code: int | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Mock Mode
# ─────────────────────────────────────────────────────────────────────────────

def _is_mock_mode() -> bool:
    """Check if LLM should operate in mock mode.

    Mock mode is enabled when:
    - ANTHROPIC_API_KEY (LLM_API_KEY) is not set, OR
    - LLM_MOCK_MODE is explicitly set to true
    """
    # Check for explicit mock mode flag
    llm_mock_mode = getattr(settings, "llm_mock_mode", False)
    if llm_mock_mode:
        return True

    # Check if API key is missing
    api_key = getattr(settings, "llm_api_key", None) or getattr(settings, "anthropic_api_key", None)
    if not api_key:
        return True

    return False


def _generate_mock_response(system_prompt: str, user_prompt: str) -> LLMResponse:
    """Generate a realistic mock response for testing.

    The mock response follows the correct format and structure
    so downstream logic can be tested without live API calls.
    """
    # Extract context from prompts to generate relevant mock content
    mock_content = _generate_mock_linkedin_post(user_prompt)

    return LLMResponse(
        content=mock_content,
        model="mock-claude-3-5-sonnet",
        input_tokens=len(system_prompt.split()) + len(user_prompt.split()),
        output_tokens=len(mock_content.split()),
        total_tokens=len(system_prompt.split()) + len(user_prompt.split()) + len(mock_content.split()),
        is_mock=True,
    )


def _generate_mock_linkedin_post(prompt: str) -> str:
    """Generate a mock LinkedIn post based on prompt context."""
    # Extract pillar and sub-theme if present in prompt
    pillar = "adtech"
    sub_theme = "innovation"

    if "Adtech fundamentals" in prompt:
        pillar = "adtech fundamentals"
    elif "Agentic AI" in prompt:
        pillar = "agentic AI"
    elif "AI in advertising" in prompt:
        pillar = "AI in advertising"

    if "Programmatic" in prompt:
        sub_theme = "programmatic buying"
    elif "measurement" in prompt.lower():
        sub_theme = "measurement and attribution"
    elif "bidding" in prompt.lower():
        sub_theme = "AI bidding agents"
    elif "creative" in prompt.lower():
        sub_theme = "creative optimisation"

    # Determine tone
    tone = "educational"
    if "OPINIONATED" in prompt:
        tone = "opinionated"
    elif "DIRECT" in prompt:
        tone = "direct"
    elif "EXPLORATORY" in prompt:
        tone = "exploratory"

    # Generate appropriate opening based on tone
    openings = {
        "educational": "One framework I find useful when thinking about",
        "opinionated": "I disagree with the common view that",
        "direct": "Straight talk:",
        "exploratory": "I have been testing an idea about",
    }

    opening = openings.get(tone, openings["educational"])

    return f"""{opening} {sub_theme} in {pillar}:

The real shift is not about technology adoption. It is about operational rhythm.

Teams that tighten the loop between insight and action consistently outperform those with better tools but slower cycles. I have seen this pattern repeatedly over 20 years in Sub-Saharan Africa markets.

Three signals that indicate maturity:
1. Decision latency under 48 hours for campaign changes
2. Cross-functional review cadence at least weekly
3. Clear ownership of optimisation levers

The question is not whether AI will transform this space. It is whether teams can adapt their operating model fast enough to capture the value.

What operational change has made the biggest difference for your team this quarter?

#Adtech #AI"""


def _generate_mock_reply(prompt: str) -> str:
    """Generate a mock comment reply based on prompt context."""
    return """Thank you for sharing that perspective. It aligns with what I have observed in the African market context.

I would be interested to hear more about how you approach the measurement challenge specifically. What framework works best for your team?"""


def _generate_mock_summary(prompt: str) -> str:
    """Generate a mock source summary."""
    return """This article discusses emerging trends in advertising technology with a focus on automation and AI integration. The key insight is that operational adaptation matters more than tool selection. The author suggests a three-phase approach to adoption. Note: claims about specific ROI percentages are not independently verified."""


# ─────────────────────────────────────────────────────────────────────────────
# API Client
# ─────────────────────────────────────────────────────────────────────────────

class LLMClient:
    """Client for interacting with the Anthropic Claude API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        """Initialize the LLM client.

        Args:
            api_key: Anthropic API key (defaults to settings.llm_api_key)
            model: Model to use (defaults to settings.llm_model)
            base_url: API base URL (defaults to settings.anthropic_base_url)
        """
        self.api_key = api_key or getattr(settings, "llm_api_key", None)
        self.model = model or getattr(settings, "llm_model", DEFAULT_MODEL)
        self.base_url = base_url or getattr(settings, "anthropic_base_url", ANTHROPIC_API_URL)

    def is_mock_mode(self) -> bool:
        """Check if client is operating in mock mode."""
        return _is_mock_mode()

    def generate(
        self,
        user_prompt: str,
        system_prompt: str = "",
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            user_prompt: The user message to send
            system_prompt: Optional system prompt for context
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            LLMResponse with content and metadata

        Raises:
            LLMError: If the API call fails after all retries
        """
        if self.is_mock_mode():
            logger.info("LLM client operating in mock mode")
            return _generate_mock_response(system_prompt, user_prompt)

        return self._call_api_with_retry(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def _call_api_with_retry(
        self,
        user_prompt: str,
        system_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Call the API with exponential backoff retry.

        Retries up to 3 times with delays of 30s, 1m, 2m.
        """
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                return self._call_api(
                    user_prompt=user_prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            except httpx.HTTPStatusError as e:
                last_error = e
                # Don't retry client errors (4xx) except rate limits (429)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    raise
                logger.warning(
                    f"LLM API error (attempt {attempt + 1}/{MAX_RETRIES}): "
                    f"{e.response.status_code} - retrying in {RETRY_DELAYS[attempt]}s"
                )
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_error = e
                logger.warning(
                    f"LLM API request error (attempt {attempt + 1}/{MAX_RETRIES}): "
                    f"{type(e).__name__} - retrying in {RETRY_DELAYS[attempt]}s"
                )

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAYS[attempt])

        # All retries exhausted
        error_msg = str(last_error) if last_error else "Unknown error"
        raise RuntimeError(f"LLM API failed after {MAX_RETRIES} attempts: {error_msg}")

    def _call_api(
        self,
        user_prompt: str,
        system_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Make a single API call to Claude."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        if system_prompt:
            payload["system"] = system_prompt

        response = httpx.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()

        data = response.json()

        # Extract text content from response
        content_blocks = data.get("content", [])
        text_parts = [
            block.get("text", "")
            for block in content_blocks
            if block.get("type") == "text"
        ]
        content = "\n".join(text_parts).strip()

        if not content:
            raise RuntimeError("Claude API returned empty content")

        # Extract usage stats
        usage = data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        return LLMResponse(
            content=content,
            model=data.get("model", self.model),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            is_mock=False,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Convenience Functions
# ─────────────────────────────────────────────────────────────────────────────

# Singleton client instance
_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get the singleton LLM client instance."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


def generate_text(
    user_prompt: str,
    system_prompt: str = "",
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
) -> LLMResponse:
    """Generate text using the default LLM client.

    Args:
        user_prompt: The user message to send
        system_prompt: Optional system prompt for context
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature

    Returns:
        LLMResponse with content and metadata
    """
    client = get_llm_client()
    return client.generate(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )


def is_mock_mode() -> bool:
    """Check if LLM is operating in mock mode."""
    return _is_mock_mode()
