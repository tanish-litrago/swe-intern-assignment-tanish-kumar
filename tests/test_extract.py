import json
from pathlib import Path

import pytest
from jsonschema import validate

from extract import SCHEMA, extract
from kessler.helpers import UnknownLayout
from make_variants import make_all

DATA = Path(__file__).resolve().parent.parent / "data"
PDFS = sorted(DATA.glob("INV-0[1-5]*.pdf"))


def load(prefix):
    return extract(next(DATA.glob(prefix + "*.pdf")))


def test_inv01_matches_expected_output():
    expected = json.loads((DATA / "INV-01_expected_output.json").read_text(encoding="utf-8"))
    assert load("INV-01") == expected


@pytest.mark.parametrize("pdf", PDFS, ids=lambda p: p.name)
def test_every_output_matches_schema(pdf):
    validate(extract(pdf), SCHEMA)


def test_inv02_carry_over_rows_are_not_items_and_quantity_is_split_from_description():
    d = load("INV-02")
    assert [i["position"] for i in d["line_items"]] == list(range(10, 270, 10))
    item30 = d["line_items"][2]
    assert (item30["quantity"], item30["description"]) == (1000.0, "Sechskantschraube DIN 933 M10x40 8.8 verz.")
    assert d["totals"]["net_by_vat_rate"] == {"19": 4787.18, "7": 318.8}


def test_inv03_credit_note():
    d = load("INV-03")
    assert d["document_type"] == "credit_note" and d["referenced_invoice"] == "RE-2026-10133"
    assert [i["line_total"] for i in d["line_items"]] == [-225.8, -155.0, -19.25]
    assert d["totals"]["gross_total"] == -476.06
    assert d["service_date"] is None and d["due_date"] is None and d["cash_discount"] is None


def test_inv04_extracts_the_printed_wrong_line_total_as_printed():
    d = load("INV-04")
    assert d["line_items"][6]["line_total"] == 1284.52  # printed value, not the recomputed 1248.52
    assert d["cash_discount"] == {"percent": 3.0, "until": "2026-10-21", "amount": 188.35}
    assert d["service_date"] == "2026-10-13"  # not the 'Liefertermin KW 42/2026' header line


def test_inv05_new_layout():
    d = load("INV-05")
    assert d["document_number"] == "2026-R-00117" and d["buyer"]["name"] == "Rheinwerk Anlagenbau AG"
    assert len(d["line_items"]) == 5  # the discount row is not an item
    item2 = d["line_items"][1]
    assert (item2["discount_percent"], item2["line_total"]) == (3.0, 451.63)
    item3 = d["line_items"][2]
    assert (item3["unit_price"], item3["price_unit"]) == (0.152, 1.0)
    assert d["totals"]["net_by_vat_rate"] == {"19": 925.33, "7": 49.8}


@pytest.mark.parametrize("name", ["A_shifted_columns", "B_two_pages", "C_minimal", "D_new_layout_two_discount_rows"])
def test_own_variants_extract_exactly(name, tmp_path):
    pdf, expected = make_all(tmp_path)[name]
    assert extract(pdf) == expected


def test_unknown_layout_fails_loudly(tmp_path):
    pdf, _ = make_all(tmp_path)["E_unknown_layout"]
    with pytest.raises(UnknownLayout):
        extract(pdf)
