# EN MOSTAFA AI AGENT 3.0.0 — Public Preview

Version 3.0.0 unifies the Windows-first MCP runtime, REST bridge, Playwright automation, memory, job control, open-source documentation, and preserved research modules in the canonical repository.

## Highlights

- Adopted the Apache License 2.0 with a maintainer `NOTICE`.
- Added an English-first README and retained complete Arabic documentation.
- Added FastMCP tools for files, system actions, browser automation, screenshots, website summaries and UX heuristics.
- Added a Flask REST bridge and Arabic RTL live operator dashboard.
- Added short-term TTL memory and thread-safe job lifecycle controls.
- Documented project impact, honest adoption status, supported functionality and release gates.
- Added governance, bug-report, feature-request and pull-request templates.
- Added CI compilation, unit tests and service smoke tests.
- Changed default REST/MCP binding to loopback and enabled read-only mode by default.
- Removed hard-coded personal Windows paths from the public snapshot.
- Fixed dashboard routes that referenced missing template files.

## Compatibility note

This is a major-version public preview. Existing 2.x WordPress, Chrome extension and integration files in the canonical repository are preserved. The new `src/` runtime and `experimental/` research layout are additive and provide the foundation for gradual adapter migration.

## Validation

- Python source compilation passed.
- Six dependency-free core tests passed locally.
- Three service smoke tests are configured to run after CI installs service dependencies.
- Secret and personal-path scan passed.
