# OpenCongress

An open source platform for tracking the U.S. Congress. Browse members, bills, votes, and committee activity — all sourced from official government data.

**Live site:** [opencongress.app](https://opencongress.app)

## Features

- **Member profiles** — All 535 members of Congress with party, state, committee assignments, and voting records
- **Hemicycle visualization** — Interactive chamber seating charts for House and Senate with vote overlays
- **Bill tracker** — Browse legislation with status, summaries, and sponsor info
- **Roll call votes** — Detailed vote breakdowns by party, state, and individual member
- **District maps** — Interactive maps of congressional districts using d3-geo
- **Weekly summaries** — AI-enriched summaries of congressional activity
- **Calendar** — Upcoming floor activity and scheduled votes
- **Member search** — Find your representatives by ZIP code

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16, React 19, Tailwind CSS v4, shadcn/ui |
| **Backend** | Django 5, Django REST Framework, PostgreSQL, Redis |
| **Task Queue** | Celery + Celery Beat |
| **State** | Zustand, TanStack React Query |
| **Maps** | d3-geo, d3-zoom, TopoJSON |
| **Auth** | Auth.js (Next.js) + JWT (Django) |
| **Data Source** | Congress.gov API (free, public domain) |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker (for PostgreSQL and Redis)
- A free Congress.gov API key from [api.data.gov/signup](https://api.data.gov/signup/)

### Setup

```bash
# Clone the repo
git clone https://github.com/PierreParienteDimitrov/OpenCongress.git
cd OpenCongress

# Copy environment template and add your API key
cp .env.example .env
# Edit .env and set CONGRESS_API_KEY=your-key-here

# Start PostgreSQL and Redis
docker compose up -d db redis

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements/development.txt
python manage.py migrate

# Seed data (uses Congress.gov API)
python manage.py seed_members
python manage.py seed_committees
python manage.py seed_bills --congress=119 --limit=50
python manage.py seed_votes --congress=119 --limit=50
python manage.py link_votes_to_bills
python manage.py generate_seats

# Start the backend
make run

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the app.

## Project Structure

```
OpenCongress/
├── backend/                  # Django API
│   ├── apps/
│   │   ├── congress/         # Core data: members, bills, votes, committees
│   │   ├── content/          # Weekly summaries, educational content
│   │   ├── jobs/             # Data sync and scheduling
│   │   ├── users/            # Authentication and user profiles
│   │   ├── analytics/        # Usage analytics
│   │   └── notifications/    # User notifications
│   ├── config/
│   │   └── settings/         # Django settings (base, dev, prod, test)
│   └── requirements/         # Python dependencies
├── frontend/                 # Next.js app
│   └── src/
│       ├── app/              # Pages (App Router)
│       ├── components/       # React components
│       │   ├── ui/           # shadcn/ui primitives
│       │   ├── hemicycle/    # Chamber visualizations
│       │   ├── map/          # District maps
│       │   └── ...
│       ├── lib/              # Utilities, API client, stores
│       └── types/            # TypeScript interfaces
├── docker-compose.yml        # Local dev infrastructure
└── .env.example              # Environment variable template
```

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and guidelines.

Good places to start:
- Issues labeled [`good first issue`](https://github.com/PierreParienteDimitrov/OpenCongress/labels/good%20first%20issue)
- Issues labeled [`help wanted`](https://github.com/PierreParienteDimitrov/OpenCongress/labels/help%20wanted)

## Data Sources

All congressional data comes from official U.S. government sources and is in the public domain:

- [Congress.gov API](https://api.congress.gov/) — Members, bills, votes, committees
- [Senate.gov](https://www.senate.gov/) — Senate vote details
- [theunitedstates.io](https://theunitedstates.io/) — Member social media accounts

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE) (AGPL-3.0).

This means you can freely use, modify, and distribute this software, but if you run a modified version as a network service, you must make your source code available to users of that service.

For commercial licensing options, please contact the maintainers.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.
