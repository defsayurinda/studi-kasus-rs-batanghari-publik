# Ringkasan Tahap 5: struktur tengah (pelat LT1, sloof, pit lift, penerusan ke pondasi)

Status: **disetujui Defsa 21 Nov 2026** (langkah 5.0-5.8). DATA SIMULASI untuk studi kasus portofolio. Bukan data
proyek nyata. Tidak untuk konstruksi.

Rencana tahap: `00 Rencana Tahap 5.md` (disetujui 20 Nov 2026). Rincian tiap langkah ada di md per langkah; angka di
bawah ini dikutip dari sana dan dari `VERIFIKASI.md`.

## 1. Keputusan Defsa per langkah

| Langkah | Keputusan (tanggal) |
|---|---|
| 5.0 Telaah data | Temuan dan permintaan data disetujui (20 Nov 2026) |
| 5.1 Letak tangki | Opsi B: tangki 8 × 8 × 3,5 m di bay as 7-8 / F-G, pelat dua arah 350 (21 Nov 2026) |
| 5.2 MRI | Opsi 2: jalur ambulans dipindah ke x 92,5-98,5, MRI tetap; baja tahan karat A955M di zona 2 × 2 m pelat 9-10/D-E; P4 (76 motor) dicarikan tempat di Tahap 7; R-06 di atas pegas (21 Nov 2026) |
| 5.3 Pelat LT1 | fc' 35 MPa (paparan S2), selimut bawah 50 mm, panel MRI monolit 250, beban arsip 7,18 kPa terbatas pada zonanya (21 Nov 2026) |
| 5.4 Sloof | SL-1 400 × 900 (10 D29 / 8 D25), SL-2 dan SL-3 400 × 800; δ desain 16 mm; T tidak masuk kombinasi gempa; kepala tiang sendi sampai Tahap 6 (21 Nov 2026) |
| 5.5 Pit lift | Opsi A: pelat dasar L-1..4 0,45 m (FK 1,11), L-5..6 dan L-7 0,40; L-7 ditumpu 2 balok penggantung 400 × 800 (5 D29) ke sloof; kedap aditif kristalin + waterstop (21 Nov 2026) |
| 5.6 Reaksi ke pondasi | Reaksi dengan ΔP sloof, amplop K1 ∪ K2, kasus E; pile cap inti 1.200 mm; tumpang tributari inti dipertahankan; SL-1 as 6 di dalam inti lift dihapus (21 Nov 2026) |
| 5.6a Kolom tangki | 800 seragam: LT2 20 D22 D13-125, LT3 32 D29 D13-150, lo 800 (21 Nov 2026) |
| 5.7 Model BIMCraft | Model LOD 300 disetujui, termasuk balok penggantung L-7 digeser 0,5 m ke muka luar dinding pit (21 Nov 2026) |
| 5.8 Gambar | GS-22 s.d. GS-26 disetujui; tiga catatan kosmetik diperbaiki (21 Nov 2026) |

## 2. Angka kunci

