# RAG Researcher

An Agentic RAG research workbench for the Gita. See [spec.md](spec.md).

## Current status

Phase 1 provides a FastAPI foundation, configuration, read-only PostgreSQL readiness
check and a Streamlit shell. Ingestion, chat, LangSmith tracing and experiments are
planned for later phases. No book content, indexes, datasets or results are included.

## Requirements and manual database setup

Use Python 3.11 or newer and PostgreSQL. Install pgvector and create the database and
role yourself as described in [db/README.md](db/README.md). The app does not create or
modify database objects. Database configuration is optional for startup; readiness
returns 503 until the configured database is reachable.

## Local setup (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Edit `.env` with your own asyncpg database URL. URL-encode special characters in
passwords. Do not commit `.env`. From the repository root, start the API:

```powershell
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

In a second activated terminal, run:

```powershell
streamlit run apps/ui/app.py
```

API health checks: `http://127.0.0.1:8000/health/live` and
`http://127.0.0.1:8000/health/ready`. Local setup does not provide authentication;
do not expose this development service to an untrusted network.

```powershell
pytest
```

The optional database integration test uses `TEST_DATABASE_URL` and otherwise skips.
It only performs a read-only query; use a database you have already created.

## Corpus

Keep your supplied Bhagavad-gita As It Is PDF locally under `data/raw/`; it is not
included in this repository. It reports copying restrictions. Verify authorized
extraction before the ingestion phase. Preserve page and edition provenance.
