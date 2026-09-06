# Workflow: Email-to-Claim Ingestion Pipeline

## Context
The system monitors an inbound email mailbox for incoming messages containing workers' compensation claim PDFs. When an email arrives with a PDF, the pipeline retrieves the PDF, maps its fields to the internal claim schema, creates a claim, attaches the original PDF, and notifies case staff.

## Trigger
A new email with a PDF attachment arrives in the inbound mailbox.

## Steps
1. Monitor the inbound email mailbox for new messages with PDF attachments.
2. Retrieve the incoming email and extract the attached PDF.
3. Validate that the PDF is a recognized claim form type.
4. Map the PDF form fields to the internal claim XML schema.
5. Validate the mapped fields against the claim creation schema.
6. Create the new claim record from the mapped data.
7. Attach the original PDF to the newly created claim.
8. Notify the assigned case staff that a new claim has been ingested.

## Constraints
- Trigger: inbound email with PDF attachment -- no manual intervention required.
- PDF field mapping uses the internal claim XML schema.
- Original PDF is preserved as an attachment.
- Case staff are notified immediately after successful claim creation.
