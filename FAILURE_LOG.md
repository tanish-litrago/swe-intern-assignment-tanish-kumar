# FAILURE_LOG

Real problems from the AI-assisted build (Claude was used to write the first version of the code), in the
order they happened. Each entry: what went wrong, how it was noticed, what changed, how the fix was verified.

## 1. Plan forgot the credit-note sign in V1
- **What went wrong:** the first plan defined V1 as `qty x price / PE x (1 - discount) = line_total`.
  For credit notes `line_total` is negative while quantity and price are positive, so INV-03 would have
  FAILED V1 for no reason (an AI planning error).
- **How noticed:** cross-checking the plan against the assignment text and the INV-03 numbers before coding.
- **What changed:** V1 multiplies the expected value by -1 for credit notes; V7 is defined on amounts only
  (not quantity or unit price).
- **How verified:** `test_credit_note_sign_is_handled_in_v1`; INV-03 passes V1 and V7 in the report.

## 2. Word extraction glued the price and the PE column
- **What went wrong:** with pdfplumber's default `x_tolerance=3`, `14,60` and `100` (INV-01 pos 5) became one
  token `14,60100`.
- **How noticed:** printing word coordinates for INV-01: the row showed `14,60100` while `pdftotext -layout`
  showed two columns.
- **What changed:** `extract_words(x_tolerance=1)` in `page_lines`, with a comment explaining why.
- **How verified:** INV-01 now equals `INV-01_expected_output.json` exactly (`test_inv01_matches_expected_output`),
  including the 400 pcs per 100 line.

## 3. Variant generator printed `0,152` as `0,15`
- **What went wrong:** my test-PDF generator formatted every price with two decimals, so variant D contained a
  different price than its expected JSON (a bug in the generator, not in the extractor).
- **How noticed:** the round-trip test of variant D showed `unit_price got 0.15 exp 0.152`.
- **What changed:** a separate `price_de()` with 2-3 decimals.
- **How verified:** variant D matches exactly (`test_own_variants_extract_exactly[D_...]`).

## 4. `Decimal("10").normalize()` produced `1E+1`
- **What went wrong:** the generator wrote the discount text as `abzgl. Sonderrabatt 1E+1 %`; the extractor read
  the number before `%` and returned a discount of 1.0.
- **How noticed:** same variant D diff: `discount_percent got 1.0 exp 10.0`.
- **What changed:** `pct_de()` uses `format(x.normalize(), "f")`, which gives `10`.
- **How verified:** variant D passes; the same bug was removed from the v1 discount column and the Skonto text.

## 5. Guessed dependency versions
- **What went wrong:** the first `requirements.txt` contained version numbers written from memory, which did not
  match the versions that were installed and tested (e.g. pdfplumber 0.11.7 vs 0.11.9).
- **How noticed:** `pip list` after installing showed different versions.
- **What changed:** `requirements.txt` now pins exactly the tested versions.
- **How verified:** a fresh virtualenv + `pip install -r requirements.txt` + `pytest` (37 passed) and a clean
  clone run of `extract.py` and `validate.py`.
