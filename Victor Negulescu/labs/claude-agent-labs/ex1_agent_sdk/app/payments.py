"""A toy payments module with security/validation bugs (Exercise 1).

`make_token` hashes card numbers with unsalted MD5 (weak, reversible via rainbow
tables). `charge` accepts negative amounts (you could "charge" -100 and credit an
attacker). The security-reviewer subagent in task 4 should flag both.
"""

import hashlib
import secrets


def make_token(card_number: str) -> str:
	salt = secrets.token_hex(16)
	digest = hashlib.sha256((salt + card_number).encode()).hexdigest()
	return salt + digest


def charge(amount: float, card_number: str) -> dict:
	if amount <= 0:
		raise ValueError(f"amount must be positive, got {amount}")
	token = make_token(card_number)
	return {"token": token, "amount": amount, "status": "charged"}
