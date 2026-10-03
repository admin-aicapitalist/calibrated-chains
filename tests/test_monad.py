from clef_monad import Decision, Step, choice, noul, score


def fake(answers):
    """Backend returning canned SystemOne answers, recording which questions were asked."""
    asked = []

    def backend(state, questions):
        (qid,) = questions
        asked.append(qid)
        return {qid: answers[qid]}

    backend.asked = asked
    return backend


def test_left_identity():
    step = Step("f", lambda ctx: Decision({**ctx, "f": 1}))
    assert Decision.pure("x").bind(step).ctx == step.run({"state": "x"}).ctx


def test_right_identity():
    d = Decision.pure("x")
    assert d.bind(Step("unit", lambda ctx: Decision(ctx))).ctx == d.ctx


def test_happy_path_runs_every_step():
    b = fake({"is_invoice": {"noul": 0.97}, "kind": {"choice": "standard", "confidence": 0.92},
              "amount": {"score": 7.5, "confidence": 0.4}})
    d = (Decision.pure("doc").bind(noul(b, "is_invoice", "?")).bind(choice(b, "kind", "?", {"standard": ""}))
         .bind(score(b, "amount", "?", ["0", "1"])).guard("amount_ok", lambda c: c["amount"] >= 5.0)
         .map("decide", lambda c: "APPROVE"))
    assert d.ok and d.ctx["decide"] == "APPROVE"
    assert b.asked == ["is_invoice", "kind", "amount"]


def test_low_confidence_blocks_and_never_calls_downstream():
    b = fake({"is_invoice": {"noul": 0.55}})
    d = (Decision.pure("doc").bind(noul(b, "is_invoice", "?")).bind(choice(b, "kind", "?", {"a": ""}))
         .bind(noul(b, "approve", "?")).map("decide", lambda c: "APPROVE"))
    assert not d.ok and "low" in d.error
    assert [e.status for e in d.trace[1:]] == ["failed", "blocked", "skipped", "skipped"]
    assert b.asked == ["is_invoice"]


def test_confident_wrong_answer_and_guard_fail():
    b = fake({"approve": {"noul": 0.02}})
    assert "expected True" in Decision.pure("doc").bind(noul(b, "approve", "?")).error
    assert Decision.pure("doc").guard("never", lambda c: False).error == "Guard failed: never"
