# Uçtan uca iş akışı

Bu belge, bir mimari projede görselleştirmenin baştan sona nasıl yürütüleceğini
tanımlar. Amaç, her projede aynı sırayı izleyerek teslim kalitesini
tekrarlanabilir kılmaktır.

## Aşama 0 — Girdi toplama

Görselleştirmeye başlamadan önce şu üç şey netleşir:

| Girdi | Neden gerekli |
|-------|----------------|
| Ölçülü plan / kesit | Ölçek ve oran yanlışsa render ne kadar iyi olursa olsun işe yaramaz |
| Malzeme kararları | Cephe kaplaması, döşeme, doğrama rengi |
| Sunum amacı | Onay mı, pazarlama mı, ruhsat eki mi — kalite profili buna göre seçilir |

Eksik bilgi varsa **varsayım olarak işaretlenir**, sessizce doldurulmaz.
Varsayımların listesi teslimle birlikte verilir.

## Aşama 1 — Çekim planı (shot list)

Render almadan önce hangi karelerin alınacağı yazılı olarak belirlenir. Bu,
en çok zaman kazandıran adımdır: 40 kare alıp 6'sını kullanmak yerine
6 kareyi doğru planlamak.

`examples/project.example.json` şablonundan yola çıkarak proje tanımı yazılır:

```bash
python -m archviz_kit shotlist proje.json --out shotlist.json --markdown cekim-listesi.md
```

Çıktı, her görünüm için şunları verir: ön ayar, çözünürlük, örneklem sayısı,
kamera değerleri ve dosya adı. Uyarı listesi boş olmalıdır.

## Aşama 2 — Taslak (draft)

Tüm kareler en düşük kalitede alınır. Amaç kadraj ve kompozisyonu görmek,
ışık yönünü doğrulamaktır. Süre: final render'ın yaklaşık **%2-5'i**.

```bash
blender -b sahne.blend --python blender/batch_render.py -- \
    --shotlist shotlist.json --outdir renders/taslak
```

Bu aşamada bakılacaklar:

- Kadraj doğru mu, özne sığıyor mu?
- Dikeyler düzgün mü?
- Gölge yönü vaziyet planıyla tutarlı mı?
- Kompozisyonda boş/dengesiz kalan bir kare var mı?

**Taslak aşaması geçilmeden final render alınmaz.** Kadraj hatasını final
kalitede fark etmek, saatlerce render'ı çöpe atar.

## Aşama 3 — Önizleme (preview)

Onay için müşteriye gösterilecek kareler bu profilde alınır. Malzeme ve ışık
okunur, süre final'in yaklaşık **%25'i**.

## Aşama 4 — Final

Teslim kalitesi. Tam örneklem, tam çözünürlük, denoise açık.

```bash
blender -b sahne.blend --python blender/batch_render.py -- \
    --shotlist shotlist.json --outdir renders/final --skip-existing
```

`--skip-existing` bayrağı, uzun render'lar bölünürse kaldığı yerden devam
etmeyi sağlar.

## Aşama 5 — Teslim kontrolü

| Kontrol | Kabul ölçütü |
|---------|--------------|
| Dosya adları | Şablona uygun (`proje_gorunum_tur_kalite_v01.png`) |
| Dikey düzeltme | Duvar/kapı kenarları eğik değil |
| Ölçek tutarlılığı | Vaziyet ile cephe gölgeleri aynı kuzey kabulünde |
| Pencere/cam | Patlamış veya delik görünmüyor |
| Bitki ölçeği | Yetişkin boyutlar gerçekçi |
| Mevsim tutarlılığı | Aynı karede karışık mevsim yok |

## Aşama 6 — Arşiv

Teslim edilen kareler, kullanılan proje tanımı ve çekim listesi birlikte
saklanır. Böylece altı ay sonra "bu görsel hangi ayarlarla alındı" sorusu
cevaplanabilir. Proje tanımı (`proje.json`) sürüm kontrolüne girer; render
çıktıları girmez.

## Zaman bütçesi

Bir görünüm için kaba oran (6 çekirdek CPU, Cycles):

| Profil | İç mekan | Dış cephe | Vaziyet | Peyzaj |
|--------|----------|-----------|---------|--------|
| Taslak | ~1 dk | ~2 dk | ~1 dk | ~2 dk |
| Önizleme | ~5 dk | ~10 dk | ~4 dk | ~8 dk |
| Final | ~25 dk | ~45 dk | ~15 dk | ~40 dk |

Değerler başlangıç tahminidir; sahne karmaşıklığına göre ölçüp güncelleyin.