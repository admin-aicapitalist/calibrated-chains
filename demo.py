"""Invoice approval: Clef-Flash decisions sequenced by the Decision monad.

    uv run python demo.py            # monadic pipeline for every document
    uv run python demo.py --naive    # also show the confidence-blind pipeline for contrast
    uv run python demo.py --jev      # Jev (TypeSafe API, key in .env as JEV) instead of local Clef-Flash
"""

from __future__ import annotations

import sys

from clef_monad import Decision, choice, noul, render, score

DOCUMENTS = {
    "clean invoice": (
        "INVOICE #INV-2026-0417\nFrom: Acme Office Supply, 1 Sample Street, Exampletown\nBill to: Example Buyer Ltd\n"
        "Date: 2026-09-14  Due: 2026-10-14 (Net 30)\n"
        "- Ergonomic chairs x4 @ 310.00 = 1240.00\n- Standing desks x2 @ 455.00 = 910.00\n"
        "Subtotal 2150.00  VAT 25% 537.50  TOTAL DUE: 2687.50 EUR\n"
        "Pay to IBAN XX00 0000 0000 0000, ref INV-2026-0417"
    ),
    "redacted scan": (
        "████████ #████-2026-0417\nFrom: ██████████ Supply\nchairs x4, desks x2\n█████ 2687.50 EUR\n████████████████"
    ),
    "already paid": (
        "INVOICE #INV-2026-0417 Acme Office Supply. Total 2687.50 EUR. "
        "STATUS: PAID IN FULL 2026-09-20 — no payment required. Copy for your records."
    ),
}

APPROVE = ("Policy: approve unpaid standard invoices from identifiable vendors with a clear total under 5000 EUR "
           "and payment details. Should this invoice be approved for payment now?")

AMOUNT_SCALE = [
    "Absurd for these goods",
    "Suspicious, far off typical prices",
    "Plausible but on the high or low side",
    "Normal for these goods",
    "Clearly consistent, line items add up",
]


def pipeline(backend, document: str) -> Decision:
    return (
        Decision.pure(document)
        .bind(noul(backend, "is_invoice", "Is this document an invoice?"))
        .bind(choice(backend, "invoice_type", "What type of invoice is this?", {
            "standard": "A regular invoice for delivered goods or services",
            "proforma": "A preliminary bill or estimate sent before delivery",
            "credit_note": "A document reducing an amount owed",
            "recurring": "A subscription or periodic charge",
        }, allowed={"standard", "recurring"}))
        .bind(score(backend, "amount_reasonable", "Is the total amount reasonable for the items listed?", AMOUNT_SCALE))
        .guard("amount_ok", lambda ctx: ctx["amount_reasonable"] >= 2.0, "amount_reasonable >= 2.0")
        .bind(noul(backend, "approve", APPROVE))
        .map("decide", lambda ctx: {"action": "APPROVE", "type": ctx["invoice_type"]})
    )


def naive_pipeline(backend, document: str) -> str:
    """Same questions, argmax at every step, no gating: whatever comes out, ships."""
    asks = {
        "is_invoice": {"type": "noul", "instructions": "Is this document an invoice?"},
        "approve": {"type": "noul", "instructions": APPROVE},
    }
    answers = {name: backend(document, {name: q})[name]["noul"] for name, q in asks.items()}
    action = "APPROVE" if answers["is_invoice"] >= 0.5 and answers["approve"] >= 0.5 else "REJECT"
    return f"naive: is_invoice={answers['is_invoice']:.0%} approve={answers['approve']:.0%} -> {action}"


def main() -> None:
    if "--jev" in sys.argv:
        from jev_backend import JevBackend
        backend = JevBackend(verbose=False)
    else:
        from clef_backend import ClefBackend
        backend = ClefBackend(verbose=False)
    for title, document in DOCUMENTS.items():
        print(f"\n━━ {title} ━━")
        print(render(pipeline(backend, document)))
        if "--naive" in sys.argv:
            print(naive_pipeline(backend, document))


if __name__ == "__main__":
    main()
