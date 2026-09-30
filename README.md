# archviz-render-kit

**Mimari görselleştirme için render ön ayarları, kamera matematiği ve çekim listesi üreticisi.**
İç mekan, dış cephe, vaziyet planı ve peyzaj renderlarını tutarlı, tekrarlanabilir ve
ölçülebilir hâle getirir.

> Bu bir "tek tuşla render" aracı değildir. Mimari kararlar sizde kalır; kit,
> kamera/ışık/kalite kararlarını standartlaştırır ve hesabı sizin yerinize yapar.

---

## Neden var

Mimari render'da en pahalı hata kadrajdır: yanlış kadrajla alınmış kusursuz bir
render işe yaramaz ve saatlerce render süresi boşa gider. Ayrıca her projede
kamera yüksekliği, odak, güneş açısı ve örneklem sayısı yeniden "hissedilerek"
seçilirse sonuçlar projeden projeye tutarsız olur.

Bu kit üç şeyi standartlaştırır:

1. **Kadraj matematiksel olarak hesaplanır** — mesafe, odak, lens kaydırması
   tahmin edilmez, formülle bulunur.
2. **Dört render türü için ön ayar tanımlıdır** — iç mekan, dış cephe, vaziyet, peyzaj.
3. **Çekim listesi önceden yazılır** — hangi karenin hangi ayarla ve hangi
   dosya adıyla üretileceği render'dan önce bellidir.

---

## Kurulum

Gereksinim: Python 3.9+ (Blender yalnızca gerçek render için gereklidir).

```bash
git clone https://github.com/fms0013/archviz-render-kit.git
cd archviz-render-kit
python3 -m venv .venv && . .venv/bin/activate
python -m pip install -e '.[dev]'
```

Blender'ı ayrıca kurun ve `blender` komutunu PATH'e ekleyin. Bu kit, sistem
Python'u ile Blender'ın kendi Python'unu ayrı tutar.

---

## Hızlı başlangıç

```bash
# 1) Ön ayarları listele
python -m archviz_kit presets

# 2) Tek bir ön ayarı kalite profiliyle çözümle
python -m archviz_kit presets interior --quality draft

# 3) Örnek projeden çekim listesi üret
python -m archviz_kit shotlist examples/project.example.json \
    --out shotlist.json --markdown cekim-listesi.md
```

Çıktı:

| # | Kimlik | Tür | Kalite | Örneklem | Çözünürlük | Dosya |
|---|--------|-----|--------|----------|------------|-------|
| 1 | `salon-kd` | interior | final | 512 | 1920×1080 | `ornek-villa-a_salon-kd_interior_final_v01.png` |
| 3 | `kuzey-cephe` | exterior | final | 768 | 2560×1440 | `ornek-villa-a_kuzey-cephe_exterior_final_v01.png` |
| 5 | `vaziyet-kuzey` | site-plan | final | 384 | 3200×3200 | `ornek-villa-a_vaziyet-kuzey_site-plan_final_v01.png` |

Blender ile uygulama:

```bash
# Tek kare
blender -b sahne.blend --python-exit-code 1 --python blender/apply_preset.py -- \
    --preset interior --quality final --camera salon-kd \
    --out renders/salon.png --render

# Tüm çekim listesi (taslak önce)
blender -b sahne.blend --python-exit-code 1 --python blender/batch_render.py -- \
    --shotlist shotlist.json --outdir renders/taslak
```

---

## Dört render türü

| Tür | Ön ayar | Varsayılan kamera | Kritik kural |
|-----|---------|-------------------|--------------|
| **İç mekan** | `interior` | 24 mm, 1,55 m, düz | Kamera eğilmez; tavan için `shift_y` |
| **Dış cephe** | `exterior` | 35 mm, 1,65 m, düz | Güneş cephe normalinden 30-60° sapmalı |
| **Vaziyet** | `site-plan` | Ortografik, tepeden | Perspektif kamera planı okunmaz yapar |
| **Peyzaj** | `landscape` | 28 mm, 1,70 m | Güneş 8-20°; düşük ışık dokuyu gösterir |

Ayrıntılı kurallar ve sık yapılan hatalar `skills/` klasöründeki ajan
becerilerinde ve `docs/` altındadır.

---

## Kalite profilleri

| Profil | Örneklem | Çözünürlük | Denoise | Kullanım |
|--------|----------|------------|---------|----------|
| `draft` | ~%6 | %50 | Kapalı | Kadraj ve kompozisyon kontrolü |
| `preview` | %25 | %100 | Açık | Müşteri onayı |
| `final` | %100 | %100 | Açık | Teslim |

**Kural: taslak aşaması geçilmeden final render alınmaz.** Kadraj hatasını final
kalitede fark etmek, saatlerce render'ı çöpe atar.

---

## Depo yapısı

