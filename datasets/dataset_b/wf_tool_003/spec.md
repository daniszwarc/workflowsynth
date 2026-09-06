# Workflow: Geocoding Coordinate Extraction

## Context
A caller wants just the latitude and longitude for a given address, not the full geocoding response.

## Trigger
A request arrives with a free-text address to geocode.

## Steps
1. Call the geocoding API with the address.
2. Extract the latitude and longitude fields from the response.

## Constraints
- Only the coordinate fields should be returned to the caller.
