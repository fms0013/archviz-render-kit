---
name: vaziyet-plani-render
description: Bir parselin vaziyet planını tepeden dik (ortografik) bakışla render etmek gerektiğinde kullanın. Yerleşim, bahçe sınırı, otopark ve komşu ilişkilerinin okunması için kadraj, ölçek ve gölge kurallarını kapsar.
license: MIT
compatibility: archviz-render-kit deposu; Blender 4.x/5.x, Cycles. Ortografik kamera zorunludur.
metadata:
  author: fms0013
  version: "1.0.0"
  category: architectural-visualization
---

# Vaziyet planı renderı

## Ne zaman kullanılır

Parsel ölçeğinde yerleşimin gösterilmesi gerektiğinde: yapının parsel içindeki
konumu, bahçe kullanımı, araç girişi, komşu parseller ve kot ilişkileri.

## Temel kurallar

1. **Ortografik kamera zorunludur.** Perspektif kamera kullanılırsa yapı
   eğilir ve plan okunmaz. `camera.type = "ORTHO"` ve tam tepeden bakış
   (`pitch_deg = 90`) kullanılır.
2. **Kuzey yukarı kabul edilir.** Kadraj döndürülmez; gölge yönü bu kabule göre
   kurulur. Kuzey oku eklenmelidir.
3. **Ölçek okunabilir olmalı.** `ortho_scale` değeri parselin en büyük kenarını
   %10–15 kenar boşluğuyla kapsamalıdır. Çok dar kadraj komşu ilişkisini
   kaybettirir; çok geniş kadraj yapıyı küçültür.
4. **Yükseklikler baskılanır.** Vaziyet, plan okuma aracıdır; bina
   yükseklikleri gölge ve kütle olarak okunmalı, cephe detayı verilmemelidir.

## Adımlar

1. `presets/site-plan.json` ön ayarını kullanın; çözünürlük kare olmalıdır
   (varsayılan 3200×3200).
2. Kadraj ölçeğini hesaplayın:
   `framing.ortho_scale_for_area(parsel_en, parsel_boy, {"width":3200,"height":3200}, margin=1.1)`
3. Gölge için güneşi kurun: vaziyette gölge **kısa ve yönlü** olmalı →
   `sun_elevation_deg` 60–70°, `sun_azimuth_deg` güneydoğu (~135°).
4. Komşu parseller, yollar ve yeşil alanlar modele girmelidir; boş zemin
   vaziyeti okunamaz hâle getirir.
5. Render ve kontrol:
   - Parsel sınırları net okunuyor mu?
   - Yapı gölgesi parsel dışına taşıyor mu? (Taşıyorsa güneş açısı yanlış)
   - Otopark/araç girişi görünüyor mu?
   - Kuzey oku kadraja girdi mi?

## Ölçek ve etiket

Teslim edilecek vaziyet görselinde ölçek çubuğu veya ölçek notu bulunmalıdır.
Yalnızca render vermek, ölçek bilgisi olmadan teknik olarak eksiktir; görselin
yanında yazılı ölçek (1/200, 1/500 gibi) verilir.

## Sık yapılan hatalar

| Hata | Sonuç | Düzeltme |
|------|-------|----------|
| Perspektif kamera | Eğik, okunamayan plan | `ORTHO` kullan |
| Düşük güneş açısı | Uzun gölgeler planı kirletir | 60–70° yükseklik |
| Kadraj döndürme | Kuzey oku yanlış olur | Döndürme, komşu kütle veya oku döndür |
| Boş komşu parseller | Parsel ilişkisi okunmaz | Komşu kütle ve yolları ekle |
| Zemin dokusuz | Ölçek algısı kaybolur | Döşeme/sert zemin dokusu ekle |

## Doğrulama

Render alındıktan sonra: yapının taban izi, parsel sınırı ve yol hattı aynı
karede net görünüyor mu? Görünmüyorsa `ortho_scale` veya kamera yüksekliği
yanlıştır.