# CLAUDE.md — SEO Agent

## Project Overview
Local AI SEO agent for Free Mind Consultancy. Connects to GA4 and Search Console APIs, analyzes performance, generates reports, and prepares website optimizations. Runs entirely on the local machine — never auto-deploys.

## Tech Stack
- Python 3.10+
- Google Analytics Data API (GA4)
- Google Search Console API
- pandas, numpy for data processing
- PyYAML for configuration
- python-dotenv for environment variables

## Key Commands
```bash
pip install -r requirements.txt          # Install dependencies
python scripts/run_pipeline.py           # Run full pipeline
python scripts/fetch_ga4.py              # Fetch GA4 data only
python scripts/fetch_search_console.py   # Fetch Search Console data only
python scripts/generate_monthly_report.py # Generate monthly report
python -m pytest tests/                  # Run tests
```

## Project Rules
- NEVER deploy or push changes to production automatically
- ALWAYS back up website files before modifying them (save to `backups/`)
- ALWAYS log script actions to `logs/`
- Store raw API data in `data/` with date-stamped filenames
- Store generated content in `output/` — never write directly to `website/`
- Use `config/settings.yaml` for all configurable values — no hardcoded constants
- Credentials live in `credentials/` and are gitignored — never commit them
- Prompts for AI analysis live in `prompts/` — keep them versioned and modular

## File Naming Conventions
- Data files: `{source}_{YYYY-MM-DD}.csv` (e.g., `ga4_2026-06-28.csv`)
- Reports: `{type}_{YYYY-MM}.md` (e.g., `monthly_2026-06.md`)
- Backups: `{filename}_{YYYY-MM-DD_HH-MM-SS}.bak`
- Logs: `{script}_{YYYY-MM-DD}.log`

## Environment Variables (defined in .env)
- `GA4_PROPERTY_ID` — Google Analytics 4 property ID
- `SEARCH_CONSOLE_PROPERTY` — Search Console property URL
- `SERVICE_ACCOUNT_FILE` — Path to service account JSON
- `WEBSITE_ROOT` — Path to website source files
