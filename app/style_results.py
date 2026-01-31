from __future__ import annotations

from typing import Any

import streamlit as st


def _bias_color(bias: str) -> str:
    normalized = bias.strip().lower()
    if normalized == "left":
        return "#d1495b"
    if normalized == "right":
        return "#1d4ed8"
    return "#6b7280"


def render_bias_result(result: dict[str, Any]) -> None:
    bias = str(result.get("bias", "neutral"))
    confidence = result.get("confidence", "N/A")
    rationale = result.get("rationale", "No rationale provided.")
    color = _bias_color(bias)

    st.markdown(
        f"""
        <div style="padding: 1rem; border-radius: 0.75rem; border: 1px solid {color};">
            <div style="font-size: 1.5rem; font-weight: 700; color: {color};">
                Bias: {bias.title()}
            </div>
            <div style="margin-top: 0.25rem; color: {color};">
                Confidence: {confidence}
            </div>
            <div style="margin-top: 0.75rem;">
                {rationale}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
