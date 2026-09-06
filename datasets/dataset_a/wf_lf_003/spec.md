# Workflow: TTS Playback with Sentence Highlighting

## Context
Cleaned French text is played back aloud using the browser's native Web Speech API with real-time sentence-by-sentence highlighting synchronized to the utterance queue.

## Trigger
Cleaned text is ready for TTS playback.

## Steps
1. Receive the cleaned text sections.
2. Split each section into individual sentences for the utterance queue.
3. Create a SpeechSynthesisUtterance for each sentence with configured rate and pitch.
4. Apply the inter-section pause rule: insert a configurable pause between sections.
5. Queue all utterances to the Web Speech API.
6. As each utterance begins, highlight the corresponding sentence and scroll it into view.

## Constraints
- TTS uses the browser's native Web Speech API -- no external TTS engine.
- Sentence highlighting is synced to utterance start events.
- Rate, pitch, and inter-section pause are user-configurable.
