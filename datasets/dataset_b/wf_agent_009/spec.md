# Workflow: Knowledge Retrieval and Response Formatting

## Context
A user query must be embedded into a searchable form, matched against the knowledge base, merged with contextual data, and formatted into a final response.

## Trigger
A user asks a question that requires a knowledge-grounded answer.

## Steps
1. Fetch the user's query.
2. Transform the user query into a searchable embedding representation.
3. Search the knowledge base using the embedded query.
4. Merge the search results with additional contextual data.
5. Format the merged result into the final response.

## Constraints
- The response must be formatted only after the search results have been merged with context.
