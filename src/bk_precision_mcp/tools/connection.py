"""MCP tools for connecting to and discovering BK Precision power supplies."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from bk_precision_mcp import registry, session
from bk_precision_mcp.transport import visa


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def bk_get_supported_models() -> list[dict]:
        """Return a table of all BK Precision power supply models supported by this MCP.

        Each entry includes: model_id, family, description, v_max, i_max, p_max,
        channels, interfaces, scpi, list_mode, high_voltage, and the driver used.

        Call this before bk_connect() to understand what capabilities a model
        has and whether it requires special handling (e.g. confirm=True for
        high-voltage models or setpoints >= 50 V).
        """
        return registry.list_models()

    @mcp.tool()
    def bk_list_instruments() -> dict:
        """List all VISA resources currently visible to PyVISA.

        Returns a dict with:
          - 'resources': list of VISA resource strings
          - 'hint': guidance on how to use resource strings with bk_connect()
          - 'connected': resource strings with active bk_connect() sessions

        Typical resource string formats:
          Serial/USB-CDC: ASRL3::INSTR  (Windows COM3)
                          ASRL/dev/ttyUSB0::INSTR  (Linux)
          USBTMC:         USB0::0x0BDB::0x1001::INSTR
          LAN:            TCPIP0::192.168.1.100::5025::SOCKET
        """
        resources = visa.list_resources()
        return {
            "resources": resources,
            "connected": session.list_sessions(),
            "hint": (
                "Pass a resource string to bk_connect(resource_string, model_id). "
                "For 168x/9103 series (proprietary protocol) you must supply model_id. "
                "For SCPI models (9200B, 9115, XLN, PVS, etc.) model_id is optional — "
                "the instrument will be identified via *IDN?."
            ),
        }

    @mcp.tool()
    def bk_connect(resource_string: str, model_id: str | None = None) -> dict:
        """Connect to a BK Precision power supply.

        Args:
            resource_string: PyVISA resource address (e.g. 'ASRL3::INSTR' for
                             Windows COM3, 'ASRL/dev/ttyUSB0::INSTR' on Linux,
                             or 'TCPIP0::192.168.1.100::5025::SOCKET' for LAN).
            model_id: Model identifier from the registry (e.g. '1685B', '9103',
                      'XLN6024'). Required for proprietary-protocol models
                      (168x, 9103 series). Optional for SCPI models — if omitted
                      the instrument is identified via *IDN?.

        Returns a dict with the model profile and connected session info.
        Call bk_get_supported_models() to see valid model_id values.
        """
        if resource_string in session.list_sessions():
            driver, profile = session.get_session(resource_string)
            return {
                "status": "already_connected",
                "model_id": profile["model_id"],
                "profile": profile,
            }

        # Resolve model profile
        if model_id is not None:
            profile = registry.get_model_profile(model_id)
        else:
            # Try SCPI auto-detect via *IDN?
            profile = _auto_detect(resource_string)

        # Instantiate and connect the driver
        driver = session.make_driver(profile["driver"])
        driver.connect(resource_string, profile)
        session.set_session(resource_string, driver, profile)

        return {
            "status": "connected",
            "model_id": profile["model_id"],
            "description": profile["description"],
            "v_max": profile["v_max"],
            "i_max": profile["i_max"],
            "p_max": profile["p_max"],
            "channels": profile["channels"],
            "interfaces": profile["interfaces"],
            "scpi": profile["scpi"],
            "list_mode": profile["list_mode"],
            "high_voltage": profile["high_voltage"],
            "hv_note": (
                f"Output requires confirm=True because this model can exceed 50 V."
                if profile["high_voltage"]
                else (
                    "Voltage setpoints >= 50 V require confirm=True on bk_set_voltage()."
                    if profile["v_max"] >= 50.0
                    else None
                )
            ),
        }

    @mcp.tool()
    def bk_disconnect(resource_string: str) -> dict:
        """Disconnect from a BK Precision power supply.

        Sends output OFF before closing the transport regardless of current
        output state. Safe to call even if the output is already off.

        Args:
            resource_string: The VISA resource string passed to bk_connect().
        """
        if resource_string not in session.list_sessions():
            return {"status": "not_connected", "resource_string": resource_string}

        driver, profile = session.get_session(resource_string)
        driver.disconnect()
        session.clear_session(resource_string)
        return {
            "status": "disconnected",
            "model_id": profile["model_id"],
            "resource_string": resource_string,
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _auto_detect(resource_string: str) -> dict:
    """Try *IDN? on the resource and match the response to the registry.

    Raises:
        ConnectionError: If *IDN? fails or the model is not in the registry.
    """
    from bk_precision_mcp.transport.visa import open_resource
    try:
        res = open_resource(resource_string, write_termination="\n", read_termination="\n")
        try:
            idn = res.query("*IDN?").strip()
        finally:
            res.close()
    except Exception as exc:
        raise ConnectionError(
            f"Could not query *IDN? on {resource_string}: {exc}. "
            "For proprietary-protocol models (168x, 9103 series), "
            "you must pass model_id explicitly."
        ) from exc

    model_id = registry.find_model_by_idn(idn)
    if model_id is None:
        known = ", ".join(m["model_id"] for m in registry.list_models() if m["scpi"])
        raise ConnectionError(
            f"*IDN? returned {idn!r} but no matching model was found in the registry. "
            f"Pass model_id explicitly. SCPI models in registry: {known}"
        )
    return registry.get_model_profile(model_id)
