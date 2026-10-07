"""Read-only MCP tools for investigating Campus Customs tickets."""

from datetime import date
from pathlib import Path
import sqlite3
from typing import Any

from fastmcp import FastMCP

DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "campus_customs_new.db"
mcp = FastMCP("Campus Customs MCP Server")


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def _require_positive(value: int, field_name: str) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


@mcp.tool
def investigate_customer_order(ticket_id: int = 101) -> dict[str, Any]:
    """Return stock, pricing, invoice, and vendor facts for ticket 101."""
    if ticket_id != 101:
        raise ValueError("investigate_customer_order supports ticket 101 only")
    with _connect() as db:
        ticket = db.execute("SELECT id,type,requester,subject,sku,size,qty,status,notes,created_at,invoice_id FROM tickets WHERE id=?", (ticket_id,)).fetchone()
        if ticket is None:
            raise ValueError(f"Ticket {ticket_id} was not found")
        inventory = db.execute("SELECT sku,name,size,qty,location FROM inventory WHERE sku=? AND size=?", (ticket["sku"], ticket["size"])).fetchone()
        pricing = db.execute("SELECT sku,unit_cost,list_price FROM pricing WHERE sku=?", (ticket["sku"],)).fetchone()
        invoice = db.execute("""
            SELECT i.id,i.vendor_id,i.amount,i.due_date,i.status,i.description,
                   v.name AS vendor_name,v.specialty,v.lead_days
            FROM invoices i JOIN vendors v ON v.id=i.vendor_id WHERE i.id=?
        """, (ticket["invoice_id"],)).fetchone()
    available = inventory["qty"] if inventory else 0
    return {"ticket": _dict(ticket), "inventory": _dict(inventory), "pricing": _dict(pricing), "shortage": max(ticket["qty"] - available, 0), "invoice_and_vendor": _dict(invoice)}


@mcp.tool
def investigate_rent_notice(ticket_id: int = 102) -> dict[str, Any]:
    """Return lease, shop-date, and cash facts for ticket 102."""
    if ticket_id != 102:
        raise ValueError("investigate_rent_notice supports ticket 102 only")
    with _connect() as db:
        ticket = db.execute("SELECT id,type,requester,subject,lease_id,status,notes,created_at FROM tickets WHERE id=?", (ticket_id,)).fetchone()
        if ticket is None:
            raise ValueError(f"Ticket {ticket_id} was not found")
        lease = db.execute("SELECT id,space_name,landlord,monthly_rent,next_due,notes FROM leases WHERE id=?", (ticket["lease_id"],)).fetchone()
        lease_payment = db.execute(
            "SELECT id,kind,ref_id,amount,account,paid_at,approved_by FROM payments WHERE kind='lease' AND ref_id=? ORDER BY id DESC LIMIT 1",
            (ticket["lease_id"],),
        ).fetchone()
        desk = db.execute("SELECT date_today,notes FROM desk LIMIT 1").fetchone()
        cash = db.execute("SELECT name,balance,date FROM cash_accounts WHERE name='checking'").fetchone()
    days_until_due = None
    if lease and desk:
        days_until_due = (date.fromisoformat(lease["next_due"]) - date.fromisoformat(desk["date_today"])).days
    return {"ticket": _dict(ticket), "lease": _dict(lease), "lease_payment": _dict(lease_payment), "desk": _dict(desk), "cash_account": _dict(cash), "days_until_due": days_until_due}


