"""Streamlit entry point for the Political Media Bias Analyzer app."""

from __future__ import annotations

import importlib.util
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType

app_path: Path = Path(__file__).with_name("app.py")
spec: ModuleSpec | None = importlib.util.spec_from_file_location("bias_app_ui", app_path)
module: ModuleType = importlib.util.module_from_spec(spec) if spec else ModuleType("bias_app_ui")
if spec and spec.loader:
    spec.loader.exec_module(module)

module.render_app()
