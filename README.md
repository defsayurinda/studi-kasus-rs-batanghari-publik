# RS Tepian Batanghari: studi kasus perencanaan terpadu

> **DATA SIMULASI.** Bukan proyek nyata dan tidak untuk konstruksi. Data tanah, owner, dan harga dibangkitkan untuk
> latihan portofolio. Bagian yang disusun AI dicatat di [DISCLAIMER.md](DISCLAIMER.md).

Perencanaan rumah sakit tipe C (150 tempat tidur) di tepi Sungai Batanghari, di atas lempung lunak, gambut sampai 3,7 m,
dan pasir yang mudah likuifaksi: dari penyelidikan tanah sampai RAB, jadwal, dan Laporan Akhir, dengan alur openBIM.

![Render eksterior dari arah Sungai Batanghari](<07 DED dan RKS/Render/R-01.png>)

![Gantt dan kurva S](<09 Jadwal/9 Gantt dan Kurva S.png>)

## Angka kunci

| | |
|---|---|
| Gedung | gedung utama 6 lantai + gedung utilitas/parkir 4 lantai, 19.328 m² |
| Tanah | lempung lunak, gambut sampai 3,7 m, pasir U5 mudah likuifaksi (kelas situs SF) |
| Pondasi | 321 tiang bor Ø800 sedalam ±38 m, 84 pile cap |
| Dokumen | model IFC federasi, 64 lembar DED, RKS 15 bab, Laporan Akhir 52 halaman |
| Biaya | RAB Rp 286,22 miliar (Rp 14,81 juta/m²), volume otomatis dari model IFC |
| Waktu | jadwal CPM 98 minggu, mulai 3 Jan 2028 |

## Peta folder

| Folder | Isi |
|---|---|
| `00 Kerangka Acuan` | TOR owner, matriks tanggapan, program ruang |
| `01 Penyelidikan Tanah`, `02 Olah Data Tanah` | Telaah data penyedia, parameter, kelas situs, likuifaksi |
| `03 Desain Konsep` | BEP, kajian tapak, peil dan urugan, program ruang, massa |
| `04 Struktur Atas` | Respons situs, model OpenSees 3D, pelat, balok, kolom, dinding geser |
| `05 Struktur Tengah`, `06 Struktur Bawah dan Basement` | Tangki, tiang bor, penurunan, perkuatan tebing |
| `07 DED dan RKS` | Model IFC federasi, clash, 64 lembar DED, RKS, render |
| `08 RAB`, `09 Jadwal` | Volume dari model, AHSP, RAB, SMKK, VE; CPM, Gantt, kurva S |
| `10 Laporan` | Laporan Akhir, Laporan Audit Akhir, Halaman Portofolio |
| `model/` | Model BIM (`.bimc`) dan IFC |
| `skrip/`, `tests/` | Skrip Python pembangun dokumen dan uji |
| `VERIFIKASI.md` | Cek silang T-06 s.d. T-127, termasuk yang gagal beserta penjelasannya |

Keputusan proyek: [00 RANCANGAN.md](00%20RANCANGAN.md); riwayat: [PROGRES.md](PROGRES.md); melanjutkan manual:
[CARA LANJUT MANUAL.md](CARA%20LANJUT%20MANUAL.md).

## Cara menjalankan

Python 3.12, Windows. Alat dan lingkungan dipasang ulang dengan:

```powershell
powershell -ExecutionPolicy Bypass -File SIAPKAN.ps1
```

```powershell
.venv\Scripts\python.exe skrip\<nama>.py          # satu skrip pembangun (Excel/Word/gambar)
.venv\Scripts\python.exe -m pytest -q tests       # uji
```

Dokumen dibangun ulang dari skrip; hasil analisis berat OpenSees disimpan di `cache/` (tidak di-commit). Dokumen
berhak cipta (SNI, manual, jurnal) tidak ikut repo; daftar acuan ada di `acuan/README.md`.

## Alat

BIMCraft (model BIM), CADCraft (gambar DWG), IfcOpenShell (IFC, Qto, validasi), OpenSees (analisis struktur 3D),
Blender (render dari IFC), Python (pandas, openpyxl, python-docx, matplotlib). Rincian: `PERINTAH DAN SKILL.md`.

## Hasil utama

- [Laporan Akhir (PDF)](<10 Laporan/Laporan Akhir.pdf>) · [Audit Akhir (PDF)](<10 Laporan/Audit Akhir.pdf>) · [RKS (PDF)](<07 DED dan RKS/7.7 RKS.pdf>)
- [Halaman Portofolio](<10 Laporan/Halaman Portofolio.md>)

## Unduh

Semua berkas ada di repositori ini: laporan (`10 Laporan/*.pdf`, `*.docx`), gambar DED (`07 DED dan RKS/Gambar/DWG` dan PDF),
Excel per tahap, model IFC (`model/`), dan RKS. Paket zip per kelompok ada di
[Releases](../../releases/latest).

Catatan: repositori ini adalah salinan publik tanpa riwayat commit dan tanpa berkas evaluasi internal.
