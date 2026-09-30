"""Dosya adlandırma testleri."""

import pytest

from archviz_kit import naming


def test_turkce_karakterler_sadelestiriliyor():
    assert naming.slugify("Salon Güneydoğu Işığı") == "salon-guneydogu-isigi"
    assert naming.slugify("İÇ MEKÂN") == "ic-mekan"
    assert naming.slugify("Çatı Örtüsü") == "cati-ortusu"


def test_bos_ve_ozel_karakterler():
    assert naming.slugify("") == ""
    assert naming.slugify("   ") == ""
    assert naming.slugify("a//b  c") == "a-b-c"
    assert naming.slugify("---") == ""


def test_uzunluk_sinirlanıyor():
    assert len(naming.slugify("a" * 100, max_length=10)) == 10


def test_cikti_adi_sablonu():
    assert (
        naming.output_name("Villa A", "Salon KD", "interior", "final", 1)
        == "villa-a_salon-kd_interior_final_v01.png"
    )


def test_surum_iki_hane():
    assert naming.output_name("P", "V", "exterior", "preview", 7) == "p_v_exterior_preview_v07.png"
    assert naming.output_name("P", "V", "exterior", "preview", 120).endswith("_v120.png")


def test_gecersiz_tur_hata_verir():
    with pytest.raises(ValueError):
        naming.output_name("P", "V", "kesit", "final")


def test_gecersiz_surum_hata_verir():
    with pytest.raises(ValueError):
        naming.output_name("P", "V", "interior", "final", 0)


def test_ad_cozumleme_gidis_donus():
    name = naming.output_name("Villa A", "Salon KD", "interior", "final", 3)
    parsed = naming.parse_output_name(name)
    assert parsed == {
        "project": "villa-a",
        "view": "salon-kd",
        "kind": "interior",
        "quality": "final",
        "version": 3,
    }


def test_bozuk_ad_hata_verir():
    with pytest.raises(ValueError):
        naming.parse_output_name("sadece-bir-ad.png")
    with pytest.raises(ValueError):
        naming.parse_output_name("a_b_c_d_e.png")