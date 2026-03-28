"""CLI interface for UVM Testbench Generator.

Usage:
    uvmgen generate --name my_dut --protocol apb --output ./tb
    uvmgen generate --config config.json --output ./tb
    uvmgen serve --port 8000
    uvmgen list-protocols
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from uvmgen.core.generator import UVMGenerator
from uvmgen.core.models import (
    Port,
    PortDirection,
    ProjectConfig,
    ProtocolConfig,
    ProtocolType,
    TestConfig,
)


@click.group()
@click.version_option(version="1.0.0", prog_name="uvmgen")
def main():
    """UVM Testbench Generator - Build production UVM testbenches fast."""
    pass


@main.command()
@click.option("--name", "-n", required=True, help="Project / DUT name")
@click.option("--protocol", "-p", default="custom",
              type=click.Choice(["custom", "axi4_lite", "apb", "spi", "uart"], case_sensitive=False),
              help="Protocol type")
@click.option("--data-width", "-dw", default=32, type=int, help="Data bus width")
@click.option("--addr-width", "-aw", default=32, type=int, help="Address bus width")
@click.option("--output", "-o", default="./output", help="Output directory")
@click.option("--config", "-c", type=click.Path(exists=True), help="JSON config file (overrides other flags)")
@click.option("--clock-mhz", default=100.0, type=float, help="Clock frequency in MHz")
@click.option("--tests", "-t", multiple=True, help="Test names (repeatable)")
def generate(name, protocol, data_width, addr_width, output, config, clock_mhz, tests):
    """Generate a complete UVM testbench."""
    if config:
        cfg_path = Path(config)
        cfg_data = json.loads(cfg_path.read_text())
        proj = ProjectConfig(**cfg_data)
    else:
        test_list = []
        if tests:
            for t in tests:
                test_list.append(TestConfig(name=t))
        else:
            test_list.append(TestConfig(name="base_test"))

        proj = ProjectConfig(
            project_name=name,
            protocol=ProtocolConfig(
                protocol=protocol,
                data_width=data_width,
                addr_width=addr_width,
                clock_freq_mhz=clock_mhz,
            ),
            tests=test_list,
            output_dir=output,
        )

    gen = UVMGenerator(proj)
    written = gen.write_to_disk(output)

    click.secho(f"\n  UVM Testbench Generated!", fg="green", bold=True)
    click.secho(f"  Protocol: {proj.protocol.protocol}", fg="cyan")
    click.secho(f"  Output:   {Path(output).resolve()}\n", fg="cyan")

    for f in written:
        click.echo(f"    {f}")

    click.echo()


@main.command("list-protocols")
def list_protocols():
    """Show all available protocol definitions."""
    from uvmgen.protocols.registry import list_protocols as _list

    protocols = _list()
    click.secho("\n  Available Protocols:\n", fg="green", bold=True)
    for p in protocols:
        click.echo(f"    {p['name']:15s} {p['description']}")
    click.echo()


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", default=8000, type=int, help="Port to listen on")
@click.option("--reload", is_flag=True, help="Enable auto-reload (dev mode)")
def serve(host, port, reload):
    """Start the web UI server."""
    import uvicorn
    click.secho(f"\n  Starting UVM Testbench Generator on http://{host}:{port}\n", fg="green", bold=True)
    uvicorn.run("uvmgen.app:app", host=host, port=port, reload=reload)


@main.command()
@click.argument("config_file", type=click.Path())
def init(config_file):
    """Create a sample JSON config file."""
    sample = ProjectConfig(
        project_name="my_dut",
        protocol=ProtocolConfig(protocol=ProtocolType.APB, data_width=32, addr_width=32),
        tests=[
            TestConfig(name="sanity_test", num_transactions=50),
            TestConfig(name="stress_test", num_transactions=500),
        ],
    )
    path = Path(config_file)
    path.write_text(json.dumps(sample.model_dump(), indent=2))
    click.secho(f"\n  Sample config written to {path}\n", fg="green", bold=True)


if __name__ == "__main__":
    main()
