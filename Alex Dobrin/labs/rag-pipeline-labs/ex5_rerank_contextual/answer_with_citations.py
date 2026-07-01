"""Exercise 5c — grounded answer generation with citations + prompt caching.

Retrieval is only half of RAG; the other half is generating an answer grounded in what
you retrieved, with citations so a user can verify it. This capstone feeds the corpus
to Claude as a document, turns on citations so the answer carries source spans, and
caches the corpus so repeated questions over the same document are cheap.

You enable the two surrounding-API features (citations + cache_control) on the document
block; the request and response handling are provided.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python answer_with_citations.py
"""

import os
import sys
from pathlib import Path

import anthropic

HERE = Path(__file__).parent
CORPUS = HERE.parent / "corpus" / "corpus.md"
MODEL = "claude-opus-4-8"

QUESTION = "What did the company change after the phishing attack, and what were the security results?"


def build_document_block(corpus_text: str) -> dict:
	"""The document Claude answers from.

	TODO(task 5c): return a 'document' content block whose source is the corpus text
	(source type 'text', media_type 'text/plain', data=corpus_text), with a 'title',
	citations ENABLED so the answer carries source spans, and a cache_control of type
	'ephemeral' so the corpus is cached across repeated questions.
	"""
	return {
		"type": "document",
		"source": {
			"type": "text",
			"media_type": "text/plain",
			"data": corpus_text,
		},
		"title": "Company annual report corpus",
		"citations": {"enabled": True},
		"cache_control": {"type": "ephemeral"},
	}


def main() -> int:
	if not os.environ.get("ANTHROPIC_API_KEY"):
		print("Set ANTHROPIC_API_KEY first.", file=sys.stderr)
		return 1

	client = anthropic.Anthropic()
	corpus_text = CORPUS.read_text()

	resp = client.messages.create(
		model=MODEL,
		max_tokens=600,
		messages=[
			{
				"role": "user",
				"content": [
					{"type": "text", "text": QUESTION},
					build_document_block(corpus_text),
				],
			}
		],
	)

	print("ANSWER:\n")
	cited = 0
	for block in resp.content:
		if block.type != "text":
			continue
		print(block.text)
		for citation in getattr(block, "citations", None) or []:
			cited += 1
			snippet = getattr(citation, "cited_text", "")
			print(f"    ↳ cited: {snippet[:80]!r}")
	print(f"\ncitations attached: {cited}")
	print(
		f"cache: created={resp.usage.cache_creation_input_tokens} "
		f"read={resp.usage.cache_read_input_tokens}"
	)
	# Run it twice in one session to see cache_read_input_tokens jump on the 2nd call.
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
