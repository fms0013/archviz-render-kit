"""Birleşik komut satırı arayüzü.

Kullanım::

    python -m archviz_kit presets                 # ön ayarları listeler
    python -m archviz_kit presets interior --quality draft
    python -m archviz_kit shotlist proje.json --out shotlist.json --markdown shotlist.md
"""

from __future__ import annotations

import sys

from archviz_kit import presets, shotlist

USAGE = """archviz-kit — mimari render yardımcıları

Komutlar:
  presets [ad] [--quality draft|preview|final] [--json]
      Ön ayarları listeler veya birini çözümler.

  shotlist proje.json [--out cikti.json] [--markdown tablo.md]
      Proje tanımından çekim listesi üretir.

Örnek:
  python -m archviz_kit shotlist examples/project.example.json --markdown cekim-listesi.md
"""


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)

    if not arguments or arguments[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0

    command, rest = arguments[0], arguments[1:]

    if command == "presets":
        sys.argv = ["archviz-kit presets", *rest]
        return presets._main()

    if command == "shotlist":
        sys.argv = ["archviz-kit shotlist", *rest]
        return shotlist._main()

    print(f"Bilinmeyen komut: {command}\n")
    print(USAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())