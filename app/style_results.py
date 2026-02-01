"""Streamlit helpers for rendering bias analysis results."""

from __future__ import annotations

from typing import Any

import streamlit as st

from app.bias_detector import parse_bias_score


def _bias_label(score: float | None) -> str:
    """Derive a qualitative label from a numeric bias score.

    Args:
        score: Bias score between -1 and 1.

    Returns:
        A qualitative label for display.
    """
    if score is None:
        return "unknown"
    if score <= -0.2:
        return "left"
    if score >= 0.2:
        return "right"
    return "neutral"


def _bias_color(score: float | None) -> str:
    """Select a display color for a bias classification.

    Args:
        score: Bias score between -1 and 1.

    Returns:
        A hex color string for UI styling.
    """
    label = _bias_label(score)
    if label == "left":
        return "#d1495b"
    if label == "right":
        return "#1d4ed8"
    return "#6b7280"


def render_bias_result(result: dict[str, Any]) -> None:
    """Render the bias result card in Streamlit.

    Args:
        result: Parsed model response including bias, confidence, and reasoning.
    """
    bias_score = parse_bias_score(result.get("bias"))
    bias_label = _bias_label(bias_score)
    confidence = result.get("confidence", "N/A")
    rationale = result.get("reasoning") or result.get("rationale") or "No reasoning provided."
    color = _bias_color(bias_score)
    bias_display = (
        f"{bias_score:.2f} ({bias_label.title()})"
        if bias_score is not None
        else bias_label.title()
    )

    st.markdown(
        f"""
        <div style="padding: 1rem; border-radius: 0.75rem; border: 1px solid {color};">
            <div style="font-size: 1.5rem; font-weight: 700; color: {color};">
                Bias: {bias_display}
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
