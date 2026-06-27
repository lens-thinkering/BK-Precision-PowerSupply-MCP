"""Abstract base driver for BK Precision programmable DC power supplies."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BKPowerSupplyDriver(ABC):
    """Unified interface that all protocol-specific drivers must implement.

    Concrete subclasses handle the wire-level differences between the
    proprietary 168x/9103 serial protocols and the SCPI IEEE-488.2 protocol
    used by the 9200B, 9115, XLN, PVS and similar families.
    """

    @abstractmethod
    def connect(self, resource_string: str, profile: dict) -> None:
        """Open the transport and verify the instrument is responding.

        Args:
            resource_string: PyVISA resource address (e.g. 'ASRL3::INSTR').
            profile: Model capability dict from the registry.
        """

    @abstractmethod
    def disconnect(self) -> None:
        """Turn off the output and close the transport."""

    @abstractmethod
    def set_voltage(self, volts: float, channel: int = 1) -> None:
        """Program the output voltage setpoint."""

    @abstractmethod
    def set_current(self, amps: float, channel: int = 1) -> None:
        """Program the current limit."""

    @abstractmethod
    def output_on(self, channel: int = 1) -> None:
        """Enable the output."""

    @abstractmethod
    def output_off(self, channel: int = 1) -> None:
        """Disable the output."""

    @abstractmethod
    def measure_voltage(self, channel: int = 1) -> float:
        """Return the measured output voltage in volts."""

    @abstractmethod
    def measure_current(self, channel: int = 1) -> float:
        """Return the measured output current in amperes."""

    @abstractmethod
    def get_status(self, channel: int = 1) -> dict:
        """Return a status dict with keys: voltage, current, mode, output.

        'mode' is 'CV' or 'CC'.
        'output' is True if the output is enabled.
        """

    def set_ovp(self, volts: float) -> None:
        """Set the over-voltage protection threshold (if supported)."""
        raise NotImplementedError(
            f"{type(self).__name__} does not support set_ovp()"
        )

    def set_ocp(self, amps: float) -> None:
        """Set the over-current protection threshold (if supported)."""
        raise NotImplementedError(
            f"{type(self).__name__} does not support set_ocp()"
        )
