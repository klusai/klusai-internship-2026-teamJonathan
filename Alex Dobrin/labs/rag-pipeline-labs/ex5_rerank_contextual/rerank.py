"""Exercise 5a — reranking retrieved results with an LLM.

Hybrid retrieval gets the right chunk into the candidate set, but not always at the
top. Reranking is a cheap second pass: hand the top candidates to Claude with the
query and let it reorder by true relevance. It catches intent the first-pass scores
miss (e.g. "what changed after the phishing attack" is incident response, not whatever
shares the most words). Here the candidate lists are deliberately mis-ordered — your
reranker should move the gold section to rank 1.

You write the reranking instruction; the tool call, parsing, and measurement are
provided.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python rerank.py
"""

import json
import os
import re
import sys
from pathlib import Path

import anthropic

HERE = Path(__file__).parent
CORPUS = HERE.parent / "corpus" / "corpus.md"
QUERIES = HERE.parent / "corpus" / "queries.json"
MODEL = "claude-sonnet-4-6"

# Candidate id lists per query, in a deliberately suboptimal order (gold not first).
CANDIDATES = {
	8: ["software-engineering", "cybersecurity", "executive-summary"],
	2: ["customer-support", "cybersecurity", "finance"],
	3: ["software-engineering", "executive-summary", "research-and-development"],
}

# TODO(task 5a): instruct Claude to act as a reranker — read the query and the
# candidate documents and call rank_documents with the ids ordered most-relevant
# first. Tell it to judge by what actually answers the query's intent, not surface
# word overlap.
RERANK_SYSTEM = (
	"You are a search reranker. You are given a user query and a set of candidate "
	"documents, each wrapped in a <doc id=\"...\"> tag. Reorder ALL of the candidate "
	"ids from most to least relevant to the query, then call the rank_documents tool "
	"with that ordering.\n\n"
	"Rank by what actually answers the query's underlying intent, not by surface word "
	"overlap. A document that shares many words with the query but does not address "
	"what the user is really asking should rank below one that directly answers the "
	"intent even if it shares fewer words. Consider the question behind the question: "
	"for example, 'what changed after the phishing attack' is about incident response "
	"and remediation, not about whatever section happens to repeat the words 'change' "
	"or 'team'.\n\n"
	"Return every candidate id exactly once, most relevant first."
)

RANK_TOOL = {
	"name": "rank_documents",
	"description": "Return the document ids ordered from most to least relevant.",
	"input_schema": {
		"type": "object",
		"properties": {
			"order": {
				"type": "array",
				"items": {"type": "string"},
				"description": "All candidate ids, most relevant first.",
			}
		},
		"required": ["order"],
	},
}


def sections_by_slug(text: str) -> dict[str, str]:
	out: dict[str, str] = {}
	current: list[str] = []
	for line in text.splitlines(keepends=True):
		if line.startswith("## ") and current:
			_store(out, current)
			current = []
		current.append(line)
	if current:
		_store(out, current)
	return out


def _store(out: dict[str, str], lines: list[str]) -> None:
	text = "".join(lines)
	header = lines[0].lstrip("# ").strip()
	slug = re.sub(r"[^a-z0-9]+", "-", header.lower()).strip("-")
	out[slug] = text


def rerank(client: anthropic.Anthropic, query: str, ids: list[str], id_to_text: dict[str, str]) -> list[str]:
	docs = "\n\n".join(f'<doc id="{cid}">\n{id_to_text[cid][:600]}\n</doc>' for cid in ids)
	resp = client.messages.create(
		model=MODEL,
		max_tokens=300,
		system=RERANK_SYSTEM,
		tools=[RANK_TOOL],
		tool_choice={"type": "tool", "name": "rank_documents"},
		messages=[{"role": "user", "content": f"Query: {query}\n\nDocuments:\n{docs}"}],
	)
	tool_use = next((b for b in resp.content if b.type == "tool_use"), None)
	return tool_use.input["order"] if tool_use else ids


def main() -> int:
	if not os.environ.get("ANTHROPIC_API_KEY"):
		print("Set ANTHROPIC_API_KEY first.", file=sys.stderr)
		return 1

	client = anthropic.Anthropic()
	id_to_text = sections_by_slug(CORPUS.read_text())
	queries = {q["id"]: q for q in json.loads(QUERIES.read_text())["queries"]}

	before = after = 0
	print(f"{'#':>2}  {'gold':<22}{'before@1':<22}{'after@1':<22}")
	print("-" * 70)
	for qid, ids in CANDIDATES.items():
		q = queries[qid]
		gold = q["gold_section"]
		reordered = rerank(client, q["query"], ids, id_to_text)
		before += int(ids[0] == gold)
		after += int(reordered[0] == gold)
		print(f"{qid:>2}  {gold:<22}{ids[0]:<22}{reordered[0]:<22}")
	print("-" * 70)
	print(f"gold at rank 1 — before: {before}/{len(CANDIDATES)}   after rerank: {after}/{len(CANDIDATES)}")
	# Expect 'after' to beat 'before': the reranker promotes the right section.
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
