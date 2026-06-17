# Test Patterns Reference

A quick-reference for writing clear, maintainable tests in a TDD workflow.
These patterns apply primarily to Python (pytest), with notes where other
frameworks differ.

---

## Arrange-Act-Assert (AAA)

The universal structure for a unit test. Every test body has three parts,
separated by a blank line:

```python
def test_apply_discount_reduces_price_by_percentage():
    # Arrange
    cart = Cart(items=[Item("book", price=20.00)])

    # Act
    result = cart.apply_discount(percent=10)

    # Assert
    assert result.total == 18.00
```

- **Arrange** — set up the object(s) under test and any inputs.
- **Act** — call the one thing being tested.
- **Assert** — verify one logical outcome (may be multiple `assert` lines
  if they all check the same thing, e.g., status code + body).

One reason to fail per test. If you need `assert a` *and* `assert b` where
`b` is a completely independent concern, split into two tests.

---

## Naming

`test_<unit>_<scenario>_<expected_outcome>` is clearer than `test_1`.

```python
# Good
def test_parse_date_with_invalid_format_raises_value_error():
def test_transfer_funds_when_balance_insufficient_raises_error():
def test_get_user_returns_none_when_not_found():

# Avoid
def test_parse():
def test_transfer_2():
def test_error():
```

In pytest, test names become the failure output — make them self-documenting.

---

## Fixtures (pytest)

Use fixtures for shared setup. Keep them small and specific.

```python
# conftest.py
import pytest
from myapp import create_app, db

@pytest.fixture
def app():
    app = create_app({"TESTING": True, "DATABASE": ":memory:"})
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()
```

Fixture scope controls how often they run:
- `scope="function"` (default) — fresh per test. Use for state that mutates.
- `scope="module"` — once per file. Use for expensive read-only setup.
- `scope="session"` — once per run. Use for DB migrations, compiled assets.

---

## Parametrize

Test the same logic with multiple inputs without duplicating the body:

```python
import pytest

@pytest.mark.parametrize("amount,expected", [
    (0,    "zero"),
    (1,    "one"),
    (2,    "two"),
    (100,  "many"),
    (-1,   "negative"),
])
def test_classify_amount(amount, expected):
    assert classify(amount) == expected
```

Use this when the inputs and outputs change but the assertion shape is identical.
Don't use it when the scenario description needs to vary — write separate tests.

---

## Exception testing

```python
import pytest

def test_divide_by_zero_raises():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

# Check the message too
def test_negative_price_raises_with_message():
    with pytest.raises(ValueError, match="price must be non-negative"):
        Item(price=-5)
```

Never wrap the assertion in the `with` block — it won't be executed:

```python
# Wrong
with pytest.raises(ValueError):
    result = risky()
    assert result == "x"   # dead line — never reached if exception is raised
```

---

## Mocking (pytest-mock / unittest.mock)

Mock at the boundary of the unit under test — not deep inside it.

```python
def test_send_welcome_email_calls_mailer(mocker):
    mock_send = mocker.patch("myapp.mailer.send")

    register_user("alice@example.com")

    mock_send.assert_called_once_with(
        to="alice@example.com",
        subject="Welcome!",
    )
```

Prefer dependency injection over patching when the design allows it — a
function that accepts a `mailer` argument is easier to test than one that
imports it internally.

---

## Test doubles: when to use which

| Double | Use when |
|--------|----------|
| **Stub** | You need the dependency to return a fixed value. |
| **Mock** | You need to assert *how* the dependency was called. |
| **Fake** | You need a real but simplified implementation (e.g., an in-memory DB). |
| **Spy** | You want to let the real call through but also assert on it. |

Mocks are not free: they couple your test to implementation details. Prefer
stubs and fakes where possible; reach for mocks only when the call *itself*
is the behaviour under test (e.g., "sends exactly one email").

---

## Test file layout

Mirror the source tree under `tests/`:

```
myapp/
  auth/
    login.py
    tokens.py
  orders/
    cart.py

tests/
  auth/
    test_login.py
    test_tokens.py
  orders/
    test_cart.py
  conftest.py   ← shared fixtures
```

Each `test_*.py` file tests one module. If a file grows beyond ~150 lines,
consider splitting by scenario group, not by arbitrary size.

---

## What makes a test "failing for the right reason"

A new test must fail *because of missing business logic*, not because of:
- Import errors (module doesn't exist yet — create a stub first)
- `AttributeError` (the method doesn't exist — add a stub that raises `NotImplementedError`)
- `SyntaxError` in the test itself

Check the failure message before writing implementation. It should read like
a business rule violation:

```
AssertionError: assert 0 == 18.0
```

not like an environment problem:

```
ModuleNotFoundError: No module named 'cart'
```

If it's an environment error, fix the stub first and re-run — only proceed
to implementation once the failure is a meaningful assertion failure.

---

## Minimal stub pattern

When a class or function referenced in a test doesn't exist yet, add a stub
so the test can *run* and fail on the assertion, not on import:

```python
# cart.py  (stub — written before implementation)
class Cart:
    def __init__(self, items):
        self.items = items

    def apply_discount(self, percent):
        raise NotImplementedError
```

The test now fails with `NotImplementedError`, which is still not the right
failure. Run once more — after replacing `raise NotImplementedError` with
`return self` or `return 0` — to confirm the assertion fires correctly.
Then implement properly.
