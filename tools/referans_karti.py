"""Kamera hızlı referans kartı üretir.

Tablolar, kitin kendi matematigi kullanılarak hesaplanır; elle yazılmış sayı
yoktur. Çıktı Markdown'dır, PDF'e çevrilebilir.

Kullanım::

    python tools/referans_karti.py > referans-karti.md
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from archviz_kit import framing  # noqa: E402

SENSOR = 36.0
EYE_INTERIOR = 1.55
TARGET_INTERIOR = 2.10
EYE_EXTERIOR = 1.65
FOCAL_INTERIOR = 24.0
FOCAL_INTERIOR_NARROW = 35.0
FOCAL_EXTERIOR = 35.0


def _fmt(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def interior_table(focal: float, label: str) -> list[str]:
    lines = [
        f"### {label} ({_fmt(focal, 0)} mm odak · göz {_fmt(EYE_INTERIOR)} m · "
        f"hedef merkez {_fmt(TARGET_INTERIOR)} m)",
        "",
        "| Odanın kadraja giren genişliği | Kamera mesafesi | Lens kaydırması (`shift_y`) |",
        "|---|---|---|",
    ]
    for width in (3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0):
        distance = framing.fit_distance_m(focal, SENSOR, width)
        shift = framing.shift_y_for_target(
            EYE_INTERIOR, TARGET_INTERIOR, distance, focal, SENSOR
        )
        lines.append(
            f"| {_fmt(width, 1)} m | **{_fmt(distance)} m** | {_fmt(shift, 3)} |"
        )
    lines.append("")
    return lines


def exterior_table() -> list[str]:
    lines = [
        f"### Dış cephe ({_fmt(FOCAL_EXTERIOR, 0)} mm odak · göz {_fmt(EYE_EXTERIOR)} m)",
        "",
        "| Yapı genişliği | Kadraja sığdıran mesafe | Alt sınır (yapı yüksekliği × 2) |",
        "|---|---|---|",
    ]
    for width, height in ((10.0, 6.0), (14.0, 7.5), (18.0, 9.0), (24.0, 12.0), (30.0, 15.0)):
        distance = framing.fit_distance_m(FOCAL_EXTERIOR, SENSOR, width)
        minimum = height * 2.0
        chosen = max(distance, minimum)
        flag = " ← yükseklik kuralı belirler" if minimum > distance else ""
        lines.append(
            f"| {_fmt(width, 0)} m (h {_fmt(height, 1)} m) | {_fmt(distance)} m | "
            f"**{_fmt(chosen)} m**{flag} |"
        )
    lines.append("")
    return lines


def site_plan_table() -> list[str]:
    lines = [
        "### Vaziyet planı (ortografik · 3200 × 3200 px · kenar boşluğu %15)",
        "",
        "| Parsel (en × boy) | `ortho_scale` | Kapsanan alan |",
        "|---|---|---|",
    ]
    resolution = {"width": 3200, "height": 3200}
    for width, height in ((20.0, 20.0), (30.0, 25.0), (40.0, 50.0), (62.0, 45.0), (100.0, 80.0)):
        scale = framing.ortho_scale_for_area(width, height, resolution, margin=1.15)
        lines.append(
            f"| {_fmt(width, 0)} × {_fmt(height, 0)} m | **{_fmt(scale, 1)}** | "
            f"{_fmt(scale)} × {_fmt(scale)} m |"
        )
    lines.append("")
    return lines


def fov_table() -> list[str]:
    lines = [
        "### Odak uzaklığı → görüş açısı (36 mm sensör)",
        "",
        "| Odak | Yatay görüş açısı | Kullanım |",
        "|---|---|---|",
    ]
    usage = {
        16: "Kaçınılır — köşelerde aşırı bozulma",
        20: "Çok küçük hacim (WC, duş)",
        24: "Standart iç mekan",
        28: "Küçük oda, peyzaj",
        35: "Mutfak, detay, dış cephe",
        50: "Kütle, kompresyon",
    }
    for focal in (16, 20, 24, 28, 35, 50):
        fov = framing.horizontal_fov_deg(float(focal), SENSOR)
        lines.append(f"| {focal} mm | {_fmt(fov, 1)}° | {usage[focal]} |")
    lines.append("")
    return lines


def build_markdown() -> str:
    lines = [
        "# Mimari render — kamera hızlı referans kartı",
        "",
        "Bu karttaki **tüm sayılar** `archviz-render-kit` kütüphanesiyle hesaplanmıştır; "
        "elle yazılmamıştır. Yeniden üretmek için:",
        "",
        "```bash",
        "python tools/referans_karti.py > referans-karti.md",
        "```",
        "",
        "**Değişmez kural:** kamera yatırılmaz. Dikey kenarların düz kalması, görselin "
        "profesyonel görünmesini belirleyen tek en güçlü etkendir. Tavanı kadraja almak "
        "için kamera açısı değil `shift_y` kullanılır.",
        "",
        "---",
        "",
        "## 1. İç mekan",
        "",
    ]
    lines += interior_table(FOCAL_INTERIOR, "Standart iç mekan")
    lines += interior_table(FOCAL_INTERIOR_NARROW, "Küçük oda / detay")
    lines += [
        "**Nasıl okunur:** 6 m genişliğinde bir salonu 24 mm odakla kadraja almak için "
        "kamera **4,00 m** geride olmalı ve lens **0,092** kaydırılmalıdır. Bu iki sayı "
        "Blender'a girildiğinde dikeyler düzgün kalır ve tavan kadrajda olur.",
        "",
        "> **Beklenmedik ama doğru bir sonuç:** iki tablodaki `shift_y` sütunları "
        "birebir aynıdır. Sebebi, mesafenin de odakla birlikte ölçeklenmesidir. "
        "Sadeleştirildiğinde:",
        ">",
        "> `shift_y = (hedef merkez yüksekliği − göz yüksekliği) / kadraj genişliği`",
        ">",
        "> Yani lens kaydırması **odak uzaklığından bağımsızdır**; yalnızca hedefin göz "
        "hizasından ne kadar yukarıda olduğuna ve kadraja giren genişliğe bağlıdır. "
        "Pratikte: tavanı kadraja almak için gereken kaydırma, odayı hangi odakla "
        "çektiğinizden etkilenmez.",
        "",
        "---",
        "",
        "## 2. Dış cephe",
        "",
    ]
    lines += exterior_table()
    lines += [
        "**Nasıl okunur:** 18 m genişliğinde, 9 m yüksekliğinde bir cephede kadraja "
        "sığdıran mesafe 17,50 m; ancak yükseklik kuralı (yapı yüksekliğinin 2 katı = 18 m) "
        "daha büyük olduğu için **18 m** kullanılır. Kural, perspektif bozulmasını "
        "sınırlar.",
        "",
        "---",
        "",
        "## 3. Vaziyet planı",
        "",
    ]
    lines += site_plan_table()
    lines += [
        "**Nasıl okunur:** 62 × 45 m parselde `ortho_scale` **71,3** olur. Bu değer "
        "Blender'ın ortografik kamerasına girildiğinde parsel, %15 kenar boşluğuyla "
        "kadraja oturur ve komşu ilişkisi okunur.",
        "",
        "---",
        "",
        "## 4. Odak seçimi",
        "",
    ]
    lines += fov_table()
    lines += [
        "---",
        "",
        "## 5. Işık açıları",
        "",
        "| Amaç | Azimut | Yükseklik |",
        "|---|---|---|",
        "| Cephe, dokuyu gösteren yumuşak gölge | Cephe normalinden 30-60° sapma | 25-45° |",
        "| Peyzaj, düşen gölge ve doku | Ters yan ışık | 8-20° |",
        "| Vaziyet, kısa ve net gölge | Güneydoğu (~135°) | 60-70° |",
        "| İç mekan, pencere ışığı | Pencere yönü | 20-40° |",
        "",
        "Azimut kuzeyden saat yönünde ölçülür: kuzey 0°, doğu 90°, güney 180°, batı 270°.",
        "",
        "---",
        "",
        "## 6. Kalite profilleri",
        "",
        "| Profil | Örneklem | Çözünürlük | Ne zaman |",
        "|---|---|---|---|",
        "| `draft` | ~%6 | %50 | Kadraj ve kompozisyon kontrolü |",
        "| `preview` | %25 | %100 | Müşteri onayı |",
        "| `final` | %100 | %100 | Teslim |",
        "",
        "**Kural:** taslak aşaması geçilmeden final render alınmaz.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    sys.stdout.write(build_markdown())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
