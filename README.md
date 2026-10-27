# RAG Researcher

Agentic RAG research workbench for Bhagavad-gita As It Is. The complete design is in [spec.md](spec.md).

## Phase 1: scaffold only

This branch establishes the folder and file layout. Application, tests, configuration files, jobs and database migrations are placeholders; nothing has been implemented or ingested. No installation, run, database migration, evaluation, or benchmark command is available yet.

## Corpus

Use your local copy of the supplied *Bhagavad-gita As It Is* PDF in `data/raw/`. Do not commit or redistribute the PDF or extracted book content; check your rights and the document permissions before extraction or publication. The supplied file reports copy restrictions, so ingestion feasibility requires checking authorized extraction in the next phase. The parser must preserve chapter, verse, translation, purport and PDF page provenance where the document structure permits; it must never fabricate structure.

A corpus manifest, golden dataset, indexes and benchmark results are not yet created. Keep the PDF unchanged so its checksum can identify the corpus version.

## Manual database preparation

See [db/README.md](db/README.md). You create and administer PostgreSQL and pgvector yourself; no database scripts or migrations are executed in this phase.

## Planned folders

- `apps/`: FastAPI and Streamlit entry points and routes.
- `src/`: ingestion, retrieval, agent, caching, evaluation, observability and storage modules.
- `workers/`: background ingestion and evaluation jobs.
- `db/`: manual setup guidance and future migrations.
- `datasets/`, `configs/`: future corpus metadata and experiments.
- `data/`: local-only source and generated artifacts.
- `tests/`: placeholders for future meaningful tests.

The planned architecture and milestones are specified in `spec.md`; placeholders are not operational features.
