# B&K Precision MCP — Project Plan

## Overview

A Model Context Protocol (MCP) server that enables AI assistants (Claude Code, Cursor, Windsurf, etc.) to control B&K Precision programmable DC power supplies via SCPI commands. Runs locally on the machine physically connected to the supply over USB, RS232, or LAN. No cloud infrastructure required beyond normal Claude inference.

**Scope:** SCPI-capable B&K supplies only. Proprietary-protocol models (older 168x series) are explicitly out of scope.

---

## Supported Model Families

| Family | Example Models | Interfaces | Notes |
|---|---|---|---|
| PVS Series | PVS10005, PVS60085, PVS60085MR | USB vCOM, RS232, GPIB, LAN | Full IEEE-488.2; high-voltage flag required |
| 9115/9115B Series | 9115, 9116, 9117 | USBTMC, RS232, RS485, LAN | Multi-range; -AT variant adds automotive waveforms |
| 9200/9200B Series | 9201B, 9202B, 9205B, 9206B | USBTMC, RS232, GPIB | Multi-range, half-rack form factor |
| 9129B Series | 9129B | USB vCOM, RS232 | Triple-output, multi-channel |
| 9130B Series | 9130B | USB vCOM, RS232, GPIB | Triple-output, multi-channel |
| 1696B/1697B/1698B | 1696B, 1697B, 1698B | USB vCOM | Basic SCPI subset only — flagged in registry |
| XLN Series | XLN6024, XLN8018 | USB, LAN, RS232 | High-power ATE rack units |
| HPS/MPS Series | HPS, MPS variants | GPIB, LAN, USB, RS232 | High/modular power, up to 20 kW |

Models flagged `scpi_subset: true` (1696B family) will gracefully skip unsupported tools rather than error.

---

## Project Structure

```
bk-precision-mcp/
├── server.py                     # MCP entry point — registers tools, starts server
├── pyproject.toml                # Dependencies and build config
├── README.md                     # Setup, config, and usage guide
│
├── bk_mcp/
│   ├── __init__.py
│   ├── transport/
│   │   ├── base.py               # Abstract transport: write(cmd), query(cmd)
│   │   ├── serial_transport.py   # USB virtual COM + RS232 via pyserial
│   │   ├── usbtmc_transport.py   # USBTMC via pyvisa (optional dep)
│   │   └── lan_transport.py      # Raw TCP socket to port 5025
│   │
│   ├── models/
│   │   └── registry.json         # Per-model capability database
│   │
│   ├── scpi/
│   │   ├── core.py               # IEEE-488.2 common commands (*IDN?, *RST, *CLS, etc.)
│   │   ├── source.py             # SOURce subsystem (voltage/current setpoints)
│   │   ├── measure.py            # MEASure subsystem (actual V/I/P readings)
│   │   ├── output.py             # OUTPut subsystem (on/off, OVP, OCP)
│   │   ├── system.py             # SYSTem subsystem (errors, comms, local/remote)
│   │   ├── trigger.py            # TRIGger subsystem (list mode execution)
│   │   └── multi_channel.py      # INSTrument subsystem for multi-output models
│   │
│   ├── safety.py                 # Setpoint clamping, HV confirmation gate, output-off guard
│   └── tools.py                  # MCP tool definitions — what the AI sees
│
└── tests/
    ├── mock_supply.py            # Simulated SCPI responder for offline development
    └── test_tools.py             # Tool-level integration tests against mock
```

---

## Transport Layer

`base.py` defines a two-method abstract interface:

```python
class Transport(ABC):
    def write(self, cmd: str) -> None: ...
    def query(self, cmd: str) -> str: ...
```

All three concrete transports implement this interface. The SCPI layer never interacts with hardware directly — it only calls `write()` and `query()`. This makes the transport swappable at connect time and mockable in tests.

**Auto-detection on `connect()`:**
1. Open the specified port/address
2. Send `*IDN?`
3. Parse the response to extract model number
4. Look up the model in `registry.json`
5. Load capability profile (max V/I, channel count, supported subsystems)
6. Raise a descriptive error if model is not in registry or is a non-SCPI proprietary model

---

## Model Registry (`registry.json`)

Each entry drives runtime behavior — tool availability, safety limits, and interface options:

```json
{
  "PVS10005": {
    "family": "PVS",
    "channels": 1,
    "v_max": 1000,
    "i_max": 5,
    "p_max": 5000,
    "interfaces": ["usb_vcom", "rs232", "gpib", "lan"],
    "scpi_subset": false,
    "supports_list_mode": true,
    "supports_remote_sense": true,
    "high_voltage": true
  },
  "9205B": {
    "family": "9200B",
    "channels": 1,
    "v_max": 60,
    "i_max": 25,
    "p_max": 600,
    "interfaces": ["usbtmc", "rs232", "gpib"],
    "scpi_subset": false,
    "supports_list_mode": true,
    "supports_remote_sense": true,
    "high_voltage": false
  },
  "9129B": {
    "family": "9129B",
    "channels": 3,
    "v_max": 30,
    "i_max": 3,
    "p_max": 90,
    "interfaces": ["usb_vcom", "rs232"],
    "scpi_subset": false,
    "supports_list_mode": true,
    "supports_remote_sense": false,
    "high_voltage": false
  },
  "1697B": {
    "family": "1696B",
    "channels": 1,
    "v_max": 40,
    "i_max": 5,
    "p_max": 200,
    "interfaces": ["usb_vcom"],
    "scpi_subset": true,
    "supports_list_mode": true,
    "supports_remote_sense": false,
    "high_voltage": false
  }
}
```

---

## MCP Tools

Tools are grouped by function. Multi-channel tools expose a `channel` parameter only when the connected model has `channels > 1` in the registry.

