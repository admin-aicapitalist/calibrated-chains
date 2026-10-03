"""Local Clef-Flash backend: loads the release once and answers SystemOne requests on CPU."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import torch

MODEL_DIR = Path(__file__).parent / "models" / "clef-flash"
sys.path.insert(0, str(MODEL_DIR))
from joint_schema_model import load_release_model, systemone  # noqa: E402


class ClefBackend:
    def __init__(self, model_dir: Path = MODEL_DIR, device: str = "cpu", verbose: bool = True):
        torch.set_num_threads(torch.get_num_threads())
        start = time.time()
        self.model, self.processor = load_release_model(model_dir, device=device, dtype=torch.bfloat16)
        self.verbose = verbose
        if verbose:
            print(f"[clef] loaded in {time.time() - start:.0f}s on {device}", file=sys.stderr)

    def __call__(self, state: Any, questions: dict[str, Any]) -> dict[str, Any]:
        start = time.time()
        response = systemone(self.model, self.processor, {"model": "clef-flash", "state": state, "questions": questions})
        if self.verbose:
            tokens = response["usage"]["input_tokens"]
            print(f"[clef] {', '.join(questions)}: {tokens} tok, {time.time() - start:.1f}s", file=sys.stderr)
        return response["answers"]


if __name__ == "__main__":
    backend = ClefBackend()
    print(backend(
        "Our checkout started returning errors and orders are blocked.",
        {
            "department": {"type": "choice", "instructions": "Which team should handle the message?",
                           "criteria": {"billing": "Payments or invoices", "technical": "Bugs or outages"}},
            "urgency": {"type": "score", "criteria": ["Can wait", "This week", "Today"]},
            "outage": {"type": "noul", "instructions": "Is a service down?"},
        },
    ))
