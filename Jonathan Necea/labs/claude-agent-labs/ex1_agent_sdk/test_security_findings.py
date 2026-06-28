"""
Security-review regression tests.

Findings covered:
  1. [Medium]  payments.charge() -- non-numeric amount raises TypeError, not ValueError.
  2. [High]    payments.charge(10, None) -- AttributeError inside make_token().
  3. [High]    payments.charge(10, "") -- silently accepts empty card number.
  4. [Low]     payments module docstring claims unsalted MD5; code uses salted SHA-256.
  5. [Medium]  utils.calculate_average([]) returns ambiguous 0.0.
  6. [Medium]  utils.get_user_name() returns "" for three distinct error states.

Run with:
    uv run pytest test_security_findings.py -v
"""

import sys
import os
import pytest

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from app.payments import charge, make_token
import app.payments as payments_module
from buggy.utils import calculate_average, get_user_name


# ===========================================================================
# Finding 1 [Medium] -- charge() with non-numeric amount raises TypeError
#   instead of a clean ValueError.
# ===========================================================================

class TestFinding1_NonNumericAmount:
    """charge() should validate that amount is numeric and raise ValueError; not TypeError."""

    def test_string_amount_string_100_raises_value_error(self):
        """charge('100', card) currently raises TypeError from `'100' <= 0`; want ValueError."""
        with pytest.raises(ValueError):
            charge("100", "4111111111111111")

    def test_string_amount_raises_type_error_confirming_bug(self):
        """Confirm the ACTUAL current behaviour is TypeError (the bug exists)."""
        with pytest.raises(TypeError):
            charge("100", "4111111111111111")

    def test_none_amount_raises_value_error(self):
        """charge(None, card) should raise ValueError with a useful message, not TypeError."""
        with pytest.raises(ValueError):
            charge(None, "4111111111111111")

    def test_none_amount_raises_type_error_confirming_bug(self):
        """Confirm the ACTUAL current behaviour for None amount is TypeError (the bug)."""
        with pytest.raises(TypeError):
            charge(None, "4111111111111111")


# ===========================================================================
# Finding 2 [High] -- charge(10, None): None card_number reaches make_token()
#   which calls card_number.encode(), raising AttributeError.
# ===========================================================================

class TestFinding2_NoneCardNumber:
    """charge() must reject None card_number with ValueError before reaching make_token()."""

    def test_none_card_currently_raises_attribute_error_confirming_bug(self):
        """Confirm the bug: charge(10, None) raises AttributeError from None.encode()."""
        with pytest.raises(AttributeError):
            charge(10, None)

    def test_none_card_should_raise_value_error(self):
        """The correct behaviour once fixed: a clean ValueError, not AttributeError."""
        with pytest.raises(ValueError):
            charge(10, None)


# ===========================================================================
# Finding 3 [High] -- charge(10, "") silently accepts an empty card number
#   and returns {"status": "charged", ...}.
# ===========================================================================

class TestFinding3_EmptyCardNumber:
    """charge() must reject an empty (or whitespace) card_number with ValueError."""

    def test_empty_card_currently_succeeds_confirming_bug(self):
        """Confirm the bug: charge(10, '') returns a charged receipt with no error."""
        result = charge(10, "")
        assert result["status"] == "charged", (
            "charge(10, '') should NOT succeed; it should raise ValueError"
        )

    def test_empty_card_should_raise_value_error(self):
        """The correct behaviour once fixed: ValueError for empty card_number."""
        with pytest.raises(ValueError):
            charge(10, "")

    def test_whitespace_only_card_should_raise_value_error(self):
        """Whitespace-only strings are also invalid card numbers."""
        with pytest.raises(ValueError):
            charge(10, "   ")


# ===========================================================================
# Finding 4 [Low] -- Module docstring claims unsalted MD5; implementation
#   actually uses salted SHA-256 (documentation defect).
# ===========================================================================

class TestFinding4_DocstringMismatch:
    """Verify the implementation is salted SHA-256 while the docstring says MD5."""

    def test_docstring_mentions_md5_confirming_documentation_bug(self):
        """The docstring still contains the misleading 'MD5' claim."""
        docstring = payments_module.__doc__ or ""
        assert "MD5" in docstring, (
            "Docstring no longer mentions MD5 -- "
            "update this test after the documentation is corrected"
        )

    def test_make_token_produces_sha256_digest_not_md5(self):
        """SHA-256 hex digest is 64 chars; MD5 would be 32. Length proves SHA-256."""
        token = make_token("4111111111111111")
        parts = token.split("$")
        assert len(parts) == 2, f"Expected 'salt$digest' format, got: {token!r}"
        _salt_hex, digest_hex = parts
        assert len(digest_hex) == 64, (
            f"Digest length {len(digest_hex)} chars != 64; not SHA-256 "
            f"(MD5 would be 32)"
        )

    def test_make_token_is_salted_random(self):
        """Two calls with the same card must produce different tokens (random salt)."""
        token1 = make_token("4111111111111111")
        token2 = make_token("4111111111111111")
        assert token1 != token2, (
            "Identical inputs yielded identical tokens -- hashing appears unsalted"
        )

    def test_salt_is_16_bytes_hex_encoded(self):
        """Salt portion must be 32 hex chars (16 bytes * 2 chars/byte)."""
        token = make_token("4111111111111111")
        salt_hex = token.split("$")[0]
        assert len(salt_hex) == 32, (
            f"Salt hex length {len(salt_hex)} != 32; expected 16-byte salt"
        )


