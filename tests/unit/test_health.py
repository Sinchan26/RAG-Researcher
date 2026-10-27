# PHASE 1 — Health route tests
# Use a FastAPI test client and override/mock the DB readiness check.
# Verify /health/live returns 200 even when the DB check would fail.
# Verify /health/ready returns 200 on success and 503 on failure/timeout.
# Verify error responses omit database credentials.
# Tests should not require PostgreSQL or any external API.
