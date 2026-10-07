"""FastAPI routes for the Campus Customs dashboard."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import shutil
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

try:
    from .mcp_client import MCPGateway
    from .models import (
        AuditEvent,
        CheckingBalanceResponse,
        PaymentApprovalRequest,
        PaymentApprovalResponse,
        RecentEventsResponse,
        ResetResponse,
        TicketBoardResponse,
        TicketRunResponse,
        TicketStatus,
    )
    from .team import TeamRuntime, create_team
    from .team import AuditTrail
except ImportError:  # Supports `uvicorn main:app` from the backend directory.
    from mcp_client import MCPGateway
    from models import (
        AuditEvent,
        CheckingBalanceResponse,
        PaymentApprovalRequest,
        PaymentApprovalResponse,
        RecentEventsResponse,
        ResetResponse,
        TicketBoardResponse,
        TicketRunResponse,
        TicketStatus,
    )
    from team import TeamRuntime, create_team
    from team import AuditTrail


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_DATABASE = PROJECT_ROOT / "data" / "campus_customs.db"
WORKING_DATABASE = PROJECT_ROOT / "data" / "campus_customs_new.db"

app = FastAPI(title="Campus Customs Multi-Agent Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_mcp = MCPGateway()
_team: TeamRuntime | None = None


def _team_runtime() -> TeamRuntime:
    global _team
    if _team is None:
        _team = create_team()
    return _team


async def _ticket_board() -> list[dict]:
    result = await _mcp.call("get_ticket_board", {})
    tickets = result.get("tickets", [])
    if not isinstance(tickets, list):
        raise HTTPException(status_code=502, detail="MCP returned an invalid ticket board")
    return tickets


@app.get("/api/tickets", response_model=TicketBoardResponse)
async def get_tickets() -> TicketBoardResponse:
    """Return all tickets with statuses sourced from the working database through MCP."""
    tickets = await _ticket_board()
    return TicketBoardResponse(
        tickets=[
            TicketStatus(
                id=ticket["id"],
                type=ticket["type"],
                requester=ticket["requester"],
                subject=ticket["subject"],
                status=ticket["status"],
                is_open=ticket["status"] == "open",
                is_resolved=ticket["status"] == "resolved",
            )
            for ticket in tickets
        ]
    )


@app.post("/api/tickets/{ticket_id}/run", response_model=TicketRunResponse)
async def run_ticket(ticket_id: int) -> TicketRunResponse:
    """Run the bounded team only for the requested ticket."""
    tickets = await _ticket_board()
    if not any(ticket.get("id") == ticket_id for ticket in tickets):
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} was not found")
    runtime = _team_runtime()
    result = await runtime.run_ticket(ticket_id)
    return TicketRunResponse(ticket_id=ticket_id, result=result, recent_events=runtime.audit.recent(50))


@app.get("/api/events", response_model=RecentEventsResponse)
async def get_recent_events(limit: Annotated[int, Query(ge=1, le=200)] = 50) -> RecentEventsResponse:
    """Return recent events from the existing append-only audit trail."""
    if _team is not None:
        events = _team.audit.recent(limit)
    else:
        events = _read_audit_events(limit)
    return RecentEventsResponse(events=events)


def _read_audit_events(limit: int) -> list:
    audit_path = PROJECT_ROOT / "output" / "audit_trail.json"
    if not audit_path.exists():
        return []
    try:
        values = json.loads(audit_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(values, list):
        return []
    try:
        from .models import AuditEvent
    except ImportError:
        from models import AuditEvent
    return [AuditEvent.model_validate(value) for value in values[-limit:]]


@app.post("/api/approvals/payment", response_model=PaymentApprovalResponse)
async def approve_payment(request: PaymentApprovalRequest) -> PaymentApprovalResponse:
    """Human boundary for the only route allowed to execute an approved payment."""
    if not request.approval_reference.strip():
        raise HTTPException(status_code=400, detail="approval_reference is required")
    if request.approved_by.strip().lower() in {"boss", "inventory", "accounting", "facilities", "customer service", "agent"}:
        raise HTTPException(status_code=400, detail="An agent cannot approve its own payment")

    accounting = await _mcp.call("get_accounting_context", {})
    duplicate = any(
        payment.get("kind") == request.kind and payment.get("ref_id") == request.ref_id
        for payment in accounting.get("payments", [])
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="This payment reference has already been executed")
    mcp_approval_reference = request.approval_reference.strip()
    if not mcp_approval_reference.startswith("human-approved:"):
        mcp_approval_reference = f"human-approved:{mcp_approval_reference}"
    try:
        result = await _mcp.call(
            "execute_approved_payment",
            {**request.model_dump(), "approval_reference": mcp_approval_reference},
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    response = PaymentApprovalResponse.model_validate(result)
    AuditTrail().append(
        AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent="Human",
            action="payment_approved",
            called="execute_approved_payment",
            result=f"Approved {response.kind} {response.ref_id} for ${response.amount:.2f}; remaining checking balance ${response.remaining_balance:.2f}",
            continuation_reason="Explicit human approval received through FastAPI approval route",
        )
    )
    return response


@app.get("/api/cash", response_model=CheckingBalanceResponse)
async def get_checking_balance() -> CheckingBalanceResponse:
    """Return checking balance through the MCP accounting context."""
    result = await _mcp.call("get_accounting_context", {})
    accounts = [account for account in result.get("cash_accounts", []) if account.get("name") == "checking"]
    if not accounts:
        raise HTTPException(status_code=404, detail="Checking account was not found")
    account = accounts[0]
    return CheckingBalanceResponse(account=account["name"], balance=account["balance"], date=account["date"])


@app.post("/api/reset", response_model=ResetResponse)
async def reset_working_database() -> ResetResponse:
    """Explicitly restore the working database from the untouched original."""
    if not ORIGINAL_DATABASE.exists():
        raise HTTPException(status_code=500, detail="Original database is missing")
    if ORIGINAL_DATABASE.resolve() == WORKING_DATABASE.resolve():
        raise HTTPException(status_code=500, detail="Reset source and working database must be different")
    WORKING_DATABASE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ORIGINAL_DATABASE, WORKING_DATABASE)
    original_hash = hashlib.sha256(ORIGINAL_DATABASE.read_bytes()).hexdigest()
    working_hash = hashlib.sha256(WORKING_DATABASE.read_bytes()).hexdigest()
    identical = original_hash == working_hash
    if not identical:
        raise HTTPException(status_code=500, detail="Working database failed post-reset verification")
    return ResetResponse(status="reset", original_sha256=original_hash, working_sha256=working_hash, byte_identical=True)
