# Development Status

## Supported public-preview core

| Area | Status | Evidence |
|---|---|---|
| Short-term memory | Tested | TTL, capacity, retrieval tests |
| Job lifecycle | Tested | Pause/resume and command parsing tests |
| REST diagnostics | Smoke-test target | `/`, `/healthz`, `/capabilities` |
| MCP tool gateway | Included | File, memory, browser, screenshot and UX tools |
| Playwright automation | Included | Requires Chromium installation for integration tests |
| RTL dashboard | Included | Served directly from the REST bridge |
| CI | Included | Python 3.14 dependency install, compile, tests |

## Experimental—not advertised as complete

The modules under `experimental/` represent ongoing research into goals, planning, dependency recovery, strategy changes, task persistence, dynamic rules, and autonomous loops. They reference internal interfaces that are not included in this public snapshot and are excluded from the default execution path.

## Release gates for stable 2.0

- Apache License 2.0 selected and included.
- Authentication and authorization for non-read-only tools.
- Path and command policy controls.
- REST and MCP integration tests on Windows.
- Reproducible browser demo with recorded expected output.
- Removal or restoration of every missing experimental dependency.
- Documented compatibility with current MCP clients.
