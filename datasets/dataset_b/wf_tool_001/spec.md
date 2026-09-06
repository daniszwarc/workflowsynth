# Workflow: Weather API Formatting

## Context
A caller wants weather data returned already formatted for display, rather than a raw API payload.

## Trigger
A request arrives for formatted weather data for a location.

## Steps
1. Call the weather API for the requested location.
2. Format the API response for display.

## Constraints
- The output must be display-ready text, not the raw API payload.
