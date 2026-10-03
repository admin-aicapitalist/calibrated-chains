"""Run a variant over a sample with local Clef-Flash; append raw logits + probabilities to a resumable JSONL.

    uv run python -m experiments.run v0_baseline dev
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import torch

from clef_backend import MODEL_DIR
from experiments.data import image, sample
from experiments.variants import VARIANTS
from joint_schema_model import collate_records, encode_record, load_release_model

RUNS = Path(__file__).parent / "runs"


def run_path(variant: str, sample_name: str) -> Path:
    return RUNS / f"{variant}__{sample_name}.jsonl"


def main(variant: str, sample_name: str) -> None:
    out = run_path(variant, sample_name)
    done = {json.loads(line)["doc_id"] for line in out.open()} if out.exists() else set()
    docs = sample(sample_name)
    # Reuse this variant's results for the same docs from other samples (e.g. dev -> dev10).
    reused = []
    for other in RUNS.glob(f"{variant}__*.jsonl"):
        if other != out:
            reused += [line for line in other.open() if (doc_id := json.loads(line)["doc_id"]) not in done
                       and doc_id in set(docs.doc_id) and not done.add(doc_id)]
    if reused:
        with out.open("a") as sink:
            sink.writelines(reused)
    todo = docs[~docs.doc_id.isin(done)]
    print(f"{variant} on {sample_name}: {len(done)} done, {len(todo)} to go", flush=True)
    if todo.empty:
        return
    model, processor = load_release_model(MODEL_DIR, device="cpu")
    build, cpu, start = VARIANTS[variant], torch.device("cpu"), time.time()
    with out.open("a") as sink, torch.inference_mode():
        for n, doc in enumerate(todo.itertuples(), 1):
            t = time.time()
            record = build(doc.text, image(doc.doc_id)) if getattr(build, "needs_image", False) else build(doc.text)
            encoded = encode_record(processor.tokenizer, record, processor=processor)
            logits = model(collate_records([encoded], processor.tokenizer.pad_token_id, cpu))[0]
            answers = {}
            for question, question_logits in zip(encoded.questions, logits):
                raw = question_logits.float().tolist()
                answers[question.question_id] = {
                    "options": list(question.option_ids),
                    "logits": [round(x, 5) for x in raw],
                    "probs": [round(x, 6) for x in question_logits.float().softmax(-1).tolist()],
                }
            sink.write(json.dumps({"doc_id": doc.doc_id, "category": doc.category, "tokens": len(encoded.input_ids),
                                   "secs": round(time.time() - t, 2), "answers": answers}) + "\n")
            sink.flush()
            if n % 25 == 0 or n == len(todo):
                rate = (time.time() - start) / n
                print(f"  {n}/{len(todo)}  {rate:.1f}s/doc  eta {rate * (len(todo) - n) / 60:.0f} min", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:3])