### Connection
| Tool | Description |
|---|---|
| `connect(port_or_ip, model?)` | Opens transport, sends `*IDN?`, loads model profile |
| `disconnect()` | Turns output off, then closes transport |
| `get_identity()` | Returns parsed IDN string (make, model, serial, firmware) |

### Configuration
| Tool | Description |
|---|---|
| `set_voltage(volts, channel?)` | Sets voltage setpoint via `SOURce:VOLTage` |
| `set_current(amps, channel?)` | Sets current limit via `SOURce:CURRent` |
| `set_ovp(volts, channel?)` | Sets overvoltage protection threshold |
| `set_ocp(amps, channel?)` | Sets overcurrent protection threshold |
| `set_output(state: on\|off, channel?, confirm?)` | Enables/disables output; `confirm=True` required for high-voltage models |

### Measurement
| Tool | Description |
|---|---|
| `measure_voltage(channel?)` | Actual output voltage via `MEASure:VOLTage?` |
| `measure_current(channel?)` | Actual output current via `MEASure:CURRent?` |
| `measure_power(channel?)` | Actual output power (reported or V×I calculated) |
| `get_status(channel?)` | Full snapshot: setpoints, measurements, CV/CC mode, output state, protection status |

### Sequencing
| Tool | Description |
|---|---|
| `run_list(steps[], channel?)` | Executes a voltage/current profile; each step is `{volts, amps, duration_ms}` |
| `abort_list()` | Immediately stops a running list sequence |

### System
| Tool | Description |
|---|---|
| `get_errors()` | Drains the SCPI error queue (`SYSTem:ERRor?`) |
| `reset()` | Sends `*RST` to restore factory defaults |
| `set_remote_lock(enabled)` | Locks or unlocks front panel keys |

---

## Safety Layer (`safety.py`)

Called before every `set_*` and `set_output` command. Not bypassable by AI tool calls.

- **Hard clamp:** Rejects any setpoint above the model's `v_max` or `i_max` from the registry. Returns a descriptive error rather than silently clamping.
- **High-voltage gate:** Models with `high_voltage: true` require `confirm=True` explicitly passed to `set_output(on)`. Without it, the tool returns a warning message asking for confirmation rather than energizing.
- **Output-off on disconnect:** `disconnect()` always sends `OUTPut OFF` before closing the transport, regardless of current state.
- **Live output warning:** `set_voltage` and `set_current` emit a warning (non-blocking) if output is currently enabled, so the AI can surface it to the user.

---

## Configuration

All configuration via environment variables. No secrets in code.

| Variable | Description | Default |
|---|---|---|
| `BK_PORT` | Serial port path (e.g. `/dev/ttyUSB0`, `COM3`) | — |
| `BK_IP` | LAN IP address (mutually exclusive with `BK_PORT`) | — |
| `BK_BAUD` | Serial baud rate | `9600` |
| `BK_MODEL` | Model number to skip auto-detect | — |
| `BK_TIMEOUT` | Command timeout in seconds | `5` |

### Claude Code config (`~/.claude.json`)

```json
{
  "mcpServers": {
    "bk-precision": {
      "command": "python",
      "args": ["/path/to/bk-precision-mcp/server.py"],
      "env": {
        "BK_PORT": "/dev/ttyUSB0",
        "BK_MODEL": "PVS10005"
      }
    }
  }
}
```

### Other clients

- **Cursor:** `.cursor/mcp.json` — same `command`/`args`/`env` structure
- **Windsurf:** `~/.codeium/windsurf/mcp_config.json` — same structure
- The MCP server code is identical across all clients; only the config file path differs.

---

## Dependencies

```toml
[project]
name = "bk-precision-mcp"
requires-python = ">=3.10"

[project.dependencies]
mcp = ">=1.0"
pyserial = ">=3.5"

[project.optional-dependencies]
visa = ["pyvisa>=1.13"]   # Enables USBTMC and GPIB transports
```

PyVISA is optional. If not installed, USBTMC and GPIB transports disable themselves at startup with a clear message. Serial and LAN work out of the box with no extra drivers.

---

## Phase Plan

### Phase 1 — Core (single-channel, serial + LAN)
- Serial and LAN transports
- `core.py`, `source.py`, `measure.py`, `output.py`, `system.py` SCPI modules
- Safety layer
- Registry entries for PVS, 9115B, 9200B, 1696B families
- Mock supply for offline development
- All connection, configuration, measurement, and system tools
- README with setup instructions

**Exit criteria:** Can connect to a PVS10005 over USB, set voltage/current, enable output, measure actuals, and read errors — all from a Claude Code session.

### Phase 2 — Multi-channel
- `multi_channel.py` and INSTrument subsystem
- Channel-aware routing in all tools
- Registry entries for 9129B and 9130B families
- Tests against mock multi-channel supply

**Exit criteria:** Can independently control all three channels on a 9129B.

### Phase 3 — Sequencing
- `trigger.py` and list mode implementation
- `run_list` and `abort_list` tools
- Sequence validation (step count limits, duration bounds) before sending to supply
- Progress reporting during sequence execution

**Exit criteria:** Can run a multi-step voltage ramp profile and abort it mid-sequence.

### Phase 4 — Broadening
- USBTMC transport via PyVISA
- GPIB transport via PyVISA
- Registry entries for XLN, HPS, MPS families
- Published to PyPI as `bk-precision-mcp`
- Config examples for Cursor and Windsurf

---

## Out of Scope

- B&K supplies using proprietary binary protocols (168x series and older)
- AC power sources (1900 series)
- Electronic loads
- Cloud/remote deployment (this MCP is intentionally local-only)
- GUI or web interface
