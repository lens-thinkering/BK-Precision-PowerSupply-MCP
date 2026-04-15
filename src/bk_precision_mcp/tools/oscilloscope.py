"""MCP tools for BK Precision oscilloscopes."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from bk_precision_mcp.instruments.oscilloscope import Oscilloscope


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def bk_osc_autoscale(resource_string: str) -> str:
        """Trigger autoscale on a BK Precision oscilloscope.

        Args:
            resource_string: VISA resource string for the instrument.
        """
        with Oscilloscope(resource_string) as osc:
            osc.autoscale()
        return "Autoscale triggered"

    @mcp.tool()
    def bk_osc_run(resource_string: str) -> str:
        """Start acquisition on a BK Precision oscilloscope.

        Args:
            resource_string: VISA resource string for the instrument.
        """
        with Oscilloscope(resource_string) as osc:
            osc.run()
        return "Acquisition running"

    @mcp.tool()
    def bk_osc_stop(resource_string: str) -> str:
        """Stop acquisition on a BK Precision oscilloscope.

        Args:
            resource_string: VISA resource string for the instrument.
        """
        with Oscilloscope(resource_string) as osc:
            osc.stop()
        return "Acquisition stopped"

    @mcp.tool()
    def bk_osc_measure_frequency(resource_string: str, channel: int = 1) -> float:
        """Measure signal frequency on an oscilloscope channel.

        Args:
            resource_string: VISA resource string for the instrument.
            channel: Channel number (default 1).
        """
        with Oscilloscope(resource_string) as osc:
            return osc.measure_frequency(channel)

    @mcp.tool()
    def bk_osc_measure_amplitude(resource_string: str, channel: int = 1) -> float:
        """Measure signal amplitude (peak-to-peak) on an oscilloscope channel.

        Args:
            resource_string: VISA resource string for the instrument.
            channel: Channel number (default 1).
        """
        with Oscilloscope(resource_string) as osc:
            return osc.measure_amplitude(channel)

    @mcp.tool()
    def bk_osc_set_timebase(resource_string: str, seconds_per_div: float) -> str:
        """Set the timebase (horizontal scale) of a BK Precision oscilloscope.

        Args:
            resource_string: VISA resource string for the instrument.
            seconds_per_div: Time per division in seconds (e.g. 0.001 for 1 ms/div).
        """
        with Oscilloscope(resource_string) as osc:
            osc.set_timebase(seconds_per_div)
        return f"Timebase set to {seconds_per_div} s/div"

    @mcp.tool()
    def bk_osc_set_voltage_scale(
        resource_string: str, volts_per_div: float, channel: int = 1
    ) -> str:
        """Set the vertical scale of an oscilloscope channel.

        Args:
            resource_string: VISA resource string for the instrument.
            volts_per_div: Volts per division (e.g. 1.0 for 1 V/div).
            channel: Channel number (default 1).
        """
        with Oscilloscope(resource_string) as osc:
            osc.set_voltage_scale(volts_per_div, channel)
        return f"Channel {channel} scale set to {volts_per_div} V/div"
