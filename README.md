# SEO Agent — Free Mind Consultancy

A local AI-powered SEO agent that connects to Google Analytics 4 and Google Search Console, analyzes SEO performance, generates reports, and optimizes website files — all running on your machine.

## What This Does

- **Fetches data** from GA4 and Search Console APIs
- **Analyzes** keyword rankings, page performance, technical SEO health
- **Generates** monthly/weekly reports with actionable recommendations
- **Optimizes** content, internal links, schema markup, sitemaps, and images
- **Stores** historical data for trend analysis
- **Never deploys** — all changes are local, reviewed by you before going live

## Quick Start

### 1. Install Dependencies

```bash
cd 10_seo_agent
pip install -r requirements.txt
```

### 2. Set Up Credentials

1. Create a Google Cloud project
2. Enable the **Google Analytics Data API** and **Search Console API**
3. Create a service account and download the JSON key
4. Save it as `credentials/service-account.json`
5. Copy `.env.example` to `.env` and fill in your property IDs

```bash
cp .env.example .env
cp credentials/service-account.json.example credentials/service-account.json
```

### 3. Configure

Edit these files for your website:

- `config/settings.yaml` — API property IDs, date ranges, thresholds
- `config/website_config.yaml` — your site URL, sitemap location, page structure
- `config/business_goals.md` — what you're optimizing for
- `config/seo_rules.md` — SEO constraints and rules to follow

### 4. Link Your Website

Symlink or copy your website source into the `website/` directory:

```bash
# Example: symlink your website folder
mklink /D website\src "D:\Free Mind Website\freemind-website"
```

### 5. Run the Pipeline

```bash
python scripts/run_pipeline.py
```

Or run individual scripts:

```bash
python scripts/fetch_ga4.py
python scripts/fetch_search_console.py
python scripts/combine_data.py
python scripts/generate_monthly_report.py
```

## Folder Structure

| Folder | Purpose |
|---|---|
| `credentials/` | Google API service account keys (gitignored) |
| `config/` | Settings, goals, rules, website config |
| `website/` | Your website source files (symlinked or copied) |
| `data/` | Raw and processed API data |
| `reports/` | Generated reports (monthly, weekly, audits) |
| `logs/` | Script execution logs |
| `prompts/` | AI prompt templates for analysis and generation |
| `scripts/` | All Python scripts |
| `output/` | Generated content, recommendations, metadata |
| `backups/` | Website file backups before modifications |
| `tests/` | Test suite |

## Safety

- No automatic deployments — ever
- Website files are backed up before any modification
- All changes go to `output/` for your review
- Logs track every action taken

## Requirements

- Python 3.10+
- Google Cloud service account with GA4 and Search Console access
- Your website source files accessible locally
