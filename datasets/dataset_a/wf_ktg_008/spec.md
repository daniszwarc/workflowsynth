# Workflow: Claim Document Attachment Upload

## Context
Case staff attach documents to claimant records via chunked file upload. Files are stored on the filesystem and registered in the attachments table.

## Trigger
A case staff member uploads a document to a claimant record.

## Steps
1. Receive the chunked file upload with form ID and claimant context.
2. Authenticate the uploading user.
3. Validate the file type and size.
4. Move confirmed files from temp to the permanent uploads directory.
5. Insert the attachment record linked to the claimant ID.
6. Log the attachment in the audit trail.

## Constraints
- Files are stored at uploads/{formID}/ on the filesystem.
- Attachment record includes claimant_id, form_name, filename, and date_added.
