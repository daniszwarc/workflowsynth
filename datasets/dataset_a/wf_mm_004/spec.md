# Workflow: Clinical Document Structuring via AI

## Context
Anonymized medical text is structured into a standardized Markdown format using an AI language model. The AI transcribes faithfully -- it does not infer, summarize, or interpret. If the primary model fails verification, a fallback model is used.

## Trigger
Text has been anonymized and is ready for AI structuring.

## Steps
1. Receive the anonymized text and document metadata.
2. Call the primary AI model with a system prompt instructing 'transcribe only, do not infer'.
3. Apply the structuring quality rule: check that numbers and dates from the source are present.
4. If the primary model output fails, call the fallback AI model with the same prompt.
5. Add the YAML frontmatter header to the Markdown output.
6. Encrypt the document content before writing to storage.

## Constraints
- The AI must transcribe only -- no inference, no summarization, no interpretation.
- The fallback model is only invoked if the primary model fails verification.
- YAML frontmatter is mandatory in every output document.
