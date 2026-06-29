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
	"acme corporation": {"name": "Acme Corporation", "email": "billing@acme.example", "tier": "enterprise", "open_orders": 3},
	"globex": {"name": "Globex", "email": "ops@globex.example", "tier": "smb", "open_orders": 1},
	"jane doe": {"name": "Jane Doe", "email": "jane.doe@example.com", "tier": "consumer", "open_orders": 0},
	"wayne enterprises": {"name": "Wayne Enterprises", "email": "bruce@wayne.example", "tier": "enterprise", "open_orders": 7},
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
	"""Look up a SINGLE order by its order id.

	Use this whenever the request contains an order identifier or asks about a
	specific order — its status, total, or which customer placed it. Order ids
	are either bare numbers like "88231" or prefixed codes like "ORD-5567".
	Treat any standalone number in the request as an order id, NOT a customer
	account number.

	This tool is NOT for finding a customer by name or company — use
	`search_customers` for that. If the user wants an order but gives only a
	company/person name (no id), you cannot call this tool: resolve the customer
	first with `search_customers`.

	Args:
		order_id: The order's identifier, e.g. "10432" or "ORD-5567".

	Example:
		"What's the status of 88231?" -> order_id="88231"
	"""
	if not order_id or not order_id.strip():
		return make_error("invalid_input", "Order id must not be empty.")
	order = _ORDERS.get(order_id.strip())
	if order is None:
		return make_error("not_found", f"No order with id {order_id!r}.")
	return order


@mcp.tool()
def search_customers(name: str) -> dict:
	"""Look up a SINGLE customer by their person or company name.

	Use this whenever the request names a person or company (e.g. "Acme
	Corporation", "Jane Doe", "Smith") rather than giving an order number. Also
	use it as the FIRST step when the user wants an order but supplies only a
	name — resolve the customer here, then act on the returned info.

	This tool is NOT for looking up orders by id/number — use `search_orders`
	for that. Bare numbers are order ids, not customer names. For an email
	address, use `search_by_email` instead.

	Args:
		name: The customer's person or company name, e.g. "Acme Corporation".

	Example:
		"Get details for Globex" -> name="Globex"
	"""
	customer = _CUSTOMERS.get(name.strip().lower())
	if customer is None:
		return make_error("not_found", f"No customer named {name!r}.")
	return customer

@mcp.tool()
def search_by_email(email: str) -> dict:
	"""Look up a SINGLE customer by their email address.

	Use this only when the request contains an email address (a string with an
	"@", e.g. "ops@globex.example"). This is the right tool when you have an
	email but not the customer's display name.

	This tool is NOT for plain names or company names — use `search_customers`
	for those — and NOT for order ids — use `search_orders`.

	Args:
		email: The customer's email address, e.g. "ops@globex.example".

	Example:
		"Who owns jane.doe@example.com?" -> email="jane.doe@example.com"
	"""
	if not email or "@" not in email:
		return make_error("invalid_input", "A valid email address is required.")
	address = email.strip().lower()
	for customer in _CUSTOMERS.values():
		if customer.get("email", "").lower() == address:
			return customer
	return make_error("not_found", f"No customer with email {email!r}.")


if __name__ == "__main__":
	# Runs the server over stdio. An MCP client (or Claude Desktop) connects to it.
	mcp.run()
