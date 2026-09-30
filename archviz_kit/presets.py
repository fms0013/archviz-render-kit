"""Render ön ayarlarının yüklenmesi, doğrulanması ve kalite profilleriyle çözülmesi."""

from __future__ import annotations

import json
import os
from copy import deepcopy

REQUIRED_KEYS = ("name", "label", "engine", "resolution", "samples", "camera")
SUPPORTED_ENGINES = ("CYCLES", "BLENDER_EEVEE_NEXT", "BLENDER_EEVEE")

# Kalite profilleri: final ayarı referans alınır, diğerleri ondan türetilir.
# Örneklem ve çözünürlük oranları, render süresini öngörülebilir biçimde ölçekler.
QUALITY_TIERS: dict[str, dict] = {
    "draft": {
        "label": "Taslak",
        "description": "Kurgu ve kadraj kontrolü. Gölge/ışık kaba, gürültülü olabilir.",
        "sample_ratio": 0.06,
        "resolution_ratio": 0.5,
        "denoise": False,
        "min_samples": 8,
    },
    "preview": {
        "label": "Önizleme",
        "description": "Müşteriye gösterilebilir ön izleme. Malzeme ve ışık okunur.",
        "sample_ratio": 0.25,
        "resolution_ratio": 1.0,
        "denoise": True,
        "min_samples": 32,
    },
    "final": {
        "label": "Final",
        "description": "Teslim kalitesi. Tam örneklem, tam çözünürlük, denoise açık.",
        "sample_ratio": 1.0,
        "resolution_ratio": 1.0,
        "denoise": True,
        "min_samples": 64,
    },
}


def preset_dir() -> str:
    """Ön ayar klasörünü bulur.

    Sıra: ``ARCHVIZ_PRESETS`` ortam değişkeni, depo kökündeki ``presets/``,
    paketin yanındaki ``presets/``.
    """
    env = os.environ.get("ARCHVIZ_PRESETS")
    if env and os.path.isdir(env):
        return env

    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(os.path.dirname(here), "presets"),
        os.path.join(here, "presets"),
    ]
    for candidate in candidates:
        if os.path.isdir(candidate):
            return candidate
    return candidates[0]


def available_presets() -> list[str]:
    """Klasördeki ön ayar adlarını (dosya adı uzantısız) döndürür."""
    directory = preset_dir()
    if not os.path.isdir(directory):
        return []
    names = [
        os.path.splitext(name)[0]
        for name in sorted(os.listdir(directory))
        if name.endswith(".json")
    ]
    return names


def load_preset(name: str) -> dict:
    """Tek bir ön ayarı yükler ve doğrular."""
    path = os.path.join(preset_dir(), f"{name}.json")
    if not os.path.isfile(path):
        available = ", ".join(available_presets()) or "(yok)"
        raise FileNotFoundError(f"Ön ayar bulunamadı: {name}. Mevcut: {available}")

    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)

    errors = validate_preset(data)
    if errors:
        raise ValueError(f"{name}.json geçersiz: " + "; ".join(errors))
    return data


def validate_preset(preset: dict) -> list[str]:
    """Ön ayarı doğrular; bulunan hataların listesini döndürür (boş liste = geçerli)."""
    errors: list[str] = []

    if not isinstance(preset, dict):
        return ["Ön ayar bir JSON nesnesi olmalı"]

    for key in REQUIRED_KEYS:
        if key not in preset:
            errors.append(f"zorunlu alan eksik: '{key}'")

    engine = preset.get("engine")
    if engine is not None and engine not in SUPPORTED_ENGINES:
        errors.append(f"desteklenmeyen engine: {engine!r}")

    resolution = preset.get("resolution")
    if isinstance(resolution, dict):
        for axis in ("width", "height"):
            value = resolution.get(axis)
            if not isinstance(value, int) or value <= 0:
                errors.append(f"resolution.{axis} pozitif tam sayı olmalı")
    elif resolution is not None:
        errors.append("resolution bir nesne olmalı: {\"width\": w, \"height\": h}")

    samples = preset.get("samples")
    if samples is not None and (not isinstance(samples, int) or samples <= 0):
        errors.append("samples pozitif tam sayı olmalı")

    camera = preset.get("camera")
    if isinstance(camera, dict):
        cam_type = camera.get("type", "PERSP")
        if cam_type not in ("PERSP", "ORTHO"):
            errors.append(f"camera.type PERSP veya ORTHO olmalı, gelen: {cam_type!r}")
        if cam_type == "PERSP":
            focal = camera.get("focal_length_mm")
            if not isinstance(focal, (int, float)) or focal <= 0:
                errors.append("camera.focal_length_mm pozitif sayı olmalı")
        if cam_type == "ORTHO":
            scale = camera.get("ortho_scale_m")
            if not isinstance(scale, (int, float)) or scale <= 0:
                errors.append("camera.ortho_scale_m pozitif sayı olmalı")
    elif camera is not None:
        errors.append("camera bir nesne olmalı")

    return errors


