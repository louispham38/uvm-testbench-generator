"""APB (Advanced Peripheral Bus) protocol definition."""

from __future__ import annotations

from uvmgen.core.models import Port, PortDirection
from uvmgen.protocols.base import ProtocolBase


class APBProtocol(ProtocolBase):
    name = "apb"
    description = "AMBA APB Protocol"

    def get_ports(self, data_width: int = 32, addr_width: int = 32, **kwargs) -> list[Port]:
        p = self._make_port
        strb_width = data_width // 8
        return [
            p("paddr",   PortDirection.INPUT,  addr_width, "APB address"),
            p("psel",    PortDirection.INPUT,  1,          "APB select"),
            p("penable", PortDirection.INPUT,  1,          "APB enable"),
            p("pwrite",  PortDirection.INPUT,  1,          "APB write"),
            p("pwdata",  PortDirection.INPUT,  data_width, "APB write data"),
            p("pstrb",   PortDirection.INPUT,  strb_width, "APB write strobe"),
            p("pprot",   PortDirection.INPUT,  3,          "APB protection"),
            p("prdata",  PortDirection.OUTPUT, data_width, "APB read data"),
            p("pready",  PortDirection.OUTPUT, 1,          "APB ready"),
            p("pslverr", PortDirection.OUTPUT, 1,          "APB slave error"),
        ]

    def get_constraints(self) -> str:
        return """
    constraint apb_basic_c {
        psel   -> penable;
    }"""

    def get_coverage_bins(self) -> str:
        return """
    covergroup apb_cg;
        apb_write: coverpoint pwrite {
            bins read  = {1'b0};
            bins write = {1'b1};
        }
        apb_error: coverpoint pslverr {
            bins ok  = {1'b0};
            bins err = {1'b1};
        }
        apb_addr: coverpoint paddr {
            bins low   = {[0:32'h0000_FFFF]};
            bins mid   = {[32'h0001_0000:32'h7FFF_FFFF]};
            bins high  = {[32'h8000_0000:32'hFFFF_FFFF]};
        }
    endgroup"""
