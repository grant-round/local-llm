# Local Agents with Ollama (LLaMA)

This project provides a lightweight local agent framework using [Ollama](https://ollama.com/) to run LLaMA models on your Mac, plus an example agent that classifies job roles.

## Prerequisites (macOS)
- Install Ollama app and run it once to start the local server.
- Pull a model, e.g.:

```bash
ollama pull llama3.1:8b
```

## Setup (Python)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## CLI Usage
Classify one or more role titles/descriptions:
```bash
python -m app.cli classify-jobs "Senior React Developer" "SRE / DevOps Engineer"
```

Read from stdin (one per line), auto mode (offline keywords first, then LLM if needed):
```bash
printf "%s\n" "React Native Engineer" "Platform Engineer (K8s)" | python -m app.cli classify-jobs --mode auto
```

Force offline-only (no model required):
```bash
python -m app.cli classify-jobs --mode offline "Backend API Engineer (Go/Rust)"
```

Force LLM classification (requires model):
```bash
python -m app.cli classify-jobs --mode llm --model llama3.1:8b "ML Platform Engineer"
```

Override label set:
```bash
python -m app.cli classify-jobs --labels front-end back-end infra other "Kubernetes Platform Engineer"
```

Environment overrides:
- `OLLAMA_HOST`: set custom host, e.g. `http://127.0.0.1:11434`
- `OLLAMA_MODEL`: default model if not passed via `--model`

## Extending with new agents
Create a new module under `app/agents/` implementing a class with a `run(inputs: List[str]) -> List[Dict[str, Any]]` method, then add a subcommand in `app/cli.py` to route to it.
