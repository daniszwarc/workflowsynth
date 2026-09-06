# Workflow: Document Commit and Version Control

## Context
After verification, each processed document is written to the raw/ directory as a Markdown file and a metadata JSON file. Each document gets its own git commit. Git push is batched every 10 documents.

## Trigger
A document has been verified and is ready for storage.

## Steps
1. Receive the verified document (Markdown content and metadata).
2. Authenticate as the pipeline service account for git operations.
3. Write the Markdown file to raw/YYYY-MM-DD_Tipo_Descripcion.md.
4. Write the metadata JSON file to the same directory.
5. Create a git commit for this document.

## Constraints
- One git commit per document -- never batch multiple documents in a single commit.
- Git push occurs every 10 commits, not after every commit.
- The .meta.json file must always accompany the .md file in the same commit.
