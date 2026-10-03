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
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from clef_monad import Backend, Decision, Entry, Step, band

Request = dict[str, Any]  # SystemOne request body: {"state": ..., "questions": {...}}
TAUS = [round(0.5 + i * 0.005, 3) for i in range(100)]  # 0.500 ... 0.995
PAIR_TAUS = [round(0.5 + i * 0.01, 2) for i in range(50)]  # coarser grid for per-answer (yes/no) gates


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
    # Which wrong answers the error budget covers. "all": any confident wrong answer. "continue": only wrong
    # answers that continue the chain (they flow on toward an action); a confident wrong stop is reported
    # as a wrong stop (missed automation) but doesn't consume budget, and the gate maximises correct continues.
    budget_on: str = "all"
    # With budget_on="continue": bound on the miss rate (share of should-continue inputs confidently stopped,
    # e.g. real invoices silently rejected). None = stops are unconstrained and
    # the gate maximises correct continues, then minimises wrong stops (blocking no's sends them to review).
    # A number = both budgets must hold and the gate maximises everything decided without review.
    stop_budget: float | None = None

    def continue_options(self) -> set[str] | None:
        if self.kind == "noul":
            return {_option(self.expect)}
        return set(self.allowed) if self.allowed else None


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



def _stable(value: Any) -> str:
    """JSON fallback for request contents: media hash by content (a PIL image's repr is its address)."""
    if hasattr(value, "tobytes"):
        return "media:" + hashlib.sha1(value.tobytes()).hexdigest()
    return str(value)


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
        digest = hashlib.sha1(json.dumps(request, sort_keys=True, default=_stable).encode()).hexdigest()[:12]
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

@lru_cache(maxsize=None)
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
    taus: dict[str, float]  # per predicted option; "*" applies to every option
    n: int  # labeled examples
    passed: int
    errors: int  # wrong AND passed
    bound: float  # upper confidence bound on the (prior-weighted) silent-error rate
    w_coverage: float | None = None  # share passed, weighted to the target prior (None = unweighted)
    w_rate: float | None = None  # silent-error rate among passed, weighted to the target prior
    ess: float | None = None  # effective sample size of the passed decisions under the weights
    useful: int = 0  # correct decisions inside the budget's scope
    wrong_stops: int = 0  # confident wrong answers outside the scope (budget_on="continue")
    stop_rate: float = 0.0  # miss rate: wrong stops / examples whose true answer continues the chain
    stop_bound: float = 0.0  # upper bound on the miss rate

    @property
    def coverage(self) -> float:
        if self.w_coverage is not None:
            return self.w_coverage
        return self.passed / self.n if self.n else 0.0

    @property
    def rate(self) -> float:
        if self.w_rate is not None:
            return self.w_rate
        return self.errors / self.passed if self.passed else 0.0

    def tau_for(self, option: str) -> float:
        return self.taus.get(option, self.taus.get("*", 1.0))

    @property
    def tau(self) -> float:
        """Display value: the single threshold, or the strictest one."""
        return max(self.taus.values())

    def describe(self) -> str:
        if "*" in self.taus:
            return f"{self.taus['*']:.3f}"
        return " / ".join(f"{o} ≥{t:.2f}" for o, t in self.taus.items())


Pred = tuple[str, float, bool, float, str]  # (predicted option, its probability, correct?, weight, true option)


def _rate_bound(items: list[tuple[bool, float]], confidence: float,
                budget: float | None) -> tuple[int, float, float | None, float]:
    """(raw errors, rate, effective size or None if unweighted, upper bound) for (correct?, weight) items.
    Weighted items use the Kish effective sample size, rounded conservatively (errors up, size down).
    The exact bound is skipped (1.0) when the observed rate alone exceeds ``budget``."""
    errors = sum(1 for ok, _ in items if not ok)
    if not items:
        return 0, 0.0, None, 1.0
    if all(w == 1.0 for _, w in items):
        rate, ess = errors / len(items), None
        bound = 1.0 if budget is not None and rate > budget else upper_bound(errors, len(items), confidence)
        return errors, rate, ess, bound
    w_sum = sum(w for _, w in items)
    rate = sum(w for ok, w in items if not ok) / w_sum
    ess = w_sum ** 2 / sum(w * w for _, w in items)
    if budget is not None and rate > budget:
        return errors, rate, ess, 1.0
    return errors, rate, ess, upper_bound(math.ceil(rate * ess - 1e-9), math.floor(ess + 1e-9), confidence)


