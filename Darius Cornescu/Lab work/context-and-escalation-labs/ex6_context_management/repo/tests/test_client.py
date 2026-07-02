"""Tests for the live HTTP client. These read the policy from config.settings,
which is the authoritative source for the retry limit (not the legacy client)."""

from client.http import HttpClient
from config import settings


def test_client_uses_config_retry_limit():
	client = HttpClient()
	# The client's retry budget must come from config, whatever it is set to.
	assert client.max_retries == settings.MAX_RETRIES


def test_retry_predicate():
	client = HttpClient()
	assert client._should_retry(429) is True
	assert client._should_retry(503) is True
	assert client._should_retry(404) is False
	assert client._should_retry(200) is False
