# Deployment Guide

This guide covers deploying CongressTrack with:
- **Backend**: Railway (Django + Celery + PostgreSQL + Redis)
- **Frontend**: Vercel (Next.js)
- **CI/CD**: GitHub Actions

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub Actions                          │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │  Test Backend   │    │  Test Frontend  │    │   Deploy    │ │
│  │  pytest, ruff   │    │  lint, tsc      │    │  Sequential │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│         Railway             │   │          Vercel             │
│  ┌───────────────────────┐  │   │  ┌───────────────────────┐  │
│  │   PostgreSQL 16       │  │   │  │     Next.js 16        │  │
│  └───────────────────────┘  │   │  │     (Frontend)        │  │
│  ┌───────────────────────┐  │   │  └───────────────────────┘  │
│  │      Redis 7          │  │   │                             │
│  └───────────────────────┘  │   │  - Auto SSL                 │
│  ┌───────────────────────┐  │   │  - Edge CDN                 │
│  │   Django API          │  │   │  - Preview deployments      │
│  └───────────────────────┘  │   │                             │
│  ┌───────────────────────┐  │   └─────────────────────────────┘
│  │   Celery Worker       │  │
│  └───────────────────────┘  │
│  ┌───────────────────────┐  │
│  │   Celery Beat         │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
```

---

## Step 1: Railway Setup (Backend)

### 1.1 Create Railway Account

1. Go to https://railway.app and sign up
2. Connect your GitHub account

### 1.2 Create New Project

1. Click **New Project** → **Deploy from GitHub repo**
2. Select your repository
3. Railway will detect the project structure

### 1.3 Add Database Services

Add these services to your Railway project:

#### PostgreSQL
1. Click **New** → **Database** → **PostgreSQL**
2. Railway automatically provisions PostgreSQL 16
3. Note the connection variables (automatically injected)

#### Redis
1. Click **New** → **Database** → **Redis**
2. Railway automatically provisions Redis 7
3. Note the `REDIS_URL` (automatically injected)

### 1.4 Deploy Backend Services

You need 3 separate services for the backend:

#### Service 1: Django API (`congresstrack-api`)
1. Click **New** → **GitHub Repo** → Select your repo
2. Configure:
   - **Root Directory**: `backend`
   - **Config file**: `railway.toml` (auto-detected)
3. The service will use `Dockerfile.production`

#### Service 2: Celery Worker (`congresstrack-celery`)
1. Click **New** → **GitHub Repo** → Select your repo
2. Configure:
   - **Root Directory**: `backend`
   - **Start Command**: `celery -A config.celery worker --loglevel=info --concurrency=4 -Q sync,ai,notifications`
3. Or rename `railway.celery.toml` to `railway.toml` for this service

#### Service 3: Celery Beat (`congresstrack-celery-beat`)
1. Click **New** → **GitHub Repo** → Select your repo
2. Configure:
   - **Root Directory**: `backend`
   - **Start Command**: `celery -A config.celery beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler`
3. Or rename `railway.celery-beat.toml` to `railway.toml` for this service

### 1.5 Configure Environment Variables

Set these variables for **all backend services** (API, Celery, Celery Beat):

| Variable | Value | Notes |
|----------|-------|-------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` | Required |
| `SECRET_KEY` | `<generate-secure-key>` | Use `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `ALLOWED_HOSTS` | `<your-app>.up.railway.app,congresstrack.org` | Comma-separated |
| `JWT_SECRET_KEY` | `<generate-secure-key>` | Different from SECRET_KEY |
| `CONGRESS_API_KEY` | `<your-key>` | Get from https://api.data.gov/signup/ |
| `GOOGLE_CIVIC_API_KEY` | `<your-key>` | Google Cloud Console |
| `OPENAI_API_KEY` | `<your-key>` | OpenAI Platform |
| `EMAIL_HOST_PASSWORD` | `<sendgrid-api-key>` | SendGrid API key |
| `DEFAULT_FROM_EMAIL` | `noreply@yourdomain.com` | Your email |
| `SENTRY_DSN` | `<your-dsn>` | Optional - Sentry.io |
| `ENVIRONMENT` | `production` | For Sentry |

**Note**: `DATABASE_URL` and `REDIS_URL` are automatically injected by Railway when you link the PostgreSQL and Redis services.

### 1.6 Link Services

1. Go to each backend service's **Variables** tab
2. Click **Add Reference** → Select your PostgreSQL service
3. Click **Add Reference** → Select your Redis service
4. This injects `DATABASE_URL` and `REDIS_URL` automatically

### 1.7 Run Initial Migration

After the API service deploys:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run migrations
railway run --service congresstrack-api python manage.py migrate

# Create superuser (optional)
railway run --service congresstrack-api python manage.py createsuperuser
```

### 1.8 Generate Custom Domain (Optional)

1. Go to your API service → **Settings** → **Domains**
2. Add custom domain: `api.congresstrack.org`
3. Configure DNS with the provided CNAME

---

## Step 2: Vercel Setup (Frontend)

### 2.1 Create Vercel Account

1. Go to https://vercel.com and sign up
2. Connect your GitHub account

### 2.2 Import Project

1. Click **Add New** → **Project**
2. Import your GitHub repository
3. Configure:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `OpenCongressWebApp/frontend`
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `.next` (default)

### 2.3 Configure Environment Variables

