# Ringkasan Tahap 3: desain konsep

> DATA SIMULASI untuk studi kasus portofolio. **Disusun AI atas permintaan Defsa (19 Nov 2026).** Seluruh langkah
> 3.1-3.11 **disetujui Defsa 19 Nov 2026**; Tahap 3 selesai. Kunci jawaban Tahap 3 tidak dibuka. Data owner dan kejadian rapat dibangkitkan sesi skenario
> tersegel (`Data Owner/`). Cek silang ada di `VERIFIKASI.md` (T-34 s.d. T-51).

## Alur alat

- **Model:** BIMCraft. Template 3.1, model massa dan ruang 3.4 (`model/RSTB-ARS-T3-Massa`), struktur pra-dimensi 3.6, dan
  struktur LOD 200 3.9 (`model/RSTB-STR-T3-LOD200`, IFC4 divalidasi IfcOpenShell).
- **Gambar:** CADCraft dengan satu kop `KOP_A3`, GK-01 s.d. GK-10. GK-09 (denah) dan GK-10 (potongan) memakai geometri
  yang diekspor dari model BIMCraft (DXF di `Gambar/BIM/`), lalu teks, as grid, ukuran, dan elevasi ditulis asli di
  CADCraft.
- **Excel dan Word:** mengikuti `FORMAT LAPORAN DAN EXCEL.md`. Rumus Excel dihitung ulang di Excel lalu dicocokkan
  dengan Python.

## Keputusan desain konsep

| No | Butir | Keputusan | Dasar | Berkas |
|---|---|---|---|---|
| 1 | BEP | LOD 200/300/350 per tahap, datum BM-1 +10,000, IFC4 | Permen PUPR 22/2018 hal. 201 | `3.1 BEP.docx` |
| 2 | Tapak | Lahan perencanaan 10.766 m², tapak maks 5.383 m², KLB maks 25.838 m²; ruang sempadan tidak diurug | PKKPR persyaratan 2, surat sempadan | `3.2 Kajian Tapak.xlsx`, GK-01 |
| 3 | Peil | Q50 terkoreksi +11,85 (bukan +11,20); lantai dan utilitas +12,85, halaman +12,05 | Gumbel dua cara, banjir 2003 +11,65 | `3.3 Peil dan Urugan.xlsx`, GK-02 |
| 4 | Urugan | 30-38 ribu m³ padat, bertahap ±1 m dengan PVD segitiga 1,2 m (±5 bulan per tahap) | Penurunan 2.8, FHWA Pers. 7-11 | `3.3`, GK-02 |
| 5 | Program | 150 TT, luas 19.328 m² (gedung utama 14.976 + gedung utilitas/parkir 4.352) | PMK 40/2022, Permenkes 6/2026 | `3.4`, GK-03, GK-04 |
| 6 | Parkir | Basement ditolak (FK blow-in 0,97-1,14 < 1,25; uplift). Opsi C: gedung utilitas + parkir 4 lantai, 129 mobil, 357 motor | SNI 8460:2017 Pasal 10.3.6.7.2 | `3.5`, GK-05 |
| 7 | Struktur | Kategori IV, KDS D (SDS 0,482, SD1 0,524 sementara). Sistem ganda, grid 8 m; helipad AW139 | SNI 1726:2019, SNI 2847, SNI 1727 | `3.6`, GK-06 |
| 8 | Pondasi | Tiang bor Ø800 ke U7 ±38 m, 373 tiang, izin 911 kN per tiang | FHWA NHI-06-089, SNI 8460:2017 | `3.7`, GK-07 |
| 9 | Biaya | ±Rp 451 M = 2,69 × pagu Rp 168 M (rentang 360-551 M); rekayasa nilai V1-V7 hemat ±Rp 72 M | Permen PUPR 22/2018 Pasal 21, 29, 31 (pedoman) | `3.8`, GK-08 |
| 10 | BIM | Model struktur LOD 200 lolos validasi; volume cocok dengan 3.6 dalam 0-7,6 % | IfcOpenShell | `3.9`, model |
| 11 | Rapat konsep | Pembiayaan bertahap: target akhir 150 TT, tahap 1 ±Rp 230 M menunggu bank; V3, V4, V6, V7 disetujui, V1/V2/V5 bersyarat | Notulen 5 Apr 2027 [Simulasi AI] | `3.10`, `10 Laporan/Notulen Rapat Desain Konsep (simulasi).docx` |

## Temuan penting

1. Banjir rencana penyedia (+11,20) terlalu rendah. Seri muka air harus dikoreksi dulu (nol papan pindah 3,15 → 3,50;
   tahun 1999 tidak lengkap). Hasilnya Q50 +11,85, sama dengan nilai Balai.
2. KDB owner (6.300 m²) dihitung dari persil. PKKPR menghitungnya dari lahan perencanaan.
3. Tanah gratis 22 ribu m³ tidak cukup dan tidak dapat dipadatkan dalam 6 minggu di atas lempung lunak.
4. Basement tidak aman tanpa dinding potong ±22 m atau sumur pelepas, dan merugikan gudang bercerucuk.
5. Fondasi Rp 90 M (54 % pagu) adalah akibat tapak, bukan pilihan desain. Struktur sistem ganda masih di dalam porsi
   standar.
6. Pagu disusun untuk 12.000 m² × 14 juta/m². Program 150 TT realistis butuh 19.328 m². Rekayasa nilai tidak cukup
   menutup selisihnya.

## Akibat untuk tahap berikutnya (tindak lanjut rapat konsep)

- **Laporan antara:**
  - paket tahap 1 ±Rp 230 M (fungsi dan TT yang beroperasi lebih dulu);
  - rincian kenaikan luas;
  - kajian stabilitas tebing dan saluran pembuang;
  - ramp beratap di gambar konsep;
  - tangki tanam dan penataan atap bersama konsultan MEP;
  - kajian parkir permukaan sementara (V5);
  - paket awal urugan + PVD.
- **Sebelum 30 April 2027:** lokasi timbunan sementara dan uji mutu tanah gratis; rincian uji tiang awal.
- **Sebelum 20 April 2027:** tanggapan teknis atas klaim retak gudang timur (catatan uji pompa Des 2026).
- **Tahap 4:** spektrum respons spesifik-situs (kelas SF) dan beban MEP rinci.
- **Tahap 6:** uji tiang, gesekan negatif, penyebaran lateral, dan stabilitas tebing.
- **Tahap 8:** harga satuan dari survei (SE 47/2026) dan HSBGN Kota Jambi.

## Acuan yang masih kurang

- Permen PUPR 28/2015 (sempadan)
- Perda RTRW/RDTR Kota Jambi
- Aturan aksesibilitas (kemiringan ramp)
- Aturan helipad (ukuran landasan)
- SK HSBGN Kota Jambi 2026
- Keputusan Menteri tentang koefisien jumlah lantai
- UU HPP (tarif PPN)

Angka yang bergantung pada acuan ini diberi label [Asumsi] di berkasnya.
