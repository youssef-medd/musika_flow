# HummingID Backend

FastAPI gateway — entry point of the HummingID platform.

## Quickstart

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements-dev.txt
cp .env.example .env

uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the OpenAPI UI.

## Health check

```bash
curl http://127.0.0.1:8000/api/v1/health
```

## Tests

```bash
pytest
```

## Layout

```
backend/
  app/
    api/routes/      # HTTP routes (health, jobs, results, ...)
    core/            # config, security, logging
    schemas/         # Pydantic request/response models
    services/        # business logic (audio, user, history)
    main.py          # FastAPI factory
  tests/
```
