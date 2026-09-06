# Workflow: CMS Article Publication

## Context
After metadata is resolved, the article is published to the CMS. Publication requires a CSRF token, creates paragraph block entities for each content section, then creates the article node referencing all blocks and metadata.

## Trigger
Article metadata has been resolved and the article is ready to publish.

## Steps
1. Retrieve a CSRF token from the CMS session endpoint.
2. Authenticate the publishing user.
3. Validate the article payload against the CMS article schema.
4. For each HTML content section, create a paragraph block entity via JSON:API POST.
5. Create the article node in the CMS referencing all block UUIDs and metadata.
6. Validate that the article node was created successfully.
7. Write an audit log entry with the article title, node ID, and timestamp.

## Constraints
- CSRF token must be obtained before any POST to the CMS.
- Paragraph blocks must be created before the article node.
- Content-Type header must be application/vnd.api+json for all JSON:API calls.
