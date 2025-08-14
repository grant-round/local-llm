from typing import Any, Dict, List, Protocol


class Agent(Protocol):
	def run(self, inputs: List[str]) -> List[Dict[str, Any]]:  # pragma: no cover - protocol definition
		...  # noqa: E701