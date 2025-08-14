import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

try:
	import ollama
except Exception as import_error:
	ollama = None  # type: ignore


class LLMNotAvailableError(RuntimeError):
	pass


class OllamaLLMClient:
	"""Thin wrapper around the Ollama Python client for chat completions.

	- Validates the server is reachable
	- Optionally ensures a model is pulled
	- Supports JSON-only responses when format='json' is provided
	"""

	def __init__(self, model: str, host: Optional[str] = None, request_timeout_s: float = 60.0) -> None:
		self.model = model
		self.host = host or os.environ.get("OLLAMA_HOST")
		self.request_timeout_s = request_timeout_s

		if ollama is None:
			raise RuntimeError(
				"The 'ollama' Python package is not installed. Install dependencies with 'pip install -r requirements.txt'."
			)

		if self.host:
			# Allow overriding the Ollama host (e.g., http://127.0.0.1:11434)
			ollama.set_host(self.host)

	def _ensure_server(self) -> None:
		start_time = time.time()
		last_error: Optional[Exception] = None
		# Probe the server by calling list
		for _ in range(3):
			try:
				_ = ollama.list()
				return
			except Exception as exc:
				last_error = exc
				time.sleep(0.5)

		raise LLMNotAvailableError(
			f"Could not reach Ollama server. Ensure it's running locally (e.g., 'ollama serve' or the macOS app). Last error: {last_error}"
		)

	def ensure_model(self, auto_pull: bool = False) -> None:
		self._ensure_server()
		try:
			models = ollama.list().get("models", [])
			if any(m.get("model") == self.model or m.get("name") == self.model for m in models):
				return
		except Exception:
			# If listing fails, attempt to pull if requested
			pass

		if not auto_pull:
			raise RuntimeError(
				f"Model '{self.model}' is not available locally. Run 'ollama pull {self.model}' or pass auto_pull=True."
			)

		# Pull the model; this may take a while depending on size
		ollama.pull(self.model)

	def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, json_mode: bool = False, extra_options: Optional[Dict[str, Any]] = None) -> str:
		self._ensure_server()
		messages: List[Dict[str, str]] = [
			{"role": "system", "content": system_prompt},
			{"role": "user", "content": user_prompt},
		]
		options = {"temperature": temperature}
		if extra_options:
			options.update(extra_options)

		kwargs: Dict[str, Any] = {"model": self.model, "messages": messages, "options": options}
		if json_mode:
			kwargs["format"] = "json"

		response = ollama.chat(**kwargs)
		content = response.get("message", {}).get("content", "")
		return content

	@staticmethod
	def coerce_json(text: str) -> Any:
		"""Attempt to parse JSON from a model string. Tries exact parse first, then extracts the first JSON object/array."""
		try:
			return json.loads(text)
		except Exception:
			pass

		# Try to locate the first JSON object or array
		start_obj = text.find("{")
		start_arr = text.find("[")
		starts = [s for s in [start_obj, start_arr] if s != -1]
		if not starts:
			raise ValueError("Model did not return JSON. Enable json_mode or adjust the prompt.")
		start = min(starts)
		substr = text[start:]
		# Heuristic: find last closing brace/bracket
		end_obj = substr.rfind("}")
		end_arr = substr.rfind("]")
		ends = [e for e in [end_obj, end_arr] if e != -1]
		if not ends:
			raise ValueError("Could not extract JSON from model output.")
		end = max(ends)
		candidate = substr[: end + 1]
		return json.loads(candidate)