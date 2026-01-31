"""Streamlit entry point for the Political Media Bias Analyzer app."""

import os
import textwrap

import streamlit as st

from app.bias_detector import analyze_with_mistral, prepare_bias_input, prepare_bias_prompt
from app.style_results import render_bias_result

st.set_page_config(page_title="Political Media Bias Analyzer", page_icon="📰", layout="centered")

st.title("Political Media Bias Analyzer")
st.markdown(
    "Paste a news article, statement, or HTML snippet below to estimate political bias."
)

tab_entry, tab_info = st.tabs(["Text / MTL Entry", "More Information"])

with tab_entry:
    st.subheader("Analyze text")
    user_input = st.text_area(
        "Text or HTML",
        placeholder="Paste article text, a transcript, or HTML content here.",
        height=220,
    )
    max_words = st.slider("Maximum words sent to the model", 50, 400, 200, step=25)
    analyze_button = st.button("Analyze bias", type="primary", use_container_width=True)

    if analyze_button:
        if not user_input.strip():
            st.warning("Please enter text or HTML before running the analysis.")
        else:
            with st.spinner("Analyzing bias with Mistral..."):
                try:
                    prompt, metadata = prepare_bias_input(user_input, max_words=max_words)
                    if metadata.get("extracted"):
                        if metadata.get("source") == "url":
                            st.write("Extracted main article text from the provided URL.")
                        else:
                            st.write("Extracted main article text from the provided HTML.")
                    st.write(f"Words cut to meet the limit: {metadata.get('words_cut', 0)}")
                    result = analyze_with_mistral(
                        user_input,
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
                    log_path = os.getenv("BIAS_LOG_PATH", "mistral_run.log")
                    st.caption(f"Latest run log written to `{log_path}`.")

with tab_info:
    st.subheader("How it works")
    st.markdown(
        textwrap.dedent(
            """
            This app sends the provided text to Mistral's `mistral-small-latest` model.
            The model is asked to classify political bias as **left**, **right**, or **neutral**
            and return a small JSON response with a confidence score and short rationale.
            """
        ).strip()
    )
    st.markdown("**Prompt template**")
    st.code(prepare_bias_prompt("Your text here...", max_words=25))
    st.markdown(
        "The input is truncated to the selected maximum word count before being sent to the API."
    )
