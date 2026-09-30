---
name: peyzaj-render
description: Bahçe, sert zemin, bitkilendirme ve dış mekan kullanımını gerçekçi render etmek gerektiğinde kullanın. Düşük güneş açısıyla doku okunurluğu, bitki ölçek gerçekliği ve gölge derinliği kurallarını kapsar.
license: MIT
compatibility: archviz-render-kit deposu; Blender 4.x/5.x, Cycles.
metadata:
  author: fms0013
  version: "1.0.0"
  category: architectural-visualization
---

# Peyzaj renderı

## Ne zaman kullanılır

Yapının çevresiyle birlikte sunumu gerektiğinde: ön bahçe, arka bahçe, teras,
sert zemin, bitkilendirme ve dış mekan yaşam alanları.

## Temel kurallar

1. **Güneş 8–20° yükseklikte.** Peyzajda doku (çim, taş, kabuk) ancak yan ve
   düşük ışıkta okunur. Yüksek güneş her şeyi düzleştirir.
2. **Altın saat renk sıcaklığı 3000–3500 K.** Doğal ve davetkâr görünüm verir;
   beyaz ışık peyzajı klinik gösterir.
3. **Bitki ölçeği gerçek olmalı.** Yaygın hata: yetişkin ağacı fidan boyutunda
   modellemek veya çalıyı insan boyundan büyük yapmak. Her bitki için
   yetişkin boyut referansı kullanılır.
4. **Zemin boş bırakılmaz.** Çim, malç, döşeme ve bordür geçişleri görünmelidir;
   tek düze yeşil alan peyzaj anlatmaz.

## Adımlar

1. `presets/landscape.json` ön ayarını kullanın; `max_bounces` yüksek
   tutulmalıdır (yaprak içinden geçen ışık için varsayılan 16).
2. Kamera: göz hizası 1,60–1,75 m, odak 24–35 mm.
   Geniş bahçede 24–28 mm, teras/detayda 35 mm.
3. Güneş açısı: `sun_elevation_deg` 8–20°, azimut gölgelerin ilgiyi
   yönlendireceği yöne (genelde arkadan yan, yani ters ışık) kurulur.
4. Mevsim tutarlılığı: yaprak rengi, çiçek ve çim tonu aynı mevsime ait olmalı.
   Karışık mevsim en sık gözden kaçan gerçeklik hatasıdır.
5. Render ve kontrol:
   - Yaprak gölgeleri zemine düşüyor mu?
   - Çim dokusu kadrajda okunuyor mu, yoksa düz yeşil mi?
   - Bitki boyutları yapı ve insan ölçeğiyle tutarlı mı?
   - Sert zemin kaplaması ve bordür net mi?

## Ters ışık (backlight) kullanımı

Gün batımı yönünde çekim, bitki kenarlarında ışık saçağı (rim light) oluşturur
ve peyzajı canlı gösterir. Ancak gölge tarafı tamamen siyah kalmamalıdır;
`world_strength` 1,0–1,3 ve düşük yoğunluklu bir dolgu ışığı ile dengeleyin.

## Sık yapılan hatalar

| Hata | Sonuç | Düzeltme |
|------|-------|----------|
| Yüksek öğle güneşi | Düz, dokusuz peyzaj | 8–20° yükseklik |
| Fidan boyutunda yetişkin ağaç | Ölçek yanlış, bahçe oyuncak gibi | Yetişkin boyut referansı kullan |
| Karışık mevsim (çiçek + sarı yaprak) | Gerçeklik kırılır | Tek mevsim seç |
| Düz yeşil zemin | Peyzaj okunmaz | Çim dokusu, malç, bordür ekle |
| Ters ışıkta siyah gölge | Detay kaybolur | Dolgu ışığı ekle |

## Doğrulama

Render'ı %25 küçültüp baktığınızda yüzeyler birbirinden ayrılıyorsa (çim, taş,
ahşap ayırt edilebiliyorsa) doku okunurluğu yeterlidir. Hepsi aynı düz yeşil/gri
görünüyorsa güneş açısı çok yüksektir.