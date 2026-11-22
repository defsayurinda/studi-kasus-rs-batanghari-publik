# Aturan Gambar CADCraft

Pegangan wajib untuk **setiap gambar ber-kop** di studi kasus ini: gambar geoteknik (GT), gambar konsep (GK), dan DED.
Dokumen ini merangkum arahan Defsa (18-20 Nov 2026) dan pelajaran dari GT-01..GT-15 serta GK-01..GK-12.
Aturan Excel/Word tetap mengikuti `FORMAT LAPORAN DAN EXCEL.md`.

## 1. Prinsip (arahan Defsa)

| No | Arahan | Sejak |
|---|---|---|
| 1 | Semua gambar **digambar asli di CADCraft**: perintah CAD di model space berkoordinat nyata. Bukan matplotlib yang disalin, bukan gambar tempelan | 19 Nov 2026 |
| 2 | Hasil harus **setara DED konsultan profesional**, tidak tampak seperti hasil AI | 19 Nov 2026 |
| 3 | **DWG dapat diedit manual** seperti buatan drafter: ukuran asosiatif, simbol berupa block, arsir asosiatif, teks asli (bukan garis) | 19 Nov 2026 |
| 4 | **Rapi, tidak ada yang tumpang tindih**: teks dengan teks, teks dengan garis, legenda dengan kurva | 19 Nov 2026 |
| 5 | Gaya mengikuti contoh Defsa: kop **KETERANGAN** di kanan, huruf **Times New Roman**, cetak **hitam-putih** | 19 Nov 2026 |
| 6 | **Satu kop** untuk semua gambar: block `KOP_A3`. Jangan membuat kop sendiri per gambar | 19 Nov 2026 |
| 7 | Penggambar tertulis **D. YURINDA** (DIGAMBAR, DIPERIKSA; DISETUJUI setelah Defsa setuju) | 19 Nov 2026 |
| 8 | **Aplikasi benar-benar dibuka**: hasil ditampilkan di jendela CADCraft supaya Defsa bisa melihat dan melanjutkan | 19 Nov 2026 |
| 9 | Denah dan potongan bangunan berasal dari **model BIMCraft**; anotasinya ditulis di CADCraft | 19-20 Nov 2026 |
| 10 | **Besi dimodelkan di BIMCraft** (`reinforce`, `rebar`) dan penampang/potongan besi diambil dari model; potongan **tidak hitam pejal** (poché beton dibuang, beton garis tepi). Contoh: `tahap4_besi.py`, `tahap4_gambar_ded.bersihkan_dxf` | 20 Nov 2026 |

## 2. Alat dan cara kerja

| Hal | Isi |
|---|---|
| Aplikasi | `C:\Program Files\ArtCraft\CADCraft\cadcraft.exe` (jendela), `cadcraft-cli.exe mcp` (skrip) |
| Klien skrip | `skrip/cadcraft.py` (`Sesi`), pustaka lembar `skrip/cad_lembar.py` (`Gambar`), kop `skrip/cad_kop.py`, grafik data `skrip/cad_grafik.py` (`LembarCAD`), pemeriksa `skrip/cad_cek.py` |
| Kop | `templat/KOP A3.dwg`, disisipkan sebagai block `KOP_A3` beratribut |
| Pola arsir tanah | `templat/geoteknik.pat` (pola `GT-...`) |
| Jendela | `cadcraft.exe --control 7979`. Skrip dengan env `CADCRAFT_JENDELA=1` membuka hasil di jendela itu; MCP `cadcraft-jendela` menyambung ke port 7979 |
| Urutan | (1) bangun DWG tanpa jendela (headless, stabil), (2) simpan DWG + plot PDF + PNG pratinjau, (3) buka DWG di jendela untuk Defsa |
| Satu skrip per kelompok gambar | contoh: `tahap3_tapak.gambar_cad()`, `la_utilitas.gambar_cad()`. Gambar harus bisa dibangun ulang dari skrip |

## 3. Satuan, koordinat, kertas, skala

- **Model space: 1 unit = 1 mm** pada koordinat proyek nyata. Di skrip, koordinat ditulis dalam **meter** grid lokal
  (x ke timur, y ke utara, nol di sudut barat daya persil); `Gambar.mm()` mengubahnya ke mm.
- Elevasi memakai datum lokal BM-1 = +10,000. Desimal pakai **koma** di teks gambar (`+12,85`), titik di kode.
- **Kertas A3 lanskap** (`ISO A3 (297.00 x 420.00 MM)`), plot `monochrome.ctb`, skala plot 1:1, ketebalan garis aktif.
- Area gambar di kertas: `cad_lembar.AREA`. Kolom KETERANGAN (kop) di kanan, lebar 75 mm.
- **Viewport terkunci** pada skala gambar: 1:200, 1:250, 1:300, 1:500, atau 1:750. Penampang tanah boleh berskala vertikal
  dilebihkan (tulis `H 1:500 V 1:250`). Grafik tanpa skala ditulis `TANPA SKALA`.
