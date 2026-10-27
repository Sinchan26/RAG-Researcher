# PHASE 1 — Health endpoints
# Create an APIRouter with GET /health/live and GET /health/ready.
# Liveness checks only that the API process responds; it must not query PostgreSQL.
# Readiness performs the bounded read-only database check from storage/database.py.
# Return HTTP 200 when ready and HTTP 503 when the database check fails/times out.
# Return a small JSON body with status; never expose connection details.
# Do not check models, indexes or LangSmith in Phase 1 because they do not exist yet.
# Acceptance: test healthy and unavailable database paths plus independent liveness.
