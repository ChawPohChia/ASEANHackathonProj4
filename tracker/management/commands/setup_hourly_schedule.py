from django.core.management.base import BaseCommand
from django.utils import timezone
from django_q.models import Schedule


class Command(BaseCommand):
    help = "Register an hourly django-q2 schedule for ingestion (requires qcluster running)."

    def handle(self, *args, **options):
        sched, created = Schedule.objects.get_or_create(
            name="hourly_weather_ingestion",
            defaults={
                "func": "tracker.tasks.ingest_and_classify",
                "schedule_type": Schedule.HOURLY,
                "repeats": -1,
                "next_run": timezone.now(),
            },
        )
        if not created:
            sched.func = "tracker.tasks.ingest_and_classify"
            sched.schedule_type = Schedule.HOURLY
            sched.repeats = -1
            if not sched.next_run:
                sched.next_run = timezone.now()
            sched.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"Schedule {'created' if created else 'updated'}: {sched.name} ({sched.schedule_type})"
            )
        )
