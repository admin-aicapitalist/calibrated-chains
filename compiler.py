"""Neuro-symbolic calibration compiler: turn a chain spec + labeled examples into a chain with measured,
budgeted error rates.

    spec = [
        NeuralStep("is_invoice", "noul", candidates=[Candidate("bare", bare), Candidate("criteria", crit)]),
        Guard("amount_ok", lambda ctx: ctx["amount"] >= 2.0),
        NeuralStep("approve", "noul", candidates=[...]),
        Map("decide", lambda ctx: {"action": "APPROVE"}),
    ]
    compiled = Compiler(spec, backend).compile(calibration_set, error_budget=0.01)
    print(compiled.report())
    compiled.run(doc)                          # a Decision; gates baked in
    print(compiled.verify(held_out_set))       # frozen gates on unseen data

Per neural step the compiler tries every candidate formulation, and for each one picks the lowest gate
tau whose 95% upper confidence bound on the silent-error rate (wrong AND passed the gate) fits the step's
share of the chain's budget. The candidate that passes the most decisions wins. Steps that can't be
certified with the data at hand are still compiled, flagged UNCERTIFIED, with the sample size that would
be needed. Symbolic steps are exact and consume no budget.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from clef_monad import Backend, Decision, Entry, Step, band

Request = dict[str, Any]  # SystemOne request body: {"state": ..., "questions": {...}}
TAUS = [round(0.5 + i * 0.005, 3) for i in range(100)]  # 0.500 ... 0.995


# --- chain spec --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Candidate:
    """One formulation of a neural step: raw input -> SystemOne request.

    ``question_id`` is the question in the request that carries the decision. ``readout`` maps that
    answer to (probability of each option) for steps whose question type differs from the step's
    (e.g. a 16-way choice read out as an is-invoice yes/no). ``backend`` overrides the compiler's
    backend, which is how Clef and Jev (or any mix) compete or vote on one step."""

    name: str
    build: Callable[[Any], Request]
    question_id: str | None = None
    readout: Callable[[dict], dict[str, float]] | None = None
    backend: Backend | None = None
    members: tuple[Candidate, ...] = ()  # non-empty = ensemble: probabilities averaged over members


def ensemble(name: str, *members: Candidate) -> Candidate:
    return Candidate(name, build=members[0].build, members=members)


@dataclass(frozen=True)
class NeuralStep:
    name: str
    kind: str  # "noul" or "choice"
    candidates: tuple[Candidate, ...] | list[Candidate]
    expect: Any = True  # noul: the answer that continues the chain
    allowed: frozenset[str] | None = None  # choice: answers that continue the chain


@dataclass(frozen=True)
class Guard:
    name: str
    predicate: Callable[[dict[str, Any]], bool]
    why: str = ""


@dataclass(frozen=True)
class Map:
    name: str
    fn: Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class Example:
    """A labeled input. ``labels`` maps step name -> correct answer; steps without a label skip it."""

    id: str
    input: Any
    labels: dict[str, Any]


# --- answers: probabilities per option, cached on disk -------------------------------------------------

def _probabilities(answer: dict) -> dict[str, float]:
    if answer["type"] == "noul":
        return {"true": answer["noul"], "false": 1 - answer["noul"]}
    return dict(answer["probabilities"])


class AnswerCache:
    """JSONL cache: (step, candidate, example, request hash) -> option probabilities."""

    def __init__(self, path: Path | None):
        self.path, self.data = path, {}
        if path and path.exists():
            for line in path.open():
                row = json.loads(line)
                self.data[row["key"]] = row["probs"]

    @staticmethod
    def key(step: str, candidate: str, example_id: str, request: Request) -> str:
        digest = hashlib.sha1(json.dumps(request, sort_keys=True, default=str).encode()).hexdigest()[:12]
        return f"{step}|{candidate}|{example_id}|{digest}"

    def get(self, key: str) -> dict[str, float] | None:
        return self.data.get(key)

    def put(self, key: str, probs: dict[str, float]) -> None:
        self.data[key] = probs
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a") as sink:
                sink.write(json.dumps({"key": key, "probs": probs}) + "\n")


def ask(candidate: Candidate, step: NeuralStep, raw: Any, backend: Backend,
        cache: AnswerCache | None = None, example_id: str | None = None) -> dict[str, float]:
    """Option probabilities for one input. Ensembles average their members' probabilities."""
    if candidate.members:
        parts = [ask(m, step, raw, backend, cache, example_id) for m in candidate.members]
        return {option: sum(p[option] for p in parts) / len(parts) for option in parts[0]}
    request = candidate.build(raw)
    qid = candidate.question_id or step.name
    key = AnswerCache.key(step.name, candidate.name, example_id, request) if cache and example_id else None
    if key and (hit := cache.get(key)) is not None:
        return hit
    answer = (candidate.backend or backend)(request["state"], {qid: request["questions"][qid]})[qid]
    probs = candidate.readout(answer) if candidate.readout else _probabilities(answer)
    if key:
        cache.put(key, probs)
    return probs


