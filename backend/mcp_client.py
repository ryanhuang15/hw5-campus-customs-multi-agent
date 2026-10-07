"""The only shop-data gateway used by the agent team."""

from pathlib import Path
from typing import Any

from fastmcp import Client


MCP_SERVER_PATH = Path(__file__).resolve().parents[1] / "mcp_server" / "server.py"
ALLOWED_TOOLS = {
    "investigate_customer_order",
    "investigate_rent_notice",
    "investigate_bulk_hoodie_request",
    "list_open_tickets",
    "get_ticket_board",
    "get_shop_date",
    "mark_ticket_resolved",
    "get_accounting_context",
    "get_restock_options",
    "execute_approved_payment",
}


class MCPGateway:
    """Call the configured local MCP server; never open the shop database here."""

    async def call(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        tool_name = tool_name.replace("\u200b", "").strip()
        aliases = {
            "ticket_board.get_ticket": "get_ticket_board",
            "ticket_board_get_ticket": "get_ticket_board",
            "ticket_board_get": "get_ticket_board",
            "ticket_board": "get_ticket_board",
            "inventory.ticket_investigation": "investigate_customer_order",
            "inventory_ticket_investigation": "investigate_customer_order",
            "ticket_investigate": "investigate_customer_order",
            "inventory_rest ock_options": "get_restock_options",
            "inventory_restock_options": "get_restock_options",
            "pricing.lookup": "get_accounting_context",
            "catalog.pricing": "get_accounting_context",
            "desk.date_today": "get_shop_date",
            "desk_date_today": "get_shop_date",
        }
        tool_name = aliases.get(tool_name, tool_name)
        if tool_name not in ALLOWED_TOOLS:
            return {
                "error": f"Unknown MCP tool: {tool_name}",
                "available_tools": sorted(ALLOWED_TOOLS),
                "instruction": "Choose one exact available tool name and try again.",
            }
        if tool_name in {"get_ticket_board", "get_shop_date"}:
            arguments = {}
        elif tool_name == "get_accounting_context":
            arguments = {}
        elif tool_name == "investigate_customer_order":
            arguments = {"ticket_id": arguments.get("ticket_id", 101)}
        elif tool_name == "investigate_rent_notice":
            arguments = {"ticket_id": arguments.get("ticket_id", 102)}
        elif tool_name == "investigate_bulk_hoodie_request":
            arguments = {"ticket_id": arguments.get("ticket_id", 103)}
        elif tool_name == "get_restock_options":
            arguments = {
                "sku": arguments.get("sku", ""),
                "size": arguments.get("size", ""),
                "requested_qty": arguments.get(
                    "requested_qty",
                    arguments.get("requested_quantity", arguments.get("quantity", arguments.get("qty", 0))),
                ),
            }
        try:
            async with Client(MCP_SERVER_PATH) as client:
                result = await client.call_tool(tool_name, arguments)
                return result.data
        except Exception as exc:
            return {
                "error": f"MCP tool {tool_name} failed validation or execution: {exc}",
                "tool_name": tool_name,
                "provided_arguments": arguments,
                "instruction": "Correct the arguments using the exact tool schema and try again; do not invent facts.",
            }
