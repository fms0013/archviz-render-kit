"""Proje tanımından çekim listesi (shot list) üretimi.

Bir mimari projede onlarca görünüm olur. Bu modül, tek bir ``project.json``
dosyasından hangi karenin hangi ön ayar, hangi kamera değeri ve hangi dosya
adıyla üretileceğini hesaplar. Böylece render kuyruğu elle kurulmaz ve
dosya adları tutarlı kalır.
"""

from __future__ import annotations

import json
from copy import deepcopy

from archviz_kit import framing
from archviz_kit.naming import VALID_KINDS, output_name
from archviz_kit.presets import QUALITY_TIERS, resolve

KIND_TO_PRESET = {
    "interior": "interior",
    "exterior": "exterior",
    "site-plan": "site-plan",
    "landscape": "landscape",
}


def build_shotlist(project: dict) -> dict:
    """Proje tanımını çözümlenmiş çekim listesine dönüştürür."""
    if not isinstance(project, dict):
        raise ValueError("project bir nesne olmalı")

    project_name = project.get("project")
    if not project_name:
        raise ValueError("project alanı (proje adı) zorunlu")

    views = project.get("views")
    if not isinstance(views, list) or not views:
        raise ValueError("views listesi boş olamaz")

    default_quality = project.get("default_quality", "final")
    if default_quality not in QUALITY_TIERS:
        raise ValueError(f"Bilinmeyen default_quality: {default_quality}")

    shots = []
    seen: set[str] = set()

    for index, view in enumerate(views):
        if not isinstance(view, dict):
            raise ValueError(f"views[{index}] bir nesne olmalı")

        shot = _build_shot(project_name, view, default_quality, index)
        if shot["id"] in seen:
            raise ValueError(f"Tekrarlanan görünüm kimliği: {shot['id']}")
        seen.add(shot["id"])
        shots.append(shot)

    return {
        "project": project_name,
        "default_quality": default_quality,
        "shot_count": len(shots),
        "shots": shots,
    }


def _build_shot(project_name: str, view: dict, default_quality: str, index: int) -> dict:
    kind = view.get("kind")
    if kind not in VALID_KINDS:
        raise ValueError(
            f"views[{index}].kind geçersiz: {kind!r}. Seçenekler: {', '.join(VALID_KINDS)}"
        )

    view_id = view.get("id") or f"{kind}-{index + 1:02d}"
    title = view.get("title") or view_id
    quality = view.get("quality", default_quality)
    version = int(view.get("version", 1))

    preset = resolve(
        KIND_TO_PRESET[kind],
        quality,
        overrides=view.get("overrides"),
    )

    camera_input = view.get("camera") or {}
    lighting_input = view.get("lighting") or {}
    warnings: list[str] = []

    computed_camera = _compute_camera(preset, camera_input, warnings)
    computed_lighting = _compute_lighting(preset, lighting_input)

    # Kamera değerleri ön ayarın üzerine yazılır; ön ayar sadece varsayılan sağlar.
    preset_camera = deepcopy(preset.get("camera", {}))
    preset_camera.update(computed_camera)
    preset["camera"] = preset_camera

    preset_lighting = deepcopy(preset.get("lighting", {}))
    preset_lighting.update(computed_lighting)
    preset["lighting"] = preset_lighting

    return {
        "id": view_id,
        "title": title,
        "kind": kind,
        "quality": quality,
        "version": version,
        "room": view.get("room"),
        "note": view.get("note"),
        "output": output_name(project_name, view_id, kind, quality, version),
        "camera": preset_camera,
        "lighting": preset_lighting,
        "resolution": preset["resolution"],
        "samples": preset["samples"],
        "warnings": warnings,
    }


