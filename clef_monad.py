"""Neuro-symbolic decisions: Clef (System One) answers wrapped in a Decision monad.

Clef is the neural part: one forward pass turns (state, typed question) into calibrated
probabilities. The monad is the symbolic part: it sequences decisions, carries an audit
trace (Writer), and short-circuits on low confidence or failed guards (Either).

    Decision.pure(doc)
        .bind(noul("is_invoice", "Is this document an invoice?"))
        .bind(choice("invoice_type", "What type of invoice?", {...}))
        .guard("amount_ok", lambda ctx: ctx["amount_reasonable"] >= 5.0)
        .map("decide", lambda ctx: {"action": "APPROVE"})

Once a step fails, every later bind/guard/map is recorded but never executed, so a shaky
"yes" can't quietly turn into an approval further down.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Callable

# A backend answers a SystemOne request body: {"state", "questions"} -> {question_id: answer}.
Backend = Callable[[Any, dict[str, Any]], dict[str, Any]]

HIGH, MEDIUM = 0.85, 0.70  # confidence bands; below MEDIUM a step blocks


def band(confidence: float) -> str:
    return "high" if confidence >= HIGH else "medium" if confidence >= MEDIUM else "low"


@dataclass(frozen=True)
class Entry:
    op: str  # pure | bind | guard | map
    name: str
    status: str  # ok | failed | blocked | skipped
    detail: str = ""
    confidence: float | None = None


@dataclass(frozen=True)
class Decision:
    """Either[error, ctx] x Writer[trace]. ``ctx`` is the input plus every typed answer so far."""

    ctx: dict[str, Any] | None
    trace: tuple[Entry, ...] = ()
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    @staticmethod
    def pure(state: Any) -> Decision:
        return Decision({"state": state}, (Entry("pure", "input", "ok"),))

    @staticmethod
    def fail(error: str, entry: Entry) -> Decision:
        return Decision(None, (entry,), error)

    def _short_circuit(self, op: str, name: str) -> Decision:
        # The first step after a failure is the one that got blocked; the rest are skipped.
        status = "skipped" if self.trace[-1].status in ("blocked", "skipped") else "blocked"
        return replace(self, trace=self.trace + (Entry(op, name, status),))

    def bind(self, step: Step) -> Decision:
        if not self.ok:
            return self._short_circuit("bind", step.name)
        result = step.run(self.ctx)
        return replace(result, trace=self.trace + result.trace)

    def guard(self, name: str, predicate: Callable[[dict[str, Any]], bool], why: str = "") -> Decision:
        if not self.ok:
            return self._short_circuit("guard", name)
        if predicate(self.ctx):
            return replace(self, trace=self.trace + (Entry("guard", name, "ok", why),))
        return Decision(None, self.trace + (Entry("guard", name, "failed", why),), f"Guard failed: {name}")

    def map(self, name: str, fn: Callable[[dict[str, Any]], Any]) -> Decision:
        if not self.ok:
            return self._short_circuit("map", name)
        value = fn(self.ctx)
        return replace(self, ctx={**self.ctx, name: value}, trace=self.trace + (Entry("map", name, "ok", str(value)),))


@dataclass(frozen=True)
class Step:
    """A Kleisli arrow ctx -> Decision, built from one Clef question."""

    name: str
    run: Callable[[dict[str, Any]], Decision]


def _ask(backend: Backend, ctx: dict[str, Any], question_id: str, question: dict[str, Any]) -> dict[str, Any]:
    return backend(ctx["state"], {question_id: question})[question_id]


def _gate(ctx: dict[str, Any], name: str, value: Any, confidence: float, detail: str, min_confidence: float) -> Decision:
    if confidence < min_confidence:
        entry = Entry("bind", name, "failed", detail, confidence)
        return Decision.fail(f"Confidence too low ({band(confidence)}, {confidence:.0%}) at {name}", entry)
    return Decision({**ctx, name: value}, (Entry("bind", name, "ok", detail, confidence),))


def noul(backend: Backend, name: str, instructions: str, expect: bool = True, min_confidence: float = MEDIUM) -> Step:
    """Yes/no question. Blocks on low confidence, and on a confident answer other than ``expect``."""

    def run(ctx: dict[str, Any]) -> Decision:
        p_true = _ask(backend, ctx, name, {"type": "noul", "instructions": instructions})["noul"]
        value = p_true >= 0.5
        confidence = p_true if value else 1 - p_true
        result = _gate(ctx, name, value, confidence, f"{instructions} -> {value} (p_true={p_true:.0%})", min_confidence)
        if result.ok and value != expect:
            return Decision(None, (replace(result.trace[0], status="failed"),), f"{name} answered {value}, expected {expect}")
        return result

    return Step(name, run)


def choice(backend: Backend, name: str, instructions: str, criteria: dict[str, str],
           allowed: set[str] | None = None, min_confidence: float = MEDIUM) -> Step:
    def run(ctx: dict[str, Any]) -> Decision:
        answer = _ask(backend, ctx, name, {"type": "choice", "instructions": instructions, "criteria": criteria})
        picked, confidence = answer["choice"], answer["confidence"]
        result = _gate(ctx, name, picked, confidence, f"{instructions} -> {picked}", min_confidence)
        if result.ok and allowed is not None and picked not in allowed:
            return Decision(None, (replace(result.trace[0], status="failed"),), f"{name}={picked} not in {sorted(allowed)}")
        return result

    return Step(name, run)


def score(backend: Backend, name: str, instructions: str, criteria: list[str], min_confidence: float = 0.0) -> Step:
    """Ordered scale; the value is the expected score. Probability mass spreads across nearby
    levels on a fine scale, so the gate is off by default and guards check the value instead."""

    def run(ctx: dict[str, Any]) -> Decision:
        answer = _ask(backend, ctx, name, {"type": "score", "instructions": instructions, "criteria": criteria})
        value, confidence = answer["score"], answer["confidence"]
        result = _gate(ctx, name, value, confidence, f"{instructions} -> {value:.1f}/{len(criteria) - 1}", min_confidence)
        # The top level's share of an ordered scale isn't a useful confidence; the value is what guards read.
        return replace(result, trace=(replace(result.trace[0], confidence=None),)) if result.ok else result

    return Step(name, run)


# --- rendering -------------------------------------------------------------------------

ICONS = {"ok": "✅", "failed": "⚠️ ", "blocked": "🛑 BLOCKED", "skipped": "⏭️  SKIPPED"}


def render(decision: Decision) -> str:
    lines = []
    for depth, entry in enumerate(decision.trace[1:]):
        conf = f" {entry.confidence:.0%} [{band(entry.confidence)}]" if entry.confidence is not None else ""
        detail = f"  {entry.detail}" if entry.detail and entry.status in ("ok", "failed") else ""
        lines.append(f"{'  ' * depth}{entry.op} {entry.name}:{conf} {ICONS[entry.status]}{detail}")
    lines.append(f"=> {decision.ctx.get('decide') if decision.ok else 'Error: ' + decision.error}")
    return "\n".join(lines)
