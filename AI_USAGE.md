# AI_USAGE

## Note on the video
The video is short, so three statements need precision. This file is the accurate version.
- "I tested and verified every issue myself": I reproduced two problems myself in the terminal (the merged numbers
  with x_tolerance=3 on INV-01, and the credit-note sign in V1 on INV-03). The third (V2 comparing a derived value
  with itself for INV-05) was pointed out in DeepLogic AI's reply to my questions.
- "I used Claude to help write the initial code": Claude wrote the first version of the extractor, validator and
  tests. Antigravity ran my verification checks and documentation edits. I reviewed and ran everything.
- "For invoice 5 the tax breakdown is not printed": precisely, the net amount per VAT rate is not printed (the VAT
  amount per rate and the totals are). I derive the net per rate from the line totals; DeepLogic AI confirmed this
  is acceptable.

## Tools and what they were used for
- **Claude (claude.ai chat, with file and code tools):** reading the assignment and the PDFs, planning the architecture in chat,
  analysing the five layouts, writing the first version of the extractor, validator, tests, own variant
  generator and these documents, and running everything in a sandbox. It also ran the OCR experiment for the bonus scan INV-06
  in a sandbox; nothing from it is in the repo.
- **Antigravity (agentic IDE):** running verification checks in WSL (clean clone, tests, output comparison,
  line endings) and applying small documentation edits. It did not change the extractor or validator code.
- No AI-generated data was used as a reference: expected values come from the PDFs
  and `INV-01_expected_output.json`.

## Concrete cases where the AI was wrong or incomplete
1. **Credit-note sign (INV-03).** Claude's first validation plan defined V1 as
   quantity x price / PE x (1 - discount) = line total, with no sign rule. On INV-03 the line totals
   are negative while quantity and price are positive, so V1 would have failed all three lines.
   How I found out: I asked Claude to cross-check the plan against the assignment text, and it
   noticed this before any code was written. I confirmed it by running validate.py without the
   sign flip: INV-03 failed V1 on every line (expected 225.80, printed -225.80).
2. **Glued numbers (INV-01, position 5).** Claude's first word extraction with pdfplumber's default
   settings returned 14,60100: the unit price and the PE column value 100 merged into one token,
   although the layout showed two columns. How I found out: Claude printed the word coordinates
   while we studied the layout. I reproduced it by running extract_words with x_tolerance=3 and 1
   on INV-01.
3. **Circular V2 check (INV-05).** Claude's validator compared the net per VAT rate with the line
   totals it was derived from, so for INV-05 it could never fail. How I found out: the organizers'
   reply to my question pointed it out. V2 now also compares the sum of the lines with the printed
   total net.

Further AI mistakes caught by tests are in FAILURE_LOG (3, 4): two formatting bugs in the AI-written variant generator.

## How the output was verified (not taken on trust)
- The amounts of all five documents were recomputed by hand from the printed text and again by `validate.py`;
  both find the same single inconsistency (INV-04, pos 7).
- INV-01 is compared with the expected JSON; all outputs are checked against `output_schema.json`
  (in `extract.py` and in tests).
- Five own variant PDFs with independently built expected results (including one that must be rejected).
