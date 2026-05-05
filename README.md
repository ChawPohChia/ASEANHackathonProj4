# ASEANHackathonProj4 — Singapore weather sentiment tracker

Django app that ingests **recent X (Twitter) posts** matching a **Singapore-focused weather** search, classifies **weather-related mood** with the **OpenAI Chat Completions** API (integer **0–9**), and stores posts + scores in **SQLite**. A **dashboard** shows bar charts for the **last hour** and **last 24 hours** of classified posts.

## Prerequisites

- Python 3.11+ (tested with 3.13)
- X API **Bearer token** with access to **recent search** (plan/tier dependent)
- **OpenAI API key**

## Local setup

```powershell
cd D:\ASEANHackathonProj4
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit .env: set X_BEARER_TOKEN, OPENAI_API_KEY, DJANGO_SECRET_KEY
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open **http://127.0.0.1:8000/** for the dashboard and **http://127.0.0.1:8000/admin/** for stored posts and sentiment rows.

## Ingestion

Manual run (good for cron or testing):

```powershell
python manage.py run_ingestion
```

### Hourly schedule (django-q2)

django-q2 runs tasks in a separate **cluster** process.

1. Apply migrations (includes django-q tables).
2. Register the hourly schedule once:

   ```powershell
   python manage.py setup_hourly_schedule
   ```

3. In a **second terminal**, start the worker cluster:

   ```powershell
   python manage.py qcluster
   ```

The scheduler enqueues `tracker.tasks.ingest_and_classify` every hour while `qcluster` is running.

## Sentiment scale

| Score | Meaning |
|------:|---------|
| 0 | Very unhappy / negative about the weather |
| 4 | Neutral / no strong feeling |
| 9 | Extremely happy / positive about the weather |

Prompt version is recorded per row (`SENTIMENT_PROMPT_VERSION`) so scores stay comparable when the prompt changes.

## Compliance and limits

- Respect **X Developer Agreement** and your product tier (retention, display, redistribution).
- Recent search returns up to **100** tweets per request; `X_MAX_RESULTS` is clamped to **10–100**.
- Rate limits: the client backs off on **429** using `x-rate-limit-reset` when present.

## Project layout

- `config/` — Django settings, URLs
- `tracker/` — models, dashboard, X + OpenAI services, django-q task, management commands