```
archviz-render-kit/
├── presets/                 # 4 render türü için JSON ön ayarlar
│   ├── interior.json
│   ├── exterior.json
│   ├── site-plan.json
│   └── landscape.json
├── archviz_kit/             # Saf Python çekirdek (Blender gerektirmez)
│   ├── presets.py           # ön ayar yükleme + kalite profili çözümleme
│   ├── framing.py           # odak/FOV, mesafe, lens kaydırma, ortografik ölçek
│   ├── shotlist.py          # proje tanımı -> çekim listesi
│   ├── naming.py            # dosya adı şablonu (Türkçe karakter desteği)
│   ├── bridge.py            # Blender sahnesine uygulama (test edilebilir)
│   └── cli.py               # komut satırı arayüzü
├── blender/                 # Blender içinde çalışan script'ler
│   ├── apply_preset.py      # ön ayarı açık sahneye uygular
│   └── batch_render.py      # çekim listesini sırayla render eder
├── skills/                  # ajan becerileri (SKILL.md)
├── docs/                    # iş akışı, kamera rehberi, kalite profilleri
├── examples/                # örnek proje tanımı + üretilmiş çekim listesi
└── tests/                   # 68 birim testi
```

---

## Ajan becerileri

`skills/` klasöründeki dört dosya, Agent Skills formatındadır ve Claude Code,
Codex, Cursor, OpenCode gibi araçlara kopyalanabilir:

```bash
cp -r skills/* ~/.claude/skills/     # veya aracınızın skills klasörü
```

| Beceri | Ne zaman devreye girer |
|--------|------------------------|
| `ic-mekan-render` | İç mekan görselleştirmesi istendiğinde |
| `dis-cephe-render` | Dış cephe / kütle sunumu istendiğinde |
| `vaziyet-plani-render` | Parsel ölçeğinde yerleşim gösterimi istendiğinde |
| `peyzaj-render` | Bahçe ve dış mekan yaşam alanı istendiğinde |

Her beceri; kamera kararları, ışık kurulumu, sık yapılan hatalar tablosu ve
doğrulama adımlarını içerir.

---

## Kamera matematiği

```python
from archviz_kit import framing

# 24 mm odak, 36 mm sensör -> yatay görüş açısı
framing.horizontal_fov_deg(24)                     # 73.74°

# 6 m genişliği kadraja sığdırmak için mesafe
framing.fit_distance_m(24, 36, 6)                  # 4.0 m

# 10 m mesafede kadrajın kapsadığı genişlik
framing.width_at_distance_m(10, 24, 36)            # 15.0 m

# Düz kamera ile tavanı kadraja almak için lens kaydırması
framing.shift_y_for_target(1.55, 2.20, 5.5, 24)    # ~0.079

# Vaziyet planı için ortografik ölçek
framing.ortho_scale_for_area(62, 45, {"width": 3200, "height": 3200}, margin=1.15)
```

---

## Koordinat ve açı kabulü

- `+X` doğu, `+Y` kuzey, `+Z` yukarı.
- Azimut **kuzeyden saat yönünde**: kuzey 0°, doğu 90°, güney 180°, batı 270°.
- Güneş yüksekliği ufuktan: 0° ufuk, 90° tepede.
- Vaziyet planında kuzey yukarı kabul edilir ve gölge yönü bu kabulle tutarlı
  olmak zorundadır.

---

## Test durumu

```bash
python -m pytest -q      # 68 test
```

**Dürüst durum bildirimi:**

- Saf Python çekirdeği (ön ayarlar, kamera matematiği, çekim listesi,
  adlandırma, Blender köprü mantığı) **68 birim testiyle doğrulanmıştır** ve
  Blender kurulumu gerektirmez.
- `blender/` altındaki iki script, Blender'ın kendi çalışma zamanını
  gerektirdiği için **henüz gerçek bir Blender oturumunda çalıştırılmamıştır**.
  Mantıkları sahte nesnelerle test edilmiştir, ancak ilk gerçek çalıştırmada
  doğrulanmaları gerekir:

  ```bash
  blender -b sahne.blend --python-exit-code 1 --python blender/apply_preset.py -- \
      --preset interior --quality draft --render
  ```

  Beklenen çıktı: `[archviz] Ön ayar: İç mekan · Taslak` satırı ve ardından
  render. Hata alırsanız Blender sürümünü (`blender --version`) bildirin.

---

## Yol haritası

- [ ] Blender script'leri için gerçek sahne üzerinde uçtan uca doğrulama
- [ ] `--device` bayrağıyla GPU (CUDA/OptiX/HIP) profilleri
- [ ] Çekim listesinden otomatik kamera yerleştirme (sahne kameraları henüz elle
      adlandırılır)
- [ ] Vaziyet planı için kuzey oku ve ölçek çubuğu üreteci
- [ ] Render sonrası otomatik kontrol (dikey eğim tespiti, patlama tespiti)

---

## Lisans

MIT — bkz. [LICENSE](LICENSE).
