"""Post-hoc recalibration and gate-threshold selection, fitted on dev only.

Platt scaling on the logit of p_invoice: p' = sigmoid(a * logit(p) + b). The dev sample is
enriched with invoices (29.6%) while the natural RVL-CDIP prior is 1/16, so before applying the
calibrator elsewhere the intercept is shifted by the change in prior log-odds.
"""

from __future__ import annotations

import numpy as np

EPS = 1e-6
NATURAL_PRIOR = 1 / 16


def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, EPS, 1 - EPS)
    return np.log(p / (1 - p))


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-z))


def fit_logreg(x: np.ndarray, y: np.ndarray, l2: float = 1e-3) -> np.ndarray:
    """L2-regularised logistic regression by Newton's method; x must include a bias column."""
    w = np.zeros(x.shape[1])
    for _ in range(100):
        q = sigmoid(x @ w)
        grad = x.T @ (q - y) + l2 * w
        hess = (x * (q * (1 - q))[:, None]).T @ x + l2 * np.eye(x.shape[1])
        step = np.linalg.solve(hess, grad)
        w -= step
        if np.abs(step).max() < 1e-9:
            break
    return w


def fit_platt(p: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    a, b = fit_logreg(np.stack([logit(p), np.ones_like(p)], 1), y)
    return float(a), float(b)


def cross_val_logreg(x: np.ndarray, y: np.ndarray, folds: int = 5, seed: int = 0) -> np.ndarray:
    """Out-of-fold probabilities from a stacked logistic regression over several Clef answers."""
    x = np.concatenate([x, np.ones((len(x), 1))], 1)
    order = np.random.default_rng(seed).permutation(len(y))
    out = np.empty(len(y))
    for k in range(folds):
        held = order[k::folds]
        train = np.setdiff1d(order, held)
        out[held] = sigmoid(x[held] @ fit_logreg(x[train], y[train], l2=1.0))
    return out


def apply_platt(p: np.ndarray, a: float, b: float, prior_from: float | None = None,
                prior_to: float | None = None) -> np.ndarray:
    if prior_from is not None and prior_to is not None:
        b = b + float(logit(np.array(prior_to)) - logit(np.array(prior_from)))
    return sigmoid(a * logit(p) + b)


def cross_val_platt(p: np.ndarray, y: np.ndarray, folds: int = 5, seed: int = 0) -> np.ndarray:
    """Out-of-fold recalibrated probabilities, so dev numbers aren't fitted on themselves."""
    order = np.random.default_rng(seed).permutation(len(p))
    out = np.empty_like(p)
    for k in range(folds):
        held = order[k::folds]
        train = np.setdiff1d(order, held)
        out[held] = apply_platt(p[held], *fit_platt(p[train], y[train]))
    return out


def pick_tau(p: np.ndarray, y: np.ndarray, max_silent_rate: float = 0.01) -> float:
    """Smallest tau (max coverage) whose silent-error rate among passed docs is <= target."""
    conf, wrong = np.maximum(p, 1 - p), (p >= 0.5) != y
    for tau in np.round(np.arange(0.5, 1.0, 0.005), 3):
        passed = conf >= tau
        if passed.any() and wrong[passed].mean() <= max_silent_rate:
            return float(tau)
    return 1.0
