from typing import Any, Dict, List, Optional

from .base import Agent
from ..llm_client import OllamaLLMClient


DEFAULT_LABELS = [
	"front-end",
	"back-end",
	"full-stack",
	"mobile",
	"data-science",
	"ml-engineering",
	"devops",
	"security",
	"qa",
	"product-management",
	"design",
	"other",
]


_KEYWORDS = {
	"front-end": ["frontend", "front end", "react", "vue", "angular", "javascript", "typescript", "css", "html", "ui", "web developer"],
	"back-end": ["backend", "back end", "api", "microservice", "java", ".net", "c#", "node.js", "nodejs", "python", "django", "flask", "go", "rust", "spring"],
	"full-stack": ["fullstack", "full stack", "mern", "mevn", "mean", "ruby on rails", "rails"],
	"mobile": ["ios", "android", "swift", "kotlin", "react native", "flutter"],
	"data-science": ["data scientist", "data science", "analysis", "analyst", "pandas", "numpy", "statistics", "notebook"],
	"ml-engineering": ["ml engineer", "machine learning engineer", "mlops", "model deployment", "pytorch", "tensorflow", "llm", "inference"],
	"devops": ["devops", "sre", "site reliability", "kubernetes", "terraform", "ansible", "ci/cd", "docker"],
	"security": ["security", "appsec", "infosec", "penetration", "pentest", "iam", "threat"],
	"qa": ["qa", "quality", "test", "automation", "selenium", "cypress"],
	"product-management": ["product manager", "pm", "product management", "roadmap", "prioritization"],
	"design": ["designer", "ui/ux", "ux", "figma", "sketch"],
}


class JobRoleClassifierAgent:
	def __init__(
		self,
		labels: Optional[List[str]] = None,
		mode: str = "auto",  # 'offline' | 'llm' | 'auto'
		ollama_model: str = "llama3.1:8b",
		ollama_host: Optional[str] = None,
	) -> None:
		self.labels = labels or DEFAULT_LABELS
		self.mode = mode
		self.ollama_model = ollama_model
		self.ollama_host = ollama_host
		self._llm: Optional[OllamaLLMClient] = None

	def _ensure_llm(self) -> OllamaLLMClient:
		if self._llm is None:
			self._llm = OllamaLLMClient(model=self.ollama_model, host=self.ollama_host)
			# Do not auto-pull by default to avoid long waits silently; can be toggled by caller if needed
			try:
				self._llm.ensure_model(auto_pull=False)
			except Exception:
				# Fallback: we will operate in offline mode if model missing
				pass
		return self._llm

	def _classify_offline(self, text: str) -> str:
		lower = text.lower()
		score: Dict[str, int] = {label: 0 for label in self.labels}
		for label, keywords in _KEYWORDS.items():
			if label not in score:
				continue
			for kw in keywords:
				if kw in lower:
					score[label] += 1
		# Choose the best label or 'other'
		best_label = max(score.items(), key=lambda kv: kv[1])[0] if score else "other"
		if score.get(best_label, 0) == 0:
			return "other"
		return best_label

	def _classify_llm(self, text: str) -> str:
		llm = self._ensure_llm()
		try:
			system = (
				"You are a precise classifier. Respond with a single JSON object: {\"label\": string}. "
				+ f"The label must be one of: {', '.join(self.labels)}."
			)
			user = f"Classify the following role title/description into one label. Text: {text}"
			resp = llm.chat(system_prompt=system, user_prompt=user, temperature=0.0, json_mode=True)
			obj = llm.coerce_json(resp)
			label = str(obj.get("label", "other")).strip().lower()
			if label not in self.labels:
				return "other"
			return label
		except Exception:
			# Fallback to offline if LLM fails
			return self._classify_offline(text)

	def run(self, inputs: List[str]) -> List[Dict[str, Any]]:
		results: List[Dict[str, Any]] = []
		for text in inputs:
			label = None
			if self.mode == "offline":
				label = self._classify_offline(text)
			elif self.mode == "llm":
				label = self._classify_llm(text)
			else:  # auto
				# Try offline first for speed/cost, fall back to LLM if 'other'
				label = self._classify_offline(text)
				if label == "other":
					label = self._classify_llm(text)

			results.append({"input": text, "label": label})
		return results