# Windows Installation

## 1. Install prerequisites

```cmd
winget install Python.Python.3.11
winget install Git.Git
```

Close and reopen the terminal, then verify:

```cmd
py -3.11 --version
git --version
```

## 2. Prepare the project

```cmd
git clone https://github.com/EN-MOSTAFA-AIAGENT/en-mostafa-ai-agent.git
cd en-mostafa-ai-agent
py -3.11 -m venv .venv
.venv\Scripts\activate
py -3.11 -m pip install --upgrade pip
py -3.11 -m pip install -r requirements.txt
py -3.11 -m playwright install chromium
copy .env.example .env
```

The Python launcher command is deliberately pinned to 3.11 for compatibility with the supplied agent design.

## 3. Start and verify

Run `scripts\run_rest.ps1`, then in another terminal run `scripts\run_mcp.ps1`.

```powershell
Invoke-RestMethod http://127.0.0.1:5001/healthz
```

Expected response includes `ok: true` and `readonly_mode: true`.

## Troubleshooting

- `No module named playwright`: activate `.venv` and reinstall requirements.
- Browser executable missing: run `py -3.11 -m playwright install chromium`.
- Port already in use: change `REST_PORT` or `MCP_PORT`.
- Power action rejected: this is expected in read-only mode; review security guidance before disabling it.
