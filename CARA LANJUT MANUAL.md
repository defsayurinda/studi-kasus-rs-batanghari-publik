# Cara melanjutkan tanpa AI

Semua berkas memakai format biasa, jadi proyek bisa dilanjutkan dengan tangan kapan saja.

## Posisi dan aturan

- Posisi terakhir: `PROGRES.md`. Keputusan proyek: `00 RANCANGAN.md`.
- Setiap tahap punya foldernya sendiri. Tulis hasil di folder tahap, catat cek silang di `VERIFIKASI.md`.

## Membuka alat

Pintasan di Desktop: **BIMCraft (Studi Kasus)** (terbuka dengan `--control 0` supaya AI bisa menyambung),
**Blender + Bonsai BIM**, **FreeCAD 1.1.4**, **QGIS 3.44 LTR**, **ProjectLibre**, **LibreCAD**, **awatif**
(web), **GeoFEM 3D**, **PLAXIS 3D**, dan **Studi Kasus Terpadu (folder)**. Kalau pintasan hilang, buka langsung
dari tabel berikut.

| Pekerjaan | Buka |
|---|---|
| Model BIM | `alat\bimcraft\bimcraft-0.12.0-windows-x64-portable\bimcraft.exe`, simpan model di `model\` (.bimc), ekspor IFC ke `model\` |
| 4D, 5D, gambar dari IFC | `alat\blender\blender.exe`, menu Bonsai (sidebar kanan / File > Open IFC) |
| BIM alternatif, FEM | `alat\freecad\bin\FreeCAD.exe` |
| Peta lokasi | QGIS 3.44 dari menu Start |
| Jadwal | ProjectLibre dari menu Start; simpan di `09 Jadwal\` |
| Analisis portal dengan GUI | https://awatif.co/app (statik linear) |
| Hitungan | Excel di folder tahap |
| Skrip Python | buka PowerShell di folder ini: `.venv\Scripts\python.exe skrip\<nama>.py` |
| Uji skrip | `.venv\Scripts\python.exe -m pytest -q tests` |
| Analisis tanah | GeoFEM3D (Desktop) atau PLAXIS 3D untuk cek silang |

## Kalau memakai laptop lain

1. Salin folder ini (atau clone repo-nya).
2. Jalankan `powershell -ExecutionPolicy Bypass -File SIAPKAN.ps1` (mengunduh alat ke `alat\`, memasang QGIS dan
   ProjectLibre, membuat `.venv`).
3. Salin dokumen SNI ke `acuan\privat\` (tidak ikut di repo).

## Kalau kembali memakai AI (akun mana pun)

Buka Claude Code dengan folder kerja `10 Studi Kasus Terpadu`, lalu tulis: *"Baca PROGRES.md, kita lanjut tahap X."*
Aturan, skill, dan sambungan BIMCraft ada di folder ini (`CLAUDE.md`, `.claude/`, `.mcp.json`), jadi tidak tergantung akun.
