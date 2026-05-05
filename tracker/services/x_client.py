"""X API v2 recent search client with basic rate-limit handling."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _clamp_max_results(n: int) -> int:
    # Recent search allows max_results in [10, 100].
    return max(10, min(100, n))


def fetch_recent_posts(
    query: str | None = None,
    max_results: int | None = None,
) -> list[dict[str, Any]]:
    """
    Returns normalized tweet dicts:
    id, text, author_id, author_username, created_at (ISO), lang, raw_tweet, raw_includes
    """
    token = (settings.X_BEARER_TOKEN or "").strip()
    if not token:
        logger.warning("X_BEARER_TOKEN is not set; skipping X fetch.")
        return []

    q = query if query is not None else settings.WEATHER_SEARCH_QUERY
    n = _clamp_max_results(max_results if max_results is not None else settings.X_MAX_RESULTS)

    url = f"{settings.X_API_BASE.rstrip('/')}/tweets/search/recent"
    params = {
        "query": q,
        "max_results": n,
        "tweet.fields": "created_at,author_id,lang",
        "expansions": "author_id",
        "user.fields": "username",
    }
    headers = {"Authorization": f"Bearer {token}"}

    backoff = 1.0
    last_error: str | None = None

    for attempt in range(settings.X_MAX_RETRIES):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
        except requests.RequestException as exc:
            last_error = str(exc)
            logger.exception("X API request failed: %s", exc)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
            continue

        if resp.status_code == 429:
            reset = resp.headers.get("x-rate-limit-reset")
            wait = int(reset) - int(time.time()) if reset and reset.isdigit() else int(backoff)
            wait = max(1, min(wait, 900))
            logger.warning("X API rate limited; sleeping %s s (attempt %s)", wait, attempt + 1)
            time.sleep(wait)
            backoff = min(backoff * 2, 60)
            continue

        if resp.status_code >= 500:
            last_error = f"HTTP {resp.status_code}"
            logger.warning("X API server error %s; retrying", resp.status_code)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
            continue

        if resp.status_code != 200:
            last_error = f"HTTP {resp.status_code}: {resp.text[:500]}"
            logger.error("X API error: %s", last_error)
            return []

        payload = resp.json()
        data = payload.get("data") or []
        includes = payload.get("includes") or {}
        users_by_id = {u["id"]: u for u in includes.get("users") or []}

        out: list[dict[str, Any]] = []
        for t in data:
            aid = t.get("author_id") or ""
            user = users_by_id.get(aid, {})
            out.append(
                {
                    "id": t.get("id"),
                    "text": t.get("text") or "",
                    "author_id": aid,
                    "author_username": user.get("username") or "",
                    "created_at": t.get("created_at"),
                    "lang": t.get("lang") or "",
                    "raw_tweet": t,
                    "raw_includes": includes,
                }
            )
        return out

    if last_error:
        logger.error("X API gave up after retries: %s", last_error)
    return []
