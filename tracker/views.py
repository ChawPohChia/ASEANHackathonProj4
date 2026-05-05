from __future__ import annotations

import json
from collections import Counter
from datetime import timedelta

from django.db.models import Max
from django.shortcuts import render
from django.utils import timezone

from tracker.models import SentimentAnalysis


def dashboard(request):
    now = timezone.now()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(hours=24)

    hour_qs = SentimentAnalysis.objects.filter(classified_at__gte=hour_ago)
    day_qs = SentimentAnalysis.objects.filter(classified_at__gte=day_ago)

    hour_counter = Counter(hour_qs.values_list("score", flat=True))
    day_counter = Counter(day_qs.values_list("score", flat=True))

    hour_counts = [hour_counter.get(i, 0) for i in range(10)]
    day_counts = [day_counter.get(i, 0) for i in range(10)]

    last_updated = SentimentAnalysis.objects.aggregate(m=Max("classified_at"))["m"]

    context = {
        "hour_counts": hour_counts,
        "day_counts": day_counts,
        "hour_total": sum(hour_counts),
        "day_total": sum(day_counts),
        "last_updated": last_updated,
        "score_labels_json": json.dumps(list(range(10))),
        "hour_counts_json": json.dumps(hour_counts),
        "day_counts_json": json.dumps(day_counts),
        "hour_caption": "Posts classified in the last 1 hour (scores 0–9).",
        "day_caption": "Accumulated posts over the last 24 hours — count per score (0–9).",
    }
    return render(request, "tracker/dashboard.html", context)
