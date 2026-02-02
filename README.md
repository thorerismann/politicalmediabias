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
ollama pull qwen2.5:3b
ollama pull phi3.5

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
- `qwen2.5:3b`
- `phi3.5`

Recent additions include `qwen2.5:3b` and `phi3.5` for improved structured responses.

You can add additional Ollama models by updating the model list in `app.py` and pulling them with `ollama pull <model>`.

## Notes

- The app uses BeautifulSoup (`beautifulsoup4`) for HTML extraction; no external readability service is required.
- Requirements are listed in `requirements.txt` and include Streamlit, BeautifulSoup, and pytest.
- The TinyLlama and DeepSeek R1 (1.5B) models often struggle to return consistently structured JSON output compared to Mistral, Qwen 2.5, or Phi 3.5.

## Future plans

- Add a headline bias tracker to compare headline framing against full-article analysis.
- Explore additional models comparable to Mistral for higher-quality structured JSON output.
- Add a lede bias tracker to analyze opening paragraphs separately from the body.
- Add subject-matter bias tracking (e.g., foreign policy vs. economic coverage).
