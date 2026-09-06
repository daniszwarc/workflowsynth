# Workflow: Document Upload and Pipeline Trigger

## Context
Editors and admins upload business documents (PDF, DOCX, TXT) and route them to the appropriate extraction pipeline based on document type.

## Trigger
An editor or admin uploads a document via the knowledge base interface.

## Steps
1. Receive the document upload with file and document type selection.
2. Authenticate the user and verify Editor or Admin role.
3. Validate the uploaded file format matches the selected document type.
4. Store the uploaded file in the uploads volume.
5. Send the document to the pipeline service to trigger extraction.

## Constraints
- Only Editor, Admin, and Developer roles can upload documents.
- SED documents must be DOCX format.
- Upload path is served with Cache-Control: private, no-store.
