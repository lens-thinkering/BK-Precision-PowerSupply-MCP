# BK Precision PowerSupply MCP

MCP server that lets AI assistants control BK Precision programmable DC power supplies via USB, RS-232, or LAN. Runs locally — the host must be physically connected to the supply.

Supports both proprietary-protocol models (168x, 9103 series) and SCPI IEEE-488.2 models (9200B, 9115, XLN, PVS, etc.).

## Project Structure

```
BK-Precision-PowerSupply-MCP/
├── pyproject.toml
├── CLAUDE.md
├── src/bk_precision_mcp/
│   ├── server.py                 # FastMCP entry point
│   ├── registry.py               # Loads registry.json; get_model_profile(), list_models()
│   ├── safety.py                 # validate_voltage/current, check_hv_output_confirm
│   ├── session.py                # Active connection store: resource_string → (driver, profile)
│   ├── models/
│   │   └── registry.json         # Per-model capability DB (22 models, 8 families)
│   ├── transport/
│   │   └── visa.py               # PyVISA singleton ResourceManager + open_resource()
│   ├── drivers/
│   │   ├── base.py               # Abstract BKPowerSupplyDriver
│   │   ├── driver_1685b.py       # 1685B/1687B/1688B/1900B proprietary protocol
│   │   ├── driver_9103.py        # 9103/9104 proprietary protocol
│   │   └── driver_scpi.py        # SCPI IEEE-488.2 (9200B, 9115, XLN, PVS, etc.)
│   └── tools/
│       ├── connection.py         # bk_connect, bk_disconnect, bk_list_instruments, bk_get_supported_models
│       └── power_supply.py       # bk_set_voltage/current, bk_output_on/off, bk_measure_*, bk_get_status, bk_set_ovp/ocp
└── tests/
    ├── mocks/
    │   ├── mock_1685b.py         # Simulated 1685B serial responder
    │   ├── mock_9103.py          # Simulated 9103 serial responder
    │   └── mock_scpi.py          # Simulated SCPI supply
    ├── test_drivers.py
    ├── test_safety.py
    └── test_tools.py
```

## Architecture

**Registry drives capability.** `registry.json` is the source of truth for every model: voltage/current limits, driver class, protocol type, interface options, `high_voltage` flag, `list_mode` support. Never hardcode model-specific limits in tool or driver logic.

**Driver pattern.** `BKPowerSupplyDriver` (abstract) defines the unified Python API. Three concrete drivers handle wire-level differences:
- `Driver1685B` — 168x/1900B proprietary: `SOUT 0=ON / 1=OFF` (inverted!), decimal string values
- `Driver9103` — 9103/9104 proprietary: `SOUT 1=ON / 0=OFF` (normal), 4-digit integer × 100 values
- `DriverSCPI` — Standard SCPI: `*IDN?`, `VOLT`, `CURR`, `OUTP ON/OFF`, `MEAS:VOLT?`, etc.

**Session management.** `session.py` holds the live `resource_string → (driver, profile)` mapping. All tool functions call `session.get_session()` first; there is no per-tool connection open/close.

**Transport.** PyVISA with the `@py` pure-Python backend (`pyvisa-py` + `pyserial`). Handles USB serial (ASRL), USBTMC (USB0::), and raw TCP socket (TCPIP...SOCKET) transparently. baud rate and line termination are configured per-driver in `open_resource()`.

## Safety Layer — Critical

`safety.py` is called before every set command. It is never bypassed.

- **Registry limit check:** reject setpoints above `v_max` / `i_max`. Descriptive error, never silent clamp.
- **50 V HV threshold:** `validate_voltage()` requires `confirm=True` for any voltage ≥ 50 V (IEC 60479 shock-hazard boundary). Applied in `bk_set_voltage`.
- **HV model output gate:** `check_hv_output_confirm()` requires `confirm=True` on `bk_output_on()` for models with `high_voltage=true` in the registry (PVS series, 9206B, XLN10014). Second gate independent of setpoint.
- **Output-off on disconnect:** `driver.disconnect()` always sends the output-off command before closing the transport.

## Supported Model Families

| Family | Models | Protocol | `high_voltage` |
|---|---|---|---|
| 168x | 1685B, 1687B, 1688B | Proprietary | false |
| 1900B | 1900B, 1901B, 1902B | Proprietary | false |
| 9103 | 9103, 9104 | Proprietary | false |
| 9200B | 9201B, 9202B, 9205B, 9206B | SCPI | 9206B only |
| 9115 | 9115, 9116, 9117 | SCPI | false |
| 9170B | 9170B, 9180B | SCPI | false |
| XLN | XLN3640, XLN6024, XLN8018, XLN10014 | SCPI | XLN10014 only |
| PVS | PVS10005, PVS60085, PVS60085MR | SCPI | true (all) |

## Protocol Notes

### 168x / 1900B (driver_1685b)
- 9600 8N1, CR terminator
- **SOUT 0 = ON, SOUT 1 = OFF** (inverted vs all other BK models)
- Values as decimal strings; `decimal_places` from registry (1685B=2dp, others=1dp)
- Identified via `GMAX` (no *IDN? support)
- `GOUT` returns output state (0=off, 1=on, not inverted)

### 9103 / 9104 (driver_9103)
- 9600 8N1, CR terminator
- **SOUT 0 = OFF, SOUT 1 = ON** (normal logic)
- Values as 4-digit integers × 100 (e.g. `1250` = 12.50 V)
- `SETD 3 VVVV AAAA` sets slot 3 (normal mode); `VOLT 3` / `CURR 3` activates it
- Identified via `GALL` (no *IDN? support)

### SCPI (driver_scpi)
- Standard IEEE-488.2: `*IDN?`, `VOLT`, `CURR`, `OUTP ON/OFF`, `MEAS:VOLT?`, `MEAS:CURR?`
- Multi-channel models: prefix with `INST:NSEL {channel}` (currently single-channel only in registry)
- OVP/OCP: `VOLT:PROT` / `CURR:PROT`
- CV/CC mode from `STAT:QUES:COND?` bit 0

## MCP Tools

Connection: `bk_get_supported_models`, `bk_list_instruments`, `bk_connect`, `bk_disconnect`
Control: `bk_set_voltage`, `bk_set_current`, `bk_set_ovp`, `bk_set_ocp`, `bk_output_on`, `bk_output_off`
Measurement: `bk_measure_voltage`, `bk_measure_current`, `bk_measure_power`, `bk_get_status`

## Running Tests

```bash
uv sync
uv run python -m pytest tests/ -v
```

All tests use mock responders — no hardware required.

## Phase Plan

- **Phase 1 (current):** Serial + LAN transports, single-channel tools, 168x/9103/9200B/9115/9170B/XLN/PVS registry entries, mock supplies, full test coverage.
- **Phase 2:** Multi-channel support (9129B, 9130B registry entries; conditional `channel` param).
- **Phase 3:** List mode sequencing (`run_list`, `abort_list`) for models with `list_mode: true`.
- **Phase 4:** Publish to PyPI.

## Out of Scope

- Non-power-supply instruments (DMM, oscilloscope, function gen)
- AC power sources, electronic loads
- Cloud or remote deployment — this MCP is local-only by design
