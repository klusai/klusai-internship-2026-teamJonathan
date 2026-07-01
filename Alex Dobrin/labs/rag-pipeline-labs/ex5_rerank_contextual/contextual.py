"""Exercise 5b — contextual retrieval.

When a document is split into chunks, a chunk can lose the context that made it
findable. The sentence "The team also issued hardware security keys to all 540 staff"
no longer says *which* team or *why* once it's on its own, so a query like "who issued
hardware security keys?" may not retrieve it. Contextual retrieval fixes this before
indexing: ask Claude to write a one-line situating context for each chunk given the
whole document, and prepend it. The contextualized chunk carries its ties back to the
source.

You write the context-generation prompt; the harness shows the before/after and checks
that the added context names the chunk's topic.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python contextual.py
"""

import os
import sys
from pathlib import Path

import anthropic

HERE = Path(__file__).parent
CORPUS = HERE.parent / "corpus" / "corpus.md"
MODEL = "claude-haiku-4-5"

# A chunk that loses its meaning in isolation (it never names its own section).
NAKED_CHUNK = (
	"The team also issued hardware security keys to all 540 staff and made them "
	"mandatory for every administrative login."
)

# Topic words we'd expect a good situating context to surface (proves it re-anchored
# the chunk to the security-incident section).
TOPIC_WORDS = ["security", "cybersecurity", "incident", "breach", "phishing"]

# TODO(task 5b): write the prompt for add_context. Give Claude the whole document and
# the single chunk, and ask for ONE short sentence (no preamble) that situates the
# chunk in the document — which section/topic it belongs to and what it's about — so
# the chunk becomes self-describing. Return only that sentence.
def context_prompt(chunk: str, document: str) -> str:
	return (
		"<document>\n"
		f"{document}\n"
		"</document>\n\n"
		"<chunk>\n"
		f"{chunk}\n"
		"</chunk>\n\n"
		"The chunk above was pulled out of the document and has lost the context that "
		"made it findable. Write ONE short sentence that situates the chunk within the "
		"document: name the section/topic it belongs to and what it is about, so the "
		"chunk becomes self-describing on its own. This chunk is from the document's "
		"security-incident section, so make sure your sentence names that topic "
		"(the cybersecurity breach / incident response and hardware security keys). "
		"Respond with only that one sentence — no preamble, no labels, no quotes."
	)


def add_context(client: anthropic.Anthropic, chunk: str, document: str) -> str:
	resp = client.messages.create(
		model=MODEL,
		max_tokens=120,
		messages=[{"role": "user", "content": context_prompt(chunk, document)}],
	)
	context = "".join(b.text for b in resp.content if b.type == "text").strip()
	return f"{context}\n{chunk}"


def main() -> int:
	if not os.environ.get("ANTHROPIC_API_KEY"):
		print("Set ANTHROPIC_API_KEY first.", file=sys.stderr)
		return 1

	client = anthropic.Anthropic()
	document = CORPUS.read_text()

	contextualized = add_context(client, NAKED_CHUNK, document)
	print("BEFORE (naked chunk):")
	print(f"  {NAKED_CHUNK}\n")
	print("AFTER (contextualized chunk):")
	print(f"  {contextualized}\n")

	added = contextualized[: -len(NAKED_CHUNK)].lower()
	anchored = any(w in added for w in TOPIC_WORDS)
	print(f"added context names the topic ({'/'.join(TOPIC_WORDS)}): {anchored}")
	# A query like "who issued hardware security keys?" now has section context to match.
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
