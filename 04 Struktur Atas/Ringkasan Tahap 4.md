# Ringkasan Tahap 4: struktur atas

> DATA SIMULASI untuk studi kasus portofolio. **Disusun AI atas permintaan Defsa (20 Nov 2026), disetujui Defsa 20 Nov 2026.**
> Seluruh langkah 4.0-4.11 **disetujui Defsa 20 Nov 2026**; Tahap 4 selesai. Kunci jawaban Tahap 4 tidak dibuka. Data owner
> dan penyelidikan pelengkap dibangkitkan sesi skenario tersegel (`Data Owner/`, PR #24). Cek silang ada di
> `VERIFIKASI.md` (T-65 s.d. T-88, semua Lolos).

## Alur alat

- **Analisis:** pystrata (respons situs ekivalen linier) dan openseespy (kolom tanah 1D nonlinier, model 3D gedung);
  PyNite dan concreteproperties sebagai cek silang. Semua hitungan desain di skrip `skrip/tahap4_*.py` dengan Excel
  yang rumusnya dicocokkan dengan Python.
- **Model:** BIMCraft. LOD 300 dari ukuran desain 4.5-4.8 (`model/RSTB-STR-T4-LOD300.bimc/.ifc`), LOD 350 berbesi
  (`model/RSTB-STR-T4-LOD350.bimc`, 143.769 batang ±375 t, dibangun ulang `skrip/tahap4_besi.py`, tidak di git karena
  82 MB), fasad V3 (`model/RSTB-ARS-T4-Fasad-V3.bimc/.ifc`).
- **Gambar:** GS-01 dan GS-02 (4.1, 4.2); GS-03 s.d. GS-20 DED struktur atas dari model BIM (DXF diekspor BIMCraft,
  anotasi asli CADCraft, satu kop `KOP_A3`), `cad_cek` 0 pasangan, PDF `4.10 Gambar Struktur Atas DED.pdf`.

## Keputusan Tahap 4

| No | Butir | Keputusan | Dasar | Berkas |
|---|---|---|---|---|
| 1 | Data gempa | 7 rekaman sintetis `SIN-01..07` dicocokkan ke MCER batuan SB (0,985-1,032 × target) | SNI 1726 Pasal 6.10.1.1, T-65 | `Rekaman Gempa/` |
| 2 | Spektrum | Spesifik-situs opsi (a): SDS 0,386 (batas 80 % SE), SD1 0,459, KDS tetap D | SNI 1726 Pasal 6.10 | `4.1`, GS-01 |
| 3 | Evakuasi udara | Mulai tahap 2; atap tahap 1 di atas LT4 baja ringan sementara tanpa helipad | Keputusan M-4 | `4.0` |
| 4 | Beban | Berat seismik K2 159.156 kN (12,1 kPa), V 13.164 kN; K1 108.411 kN, V 8.967 kN; angin tidak menentukan | SNI 1727:2020, SNI 1726 Pasal 7.8 | `4.2`, GS-02 |
| 5 | Analisis | T1 0,684/0,592 s; simpangan maks 46 % batas 0,010 hsx; torsi 1b arah Y diterima dengan ρ 1,3 dan Ax s.d. 1,56 | SNI 1726 Pasal 7.3, 7.8.6, 7.12 | `4.3` |
| 6 | Pelat | 200 mm, D10-125 s.d. D10-200; pelat tangki 250 mm + balok anak; atap helipad D13-200 | SNI 2847 Pasal 8.10 | `4.5` |
| 7 | Balok | SRPMK 350 × 600; balok transfer tangki x 68 600 × 1.200 (tanpa kolom tambahan) | SNI 2847 Pasal 18.6 | `4.6` |
| 8 | Kolom | 750/650; kolom transfer tangki 950 × 950 (x 68) dan 800 × 800 (x 60/76) menerus LT1-LT3 | SNI 2847 Pasal 18.7, 18.8 | `4.7` |
| 9 | Dinding geser | 350 mm, fc' 35, tanpa elemen batas khusus (σ 6,86 < 7,0 MPa); asumsi pintu inti diterima | SNI 2847 Pasal 18.10 | `4.8` |
| 10 | Model dan shaft | SH-4 digeser ke x 60,6-63,0, y 43,6-46,0 (0 clash); void LT3 di bawah menara dihapus | Clash T-85 | `4.9` |
| 11 | Fasad | V3 (kaca + overstek 0,9 m U-S, terakota B-T), berat 6.028 kN < asumsi 4.2; elevasi overstek disesuaikan di Tahap 7 | SNI 1726 Pasal 13.3, SNI 2847 Pasal 17 | `4.10 Rincian Fasad V3.xlsx` |
| 12 | Balok tepi | Torsi keseimbangan terakota 31,0 kNm ditahan sengkang rapat D10-75/100 (opsi a) | SNI 2847 Pasal 22.7 | GS-13 |

## Temuan penting

1. **Data penyedia menyesatkan.** Lapisan Vs 167 m/s di 46-47 m adalah loncatan pemicu, batuan dasar 33 m tidak
   memenuhi Vs SB, dan f0 2,5 Hz adalah resonansi lempung U4. Masukan respons situs harus batuan SB di ±85 m.
2. **Spektrum spesifik-situs turun ±20 %** terhadap spektrum SE sementara, tetapi dibatasi 80 % SE; simpangan tetap
   dicek dengan SE.
3. **Ringkasan atap MEP memakai angka lama** (2.676 kN, bukan 1.748) dan tangki 210 m³ jatuh di tengah balok induk:
   akibatnya balok transfer 600 × 1.200 dan kolom transfer 950/800 yang harus diteruskan ke pondasi.
4. **Torsi tipe 1b** arah Y (1,48) tidak bisa dihilangkan tanpa mengubah denah; diterima dengan akibat desain.
5. **Shaft SH-4 owner tepat di as 7/C** (kolom dan 4 balok LT3); ketahuan dari clash model, bukan dari gambar.
6. **Asumsi fasad 4.2 konservatif** (14.821 vs 6.028 kN); terakota menimbulkan torsi keseimbangan di balok tepi.

## Batas dan yang dibawa ke tahap berikutnya

| Butir | Tahap |
|---|---|
| Kolom transfer 950/800 dan reaksi tangki diteruskan ke basement dan tiang | 5, 6 |
| Pit lift +11,25 di bawah banjir rencana perlu kedap (M-3) | 5 |
| M-6 kipas atap di area helipad, M-7 jarak MRI ke jalur ambulans (M-5 ruang AHU LT3 sudah masuk K1 di 4.2; biaya fit-out dicatat di RAB) | 5, 7 |
| Tindak lanjut evaluasi kunci (chiller dan frekuensi 14,5 Hz, opsi geser tangki, MRI, LB-1, surat owner/TABG) | `10 Laporan/Evaluasi Kunci Tahap 4.md` |
| Elevasi overstek fasad, arsitektur lengkap, nama RS, lingkungan, render akhir fotorealistis | 7 |
| Model LOD 350 belum membesi dinding inti dan pelat LT2/LT3 (batas perintah BIMCraft); GS-15 digambar di CADCraft | 7 |
| Ve dinding ACI 318-19 (informasi) bila SNI baru mengadopsi | catatan |
| Rekaman sintetis dan regangan EL 1,4-2,8 % sebagai keterbatasan respons situs | laporan akhir |

## Berkas

`04 Struktur Atas/`: `00 Rencana Tahap 4.md`, `4.0`-`4.10` (Excel, PDF, catatan), `Gambar/` (DWG, render fasad),
`Ringkasan Tahap 4.md`. Skrip `skrip/tahap4_*.py`, uji `tests/test_tahap4_*.py`.
