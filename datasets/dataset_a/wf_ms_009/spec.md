# Workflow: Full Clinical Analysis Pipeline

## Context
The complete end-to-end pipeline from PDF upload through anonymization, wiki building, literature search, adversarial analysis, and two-tier report generation. Anonymization is a hard gate.

## Trigger
A user uploads a patient medical history PDF.

## Steps
1. Receive the PDF upload from the authenticated user.
2. Extract text using digital extraction with OCR fallback.
3. Anonymize the extracted text. If anonymization fails, abort the entire pipeline.
4. Ingest the anonymized text into the per-case wiki. Encrypt all wiki content.
5. Once 3 or more wiki pages exist, trigger PubMed literature search.
6. Run the adversarial analysis loop for up to 8 iterations.
7. Check for convergence after each iteration.
8. Validate all NCT numbers in findings.
9. Generate the two-tier report (documented vs inferred).
10. Update the case wiki with the final findings.
11. Log the complete pipeline run.
12. Validate the final report has no unanonymized PII.
13. Serve the encrypted report to the authenticated user.

## Constraints
- HARD GATE: anonymization must succeed before any data reaches external AI providers.
- All LLM prompts, responses, wiki content, and report content are encrypted at rest.
- Adversarial loop: MAX_ITERATIONS = 8, CONVERGENCE_THRESHOLD = 0.10.
- Two-tier findings must remain separated throughout the pipeline.
- Full audit trail required.
