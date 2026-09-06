# Workflow: Patient Data Anonymization

## Context
A hard gate that anonymizes extracted medical text before any data reaches an external AI provider. Anonymization failure aborts the pipeline -- there is no fallback to sending unanonymized data.

## Trigger
Text has been extracted from a medical PDF.

## Steps
1. Receive the extracted text.
2. Apply regex pre-pass to detect structured PII.
3. Apply local NER model pass with confidence threshold 0.85.
4. Validate that anonymization confidence meets the required threshold. If not, abort.
5. Replace all detected PII with anonymization tokens.
6. Log the anonymization event in the audit trail.

## Constraints
- HARD GATE: anonymization failure must abort the pipeline. Never fall through to sending unanonymized data.
- NER confidence threshold: 0.85.
- Anonymization event must always be logged.
