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
        return ""

    def get_coverage_bins(self) -> str:
        return ""
