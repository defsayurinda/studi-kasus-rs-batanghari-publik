# Ringkasan Tahap 7: DED dan RKS

STATUS: **disetujui Defsa 23 Nov 2026** (langkah 7.0-7.7 dikerjakan atas delegasi 22 Nov 2026, 7.8 render 23 Nov 2026; ringkasan ditelaah Defsa). DATA SIMULASI untuk studi kasus portofolio, tidak untuk konstruksi.

Sumber: md tiap langkah di folder ini, `00 Rencana Tahap 7.md`, `PROGRES.md`, `10 Laporan/Evaluasi Kunci Tahap 4.md`
(untuk B-12). Angka di bawah disalin dari berkas sumber, tidak dihitung ulang.

## 1. Hasil per langkah

| Langkah | Keluaran | Hasil pokok | Cek silang |
|---|---|---|---|
| 7.0 Telaah | `7.0 Telaah dan Daftar Dokumen.xlsx` + `.md` | Status 6.9-6.11; daftar DED tiga disiplin; RKS 15 bab + 2 lampiran dengan status acuan (9 acuan belum ada); keputusan K7-1..K7-5 | Elevasi/grid STR vs `tahap4_beban` 0,0 mm |
| 7.1 Model ARS | `model/RSTB-ARS-T7-LOD300.bimc/.ifc` (+ `-v0.11.bimc`), `7.1 Model Arsitektur.md` | LOD 300: 1.414 dinding, 224 pintu, 235 ruang bernama, 171 plafon, fasad V4, overstek +3,60-+3,90, tapak (P4 76 motor sisi barat), taman atap, helipad, gedung utilitas, tebing | T-110 lolos (0,000 mm); T-109 (a)(b) lolos, (c) gagal karena Rekap 3.4, lalu Rekap dikoreksi di 7.2 |
| 7.2 Federasi dan clash | `model/RSTB-FED-T7.ifc`, `7.2 Koordinasi dan Clash.xlsx` + `.md` | ARS + STR + 7 alat MEP + 31 ruang shaft; clash 2,5D 1.612 → 1.156 pasangan; shaft di ARS diperbaiki (K-03 392 → 0); jalur IGD ke lajur x 92,5-98,5, jarak MRI 4,1 → 12,0 m | T-111 awalnya gagal (K-01), lolos setelah 7.3: 1.132 pasangan, 0 kritis terbuka |
| 7.3 Cek struktur | `7.3 Cek Struktur Tambahan.xlsx` + `.md`, `model/RSTB-STR-T7-LOD300` | K-01: 6 balok as 6 di inti lift dihapus (OpenSees berubah maks 0,22 %); chiller pindah ke y ≥ 63 di atas 7 rel baru + pegas δ 25 mm (frekuensi atap 4,1/5,6 Hz < 20,3 Hz); L-7 Cap E diperlebar + 2 tiang Ø800 (321 tiang, 84 cap); LB-1 balok tepi lolos | T-112 lolos (fasad V4 2.989 kN vs V3 6.028 kN); T-113b lolos; T-113 gagal toleransi 10 % (-28 %, ragam berbeda, keputusan tidak peka) |
| 7.4 DED arsitektur | GA-01..GA-23 (DWG + PNG), `7.4 Gambar Arsitektur DED.pdf`, `7.4 Gambar Arsitektur.md` | Denah 1:250 per setengah (LT1-LT3), 1:300 (LT4-6, atap); tampak diproyeksikan dari dinding fasad model | T-114 lolos (53 ukuran, 0,000 mm); cad_cek 0 pasangan di 23 DWG |
| 7.5 DED struktur | GS-01..GS-35, `7.5 Gambar Struktur DED.pdf` (35 hal.), `7.5 Gambar Struktur.md` | Rakit GS-01..32 dari Tahap 4-6; baru GS-33 LB-1, GS-34 rel chiller, GS-35 catatan umum + skema tebing B-2; GS-28/29/32 diperbarui untuk Cap E diperlebar | cad_cek 0; uji 321 tiang |
| 7.6 DED MEP dasar | GM-01..GM-06, `7.6 Gambar MEP Dasar DED.pdf` (6 hal.), `7.6 MEP Dasar.md` | Koordinasi saja: 8 shaft + void lift, bukaan 7 inti, ruang alat atap podium, zona MRI 12,0 m, beban alat per lantai (LT3 3.010,3 kN) | Lubang pelat IFC STR 7.3 = `tahap4_bim.SHAFT`; cad_cek 0 |
| 7.7 RKS | `7.7 RKS.docx` + `.pdf` (25 hal.) | 15 bab + Lampiran A program uji tiang, B ambang pemantauan, C pasal dan keputusan; angka dari Ringkasan Tahap 6 dan 6.8 | T-115 lolos (30 pasal: 20 dicek ke PDF, 9 belum ada di acuan, 1 acuan publik); T-116 lolos (32 angka, 0 selisih) |
| 7.8 Render | lihat bagian 3 | **Selesai (draf, atas delegasi Defsa)**: render v2 R-01..R-08, 5 dipilih | T-117 lolos (5.029 unsur, 0 selisih; v2 memakai blend dasar yang sama) |

