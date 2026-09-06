# Workflow: Wiki Page Compilation

## Context
A thematic wiki knowledge base is compiled from all raw Markdown documents. Each wiki page synthesizes patterns, timelines, and connections across all relevant documents for a specific clinical theme. Every claim must cite its source file.

## Trigger
An administrator triggers a wiki page rebuild for a specific theme.

## Steps
1. Read all raw Markdown files from the raw/ directory.
2. Filter documents relevant to the target wiki page theme.
3. Chunk the filtered documents into manageable pieces for LLM context.
4. For each chunk, call the AI API to synthesize patterns and extract timelines.
5. Aggregate the per-chunk outputs into a single coherent wiki page.
6. Validate that all citations reference files that exist in raw/.
7. Write the compiled wiki page to wiki/{page_name}.md.
8. Log the compilation run with document count and any lint warnings.

## Constraints
- Every claim in the wiki must cite its source: [fuente: filename.md].
- The LLM must not infer or interpret -- only synthesize from existing documents.
- Citation lint warnings for documents not in the dataset are acceptable.
