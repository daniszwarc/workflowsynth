# Workflow: Post-Install Geocoding and Service Partner Lookup

## Context
When a unit is registered at a customer installation site, the system geocodes the address to find the nearest authorized service partner within a distance threshold.

## Trigger
A unit is registered at a new installation site.

## Steps
1. Receive the post-install registration form with installation address.
2. Call the geocoder API with the address to obtain latitude/longitude.
3. Parse the geocoder API response to extract coordinates.
4. Read all authorized service partners from the database.
5. Apply the haversine distance rule to compute distance from installation to each partner.
6. Filter service partners within the maximum distance threshold.
7. Format and return the nearest service partner details.

## Constraints
- Geocoding uses an external Maps API.
- Distance computation uses the haversine formula.
- Only partners within the distance threshold are returned.
