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

        files["file.list"] = self._render_file_list(files)
        files["README.txt"] = self._render_readme(files)
        files["run.sh"] = self._render_run_script()

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


    def _render_file_list(self, files: dict[str, str]) -> str:
        """Generate file.list containing only top-level compile units.

        Files that are `include'd inside the package are not listed here
        to avoid double-compilation and cross-module reference errors.
        Order: interface first, then package, then tb_top last, then DUT placeholder.
        """
        name = self.config.effective_module_name()
        included_in_pkg = {
            f"{name}_seq_item.sv",
            f"{name}_sequences.sv",
            f"{name}_driver.sv",
            f"{name}_monitor.sv",
            f"{name}_sequencer.sv",
            f"{name}_agent.sv",
            f"{name}_scoreboard.sv",
            f"{name}_coverage.sv",
            f"{name}_env.sv",
            f"{name}_test.sv",
        }
        preferred_order = [
            f"{name}_if.sv",
            f"{name}_pkg.sv",
            f"{name}_tb_top.sv",
        ]
        top_level = [
            f for f in files
            if f.endswith(".sv") and f not in included_in_pkg
        ]
        ordered = [f for f in preferred_order if f in top_level]
        ordered += [f for f in top_level if f not in preferred_order]

        lines = [
            f"# file.list - UVM Testbench Compile File List",
            f"# Project: {self.config.project_name}",
            f"# Generated by UVM Testbench Generator (https://uvmgen-app.vercel.app)",
            f"#",
            f"# Quick compile (Synopsys VCS):",
            f"#   vcs -full64 -sverilog -ntb_opts uvm-1.2 -f file.list",
            f"#",
            f"# Quick compile (Cadence Xcelium):",
            f"#   xrun -sv -uvm -f file.list",
            f"#",
            f"# Quick compile (Mentor Questa):",
            f"#   vlog -sv -f file.list && vsim -c {name}_tb_top",
            f"#",
            f"# Or simply run: bash run.sh",
            f"#",
            f"# NOTE: Component files ({name}_driver.sv, {name}_monitor.sv, etc.) are",
            f"# `include'd inside {name}_pkg.sv and must NOT be listed here separately.",
            f"",
        ]
        for f in ordered:
            lines.append(f)
        lines += [
            f"",
            f"# ── DUT file(s) ──────────────────────────────────────────────────────",
            f"# Add your design file(s) below. Uncomment and update the path:",
            f"# {self.config.project_name}.v",
            f"# {self.config.project_name}.sv",
        ]
        return "\n".join(lines) + "\n"

    def _render_readme(self, files: dict[str, str]) -> str:
        """Generate a README.txt with compile and usage instructions."""
        name = self.config.effective_module_name()
        proto = self.config.protocol.protocol
        sv_files = [f for f in files if f.endswith(".sv")]
        return f"""\
================================================================================
  UVM Testbench: {name}
  Protocol: {proto}
  Generated by UVM Testbench Generator (https://uvmgen-app.vercel.app)
================================================================================

QUICK START
-----------

  1. Add your DUT file(s) to this directory.

  2. Edit {name}_tb_top.sv:
     - Uncomment and connect the DUT instantiation section.
     - Map DUT ports to the interface signals (intf.<signal>).

  3. Add your DUT file(s) to file.list:
     - Open file.list, scroll to the "DUT file(s)" section at the bottom.
     - Uncomment or add your .v / .sv file paths.

  4. Compile and run:

     # Synopsys VCS
     vcs -full64 -sverilog -ntb_opts uvm-1.2 -f file.list
     ./simv +UVM_TESTNAME={name}_base_test

     # Cadence Xcelium
     xrun -sv -uvm -f file.list +UVM_TESTNAME={name}_base_test

     # Mentor Questa
     vlog -sv -f file.list
     vsim -c {name}_tb_top +UVM_TESTNAME={name}_base_test -do "run -all"

     # Or simply:
     bash run.sh

RUN SPECIFIC TEST
-----------------
     ./simv +UVM_TESTNAME={name}_<test_name>

     Available tests:
{self._format_test_list(name)}

GENERATED FILES
---------------
  file.list                   Compile file list (top-level units only)
  run.sh                      One-click compile & run script (VCS)
  {name}_if.sv           Interface with clocking blocks & modports
  {name}_pkg.sv          Package (includes all components below)
  {name}_tb_top.sv       Top-level testbench module
  {name}_seq_item.sv     Sequence item (transaction)
  {name}_sequences.sv    Sequences (stimulus generation)
  {name}_driver.sv       Driver (drives DUT via interface)
  {name}_monitor.sv      Monitor (observes DUT via interface)
  {name}_sequencer.sv    Sequencer
  {name}_agent.sv        Agent (bundles driver/monitor/sequencer)
  {name}_scoreboard.sv   Scoreboard (checking)
  {name}_coverage.sv     Functional coverage collector
  {name}_env.sv          Environment (top-level UVM env)
  {name}_test.sv         Test classes

COMPILE ORDER (Important!)
--------------------------
  Only these files go in file.list (the rest are `include'd in the package):
    1. {name}_if.sv          (interface - must be first)
    2. {name}_pkg.sv         (package - includes all components)
    3. {name}_tb_top.sv      (top - must be after package)
    4. your_dut.v            (your design)

  Do NOT add component files (driver, monitor, etc.) to file.list directly.
  They are already `include'd inside {name}_pkg.sv.
"""

    def _format_test_list(self, name: str) -> str:
        lines = []
        for t in self.config.tests:
            tname = t.name + "_0" if t.name == "base_test" else t.name
            desc = f" - {t.description}" if t.description else ""
            lines.append(f"       {name}_{tname}{desc}")
        return "\n".join(lines) if lines else f"       {name}_base_test"

    def _render_run_script(self) -> str:
        """Generate a run.sh script for one-click compile & simulate."""
        name = self.config.effective_module_name()
        return f"""\
#!/bin/bash
# run.sh - Compile and run UVM testbench
# Generated by UVM Testbench Generator (https://uvmgen-app.vercel.app)
#
# Usage:
#   bash run.sh                            # compile + run base_test
#   bash run.sh {name}_sanity_test    # compile + run specific test
#   bash run.sh --compile-only             # compile only, no simulation

set -e

TESTNAME="${{1:-{name}_base_test}}"
TB_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── Detect simulator ─────────────────────────────────────────────────────
if command -v vcs &>/dev/null; then
    SIM="vcs"
elif command -v xrun &>/dev/null; then
    SIM="xrun"
elif command -v vlog &>/dev/null; then
    SIM="questa"
else
    echo "ERROR: No supported simulator found (vcs, xrun, or questa)."
    echo "Please add your simulator to PATH."
    exit 1
fi

echo "========================================"
echo " UVM Testbench: {name}"
echo " Simulator:     $SIM"
echo " Test:          $TESTNAME"
echo "========================================"

cd "$TB_DIR"

case "$SIM" in
  vcs)
    echo "[COMPILE] vcs -full64 -sverilog -ntb_opts uvm-1.2 -f file.list"
    vcs -full64 -sverilog -ntb_opts uvm-1.2 -f file.list -o simv 2>&1 | tee compile.log
    if [[ "$1" == "--compile-only" ]]; then echo "Compile done."; exit 0; fi
    echo "[RUN] ./simv +UVM_TESTNAME=$TESTNAME"
    ./simv +UVM_TESTNAME=$TESTNAME +UVM_VERBOSITY=UVM_MEDIUM 2>&1 | tee sim.log
    ;;
  xrun)
    echo "[COMPILE+RUN] xrun -sv -uvm -f file.list +UVM_TESTNAME=$TESTNAME"
    xrun -sv -uvm -f file.list +UVM_TESTNAME=$TESTNAME +UVM_VERBOSITY=UVM_MEDIUM 2>&1 | tee sim.log
    ;;
  questa)
    echo "[COMPILE] vlog -sv -f file.list"
    vlib work 2>/dev/null || true
    vlog -sv -f file.list 2>&1 | tee compile.log
    if [[ "$1" == "--compile-only" ]]; then echo "Compile done."; exit 0; fi
    echo "[RUN] vsim -c {name}_tb_top +UVM_TESTNAME=$TESTNAME"
    vsim -c {name}_tb_top +UVM_TESTNAME=$TESTNAME +UVM_VERBOSITY=UVM_MEDIUM -do "run -all; quit" 2>&1 | tee sim.log
    ;;
esac

echo ""
echo "========================================"
if grep -q "UVM_FATAL\\|UVM_ERROR" sim.log 2>/dev/null; then
    echo " RESULT: FAIL (check sim.log)"
else
    echo " RESULT: PASS"
fi
echo "========================================"
"""


def _default_ports():
    """Fallback minimal ports when nothing is specified."""
    from uvmgen.core.models import Port, PortDirection
    return [
        Port(name="data_in",  direction=PortDirection.INPUT,  width=32),
        Port(name="data_out", direction=PortDirection.OUTPUT, width=32),
        Port(name="valid",    direction=PortDirection.INPUT,  width=1),
        Port(name="ready",    direction=PortDirection.OUTPUT, width=1),
    ]
