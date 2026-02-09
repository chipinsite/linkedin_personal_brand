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


@dataclass
class LinkedInPostMetrics:
    """Post engagement metrics from LinkedIn."""
    impressions: int = 0
    reactions: int = 0
    comments_count: int = 0
    shares: int = 0
    engagement_rate: float = 0.0

    def __post_init__(self):
        # Calculate engagement rate if we have impressions
        if self.impressions > 0:
            total_engagements = self.reactions + self.comments_count + self.shares
            self.engagement_rate = round((total_engagements / self.impressions) * 100, 2)



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


def _parse_metrics_response(payload: dict) -> LinkedInPostMetrics:
    """Parse LinkedIn API response into metrics dataclass."""
    # LinkedIn API can return metrics in various formats
    # Handle common response structures

    # Direct fields
    impressions = payload.get("impressions") or payload.get("views") or 0
    reactions = payload.get("reactions") or payload.get("likes") or payload.get("numLikes") or 0
    comments_count = payload.get("comments") or payload.get("numComments") or 0
    shares = payload.get("shares") or payload.get("numShares") or payload.get("reposts") or 0

    # Nested structure (LinkedIn Marketing API format)
    if "elements" in payload and isinstance(payload["elements"], list):
        for element in payload["elements"]:
            if isinstance(element, dict):
                impressions = element.get("impressionCount", impressions)
                reactions = element.get("likeCount", reactions)
                comments_count = element.get("commentCount", comments_count)
                shares = element.get("shareCount", shares)

    # Statistics block format
    if "statistics" in payload:
        stats = payload["statistics"]
        if isinstance(stats, dict):
            impressions = stats.get("impressions", impressions)
            reactions = stats.get("reactions", reactions)
            comments_count = stats.get("comments", comments_count)
            shares = stats.get("shares", shares)

    return LinkedInPostMetrics(
        impressions=int(impressions) if impressions else 0,
        reactions=int(reactions) if reactions else 0,
        comments_count=int(comments_count) if comments_count else 0,
        shares=int(shares) if shares else 0,
    )


def _mock_metrics_for_post(linkedin_post_id: str) -> LinkedInPostMetrics | None:
    """Return mock metrics for testing."""
    if not settings.linkedin_mock_metrics_json:
        return None

    try:
        payload = json.loads(settings.linkedin_mock_metrics_json)
        if isinstance(payload, dict):
            post_data = payload.get(linkedin_post_id)
            if isinstance(post_data, dict):
                return _parse_metrics_response(post_data)
        return None
    except Exception:
        return None


def fetch_post_metrics(
    linkedin_post_id: str,
    _client: httpx.Client | None = None,
) -> LinkedInPostMetrics:
    """Fetch engagement metrics for a LinkedIn post.

    Args:
        linkedin_post_id: The LinkedIn post URN or ID
        _client: Optional httpx client for connection reuse

    Returns:
        LinkedInPostMetrics with impressions, reactions, comments, shares

    Raises:
        LinkedInAuthError: If authentication fails
        LinkedInRateLimitError: If rate limit is exceeded
        LinkedInApiError: For other API errors
    """
    # Check for mock metrics first
    mock_metrics = _mock_metrics_for_post(linkedin_post_id)
    if mock_metrics is not None:
        return mock_metrics

    # Return empty metrics if not configured for API mode
    if settings.linkedin_api_mode != "api" or not settings.linkedin_api_token:
        return LinkedInPostMetrics()

    own_client = _client is None
    client = _client or httpx.Client(timeout=settings.linkedin_api_timeout_seconds)

    try:
        headers = {"Authorization": f"Bearer {settings.linkedin_api_token}"}

        # LinkedIn Marketing API endpoint for share statistics
        # Format: /rest/organizationalEntityShareStatistics?q=organizationalEntity&shares=List(urn:li:share:{id})
        # Or for UGC posts: /rest/shares/{id}/statistics
        url = f"{settings.linkedin_api_base_url.rstrip('/')}/rest/shares/{linkedin_post_id}/statistics"

        last_exc: Exception | None = None
        response: httpx.Response | None = None

        for _attempt in range(settings.linkedin_api_retries + 1):
            try:
                response = client.get(url, headers=headers)
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
        return _parse_metrics_response(payload)

    finally:
        if own_client:
            client.close()


def fetch_metrics_batch(
    post_ids: list[str],
    _client: httpx.Client | None = None,
) -> dict[str, LinkedInPostMetrics]:
    """Fetch metrics for multiple posts.

    Args:
        post_ids: List of LinkedIn post IDs
        _client: Optional httpx client for connection reuse

    Returns:
        Dict mapping post_id to LinkedInPostMetrics
    """
    results: dict[str, LinkedInPostMetrics] = {}

    own_client = _client is None
    client = _client or httpx.Client(timeout=settings.linkedin_api_timeout_seconds)

    try:
        for post_id in post_ids:
            try:
                metrics = fetch_post_metrics(post_id, _client=client)
                results[post_id] = metrics
            except LinkedInApiError:
                # Continue with other posts on error
                results[post_id] = LinkedInPostMetrics()
    finally:
        if own_client:
            client.close()

    return results
