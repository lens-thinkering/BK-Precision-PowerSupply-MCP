"""BK Precision function generator SCPI commands."""

from __future__ import annotations

from typing import Literal

from bk_precision_mcp.instruments.base import BaseInstrument

Waveform = Literal["SIN", "SQU", "RAMP", "PULS", "NOIS", "DC"]


class FunctionGenerator(BaseInstrument):
    def set_waveform(self, shape: Waveform, channel: int = 1) -> None:
        self.write(f"SOURce{channel}:FUNCtion:SHAPe {shape}")

    def set_frequency(self, hz: float, channel: int = 1) -> None:
        self.write(f"SOURce{channel}:FREQuency {hz:.6g}")

    def set_amplitude(self, volts: float, channel: int = 1) -> None:
        self.write(f"SOURce{channel}:VOLTage:AMPLitude {volts:.6g}")

    def set_offset(self, volts: float, channel: int = 1) -> None:
        self.write(f"SOURce{channel}:VOLTage:OFFSet {volts:.6g}")

    def output_on(self, channel: int = 1) -> None:
        self.write(f"OUTPut{channel}:STATe ON")

    def output_off(self, channel: int = 1) -> None:
        self.write(f"OUTPut{channel}:STATe OFF")
