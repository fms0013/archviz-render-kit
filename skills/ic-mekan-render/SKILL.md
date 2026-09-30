---
name: ic-mekan-render
description: Mimari bir iç mekanı (salon, mutfak, yatak odası) Blender ile gerçekçi render etmek gerektiğinde kullanın. Kamera yüksekliği, odak seçimi, lens kaydırması ve iç mekan ışıklandırması için mimari pratiğe uygun kurallar içerir.
license: MIT
compatibility: archviz-render-kit deposu; Blender 4.x/5.x, Cycles. Blender kurulu değilse yalnızca çekim listesi planlaması için kullanılabilir.
metadata:
  author: fms0013
  version: "1.0.0"
  category: architectural-visualization
---

# İç mekan renderı

## Ne zaman kullanılır

Bir iç mekanın (salon, mutfak, yatak odası, koridor) fotoğraf gerçekliğinde
görselleştirmesi istendiğinde. Amaç "geniş ve ferah ama bozulmamış" görüntüdür;
geniş açı ile gerçeklik arasındaki denge bu işin özüdür.

## Temel kurallar

1. **Kamera eğilmez.** Göz hizası 1,50–1,60 m. Tavanı veya zemini kadraja almak
   için kamerayı yatırmayın; `shift_y` kullanın. Kamera yatırılırsa dikey duvar
   ve kapı kenarları eğilir ve görüntü amatör görünür.
2. **Odak 20–28 mm.** 24 mm mimari iç mekan için güvenli aralıktır. 16 mm altı
   köşelerde aşırı perspektif bozulması yapar; 35 mm'yi yalnızca küçük hacimlerde
   (banyo, niş) veya detay karelerinde kullanın.
3. **Bir kare, bir konu.** Her karede birincil mobilya/aks vurgulanır; oda
   merkezine simetrik bakış, kompozisyonu zayıflatır. Köşeden bakış tercih edin.
4. **Pencere patlamaz.** Dış mekan parlak, iç mekan karanlık kalır. Bunu
   pozlamayı düşürerek değil, pencere önüne dolgu ışığı ve tavan-detay
   aydınlatması ekleyerek dengeleyin.

## Adımlar

1. `presets/interior.json` ön ayarını `final` profiliyle çözümleyin.
2. Kamera mesafesini belirleyin: `framing.fit_distance_m(odak, 36, oda_genişliği)`.
   Oda kadraja sığmıyorsa mesafeyi artırın; odak kısaltmayı son çare olarak
   kullanın.
3. `framing.shift_y_for_target(kamera_yüksekliği, hedef_merkez_yüksekliği, mesafe, odak)`
   ile lens kaydırmasını hesaplayın. Hedef merkez yüksekliği genelde 1,9–2,2 m.
4. Sahneye uygulayın:
   `blender -b sahne.blend --python blender/apply_preset.py -- --preset interior --quality final --camera salon-kd --out renders/salon.png --render`
5. Render sonrası kontroller:
   - Dikey kenarlar düzgün mü? (duvar köşesi, kapı kasası)
   - Pencere içi tamamen beyaz patlamış mı?
   - Gölgeler yumuşak ama yönlü mü? (tek sert gölge = yapay görünüm)
   - Zemin yansıması aşırı mı?

## Işık kurulumu

- **Ana ışık:** pencere yönünden gelen gün ışığı; `world_strength` 0,3–0,5.
- **Dolgu:** pencere karşısına 1 adet geniş alan ışığı, gücü ana ışığın ~%30'u.
- **Vurgu:** tavan kirişi veya niş varsa 2–3 küçük alan ışığı, 4000K.
- Renk sıcaklığı 3800–4200 K aralığı iç mekanda doğal durur.

## Sık yapılan hatalar

| Hata | Sonuç | Düzeltme |
|------|-------|----------|
| Kamerayı yatırmak | Eğik dikeyler | Kamerayı düz tut, `shift_y` kullan |
| 16 mm odak | Köşelerde lastik görünüm | 24 mm'ye çık, mesafe ekle |
| Sadece pencere ışığı | İç mekan siyah, pencere patlak | Dolgu ışığı + pozlama dengesi |
| Geniş `filter_size` | Yumuşak ölü görüntü | 1,5 civarında tut |
| Tüm mobilya merkezde | Düz, derinliksiz kompozisyon | Köşeden bakış, ön plan nesnesi |

## Doğrulama

```bash
python3 -m archviz_kit shotlist proje.json --markdown
python3 -m pytest tests/ -q
```

Kamera değerleri çekim listesinde görünmeli; `shift_y` sıfırdan farklı olmalı ve
uyarı listesi boş olmalıdır.
