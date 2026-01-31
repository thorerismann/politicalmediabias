# Political Bias Detector

A local Streamlit app that analyzes political bias (left, right, or neutral) in pasted text or HTML using a local LLM via Ollama.

## Features

- Paste raw text or HTML
- Extracts main article text using Readability
- Classifies political bias via LLM (Ollama)
- Clean output + optional structured logic

## Setup

```bash
# Clone
git clone https://github.com/yourusername/politicalbias.git
cd politicalbias

# Create environment
mamba create -n polibias --file requirements.txt
mamba activate polibias

# Run tests
pytest tests/

# Run app
streamlit run main.py