# --- statistics ----------------------------------------------------------------------------------------

def upper_bound(errors: int, n: int, confidence: float = 0.95) -> float:
    """One-sided Clopper-Pearson upper bound on an error rate (k errors in n)."""
    if n == 0:
        return 1.0
    alpha = 1 - confidence
    if errors == 0:
        return 1 - alpha ** (1 / n)
    if errors >= n:
        return 1.0

    def cdf(p: float) -> float:  # P(X <= errors) for Binomial(n, p), in log space for stability
        total = 0.0
        for i in range(errors + 1):
            total += math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
                              + i * math.log(p) + (n - i) * math.log1p(-p))
        return total

    lo, hi = errors / n, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if cdf(mid) > alpha else (lo, mid)
    return hi


def samples_needed(epsilon: float, confidence: float = 0.95) -> int:
    """Gated decisions with zero errors needed to certify silent-error rate <= epsilon."""
    return math.ceil(math.log(1 - confidence) / math.log(1 - epsilon))


@dataclass
class GateStats:
    tau: float
    n: int  # labeled examples
    passed: int
    errors: int  # wrong AND passed
    bound: float  # upper confidence bound on errors / passed

    @property
    def coverage(self) -> float:
        return self.passed / self.n if self.n else 0.0

    @property
    def rate(self) -> float:
        return self.errors / self.passed if self.passed else 0.0


def gate_stats(preds: list[tuple[str, float, bool]], tau: float, confidence: float) -> GateStats:
    """preds: (predicted option, its probability, correct?)."""
    passed = [ok for _, conf, ok in preds if conf >= tau]
    errors = sum(1 for ok in passed if not ok)
    return GateStats(tau, len(preds), len(passed), errors, upper_bound(errors, len(passed), confidence))


def predictions(probs: list[dict[str, float]], truths: list[Any]) -> list[tuple[str, float, bool]]:
    out = []
    for p, truth in zip(probs, truths):
        option = max(p, key=p.__getitem__)
        out.append((option, p[option], option == _option(truth)))
    return out


def _option(truth: Any) -> str:
    return ("true" if truth else "false") if isinstance(truth, bool) else str(truth)


def error_correlation(a: list[tuple[str, float, bool]], b: list[tuple[str, float, bool]]) -> float:
    """Phi coefficient between two candidates' error indicators (thresholded, no gate)."""
    x = [not ok for _, _, ok in a]
    y = [not ok for _, _, ok in b]
    n = len(x)
    sx, sy, sxy = sum(x), sum(y), sum(1 for i, j in zip(x, y) if i and j)
    den = math.sqrt(sx * (n - sx) * sy * (n - sy))
    return (n * sxy - sx * sy) / den if den else float("nan")


# --- compiler --------------------------------------------------------------------------------------------

@dataclass
class StepResult:
    step: NeuralStep
    budget: float
    chosen: Candidate
    gate: GateStats
    certified: bool
    table: list[tuple[str, GateStats, bool]]  # per candidate: best gate, certified?
    correlations: dict[tuple[str, str], float] = field(default_factory=dict)


