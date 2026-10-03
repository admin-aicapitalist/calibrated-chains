import math

from compiler import (Candidate, Compiler, Example, Guard, Map, NeuralStep, ensemble, error_correlation,
                      samples_needed, upper_bound)


def noul_backend(p_by_input):
    """Fake SystemOne backend: p(true) looked up by the request's state."""
    calls = []

    def backend(state, questions):
        (qid,) = questions
        calls.append((state, qid))
        return {qid: {"type": "noul", "noul": p_by_input[state]}}

    backend.calls = calls
    return backend


def plain(name="plain", qid="is_x"):
    return Candidate(name, build=lambda raw: {"state": raw, "questions": {qid: {"type": "noul"}}})


def test_upper_bound_matches_rule_of_three_and_known_values():
    assert math.isclose(upper_bound(0, 29), 1 - 0.05 ** (1 / 29))
    assert abs(upper_bound(0, 3000) - 0.000998) < 2e-5  # rule of three: ~3/n
    assert 0.0035 < upper_bound(1, 1000) < 0.0050       # exact CP value is 0.00473
    assert upper_bound(0, 0) == 1.0
    assert samples_needed(0.001) == 2995


def test_compile_picks_the_formulation_that_passes_most_within_budget():
    # 400 inputs; "good" is confident and right, "bad" is confident and wrong on 10%.
    inputs = [f"doc{i}" for i in range(400)]
    truth = {d: i % 2 == 0 for i, d in enumerate(inputs)}
    good = noul_backend({d: 0.99 if truth[d] else 0.01 for d in inputs})
    bad = noul_backend({d: (0.99 if truth[d] else 0.01) if i % 10 else (0.01 if truth[d] else 0.99)
                        for i, d in enumerate(inputs)})
    step = NeuralStep("is_x", "noul", [Candidate("bad", plain().build, backend=bad),
                                        Candidate("good", plain().build, backend=good)])
    examples = [Example(d, d, {"is_x": truth[d]}) for d in inputs]
    compiled = Compiler([step], backend=good).compile(examples, error_budget=0.01)
    result = compiled.results["is_x"]
    assert result.chosen.name == "good" and result.certified
    assert result.gate.errors == 0 and result.gate.bound <= 0.01
    assert "certified" in compiled.report() and "UNCERTIFIED" not in compiled.report()


def test_small_sample_is_flagged_uncertified_with_needed_size():
    inputs = [f"doc{i}" for i in range(30)]
    backend = noul_backend({d: 0.99 for d in inputs})
    step = NeuralStep("is_x", "noul", [plain()])
    compiled = Compiler([step], backend).compile([Example(d, d, {"is_x": True}) for d in inputs], 0.01)
    assert not compiled.results["is_x"].certified
    assert "needs ≥299 decided" in compiled.report()


def test_budget_is_split_over_neural_steps_only():
    inputs = ["a"]
    backend = noul_backend({"a": 0.99})
    spec = [NeuralStep("s1", "noul", [plain(qid="s1")]), Guard("g", lambda ctx: True),
            NeuralStep("s2", "noul", [plain(qid="s2")]), Map("m", lambda ctx: 1)]
    compiled = Compiler(spec, backend).compile([Example("a", "a", {"s1": True, "s2": True})], 0.02)
    budget = compiled.results["s1"].budget
    assert math.isclose(1 - (1 - budget) ** 2, 0.02)


def test_compiled_chain_runs_with_frozen_gates_and_short_circuits():
    backend = noul_backend({"sure": 0.99, "unsure": 0.6})
    spec = [NeuralStep("is_x", "noul", [plain()]), Map("decide", lambda ctx: "APPROVE")]
    compiled = Compiler(spec, backend).compile([Example(str(i), "sure", {"is_x": True}) for i in range(5)], 0.5)
    tau = compiled.results["is_x"].gate.tau
    assert tau > 0.6
    assert compiled.run("sure").ctx["decide"] == "APPROVE"
    blocked = compiled.run("unsure")
    assert not blocked.ok and [e.status for e in blocked.trace[1:]] == ["failed", "blocked"]


def test_ensemble_averages_members_and_cache_avoids_repeat_calls(tmp_path):
    b1, b2 = noul_backend({"a": 0.9}), noul_backend({"a": 0.5})
    vote = ensemble("vote", Candidate("m1", plain().build, backend=b1), Candidate("m2", plain().build, backend=b2))
    step = NeuralStep("is_x", "noul", [vote])
    cache = tmp_path / "answers.jsonl"
    Compiler([step], b1, cache_path=cache).compile([Example("e", "a", {"is_x": True})], 0.5)
    first_calls = len(b1.calls) + len(b2.calls)
    compiled = Compiler([step], b1, cache_path=cache).compile([Example("e", "a", {"is_x": True})], 0.5)
    assert len(b1.calls) + len(b2.calls) == first_calls  # second compile served from cache
    assert math.isclose(compiled.results["is_x"].gate.n, 1)


def test_error_correlation():
    a = [("x", 0.9, ok) for ok in (True, False, True, False)]
    assert math.isclose(error_correlation(a, a), 1.0)


def test_asymmetric_gates_pass_more_when_one_answer_is_less_reliable():
    # "yes" answers at p=0.85 are always right. "no" answers at confidence 0.90 are wrong 3 times in 7;
    # "no" answers at confidence 0.98 are always right. One symmetric tau must exceed 0.90 to block the
    # noisy no's, which also blocks every yes; separate thresholds keep both the yes's and the sure no's.
    inputs = [f"d{i}" for i in range(1000)]
    truth, p = {}, {}
    for i, d in enumerate(inputs):
        if i < 500:
            truth[d], p[d] = True, 0.85
        elif i % 10 < 3:
            truth[d], p[d] = False, 0.02
        else:
            truth[d], p[d] = (i % 10 < 6), 0.10
    backend = noul_backend(p)
    examples = [Example(d, d, {"is_x": truth[d]}) for d in inputs]
    spec = [NeuralStep("is_x", "noul", [plain()])]
    sym = Compiler(spec, backend).compile(examples, 0.01).results["is_x"]
    asym = Compiler(spec, backend, asymmetric=True).compile(examples, 0.01).results["is_x"]
    # Symmetric: only the 150 sure no's pass; 0 errors in 150 still bounds at ~2%, so it can't certify 1%.
    assert not sym.certified and sym.gate.passed == 150
    assert asym.certified and asym.gate.passed == 650 and asym.gate.errors == 0
    assert asym.gate.tau_for("true") < asym.gate.tau_for("false")
