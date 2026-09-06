# Workflow: Weather Report Generation

## Context
A user wants a quick, readable weather report for a given city, generated from a live weather feed.

## Trigger
A request arrives asking for the current weather report for a specified city.

## Steps
1. Fetch the current weather data for the requested city from the weather API.
2. Format the raw weather data into a human-readable report.

## Constraints
- The report must be generated from the freshest available data -- no caching.