def resolve(name: str, quality: str = "final", overrides: dict | None = None) -> dict:
    """Ön ayarı kalite profiliyle birleştirip render'a hazır sözlük döndürür.

    Args:
        name: ``interior``, ``exterior``, ``site-plan``, ``landscape`` ...
        quality: ``draft``, ``preview`` veya ``final``.
        overrides: Çözümlemeden sonra uygulanacak nokta atışı düzeltmeler
            (örn. ``{"samples": 128, "camera": {"shift_y": 0.05}}``).
    """
    if quality not in QUALITY_TIERS:
        raise ValueError(
            f"Bilinmeyen kalite profili: {quality}. Seçenekler: {', '.join(QUALITY_TIERS)}"
        )

    preset = deepcopy(load_preset(name))
    tier = QUALITY_TIERS[quality]

    base_samples = int(preset["samples"])
    scaled = int(round(base_samples * tier["sample_ratio"]))
    preset["samples"] = max(int(tier["min_samples"]), _round_samples(scaled))

    preset["denoise"] = bool(preset.get("denoise", True) and tier["denoise"])

    if tier["resolution_ratio"] != 1.0:
        ratio = tier["resolution_ratio"]
        # Çift sayıya yuvarla: video kodlayıcıları tek sayı çözünürlükte sorun çıkarır.
        preset["resolution"] = {
            "width": _even(int(round(preset["resolution"]["width"] * ratio))),
            "height": _even(int(round(preset["resolution"]["height"] * ratio))),
        }

    preset["quality"] = quality
    preset["quality_label"] = tier["label"]
    preset["base_samples"] = base_samples

    if overrides:
        preset = _deep_merge(preset, overrides)

    return preset


def _even(value: int) -> int:
    return value if value % 2 == 0 else value + 1


def _round_samples(value: int, step: int = 8) -> int:
    """Örneklem sayısını okunur bir adıma yuvarlar (varsayılan 8'in katı)."""
    if value <= step:
        return step
    return int(round(value / step)) * step


def _deep_merge(base: dict, extra: dict) -> dict:
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_merge(dict(base[key]), value)
        else:
            base[key] = value
    return base


def _main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Render ön ayarlarını listeler veya çözer.")
    parser.add_argument("name", nargs="?", help="Ön ayar adı (örn. interior)")
    parser.add_argument("--quality", default="final", choices=sorted(QUALITY_TIERS))
    parser.add_argument("--json", action="store_true", help="JSON olarak yazdır")
    args = parser.parse_args()

    if not args.name:
        for preset_name in available_presets():
            preset = load_preset(preset_name)
            print(f"{preset_name:<12} {preset.get('label', ''):<12} {preset.get('description', '')}")
        return 0

    resolved = resolve(args.name, args.quality)
    if args.json:
        print(json.dumps(resolved, ensure_ascii=False, indent=2))
    else:
        print(f"{resolved['label']} · {resolved['quality_label']}")
        print(f"  çözünürlük : {resolved['resolution']['width']}x{resolved['resolution']['height']}")
        print(f"  örneklem   : {resolved['samples']} (final tabanı {resolved['base_samples']})")
        print(f"  denoise    : {resolved['denoise']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