def gate_stats(preds: list[Pred], taus: dict[str, float] | float, confidence: float,
               budget: float | None = None, scope: set[str] | None = None,
               stop_budget: float | None = None) -> GateStats:
    """A decision passes if its probability clears the threshold for the option it predicts.

    ``scope`` (options that continue the chain) splits passed decisions: the main rate and bound cover
    in-scope decisions (wrong continues), and stop_rate / stop_bound cover the rest (wrong stops). Weighted
    preds (reweighted to a target prior) give weighted rates and coverage with effective-size bounds."""
    taus = {"*": taus} if isinstance(taus, (int, float)) else taus
    probe = GateStats(taus, 0, 0, 0, 0)
    all_passed = [(option, ok, w) for option, conf, ok, w, _ in preds if conf >= probe.tau_for(option)]
    in_scope = [(ok, w) for option, ok, w in all_passed if scope is None or option in scope]
    errors, rate, ess, bound = _rate_bound(in_scope, confidence, budget)
    # Wrong stops are measured as a miss rate: the share of examples whose true answer continues the chain
    # that were confidently stopped. Class-conditional, so it doesn't depend on the class mix.
    should_continue = sum(1 for *_, truth in preds if scope is not None and truth in scope)
    wrong_stops = sum(1 for option, ok, _ in all_passed if scope is not None and option not in scope and not ok)
    stop_rate = wrong_stops / should_continue if should_continue else 0.0
    if scope is None or not should_continue:
        stop_bound = 0.0
    elif stop_budget is not None and stop_rate > stop_budget:
        stop_bound = 1.0
    else:
        stop_bound = upper_bound(wrong_stops, should_continue, confidence)
    weighted = not all(p[3] == 1.0 for p in preds)
    total = sum(p[3] for p in preds)
    return GateStats(taus, len(preds), len(all_passed), errors, bound,
                     w_coverage=sum(w for *_, w in all_passed) / total if weighted and total else None,
                     w_rate=rate if weighted else None, ess=ess,
                     useful=len(in_scope) - errors, wrong_stops=wrong_stops,
                     stop_rate=stop_rate, stop_bound=stop_bound)


def predictions(probs: list[dict[str, float]], truths: list[Any], weights: list[float] | None = None) -> list[Pred]:
    out = []
    for i, (p, truth) in enumerate(zip(probs, truths)):
        option = max(p, key=p.__getitem__)
        out.append((option, p[option], option == _option(truth), weights[i] if weights else 1.0, _option(truth)))
    return out


def prior_weights(truths: list[Any], prior: dict[Any, float] | None) -> list[float] | None:
    """Importance weights that reweight the labeled sample to a target label distribution."""
    if not prior:
        return None
    counts = {}
    for t in truths:
        counts[_option(t)] = counts.get(_option(t), 0) + 1
    target = {_option(k): v for k, v in prior.items()}
    return [target.get(_option(t), 0.0) / (counts[_option(t)] / len(truths)) for t in truths]


def _option(truth: Any) -> str:
    return ("true" if truth else "false") if isinstance(truth, bool) else str(truth)


