---
name: dis-cephe-render
description: Bir yapının dış cephesini gün ışığında gerçekçi render etmek gerektiğinde kullanın. Güneş açısı seçimi, cephe gölgeleme dengesi, silüet ve kadraj kuralları ile dış mekan malzeme okunabilirliğini kapsar.
license: MIT
compatibility: archviz-render-kit deposu; Blender 4.x/5.x, Cycles.
metadata:
  author: fms0013
  version: "1.0.0"
  category: architectural-visualization
---

# Dış cephe renderı

## Ne zaman kullanılır

Yapının dış cephesinin, giriş aksının veya kütle silüetinin sunum kalitesinde
görselleştirilmesi istendiğinde.

## Temel kurallar

1. **Cephe yarı gölgede olmalı.** Güneş tam karşıdan gelirse cephe düzleşir,
   doku ve derinlik kaybolur. Azimut, cephe normali ile 30–60° arasında kalsın.
2. **Güneş yüksekliği 25–45°.** Daha düşük açıda gölgeler uzayıp cepheyi kirletir;
   daha yüksek açıda saçak ve balkon gölgeleri kaybolur, cephe yassı görünür.
3. **İki nokta / tek nokta perspektif bilinçli seçilir.** Kütleyi anlatmak için
   iki nokta (köşe görünümü), simetriyi anlatmak için tek nokta kullanın.
   Her iki durumda da kamera **düz** tutulur, dikeyler korunur.
4. **Gökyüzü boş bırakılmaz.** Cephe/gökyüzü oranı genelde 60/40 olacak şekilde
   kadraj kurulur; boş gökyüzü görüntüyü zayıflatır.

## Adımlar

1. `presets/exterior.json` ön ayarını seçin (`final` teslim, `preview` onay).
2. Kamera mesafesi: yapı yüksekliğinin en az **2 katı**, genişlik baskınsa
   `framing.fit_distance_m(35, 36, yapı_genişliği)` sonucu kullanılır.
3. Güneş açısını seçin (`sun_azimuth_deg`, `sun_elevation_deg`) ve gölgenin
   cepheyi nasıl böldüğünü draft profiliyle hızlıca kontrol edin.
4. Uygula ve render al:
   `blender -b sahne.blend --python blender/apply_preset.py -- --preset exterior --quality draft --out renders/onizleme.png --render`
5. Onaydan sonra `--quality final` ile tekrar alın.

## Gölge yönü ve kuzey uyumu

Vaziyet planıyla tutarlılık zorunludur: vaziyette kuzey yukarıysa, cephe
renderındaki gölge yönü de aynı kuzey kabulüne uymalıdır. Aksi hâlde aynı
projenin iki görseli birbiriyle çelişir ve teknik olarak yanlış okunur.

## Malzeme okunabilirliği

| Malzeme | Doğru okunma koşulu |
|---------|---------------------|
| Sıva / boya | Yumuşak gradyan gölge; sert gölge sıvayı beton gibi gösterir |
| Ahşap kaplama | Güneş yönüne göre lif dokusu okunur; tam karşı ışıkta kaybolur |
| Cam | Yansıma açısı kritik; cam önünde ağaç/komşu yansıması olmalı, boş gökyüzü camı delik gösterir |
| Beton / taş | Yan ışık dokuyu ortaya çıkarır; bu yüzden 30–60° azimut kuralı önemlidir |

## Sık yapılan hatalar

| Hata | Sonuç | Düzeltme |
|------|-------|----------|
| Güneş cepheye tam karşı | Yassı, dokusuz cephe | Azimutu 30–60° kaydır |
| Kamera yapıya çok yakın | Aşırı perspektif, eğik dikeyler | Mesafeyi yapı yüksekliğinin 2 katına çıkar |
| Öğle güneşi (90°) | Saçak gölgesi yok, cephe ıslak görünür | 30–40° yükseklik kullan |
| Kadrajda çok gökyüzü | Yapı küçük ve zayıf | Cephe/gökyüzü oranını 60/40 yap |
| Zemin boş | Yapı havada duruyor | Peyzaj, sert zemin veya komşu kütle ekle |

## Doğrulama

Silüet kontrolü: render'ı küçültüp siyah-beyaz silüete çevirdiğinizde kütle
okunuyorsa kadraj doğrudur. Okunmuyorsa gökyüzü oranı veya mesafe yanlıştır.