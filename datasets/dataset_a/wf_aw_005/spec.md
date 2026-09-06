# Workflow: SED Field Extraction and Indexing

## Context
Small Enhancement Documents (SEDs) are DOCX files with specific structured fields extracted automatically and indexed for the specialized SED streaming search.

## Trigger
A SED DOCX file has been uploaded.

## Steps
1. Receive the SED DOCX from the upload pipeline.
2. Authenticate the pipeline service.
3. Extract the structured SED fields from the DOCX content.
4. Validate that all required SED fields are present.
5. Store the SED record in the seds table.
6. Generate embeddings for the SED content.

## Constraints
- SED source must be DOCX format.
- All required SED fields must be present -- partial SEDs are rejected.
- SED embeddings power the specialized streaming search endpoint.
