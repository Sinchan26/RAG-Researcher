# PHASE 1 — Application settings
# Implement a Pydantic settings class that reads environment variables and .env.
# Add typed settings matching .env.example; give safe defaults to non-secret values.
# Treat model-provider and LangSmith credentials as optional in this phase.
# Validate port range and required database settings with understandable errors.
# Never log passwords, API keys, or the full database URL.
# Provide a reusable settings accessor; keep imports and tests side-effect free.
# Acceptance: environment overrides work and invalid required settings are reported.
