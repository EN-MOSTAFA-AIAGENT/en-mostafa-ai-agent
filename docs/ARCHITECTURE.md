# Architecture

## Runtime components

| Component | File | Responsibility |
|---|---|---|
| MCP gateway | `src/mcp_server.py` | Publishes tools to MCP clients and coordinates browser automation |
| REST bridge | `src/server.py` | Executes local safe/power actions and serves status endpoints |
| Dashboard | Embedded in `src/server.py` | RTL monitoring UI, commands, logs and live screenshots |
| Browser runtime | `src/browser_manager.py` and MCP browser pool | Reusable Playwright Chromium sessions |
| Session memory | `src/memory.py` | TTL key/value memory, session context and recent interactions |
| Job state | `src/job_manager.py` | Thread-safe lifecycle, commands, pause/resume/cancel |

## Request flow

1. An MCP client calls a tool exposed by the FastMCP gateway.
2. Browser-native tools run inside the gateway's Playwright context.
3. Filesystem and shell tools are forwarded to the local REST bridge.
4. The bridge returns structured JSON to the MCP gateway.
5. Status and screenshots are pushed to the dashboard.

## Tool planes

| Plane | Examples | Risk |
|---|---|---|
| Safe | UUID, read file, list directory, metadata, search | Data disclosure |
| Power | create file/folder, copy batches, execute shell | Host modification/code execution |
| Browser | navigate, click, type, evaluate JS, screenshot | Session/data exposure and external side effects |
| Memory | set/get context, project context, clear | Ephemeral local state |

## Experimental layer

`experimental/` preserves the supplied research modules for goals, planning, dynamic rules, recovery, dependency installation and task persistence. They are intentionally excluded from the default runtime because the supplied snapshot does not contain `AgentBrain`, `MemoryEngine`, `StrategyEngine`, `EventLogger`, `SelfMonitor` or `SelfImprovementEngine`.
