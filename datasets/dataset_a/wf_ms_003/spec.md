# Workflow: Clinical Wiki Page Ingest

## Context
Anonymized medical text is ingested into a per-case clinical wiki. Wiki pages are full-content replacements -- never diffs. Content is encrypted at rest.

## Trigger
Anonymized text is ready for wiki ingestion.

## Steps
1. Receive the anonymized text and target wiki page path.
2. Authenticate the pipeline service.
3. Call the wiki AI model to generate the full wiki page content.
4. Validate the generated page contains no unanonymized PII.
5. Encrypt the wiki page content before writing.
6. Write the encrypted wiki page using upsert on (case_id, page_path).

## Constraints
- Wiki pages are full-content replacements -- never partial/delta updates.
- All wiki content is encrypted at rest.
- Idempotent: (case_id, page_path) unique constraint -- re-ingest replaces content.
