# Clarifresh — Setup Instructions

## What's already done
- Full Python/FastAPI backend (20 API endpoints)
- React/Vite dashboard frontend
- PostgreSQL schema (7 tables) via Alembic migrations
- Supabase database connected (host + password in `.env`)
- Apify integration for TikTok + Instagram scraping (wired up, needs token)
- Claude API integration for sentiment analysis + weekly insights (wired up, needs key)
- Competitor seed script with 10 companies × 2 platforms

---

## Your job: add the API keys (Step 2)

Open `.env` in the project root and fill in the two blank values:

```
APIFY_API_TOKEN=         ← your token from console.apify.com
ANTHROPIC_API_KEY=       ← your key from console.anthropic.com
```

Everything else in `.env` is already set.

---

## Then run these commands (in order)

Make sure you're in the project root directory.

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Create the database tables
```bash
python -m alembic upgrade head
```

### 3. Seed the competitors
```bash
python seeds/seed_competitors.py
```

> Note: The handles in the seed script are best-guess based on public profiles.
> Before triggering a live ingestion, verify each handle exists on TikTok/Instagram.
> If a handle is wrong, update it directly in the Supabase table (competitors) or re-run
> the seed script after editing seeds/seed_competitors.py.

### 4. Start the backend
```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Start the frontend (separate terminal)
```bash
cd dashboard
npm install
npm run dev
```

Frontend runs at http://localhost:3001
Backend API at http://localhost:8000/api/v1

---

## Trigger your first data pull

Once both servers are running and keys are set:

1. Open http://localhost:3001
2. Click **"Trigger Ingest"** in the top bar
3. This kicks off Apify scraping for all 10 competitors on TikTok + Instagram
4. After it completes (~5 min), the dashboard will populate with real data

---

## Apify actor notes

The backend uses two Apify actors:
- TikTok: `clockworks~tiktok-scraper`
- Instagram: `apify~instagram-scraper`

Make sure your Apify account has access to both. You may need to subscribe to them
in the Apify Store (both have free tiers).

---

## Architecture recap

```
Backend (FastAPI)
├── /api/v1/competitors   — CRUD for tracked companies
├── /api/v1/posts         — scraped social posts
├── /api/v1/sentiment     — Claude-powered sentiment per post
├── /api/v1/insights      — weekly AI-generated summaries
├── /api/v1/analytics     — rankings, engagement charts
└── /api/v1/ingestion     — trigger + monitor Apify runs

Scheduler (APScheduler)
├── Daily 6am UTC         — scrape all competitors
├── Sunday 2am UTC        — generate weekly insights
└── Every 6h              — purge posts older than 14 days

Database (Supabase PostgreSQL)
└── competitors, social_posts, comments, post_metrics,
    sentiment_results, insights, ingestion_jobs
```
