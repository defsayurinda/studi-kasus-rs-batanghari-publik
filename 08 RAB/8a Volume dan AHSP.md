# 8a Volume dan AHSP

Status: disetujui Defsa 23 Nov 2026. Data simulasi studi kasus. Harga [Asumsi: Jambi 2026], belum survei harga (SE 47/2026 Lampiran I).

Skrip `skrip/tahap8_volume.py`, Excel `08 RAB/8a Volume dan AHSP.xlsx` (6 lembar). Keputusan K8-1..K8-7: `08 RAB/00 Rencana Tahap 8.md`.

## 1. Volume struktur (IFC STR 7.3)

| Kelompok | Unsur | Beton Qto (m³) | Beton bersih (m³) | Bekisting (m²) | Besi/baja (kg) |
|---|---:|---:|---:|---:|---:|
| Balok | 496 | 840,0 | 507,4 | 4.177,1 | 91.336 |
| Dinding geser inti | 152 | 1.052,4 | 1.052,4 | 6.013,8 | 147.337 |
| Kolom | 370 | 704,9 | 666,0 | 3.690,2 | 133.210 |
| Kolom baja HEB 200 | 36 | 0,2 | 0,0 | 0,0 | 1.324 |
| Pelat lantai | 8 | 2.620,9 | 2.620,9 | 11.783,6 | 262.087 |
| Pelat lantai 1 | 1 | 679,0 | 679,0 | 0,0 | 74.694 |
| Pile cap | 84 | 2.171,9 | 2.171,9 | 1.496,4 | 217.194 |
| Pit lift | 15 | 49,2 | 49,2 | 201,4 | 5.906 |
| Sloof dan balok pondasi | 124 | 346,9 | 346,9 | 1.734,4 | 52.032 |
| Tangga | 100 | 141,6 | 141,6 | 222,2 | 14.164 |
| Tiang bor Ø800 | 321 | 6.224,5 | 6.200,3 | 0,0 | 883.633 |

Beton bersih 14.435,7 m³, besi 1.881,6 t (rata-rata 130,3 kg/m³).

## 2. Volume arsitektur (IFC ARS 7.1)

| Kode | Uraian | Sat. | Volume |
|---|---|---|---:|
| R-PF | Plafon gipsum 12 mm + rangka hollow | m² | 9.077,6 |
| R-P2 | Pintu ganda 1200-1500 × 2100 + kusen + kunci | bh | 123,0 |
| R-P3 | Pintu lift 1400 × 2400 (bagian paket lift) | bh | 12,0 |
| R-P1 | Pintu tunggal 900 × 2100 + kusen + kunci | bh | 89,0 |
| R-RL | Railing 1000 mm | bh | 10,0 |
| R-LG | Lantai granit/homogeneous tile 60 × 60 | m² | 3.979,2 |
| R-LE | Lantai epoksi (parkir, servis, utilitas) | m² | 6.486,4 |
| R-LV | Lantai vinil homogen RS (rawat, intensif, OK, klinik) | m² | 4.464,2 |
| R-OV | Overstek fasad | m² | 131,8 |
| R-RT | Lansekap rumput dan tanah humus | m² | 7.829,9 |
| R-AS | Perkerasan aspal jalan dan parkir luar | m² | 2.060,2 |
| R-PV | Paving blok | m² | 118,8 |
| R-PB | Perkerasan beton | m² | 70,2 |
| R-KN | Kanopi drop-off | m² | 326,5 |
| R-TA | Taman atap (kedap air + media tanam) | m² | 765,6 |
| R-HP | Dek helipad (tahap 2, struktur disiapkan) | m² | 1.108,9 |
| A7b | Dinding bata ringan 100 mm | m² | 4.431,8 |
| A7a | Dinding bata ringan 150 mm | m² | 11.896,7 |
| R-DL | Lapis dinding inti 50 mm (finishing) | m² | 2.516,0 |
| A10 | Fasad panel komposit aluminium + rangka | m² | 4.591,4 |
| A9 | Fasad kaca (curtain wall unitized) | m² | 2.885,0 |
| R-PG | Pagar keliling | m² | 1.072,4 |
| R-NM | Papan nama | m² | 10,1 |
| R-BK | Bak tanaman beton | m³ | 7,6 |
| R-TK | Dinding panel tangki air | m² | 112,0 |
| A8 | Plesteran + acian dinding bata (2 sisi) | m² | 32.657,0 |
| R-CT | Cat dinding interior (2 sisi bata + lapis inti) | m² | 35.173,0 |

