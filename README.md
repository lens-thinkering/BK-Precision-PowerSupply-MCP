# BK Precision PowerSupply MCP

MCP server that lets AI assistants (Claude, Cursor, Copilot, etc.) control BK Precision programmable DC power supplies. Runs locally — the machine running this server must be physically connected to the supply.

Supports both **proprietary-protocol** models (168x, 9103 series) and **SCPI** models (9200B, 9115, XLN, PVS, etc.) over USB, RS-232, and LAN.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (`pip install uv` or see [uv docs](https://docs.astral.sh/uv/getting-started/installation/))
- Power supply connected via USB, RS-232, or LAN
- Windows: CP210x or CH340 USB driver installed for serial-based models (168x, 9103)

## Install

```bash
git clone https://github.com/lens-thinkering/BK-Precision-PowerSupply-MCP
cd BK-Precision-PowerSupply-MCP
uv sync
```

## Register with your MCP client

Add to your MCP client config (e.g. `claude_desktop_config.json` or `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "bk-precision": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/BK-Precision-PowerSupply-MCP",
        "bk-precision-mcp"
      ]
    }
  }
}
```

Replace `/absolute/path/to/BK-Precision-PowerSupply-MCP` with the actual clone path. On Windows use forward slashes or escape backslashes: `C:/Users/you/BK-Precision-PowerSupply-MCP`.

## Quickstart

Once registered, ask your AI assistant to:

```
What BK Precision power supply models are supported?
```
→ calls `bk_get_supported_models()` — shows the full model table with limits

```
List connected instruments.
```
→ calls `bk_list_instruments()` — shows available VISA resource strings

```
Connect to my 1685B on COM3 and set 5 V at 1 A, then enable the output.
```
→ calls `bk_connect`, `bk_set_voltage`, `bk_set_current`, `bk_output_on`

## Supported Models

| Family | Models | Protocol | Interface |
|---|---|---|---|
| 168x | 1685B, 1687B, 1688B | Proprietary | USB serial |
| 1900B | 1900B, 1901B, 1902B | Proprietary | USB serial |
| 9103 | 9103, 9104 | Proprietary | USB serial |
| 9200B | 9201B, 9202B, 9205B, 9206B | SCPI | USB, RS-232, GPIB, LAN |
| 9115 | 9115, 9116, 9117 | SCPI | USB, RS-232, GPIB, LAN |
| 9170B | 9170B, 9180B | SCPI | USB, RS-232, GPIB, LAN |
| XLN | XLN3640, XLN6024, XLN8018, XLN10014 | SCPI | USB, GPIB, LAN |
| PVS | PVS10005, PVS60085, PVS60085MR | SCPI | USB, RS-232, GPIB, LAN |

Call `bk_get_supported_models()` for the full table including voltage/current limits and feature flags.

## Tools

### Connection
| Tool | Description |
|---|---|
| `bk_get_supported_models` | Show all supported models with limits and capabilities |
| `bk_list_instruments` | List VISA resource strings for connected instruments |
| `bk_connect(resource, model_id)` | Connect — `model_id` required for 168x/9103 (proprietary), optional for SCPI |
| `bk_disconnect(resource)` | Turn off output and close connection |

### Control
| Tool | Description |
|---|---|
| `bk_set_voltage(resource, volts, confirm)` | Set voltage — **`confirm=True` required for ≥ 50 V** |
| `bk_set_current(resource, amps)` | Set current limit |
| `bk_set_ovp(resource, volts)` | Set over-voltage protection threshold |
| `bk_set_ocp(resource, amps)` | Set over-current protection threshold |
| `bk_output_on(resource, confirm)` | Enable output — `confirm=True` required for HV models |
| `bk_output_off(resource)` | Disable output |

### Measurement
| Tool | Description |
|---|---|
| `bk_measure_voltage(resource)` | Measure actual output voltage |
| `bk_measure_current(resource)` | Measure actual output current |
| `bk_measure_power(resource)` | Measure output power (V × I) |
| `bk_get_status(resource)` | Get voltage, current, CV/CC mode, and output state |

## Resource String Formats

| Interface | Windows | Linux / macOS |
|---|---|---|
| USB serial (168x, 9103) | `ASRL3::INSTR` (COM3) | `ASRL/dev/ttyUSB0::INSTR` |
| USBTMC | `USB0::0x0BDB::0x1001::INSTR` | same |
| LAN (raw socket) | `TCPIP0::192.168.1.100::5025::SOCKET` | same |

Use `bk_list_instruments` to discover the correct string for your device.

## Connecting to a model

**SCPI models** (9200B, 9115, XLN, PVS, etc.) are auto-detected via `*IDN?` — `model_id` is optional:
```
bk_connect("USB0::0x0BDB::0x1001::INSTR")
```

**Proprietary-protocol models** (168x, 9103 series) cannot respond to `*IDN?`, so you must supply `model_id`:
```
bk_connect("ASRL3::INSTR", "1685B")
bk_connect("ASRL4::INSTR", "9103")
```

## Safety

- Setpoints validated against each model's rated limits (from `registry.json`) before any command is sent
- Voltage setpoints **≥ 50 V** require `confirm=True` on `bk_set_voltage()` (IEC 60479 / OSHA shock-hazard threshold)
- Models with `high_voltage=true` (PVS series, 9206B, XLN10014) require `confirm=True` on `bk_output_on()` as a second gate
- Output is always turned off on disconnect, regardless of current output state

## Run Tests

All tests run offline against mock instruments — no hardware required:

```bash
uv run python -m pytest tests/ -v
```

## Verify with MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run bk-precision-mcp
```
