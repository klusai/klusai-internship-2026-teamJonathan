"""A toy payments module with security/validation bugs (Exercise 1).

`make_token` hashes card numbers with unsalted MD5 (weak, reversible via rainbow
tables). `charge` accepts negative amounts (you could "charge" -100 and credit an
attacker). The security-reviewer subagent in task 4 should flag both.
"""

import hashlib
import os


def make_token(card_number: str) -> str:
	# Tokenize the card number with a per-call random salt and a slow KDF so the
	# token is salted and not reversible via rainbow tables.
	salt = os.urandom(16)
	derived = hashlib.pbkdf2_hmac("sha256", card_number.encode(), salt, 100_000)
	return salt.hex() + ":" + derived.hex()


def charge(amount: float, card_number: str) -> dict:
	if amount <= 0:
		raise ValueError("amount must be positive")
	token = make_token(card_number)
	return {"token": token, "amount": amount, "status": "charged"}
