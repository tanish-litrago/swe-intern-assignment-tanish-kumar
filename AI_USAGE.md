# AI_USAGE

## Tools and what they were used for
- **Claude (claude.ai chat, with file and code tools):** reading the assignment and the PDFs, planning (`plan.md`),
  analysing the five layouts, writing the first version of the extractor, validator, tests, own variant
  generator and these documents, and running everything in a sandbox.
- No other AI tool. No AI-generated data was used as a reference: expected values come from the PDFs
  and `INV-01_expected_output.json`.

## Two concrete cases where the AI was wrong or incomplete
1. **Validation plan missed credit notes.** The first plan described V1 without the sign rule. Applied literally
   it would mark INV-03 (credit note) as FAIL. It was found when the plan was cross-checked against the brief and
   the INV-03 numbers; V1 now flips the sign for credit notes (see FAILURE_LOG 1, test
   `test_credit_note_sign_is_handled_in_v1`).
2. **Invented dependency pins.** `requirements.txt` first listed version numbers that were not the tested ones.
   Found by comparing with `pip list`; replaced by the exact tested versions (FAILURE_LOG 5).

Further AI mistakes caught by tests are in FAILURE_LOG (2, 3, 4): a token-gluing default in the PDF library and
two formatting bugs in the AI-written variant generator.

## How the output was verified (not taken on trust)
- The amounts of all five documents were recomputed by hand from the printed text and again by `validate.py`;
  both find the same single inconsistency (INV-04, pos 7).
- INV-01 is compared with the expected JSON; all outputs are checked against `output_schema.json`
  (in `extract.py` and in tests).
- Five own variant PDFs with independently built expected results (including one that must be rejected).
