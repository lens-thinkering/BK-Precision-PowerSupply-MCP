"""Smoke tests for MCP tool registration."""

import asyncio

from mcp.server.fastmcp import FastMCP

from bk_precision_mcp.tools import (
    discovery,
    function_gen,
    multimeter,
    oscilloscope,
    power_supply,
)


def _make_mcp() -> FastMCP:
    mcp = FastMCP("test")
    discovery.register(mcp)
    power_supply.register(mcp)
    multimeter.register(mcp)
    oscilloscope.register(mcp)
    function_gen.register(mcp)
    return mcp


def test_all_tools_registered():
    mcp = _make_mcp()
    tool_names = {t.name for t in asyncio.run(mcp.list_tools())}
    expected = {
        "bk_list_instruments",
        "bk_identify_instrument",
        "bk_ps_set_voltage",
        "bk_ps_set_current",
        "bk_ps_output_on",
        "bk_ps_output_off",
        "bk_ps_measure_voltage",
        "bk_ps_measure_current",
        "bk_ps_get_status",
        "bk_dmm_measure_voltage",
        "bk_dmm_measure_current",
        "bk_dmm_measure_resistance",
        "bk_dmm_measure_continuity",
        "bk_dmm_measure_diode",
        "bk_osc_autoscale",
        "bk_osc_run",
        "bk_osc_stop",
        "bk_osc_measure_frequency",
        "bk_osc_measure_amplitude",
        "bk_osc_set_timebase",
        "bk_osc_set_voltage_scale",
        "bk_fg_set_waveform",
        "bk_fg_set_frequency",
        "bk_fg_set_amplitude",
        "bk_fg_set_offset",
        "bk_fg_output_on",
        "bk_fg_output_off",
    }
    assert expected.issubset(tool_names), f"Missing tools: {expected - tool_names}"
