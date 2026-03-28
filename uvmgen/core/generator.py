"""UVM code generation engine."""

from __future__ import annotations

import io
import os
import zipfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from uvmgen.core.models import ProjectConfig
from uvmgen.protocols.registry import get_protocol

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


class UVMGenerator:
    """Renders Jinja2 templates into a complete UVM testbench."""

    def __init__(self, config: ProjectConfig):
        self.config = config
        self.env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        self._protocol = get_protocol(config.protocol.protocol)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_all(self) -> dict[str, str]:
        """Return {relative_filename: contents} for every selected component."""
        files: dict[str, str] = {}
        name = self.config.effective_module_name()
        comp = self.config.components

        if comp.interface:
            files[f"{name}_if.sv"] = self._render_interface()
        if comp.sequence_item:
            files[f"{name}_seq_item.sv"] = self._render_sequence_item()
        if comp.sequences:
            files[f"{name}_sequences.sv"] = self._render_sequences()
        if comp.driver:
            files[f"{name}_driver.sv"] = self._render_driver()
        if comp.monitor:
            files[f"{name}_monitor.sv"] = self._render_monitor()
        if comp.sequencer:
            files[f"{name}_sequencer.sv"] = self._render_sequencer()
        if comp.agent:
            files[f"{name}_agent.sv"] = self._render_agent()
        if comp.scoreboard:
            files[f"{name}_scoreboard.sv"] = self._render_scoreboard()
        if comp.coverage:
            files[f"{name}_coverage.sv"] = self._render_coverage()
        if comp.env:
            files[f"{name}_env.sv"] = self._render_env()
        if comp.test:
            files[f"{name}_test.sv"] = self._render_test()
        if comp.top:
            files[f"{name}_tb_top.sv"] = self._render_top()
        if comp.package:
            files[f"{name}_pkg.sv"] = self._render_package()

        return files

    def generate_zip(self) -> bytes:
        """Return an in-memory ZIP archive of all generated files."""
        files = self.generate_all()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname, content in files.items():
                zf.writestr(fname, content)
        return buf.getvalue()

    def write_to_disk(self, output_dir: str | None = None) -> list[str]:
        """Write generated files to *output_dir* and return the file paths."""
        out = Path(output_dir or self.config.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        files = self.generate_all()
        written: list[str] = []
        for fname, content in files.items():
            path = out / fname
            path.write_text(content, encoding="utf-8")
            written.append(str(path))
        return written

    # ------------------------------------------------------------------
    # Private renderers
    # ------------------------------------------------------------------

    def _common_ctx(self) -> dict:
        """Context shared by all templates."""
        ports = self._effective_ports()
        return {
            "name": self.config.effective_module_name(),
            "module_name": self.config.effective_module_name(),
            "ports": ports,
            "protocol_name": self._protocol.name,
        }

    def _effective_ports(self):
        """Use protocol ports if no custom ports defined."""
        if self.config.ports:
            return self.config.ports
        proto_ports = self._protocol.get_ports(
            data_width=self.config.protocol.data_width,
            addr_width=self.config.protocol.addr_width,
        )
        return proto_ports if proto_ports else _default_ports()

    def _render(self, template_path: str, extra_ctx: dict | None = None) -> str:
        ctx = self._common_ctx()
        if extra_ctx:
            ctx.update(extra_ctx)
        tpl = self.env.get_template(template_path)
        return tpl.render(**ctx)

    def _render_interface(self) -> str:
        return self._render("top/interface.sv.j2", {
            "protocol_assertions": "",
        })

    def _render_sequence_item(self) -> str:
        return self._render("seq/sequence_item.sv.j2", {
            "protocol_constraints": self._protocol.get_constraints(),
        })

    def _render_sequences(self) -> str:
        return self._render("seq/sequence.sv.j2", {
            "tests": self.config.tests,
            "num_transactions": self.config.tests[0].num_transactions if self.config.tests else 100,
        })

    def _render_driver(self) -> str:
        return self._render("agent/driver.sv.j2")

    def _render_monitor(self) -> str:
        return self._render("agent/monitor.sv.j2")

    def _render_sequencer(self) -> str:
        return self._render("agent/sequencer.sv.j2")

    def _render_agent(self) -> str:
        return self._render("agent/agent.sv.j2", {
            "has_driver": self.config.agent.has_driver,
            "has_monitor": self.config.agent.has_monitor,
            "has_sequencer": self.config.agent.has_sequencer,
        })

    def _render_scoreboard(self) -> str:
        return self._render("env/scoreboard.sv.j2")

    def _render_coverage(self) -> str:
        return self._render("env/coverage.sv.j2", {
            "protocol_coverage": self._protocol.get_coverage_bins(),
        })

    def _render_env(self) -> str:
        return self._render("env/env.sv.j2", {
            "has_scoreboard": self.config.components.scoreboard,
            "has_coverage": self.config.components.coverage,
        })

    def _render_test(self) -> str:
        return self._render("test/test.sv.j2", {
            "tests": self.config.tests,
            "has_reset": any(t.has_reset_sequence for t in self.config.tests),
        })

    def _render_top(self) -> str:
        clk_mhz = self.config.protocol.clock_freq_mhz
        clk_period = round(1000.0 / clk_mhz, 2) if clk_mhz else 10.0
        timeout = max(t.timeout_ns for t in self.config.tests) * 10 if self.config.tests else 100_000
        return self._render("top/top.sv.j2", {
            "clk_period_ns": clk_period,
            "timeout_ns": timeout,
        })

    def _render_package(self) -> str:
        c = self.config.components
        return self._render("pkg/package.sv.j2", {
            "gen_sequence_item": c.sequence_item,
            "gen_sequences": c.sequences,
            "gen_driver": c.driver,
            "gen_monitor": c.monitor,
            "gen_sequencer": c.sequencer,
            "gen_agent": c.agent,
            "gen_scoreboard": c.scoreboard,
            "gen_coverage": c.coverage,
            "gen_env": c.env,
            "gen_test": c.test,
        })


def _default_ports():
    """Fallback minimal ports when nothing is specified."""
    from uvmgen.core.models import Port, PortDirection
    return [
        Port(name="data_in",  direction=PortDirection.INPUT,  width=32),
        Port(name="data_out", direction=PortDirection.OUTPUT, width=32),
        Port(name="valid",    direction=PortDirection.INPUT,  width=1),
        Port(name="ready",    direction=PortDirection.OUTPUT, width=1),
    ]
