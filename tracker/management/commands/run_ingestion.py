import json

from django.core.management.base import BaseCommand

from tracker.services.pipeline import run_ingestion_pipeline


class Command(BaseCommand):
    help = "Fetch recent X posts and classify weather sentiment (manual / cron)."

    def handle(self, *args, **options):
        summary = run_ingestion_pipeline()
        self.stdout.write(json.dumps(summary, indent=2))
