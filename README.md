# Political Bias Detector

A local Streamlit app that analyzes political bias (left, right, or neutral) in pasted text or HTML using local LLMs through Ollama.

## Features

- Paste raw text or HTML and extract readable article text with BeautifulSoup.
- Classify political bias via Ollama-backed models.
- View structured JSON output, confidence, and rationale.
- Writes the latest prompt/output to `<model>_run.log` (override with `BIAS_LOG_PATH`).

## Setup

```bash
# Clone
git clone https://github.com/yourusername/politicalbias.git
cd politicalbias

# Create environment
mamba create -n polibias --file requirements.txt
mamba activate polibias

# Install Ollama from https://ollama.com and pull the models you want to run.
ollama pull mistral
ollama pull tinyllama
ollama pull deepseek-r1:1.5b

# Run tests
pytest tests/

# Run app
streamlit run main.py
```

## Models

The UI lets you select one of the following Ollama model names:

- `mistral`
- `tinyllama`
- `deepseek-r1:1.5b`

You can add additional Ollama models by updating the model list in `app.py` and pulling them with `ollama pull <model>`.

## Notes

- The app uses BeautifulSoup (`beautifulsoup4`) for HTML extraction; no external readability service is required.
- Requirements are listed in `requirements.txt` and include Streamlit, BeautifulSoup, and pytest.
