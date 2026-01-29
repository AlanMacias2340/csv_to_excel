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

## Tests

Run tests with:

```bash
PYTHONPATH=src pytest -q
```
