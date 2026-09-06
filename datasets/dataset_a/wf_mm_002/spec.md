# Workflow: Medical PDF Text Extraction

## Context
Each medical PDF must have its text extracted before processing. The pipeline uses a primary digital extraction method for native PDFs and falls back to OCR for scanned documents.

## Trigger
A PDF file has been downloaded and is ready for text extraction.

## Steps
1. Receive the downloaded PDF file.
2. Attempt text extraction using the primary digital method.
3. Apply the extraction quality rule: if extracted text is too sparse, flag for OCR fallback.
4. If flagged, re-extract using OCR with image rendering.
5. Compute the SHA-256 hash of the original PDF binary and store it in document metadata.

## Constraints
- The original PDF is never modified -- extraction is read-only.
- SHA-256 hash must be computed from the original binary.
- OCR is only used as a fallback -- digital extraction is always attempted first.
