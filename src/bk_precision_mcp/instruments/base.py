"""Base instrument class providing SCPI primitives."""

from __future__ import annotations

import pyvisa

from bk_precision_mcp.connection import open_instrument


class BaseInstrument:
    def __init__(self, resource_string: str, timeout_ms: int = 5000) -> None:
        self.resource_string = resource_string
        self.timeout_ms = timeout_ms
        self._resource: pyvisa.resources.Resource | None = None

    def open(self) -> None:
        self._resource = open_instrument(self.resource_string, self.timeout_ms)

    def close(self) -> None:
        if self._resource is not None:
            self._resource.close()
            self._resource = None

    def __enter__(self) -> "BaseInstrument":
        self.open()
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def _check_open(self) -> pyvisa.resources.Resource:
        if self._resource is None:
            raise RuntimeError(f"Instrument not open: {self.resource_string}")
        return self._resource

    def write(self, cmd: str) -> None:
        self._check_open().write(cmd)

    def query(self, cmd: str) -> str:
        return self._check_open().query(cmd).strip()

    def identify(self) -> str:
        """Send *IDN? and return the instrument identification string."""
        return self.query("*IDN?")

    def reset(self) -> None:
        """Send *RST to restore factory defaults."""
        self.write("*RST")

    def clear(self) -> None:
        """Send *CLS to clear status registers."""
        self.write("*CLS")