Add this environment variable:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://<your-railway-api-domain>/api/v1` |

Example: `https://congresstrack-api.up.railway.app/api/v1`

### 2.4 Deploy

Click **Deploy**. Vercel will:
1. Install dependencies (`npm ci`)
2. Build the Next.js app
3. Deploy to edge CDN
4. Provide a `.vercel.app` URL

### 2.5 Custom Domain (Optional)

1. Go to **Settings** → **Domains**
2. Add your domain: `congresstrack.org`
3. Configure DNS:
   - **A Record**: `76.76.21.21`
   - **CNAME**: `cname.vercel-dns.com`

---

## Step 3: GitHub Actions Setup

### 3.1 Get Railway Token

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and get token
railway login

# View your token
railway whoami
```

Or get it from Railway Dashboard → Account Settings → Tokens → Create Token

### 3.2 Get Vercel Credentials

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Link project (run from frontend directory)
cd frontend
vercel link

# This creates .vercel/project.json with:
# - orgId (VERCEL_ORG_ID)
# - projectId (VERCEL_PROJECT_ID)
cat .vercel/project.json
```

Create a Vercel token:
1. Go to https://vercel.com/account/tokens
2. Create new token with appropriate scope

### 3.3 Add GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**

Add these secrets:

| Secret Name | Value | How to Get |
|-------------|-------|------------|
| `RAILWAY_TOKEN` | Railway API token | Railway Dashboard → Tokens |
| `VERCEL_TOKEN` | Vercel API token | Vercel Dashboard → Tokens |
| `VERCEL_ORG_ID` | Your Vercel org/user ID | `.vercel/project.json` → `orgId` |
| `VERCEL_PROJECT_ID` | Your Vercel project ID | `.vercel/project.json` → `projectId` |

### 3.4 Verify Workflow

The workflow file is at `.github/workflows/deploy.yml`. It will:

1. **On Pull Request**: Run tests only (no deployment)
2. **On Push to main**: Run tests → Deploy backend → Health check → Deploy frontend

---

## Step 4: Verify Deployment

### 4.1 Check Backend Health

```bash
curl https://<your-railway-domain>/api/health/
```

Expected response:
```json
{
  "status": "healthy",
  "database": "healthy",
  "redis": "healthy"
}
```

### 4.2 Check API Documentation

Visit: `https://<your-railway-domain>/api/v1/schema/swagger-ui/`

### 4.3 Check Frontend

Visit your Vercel URL and verify:
- Page loads correctly
- API calls work (check Network tab)
- No CORS errors in console

---

## Troubleshooting

### Backend won't start

1. Check Railway logs: Service → **Deployments** → **View Logs**
2. Verify environment variables are set
3. Ensure DATABASE_URL and REDIS_URL are linked

### Database connection errors

```bash
# Test connection
railway run --service congresstrack-api python manage.py dbshell
```

### CORS errors on frontend

1. Verify `CORS_ALLOWED_ORIGINS` in `production.py` includes your Vercel domain
2. The regex `r"^https://.*\.vercel\.app$"` allows all Vercel preview URLs
3. Add your production domain explicitly

### Celery tasks not running

1. Check Celery worker logs in Railway
2. Verify REDIS_URL is set correctly
3. Ensure queues match: `sync`, `ai`, `notifications`

### Health check failing in CI/CD

1. Increase `MAX_ATTEMPTS` in workflow if needed
2. Check if migrations are running successfully
3. Verify the health endpoint path: `/api/health/`

---

## Cost Estimation

### Railway (Backend)

| Service | Estimated Cost |
|---------|---------------|
| PostgreSQL | ~$5-15/month |
| Redis | ~$5-10/month |
| Django API | ~$5-20/month |
| Celery Worker | ~$5-15/month |
| Celery Beat | ~$5/month |
| **Total** | **~$25-65/month** |

Railway offers $5 free credit monthly and usage-based pricing.

### Vercel (Frontend)

| Plan | Cost | Includes |
|------|------|----------|
| Hobby | Free | Personal projects, 100GB bandwidth |
| Pro | $20/month | Team features, more bandwidth |

For most projects, the Hobby plan is sufficient.

---

## Security Checklist

- [ ] `SECRET_KEY` is unique and secure (not the default)
- [ ] `JWT_SECRET_KEY` is different from `SECRET_KEY`
- [ ] `DEBUG=False` in production (set via `DJANGO_SETTINGS_MODULE`)
- [ ] `ALLOWED_HOSTS` only includes your domains
- [ ] Database credentials are not in code
- [ ] API keys are stored as environment variables
- [ ] HTTPS is enforced (automatic on Railway/Vercel)
- [ ] CORS only allows your frontend domains

---

## Useful Commands

```bash
# Railway CLI
railway login                    # Authenticate
railway link                     # Link to project
railway up                       # Deploy current directory
railway logs                     # View logs
railway run <command>            # Run command in service

# Vercel CLI
vercel login                     # Authenticate
vercel link                      # Link to project
vercel                          # Deploy preview
vercel --prod                   # Deploy production
vercel logs                     # View logs

# Django management (via Railway)
railway run --service congresstrack-api python manage.py migrate
railway run --service congresstrack-api python manage.py createsuperuser
railway run --service congresstrack-api python manage.py collectstatic
railway run --service congresstrack-api python manage.py shell
```
