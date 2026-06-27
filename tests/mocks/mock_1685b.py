"""Simulated BK Precision 1685B serial interface for offline testing.

Implements the same proprietary protocol as the real instrument so that
Driver1685B can be tested without physical hardware.

Usage:
    mock = Mock1685B(v_max=60.0, i_max=5.0)
    mock.write("GMAX")
    assert mock.read() == "60.00"
    assert mock.read() == " 5.00"
    assert mock.read() == "OK"
"""

from __future__ import annotations


class Mock1685B:
    """In-memory simulation of the 1685B serial command interface.

    The real supply sends each line terminated by \\r. Here we model the
    response queue as a list of strings; callers drain it with read().
    """

    def __init__(self, v_max: float = 60.0, i_max: float = 5.0, dp: int = 2) -> None:
        self.v_max = v_max
        self.i_max = i_max
        self.dp = dp
        self._v_set: float = 0.0
        self._i_set: float = 0.0
        self._v_meas: float = 0.0
        self._i_meas: float = 0.0
        self._output_on: bool = False  # tracks real state (not inverted)
        self._ovp: float = v_max
        self._ocp: float = i_max
        self._rx: list[str] = []  # response queue

    # ------------------------------------------------------------------
    # PyVISA-compatible interface
    # ------------------------------------------------------------------

    def write(self, cmd: str) -> None:
        """Process one command line (without the \\r terminator)."""
        cmd = cmd.strip()
        parts = cmd.split()
        name = parts[0].upper()

        if name == "GMAX":
            self._push(f"{self.v_max:.{self.dp}f}")
            self._push(f"{self.i_max:.{self.dp}f}")
            self._push("OK")

        elif name == "GETD":
            mode = "1" if self._i_meas >= self._i_set and self._output_on else "0"
            self._push(f"{self._v_meas:.{self.dp}f}")
            self._push(f"{self._i_meas:.{self.dp}f}")
            self._push(mode)
            self._push("OK")

        elif name == "GETS":
            self._push(f"{self._v_set:.{self.dp}f}")
            self._push(f"{self._i_set:.{self.dp}f}")
            self._push("OK")

        elif name == "GOUT":
            self._push("1" if self._output_on else "0")
            self._push("OK")

        elif name == "GOVP":
            self._push(f"{self._ovp:.{self.dp}f}")
            self._push("OK")

        elif name == "GOCP":
            self._push(f"{self._ocp:.{self.dp}f}")
            self._push("OK")

        elif name == "VOLT" and len(parts) == 2:
            self._v_set = float(parts[1])
            if self._output_on:
                self._v_meas = self._v_set
            self._push("OK")

        elif name == "CURR" and len(parts) == 2:
            self._i_set = float(parts[1])
            self._push("OK")

        elif name == "SOUT" and len(parts) == 2:
            # 1685B SOUT is INVERTED: 0=ON, 1=OFF
            self._output_on = (parts[1] == "0")
            if self._output_on:
                self._v_meas = self._v_set
                self._i_meas = min(self._i_set * 0.5, self._i_set)  # simulated load
            else:
                self._v_meas = 0.0
                self._i_meas = 0.0
            self._push("OK")

        elif name == "SOVP" and len(parts) == 2:
            self._ovp = float(parts[1])
            self._push("OK")

        elif name == "SOCP" and len(parts) == 2:
            self._ocp = float(parts[1])
            self._push("OK")

        elif name == "RUNM":
            self._push("OK")  # preset load — simplified

        else:
            self._push("OK")  # unknown command: just ack

    def read(self) -> str:
        """Return the next queued response line."""
        if not self._rx:
            raise TimeoutError("No response queued (mock supply)")
        return self._rx.pop(0)

    def query(self, cmd: str) -> str:
        """Write a command and return the first response line (PyVISA compat)."""
        self.write(cmd)
        return self.read()

    def close(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Test helpers
    # ------------------------------------------------------------------

    def simulate_load(self, v_meas: float, i_meas: float) -> None:
        """Inject measured V/I values (simulates a connected load)."""
        self._v_meas = v_meas
        self._i_meas = i_meas

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _push(self, line: str) -> None:
        self._rx.append(line)
