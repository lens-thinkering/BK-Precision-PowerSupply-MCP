"""PyVISA resource manager singleton and resource open helper."""

from __future__ import annotations

import pyvisa

_rm: pyvisa.ResourceManager | None = None


def get_resource_manager() -> pyvisa.ResourceManager:
    """Return the shared ResourceManager, creating it once on first call."""
    global _rm
    if _rm is None:
        _rm = pyvisa.ResourceManager("@py")
    return _rm


def list_resources() -> list[str]:
    """Return all VISA resource strings currently visible to pyvisa-py.

    Typical formats returned:
      Serial/USB-CDC : ASRL3::INSTR  (Windows COM3)
                       ASRL/dev/ttyUSB0::INSTR  (Linux)
      USBTMC         : USB0::0x0BDB::0x1001::INSTR
      LAN            : TCPIP0::192.168.1.100::inst0::INSTR
                       TCPIP0::192.168.1.100::5025::SOCKET
    """
    return list(get_resource_manager().list_resources())


def open_resource(
    resource_string: str,
    timeout_ms: int = 5000,
    baud_rate: int | None = None,
    write_termination: str = "\r",
    read_termination: str = "\r",
) -> pyvisa.resources.Resource:
    """Open a VISA resource and return the handle.

    Args:
        resource_string: VISA address string.
        timeout_ms: Read/write timeout in milliseconds.
        baud_rate: Serial baud rate override (serial resources only).
        write_termination: Line terminator appended to every write().
        read_termination: Line terminator that ends a read().
    """
    rm = get_resource_manager()
    resource = rm.open_resource(resource_string)
    resource.timeout = timeout_ms
    resource.write_termination = write_termination
    resource.read_termination = read_termination
    if baud_rate is not None and hasattr(resource, "baud_rate"):
        resource.baud_rate = baud_rate  # type: ignore[attr-defined]
    return resource
