"""Protocol registry - central place to look up protocol definitions."""

from __future__ import annotations

from uvmgen.core.models import ProtocolType
from uvmgen.protocols.ahb_lite import AHBLiteProtocol
from uvmgen.protocols.apb import APBProtocol
from uvmgen.protocols.axi4_lite import AXI4LiteProtocol
from uvmgen.protocols.base import ProtocolBase
from uvmgen.protocols.i2c import I2CProtocol
from uvmgen.protocols.spi import SPIProtocol
from uvmgen.protocols.uart import UARTProtocol

_BUILTIN: dict[str, ProtocolBase] = {
    ProtocolType.AXI4_LITE: AXI4LiteProtocol(),
    ProtocolType.APB: APBProtocol(),
    ProtocolType.AHB: AHBLiteProtocol(),
    ProtocolType.SPI: SPIProtocol(),
    ProtocolType.UART: UARTProtocol(),
    ProtocolType.I2C: I2CProtocol(),
}

_custom: dict[str, ProtocolBase] = {}


def get_protocol(name: str) -> ProtocolBase:
    if name in _custom:
        return _custom[name]
    if name in _BUILTIN:
        return _BUILTIN[name]
    return ProtocolBase()


def register_protocol(name: str, protocol: ProtocolBase) -> None:
    """Register a custom protocol at runtime (extensibility hook)."""
    _custom[name] = protocol


def list_protocols() -> list[dict]:
    combined = {**_BUILTIN, **_custom}
    return [
        {"name": k, "description": v.description}
        for k, v in combined.items()
    ]
