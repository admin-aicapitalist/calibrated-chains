# system_one_clef

Neural System One meets a symbolic monad.

- **Neural:** [Clef-Flash](https://huggingface.co/Cloudflare/clef-flash) (Qwen3.5-9B backbone + joint schema head)
  answers typed questions (`noul` / `choice` / `score`) with calibrated probabilities in one forward pass.
- **Symbolic:** `Decision` in `clef_monad.py` is Either (ok / blocked) x Writer (audit trace).
  Each Clef question is a Kleisli arrow; `bind` gates on confidence, `guard` on rules, `map` builds the result.
  The first failure short-circuits the chain: downstream steps are recorded as BLOCKED / SKIPPED and never run.

## Run

```bash
uv sync
hf download Cloudflare/clef-flash --local-dir models/clef-flash   # ~18 GB
uv run python demo.py --naive   # CPU works: ~14 GB RAM, ~6 s per decision
uv run python demo.py --jev --naive   # same pipeline on Jev (TypeSafe API, key as JEV in .env)
uv run pytest                   # monad tests, fake backend, no model needed
```

Confidence bands: high >= 85%, medium >= 70%, low blocks.
