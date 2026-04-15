"""BK Precision MCP server entry point."""

from mcp.server.fastmcp import FastMCP

from bk_precision_mcp.tools import (
    discovery,
    function_gen,
    multimeter,
    oscilloscope,
    power_supply,
)

mcp = FastMCP("BK Precision Instruments")

discovery.register(mcp)
power_supply.register(mcp)
multimeter.register(mcp)
oscilloscope.register(mcp)
function_gen.register(mcp)


def main() -> None:
    mcp.run()
