# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Quiz Taxons is a Django web application that helps users learn biological taxonomy (species identification) for the CNBs (Cercles Naturalistes de Belgique) Naturalist Training program. Users are shown Google Images of a species and must identify it by name or from multiple-choice options.

## Development Commands

All commands run inside the Docker container:

```bash
# Start the development environment
docker compose up -d

# Run Django management commands
docker compose exec -T quiz uv run python manage.py migrate
docker compose exec -T quiz uv run python manage.py import_taxons   # Import species from taxons.pdf
docker compose exec -T quiz uv run python manage.py createsuperadmin

# Run tests
docker compose exec -T quiz uv run python manage.py test

# Install/sync dependencies (uses uv, not pip)
docker compose exec quiz uv sync
```

App is at `http://localhost:8000`, admin at `http://localhost:8000/admin`.

## Architecture

**Single Django app** (`taxons/`) with HTMX for partial page updates — no SPA framework.

### Models (`taxons/models.py`)
- **Taxon** — species data (taxonomy hierarchy + vernacular name + identifying features)
- **SearchResult** — cached Google Custom Search image results per taxon
- **UserScore** — per-session score per taxon; compound index on `(session_id, score)` drives taxon selection

### Quiz flow
1. `index()` selects the taxon with the lowest score for the current session (unseen taxons score 0 by default)
2. `render_images_grid()` (HTMX) calls Google Custom Search API and renders images; subsequent calls add more images and deduct points
3. `show_propositions()` (HTMX) generates 4 multiple-choice options by finding taxons at the same taxonomic level (genus → family → order → class → phylum → random); deducts points
4. `render_result()` (HTMX) checks the answer, updates `UserScore`, and returns feedback

### Scoring
- Each question starts at 10 points
- -5 for requesting multiple-choice propositions
- -2 per additional image batch (max 4 total)
- Correct: +current_score to the taxon's UserScore
- Wrong: -5 from the guessed taxon's score (minimum -1)

### Session tracking
Sessions use a `session_id` cookie set to `secrets.token_urlsafe()` — no login required.

## Key Files

| File | Purpose |
|------|---------|
| `taxons/views.py` | All quiz logic and HTMX endpoints |
| `taxons/models.py` | Taxon, SearchResult, UserScore |
| `taxons/urls.py` | URL routes for all HTMX endpoints |
| `taxons/management/commands/import_taxons.py` | Parses `taxons.pdf` with pdfplumber → `taxons.csv` → DB |
| `quiz/settings.py` | Django settings (WhiteNoise, django-htmx, PostgreSQL) |

## Environment Variables

Required in `.env` (dev) or `prod.env` (prod):

```
SECRET_KEY
DEBUG                    # 1 for dev, 0 for prod
ALLOWED_HOSTS
GOOGLE_SEARCH_ENGINE     # Google Custom Search engine ID
GOOGLE_SEARCH_API_KEY
POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_HOST
```

Production also needs `CSRF_TRUSTED_ORIGINS` and `NGROK_AUTHTOKEN`.

## Tech Stack

- Python 3.11, Django 5.2, PostgreSQL 17
- HTMX (partial updates) + Alpine.js (UI interactivity)
- WhiteNoise (static files), Gunicorn (prod WSGI)
- uv (package manager — do not use pip directly)
- Docker Compose for both dev and prod environments