| Unsur | Angka | Sumber |
|---|---|---|
| Tangki opsi B | balok x 68 450 × 800 (A 600 × 1.200); kolom 800; beton B 78,1 m³, besi 15,6 t; Δ biaya dengan BTL + PPN -291,9 juta; tinggi bersih LT2 3,70 m | 5.1, 5.6a |
| MRI | jarak isocenter ke tepi lajur lama 7,5 m < 12,0 m; fn panel 11,2 Hz (5.2) / 11,67 Hz (5.3, monolit 250); baja tahan karat 144,6 kg | 5.2, 5.3 |
| Pelat LT1 PL-1 | h 250, D13-200 atas dan bawah; hmin 177 mm; pons kaki magnet 0,030, roda 0,052 | 5.3 |
| Sloof | Ftie 235 kN (rasio 0,09, tidak menentukan); M penurunan beda 249 kNm; SL-1 400 × 800 gagal (ρ 2,88 % > 2,5 %), 400 × 900 lolos | 5.4 |
| Pit lift L-1..4 | U 565 kN / W 602 kN pada Q100; t min 0,439 m, dipakai 0,45 (FK 1,11); pelat atas D13-175, bawah D13-100 | 5.5 |
| Reaksi ke pondasi | 77 titik; Pmax layan kolom 4/B 5.825 kN; Pu maks inti lift 13.006 kN (Mux 92.865, Muy 125.471 kNm); tidak ada tarik (Pu min 599 kN); Σ tambahan struktur tengah 58.040,1 kN; ΔP sloof maks 37,4 kN | 5.6 |
| Kolom tangki 800 | LT3 P-M 0,99, ΣMnc/ΣMnb 1,27, geser joint 0,98; Pu maks 3.795 kN; stek ke cap 1.200: ldh 375, ld 919 mm (tersedia 1.093 / 1.125) | 5.6a |
| Model LOD 300 | 122 sloof, 70 stek kolom + 28 stek dinding inti, 5.244 batang besi kolom tangki (10,5 t); Pset kurang 0 dari 1.306; clash dasar 0 | 5.7 |
| Gambar | 5 lembar ber-kop KOP_A3, cad_cek 0 pasangan | 5.8 |

## 3. Cek silang (VERIFIKASI.md)

| No | Langkah | Yang dicek | Selisih | Toleransi | Hasil |
|---|---|---|---|---|---|
| T-89 | 5.0 | Jarak MRI ke jalur (rencana: koordinat skrip vs ukur DWG) | tidak dicatat terpisah; jarak 7,500 m dicek silang di T-91 (a) | - | Lihat T-91 |
| T-90 | 5.1 | Beban tangki ke kolom, Mu balok as 8, reaksi balok anak | 0,00 %; -7,9 / +3,3 %; 0,00 % | 0,5 %; 15 %; 10 % | Lolos |
| T-91 | 5.2 | Jarak isocenter, fn pelat, berat besi tahan karat | 0,00 %; -10,6 %; 0,00 % | 0,5 %; 15 %; 0,5 % | Lolos |
| T-92 | 5.3 | qu dan Mo, Mx beban titik, φVc pons, massa besi tahan karat | 0,00 %; 1,07 %; 0,00 %; 0,00 % | 0,5 %; 5 %; 0,5 %; 0,5 % | Lolos |
| T-93 | 5.4 | Ftie, momen ujung SL-1, momen penurunan beda, φMn SL-2 | 0,00 %; 0,13 %; 0,00 %; 0,00 % | 0,5 %; 5 %; 1 %; 2 % | Lolos |
| T-94 | 5.5 | Gaya angkat U, momen pelat, momen dinding, t min | 0,00 %; 3,47 %; 0,00 %; 0,00 % | 0,5 %; 5 %; 1 %; 0,5 % | Lolos |
| T-95 | 5.6 | Σ D, Σ geser dasar E, Σ tambahan, Excel = Python | 0,73 / 2,53 / 0,00 %; 0,00 %; 0,00 %; cocok | 5 %; 1 %; 0,5 %; 0,5 % | Lolos |
| T-96 | 5.6a | Mn kolom LT3, Mn balok x 68, Pu kolom (68;67), Excel = Python | 0,03 %; 0,00 %; 1,53 %; 0,12 % | 3 %; 1 %; 5 %; 0,5 % | Lolos |
| T-97 | 5.7 | Volume IFC vs rencana per kelompok | 0,00 % (pelat -0,40 %) | 5 % | Lolos |

Catatan: nomor T-89 dipakai rencana untuk jarak MRI di DWG, tetapi cek itu tidak dicatat sebagai baris tersendiri.
Jarak isocenter (7,500 m) sudah dicek dua cara di T-91 (a). T-96 (b) memakai rumus blok persegi yang sama dengan
`kl.momen_balok`, jadi bukan pembanding independen penuh.

## 4. Temuan dan bawaan untuk Tahap 6 (pondasi)

