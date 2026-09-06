# Workflow: Reference Article Publication

## Context
Reference articles are published as complete searchable wiki pages. The full document is stored and embedded for semantic and full-text search.

## Trigger
A reference article document has been uploaded.

## Steps
1. Receive the reference article from the upload pipeline.
2. Authenticate the pipeline service.
3. Extract the full document text.
4. Store the article content in the articles table.
5. Generate embeddings for the full article text.
6. Store the embeddings in the vector database linked to the article.

## Constraints
- Reference articles are immediately searchable -- no review step required.
- Full document is stored, not chunked into individual rules.
