"""Simulated SCPI power supply interface for offline testing.

Covers the command set used by DriverSCPI (9200B, 9115, XLN, PVS, etc.).
"""

from __future__ import annotations


class MockSCPI:
    """In-memory simulation of a SCPI IEEE-488.2 power supply."""

    def __init__(
        self,
        model_id: str = "XLN6024",
        v_max: float = 60.0,
        i_max: float = 24.0,
    ) -> None:
        self.model_id = model_id
        self.v_max = v_max
        self.i_max = i_max
        self._v_set: float = 0.0
        self._i_set: float = 0.0
        self._v_meas: float = 0.0
        self._i_meas: float = 0.0
        self._output_on: bool = False
        self._ovp: float = v_max
        self._ocp: float = i_max
        self._channel: int = 1

    # ------------------------------------------------------------------
    # PyVISA-compatible interface (query only — SCPI driver uses query())
    # ------------------------------------------------------------------

    def write(self, cmd: str) -> None:
        cmd = cmd.strip()
        upper = cmd.upper()

        if upper.startswith("INST:NSEL"):
            self._channel = int(cmd.split()[-1])

        elif upper.startswith("VOLT:PROT"):
            self._ovp = float(cmd.split()[-1])

        elif upper.startswith("CURR:PROT"):
            self._ocp = float(cmd.split()[-1])

        elif upper.startswith("VOLT"):
            self._v_set = float(cmd.split()[-1])
            if self._output_on:
                self._v_meas = self._v_set

        elif upper.startswith("CURR"):
            self._i_set = float(cmd.split()[-1])

        elif upper == "OUTP ON":
            self._output_on = True
            self._v_meas = self._v_set
            self._i_meas = self._i_set * 0.5  # simulated load

        elif upper == "OUTP OFF":
            self._output_on = False
            self._v_meas = 0.0
            self._i_meas = 0.0

        elif upper in ("*CLS", "*RST"):
            pass  # status-register commands — no state change in mock

    def read(self) -> str:
        raise NotImplementedError("Use query() for SCPI mock")

    def query(self, cmd: str) -> str:
        cmd = cmd.strip()
        upper = cmd.upper()

        if upper == "*IDN?":
            return f"B&K Precision,{self.model_id},SN000001,1.00"

        elif upper == "MEAS:VOLT?":
            return f"{self._v_meas:.4f}"

        elif upper == "MEAS:CURR?":
            return f"{self._i_meas:.4f}"

        elif upper == "OUTP?":
            return "1" if self._output_on else "0"

        elif upper == "STAT:QUES:COND?":
            # bit 0 = CC mode
            in_cc = self._output_on and self._i_meas >= self._i_set
            return "1" if in_cc else "0"

        elif upper == "VOLT?":
            return f"{self._v_set:.4f}"

        elif upper == "CURR?":
            return f"{self._i_set:.4f}"

        return ""

    def close(self) -> None:
        pass

    def simulate_load(self, v_meas: float, i_meas: float) -> None:
        self._v_meas = v_meas
        self._i_meas = i_meas

    # Properties to match PyVISA resource attributes
    @property
    def timeout(self) -> int:
        return 5000

    @timeout.setter
    def timeout(self, value: int) -> None:
        pass

    @property
    def write_termination(self) -> str:
        return "\n"

    @write_termination.setter
    def write_termination(self, value: str) -> None:
        pass

    @property
    def read_termination(self) -> str:
        return "\n"

    @read_termination.setter
    def read_termination(self, value: str) -> None:
        pass
