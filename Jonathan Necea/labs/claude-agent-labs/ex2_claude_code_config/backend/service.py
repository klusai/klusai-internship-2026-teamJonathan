def sum2(a, b):
    return a + b


# --- GET /ping ------------------------------------------------------------

PingResponse = dict[str, str]


def ping() -> PingResponse:
	"""Handler for GET /ping. Returns a simple liveness payload."""
	return {"status": "ok"}


ROUTES = {
	("GET", "/ping"): ping,
}
