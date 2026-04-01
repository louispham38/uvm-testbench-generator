"""I2C protocol definition."""

from __future__ import annotations

from uvmgen.core.models import Port, PortDirection
from uvmgen.protocols.base import ProtocolBase


class I2CProtocol(ProtocolBase):
    name = "i2c"
    description = "I2C (Inter-Integrated Circuit) Protocol"

    def get_ports(self, data_width: int = 8, addr_width: int = 7, **kwargs) -> list[Port]:
        p = self._make_port
        return [
            p("scl_i",  PortDirection.INPUT,  1, "I2C clock input"),
            p("scl_o",  PortDirection.OUTPUT, 1, "I2C clock output"),
            p("scl_oe", PortDirection.OUTPUT, 1, "I2C clock output enable"),
            p("sda_i",  PortDirection.INPUT,  1, "I2C data input"),
            p("sda_o",  PortDirection.OUTPUT, 1, "I2C data output"),
            p("sda_oe", PortDirection.OUTPUT, 1, "I2C data output enable"),
        ]

    def get_constraints(self) -> str:
        return """
    constraint i2c_addr_c {
        addr inside {[7'h08 : 7'h77]};  // valid 7-bit addresses (avoid reserved)
    }
    constraint i2c_data_c {
        data_byte inside {[0:255]};
    }"""

    def get_coverage_bins(self) -> str:
        return """
      rw_cp : coverpoint rw_bit {
        bins write = {0};
        bins read  = {1};
      }
      addr_cp : coverpoint addr {
        bins low_range  = {[7'h08:7'h3F]};
        bins high_range = {[7'h40:7'h77]};
      }
      ack_cp : coverpoint ack {
        bins ack  = {0};
        bins nack = {1};
      }"""
