"""Kadraj doğrulama diyagramı üretir (plan görünüş, SVG).

Render almadan önce kameranın odaya sığıp sığmadığını gösterir.

Kullanım::

    python tools/kadraj_diagram.py --genislik 6.0 --derinlik 5.5 --odak 24 --cikti kadraj.svg
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from archviz_kit import diagram  # noqa: E402


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Kadraj doğrulama diyagramı (SVG) üretir."
    )
    parser.add_argument("--genislik", type=float, required=True, help="Duvar genişliği (m)")
    parser.add_argument("--derinlik", type=float, required=True, help="Oda derinliği (m)")
    parser.add_argument("--odak", type=float, default=24.0, help="Odak uzaklığı (mm)")
    parser.add_argument("--sensör", type=float, default=36.0, help="Sensör genişliği (mm)")
    parser.add_argument("--baslik", default=None, help="Diyagram başlığı")
    parser.add_argument("--cikti", default=None, help="SVG çıktı yolu")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    analysis = diagram.kadraj_analizi(
        room_width_m=args.genislik,
        room_depth_m=args.derinlik,
        focal_mm=args.odak,
        sensor_width_mm=args.sensör,
    )

    title = args.baslik or f"{args.genislik:.1f} m duvar · {args.odak:.0f} mm"

    # Türkçe karakterler SVG içinde sorun çıkarmaz; dosya adı için sadeleştir.
    from archviz_kit.naming import slugify

    output = args.cikti or f"kadraj-{slugify(title)}.svg"
    svg = diagram.plan_view_svg(analysis, title=title)

    with open(output, "w", encoding="utf-8") as handle:
        handle.write(svg)

    status = "UYGUN" if analysis["fits"] else "UYGUN DEĞİL"
    print(f"Kadraj: {status}")
    print(f"  gereken mesafe : {analysis['required_distance_m']:.2f} m")
    print(f"  oda derinliği  : {analysis['room_depth_m']:.2f} m")
    print(f"  kadraja giren  : {analysis['framed_width_m']:.2f} m")
    print(f"  doluluk oranı  : {analysis['room_fill_ratio'] * 100:.0f}%")
    if not analysis["fits"]:
        print(f"  öneri          : odağı {analysis['max_focal_mm']:.0f} mm veya altına düşürün")
    print(f"  diyagram       : {output}")
    return 0 if analysis["fits"] else 1


if __name__ == "__main__":
    raise SystemExit(main())