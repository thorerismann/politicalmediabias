"""Streamlit entry point for the Political Media Bias Analyzer app."""

from __future__ import annotations

import importlib.util
from pathlib import Path

app_path = Path(__file__).with_name("app.py")
spec = importlib.util.spec_from_file_location("bias_app_ui", app_path)
module = importlib.util.module_from_spec(spec)
if spec and spec.loader:
    spec.loader.exec_module(module)

module.render_app()
