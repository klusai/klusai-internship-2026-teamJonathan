"""Exercise 4 — the invoice schema and the extraction tool.

`vendor`, `total`, and `line_items` are required. `tax_id` is **optional and
nullable** — two of the fixture invoices (inv_03, inv_05) have no tax id at all, so
the model must be allowed to return `null` (or omit it) without that being a
validation error.
"""

LINE_ITEM_SCHEMA = {
	"type": "object",
	"properties": {
		"description": {"type": "string"},
		"quantity": {"type": ["number", "null"]},
		"unit_price": {"type": ["number", "null"]},
		"amount": {"type": "number"},
	},
	"required": ["description", "amount"],
	"additionalProperties": False,
}

INVOICE_SCHEMA = {
	"type": "object",
	"properties": {
		"vendor": {"type": "string"},
		"invoice_number": {"type": ["string", "null"]},
		"date": {"type": ["string", "null"]},
		# Optional + nullable: NOT in `required`, and `null` is a valid value.
		"tax_id": {"type": ["string", "null"]},
		"currency": {"type": ["string", "null"]},
		"line_items": {
			"type": "array",
			"items": LINE_ITEM_SCHEMA,
			"minItems": 1,
		},
		"total": {"type": "number"},
	},
	"required": ["vendor", "total", "line_items"],
	"additionalProperties": False,
}

# Anthropic tool the model calls to return structured output. Its `input_schema`
# IS the invoice schema, so a successful tool call is already shaped correctly —
# we still validate with jsonschema to catch the cases the model gets subtly wrong
# (extra fields, wrong types, missing required keys).
EXTRACT_TOOL = {
	"name": "extract_invoice",
	"description": (
		"Return the structured fields extracted from an invoice. Use null for "
		"tax_id when the invoice does not show a tax / VAT / EIN number — do not "
		"invent one."
	),
	"input_schema": INVOICE_SCHEMA,
}

# Cross-field invariant jsonschema can't express: the line-item amounts should
# add up to the invoice total. We check it in code (within one cent, to tolerate
# rounding) and feed any mismatch back to the model the same way a schema error
# is fed back.
LINE_ITEM_TOLERANCE = 0.01


def line_item_mismatch(data: dict) -> str | None:
	"""Return an error message if line-item amounts don't sum to `total`, else None."""
	line_sum = sum(item["amount"] for item in data["line_items"])
	total = data["total"]
	if abs(line_sum - total) > LINE_ITEM_TOLERANCE:
		return (
			f"line_items amounts sum to {line_sum:.2f} but total is {total:.2f} "
			f"(difference {abs(line_sum - total):.2f} exceeds {LINE_ITEM_TOLERANCE:.2f}). "
			"Re-read the invoice and correct either the line items or the total."
		)
	return None
