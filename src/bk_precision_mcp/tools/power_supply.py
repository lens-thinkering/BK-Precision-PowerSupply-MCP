"""MCP tools for BK Precision power supplies."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from bk_precision_mcp.instruments.power_supply import PowerSupply


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def bk_ps_set_voltage(resource_string: str, volts: float, channel: int = 1) -> str:
        """Set the output voltage on a BK Precision power supply.

        Args:
            resource_string: VISA resource string for the instrument.
            volts: Target voltage in volts.
            channel: Output channel number (default 1).
        """
        with PowerSupply(resource_string) as ps:
            ps.set_voltage(volts, channel)
        return f"Channel {channel} voltage set to {volts} V"

    @mcp.tool()
    def bk_ps_set_current(resource_string: str, amps: float, channel: int = 1) -> str:
        """Set the current limit on a BK Precision power supply.

        Args:
            resource_string: VISA resource string for the instrument.
            amps: Current limit in amperes.
            channel: Output channel number (default 1).
        """
        with PowerSupply(resource_string) as ps:
            ps.set_current(amps, channel)
        return f"Channel {channel} current limit set to {amps} A"

    @mcp.tool()
    def bk_ps_output_on(resource_string: str, channel: int = 1) -> str:
        """Enable the output of a BK Precision power supply.

        Args:
            resource_string: VISA resource string for the instrument.
            channel: Output channel number (default 1).
        """
        with PowerSupply(resource_string) as ps:
            ps.output_on(channel)
        return f"Channel {channel} output enabled"

    @mcp.tool()
    def bk_ps_output_off(resource_string: str, channel: int = 1) -> str:
        """Disable the output of a BK Precision power supply.

        Args:
            resource_string: VISA resource string for the instrument.
            channel: Output channel number (default 1).
        """
        with PowerSupply(resource_string) as ps:
            ps.output_off(channel)
        return f"Channel {channel} output disabled"

    @mcp.tool()
    def bk_ps_measure_voltage(resource_string: str, channel: int = 1) -> float:
        """Measure the actual output voltage of a BK Precision power supply.

        Args:
            resource_string: VISA resource string for the instrument.
            channel: Output channel number (default 1).
        """
        with PowerSupply(resource_string) as ps:
            return ps.measure_voltage(channel)

    @mcp.tool()
    def bk_ps_measure_current(resource_string: str, channel: int = 1) -> float:
        """Measure the actual output current of a BK Precision power supply.

        Args:
            resource_string: VISA resource string for the instrument.
            channel: Output channel number (default 1).
        """
        with PowerSupply(resource_string) as ps:
            return ps.measure_current(channel)

    @mcp.tool()
    def bk_ps_get_status(resource_string: str, channel: int = 1) -> dict:
        """Get voltage, current, and output state of a BK Precision power supply channel.

        Args:
            resource_string: VISA resource string for the instrument.
            channel: Output channel number (default 1).
        """
        with PowerSupply(resource_string) as ps:
            return ps.get_status(channel)
