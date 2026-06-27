"""Simulated BK Precision 9103 serial interface for offline testing.

Implements the proprietary 9103/9104 protocol so Driver9103 can be tested
without physical hardware.

Values are transmitted as 4-digit integers × 100 (e.g. 1250 = 12.50 V).
SOUT logic is NORMAL: 0 = OFF, 1 = ON.
"""

from __future__ import annotations


class Mock9103:
    """In-memory simulation of the 9103 serial command interface."""

    def __init__(self, v_max: float = 42.0, i_max: float = 20.0) -> None:
        self.v_max = v_max
        self.i_max = i_max
        # 4 preset slots (index 0-3, slot 3 = normal mode)
        self._presets: list[tuple[float, float]] = [(0.0, 0.0)] * 4
        self._active_slot: int = 3
        self._v_meas: float = 0.0
        self._i_meas: float = 0.0
        self._output_on: bool = False
        self._ovp: float = v_max
        self._ocp: float = i_max
        self._rx: list[str] = []

    # ------------------------------------------------------------------
    # PyVISA-compatible interface
    # ------------------------------------------------------------------

    def write(self, cmd: str) -> None:
        cmd = cmd.strip()
        parts = cmd.split()
        name = parts[0].upper()

        if name == "GALL":
            # Return a minimal multi-line dump; driver just checks for response
            self._push(f"{_enc(self._presets[3][0]):04d}")
            self._push(f"{_enc(self._presets[3][1]):04d}")
            self._push(f"{int(self._output_on)}")
            self._push("OK")

        elif name == "GETD":
            mode = "1" if (self._output_on and self._i_meas >= self._presets[3][1]) else "0"
            self._push(f"{_enc(self._v_meas):04d}")
            self._push(f"{_enc(self._i_meas):04d}")
            self._push(mode)
            self._push("OK")

        elif name == "GOUT":
            self._push("1" if self._output_on else "0")
            self._push("OK")

        elif name == "GOVP":
            self._push(f"{_enc(self._ovp):04d}")
            self._push("OK")

        elif name == "GOCP":
            self._push(f"{_enc(self._ocp):04d}")
            self._push("OK")

        elif name == "SETD" and len(parts) == 4:
            slot = int(parts[1])
            v = _dec(parts[2])
            i = _dec(parts[3])
            self._presets[slot] = (v, i)
            self._push("OK")

        elif name == "VOLT" and len(parts) == 2:
            # Selects which slot's voltage is active
            self._active_slot = int(parts[1])
            if self._output_on:
                self._v_meas = self._presets[self._active_slot][0]
            self._push("OK")

        elif name == "CURR" and len(parts) == 2:
            self._active_slot = int(parts[1])
            self._push("OK")

        elif name == "SOUT" and len(parts) == 2:
            # 9103 SOUT is NORMAL: 0=OFF, 1=ON
            self._output_on = (parts[1] == "1")
            if self._output_on:
                self._v_meas = self._presets[self._active_slot][0]
                self._i_meas = self._presets[self._active_slot][1] * 0.5  # simulated load
            else:
                self._v_meas = 0.0
                self._i_meas = 0.0
            self._push("OK")

        elif name == "SOVP" and len(parts) == 2:
            self._ovp = _dec(parts[1])
            self._push("OK")

        elif name == "SOCP" and len(parts) == 2:
            self._ocp = _dec(parts[1])
            self._push("OK")

        elif name == "STOP":
            self._push("OK")

        else:
            self._push("OK")

    def read(self) -> str:
        if not self._rx:
            raise TimeoutError("No response queued (mock 9103)")
        return self._rx.pop(0)

    def query(self, cmd: str) -> str:
        self.write(cmd)
        return self.read()

    def close(self) -> None:
        pass

    def simulate_load(self, v_meas: float, i_meas: float) -> None:
        self._v_meas = v_meas
        self._i_meas = i_meas

    def _push(self, line: str) -> None:
        self._rx.append(line)


def _enc(value: float) -> int:
    return round(value * 100)


def _dec(raw: str) -> float:
    return int(raw.strip()) / 100.0
