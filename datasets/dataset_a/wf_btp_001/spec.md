# Workflow: Medical PDF Upload and Auto-Naming

## Context
A clinical AI platform allows authorized administrators to upload medical PDF documents. Each PDF is automatically named by an AI vision model that reads the document content and generates a standardized filename.

## Trigger
An administrator uploads a medical PDF via the platform.

## Steps
1. Receive the PDF upload from the authenticated administrator.
2. Authenticate the uploading user and verify they have admin role.
3. Validate the uploaded file is a valid PDF within the size limit.
4. Send the PDF binary to the AI vision API to generate a standardized filename.
5. Encrypt the document content before storage.
6. Store the PDF with the AI-generated filename in the document store.
7. Write an audit log entry recording the upload.

## Constraints
- Only users with admin role can upload documents.
- Maximum file size: 50MB.
- Document content must be encrypted before storage.
- Every upload must be logged in the audit trail.
