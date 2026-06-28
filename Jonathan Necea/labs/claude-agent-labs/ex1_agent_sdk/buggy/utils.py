"""Buggy utilities for the agent to find and fix (Exercise 1, task 1).

Do NOT fix these by hand — point the bug-fixer agent at this file and let it edit.
Both functions crash on perfectly normal inputs.
"""


def calculate_average(numbers):
	if not numbers:
		return 0.0
	return sum(numbers) / len(numbers)


def get_user_name(user):
	if not user:
		return ""
	name = user.get("name")
	if not name:
		return ""
	return name.upper()
