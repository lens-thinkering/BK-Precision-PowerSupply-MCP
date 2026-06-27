"""Unit tests for the safety validation layer."""

from __future__ import annotations

import pytest

from bk_precision_mcp.safety import (
    HV_THRESHOLD,
    check_hv_output_confirm,
    validate_current,
    validate_voltage,
)


def _profile(model_id="1685B", v_max=60.0, i_max=5.0, high_voltage=False):
    return {
        "model_id": model_id,
        "v_max": v_max,
        "i_max": i_max,
        "high_voltage": high_voltage,
    }


# ---------------------------------------------------------------------------
# validate_voltage
# ---------------------------------------------------------------------------

class TestValidateVoltage:
    def test_valid_low_voltage_passes(self):
        validate_voltage(_profile(), volts=12.0)  # no exception

    def test_exactly_at_v_max_passes(self):
        validate_voltage(_profile(v_max=60.0), volts=60.0, confirm=True)

    def test_above_v_max_raises(self):
        with pytest.raises(ValueError, match="exceeds the 1685B rated maximum"):
            validate_voltage(_profile(v_max=60.0), volts=61.0)

    def test_negative_voltage_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            validate_voltage(_profile(), volts=-1.0)

    def test_hv_threshold_no_confirm_raises(self):
        with pytest.raises(ValueError, match=f"{HV_THRESHOLD}"):
            validate_voltage(_profile(v_max=60.0), volts=50.0, confirm=False)

    def test_exactly_at_hv_threshold_no_confirm_raises(self):
        with pytest.raises(ValueError, match="high-voltage threshold"):
            validate_voltage(_profile(v_max=60.0), volts=HV_THRESHOLD, confirm=False)

    def test_hv_threshold_with_confirm_passes(self):
        validate_voltage(_profile(v_max=60.0), volts=50.0, confirm=True)

    def test_above_hv_threshold_with_confirm_passes(self):
        validate_voltage(_profile(v_max=60.0), volts=59.9, confirm=True)

    def test_just_below_hv_threshold_no_confirm_passes(self):
        validate_voltage(_profile(v_max=60.0), volts=49.99, confirm=False)

    def test_hv_model_above_limit_still_raises(self):
        """confirm=True for HV threshold doesn't bypass the v_max check."""
        with pytest.raises(ValueError, match="rated maximum"):
            validate_voltage(_profile(v_max=60.0), volts=70.0, confirm=True)

    def test_error_message_includes_model_id(self):
        with pytest.raises(ValueError, match="9103"):
            validate_voltage(_profile(model_id="9103", v_max=42.0), volts=45.0)

    def test_hv_threshold_value_is_50v(self):
        assert HV_THRESHOLD == 50.0


# ---------------------------------------------------------------------------
# validate_current
# ---------------------------------------------------------------------------

class TestValidateCurrent:
    def test_valid_current_passes(self):
        validate_current(_profile(i_max=5.0), amps=3.0)

    def test_exactly_at_i_max_passes(self):
        validate_current(_profile(i_max=5.0), amps=5.0)

    def test_above_i_max_raises(self):
        with pytest.raises(ValueError, match="exceeds the 1685B rated maximum"):
            validate_current(_profile(i_max=5.0), amps=5.1)

    def test_negative_current_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            validate_current(_profile(), amps=-0.1)

    def test_zero_current_passes(self):
        validate_current(_profile(i_max=5.0), amps=0.0)


# ---------------------------------------------------------------------------
# check_hv_output_confirm
# ---------------------------------------------------------------------------

class TestCheckHVOutputConfirm:
    def test_non_hv_model_no_confirm_passes(self):
        check_hv_output_confirm(_profile(high_voltage=False), confirm=False)

    def test_non_hv_model_with_confirm_passes(self):
        check_hv_output_confirm(_profile(high_voltage=False), confirm=True)

    def test_hv_model_no_confirm_raises(self):
        with pytest.raises(ValueError, match="HIGH VOLTAGE"):
            check_hv_output_confirm(
                _profile(model_id="PVS10005", v_max=1000.0, high_voltage=True),
                confirm=False,
            )

    def test_hv_model_with_confirm_passes(self):
        check_hv_output_confirm(
            _profile(model_id="PVS10005", v_max=1000.0, high_voltage=True),
            confirm=True,
        )

    def test_error_includes_model_id(self):
        with pytest.raises(ValueError, match="PVS10005"):
            check_hv_output_confirm(
                _profile(model_id="PVS10005", v_max=1000.0, high_voltage=True),
                confirm=False,
            )
