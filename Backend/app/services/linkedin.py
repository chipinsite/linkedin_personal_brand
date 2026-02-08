from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from ..config import settings


class LinkedInApiError(RuntimeError):
    pass


class LinkedInAuthError(LinkedInApiError):
    pass


class LinkedInRateLimitError(LinkedInApiError):
    pass


@dataclass
class LinkedInComment:
    linkedin_comment_id: str
    commenter_name: str
    comment_text: str
    commenter_profile_url: str | None = None
    commenter_follower_count: int | None = None



def _parse_comment_item(row: dict) -> LinkedInComment | None:
    comment_id = row.get("id") or row.get("linkedin_comment_id")
    if not comment_id:
        return None

    profile = row.get("actor") or row.get("commenter") or {}
    commenter_name = (
        profile.get("name")
        or row.get("commenter_name")
        or "Unknown"
    )
    comment_text = row.get("message") or row.get("comment_text") or row.get("text") or ""

    return LinkedInComment(
        linkedin_comment_id=str(comment_id),
        commenter_name=str(commenter_name),
        comment_text=str(comment_text),
        commenter_profile_url=profile.get("profile_url") or row.get("commenter_profile_url"),
        commenter_follower_count=profile.get("follower_count") or row.get("commenter_follower_count"),
    )



def _parse_comments_page(payload: dict) -> tuple[list[LinkedInComment], int | None]:
    rows = payload.get("elements") or payload.get("comments") or payload.get("data") or []
    comments: list[LinkedInComment] = []
    for row in rows:
        if isinstance(row, dict):
            parsed = _parse_comment_item(row)
            if parsed:
                comments.append(parsed)

    paging = payload.get("paging") or {}
    next_start = paging.get("nextStart")
    if next_start is None:
        links = paging.get("links") or []
        for link in links:
            if isinstance(link, dict) and link.get("rel") == "next":
                start = link.get("start")
                if isinstance(start, int):
                    next_start = start
                    break
    return comments, next_start



def _mock_comments_for_post(linkedin_post_id: str) -> list[LinkedInComment]:
    if not settings.linkedin_mock_comments_json:
        return []

    try:
        payload = json.loads(settings.linkedin_mock_comments_json)
        raw = payload.get(linkedin_post_id, []) if isinstance(payload, dict) else []
        if isinstance(raw, dict) and isinstance(raw.get("pages"), list):
            rows = []
            for page in raw["pages"]:
                if isinstance(page, list):
                    rows.extend(page)
        elif isinstance(raw, list):
            rows = raw
        else:
            rows = []

        out: list[LinkedInComment] = []
        seen: set[str] = set()
        for row in rows:
            if isinstance(row, dict):
                parsed = _parse_comment_item(row)
                if parsed and parsed.linkedin_comment_id not in seen:
                    seen.add(parsed.linkedin_comment_id)
                    out.append(parsed)
        return out
    except Exception:
        return []



def fetch_recent_comments_for_post(
    linkedin_post_id: str,
    since_minutes: int = 15,
    _client: httpx.Client | None = None,
) -> list[LinkedInComment]:
    _ = since_minutes

    mock_comments = _mock_comments_for_post(linkedin_post_id)
    if mock_comments:
        return mock_comments

    if settings.linkedin_api_mode != "api" or not settings.linkedin_api_token:
        return []

    own_client = _client is None
    client = _client or httpx.Client(timeout=settings.linkedin_api_timeout_seconds)

    try:
        headers = {"Authorization": f"Bearer {settings.linkedin_api_token}"}
        start = 0
        count = max(1, settings.linkedin_api_page_size)
        output: list[LinkedInComment] = []
        seen: set[str] = set()

        while True:
            url = f"{settings.linkedin_api_base_url.rstrip('/')}/rest/socialActions/{linkedin_post_id}/comments"
            params = {"start": start, "count": count}

            last_exc: Exception | None = None
            response: httpx.Response | None = None
            for _attempt in range(settings.linkedin_api_retries + 1):
                try:
                    response = client.get(url, headers=headers, params=params)
                    if response.status_code >= 500:
                        raise LinkedInApiError(f"LinkedIn server error {response.status_code}")
                    break
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    response = None

            if response is None:
                raise LinkedInApiError(f"LinkedIn request failed: {last_exc}")

            if response.status_code in (401, 403):
                raise LinkedInAuthError("LinkedIn auth failed")
            if response.status_code == 429:
                raise LinkedInRateLimitError("LinkedIn rate limit reached")
            if response.status_code >= 400:
                raise LinkedInApiError(f"LinkedIn API error {response.status_code}: {response.text}")

            payload = response.json()
            parsed, next_start = _parse_comments_page(payload)
            for comment in parsed:
                if comment.linkedin_comment_id not in seen:
                    seen.add(comment.linkedin_comment_id)
                    output.append(comment)

            if next_start is None:
                break
            start = next_start

        return output
    finally:
        if own_client:
            client.close()
