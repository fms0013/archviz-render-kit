"""Ön ayar yükleme, doğrulama ve kalite profili testleri."""

import pytest

from archviz_kit import presets


def test_beklenen_on_ayarlar_var():
    available = presets.available_presets()
    for name in ("interior", "exterior", "site-plan", "landscape"):
        assert name in available


@pytest.mark.parametrize("name", ["interior", "exterior", "site-plan", "landscape"])
def test_tum_on_ayarlar_gecerli(name):
    preset = presets.load_preset(name)
    assert presets.validate_preset(preset) == []
    assert preset["name"] == name


def test_eksik_alan_yakalaniyor():
    errors = presets.validate_preset({"name": "x"})
    assert any("engine" in error for error in errors)
    assert any("resolution" in error for error in errors)
    assert any("camera" in error for error in errors)


def test_gecersiz_kamera_tipi_yakalaniyor():
    errors = presets.validate_preset(
        {
            "name": "x",
            "label": "X",
            "engine": "CYCLES",
            "resolution": {"width": 100, "height": 100},
            "samples": 10,
            "camera": {"type": "PANORAMA"},
        }
    )
    assert any("camera.type" in error for error in errors)


def test_ortografik_kamera_ortho_scale_ister():
    errors = presets.validate_preset(
        {
            "name": "x",
            "label": "X",
            "engine": "CYCLES",
            "resolution": {"width": 100, "height": 100},
            "samples": 10,
            "camera": {"type": "ORTHO"},
        }
    )
    assert any("ortho_scale_m" in error for error in errors)


def test_bilinmeyen_on_ayar_hata_verir():
    with pytest.raises(FileNotFoundError):
        presets.load_preset("olmayan-ayar")


def test_final_profili_taban_degerleri_korur():
    resolved = presets.resolve("interior", "final")
    base = presets.load_preset("interior")
    assert resolved["samples"] == base["samples"]
    assert resolved["resolution"] == base["resolution"]
    assert resolved["denoise"] is True


def test_taslak_profili_orneklem_ve_cozunurluk_dusurur():
    resolved = presets.resolve("exterior", "draft")
    base = presets.load_preset("exterior")
    assert resolved["samples"] < base["samples"]
    assert resolved["resolution"]["width"] < base["resolution"]["width"]
    assert resolved["denoise"] is False
    # Video kodlayıcıları için çift sayı kuralı.
    assert resolved["resolution"]["width"] % 2 == 0
    assert resolved["resolution"]["height"] % 2 == 0


def test_onslem_minimumu_altina_inmez():
    resolved = presets.resolve("site-plan", "draft")
    assert resolved["samples"] >= presets.QUALITY_TIERS["draft"]["min_samples"]


def test_orneklem_okunur_adima_yuvarlanir():
    # 512 * 0.06 = 30.7 -> 32 (8'in katı)
    assert presets.resolve("interior", "draft")["samples"] == 32
    # 768 * 0.06 = 46.1 -> 48
    assert presets.resolve("exterior", "draft")["samples"] == 48
    # Önizleme profilinde yuvarlama sonucu değiştirmemeli.
    assert presets.resolve("interior", "preview")["samples"] == 128


def test_gecersiz_kalite_profili_hata_verir():
    with pytest.raises(ValueError):
        presets.resolve("interior", "ultra")


def test_overrides_uygulaniyor():
    resolved = presets.resolve("interior", "final", overrides={"samples": 42, "camera": {"shift_y": 0.2}})
    assert resolved["samples"] == 42
    assert resolved["camera"]["shift_y"] == 0.2
    # Diğer kamera alanları korunmalı.
    assert resolved["camera"]["focal_length_mm"] == 24.0
