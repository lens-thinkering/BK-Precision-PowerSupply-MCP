# B&K Precision MCP

MCP server that lets AI assistants control B&K Precision programmable DC power supplies via SCPI. Runs locally — the machine running this server must be physically connected to the supply over USB, RS232, or LAN.

**SCPI-capable models only.** Proprietary-protocol models (older 168x series) are explicitly out of scope.

## Project Structure

```
bk-precision-mcp/
├── server.py                     # MCP entry point
├── pyproject.toml
├── CLAUDE.md
├── bk_mcp/
│   ├── transport/
│   │   ├── base.py               # Abstract transport: write(cmd), query(cmd) only
│   │   ├── serial_transport.py   # USB vCOM + RS232 via pyserial
│   │   ├── usbtmc_transport.py   # USBTMC via pyvisa (optional)
│   │   └── lan_transport.py      # Raw TCP socket port 5025
│   ├── models/
│   │   └── registry.json         # Per-model capability database
│   ├── scpi/
│   │   ├── core.py               # IEEE-488.2 common commands
│   │   ├── source.py             # SOURce subsystem
│   │   ├── measure.py            # MEASure subsystem
│   │   ├── output.py             # OUTPut subsystem
│   │   ├── system.py             # SYSTem subsystem
│   │   ├── trigger.py            # TRIGger / list mode
│   │   └── multi_channel.py      # INSTrument subsystem
│   ├── safety.py                 # Clamp validation, HV gate — never bypass
│   └── tools.py                  # MCP tool definitions
└── tests/
    ├── mock_supply.py            # Simulated SCPI responder for offline dev
    └── test_tools.py
```

## Architecture Decisions

**Transport abstraction is strict.** `base.py` defines only `write(cmd)` and `query(cmd)`. SCPI modules never touch hardware directly — they always go through the transport. This keeps things mockable and swappable.

**Registry drives everything.** `registry.json` controls what tools are available, what the safety limits are, and whether a model supports list mode, remote sense, or multi-channel. Don't hardcode model-specific behavior in tool logic — look it up from the registry.

**Multi-channel tools are conditional.** Only expose the `channel` parameter when the connected model has `channels > 1` in the registry.

**`scpi_subset: true` models** (1696B family) gracefully skip unsupported tools rather than erroring.

## Safety Layer — Critical

`safety.py` is called before every `set_*` and `set_output` command. It is not bypassable.

- Hard clamp: reject setpoints above `v_max` / `i_max` from registry. Return a descriptive error, never silently clamp.
- High-voltage gate: models with `high_voltage: true` require `confirm=True` on `set_output(on)`. Without it, return a warning, do not energize.
- Output-off on disconnect: always send `OUTPut OFF` before closing transport regardless of state.
- Live output warning: emit a non-blocking warning if output is on when `set_voltage` or `set_current` is called.

## Supported Model Families

| Family | Key Models | `high_voltage` |
|---|---|---|
| PVS | PVS10005, PVS60085, PVS60085MR | true |
| 9115/9115B | 9115, 9116, 9117 | false |
| 9200/9200B | 9201B, 9202B, 9205B, 9206B | false |
| 9129B | 9129B (3-channel) | false |
| 9130B | 9130B (3-channel) | false |
| 1696B | 1696B, 1697B, 1698B (`scpi_subset: true`) | false |
| XLN | XLN6024, XLN8018 | false |
| HPS/MPS | Various high-power rack units | true |

## MCP Tools

Connection: `connect`, `disconnect`, `get_identity`
Configuration: `set_voltage`, `set_current`, `set_ovp`, `set_ocp`, `set_output`
Measurement: `measure_voltage`, `measure_current`, `measure_power`, `get_status`
Sequencing: `run_list`, `abort_list`
System: `get_errors`, `reset`, `set_remote_lock`

## Configuration (Environment Variables)

| Variable | Description |
|---|---|
| `BK_PORT` | Serial port (e.g. `/dev/ttyUSB0`, `COM3`) |
| `BK_IP` | LAN IP — mutually exclusive with `BK_PORT` |
| `BK_BAUD` | Baud rate, default `9600` |
| `BK_MODEL` | Optional — skips `*IDN?` auto-detect |
| `BK_TIMEOUT` | Command timeout seconds, default `5` |

## Dependencies

```toml
[project.dependencies]
mcp = ">=1.0"
pyserial = ">=3.5"

[project.optional-dependencies]
visa = ["pyvisa>=1.13"]   # Enables USBTMC and GPIB transports
```

## Phase Plan

- **Phase 1 (current):** Serial + LAN transports, single-channel tools, PVS/9115B/9200B/1696B registry entries, mock supply, full test coverage. Exit: connect to PVS10005 over USB from a Claude Code session and run a basic test.
- **Phase 2:** Multi-channel support, 9129B/9130B registry entries.
- **Phase 3:** List mode sequencing (`run_list`, `abort_list`), sequence validation.
- **Phase 4:** USBTMC + GPIB via PyVISA, XLN/HPS/MPS families, publish to PyPI.

## Out of Scope

- Proprietary-protocol models (168x series and older)
- AC power sources, electronic loads
- Cloud or remote deployment — this MCP is local-only by design
