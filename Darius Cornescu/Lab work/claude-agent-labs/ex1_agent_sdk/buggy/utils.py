"""Buggy utilities for the agent to find and fix (Exercise 1, task 1).

Do NOT fix these by hand — point the bug-fixer agent at this file and let it edit.
Both functions crash on perfectly normal inputs.
"""


def calculate_average(numbers):
	# BUG: ZeroDivisionError when `numbers` is an empty list.
	return sum(numbers) / len(numbers)


def get_user_name(user):
	# BUG: KeyError when "name" is missing; AttributeError/TypeError when `user`
	# is None. No defensive handling at all.
	return user["name"].upper()
