# PHASE 1 — FastAPI dependencies
# Expose the settings and async database session through FastAPI dependency injection.
# Reuse the shared session factory; do not instantiate an engine per request.
# Ensure sessions close even when a request raises an error.
# Do not introduce authentication or corpus authorization as completed features.
# Acceptance: endpoints can request dependencies and tests can override them.
