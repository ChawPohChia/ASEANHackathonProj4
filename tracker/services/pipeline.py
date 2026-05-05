"""End-to-end ingestion: X fetch → persist posts → OpenAI sentiment."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from tracker.models import SentimentAnalysis, XPost

from .openai_sentiment import classify_weather_sentiment
from .x_client import fetch_recent_posts

logger = logging.getLogger(__name__)


def _parse_post_dt(value: str | None) -> datetime:
    if not value:
        return timezone.now()
    dt = parse_datetime(value)
    if dt is None:
        return timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone=timezone.utc)
    return dt


def run_ingestion_pipeline() -> dict[str, Any]:
    tweets = fetch_recent_posts()
    created_posts = 0
    classified = 0
    skipped = 0
    errors: list[str] = []

    for tw in tweets:
        pid = tw.get("id")
        if not pid:
            continue

        with transaction.atomic():
            post, created = XPost.objects.select_for_update().get_or_create(
                post_id=str(pid),
                defaults={
                    "text": tw.get("text") or "",
                    "author_id": tw.get("author_id") or "",
                    "author_username": tw.get("author_username") or "",
                    "lang": tw.get("lang") or "",
                    "post_created_at": _parse_post_dt(tw.get("created_at")),
                    "raw_payload": {
                        "tweet": tw.get("raw_tweet"),
                        "includes": tw.get("raw_includes"),
                    },
                },
            )
            if created:
                created_posts += 1

            if SentimentAnalysis.objects.filter(post=post).exists():
                skipped += 1
                continue

        try:
            result = classify_weather_sentiment(post.text)
        except Exception as exc:  # noqa: BLE001 — log and continue batch
            errors.append(f"{post.post_id}: {exc}")
            logger.exception("Sentiment failed for %s", post.post_id)
            continue

        SentimentAnalysis.objects.create(
            post=post,
            score=result["score"],
            model_name=result["model"],
            prompt_version=settings.SENTIMENT_PROMPT_VERSION,
            rationale=result.get("rationale") or "",
        )
        classified += 1

    summary = {
        "fetched": len(tweets),
        "new_posts": created_posts,
        "classified": classified,
        "skipped_existing_sentiment": skipped,
        "errors": errors,
    }
    logger.info("Ingestion complete: %s", summary)
    return summary
