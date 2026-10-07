# AI Prompt Log

## Problem 1: Vibe Coder Prompts

Create `AI_prompts.md` at the root of my HW5 project. This file will serve as the prompt log for the assignment and should be maintained as we complete each later problem.

Set up the file so that there will be one section for each homework problem. Each section should identify the problem number and title and include the prompt I gave you for that problem in my own words. If I later need a follow-up prompt for a problem, that section should also record the follow-up prompt and one short sentence explaining what was missing or needed correction after the first prompt.

For now, create only the section for Problem 1, titled Problem 1: Vibe Coder Prompts. Record this prompt as the prompt I used for Problem 1. Do not invent a follow-up prompt because I have not needed one yet.

Keep `AI_prompts.md` readable and organized so that we can append the later problem sections as we work through the assignment. Do not implement anything from future problems and do not create future problem sections yet.

## Problem 2: Study the Campus Customs Database

Study the Campus Customs database in `data/campus_customs.db`. Inspect every table and all fields, examine useful records, trace the three open tickets through related tables, and understand what information the future agents will need without building agents or resolving tickets. Create `data/campus_customs_new.db` as an exact unchanged working copy of the original and verify that its tables and data match. Create `output/harness.md` documenting every table, its fields, why it matters to the agent team, and the relationships to the three open tickets. Complete only Problem 2 and do not build later project components.

## Problem 3: Build the MCP Server

Build the initial FastMCP server for the Campus Customs multi-agent system inside `mcp_server/`, using `data/campus_customs_new.db`. Create exactly three focused, read-only MCP tools based on the actual information needs of tickets 101, 102, and 103. Do not connect or run the server, build agents, create the FastAPI integration, or work on the React dashboard. Document the tools in `output/harness.md`, create `mcp_server/README.md`, and complete only Problem 3.

## Problem 4: Add the MCP Server to Vibe Coder and Test Each Tool

Connect the Problem 3 MCP server to this Codex project, save the local connection configuration in `.mcp.json` at the project root, and continue using `data/campus_customs_new.db`. Actually call each of the three MCP tools with a natural ticket-specific prompt, record the prompts, exact tool names, and real returned outputs in valid `output/mcp_smoke.json`, and verify every returned value against the working database. Correct any connection or implementation issue if necessary. Complete only Problem 4 and do not build the multi-agent team, FastAPI integration, React dashboard, or future MCP tools.

## Problem 5: Build the Agent Team and Grow the MCP Tools

Build the Campus Customs multi-agent team using PydanticAI and expand the MCP server so the agents can investigate and eventually resolve the three open tickets. Create separate Boss, Inventory, Accounting, Facilities, and Customer Service agents with detailed role prompts, full bounded delegation connectivity, centralized `gpt-6-luna` through Portkey configuration using `PORTKEY_API_KEY`, and MCP-only shop-data access. Add genuinely necessary focused MCP tools, including conservative human-approved payment handling with insufficient-cash protection. Create an append-only audit trail, update the harness and MCP README, and complete only Problem 5 without building the React dashboard, later features, or running a full ticket-resolution pass.

## Problem 6: Plan the Three Tickets

Create a standalone `output/desk_tickets.html` planning page with working local tabs for Ticket 101, Ticket 102, Ticket 103, Cash, and Reflection. Before running the agents, document the expected specialist-first path, all reasonable agent-to-agent delegations, and specific current MCP tools for each open ticket. Leave each Actual section empty for later comparison and leave Cash and Reflection for later problems. Respect all database, payment-approval, cash, vendor, date, and draft-communication rules. Complete only Problem 6 and do not run or resolve the agent team.

## Problem 7: Backend Routes

Build the FastAPI backend routes in `backend/main.py` for ticket status, running one selected ticket through the existing bounded multi-agent team, recent audit events, explicit human-approved payment execution, checking-balance retrieval, and safe database reset. Use MCP for shop facts and database operations, preserve the `gpt-6-luna` Portkey configuration and agent controls, add local React CORS, test the routes without a full three-ticket run, and document the routes in `output/harness.md`. Complete only Problem 7.

