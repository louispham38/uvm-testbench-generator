"""UART protocol definition."""

from __future__ import annotations

from uvmgen.core.models import Port, PortDirection
from uvmgen.protocols.base import ProtocolBase


class UARTProtocol(ProtocolBase):
    name = "uart"
    description = "UART (Universal Asynchronous Receiver Transmitter) Protocol"

    def get_ports(self, data_width: int = 8, addr_width: int = 32, **kwargs) -> list[Port]:
        p = self._make_port
        return [
            p("tx",       PortDirection.OUTPUT, 1, "UART transmit"),
            p("rx",       PortDirection.INPUT,  1, "UART receive"),
            p("cts_n",    PortDirection.INPUT,  1, "Clear to send (active low)"),
            p("rts_n",    PortDirection.OUTPUT, 1, "Request to send (active low)"),
        ]

    def get_constraints(self) -> str:
        return """
    constraint uart_data_c {
        data inside {[0:255]};
    }
    constraint uart_baud_c {
        baud_rate inside {9600, 19200, 38400, 57600, 115200};
    }"""

    def get_coverage_bins(self) -> str:
        return """
    covergroup uart_cg;
        uart_data: coverpoint data {
            bins low  = {[0:63]};
            bins mid  = {[64:191]};
            bins high = {[192:255]};
        }
        uart_parity: coverpoint parity_error {
            bins ok  = {1'b0};
            bins err = {1'b1};
        }
    endgroup"""
