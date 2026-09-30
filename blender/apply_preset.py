"""Blender içinde çalışır: bir render ön ayarını açık sahneye uygular.

Kullanım::

    blender -b sahne.blend --python-exit-code 1 --python blender/apply_preset.py -- \\
        --preset exterior --quality final --out renders/dis-cephe.png --render

Blender, ``--`` sonrasındaki argümanları betiğe bırakır. Bu betik sahneyi
kaydetmez; sadece ayarları uygular ve (istenirse) render alır.
"""

from __future__ import annotations

import argparse
import os
import sys

import bpy

# Depo kökünü import yoluna ekle: blender/ klasörünün bir üstü.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from archviz_kit import bridge, presets  # noqa: E402


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render ön ayarını Blender sahnesine uygular.")
    parser.add_argument("--preset", required=True, help="Ön ayar adı (interior, exterior, ...)")
    parser.add_argument("--quality", default="final", choices=sorted(presets.QUALITY_TIERS))
    parser.add_argument("--camera", default=None, help="Kamera nesnesi adı (varsayılan: sahne kamerası)")
    parser.add_argument("--sun", default=None, help="Güneş lambası nesnesi adı (varsayılan: ilk SUN)")
    parser.add_argument("--out", default=None, help="Render çıktı yolu")
    parser.add_argument("--render", action="store_true", help="Ayarları uyguladıktan sonra render al")
    return parser.parse_args(argv)


def find_sun(scene):
    for obj in scene.objects:
        if obj.type == "LIGHT" and obj.data.type == "SUN":
            return obj
    return None


def resolve_camera(scene, name: str | None):
    if name:
        camera_object = scene.objects.get(name)
        if camera_object is None:
            raise SystemExit(f"Kamera bulunamadı: {name}")
        return camera_object

    camera_object = scene.camera
    if camera_object is None:
        raise SystemExit("Sahnede etkin kamera yok; --camera ile bir kamera belirtin.")
    return camera_object


def main() -> int:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    args = parse_args(argv)

    scene = bpy.context.scene
    preset = presets.resolve(args.preset, args.quality)

    bridge.apply_render_settings(scene, preset)

    warnings = bridge.apply_color_management(scene, preset.get("color_management", {}))

    camera_object = resolve_camera(scene, args.camera)
    bridge.apply_camera(camera_object, preset.get("camera", {}))
    scene.camera = camera_object

    lighting = preset.get("lighting", {})
    sun = find_sun(scene)
    if sun is not None:
        bridge.apply_sun(sun, lighting)
    elif lighting.get("sun_energy"):
        warnings.append("Sahnede güneş lambası yok; güneş ayarları atlandı.")

    if "world_strength" in lighting:
        warnings += bridge.apply_world_strength(scene, lighting["world_strength"])

    if args.out:
        scene.render.filepath = os.path.abspath(args.out)
        scene.render.image_settings.file_format = "PNG"

    print(f"[archviz] Ön ayar: {preset['label']} · {preset['quality_label']}")
    print(
        f"[archviz] Çözünürlük: {preset['resolution']['width']}x{preset['resolution']['height']}"
        f" · Örneklem: {preset['samples']} · Denoise: {preset['denoise']}"
    )
    print(f"[archviz] Kamera: {camera_object.name} ({camera_object.data.type})")
    if args.out:
        print(f"[archviz] Çıktı: {scene.render.filepath}")
    for warning in warnings:
        print(f"[archviz][uyarı] {warning}")

    if args.render:
        bpy.ops.render.render(write_still=True)
        print("[archviz] Render tamamlandı.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())