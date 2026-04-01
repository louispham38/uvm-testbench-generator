"""AXI4-Lite protocol definition."""

from __future__ import annotations

from uvmgen.core.models import Port, PortDirection
from uvmgen.protocols.base import ProtocolBase


class AXI4LiteProtocol(ProtocolBase):
    name = "axi4_lite"
    description = "AMBA AXI4-Lite Protocol"

    def get_ports(self, data_width: int = 32, addr_width: int = 32, **kwargs) -> list[Port]:
        p = self._make_port
        strb_width = data_width // 8
        return [
            # Write address channel
            p("awaddr",  PortDirection.INPUT,  addr_width, "Write address"),
            p("awprot",  PortDirection.INPUT,  3,          "Write protection"),
            p("awvalid", PortDirection.INPUT,  1,          "Write address valid"),
            p("awready", PortDirection.OUTPUT, 1,          "Write address ready"),
            # Write data channel
            p("wdata",   PortDirection.INPUT,  data_width, "Write data"),
            p("wstrb",   PortDirection.INPUT,  strb_width, "Write strobe"),
            p("wvalid",  PortDirection.INPUT,  1,          "Write data valid"),
            p("wready",  PortDirection.OUTPUT, 1,          "Write data ready"),
            # Write response channel
            p("bresp",   PortDirection.OUTPUT, 2,          "Write response"),
            p("bvalid",  PortDirection.OUTPUT, 1,          "Write response valid"),
            p("bready",  PortDirection.INPUT,  1,          "Write response ready"),
            # Read address channel
            p("araddr",  PortDirection.INPUT,  addr_width, "Read address"),
            p("arprot",  PortDirection.INPUT,  3,          "Read protection"),
            p("arvalid", PortDirection.INPUT,  1,          "Read address valid"),
            p("arready", PortDirection.OUTPUT, 1,          "Read address ready"),
            # Read data channel
            p("rdata",   PortDirection.OUTPUT, data_width, "Read data"),
            p("rresp",   PortDirection.OUTPUT, 2,          "Read response"),
            p("rvalid",  PortDirection.OUTPUT, 1,          "Read data valid"),
            p("rready",  PortDirection.INPUT,  1,          "Read data ready"),
        ]

    def get_constraints(self) -> str:
        return """
    constraint axi_lite_resp_c {
        bresp inside {2'b00, 2'b10};  // OKAY or SLVERR
        rresp inside {2'b00, 2'b10};
    }
    constraint axi_lite_prot_c {
        awprot inside {3'b000, 3'b001, 3'b010};
        arprot inside {3'b000, 3'b001, 3'b010};
    }"""

    def get_coverage_bins(self) -> str:
        return ""
