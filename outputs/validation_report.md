# Validation report

Checks V1-V7 on the extracted JSON files. A FAIL means the *document* is inconsistent as printed (values are extracted as printed, never corrected). Likely causes are hypotheses, not facts.

| Document | V1 | V2 | V3 | V4 | V5 | V6 | V7 |
|---|---|---|---|---|---|---|---|
| INV-01_RE-2026-10418 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| INV-02_RE-2026-10431 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| INV-03_GS-2026-00872 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| INV-04_RE-2026-10457 | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS |
| INV-05_2026-R-00117 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

Check definitions: V1 = line total = qty x price / PE x (1 - discount); V2 = sum of lines = net per VAT rate; V3 = net x rate = VAT per rate; V4 = net + VAT = gross; V5 = supplier VAT ID is DE + 9 digits; V6 = dates valid, due date not before document date; V7 = sign matches document type

## INV-01_RE-2026-10418 (invoice RE-2026-10418)

- **V1 PASS** - line total = qty x price / PE x (1 - discount)
  - 6 lines checked, largest difference 0.00
- **V2 PASS** - sum of lines = net per VAT rate
  - 19% : sum of lines 801.47, printed net 801.47, difference +0.00
- **V3 PASS** - net x rate = VAT per rate
  - 19% : net 801.47 x 19% = 152.28, printed VAT 152.28, difference +0.00
- **V4 PASS** - net + VAT = gross
  - net 801.47 + VAT 152.28 = 953.75, printed gross 953.75, difference +0.00
- **V5 PASS** - supplier VAT ID is DE + 9 digits
  - supplier VAT ID DE287364519
- **V6 PASS** - dates valid, due date not before document date
  - document_date 2026-10-06 valid
  - service_date 2026-10-02 valid
  - due_date 2026-11-05 valid
  - cash discount until 2026-10-16 valid
  - due date not before document date
- **V7 PASS** - sign matches document type
  - invoice: 11 of 11 amounts have the expected sign (positive); quantity and unit price excluded

## INV-02_RE-2026-10431 (invoice RE-2026-10431)

- **V1 PASS** - line total = qty x price / PE x (1 - discount)
  - 26 lines checked, largest difference 0.00
- **V2 PASS** - sum of lines = net per VAT rate
  - 7% : sum of lines 318.80, printed net 318.80, difference +0.00
  - 19% : sum of lines 4787.18, printed net 4787.18, difference +0.00
- **V3 PASS** - net x rate = VAT per rate
  - 19% : net 4787.18 x 19% = 909.56, printed VAT 909.56, difference -0.00
  - 7% : net 318.80 x 7% = 22.32, printed VAT 22.32, difference +0.00
- **V4 PASS** - net + VAT = gross
  - net 5105.98 + VAT 931.88 = 6037.86, printed gross 6037.86, difference +0.00
- **V5 PASS** - supplier VAT ID is DE + 9 digits
  - supplier VAT ID DE287364519
- **V6 PASS** - dates valid, due date not before document date
  - document_date 2026-10-09 valid
  - service_date 2026-10-07 valid
  - due_date 2026-11-08 valid
  - cash discount until 2026-10-19 valid
  - due date not before document date
- **V7 PASS** - sign matches document type
  - invoice: 33 of 33 amounts have the expected sign (positive); quantity and unit price excluded

## INV-03_GS-2026-00872 (credit_note GS-2026-00872)

- **V1 PASS** - line total = qty x price / PE x (1 - discount)
  - 3 lines checked, largest difference 0.00
- **V2 PASS** - sum of lines = net per VAT rate
  - 19% : sum of lines -400.05, printed net -400.05, difference +0.00
- **V3 PASS** - net x rate = VAT per rate
  - 19% : net -400.05 x 19% = -76.01, printed VAT -76.01, difference -0.00
- **V4 PASS** - net + VAT = gross
  - net -400.05 + VAT -76.01 = -476.06, printed gross -476.06, difference +0.00
- **V5 PASS** - supplier VAT ID is DE + 9 digits
  - supplier VAT ID DE287364519
- **V6 PASS** - dates valid, due date not before document date
  - document_date 2026-10-12 valid
- **V7 PASS** - sign matches document type
  - credit_note: 8 of 8 amounts have the expected sign (negative); quantity and unit price excluded

## INV-04_RE-2026-10457 (invoice RE-2026-10457)

- **V1 FAIL** - line total = qty x price / PE x (1 - discount)
  - 15 lines checked, largest difference 36.00
  - line pos 7 (KI-71004): expected 1248.52, printed 1284.52, difference +36.00; likely cause: printed digits are a permutation of the expected digits: possible digit-transposition typo
- **V2 FAIL** - sum of lines = net per VAT rate
  - 7% : sum of lines 69.80, printed net 69.80, difference +0.00
  - 19% : sum of lines 5249.22, printed net 5213.22, difference +36.00; this equals the V1 error: the printed net matches the recomputed line, so the printed line total (not the totals) is the likely mistake
- **V3 PASS** - net x rate = VAT per rate
  - 19% : net 5213.22 x 19% = 990.51, printed VAT 990.51, difference -0.00
  - 7% : net 69.80 x 7% = 4.89, printed VAT 4.89, difference +0.00
- **V4 PASS** - net + VAT = gross
  - net 5283.02 + VAT 995.40 = 6278.42, printed gross 6278.42, difference +0.00
- **V5 PASS** - supplier VAT ID is DE + 9 digits
  - supplier VAT ID DE287364519
- **V6 PASS** - dates valid, due date not before document date
  - document_date 2026-10-14 valid
  - service_date 2026-10-13 valid
  - due_date 2026-11-13 valid
  - cash discount until 2026-10-21 valid
  - due date not before document date
- **V7 PASS** - sign matches document type
  - invoice: 22 of 22 amounts have the expected sign (positive); quantity and unit price excluded

## INV-05_2026-R-00117 (invoice 2026-R-00117)

- **V1 PASS** - line total = qty x price / PE x (1 - discount)
  - 5 lines checked, largest difference 0.00
- **V2 PASS** - sum of lines = net per VAT rate
  - 7% : sum of lines 49.80, printed net 49.80, difference +0.00
  - 19% : sum of lines 925.33, printed net 925.33, difference +0.00
- **V3 PASS** - net x rate = VAT per rate
  - 19% : net 925.33 x 19% = 175.81, printed VAT 175.81, difference -0.00
  - 7% : net 49.80 x 7% = 3.49, printed VAT 3.49, difference +0.00
- **V4 PASS** - net + VAT = gross
  - net 975.13 + VAT 179.30 = 1154.43, printed gross 1154.43, difference +0.00
- **V5 PASS** - supplier VAT ID is DE + 9 digits
  - supplier VAT ID DE287364519
- **V6 PASS** - dates valid, due date not before document date
  - document_date 2026-10-19 valid
  - service_date 2026-10-16 valid
  - due_date 2026-11-18 valid
  - due date not before document date
- **V7 PASS** - sign matches document type
  - invoice: 12 of 12 amounts have the expected sign (positive); quantity and unit price excluded

## Summary

Failed checks: INV-04_RE-2026-10457: V1, INV-04_RE-2026-10457: V2
