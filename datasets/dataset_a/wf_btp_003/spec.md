# Workflow: RAG Clinical Chat

## Context
The clinical AI assistant answers questions about the patient's medical history using RAG over the anonymized document collection. Four layers of prompt injection defense protect against adversarial inputs.

## Trigger
An authenticated user submits a clinical question via the chat interface.

## Steps
1. Receive the clinical question from the authenticated user.
2. Authenticate the user.
3. Apply injection defense: validate the query does not contain injection patterns.
4. Generate a semantic embedding of the query.
5. Search the raw documents vector store for relevant clinical data.
6. Search the wiki pages vector store for synthesized clinical knowledge.
7. Merge the search results and validate context does not contain injection payloads.
8. Call the LLM with the query and retrieved context. Require mandatory source citations.

## Constraints
- 4-layer prompt injection defense: query validation, context validation, system prompt hardening, output validation.
- Every response must include source citations.
- Both raw/ and wiki/ must be searched before generating a response.
