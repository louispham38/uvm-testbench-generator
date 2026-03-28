"""Base protocol definition."""

from __future__ import annotations

from uvmgen.core.models import Port, PortDirection


class ProtocolBase:
    """Base class for protocol definitions. Subclass to add built-in protocols."""

    name: str = "custom"
    description: str = "Custom protocol"

    def get_ports(self, data_width: int = 32, addr_width: int = 32, **kwargs) -> list[Port]:
        """Return the list of ports for this protocol."""
        return []

    def get_constraints(self) -> str:
        """Return SystemVerilog constraint blocks for this protocol."""
        return ""

    def get_coverage_bins(self) -> str:
        """Return coverage bins specific to this protocol."""
        return ""

    @staticmethod
    def _make_port(name: str, direction: PortDirection, width: int = 1, desc: str = "") -> Port:
        return Port(name=name, direction=direction, width=width, description=desc)
