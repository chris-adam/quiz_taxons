# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Quiz Taxons is a Django web application that helps users learn biological taxonomy (species identification) for the CNBs (Cercles Naturalistes de Belgique) Naturalist Training program. Users are shown photos (or hear bird songs) of a species and must identify it by name or from multiple-choice options.

## Development Commands

All commands run inside the Docker container:

```bash
# Start the development environment
docker compose up -d

# Run Django management commands
docker compose exec -T quiz uv run python manage.py migrate
docker compose exec -T quiz uv run python manage.py import_taxons   # Import species from nature.csv / rando.csv (or .pdf if CSV absent)
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
- **Taxon** — species data (taxonomy hierarchy + vernacular name + identifying features); has `dataset` (e.g. `"nature"`, `"rando"`) and `category` (e.g. `"Oiseaux"`, `"Plantes"`) fields used for filtering
- **SearchResult** — cached media results per taxon: iNaturalist photos (non-birds) or Xeno-canto MP3 recordings (Aves)
- **UserScore** — per-session score per taxon; compound index on `(session_id, score)` drives taxon selection

### Quiz flow
1. `index()` — if no `dataset` param, shows the dataset selector widget (lists all distinct datasets). Once a dataset is chosen, resets the session if the dataset or category changed, then selects the lowest-scoring taxon via `get_next_taxon()`. Multiple-choice propositions and the answer dropdown are pre-generated here (filtered to the active dataset/category) and embedded in the page.
2. `render_images_grid()` (HTMX) fetches and renders media: iNaturalist photos for non-birds, Xeno-canto songs (MP3) for Aves; subsequent POST calls add more images and deduct points
3. `show_propositions()` (HTMX) — only deducts 5 points from the session score (propositions are already in the DOM from `index()`)
4. `render_result()` (HTMX) checks the answer, updates `UserScore`, and returns feedback + updated score portlet
5. `skip_question()` (HTMX) — clears the current question from the session and triggers a full page refresh

### Category filtering
Within a dataset, users can further filter by category (e.g. Oiseaux, Plantes, Insectes). The active category is preserved as a `category` query param and stored in the session. Switching dataset or category resets the current question state.

### Scoring
- Each question starts at 10 points
- -5 for requesting multiple-choice propositions
- -2 per additional image batch (max 4 total)
- Correct: +current_score to the taxon's UserScore
- Wrong: -5 from the guessed taxon's score (minimum -1)

### Session tracking
Sessions use Django's session framework; `user_session_id` is stored in the session (not a raw cookie). Session keys `current_dataset` and `current_category` track the active filter state and trigger resets when they change.

## Key Files

| File | Purpose |
|------|---------|
| `taxons/views.py` | All quiz logic and HTMX endpoints |
| `taxons/models.py` | Taxon, SearchResult, UserScore |
| `taxons/urls.py` | URL routes for all HTMX endpoints |
| `taxons/management/commands/import_taxons.py` | Iterates `DATASETS = ["nature", "rando"]`; for each, reads `<dataset>.csv` (or extracts from `<dataset>.pdf` via pdfplumber) → DB |
| `nature.csv` / `rando.csv` | Species data for each dataset |
| `quiz/settings.py` | Django settings (WhiteNoise, django-htmx, PostgreSQL) |

## Environment Variables

Required in `.env` (dev) or `prod.env` (prod):

```
SECRET_KEY
DEBUG                    # 1 for dev, 0 for prod
ALLOWED_HOSTS
XENOCANTO_API_KEY        # Free key from xeno-canto.org (required for bird songs)
POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_HOST
```

Production also needs `CSRF_TRUSTED_ORIGINS` and `NGROK_AUTHTOKEN`.

## Tech Stack

- Python 3.11, Django 5.2, PostgreSQL 17
- HTMX (partial updates) + Alpine.js (UI interactivity)
- WhiteNoise (static files), Gunicorn (prod WSGI)
- uv (package manager — do not use pip directly)
- Docker Compose for both dev and prod environments
