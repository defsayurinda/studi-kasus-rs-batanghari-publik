# 8b RAB, SMKK, Value Engineering

Status: disetujui Defsa 23 Nov 2026. Data simulasi studi kasus. Harga [Asumsi: Jambi 2026], belum survei harga (SE 47/2026 Lampiran I).

Skrip `skrip/tahap8_rab.py`, Excel `08 RAB/8b RAB SMKK VE.xlsx` (5 lembar, rekap dan jumlah dengan rumus). Keputusan K8-8..K8-11: `08 RAB/00 Rencana Tahap 8.md`.

## 1. Rekapitulasi

| No | Uraian | Jumlah (Rp juta) | Porsi (%) |
|---|---|---:|---:|
| I | Pekerjaan persiapan | 8.547,6 | 3,3 |
| II | Pekerjaan tanah dan pondasi | 48.400,4 | 18,8 |
| III | Pekerjaan struktur atas | 26.441,4 | 10,3 |
| IV | Pekerjaan arsitektur | 42.374,2 | 16,4 |
| V | Pekerjaan tapak dan pematangan lahan | 16.614,9 | 6,4 |
| VI | Pekerjaan MEP rumah sakit (K8-8) | 112.722,3 | 43,7 |
| VII | Biaya penerapan SMKK | 2.757,1 | 1,1 |
| | **Jumlah I-VII** | **257.857,9** | 100,0 |
| | PPN 11 % | 28.364,4 | |
| | **Total dibulatkan** | **286.222,0** | |
| | Biaya per m² (19.328 m² kotor) | 14,81 juta/m² | |

## 2. Rincian di luar model BIM

- MEP RS (K8-8): Alat pengondisian udara 20.808,7; Lift 16.647,0; Tata suara 4.161,7; Telepon dan PABX 2.774,5; Instalasi informasi dan teknologi 11.098,0; Elektrikal termasuk genset 16.647,0; Sistem proteksi kebakaran 13.872,5; Penangkal petir khusus 2.080,9; Instalasi pengolahan air limbah 2.774,5; Gas pembakaran 1.387,2; Gas medis 5.549,0; Penyambungan utilitas 2.774,5; Elektrikal dek parkir 1.068,7; Proteksi kebakaran dek parkir 1.068,7; Utilitas dasar: plambing, sanitair, penerangan, stop kontak 10.009,4 (Rp juta).
- SMKK 9 komponen SE 47/2026 Lampiran III, 15 rincian, Rp 2.757,1 juta (1,08 % biaya fisik); CAR 0,1 % (hal. 260).
- Persiapan, drainase, kolam retensi: lumsum/volume [Asumsi: Jambi 2026]; pematangan lahan dari 3.8 `lahan_nyata()`.

## 3. Value engineering

| Kode | Usulan | Volume | Hemat (Rp juta) | Porsi (%) | Akibat dan syarat |
|---|---|---:|---:|---:|---|
| VE-1 | Spiral tiang di bawah 6 m atas: D13-80 → D13-150 | 92,1 t besi | 1.921,5 | 0,67 | Perencana memeriksa syarat tulangan transversal tiang KDS D di luar zona sendi (SNI 2847:2019, acuan/privat) dan geser tiang Tahap 6.7; tidak dihitung ulang di sini. |
| VE-2 | Fasad kaca: curtain wall unitized → sistem stick (rangka dipasang di tempat) | 2.885 m² | 2.804,9 | 0,98 | Tampak sama; waktu pasang lebih lama ±2 bulan dan mutu kedap air bergantung pengawasan lapangan. |
| VE-3 | Dinding bata ringan: acian langsung 3-5 mm (mortar instan) ganti plester 15 mm + acian | 32.657 m² | 3.067,7 | 1,07 | Syarat pasangan bata ringan rata (toleransi 3 mm); dinding basah tetap plester. |
| VE-4 | Dek helipad ditunda ke tahap 2 (struktur atap sudah disiapkan, K7) | 1.109 m² | 3.200,3 | 1,12 | Sejalan keputusan helipad tahap 2 (Tahap 7); atap dilapis kedap air sementara. |
| VE-5 | Lantai rawat inap: vinil homogen → homogeneous tile 60 × 60 nat epoksi | 2.232 m² | 198,2 | 0,07 | OK, ICU, isolasi tetap vinil (sambungan las, pengendalian infeksi). |

Total VE Rp 11,19 miliar (3,9 %); setelah VE Rp 275,0 miliar terhadap pagu Rp 168,0 miliar (selisih 107,0 miliar).

Kesimpulan (atas delegasi Defsa): biaya per m² Rp 14,81 juta sudah sekitar asumsi owner Rp 14 juta/m², tetapi luas kotor 19.328 m² jauh di atas 12.000 m² dasar pagu. VE saja tidak menutup selisih; pagu cukup untuk ±11.345 m². Rekomendasi: owner menaikkan pagu ke ±Rp 275 miliar (dengan VE-1..VE-5) atau pembangunan bertahap memakai opsi lingkup 3.8 (V1 rampingkan podium LT3, V5 tunda LT4 parkir, V6 LT6 cangkang).

## 4. Cek silang (T-121)

| Kode | Besaran | Cara 1 (Rp juta) | Cara 2 (Rp juta) | Selisih | Batas | Hasil |
|---|---|---:|---:|---:|---|---|
| T-121a | Total RAB termasuk PPN vs perkiraan 3.8 | 286.222,0 | 451.382,0 | -36,6 % | -30 s.d. +50 % | gagal |
| T-121b | Pondasi + struktur tanpa PPN vs 3.8 (fondasi A + struktur) | 74.841,8 | 122.370,3 | -38,8 % | -30 s.d. +50 % | gagal |
| T-121d | Item 8a di divisi II-V (43 baris, 38 kode) | 113.232,7 | 113.232,7 | Rp 0,00 | ≤ Rp 1 | lolos |
| T-121c | Total RAB rumus Excel vs Python | | | -0,0000 % | ≤ 0,01 % | lolos |

## 5. Catatan

- T-121a/b membandingkan RAB rinci dengan perkiraan konsep 3.8. Perkiraan 3.8 menambahkan nonstandar dan fondasi dalam di atas biaya standar HSBGN (Permen PUPR 22/2018), sedangkan RAB menghitung volume nyata dari model; selisih di luar batas dijelaskan di Ringkasan Tahap 8.
- MEP memakai persentase 3.8, bukan volume dari model MEP (model MEP 7.2 hanya koordinasi); MEP rinci menunggu konsultan MEP.
- Harga [Asumsi: Jambi 2026], belum survei harga SE 47/2026 Lampiran I.
