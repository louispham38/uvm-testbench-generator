"""FastAPI application for UVM Testbench Generator."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from uvmgen.core.generator import UVMGenerator
from uvmgen.core.models import (
    ComponentSelection,
    Port,
    ProjectConfig,
    ProtocolConfig,
    ProtocolType,
    TestConfig,
)
from uvmgen.protocols.registry import list_protocols

_STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="UVM Testbench Generator",
    version="1.0.0",
    description="Generate production-ready UVM testbench code from a simple configuration.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── API routes ────────────────────────────────────────────────────────────────

@app.get("/api/protocols")
def api_list_protocols():
    """Return available protocol definitions."""
    return {"protocols": list_protocols()}


@app.get("/api/protocol/{name}/ports")
def api_protocol_ports(name: str, data_width: int = 32, addr_width: int = 32):
    """Return the default ports for a given protocol."""
    from uvmgen.protocols.registry import get_protocol

    proto = get_protocol(name)
    ports = proto.get_ports(data_width=data_width, addr_width=addr_width)
    return {"ports": [p.model_dump() for p in ports]}


@app.post("/api/generate")
def api_generate(config: ProjectConfig):
    """Generate UVM files and return them as JSON."""
    try:
        gen = UVMGenerator(config)
        files = gen.generate_all()
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/generate/zip")
def api_generate_zip(config: ProjectConfig):
    """Generate UVM files and return as a downloadable ZIP."""
    try:
        gen = UVMGenerator(config)
        zip_bytes = gen.generate_zip()
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={config.effective_module_name()}_uvm_tb.zip"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/generate/preview")
def api_preview(config: ProjectConfig, component: str = "interface"):
    """Preview a single generated component."""
    try:
        gen = UVMGenerator(config)
        files = gen.generate_all()
        name = config.effective_module_name()
        key_map = {
            "interface": f"{name}_if.sv",
            "sequence_item": f"{name}_seq_item.sv",
            "sequences": f"{name}_sequences.sv",
            "driver": f"{name}_driver.sv",
            "monitor": f"{name}_monitor.sv",
            "sequencer": f"{name}_sequencer.sv",
            "agent": f"{name}_agent.sv",
            "scoreboard": f"{name}_scoreboard.sv",
            "coverage": f"{name}_coverage.sv",
            "env": f"{name}_env.sv",
            "test": f"{name}_test.sv",
            "top": f"{name}_tb_top.sv",
            "package": f"{name}_pkg.sv",
        }
        fname = key_map.get(component)
        if not fname or fname not in files:
            raise HTTPException(status_code=404, detail=f"Component '{component}' not found")
        return {"filename": fname, "content": files[fname]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Serve frontend ────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return FileResponse(str(_STATIC_DIR / "index.html"))


app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