@mcp.tool
def investigate_bulk_hoodie_request(ticket_id: int = 103) -> dict[str, Any]:
    """Return stock, margin, lead-time, and invoice-blocking facts for ticket 103."""
    if ticket_id != 103:
        raise ValueError("investigate_bulk_hoodie_request supports ticket 103 only")
    with _connect() as db:
        ticket = db.execute("SELECT id,type,requester,subject,sku,size,qty,status,notes,created_at FROM tickets WHERE id=?", (ticket_id,)).fetchone()
        if ticket is None:
            raise ValueError(f"Ticket {ticket_id} was not found")
        inventory = db.execute("SELECT sku,name,size,qty,location FROM inventory WHERE sku=? AND size=?", (ticket["sku"], ticket["size"])).fetchone()
        pricing = db.execute("SELECT sku,unit_cost,list_price FROM pricing WHERE sku=?", (ticket["sku"],)).fetchone()
        vendors = db.execute("""
            SELECT v.id,v.name,v.specialty,v.lead_days,
                   i.id AS open_invoice_id,i.amount AS open_invoice_amount,
                   i.due_date AS open_invoice_due_date,i.description AS open_invoice_description
            FROM vendors v LEFT JOIN invoices i ON i.vendor_id=v.id AND i.status='open'
            WHERE v.specialty='apparel reprint' ORDER BY v.id
        """).fetchall()
    available = inventory["qty"] if inventory else 0
    return {"ticket": _dict(ticket), "inventory": _dict(inventory), "pricing": _dict(pricing), "shortage": max(ticket["qty"] - available, 0), "apparel_reprint_vendors": [_dict(row) for row in vendors]}


@mcp.tool
def list_open_tickets() -> dict[str, Any]:
    """Return the current open ticket board for the Boss agent."""
    with _connect() as db:
        rows = db.execute(
            """
            SELECT id, type, requester, subject, sku, size, qty, lease_id,
                   invoice_id, status, notes, created_at
            FROM tickets
            WHERE status = 'open'
            ORDER BY id
            """
        ).fetchall()
    return {"tickets": [_dict(row) for row in rows]}


@mcp.tool
def get_ticket_board() -> dict[str, Any]:
    """Return all tickets and their database-backed current statuses."""
    with _connect() as db:
        rows = db.execute(
            """
            SELECT id, type, requester, subject, sku, size, qty, lease_id,
                   invoice_id, status, notes, created_at
            FROM tickets
            ORDER BY id
            """
        ).fetchall()
    return {"tickets": [_dict(row) for row in rows]}


@mcp.tool
def get_shop_date() -> dict[str, Any]:
    """Return the authoritative shop date from the desk table."""
    with _connect() as db:
        row = db.execute("SELECT date_today, notes FROM desk LIMIT 1").fetchone()
    if row is None:
        raise ValueError("The desk date is missing")
    return _dict(row)


@mcp.tool
def mark_ticket_resolved(ticket_id: int, resolution_summary: str) -> dict[str, Any]:
    """Mark one ticket resolved with a concise factual summary after its work is complete."""
    if ticket_id <= 0:
        raise ValueError("ticket_id must be positive")
    if not resolution_summary.strip() or len(resolution_summary) > 1000:
        raise ValueError("resolution_summary must be 1-1000 characters")
    with _connect() as db:
        ticket = db.execute("SELECT id, status FROM tickets WHERE id=?", (ticket_id,)).fetchone()
        if ticket is None:
            raise ValueError(f"Ticket {ticket_id} was not found")
        if ticket["status"] == "resolved":
            return {"ticket_id": ticket_id, "status": "resolved", "resolution_summary": resolution_summary.strip(), "already_resolved": True}
        db.execute("UPDATE tickets SET status='resolved', notes=? WHERE id=?", (resolution_summary.strip(), ticket_id))
        db.commit()
    return {"ticket_id": ticket_id, "status": "resolved", "resolution_summary": resolution_summary.strip(), "already_resolved": False}


@mcp.tool
def get_accounting_context() -> dict[str, Any]:
    """Return cash, invoice, payment, lease, and pricing facts for financial decisions."""
    with _connect() as db:
        cash = db.execute("SELECT name, balance, date FROM cash_accounts ORDER BY name").fetchall()
        invoices = db.execute(
            """
            SELECT i.id, i.vendor_id, i.amount, i.due_date, i.status, i.description,
                   v.name AS vendor_name
            FROM invoices i JOIN vendors v ON v.id = i.vendor_id ORDER BY i.id
            """
        ).fetchall()
        payments = db.execute(
            "SELECT id, kind, ref_id, amount, account, paid_at, approved_by FROM payments ORDER BY id"
        ).fetchall()
        leases = db.execute(
            "SELECT id, space_name, landlord, monthly_rent, next_due, notes FROM leases ORDER BY id"
        ).fetchall()
        pricing = db.execute("SELECT sku, unit_cost, list_price FROM pricing ORDER BY sku").fetchall()
    return {
        "cash_accounts": [_dict(row) for row in cash],
        "invoices": [_dict(row) for row in invoices],
        "payments": [_dict(row) for row in payments],
        "leases": [_dict(row) for row in leases],
        "pricing": [_dict(row) for row in pricing],
    }


