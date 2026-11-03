# AI_USAGE

## Tools and what they were used for
- **Claude (claude.ai chat, with file and code tools):** reading the assignment and the PDFs, planning the architecture in chat,
  analysing the five layouts, writing the first version of the extractor, validator, tests, own variant
  generator and these documents, and running everything in a sandbox.
- **Antigravity (agentic IDE):** running verification checks in WSL (clean clone, tests, output comparison,
  line endings) and applying small documentation edits. It did not change the extractor or validator code.
- No AI-generated data was used as a reference: expected values come from the PDFs
  and `INV-01_expected_output.json`.

## Two concrete cases where the AI was wrong or incomplete
1. The AI's first validation plan defined V1 as qty x price / PE x (1 - discount) = line_total
   with no sign rule. On INV-03 (credit note) the line totals are negative (e.g. 225,80-) while quantity and
   price are positive, so V1 would have failed all three lines for no reason. This was found when the plan
   was cross-checked against the brief (rule 4) and the INV-03 numbers before coding. V1 now flips the sign
   for credit notes; test_credit_note_sign_is_handled_in_v1 covers it (FAILURE_LOG 1).
2. The AI's first word extraction from INV-01 used pdfplumber's default x_tolerance=3 and
   returned '14,60100' for pos 5: unit price 14,60 and the PE column 100 were merged, although the layout
   showed two columns. The AI's plan had not anticipated this. It was found by printing word coordinates.
   page_lines now uses x_tolerance=1 and INV-01 equals the expected output (FAILURE_LOG 2).

Further AI mistakes caught by tests are in FAILURE_LOG (3, 4): two formatting bugs in the AI-written variant generator.

## How the output was verified (not taken on trust)
- The amounts of all five documents were recomputed by hand from the printed text and again by `validate.py`;
  both find the same single inconsistency (INV-04, pos 7).
- INV-01 is compared with the expected JSON; all outputs are checked against `output_schema.json`
  (in `extract.py` and in tests).
- Five own variant PDFs with independently built expected results (including one that must be rejected).
