# Manual database setup

You manage the database manually. No database connection, schema, migration, or SQL script has been created or run in phase 1.

## Prerequisites

1. Install PostgreSQL locally or provision an existing PostgreSQL server without Docker.
2. Install the `pgvector` extension compatible with that PostgreSQL instance. On managed services, check that your provider supports and permits it.
3. Create a dedicated database and a restricted application role using your preferred administration tool, such as pgAdmin or `psql`.
4. Enable the `vector` extension in that database using an account with the required privileges. Confirm the extension is available and enabled using your administration tool.
5. Keep your hostname, port, database name, username and password private. Later we will supply an environment template; never commit credentials.

The application connection settings, vector dimensions, schema, indexes and manual migration instructions will be specified when their models are implemented. Do not create speculative tables now. Future migrations will be provided for you to review and run yourself, rather than automatically modifying your database.

## Planned data

Corpus versions and documents, parsed blocks and chunks, embeddings, ingestion jobs, conversations, cache entries, datasets and experiment results. BM25 indexes are separate persisted artifacts. Exact schema is pending implementation.
