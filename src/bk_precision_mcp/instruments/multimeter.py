"""BK Precision multimeter/DMM SCPI commands."""

from __future__ import annotations

from bk_precision_mcp.instruments.base import BaseInstrument


class Multimeter(BaseInstrument):
    def measure_voltage(self, dc: bool = True) -> float:
        cmd = "MEASure:VOLTage:DC?" if dc else "MEASure:VOLTage:AC?"
        return float(self.query(cmd))

    def measure_current(self, dc: bool = True) -> float:
        cmd = "MEASure:CURRent:DC?" if dc else "MEASure:CURRent:AC?"
        return float(self.query(cmd))

    def measure_resistance(self) -> float:
        return float(self.query("MEASure:RESistance?"))

    def measure_continuity(self) -> float:
        return float(self.query("MEASure:CONTinuity?"))

    def measure_diode(self) -> float:
        return float(self.query("MEASure:DIODe?"))
