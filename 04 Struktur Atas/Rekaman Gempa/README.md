# Rekaman gempa untuk 4.1

> Disusun AI atas permintaan Defsa (20 Nov 2026). **Keputusan Defsa 20 Nov 2026: memakai rekaman sintetis** karena
> PEER NGA-West2 hanya menerima email kampus/perusahaan dan semua akun lama dinonaktifkan 2 Juli 2026.
> Status rekaman sintetis: disetujui Defsa 20 Nov 2026 bersama langkah 4.1 (opsi a).

## Rekaman yang dipakai: 7 rekaman sintetis (`sintetis/`)

- Dibangkitkan `skrip/tahap4_rekaman.py`: derau Gauss × selubung Saragoni-Hart (durasi kuat D5-95 19-23 s, [Asumsi]
  untuk Mw 7,0), pencocokan spektrum di domain frekuensi (20 iterasi), saringan lolos-tinggi 0,08-0,16 Hz, dan koreksi
  garis dasar. Hasilnya `SIN-01.csv` s.d. `SIN-07.csv` (dt 0,01 s, 40 s, satuan g).
- Sah menurut Pasal 6.10.1.1, yang menyebut "rekaman atau simulasi riwayat waktu". Bentuk rekaman sintetis kurang
  realistis dibanding rekaman nyata; rekaman PEER dapat menggantikannya kelak tanpa mengubah alur 4.1.
- Kecocokan pada T 0,1-3,0 s: tiap rekaman 0,92-1,16 × target, rata-rata 7 rekaman 0,985-1,032 × target. PGA
  0,125-0,155 g (rata 0,137 g) terhadap PGA batuan 0,9 × 0,164 = 0,148 g. Perpindahan akhir ≤ 9 cm.
- Spektrum dihitung dua cara (Nigam-Jennings vs Newmark), selisih ≤ 2,3 % (VERIFIKASI T-65).
- Ringkasan: `sintetis/Ringkasan Rekaman Sintetis.csv`; grafik pratinjau: `sintetis/Spektrum Rekaman Sintetis.png`
  (gambar resmi GS-01 dibuat di CADCraft).

## Syarat dari SNI 1726:2019

- Pasal 6.10.1.1 (hal. 40):
  - spektrum MCER batuan dasar dibuat dengan anggapan **kelas situs SB**;
  - diperlukan **minimal 5 rekaman** gerak tanah horizontal;
  - rekaman berasal dari gempa yang magnitudo dan jarak sumbernya mengontrol MCER;
  - rekaman diskalakan sehingga spektrum rata-ratanya mendekati MCER batuan pada rentang periode penting.
- Tabel 6 dan Tabel 7 (hal. 34-35): kelas situs SB memakai Fa 0,9 dan Fv 0,8.

## Spektrum target

Berkas `Target MCER Batuan SB.csv` dipakai sebagai *user-defined spectrum* di PEER, 5 % redaman.

| Besaran | Nilai |
|---|---|
| Ss, S1 | 0,334 g; 0,264 g (Desain Spektra PUPR, langkah 2.6) |
| SMS = 0,9 × Ss | 0,301 g |
| SM1 = 0,8 × S1 | 0,211 g |
| T0, Ts | 0,141 s; 0,703 s |

Bentuk spektrum mengikuti Pasal 6.4 pada taraf MCER (tidak dikali 2/3).

## Cara unduh rekaman nyata (bila kelak ada akun PEER/ESM)

**PEER NGA-West2** (https://ngawest2.berkeley.edu/, akun gratis):

1. Pilih *Spectrum Model: User Defined*, lalu tempel isi CSV.
2. Isi kriteria pencarian:
   - **Magnitude** 6,5-7,5. Deagregasi PuSGeN 2017 untuk Kota Jambi ±6,6-7,2; dipakai Mw 7,0 di 2.6.
   - **Vs30** 760-1.500 m/s, karena rekaman harus di batuan (SB).
   - **Rrup**: dibuat lebar dulu, misalnya 30-200 km. Jarak dominan dibaca AI dari peta deagregasi
     (`acuan/pustaka/PUPR-PuSGeN-...`, berupa gambar) di awal 4.1.
   - **Pulse-like**: tidak. Tapak bukan *near-fault*.
3. Atur penskalaan: rentang periode 0,1-3,0 s (meliputi periode gedung ±0,5-0,8 s dan periode situs), faktor skala
   0,5-4.
4. Ambil **7 rekaman** (lebih dari minimum 5) dari **gempa yang berbeda**, paling banyak 2 per kejadian.
5. Unduh file AT2 dan `_SearchResults.csv`.

**Alternatif ESM** (https://esm-db.eu/): kriteria sama. Pilih rekaman kelas situs A atau EC8.

## Tempat menyimpan

Simpan rekaman mentah dan `_SearchResults.csv` ke `04 Struktur Atas/Rekaman Gempa/mentah/`. Folder ini tidak di-commit
(lihat `.gitignore`) karena data PEER/ESM punya syarat pemakaiannya sendiri; yang di-commit hanya daftar rekaman dan
faktor skalanya. Setelah selesai, beri tahu AI untuk memulai 4.1.
