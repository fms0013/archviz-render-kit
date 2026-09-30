"""Kamera çerçeveleme matematiği.

Bu modül bilinçli olarak saf Python'dur; Blender çalıştırmadan kadraj
hesaplanabilir. Tüm formüller ince mercek (thin lens) yaklaşımını kullanır ve
mimari çekim pratiğine göre sadeleştirilmiştir.
"""

from __future__ import annotations

import math

DEFAULT_SENSOR_WIDTH_MM = 36.0
# Mimari çekimde göz hizası kabulü: ayakta duran insanın gözü ~1,60-1,70 m.
DEFAULT_EYE_HEIGHT_M = 1.6


def sensor_height_mm(sensor_width_mm: float, aspect: float) -> float:
    """Yatay sensör genişliğinden dikey sensör yüksekliğini verir (aspect = en/boy)."""
    if aspect <= 0:
        raise ValueError("aspect pozitif olmalı")
    return sensor_width_mm / aspect


def horizontal_fov_deg(focal_mm: float, sensor_width_mm: float = DEFAULT_SENSOR_WIDTH_MM) -> float:
    """Yatay görüş açısı (derece)."""
    _require_positive(focal_mm=focal_mm, sensor_width_mm=sensor_width_mm)
    return math.degrees(2.0 * math.atan(sensor_width_mm / (2.0 * focal_mm)))


def vertical_fov_deg(focal_mm: float, sensor_height: float) -> float:
    """Dikey görüş açısı (derece)."""
    _require_positive(focal_mm=focal_mm, sensor_height=sensor_height)
    return math.degrees(2.0 * math.atan(sensor_height / (2.0 * focal_mm)))


def fit_distance_m(focal_mm: float, sensor_mm: float, subject_size_m: float) -> float:
    """Öznenin verilen boyutu kadrajı tam doldurduğunda gereken kamera mesafesi.

    ``subject_size_m`` yatay ölçüyle ve ``sensor_mm`` yatay sensörle eşleşmelidir;
    dikey ölçü için ``sensor_height_mm`` kullanın.
    """
    _require_positive(focal_mm=focal_mm, sensor_mm=sensor_mm, subject_size_m=subject_size_m)
    return (focal_mm * subject_size_m) / sensor_mm


def width_at_distance_m(
    distance_m: float, focal_mm: float, sensor_mm: float = DEFAULT_SENSOR_WIDTH_MM
) -> float:
    """Belirli mesafede kadrajın kapsadığı yatay genişlik (metre)."""
    _require_positive(distance_m=distance_m, focal_mm=focal_mm, sensor_mm=sensor_mm)
    return (distance_m * sensor_mm) / focal_mm


def shift_y_for_target(
    camera_height_m: float,
    target_center_height_m: float,
    distance_m: float,
    focal_mm: float,
    sensor_width_mm: float = DEFAULT_SENSOR_WIDTH_MM,
) -> float:
    """Kamera düz tutulurken hedefi dikeyde ortalamak için gereken ``shift_y``.

    Mimari çekimde kamera eğilmez (``level``); tavanı kadraja almak için lens
    kaydırması kullanılır. Bu, dikey duvar ve kapı kenarlarının eğilmesini
    engeller — iki nokta perspektifinin temel kuralı.

    Blender'da ``sensor_fit = 'HORIZONTAL'`` iken ``shift_y`` birimi
    ``sensor_width``tir; formül bu kabule göre yazılmıştır.
    """
    _require_positive(distance_m=distance_m, focal_mm=focal_mm, sensor_width_mm=sensor_width_mm)
    tan_theta = (target_center_height_m - camera_height_m) / distance_m
    return (focal_mm * tan_theta) / sensor_width_mm


def ortho_scale_for_area(
    width_m: float, height_m: float, resolution: dict, margin: float = 1.1
) -> float:
    """Ortografik kamerada verilen alanı kadraja almak için ``ortho_scale`` değeri.

    Blender ``ortho_scale`` değeri, ``sensor_fit`` ile seçilen eksene karşılık gelir;
    kare çözünürlükte her iki eksen de aynıdır. Kenar boşluğu için ``margin`` > 1.
    """
    _require_positive(width_m=width_m, height_m=height_m)
    if margin <= 0:
        raise ValueError("margin pozitif olmalı")

    res_w = int(resolution.get("width", 1))
    res_h = int(resolution.get("height", 1))
    if res_w <= 0 or res_h <= 0:
        raise ValueError("resolution pozitif olmalı")

    needed_x = width_m * margin
    needed_y = height_m * margin

    if res_w >= res_h:
        # Yatay eksen baskın: ortho_scale yatay genişliği belirler.
        return max(needed_x, needed_y * (res_w / res_h))
    return max(needed_y, needed_x * (res_h / res_w))


def _require_positive(**values: float) -> None:
    for key, value in values.items():
        if value <= 0:
            raise ValueError(f"{key} pozitif olmalı, gelen: {value}")