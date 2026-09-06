# Workflow: Medical PDF Download from Google Drive

## Context
A clinical AI platform maintains a library of medical documents for a patient with complex oncology history. PDF documents are stored in a Google Drive folder and must be downloaded securely before processing.

## Trigger
New medical documents are added to the Google Drive folder.

## Steps
1. Authenticate with Google Drive using a service account credentials file.
2. List all PDF files in the designated medical documents Drive folder.
3. Read the list of already-processed documents from the local raw/ directory.
4. Download only the new PDF files to the local tmp/ directory.

## Constraints
- Authentication uses a service account -- no user interaction required.
- Only files matching the naming convention YYYY-MM-DD - Tipo - Descripcion.pdf are processed.
- Already-processed documents are never re-downloaded.
