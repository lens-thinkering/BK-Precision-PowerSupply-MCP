"""Integration tests for the MCP tool layer.

Tests verify the full call path: tool → session → safety → driver → mock.
"""

from __future__ import annotations

import pytest

from tests.mocks.mock_1685b import Mock1685B
from tests.mocks.mock_9103 import Mock9103
from tests.mocks.mock_scpi import MockSCPI


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patch_visa(monkeypatch, mock):
    import bk_precision_mcp.drivers.driver_1685b as d1
    import bk_precision_mcp.drivers.driver_9103 as d9
    import bk_precision_mcp.drivers.driver_scpi as ds
    for mod in (d1, d9, ds):
        monkeypatch.setattr(mod, "open_resource", lambda *a, **kw: mock)


def _connect(resource_string: str, model_id: str):
    """Connect a driver to a resource, storing the session."""
    from bk_precision_mcp.registry import get_model_profile
    from bk_precision_mcp import session as session_mod
    profile = get_model_profile(model_id)
    driver = session_mod.make_driver(profile["driver"])
    driver.connect(resource_string, profile)
    session_mod.set_session(resource_string, driver, profile)
    return driver, profile


def _disconnect(resource_string: str):
    from bk_precision_mcp import session as session_mod
    if resource_string in session_mod.list_sessions():
        driver, _ = session_mod.get_session(resource_string)
        driver.disconnect()
        session_mod.clear_session(resource_string)


# ---------------------------------------------------------------------------
# Tool registration smoke test
# ---------------------------------------------------------------------------

class TestToolRegistration:
    def test_all_tools_registered(self):
        from mcp.server.fastmcp import FastMCP
        from bk_precision_mcp.tools import connection, power_supply

        mcp = FastMCP("test")
        connection.register(mcp)
        power_supply.register(mcp)

        tool_names = {t.name for t in mcp._tool_manager.list_tools()}
        expected = {
            "bk_get_supported_models",
            "bk_list_instruments",
            "bk_connect",
            "bk_disconnect",
            "bk_set_voltage",
            "bk_set_current",
            "bk_set_ovp",
            "bk_set_ocp",
            "bk_output_on",
            "bk_output_off",
            "bk_measure_voltage",
            "bk_measure_current",
            "bk_measure_power",
            "bk_get_status",
        }
        assert expected.issubset(tool_names), (
            f"Missing tools: {expected - tool_names}"
        )


# ---------------------------------------------------------------------------
# bk_get_supported_models
# ---------------------------------------------------------------------------

class TestGetSupportedModels:
    def test_returns_known_models(self):
        from bk_precision_mcp.registry import list_models
        models = list_models()
        ids = [m["model_id"] for m in models]
        assert "1685B" in ids
        assert "9103" in ids
        assert "XLN6024" in ids
        assert "PVS10005" in ids

    def test_hv_models_flagged(self):
        from bk_precision_mcp.registry import list_models
        hv_ids = [m["model_id"] for m in list_models() if m["high_voltage"]]
        assert "PVS10005" in hv_ids
        assert "PVS60085" in hv_ids

    def test_proprietary_models_not_scpi(self):
        from bk_precision_mcp.registry import list_models
        prop_ids = [m["model_id"] for m in list_models() if not m["scpi"]]
        assert "1685B" in prop_ids
        assert "9103" in prop_ids


# ---------------------------------------------------------------------------
# Safety integration via tools
# ---------------------------------------------------------------------------

