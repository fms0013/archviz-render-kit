# Kalite profilleri

Aynı sahne üç farklı profilde render edilebilir. Amaç, karar aşamalarında
gereksiz render süresi harcamamaktır.

## Profiller

| Profil | Örneklem | Çözünürlük | Denoise | Kullanım |
|--------|----------|------------|---------|----------|
| `draft` | final'in ~%6'sı | %50 | Kapalı | Kadraj, kompozisyon, ışık yönü kontrolü |
| `preview` | final'in %25'i | %100 | Açık | Müşteri onayı, ara sunum |
| `final` | Tam | %100 | Açık | Teslim |

## Ön ayar başına taban değerler

| Ön ayar | Çözünürlük | Final örneklem |
|---------|------------|----------------|
| `interior` | 1920×1080 | 512 |
| `exterior` | 2560×1440 | 768 |
| `site-plan` | 3200×3200 | 384 |
| `landscape` | 2560×1440 | 640 |

Vaziyet planında örneklem neden düşük? Ortografik, tepeden bakışta global
aydınlatma yolları kısalır ve gürültü üreten dolaylı sekme sayısı azalır.

## Kullanım

```bash
# Ön ayarı kalite profiliyle çözümle ve gör
python -m archviz_kit presets exterior --quality preview

# JSON olarak al (kendi script'inize gömmek için)
python -m archviz_kit presets exterior --quality draft --json
```

Python içinden:

```python
from archviz_kit import presets

preset = presets.resolve("interior", "preview", overrides={"samples": 200})
print(preset["resolution"], preset["samples"], preset["denoise"])
```

## Örneklem sayısı nasıl seçilir

Örneklem sayısı gürültüyü azaltır, ama doğrusal olmayan verimle:

- Gürültü, örneklem sayısının kareköküyle azalır. 4 kat örneklem = yarı gürültü.
- 256 örneklemden sonra kazanç hızla düşer; kalan gürültü genelde denoise ile
  temizlenir.
- **Kural:** önce denoise'ın temizleyemediği yapısal gürültüyü (cam, metal,
  ince gölge) gördüğünüzde örneklemi artırın; körlemesine yükseltmeyin.

## Bellek ve süre

`use_persistent_data` açıktır: sahne, kareler arasında bellekte tutulur ve
toplu render'da her kare için yeniden yükleme yapılmaz. Bellek yetersizse
(çok büyük sahnelerde) kapatılabilir; bu süreyi artırır ama çökme riskini
azaltır.

Örneklem ve çözünürlük **çarpımsal** maliyetlidir: çözünürlüğü 2 katına
çıkarmak piksel sayısını 4 katına çıkarır, yani süreyi yaklaşık 4 katına.
Bu yüzden `draft` profilinde çözünürlüğü düşürmek en etkili hızlandırmadır.

## Profil değiştirirken dikkat

Aynı çıktı klasörüne farklı profillerde render yazmak, dosya adı şablonunda
kalite alanı bulunduğu için karışıklık yaratmaz:

```
ornek-villa-a_salon-kd_interior_final_v01.png
ornek-villa-a_salon-kd_interior_draft_v01.png
```

Ayrı klasör kullanmak (`renders/taslak`, `renders/final`) yine de önerilir;
böylece yanlışlıkla taslağı teslim etme riski ortadan kalkar.