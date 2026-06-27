"""MCP tools for controlling BK Precision programmable DC power supplies.

All tools require an active connection established via bk_connect().
Safety validation (registry limits + 50 V HV threshold) is applied before
every set command — the instrument is never contacted if validation fails.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from bk_precision_mcp import safety, session


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    def bk_set_voltage(
        resource_string: str,
        volts: float,
        channel: int = 1,
        confirm: bool = False,
    ) -> dict:
        """Set the output voltage setpoint on a connected BK Precision power supply.

        Args:
            resource_string: VISA resource string of a connected instrument.
            volts: Target voltage in volts (must be <= model v_max).
            channel: Output channel (default 1; only relevant for multi-channel models).
            confirm: Must be True when volts >= 50 V (IEC 60479 shock-hazard
                     threshold). The tool returns an error without confirm=True
                     to ensure the operator acknowledges the risk.

        Returns a dict with the programmed value and units.
        """
        driver, profile = session.get_session(resource_string)
        safety.validate_voltage(profile, volts, confirm)
        driver.set_voltage(volts, channel)
        return {"set_voltage_V": volts, "channel": channel, "model": profile["model_id"]}

    @mcp.tool()
    def bk_set_current(
        resource_string: str,
        amps: float,
        channel: int = 1,
    ) -> dict:
        """Set the current limit on a connected BK Precision power supply.

        Args:
            resource_string: VISA resource string of a connected instrument.
            amps: Current limit in amperes (must be <= model i_max).
            channel: Output channel (default 1).

        Returns a dict with the programmed value and units.
        """
        driver, profile = session.get_session(resource_string)
        safety.validate_current(profile, amps)
        driver.set_current(amps, channel)
        return {"set_current_A": amps, "channel": channel, "model": profile["model_id"]}

    @mcp.tool()
    def bk_set_ovp(resource_string: str, volts: float) -> dict:
        """Set the over-voltage protection (OVP) threshold.

        Args:
            resource_string: VISA resource string of a connected instrument.
            volts: OVP trip voltage in volts.

        Returns a confirmation dict, or an error message if the model does
        not support OVP programming.
        """
        driver, profile = session.get_session(resource_string)
        safety.validate_voltage(profile, volts, confirm=True)  # OVP can exceed HV threshold
        try:
            driver.set_ovp(volts)
        except NotImplementedError as exc:
            return {"error": str(exc)}
        return {"set_ovp_V": volts, "model": profile["model_id"]}

    @mcp.tool()
    def bk_set_ocp(resource_string: str, amps: float) -> dict:
        """Set the over-current protection (OCP) threshold.

        Args:
            resource_string: VISA resource string of a connected instrument.
            amps: OCP trip current in amperes.

        Returns a confirmation dict, or an error message if the model does
        not support OCP programming.
        """
        driver, profile = session.get_session(resource_string)
        safety.validate_current(profile, amps)
        try:
            driver.set_ocp(amps)
        except NotImplementedError as exc:
            return {"error": str(exc)}
        return {"set_ocp_A": amps, "model": profile["model_id"]}

    @mcp.tool()
    def bk_output_on(
        resource_string: str,
        channel: int = 1,
        confirm: bool = False,
    ) -> dict:
        """Enable the output of a connected BK Precision power supply.

        For models with v_max >= 50 V (registry high_voltage=true), confirm=True
        is required regardless of the current voltage setpoint. This is an
        additional gate on top of the per-setpoint check in bk_set_voltage().

        Args:
            resource_string: VISA resource string of a connected instrument.
            channel: Output channel (default 1).
            confirm: Must be True for high_voltage=true models.

        Returns a confirmation dict.
        """
        driver, profile = session.get_session(resource_string)
        safety.check_hv_output_confirm(profile, confirm)
        driver.output_on(channel)
        return {"output": "on", "channel": channel, "model": profile["model_id"]}

    @mcp.tool()
    def bk_output_off(resource_string: str, channel: int = 1) -> dict:
        """Disable the output of a connected BK Precision power supply.

        Args:
            resource_string: VISA resource string of a connected instrument.
            channel: Output channel (default 1).

        Returns a confirmation dict.
        """
        driver, profile = session.get_session(resource_string)
        driver.output_off(channel)
        return {"output": "off", "channel": channel, "model": profile["model_id"]}

    @mcp.tool()
    def bk_measure_voltage(resource_string: str, channel: int = 1) -> dict:
        """Measure the actual output voltage of a connected power supply.

        Args:
            resource_string: VISA resource string of a connected instrument.
            channel: Output channel (default 1).

        Returns a dict with the measured voltage and units.
        """
        driver, profile = session.get_session(resource_string)
        voltage = driver.measure_voltage(channel)
        return {"measured_V": voltage, "channel": channel, "model": profile["model_id"]}

    @mcp.tool()
    def bk_measure_current(resource_string: str, channel: int = 1) -> dict:
        """Measure the actual output current of a connected power supply.

        Args:
            resource_string: VISA resource string of a connected instrument.
            channel: Output channel (default 1).

        Returns a dict with the measured current and units.
        """
        driver, profile = session.get_session(resource_string)
        current = driver.measure_current(channel)
        return {"measured_A": current, "channel": channel, "model": profile["model_id"]}

    @mcp.tool()
    def bk_measure_power(resource_string: str, channel: int = 1) -> dict:
        """Measure the output power (V × I) of a connected power supply.

        Args:
            resource_string: VISA resource string of a connected instrument.
            channel: Output channel (default 1).

        Returns a dict with measured voltage, current, computed power, and units.
        """
        driver, profile = session.get_session(resource_string)
        voltage = driver.measure_voltage(channel)
        current = driver.measure_current(channel)
        power = round(voltage * current, 4)
        return {
            "measured_V": voltage,
            "measured_A": current,
            "computed_W": power,
            "channel": channel,
            "model": profile["model_id"],
        }

    @mcp.tool()
    def bk_get_status(resource_string: str, channel: int = 1) -> dict:
        """Get the full output status of a connected power supply.

        Returns voltage, current, regulation mode (CV/CC), and output state.

        Args:
            resource_string: VISA resource string of a connected instrument.
            channel: Output channel (default 1).
        """
        driver, profile = session.get_session(resource_string)
        status = driver.get_status(channel)
        status["channel"] = channel
        status["model"] = profile["model_id"]
        return status