- Pilih skala supaya isi memenuhi viewport **tanpa terpotong**. Hitung lebar dan tinggi isi (m) × 1000 / skala ≤ ukuran
  viewport (mm). Kalau tidak muat, perbesar viewport atau ganti skala; jangan biarkan label terpotong tepi.

## 4. Lembar (layout)

`Gambar.lembar(nomor, judul, teks_skala, pusat, subjudul, status, catatan, vp, judul_kop, ...)` membuat satu layout per
lembar. Isi wajib setiap lembar:

1. **Kop KOP_A3** dengan atribut STATUS, JUDUL, NO_GAMBAR, SKALA, REV, LEMBAR, TANGGAL, DIGAMBAR, DIPERIKSA, DISETUJUI.
   - Judul di kop maksimal ±30 huruf. Kalau lebih, isi `judul_kop` dengan versi pendek; judul panjang tetap di judul gambar.
   - STATUS: `STATUS_DRAF` sampai Defsa setuju, lalu `STATUS_SETUJU` dengan **tanggal persetujuan sebenarnya**. Setelah
     label berubah, gambar **wajib dibangun ulang** (pelajaran 3.6: Excel dan GK-06 sempat tertinggal berlabel draf).
   - Baris DATA SIMULASI - TIDAK UNTUK KONSTRUKSI sudah ada di kop; jangan ditulis lagi di gambar.
2. **Viewport utama** (dan `viewport_tambahan` bila perlu, misalnya potongan) dengan judul kecil bergaris bawah dan
   teks skalanya.
3. **Judul gambar** di kiri bawah: lingkaran bernomor, JUDUL bergaris bawah, `SKALA 1:...`, subjudul (sumber dan langkah).
4. **LEGENDA** di kotak KETERANGAN (`legenda_tambah`): contoh arsir/garis untuk setiap layer yang tampil.
5. **CATATAN** bernomor di kotak KETERANGAN: dasar angka (SNI dan pasal, langkah), asumsi `[Asumsi]`, hal yang belum
   final. Kalau tidak muat, huruf mengecil otomatis sampai 5 pt; lebih dari itu, persingkat catatannya.
6. **Skala grafis** (`skala_grafis`) dan **panah utara** (`panah_utara`) pada denah dan peta.
7. **Penomoran**: `GT-xx` geoteknik (Tahap 2), `GK-xx` konsep (Tahap 3 dan laporan antara), DED mengikuti kode disiplin
   di BEP 3.1 (mis. `S-` struktur, `A-` arsitektur). Satu nomor, satu layout, satu DWG.

## 5. Unsur gambar seperti buatan drafter

| Unsur | Aturan | Fungsi `Gambar` |
|---|---|---|
| Layer | Satu layer per jenis unsur; awalan disiplin: `A-` arsitektur, `S-` struktur, `C-` sipil/tapak, `G-` geoteknik, `M-` MEP, `D-` diagram. Contoh `A-MASSA`, `S-GRID`, `C-SEMPADAN`, `G-U4` | `layer(nama, warna, tebal, garis)` |
| Tebal garis | Garis potong/massa 0,5-0,7; garis biasa 0,25-0,35; garis bantu, grid, lapisan 0,13-0,18 | parameter `tebal` |
| Jenis garis | Grid/as: CENTER; tersembunyi/rencana tahap 2: DASHED/HIDDEN; batas persil: PHANTOM; `ltscale 0,3`, `PSLTSCALE 1` | parameter `garis` |
| Teks | Gaya `TNR` dan `TNR_TEBAL` (Times). Tinggi dalam **mm kertas** (`TINGGI`): judul 4,0; sub 2,2; label 2,0; kecil 1,6; catatan 1,9. Pada viewport skala lain, tinggi model disesuaikan rasio skalanya | `teks`, `mteks` |
| Ukuran | **Garis ukur asosiatif** gaya `PROYEK` (DIMLFAC 0,001 → meter, koma desimal, tick miring, latar teks diisi). Angka berasal dari geometri, bukan teks tetap. Titik `at` di tengah ruas supaya arah ukur benar | `ukur(p1, p2, at)` |
| Arsir | Asosiatif terhadap batasnya. Di bawah teks, buat **lubang** supaya teks tidak tertimpa pola | `arsir`, `arsir_lubang` |
| Simbol | **Block**: titik tinggi `TITIK_TINGGI`, silang grid `GRID_SILANG`, panah utara `PANAH_UTARA` | `titik_tinggi`, `grid_koordinat`, `panah_utara` |
| As grid | Garis CENTER dengan gelembung bernama (1, 2, ... dan A, B, ...) | `as_grid` |
| Penunjuk | Multileader, teks di ujung bebas | `tunjuk(panah, letak, teks)` |
| Warna | Warna layer boleh berbeda di layar, tetapi plot selalu hitam-putih: bedakan unsur dengan jenis garis, tebal, arsir, dan simbol, **bukan warna** | - |

