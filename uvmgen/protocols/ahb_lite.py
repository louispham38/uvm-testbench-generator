"""AHB-Lite protocol definition."""

from __future__ import annotations

from uvmgen.core.models import Port, PortDirection
from uvmgen.protocols.base import ProtocolBase


class AHBLiteProtocol(ProtocolBase):
    name = "ahb"
    description = "AMBA AHB-Lite Protocol"

    def get_ports(self, data_width: int = 32, addr_width: int = 32, **kwargs) -> list[Port]:
        p = self._make_port
        return [
            p("haddr",    PortDirection.INPUT,  addr_width, "AHB address bus"),
            p("hwrite",   PortDirection.INPUT,  1,          "AHB write"),
            p("hsize",    PortDirection.INPUT,  3,          "AHB transfer size"),
            p("hburst",   PortDirection.INPUT,  3,          "AHB burst type"),
            p("hprot",    PortDirection.INPUT,  4,          "AHB protection control"),
            p("htrans",   PortDirection.INPUT,  2,          "AHB transfer type"),
            p("hmastlock", PortDirection.INPUT, 1,          "AHB locked transfer"),
            p("hwdata",   PortDirection.INPUT,  data_width, "AHB write data"),
            p("hsel",     PortDirection.INPUT,  1,          "AHB slave select"),
            p("hrdata",   PortDirection.OUTPUT, data_width, "AHB read data"),
            p("hready",   PortDirection.OUTPUT, 1,          "AHB ready"),
            p("hreadyout", PortDirection.OUTPUT, 1,         "AHB ready output (from slave)"),
            p("hresp",    PortDirection.OUTPUT, 1,          "AHB transfer response"),
        ]

    def get_constraints(self) -> str:
        return """
    constraint ahb_trans_c {
        htrans inside {2'b00, 2'b01, 2'b10, 2'b11};  // IDLE, BUSY, NONSEQ, SEQ
    }
    constraint ahb_size_c {
        hsize <= 3'b010;  // max 32-bit (word)
    }
    constraint ahb_burst_c {
        hburst inside {3'b000, 3'b001, 3'b010, 3'b011};  // SINGLE, INCR, WRAP4, INCR4
    }"""

    def get_coverage_bins(self) -> str:
        return """
      htrans_cp : coverpoint htrans {
        bins idle   = {2'b00};
        bins busy   = {2'b01};
        bins nonseq = {2'b10};
        bins seq    = {2'b11};
      }
      hsize_cp : coverpoint hsize {
        bins byte_t = {3'b000};
        bins half_t = {3'b001};
        bins word_t = {3'b010};
      }
      hwrite_cp : coverpoint hwrite {
        bins read  = {0};
        bins write = {1};
      }
      hburst_cp : coverpoint hburst {
        bins single = {3'b000};
        bins incr   = {3'b001};
        bins wrap4  = {3'b010};
        bins incr4  = {3'b011};
      }"""
