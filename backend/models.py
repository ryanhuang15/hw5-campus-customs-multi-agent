"""Shared structured types for the Campus Customs agent team."""

from typing import Any, Literal

from pydantic import BaseModel, Field


AgentName = Literal["Boss", "Inventory", "Accounting", "Facilities", "Customer Service"]


class ApprovalRequest(BaseModel):
    kind: Literal["invoice", "lease"]
    ref_id: int = Field(gt=0)
    amount: float = Field(gt=0)
    reason: str = Field(min_length=1, max_length=500)


class AgentReply(BaseModel):
    """Small, auditable result returned by every specialist."""

    status: Literal["complete", "needs_delegation", "blocked", "draft"]
    summary: str = Field(max_length=2000)
    facts_used: list[str] = Field(default_factory=list, max_length=12)
    next_action: str | None = Field(default=None, max_length=500)
    delegated_to: list[AgentName] = Field(default_factory=list, max_length=5)
    approval_request: ApprovalRequest | None = None


class DelegationRequest(BaseModel):
    recipient: AgentName
    task: str = Field(min_length=1, max_length=1200)


class DelegationResult(BaseModel):
    recipient: AgentName
    status: Literal["complete", "blocked", "limit_reached"]
    summary: str = Field(max_length=2000)
    facts_used: list[str] = Field(default_factory=list, max_length=12)


class MCPRequest(BaseModel):
    tool_name: str = Field(min_length=1, max_length=100)
    arguments: dict[str, Any] = Field(default_factory=dict)


class AuditEvent(BaseModel):
    timestamp: str
    ticket_id: int | None = None
    task: str | None = Field(default=None, max_length=500)
    agent: AgentName | str
    action: str = Field(max_length=100)
    called: str | None = None
    result: str = Field(max_length=2000)
    continuation_reason: str = Field(max_length=500)


class TeamLimits(BaseModel):
    max_iterations: int = 12
    max_delegation_depth: int = 4
    max_repeated_delegation: int = 2
    max_result_chars: int = 4000


class TicketStatus(BaseModel):
    id: int
    type: str
    requester: str
    subject: str
    status: str
    is_open: bool
    is_resolved: bool


class TicketBoardResponse(BaseModel):
    tickets: list[TicketStatus]


class TicketRunResponse(BaseModel):
    ticket_id: int
    result: AgentReply
    recent_events: list[AuditEvent] = Field(default_factory=list)


class PaymentApprovalRequest(BaseModel):
    kind: Literal["invoice", "lease"]
    ref_id: int = Field(gt=0)
    approved_by: str = Field(min_length=1, max_length=200)
    approval_reference: str = Field(min_length=8, max_length=300)


class PaymentApprovalResponse(BaseModel):
    status: Literal["paid"]
    kind: Literal["invoice", "lease"]
    ref_id: int
    amount: float
    account: str
    paid_at: str
    approved_by: str
    remaining_balance: float


class CheckingBalanceResponse(BaseModel):
    account: str
    balance: float
    date: str


class ResetResponse(BaseModel):
    status: Literal["reset"]
    original_sha256: str
    working_sha256: str
    byte_identical: bool


class RecentEventsResponse(BaseModel):
    events: list[AuditEvent]
