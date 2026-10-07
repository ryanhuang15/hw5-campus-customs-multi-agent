# Campus Customs Multi-Agent Operations

Campus Customs is a classroom multi-agent operations desk for three shop tickets. A Boss agent coordinates Inventory, Accounting, Facilities, and Customer Service agents. The agents obtain shop facts and perform guarded database operations through the local FastMCP server. A FastAPI backend exposes the team and approval boundary, and the React/Vite frontend provides the human-facing dashboard.

## Project layout

- `mcp_server/server.py` — FastMCP tools backed by the working SQLite database.
- `backend/` — PydanticAI team, role prompts, MCP gateway, and FastAPI routes.
- `frontend/` — React/Vite dashboard.
- `data/campus_customs.db` — untouched original database.
- `data/campus_customs_new.db` — working database used by the MCP server and backend.
- `output/` — harness, smoke-test, planning, design, and append-only audit evidence.

## Setup

Use Python 3.11 or newer and Node.js with npm. From this project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `PORTKEY_API_KEY` to the real Portkey key. The real `.env` is local-only and must never be committed. All AI agents use `gpt-6-luna` through the official Portkey client.

Install frontend dependencies:

```powershell
cd frontend
npm install
cd ..
```

## Database workflow

The original database is never modified. For a clean full run, reset the working copy before starting the run:

```powershell
Copy-Item data\campus_customs.db data\campus_customs_new.db -Force
```

The MCP server and backend use only `data/campus_customs_new.db`. Do not reset when you need to preserve a graded run’s working state.

## Run the application

Start the MCP server directly when a standalone MCP process is needed:

```powershell
python mcp_server/server.py
```

The local project MCP configuration is in `.mcp.json` and uses the relative command `python mcp_server/server.py`.

Start the FastAPI backend from the `backend` folder on port 8000:

```powershell
cd backend
uvicorn main:app --reload --port 8000
```

In another terminal, start the React dashboard:

```powershell
cd frontend
npm run dev
```

The dashboard is configured to call `http://localhost:8000`. Payment and purchase execution is not automatic: an explicit human approval through the backend approval route is required, and insufficient cash is refused.

## Full three-ticket workflow

For a fresh run, reset `data/campus_customs_new.db` first, then start the MCP server, backend, and dashboard. Open the dashboard and run Tickets 101, 102, and 103 individually from the ticket board. Review the agent result and events after each run. If an agent prepares a payment request, a human must approve it through the dashboard/API approval boundary before the guarded payment operation can execute. Do not approve an action unless its amount, purpose, ticket, current balance, and projected balance have been reviewed. After all runs, verify ticket statuses, payments, checking balance, `output/audit_trail.json`, and the resolved-ticket evidence.

## Evidence and clean submission

Open `output/desk_tickets.html` directly in a browser for the local ticket, Cash, and Reflection tabs. `output/audit_trail.json` is append-only run evidence. Before publishing, verify that the working database contains the intended graded state, both database files are included, and the real `.env`, caches, virtual environments, `node_modules`, and build artifacts remain ignored.

This workspace has not been initialized, committed, published, or pushed by this preparation step. `output/github_url.txt` is intentionally a placeholder until the public repository exists.
