# PHASE 1 — Optional real database integration test
# Make this test explicitly opt-in through a dedicated test database URL.
# Check successful read-only connectivity and cleanup against a database you created.
# Skip clearly when the test URL is absent; never create/drop tables or databases.
# Include a separately mocked unit test for failure/timeout without real network access.
