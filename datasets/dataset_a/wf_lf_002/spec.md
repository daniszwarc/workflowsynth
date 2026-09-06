# Workflow: LLM Text Cleanup via FastAPI Proxy

## Context
Before TTS playback, extracted text is sent to a FastAPI proxy that forwards it to a language model with a French system prompt. The LLM strips page numbers, running headers, footnotes, and hyphenation artifacts.

## Trigger
Extracted text is ready for cleanup before playback.

## Steps
1. Receive the extracted text section from the PWA frontend.
2. Validate the request origin matches the allowed CORS origin.
3. Forward the text to the LLM API with a French cleanup system prompt.
4. Receive the cleaned text response.
5. Return the cleaned text to the PWA for TTS playback.

## Constraints
- CORS is locked to the GitHub Pages app origin -- no other origins accepted.
- The backend is a proxy only -- no storage, no user data retained.
- TLS provided by the reverse proxy.
