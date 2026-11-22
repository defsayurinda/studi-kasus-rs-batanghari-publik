# Rencana Tahap 6: Pondasi (disetujui Defsa 21 Nov 2026)

## Konteks

Tahap 5 struktur tengah selesai dan di-merge (PR #42, `05 Struktur Tengah/Ringkasan Tahap 5.md`). Lingkup Tahap 6
menurut `00 RANCANGAN.md`: tiang, pile cap, gesekan negatif akibat urugan, dinding penahan galian, dewatering, uplift,
penurunan, stabilitas tebing sungai. Karena opsi C (3.5) tanpa basement, dinding penahan galian dan dewatering
menyusut menjadi **galian pile cap dan pit lift** (dangkal, tetapi dekat gudang timur bercerucuk gelam).

Konsep Tahap 3 (3.7, GK-07): tiang bor Ø800 ke U7 ±38 m, 373 tiang, izin 911 kN per tiang [FHWA NHI-06-089,
SNI 8460:2017]. Tahap 3 juga menitipkan ke Tahap 6: uji tiang, gesekan negatif, penyebaran lateral, stabilitas tebing.

Bawaan Tahap 5 (bagian 4 ringkasan) yang wajib masuk:

| No | Butir | Langkah |
|---|---|---|
| B-1 | 30 pasang tiang LOD 200 Tahap 3 berjarak pusat < 2,0 m (terdekat 0,83 m) di sekitar inti: cap inti dan cap kolom sekitarnya digabung, jarak minimum dicek ulang | 6.0, 6.3 |
| B-2 | Reaksi 77 titik (layan dan ultimit, K1 ∪ K2, kasus E, dengan ΔP sloof) dari `05 Struktur Tengah/5.6 Reaksi ke Pondasi.xlsx` lembar "Ringkasan Tahap 6"; Σ D inti tumpang 6,3 % dibiarkan (konservatif) | 6.0, 6.3 |
| B-3 | Pile cap inti 1.200 mm; kolom (52,35) dan (52,43) masuk cap inti | 6.3, 6.7 |
| B-4 | Kepala tiang sendi di Tahap 5; bila Tahap 6 memilih jepit, sloof 5.4 dicek ulang | 6.5 |
| B-5 | Penurunan beda δ 16 mm [Asumsi: SNI 1726 Tabel 22] dibandingkan dengan penurunan hasil Tahap 6 | 6.6 |
| B-6 | Angkur sloof di inti: kait 90° turun ke cap, ldh 381 mm, tebal cap minimum 488 mm | 6.7 |
| B-7 | Pit L-1..4 diangkurkan berat sendiri (FK 1,11); pengangkuran izin SNI 8460 pasal 10 belum ada di acuan | 6.7 |
| B-8 | Serakan lateral dan penurunan pile cap belum ada datanya | 6.4, 6.6 |

## Cara kerja

- **Defsa menghitung inti dulu, AI memeriksa.** Untuk 6.1 (satu tiang tunggal Ø800 di satu titik bor) dan 6.3
  (pile cap inti lift: jumlah dan susunan tiang, beban tiang maksimum), Defsa menghitung lebih dulu; AI baru menyusun
  versi skripnya dan membandingkan. Unsur lain disusun AI lalu diperiksa Defsa.
- Setiap langkah berhenti dengan label **"draf, menunggu persetujuan Defsa"**.
- Pasal SNI dicocokkan ke PDF di `acuan/privat/` (SNI 8460:2017, 2847:2019, 1726:2019). Metode tiang dari
  `acuan/pustaka/` (FHWA GEC10 drilled shafts, GEC9 lateral, NHI-06-089). Pasal atau halaman yang tidak ditemukan
  ditulis "belum ada di acuan", bukan ditebak (contoh: pengangkuran SNI 8460 pasal 10).
- Parameter tanah dari Tahap 2 (U1-U8, likuifaksi U5, penurunan urugan 2.8); data uji tiang diminta ke sesi skenario.
- Excel dan Word mengikuti `FORMAT LAPORAN DAN EXCEL.md`; Excel dihitung ulang di Excel lalu dicocokkan dengan Python.
- Gambar dari model BIM, anotasi di CADCraft dengan `KOP_A3`, `cad_cek` 0 pasangan, potongan tanpa poché pejal.
- Kunci di `../02 Siap Terbit/privat/studi-kasus-kunci/` tidak dibuka.
- Model/effort: Opus medium untuk sesi langkah, high untuk metode baru (6.2, 6.4) dan review akhir; pelaksanaan
  (skrip, Excel, CADCraft, BIMCraft) oleh subagen Sonnet. Skill defsa-yurinda-skill, scientific-critical-thinking.
  Modul openpile, groundhog, pyslope, openseespy; alat GeoFEM3D, PLAXIS 3D (cek silang saja), BIMCraft.
- Uji hanya berkas yang disentuh; seluruh uji sekali di akhir tahap.
- Git: cabang `fitur/tahap-6-<langkah>`, pesan Indonesia, PR selesai langsung merge (arahan Defsa), lalu pull `main`.
- Cek silang mulai **T-98**; gambar struktur mulai **GS-27**; potongan geoteknik melanjutkan seri **GT-16**.

## Langkah

| Langkah | Isi | Keluaran (`06 Struktur Bawah dan Basement/`) |
|---|---|---|
| 6.0 | Persiapan: plot tiang LOD 200 dan 77 reaksi di atas grid, pasangan tiang dekat, parameter tanah desain, permintaan data uji tiang | `6.0 Telaah Data Tahap 6.xlsx`, GS-27 |
| 6.1 | Daya dukung tiang tunggal Ø800 (tekan, tarik), panjang tiang per zona | `6.1 Daya Dukung Tiang.xlsx` |
| 6.2 | Gesekan negatif akibat urugan + PVD dan akibat likuifaksi U5 | `6.2 Gesekan Negatif.xlsx` |
| 6.3 | Jumlah dan tata letak tiang, gabung cap inti, jarak minimum, efisiensi kelompok | `6.3 Tata Letak Tiang.xlsx` |
| 6.4 | Stabilitas tebing sungai dan serakan lateral (profil perpindahan tanah) | `6.4 Tebing dan Serakan Lateral.xlsx`, GT-16 |
| 6.5 | Tiang lateral (inersia + kinematik), kepala sendi atau jepit | `6.5 Tiang Lateral.xlsx` |
| 6.6 | Penurunan tiang kelompok dan penurunan beda vs δ 16 mm | `6.6 Penurunan Pondasi.xlsx` |
| 6.7 | Desain struktur tiang dan pile cap, angkur sloof, stek, pengangkuran pit | `6.7 Desain Tiang dan Pile Cap.xlsx` |
| 6.8 | Uji tiang dan metode pelaksanaan (galian cap, dewatering dekat gudang) | `6.8 Uji Tiang dan Pelaksanaan.xlsx` |
| 6.9 | Model BIMCraft LOD 300 pondasi | `model/RSTB-STR-T6-LOD300.bimc/.ifc` |
| 6.10 | Gambar pondasi setara DED | `Gambar/DWG/`, PDF A3 |
| 6.11 | Ringkasan Tahap 6, PROGRES, PR | `Ringkasan Tahap 6.md` |

### 6.0 Persiapan dan telaah data

1. **Plot dulu, baru baca angka.** Di atas grid (as 1-10, A-G, modul 8 m) dan rencana tapak: 373 tiang LOD 200 (model
   Tahap 3), 77 titik reaksi B-2, cap inti 1.200, pit L-1..L-7, titik bor/sondir Tahap 1, garis tebing P-2 dan
   sempadan sungai, gudang timur bercerucuk.
2. **Daftar pasangan tiang < 3D (2,4 m)** dengan jarak terdekat (B-1: 30 pasang < 2,0 m) dan cap mana yang harus
   digabung. Keluarannya lembar GS-27 (CADCraft) dan tabel di Excel.
3. **Cek murah:** jumlah titik reaksi = jumlah kolom LT1 + 7 inti; Σ reaksi layan = Σ 5.6 (T-95); satuan; elevasi
   kepala tiang (muka cap +12,05 dikurangi tebal cap); muka air desain +11,20 dan Q50 +11,85.
4. **Parameter tanah desain per unit** (U1-U8) dari Tahap 2: su, φ', γ, Cc/Cv, qc; zona utara (gambut 3,3-3,7 m) vs
   selatan; penurunan urugan 0,15-1,18 m dan sisa setelah PVD.
5. **Permintaan data ke sesi skenario** (isi disetujui Defsa dulu): rincian uji tiang awal (Tahap 3 "sebelum 30 April
   2027"), data PDA/beban statik bila ada, dan data pemantauan urugan + PVD.
6. Daftar acuan yang dibutuhkan dan yang belum ada (SNI 8460 pasal 10, pedoman serakan lateral, Fellenius untuk
   bidang netral bila tidak ada di GEC10).

**Berhenti: Defsa menyetujui telaah data dan permintaan data.**

### 6.1 Daya dukung tiang tunggal Ø800 (Defsa menghitung dulu)

- Tahanan selimut dan ujung tiang bor menurut FHWA GEC10 (metode α untuk lempung, β untuk pasir; halaman dicek),
  dibandingkan dengan cara SNI 8460:2017 (pasal tiang bor dicek ke PDF) dan korelasi sondir/SPT Tahap 1.
- Lapisan yang tidak dihitung: urugan, gambut, dan U5 saat gempa (likuifaksi, FS 0,22-0,75).
- FK atau faktor tahanan dari SNI 8460 (nilai dan pasal dicek); izin 911 kN Tahap 3 dibandingkan.
- Tahanan tarik (untuk kasus gempa, walaupun Pu min 599 kN tekan).
- Panjang tiang per zona (utara/selatan) bila ujung U7 berbeda elevasinya.

**Berhenti: Defsa menyetujui daya dukung tiang tunggal.**

### 6.2 Gesekan negatif

- **Akibat urugan + PVD:** bidang netral dan gaya seret (FHWA GEC10 atau Fellenius; acuan dicek), penurunan sisa
  urugan setelah PVD dari 2.8 dan 3.3 di zona utara dan selatan.
- **Akibat likuifaksi U5:** gaya seret dari lapisan di atas U5 setelah gempa (pasca-likuifaksi), tidak dijumlah dengan
  beban hidup sementara (kombinasi dicek).
- Hasilnya beban struktur tiang maksimum (di bidang netral) dan pengurangan daya dukung izin per zona.

**Berhenti: Defsa menyetujui gesekan negatif dan daya dukung akhir per tiang.**

### 6.3 Jumlah dan tata letak tiang (Defsa menghitung cap inti dulu)

- Jumlah tiang per titik dari reaksi layan (daya dukung izin 6.1-6.2) dan dicek terhadap ultimit (beban tiang dengan
  momen, rumus cap kaku P/n ± M·x/Σx²).
- **Jarak minimum** dari SNI 8460 (pasal dicek; umumnya 2,5-3D) untuk semua cap; pasangan < 2,0 m dari B-1 dihapus
  dengan menggabung cap inti dan cap kolom di sekitarnya (termasuk kolom (52,35) dan (52,43), B-3).
- Efisiensi kelompok (Converse-Labarre atau blok; acuan dicek) dan kegagalan blok untuk cap inti.
- Jumlah tiang total dibandingkan 373 Tahap 3; perubahan biaya dicatat untuk Tahap 8.

**Berhenti: Defsa menyetujui tata letak tiang.**

### 6.4 Stabilitas tebing sungai dan serakan lateral

- Potongan tebing P-2 (longsoran lama, puncak 6,5 m dari batas lahan) dengan urugan, muka air rendah dan surut cepat,
  dan gempa (pyslope Bishop dan Spencer; GeoFEM3D sebagai cek silang). FK dari SNI 8460 (pasal dicek).
- **Serakan lateral** akibat likuifaksi U5 yang terpotong sungai: perpindahan tanah per kedalaman di garis tiang
  terdekat tebing (metode empiris; acuan dicari, bila tidak ada ditulis "belum ada di acuan").
- Bila FK kurang: perkuatan tebing (bronjong, cerucuk, geser garis tiang) dibandingkan.

**Berhenti: Defsa menyetujui FK tebing dan profil perpindahan tanah.**

### 6.5 Tiang lateral dan kepala tiang

- Beban inersia gempa (geser dasar 4.2 dibagi per tiang) dan beban kinematik dari 6.4, dengan p-y (openpile; GEC9),
  pengali p untuk U5 terlikuifaksi.
- **Kepala tiang sendi vs jepit:** momen tiang dan defleksi kepala. Bila jepit dipilih, sloof 5.4 dicek ulang
  dengan momen jepit (B-4).
- Hasilnya momen dan geser tiang sepanjang kedalaman untuk desain 6.7.

**Berhenti: Defsa memilih kondisi kepala tiang.**

### 6.6 Penurunan

- Penurunan kelompok (rakit ekuivalen di 2/3 panjang tiang atau bidang netral; acuan dicek) per cap, ditambah
  pemendekan elastis tiang.
- GeoFEM3D untuk cap inti dan satu cap tipikal; PLAXIS 3D hanya cek silang.
- **Penurunan beda** antar cap bertetangga dibandingkan dengan δ 16 mm (B-5). Bila lebih besar, momen sloof 5.4
  dihitung ulang dengan δ hasil.

**Berhenti: Defsa menyetujui penurunan.**

### 6.7 Desain struktur tiang dan pile cap

- **Tiang:** tulangan memanjang dan spiral Ø800 dari gaya 6.2 dan 6.5 (SNI 2847:2019 Pasal 13 dan 18.13; pasal dicek),
  panjang tulangan penuh sampai di bawah U5 dan bidang netral, selimut paparan S2 + asam (keputusan 2.7).
- **Pile cap:** geser satu arah, pons kolom dan tiang, lentur; cap inti 1.200 mm dengan strut-and-tie (SNI 2847 Pasal 23).
  Tebal ≥ 488 mm untuk angkur sloof (B-6) dan cukup untuk ldh/ld stek kolom (5.6a: ldh 375, ld 919).
- **Pengangkuran pit** L-1..4 (B-7): FK 1,11 dari 5.5 dicek ulang dengan pasal SNI 8460 bila ditemukan; bila tidak,
  ikat pit ke cap inti/tiang tarik sebagai opsi.

**Berhenti: Defsa menyetujui desain tiang dan pile cap.**

### 6.8 Uji tiang dan metode pelaksanaan

- Program uji: uji beban statik tiang awal, PDA, PIT/CSL (jumlah dari SNI 8460; pasal dicek), letak tiang uji di zona
  utara dan selatan.
- Galian cap dan pit: lereng galian, dewatering terkendali dekat gudang timur (cerucuk gelam lapuk, klaim retak),
  urutan dengan urugan + PVD.

**Berhenti: Defsa menyetujui program uji dan metode.**

### 6.9 Model BIMCraft LOD 300

- Tiang, pile cap, dan tulangan cap inti ditambahkan ke model 5.7 (`skrip/bimcraft.py`), dengan Pset_RSTB_Umum.
- Clash: tiang vs tiang (jarak), cap vs sloof dan pit, stek vs tulangan cap. Volume IFC vs desain.

### 6.10 Gambar

- Dari model BIM: GS-27 telaah (6.0), GS-28 denah tiang dan pile cap, GS-29 pile cap inti, GS-30 pile cap tipikal,
  GS-31 detail tiang bor dan penulangan, GS-32 tabel tiang dan cap. GT-16 potongan tebing. CADCraft `KOP_A3`.

### 6.11 Ringkasan dan PR

- `Ringkasan Tahap 6.md`, PROGRES, seluruh uji sekali di latar, pindai privasi, PR, merge, pull `main`.

## Cek silang yang direncanakan

Toleransi ditetapkan sebelum hitung dan dicatat di `VERIFIKASI.md`:

| No | Cek | Cara 1 | Cara 2 |
|---|---|---|---|
| T-98 | Jarak dan jumlah tiang | koordinat skrip | ukur di DWG / IFC |
| T-99 | Daya dukung tiang tunggal | hitungan Defsa / GEC10 | skrip / korelasi sondir |
| T-100 | Gaya seret dan bidang netral | hitung tangan | skrip |
| T-101 | Beban tiang maksimum di cap inti | rumus cap kaku | model pegas (PyNite/openseespy) |
| T-102 | FK tebing | pyslope Bishop | Spencer / GeoFEM3D |
| T-103 | Momen dan defleksi tiang lateral | openpile | GeoFEM3D (PLAXIS 3D cek silang) |
| T-104 | Penurunan cap inti | rakit ekuivalen | GeoFEM3D |
| T-105 | Kapasitas pile cap (geser, pons, STM) | hitung tangan | skrip |
| T-106 | Uji tiang dan dewatering (6.8) | hitung tangan / uji beban | skrip / aliran 1-D |
| T-107 | Volume IFC vs rencana | skrip | model IFC |
| T-108 | Excel = Python | Excel dihitung ulang | Python |

## Keputusan yang dibutuhkan dari Defsa

1. **(6.0)** Isi permintaan data uji tiang dan pemantauan urugan ke sesi skenario.
2. **(6.0)** Lingkup gedung utilitas + parkir 4 lantai (opsi C): ikut Tahap 6 atau ditunda; reaksi 77 titik hanya
   gedung utama.
3. **(6.1-6.2)** Faktor keamanan / faktor tahanan dan cara gesekan negatif yang dipakai.
4. **(6.3)** Susunan gabungan cap inti (satu rakit tiang inti vs beberapa cap terikat).
5. **(6.4)** Perkuatan tebing bila FK kurang.
6. **(6.5)** Kepala tiang sendi atau jepit (menentukan cek ulang sloof).
7. **(6.7)** Pit L-1..4: tetap berat sendiri atau diikat ke cap/tiang.
8. **(Tiap langkah)** Persetujuan hasil sebelum lanjut.

Lingkup yang lebih kecil bila Defsa ingin cepat: gabungkan 6.9-6.10 ke Tahap 7 (DED) dan tutup Tahap 6 di 6.8, atau
pindahkan 6.8 ke RKS Tahap 7.
