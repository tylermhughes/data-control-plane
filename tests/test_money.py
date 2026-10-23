from decimal import Decimal

import pytest

from app.schemas.common import format_money


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("25000", "25000.00"),
        ("25000.0000", "25000.00"),
        ("30000.5", "30000.50"),
        ("0.0125", "0.0125"),
        ("1.123", "1.123"),
        ("0", "0.00"),
        ("1E+3", "1000.00"),
    ],
)
def test_money_has_one_canonical_form(value: str, expected: str) -> None:
    assert format_money(Decimal(value)) == expected
