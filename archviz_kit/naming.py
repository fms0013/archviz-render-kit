"""Render çıktı dosyası adlandırma.

Amaç: aynı projede üretilen yüzlerce karenin dosya adından okunabilmesi.
Şablon: ``{proje}_{gorunum}_{tur}_{kalite}_v{surum}.png``
"""

from __future__ import annotations

import re
import unicodedata

_TR_MAP = str.maketrans(
    {
        "ç": "c",
        "Ç": "c",
        "ğ": "g",
        "Ğ": "g",
        "ı": "i",
        "I": "i",
        "İ": "i",
        "ö": "o",
        "Ö": "o",
        "ş": "s",
        "Ş": "s",
        "ü": "u",
        "Ü": "u",
    }
)

VALID_KINDS = ("interior", "exterior", "site-plan", "landscape")


def slugify(text: str, max_length: int = 40) -> str:
    """Türkçe karakterleri sadeleştirip dosya adına uygun bir kısa ad üretir."""
    if text is None:
        return ""

    cleaned = str(text).translate(_TR_MAP)
    cleaned = unicodedata.normalize("NFKD", cleaned)
    cleaned = cleaned.encode("ascii", "ignore").decode("ascii")
    cleaned = cleaned.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", cleaned).strip("-")
    cleaned = re.sub(r"-{2,}", "-", cleaned)

    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip("-")
    return cleaned


def output_name(
    project: str,
    view: str,
    kind: str = "interior",
    quality: str = "final",
    version: int = 1,
    extension: str = "png",
) -> str:
    """Tek bir render karesi için dosya adı üretir.

    Args:
        project: Proje kısa adı (örn. "Villa A").
        view: Görünüm/görüş adı (örn. "Salon KD", "Kuzey Cephe").
        kind: ``interior``, ``exterior``, ``site-plan`` veya ``landscape``.
        quality: ``draft``, ``preview`` veya ``final``.
        version: Sürüm numarası; iki haneye tamamlanır (``v01``).
        extension: Uzantı, nokta olmadan.
    """
    if kind not in VALID_KINDS:
        raise ValueError(f"Bilinmeyen tür: {kind}. Seçenekler: {', '.join(VALID_KINDS)}")
    if version < 1:
        raise ValueError("version 1 veya daha büyük olmalı")

    parts = [
        slugify(project) or "proje",
        slugify(view) or "gorunum",
        slugify(kind),
        slugify(quality),
        f"v{version:02d}",
    ]
    ext = (extension or "png").lstrip(".").lower()
    return "_".join(parts) + f".{ext}"


def parse_output_name(filename: str) -> dict:
    """``output_name`` ile üretilmiş bir adı bileşenlerine ayırır."""
    stem = filename.rsplit(".", 1)[0]
    parts = stem.split("_")
    if len(parts) < 5:
        raise ValueError(f"Ad beklenen şablona uymuyor: {filename}")

    version_raw = parts[-1]
    quality = parts[-2]
    kind = parts[-3]
    view = "_".join(parts[1:-3])
    project = parts[0]

    if not version_raw.startswith("v") or not version_raw[1:].isdigit():
        raise ValueError(f"Sürüm alanı okunamadı: {version_raw}")

    return {
        "project": project,
        "view": view,
        "kind": kind,
        "quality": quality,
        "version": int(version_raw[1:]),
    }