Tidak dihitung: RSTB Huruf A 6; RSTB Huruf B 1; RSTB Huruf E 1; RSTB Huruf G 1; RSTB Huruf H 2; RSTB Huruf I 3; RSTB Huruf K 1; RSTB Huruf M 1; RSTB Huruf N 2; RSTB Huruf P 1; RSTB Huruf R 2; RSTB Huruf S 1; RSTB Huruf T 3; RSTB Huruf U 1; RSTB Lampu Jalan 16; RSTB Logo H 3; RSTB Mobil 59; RSTB Motor 76; RSTB Pohon 41; TP-Air 1; TP-AtapTangki 4; TP-Lereng 7; TP-MarkaKuning 1; TP-MarkaPutih 3.

## 3. AHSP pekerjaan utama

| Kode | Pekerjaan | Sat. | Biaya langsung (Rp) | HSP + BTL 12 % (Rp) |
|---|---|---|---:|---:|
| A1 | Tiang bor Ø800 fc' 35 (bor, cor tremie, tanpa besi) | m' | 1.282.526 | 1.436.429 |
| A2 | Beton siap pakai fc' 35 MPa dicor dengan pompa | m³ | 1.495.950 | 1.675.464 |
| A3 | Beton siap pakai fc' 30 MPa dicor dengan pompa | m³ | 1.404.150 | 1.572.648 |
| A4 | Pembesian BjTS 420B (potong, bengkok, pasang) | kg | 16.778 | 18.792 |
| A5 | Bekisting kolom, dinding, sisi cap/sloof (multipleks, pakai 3 kali) | m² | 203.594 | 228.026 |
| A6 | Bekisting pelat dan balok + perancah (multipleks, pakai 3 kali) | m² | 219.714 | 246.080 |
| A7a | Dinding bata ringan 150 mm | m² | 193.800 | 217.056 |
| A7b | Dinding bata ringan 100 mm | m² | 149.550 | 167.496 |
| A8 | Plesteran 1:4 tebal 15 mm + acian (satu sisi) | m² | 136.274 | 152.627 |
| A9 | Fasad kaca curtain wall unitized (pasok + pasang) | m² | 2.880.250 | 3.225.880 |
| A10 | Fasad panel komposit aluminium + rangka hollow | m² | 923.700 | 1.034.544 |
| A11 | Dewatering sump terbuka (sewa pompa + operator) | pompa-hari | 895.000 | 1.002.400 |

## 4. Item pekerjaan dan Pareto (T-120)

