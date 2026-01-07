# BizListingScraper

Automated web scraper for business-for-sale listing sites with daily updates, deduplication, and a web dashboard. Currently scraping **7,070 listings** from 7 sources for Michigan and Connecticut.

## Features

- 🕷️ **Multi-Source Scraping** - 7 sources: BizQuest, BizBuySell, BusinessesForSale, Transworld, Synergy BB, SMB Deal Hunter, FCBB
- 🔄 **Smart Deduplication** - Only stores new/changed listings
- 📊 **Change Tracking** - Logs when prices change, listings removed
- 🌐 **REST API** - FastAPI backend for data access
- 📱 **Web Dashboard** - React frontend to browse listings with filters
- 💰 **Financial Data** - Asking Price, Cash Flow, Revenue, EBITDA
- 📍 **Geographic Filters** - Michigan and Connecticut focus
- 📥 **Excel Export** - Export filtered listings as .xlsx with formatting

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (fast Python package manager)
- Node.js 18+
- PostgreSQL (or [Neon](https://neon.tech) free account)

### Backend Setup

```bash
cd backend

# Install dependencies with uv (fast!)
uv sync

# Install Playwright browser
uv run playwright install chromium

# Set up environment
cp ../.env.example .env
# Edit .env with your DATABASE_URL

# Run database migrations
psql $DATABASE_URL < migrations/001_initial.sql

# Test the scraper
uv run python -m scraper.bizbuysell

# Start API server
uv run uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

### Run Scraper Manually

```bash
cd backend
uv run python -m scraper.main
```

## Project Structure

```
BizListingScraper/
├── backend/
│   ├── app/              # FastAPI application
│   │   ├── main.py       # Entry point
│   │   ├── routers/      # API endpoints
│   │   └── models.py     # Pydantic models
│   ├── scraper/          # Scraping logic
│   │   ├── main.py       # Scraper entry point
│   │   ├── bizbuysell.py # BizBuySell scraper
│   │   ├── bizquest.py   # BizQuest scraper
│   │   ├── businessesforsale.py # BusinessesForSale
│   │   ├── transworld.py # Transworld scraper
│   │   ├── fcbb.py       # FCBB scraper
│   │   ├── synergybb.py  # Synergy BB scraper
│   │   ├── smbdealhunter.py # SMB Deal Hunter
│   │   ├── murphybusiness.py # Murphy Business
│   │   └── upsert.py     # Database logic
│   └── migrations/       # SQL schema
├── frontend/             # React dashboard
└── .github/workflows/    # GitHub Actions
```

## Configuration

See `.env.example` for all configuration options.

Key settings:
- `DATABASE_URL` - PostgreSQL connection string
- `TARGET_STATE` - State to scrape (e.g., "MI")
- `MAX_PAGES_PER_SCRAPE` - Maximum pages per run

## Automated Daily Scraping

The scraper runs automatically via GitHub Actions **daily at 6 AM UTC (1 AM EST)**.

**MI and CT run in parallel** on separate GitHub runners:
- Each runner has a **different IP address**
- This avoids rate limiting issues (sites see two different IPs)
- Both complete in ~15-20 minutes

### Manual Trigger

1. Go to **Actions → Daily Scrape → Run workflow**
2. Choose: `both`, `MI`, or `CT`
3. Click **Run workflow**

### Environment Variable

The `SCRAPE_STATE` env var controls which state to scrape:
- `MI` - Michigan only
- `CT` - Connecticut only

## Known Limitations

| Site | Issue | Impact |
|------|-------|--------|
| **BizBuySell** | 403 rate limit after ~30 pages | Can only scrape one full state per run |
| **BusinessesForSale** | Cloudflare blocks pagination | Only ~25 listings per state (page 1) |
| **DealStream** | CAPTCHA slider | Not automated |
| **BusinessBroker.net** | Aggressive CAPTCHA | Not automated |

## Deployment

| Service | Platform | Tier |
|---------|----------|------|
| Database | [Neon](https://neon.tech) | Free |
| Backend | [Render](https://render.com) | Starter ($7/mo) |
| Frontend | [Netlify](https://netlify.com) | Free |
| Automation | GitHub Actions | Free |

See `PROJECT_DOCUMENTATION.md` for detailed deployment guide.

## Documentation

📚 **[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)** - Complete technical documentation including:
- Product Requirements Document (PRD)
- Crawl4AI complete guide
- Database schema design
- API endpoints
- Deployment instructions

## License

MIT
