"""Small backend module. The function below has NO type hints, so the
backend/** rule (.claude/rules/backend.md) fires when Claude reviews it."""


# VIOLATION (backend rule): missing type hints on the params and return.
def compute_discount(price, percent):
	return price - (price * percent / 100)
