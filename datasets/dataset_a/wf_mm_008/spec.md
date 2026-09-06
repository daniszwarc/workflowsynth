# Workflow: Full Medical Document Processing Pipeline

## Context
The complete end-to-end pipeline that processes a medical PDF from Google Drive into an anonymized, verified, version-controlled Markdown document. Used to process hundreds of medical documents spanning years for a patient with complex oncology history.

## Trigger
New medical PDF documents are available in the Google Drive folder.

## Steps
1. Authenticate with Google Drive using a service account.
2. List PDF files and identify new documents not yet processed.
3. Download each new PDF to the local processing directory.
4. Extract text using digital extraction with OCR fallback. Compute SHA-256 hash.
5. Anonymize the extracted text: replace doctor names, hospital names, addresses with tokens. Preserve all clinical values.
6. Structure the anonymized text into Markdown using the primary AI model. Apply fallback if primary fails verification.
7. Verify: confirm all numbers and dates from the source appear unchanged in the Markdown. Assign confidence level.
8. If confidence = low, add to the review queue and skip commit.
9. Write the Markdown file and metadata JSON to raw/.
10. Authenticate for git operations and create a commit.
11. Every 10 documents, push all pending commits to the remote repository.
12. Clean up the local tmp/ directory after processing.
13. Write a run log entry with processing statistics.

## Constraints
- The original PDF is never modified -- all operations are read-only on the source.
- PII anonymization must run BEFORE AI structuring.
- Verification must run BEFORE committing.
- Documents with confidence = low go to review queue, not to raw/.
- Full audit trail required for every document.
