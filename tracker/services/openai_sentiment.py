"""Weather-related sentiment scoring via OpenAI Chat Completions."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You classify how the author feels about the *weather* in a single social post.
Focus on Singapore-relevant weather (heat, rain, haze, humidity, storms, forecasts, etc.).
If the post is not really about weather mood, infer neutral (4).
Return strict JSON only with keys: score (integer 0-9), rationale (short string, <= 200 chars).
Scale: 0 = very unhappy/negative about weather, 4 = neutral/no strong feeling, 9 = extremely happy/positive about weather."""


def classify_weather_sentiment(text: str) -> dict[str, Any]:
    """
    Returns dict: score (int 0-9), rationale (str), model (str), raw (dict optional).
    On failure, raises or returns safe fallback — caller should handle.
    """
    api_key = (settings.OPENAI_API_KEY or "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    model = settings.OPENAI_MODEL
    client = OpenAI(api_key=api_key, max_retries=settings.OPENAI_MAX_RETRIES)

    user_content = json.dumps(
        {"post_text": text, "prompt_version": settings.SENTIMENT_PROMPT_VERSION},
        ensure_ascii=False,
    )

    completion = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )

    raw_content = completion.choices[0].message.content or "{}"
    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        logger.warning("OpenAI returned non-JSON: %s", raw_content[:300])
        parsed = _extract_json_object(raw_content)

    score = int(parsed.get("score", 4))
    score = max(0, min(9, score))
    rationale = str(parsed.get("rationale", ""))[:2000]

    return {
        "score": score,
        "rationale": rationale,
        "model": model,
        "raw": parsed,
    }


def _extract_json_object(text: str) -> dict[str, Any]:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {"score": 4, "rationale": "Unparseable model output."}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"score": 4, "rationale": "Unparseable model output."}
