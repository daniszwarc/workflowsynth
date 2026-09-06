# Workflow: Document Indexing Pipeline

## Context
After a document is uploaded, it is indexed into the vector database for RAG retrieval. The document text is extracted, split into chunks, embedded, and stored for semantic search.

## Trigger
A document has been uploaded and is ready for indexing.

## Steps
1. Receive the document to be indexed.
2. Authenticate the indexing service.
3. Validate that the document has been anonymized.
4. Split the document into overlapping chunks for embedding.
5. Generate embeddings for each chunk using the embedding model.
6. Store all embeddings in the vector database linked to their source document.

## Constraints
- Documents must be anonymized before indexing -- PII must not reach the vector store.
- Each chunk is linked to its source document ID for citation.
