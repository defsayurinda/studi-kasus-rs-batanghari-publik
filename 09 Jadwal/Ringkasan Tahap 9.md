# Ringkasan Tahap 9: Jadwal dan Kurva S (4D ringkas)

Status: **disetujui Defsa 23 Nov 2026** (dikerjakan atas delegasi, Mode cepat; ringkasan ditelaah Defsa). Data simulasi studi kasus.

## 1. Hasil

| Keluaran | Isi |
|---|---|
| `skrip/tahap9_jadwal.py` | 21 kegiatan, CPM maju-mundur (FS/SS + jeda), bobot dari `tahap8_rab.rekap()`, durasi tiang bor dari `tahap8_volume.koef_bor` |
| `9 Gantt dan Kurva S.png` / `.pdf` | satu Gantt (lintasan kritis merah) + kurva S kumulatif |
| `9 Jadwal dan Kurva S.xlsx` + `.md` | 4 lembar (Ringkasan, Kegiatan, Kurva S, Verifikasi dan Acuan); bobot, selesai, kurva S rumus hidup, dihitung Excel |
| `9 Jadwal.xml` | MSPDI untuk ProjectLibre (kalender standar 5 hari) |
| `tests/test_tahap9_jadwal.py` | 3 uji lolos |

- Mulai 3 Jan 2028 [Asumsi; semula 4 Jan 2027, digeser K10-8], **durasi 98 minggu (22,6 bulan)**, selesai 19 Nov 2029.
- Lintasan kritis: persiapan → pematangan lahan → tiang bor (20 minggu, SE 47/2026) → galian/cap → struktur LT1-LT2 → MEP instalasi kasar → MEP alat utama → uji fungsi dan serah terima. Struktur LT3-atap, arsitektur, fasad, lift, tapak punya float.
- Bobot terbesar: MEP 43,7 % (instalasi kasar 22,4; alat utama 14,9; lift 6,5), tiang bor 13,3 %, arsitektur dalam 10,9 %. Kurva S: 26 % di minggu 26 (pondasi selesai), 56 % di minggu 52, 100 % di minggu 98.

## 2. Keputusan (atas delegasi Defsa)

K9-1..K9-7 di `00 Rencana Tahap 9.md`: satuan minggu (6 hari kerja), bobot = biaya RAB sebelum PPN, tiang bor 2 rig × 8 jam (SE 47/2026 Lamp. II hal. 187-188), siklus struktur 5/4 minggu per lantai, MEP 60/40 [Asumsi], tower crane/manajemen/SMKK sebagai kegiatan ringkas.

## 3. Cek silang

| Kode | Hasil | Catatan |
|---|---|---|
| T-122a/b/c | lolos | Σ bobot 100 % dan kurva S akhir 100 % (Excel = Python), Σ biaya = RAB 8b I-VII (Rp 257,86 miliar) |
| T-123 | lolos (-25,2 %; ± 30 %) | tiang bor 20 minggu (SE) vs 26,8 minggu (1 tiang/rig/hari); risiko jadwal +7 minggu |
| T-124 | lolos (-5,8 %) | 22,6 bulan vs SMKK 24 bulan: cadangan ±1,4 bulan |
| T-125 | **gagal** (-44,9 %; ± 15 %) | tower crane dipakai 9,9 bulan vs sewa 18 bulan di RAB 8b |

T-125: sewa P5 RAB 8b (2 unit × 18 bulan) konservatif. Usul **VE-6**: sewa 2 × 11 bulan (termasuk pasang/bongkar ±1 bulan), hemat ±Rp 1,89 miliar sebelum PPN (±Rp 2,10 miliar dengan PPN). RAB 8b tidak diubah; dibawa ke Tahap 10 bersama VE-1..VE-5.

## 4. Butir terbuka

- O9-1: durasi selain tiang bor [Asumsi]; perlu metode pelaksanaan kontraktor (jumlah zona cor, bekisting sistem).
- O9-2: MEP di lintasan kritis karena RAB MEP masih persentase (O8-2); jadwal MEP rinci menunggu konsultan MEP.
- O9-3: ~~Excel belum dirender ke PDF~~ **ditutup 23 Nov 2026**: Excel 8a/8b/9 dirender lewat Excel, format lolos dengan catatan kecil (`10 Laporan/Audit Akhir.md` AU-09); tanpa simulasi 4D (Mode cepat).
- Langkah berikutnya: Tahap 10 Laporan Akhir + halaman portofolio.
