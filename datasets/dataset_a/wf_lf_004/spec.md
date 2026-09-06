# Workflow: PWA Offline Asset Caching

## Context
The PWA is installable and works offline. A service worker intercepts network requests and serves cached assets when the user is offline.

## Trigger
Service worker installation or a network request from the PWA.

## Steps
1. On service worker installation, pre-cache all critical static assets.
2. Intercept every fetch request from the PWA.
3. Apply the cache-first rule: serve from cache if available, fall back to network.

## Constraints
- Critical assets must be pre-cached on install.
- The LLM cleanup backend is NOT cached -- cleanup requires network.
- Cache-first strategy: cached assets always served over network for performance.
