# Kessler fingerprint: PDF to JSON extractor + validator

Extracts invoices and credit notes of the supplier **Kessler Industrietechnik GmbH** into JSON that follows
`data/output_schema.json`, and checks that the printed numbers add up.
Developed and tested on Ubuntu (WSL2), Python 3.12.

## Setup and run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python extract.py data/INV-0*.pdf        # writes outputs/<pdf name>.json (schema-checked)
python validate.py outputs/              # writes outputs/validation_report.md
python -m pytest -q                      # 37 tests
```

`extract.py <pdf>` works for one file too. An unknown layout stops with a clear message and exit code 2.
`data/` holds the files from the assignment pack (fictional documents, schema, INV-01 expected output).

## Design

```
extract.py            CLI: detect layout -> parse -> validate against schema -> write JSON
validate.py           CLI: checks V1-V7 on outputs/*.json -> validation_report.md
kessler/helpers.py    generic: German numbers/dates, line grouping, column assignment, address block, JSON output
kessler/detect.py     chooses the layout from the table header words, raises UnknownLayout otherwise
kessler/layout_v1.py  supplier logic for INV-01..04 (label block top right, PE and Rab. columns, carry-over rows)
kessler/layout_v2.py  supplier logic for INV-05 (new format: other labels, no PE column, discount rows)
tests/                pytest + tests/make_variants.py (our own synthetic Kessler-style PDFs)
```

Principles:
- **Extract what is printed.** Wrong values (INV-04, pos 7) are written as printed and reported by the validator.
- **Columns come from the header row** of each page (right-aligned numbers by right edge, text by left edge),
  not from fixed coordinates.
- **Supplier logic is separate from generic helpers.** One module per layout; the detector picks one.
- **Money is `Decimal`** until it is written to JSON.

### Validation report
`validate.py` prints a PASS/FAIL table (documents x V1..V7) and, per document, the numbers behind every check.
Failures name the line, expected vs. printed and the difference, plus a *hypothesis* for the cause (rounding,
digit transposition, consistency with the totals). Credit notes are compared with the sign flipped in V1
(quantity and price stay positive, totals are negative). Result on the pack: only **INV-04** fails
(V1 and V2, pos 7: printed 1.284,52 instead of 1.248,52, difference +36,00; the printed net total matches the
recomputed value, so the line is probably the typo).

### Own variants (robustness proof)
`tests/make_variants.py` generates five PDFs of our own, with their expected output: columns shifted by 8 pt,
a two-page invoice with carry-over rows, minimal fields, the new layout with discount rows, and an unknown
layout (must raise `UnknownLayout`). These are not part of the assignment pack.

### How to add a layout
1. Create `kessler/layout_xx.py` with `HEADER_WORDS`, `_columns(header_line)` and `parse(pdf)`.
2. Register it in `kessler/detect.py`.
3. Add a variant to `tests/make_variants.py` and a test.

## Known limitations (shortcuts)
- Only text-layer PDFs. **No OCR; the optional scan INV-06 was not attempted.**
- Only the Kessler supplier and these two layouts; German formats only.
- v2 prints no net per VAT rate: it is derived from the line totals. v2 Skonto is always `null`
  (only "Kein Skontoabzug" was seen).
- Skonto given as "N Tagen ab Rechnungsdatum" is converted to a date (document date + N days).
- `net_total` / `vat_total` are sums of the printed per-rate values (no total lines are printed in v1).
- The label block is assumed right of x=340 (v1) and the buyer address right of x=330 (v2).
- Quantities wider than the gap to the description (e.g. `1.000.000`) could be mis-assigned.
- A discount row placed *above* its item, or two discount rows for one item, is not handled.
- Header block and the first table header must be on page 1.
