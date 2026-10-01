"""Kadraj analizi ve plan görünüşlü doğrulama diyagramı.

Amaç: render almadan **önce** kameranın odaya sığıp sığmadığını ve duvarın
kadrajı doldurup doldurmadığını görmek. Yanlış kadrajla alınan final render,
harcanan sürenin tamamını çöpe atar.

Çıktı, bağımlılık gerektirmeyen SVG'dir; tarayıcıda veya vektör düzenleyicide
açılır.
"""

from __future__ import annotations

import math

from archviz_kit import framing

# Çizim yerleşimi (SVG kullanıcı birimi). Bölgeler birbiriyle çakışmayacak
# şekilde ayrılmıştır: başlık / çizim alanı / bilgi paneli.
CANVAS_WIDTH = 900
CANVAS_HEIGHT = 780
DRAW_LEFT = 150
DRAW_RIGHT = 850
DRAW_TOP = 120
DRAW_BOTTOM = 470
PANEL_TOP = 496
PANEL_HEIGHT = 254
FONT = "system-ui, -apple-system, Segoe UI, sans-serif"


def kadraj_analizi(
    room_width_m: float,
    room_depth_m: float,
    focal_mm: float,
    sensor_width_mm: float = framing.DEFAULT_SENSOR_WIDTH_MM,
) -> dict:
    """Oda ölçüleri ve odak uzaklığı için kadraj analizini hesaplar.

    Args:
        room_width_m: Fotoğraflanacak duvarın genişliği (metre).
        room_depth_m: Kameranın duvara uzaklığının üst sınırı; odanın derinliği.
        focal_mm: Odak uzaklığı.
        sensor_width_mm: Sensör genişliği.

    Returns:
        Analiz sözlüğü: gerekli mesafe, görüş açısı, sığıp sığmadığı ve
        odanın izin verdiği en uzun odak.
    """
    for name, value in (
        ("room_width_m", room_width_m),
        ("room_depth_m", room_depth_m),
        ("focal_mm", focal_mm),
        ("sensor_width_mm", sensor_width_mm),
    ):
        if value <= 0:
            raise ValueError(f"{name} pozitif olmalı, gelen: {value}")

    required_distance = framing.fit_distance_m(focal_mm, sensor_width_mm, room_width_m)
    fov = framing.horizontal_fov_deg(focal_mm, sensor_width_mm)
    max_focal = (sensor_width_mm * room_depth_m) / room_width_m

    # Kameranın gerçekten durabileceği yer: duvarı tam kadraja alan mesafe,
    # ancak odanın izin verdiği kadar geriye gidilebilir.
    camera_distance = min(required_distance, room_depth_m)
    framed_width = framing.width_at_distance_m(camera_distance, focal_mm, sensor_width_mm)

    fits = required_distance <= room_depth_m

    return {
        "room_width_m": room_width_m,
        "room_depth_m": room_depth_m,
        "focal_mm": focal_mm,
        "sensor_width_mm": sensor_width_mm,
        "horizontal_fov_deg": round(fov, 2),
        "required_distance_m": round(required_distance, 3),
        "camera_distance_m": round(camera_distance, 3),
        "framed_width_m": round(framed_width, 3),
        "margin_m": round(framed_width - room_width_m, 3),
        "fits": fits,
        "max_focal_mm": round(max_focal, 1),
        "room_fill_ratio": round(room_width_m / framed_width, 3) if framed_width else 0.0,
    }


def _scale_and_origin(room_width_m: float, room_depth_m: float, camera_distance_m: float):
    """Dünya koordinatlarını SVG koordinatlarına çeviren ölçek ve kayma."""
    world_width = room_width_m
    world_depth = max(room_depth_m, camera_distance_m)

    available_width = DRAW_RIGHT - DRAW_LEFT
    available_height = DRAW_BOTTOM - DRAW_TOP

    scale = min(available_width / world_width, available_height / world_depth)
    drawn_width = world_width * scale
    drawn_height = world_depth * scale

    origin_x = DRAW_LEFT + (available_width - drawn_width) / 2.0
    origin_y = DRAW_TOP + (available_height - drawn_height) / 2.0
    return scale, origin_x, origin_y


