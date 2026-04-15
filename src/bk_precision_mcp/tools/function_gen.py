"""MCP tools for BK Precision function generators."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from bk_precision_mcp.instruments.function_gen import FunctionGenerator


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def bk_fg_set_waveform(
        resource_string: str,
        shape: str,
        channel: int = 1,
    ) -> str:
        """Set the output waveform shape on a BK Precision function generator.

        Args:
            resource_string: VISA resource string for the instrument.
            shape: Waveform shape — one of SIN, SQU, RAMP, PULS, NOIS, DC.
            channel: Output channel number (default 1).
        """
        with FunctionGenerator(resource_string) as fg:
            fg.set_waveform(shape.upper(), channel)  # type: ignore[arg-type]
        return f"Channel {channel} waveform set to {shape.upper()}"

    @mcp.tool()
    def bk_fg_set_frequency(resource_string: str, hz: float, channel: int = 1) -> str:
        """Set the output frequency on a BK Precision function generator.

        Args:
            resource_string: VISA resource string for the instrument.
            hz: Frequency in hertz.
            channel: Output channel number (default 1).
        """
        with FunctionGenerator(resource_string) as fg:
            fg.set_frequency(hz, channel)
        return f"Channel {channel} frequency set to {hz} Hz"

    @mcp.tool()
    def bk_fg_set_amplitude(resource_string: str, volts: float, channel: int = 1) -> str:
        """Set the output amplitude (peak-to-peak) on a BK Precision function generator.

        Args:
            resource_string: VISA resource string for the instrument.
            volts: Amplitude in volts peak-to-peak.
            channel: Output channel number (default 1).
        """
        with FunctionGenerator(resource_string) as fg:
            fg.set_amplitude(volts, channel)
        return f"Channel {channel} amplitude set to {volts} Vpp"

    @mcp.tool()
    def bk_fg_set_offset(resource_string: str, volts: float, channel: int = 1) -> str:
        """Set the DC offset on a BK Precision function generator.

        Args:
            resource_string: VISA resource string for the instrument.
            volts: DC offset in volts.
            channel: Output channel number (default 1).
        """
        with FunctionGenerator(resource_string) as fg:
            fg.set_offset(volts, channel)
        return f"Channel {channel} offset set to {volts} V"

    @mcp.tool()
    def bk_fg_output_on(resource_string: str, channel: int = 1) -> str:
        """Enable the output of a BK Precision function generator.

        Args:
            resource_string: VISA resource string for the instrument.
            channel: Output channel number (default 1).
        """
        with FunctionGenerator(resource_string) as fg:
            fg.output_on(channel)
        return f"Channel {channel} output enabled"

    @mcp.tool()
    def bk_fg_output_off(resource_string: str, channel: int = 1) -> str:
        """Disable the output of a BK Precision function generator.

        Args:
            resource_string: VISA resource string for the instrument.
            channel: Output channel number (default 1).
        """
        with FunctionGenerator(resource_string) as fg:
            fg.output_off(channel)
        return f"Channel {channel} output disabled"
