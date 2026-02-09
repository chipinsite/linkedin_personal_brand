"""Comment Reply Generation Service.

Generates contextual auto-replies and suggested replies for comments
using LLM or deterministic fallback templates.
"""

from __future__ import annotations

from ..config import settings
from .llm_client import generate_text


# Fallback reply templates by context
FALLBACK_AUTO_REPLIES = [
    "Thanks for sharing your perspective on this.",
    "Appreciate you taking the time to comment.",
    "Great point - thanks for adding to the conversation.",
    "Thanks for the thoughtful comment.",
    "Appreciate the engagement on this topic.",
]

FALLBACK_SUGGESTED_REPLIES = {
    "PARTNERSHIP_SIGNAL": [
        "Thanks for reaching out! I'd be happy to explore this further. Feel free to connect with me directly.",
        "Appreciate the interest! Let's connect - I'd love to hear more about what you have in mind.",
        "Thank you! Always open to exploring synergies. Drop me a message and we can discuss.",
    ],
    "TECHNICAL_QUESTION": [
        "Great question! In short, [brief answer]. Happy to dive deeper if useful.",
        "Thanks for asking! The key consideration here is [main point]. Let me know if you'd like more detail.",
        "Good question - the answer depends on context, but generally [overview]. What's your specific use case?",
    ],
    "OBJECTION": [
        "Appreciate the pushback! You raise a valid point about [aspect]. My view is based on [reasoning].",
        "Thanks for the different perspective. You're right that [acknowledgment], though I'd argue [counter].",
        "Fair challenge! I see where you're coming from. The nuance I'd add is [clarification].",
    ],
    "INFLUENTIAL": [
        "Thanks for weighing in! Always great to hear your perspective on this.",
        "Appreciate you taking the time to comment. Your insights on this space are always valuable.",
        "Thank you! Would love to continue this conversation - feel free to connect.",
    ],
    "MEDIA_INQUIRY": [
        "Thanks for reaching out! Happy to discuss further. Please feel free to connect directly.",
        "Appreciate the interest! I'd be glad to contribute. Drop me a message with more details.",
        "Thank you! Always happy to share insights on these topics. Let's connect.",
    ],
}

DEFAULT_SUGGESTED_REPLIES = [
    "Thanks for the comment! Appreciate your engagement.",
    "Great point - thanks for sharing your thoughts.",
    "Thanks for taking the time to comment on this.",
]


def _get_fallback_auto_reply(comment_text: str) -> str:
    """Get a deterministic fallback auto-reply based on comment hash."""
    # Use comment text hash to pick a consistent reply
    idx = hash(comment_text) % len(FALLBACK_AUTO_REPLIES)
    return FALLBACK_AUTO_REPLIES[idx]


def _get_fallback_suggested_replies(high_value_reason: str | None) -> list[str]:
    """Get fallback suggested replies based on escalation reason."""
    if high_value_reason and high_value_reason in FALLBACK_SUGGESTED_REPLIES:
        return FALLBACK_SUGGESTED_REPLIES[high_value_reason]
    return DEFAULT_SUGGESTED_REPLIES


def generate_auto_reply(
    comment_text: str,
    post_summary: str | None = None,
) -> str:
    """Generate a contextual auto-reply for a comment.

    Uses LLM when available, falls back to templates otherwise.

    Args:
        comment_text: The comment to reply to
        post_summary: Optional summary of the original post for context

    Returns:
        Generated reply text (1-3 sentences)
    """
    # Use fallback in mock mode or when no API key
    if settings.llm_mock_mode or not settings.llm_api_key:
        return _get_fallback_auto_reply(comment_text)

    prompt = f"""You are writing a reply to a LinkedIn comment on Sphiwe's post.

Comment: {comment_text}
{f"Post summary: {post_summary}" if post_summary else ""}

Reply rules:
- Friendly and professional tone
- 1 to 3 sentences maximum
- Acknowledge the commenter's point
- Add value where possible
- No promotional language
- No excessive gratitude or flattery

Generate a reply."""

    try:
        response = generate_text(user_prompt=prompt, max_tokens=150)
        reply = response.content
        # Clean up any quotes or prefixes
        reply = reply.strip().strip('"').strip("'")
        if reply.lower().startswith("reply:"):
            reply = reply[6:].strip()
        return reply
    except Exception:
        return _get_fallback_auto_reply(comment_text)


def generate_suggested_replies(
    comment_text: str,
    high_value_reason: str | None,
    post_summary: str | None = None,
    num_suggestions: int = 3,
) -> list[str]:
    """Generate suggested reply options for an escalated comment.

    Args:
        comment_text: The comment to reply to
        high_value_reason: Why this comment was flagged as high-value
        post_summary: Optional summary of the original post
        num_suggestions: Number of suggestions to generate (default 3)

    Returns:
        List of suggested reply texts
    """
    # Use fallback in mock mode or when no API key
    if settings.llm_mock_mode or not settings.llm_api_key:
        return _get_fallback_suggested_replies(high_value_reason)[:num_suggestions]

    reason_context = {
        "PARTNERSHIP_SIGNAL": "This comment mentions collaboration or partnership opportunity.",
        "TECHNICAL_QUESTION": "This comment asks a technical question requiring expertise.",
        "OBJECTION": "This comment disagrees with or challenges the post.",
        "INFLUENTIAL": "This commenter has a large following.",
        "MEDIA_INQUIRY": "This comment mentions interview, quote, or media opportunity.",
    }

    context = reason_context.get(high_value_reason, "This is a high-value comment requiring attention.")

    prompt = f"""You are generating reply options for a high-value LinkedIn comment on Sphiwe's post.

Comment: {comment_text}
{f"Post summary: {post_summary}" if post_summary else ""}

Context: {context}

Generate {num_suggestions} distinct reply options. Each should:
- Be 1-3 sentences
- Be friendly and professional
- Address the specific comment
- Vary in tone (one more formal, one more conversational, one with a follow-up question)

Format as numbered list:
1. [reply 1]
2. [reply 2]
3. [reply 3]"""

    try:
        llm_response = generate_text(user_prompt=prompt, max_tokens=400)
        response_text = llm_response.content
        # Parse numbered list
        replies = []
        for line in response_text.strip().split("\n"):
            line = line.strip()
            if line and line[0].isdigit() and "." in line:
                # Remove number prefix
                reply = line.split(".", 1)[1].strip()
                reply = reply.strip('"').strip("'")
                if reply:
                    replies.append(reply)
        if len(replies) >= num_suggestions:
            return replies[:num_suggestions]
        # Fall back if parsing failed
        return _get_fallback_suggested_replies(high_value_reason)[:num_suggestions]
    except Exception:
        return _get_fallback_suggested_replies(high_value_reason)[:num_suggestions]
