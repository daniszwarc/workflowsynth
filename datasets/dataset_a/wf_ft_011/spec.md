# Workflow: Progress Photo Upload

## Context
Users upload progress photos to visually track their fitness journey. Photos are stored privately and never shared.

## Trigger
A user uploads a progress photo.

## Steps
1. Receive the photo upload with date and optional notes.
2. Authenticate the user.
3. Validate the image format and size.
4. Store the photo securely linked to the user.

## Constraints
- Progress photos are private -- never shared or visible to other users.
- Maximum photo size: 10MB.
