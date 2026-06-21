"""DEPRECATED legacy client. Kept only for reference; nothing imports this.

This predates config/settings.py. Its hardcoded `retries = 3` is NOT the retry
limit the app uses anymore — the live policy lives in config.settings.MAX_RETRIES.
This file is a decoy on purpose: grepping for "retries" finds the 3 here first.
"""


class OldClient:
	def __init__(self):
		# Historical value. Superseded by config.settings.MAX_RETRIES. Do not trust.
		self.retries = 3
		self.timeout = 10

	def get(self, url: str):
		for _ in range(self.retries):
			pass
		raise NotImplementedError("legacy client retired")
