"""Jev (TypeSafe AI) backend: same SystemOne request/response contract as Clef, served over HTTP."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

URL = "https://api.typesafe.ai/v1/systemone"
ENV_FILE = Path(__file__).parent / ".env"


def _api_key() -> str:
    if key := os.environ.get("JEV"):
        return key
    for line in ENV_FILE.read_text().splitlines():
        name, _, value = line.partition("=")
        if name.strip() == "JEV":
            return value.strip().strip('"').strip("'")
    raise RuntimeError("JEV api key not found in environment or .env")


class JevBackend:
    def __init__(self, model: str = "jev-latest", url: str = URL, verbose: bool = True):
        self.model, self.url, self.verbose = model, url, verbose
        self.key = _api_key()

    def __call__(self, state: Any, questions: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps({"model": self.model, "state": state, "questions": questions}).encode()
        request = urllib.request.Request(self.url, body, {
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        })
        start = time.time()
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"Jev HTTP {error.code}: {error.read().decode()[:500]}") from None
        if self.verbose:
            print(f"[jev] {payload['model']} {', '.join(questions)}: {payload['usage']}, {time.time() - start:.1f}s",
                  file=sys.stderr)
        return payload["answers"]


if __name__ == "__main__":
    print(JevBackend()(
        "Our checkout started returning errors and orders are blocked.",
        {
            "department": {"type": "choice", "instructions": "Which team should handle the message?",
                           "criteria": {"billing": "Payments or invoices", "technical": "Bugs or outages"}},
            "urgency": {"type": "score", "criteria": ["Can wait", "This week", "Today"]},
            "outage": {"type": "noul", "instructions": "Is a service down?"},
        },
    ))