def plan_view_svg(analysis: dict, title: str = "Kadraj doğrulama") -> str:
    """Analizden plan görünüşlü SVG üretir.

    Duvar üstte, kamera altta; görüş açısı konisi ve kadraja giren genişlik
    ölçekli olarak çizilir.
    """
    room_width = analysis["room_width_m"]
    room_depth = analysis["room_depth_m"]
    camera_distance = analysis["camera_distance_m"]
    framed_width = analysis["framed_width_m"]
    fov = analysis["horizontal_fov_deg"]
    fits = analysis["fits"]

    scale, origin_x, origin_y = _scale_and_origin(room_width, room_depth, camera_distance)

    def sx(x_m: float) -> float:
        return origin_x + x_m * scale

    def sy(y_m: float) -> float:
        # Dünya: duvar y=0, oda içi +y. SVG'de aşağı doğru artar.
        return origin_y + y_m * scale

    wall_y = sy(0.0)
    room_bottom_y = sy(room_depth)
    camera_y = sy(camera_distance)
    camera_x = sx(room_width / 2.0)

    half_angle = math.radians(fov / 2.0)
    cone_half = camera_distance * math.tan(half_angle)
    left_x = sx(room_width / 2.0 - cone_half)
    right_x = sx(room_width / 2.0 + cone_half)

    accent = "#1f6feb" if fits else "#c2410c"
    cone_fill = "rgba(31,111,235,0.10)" if fits else "rgba(194,65,12,0.10)"

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}" '
        f'width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}">',
        f'<rect width="{CANVAS_WIDTH}" height="{CANVAS_HEIGHT}" fill="#ffffff"/>',
        f'<text x="70" y="46" font-size="21" font-weight="700" fill="#111" '
        f'font-family="{FONT}">{title}</text>',
        # Oda zemini
        f'<rect x="{sx(0):.1f}" y="{wall_y:.1f}" width="{room_width * scale:.1f}" '
        f'height="{room_depth * scale:.1f}" fill="#f6f7f9" stroke="#d0d7de" stroke-width="1"/>',
    ]

    # Fotoğraflanacak duvar
    parts.append(
        f'<line x1="{sx(0):.1f}" y1="{wall_y:.1f}" x2="{sx(room_width):.1f}" y2="{wall_y:.1f}" '
        f'stroke="#111" stroke-width="6"/>'
    )
    parts.append(
        f'<text x="{sx(room_width / 2):.1f}" y="{wall_y - 14:.1f}" font-size="13" '
        f'fill="#111" text-anchor="middle" font-family="{FONT}">'
        f'Fotoğraflanacak duvar — {room_width:.1f} m</text>'
    )

    # Görüş konisi
    parts.append(
        f'<polygon points="{camera_x:.1f},{camera_y:.1f} {left_x:.1f},{wall_y:.1f} '
        f'{right_x:.1f},{wall_y:.1f}" fill="{cone_fill}" stroke="none"/>'
    )
    for x in (left_x, right_x):
        parts.append(
            f'<line x1="{camera_x:.1f}" y1="{camera_y:.1f}" x2="{x:.1f}" y2="{wall_y:.1f}" '
            f'stroke="{accent}" stroke-width="1.5" stroke-dasharray="6 4"/>'
        )

    # Kadraja giren genişlik — duvarın hemen altında, başlıkla çakışmaz.
    mark_y = wall_y + 28
    parts.append(
        f'<line x1="{left_x:.1f}" y1="{mark_y:.1f}" x2="{right_x:.1f}" y2="{mark_y:.1f}" '
        f'stroke="{accent}" stroke-width="3"/>'
    )
    parts.append(
        f'<line x1="{left_x:.1f}" y1="{mark_y - 8:.1f}" x2="{left_x:.1f}" y2="{mark_y + 8:.1f}" '
        f'stroke="{accent}" stroke-width="1.5"/>'
    )
    parts.append(
        f'<line x1="{right_x:.1f}" y1="{mark_y - 8:.1f}" x2="{right_x:.1f}" y2="{mark_y + 8:.1f}" '
        f'stroke="{accent}" stroke-width="1.5"/>'
    )
    parts.append(
        f'<text x="{(left_x + right_x) / 2:.1f}" y="{mark_y + 26:.1f}" font-size="13.5" '
        f'fill="{accent}" text-anchor="middle" font-weight="700" font-family="{FONT}">'
        f'kadraja giren: {framed_width:.2f} m</text>'
    )

    # Kamera
    parts.append(f'<circle cx="{camera_x:.1f}" cy="{camera_y:.1f}" r="8" fill="{accent}"/>')
    parts.append(
        f'<text x="{camera_x + 15:.1f}" y="{camera_y + 5:.1f}" font-size="13.5" fill="{accent}" '
        f'font-weight="700" font-family="{FONT}">kamera</text>'
    )

    # Kamera mesafesi ölçüsü (sol taraf)
    dim_x = DRAW_LEFT - 44
    parts.append(
        f'<line x1="{dim_x:.1f}" y1="{camera_y:.1f}" x2="{dim_x:.1f}" y2="{wall_y:.1f}" '
        f'stroke="#8a8a8a" stroke-width="1"/>'
    )
    for y in (camera_y, wall_y):
        parts.append(
            f'<line x1="{dim_x - 7:.1f}" y1="{y:.1f}" x2="{dim_x + 7:.1f}" y2="{y:.1f}" '
            f'stroke="#8a8a8a" stroke-width="1"/>'
        )
    parts.append(
        f'<text x="{dim_x - 12:.1f}" y="{(camera_y + wall_y) / 2:.1f}" font-size="13.5" '
        f'fill="#444" text-anchor="end" font-family="{FONT}">{camera_distance:.2f} m</text>'
    )

    # Oda derinliği (sağ taraf) — etiket odanın içine doğru hizalanır, taşmaz.
    depth_x = min(sx(room_width) + 26, CANVAS_WIDTH - 40)
    parts.append(
        f'<line x1="{depth_x:.1f}" y1="{wall_y:.1f}" x2="{depth_x:.1f}" y2="{room_bottom_y:.1f}" '
        f'stroke="#c9c9c9" stroke-width="1" stroke-dasharray="5 4"/>'
    )
    parts.append(
        f'<text x="{depth_x - 10:.1f}" y="{(wall_y + room_bottom_y) / 2:.1f}" font-size="13" '
        f'fill="#888" text-anchor="end" font-family="{FONT}">oda derinliği {room_depth:.1f} m</text>'
    )

    # Bilgi paneli
    parts.append(
        f'<rect x="70" y="{PANEL_TOP}" width="{CANVAS_WIDTH - 140}" height="{PANEL_HEIGHT}" '
        f'rx="8" fill="#f6f7f9" stroke="#d0d7de"/>'
    )

    status_text = (
        "KADRAJ UYGUN — kamera odaya sığıyor, duvar kadrajı dolduruyor."
        if fits
        else "KADRAJ UYGUN DEĞİL — kamera bu odakla yeterince geriye gidemiyor."
    )
    parts.append(
        f'<text x="90" y="{PANEL_TOP + 34}" font-size="15" font-weight="700" fill="{accent}" '
        f'font-family="{FONT}">{status_text}</text>'
    )

    rows = [
        ("Odak uzaklığı", f"{analysis['focal_mm']:.0f} mm"),
        ("Yatay görüş açısı", f"{fov:.1f}°"),
        ("Gereken mesafe", f"{analysis['required_distance_m']:.2f} m"),
        ("Kamera mesafesi", f"{camera_distance:.2f} m"),
        ("Kadraja giren genişlik", f"{framed_width:.2f} m"),
        ("Duvarın kadrajı doldurma oranı", f"{analysis['room_fill_ratio'] * 100:.0f}%"),
        ("Bu odanın izin verdiği en uzun odak", f"{analysis['max_focal_mm']:.0f} mm"),
    ]
    for index, (label, value) in enumerate(rows):
        column = index % 2
        row = index // 2
        x = 90 + column * ((CANVAS_WIDTH - 180) / 2)
        y = PANEL_TOP + 72 + row * 26
        parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="13" fill="#555" font-family="{FONT}">'
            f'{label}: <tspan font-weight="700" fill="#111">{value}</tspan></text>'
        )

    if not fits:
        parts.append(
            f'<text x="90" y="{PANEL_TOP + 196}" font-size="13" fill="{accent}" '
            f'font-family="{FONT}">'
            f'Çözüm: odağı {analysis["max_focal_mm"]:.0f} mm veya altına düşürün, ya da '
            f'duvarın tamamını tek kareye sığdırmaktan vazgeçip iki kare çekin.</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)
