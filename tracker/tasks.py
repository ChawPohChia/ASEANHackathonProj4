"""django-q2 task entrypoints (import path must be a dotted string)."""

from tracker.services.pipeline import run_ingestion_pipeline


def ingest_and_classify():
    """Scheduled / queued ingestion + classification."""
    return run_ingestion_pipeline()
