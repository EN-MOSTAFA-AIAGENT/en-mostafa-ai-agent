# Capability Reference

## MCP memory tools

`set_context`, `get_context`, `get_memory_summary`, `clear_memory`, `set_project`.

## Filesystem and system tools

`generate_uuid`, `read_file`, `list_dir`, `get_file_metadata`, `list_desktop_snapshot`, `search_files`, `create_file`, `create_folder`, `execute_shell`, `batch_mkdir_and_copy`.

Power actions are blocked when `READONLY_MODE=true`.

## Browser tools

- Lifecycle: `launch_browser`, `close_browser`, `get_current_url`.
- Navigation/interactions: `navigate`, `click`, `click_by_text`, `type_text`, `wait_for_selector`.
- Extraction: `get_text`, `get_attribute`, `evaluate_js`, `html_preview`.
- Visuals: `screenshot`, `screenshot_base64`, `render_site`, `smart_screenshot`.
- Analysis: `analyze_ux`, `website_summary`, DOM counts and heuristic UX checks.

## REST endpoints

- Diagnostics: `/`, `/healthz`, `/capabilities`.
- Tool bridge: `/mcp/safe`, `/mcp/power`, `/mcp/playwright`.
- Screenshots: `/screenshots/<filename>`, `/mcp/screenshot/save`.
- Agent control: `/agent/status`, `/agent/running`, `/agent/screenshot`, `/agent/command`.
- Monitoring: `/dashboard`, `/stream`, `/events`, dashboard update/status routes.

## Job control

The job layer supports `pending`, `running`, `waiting_user`, `paused`, `completed`, `failed` and `cancelled`. Natural-language commands include pause, resume, cancel, reload, back, screenshot, scroll and go-to URL in Arabic and English.

## Explicit non-capabilities

- This snapshot does not contain an LLM provider or API key integration.
- It does not autonomously grant itself administrator privileges.
- It does not include production authentication or authorization.
- Reverse-image search is a placeholder path-validation script only.
- Experimental self-improvement modules are not part of the runnable core.
