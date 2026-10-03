"""RVL-CDIP OCR (HAMMALE/rvl_cdip_OCR): real scanned business documents, Tesseract OCR, 16 classes."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
from PIL import Image

DATA = Path(__file__).parent.parent / "data" / "rvl_cdip_ocr" / "data"
CLASSES = [
    "letter", "form", "email", "handwritten", "advertisement", "scientific report", "scientific publication",
    "specification", "file folder", "news article", "budget", "invoice", "presentation", "questionnaire",
    "resume", "memo",
]
MAX_WORDS = 600  # ~1k tokens; a handful of docs run longer and only add CPU time


def _path(split: str) -> Path:
    return DATA / f"{split}-00000-of-00001.parquet"


def load(split: str) -> pd.DataFrame:
    df = pd.read_parquet(_path(split), columns=["category", "ocr_paragraphs"])
    df["text"] = df.ocr_paragraphs.map(lambda p: " ".join(" ".join(p).split()[:MAX_WORDS]) if len(p) else "")
    df["doc_id"] = [f"{split}/{i}" for i in range(len(df))]
    df["is_invoice"] = df.category == "invoice"
    return df.drop(columns="ocr_paragraphs").reset_index(drop=True)


def image(doc_id: str) -> Image.Image:
    """Original scan for one doc (loaded lazily: the image column is ~200 MB per split)."""
    split, index = doc_id.split("/")
    table = _images(split)
    return Image.open(io.BytesIO(table[int(index)]["bytes"])).convert("RGB")


_IMAGE_CACHE: dict[str, list] = {}


def _images(split: str) -> list:
    if split not in _IMAGE_CACHE:
        _IMAGE_CACHE[split] = pq.read_table(_path(split), columns=["image"]).column(0).to_pylist()
    return _IMAGE_CACHE[split]


def sample(name: str) -> pd.DataFrame:
    """dev: all validation invoices + 20 per other class (tuning). dev10: stratified 10% of the validation
    split, natural class distribution (fast screening). test: the full test split (final numbers)."""
    if name == "bal120":
        # Balanced screening set: 60 invoices + 4 docs from each of the 15 other classes.
        df = load("validation")
        invoices = df[df.is_invoice].sample(60, random_state=0)
        others = df[~df.is_invoice].groupby("category", group_keys=False).sample(4, random_state=0)
        return pd.concat([invoices, others]).sort_index()
    if name == "test_bal":
        # Held-out verification set: every test invoice + 8 docs from each of the 15 other classes.
        df = load("test")
        others = df[~df.is_invoice].groupby("category", group_keys=False).sample(8, random_state=0)
        return pd.concat([df[df.is_invoice], others]).sort_index()
    if name == "chain_cal":
        # Full-chain calibration: every validation invoice + bal120's 60 non-invoices.
        df = load("validation")
        bal = sample("bal120")
        return pd.concat([df[df.is_invoice], bal[~bal.is_invoice]]).sort_index()
    if name == "chain_ver":
        # Small held-out set for the full chain: 40 test invoices + 3 docs from each other class.
        df = load("test")
        invoices = df[df.is_invoice].sample(40, random_state=0)
        others = df[~df.is_invoice].groupby("category", group_keys=False).sample(3, random_state=0)
        return pd.concat([invoices, others]).sort_index()
    if name == "chain_atoms":
        # Docs needing the atomic-condition pass: bal120's invoices + all of chain_ver.
        bal = sample("bal120")
        return pd.concat([bal[bal.is_invoice], sample("chain_ver")]).sort_index()
    if name == "dev10":
        return load("validation").groupby("category", group_keys=False).sample(frac=0.1, random_state=0).sort_index()
    if name == "dev":
        df = load("validation")
        others = df[~df.is_invoice].groupby("category", group_keys=False).sample(20, random_state=0)
        return pd.concat([df[df.is_invoice], others]).sort_index()
    if name == "test":
        return load("test")
    if name.startswith("smoke"):
        return sample("dev").sample(int(name.removeprefix("smoke") or 8), random_state=1)
    raise ValueError(name)
