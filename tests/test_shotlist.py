"""Çekim listesi üretimi testleri."""

import pytest

from archviz_kit import shotlist

PROJE = {
    "project": "Villa A",
    "default_quality": "final",
    "views": [
        {
            "id": "salon-kd",
            "kind": "interior",
            "title": "Salon — güneydoğu",
            "camera": {"eye_height_m": 1.55, "distance_m": 5.0, "target_center_height_m": 2.1},
        },
        {
            "id": "kuzey-cephe",
            "kind": "exterior",
            "camera": {"distance_m": 20.0, "subject_width_m": 14.0, "subject_height_m": 9.0},
            "lighting": {"sun_azimuth_deg": 150.0, "sun_elevation_deg": 40.0},
        },
        {
            "id": "vaziyet",
            "kind": "site-plan",
            "camera": {"area_width_m": 55.0, "area_height_m": 40.0},
        },
    ],
}


def test_cekim_listesi_uretiliyor():
    result = shotlist.build_shotlist(PROJE)
    assert result["shot_count"] == 3
    assert [shot["id"] for shot in result["shots"]] == ["salon-kd", "kuzey-cephe", "vaziyet"]


def test_dosya_adlari_tutarli():
    result = shotlist.build_shotlist(PROJE)
    assert result["shots"][0]["output"] == "villa-a_salon-kd_interior_final_v01.png"
    assert result["shots"][2]["output"] == "villa-a_vaziyet_site-plan_final_v01.png"


def test_ic_mekan_shift_y_hesaplaniyor():
    result = shotlist.build_shotlist(PROJE)
    camera = result["shots"][0]["camera"]
    assert camera["focal_length_mm"] == 24.0
    assert camera["distance_m"] == pytest.approx(5.0)
    # 24 * ((2.1 - 1.55) / 5) / 36
    assert camera["shift_y"] == pytest.approx(0.0733, abs=0.0005)


def test_ic_mekan_odak_degistirilebilir():
    proje = {
        "project": "P",
        "views": [
            {
                "id": "mutfak",
                "kind": "interior",
                "camera": {"distance_m": 4.0, "focal_mm": 35.0, "target_center_height_m": 1.6},
                "overrides": {"samples": 128},
            }
        ],
    }
    shot = shotlist.build_shotlist(proje)["shots"][0]
    assert shot["camera"]["focal_length_mm"] == 35.0
    assert shot["samples"] == 128


def test_vaziyet_ortografik_olcek_hesaplaniyor():
    result = shotlist.build_shotlist(PROJE)
    camera = result["shots"][2]["camera"]
    assert camera["ortho_scale_m"] == pytest.approx(60.5)


def test_uzaklik_ozneden_hesaplanabiliyor():
    proje = {
        "project": "P",
        "views": [
            {
                "id": "cephe",
                "kind": "exterior",
                "camera": {"subject_width_m": 14.0},
            }
        ],
    }
    camera = shotlist.build_shotlist(proje)["shots"][0]["camera"]
    # 35 mm odak, 36 mm sensör, 14 m genişlik -> 35*14/36 = 13.61 m
    assert camera["distance_m"] == pytest.approx(13.611, abs=0.01)


def test_kadraja_sigmayan_ozne_uyari_uretiyor():
    proje = {
        "project": "P",
        "views": [
            {
                "id": "dar",
                "kind": "interior",
                "camera": {"distance_m": 3.0, "subject_width_m": 12.0},
            }
        ],
    }
    shot = shotlist.build_shotlist(proje)["shots"][0]
    assert any("kadraja sığmıyor" in warning for warning in shot["warnings"])


def test_vaziyet_alan_verilmezse_uyari():
    proje = {
        "project": "P",
        "views": [{"id": "v", "kind": "site-plan", "camera": {}}],
    }
    shot = shotlist.build_shotlist(proje)["shots"][0]
    assert any("area_width_m" in warning for warning in shot["warnings"])


def test_gecersiz_tur_hata_verir():
    with pytest.raises(ValueError):
        shotlist.build_shotlist(
            {"project": "P", "views": [{"id": "x", "kind": "kesit"}]}
        )


def test_tekrarlanan_kimlik_hata_verir():
    with pytest.raises(ValueError):
        shotlist.build_shotlist(
            {
                "project": "P",
                "views": [
                    {"id": "a", "kind": "interior"},
                    {"id": "a", "kind": "exterior"},
                ],
            }
        )


def test_bos_gorunum_listesi_hata_verir():
    with pytest.raises(ValueError):
        shotlist.build_shotlist({"project": "P", "views": []})


def test_proje_adi_zorunlu():
    with pytest.raises(ValueError):
        shotlist.build_shotlist({"views": [{"id": "a", "kind": "interior"}]})


def test_markdown_cikisi_tablo_iceriyor():
    md = shotlist.render_markdown(shotlist.build_shotlist(PROJE))
    assert "# Çekim listesi — Villa A" in md
    assert "| 1 | `salon-kd` |" in md
    assert "Toplam **3** görünüm." in md


def test_isik_degerleri_cekim_listesine_geciyor():
    result = shotlist.build_shotlist(PROJE)
    lighting = result["shots"][1]["lighting"]
    assert lighting["sun_azimuth_deg"] == 150.0
    assert lighting["sun_elevation_deg"] == 40.0