def _compute_camera(preset: dict, camera_input: dict, warnings: list[str]) -> dict:
    camera_preset = preset.get("camera", {})
    cam_type = camera_preset.get("type", "PERSP")
    result: dict = {}

    eye_height = camera_input.get("eye_height_m", camera_preset.get("eye_height_m"))
    if eye_height is not None:
        result["eye_height_m"] = float(eye_height)

    if cam_type == "ORTHO":
        area_w = camera_input.get("area_width_m")
        area_h = camera_input.get("area_height_m")
        if area_w and area_h:
            result["ortho_scale_m"] = round(
                framing.ortho_scale_for_area(
                    float(area_w),
                    float(area_h),
                    preset.get("resolution", {"width": 1, "height": 1}),
                    margin=float(camera_input.get("margin", 1.1)),
                ),
                3,
            )
        elif "ortho_scale_m" in camera_input:
            result["ortho_scale_m"] = float(camera_input["ortho_scale_m"])
        else:
            warnings.append(
                "Ortografik görünüm için area_width_m/area_height_m verilmedi; "
                "ön ayarın varsayılan ortho_scale_m değeri kullanılacak."
            )
        return result

    focal = float(camera_input.get("focal_mm", camera_preset.get("focal_length_mm", 35.0)))
    result["focal_length_mm"] = focal

    sensor_width = float(camera_preset.get("sensor_width_mm", framing.DEFAULT_SENSOR_WIDTH_MM))
    aspect = preset["resolution"]["width"] / preset["resolution"]["height"]

    distance = camera_input.get("distance_m")
    subject_width = camera_input.get("subject_width_m")

    if distance is None and subject_width:
        distance = framing.fit_distance_m(focal, sensor_width, float(subject_width))
        result["distance_m"] = round(distance, 3)
    elif distance is not None:
        distance = float(distance)
        result["distance_m"] = distance
        if subject_width:
            framed = framing.width_at_distance_m(distance, focal, sensor_width)
            if float(subject_width) > framed:
                warnings.append(
                    f"Özne ({subject_width} m) bu mesafede kadraja sığmıyor "
                    f"(kadraj genişliği {framed:.2f} m); mesafeyi artırın veya odağı kısaltın."
                )

    target_height = camera_input.get("target_center_height_m")
    if target_height is not None and distance:
        result["shift_y"] = round(
            framing.shift_y_for_target(
                float(eye_height if eye_height is not None else framing.DEFAULT_EYE_HEIGHT_M),
                float(target_height),
                float(distance),
                focal,
                sensor_width,
            ),
            4,
        )
    else:
        result["shift_y"] = float(camera_preset.get("shift_y", 0.0))

    # Kadraj sığdırma kontrolü: özne yüksekliği dikeyde sığıyor mu?
    subject_h = camera_input.get("subject_height_m")
    if subject_h and distance:
        sensor_h = framing.sensor_height_mm(sensor_width, aspect)
        framed_h = framing.width_at_distance_m(float(distance), focal, sensor_h)
        if float(subject_h) > framed_h:
            warnings.append(
                f"Özne yüksekliği ({subject_h} m) kadraja sığmıyor "
                f"(kadraj yüksekliği {framed_h:.2f} m); daha geniş odak veya daha uzak kamera gerekir."
            )

    return result


def _compute_lighting(preset: dict, lighting_input: dict) -> dict:
    result: dict = {}
    for key in ("sun_azimuth_deg", "sun_elevation_deg", "sun_energy", "sun_angle_deg", "world_strength"):
        if key in lighting_input:
            result[key] = float(lighting_input[key])
    return result


def render_markdown(shotlist: dict) -> str:
    """Çekim listesini Markdown tablosu olarak döndürür."""
    lines = [
        f"# Çekim listesi — {shotlist['project']}",
        "",
        f"Toplam **{shotlist['shot_count']}** görünüm.",
        "",
        "| # | Kimlik | Tür | Kalite | Örneklem | Çözünürlük | Dosya |",
        "|---|--------|-----|--------|----------|------------|-------|",
    ]
    for index, shot in enumerate(shotlist["shots"], start=1):
        res = shot["resolution"]
        lines.append(
            f"| {index} | `{shot['id']}` | {shot['kind']} | {shot['quality']} | "
            f"{shot['samples']} | {res['width']}×{res['height']} | `{shot['output']}` |"
        )

    warned = [shot for shot in shotlist["shots"] if shot["warnings"]]
    if warned:
        lines += ["", "## Uyarılar", ""]
        for shot in warned:
            for warning in shot["warnings"]:
                lines.append(f"- `{shot['id']}`: {warning}")
    return "\n".join(lines) + "\n"


def _main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Proje tanımından çekim listesi üretir."
    )
    parser.add_argument("project", help="project.json yolu")
    parser.add_argument("--out", help="Çıktı JSON yolu (varsayılan: ekrana yaz)")
    parser.add_argument("--markdown", help="Markdown tablosu olarak bu dosyaya yaz")
    args = parser.parse_args()

    with open(args.project, encoding="utf-8") as handle:
        project = json.load(handle)

    shotlist = build_shotlist(project)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(shotlist, handle, ensure_ascii=False, indent=2)
        print(f"Çekim listesi yazıldı: {args.out}")
    else:
        print(json.dumps(shotlist, ensure_ascii=False, indent=2))

    if args.markdown:
        with open(args.markdown, "w", encoding="utf-8") as handle:
            handle.write(render_markdown(shotlist))
        print(f"Markdown yazıldı: {args.markdown}")

    warnings = sum(len(shot["warnings"]) for shot in shotlist["shots"])
    print(f"{shotlist['shot_count']} görünüm, {warnings} uyarı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())