# Changelog

All notable changes are documented here. The project follows Semantic Versioning where practical.

## [3.0.0-public-preview] - 2026-07-12

### Added

- Apache License 2.0 and project attribution notice.
- English-first project overview with a dedicated Arabic README.
- Project impact, development-status, architecture, capability, installation and roadmap documentation.
- Governance, issue forms and pull-request template for community onboarding.
- FastMCP server with file, memory, browser, screenshot, UX and system tools.
- Flask REST bridge and Arabic RTL live dashboard.
- Thread-safe job state and Arabic/English command parsing.
- Windows installation and launch scripts.
- CI dependency installation, syntax compilation, core tests and REST smoke tests.

### Changed

- Unified the public runtime, documentation and research modules in the canonical repository.
- REST and MCP hosts now bind to `127.0.0.1` by default.
- Read-only mode is enabled by default.
- Machine-specific experimental paths are environment-configurable.
- Incomplete cognition modules are explicitly isolated under `experimental/`.

### Fixed

- Dashboard routes now serve the embedded HTML shipped with the server instead of referencing missing template files.
- Removed hard-coded personal Windows paths from the public snapshot.

### Security

- Documented the trust boundary around shell, file-write, JavaScript and browser-control tools.
- Added explicit warnings against direct public exposure.
- Added secret and personal-path checks to the release workflow.

### Known limitations

- Experimental cognition modules reference internal components not included in this snapshot.
- Built-in authentication is planned; keep the services loopback-only.

Earlier 2.x development remains available in the Git history of the canonical repository.
