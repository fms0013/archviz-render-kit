"""Blender köprüsü yardımcıları.

Buradaki fonksiyonlar ``bpy`` nesnelerini duck-typing ile kullanır: gerçek
Blender sahnesi de, testlerdeki sahte nesneler de çalışır. Böylece Blender
kurulmadan ışık/kamera mantığı doğrulanabilir.

Koordinat kabulü: ``+X`` doğu, ``+Y`` kuzey, ``+Z`` yukarı (sağ elli).
Azimut kuzeyden saat yönünde ölçülür; güneydoğu = 135°, batı = 270°.
"""

from __future__ import annotations

import math

ELEVATION_MIN_DEG = -5.0
ELEVATION_MAX_DEG = 90.0


def sun_direction(azimuth_deg: float, elevation_deg: float) -> tuple[float, float, float]:
    """Güneşten sahneye gelen ışığın birim yön vektörünü döndürür (aşağı yönlü)."""
    if not ELEVATION_MIN_DEG <= elevation_deg <= ELEVATION_MAX_DEG:
        raise ValueError(
            f"elevation_deg {ELEVATION_MIN_DEG} ile {ELEVATION_MAX_DEG} arasında olmalı"
        )

    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)

    # Güneşe doğru birim vektör, sonra ışığın geliş yönü (tersi).
    to_sun = (math.cos(el) * math.sin(az), math.cos(el) * math.cos(az), math.sin(el))
    return (-to_sun[0], -to_sun[1], -to_sun[2])


def sun_rotation_euler(azimuth_deg: float, elevation_deg: float) -> tuple[float, float, float]:
    """Güneş lambasının yönünü veren XYZ Euler açıları (radyan).

    Blender'da güneş lambasının yerel ``-Z`` ekseni ışık yönüdür.
    """
    direction = sun_direction(azimuth_deg, elevation_deg)
    dx, dy, dz = direction

    rot_x = math.acos(max(-1.0, min(1.0, -dz)))
    rot_z = math.atan2(-dx, dy)
    return (rot_x, 0.0, rot_z)


def apply_render_settings(scene, preset: dict) -> None:
    """Ön ayardaki render/çözünürlük/denoise ayarlarını sahneye uygular."""
    scene.render.engine = preset["engine"]
    scene.render.resolution_x = int(preset["resolution"]["width"])
    scene.render.resolution_y = int(preset["resolution"]["height"])
    scene.render.resolution_percentage = 100

    film = preset.get("film") or {}
    if "transparent" in film:
        scene.render.film_transparent = bool(film["transparent"])
    if "filter_size" in film:
        scene.render.filter_size = float(film["filter_size"])

    render = preset.get("render") or {}
    if "use_persistent_data" in render:
        scene.render.use_persistent_data = bool(render["use_persistent_data"])

    cycles = getattr(scene, "cycles", None)
    if cycles is None:
        return

    cycles.samples = int(preset["samples"])
    if hasattr(cycles, "use_denoising"):
        cycles.use_denoising = bool(preset.get("denoise", True))
    if "denoiser" in preset and hasattr(cycles, "denoiser"):
        cycles.denoiser = preset["denoiser"]

    for key in ("max_bounces", "transparent_max_bounces"):
        if key in render and hasattr(cycles, key):
            setattr(cycles, key, int(render[key]))
    for key in ("caustics_reflective", "caustics_refractive"):
        if key in render and hasattr(cycles, key):
            setattr(cycles, key, bool(render[key]))


def apply_color_management(scene, color_management: dict) -> list[str]:
    """Renk yönetimi ayarlarını uygular; uygulanamayanları uyarı olarak döndürür.

    Blender sürümleri arasında ``view_transform`` ve ``look`` adları değişebilir.
    Bu yüzden geçersiz bir değer sessizce yazılmaz; atlanır ve raporlanır.
    """
    warnings: list[str] = []
    view_settings = getattr(scene, "view_settings", None)
    if view_settings is None:
        return ["scene.view_settings bulunamadı; renk yönetimi atlandı"]

    view_transform = color_management.get("view_transform")
    if view_transform:
        if hasattr(view_settings, "view_transform"):
            view_settings.view_transform = view_transform
        else:
            warnings.append("view_transform ayarlanamadı")

    look = color_management.get("look")
    if look:
        if hasattr(view_settings, "look"):
            try:
                view_settings.look = look
            except (TypeError, ValueError) as exc:  # pragma: no cover - Blender'a bağlı
                warnings.append(f"look uygulanamadı ({look}): {exc}")
        else:
            warnings.append("look ayarlanamadı")

    for key in ("exposure", "gamma"):
        if key in color_management and hasattr(view_settings, key):
            setattr(view_settings, key, float(color_management[key]))

    return warnings


def apply_camera(camera, camera_preset: dict) -> None:
    """Kamera ayarlarını (tip, odak, kaydırma, kırpma) uygular."""
    data = camera.data
    cam_type = camera_preset.get("type", "PERSP")
    data.type = cam_type

    if cam_type == "ORTHO":
        data.ortho_scale = float(camera_preset["ortho_scale_m"])
    else:
        data.lens = float(camera_preset["focal_length_mm"])

    if "sensor_width_mm" in camera_preset:
        data.sensor_width = float(camera_preset["sensor_width_mm"])
    if "sensor_fit" in camera_preset:
        data.sensor_fit = camera_preset["sensor_fit"]
    if "shift_y" in camera_preset:
        data.shift_y = float(camera_preset["shift_y"])
    if "shift_x" in camera_preset:
        data.shift_x = float(camera_preset["shift_x"])
    if "clipping_start_m" in camera_preset:
        data.clip_start = float(camera_preset["clipping_start_m"])
    if "clipping_end_m" in camera_preset:
        data.clip_end = float(camera_preset["clipping_end_m"])

    # Düz kamera kuralı: mimari çekimde kamera eğilmez, lens kaydırılır.
    if camera_preset.get("level") and cam_type == "PERSP":
        try:
            rotation = camera.rotation_euler
            camera.rotation_euler = (math.pi / 2.0, rotation[1], rotation[2])
        except (AttributeError, TypeError):  # pragma: no cover - Blender'a bağlı
            pass


def apply_sun(light_object, lighting: dict) -> None:
    """Güneş lambasının enerjisini, yumuşaklığını ve yönünü ayarlar."""
    data = light_object.data
    if "sun_energy" in lighting:
        data.energy = float(lighting["sun_energy"])
    if "sun_angle_deg" in lighting and hasattr(data, "angle"):
        data.angle = math.radians(float(lighting["sun_angle_deg"]))

    if "sun_elevation_deg" in lighting and "sun_azimuth_deg" in lighting:
        light_object.rotation_euler = sun_rotation_euler(
            float(lighting["sun_azimuth_deg"]), float(lighting["sun_elevation_deg"])
        )


def apply_world_strength(scene, strength: float) -> list[str]:
    """Dünya (gökyüzü) ışık şiddetini ayarlar."""
    world = getattr(scene, "world", None)
    if world is None:
        return ["scene.world bulunamadı; gökyüzü şiddeti atlandı"]

    node_tree = getattr(world, "node_tree", None)
    if node_tree is not None and getattr(node_tree, "nodes", None):
        for node in node_tree.nodes:
            if getattr(node, "type", None) == "BACKGROUND" and "Strength" in node.inputs:
                node.inputs["Strength"].default_value = float(strength)
                return []

    if hasattr(world, "strength"):
        world.strength = float(strength)
        return []
    return ["gökyüzü şiddeti ayarlanamadı"]