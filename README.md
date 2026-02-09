# Political Bias Detector

A local Streamlit app that estimates political bias (left, right, or neutral) for pasted text, HTML, or URLs using local LLMs via Ollama.

## Requirements

- **Python 3.10+**
- **Ollama** installed and running locally (https://ollama.com)
- Streamlit and app dependencies from `requirements.txt`

> This project does **not** call external LLM APIs. It runs models locally through Ollama.

## Quick start

```bash
# Clone
git clone https://github.com/yourusername/politicalbias.git
cd politicalbias

# Create environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install Ollama and pull models you want to use.
ollama pull mistral
ollama pull tinyllama
ollama pull deepseek-r1:1.5b
ollama pull qwen2.5:3b
ollama pull phi3.5

# Ensure the Ollama server is running (usually auto-started on install).
ollama serve

# Run tests
pytest tests/

# Run the Streamlit app
streamlit run main.py
```

## How it works

1. The app normalizes input text (or extracts readable text from HTML/URLs).
2. It truncates the text to the configured word limit.
3. It sends the prompt to a local Ollama model and expects a structured JSON response.
4. It renders the bias score, confidence, and model reasoning in the UI.

Latest prompts and raw outputs are written to `<model>_run.log` by default (override with `BIAS_LOG_PATH`).

## Models

The UI lets you select one of the following Ollama model names:

- `mistral`
- `tinyllama`
- `deepseek-r1:1.5b`
- `qwen2.5:3b`
- `phi3.5`

Add additional Ollama models by updating the model list in `app.py` and pulling them with `ollama pull <model>`.

## Notes

- The app uses BeautifulSoup (`beautifulsoup4`) for HTML extraction; no external readability service is required.
- Requirements are listed in `requirements.txt` and include Streamlit, BeautifulSoup, and pytest.
- The TinyLlama and DeepSeek R1 (1.5B) models often struggle to return consistently structured JSON output compared to Mistral, Qwen 2.5, or Phi 3.5.
