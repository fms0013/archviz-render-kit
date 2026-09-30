"""Kamera çerçeveleme matematiği testleri."""

import math

import pytest

from archviz_kit import framing


def test_yatay_gorus_acisi_bilinen_deger():
    # 24 mm odak, 36 mm sensör: 2*atan(36/48) = 73.74 derece
    assert framing.horizontal_fov_deg(24.0, 36.0) == pytest.approx(73.74, abs=0.01)
    # 50 mm odak: 2*atan(36/100) = 39.60 derece
    assert framing.horizontal_fov_deg(50.0, 36.0) == pytest.approx(39.60, abs=0.01)


def test_sensor_yuksekligi_16_9():
    assert framing.sensor_height_mm(36.0, 16 / 9) == pytest.approx(20.25, abs=0.01)


def test_kadraja_sigdirmak_icin_mesafe():
    # 6 m genişlik, 24 mm odak, 36 mm sensör -> 4 m mesafe
    assert framing.fit_distance_m(24.0, 36.0, 6.0) == pytest.approx(4.0)


def test_mesafe_ve_genislik_ters_islem():
    distance = framing.fit_distance_m(35.0, 36.0, 12.0)
    assert framing.width_at_distance_m(distance, 35.0, 36.0) == pytest.approx(12.0)


def test_shift_y_hedefi_ortalar():
    # Kamera 1.55 m, hedef merkez 2.10 m, mesafe 5 m, odak 24 mm, sensör 36 mm
    shift = framing.shift_y_for_target(1.55, 2.10, 5.0, 24.0, 36.0)
    assert shift == pytest.approx((24.0 * (0.55 / 5.0)) / 36.0, abs=1e-9)
    assert shift > 0  # Hedef göz hizasının üstünde -> yukarı kaydırma


def test_shift_y_asagi_bakis_negatif():
    shift = framing.shift_y_for_target(1.6, 1.0, 4.0, 35.0, 36.0)
    assert shift < 0


def test_shift_y_sonlu_ve_makul():
    shift = framing.shift_y_for_target(1.6, 2.4, 6.0, 24.0, 36.0)
    assert math.isfinite(shift)
    assert abs(shift) < 0.5  # Aşırı kaydırma lens bozulması gibi görünür


def test_ortografik_olcek_kare_cozunurluk():
    scale = framing.ortho_scale_for_area(55.0, 40.0, {"width": 3200, "height": 3200}, margin=1.1)
    assert scale == pytest.approx(60.5)


def test_ortografik_olcek_yatay_baskin():
    # Yatay alan baskın olduğunda ölçek yatay genişliğe göre belirlenir.
    scale = framing.ortho_scale_for_area(80.0, 30.0, {"width": 3200, "height": 3200}, margin=1.0)
    assert scale == pytest.approx(80.0)


@pytest.mark.parametrize(
    "call",
    [
        lambda: framing.horizontal_fov_deg(0.0),
        lambda: framing.fit_distance_m(24.0, 36.0, 0.0),
        lambda: framing.sensor_height_mm(36.0, 0.0),
        lambda: framing.shift_y_for_target(1.6, 2.0, 0.0, 24.0),
        lambda: framing.ortho_scale_for_area(10.0, 10.0, {"width": 100, "height": 100}, margin=0.0),
    ],
)
def test_gecersiz_girdiler_hata_verir(call):
    with pytest.raises(ValueError):
        call()