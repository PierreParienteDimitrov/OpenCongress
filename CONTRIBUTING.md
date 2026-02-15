# Contributing to OpenCongress

Thanks for your interest in contributing! This guide will help you get set up and submit your first pull request.

## Prerequisites

- **Python 3.12+**
- **Node.js 20+**
- **Docker** (for PostgreSQL and Redis)
- **Git**
- A free **Congress.gov API key** — get one at [api.data.gov/signup](https://api.data.gov/signup/)

## Getting Started

### 1. Fork and clone

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR-USERNAME/OpenCongress.git
cd OpenCongress

# Add the upstream remote to stay in sync
git remote add upstream https://github.com/PierreParienteDimitrov/OpenCongress.git
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and set at minimum:
- `CONGRESS_API_KEY` — your free API key from api.data.gov
- `SECRET_KEY` — any random string for local dev

Everything else has working defaults for local development.

### 3. Start infrastructure

```bash
# Start PostgreSQL and Redis containers
docker compose up -d db redis
```

### 4. Set up the backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/development.txt

# Run database migrations
python manage.py migrate
```

### 5. Seed the database

These commands pull data from the Congress.gov API to populate your local database:

```bash
# Required: members and committees
python manage.py seed_members
python manage.py seed_committees

# Recommended: recent bills and votes
python manage.py seed_bills --congress=119 --limit=50
python manage.py seed_votes --congress=119 --limit=50

# Link votes to bills and generate hemicycle seats
python manage.py link_votes_to_bills
python manage.py generate_seats
```

Seeding takes a few minutes depending on your connection. You can adjust `--limit` to get more or less data.

### 6. Start the backend

```bash
# From the backend/ directory
make run
```

This starts the Docker containers (if not already running) and the Django dev server on port 8000.

### 7. Set up the frontend

```bash
# In a new terminal, from the repo root
cd frontend

npm install
npm run dev
```

The frontend runs on [http://localhost:3000](http://localhost:3000).

## Development Workflow

### Creating a branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create your feature branch
git checkout -b feature/your-feature-name
```

### Running checks before committing

**Backend:**

```bash
cd backend
source venv/bin/activate

# Linting
venv/bin/ruff check .
venv/bin/black --check .

# Auto-format
venv/bin/black .

# Type checking
venv/bin/mypy .

# Tests
pytest -v
```

**Frontend:**

```bash
cd frontend

# Linting
npm run lint

# Type checking
npm run typecheck

# Build (catches errors that dev mode doesn't)
npm run build
```

### Submitting a pull request

1. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Open a pull request on GitHub against `main`

3. Fill out the PR template — describe what you changed and why

4. CI will run automatically (linting, type checks, tests, build)

5. A maintainer will review your PR

### CLA (Contributor License Agreement)

On your first PR, the CLA Assistant bot will ask you to sign our [Contributor License Agreement](.github/CLA.md). This is a one-time step that allows us to dual-license the project (AGPL-3.0 open source + commercial).

## Code Style

### Backend (Python)

- **Formatter:** Black (line length 88)
- **Linter:** Ruff
- **Type checker:** mypy
- Run `venv/bin/black .` before committing

### Frontend (TypeScript/React)

- **Linter:** ESLint
- **UI components:** Use shadcn/ui from `@/components/ui/`
- **Styling:** Tailwind CSS v4 (utility classes, no `tailwind.config`)
- **Clickable elements:** Always add `cursor-pointer` class to buttons, links, and interactive items
- **Imports:** Use `@/` path alias (maps to `frontend/src/`)

## Project Architecture

### Backend

- Django REST Framework API at `/api/v1/`
- Settings split: `config/settings/base.py`, `development.py`, `production.py`, `test.py`
- Apps: `congress` (core data), `users` (auth), `jobs` (data sync), `content` (summaries)
- Celery for async tasks (data syncing, AI enrichment)

### Frontend

- Next.js App Router with server-side rendering
- Zustand for client state, TanStack React Query for server state
- shadcn/ui (New York style) for UI primitives
- d3-geo for maps (not react-simple-maps — incompatible with React 19)
- next-themes for dark mode

## Common Tasks

### Adding a new API endpoint

1. Create/update the serializer in `backend/apps/<app>/serializers.py`
2. Create/update the view in `backend/apps/<app>/views.py`
3. Register the route in `backend/apps/<app>/urls.py`
4. Add TypeScript types in `frontend/src/types/`
5. Add the API call in `frontend/src/lib/api.ts`

### Adding a new page

1. Create a directory in `frontend/src/app/<route>/`
2. Add `page.tsx` with your component
3. Add the route to `frontend/src/lib/routes.ts`

### Adding a new shadcn/ui component

```bash
cd frontend
npx shadcn@latest add <component-name>
```

Components are installed to `frontend/src/components/ui/`.

## Getting Help

- **GitHub Issues** — for bugs and feature requests
- **GitHub Discussions** — for questions and ideas

## License

By contributing, you agree that your contributions will be licensed under the [AGPL-3.0 License](LICENSE), and you grant the maintainers the right to also offer your contributions under a commercial license per the [CLA](.github/CLA.md).
