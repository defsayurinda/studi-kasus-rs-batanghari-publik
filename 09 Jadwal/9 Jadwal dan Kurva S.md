# Tahap 9: Jadwal dan Kurva S

Status: disetujui Defsa 23 Nov 2026. Data simulasi studi kasus. Durasi selain tiang bor [Asumsi: praktik gedung beton 6 lantai].

Mulai 03-01-2028 [Asumsi], durasi **98 minggu (22,6 bulan)**, selesai 19-11-2029. Bobot = biaya RAB 8b sebelum PPN (Rp 257,86 miliar).

| Kode | Kegiatan | Bobot (%) | Mulai (mgg) | Durasi (mgg) | Selesai (mgg) | Kritis | Sumber |
|---|---|---:|---:|---:|---:|:-:|---|
| PER | Persiapan: uitzet, pagar, mobilisasi alat | 0,62 | 0 | 6 | 6 | ya | [Asumsi] |
| LHN | Pematangan lahan (urugan, perkuatan tepi sungai) | 5,03 | 2 | 10 | 12 | ya | [Asumsi] |
| TB | Tiang bor Ø800 (321 tiang, 2 rig) | 13,34 | 6 | 20 | 26 | ya | SE 47/2026 Lamp. II hal. 187-188 |
| GAL | Galian, dewatering, pile cap, sloof, pelat LT1, pit lift | 5,43 | 14 | 14 | 28 | ya | [Asumsi] |
| STR1 | Struktur LT1 (kolom/dinding inti + pelat LT2) | 1,46 | 20 | 5 | 25 | ya | [Asumsi] siklus K9-4 |
| STR2 | Struktur LT2 (+ pelat LT3, atap podium) | 1,46 | 25 | 5 | 30 | ya | [Asumsi] siklus K9-4 |
| STR3 | Struktur LT3 (+ pelat LT4) | 1,46 | 30 | 5 | 35 |  | [Asumsi] siklus K9-4 |
| STR4 | Struktur LT4 (+ pelat LT5) | 1,46 | 35 | 4 | 39 |  | [Asumsi] siklus K9-4 |
| STR5 | Struktur LT5 (+ pelat LT6) | 1,46 | 39 | 4 | 43 |  | [Asumsi] siklus K9-4 |
| STR6 | Struktur LT6 (+ pelat atap) | 1,46 | 43 | 4 | 47 |  | [Asumsi] siklus K9-4 |
| STR7 | Struktur atap (ruang alat, tangki, dek helipad) | 1,46 | 47 | 4 | 51 |  | [Asumsi] siklus K9-4 |
| ARS | Arsitektur dalam: dinding, plester, lantai, plafon, pintu, cat | 10,93 | 35 | 40 | 75 |  | [Asumsi] |
| FAS | Fasad kaca dan panel komposit | 5,50 | 39 | 24 | 63 |  | [Asumsi] |
| MEP1 | MEP instalasi kasar (pipa, kabel, ducting, sprinkler) | 22,36 | 30 | 44 | 74 | ya | [Asumsi] K9-5 |
| MEP2 | MEP alat utama (chiller, genset, gas medis) dan finishing | 14,90 | 60 | 30 | 90 | ya | [Asumsi] K9-5 |
| LIF | Lift (pemasangan dan uji) | 6,46 | 51 | 26 | 77 |  | [Asumsi] |
| TPK | Tapak: jalan, parkir, drainase, taman, dermaga | 1,41 | 57 | 20 | 77 |  | [Asumsi] |
| UJI | Uji fungsi, commissioning, pembersihan, serah terima | 0,06 | 90 | 8 | 98 | ya | [Asumsi] |
| TC | Sewa tower crane 2 unit (struktur LT1 s.d. fasad) | 1,88 | 20 | 43 | 63 |  | K9-6 |
| MP | Manajemen lapangan: direksi keet, listrik/air kerja, dokumentasi | 0,75 | 0 | 98 | 98 |  | K9-6 |
| SMKK | Penerapan SMKK (9 komponen) | 1,07 | 0 | 98 | 98 |  | K9-6 |

Tiang bor: 321 tiang, 12.383 m', 1.902 jam alat (koef 0,1536 jam/m', SE 47/2026 Lamp. II hal. 187-188) / (2 rig × 8 jam × 6 hari) = 20 minggu.

## Kurva S (tiap 13 minggu)

| Minggu | Kumulatif (%) |
|---:|---:|
| 13 | 10,6 |
| 26 | 26,2 |
| 39 | 37,5 |
| 52 | 56,1 |
| 65 | 75,8 |
| 78 | 93,6 |
| 91 | 99,8 |
| 98 | 100,0 |

## Cek silang

| Kode | Besaran | Cara 1 | Cara 2 | Selisih | Hasil |
|---|---|---:|---:|---:|---|
| T-122a | Σ bobot kegiatan (%) | 100,00 | 100,00 | 0,0000 | lolos |
| T-122b | Σ biaya kegiatan vs jumlah RAB 8b I-VII (Rp) | 257.857.917.002 | 257.857.917.002 | 0,0000 | lolos |
| T-122c | Kumulatif kurva S minggu akhir (%) | 100,00 | 100,00 | 0,0000 | lolos |
| T-123 | Durasi tiang bor (minggu): SE 47/2026 vs 1 tiang/rig/hari | 20,00 | 26,75 | -25,2336 | lolos |
| T-124 | Durasi lintasan kritis (bulan) vs SMKK RAB 8b | 22,62 | 24,00 | -5,7692 | lolos |
| T-125 | Masa pakai tower crane (bulan) vs sewa P5 RAB 8b | 9,92 | 18,00 | -44,8718 | gagal |
| T-122a/c Excel | Σ bobot / kumulatif akhir / durasi (rumus dihitung Excel) | 100,0000 % / 100,0000 % / 98 mgg | 100 / 100 / 98 | | lolos |

Keluaran: `9 Jadwal dan Kurva S.xlsx`, `9 Gantt dan Kurva S.png/.pdf`, `9 Jadwal.xml` (ProjectLibre).
