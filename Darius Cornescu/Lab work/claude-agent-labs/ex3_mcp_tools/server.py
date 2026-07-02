"""Exercise 3 — a small MCP server with two *deliberately confusable* tools.

`search_orders` looks things up by **order id**; `search_customers` looks things up
by **customer name**. The whole point of the exercise is that the model picks the
right one based ONLY on the tool descriptions — so the descriptions below start as
weak TODO stubs that you must rewrite to disambiguate.

Run the server (after `pip install mcp`):

    python server.py            # stdio transport, for an MCP client / Claude Desktop

You don't need a running server to do the core exercise: `run_ambiguity_test.py`
imports the two tool functions and reads their docstrings directly.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("orders-and-customers")


# --- Tiny in-memory fixture data -------------------------------------------------

_ORDERS = {
	"10432": {"order_id": "10432", "customer": "Acme Corporation", "total": 249.00, "status": "shipped"},
	"88231": {"order_id": "88231", "customer": "Globex", "total": 18.50, "status": "processing"},
	"ORD-5567": {"order_id": "ORD-5567", "customer": "Wayne Enterprises", "total": 999.99, "status": "delivered"},
	"7741": {"order_id": "7741", "customer": "Jane Doe", "status": "cancelled", "total": 0.0},
}

_CUSTOMERS = {
	"acme corporation": {"name": "Acme Corporation", "tier": "enterprise", "open_orders": 3},
	"globex": {"name": "Globex", "tier": "smb", "open_orders": 1},
	"jane doe": {"name": "Jane Doe", "tier": "consumer", "open_orders": 0},
	"wayne enterprises": {"name": "Wayne Enterprises", "tier": "enterprise", "open_orders": 7},
}


# --- Structured errors -----------------------------------------------------------

# Only this category is safe to retry. Everything else is a permanent failure the
# caller should NOT hammer.
_RETRYABLE_CATEGORIES = {"rate_limit"}


def make_error(category: str, message: str) -> dict:
	"""Build a structured error the model can reason about.

	Returns a dict with three keys:
	  - error_category: a short machine-readable category (e.g. "not_found",
	    "rate_limit", "invalid_input").
	  - message: a human-readable explanation.
	  - retryable: True ONLY when the category is `rate_limit`; False otherwise.

	The retry flag is the important bit: a `not_found` should never be retried,
	but a `rate_limit` should be retried after a backoff.
	"""
	return {
		"error_category": category,
		"message": message,
		"retryable": category in _RETRYABLE_CATEGORIES,
	}


# --- Tools -----------------------------------------------------------------------

@mcp.tool()
def search_orders(order_id: str) -> dict:
	"""Look up a single order by its order id.

	Use this ONLY when the user has identified a specific order by its identifier —
	either bare digits (e.g. "10432", "88231") or a prefixed order code (e.g.
	"ORD-5567"). Phrasing like "order #10432", "status of 7741", or "pull up
	ORD-5567" means use this tool.

	Argument:
	  order_id: the order identifier as a string. Digits or a code like "ORD-5567".

	Example: user says "What's the status of order 88231?" -> call with
	order_id="88231".

	NOT for looking up a customer by name, and NOT for finding an order when the
	user only gives a person or company (no order id). In that case resolve the
	customer first with `search_customers`. Returns an `invalid_input` error on an
	empty id and a `not_found` error when no such order exists.
	"""
	if not order_id or not order_id.strip():
		return make_error("invalid_input", "order_id must be a non-empty string.")
	order = _ORDERS.get(order_id)
	if order is None:
		return make_error("not_found", f"No order with id {order_id!r}.")
	return order


@mcp.tool()
def search_customers(name: str) -> dict:
	"""Look up a single customer by their name.

	Use this ONLY when the user identifies a person or company by name (free text) —
	e.g. "Acme Corporation", "Jane Doe", "Globex", "Smith". Phrasing like "look up
	the customer X", "details for X", or "everything for X" means use this tool. Also
	use it as the FIRST step when the user wants an order but only gives a
	company/person (e.g. "the order from Wayne Enterprises") — resolve the customer
	here first, since `search_orders` needs an order id you don't have yet.

	Argument:
	  name: a person or company name as free text (case-insensitive).

	Example: user says "Show me everything for Jane Doe" -> call with name="Jane Doe".

	NOT for looking up an order by its id (digits or an "ORD-" code) — use
	`search_orders` for that.
	"""
	customer = _CUSTOMERS.get(name.strip().lower())
	if customer is None:
		return make_error("not_found", f"No customer named {name!r}.")
	return customer


if __name__ == "__main__":
	# Runs the server over stdio. An MCP client (or Claude Desktop) connects to it.
	mcp.run()