# ===========================================================================
# Finding 5 [Medium] -- calculate_average([]) returns 0.0, which is the same
#   value as a list whose real average is zero (e.g. [-1, 0, 1]).
# ===========================================================================

class TestFinding5_EmptyListAverage:
    """calculate_average([]) should raise an exception, not return 0.0."""

    def test_empty_list_currently_returns_zero_confirming_bug(self):
        """Confirm the bug: calculate_average([]) returns 0.0 instead of raising."""
        result = calculate_average([])
        assert result == 0.0, (
            "calculate_average([]) no longer returns 0.0 -- "
            "the bug may have been fixed; remove or rewrite this test"
        )

    def test_empty_list_is_ambiguous_with_zero_average_dataset(self):
        """Demonstrate the ambiguity: both inputs return the same 0.0."""
        empty_result = calculate_average([])
        zero_avg_result = calculate_average([-1, 0, 1])
        assert empty_result == zero_avg_result, (
            "The two results now differ -- ambiguity resolved; update this test"
        )

    def test_empty_list_should_raise(self):
        """Correct behaviour: an empty list should raise ValueError or similar."""
        with pytest.raises((ValueError, ZeroDivisionError, TypeError)):
            result = calculate_average([])
            pytest.fail(
                f"calculate_average([]) returned {result!r} instead of raising"
            )

    def test_non_empty_lists_still_return_correct_average(self):
        """Sanity check: normal inputs must not be broken by any future fix."""
        assert calculate_average([2, 4, 6]) == 4.0
        assert calculate_average([1]) == 1.0
        assert calculate_average([-1, 0, 1]) == 0.0


# ===========================================================================
# Finding 6 [Medium] -- get_user_name() returns "" for three distinct states:
#   None input, missing "name" key, and empty name value.
# ===========================================================================

class TestFinding6_GetUserNameAmbiguity:
    """get_user_name() conflates three distinct error conditions into a single ''."""

    # -- Confirm current (buggy) behaviours --

    def test_none_input_currently_returns_empty_string_confirming_bug(self):
        """Confirm bug: get_user_name(None) -> '' instead of raising."""
        assert get_user_name(None) == ""

    def test_missing_name_key_currently_returns_empty_string_confirming_bug(self):
        """Confirm bug: get_user_name({'id': 1}) -> '' instead of raising."""
        assert get_user_name({"id": 1}) == ""

    def test_empty_name_value_currently_returns_empty_string_confirming_bug(self):
        """Confirm bug: get_user_name({'name': ''}) -> '' instead of raising."""
        assert get_user_name({"name": ""}) == ""

    def test_all_three_error_states_are_indistinguishable(self):
        """All three bad inputs return identical '' -- caller cannot tell them apart."""
        r1 = get_user_name(None)
        r2 = get_user_name({"id": 99})
        r3 = get_user_name({"name": ""})
        assert r1 == r2 == r3 == "", (
            "Results differ -- ambiguity may have been resolved; update this test"
        )

    # -- Desired (fixed) behaviours --

    def test_none_input_should_raise(self):
        """Correct behaviour: None user should raise TypeError or ValueError."""
        with pytest.raises((TypeError, ValueError)):
            result = get_user_name(None)
            pytest.fail(f"get_user_name(None) returned {result!r} instead of raising")

    def test_missing_key_should_raise(self):
        """Correct behaviour: missing 'name' key should raise KeyError or ValueError."""
        with pytest.raises((KeyError, ValueError)):
            result = get_user_name({"id": 42})
            pytest.fail(
                f"get_user_name({{'id': 42}}) returned {result!r} instead of raising"
            )

    def test_empty_name_should_raise(self):
        """Correct behaviour: empty name value should raise ValueError."""
        with pytest.raises(ValueError):
            result = get_user_name({"name": ""})
            pytest.fail(
                f"get_user_name({{'name': ''}}) returned {result!r} instead of raising"
            )

    def test_valid_user_returns_uppercased_name(self):
        """Sanity check: a properly formed user dict must still work correctly."""
        assert get_user_name({"name": "alice"}) == "ALICE"
        assert get_user_name({"name": "Bob"}) == "BOB"
