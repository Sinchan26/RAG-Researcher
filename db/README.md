# Manual database setup

You create and administer PostgreSQL and pgvector. No application startup, test or
script in this phase creates a database, enables extensions, or changes schema.

1. Install PostgreSQL and a pgvector build compatible with your PostgreSQL version.
   On a managed service, first check provider support and extension permissions.
2. In pgAdmin or `psql`, create a dedicated database and an application role. Grant
   the role permission to connect to that database. Use your own names/passwords.
3. Connect to the new database as a suitably privileged account, enable the `vector`
   extension, then confirm it appears in the installed extensions list.
4. Copy `.env.example` to `.env`; set `DATABASE_URL` to the connection for your role
   using the `postgresql+asyncpg` driver. URL-encode special password characters.
5. Start the API and visit `/health/ready`. A 200 means the read-only `SELECT 1`
   succeeded; 503 means the database is missing, unavailable or misconfigured.

No tables or schema migrations are required in Phase 1. Later schema SQL and
migration instructions will be supplied in this folder for you to review and run.
Keep credentials private; `.env` is ignored by git.
