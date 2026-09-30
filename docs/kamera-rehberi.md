# Kamera rehberi

Mimari görselleştirmede kadraj, malzeme ve ışıktan önce gelir. Yanlış kadrajla
alınmış kusursuz bir render işe yaramaz.

## Düz kamera kuralı

Kamera **hiçbir zaman yatırılmaz**. Dikey kenarların düz kalması, bir görselin
profesyonel mi amatör mü göründüğünü belirleyen tek en güçlü etkendir.

| İstediğiniz | Yanlış yol | Doğru yol |
|-------------|-----------|-----------|
| Tavanı görmek | Kamerayı yukarı yatırmak | `shift_y` ile lens kaydırması |
| Zemini görmek | Kamerayı aşağı yatırmak | Negatif `shift_y` |
| Yüksekten bakmak | Kamerayı aşağı yatırmak | Kamerayı gerçekten yükseltmek |

`shift_y` hesabı:

```python
from archviz_kit import framing

shift = framing.shift_y_for_target(
    camera_height_m=1.55,       # kamera yüksekliği
    target_center_height_m=2.20, # kadraj merkezine gelmesi istenen yükseklik
    distance_m=5.5,              # özneye mesafe
    focal_mm=24.0,
)
```

## Odak uzaklığı seçimi

| Odak | Kullanım | Not |
|------|----------|-----|
| 16-20 mm | Çok küçük hacimler (WC, duş) | Kaçınılması gereken aralık; bozulma yüksek |
| 24 mm | Standart iç mekan | Mimari iç mekanın güvenli varsayılanı |
| 28-35 mm | Küçük oda, mutfak, detay | Daha doğal oranlar |
| 35-50 mm | Dış cephe, kütle | Perspektif bozulması düşük |
| 50 mm+ | Kompresyon, detay | Kütle bütünlüğü için |

## Mesafe hesabı

Bir öznenin kadrajı tam doldurması için gereken mesafe:

```python
from archviz_kit import framing

# 6 m genişliğindeki bir duvarı 24 mm odakla kadraja sığdırmak:
distance = framing.fit_distance_m(focal_mm=24, sensor_mm=36, subject_size_m=6)
# -> 4.0 m
```

Ters yön: "10 m mesafede ne kadar genişlik görürüm?"

```python
framing.width_at_distance_m(distance_m=10, focal_mm=24, sensor_mm=36)
# -> 15.0 m
```

## İç mekan / dış cephe perspektif tipleri

| Tip | Ne zaman | Kamera konumu |
|-----|----------|---------------|
| Tek nokta (bir kaçışlı) | Simetri, koridor, giriş aksı | Cepheye dik |
| İki nokta (iki kaçışlı) | Kütle, hacim anlatımı | Köşeye çapraz, kamera düz |
| Üç nokta | Genelde kaçınılır (dikeyler eğilir) | Yalnızca bilinçli dramatik amaçla |

## Vaziyet planı kamerası

Vaziyet **ortografik** olmalıdır; perspektif kamera plan okunurluğunu yok eder.

```python
scale = framing.ortho_scale_for_area(
    width_m=62, height_m=45,
    resolution={"width": 3200, "height": 3200},
    margin=1.15,
)
# -> 71.3
```

Blender'da `ortho_scale` değeri, `sensor_fit` ile seçilen eksene karşılık gelir;
kare çözünürlükte her iki eksen aynıdır. Kenar boşluğu için `margin` 1,10-1,20
arasında tutulur.

## Azimut ve yükseklik kabulü

Bu kit boyunca:

- `+X` doğu, `+Y` kuzey, `+Z` yukarı.
- Azimut **kuzeyden saat yönünde**: kuzey 0°, doğu 90°, güney 180°, batı 270°.
- Yükseklik ufuktan ölçülür: 0° ufuk, 90° tam tepede.

| Amaç | Azimut | Yükseklik |
|------|--------|-----------|
| Cephe, yumuşak doku | Cephe normalinden 30-60° sapma | 25-45° |
| Peyzaj, doku ve düşen gölge | Ters yan ışık | 8-20° |
| Vaziyet, kısa net gölge | Güneydoğu (~135°) | 60-70° |
| İç mekan, pencere ışığı | Pencere yönü | 20-40° |

## Sık yapılan kadraj hataları

1. **Oda merkezine simetrik bakış** — düz ve derinliksiz görünür. Köşeden bakış
   ve bir ön plan nesnesi (bitki, sandalye, korkuluk) eklemek derinlik verir.
2. **Ufuk çizgisini kadrajın tam ortasına koymak** — görüntüyü ikiye böler.
   İç mekanda ufku alt 1/3'e, dış cephede üst 1/3'e yerleştirin.
3. **Zeminin boş kalması** — yapı havada duruyormuş gibi görünür.
4. **Kadrajda çok gökyüzü** — cephe küçülür ve zayıflar; 60/40 cephe/gökyüzü
   oranı hedeflenir.