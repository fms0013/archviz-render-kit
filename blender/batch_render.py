"""Blender içinde çalışır: çekim listesini sırayla render eder.

Kullanım::

    blender -b sahne.blend --python-exit-code 1 --python blender/batch_render.py -- \\
        --shotlist shotlist.json --outdir renders

Kabul: ``shotlist.json`` içindeki her görünüm için sahnede aynı adı taşıyan bir
kamera vardır (örn. ``shot["id"] == "salon-kd"`` ise ``salon-kd`` adlı kamera).
Kamera konumlandırması projeye özgüdür; bu betik yalnızca kalite/çıktı
ayarlarını ve render kuyruğunu yönetir.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import bpy

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from archviz_kit import bridge, presets  # noqa: E402


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Çekim listesini Blender'da toplu render eder.")
    parser.add_argument("--shotlist", required=True, help="shotlist.json yolu")
    parser.add_argument("--outdir", required=True, help="Render çıktı klasörü")
    parser.add_argument("--only", default=None, help="Virgülle ayrılmış görünüm kimlikleri")
    parser.add_argument("--skip-existing", action="store_true", help="Var olan kareleri atla")
    parser.add_argument("--sun", default=None, help="Güneş lambası nesnesi adı")
    return parser.parse_args(argv)


def find_sun(scene):
    for obj in scene.objects:
        if obj.type == "LIGHT" and obj.data.type == "SUN":
            return obj
    return None


def main() -> int:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    args = parse_args(argv)

    with open(args.shotlist, encoding="utf-8") as handle:
        shotlist = json.load(handle)

    selected = set(args.only.split(",")) if args.only else None
    shots = [shot for shot in shotlist["shots"] if not selected or shot["id"] in selected]

    if not shots:
        print("[archviz] Seçilen görünüm yok; çıkış.")
        return 0

    os.makedirs(args.outdir, exist_ok=True)

    scene = bpy.context.scene
    sun = scene.objects.get(args.sun) if args.sun else find_sun(scene)

    failures: list[str] = []
    total_started = time.time()

    for index, shot in enumerate(shots, start=1):
        label = f"[{index}/{len(shots)}] {shot['id']} ({shot['kind']}/{shot['quality']})"
        target = os.path.join(os.path.abspath(args.outdir), shot["output"])

        if args.skip_existing and os.path.isfile(target):
            print(f"{label} — atlandı (dosya var)")
            continue

        camera_object = scene.objects.get(shot["id"])
        if camera_object is None or camera_object.type != "CAMERA":
            message = f"{shot['id']}: sahnede bu adla kamera yok"
            print(f"{label} — HATA: {message}")
            failures.append(message)
            continue

        preset = {
            "engine": "CYCLES",
            "resolution": shot["resolution"],
            "samples": shot["samples"],
            "denoise": shot.get("denoise", True),
            "denoiser": "OPENIMAGEDENOISE",
            "film": {"transparent": False},
            "render": {},
            "camera": shot["camera"],
            "lighting": shot["lighting"],
        }
        # Motor ve renk yönetimi ön ayardan gelir; çekim listesi yalnızca
        # çözünürlük, örneklem ve kamera/ışık değerlerini taşır.
        source_preset = presets.resolve(
            {"interior": "interior", "exterior": "exterior",
             "site-plan": "site-plan", "landscape": "landscape"}[shot["kind"]],
            shot["quality"],
        )
        preset["engine"] = source_preset["engine"]
        preset["color_management"] = source_preset.get("color_management", {})
        preset["film"] = source_preset.get("film", {})
        preset["render"] = source_preset.get("render", {})

        bridge.apply_render_settings(scene, preset)

        for warning in bridge.apply_color_management(scene, preset.get("color_management", {})):
            print(f"[archviz][uyarı] {shot['id']}: {warning}")

        bridge.apply_camera(camera_object, shot["camera"])
        scene.camera = camera_object

        if sun is not None:
            bridge.apply_sun(sun, shot["lighting"])
        if "world_strength" in shot["lighting"]:
            bridge.apply_world_strength(scene, shot["lighting"]["world_strength"])

        scene.render.filepath = target
        scene.render.image_settings.file_format = "PNG"

        started = time.time()
        bpy.ops.render.render(write_still=True)
        elapsed = time.time() - started

        status = "tamam" if os.path.isfile(target) else "DOSYA YOK"
        print(f"{label} — {status} · {elapsed:.1f} sn · {target}")
        if status != "tamam":
            failures.append(f"{shot['id']}: çıktı üretilmedi")

    total = time.time() - total_started
    print(f"[archviz] Toplam {len(shots)} görünüm, {total / 60:.1f} dakika.")
    if failures:
        print("[archviz] Başarısız görünümler:")
        for item in failures:
            print(f"  - {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())