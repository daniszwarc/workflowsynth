# Workflow: Medical PDF Upload and Text Extraction

## Context
A clinical research tool accepts patient medical history PDFs for analysis. Text is extracted using digital extraction as primary with OCR as fallback.

## Trigger
A user uploads a medical PDF.

## Steps
1. Receive the PDF upload from the authenticated user.
2. Authenticate the user and verify case access rights.
3. Validate the uploaded file is a valid PDF within the size limit.
4. Attempt text extraction using digital extraction.
5. Apply the quality rule: if too sparse, re-extract using OCR fallback.

## Constraints
- The original PDF is never modified.
- OCR is only used as a fallback.
