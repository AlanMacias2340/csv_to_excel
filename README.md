# CSV to Excel - FastAPI Base Project

A minimal FastAPI project skeleton using Uvicorn for development.

## Quickstart

- Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

- Install dependencies:

```bash
pip install -r requirements.txt
```

- Run the app (ensure Python imports see `src`):

```bash
PYTHONPATH=src uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Health check: GET http://127.0.0.1:8000/health
- Example: GET http://127.0.0.1:8000/api/v1/hello
- Upload page: GET http://127.0.0.1:8000/api/v1/upload (web UI for converting CSV to Excel). The page supports selecting multiple CSV files; when multiple files are uploaded the server returns a ZIP archive of converted XLSX files. The UI now uses a Jinja2 template and serves modern static assets (CSS, JS) from `/static`.

Image conversion: POST `/api/v1/convert-image` accepts PNG uploads and returns a single `.webp` (for one image) or a ZIP archive of `.webp` files (for multiple images). POST `/api/v1/convert-webp` accepts WebP uploads and returns PNG files. The web UI includes three tabs: CSV → Excel, PNG → WebP, and WebP → PNG.

## Tests

Run tests with:

```bash
PYTHONPATH=src pytest -q
```
