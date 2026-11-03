# MARKING_NOTES: fingerprint for Kessler Industrietechnik GmbH

Two layouts are supported. **v1** = INV-01 to INV-04, **v2** = INV-05 (new format since 01.10.2026).
All positions come from `pdfplumber` words with coordinates (`x_tolerance=1`). "Header row" below means the
table header line, whose word positions define the columns on every page, so small drifts do not matter.
"Right block" = the label/value area top right (v1, words with x0 >= 340); in v2 the labels are top left.

## Per-field notes

| Field | How it is located | Why it is robust | What would break it |
|---|---|---|---|
| `document_type` | v1: label `Rechnungs-Nr.` = invoice, `Gutschrift-Nr.` = credit_note. v2: always invoice (label `Rechnung Nr.`) | Uses the label that also carries the number | A new document type (e.g. Storno) with another label: no match, `KeyError`, loud failure |
| `document_number` | Text after the label (`Rechnungs-Nr.` / `Gutschrift-Nr.` / v2 `Rechnung Nr.`) on page 1, before the table header | Label-based, not position-based; page 2/3 repeats are ignored because only lines above the page-1 table header are read | Label wording changes; number printed below the table header |
| `document_date` | v1: label `Datum`. v2: `Rechnungsdatum`. Parsed by `parse_date` (numeric or month name) | Two date formats handled in one tested helper | A third date format (e.g. `19-Oct-2026`) raises `ValueError` |
| `service_date` | v1: `Leistungsdatum`; v2: `Lieferdatum`; null if the label is absent | Absence gives null, never a guess. The header line `Liefertermin KW 42/2026` is deliberately not used | Supplier prints the service date under another label |
| `due_date` | v1: `Zahlbar bis <date> ohne Abzug`; v2: `(bis <date>)` in the `Zahlungsziel` line; null otherwise (credit note) | Anchored on the phrase, searched on all pages | Phrase reworded, or a due date given only as "30 Tage" (would be null, see README limitations) |
| `currency` | Constant `EUR` | Schema allows only EUR | Another currency would need real detection |
| `supplier.name` | Return-address line (`<name> · street · postal city`); text before the first `·` | The postal-code pattern distinguishes it from the logo line `Industrietechnik GmbH · seit 1987` | Address line without the `·` separators |
| `supplier.vat_id` | Regex `USt-IdNr. DE\d{9}` anywhere in the text (page footer), spaces removed | Footer is on every page | Footer missing or ID in another format |
| `buyer.name` | First line of the address block under the return-address line (v1 left column, v2 right column) | Attention lines (`Abt.`, `z. Hd.`) are filtered out | A company name that wraps over two lines |
| `buyer.street` | The line directly before the `NNNNN City` line, after attention lines are removed | Independent of how many attention lines exist | Street line placed after the postal line |
| `buyer.postal_code`, `buyer.city` | Line matching `^\d{5} <city>`; country line (`DEUTSCHLAND`) is ignored | Pattern, not position | Non-German postal codes |
| `buyer.customer_number` | Label `Kunden-Nr.` (v1) / `Kundennummer` (v2) | Label-based | Label renamed |
| `order_reference` | Label `Ihre Bestellung` (v1) / `Bestellnummer` (v2); v1 keeps only the first token, which drops `vom <date>` | The number is always the first token | Order number containing spaces |
| `delivery_note_number` | Label `Lieferschein-Nr.` (v1) / `Lieferschein` (v2) | Label-based | Several delivery notes on one document |
| `referenced_invoice` | v1 credit notes: label `Bezug Rechnung`, first token (drops `v. <date>`); null elsewhere | Same first-token rule as order_reference | Reference to several invoices |
| `line_items[].position` | Cell in the `Pos.` column that is all digits; `int()` removes leading zeros (`001` -> 1) | A row is an item only if it has a numeric position, so carry-over rows and notes are never items | Items without a position number |
| `article_number` | Cell in the `Art.-Nr.` (v1) / `Artikel` (v2) column | Column read from header row | Article number wider than its column |
| `description` | Cell in the description column plus every following row without position (notes, batch, discount-free references), joined with single spaces | Handles any number of extra lines; `Pos. 12` inside a note is not treated as a position because it sits in the description column | Note lines that start left of the description column |
| `quantity` | `Menge` column, matched on the **right edge** (x1) of the word; `parse_de_number` | Quantities like `1.000` touch the description text but are right-aligned under the header, so the right edge separates them | A quantity wider than the gap, e.g. `1.000.000` |
| `unit` | `ME` (v1) / `Einh.` (v2) column, matched on the left edge | Left-aligned text column | Units wider than the column |
| `unit_price` | `Einzelpreis` / `Preis/Einh.` column, right edge, tolerance 10 pt (data ends 7 pt right of the header) | Tolerance covers the header/data offset; `€` glyphs are dropped | Two numeric columns closer than 10 pt |
| `price_unit` | v1: `PE` column, 1 if empty. v2: always 1 (no PE column; "Preis je Stück" stays in the description) | Matches the schema rule "1 if not printed" | A v2 document that prints a per-100 price in another way |
| `discount_percent` | v1: `Rab. %` column, null if empty. v2: number before `%` in an `abzgl. ...` row, applied to the item above | Discount rows never become items | A discount row above its item, or two discount rows on one item (second overwrites the first) |
| `line_total` | `Gesamt` / `Betrag` column; trailing minus gives a negative value. v2: item amount plus the (negative) discount row | Printed value is kept, never recomputed | Amount column far off from the header edge |
| `vat_rate` | `USt %` (v1) / `MwSt` (v2, `%` stripped) column, `int` | Plain integer | Rates with decimals |
| `totals.net_by_vat_rate` | v1: lines `Nettobetrag <r> % USt`. v2: **derived** by summing line totals per rate (not printed) | Decision documented and asked to the organizers | If the supplier prints a different per-rate net in a v2 document |
| `totals.vat_by_vat_rate` | v1: `zzgl. <r> % USt auf <net>` (last token). v2: `MwSt <r>%` lines | Printed values | Label rewording |
| `totals.net_total` | v1: sum of the printed per-rate nets (no total net line is printed). v2: `Summe netto` | Matches INV-01's expected output | A document that prints a total net different from the sum of its parts |
| `totals.vat_total` | Sum of the printed per-rate VAT amounts (neither layout prints a VAT total) | Same | Same |
| `totals.gross_total` | `Rechnungsbetrag` / `Gutschriftsbetrag` (v1), `Gesamtbetrag` (v2) | Anchored on the label | Label rewording |
| `cash_discount.percent`, `.amount` | v1 Skonto sentence: `... <p> % Skonto (= <amount> EUR)`; v2: null (`Kein Skontoabzug`) | Regex on the full sentence | Skonto wording changes |
| `cash_discount.until` | v1: date in `Bei Zahlung bis <date>`; or **computed** = document date + N days for `innerhalb von N Tagen ab Rechnungsdatum` (INV-04) | Both wordings covered; computed case is documented | Skonto period counted from another date |

## INV-05 question (max. 200 words)

INV-05 changed almost everything visible. The label block moved to the left and the buyer address to the right.
Labels and column order changed, the PE and Rab. columns disappeared, dates use month names, amounts carry a
euro sign, and a discount became its own row under the item. I added `layout_v2.py` with its own label list,
its own column map (read from the header row, like before) and a rule that folds a discount row into the item
above. The net per VAT rate is not printed, so it is derived from the line totals. `layout_v1.py` was not
touched. Both modules share the generic helpers (number and date parsing, line grouping, column assignment,
address parsing); the month-name date format lives in `parse_date`, tested for both formats. A small detector
chooses the module from the table header words and raises `UnknownLayout` otherwise, so a new layout can never
be parsed silently with the wrong rules. Tests pin INV-01 exactly and the key fields of INV-02 to INV-05, plus
four own variants, so a change for one layout that breaks another shows up immediately.