| Kode | Pekerjaan | Volume | Jumlah (Rp juta) | Porsi (%) |
|---|---|---:|---:|---:|
| A4 | Pembesian BjTS 420B (rasio kg/m³ + tiang 6.7) | 1.881.591,4 kg | 35.358,7 | 31,23 |
| A1 | Tiang bor Ø800 fc' 35 | 12.383,2 m' | 17.787,6 | 15,71 |
| A9 | Fasad kaca (curtain wall unitized) | 2.885,0 m² | 9.306,8 | 8,22 |
| A2 | Beton fc' 35 (cap, sloof, kolom, dinding, pelat LT1, pit) | 4.965,5 m³ | 8.319,6 | 7,35 |
| A3 | Beton fc' 30 (balok, pelat, tangga) | 3.269,9 m³ | 5.142,4 | 4,54 |
| A8 | Plesteran + acian dinding bata (2 sisi) | 32.657,0 m² | 4.984,3 | 4,40 |
| A10 | Fasad panel komposit aluminium + rangka | 4.591,4 m² | 4.750,0 | 4,19 |
| A6 | Bekisting pelat dan balok + perancah | 16.251,0 m² | 3.999,0 | 3,53 |
| A5 | Bekisting vertikal | 13.068,1 m² | 2.979,9 | 2,63 |
| R-HP | Dek helipad (tahap 2, struktur disiapkan) | 1.108,9 m² | 2.883,1 | 2,55 |
| A7a | Dinding bata ringan 150 mm | 11.896,7 m² | 2.582,2 | 2,28 |
| R-LV | Lantai vinil homogen RS (rawat, intensif, OK, klinik) | 4.464,2 m² | 2.142,8 | 1,89 |
| R-PF | Plafon gipsum 12 mm + rangka hollow | 9.077,6 m² | 1.770,1 | 1,56 |
| R-LE | Lantai epoksi (parkir, servis, utilitas) | 6.486,4 m² | 1.686,5 | 1,49 |
| R-CT | Cat dinding interior (2 sisi bata + lapis inti) | 35.173,0 m² | 1.477,3 | 1,30 |

Total 38 item: Rp 113,23 miliar (biaya langsung + BTL, tanpa MEP, SMKK, PPN). 12 item AHSP rinci = 85,1 % biaya (batas ≥ 75 %): lolos.

## 5. Cek silang (T-119)

| Kode | Besaran | IFC 7.3 | Pembanding | Selisih | Batas | Hasil |
|---|---|---:|---:|---:|---:|---|
| T-119a | Tiang bor (m³) | 6.224,5 | 6.214,9 | 0,15 % | 1 % | lolos |
| T-119a | Pile cap (m³) | 2.171,9 | 2.172,0 | -0,00 % | 1 % | lolos |
| T-119b | Kolom (m³) | 704,9 | 677,8 | 4,00 % | 5 % | lolos |
| T-119b | Balok (m³) | 840,0 | 860,6 | -2,39 % | 5 % | lolos |
| T-119b | Pelat lantai (m³) | 2.620,9 | 2.543,3 | 3,05 % | 5 % | lolos |
| T-119b | Dinding geser inti (m³) | 1.052,4 | 1.009,8 | 4,22 % | 5 % | lolos |
| T-119b | Tangga (m³) | 141,6 | 141,6 | 0,03 % | 5 % | lolos |

## 6. Catatan

- Koefisien AHSP berlabel [Asumsi]: lampiran AHSP Permen PUPR 8/2023 di `acuan/` berupa pindaian (K8-6).
- Harga dasar [Asumsi: Jambi 2026]; survei harga belum dilakukan.
- T-119 memakai Qto NetVolume (lubang shaft dikurangi) karena T-84 dihitung dari geometri IFC yang juga mengurangi lubang. Perbandingan pertama dengan GrossVolume gagal untuk pelat (+6,7 %) dan dinding inti (+8,1 %); selisih yang tersisa (kolom +4,0 %, pelat +3,1 %, dinding +4,2 %, balok -2,4 %) sejalan dengan perubahan Tahap 5 (tangki, kolom 800, pelat 350) dan 7.3 (K-01 6 balok dihapus, LB-1, rel chiller).
- Besi tiang 6.7 (16 D25 + spiral D13 40/80) ±142 kg/m³ dan 31 % biaya 8a: periksa susunan spiral pada VE 8b.
- Biaya 8a Rp 113 miliar tanpa MEP; pagu owner 12.000 m² × Rp 14 juta = Rp 168 miliar (TOR, `tahap3_biaya.PAGU_*`). Dengan MEP RS (±30-40 % [Asumsi]) total berisiko melewati pagu: dibahas di VE 8b.
- Langkah berikutnya: 8b RAB (volume × HSP), SMKK, MEP, PPN, value engineering.
