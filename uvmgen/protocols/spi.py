"""SPI protocol definition."""

from __future__ import annotations

from uvmgen.core.models import Port, PortDirection
from uvmgen.protocols.base import ProtocolBase


class SPIProtocol(ProtocolBase):
    name = "spi"
    description = "SPI (Serial Peripheral Interface) Protocol"

    def get_ports(self, data_width: int = 8, addr_width: int = 32, **kwargs) -> list[Port]:
        p = self._make_port
        return [
            p("sclk", PortDirection.INPUT,  1, "SPI clock"),
            p("mosi", PortDirection.INPUT,  1, "Master Out Slave In"),
            p("miso", PortDirection.OUTPUT, 1, "Master In Slave Out"),
            p("cs_n", PortDirection.INPUT,  1, "Chip select (active low)"),
        ]

    def get_constraints(self) -> str:
        return ""

    def get_coverage_bins(self) -> str:
        return ""
