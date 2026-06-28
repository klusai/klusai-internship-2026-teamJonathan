"""The HTTP client the app actually uses.

It pulls its retry policy from config.settings — so the real, effective retry limit
is whatever MAX_RETRIES is set to there, not any number hardcoded in this file.
"""

import time

from config import settings


class HttpClient:
	"""Thin wrapper that retries transient failures per the config policy."""

	def __init__(self, base_url: str | None = None):
		self.base_url = base_url or settings.BASE_URL
		# The retry budget comes from config.settings.MAX_RETRIES — single source
		# of truth. Do not hardcode a number here.
		self.max_retries = settings.MAX_RETRIES

	def _should_retry(self, status: int) -> bool:
		return status == 429 or 500 <= status < 600

	def request(self, method: str, path: str) -> dict:
		attempt = 0
		while True:
			status, body = self._send(method, path)
			if not self._should_retry(status) or attempt >= self.max_retries:
				return {"status": status, "body": body, "attempts": attempt + 1}
			backoff = settings.RETRY_BACKOFF_BASE_SECONDS * (2 ** attempt)
			time.sleep(backoff)
			attempt += 1

	def _send(self, method: str, path: str) -> tuple[int, dict]:
		# Placeholder transport — a real client would use httpx/requests here.
		raise NotImplementedError("wire up a transport")
