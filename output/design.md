# Campus Customs Agent Operations Desk

## Overall direction

The dashboard is a human-first operations desk rather than a generic ticket list. It uses a dark Yale-inspired navigation rail, warm paper-like work surfaces, restrained pink accents, and a serif editorial headline to make the tool feel like a serious campus retail command center. The layout is intentionally split into a work queue, selected-ticket control area, live activity feed, and decision readout so an operator can scan status first and investigate detail second.

## Layout and workflow

The left rail identifies Campus Customs, shows the local MCP/FastAPI connection state, and keeps the human-approval principle visible. The top metrics make checking balance, open-ticket count, and team capacity immediately visible. The ticket board loads from `GET /api/tickets`; selecting a row only changes the detail view and never starts a run. The `Start agent team` button deliberately calls `POST /api/tickets/{ticket_id}/run` for the selected ticket only.

Agent events are refreshed from `GET /api/events?limit=100` while a run is in progress. The activity stream shows the acting agent, action, timestamp, result, called MCP tool when present, and the reason the loop continued. Once the run returns, the structured Boss result appears in the Run readout with its status, summary, next action, and database-backed facts used.

## Agent identities

Each role has a distinct color and icon so the stream can be understood without reading every label:

- Boss uses magenta and a sparkle mark for orchestration.
- Inventory uses teal and a package-search mark for stock and supply.
- Accounting uses blue and a wallet mark for financial control.
- Facilities uses amber and a store mark for the physical shop.
- Customer Service uses purple and a message mark for drafts.

The agent strip shows all five roles at all times, while active participants become fully opaque and receive a pink activity underline. This distinguishes team membership from actual participation in the selected ticket.

## Status and activity treatment

Open tickets use pink status dots and pink ticket number badges; resolved tickets use green treatments. Status is never hard-coded in the frontend: it comes from the FastAPI ticket route, which reads the working database through MCP. The event feed stays quiet on first load and explicitly tells the operator that activity appears after a deliberate run, avoiding the impression that selecting a ticket has started work.

## Cash and human approval

Checking balance is a prominent metric loaded from `GET /api/cash`; the frontend does not calculate or hard-code it. After an approval, the dashboard refreshes the balance and ticket/event data so a real cash decrease is visible only after the backend operation succeeds.

When the structured agent result contains an `approval_request`, a high-contrast Human decision required card appears beside the run readout. It shows the reason, amount, payment kind, and reference before asking for the human name and approval reference. The approve button calls only `POST /api/approvals/payment`; there is no automatic approval path, and the UI requires the explicit `human-approved:` reference format enforced by the backend. The card also states that this is the only interface action that can authorize a payment.

## Distinctive details and operator value

Small touches reinforce operational clarity: a live connection pill, compact monospaced metadata labels, an animated spinner while the team is working, a reversed newest-first event stream, a clear empty state before any run, and a responsive layout that collapses the rail and stacks the panels on smaller screens. The visual system keeps pink for attention and action, green for safe/resolved states, and neutral ink for facts so approvals and unresolved work remain difficult to overlook without making the screen feel alarmist.

## Integration boundary

The frontend uses `http://localhost:8000` for all data and actions. It calls the existing ticket, run, events, approval, and cash routes and does not open SQLite or recreate MCP logic. Vite serves the app on port 5173, which is allowed by the FastAPI CORS configuration. No ticket is run on page load, no ticket is run by selection, and this problem does not perform the final three-ticket resolution run.