class TestSafetyViaTools:
    RES = "ASRL5::INSTR"

    def setup_method(self):
        _disconnect(self.RES)

    def teardown_method(self):
        _disconnect(self.RES)

    def test_set_voltage_above_v_max_rejected(self, monkeypatch):
        mock = Mock1685B()
        _patch_visa(monkeypatch, mock)
        _connect(self.RES, "1685B")

        from bk_precision_mcp import safety, session as sess
        _, profile = sess.get_session(self.RES)
        with pytest.raises(ValueError, match="rated maximum"):
            safety.validate_voltage(profile, 999.0, confirm=True)

    def test_set_voltage_at_50v_without_confirm_rejected(self, monkeypatch):
        mock = Mock1685B()
        _patch_visa(monkeypatch, mock)
        _connect(self.RES, "1685B")

        from bk_precision_mcp import safety, session as sess
        _, profile = sess.get_session(self.RES)
        with pytest.raises(ValueError, match="high-voltage threshold"):
            safety.validate_voltage(profile, 50.0, confirm=False)

    def test_set_voltage_at_50v_with_confirm_accepted(self, monkeypatch):
        mock = Mock1685B()
        _patch_visa(monkeypatch, mock)
        _connect(self.RES, "1685B")

        from bk_precision_mcp import safety, session as sess
        _, profile = sess.get_session(self.RES)
        safety.validate_voltage(profile, 50.0, confirm=True)  # no exception

    def test_set_voltage_below_50v_no_confirm_accepted(self, monkeypatch):
        mock = Mock1685B()
        _patch_visa(monkeypatch, mock)
        _connect(self.RES, "1685B")

        from bk_precision_mcp import safety, session as sess
        _, profile = sess.get_session(self.RES)
        safety.validate_voltage(profile, 12.0, confirm=False)  # no exception

    def test_hv_output_on_without_confirm_rejected(self, monkeypatch):
        mock = MockSCPI(model_id="PVS10005", v_max=1000.0, i_max=5.0)
        _patch_visa(monkeypatch, mock)
        _disconnect(self.RES)
        _connect(self.RES, "PVS10005")

        from bk_precision_mcp import safety, session as sess
        _, profile = sess.get_session(self.RES)
        with pytest.raises(ValueError, match="HIGH VOLTAGE"):
            safety.check_hv_output_confirm(profile, confirm=False)

    def test_set_current_above_i_max_rejected(self, monkeypatch):
        mock = Mock1685B()
        _patch_visa(monkeypatch, mock)
        _connect(self.RES, "1685B")

        from bk_precision_mcp import safety, session as sess
        _, profile = sess.get_session(self.RES)
        with pytest.raises(ValueError, match="rated maximum"):
            safety.validate_current(profile, 100.0)


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

class TestSession:
    RES = "ASRL6::INSTR"

    def setup_method(self):
        _disconnect(self.RES)

    def teardown_method(self):
        _disconnect(self.RES)

    def test_get_session_without_connect_raises(self):
        from bk_precision_mcp import session as sess
        with pytest.raises(RuntimeError, match="No active connection"):
            sess.get_session(self.RES)

    def test_session_stored_after_connect(self, monkeypatch):
        mock = Mock1685B()
        _patch_visa(monkeypatch, mock)
        _connect(self.RES, "1685B")

        from bk_precision_mcp import session as sess
        _, profile = sess.get_session(self.RES)
        assert profile["model_id"] == "1685B"

    def test_session_cleared_after_disconnect(self, monkeypatch):
        mock = Mock1685B()
        _patch_visa(monkeypatch, mock)
        _connect(self.RES, "1685B")
        _disconnect(self.RES)

        from bk_precision_mcp import session as sess
        with pytest.raises(RuntimeError):
            sess.get_session(self.RES)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_known_model_returns_profile(self):
        from bk_precision_mcp.registry import get_model_profile
        profile = get_model_profile("9103")
        assert profile["model_id"] == "9103"
        assert profile["v_max"] == 42.0
        assert profile["scpi"] is False

    def test_unknown_model_raises_with_hint(self):
        from bk_precision_mcp.registry import get_model_profile
        with pytest.raises(KeyError, match="Supported models"):
            get_model_profile("NOSUCHMODEL")

    def test_find_model_by_idn_scpi(self):
        from bk_precision_mcp.registry import find_model_by_idn
        result = find_model_by_idn("B&K Precision,XLN6024,SN12345,1.00")
        assert result == "XLN6024"

    def test_find_model_by_idn_unknown_returns_none(self):
        from bk_precision_mcp.registry import find_model_by_idn
        result = find_model_by_idn("Agilent Technologies,E3631A,0,1.0")
        assert result is None