Bawaan B-1..B-11 dari Tahap 2-6 tertutup di langkah tujuannya (B-1 di 7.5, B-2 skema di GS-35 + RKS bab 5, B-3/B-4/B-10/B-11
di RKS, B-5 di GS-35 + RKS, B-6 dan B-8 di 7.3, B-7 di 7.3, B-9 di 7.1). B-12 menjadi Lampiran A ringkasan ini.

## 2. Keputusan (disetujui atas delegasi Defsa 22 Nov 2026)

Defsa mendelegasikan semua keputusan Tahap 7 ke AI pada malam 22 Nov 2026. Semua boleh diubah Defsa saat meninjau.

| No | Langkah | Keputusan |
|---|---|---|
| K7-1 | 7.0 | B-2 serakan Zhang 4,58 m: perkuatan tebing di batas lahan (berm + pelandaian + satu baris tiang bor Ø600) dan perbaikan tanah U5 sampai di belakang baris tiang y 26,3 m |
| K7-2 | 7.0 | Gambar pondasi tetap milik 6.10; 7.5 hanya merakit |
| K7-3 | 7.1 | Fasad V4 dikunci untuk DED dan render; V3 tetap dasar beban sampai T-112 |
| K7-4 | 7.1 | P4 76 motor di sisi barat tapak dekat gedung utilitas (x 1-7, y 35-63,5) |
| K7-5 | 7.3 | Chiller M-01 pindah ke y ≥ 63, unit diputar, di atas 7 rel 300 × 500 + pegas δ 25 mm (frekuensi pelat < 1,4 × 14,5 Hz) |
| K7-6 | 7.3 | K-01: balok BL-350x600 as 6 di ruang luncur lift dihapus (perubahan respons ≤ 0,22 %) |
| K7-7 | 7.3 | K-04b: pit L-5..6 sebagai kantilever pelat dasar; L-7 dengan perlebaran Cap E + 2 tiang Ø800 baru |
| K7-8 | 7.3 | LB-1: balok tepi di sekeliling pelat turun, pelat tetap tebal tipikal |
| K7-9 | 7.4 | Skala denah disesuaikan A3 (1:250-1:300); set A1 1:100 bisa dibangun dari tabel `LEMBAR` bila perlu |
| K7-10 | 7.6 | MEP hanya koordinasi (shaft, ruang alat, bukaan, beban) |
| K7.7-1..6 | 7.7 | Kriteria lateral SNI 8460 Pasal 9.8.3 dievaluasi terhadap prediksi 6.5; uji k urugan sebelum galian; pompa 2 × Q + cadangan [Asumsi]; berhenti kerja bila INC-1 > 0,18 mm/hari selama 3 hari; deep mixing untuk U5; f'c 35 unsur kontak tanah |
| K7-11 | 7.8 | Blender Cycles + Bonsai dari IFC federasi, berkas `.blend` terpisah; 8 sudut ≥ 3.000 px |

## 3. Langkah 7.8 render (selesai, draf atas delegasi Defsa, 23 Nov 2026)

