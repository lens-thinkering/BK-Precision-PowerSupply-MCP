"""Unit tests for all three protocol drivers against their mock instruments."""

from __future__ import annotations

import pytest

from tests.mocks.mock_1685b import Mock1685B
from tests.mocks.mock_9103 import Mock9103
from tests.mocks.mock_scpi import MockSCPI


# ---------------------------------------------------------------------------
# Helpers — patch open_resource to return a mock instead of opening real VISA
# ---------------------------------------------------------------------------

def _patch_1685b(monkeypatch, mock: Mock1685B):
    import bk_precision_mcp.drivers.driver_1685b as drv
    monkeypatch.setattr(drv, "open_resource", lambda *a, **kw: mock)


def _patch_9103(monkeypatch, mock: Mock9103):
    import bk_precision_mcp.drivers.driver_9103 as drv
    monkeypatch.setattr(drv, "open_resource", lambda *a, **kw: mock)


def _patch_scpi(monkeypatch, mock: MockSCPI):
    import bk_precision_mcp.drivers.driver_scpi as drv
    monkeypatch.setattr(drv, "open_resource", lambda *a, **kw: mock)


def _profile_1685b():
    from bk_precision_mcp.registry import get_model_profile
    return get_model_profile("1685B")


def _profile_9103():
    from bk_precision_mcp.registry import get_model_profile
    return get_model_profile("9103")


def _profile_scpi():
    from bk_precision_mcp.registry import get_model_profile
    return get_model_profile("XLN6024")


# ===========================================================================
# Driver1685B tests
# ===========================================================================

