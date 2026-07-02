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
