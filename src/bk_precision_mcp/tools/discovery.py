"""MCP tools for instrument discovery and identification."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from bk_precision_mcp.connection import list_resources, open_instrument


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def bk_list_instruments() -> list[str]:
        """List all VISA resource strings for connected BK Precision instruments."""
        return list_resources()

    @mcp.tool()
    def bk_identify_instrument(resource_string: str) -> str:
        """Send *IDN? to an instrument and return its identification string.

        Args:
            resource_string: VISA resource string, e.g. USB0::0x0BDB::0x1001::INSTR
        """
        resource = open_instrument(resource_string)
        try:
            return resource.query("*IDN?").strip()
        finally:
            resource.close()
