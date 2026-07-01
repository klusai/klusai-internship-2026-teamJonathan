"""Exercise 5, task 2 — vague vs. explicit-criteria review.

Run a VAGUE review prompt 3 times and an EXPLICIT-CRITERIA review prompt 3 times
over big_diff.txt. Compare: the vague prompt finds different things each run and
often misses planted issues; the explicit prompt finds the same real issues every
time. The diff has three planted problems — SQL injection, a bare `except: pass`,
and unsalted MD5 password hashing.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python task2_review_criteria.py
"""

import os
import sys
from pathlib import Path

import anthropic

MODEL = "claude-opus-4-8"
RUNS = 3
HERE = Path(__file__).parent

VAGUE_PROMPT = "Review this diff and tell me about any problems.\n\n{diff}"

# TODO(task 2): complete the criteria checklist. One item is seeded; add the rest
# so the review reliably catches the three planted issues (and anything else worth
# flagging). Be specific — explicit criteria are the whole point.
CRITERIA = [
	"Security: flag any SQL built by string concatenation / f-strings (injection risk).",
	"Error handling: flag bare `except:` or `except Exception: pass` that silently swallows errors.",
	"Password hashing: flag any use of MD5, SHA-1, or other fast/unsalted hashes for passwords or tokens — require bcrypt, argon2, or PBKDF2 with a per-record salt.",
	"Input validation: flag functions that accept external input without checking type, range, or length before using it.",
	"Secrets in code: flag any hardcoded credentials, API keys, or tokens that should be in environment variables.",
]

EXPLICIT_PROMPT = (
	"Review this diff against these explicit criteria. For EACH criterion, state "
	"whether it is violated and cite the file and line.\n\nCriteria:\n{criteria}\n\n{diff}"
)


def review(client: anthropic.Anthropic, prompt: str) -> str:
	resp = client.messages.create(
		model=MODEL,
		max_tokens=1500,
		messages=[{"role": "user", "content": prompt}],
	)
	return "".join(b.text for b in resp.content if b.type == "text")


def main() -> int:
	if not os.environ.get("ANTHROPIC_API_KEY"):
		print("Set ANTHROPIC_API_KEY first.", file=sys.stderr)
		return 1

	diff = (HERE / "big_diff.txt").read_text()
	client = anthropic.Anthropic()
	criteria_block = "\n".join(f"- {c}" for c in CRITERIA)

	print("=" * 80)
	print("VAGUE prompt — 3 runs (expect inconsistent coverage)")
	print("=" * 80)
	for i in range(1, RUNS + 1):
		print(f"\n--- vague run {i} ---")
		print(review(client, VAGUE_PROMPT.format(diff=diff)))

	print("\n" + "=" * 80)
	print("EXPLICIT-CRITERIA prompt — 3 runs (expect the same real issues each time)")
	print("=" * 80)
	for i in range(1, RUNS + 1):
		print(f"\n--- explicit run {i} ---")
		print(review(client, EXPLICIT_PROMPT.format(criteria=criteria_block, diff=diff)))

	print("\nCompare: did the explicit runs find SQL injection, bare except, and MD5 every time?")
	return 0


# --- Planted issues in big_diff.txt (all three must appear in every explicit run) ---
#
# 1. SQL injection
#    api/auth.py   line 26 — verify_login: WHERE clause built by string concat
#                             "WHERE username = '" + username + "'"
#    api/orders.py line 62 — search_orders: f-string column/value injected into WHERE
#                             f"{column} = '{value}'"
#
# 2. Bare except
#    api/orders.py line 74 — cancel_order: `except: pass` swallows all exceptions
#    api/utils.py  line 103 — parse_int: second `except: pass`
#
# 3. Unsalted MD5
#    api/auth.py   line 18 — hash_password: hashlib.md5(password.encode()).hexdigest()
#    api/utils.py  line 110 — api_key_fingerprint: hashlib.md5(api_key.encode())...
#
# Vague-run variance: the vague prompt finds different subsets each run and often
# misses at least one of the three classes (commonly the bare-except on parse_int or
# the second MD5 use). The explicit-criteria prompt finds all three every run because
# each criterion forces the model to check for that class regardless of salience.

if __name__ == "__main__":
	raise SystemExit(main())
