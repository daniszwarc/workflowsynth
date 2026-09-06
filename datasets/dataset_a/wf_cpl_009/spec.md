# Workflow: Attachment Upload for Requests

## Context
Users can attach files to their requests. Attachments are stored and linked to the parent request record.

## Trigger
A user uploads a file attachment via the Dropzone interface.

## Steps
1. Receive the file upload with the parent request ID.
2. Validate the file type and size.
3. Store the attachment file.
4. Insert the attachment record linked to the parent request.

## Constraints
- Attachments must be linked to an existing request record.
- File type and size validation must occur before storage.
