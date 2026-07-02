"""
Security-finding regression tests.

Each test is written so that it FAILS against the current buggy code,
confirming the bug exists.  When the bugs are fixed the tests should pass.

Finding IDs match the security-review report:
  F1 - make_token uses unsalted MD5 (payments.py:13)
  F2 - charge uses float for money (payments.py:16-20)
  F3 - no card_number validation (payments.py)
  F4 - NaN/Infinity bypass the amount <= 0 guard (payments.py:17)
  F5 - calculate_average([]) returns 0.0 instead of raising (utils.py:8-11)
  F6 - get_user_name non-string name handling (utils.py:14-20)
"""

import hashlib
import math
from decimal import Decimal

import pytest

# ---------------------------------------------------------------------------
# Import paths derived from reading the source files directly.
# Both modules live inside the ex1_agent_sdk package tree so we rely on the
# tests/ directory being inside that same tree and pytest adding the parent
# to sys.path automatically (no conftest.py needed for simple cases).
# ---------------------------------------------------------------------------
from app.payments import charge, make_token
from buggy.utils import calculate_average, get_user_name


# ===========================================================================
# F1 — make_token uses unsalted MD5 (reversible token)
# ===========================================================================

class TestF1_UnsaltedMD5:
    """
    The token returned by make_token SHOULD be an opaque, irreversible value
    that cannot be linked back to the original PAN via a lookup table.
    Using plain MD5 means anyone with a rainbow table can recover the PAN.

    This test CONFIRMS the bug by asserting that the returned token IS the
    raw MD5 digest — something a secure implementation must NOT do.
    The test is written as a security-confirming assertion: if make_token
    ever stops returning the raw MD5, the test will fail (which is the goal).
    For pytest to FAIL against buggy code we assert the *opposite* of what
    a fixed implementation should do, i.e. we assert the bug IS present.
    """

    PAN = "4111111111111111"
    KNOWN_MD5 = hashlib.md5(PAN.encode()).hexdigest()

    def test_token_equals_raw_md5_digest(self):
        """
        BUG CONFIRMED when this assertion holds: token == raw MD5 of the PAN.
        A secure token must NOT equal the raw MD5, so this test should FAIL
        once the bug is fixed.  Right now (buggy code) it PASSES trivially,
        but the *intent* expressed by the name signals the problem.

        To turn this into a test that FAILS against buggy code we assert the
        secure property: the token must NOT be the raw MD5.
        """
        token = make_token(self.PAN)
        # DESIRED (secure) behaviour: token is NOT the raw MD5 digest.
        # Against buggy code this assertion FAILS, proving the bug.
        assert token != self.KNOWN_MD5, (
            f"make_token returned the raw unsalted MD5 ({token!r}), "
            "which is reversible via rainbow tables."
        )


# ===========================================================================
# F2 — charge uses float for money (precision loss)
# ===========================================================================

class TestF2_FloatMoney:
    """
    Financial amounts must never be stored as IEEE-754 floats.
    0.1 + 0.2 in Python float != 0.3 exactly.
    """

    def test_charge_amount_equals_decimal_030(self):
        """
        DESIRED behaviour: the returned amount is exactly Decimal('0.30').
        Against buggy code (pure float) this FAILS because
        float(0.1 + 0.2) != Decimal('0.30').
        """
        result = charge(0.1 + 0.2, "4111111111111111")
        # This assertion FAILS against buggy code — confirming the bug.
        assert result["amount"] == Decimal("0.30"), (
            f"amount is {result['amount']!r}, not Decimal('0.30'). "
            "Float arithmetic causes precision loss in financial calculations."
        )


# ===========================================================================
# F3 — no card_number validation
# ===========================================================================

class TestF3_NoCardValidation:
    """
    charge() must validate that card_number is a non-empty, non-None string
    before proceeding.  The current implementation accepts any value.
    """

    def test_empty_card_number_raises_value_error(self):
        """
        DESIRED behaviour: charge(10.0, "") raises ValueError.
        Against buggy code it returns status "charged" — FAILS here.
        """
        with pytest.raises(ValueError):
            charge(10.0, "")

    def test_none_card_number_raises_value_error(self):
        """
        DESIRED behaviour: charge(10.0, None) raises a clean ValueError.
        Against buggy code it raises AttributeError (None.encode()) — FAILS
        because pytest.raises(ValueError) does not catch AttributeError.
        """
        with pytest.raises(ValueError):
            charge(10.0, None)


# ===========================================================================
# F4 — NaN/Infinity bypass the amount <= 0 guard
# ===========================================================================

class TestF4_NanInfinityBypass:
    """
    math.nan <= 0 evaluates to False in Python, so the guard is silently
    bypassed and the function proceeds as if the amount is valid.
    """

    def test_nan_amount_raises_value_error(self):
        """
        DESIRED behaviour: charge(float('nan'), ...) raises ValueError.
        Against buggy code it returns {"status": "charged"} — FAILS here.
        """
        with pytest.raises(ValueError):
            charge(float("nan"), "4111111111111111")

    def test_infinity_amount_raises_value_error(self):
        """
        DESIRED behaviour: charge(float('inf'), ...) raises ValueError.
        Against buggy code it returns {"status": "charged"} — FAILS here.
        """
        with pytest.raises(ValueError):
            charge(float("inf"), "4111111111111111")


# ===========================================================================
# F5 — calculate_average([]) returns 0.0 instead of raising
# ===========================================================================

class TestF5_EmptyListAverage:
    """
    Returning 0.0 for an empty list silently hides the fact that no data was
    provided.  The function should raise ValueError instead.
    """

    def test_empty_list_raises_value_error(self):
        """
        DESIRED behaviour: calculate_average([]) raises ValueError.
        Against buggy code it returns 0.0 — FAILS here.
        """
        with pytest.raises(ValueError):
            calculate_average([])


# ===========================================================================
# F6 — get_user_name non-string name silently misbehaves
# ===========================================================================

class TestF6_NonStringName:
    """
    When "name" is an integer (or other non-string), the function either
    crashes with AttributeError (int.upper()) or silently returns "" (falsy
    int like 0).  Both are wrong; a clean TypeError should be raised.
    """

    def test_integer_name_raises_type_error(self):
        """
        get_user_name({"name": 42}) — "name" is an int, not a str.
        DESIRED behaviour: raises TypeError.
        Against buggy code it raises AttributeError — FAILS here because
        pytest.raises(TypeError) will not catch AttributeError.
        """
        with pytest.raises(TypeError):
            get_user_name({"name": 42})

    def test_zero_name_raises_type_error(self):
        """
        get_user_name({"name": 0}) — "name" is 0 (falsy int).
        DESIRED behaviour: raises TypeError.
        Against buggy code `not name` is True (0 is falsy) so it returns ""
        silently — FAILS here.
        """
        with pytest.raises(TypeError):
            get_user_name({"name": 0})
