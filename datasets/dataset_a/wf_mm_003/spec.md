# Workflow: Medical PII Anonymization

## Context
Extracted medical document text must be anonymized before storage. Doctor names, hospital names, clinic addresses, phone numbers, emails, and staff signatures are replaced with tokens. All clinical values, lab results, dates, dosages, and diagnoses are preserved exactly.

## Trigger
Text has been extracted from a medical PDF and is ready for anonymization.

## Steps
1. Receive the extracted text from the PDF.
2. Apply regex-based PII detection for structured patterns: phone numbers, emails, signature fields.
3. Apply NER-based detection for unstructured names using a medical NER model.
4. Replace all detected PII with tokens: doctor names to [MEDICO], hospitals to [HOSPITAL], addresses to [DIRECCION].
5. Validate that all clinical values, dates, and lab results from the original are still present.
6. Record the anonymization count and token locations in the metadata log.

## Constraints
- REMOVE: doctor names, hospital names, clinic addresses, phone numbers, emails, staff signatures.
- PRESERVE: all clinical values, lab results, dates, dosages, diagnoses, medication names.
- ALL CAPS hospital names must be caught by case-insensitive patterns.