class Compiler:
    def __init__(self, spec: list[NeuralStep | Guard | Map], backend: Backend,
                 cache_path: Path | None = None, confidence: float = 0.95):
        self.spec, self.backend, self.confidence = spec, backend, confidence
        self.cache = AnswerCache(cache_path)

    def neural_steps(self) -> list[NeuralStep]:
        return [s for s in self.spec if isinstance(s, NeuralStep)]

    def compile(self, examples: list[Example], error_budget: float) -> CompiledChain:
        steps = self.neural_steps()
        per_step = 1 - (1 - error_budget) ** (1 / max(len(steps), 1))
        results = {s.name: self._calibrate(s, examples, per_step) for s in steps}
        return CompiledChain(self.spec, results, self.backend, error_budget, self.confidence)

    def _calibrate(self, step: NeuralStep, examples: list[Example], budget: float) -> StepResult:
        labeled = [e for e in examples if step.name in e.labels]
        truths = [e.labels[step.name] for e in labeled]
        table, preds_by = [], {}
        for candidate in step.candidates:
            probs = [ask(candidate, step, e.input, self.backend, self.cache, e.id) for e in labeled]
            preds = preds_by[candidate.name] = predictions(probs, truths)
            gates = [gate_stats(preds, tau, self.confidence) for tau in TAUS]
            ok = [g for g in gates if g.passed and g.bound <= budget]
            # Among gates passing the same decisions, take the highest tau: a lower one would also pass
            # confidence levels the calibration data never showed, which nothing here has certified.
            best = max(ok, key=lambda g: (g.passed, g.tau)) if ok else min(gates, key=lambda g: (g.bound, -g.passed))
            table.append((candidate.name, best, bool(ok)))
        # Certified candidates first, then most decisions passed, then lowest bound.
        name, gate, certified = max(table, key=lambda row: (row[2], row[1].passed if row[2] else -row[1].bound))
        chosen = next(c for c in step.candidates if c.name == name)
        names = list(preds_by)
        correlations = {(a, b): error_correlation(preds_by[a], preds_by[b])
                        for i, a in enumerate(names) for b in names[i + 1:]}
        return StepResult(step, budget, chosen, gate, certified, table, correlations)


