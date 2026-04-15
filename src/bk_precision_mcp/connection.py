"""PyVISA resource manager singleton and instrument open/close helpers."""

import pyvisa

_rm: pyvisa.ResourceManager | None = None


def get_resource_manager() -> pyvisa.ResourceManager:
    global _rm
    if _rm is None:
        _rm = pyvisa.ResourceManager("@py")
    return _rm


def list_resources() -> list[str]:
    """Return all VISA resource strings visible to pyvisa-py."""
    rm = get_resource_manager()
    return list(rm.list_resources())


def open_instrument(resource_string: str, timeout_ms: int = 5000) -> pyvisa.resources.Resource:
    """Open a VISA resource and return the handle.

    Supported resource string formats:
      USB:      USB0::0x0BDB::0x1001::INSTR
      Ethernet: TCPIP0::192.168.1.100::inst0::INSTR
                TCPIP0::192.168.1.100::5025::SOCKET
      Serial:   ASRL/dev/ttyUSB0::INSTR  (Linux)
                ASRL3::INSTR              (Windows COM3)
    """
    rm = get_resource_manager()
    resource = rm.open_resource(resource_string)
    resource.timeout = timeout_ms
    return resource
