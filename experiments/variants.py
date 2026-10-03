"""Question/state variants. Each maps an OCR text to a Clef record; all questions go in one forward pass."""

from __future__ import annotations

from typing import Any, Callable

from experiments.data import CLASSES

Variant = Callable[[str], dict[str, Any]]
VARIANTS: dict[str, Variant] = {}


def variant(fn: Variant) -> Variant:
    VARIANTS[fn.__name__] = fn
    return fn


@variant
def v0_baseline(text: str) -> dict[str, Any]:
    """The demo's question, verbatim, on raw OCR text."""
    return {"state": text, "questions": {"is_invoice": {"type": "noul", "instructions": "Is this document an invoice?"}}}


FRAMING = ("Tesseract OCR of a scanned paper business document from a 1980s-90s corporate archive. "
           "Expect misspellings, merged or garbled tokens, and lost layout.")

INVOICE_CRITERIA = {
    "true": "An invoice or bill from a vendor requesting payment: typically has an invoice number or date, "
            "bill-to / remit-to details, line items or charges, amounts, a total due, or payment terms.",
    "false": "Any other document: letters, memos, emails, forms, questionnaires, budgets, financial reports, "
             "purchase orders, specifications, articles, resumes, ads, file folders, handwritten notes.",
}

CLASS_CRITERIA = {
    "letter": "A business letter with salutation and signature",
    "form": "A form with labeled fields to fill in",
    "email": "An email printout with From/To/Subject headers",
    "handwritten": "Mostly handwritten notes",
    "advertisement": "An advertisement or promotional piece",
    "scientific report": "An internal scientific or technical report",
    "scientific publication": "A published scientific article or paper",
    "specification": "A product or material specification sheet",
    "file folder": "A file folder cover or label",
    "news article": "A newspaper or magazine article",
    "budget": "A budget, financial plan, or spreadsheet of planned spending",
    "invoice": "An invoice or bill requesting payment for goods or services",
    "presentation": "Presentation slides",
    "questionnaire": "A survey or questionnaire",
    "resume": "A resume or curriculum vitae",
    "memo": "An internal memorandum",
}


@variant
def v1_criteria(text: str) -> dict[str, Any]:
    """Hypothesis: describing what counts as true/false sharpens the decision boundary."""
    return {"state": text, "questions": {"is_invoice": {
        "type": "noul", "instructions": "Is this document an invoice?", "criteria": INVOICE_CRITERIA}}}


@variant
def v2_framing(text: str) -> dict[str, Any]:
    """Hypothesis: telling the model the text is noisy OCR stops it from over-trusting surface form."""
    return {"state": {"source": FRAMING, "ocr_text": text}, "questions": {"is_invoice": {
        "type": "noul", "instructions": "Is this document an invoice?", "criteria": INVOICE_CRITERIA}}}


@variant
def v3_choice16(text: str) -> dict[str, Any]:
    """Hypothesis: contrastive alternatives (budget, form, ...) calibrate better than a lone yes/no."""
    return {"state": {"source": FRAMING, "ocr_text": text}, "questions": {"doc_type": {
        "type": "choice", "instructions": "What type of document is this?", "criteria": CLASS_CRITERIA}}}


EVIDENCE = {
    "has_total_due": "Does the document state a total or amount due for payment?",
    "has_invoice_ref": "Does the document carry an invoice number, invoice date, or the word invoice/bill?",
    "requests_payment": "Is the sender asking the recipient to pay them?",
    "has_line_items": "Does the document list goods or services with quantities or prices?",
    "is_purchase_order": "Is this a purchase order or internal payment voucher rather than a vendor's bill?",
}


@variant
def v4_evidence(text: str) -> dict[str, Any]:
    """Hypothesis: several narrow factual questions + the type question, combined symbolically,
    are more trustworthy than one holistic yes/no; disagreement between them is a block signal."""
    questions = {
        "is_invoice": {"type": "noul", "instructions": "Is this document an invoice?", "criteria": INVOICE_CRITERIA},
        "doc_type": {"type": "choice", "instructions": "What type of document is this?", "criteria": CLASS_CRITERIA},
    }
    questions |= {name: {"type": "noul", "instructions": text_} for name, text_ in EVIDENCE.items()}
    return {"state": {"source": FRAMING, "ocr_text": text}, "questions": questions}


def needs_image(fn: Variant) -> Variant:
    fn.needs_image = True
    return fn


@variant
@needs_image
def v5_image_text(text: str, image: Any) -> dict[str, Any]:
    """Hypothesis: RVL-CDIP classes are largely defined by layout; the scan fixes what OCR garbles."""
    record = v4_evidence(text)
    record["state"] = {"source": FRAMING + " The original scan is attached as an image.", "ocr_text": text}
    return record | {"images": [image]}


@variant
@needs_image
def v6_image_only(text: str, image: Any) -> dict[str, Any]:
    """Control for v5: the scan without OCR text."""
    record = v4_evidence(text)
    record["state"] = {"source": "A scanned paper business document from a 1980s-90s corporate archive (attached image)."}
    return record | {"images": [image]}



# --- judges for multi-judge experiments (E-MJ2): same model, structurally different evidence or angle ---

def _window(text: str, start: float, end: float) -> str:
    words = text.split()
    return " ".join(words[int(len(words) * start):max(int(len(words) * end), int(len(words) * start) + 1)])


def _v2_on(text: str) -> dict[str, Any]:
    return v2_framing(text)


@variant
def j_first70(text: str) -> dict[str, Any]:
    """v2 formulation on the first 70% of the OCR words."""
    return _v2_on(_window(text, 0.0, 0.7))


@variant
def j_last70(text: str) -> dict[str, Any]:
    return _v2_on(_window(text, 0.3, 1.0))


@variant
def j_mid70(text: str) -> dict[str, Any]:
    return _v2_on(_window(text, 0.15, 0.85))


@variant
def j_trim80(text: str) -> dict[str, Any]:
    return _v2_on(_window(text, 0.1, 0.9))


@variant
def j_inverted(text: str) -> dict[str, Any]:
    """Inverted angle: ask whether it is NOT an invoice; p_invoice = P(false)."""
    return {"state": {"source": FRAMING, "ocr_text": text}, "questions": {"not_invoice": {
        "type": "noul", "instructions": "Is this document something other than an invoice?",
        "criteria": {"true": INVOICE_CRITERIA["false"], "false": INVOICE_CRITERIA["true"]}}}}


@variant
def j_clerk(text: str) -> dict[str, Any]:
    """Role angle: would accounts payable book it as a vendor bill to pay?"""
    return {"state": {"source": FRAMING, "ocr_text": text}, "questions": {"is_invoice": {
        "type": "noul",
        "instructions": "Would an accounts-payable clerk enter this document into the payables system as a vendor bill to pay?",
        "criteria": INVOICE_CRITERIA}}}
