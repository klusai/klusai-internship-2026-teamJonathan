"""Exercise 4, single-doc extraction with a validation/retry loop.

The model returns structured data by calling the `extract_invoice` tool. We then
validate that data against `INVOICE_SCHEMA` with `jsonschema`. When validation
fails, we feed the error back to the model and let it try again — that feedback
loop is the part you implement.

Setup:
    pip install anthropic jsonschema
    export ANTHROPIC_API_KEY=sk-ant-...
    python extract.py invoices/inv_03.txt
"""

import json
import sys
from pathlib import Path

import anthropic
import jsonschema

from schema import EXTRACT_TOOL, INVOICE_SCHEMA

MODEL = "claude-opus-4-8"
MAX_ATTEMPTS = 3

SYSTEM = (
	"You extract structured data from invoices. Call extract_invoice exactly once "
	"with the fields you find. If the invoice shows no tax/VAT/EIN number, set "
	"tax_id to null — never guess one."
)


def extract_one(client: anthropic.Anthropic, text: str) -> dict:
	"""Extract one invoice, retrying up to MAX_ATTEMPTS times on schema failure."""
	messages = [
		{
			"role": "user",
			"content": f"Extract this invoice:\n\n<invoice>\n{text}\n</invoice>",
		}
	]

	last_error = None
	for attempt in range(1, MAX_ATTEMPTS + 1):
		resp = client.messages.create(
			model=MODEL,
			max_tokens=1024,
			system=SYSTEM,
			tools=[EXTRACT_TOOL],
			tool_choice={"type": "tool", "name": "extract_invoice"},
			messages=messages,
		)

		tool_use = next((b for b in resp.content if b.type == "tool_use"), None)
		if tool_use is None:
			raise RuntimeError("Model did not call extract_invoice.")
		data = tool_use.input

		# TODO(task 1): validate `data` against INVOICE_SCHEMA using jsonschema.
		# On success, return `data`. On jsonschema.ValidationError, capture the
		# error message in `last_error` and fall through to the feedback step.
		try:
			jsonschema.validate(data, INVOICE_SCHEMA)
			return data
		except jsonschema.ValidationError as err:
			last_error = err.message
			print(f"  attempt {attempt}: invalid — {err.message}", file=sys.stderr)

		# TODO(task 2): feed the error back so the model can correct itself.
		# Append the assistant's tool_use turn, then a user turn containing a
		# tool_result block that references `tool_use.id`, sets "is_error": True,
		# and explains what was wrong. Then the loop calls the API again.
		messages.append({"role": "assistant", "content": resp.content})
		messages.append(
			{
				"role": "user",
				"content": [
					{
						"type": "tool_result",
						"tool_use_id": tool_use.id,
						"is_error": True,
						"content": (
							f"Schema validation failed: {last_error}. "
							"Fix the issue and call extract_invoice again."
						),
					}
				],
			}
		)

	raise RuntimeError(f"Failed after {MAX_ATTEMPTS} attempts. Last error: {last_error}")


def main() -> int:
	if len(sys.argv) != 2:
		print("usage: python extract.py <invoice.txt>", file=sys.stderr)
		return 2
	text = Path(sys.argv[1]).read_text()
	client = anthropic.Anthropic()
	data = extract_one(client, text)
	print(json.dumps(data, indent=2))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
