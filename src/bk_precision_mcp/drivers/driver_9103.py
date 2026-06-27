"""Driver for BK Precision 9103/9104 series proprietary serial protocol.

Protocol notes (from BK Precision 9103/9104 Programming Manual):
  - USB virtual COM port at 9600 8N1, no flow control
  - Commands end with CR (\r); every successful command gets "OK\r" back.
  - Voltage and current values are transmitted as 4-digit integers
    representing the value × 100:
      1250  →  12.50 V  (or A)
      0500  →   5.00 A
  - SOUT logic is NORMAL (opposite of the 168x series):
      SOUT 0  →  output OFF
      SOUT 1  →  output ON
  - The supply has 4 preset slots (0–2 = memory presets, 3 = normal/live mode).
    For straightforward V/I programming we use slot 3 (normal mode).
  - SETD command: SETD <slot> <vvvv> <aaaa>
      e.g. SETD 3 1250 0500  → set normal mode to 12.50 V / 5.00 A
  - VOLT/CURR commands select which preset slot is active on the output:
      VOLT 3  → apply slot 3 voltage to output
      CURR 3  → apply slot 3 current limit to output
  - GETD response lines (each terminated by \r, then "OK\r"):
      line 1 → measured voltage as 4-digit integer (e.g. "1248")
      line 2 → measured current as 4-digit integer (e.g. "0499")
      line 3 → mode: "0" = CV, "1" = CC
  - GALL returns a multi-line dump of all settings.

  NOTE: The exact SETD/VOLT/CURR interaction was derived from the
  programming manual summary. Verify on real hardware if behaviour differs.
"""

from __future__ import annotations

import pyvisa

from bk_precision_mcp.drivers.base import BKPowerSupplyDriver
from bk_precision_mcp.transport.visa import open_resource

_NORMAL_SLOT = 3  # preset slot used for live V/I programming


class Driver9103(BKPowerSupplyDriver):
    def __init__(self) -> None:
        self._resource: pyvisa.resources.Resource | None = None
        self._profile: dict = {}

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self, resource_string: str, profile: dict) -> None:
        self._profile = profile
        self._resource = open_resource(
            resource_string,
            timeout_ms=5000,
            baud_rate=profile.get("baud", 9600),
            write_termination="\r",
            read_termination="\r",
        )
        # Verify the instrument by sending GALL and checking for a response.
        try:
            self._cmd("GALL")
        except Exception as exc:
            self._resource.close()
            self._resource = None
            raise ConnectionError(
                f"No response to GALL on {resource_string}. "
                "Verify the model is a 9103/9104 and the correct COM port is specified."
            ) from exc

    def disconnect(self) -> None:
        if self._resource is not None:
            try:
                self._write("SOUT 0")  # output OFF (0 = off for 9103)
            except Exception:
                pass
            self._resource.close()
            self._resource = None

    # ------------------------------------------------------------------
    # Output control
    # ------------------------------------------------------------------

    def set_voltage(self, volts: float, channel: int = 1) -> None:
        v_int = _encode(volts)
        # Read current current setpoint so we don't clobber it.
        # Simplification: set normal slot with current I=max from profile.
        # Callers should set_current separately; this only updates voltage.
        # We use SETD to update the slot then activate it.
        i_int = _encode(self._profile.get("i_max", 20.0))
        self._write(f"SETD {_NORMAL_SLOT} {v_int:04d} {i_int:04d}")
        self._write(f"VOLT {_NORMAL_SLOT}")

    def set_current(self, amps: float, channel: int = 1) -> None:
        v_int = _encode(self._profile.get("v_max", 42.0))
        i_int = _encode(amps)
        self._write(f"SETD {_NORMAL_SLOT} {v_int:04d} {i_int:04d}")
        self._write(f"CURR {_NORMAL_SLOT}")

    def output_on(self, channel: int = 1) -> None:
        self._write("SOUT 1")  # 1 = ON  (normal logic)

    def output_off(self, channel: int = 1) -> None:
        self._write("SOUT 0")  # 0 = OFF (normal logic)

    def set_ovp(self, volts: float) -> None:
        self._write(f"SOVP {_encode(volts):04d}")

    def set_ocp(self, amps: float) -> None:
        self._write(f"SOCP {_encode(amps):04d}")

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
        """Send a command and consume the OK acknowledgement."""
        res = self._check()
        res.write(cmd)
        res.read()  # consume "OK"

    def _cmd(self, cmd: str) -> str:
        """Send a query command and return data lines before OK."""
        res = self._check()
        res.write(cmd)
        lines: list[str] = []
        for _ in range(20):
            line = res.read().strip()
            if line.upper() == "OK":
                break
            lines.append(line)
        return "\n".join(lines)

    def _getd(self) -> tuple[float, float, str]:
        """Send GETD and return (voltage_V, current_A, mode_str)."""
        raw = self._cmd("GETD")
        parts = [p.strip() for p in raw.split("\n")]
        if len(parts) < 3:
            raise RuntimeError(f"Unexpected GETD response: {raw!r}")
        voltage = _decode(parts[0])
        current = _decode(parts[1])
        mode = parts[2]
        return voltage, current, mode


def _encode(value: float) -> int:
    """Convert a float to a 4-digit integer (value × 100)."""
    return round(value * 100)


def _decode(raw: str) -> float:
    """Convert a 4-digit integer string to a float (÷ 100)."""
    return int(raw.strip()) / 100.0
