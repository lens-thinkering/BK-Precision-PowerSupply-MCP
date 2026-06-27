"""Driver for BK Precision SCPI IEEE-488.2 power supply families.

Covers: 9200B, 9115/9116/9117, 9170B/9180B, XLN, PVS, HPS series.

These models use standard SCPI commands and are auto-detectable via *IDN?.
Transport can be USBTMC (USB), raw TCP socket on port 5025 (LAN),
or RS-232 serial — all handled transparently by PyVISA.

Multi-channel models (9129B, 9130B) use INSTrument:NSELect for channel
routing — this driver handles the channel parameter but those models are
not yet in the registry (Phase 2).
"""

from __future__ import annotations

import pyvisa

from bk_precision_mcp.drivers.base import BKPowerSupplyDriver
from bk_precision_mcp.transport.visa import open_resource


class DriverSCPI(BKPowerSupplyDriver):
    def __init__(self) -> None:
        self._resource: pyvisa.resources.Resource | None = None
        self._profile: dict = {}

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self, resource_string: str, profile: dict) -> None:
        self._profile = profile
        # SCPI over LAN uses raw socket on port 5025; no CR termination needed.
        is_socket = "SOCKET" in resource_string.upper()
        self._resource = open_resource(
            resource_string,
            timeout_ms=5000,
            write_termination="\n",
            read_termination="\n",
        )
        # Verify with *IDN?
        try:
            idn = self._query("*IDN?")
        except Exception as exc:
            self._resource.close()
            self._resource = None
            raise ConnectionError(
                f"No response to *IDN? on {resource_string}. "
                "Verify the instrument is powered on and the interface is correct."
            ) from exc
        if "B&K" not in idn.upper() and "BK" not in idn.upper():
            raise ConnectionError(
                f"Unexpected *IDN? response: {idn!r}. "
                "This does not appear to be a BK Precision instrument."
            )
        self._write("*CLS")  # clear status registers

    def disconnect(self) -> None:
        if self._resource is not None:
            try:
                self._write("OUTP OFF")
            except Exception:
                pass
            self._resource.close()
            self._resource = None

    # ------------------------------------------------------------------
    # Output control
    # ------------------------------------------------------------------

    def set_voltage(self, volts: float, channel: int = 1) -> None:
        self._select_channel(channel)
        self._write(f"VOLT {volts:.3f}")

    def set_current(self, amps: float, channel: int = 1) -> None:
        self._select_channel(channel)
        self._write(f"CURR {amps:.3f}")

    def output_on(self, channel: int = 1) -> None:
        self._select_channel(channel)
        self._write("OUTP ON")

    def output_off(self, channel: int = 1) -> None:
        self._select_channel(channel)
        self._write("OUTP OFF")

    def set_ovp(self, volts: float) -> None:
        self._write(f"VOLT:PROT {volts:.3f}")

    def set_ocp(self, amps: float) -> None:
        self._write(f"CURR:PROT {amps:.3f}")

    # ------------------------------------------------------------------
    # Measurement
    # ------------------------------------------------------------------

    def measure_voltage(self, channel: int = 1) -> float:
        self._select_channel(channel)
        return float(self._query("MEAS:VOLT?"))

    def measure_current(self, channel: int = 1) -> float:
        self._select_channel(channel)
        return float(self._query("MEAS:CURR?"))

    def get_status(self, channel: int = 1) -> dict:
        self._select_channel(channel)
        voltage = float(self._query("MEAS:VOLT?"))
        current = float(self._query("MEAS:CURR?"))
        out_raw = self._query("OUTP?").strip().upper()
        output_on = out_raw in ("1", "ON")
        # Determine CV vs CC via status register (bit 1 of questionable status)
        stat = int(self._query("STAT:QUES:COND?"))
        mode = "CC" if (stat & 0x01) else "CV"
        return {
            "voltage": voltage,
            "current": current,
            "mode": mode,
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
        self._check().write(cmd)

    def _query(self, cmd: str) -> str:
        return self._check().query(cmd).strip()

    def _select_channel(self, channel: int) -> None:
        """Issue INSTrument:NSELect only for multi-channel models."""
        if self._profile.get("channels", 1) > 1:
            self._write(f"INST:NSEL {channel}")