1. **Jarak tiang LOD 200 Tahap 3:** 30 pasang tiang Ø800 berjarak pusat < 2,0 m (terdekat 0,83 m) di sekitar inti.
   Cap inti dan cap kolom di sekitarnya digabung; jarak minimum tiang dicek ulang.
2. Reaksi per titik dari `5.6 Reaksi ke Pondasi.xlsx` lembar "Ringkasan Tahap 6" (77 titik, layan dan ultimit, kasus E,
   dengan ΔP sloof). Σ D inti tumpang 6,3 % (konservatif, tidak dikurangkan).
3. Pile cap inti 1.200 mm; kolom (52,35) dan (52,43) masuk pile cap inti; angkur sloof di inti: kait 90° turun ke cap,
   ldh 381 mm, cap minimum 488 mm.
4. Kepala tiang dianggap sendi (momen dasar kolom ke sloof); bila Tahap 6 memakai jepit, sloof dicek ulang.
5. Pit L-1..4 diangkurkan berat sendiri (opsi A); pengangkuran izin SNI 8460 pasal 10 belum ada di acuan.
6. Penurunan beda δ 16 mm [Asumsi: SNI 1726 Tabel 22] dibandingkan dengan hasil penurunan Tahap 6.
7. Serakan lateral dan penurunan pile cap: data belum ada (ditunggu dari Tahap 6).

Bawaan ke Tahap 7: tempat parkir P4 (76 motor), spesifikasi produk kedap di RKS, beban arsip terbatas zona, R-06 di
atas pegas, fasad sesuai arahan foto.

## 5. Acuan yang belum ada

Pedoman getaran lantai untuk MRI, ACI 440 (GFRP), kelas W2, SNI 8460 pasal 10 (pengangkuran), ACI 350 / EN 1992-3,
EN 81-20, data pabrikan pelindung MRI dan produk membran/aditif.

## 6. Daftar berkas

| Langkah | Berkas | Skrip | Uji |
|---|---|---|---|
| 5.0 | `5.0 Telaah Data Tahap 5.md/.xlsx`, `5.0 Gambar Plot Data Owner.pdf` (GS-21) | `tahap5_telaah.py`, `tahap5_gambar_plot.py` | `test_tahap5_telaah.py` |
| 5.1 | `5.1 Kajian Letak Tangki.md/.xlsx` | `tahap5_tangki.py` | `test_tahap5_tangki.py` |
| 5.2 | `5.2 Kajian MRI.md/.xlsx` | `tahap5_mri.py` | `test_tahap5_mri.py` |
| 5.3 | `5.3 Desain Pelat LT1.md/.xlsx` | `tahap5_pelat_lt1.py` | `test_tahap5_pelat_lt1.py` |
| 5.4 | `5.4 Desain Sloof.md/.xlsx` | `tahap5_sloof.py` | `test_tahap5_sloof.py` |
| 5.5 | `5.5 Desain Pit Lift.md/.xlsx` | `tahap5_pit_lift.py` | `test_tahap5_pit_lift.py` |
| 5.6 | `5.6 Reaksi ke Pondasi.md/.xlsx` | `tahap5_penerusan.py` | `test_tahap5_penerusan.py` |
| 5.6a | `5.6a Kolom Tangki Opsi B.md/.xlsx` | `tahap5_kolom_tangki.py` | `test_tahap5_kolom_tangki.py` |
| 5.7 | `5.7 Model BIMCraft.md`, `model/RSTB-STR-T5-LOD300.bimc/.ifc` (+ `-v0.11.bimc`), `Gambar/5.7 Model LOD 300 3D.png` | `tahap5_bim.py` | `test_tahap5_bim.py` |
| 5.8 | `5.8 Gambar Struktur Tengah.md/.pdf`, `Gambar/DWG/GS-22..GS-26` | `tahap5_gambar_ded.py` | `test_tahap5_gambar_ded.py` |
| 5.9 | `Ringkasan Tahap 5.md` (berkas ini) | - | - |
