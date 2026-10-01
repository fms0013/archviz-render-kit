"""Kadraj analizi ve SVG diyagram testleri."""

import pytest

from archviz_kit import diagram


def test_sigan_kadraj_uygun_isaretlenir():
    # 6 m duvar, 24 mm odak -> 4,00 m gerekir; oda 5,5 m derin -> sığar
    analysis = diagram.kadraj_analizi(6.0, 5.5, 24.0)
    assert analysis["fits"] is True
    assert analysis["required_distance_m"] == pytest.approx(4.0)
    assert analysis["camera_distance_m"] == pytest.approx(4.0)
    assert analysis["framed_width_m"] == pytest.approx(6.0)


def test_dar_odada_kadraj_sigmaz():
    # 6 m duvar, 24 mm odak 4,00 m ister ama oda sadece 3 m derin
    analysis = diagram.kadraj_analizi(6.0, 3.0, 24.0)
    assert analysis["fits"] is False
    assert analysis["camera_distance_m"] == pytest.approx(3.0)
    # 3 m mesafede kadraja 4,50 m girer -> duvarın 6 m'si sığmaz
    assert analysis["framed_width_m"] == pytest.approx(4.5)
    assert analysis["room_fill_ratio"] > 1.0


def test_odanin_izin_verdigi_en_uzun_odak():
    # f = sensor * derinlik / genislik = 36 * 3 / 6 = 18 mm
    analysis = diagram.kadraj_analizi(6.0, 3.0, 24.0)
    assert analysis["max_focal_mm"] == pytest.approx(18.0)


def test_doluluk_orani_tam_kadrajda_bir():
    analysis = diagram.kadraj_analizi(6.0, 4.0, 24.0)
    assert analysis["room_fill_ratio"] == pytest.approx(1.0, abs=0.01)


def test_gorus_acisi_dogru_hesaplaniyor():
    analysis = diagram.kadraj_analizi(6.0, 5.0, 24.0)
    assert analysis["horizontal_fov_deg"] == pytest.approx(73.74, abs=0.01)


@pytest.mark.parametrize(
    "args",
    [
        (0.0, 5.0, 24.0),
        (6.0, 0.0, 24.0),
        (6.0, 5.0, 0.0),
    ],
)
def test_gecersiz_girdiler_hata_verir(args):
    with pytest.raises(ValueError):
        diagram.kadraj_analizi(*args)


def test_svg_gecerli_yapi_iceriyor():
    analysis = diagram.kadraj_analizi(6.0, 5.5, 24.0)
    svg = diagram.plan_view_svg(analysis, title="Test")
    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    assert "Test" in svg
    assert "kamera" in svg
    assert "KADRAJ UYGUN" in svg


def test_svg_sigmayan_kadrajda_cozum_onerir():
    analysis = diagram.kadraj_analizi(6.0, 3.0, 24.0)
    svg = diagram.plan_view_svg(analysis)
    assert "KADRAJ UYGUN DEĞİL" in svg
    assert "18 mm" in svg


def test_svg_olculeri_tutarli():
    """Kadraj genişliği, duvar hizasındaki koni genişliğine eşit olmalı."""
    analysis = diagram.kadraj_analizi(6.0, 5.5, 24.0)
    svg = diagram.plan_view_svg(analysis)
    assert f"kadraja giren: {analysis['framed_width_m']:.2f} m" in svg
    assert f"{analysis['camera_distance_m']:.2f} m" in svg


def test_svg_etiketleri_cakismaz():
    """Bilgi paneli satırları ve öneri metni panel sınırları içinde kalmalı."""
    analysis = diagram.kadraj_analizi(6.0, 3.0, 24.0)
    svg = diagram.plan_view_svg(analysis)

    panel_bottom = diagram.PANEL_TOP + diagram.PANEL_HEIGHT
    for line in svg.splitlines():
        if "font-size" not in line or "y=" not in line:
            continue
        y_value = float(line.split('y="', 1)[1].split('"', 1)[0])
        assert y_value < diagram.CANVAS_HEIGHT, f"metin tuvalin dışında: {y_value}"

    suggestion_y = diagram.PANEL_TOP + 196
    last_row_y = diagram.PANEL_TOP + 72 + 3 * 26
    assert suggestion_y > last_row_y, "öneri metni son satırla çakışıyor"
    assert suggestion_y < panel_bottom
