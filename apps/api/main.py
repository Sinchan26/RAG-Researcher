# PHASE 1 — FastAPI entry point
# Create the FastAPI app and register the health router without adding a /v1 prefix
# to /health/live and /health/ready; future business routes belong under /v1.
# Configure logging and manage engine setup/disposal through app lifespan.
# Add safe, consistent error responses without leaking secrets or stack traces.
# Keep startup independent of a live DB so liveness works while readiness reports 503.
# Do not initialize tables or run migrations; database administration is manual.
# Acceptance: uvicorn can start the app and serve both health routes.
