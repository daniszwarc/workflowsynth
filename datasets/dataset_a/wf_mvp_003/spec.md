# Workflow: Create RMA

## Context
The core workflow. When a commercial kitchen equipment unit needs warranty service, an RMA is created. The workflow reads unit history from the local database and the ERP system, branches on damage reason and instructions, writes to multiple tables, and sends automated email notifications.

## Trigger
An office staff member submits an RMA creation form.

## Steps
1. Receive the RMA creation form with unit serial number, reason, and instructions.
2. Authenticate the submitting office staff user.
3. Read unit and client data from the local database and ERP system.
4. Validate that the unit exists and has a valid card record.
5. Compute the next sequential RMA number.
6. Apply the damage reason rule: freight damage routes to freight claims, dead on arrival to manufacturer claims.
7. Insert the RMA header record.
8. Send email notification to warehouse staff.
9. Insert the RMA history record.
10. Apply the instructions rule: if replacement required, insert a purchase order record.
11. Apply the tag rule: if tag required, insert rmaTag and send tag email; otherwise send standard email.
12. Apply the pickup rule: if pickup address is 'Other', redirect to address form.

## Constraints
- RMA number is sequential -- computed as MAX(rma)+1.
- Damage reason determines which claims table receives the record.
- Replacement instruction triggers a purchase order record.
- Unit card must exist before RMA creation.
