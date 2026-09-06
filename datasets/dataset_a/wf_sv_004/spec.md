# Workflow: RAG-Powered Draft Response Generation

## Context
When an email is classified as a customer support request, an AI agent searches three knowledge bases and drafts a response. The agent always searches all three sources before drafting. Responses are created as Gmail drafts for staff review -- the agent never sends directly.

## Trigger
An email has been classified as a customer support request.

## Steps
1. Receive the classified email thread history and original email body.
2. Search the customerSupportDocs knowledge base for relevant club information.
3. Search the clubDocuments knowledge base for schedules and official documents.
4. Search the previousEmailResponses knowledge base for similar past exchanges.
5. Detect the language of the incoming email (EN/FR/ES) and apply season mapping rules.
6. Draft the response using only information retrieved from the three knowledge bases.
7. Apply date awareness: use today's date to determine if activities are current or past.
8. Create a Gmail draft (never send) with the response in the customer's language.

## Constraints
- All three knowledge bases MUST be searched before drafting.
- The agent MUST call createDraft -- presenting information without creating the draft is a failure.
- Response language must match the customer's language (EN/FR/ES).
- Never include links or information not found in the knowledge base.
