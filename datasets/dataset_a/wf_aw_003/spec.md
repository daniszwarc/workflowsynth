# Workflow: Business Rule Extraction from Process Document

## Context
When a process document is uploaded, the pipeline extracts business rules using an LLM. Each rule is stored individually, embedded for semantic search, and flagged for validator review.

## Trigger
A process document has been uploaded to the knowledge base.

## Steps
1. Receive the process document from the upload pipeline.
2. Authenticate the pipeline service.
3. Extract the document text.
4. Call the LLM via LangGraph to identify and extract individual business rules.
5. Validate the extracted rules structure.
6. Store each rule in the rules table with status 'pending_review'.
7. Generate embeddings for each rule.
8. Store the embeddings in the vector database linked to each rule.

## Constraints
- Extracted rules start with status 'pending_review' -- not searchable until validated.
- Embeddings use 4096 dimensions stored in pgvector.
- Pipeline timeout is 300 seconds to handle AI cold starts.
