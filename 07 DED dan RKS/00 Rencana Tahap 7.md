# Rencana Tahap 7: DED dan RKS (disetujui atas delegasi Defsa 22 Nov 2026)

## Konteks

Tahap 4 (struktur atas), Tahap 5 (struktur tengah), dan Tahap 6 sampai 6.8 (pondasi tiang bor Ø800) sudah selesai dan
di-merge (PR #54-#56). Langkah 6.9 (model BIM pondasi; Cap C digabung ke Cap E, Cap E pelat h 1.800) sedang dikerjakan
di cabang `fitur/tahap-6-9-bim`. Langkah 6.10 (gambar) dan 6.11 (ringkasan) menyusul. Rencana ini tidak memakai angka
6.9: angka pondasi dibaca dari model dan ringkasan Tahap 6 saat langkah 7.0 dimulai.

Lingkup Tahap 7 menurut `00 RANCANGAN.md` bagian 3 adalah DED dari model BIM, RKS (spesifikasi teknis), model arsitektur
lengkap, dan **render akhir setara portofolio**. Syarat render (arahan Defsa 20 Nov 2026) ada di RANCANGAN baris 44-54:
acuan gaya foto `acuan/privat/Referensi Fasad RS dari Defsa.jpg` dan purwarupa `model/RSTB-ARS-T4-Fasad-V4.bimc`;
nama "RUMAH SAKIT TEPIAN BATANGHARI" dan logo "H" terbaca, lingkungan lengkap, beberapa sudut, fotorealistis (Blender
+ Bonsai dari IFC BIMCraft), dan struktur tidak diubah oleh fasad. Desain MEP tetap di luar lingkup (RANCANGAN bagian
2): MEP hanya beban, ruang, shaft, dan lubang.

Bawaan dari Tahap 2-6 yang wajib masuk:

| No | Butir | Asal | Langkah |
|---|---|---|---|
| B-1 | Gambar pondasi 6.10 (GS-28..GS-32, GT-16): bila 6.10 belum selesai saat 7.0, gambar dirakit di 7.5 dari model 6.9 | Rencana 6.10 | 7.0, 7.5 |
| B-2 | Serakan lateral Zhang 4,58 m masih terbuka: tiang Ø800 tidak menahan (rasio M 8,4-8,5); syarat perbaikan tanah U5 di jalur tebing atau tiang batas Ø600 (6.4: berm + pelandaian + baris Ø600 ±9,6 m) | 6.4, 6.5, 6.7 | 7.0 (keputusan), 7.5, 7.7 |
| B-3 | Program uji tiang 6.8 dirinci di RKS: 2 uji statik konstruksi 200 % × izin (3.166 / 2.886 kN), tarik Cap D 2.178 kN, lateral 2 × 53,95 kN, PIT +23 / +9, CSL dan PDA, T113 CSL ulang + coring | 6.8 | 7.7 |
| B-4 | Dewatering galian cap: sump terbuka cap kolom, parit keliling + sump Cap E dan pit, pompa cadangan; muka air di sisi gudang timur tidak di bawah +8,6 (kepala cerucuk +8,62); INC-1 ≤ 0,18 mm/hari (margin tipis) | 2.8, 6.8 | 7.7 |
| B-5 | Beton paparan S2 + perlindungan asam, f'c tiang 35 MPa, pelat LT1 dan sloof f'c 35, selimut bawah 50 mm | 2.7, 5.3, 6.7 | 7.5, 7.7 |
| B-6 | Fasad: elevasi overstek disesuaikan di model (konsol +3,60-+3,90, GS-19); beban fasad akhir dicek ulang terhadap `4.10 Rincian Fasad V3.xlsx` (6.028 kN), angkur, balok tepi | 4.10 | 7.1, 7.3 |
| B-7 | Chiller M-01 vs 14,5 Hz: pegas 25 mm di atas balok utama atau pindah ke y ≥ 63; frekuensi alami pelat/balok atap | Evaluasi Kunci Tahap 4 no. 1 | 7.2, 7.3 |
| B-8 | Pelat turun LB-1 (CSSD LT2, -300 mm): tebal/tulangan lokal atau balok tepi | Evaluasi Kunci Tahap 4 no. 5 | 7.3, 7.5 |
| B-9 | Tempat parkir P4 (76 motor) yang hilang oleh jalur ambulans 5.2; R-06 di atas pegas; beban arsip terbatas zona; tangki opsi B tampak di tepi utara | 5.1, 5.2, Ringkasan Tahap 5 | 7.1, 7.2 |
| B-10 | Spesifikasi produk kedap (pit, pelat LT1), baja tahan karat ASTM A955M di zona MRI 2 × 2 m | 5.2, 5.5 | 7.7 |
| B-11 | Sisa penurunan tanah utara 874 mm terhadap pelat halaman dan sambungan utilitas (bukan tiang) | 6.6 | 7.1, 7.2, 7.7 |
| B-12 | Surat tanggapan teknis ke owner (atap, chiller, MRI, AHU LT3, helipad tahap 2, pit lift) dan jawaban kelas situs SF untuk TABG | Evaluasi Kunci Tahap 4 no. 6-7 | 7.9 (lampiran laporan akhir) |

## Cara kerja

- **Defsa menetapkan isi, AI menyusun.** Tahap 7 sebagian besar dokumentasi. Hitungan baru hanya di 7.3 (cek kecil
  B-6..B-8); untuk itu Defsa menghitung dulu bila sempat, kalau tidak AI menghitung dan Defsa memeriksa.
- Setiap langkah berhenti dengan label **"draf, menunggu persetujuan Defsa"**.
- **Gambar dari model, bukan digambar ulang.** Denah, tampak, dan potongan dari IFC BIMCraft; anotasi, kop, dan detail
  di CADCraft menurut `ATURAN GAMBAR CADCRAFT.md` (`KOP_A3`, ukuran asosiatif, block, `cad_cek` 0 pasangan, potongan
  tanpa poché pejal, cap "STUDI KASUS PORTOFOLIO — TIDAK UNTUK KONSTRUKSI").
- Word (RKS) dan Excel mengikuti `FORMAT LAPORAN DAN EXCEL.md` (`skrip/format_dokumen.py`), dirender ke PDF dan dicek.
- **RKS: tiap pasal teknis menyebut acuannya dan dicek ke PDF** di `acuan/`. Yang sudah ada: SNI 2847:2019 Pasal 26
  (dokumen konstruksi dan inspeksi: 26.4 material beton, 26.5 produksi dan perawatan, 26.6 tulangan, 26.11 bekisting,
  26.12 evaluasi dan penerimaan beton, 26.13 inspeksi; hal. PDF 640-681), SNI 8460:2017 Pasal 9.8 (uji tiang: 9.8.1
  tekan, 9.8.2 tarik, 9.8.3 lateral, 9.8.4 PDA, 9.8.5-9.8.6 integritas; hal. PDF 205-209), SNI 2052:2017 (baja tulangan),
  SNI 1726:2019, SNI 1727:2020. SNI uji material (uji tekan silinder, slump), pekerjaan arsitektur, proteksi kebakaran,
  dan aksesibilitas **belum ada di acuan** (lihat `acuan/README.md`): ditulis "belum ada di acuan", tidak ditebak.
- Render: sumber tetap model BIM (IFC). Blender + Bonsai di `alat/blender/`; material, lampu, lansekap, dan kamera
  ditambahkan di berkas Blender terpisah supaya IFC tetap bersih.
- Kunci di `../02 Siap Terbit/privat/studi-kasus-kunci/` tidak dibuka.
- Model/effort (`PERINTAH DAN SKILL.md` baris 44): Opus medium untuk sesi langkah dan RKS; gambar, model, dan render
  oleh subagen Sonnet. Skill: bonsai-impl-drawing, bim-clash-detection, bim-validation-pipeline, ifcos-impl-validation,
  docx. Modul ifcopenshell, python-docx.
- Uji hanya berkas yang disentuh; seluruh uji sekali di akhir tahap.
- Git: cabang `fitur/tahap-7-<langkah>`, pesan Indonesia, PR selesai langsung merge, lalu pull `main`.
- Cek silang mulai **T-109**. Seri gambar: arsitektur **GA-01..**, struktur melanjutkan **GS-33..** (GS-27..32 milik
  Tahap 6), MEP dasar **GM-01..**, render **R-01..**. Catatan: tiang "T113" (CSL) bukan cek silang T-113.

## Langkah

| Langkah | Isi | Keluaran (`07 DED dan RKS/`) |
|---|---|---|
| 7.0 | Telaah dan daftar dokumen: status 6.9-6.11, daftar lembar DED tiga disiplin, daftar pasal RKS, acuan yang belum ada, keputusan B-2 | `7.0 Telaah dan Daftar Dokumen.xlsx` + `.md` |
| 7.1 | Model arsitektur lengkap BIMCraft LOD 300 (gedung utama, utilitas + parkir, tapak dan lansekap), fasad V4 dikunci | `model/RSTB-ARS-T7-LOD300.bimc/.ifc` |
| 7.2 | Federasi model ARS + STR (5.7, 6.9) + ruang MEP, clash dan koordinasi (shaft, bukaan, ruang alat, chiller, P4) | `7.2 Koordinasi dan Clash.xlsx`, `model/RSTB-FED-T7.ifc` |
| 7.3 | Cek struktur tambahan kecil: beban fasad akhir, frekuensi pelat atap chiller, pelat turun LB-1 | `7.3 Cek Struktur Tambahan.xlsx` + `.md` |
| 7.4 | DED arsitektur dari model: denah tiap lantai, tampak, potongan, detail fasad, tangga, toilet, finishing, tapak | GA-01.., `Gambar/DWG/`, PDF A3 |
| 7.5 | DED struktur: rakit GS-01..32 (+ pondasi 6.10 bila B-1), tambahan GS-33.. (LB-1, perkuatan tebing B-2), catatan umum | GS-33.., satu set PDF struktur |
| 7.6 | DED MEP dasar (koordinasi saja): denah shaft, ruang alat, bukaan pelat/dinding, beban alat | GM-01.. |
| 7.7 | RKS per pekerjaan: umum, tanah dan dewatering, tiang bor dan uji, beton dan tulangan, arsitektur, fasad, kedap, MEP dasar | `7.7 RKS.docx` + PDF |
| 7.8 | Render akhir fotorealistis setara portofolio (Blender + Bonsai) | `Render/R-01..R-08.png` (≥ 3.000 px), `render/RSTB-Render-T7.blend` |
| 7.9 | Ringkasan Tahap 7, daftar dokumen DED, PROGRES, PR | `Ringkasan Tahap 7.md` |

### 7.0 Telaah dan daftar dokumen

1. **Status Tahap 6:** 6.9 model (IFC pondasi, Cap E sesuai 6.9), 6.10 gambar, 6.11 ringkasan. Yang belum selesai dicatat
   ke B-1; angka pondasi untuk RKS dibaca dari ringkasan Tahap 6, bukan dari rencana ini.
2. **Daftar lembar DED** tiga disiplin (nomor, judul, skala, sumber view model), dari rencana di
   `04 Struktur Atas/00 Rencana Tahap 4.md` bagian B dan daftar GS-01..GS-32 yang ada.
3. **Daftar isi RKS** dan pasal acuan per pekerjaan; tiap pasal diberi status "dicek ke PDF" atau "belum ada di acuan".
4. **Keputusan B-2 (serakan Zhang)** diambil di sini karena menentukan gambar tebing GS dan RKS tanah.
5. Cek murah: jumlah lantai dan elevasi model ARS = STR (peil +12,85, halaman +12,05), grid as 1-10 / A-G modul 8 m,
   luas lantai model 3.9/4.10 vs program ruang 3.4.

**Berhenti: Defsa menyetujui daftar dokumen dan keputusan B-2.**

### 7.1 Model arsitektur lengkap

- Basis: fasad V4 (`RSTB-ARS-T4-Fasad-V4.bimc`) di atas model struktur 5.7 + pondasi 6.9, dengan `skrip/bimcraft.py`.
- Isi: dinding dalam dan luar, pintu dan jendela bertipe, ruang bernama sesuai program 3.4, tangga dan lift, plafon,
  finishing lantai per zona (Pset), dinding tirai, overstek pada elevasi konsol (B-6), mahkota menara, tangki tepi utara.
- Tapak: halaman, jalan masuk dan drop-off berkanopi, ramp IGD beratap, parkir (termasuk P4, B-9), pagar dan gerbang,
  papan nama, lampu jalan, taman atap V1, dek helipad, gedung utilitas + parkir, tepi sungai dan tebing (B-2).
- Model utuh, bisa dibuka 3D di jendela BIMCraft (`ke_v011()` bila perlu) dan dilanjutkan manual.

**Berhenti: Defsa menyetujui model arsitektur.**

### 7.2 Federasi dan koordinasi

- Gabung IFC ARS + STR + ruang MEP; clash (ifcopenshell / skill bim-clash-detection): struktur vs arsitektur, shaft dan
  bukaan vs balok, pit vs cap, chiller M-01 vs balok atap (B-7), R-06 di atas pegas, ruang MRI dan jalur ambulans.
- Validasi IFC: hierarki ruang, Pset wajib, nama unsur (skill ifcos-impl-validation, IDS sederhana).
- Daftar clash berstatus (diperbaiki / diterima / ditanyakan); "ditanyakan" harus punya tindakan dan pemilik.

**Berhenti: Defsa menyetujui hasil koordinasi.**

### 7.3 Cek struktur tambahan

- Beban fasad akhir model 7.1 vs 4.10 (6.028 kN) dan asumsi 4.2; bila naik, angkur dan balok tepi dicek ulang.
- Frekuensi alami pelat/balok atap dengan massa chiller vs 14,5 Hz; pilihan pegas 25 mm atau pindah ke y ≥ 63 (B-7).
- Pelat turun LB-1: tebal dan tulangan lokal atau balok tepi (SNI 2847 pasal dicek saat menghitung) (B-8).

**Berhenti: Defsa menyetujui cek tambahan.**

### 7.4-7.6 DED tiga disiplin

- Arsitektur GA: denah LT1-LT6 dan atap 1:100 (1:200 bila tidak muat A3, dicatat), tampak empat sisi, dua potongan,
  detail fasad 1:20, tangga, toilet tipikal, rencana tapak, daftar pintu dan jendela, daftar finishing.
- Struktur GS: rakit set lama, tambah GS-33.. (LB-1, perkuatan tebing B-2, catatan umum mutu S2 B-5), satu PDF.
- MEP dasar GM: shaft, ruang alat, bukaan, beban alat per lantai (bukan desain sistem).
- Tiap lembar dicek dengan daftar periksa gambar konsultan (Tahap 4 bagian B) dan `cad_cek` 0 pasangan.

**Berhenti: Defsa menyetujui tiap set gambar.**

### 7.7 RKS

- Bab: syarat umum (lingkup, acuan, mutu, K3 SMKK), pekerjaan persiapan dan tanah (urugan + PVD, galian cap,
  dewatering B-4 dengan batas +8,6 dan pemantauan INC-1, pemantauan gudang), tiang bor dan uji (B-3, SNI 8460 9.8),
  beton dan tulangan (SNI 2847 Pasal 26, S2 + asam B-5, A955M B-10), kedap dan pit, arsitektur dan fasad, MEP dasar
  (bukaan dan landasan alat), toleransi dan penerimaan.
- Angka di RKS diambil dari dokumen tahap yang disetujui dan dirujuk (berkas + butir); tidak ada angka baru tanpa sumber.
- Pekerjaan tanpa acuan di `acuan/` ditulis "acuan belum ada" dan masuk daftar acuan yang dicari.

**Berhenti: Defsa menyetujui RKS.**

### 7.8 Render akhir

- IFC federasi 7.2 dibuka di Blender + Bonsai; material PBR (panel putih, kaca biru, panel abu podium, aspal, rumput,
  air sungai), langit HDRI atau Sky Texture, Cycles, resolusi ≥ 3.000 px.
- Sudut minimum: siang tiga perempat dari jalan masuk, senja dengan lampu menyala, mata burung dengan sungai dan tebing,
  depan lobi dengan papan nama, IGD dengan ramp beratap, helipad; ditambah dua sudut bebas (R-01..R-08).
- Cek: nama dan logo "H" terbaca di ukuran thumbnail; tidak ada unsur melayang atau tembus; skala manusia dan mobil wajar.
- Render BIMCraft datar tidak dipakai sebagai hasil akhir.

**Berhenti: Defsa memilih render yang dipakai portofolio.**

### 7.9 Ringkasan dan PR

- `Ringkasan Tahap 7.md`, daftar dokumen DED (nomor, revisi, status), lampiran surat tanggapan B-12, PROGRES, seluruh
  uji sekali di latar, pindai privasi, PR, merge, pull `main`.

## Cek silang yang direncanakan

Toleransi ditetapkan sebelum mengerjakan dan dicatat di `VERIFIKASI.md`:

| No | Cek | Cara 1 | Cara 2 | Toleransi |
|---|---|---|---|---|
| T-109 | Luas ruang model vs program ruang | IFC IfcSpace (ifcopenshell) | program 3.4 | ≤ 5 % per zona, ≤ 2 % total |
| T-110 | Elevasi dan grid ARS = STR | IFC ARS | IFC STR 5.7/6.9 | ≤ 1 mm |
| T-111 | Clash kritis | ifcopenshell (bim-clash-detection) | Bonsai / pemeriksaan visual 3D | 0 clash kritis terbuka |
| T-112 | Beban fasad akhir | QTO model 7.1 | rincian 4.10 | ≤ 5 % (lebih: cek ulang angkur) |
| T-113 | Frekuensi alami pelat atap chiller | rumus tangan | openseespy | ≤ 10 % |
| T-114 | Ukuran gambar vs model | ukuran asosiatif DWG | koordinat IFC | ≤ 1 mm |
| T-115 | Pasal RKS vs PDF acuan | daftar pasal RKS | teks PDF di `acuan/` | 100 % ditemukan atau berlabel "belum ada" |
| T-116 | Angka RKS vs dokumen tahap | angka di RKS | berkas sumber yang dirujuk | 0 selisih |
| T-117 | Render vs model | jumlah unsur IFC di Blender | jumlah unsur IFC BIMCraft | 0 selisih |
| T-118 | Excel = Python | Excel dihitung ulang | Python | ≤ 0,1 % |

## Keputusan (disetujui atas delegasi Defsa 22 Nov 2026)

Defsa mendelegasikan semua keputusan rencana ke AI pada malam 22 Nov 2026. Usulan AI di bawah dipakai dan boleh diubah
Defsa di awal langkah terkait.

| No | Keputusan | Usulan AI (dipakai) | Alasan |
|---|---|---|---|
| 1 | **(7.0) Serakan Zhang B-2** | Perkuatan tebing di batas lahan: berm + pelandaian + satu baris tiang bor Ø600 (rincian 6.4) dan perbaikan tanah U5 di jalur tebing sampai di belakang baris tiang y 26,3 m; dimensi akhir dihitung di 7.3 bila perlu, gambar di 7.5, metode di 7.7 | Tiang gedung Ø800 tidak menahan Zhang (rasio 8,4); geser garis tiang tidak menolong (6.4) |
| 2 | **(7.0) Gambar pondasi bila 6.10 belum selesai** | Tetap di Tahap 6 (6.10); 7.5 hanya merakit. Bila 6.10 belum selesai saat 7.5, dikerjakan di 7.5 dengan nomor GS-28..32 | Nomor dan isi sudah direncanakan di Tahap 6 |
| 3 | **(7.1) Varian fasad** | V4 (gaya foto acuan) dikunci untuk DED dan render; V3 tetap dasar beban struktur sampai T-112 | Arahan Defsa 20 Nov 2026; V4 sudah diuji render |
| 4 | **(7.1) Tempat P4 76 motor** | Area parkir motor di sisi barat tapak dekat gedung utilitas, dicek KDB dan jalur ambulans di 7.2 | Jalur ambulans timur dan MRI tetap (5.2 opsi 2) |
| 5 | **(7.3) Chiller M-01** | Pegas 25 mm di atas balok utama bila frekuensi pelat ≥ 1,4 × 14,5 Hz (rasio [Asumsi], dicek ke acuan getaran bila ada); jika tidak, pindah ke y ≥ 63 | Tidak memindah tata letak atap bila tidak perlu |
| 6 | **(7.3) LB-1** | Balok tepi di sekeliling pelat turun, pelat tetap tebal tipikal | Mengikuti pola balok tepi 4.10 |
| 7 | **(7.4) Skala denah** | 1:100 per bagian (dibagi dua lembar bila panjang); kunci plan 1:300 | Standar DED; A3 |
| 8 | **(7.6) MEP** | Hanya koordinasi (shaft, ruang alat, bukaan, beban), sesuai lingkup RANCANGAN | Desain MEP di luar lingkup |
| 9 | **(7.7) Bentuk RKS** | Satu Word per pekerjaan dalam satu berkas, pasal bernomor, acuan per pasal, lampiran program uji tiang dan dewatering | Mudah dirujuk di RAB Tahap 8 |
| 10 | **(7.7) Dewatering di RKS** | Metode 6.8 (sump terbuka + parit keliling Cap E dan pit, pompa cadangan), batas muka air +8,6 di sisi gudang, berhenti kerja bila INC-1 > 0,18 mm/hari | Disetujui di 6.8; margin INC-1 tipis |
| 11 | **(7.8) Alat render** | Blender Cycles + Bonsai dari IFC federasi; berkas `.blend` terpisah | Syarat RANCANGAN; BIMCraft render datar |
| 12 | **(7.8) Jumlah render** | 8 sudut (6 wajib + 2 bebas), ≥ 3.000 px | Isi minimum RANCANGAN baris 51 |
| 13 | **(Tiap langkah)** Persetujuan hasil | Tiap langkah tetap berhenti "draf, menunggu persetujuan Defsa" | Aturan proyek |

Lingkup yang lebih kecil bila Defsa ingin cepat: gabung 7.4-7.6 menjadi satu langkah gambar, atau render 6 sudut wajib
saja.
