# PHASE 1 — Async PostgreSQL connectivity
# Create an async SQLAlchemy engine using the validated DATABASE_URL.
# Create an async session factory; make construction explicit and reusable.
# Provide an async session dependency/context manager that always closes sessions.
# Add an async read-only connectivity check using SELECT 1 and a bounded timeout.
# Dispose of the engine on application shutdown.
# Do not create a database, extension, tables or run migrations in application startup:
# the owner performs every database change manually.
# Acceptance: reachable DB passes; unavailable DB fails cleanly without secrets.
