# Perintah, skill, dan modul per tahap

Pegangan cepat setiap membuka sesi. Skill proyek ada di `.claude/skills/`; modul Python di `.venv` (lihat `requirements.txt`).
Panggil skill dengan menyebut namanya, misalnya *"pakai skill bonsai-impl-qto"*, atau ketik `/nama-skill`.

## Pengaturan dasar

| Pengaturan | Saran |
|---|---|
| Folder kerja | `10 Studi Kasus Terpadu` |
| Output style | Explanatory (sehari-hari), Learning (belajar konsep baru) |
| Mode izin | Default; Accept edits setelah terbiasa |
| Ponytail | off; lite saat membuat skrip |
| Plan mode | Nyalakan di awal Tahap 3, 4, 6, 8 |
| Model / effort | Dipilih AI menurut tabel "Model, effort, dan ponytail" di `~/.claude/CLAUDE.md` (hitungan rutin Opus medium, keputusan/review Opus high, format/rutin Sonnet medium, rapikan berkas Haiku low) |

## Perintah sesi

| Kapan | Perintah |
|---|---|
| Buka sesi | `Baca PROGRES.md, kita lanjut tahap X.` |
| Belajar dulu | `Jelaskan konsep tahap X dulu, pakai contoh soal.` |
| Periksa | `Periksa hitunganku di <berkas>, cek pasal SNI dan satuan, lalu buat cek silang.` |
| Macet | `Minta petunjuk level 1` (naik sampai level 4) |
| Rapat | `Jadilah owner / konsultan MK / reviewer, saya presentasi <topik>.` |
| BIMCraft | Buka pintasan Desktop, lalu `Sambungkan ke BIMCraft dan periksa model.` |
| Kunci | `Buka kunci tahap X.` (setelah tahap selesai) |
| Kejadian baru | `Minta sesi skenario membangkitkan kejadian tahap X.` |
| Review segar | Di sesi baru: `Review <folder/berkas> tanpa konteks, cari kesalahan.` |
| Hemat | `Compact` saat sesi panjang |
| Tutup sesi | `Perbarui PROGRES.md dan commit.` |

## Per tahap

| Tahap | Model / effort | Skill | Modul Python | Alat |
|---|---|---|---|---|
| 0 Kerangka acuan | Opus / medium | defsa-yurinda-skill, docx, xlsx | openpyxl, python-docx | Word, Excel, QGIS |
| 1 Penyelidikan tanah | Opus / high | defsa-yurinda-skill, scientific-critical-thinking | pandas, pygef | Excel |
| 2 Olah data tanah | Opus / high | defsa-yurinda-skill, xlsx, dataviz, scientific-visualization | pandas, matplotlib, groundhog, pint | Excel, GeoFEM3D |
| 3 Desain konsep | Opus / high, plan mode | defsa-yurinda-skill, bonsai-impl-modeling, ifcos-impl-creation, qgis-agents-map-generator, scientific-critical-thinking | ifcopenshell, Pynite (pra-dimensi cepat) | BIMCraft (LOD 200), QGIS, awatif |
| 4 Struktur atas | Opus / medium (high untuk keputusan dan review akhir) | defsa-yurinda-skill, ifcos-syntax-api, ifcos-impl-creation, bonsai-impl-modeling | openseespy, opstool, Pynite, concreteproperties, sectionproperties, ifcopenshell | BIMCraft, awatif |
| 5 Struktur tengah | Opus / high | defsa-yurinda-skill | Pynite, concreteproperties | BIMCraft |
| 6 Struktur bawah + basement | Opus / high, plan mode | defsa-yurinda-skill, scientific-critical-thinking | openpile, groundhog, pyslope, openseespy | GeoFEM3D, PLAXIS (cek silang), BIMCraft |
| 7 DED dan RKS | Sonnet / medium (gambar), Opus / medium (RKS) | bonsai-impl-drawing, bim-clash-detection, bim-validation-pipeline, ifcos-impl-validation, docx | ifcopenshell, python-docx | BIMCraft, Bonsai, LibreCAD, Word |
| 8 RAB (5D) | Opus / high (aturan volume), Sonnet / medium (isi Excel), plan mode | bim-qto, bonsai-impl-qto, xlsx | ifcopenshell, pandas, openpyxl | Bonsai, Excel |
| 9 Jadwal (4D) | Sonnet / medium | gantt-chart, bonsai-impl-qto | ifcopenshell, networkx | Bonsai, ProjectLibre |
| 10 Laporan dan situs | Opus (isi), Sonnet (format) | scientific-writing, docx, pdf, dataviz, qgis-impl-print-layouts | matplotlib | Word, situs |
| Review akhir tiap tahap | Opus / high, sesi baru | scientific-critical-thinking, code-review | pytest | - |

**Pola hemat (arahan Defsa 20 Nov 2026):** kolom model di atas berlaku untuk sesi Opus yang merencanakan dan memeriksa;
pelaksanaan (skrip, Excel/Word, CADCraft, BIMCraft, commit) didelegasikan ke subagen `Agent` model `sonnet`. Rincian
di `~/.claude/CLAUDE.md` bagian "Pola kerja Opus-pikir, Sonnet-kerja".

## Aturan pakai skill

- **defsa-yurinda-skill** dipakai di setiap tahap yang ada hitungan atau berkas teknik sipil.
- Skill pihak ketiga (ifcos-*, bonsai-*, bim-*, gantt-chart, qgis-*, scientific-*) hanya panduan; angka tetap dicek ke SNI dan `VERIFIKASI.md`.
- Skrip baru wajib punya uji di `tests/` dan lolos `.venv\Scripts\python.exe -m pytest -q tests`.
