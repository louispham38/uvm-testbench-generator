"""Data models for UVM Testbench Generator."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PortDirection(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"


class SignalType(str, Enum):
    LOGIC = "logic"
    WIRE = "wire"
    REG = "reg"


class ProtocolType(str, Enum):
    AXI4 = "axi4"
    AXI4_LITE = "axi4_lite"
    APB = "apb"
    AHB = "ahb"
    SPI = "spi"
    UART = "uart"
    I2C = "i2c"
    CUSTOM = "custom"


class Port(BaseModel):
    name: str = Field(..., description="Signal name")
    direction: PortDirection = PortDirection.INPUT
    width: int = Field(1, ge=1, description="Bit width")
    signal_type: SignalType = SignalType.LOGIC
    description: str = ""


class ProtocolConfig(BaseModel):
    protocol: ProtocolType = ProtocolType.CUSTOM
    data_width: int = Field(32, ge=1)
    addr_width: int = Field(32, ge=1)
    has_burst: bool = False
    has_parity: bool = False
    clock_freq_mhz: float = Field(100.0, gt=0)
    extra_params: dict = Field(default_factory=dict)


class AgentConfig(BaseModel):
    is_active: bool = True
    has_driver: bool = True
    has_monitor: bool = True
    has_sequencer: bool = True
    has_coverage: bool = True


class TestConfig(BaseModel):
    name: str = "base_test"
    description: str = ""
    num_transactions: int = Field(100, ge=1)
    timeout_ns: int = Field(10000, ge=1)
    has_reset_sequence: bool = True


class ComponentSelection(BaseModel):
    """Which UVM components to generate."""
    interface: bool = True
    sequence_item: bool = True
    driver: bool = True
    monitor: bool = True
    sequencer: bool = True
    agent: bool = True
    scoreboard: bool = True
    coverage: bool = True
    env: bool = True
    test: bool = True
    top: bool = True
    package: bool = True
    sequences: bool = True


class ProjectConfig(BaseModel):
    """Top-level configuration for the entire UVM testbench project."""
    project_name: str = Field(..., min_length=1, description="Project / DUT name")
    module_name: str = Field("", description="DUT module name (defaults to project_name)")
    ports: list[Port] = Field(default_factory=list)
    protocol: ProtocolConfig = Field(default_factory=ProtocolConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    tests: list[TestConfig] = Field(
        default_factory=lambda: [TestConfig()],
    )
    components: ComponentSelection = Field(default_factory=ComponentSelection)
    output_dir: str = Field("output", description="Output directory for generated files")

    def effective_module_name(self) -> str:
        return self.module_name or self.project_name