## 6. Kerapian: tidak boleh ada yang bertumpuk

1. **`skrip/cad_cek.py <dwg>` wajib 0 pasangan.** Alat ini membandingkan kotak teks dengan kotak teks (model, ukuran,
   paper space).
2. **Periksa juga render PNG/PDF dengan mata.** `cad_cek` tidak menangkap teks yang tertimpa garis, legenda yang menutup
   kurva, atau isi yang terpotong viewport. Kasus nyata yang pernah lolos `cad_cek` tetapi salah:
   - garis grid menembus label zona → **as grid dibuat potongan pendek di luar bangunan** (gelembung di luar, garis
     berhenti di tepi massa);
   - garis level dan lapisan tanah mencoret teks → teks diletakkan di sela garis (di atas atau di bawah garis, bukan
     menempel);
   - kontur menembus label → kontur **diputus** di sekitar teks;
   - arsir menimpa teks → `arsir_lubang`;
   - legenda grafik menutup kurva atau keluar bingkai (GT-06, GT-15) → legenda di ruang kosong di dalam bingkai;
   - label menyentuh kurva (GT-12) → geser label;
   - viewport kedua memotong isi (GK-12 versi awal) → isi dipindah ke viewport utama atau skala diganti;
   - judul kop terpotong → `judul_kop`;
   - kolom tabel terlalu sempit (judul "Pake t").
3. Label zona memakai penempatan otomatis yang menghindari inti tangga/lif (`tahap3_zonasi.tempat_label`); teks yang
   tidak muat dipecah per baris, bukan diperkecil di bawah 1,4 mm.
4. Penunjuk (leader) tidak menyilang teks lain; arah leader ke ruang kosong.

## 7. Denah dan potongan dari model BIMCraft

Model gedung dibangun di BIMCraft (CLI 0.12.0; jendela memakai 0.11.0 karena jendela 0.12.0 berhenti sendiri di laptop
ini). Denah dan potongan untuk lembar CAD dibuat dengan alur berikut (`skrip/tahap3_gambar_konsep.py`):

1. Buat view di model (`section` untuk potongan, `depth` sesuai kebutuhan) dan simpan ke model supaya bisa dibuka lagi.
2. Ekspor view ke **DXF** (`export format dxf`) ke `03 Desain Konsep/Gambar/BIM/`.
3. Impor DXF ke model space CADCraft (`import`, titik 0,0; koordinat proyek sama).
4. **Hapus layer teks BIMCraft** (`laydel`: `room`, `tag`, `grid`, `level`, `section`), karena teks BIMCraft keluar
   sebagai garis dan tidak bisa diedit.
5. Tulis ulang anotasi asli CADCraft: nama ruang dan luas, as grid, ukuran, titik tinggi, catatan.
6. Batasan yang diketahui: ekspor DXF potongan hanya memuat unsur yang **terpotong**. Pilih garis potong yang memotong
   kolom (mis. pada as), dan jelaskan unsur di belakang bidang potong di catatan.

## 8. Grafik data (hidrograf, profil, kurva)

- Pakai `cad_grafik.LembarCAD`: susun data dengan matplotlib, lalu `simpan()` menggambar **ulang** setiap unsur sebagai
  entitas CAD (bingkai, tick, grid titik, pline per seri, legenda berbingkai). Tidak menyalin gambar matplotlib.
- Unit tanah memakai pola `GT-...` dari `templat/geoteknik.pat`; air `GT-AIR`.
- Seri yang di layar hanya dibedakan warna **wajib** diberi simbol penanda atau jenis garis berbeda (cetak hitam-putih).
- Sumbu bersatuan, angka berkoma desimal, sumber data di catatan.

## 9. Isi teknis minimum per jenis gambar

| Jenis | Wajib ada |
|---|---|
| Tapak/situasi | batas persil, sempadan, GSB, rumija, kontur/titik tinggi, massa, akses, panah utara, skala grafis |
| Denah | as grid bernama, ukuran antar-as dan total, nama ruang + luas, titik tinggi lantai, bukaan/ramp, garis potong |
| Potongan | level dan elevasi, muka tanah asli dan rencana, muka air/banjir rencana, lapisan tanah (geoteknik), tiang, as grid |
| Struktur (DED) | as grid, kode unsur (K1, B1, P1) dengan tabel ukuran/tulangan, mutu beton dan baja, selimut, catatan umum SNI 2847 |
| Detail (DED) | skala 1:10-1:50, penulangan (jumlah-diameter-jarak, panjang penyaluran, kait), tebal selimut, ukuran lengkap |
| Geoteknik | titik penyelidikan, unit tanah berpola standar, parameter desain, muka air, sumber data |

