from pathlib import Path

import pytest

from extract import extract
from validate import CHECKS, validate

DATA = Path(__file__).resolve().parent.parent / "data"


def results(prefix):
    return validate(extract(next(DATA.glob(prefix + "*.pdf"))))


@pytest.mark.parametrize("prefix", ["INV-01", "INV-02", "INV-03", "INV-05"])
def test_clean_documents_pass_everything(prefix):
    assert all(results(prefix)[c][0] for c in CHECKS)


def test_inv04_fails_v1_and_v2_only_and_explains_why():
    r = results("INV-04")
    assert [c for c in CHECKS if not r[c][0]] == ["V1", "V2"]
    assert any("pos 7" in line and "difference +36.00" in line and "transposition" in line for line in r["V1"][1])
    assert any("equals the V1 error" in line for line in r["V2"][1])


def test_credit_note_sign_is_handled_in_v1():
    assert results("INV-03")["V1"][0] and results("INV-03")["V7"][0]