@dataclass
class CompiledChain:
    spec: list[NeuralStep | Guard | Map]
    results: dict[str, StepResult]
    backend: Backend
    error_budget: float
    confidence: float

    def run(self, raw: Any) -> Decision:
        decision = Decision.pure(raw)
        for step in self.spec:
            if isinstance(step, Guard):
                decision = decision.guard(step.name, step.predicate, step.why)
            elif isinstance(step, Map):
                decision = decision.map(step.name, step.fn)
            else:
                decision = decision.bind(self._step(step))
        return decision

    def _step(self, step: NeuralStep) -> Step:
        result = self.results[step.name]

        def run(ctx: dict[str, Any]) -> Decision:
            probs = ask(result.chosen, step, ctx["state"], self.backend)
            option = max(probs, key=probs.__getitem__)
            confidence = probs[option]
            value = (option == "true") if step.kind == "noul" else option
            detail = f"{result.chosen.name}: {option} (p={confidence:.2f}, gate {result.gate.tau:.3f})"
            if confidence < result.gate.tau:
                return Decision.fail(f"Confidence too low ({band(confidence)}, {confidence:.0%}) at {step.name}",
                                     Entry("bind", step.name, "failed", detail, confidence))
            if (step.kind == "noul" and value != step.expect) or (step.allowed and value not in step.allowed):
                return Decision.fail(f"{step.name} answered {value}",
                                     Entry("bind", step.name, "failed", detail, confidence))
            return Decision({**ctx, step.name: value}, (Entry("bind", step.name, "ok", detail, confidence),))

        return Step(step.name, run)

    def chain_bound(self) -> float:
        return 1 - math.prod(1 - r.gate.bound for r in self.results.values())

    def certified(self) -> bool:
        return all(r.certified for r in self.results.values())

    def report(self) -> str:
        lines = [f"# Calibration report", "",
                 f"Chain error budget **{self.error_budget:.2%}** silent errors at {self.confidence:.0%} confidence, "
                 f"split over {len(self.results)} neural step(s) "
                 f"({next(iter(self.results.values())).budget:.3%} each). Symbolic steps are exact.", "",
                 "| step | type | formulation | gate τ | decided | silent errors | rate | 95% bound | budget | status |",
                 "|---|---|---|---|---|---|---|---|---|---|"]
        for step in self.spec:
            if isinstance(step, (Guard, Map)):
                lines.append(f"| {step.name} | symbolic | exact rule | | | 0 | 0 | 0 | 0 | exact |")
                continue
            r = self.results[step.name]
            g = r.gate
            status = "certified" if r.certified else f"UNCERTIFIED: needs ≥{samples_needed(r.budget, self.confidence):,} decided, 0 errors"
            lines.append(f"| {step.name} | neural · {step.kind} | {r.chosen.name} | {g.tau:.3f} | {g.passed}/{g.n} "
                         f"({g.coverage:.0%}) | {g.errors} | {g.rate:.2%} | {g.bound:.2%} | {r.budget:.2%} | {status} |")
        lines += ["", f"**Whole chain:** silent-error bound {self.chain_bound():.2%} "
                      f"({'within' if self.chain_bound() <= self.error_budget else 'over'} the {self.error_budget:.2%} budget). "
                      f"Chain {'CERTIFIED' if self.certified() else 'NOT certified'}.", ""]
        for r in self.results.values():
            lines += [f"## {r.step.name}: formulations tried", "",
                      "| formulation | gate τ | decided | silent errors | 95% bound | fits budget |", "|---|---|---|---|---|---|"]
            lines += [f"| {name}{' ← chosen' if name == r.chosen.name else ''} | {g.tau:.3f} | {g.passed}/{g.n} | {g.errors} | "
                      f"{g.bound:.2%} | {'yes' if ok else 'no'} |" for name, g, ok in r.table]
            if r.correlations:
                lines += ["", "Error correlation between formulations (φ; near 1 means they fail on the same inputs, "
                              "so voting between them buys little):", ""]
                lines += [f"- {a} / {b}: {phi:.2f}" for (a, b), phi in r.correlations.items()]
            lines.append("")
        lines += ["Gates were chosen on the calibration set, so these numbers are optimistic until `verify()` "
                  "runs on held-out data."]
        return "\n".join(lines) + "\n"

    def verify(self, examples: list[Example], cache: AnswerCache | None = None) -> str:
        """Frozen gates on held-out examples: does each step stay within its budget?"""
        lines = ["# Verification on held-out data", "",
                 "| step | formulation | gate τ | decided | silent errors | rate | 95% bound | budget | holds |",
                 "|---|---|---|---|---|---|---|---|---|"]
        bounds = []
        for name, r in self.results.items():
            labeled = [e for e in examples if name in e.labels]
            probs = [ask(r.chosen, r.step, e.input, self.backend, cache, e.id) for e in labeled]
            g = gate_stats(predictions(probs, [e.labels[name] for e in labeled]), r.gate.tau, self.confidence)
            bounds.append(g.bound)
            lines.append(f"| {name} | {r.chosen.name} | {g.tau:.3f} | {g.passed}/{g.n} ({g.coverage:.0%}) | {g.errors} | "
                         f"{g.rate:.2%} | {g.bound:.2%} | {r.budget:.2%} | {'yes' if g.bound <= r.budget else 'NO'} |")
        chain = 1 - math.prod(1 - b for b in bounds)
        lines += ["", f"**Whole chain on held-out data:** silent-error bound {chain:.2%} vs budget {self.error_budget:.2%}."]
        return "\n".join(lines) + "\n"

    def to_json(self) -> dict[str, Any]:
        """The compiled artifact: what production needs to load alongside the spec."""
        return {"error_budget": self.error_budget, "confidence": self.confidence, "steps": {
            name: {"formulation": r.chosen.name, "tau": r.gate.tau, "decided": r.gate.passed, "n": r.gate.n,
                   "errors": r.gate.errors, "bound": r.gate.bound, "budget": r.budget, "certified": r.certified}
            for name, r in self.results.items()}}
