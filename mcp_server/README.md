# Campus Customs MCP Server

This initial read-only FastMCP server investigates the three open Campus Customs tickets. It reads from `data/campus_customs_new.db`, the working database copy, and is not connected to the backend or agent team yet.

Current tools:

- `investigate_customer_order` (ticket 101): reads the requested product's inventory and pricing, then traces its invoice and vendor.
- `investigate_rent_notice` (ticket 102): reads the linked lease, authoritative shop date, and checking cash balance.
- `investigate_bulk_hoodie_request` (ticket 103): reads hoodie stock and pricing plus apparel-reprint vendors and their open invoices.
- `list_open_tickets`: reads the open ticket board for Boss triage.
- `get_ticket_board`: reads all tickets and their current database-backed statuses for the dashboard.
- `get_shop_date`: reads the authoritative `desk.date_today` value.
- `mark_ticket_resolved`: updates one ticket to resolved with a factual summary after the team completes its work.
- `get_accounting_context`: reads cash accounts, invoices, payments, leases, and pricing for financial decisions.
- `get_restock_options`: reads a requested SKU/size, pricing, all vendors, lead times, and open-invoice shipping blocks.
- `execute_approved_payment`: guarded write tool for an invoice or lease payment after a human approval reference; it checks cash, records the payment, and marks invoices paid.

The investigation tools are read-only. `execute_approved_payment` is the only financial write tool and rejects missing human approval, agent approvers, closed records, and insufficient cash. `mark_ticket_resolved` is the controlled ticket-status write used only after a completed resolution. Problem 9 performs the first full ticket-resolution run.
