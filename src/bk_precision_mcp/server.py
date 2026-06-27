"""BK Precision MCP server entry point."""

from mcp.server.fastmcp import FastMCP

from bk_precision_mcp.tools import connection, power_supply

mcp = FastMCP("BK Precision Power Supplies")

connection.register(mcp)
power_supply.register(mcp)


def main() -> None:
    mcp.run()