Render revisi archviz (aset CC0 Poly Haven, mobil berbentuk, papan nama huruf asli, mullion, kaca reflektif, HDRI langit)
dirender di **Google Colab (T4)** pada 3.200 × 1.800 px, 128 sampel + denoiser, karena laptop mati sendiri saat render
(pendingin hasil servis 7 Nov 2026 tidak menempel). Render v1 (PR #70) diganti. Dilihat AI pada pratinjau 1.000 px.

| Berkas | Sudut | Penilaian | Dipilih |
|---|---|---|---|
| `Render/R-01.png` | Siang, dari atas Batanghari, pantulan gedung di air | langit berawan, nama dan logo H terbaca, tebing berumput; **pilihan utama (sampul, Laporan Akhir)** | **ya** |
| `Render/R-02.png` | Sore keemasan dari barat daya | hangat, tetapi pohon depan menutup separuh gedung dan langit polos | tidak |
| `Render/R-03.png` | Udara, konteks tapak | gedung utama, gedung parkir, parkir, pagar, jalan; menunjukkan tapak | **ya** |
| `Render/R-04.png` | Senja biru, lobi dan gerbang utara | jendela menyala, papan nama gerbang, pagar jeruji | **ya** |
| `Render/R-05.png` | Senja biru, IGD dan kanopi drop-off | mobil terlalu dekat dan bodinya menggelembung (salib besar); ramp tak terlihat | tidak |
| `Render/R-06.png` | Udara dekat, helipad | marka H dan lingkar kuning jelas, atap dan parkir; terbaik untuk atap | **ya** |
| `Render/R-07.png` | Sore mata burung | horizon tinggi, rumput datar, gedung kecil | tidak |
| `Render/R-08.png` | Seberang sungai, pantulan | frontal datar tetapi pantulan dan nama terbaca | **ya** |

- **Urutan pakai:** R-01 (sampul, Laporan Akhir), R-06, R-03, R-04, R-08.
- **Kelemahan tersisa:** tanpa figur orang (tidak ada aset orang CC0 yang layak); mobil R-05 kurang halus; video 6 shot
  tidak dikejar (tidak masuk hasil Colab).
- **T-117 (adegan revisi):** adegan revisi hanya menambah aset dan bahan di atas `render/RSTB-Dasar-T7.blend`, yang
  disimpan dari impor Bonsai yang sama dengan v1 (`skrip/tahap7_render.py`); unsur gedung tidak diubah, jadi hasil T-117
  tetap 20 kelas, 5.029 unsur, 0 selisih. Uji `test_t117_unsur_blender_sama_ifc` lolos. Log render Colab tidak dibawa
  kembali, jadi hitungan tidak diulang di adegan akhir.

## 4. Daftar dokumen DED

Konvensi revisi daftar ini: **Rev. 0** = terbitan DED Tahap 7 (22 Nov 2026); **Rev. 1** = lembar yang diubah setelah
terbit pertamanya. Semua lembar berstatus **draf, disetujui atas delegasi Defsa** dan bercap "STUDI KASUS PORTOFOLIO —
TIDAK UNTUK KONSTRUKSI". Ukuran kertas A3.

### 4.1 Arsitektur (`7.4 Gambar Arsitektur DED.pdf`)

| No | Judul | Skala | Rev. |
|---|---|---|---|
| GA-01 | Daftar gambar, catatan umum arsitektur, legenda | - | 0 |
| GA-02 | Rencana tapak dan lansekap (parkir, P4, pagar, tebing) | 1:500 | 0 |
| GA-03 | Kunci denah | 1:300 | 0 |
| GA-04 | Denah LT1 bagian barat (as 1-5) | 1:250 | 0 |
| GA-05 | Denah LT1 bagian timur (as 5-10) | 1:250 | 0 |
| GA-06 | Denah LT2 bagian barat | 1:250 | 0 |
| GA-07 | Denah LT2 bagian timur | 1:250 | 0 |
| GA-08 | Denah LT3 bagian barat | 1:250 | 0 |
| GA-09 | Denah LT3 bagian timur | 1:250 | 0 |
| GA-10 | Denah LT4-LT6 tipikal rawat inap | 1:300 | 0 |
| GA-11 | Denah atap, taman atap, dek helipad | 1:300 | 0 |
| GA-12 | Denah plafon (RCP) LT1-LT3 | 1:750 | 0 |
| GA-13 | Tampak selatan dan utara | 1:500 | 0 |
| GA-14 | Tampak barat dan timur | 1:400 | 0 |
| GA-15 | Potongan A-A dan B-B | 1:400 | 0 |
| GA-16 | Detail fasad tipikal | 1:25 | 0 |
| GA-17 | Detail overstek podium dan mahkota menara | 1:50 | 0 |
| GA-18 | Detail tangga darurat dan ruang lift | 1:100 | 0 |
| GA-19 | Detail toilet tipikal dan toilet difabel | 1:30 | 0 |
| GA-20 | Detail kanopi drop-off dan ramp IGD beratap | 1:150 | 0 |
| GA-21 | Daftar pintu dan jendela | - | 0 |
| GA-22 | Daftar finishing ruang | - | 0 |
| GA-23 | Gedung utilitas dan parkir: denah dan tampak | 1:300 | 0 |

### 4.2 Struktur (`7.5 Gambar Struktur DED.pdf`)

| No | Isi | Asal | Rev. |
|---|---|---|---|
| GS-01 | Respons spesifik situs | 4.1 | 0 |
| GS-02 | Zona beban | 4.2 | 0 |
| GS-03..GS-20 | Struktur atas DED (18 lembar) | 4.10 | 0 |
| GS-21 | Plot data owner | 5.0 | 0 |
| GS-22..GS-26 | Struktur tengah: pelat LT1, sloof, pit lift (5 lembar) | 5.8 | 0 |
| GS-27 | Telaah data pondasi | 6.0 | 0 |
| GS-28 | Denah tiang dan pile cap (321 tiang) | 6.10, diperbarui 7.5 | **1** (Cap E diperlebar + 2 tiang) |
| GS-29 | Pile cap inti dan Cap E | 6.10, diperbarui 7.5 | **1** (Cap E berbentuk L) |
| GS-30 | Pile cap tipikal | 6.10 | 0 |
| GS-31 | Detail tiang bor dan penulangan | 6.10 | 0 |
| GS-32 | Tabel tiang dan cap | 6.10, diperbarui 7.5 | **1** (321 tiang, PC-E 56 tiang) |
| GS-33 | Denah dan penampang balok LB-1, pelat turun | 7.5 | 0 |
| GS-34 | Rel dan dudukan chiller M-01 di pelat atap | 7.5 | 0 |
| GS-35 | Catatan umum struktur + skema perkuatan tebing B-2 | 7.5 | 0 |

Geoteknik GT-16 (potongan tebing, 6.10) tidak masuk set struktur. Penomoran GS-33..35 berbeda dari rencana 7.0
(GS-33..36); yang berlaku adalah tabel ini.

### 4.3 MEP dasar (`7.6 Gambar MEP Dasar DED.pdf`)

| No | Judul | Skala | Rev. |
|---|---|---|---|
| GM-01 | Daftar gambar, lingkup, catatan umum MEP dasar | - | 0 |
| GM-02 | Denah kunci shaft dan lubang pelat per lantai | 1:300 | 0 |
| GM-03 | Ruang alat atap podium: chiller M-01, pompa M-04 | 1:150 | 0 |
| GM-04 | Zona MRI LT1, lingkar 12,0 m dari isocenter | 1:250 | 0 |
| GM-05 | Bukaan pintu dinding inti lift dan tangga | 1:100 | 0 |
| GM-06 | Beban alat MEP per lantai dan daftar alat | - | 0 |

### 4.4 Dokumen lain

| Dokumen | Berkas | Rev. | Status |
|---|---|---|---|
| RKS | `7.7 RKS.docx` + `.pdf` | 0 | disetujui atas delegasi |
| Model ARS LOD 300 | `model/RSTB-ARS-T7-LOD300.bimc/.ifc` | 0 | disetujui atas delegasi |
| Model STR Tahap 7 | `model/RSTB-STR-T7-LOD300.bimc/.ifc` | 0 | disetujui atas delegasi |
| Model federasi | `model/RSTB-FED-T7.ifc` | 0 | disetujui atas delegasi |
| Render R-01..R-08 | `Render/` | v2 | selesai, 5 dipilih (bagian 3) |

Jumlah: 23 GA + 35 GS + 6 GM = **64 lembar**.

## 5. Butir terbuka

| No | Butir | Asal | Ke |
|---|---|---|---|
| O-1 | ~~Render revisi (Colab), pemilihan, T-117~~ **ditutup 23 Nov 2026** (video 6 shot tidak dikejar) | 7.8 | - |
| O-2 | IFC STR 6.9 belum memuat Cap E diperlebar + 2 tiang (model STR 7.3 sudah, 321 IfcPile); tulangan perlebaran [Asumsi sama dengan Cap E] belum dihitung | 7.3, 7.5 | **Ditutup 23 Nov 2026** (atas delegasi Defsa, `10 Laporan/Audit Akhir.md` AU-05): IFC STR 7.3 adalah model pondasi akhir dan sumber Qto 8a (T-119a lolos); IFC 6.9 dibiarkan sebagai rekaman Tahap 6. Tulangan perlebaran: di luar lingkup portofolio |
| O-3 | Dimensi akhir dan gambar rinci perkuatan tebing B-2 (GS-35 hanya skema) | 7.0, 7.5 | sebelum RAB Tahap 8 |
| O-4 | ARS 7.1 belum memuat letak chiller/pompa baru; GA-11 atap belum menampilkan letak 7.3 (alat ada di federasi dan GM-03) | 7.3, 7.4 | **Di luar lingkup portofolio** (23 Nov 2026, AU-06): letak alat ada di federasi 7.2 dan GM-03; GA-11 tidak mengubah angka |
| O-5 | Temuan ke konsultan MEP: pompa M-04 0,4 m dari chiller (< zona servis 1,0 m [Asumsi], usul geser ke x 59,4-67,4); chiller 0,5 m dari tepi podium utara; SH-7 di pelat turun LB-1 | 7.6 | konsultan MEP |
| O-6 | Acuan belum ada: Permen PUPR 14/2017 (toilet, ramp), SNI uji material, pekerjaan arsitektur, proteksi kebakaran; pasal RKS terkait berlabel "belum ada di acuan" | 7.0, 7.4, 7.7 | `acuan/` |
| O-7 | Label ruang melintas partisi di 1:250-1:300; anak tangga, fixture, titik lampu belum di ARS; set A1 1:100 belum dibuat | 7.4 | Tahap 8 / bila diminta |
| O-8 | Validasi IFC 16/20 (Pset_WallCommon/PileCommon STR, Pset lapis lantai/plafon ARS); render STR 7.3 dan pemeriksaan visual Bonsai | 7.2, 7.3 | **Di luar lingkup portofolio** (23 Nov 2026, AU-07): Qto 8a memakai BaseQuantities (T-119a/b lolos); Pset tambahan tidak mengubah angka |
| O-9 | T-113 di luar toleransi 10 % (-28 %, ragam berbeda); keputusan chiller tidak peka | 7.3 | dicatat di `VERIFIKASI.md` |
| O-10 | Seluruh uji Tahap 7 sekali di akhir tahap belum dijalankan (laptop panas; hanya uji per berkas) | 7.9 | setelah pendingin diperbaiki |

## Lampiran A. Surat tanggapan teknis (B-12)

Draf lampiran laporan akhir. Asal: `10 Laporan/Evaluasi Kunci Tahap 4.md` tindak lanjut no. 6 dan 7.

### A.1 Kepada owner dan konsultan MEP

Perihal: tanggapan teknis atas data dan permintaan owner untuk RS tipe C 6 lantai + basement.

| No | Hal | Tanggapan | Dasar |
|---|---|---|---|
| 1 | Beban atap podium | Ringkasan Atap owner 1.748 kN tidak dipakai; jumlah alat yang dihitung 2.676 kN, tangki 2.168 kN | Tahap 4 (M-1, M-8, M-10), T4-1 |
| 2 | Chiller M-01 di atas ruang sensitif | Frekuensi pelat/balok atap 4,1-5,6 Hz di bawah 1,4 × 14,5 Hz kipas; chiller dipindah ke y ≥ 63 di atas 7 rel 300 × 500 dan pegas δ 25 mm, tidak di atas kamar operasi. Mohon konsultan MEP menggeser pompa M-04 ke x 59,4-67,4 untuk zona servis | 7.3 (K7-5), 7.6, GS-34, GM-03 |
| 3 | MRI dan jalur ambulans | Jarak isocenter ke tepi lajur lama 7,5 m < 12,0 m; jalur ambulans dipindah ke x 92,5-98,5 (jarak 12,0 m), MRI tetap; tulangan baja tahan karat A955M di zona 2 × 2 m, panel MRI monolit 250 | 5.2 opsi 2, 5.3, 7.2, GM-04 |
| 4 | Ruang AHU LT3 pada tahap 1 | Ruang AHU LT3 dihitung terpasang sejak tahap 1 (291 kN + gantung 0,8 kPa); biaya fit-out ruang AHU masuk tahap 1 | Tahap 4 (M-5), K1 |
| 5 | Helipad | Helipad mulai **tahap 2**; atap tahap 1 baja ringan dicek terhadap hisap angin | Tahap 4 (M-4), 4.8 |
| 6 | Pit lift "tidak perlu kedap" | Tidak dapat diterima: dasar pit di bawah muka banjir Q50/Q100 dan tinggi tekan +11,20; pit dibuat kedap (aditif kristalin + waterstop) dan dicek angkat (FK 1,11, pelat dasar 0,45 m) | Tahap 4 (M-3), 5.5, RKS bab kedap |

### A.2 Kepada reviewer TABG: kelas situs

Pertanyaan: "SE atau SF?" Jawaban: situs digolongkan **SF** sejak Tahap 2, sehingga dipakai **spektrum spesifik-situs**
(SNI 1726:2019 Pasal 6.10): SDS 0,386 (dibatasi 80 % spektrum SE), SD1 0,459, KDS D dengan kategori risiko IV.
Frekuensi situs dari fungsi transfer 1,30-1,35 Hz, sesuai HVSR puncak pertama rata-rata 1,36 Hz (T-67); periode situs
0,74-0,77 s. Rincian di `4.1` dan lembar GS-01.
