"""MCP tools for BK Precision multimeters/DMMs."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from bk_precision_mcp.instruments.multimeter import Multimeter


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def bk_dmm_measure_voltage(resource_string: str, dc: bool = True) -> float:
        """Measure voltage with a BK Precision DMM.

        Args:
            resource_string: VISA resource string for the instrument.
            dc: True for DC voltage, False for AC voltage.
        """
        with Multimeter(resource_string) as dmm:
            return dmm.measure_voltage(dc)

    @mcp.tool()
    def bk_dmm_measure_current(resource_string: str, dc: bool = True) -> float:
        """Measure current with a BK Precision DMM.

        Args:
            resource_string: VISA resource string for the instrument.
            dc: True for DC current, False for AC current.
        """
        with Multimeter(resource_string) as dmm:
            return dmm.measure_current(dc)

    @mcp.tool()
    def bk_dmm_measure_resistance(resource_string: str) -> float:
        """Measure resistance with a BK Precision DMM.

        Args:
            resource_string: VISA resource string for the instrument.
        """
        with Multimeter(resource_string) as dmm:
            return dmm.measure_resistance()

    @mcp.tool()
    def bk_dmm_measure_continuity(resource_string: str) -> float:
        """Test continuity with a BK Precision DMM. Returns resistance in ohms.

        Args:
            resource_string: VISA resource string for the instrument.
        """
        with Multimeter(resource_string) as dmm:
            return dmm.measure_continuity()

    @mcp.tool()
    def bk_dmm_measure_diode(resource_string: str) -> float:
        """Measure diode forward voltage with a BK Precision DMM.

        Args:
            resource_string: VISA resource string for the instrument.
        """
        with Multimeter(resource_string) as dmm:
            return dmm.measure_diode()
