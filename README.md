# UVM Testbench Generator

A SaaS tool and local CLI for verification engineers to rapidly generate production-ready UVM testbench structures.

## Features

- **Web UI** with real-time preview, syntax highlighting, and ZIP download
- **CLI tool** for local/CI integration (`uvmgen generate --name my_dut --protocol apb`)
- **Built-in protocol support**: AXI4-Lite, APB, SPI, UART (with auto-populated ports, constraints, coverage)
- **Custom protocol support**: define your own ports and constraints
- **Full UVM component generation**: Interface, Sequence Item, Sequences, Driver, Monitor, Sequencer, Agent, Scoreboard, Coverage, Environment, Tests, TB Top, Package
- **Extensible architecture**: add new protocols, templates, or components via Python plugins
- **JSON config files** for reproducible, version-controlled testbench specifications

## Quick Start

### Install

```bash
cd UVM_Gen
pip install -e .
```

### CLI Usage

```bash
# Generate a basic testbench
uvmgen generate --name my_dut --protocol apb --output ./tb_output

# Generate with AXI4-Lite
uvmgen generate --name axi_slave --protocol axi4_lite --data-width 64 --output ./axi_tb

# Generate with multiple tests
uvmgen generate --name spi_master --protocol spi -t sanity_test -t stress_test --output ./spi_tb

# Use a JSON config file
uvmgen generate --name my_dut --config my_config.json --output ./tb

# Create a sample config file
uvmgen init my_config.json

# List available protocols
uvmgen list-protocols
```

### Web UI

```bash
# Start the web server
uvmgen serve --port 8000

# With auto-reload for development
uvmgen serve --port 8000 --reload
```

Then open http://localhost:8000 in your browser.

### JSON Config File

```json
{
  "project_name": "axi_slave",
  "protocol": {
    "protocol": "axi4_lite",
    "data_width": 32,
    "addr_width": 32,
    "clock_freq_mhz": 100
  },
  "tests": [
    {"name": "sanity_test", "num_transactions": 50, "timeout_ns": 5000},
    {"name": "stress_test", "num_transactions": 500, "timeout_ns": 50000}
  ],
  "components": {
    "interface": true,
    "sequence_item": true,
    "driver": true,
    "monitor": true,
    "sequencer": true,
    "agent": true,
    "scoreboard": true,
    "coverage": true,
    "env": true,
    "test": true,
    "top": true,
    "package": true,
    "sequences": true
  }
}
```

## Generated File Structure

```
output/
├── {name}_if.sv           # Interface with clocking blocks & modports
├── {name}_seq_item.sv     # Sequence item with constraints
├── {name}_sequences.sv    # Base + per-test sequences
├── {name}_driver.sv       # Driver with virtual interface
├── {name}_monitor.sv      # Monitor with analysis port
├── {name}_sequencer.sv    # Parameterized sequencer
├── {name}_agent.sv        # Agent (active/passive)
├── {name}_scoreboard.sv   # Scoreboard with reference model hook
├── {name}_coverage.sv     # Functional coverage collector
├── {name}_env.sv          # Environment
├── {name}_test.sv         # Base test + scenario tests
├── {name}_tb_top.sv       # Top-level with clock, reset, DUT stub
└── {name}_pkg.sv          # Package with all includes
```

## Extending

### Add a New Protocol

Create a file in `uvmgen/protocols/` that subclasses `ProtocolBase`:

```python
from uvmgen.protocols.base import ProtocolBase
from uvmgen.core.models import Port, PortDirection

class MyProtocol(ProtocolBase):
    name = "my_proto"
    description = "My Custom Protocol"

    def get_ports(self, data_width=32, addr_width=32, **kwargs):
        return [
            self._make_port("data", PortDirection.INPUT, data_width),
            self._make_port("valid", PortDirection.INPUT, 1),
            self._make_port("ready", PortDirection.OUTPUT, 1),
        ]

    def get_constraints(self):
        return "constraint my_c { data != 0; }"

    def get_coverage_bins(self):
        return ""
```

Then register it:

```python
from uvmgen.protocols.registry import register_protocol
register_protocol("my_proto", MyProtocol())
```

### Add a New Test Template

Add a `.sv.j2` Jinja2 template in `uvmgen/templates/` and extend the generator in `uvmgen/core/generator.py`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/protocols` | List available protocols |
| GET | `/api/protocol/{name}/ports` | Get default ports for a protocol |
| POST | `/api/generate` | Generate files (returns JSON) |
| POST | `/api/generate/zip` | Generate and download ZIP |
| POST | `/api/generate/preview` | Preview a single component |

## Tech Stack

- **Backend**: Python, FastAPI, Jinja2, Pydantic
- **Frontend**: HTML, TailwindCSS, Vanilla JS, highlight.js
- **CLI**: Click
- **Templates**: Jinja2 (`.sv.j2` files)

## License

MIT
