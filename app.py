"""Streamlit UI for the Political Media Bias Analyzer app."""

from __future__ import annotations

import os
import textwrap

import streamlit as st

from app.bias_detector import (
    analyze_with_model,
    prepare_bias_input,
    prepare_bias_prompt,
)
from app.style_results import render_bias_result

DEFAULT_PROMPT_TEMPLATE = (
    "You are a media bias analyst. Classify the political bias of the text as "
    "left, right, or neutral. Respond ONLY with a JSON object using keys "
    '"bias", "confidence", and "rationale". The rationale should be 1-3 sentences.'
    "\n\nText:\n\"\"\"\n{text}\n\"\"\""
)


def render_app() -> None:
    """Render the Streamlit UI."""
    st.set_page_config(page_title="Political Media Bias Analyzer", page_icon="📰", layout="centered")

    st.title("Political Media Bias Analyzer")
    st.markdown(
        "Paste a news article, statement, or HTML snippet below to estimate political bias."
    )

    with st.sidebar:
        st.header("Model & Prompt Settings")
        max_words = st.slider("Maximum words sent to the model", 50, 400, 200, step=25)
        model_name = st.radio(
            "Model choice",
            options=["mistral", "tinyllama"],
            index=0,
            horizontal=True,
        )
        prompt_template = st.text_area(
            "Custom prompt template",
            value=DEFAULT_PROMPT_TEMPLATE,
            height=200,
            help="Include {text} where the article text should be inserted.",
        )

    tab_text, tab_link, tab_info = st.tabs(["Text Entry", "HTML Entry", "More Information"])

    with tab_text:
        st.subheader("Analyze text")
        user_input_text = st.text_area(
            "Text",
            placeholder="Paste text here.",
            height=220,
            key="text_input",
        )
        analyze_text_button = st.button(
            "Analyze bias",
            type="primary",
            use_container_width=True,
            key="analyze_text_button",
        )

        if analyze_text_button:
            if not user_input_text.strip():
                st.warning("Please enter text or HTML before running the analysis.")
            else:
                with st.spinner(f"Analyzing bias with {model_name}..."):
                    try:
                        prompt, metadata = prepare_bias_input(
                            user_input_text,
                            max_words=max_words,
                            prompt_template=prompt_template,
                        )
                        if metadata.get("extracted"):
                            if metadata.get("source") == "url":
                                st.write("Extracted main article text from the provided URL.")
                            else:
                                st.write("Extracted main article text from the provided HTML.")
                        st.write(f"Words cut to meet the limit: {metadata.get('words_cut', 0)}")
                        result = analyze_with_model(
                            user_input_text,
                            model_name=model_name,
                            max_words=max_words,
                            prepared_prompt=prompt,
                        )
                        st.write(result)
                    except ValueError as exc:
                        st.error(str(exc))
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Analysis failed: {exc}")
                    else:
                        render_bias_result(result)
                        rationale = result.get("rationale")
                        confidence = result.get("confidence")
                        if rationale:
                            st.markdown("**Model rationale**")
                            st.write(rationale)
                        if confidence is not None:
                            st.markdown(f"**Confidence:** {confidence}")
                        if "raw_output" in result:
                            with st.expander("Raw model output"):
                                st.code(result.get("raw_output", ""))
                        log_path = os.getenv("BIAS_LOG_PATH", f"{model_name}_run.log")
                        st.caption(f"Latest run log written to `{log_path}`.")

    with tab_link:
        st.subheader("Analyze text")
        user_input_link = st.text_area(
            "link",
            placeholder="Paste HTML here.",
            height=220,
            key="link",
        )
        analyze_link_button = st.button(
            "Analyze bias",
            type="primary",
            use_container_width=True,
            key="analize_link_bias",
        )

        if analyze_link_button:
            st.write("link coming soon")

    with tab_info:
        st.subheader("How it works")
        st.markdown(
            textwrap.dedent(
                f"""
                This app sends the provided text to a local Ollama model (currently
                `{model_name}`).
                The model is asked to classify political bias as **left**, **right**, or **neutral**
                and return a small JSON response with a confidence score and short rationale.
                """
            ).strip()
        )
        st.markdown("**Prompt template**")
        st.code(prepare_bias_prompt("Your text here...", max_words=25, prompt_template=prompt_template))
        st.markdown(
            "The input is truncated to the selected maximum word count before being sent to the API."
        )


if __name__ == "__main__":
    render_app()
