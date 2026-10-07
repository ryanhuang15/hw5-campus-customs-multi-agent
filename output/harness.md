# Campus Customs Database Harness

## Scope and snapshot

This harness documents the initial schema and records in `data/campus_customs.db`. The working database is `data/campus_customs_new.db`, created as an exact copy before database-changing work. The authoritative shop date is `desk.date_today` (`2026-08-31`), not the computer clock.

## Tables and fields

### `cash_accounts`

| Field | Type | Purpose |
|---|---|---|
| `name` | TEXT PRIMARY KEY | Cash account name. |
| `balance` | REAL NOT NULL | Current balance. |
| `date` | TEXT NOT NULL | Date of the balance. |

The completed working run has one `checking` row at $160, dated 2026-08-31. The clean-run starting balance was $3,400; invoice 501 reduced it by $840 and approved lease 1 rent reduced it by $2,400. Accounting uses this to prevent negative cash; cash only goes out in this assignment.

### `desk`

| Field | Type | Purpose |
|---|---|---|
| `date_today` | TEXT NOT NULL | Shop's current date. |
| `notes` | TEXT | Optional operating notes. |

One row has date 2026-08-31 and no notes. All agent date calculations must use this value.

### `inventory`

| Field | Type | Purpose |
|---|---|---|
| `sku` | TEXT NOT NULL | Product identifier; part of composite primary key. |
| `name` | TEXT NOT NULL | Product name. |
| `size` | TEXT NOT NULL | Size or `OS`; part of composite primary key. |
| `qty` | INTEGER NOT NULL | On-hand quantity. |
| `location` | TEXT NOT NULL | Storage/display location. |

Inventory is keyed by `(sku, size)` for stock checks. Initial relevant rows include `CC-TEE-WHITE/S` = 0, `CC-HOOD-NAVY/M` = 8, and `CC-MUG-CREST/OS` = 0. The Inventory agent uses it to detect shortages.

### `invoices`

| Field | Type | Purpose |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Invoice identifier. |
| `vendor_id` | INTEGER NOT NULL | Foreign key to `vendors.id`. |
| `amount` | REAL NOT NULL | Amount owed. |
| `due_date` | TEXT NOT NULL | Due date. |
| `status` | TEXT NOT NULL | Payment state. |
| `description` | TEXT | Invoice details. |

Invoice 501 is open for vendor 1, amount $840, due 2026-08-28, description `Rush reprint CC-TEE-WHITE S`. Accounting uses it for payment decisions; an open unpaid invoice blocks that vendor from shipping.

### `leases`

| Field | Type | Purpose |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Lease identifier. |
| `space_name` | TEXT NOT NULL | Leased space. |
| `landlord` | TEXT NOT NULL | Landlord/property manager. |
| `monthly_rent` | REAL NOT NULL | Rent amount. |
| `next_due` | TEXT NOT NULL | Next due date. |
| `notes` | TEXT | Optional lease notes. |

Lease 1 is the Chapel Street shop, Elm City Properties, $2,400 monthly rent, next due 2026-09-02. Facilities uses it for rent and physical-shop matters.

### `payments`

| Field | Type | Purpose |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Payment identifier. |
| `kind` | TEXT NOT NULL | Payment category. |
| `ref_id` | INTEGER | Related record identifier. |
| `amount` | REAL NOT NULL | Amount paid. |
| `account` | TEXT NOT NULL | Account used. |
| `paid_at` | TEXT NOT NULL | Payment date/time. |
| `approved_by` | TEXT NOT NULL | Human approver. |

Initially empty. It records payments only after explicit human approval; `ref_id` is a polymorphic reference without a declared foreign key.

### `pricing`

| Field | Type | Purpose |
|---|---|---|
| `sku` | TEXT PRIMARY KEY | Product identifier. |
| `unit_cost` | REAL NOT NULL | Unit cost. |
| `list_price` | REAL NOT NULL | Standard selling price. |

It supports margin, quote, and price-override decisions. It logically connects to product SKUs in `inventory` and `tickets`, but has no declared foreign key.

### `tickets`

| Field | Type | Purpose |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Ticket identifier. |
| `type` | TEXT NOT NULL | Workflow category. |
| `requester` | TEXT NOT NULL | Requesting person/organization. |
| `subject` | TEXT NOT NULL | Short subject. |
| `sku` | TEXT | Related product SKU. |
| `size` | TEXT | Related size. |
| `qty` | INTEGER | Requested quantity. |
| `lease_id` | INTEGER | Foreign key to `leases.id`. |
| `invoice_id` | INTEGER | Foreign key to `invoices.id`. |
| `status` | TEXT NOT NULL | Current status. |
| `notes` | TEXT | Request details. |
| `created_at` | TEXT NOT NULL | Creation timestamp with offset. |

