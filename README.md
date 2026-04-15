WIP! Initial scaffolding done. Next step is to test on various BK hardware.

# BK Precision MCP

MCP server for controlling BK Precision test and measurement instruments via SCPI. Exposes 27 tools covering power supplies, multimeters, oscilloscopes, and function generators over USB, Ethernet, and RS-232.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Instrument connected via USB, LAN, or serial

## Install

```bash
git clone https://github.com/your-username/BK-Precision-MCP
cd BK-Precision-MCP
uv sync
```

## Register with your MCP client

Add to your client's MCP config (Claude Code, Cursor, VS Code Copilot, etc.):

```json
{
  "mcpServers": {
    "bk-precision": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/BK-Precision-MCP", "bk-precision-mcp"]
    }
  }
}
```

## Tools

### Discovery
| Tool | Description |
|------|-------------|
| `bk_list_instruments` | List all connected VISA resource strings |
| `bk_identify_instrument` | Send `*IDN?` to identify a device |

### Power Supply (`bk_ps_*`)
`set_voltage`, `set_current`, `output_on`, `output_off`, `measure_voltage`, `measure_current`, `get_status`

### Multimeter / DMM (`bk_dmm_*`)
`measure_voltage`, `measure_current`, `measure_resistance`, `measure_continuity`, `measure_diode`

### Oscilloscope (`bk_osc_*`)
`autoscale`, `run`, `stop`, `measure_frequency`, `measure_amplitude`, `set_timebase`, `set_voltage_scale`

### Function Generator (`bk_fg_*`)
`set_waveform`, `set_frequency`, `set_amplitude`, `set_offset`, `output_on`, `output_off`

## Resource String Examples

| Interface | Example |
|-----------|---------|
| USB | `USB0::0x0BDB::0x1001::INSTR` |
| Ethernet | `TCPIP0::192.168.1.100::inst0::INSTR` |
| Serial | `ASRL3::INSTR` (Windows COM3) / `ASRL/dev/ttyUSB0::INSTR` (Linux) |

Use `bk_list_instruments` to discover the correct string for your device.

## Run Tests

```bash
uv run pytest tests/ -v
```

## Verify with MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run bk-precision-mcp
```
