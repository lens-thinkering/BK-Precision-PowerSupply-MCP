"""BK Precision power supply SCPI commands."""

from __future__ import annotations

from bk_precision_mcp.instruments.base import BaseInstrument


class PowerSupply(BaseInstrument):
    def set_voltage(self, volts: float, channel: int = 1) -> None:
        self.write(f"INSTrument:NSELect {channel}")
        self.write(f"SOURce:VOLTage {volts:.6g}")

    def set_current(self, amps: float, channel: int = 1) -> None:
        self.write(f"INSTrument:NSELect {channel}")
        self.write(f"SOURce:CURRent {amps:.6g}")

    def output_on(self, channel: int = 1) -> None:
        self.write(f"INSTrument:NSELect {channel}")
        self.write("OUTPut:STATe ON")

    def output_off(self, channel: int = 1) -> None:
        self.write(f"INSTrument:NSELect {channel}")
        self.write("OUTPut:STATe OFF")

    def measure_voltage(self, channel: int = 1) -> float:
        self.write(f"INSTrument:NSELect {channel}")
        return float(self.query("MEASure:VOLTage:DC?"))

    def measure_current(self, channel: int = 1) -> float:
        self.write(f"INSTrument:NSELect {channel}")
        return float(self.query("MEASure:CURRent:DC?"))

    def get_status(self, channel: int = 1) -> dict:
        self.write(f"INSTrument:NSELect {channel}")
        voltage = float(self.query("MEASure:VOLTage:DC?"))
        current = float(self.query("MEASure:CURRent:DC?"))
        output_state = self.query("OUTPut:STATe?")
        return {
            "channel": channel,
            "voltage_V": voltage,
            "current_A": current,
            "output": output_state,
        }