## Problem 8: Agent Dashboard

Build the human-facing Campus Customs agent operations dashboard in `frontend/` using React, Vite, and TypeScript. Connect it to the FastAPI backend at `http://localhost:8000`, show the three real tickets and statuses, allow deliberate single-ticket runs, refresh real agent events, show role-specific agent activity and summaries, surface structured human-approval requests through the approval route, display the backend checking balance, and preserve the payment boundary. Use a polished Campus Customs/Yale-inspired responsive design, create `output/design.md`, test the frontend build and safe backend integration without the final three-ticket run, and complete only Problem 8.

## Problem 9: Resolve the Tickets

Perform the full end-to-end run of Tickets 101, 102, and 103 using the real MCP server, PydanticAI team, FastAPI backend, React dashboard, and working database. Reset first, record starting cash, preserve the human approval boundary, verify every database mutation and final status, update the desk planning page with actual evidence, create resolved-ticket and resolved-board outputs, append audit history, finish the harness, and complete only Problem 9. Stop for explicit human approval or manual screenshot capture when required; do not simulate approval or invent evidence.

### Problem 9 follow-up prompt

Before publishing, inspect and repair the incomplete Problem 9 run without resetting the working database or rerunning legitimately completed tickets. Continue unresolved Ticket 103 through the real MCP/PydanticAI/FastAPI workflow, stop for any new human approval, reconcile cash and all ticket statuses, complete the Actual and Cash sections, create `output/resolved_tickets.json`, and prepare `output/resolved_board.html` with genuine dashboard screenshots or clearly identify the manual screenshot work still required. Preserve all valid audit evidence and record only real outcomes.

The initial Problem 9 run was incomplete because Ticket 103 and the required resolved-ticket evidence were missing.

### Problem 9 screenshot follow-up prompt

Use the three genuine React dashboard screenshots I manually captured in `output/screenshots/` as the final Problem 9 evidence. Inspect them, rename them only if needed so they clearly correspond to Tickets 101, 102, and 103, and create the portable standalone `output/resolved_board.html` with relative image paths and factual captions. Preserve the image contents, verify the completed database and audit state, and do not reset, rerun, execute payments, or perform Git operations.

This follow-up was needed to incorporate the manually captured genuine React dashboard screenshots into the resolved-board evidence.

## Problem 10: Reflection

Complete the Reflection tab in `output/desk_tickets.html` using evidence from the actual Campus Customs application, the Expected and Actual ticket sections, the Cash tab, `output/resolved_tickets.json`, and `output/audit_trail.json`. Evaluate Tickets 101, 102, and 103 separately; compare the actual workflows with the Problem 6 plans; discuss useful and unnecessary multi-agent delegation; describe three new problems the current team can solve; describe three problems the current tools cannot solve and what additions would be needed; and write in a natural first-person student voice without inventing missing run evidence. Preserve the existing ticket and cash evidence, complete only Problem 10, and do not rerun, reset, or alter outcomes.

## Problem 11: Submit to GitHub

Prepare the completed HW5 project for a future public GitHub submission without creating, initializing, committing, publishing, or pushing anything. Audit the required file structure, preserve both required databases, exclude the real `.env` and other secrets or local artifacts, review the prompt log and output evidence, create reproducible setup instructions in `README.md`, verify dependencies and frontend configuration, run safe final validation, inspect the Git-visible file set, and create `output/github_url.txt` as a clearly marked placeholder because no repository exists yet. Report any missing files or remaining fixes honestly.

### Problem 11 follow-up prompt

Perform a final submission audit of the entire HW5 project through Problems 1–10. Confirm all required source, configuration, database, backend, MCP, frontend, prompt-log, output, audit, resolved-ticket, resolved-board, screenshot, and documentation files; preserve both databases and the completed $160 working state; scan for secrets, real `.env` files, other models, caches, node_modules, build artifacts, ZIPs, and unrelated files; validate Python, JSON, SQLite, frontend, and relative HTML paths; improve README reproducibility instructions; and leave the GitHub URL pending. Do not initialize Git or perform any GitHub operation.
