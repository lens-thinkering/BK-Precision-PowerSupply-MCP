"""Active connection session registry.

Stores the live (driver, profile) pair for each connected resource string.
Drivers are imported lazily to avoid pulling in PyVISA at import time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bk_precision_mcp.drivers.base import BKPowerSupplyDriver

# resource_string → (driver_instance, model_profile_dict)
_sessions: dict[str, tuple["BKPowerSupplyDriver", dict]] = {}

_DRIVER_MAP = {
    "driver_1685b": "bk_precision_mcp.drivers.driver_1685b:Driver1685B",
    "driver_9103": "bk_precision_mcp.drivers.driver_9103:Driver9103",
    "driver_scpi": "bk_precision_mcp.drivers.driver_scpi:DriverSCPI",
}


def make_driver(driver_key: str) -> "BKPowerSupplyDriver":
    """Instantiate a driver by its registry key string (e.g. 'driver_1685b')."""
    if driver_key not in _DRIVER_MAP:
        raise KeyError(f"Unknown driver key '{driver_key}'. Known: {list(_DRIVER_MAP)}")
    module_path, class_name = _DRIVER_MAP[driver_key].split(":")
    import importlib
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    return cls()


def set_session(resource_string: str, driver: "BKPowerSupplyDriver", profile: dict) -> None:
    """Store a connected (driver, profile) pair."""
    _sessions[resource_string] = (driver, profile)


def get_session(resource_string: str) -> tuple["BKPowerSupplyDriver", dict]:
    """Return (driver, profile) for an active connection.

    Raises:
        RuntimeError: If the resource_string is not currently connected.
    """
    if resource_string not in _sessions:
        connected = list(_sessions) or ["(none)"]
        raise RuntimeError(
            f"No active connection for '{resource_string}'. "
            f"Call bk_connect() first. Currently connected: {connected}"
        )
    return _sessions[resource_string]


def clear_session(resource_string: str) -> None:
    """Remove a session entry (called after disconnect)."""
    _sessions.pop(resource_string, None)


def list_sessions() -> list[str]:
    """Return resource strings of all currently connected instruments."""
    return list(_sessions)
