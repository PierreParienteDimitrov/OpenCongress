# AI Summaries Setup Guide

This guide explains how to configure the AI-powered summaries feature for OpenCongress, which uses Google's Gemini 2.5 Flash model to generate:

- **Bill Summaries** - Plain-English explanations of legislation
- **Member Bios** - Biographical summaries for Congress members
- **Weekly Recap** - Saturday summary of the week's congressional activity
- **Weekly Preview** - Sunday preview of the upcoming week

## Table of Contents

1. [Getting API Keys](#getting-api-keys)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Testing the Integration](#testing-the-integration)
5. [Scheduled Tasks](#scheduled-tasks)
6. [Cost Estimates](#cost-estimates)

---

## Getting API Keys

### Google API Key (Gemini)

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click **Get API Key** in the left sidebar
4. Click **Create API Key**
5. Select or create a Google Cloud project
6. Copy the generated API key

> **Note**: The free tier includes generous limits suitable for development. For production, consider setting up billing on Google Cloud.

### Revalidation Secret

Generate a secure random string for ISR (Incremental Static Regeneration) revalidation:

```bash
# Using openssl
openssl rand -hex 32

# Or using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

This secret ensures only your backend can trigger frontend cache invalidation.

---

## Local Development Setup

### Backend Configuration

Create or update `/backend/.env`:

```bash
# AI Configuration
GOOGLE_API_KEY=your-gemini-api-key-here

# Frontend Integration (for ISR revalidation)
FRONTEND_URL=http://localhost:3000
REVALIDATION_SECRET=your-generated-secret-here

# Existing variables (keep these)
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
CONGRESS_API_KEY=your-congress-api-key
```

### Frontend Configuration

Create or update `/frontend/.env.local`:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# ISR Revalidation (must match backend REVALIDATION_SECRET)
REVALIDATION_SECRET=your-generated-secret-here
```

### Install Dependencies

```bash
# Backend
cd backend
source venv/bin/activate
pip install -r requirements/base.txt

# Frontend
cd ../frontend
npm install
```

### Run Migrations

```bash
cd backend
source venv/bin/activate
python manage.py migrate
```

---

## Production Deployment

### Environment Variables

Set these environment variables in your deployment platform (Railway, Heroku, AWS, etc.):

#### Backend Service

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Gemini API key | `AIzaSy...` |
| `FRONTEND_URL` | Production frontend URL | `https://opencongress.app` |
| `REVALIDATION_SECRET` | Shared secret for ISR | `a1b2c3d4...` |
| `SECRET_KEY` | Django secret key | (generate securely) |
| `DATABASE_URL` | PostgreSQL connection | `postgres://...` |
| `REDIS_URL` | Redis connection | `redis://...` |

#### Frontend Service

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `https://api.opencongress.app/api/v1` |
| `REVALIDATION_SECRET` | Must match backend | `a1b2c3d4...` |

### Railway Deployment

If using Railway, add these to your service variables:

1. Go to your Railway project
2. Select the backend service
3. Go to **Variables** tab
4. Add each variable listed above

Repeat for the frontend service with its variables.

### Security Notes

- Never commit `.env` files to version control
- Use different secrets for development and production
- Rotate the `REVALIDATION_SECRET` periodically
- Consider using Google Cloud's Secret Manager for production API keys

---

## Testing the Integration

### 1. Verify Backend Configuration

```bash
cd backend
source venv/bin/activate
python manage.py shell
```

```python
from django.conf import settings

# Check API key is set (don't print the full key!)
print(f"GOOGLE_API_KEY set: {bool(settings.GOOGLE_API_KEY)}")
print(f"FRONTEND_URL: {settings.FRONTEND_URL}")
print(f"REVALIDATION_SECRET set: {bool(settings.REVALIDATION_SECRET)}")
```

### 2. Test AI Generation (Single Bill)

```python
from tasks.ai import generate_bill_summary
from apps.congress.models import Bill

# Get a bill ID
bill = Bill.objects.first()
print(f"Testing with bill: {bill.bill_id}")

# Run synchronously for testing
result = generate_bill_summary(bill.bill_id)
print(result)
```

### 3. Test API Endpoints

```bash
# Start the backend server
python manage.py runserver

# In another terminal, test the API
curl http://localhost:8000/api/v1/content/weekly-summaries/
curl http://localhost:8000/api/v1/content/weekly-summaries/current/
```

### 4. Test Frontend Page

```bash
cd frontend
npm run dev
```

Visit http://localhost:3000/this-week to see the weekly summaries page.

### 5. Test ISR Revalidation

```bash
curl -X POST http://localhost:3000/api/revalidate \
  -H "Content-Type: application/json" \
  -d '{"path": "/this-week", "secret": "your-revalidation-secret"}'
```

Expected response:
```json
{"revalidated": true, "path": "/this-week", "timestamp": "2024-..."}
```

---

## Scheduled Tasks

The following Celery Beat tasks are configured:

| Task | Schedule | Description |
|------|----------|-------------|
| `generate_bill_summaries` | Daily 6:30 AM ET | Batch process bills needing summaries |
| `generate_weekly_recap` | Saturday 6:00 AM ET | Generate week-in-review summary |
| `generate_weekly_preview` | Sunday 6:00 PM ET | Generate week-ahead preview |
| `generate_member_bios` | Monday 5:00 AM ET | Batch process members needing bios |

### Running Celery Locally

```bash
# Terminal 1: Redis (if not running)
redis-server

# Terminal 2: Celery Worker
cd backend
source venv/bin/activate
celery -A config worker -l info -Q ai,sync,notifications

# Terminal 3: Celery Beat (scheduler)
celery -A config beat -l info
```

### Manual Task Execution

To run tasks manually (useful for initial data population):

```python
from tasks.ai import (
    generate_bill_summaries,
    generate_member_bios,
    generate_weekly_recap,
    generate_weekly_preview
)

# Generate summaries for bills without them
generate_bill_summaries.delay()

# Generate bios for members without them
generate_member_bios.delay()

# Generate this week's recap
generate_weekly_recap.delay()

# Generate next week's preview
generate_weekly_preview.delay()
```

---

## Cost Estimates

Using Gemini 2.5 Flash pricing ($0.15/MTok input, $0.60/MTok output):

| Content Type | Annual Volume | Est. Tokens | Annual Cost |
|--------------|---------------|-------------|-------------|
| Bill summaries | ~700 bills | ~612K | ~$0.13 |
| Weekly recaps | 52 weeks | ~156K | ~$0.03 |
| Weekly previews | 52 weeks | ~156K | ~$0.03 |
| Member bios | ~535 members | ~321K | ~$0.07 |
| **Total** | | **~1.25M** | **~$0.26/year** |

With 10x safety buffer: **~$2.60/year**

> These estimates assume one-time generation. Regenerating content (e.g., after prompt updates) will increase costs proportionally.

---

## Troubleshooting

### "GOOGLE_API_KEY is not configured"

Ensure the environment variable is set and the Django settings are loading it:

```python
# In Django shell
import os
print(os.environ.get('GOOGLE_API_KEY'))
```

### "Invalid API key"

1. Verify the key in [Google AI Studio](https://aistudio.google.com/)
2. Check for extra whitespace when copying
3. Ensure the key hasn't been revoked

### ISR Revalidation Failing

1. Verify `REVALIDATION_SECRET` matches in both backend and frontend
2. Check `FRONTEND_URL` is correct and accessible from backend
3. Review frontend logs for the `/api/revalidate` endpoint

### Tasks Not Running

1. Ensure Redis is running: `redis-cli ping`
2. Check Celery worker is connected: look for "ready" message in worker logs
3. Verify Celery Beat is running and scheduling tasks

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Celery Beat   │────▶│  Celery Worker  │────▶│   Gemini API    │
│   (Scheduler)   │     │   (AI Tasks)    │     │  (2.5 Flash)    │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   PostgreSQL    │
                        │   (Database)    │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  Django API     │────▶│  Next.js ISR    │
                        │  (REST)         │     │  Revalidation   │
                        └─────────────────┘     └─────────────────┘
```

1. **Celery Beat** triggers scheduled tasks
2. **Celery Worker** processes AI generation tasks
3. **Gemini API** generates the content
4. Results are stored in **PostgreSQL**
5. **Django API** serves the content
6. **ISR Revalidation** updates cached frontend pages
