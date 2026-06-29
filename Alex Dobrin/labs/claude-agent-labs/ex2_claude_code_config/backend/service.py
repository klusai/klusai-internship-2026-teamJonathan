"""Backend service — used to test the backend/** rule (require type hints)."""


def add_user(name, age):  # <- no type hints; should be flagged by .claude/rules/backend.md
	return {"name": name, "age": age}
