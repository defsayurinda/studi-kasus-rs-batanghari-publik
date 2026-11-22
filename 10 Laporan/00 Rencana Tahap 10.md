# Rencana Tahap 10: Laporan Akhir dan halaman portofolio

Status: **disetujui Defsa 23 Nov 2026** (dikerjakan atas delegasi, Mode cepat; Laporan Akhir dan audit ditelaah Defsa). DATA SIMULASI untuk studi kasus portofolio.

## 1. Keluaran

| No | Keluaran | Berkas |
|---|---|---|
| 10.1 | Laporan Akhir Word + PDF (format `FORMAT LAPORAN DAN EXCEL.md`, `format_dokumen.Laporan`) | `skrip/laporan_akhir.py`, `10 Laporan/Laporan Akhir.docx/.pdf` |
| 10.2 | Draf halaman portofolio (belum terbit) | `10 Laporan/Halaman Portofolio.md` |
| 10.3 | Uji kecil berkas baru | `tests/test_laporan_akhir.py` |

## 2. Struktur Laporan Akhir

Sampul, Ringkasan Eksekutif, daftar isi/tabel/gambar, lalu:

| Bab | Isi | Sumber angka |
|---|---|---|
| I Pendahuluan | dasar KAK, lingkup, alur tahap 0-10, cara kerja openBIM | `00 RANCANGAN.md` |
| II Data dan Geoteknik | stratigrafi U1-U8, air tanah, parameter, kelas situs SF, likuifaksi, kimia, kesalahan data penyedia | Ringkasan Tahap 2 |
| III Desain Konsep | peil, urugan + PVD, program 19.328 m², parkir tanpa basement, biaya konsep | Ringkasan Tahap 3 |
| IV Struktur Atas dan Tengah | spektrum spesifik-situs, analisis, pelat/balok/kolom/dinding geser, tangki, MRI, sloof, pit lift | Ringkasan Tahap 4-5 |
| V Struktur Bawah | tiang bor Ø800 (321 tiang, 84 cap), gesekan negatif, Cap E, tebing P-2, uji tiang | Ringkasan Tahap 6, 7.3 |
| VI BIM dan DED | model federasi, clash, DED 64 lembar, RKS, render | Ringkasan Tahap 7 |
| VII RAB dan Rekayasa Nilai | 6 divisi + SMKK + PPN Rp 286,22 miliar, VE-1..VE-5 + usul VE-6 | Ringkasan Tahap 8, 9 (T-125) |
| VIII Jadwal | 98 minggu, lintasan kritis, Gantt + kurva S | Ringkasan Tahap 9 |
| IX Keputusan Owner, Butir Terbuka, Kesimpulan | pagu, O-x / O8-x / O9-x / O10-x, catatan penyusunan | Ringkasan 7-9 |
| Lampiran A | daftar dokumen keluaran per tahap | Ringkasan 2-9 |

Gambar: R-01 (render), `9 Gantt dan Kurva S.png`. Tabel: angka kunci per tahap, rekap RAB, VE, cek silang gagal, butir terbuka.

## 3. Keputusan (atas delegasi Defsa)

| No | Keputusan |
|---|---|
| K10-1 | Angka dikutip dari Ringkasan Tahap 2-9, tidak dihitung ulang (Mode cepat); satu Laporan Akhir menggantikan laporan terpisah |
| K10-2 | Jumlah tiang akhir 321 / 84 cap (model STR 7.3, RAB 8a), bukan 319 / 83 (6.9) |
| K10-3 | VE-6 tower crane (T-125) disajikan sebagai usul, RAB 8b tidak diubah |
| K10-4 | Rekomendasi pagu: Rp ±275 miliar dengan VE-1..VE-5 (±Rp 273 miliar bila VE-6 diterima) atau bertahap opsi 3.8; keputusan pada owner |
| K10-5 | Render memakai versi pertama R-01..R-08 (`main`); render v2 Colab menyusul (O-1) |
| K10-6 | Halaman portofolio berupa draf md di repo ini; terbit ke `situs/` setelah Defsa menelaah dan pindai privasi |
| K10-7 | Tanggal laporan simulasi Agustus 2027 (sesudah Laporan Antara April 2027) |
| K10-8 | O10-1 ditutup: mulai konstruksi digeser dari 4 Jan 2027 ke 3 Jan 2028 (sesudah Laporan Akhir + tender); durasi, bobot, dan cek silang Tahap 9 tidak berubah; selesai 19 Nov 2029 |
| K10-9 | Bab VIII lanskap agar Gantt terbaca (lebar 24 cm) |

## 4. Cek silang

- T-126: angka kunci di Laporan Akhir = ringkasan tahap (uji `test_laporan_akhir.py` mencari angka kunci di teks Word).
- T-127: total RAB dan durasi jadwal di Ringkasan Eksekutif = Bab VII/VIII.