class TestDriver1685B:
    def _make(self, monkeypatch, **kwargs):
        from bk_precision_mcp.drivers.driver_1685b import Driver1685B
        mock = Mock1685B(**kwargs)
        _patch_1685b(monkeypatch, mock)
        driver = Driver1685B()
        driver.connect("ASRL3::INSTR", _profile_1685b())
        return driver, mock

    def test_connect_sends_gmax(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        # If connect() succeeded, GMAX was sent and parsed without error
        assert driver._resource is not None

    def test_set_voltage(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        driver.set_voltage(12.50)
        # Last written command should include "VOLT 12.50"
        # We verify via the mock's internal state
        assert mock._v_set == pytest.approx(12.50)

    def test_set_current(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        driver.set_current(2.00)
        assert mock._i_set == pytest.approx(2.00)

    def test_output_on_inverted_logic(self, monkeypatch):
        """SOUT 0 must turn the output ON for the 1685B."""
        driver, mock = self._make(monkeypatch)
        driver.output_on()
        assert mock._output_on is True

    def test_output_off_inverted_logic(self, monkeypatch):
        """SOUT 1 must turn the output OFF for the 1685B."""
        driver, mock = self._make(monkeypatch)
        driver.output_on()
        driver.output_off()
        assert mock._output_on is False

    def test_measure_voltage(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        mock.simulate_load(11.98, 1.47)
        v = driver.measure_voltage()
        assert v == pytest.approx(11.98)

    def test_measure_current(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        mock.simulate_load(11.98, 1.47)
        i = driver.measure_current()
        assert i == pytest.approx(1.47)

    def test_get_status(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        mock.simulate_load(12.01, 0.55)
        status = driver.get_status()
        assert status["voltage"] == pytest.approx(12.01)
        assert status["current"] == pytest.approx(0.55)
        assert status["mode"] in ("CV", "CC")
        assert "output" in status

    def test_set_ovp(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        driver.set_ovp(15.00)
        assert mock._ovp == pytest.approx(15.00)

    def test_set_ocp(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        driver.set_ocp(3.00)
        assert mock._ocp == pytest.approx(3.00)

    def test_disconnect_turns_off_output(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        driver.output_on()
        assert mock._output_on is True
        driver.disconnect()
        assert mock._output_on is False
        assert driver._resource is None


# ===========================================================================
# Driver9103 tests
# ===========================================================================

class TestDriver9103:
    def _make(self, monkeypatch):
        from bk_precision_mcp.drivers.driver_9103 import Driver9103
        mock = Mock9103()
        _patch_9103(monkeypatch, mock)
        driver = Driver9103()
        driver.connect("ASRL4::INSTR", _profile_9103())
        return driver, mock

    def test_connect_sends_gall(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        assert driver._resource is not None

    def test_set_voltage_encodes_integer(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        driver.set_voltage(12.50)
        # Slot 3 should now have 12.50 V
        assert mock._presets[3][0] == pytest.approx(12.50)

    def test_set_current_encodes_integer(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        driver.set_current(5.00)
        assert mock._presets[3][1] == pytest.approx(5.00)

    def test_output_on_normal_logic(self, monkeypatch):
        """SOUT 1 must turn the output ON for the 9103."""
        driver, mock = self._make(monkeypatch)
        driver.output_on()
        assert mock._output_on is True

    def test_output_off_normal_logic(self, monkeypatch):
        """SOUT 0 must turn the output OFF for the 9103."""
        driver, mock = self._make(monkeypatch)
        driver.output_on()
        driver.output_off()
        assert mock._output_on is False

    def test_measure_voltage_decodes_integer(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        mock.simulate_load(12.48, 4.99)
        v = driver.measure_voltage()
        assert v == pytest.approx(12.48)

    def test_measure_current_decodes_integer(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        mock.simulate_load(12.48, 4.99)
        i = driver.measure_current()
        assert i == pytest.approx(4.99)

    def test_get_status(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        mock.simulate_load(5.00, 2.00)
        status = driver.get_status()
        assert status["voltage"] == pytest.approx(5.00)
        assert status["current"] == pytest.approx(2.00)

    def test_set_ovp(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        driver.set_ovp(20.00)
        assert mock._ovp == pytest.approx(20.00)

    def test_disconnect_turns_off_output(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        driver.output_on()
        assert mock._output_on is True
        driver.disconnect()
        assert mock._output_on is False
        assert driver._resource is None


# ===========================================================================
# DriverSCPI tests
# ===========================================================================

class TestDriverSCPI:
    def _make(self, monkeypatch, model_id="XLN6024"):
        from bk_precision_mcp.drivers.driver_scpi import DriverSCPI
        mock = MockSCPI(model_id=model_id)
        _patch_scpi(monkeypatch, mock)
        driver = DriverSCPI()
        driver.connect("USB0::INSTR", _profile_scpi())
        return driver, mock

    def test_connect_checks_idn(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        assert driver._resource is not None

    def test_connect_rejects_non_bk_idn(self, monkeypatch):
        from bk_precision_mcp.drivers.driver_scpi import DriverSCPI
        import bk_precision_mcp.drivers.driver_scpi as drv

        class NonBKMock(MockSCPI):
            def query(self, cmd: str) -> str:
                if cmd.strip().upper() == "*IDN?":
                    return "Keysight Technologies,E3631A,MY12345,1.0-1.0"
                return super().query(cmd)

        mock = NonBKMock()
        monkeypatch.setattr(drv, "open_resource", lambda *a, **kw: mock)
        driver = DriverSCPI()
        with pytest.raises(ConnectionError, match="not appear to be a BK Precision"):
            driver.connect("USB0::INSTR", _profile_scpi())

    def test_set_voltage(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        driver.set_voltage(24.0)
        assert mock._v_set == pytest.approx(24.0)

    def test_set_current(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        driver.set_current(3.0)
        assert mock._i_set == pytest.approx(3.0)

    def test_output_on_off(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        driver.output_on()
        assert mock._output_on is True
        driver.output_off()
        assert mock._output_on is False

    def test_measure_voltage(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        mock.simulate_load(23.97, 2.98)
        assert driver.measure_voltage() == pytest.approx(23.97)

    def test_measure_current(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        mock.simulate_load(23.97, 2.98)
        assert driver.measure_current() == pytest.approx(2.98)

    def test_set_ovp(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        driver.set_ovp(30.0)
        assert mock._ovp == pytest.approx(30.0)

    def test_set_ocp(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        driver.set_ocp(5.0)
        assert mock._ocp == pytest.approx(5.0)

    def test_get_status(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        mock.simulate_load(12.0, 1.0)
        status = driver.get_status()
        assert status["voltage"] == pytest.approx(12.0)
        assert status["current"] == pytest.approx(1.0)
        assert status["mode"] in ("CV", "CC")
        assert isinstance(status["output"], bool)

    def test_disconnect_sends_outp_off(self, monkeypatch):
        driver, mock = self._make(monkeypatch)
        driver.output_on()
        assert mock._output_on is True
        driver.disconnect()
        assert mock._output_on is False
        assert driver._resource is None
