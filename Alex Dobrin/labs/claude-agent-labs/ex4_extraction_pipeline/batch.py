"""Exercise 4, batch extraction via the Message Batches API.

Submit all 6 invoices in one batch (50% cheaper than synchronous calls), poll until
the batch ends, then validate and aggregate the results. Compare the cost and
throughput against running `extract.py` 6 times in a row (see the README).

Setup:
    pip install anthropic jsonschema
    export ANTHROPIC_API_KEY=sk-ant-...
    python batch.py
"""

import json
import time
from pathlib import Path

import anthropic
import jsonschema
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

from schema import EXTRACT_TOOL, INVOICE_SCHEMA, line_item_mismatch

MODEL = "claude-opus-4-8"
HERE = Path(__file__).parent
INVOICES = sorted((HERE / "invoices").glob("*.txt"))

SYSTEM = (
	"You extract structured data from invoices. Call extract_invoice exactly once "
	"with the fields you find. If the invoice shows no tax/VAT/EIN number, set "
	"tax_id to null — never guess one."
)

# Prompt-cache the shared prefix (tools + system) so every request after the
# first reads it from cache instead of reprocessing it. The breakpoint goes on
# the last system block, which caches the tool definitions ahead of it too.
# Note: Opus needs a 4096-token cacheable prefix, so this short prompt won't
# actually populate the cache — the wiring is the point. Enlarge the prefix (or
# watch usage.cache_read_input_tokens) to see real hits.
SYSTEM_BLOCKS = [
	{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}
]


def build_requests() -> list[Request]:
	"""One batch request per invoice file; custom_id is the file stem (e.g. inv_03)."""
	requests = []
	for path in INVOICES:
		text = path.read_text()
		requests.append(
			Request(
				custom_id=path.stem,
				params=MessageCreateParamsNonStreaming(
					model=MODEL,
					max_tokens=1024,
					system=SYSTEM_BLOCKS,
					tools=[EXTRACT_TOOL],
					tool_choice={"type": "tool", "name": "extract_invoice"},
					messages=[
						{
							"role": "user",
							"content": f"Extract this invoice:\n\n<invoice>\n{text}\n</invoice>",
						}
					],
				),
			)
		)
	return requests


def main() -> int:
	client = anthropic.Anthropic()

	batch = client.messages.batches.create(requests=build_requests())
	print(f"submitted batch {batch.id} ({len(INVOICES)} invoices)")

	# Poll until the batch ends (most finish well under an hour).
	while True:
		batch = client.messages.batches.retrieve(batch.id)
		if batch.processing_status == "ended":
			break
		print(f"  status={batch.processing_status} processing={batch.request_counts.processing}")
		time.sleep(10)

	# Collect, validate, aggregate.
	results: dict[str, dict] = {}
	failures: dict[str, str] = {}
	for result in client.messages.batches.results(batch.id):
		cid = result.custom_id
		if result.result.type != "succeeded":
			failures[cid] = result.result.type
			continue

		msg = result.result.message
		tool_use = next((b for b in msg.content if b.type == "tool_use"), None)
		if tool_use is None:
			failures[cid] = "no_tool_use"
			continue
		data = tool_use.input

		# Validate against INVOICE_SCHEMA, then run the line-item cross-check. On
		# success store the data; on either failure record the reason. The Batches
		# API has no per-item retry, so a failure here (e.g. malformed inv_07) is
		# an invoice you'd note and resubmit in a new batch — not a crash.
		try:
			jsonschema.validate(data, INVOICE_SCHEMA)
		except jsonschema.ValidationError as err:
			failures[cid] = f"invalid at {err.json_path}: {err.message}"
			continue

		mismatch = line_item_mismatch(data)
		if mismatch is not None:
			failures[cid] = f"line-item mismatch: {mismatch}"
		else:
			results[cid] = data

	# Aggregate: sum every `total`, and list invoices with no tax_id
	# (expect inv_03 and inv_05).
	grand_total = sum(r["total"] for r in results.values())
	no_tax_id = sorted(cid for cid, r in results.items() if r.get("tax_id") is None)

	print("\n=== results ===")
	print(json.dumps(results, indent=2, sort_keys=True))
	print(f"\nextracted OK: {len(results)}/{len(INVOICES)}")
	print(f"grand total (sum of totals): {grand_total}")
	print(f"invoices with no tax_id: {no_tax_id}")
	if failures:
		print(f"failures: {failures}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
