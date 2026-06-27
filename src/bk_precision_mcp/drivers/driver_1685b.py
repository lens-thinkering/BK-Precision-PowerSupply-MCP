"""Driver for BK Precision 168x and 1900B series proprietary serial protocol.

Covers: 1685B, 1687B, 1688B, 1900B, 1901B, 1902B.

Protocol notes (from BK Precision 1685B Series Programming Manual):
  - USB virtual COM port at 9600 8N1, no flow control
  - Commands end with CR (\r); responses end with "OK\r" (write commands)
    or the data value(s) followed by "OK\r" (query commands)
  - SOUT logic is INVERTED vs every other BK model:
      SOUT 0  →  output ON
      SOUT 1  →  output OFF
  - Voltage and current are sent/received as decimal strings.
    Decimal places depend on model (registry key 'decimal_places'):
      1685B  →  2 dp  (e.g. "12.50")
      1687B, 1688B, 1900B series  →  1 dp  (e.g. "12.5")
  - GETD response lines (each terminated by \r, query ends with OK\r):
      line 1 → measured voltage  (e.g. "12.50")
      line 2 → measured current  (e.g. " 1.45")
      line 3 → mode: "0" = CV, "1" = CC
  - GMAX response lines:
      line 1 → max voltage
      line 2 → max current
"""

from __future__ import annotations

import pyvisa

from bk_precision_mcp.drivers.base import BKPowerSupplyDriver
from bk_precision_mcp.transport.visa import open_resource


class Driver1685B(BKPowerSupplyDriver):
    def __init__(self) -> None:
        self._resource: pyvisa.resources.Resource | None = None
        self._profile: dict = {}
        self._dp: int = 2  # decimal places for V/I formatting

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self, resource_string: str, profile: dict) -> None:
        self._profile = profile
        self._dp = profile.get("decimal_places", 2)
        self._resource = open_resource(
            resource_string,
            timeout_ms=5000,
            baud_rate=profile.get("baud", 9600),
            write_termination="\r",
            read_termination="\r",
        )
        # Verify the instrument is a 168x/1900B by issuing GMAX.
        # GMAX returns two lines (max V, max I) then "OK".
        try:
            self._cmd("GMAX")
        except Exception as exc:
            self._resource.close()
            self._resource = None
            raise ConnectionError(
                f"No response to GMAX on {resource_string}. "
                "Verify the model is a 1685B/1687B/1688B/1900B series and "
                "that the correct COM port is specified."
            ) from exc

    def disconnect(self) -> None:
        if self._resource is not None:
            try:
                self._write("SOUT 1")  # output OFF (inverted: 1 = off)
            except Exception:
                pass
            self._resource.close()
            self._resource = None

    # ------------------------------------------------------------------
    # Output control
    # ------------------------------------------------------------------

    def set_voltage(self, volts: float, channel: int = 1) -> None:
        self._write(f"VOLT {volts:.{self._dp}f}")

    def set_current(self, amps: float, channel: int = 1) -> None:
        self._write(f"CURR {amps:.{self._dp}f}")

    def output_on(self, channel: int = 1) -> None:
        self._write("SOUT 0")  # 0 = ON  (inverted logic)

    def output_off(self, channel: int = 1) -> None:
        self._write("SOUT 1")  # 1 = OFF (inverted logic)

    def set_ovp(self, volts: float) -> None:
        self._write(f"SOVP {volts:.{self._dp}f}")

    def set_ocp(self, amps: float) -> None:
        self._write(f"SOCP {amps:.{self._dp}f}")

    # ------------------------------------------------------------------
    # Measurement
    # ------------------------------------------------------------------

    def measure_voltage(self, channel: int = 1) -> float:
        v, _, _ = self._getd()
        return v

    def measure_current(self, channel: int = 1) -> float:
        _, i, _ = self._getd()
        return i

    def get_status(self, channel: int = 1) -> dict:
        v, i, mode_raw = self._getd()
        # Query output state via GOUT (returns "0" = off, "1" = on — NOT inverted)
        try:
            out_raw = self._cmd("GOUT").strip()
            output_on = out_raw == "1"
        except Exception:
            output_on = None  # type: ignore[assignment]
        return {
            "voltage": v,
            "current": i,
            "mode": "CC" if mode_raw == "1" else "CV",
            "output": output_on,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check(self) -> pyvisa.resources.Resource:
        if self._resource is None:
            raise RuntimeError("Not connected. Call bk_connect() first.")
        return self._resource

    def _write(self, cmd: str) -> None:
        """Send a command and consume the trailing OK response."""
        res = self._check()
        res.write(cmd)
        # Read and discard the "OK" acknowledgement line.
        res.read()

    def _cmd(self, cmd: str) -> str:
        """Send a query command and return the data line(s) before OK."""
        res = self._check()
        res.write(cmd)
        # Read lines until we see "OK".
        lines: list[str] = []
        for _ in range(10):
            line = res.read().strip()
            if line.upper() == "OK":
                break
            lines.append(line)
        return "\n".join(lines)

    def _getd(self) -> tuple[float, float, str]:
        """Send GETD and parse the three-line response.

        Returns (voltage_V, current_A, mode_str) where mode_str is "0" (CV)
        or "1" (CC).
        """
        raw = self._cmd("GETD")
        parts = [p.strip() for p in raw.split("\n")]
        if len(parts) < 3:
            raise RuntimeError(f"Unexpected GETD response: {raw!r}")
        voltage = float(parts[0])
        current = float(parts[1])
        mode = parts[2]
        return voltage, current, mode
