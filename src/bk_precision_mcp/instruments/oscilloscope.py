"""BK Precision oscilloscope SCPI commands."""

from __future__ import annotations

from bk_precision_mcp.instruments.base import BaseInstrument


class Oscilloscope(BaseInstrument):
    def autoscale(self) -> None:
        self.write("AUToscale")

    def run(self) -> None:
        self.write("RUN")

    def stop(self) -> None:
        self.write("STOP")

    def measure_frequency(self, channel: int = 1) -> float:
        self.write(f"MEASure:SOURce CHANnel{channel}")
        return float(self.query("MEASure:FREQuency?"))

    def measure_amplitude(self, channel: int = 1) -> float:
        self.write(f"MEASure:SOURce CHANnel{channel}")
        return float(self.query("MEASure:AMPLitude?"))

    def set_timebase(self, seconds_per_div: float) -> None:
        self.write(f"TIMebase:SCALe {seconds_per_div:.6g}")

    def set_voltage_scale(self, volts_per_div: float, channel: int = 1) -> None:
        self.write(f"CHANnel{channel}:SCALe {volts_per_div:.6g}")
