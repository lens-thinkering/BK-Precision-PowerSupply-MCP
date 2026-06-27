"""Safety validation layer for BK Precision power supply setpoints.

All set_voltage, set_current, and output_on operations must pass through
these checks before any command is sent to the instrument. This layer is
never bypassed, regardless of protocol or model.
"""

from __future__ import annotations

# IEC 60479 / OSHA "hazardous voltage" threshold.
# Any setpoint at or above this value requires explicit confirmation.
HV_THRESHOLD = 50.0  # volts


def validate_voltage(profile: dict, volts: float, confirm: bool = False) -> None:
    """Validate a voltage setpoint against model limits and the HV threshold.

    Args:
        profile: Model capability dict from the registry (must include
                 'model_id' and 'v_max').
        volts: Requested voltage in volts.
        confirm: Must be True when volts >= HV_THRESHOLD.

    Raises:
        ValueError: If the setpoint exceeds the model's rated maximum,
                    or if volts >= HV_THRESHOLD and confirm is False.
    """
    model_id = profile.get("model_id", "unknown")
    v_max = profile["v_max"]

    if volts < 0:
        raise ValueError(f"Voltage must be non-negative, got {volts} V.")

    if volts > v_max:
        raise ValueError(
            f"{volts} V exceeds the {model_id} rated maximum of {v_max} V. "
            "Check the registry for this model's limits."
        )

    if volts >= HV_THRESHOLD and not confirm:
        raise ValueError(
            f"{volts} V meets or exceeds the {HV_THRESHOLD} V high-voltage "
            "threshold (IEC 60479 shock-hazard boundary). "
            "Pass confirm=True to bk_set_voltage() to acknowledge the risk "
            "and proceed."
        )


def validate_current(profile: dict, amps: float) -> None:
    """Validate a current setpoint against model limits.

    Args:
        profile: Model capability dict from the registry.
        amps: Requested current in amperes.

    Raises:
        ValueError: If the setpoint exceeds the model's rated maximum.
    """
    model_id = profile.get("model_id", "unknown")
    i_max = profile["i_max"]

    if amps < 0:
        raise ValueError(f"Current must be non-negative, got {amps} A.")

    if amps > i_max:
        raise ValueError(
            f"{amps} A exceeds the {model_id} rated maximum of {i_max} A. "
            "Check the registry for this model's limits."
        )


def check_hv_output_confirm(profile: dict, confirm: bool) -> None:
    """Require explicit confirmation before enabling output on HV-flagged models.

    Models marked high_voltage=true in the registry (e.g. PVS, XLN10014,
    9206B) present a second gate at output-enable time, independent of the
    voltage setpoint gate in validate_voltage().

    Args:
        profile: Model capability dict from the registry.
        confirm: Must be True to proceed.

    Raises:
        ValueError: If high_voltage=true and confirm is False.
    """
    if profile.get("high_voltage") and not confirm:
        model_id = profile.get("model_id", "unknown")
        v_max = profile.get("v_max", "?")
        raise ValueError(
            f"{model_id} is rated for up to {v_max} V — a HIGH VOLTAGE supply. "
            f"Pass confirm=True to bk_output_on() to acknowledge the shock "
            "hazard and enable the output."
        )