This is the Boss agent's entry point and links requests to product, lease, and invoice data. All three initial tickets are open.

### `vendors`

| Field | Type | Purpose |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Vendor identifier. |
| `name` | TEXT NOT NULL | Vendor name. |
| `specialty` | TEXT NOT NULL | Supply/service category. |
| `lead_days` | INTEGER NOT NULL | Lead time in days. |

Initial vendors: Bulldog Print Co (apparel reprint, 5 days), Elm City Gifts (mugs and small goods, 3 days), and QuickShip CT (local courier, 1 day). Inventory uses specialty and lead time to identify restock options. No explicit SKU-to-vendor mapping exists.

## Relationships and the three open tickets

Declared foreign keys are `tickets.lease_id -> leases.id`, `tickets.invoice_id -> invoices.id`, and `invoices.vendor_id -> vendors.id`. Product relationships are logical: `tickets.sku` and `inventory.sku` connect to `pricing.sku`, with `(sku, size)` identifying stock. `payments.ref_id` has no declared foreign key.

### Ticket 101 — customer order

Tauhid Zaman requests one `CC-TEE-WHITE`, size S. Inventory has zero, so it is unavailable. Pricing is $8 cost/$28 list. The ticket points to invoice 501, an open $840 Bulldog Print Co invoice for a rush reprint of the same SKU/size. That unpaid invoice blocks the vendor from shipping new product. Customer communication remains a draft.

### Ticket 102 — rent notice

Elm City Properties reports rent due in two days. Ticket 102 points to lease 1: $2,400 due 2026-09-02, while `desk.date_today` is 2026-08-31. Checking has $3,400, but any payment requires human approval and must preserve a nonnegative balance. Facilities handles the lease context; Accounting handles an approved payment; external contact remains a draft.

### Ticket 103 — price override

Yale AI Club requests 20 `CC-HOOD-NAVY`, size M, at a bulk discount. Inventory has 8, leaving a shortage of 12. Pricing is $22 cost/$58 list, so any discount must preserve a sensible margin. Bulldog Print Co's apparel specialty and 5-day lead time are relevant, but its open invoice 501 currently blocks shipment. Customer Service can prepare a draft after the other agents determine a feasible offer.

## Operational rules captured by this model

- Use `desk.date_today` for all dates and use `vendors.lead_days` for lead-time calculations.
- Use `data/campus_customs_new.db` for future changes and preserve the original as the reset source.
- Check product availability by `(sku, size)` before making promises.
- Check open unpaid invoices before selecting a restock vendor.
- Require explicit human approval for every payment and reject insufficient-cash payments.
- Never actually email customers or contact vendors; keep communications as drafts.

## MCP server

The initial FastMCP server is in `mcp_server/server.py`. All three tools are read-only and use `data/campus_customs_new.db`.

### `investigate_customer_order`

- **Tables:** `tickets`, `inventory`, `pricing`, `invoices`, `vendors`.
- **Ticket:** 101.
- **Why it matters:** Shows whether Tauhid Zaman's requested `CC-TEE-WHITE` size S is in stock, its price, and whether the related open Bulldog Print Co invoice blocks a restock.

### `investigate_rent_notice`

- **Tables:** `tickets`, `leases`, `desk`, `cash_accounts`, `payments`.
- **Ticket:** 102.
- **Why it matters:** Connects the rent notice to the Chapel Street lease, calculates days until its database-stored due date from `desk.date_today`, shows checking cash, and reports any recorded lease payment so Boss can distinguish a cleared obligation from a pending approval.

### `investigate_bulk_hoodie_request`

- **Tables:** `tickets`, `inventory`, `pricing`, `vendors`, `invoices`.
- **Ticket:** 103.
- **Why it matters:** Quantifies the shortage for 20 `CC-HOOD-NAVY` size M units, supplies cost/list-price facts for a discount decision, and identifies the apparel-reprint vendor's lead time and open-invoice shipping block.

### `list_open_tickets`

- **Tables:** `tickets`.
- **Agent use:** Boss triage for tickets 101, 102, and 103.
- **Why it matters:** Gives Boss the current open ticket board directly from the database before delegating each ticket.

### `get_ticket_board`

