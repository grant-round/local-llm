import argparse
import json
import os
import sys
from typing import List

from .agents.job_role_classifier import JobRoleClassifierAgent, DEFAULT_LABELS


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Local Agents CLI")
	sub = parser.add_subparsers(dest="command", required=True)

	# job-role classifier
	cls = sub.add_parser("classify-jobs", help="Classify job role titles/descriptions")
	cls.add_argument("inputs", nargs="*", help="Job titles or descriptions. If none provided, read from stdin lines.")
	cls.add_argument("--mode", choices=["auto", "offline", "llm"], default="auto")
	cls.add_argument("--labels", nargs="*", default=DEFAULT_LABELS, help="Override label set")
	cls.add_argument("--model", default=os.environ.get("OLLAMA_MODEL", "llama3.1:8b"), help="Ollama model name")
	cls.add_argument("--host", default=os.environ.get("OLLAMA_HOST"), help="Ollama host, e.g., http://127.0.0.1:11434")

	return parser.parse_args()


def read_inputs_from_stdin() -> List[str]:
	return [line.strip() for line in sys.stdin if line.strip()]


def cmd_classify_jobs(args: argparse.Namespace) -> None:
	inputs = args.inputs or read_inputs_from_stdin()
	agent = JobRoleClassifierAgent(labels=args.labels, mode=args.mode, ollama_model=args.model, ollama_host=args.host)
	results = agent.run(inputs)
	print(json.dumps(results, indent=2))


def main() -> None:
	args = parse_args()
	if args.command == "classify-jobs":
		cmd_classify_jobs(args)
	else:
		raise SystemExit(2)


if __name__ == "__main__":
	main()