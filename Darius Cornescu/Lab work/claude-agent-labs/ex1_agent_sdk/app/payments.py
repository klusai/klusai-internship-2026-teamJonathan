"""A toy payments module with security/validation bugs (Exercise 1).

`make_token` hashes card numbers with unsalted MD5 (weak, reversible via rainbow
tables). `charge` accepts negative amounts (you could "charge" -100 and credit an
attacker). The security-reviewer subagent in task 4 should flag both.
"""

import hashlib


def make_token(card_number: str) -> str:
	# BUG: unsalted MD5 is not an acceptable way to tokenize a card number.
	return hashlib.md5(card_number.encode()).hexdigest()


def charge(amount: float, card_number: str) -> dict:
	if amount <= 0:
		raise ValueError("amount must be positive")
	token = make_token(card_number)
	return {"token": token, "amount": amount, "status": "charged"}