@mcp.tool
def get_restock_options(sku: str, size: str, requested_qty: int) -> dict[str, Any]:
    """Return database-backed stock, pricing, vendors, lead times, and invoice blocks."""
    if not sku.strip() or not size.strip():
        raise ValueError("sku and size are required")
    _require_positive(requested_qty, "requested_qty")
    with _connect() as db:
        inventory = db.execute(
            "SELECT sku, name, size, qty, location FROM inventory WHERE sku=? AND size=?",
            (sku, size),
        ).fetchone()
        pricing = db.execute("SELECT sku, unit_cost, list_price FROM pricing WHERE sku=?", (sku,)).fetchone()
        vendors = db.execute(
            """
            SELECT v.id, v.name, v.specialty, v.lead_days,
                   i.id AS open_invoice_id, i.amount AS open_invoice_amount,
                   i.due_date AS open_invoice_due_date, i.description AS open_invoice_description
            FROM vendors v
            LEFT JOIN invoices i ON i.vendor_id=v.id AND i.status='open'
            ORDER BY v.id
            """
        ).fetchall()
    available = inventory["qty"] if inventory else 0
    return {
        "product": _dict(inventory),
        "pricing": _dict(pricing),
        "requested_qty": requested_qty,
        "shortage": max(requested_qty - available, 0),
        "vendors": [
            {**_dict(row), "can_ship": row["open_invoice_id"] is None}
            for row in vendors
        ],
    }


@mcp.tool
def execute_approved_payment(
    kind: str,
    ref_id: int,
    approved_by: str,
    approval_reference: str,
) -> dict[str, Any]:
    """Execute an explicitly human-approved invoice or lease payment safely."""
    if kind not in {"invoice", "lease"}:
        raise ValueError("kind must be 'invoice' or 'lease'")
    if not approved_by.strip() or not approval_reference.startswith("human-approved:"):
        raise ValueError("A human approver and human-approved reference are required")
    if approved_by.strip().lower() in {"boss", "inventory", "accounting", "facilities", "customer service", "agent"}:
        raise ValueError("Agents cannot approve their own payments")

    with _connect() as db:
        desk = db.execute("SELECT date_today FROM desk LIMIT 1").fetchone()
        cash = db.execute("SELECT name, balance FROM cash_accounts WHERE name='checking'").fetchone()
        if desk is None or cash is None:
            raise ValueError("Required shop date or checking account is missing")
        if kind == "invoice":
            record = db.execute("SELECT id, amount, status FROM invoices WHERE id=?", (ref_id,)).fetchone()
            if record is None:
                raise ValueError(f"Invoice {ref_id} was not found")
            if record["status"] != "open":
                raise ValueError(f"Invoice {ref_id} is not open")
            amount = record["amount"]
        else:
            record = db.execute("SELECT id, monthly_rent FROM leases WHERE id=?", (ref_id,)).fetchone()
            if record is None:
                raise ValueError(f"Lease {ref_id} was not found")
            amount = record["monthly_rent"]
        if cash["balance"] < amount:
            raise ValueError("Payment refused: insufficient cash")

        new_balance = cash["balance"] - amount
        db.execute("UPDATE cash_accounts SET balance=?, date=? WHERE name='checking'", (new_balance, desk["date_today"]))
        db.execute(
            "INSERT INTO payments(kind, ref_id, amount, account, paid_at, approved_by) VALUES (?, ?, ?, ?, ?, ?)",
            (kind, ref_id, amount, "checking", desk["date_today"], approved_by.strip()),
        )
        if kind == "invoice":
            db.execute("UPDATE invoices SET status='paid' WHERE id=?", (ref_id,))
        db.commit()
    return {
        "status": "paid",
        "kind": kind,
        "ref_id": ref_id,
        "amount": amount,
        "account": "checking",
        "paid_at": desk["date_today"],
        "approved_by": approved_by.strip(),
        "remaining_balance": new_balance,
    }


if __name__ == "__main__":
    mcp.run()
