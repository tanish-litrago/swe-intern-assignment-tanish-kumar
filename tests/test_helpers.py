from datetime import date
from decimal import Decimal as D

import pytest

from kessler.helpers import parse_date, parse_de_number


@pytest.mark.parametrize("text,expected", [
    ("1.234,56", D("1234.56")), ("8,45", D("8.45")), ("0,152", D("0.152")), ("1.000", D("1000")),
    ("225,80-", D("-225.80")), ("-13,97", D("-13.97")), ("260,70 €", D("260.70")), ("953,75 EUR", D("953.75")),
])
def test_parse_de_number(text, expected):
    assert parse_de_number(text) == expected


def test_parse_de_number_rejects_garbage():
    with pytest.raises(ValueError):
        parse_de_number("abc")


@pytest.mark.parametrize("text,expected", [
    ("06.10.2026", date(2026, 10, 6)), ("19. Oktober 2026", date(2026, 10, 19)),
    ("1. März 2027", date(2027, 3, 1)), ("18. November 2026", date(2026, 11, 18)),
])
def test_parse_date(text, expected):
    assert parse_date(text) == expected


@pytest.mark.parametrize("text", ["31.02.2026", "12. Foo 2026", "2026-10-06"])
def test_parse_date_rejects_invalid(text):
    with pytest.raises(ValueError):
        parse_date(text)
