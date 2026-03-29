"""Vercel serverless entry point for UVM Testbench Generator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from uvmgen.app import app
