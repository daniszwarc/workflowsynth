# Workflow: Website Content Ingestion Pipeline

## Context
A community soccer club maintains a knowledge base for its AI email agent. The club website content is periodically scraped and indexed into a vector store for semantic search.

## Trigger
Manual trigger by club administrator to refresh the knowledge base.

## Steps
1. Fetch the club website sitemap XML from the sitemap endpoint.
2. Parse the XML sitemap and extract all page URLs into a list.
3. Split the URL list into individual items for batch processing.
4. For each batch of pages, fetch the HTML content of each URL.
5. Extract the main content from each page using the .main_content CSS selector.
6. Send the extracted content to the vector store with embeddings into the knowledge base namespace.

## Constraints
- Pages are processed in batches of 10 with a 5-second wait between batches.
- Pages that return errors are skipped and do not halt the pipeline.
