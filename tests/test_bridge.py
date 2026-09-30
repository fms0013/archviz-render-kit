"""Blender köprüsü mantık testleri (Blender kurulmadan çalışır)."""

import math

import pytest

from archviz_kit import bridge


def _rotate_x(vector, angle):
    x, y, z = vector
    return (x, y * math.cos(angle) - z * math.sin(angle), y * math.sin(angle) + z * math.cos(angle))


def _rotate_z(vector, angle):
    x, y, z = vector
    return (x * math.cos(angle) - y * math.sin(angle), x * math.sin(angle) + y * math.cos(angle), z)


def test_gunes_yonu_asagi_bakar():
    dx, dy, dz = bridge.sun_direction(0.0, 90.0)
    assert dz == pytest.approx(-1.0, abs=1e-9)
    assert abs(dx) < 1e-9 and abs(dy) < 1e-9


def test_gunes_yonu_birim_vektordur():
    for azimuth in (0, 45, 135, 240, 359):
        for elevation in (5, 30, 60, 85):
            dx, dy, dz = bridge.sun_direction(azimuth, elevation)
            assert math.sqrt(dx * dx + dy * dy + dz * dz) == pytest.approx(1.0, abs=1e-9)


def test_gunes_yonu_dogu_bati():
    # Azimut 90 = doğu -> ışık batıya doğru gelir (dx negatif)
    dx, _, _ = bridge.sun_direction(90.0, 30.0)
    assert dx < 0
    # Azimut 270 = batı -> ışık doğuya doğru gelir (dx pozitif)
    dx, _, _ = bridge.sun_direction(270.0, 30.0)
    assert dx > 0
    # Azimut 0 = kuzey -> ışık güneye doğru gelir (dy negatif)
    _, dy, _ = bridge.sun_direction(0.0, 30.0)
    assert dy < 0


def test_gecersiz_yukseklik_hata_verir():
    with pytest.raises(ValueError):
        bridge.sun_direction(0.0, 120.0)


@pytest.mark.parametrize(
    "azimuth, elevation",
    [(0.0, 45.0), (135.0, 35.0), (250.0, 12.0), (315.0, 70.0)],
)
def test_euler_acilari_gercek_yonu_uretir(azimuth, elevation):
    """Euler açıları uygulandığında lambanın -Z ekseni ışık yönüne eşit olmalı."""
    rot_x, _, rot_z = bridge.sun_rotation_euler(azimuth, elevation)
    local_axis = (0.0, 0.0, -1.0)

    rotated = _rotate_z(_rotate_x(local_axis, rot_x), rot_z)
    expected = bridge.sun_direction(azimuth, elevation)

    for actual_value, expected_value in zip(rotated, expected):
        assert actual_value == pytest.approx(expected_value, abs=1e-9)


class FakeViewSettings:
    def __init__(self):
        self.view_transform = "Standard"
        self.look = "None"
        self.exposure = 0.0
        self.gamma = 1.0


class FakeScene:
    def __init__(self):
        self.view_settings = FakeViewSettings()
        self.world_strength = None


def test_renk_yonetimi_uygulaniyor():
    scene = FakeScene()
    warnings = bridge.apply_color_management(
        scene, {"view_transform": "AgX", "look": "AgX - Medium Contrast", "exposure": 0.5}
    )
    assert warnings == []
    assert scene.view_settings.view_transform == "AgX"
    assert scene.view_settings.exposure == 0.5


def test_renk_yonetimi_olmayan_ozellikte_uyari_dondurur():
    scene = FakeScene()
    del scene.view_settings.look
    warnings = bridge.apply_color_management(scene, {"look": "AgX - Medium Contrast"})
    assert any("look" in warning for warning in warnings)


class FakeNode:
    def __init__(self, node_type, input_names):
        self.type = node_type
        self.inputs = {name: FakeSocket() for name in input_names}


class FakeSocket:
    def __init__(self):
        self.default_value = None


class FakeWorld:
    def __init__(self, background=True):
        if background:
            self.node_tree = type(
                "Tree", (), {"nodes": [FakeNode("BACKGROUND", ["Color", "Strength"])]}
            )()
        else:
            self.node_tree = None
        self.strength = 1.0


def test_dunya_siddeti_arka_plan_dugumune_yazilir():
    scene = FakeScene()
    scene.world = FakeWorld()
    warnings = bridge.apply_world_strength(scene, 0.4)
    assert warnings == []
    node = scene.world.node_tree.nodes[0]
    assert node.inputs["Strength"].default_value == 0.4


def test_dunya_siddeti_geri_donus_olarak_uygulanir():
    scene = FakeScene()
    scene.world = FakeWorld(background=False)
    bridge.apply_world_strength(scene, 0.75)
    assert scene.world.strength == 0.75


def test_dunya_yoksa_uyari_dondurur():
    scene = FakeScene()
    scene.world = None
    assert bridge.apply_world_strength(scene, 1.0) == [
        "scene.world bulunamadı; gökyüzü şiddeti atlandı"
    ]


class FakeCameraData:
    def __init__(self):
        self.type = "PERSP"
        self.lens = 50.0
        self.sensor_width = 36.0
        self.sensor_fit = "AUTO"
        self.shift_y = 0.0
        self.clip_start = 0.1


class FakeCamera:
    def __init__(self):
        self.data = FakeCameraData()
        self.rotation_euler = (0.0, 0.0, 0.0)


def test_kamera_perspektif_ayarlari():
    camera = FakeCamera()
    bridge.apply_camera(
        camera,
        {"type": "PERSP", "focal_length_mm": 24.0, "sensor_width_mm": 36.0,
         "sensor_fit": "HORIZONTAL", "shift_y": 0.08, "clipping_start_m": 0.05},
    )
    assert camera.data.lens == 24.0
    assert camera.data.sensor_fit == "HORIZONTAL"
    assert camera.data.shift_y == 0.08
    assert camera.data.clip_start == 0.05


def test_kamera_ortografik_ayarlari():
    camera = FakeCamera()
    bridge.apply_camera(camera, {"type": "ORTHO", "ortho_scale_m": 60.5})
    assert camera.data.type == "ORTHO"
    assert camera.data.ortho_scale == 60.5


def test_duz_kamera_kurali_uygulaniyor():
    camera = FakeCamera()
    bridge.apply_camera(camera, {"type": "PERSP", "focal_length_mm": 35.0, "level": True})
    assert camera.rotation_euler[0] == pytest.approx(math.pi / 2.0)