## 10. Angka dan sumber

- Tidak ada angka tanpa sumber. Catatan lembar menyebut SNI dan pasal/halaman atau langkah perhitungan
  (mis. `SNI 8460:2017 Pasal 9.8`, `langkah 3.3`).
- Angka yang belum berdasar dokumen di `acuan/` diberi `[Asumsi]`.
- Angka di gambar **diambil dari skrip perhitungan** (bukan diketik ulang), supaya gambar ikut berubah bila hitungan
  berubah.

## 11. Keluaran dan penyimpanan

| Berkas | Tempat |
|---|---|
| DWG (sumber yang bisa diedit) | `<folder tahap>/Gambar/DWG/<NOMOR> <Judul>.dwg` |
| PDF hasil plot layout | `<folder tahap>/<langkah> Gambar <Judul>.pdf` |
| PNG pratinjau | `<folder tahap>/Gambar/<NOMOR> <Judul>.png` |
| DXF dari BIMCraft | `<folder tahap>/Gambar/BIM/` (`*.dxf -text` di `.gitattributes`) |

## 12. Daftar periksa sebelum diserahkan

- [ ] Digambar asli di CADCraft melalui skrip; DWG terbuka dan dapat diedit di jendela CADCraft.
- [ ] Kop `KOP_A3` lengkap; judul kop tidak terpotong; nomor, skala, lembar, tanggal, revisi benar.
- [ ] STATUS sesuai: draf, atau disetujui dengan tanggal; gambar dibangun ulang setelah status berubah.
- [ ] Legenda memuat setiap jenis unsur; catatan memuat sumber dan asumsi.
- [ ] Skala grafis dan panah utara (denah/peta); skala viewport sesuai teks skala.
- [ ] Ukuran asosiatif, arsir asosiatif, simbol block, teks asli (bukan garis).
- [ ] `cad_cek.py` = 0 pasangan.
- [ ] Render PNG/PDF diperiksa dengan mata: tidak ada teks tercoret garis, legenda menutup kurva, isi terpotong.
- [ ] Hitam-putih tetap terbaca (jenis garis, arsir, simbol).
- [ ] Angka cocok dengan skrip/Excel; skrip gambar ter-commit bersama DWG, PDF, PNG.

## 13. Yang tidak boleh

- Menggambar dengan matplotlib lalu menempel gambarnya, atau memakai `gambar_teknik.Kertas` / `cad_render.py` untuk
  gambar baru.
- Membuat kop sendiri per gambar, atau menulis label status/simulasi di luar kop.
- Teks ukuran yang diketik manual (angka tidak mengikuti geometri).
- Meledakkan (explode) block, ukuran, atau arsir sehingga tidak bisa diedit.
- Menyerahkan gambar hanya karena `cad_cek` = 0 tanpa melihat render.
- Memakai warna sebagai satu-satunya pembeda unsur.

## 14. Contoh minimal

```python
from cad_lembar import STATUS_DRAF, Gambar

with Gambar(500) as g:                                  # skala viewport 1:500
    g.layer("A-MASSA", 7, 0.7)
    g.pline([(12, 27), (84, 27), (84, 75), (12, 75)], "A-MASSA", tutup=True)
    g.legenda_tambah("garis", "Massa bangunan", tebal=0.7)
    g.as_grid("1", (12, 75), (12, 82), r_kertas=3.0, dua_ujung=False)   # as grid di luar bangunan
    g.ukur((12, 89), (84, 89), (48, 92))                # ukuran asosiatif, titik at di tengah ruas
    g.titik_tinggi((14, 72), "+12,85 LANTAI", "A-ELEVASI")
    g.teks((48, 51), "PODIUM", "A-TEKS", 2.0, j="MC", tebal=True)
    g.lembar("GK-xx", "Judul gambar", "1:500", pusat=(70, 52), status=STATUS_DRAF,
             subjudul="Langkah x.y: sumber dan maksud gambar",
             catatan=["Dasar angka: SNI ... Pasal ...; langkah ...", "Ukuran ... [Asumsi]."])
    g.skala_grafis(205, 22, 50)
    g.panah_utara(318, 262, 10)
    g.simpan(dwg, pdf, png)                             # lalu: cad_cek.py dwg, lihat png
```
