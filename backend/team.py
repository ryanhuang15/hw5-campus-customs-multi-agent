"""PydanticAI multi-agent team with bounded, fully connected delegation."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Awaitable, Callable, cast

from dotenv import load_dotenv
from openai.types.chat import ChatCompletion as OpenAIChatCompletion
from portkey_ai import Portkey
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

try:
    from .mcp_client import MCPGateway
    from .models import AgentName, AgentReply, AuditEvent, DelegationRequest, DelegationResult, TeamLimits
except ImportError:  # Supports `uvicorn main:app` from the backend directory.
    from mcp_client import MCPGateway
    from models import AgentName, AgentReply, AuditEvent, DelegationRequest, DelegationResult, TeamLimits


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = PROJECT_ROOT / "backend" / "prompts"
AUDIT_PATH = PROJECT_ROOT / "output" / "audit_trail.json"
MODEL_NAME = "gpt-6-luna"


class _AsyncPortkeyAdapter:
    """Minimal async facade allowing PydanticAI to await the official Portkey client."""

    def __init__(self, client: Portkey) -> None:
        self.base_url = client.base_url
        self.chat = _AsyncChat(client)


class _AsyncChat:
    def __init__(self, client: Portkey) -> None:
        self.completions = _AsyncCompletions(client)


class _AsyncCompletions:
    def __init__(self, client: Portkey) -> None:
        self._client = client

    async def create(self, *args: Any, **kwargs: Any) -> Any:
        response = await asyncio.to_thread(self._client.chat.completions.create, *args, **kwargs)
        # Portkey's official client returns its vendored OpenAI-compatible model.
        # PydanticAI validates against the public OpenAI model class, so convert
        # the already-returned response without changing the provider or endpoint.
        return OpenAIChatCompletion.model_validate(response.model_dump())


def build_model() -> OpenAIChatModel:
    """Build the one permitted model configuration for every team agent."""
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(PROJECT_ROOT.parent / ".env")
    import os

    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is not set")
    portkey = Portkey(api_key=api_key, provider="openai")
    adapter = cast(Any, _AsyncPortkeyAdapter(portkey))
    return OpenAIChatModel(
        MODEL_NAME,
        provider=OpenAIProvider(openai_client=adapter),
        settings={"openai_reasoning_effort": "none"},
    )


class AuditTrail:
    """Persist an append-only JSON list without secrets or full model messages."""

    def __init__(self, path: Path = AUDIT_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: AuditEvent) -> None:
        if self.path.exists():
            try:
                events = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                events = []
        else:
            events = []
        if not isinstance(events, list):
            raise ValueError("audit_trail.json must contain a JSON list")
        events.append(event.model_dump())
        self.path.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")

    def recent(self, limit: int = 50) -> list[AuditEvent]:
        if limit < 1:
            return []
        if not self.path.exists():
            return []
        try:
            events = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(events, list):
            return []
        return [AuditEvent.model_validate(item) for item in events[-limit:]]


@dataclass
class AgentDependencies:
    runtime: "TeamRuntime"
    ticket_id: int | None
    task: str
    depth: int = 0
    counters: dict[str, int] = field(default_factory=lambda: {"iterations": 0})
    delegation_counts: dict[tuple[str, str], int] = field(default_factory=dict)


class TeamRuntime:
    """Owns the five agents and enforces delegation and loop limits."""

    def __init__(self, limits: TeamLimits | None = None) -> None:
        self.limits = limits or TeamLimits()
        self.gateway = MCPGateway()
        self.audit = AuditTrail()
        self.agents: dict[AgentName, Agent[AgentDependencies, AgentReply]] = {}
        self._build_agents()

    def _build_agents(self) -> None:
        prompt_files: dict[AgentName, str] = {
            "Boss": "boss.md",
            "Inventory": "inventory.md",
            "Accounting": "accounting.md",
            "Facilities": "facilities.md",
            "Customer Service": "customer_service.md",
        }
        for name, filename in prompt_files.items():
            self.agents[name] = Agent(
                model=build_model(),
                name=name.lower().replace(" ", "_"),
                output_type=AgentReply,
                deps_type=AgentDependencies,
                system_prompt=(PROMPTS_DIR / filename).read_text(encoding="utf-8"),
                tools=[self._mcp_tool, self._delegation_tool],
                retries=1,
            )

    async def run_ticket(self, ticket_id: int) -> AgentReply:
        deps = AgentDependencies(self, ticket_id, f"Resolve ticket {ticket_id}")
        self._record(ticket_id, "Boss", "run_started", "team", "Ticket run started", "Boss begins ticket triage")
        result = await self.agents["Boss"].run(
            f"Continue the real end-to-end workflow for ticket {ticket_id} from its current database state. Re-check any earlier approval blocker with MCP. If the required human-approved payment is now recorded, it is no longer a blocker: continue coordinating the ticket. For ticket 103 specifically, this is a price-override request, not an instruction to purchase inventory. Use the existing stock, pricing, vendor, and accounting facts to make a bounded decision: it is acceptable to resolve the request by documenting the available quantity, the shortage, the list-price/unit-cost economics, and that no safe discount or delivery promise can be made without a vendor quote. Do not invent a purchase, quote, shipment, or discount. Call the exact MCP tool mark_ticket_resolved when the ticket’s decision is complete. Do not execute payments or send communications.",
            deps=deps,
        )
        self._record(ticket_id, "Boss", "run_stopped", "Boss", result.output.summary, "Boss returned the final bounded response")
        return result.output

    async def _mcp_tool(self, ctx: RunContext[AgentDependencies], tool_name: str, arguments: dict[str, Any]) -> Any:
        if ctx.deps.counters["iterations"] >= self.limits.max_iterations:
            raise RuntimeError("Maximum team iterations reached")
        ctx.deps.counters["iterations"] += 1
        agent_name = self._agent_name(ctx)
        self._record(ctx.deps.ticket_id, agent_name, "mcp_call", tool_name, "MCP call requested", "Agent needs database-backed shop facts")
        result = await self.gateway.call(tool_name, arguments)
        bounded = self._bounded(result)
        self._record(ctx.deps.ticket_id, agent_name, "mcp_result", tool_name, self._clip(bounded), "Agent received MCP facts")
        return bounded

    async def _delegation_tool(self, ctx: RunContext[AgentDependencies], request: DelegationRequest) -> DelegationResult:
        sender = self._agent_name(ctx)
        if request.recipient == sender:
            raise ValueError("An agent cannot delegate to itself")
        if ctx.deps.depth >= self.limits.max_delegation_depth:
            return DelegationResult(recipient=request.recipient, status="limit_reached", summary="Delegation depth limit reached")
        key = (sender, request.recipient)
        count = ctx.deps.delegation_counts.get(key, 0)
        if count >= self.limits.max_repeated_delegation:
            return DelegationResult(recipient=request.recipient, status="limit_reached", summary="Repeated delegation limit reached")
        ctx.deps.delegation_counts[key] = count + 1
        self._record(ctx.deps.ticket_id, sender, "delegation", request.recipient, request.task, "Specialist input requested")
        child = AgentDependencies(self, ctx.deps.ticket_id, request.task, ctx.deps.depth + 1, ctx.deps.counters, ctx.deps.delegation_counts)
        result = await self.agents[request.recipient].run(request.task, deps=child)
        summary = self._clip(result.output.summary)
        self._record(ctx.deps.ticket_id, request.recipient, "delegation_result", sender, summary, "Result returned to requesting agent")
        return DelegationResult(recipient=request.recipient, status="complete", summary=summary, facts_used=result.output.facts_used)

    def _record(self, ticket_id: int | None, agent: str, action: str, called: str | None, result: str, reason: str) -> None:
        self.audit.append(AuditEvent(timestamp=datetime.now(timezone.utc).isoformat(), ticket_id=ticket_id, agent=agent, action=action, called=called, result=self._clip(result), continuation_reason=reason))

    def _clip(self, value: Any) -> str:
        text = value if isinstance(value, str) else json.dumps(value, default=str, sort_keys=True)
        return text[: self.limits.max_result_chars]

    def _bounded(self, value: Any) -> Any:
        text = json.dumps(value, default=str, sort_keys=True)
        if len(text) <= self.limits.max_result_chars:
            return value
        return {
            "truncated": True,
            "content_excerpt": text[: self.limits.max_result_chars],
        }

    @staticmethod
    def _agent_name(ctx: RunContext[AgentDependencies]) -> AgentName:
        names = {
            "boss": "Boss",
            "inventory": "Inventory",
            "accounting": "Accounting",
            "facilities": "Facilities",
            "customer_service": "Customer Service",
        }
        return cast(AgentName, names.get(ctx.agent.name, "Boss"))


def create_team(limits: TeamLimits | None = None) -> TeamRuntime:
    """Construct the five-agent team without starting a ticket run."""
    return TeamRuntime(limits)
