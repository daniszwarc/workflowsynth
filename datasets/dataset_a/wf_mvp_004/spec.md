# Workflow: Create Unit Card from ERP

## Context
When an RMA is being created for a unit whose card does not exist locally, this workflow pulls the unit data from the ERP system and creates a local card record.

## Trigger
An RMA creation attempt finds no local card for the unit serial number.

## Steps
1. Receive the unit serial number and item number for which no local card exists.
2. Authenticate the office staff user.
3. Fetch the unit serial and item data from the ERP system.
4. Validate that the unit exists in the ERP.
5. Create the local card record from the ERP data.
6. Return to the RMA creation flow with the newly created card.

## Constraints
- This workflow is a fallback -- only triggered when local card lookup returns no result.
- Card data is sourced from the ERP -- not invented locally.