- **Tables:** `tickets`.
- **Agent/dashboard use:** Backend ticket-status route.
- **Why it matters:** Returns all three tickets, including their current open or resolved database status, without hard-coding dashboard state.

### `get_shop_date`

- **Tables:** `desk`.
- **Agent use:** Any agent reasoning about the shop date.
- **Why it matters:** Provides `desk.date_today` directly so deadlines and overdue reasoning never use the computer clock.

### `mark_ticket_resolved`

- **Tables:** `tickets`.
- **Agent use:** Boss after all required specialist work and approvals are complete.
- **Why it matters:** Persists the factual resolution summary and resolved status in the working database so the dashboard and final evidence reflect the real system state.

### `get_accounting_context`

- **Tables:** `cash_accounts`, `invoices`, `vendors`, `payments`, `leases`, `pricing`.
- **Agent use:** Accounting, with support from Boss, Facilities, and Inventory.
- **Why it matters:** Combines the checking balance, unpaid invoice state, prior payments, rent obligations, and product economics needed to assess feasibility without a backend database bypass.

### `get_restock_options`

- **Tables:** `inventory`, `pricing`, `vendors`, `invoices`.
- **Agent use:** Inventory and Accounting for tickets 101 and 103.
- **Why it matters:** Computes the requested SKU/size shortage and exposes every vendor's database lead time and open-invoice shipping block for a restock decision.

### `execute_approved_payment`

- **Tables:** `desk`, `cash_accounts`, `invoices`, `leases`, `payments`.
- **Agent use:** Accounting only, after a human approves an invoice or lease payment.
- **Why it matters:** It refuses missing or agent approval, closed records, and insufficient cash, then atomically updates checking, records the payment, and marks an invoice paid when valid.

## Multi-agent team

The PydanticAI team is implemented in `backend/team.py`; each agent has a separate role prompt in `backend/prompts/` and shares the same bounded delegation runtime and MCP gateway.

| Agent | Responsibility |
|---|---|
| Boss | Reads the ticket board, routes work, coordinates specialist results, and makes the final bounded recommendation. |
| Inventory | Checks SKU/size stock, shortages, restock options, vendor specialties, and lead times. |
| Accounting | Checks cash, invoices, margins, payment feasibility, and approval blockers. |
| Facilities | Handles leases, rent, due dates, and shop-space matters. |
| Customer Service | Produces factual customer-facing drafts and never sends them. |

Every agent receives both MCP inspection and delegation tools. Delegation can target any of the five roles, carries the original ticket ID, and returns a structured `DelegationResult`. `TeamLimits` caps a run at 12 iterations, delegation depth at 4, repeated sender/recipient delegation at 2, and logged/result text at 4,000 characters.

## Safety and audit controls

- Shop facts and database interactions flow through the MCP server; the backend has no SQLite shop-data layer.
- `desk.date_today` and database vendor lead times are authoritative; agents must not use the computer clock or invent facts.
- Payments require a non-agent approver and an external `human-approved:` reference, reject insufficient checking cash, and update records only inside the guarded MCP transaction.
- Customer and vendor communications are drafts only; no external message tool exists.
- Audit events are concise and append to `output/audit_trail.json`; they exclude prompts containing secrets, API keys, and full model messages.
- Delegation depth, repeated delegation, iterations, and result size are bounded to prevent uncontrolled loops and token waste.

## FastAPI backend routes

The dashboard-facing FastAPI app is `backend/main.py`. Start it from the `backend` folder with `uvicorn main:app --reload --port 8000`. CORS permits the local React origins `http://localhost:3000` and `http://127.0.0.1:3000`.

| Method | URL | Purpose |
|---|---|---|
| GET | `/api/tickets` | Returns all tickets and open/resolved status from the working database through MCP. |
| POST | `/api/tickets/{ticket_id}/run` | Runs the bounded Boss-led team for one requested ticket and returns its structured result plus recent audit events. |
| GET | `/api/events?limit=50` | Returns recent events from the existing append-only `output/audit_trail.json`. |
| POST | `/api/approvals/payment` | Human approval boundary: validates explicit approval, prevents duplicate execution, and then calls the guarded MCP payment tool. |
| GET | `/api/cash` | Returns the checking balance through MCP accounting context. |
| POST | `/api/reset` | Explicitly copies untouched `campus_customs.db` over the working database and verifies matching hashes. |

Agents cannot invoke the approval route. Only a separate explicit request to `POST /api/approvals/payment` with a human approval reference can reach `execute_approved_payment`; the MCP tool still rejects agent approvers, duplicate references, closed records, and insufficient cash.
