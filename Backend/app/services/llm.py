from __future__ import annotations

import json

import httpx

from ..config import settings
from ..models import PostFormat, PostTone


def _fallback_post(pillar: str, sub_theme: str, tone: PostTone) -> str:
    lead = {
        PostTone.educational: "Here is one framework I use:",
        PostTone.opinionated: "I disagree with the default industry approach:",
        PostTone.direct: "Direct take:",
        PostTone.exploratory: "I am testing this hypothesis:",
    }[tone]
    return (
        f"{lead}\n\n"
        f"In {pillar.lower()}, {sub_theme.lower()} performance often depends more on execution rhythm than tool count. "
        "Teams that tighten decision loops between media, creative, and analytics usually outperform.\n\n"
        "What is one operating change that has had measurable impact for your team? #Adtech #AI"
    )


def _build_generation_prompt(
    pillar: str,
    sub_theme: str,
    post_format: PostFormat,
    tone: PostTone,
    research_context: str,
) -> str:
    return (
        "You are writing a LinkedIn post for Sphiwe, a Head of Sales focused on Adtech and AI in advertising.\\n\\n"
        f"Pillar theme: {pillar}\\n"
        f"Sub theme: {sub_theme}\\n"
        f"Format: {post_format.value}\\n"
        f"Tone: {tone.value}\\n"
        f"Research context:\\n{research_context}\\n\\n"
        "Rules:\\n"
        "- Use South African English\\n"
        "- First person singular\\n"
        "- Keep explicit topical consistency with Adtech and AI in advertising\\n"
        "- Avoid hype and banned business cliches\\n"
        "- Avoid engagement bait (no 'like/comment/tag/follow' prompts)\\n"
        "- Do not include external URLs in the post body\\n"
        "- Keep hashtags between 1 and 3\\n"
        "- Max 300 words\\n"
        "- Optimise dwell time: strong first line, short paragraphs, clear structure\\n"
        "- End with a practical takeaway or discussion question\\n"
        "- If making a prediction, label it as a prediction\\n"
        "Return only the final post body."
    )


def _build_summary_prompt(source_name: str, title: str, content: str) -> str:
    return (
        "Summarise this article in 3 to 5 sentences, focusing on adtech/AI implications and uncertainty flags.\\n"
        f"Source: {source_name}\\n"
        f"Title: {title}\\n"
        f"Content:\\n{content[:7000]}"
    )


def _call_claude(prompt: str) -> str:
    if not settings.llm_api_key:
        raise RuntimeError("Missing LLM_API_KEY")

    headers = {
        "x-api-key": settings.llm_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": settings.llm_model,
        "max_tokens": 900,
        "temperature": 0.4,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = httpx.post(settings.anthropic_base_url, headers=headers, json=payload, timeout=30)
    if response.status_code >= 300:
        raise RuntimeError(f"Claude API error: {response.status_code} {response.text}")

    body = response.json()
    blocks = body.get("content", [])
    text_blocks = [b.get("text", "") for b in blocks if b.get("type") == "text"]
    result = "\\n".join([t.strip() for t in text_blocks if t.strip()]).strip()
    if not result:
        raise RuntimeError("Claude API returned empty content")
    return result


def generate_linkedin_post(
    pillar: str,
    sub_theme: str,
    post_format: PostFormat,
    tone: PostTone,
    research_context: str,
) -> str:
    if settings.llm_provider.lower() != "claude":
        return _fallback_post(pillar, sub_theme, tone)

    prompt = _build_generation_prompt(pillar, sub_theme, post_format, tone, research_context)
    try:
        return _call_claude(prompt)
    except Exception:
        return _fallback_post(pillar, sub_theme, tone)


def summarize_source(source_name: str, title: str, content: str) -> str:
    if settings.llm_provider.lower() != "claude" or not settings.llm_api_key:
        sentence = content.strip().replace("\n", " ")
        return sentence[:420] if sentence else f"Summary unavailable for {title}."

    prompt = _build_summary_prompt(source_name, title, content)
    try:
        return _call_claude(prompt)
    except Exception:
        sentence = content.strip().replace("\n", " ")
        return sentence[:420] if sentence else f"Summary unavailable for {title}."


def parse_citations(raw: str) -> str:
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return json.dumps(parsed)
    except Exception:
        pass
    return json.dumps([])