def error_correlation(a: list[Pred], b: list[Pred]) -> float:
    """Phi coefficient between two candidates' error indicators (thresholded, no gate, unweighted)."""
    x = [not p[2] for p in a]
    y = [not p[2] for p in b]
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
    """``asymmetric=True`` lets yes/no steps gate "yes" and "no" at different thresholds, for models whose
    two answers aren't equally trustworthy."""

    def __init__(self, spec: list[NeuralStep | Guard | Map], backend: Backend,
                 cache_path: Path | None = None, confidence: float = 0.95, asymmetric: bool = False):
        self.spec, self.backend, self.confidence, self.asymmetric = spec, backend, confidence, asymmetric
        self.cache = AnswerCache(cache_path)

    def neural_steps(self) -> list[NeuralStep]:
        return [s for s in self.spec if isinstance(s, NeuralStep)]

    def compile(self, examples: list[Example], error_budget: float,
                priors: dict[str, dict[Any, float]] | None = None) -> CompiledChain:
        """``priors`` maps step name -> production label distribution (e.g. {"is_invoice": {True: 0.06,
        False: 0.94}}); calibration examples are reweighted to it, so the certified rate is the one
        production will see rather than the calibration sample's mix."""
        steps = self.neural_steps()
        per_step = 1 - (1 - error_budget) ** (1 / max(len(steps), 1))
        priors = priors or {}
        results = {s.name: self._calibrate(s, examples, per_step, priors.get(s.name)) for s in steps}
        return CompiledChain(self.spec, results, self.backend, error_budget, self.confidence, priors)

    def _calibrate(self, step: NeuralStep, examples: list[Example], budget: float,
                   prior: dict[Any, float] | None = None) -> StepResult:
        labeled = [e for e in examples if step.name in e.labels]
        truths = [e.labels[step.name] for e in labeled]
        weights = prior_weights(truths, prior)
        table, preds_by = [], {}
        for candidate in step.candidates:
            probs = [ask(candidate, step, e.input, self.backend, self.cache, e.id) for e in labeled]
            preds = preds_by[candidate.name] = predictions(probs, truths, weights)
            scope = step.continue_options() if step.budget_on == "continue" else None
            stop_budget = step.stop_budget if scope else None
            if self.asymmetric and step.kind == "noul":
                gates = [gate_stats(preds, {"true": ty, "false": tn}, self.confidence, budget, scope, stop_budget)
                         for ty in PAIR_TAUS for tn in PAIR_TAUS]
            else:
                gates = [gate_stats(preds, tau, self.confidence, None, scope, stop_budget) for tau in TAUS]
            ok = [g for g in gates if g.useful and g.bound <= budget
                  and (stop_budget is None or g.stop_bound <= stop_budget)]
            if not ok and any(g.bound == 1.0 and g.passed for g in gates):  # fill skipped bounds for the report
                gates = [g if g.bound < 1.0 or not g.passed else gate_stats(preds, g.taus, self.confidence, None, scope)
                         for g in gates]
            # Objective: with a stop budget, everything decided without review; otherwise correct in-scope
            # decisions, then fewest wrong stops. Ties go to the strictest gate: a looser one would also pass
            # confidence levels the calibration data never showed, which nothing here has certified.
            if scope and stop_budget is not None:
                objective = lambda g: (g.passed - g.errors - g.wrong_stops, sum(g.taus.values()))
            else:
                objective = lambda g: (g.useful, -g.wrong_stops, sum(g.taus.values()))
            # Nothing certifiable: show the gate closest to certification among those that respect the stop
            # budget (if any do), so the report never recommends a gate that silently drops what it must keep.
            stop_ok = [g for g in gates if stop_budget is None or g.stop_bound <= stop_budget] or gates
            best = max(ok, key=objective) if ok else min(stop_ok, key=lambda g: (g.bound, -g.useful))
            table.append((candidate.name, best, bool(ok)))
        # Certified candidates first, then most correct in-scope decisions, then lowest bound.
        name, gate, certified = max(table, key=lambda row: (row[2], row[1].useful if row[2] else -row[1].bound))
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
    priors: dict[str, dict[Any, float]] = field(default_factory=dict)

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
            tau = result.gate.tau_for(option)
            detail = f"{result.chosen.name}: {option} (p={confidence:.2f}, gate {tau:.3f})"
            if confidence < tau:
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
                 *([f"Rates and coverage are reweighted to the production label mix "
                    f"({'; '.join(f'{k}: ' + ', '.join(f'{v}={p:.0%}' for v, p in d.items()) for k, d in self.priors.items())}); "
                    f"bounds use the effective sample size of the decided examples (ESS).", ""] if self.priors else []),
                 "Silent errors are confident wrong answers within each step's budget scope; for steps budgeted "
                 "on `continue`, that means wrong answers that let the chain continue, while confident wrong stops "
                 "are counted separately as missed automation.", "",
                 "| step | type | formulation | gate τ | decided | correct in scope | silent errors | rate | 95% bound | budget | wrong stops | status |",
                 "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for step in self.spec:
            if isinstance(step, (Guard, Map)):
                lines.append(f"| {step.name} | symbolic | exact rule | | | | 0 | 0 | 0 | 0 | | exact |")
                continue
            r = self.results[step.name]
            g = r.gate
            unit = "continued (accepted) decisions" if step.budget_on == "continue" else "decided"
            status = "certified" if r.certified else f"UNCERTIFIED: needs ≥{samples_needed(r.budget, self.confidence):,} {unit}, 0 errors"
            if g.ess is not None:
                status += f" (ESS {g.ess:.0f})"
            if step.budget_on == "continue":
                stop_note = f"; missed {g.stop_rate:.1%} of should-continue, bound {g.stop_bound:.1%}"
                status += stop_note + (f" vs {step.stop_budget:.0%}" if step.stop_budget is not None else "")
            scope = f" (on {step.budget_on})" if step.budget_on != "all" else ""
            lines.append(f"| {step.name} | neural · {step.kind}{scope} | {r.chosen.name} | {g.describe()} | {g.passed}/{g.n} "
                         f"({g.coverage:.0%}) | {g.useful} | {g.errors} | {g.rate:.2%} | {g.bound:.2%} | {r.budget:.2%} | "
                         f"{g.wrong_stops} | {status} |")
        lines += ["", f"**Whole chain:** silent-error bound {self.chain_bound():.2%} "
                      f"({'within' if self.chain_bound() <= self.error_budget else 'over'} the {self.error_budget:.2%} budget). "
                      f"Chain {'CERTIFIED' if self.certified() else 'NOT certified'}.", ""]
        for r in self.results.values():
            lines += [f"## {r.step.name}: formulations tried", "",
                      "| formulation | gate τ | decided | correct in scope | silent errors | 95% bound | wrong stops | fits budget |",
                      "|---|---|---|---|---|---|---|---|"]
            lines += [f"| {name}{' ← chosen' if name == r.chosen.name else ''} | {g.describe()} | {g.passed}/{g.n} | {g.useful} | "
                      f"{g.errors} | {g.bound:.2%} | {g.wrong_stops} | {'yes' if ok else 'no'} |" for name, g, ok in r.table]
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
            truths = [e.labels[name] for e in labeled]
            scope = r.step.continue_options() if r.step.budget_on == "continue" else None
            g = gate_stats(predictions(probs, truths, prior_weights(truths, self.priors.get(name))),
                           r.gate.taus, self.confidence, None, scope)
            bounds.append(g.bound)
            lines.append(f"| {name} | {r.chosen.name} | {g.describe()} | {g.passed}/{g.n} ({g.coverage:.0%}) | {g.errors} | "
                         f"{g.rate:.2%} | {g.bound:.2%} | {r.budget:.2%} | {'yes' if g.bound <= r.budget else 'NO'} |")
        chain = 1 - math.prod(1 - b for b in bounds)
        lines += ["", f"**Whole chain on held-out data:** silent-error bound {chain:.2%} vs budget {self.error_budget:.2%}."]
        return "\n".join(lines) + "\n"

    def to_json(self) -> dict[str, Any]:
        """The compiled artifact: what production needs to load alongside the spec."""
        return {"error_budget": self.error_budget, "confidence": self.confidence, "steps": {
            name: {"formulation": r.chosen.name, "gate": r.gate.taus, "decided": r.gate.passed, "n": r.gate.n,
                   "errors": r.gate.errors, "bound": r.gate.bound, "budget": r.budget, "certified": r.certified}
            for name, r in self.results.items()}}
