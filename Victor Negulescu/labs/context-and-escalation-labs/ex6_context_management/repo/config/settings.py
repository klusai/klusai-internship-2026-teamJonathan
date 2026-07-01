"""Central configuration for the API client.

These values are read at import time and shared across the app. The HTTP client in
client/http.py imports from here — this module is the single source of truth for the
retry policy. (The legacy/ client predates this module and is no longer wired in.)
"""

import os

# --- Networking -----------------------------------------------------------------
BASE_URL = os.environ.get("API_BASE_URL", "https://api.example.com")
CONNECT_TIMEOUT_SECONDS = 5.0
READ_TIMEOUT_SECONDS = 30.0

# --- Retry policy ---------------------------------------------------------------
# How many times the HTTP client retries a transient failure (429 / 5xx) before
# giving up. This is THE effective retry limit for the app.
MAX_RETRIES = 5
RETRY_BACKOFF_BASE_SECONDS = 0.5
RETRY_JITTER_SECONDS = 0.25

# --- Auth -----------------------------------------------------------------------
TOKEN_TTL_SECONDS = 3600
REFRESH_SKEW_SECONDS = 60

# --- Feature flags --------------------------------------------------------------
ENABLE_HTTP2 = True
ENABLE_REQUEST_LOGGING = False
