# Studi Kasus Terpadu: RS tipe C 6 lantai + basement, tepi Batanghari (Claude Code)

Dibaca otomatis tiap sesi yang dibuka di folder ini (CLAUDE.md folder `Portofolio` di atasnya ikut terbaca).
Keputusan proyek ada di `00 RANCANGAN.md`, posisi terakhir di `PROGRES.md`. Baca keduanya di awal sesi.
Skill, modul Python, model, dan effort yang dipakai per tahap ada di `PERINTAH DAN SKILL.md`; ikuti tabel itu.

## Mode cepat (arahan Defsa 22 Nov 2026, berlaku sampai portofolio selesai; mengalahkan aturan di bawah bila bertabrakan)

Tujuan: portofolio cepat selesai, tetap bagus, hemat jatah. Sisa: 7.8 (render di Colab), 7.9, Tahap 8 RAB, 9 Jadwal, 10 Laporan.
- **Sesi besar per tahap**: Tahap 8 dalam 2-3 sesi (a: volume dari model + AHSP; b: RAB, SMKK, VE), Tahap 9 dalam 1-2 sesi,
  Tahap 10 dalam 2-3 sesi. Langkah kecil dalam satu tahap digabung; tidak ada titik berhenti per langkah.
- **AI menghitung dan memutuskan** dengan label "atas delegasi Defsa"; Defsa menelaah **satu ringkasan per tahap** di akhir
  (aturan "Defsa menghitung dulu" ditangguhkan). PR langsung di-merge.
- **Isi secukupnya, fokus yang terlihat di portofolio**: RAB dengan volume otomatis dari model BIM, AHSP rinci hanya untuk
  pekerjaan utama (±20 % item yang mencakup ±80 % biaya), sisanya harga satuan ringkas; Jadwal = satu Gantt + kurva S dari
  volume RAB (tanpa simulasi 4D berat); Laporan = satu Laporan Akhir + halaman portofolio (bukan tiga laporan).
- **Hemat**: Opus untuk keputusan/pemeriksaan, Sonnet untuk format Word/Excel; uji hanya berkas yang disentuh, seluruh uji
  sekali di akhir tahap saja; jawaban ke Defsa singkat; tidak ada iterasi render tambahan kecuali hasilnya jelek.
- **Laptop panas** (heatsink tidak menempel setelah servis 7 Nov): tidak ada render/hitungan berat/seluruh `pytest` di laptop
  sampai diperbaiki; render di Colab (`skrip/tahap7_render_colab.ipynb`). Commit sesering mungkin.
- Tetap wajib: sumber angka (SNI/pasal), cek silang di `VERIFIKASI.md`, format `FORMAT LAPORAN DAN EXCEL.md`, kunci jawaban
  tidak dibuka.

## Aturan kerja

- Defsa insinyurnya, AI asistennya. Untuk hitungan inti: Defsa menghitung dulu, AI memeriksa. Jangan memberi
  jawaban tahap sebelum Defsa mencoba, kecuali diminta.
- Tidak ada angka tanpa sumber: tulis SNI dan pasalnya, atau buku dan halamannya. Cocokkan ke `acuan/`.
  Kalau dokumen acuannya tidak ada, katakan, jangan menebak pasal.
- Setiap angka penting dicek silang minimal dua cara dan dicatat di `VERIFIKASI.md` (batas toleransi ditetapkan dulu).
- Satuan SI (kN, m, kPa, MPa). Desimal dengan koma di laporan, titik di kode.
- Data skenario bersifat simulasi dan diberi label `[Uji sendiri]`, `[Literatur: ...]`, atau `[Asumsi: ...]`.
- **Kunci jawaban dan pembangkit data ada di `../02 Siap Terbit/privat/studi-kasus-kunci/`. Jangan membuka,
  mengutip, atau memberi petunjuk dari sana kecuali Defsa minta petunjuk atau membuka kunci tahap.**
- Petunjuk bertingkat bila Defsa macet: (1) arah umum, (2) data mana yang perlu dilihat, (3) metode, baru (4) jawaban.
- Format berkas biasa (.xlsx, .docx, .ifc, .py, .pdf) supaya bisa dilanjutkan manual (`CARA LANJUT MANUAL.md`).
- **Bentuk Word dan Excel wajib mengikuti `FORMAT LAPORAN DAN EXCEL.md`** (pakai `skrip/format_dokumen.py`). Sebelum
  menyerahkan, render ke PDF dan cek inden subbab/butir, bentuk tabel, proporsi sel, dan *freeze panes*.
- Akhir sesi: perbarui `PROGRES.md` dan tawarkan commit. Git mengikuti aturan di CLAUDE.md folder `Portofolio`.
- `acuan/privat/` berisi dokumen berhak cipta (SNI): tidak boleh di-commit atau terbit.

## Alat dan perintah

```
.venv\Scripts\python.exe -m pytest -q tests                  # uji skrip
.venv\Scripts\python.exe skrip\<nama>.py                       # skrip proyek
alat\bimcraft\bimcraft-0.12.0-windows-x64-portable\bimcraft.exe            # BIMCraft (GUI)
alat\bimcraft\bimcraft-0.12.0-windows-x64-portable\bimcraft-cli.exe info model\<berkas>
alat\blender\blender.exe                                       # Blender + Bonsai (mode portable)
alat\freecad\bin\FreeCAD.exe                                   # FreeCAD portable
"C:\Program Files\ArtCraft\CADCraft\cadcraft.exe"              # CADCraft (GUI, buka/edit DWG)
.venv\Scripts\python.exe skrip\tahap2_gambar_cad.py            # bangun ulang gambar GT-01..GT-15 di CADCraft
```

- **Aturan lengkap gambar: `ATURAN GAMBAR CADCRAFT.md`** (wajib dibaca sebelum membuat atau mengubah gambar).
- **Semua gambar digambar asli di CADCraft** (`cadcraft-cli mcp`, klien `skrip/cadcraft.py`) dengan `skrip/cad_lembar.py`
  (`Gambar`): model space berkoordinat nyata (1 unit = 1 mm), layer per unsur, pline/hatch/garis ukur/teks; layout A3
  dengan satu kop block `KOP_A3` (`templat/KOP A3.dwg`, `skrip/cad_kop.py`), viewport terkunci pada skala gambar,
  legenda dan catatan di kolom kanan; DWG di `Gambar/DWG/` dan PDF hasil plot layout. `gambar_teknik.Kertas`
  (matplotlib disalin ke CAD) tidak dipakai lagi untuk gambar baru (arahan Defsa 19 Nov 2026). Model gedung, denah
  lantai, dan potongan bangunan dari BIMCraft (IFC). Jangan membuat kop sendiri per gambar.
  DWG harus seperti buatan drafter: garis ukur asosiatif (nilai terukur, bukan teks tetap), simbol berupa block,
  arsir asosiatif, satu layout per lembar, tanpa teks bertumpuk (`skrip/cad_cek.py <dwg>` wajib 0 pasangan).

- MCP BIMCraft (`.mcp.json`): server `bimcraft` headless (proyek sendiri tanpa jendela; buka/simpan `.bimc` dan
  ekspor IFC lewat alat `open`/`save`), selalu bisa dipakai. Server `bimcraft-jendela` menyambung ke jendela yang dibuka
  dengan `bimcraft.exe --control 0` (atau File > Settings > Agents); tanpa jendela, server ini gagal dan itu wajar.
- **BIMCraft setara CADCraft:** klien `skrip/bimcraft.py` (`Sesi(berkas)` membangun model dengan CLI 0.12.0; `tampilkan()`
  membuka hasil di jendela BIMCraft). **Jendela memakai BIMCraft 0.11.0** karena jendela 0.12.0 berhenti sendiri di laptop
  ini (19 Nov 2026); 0.11.0 hanya membaca `.bimc` sampai format 17, jadi model 0.12.0 ditampilkan lewat IFC-nya
  (`ke_v011()` → `<nama>-v0.11.bimc`). Jendela dibuka dengan `BUKA BIMCRAFT.cmd` (bisa juga diluncurkan dari tab
  terminal panel). Model harus utuh, bisa dilihat 3D, dan bisa dilanjutkan manual; cadangan: `BUKA MODEL DI BLENDER.cmd`.
- **Aplikasi dibuka sungguhan:** gambar dibuat di jendela CADCraft (`cadcraft.exe --control 7979`; skrip dengan env
  `CADCRAFT_JENDELA=1` atau `Sesi(jendela=True)` membukanya otomatis; MCP `cadcraft-jendela`) dan model di jendela
  BIMCraft (`bimcraft.exe --control 0`; MCP `bimcraft-jendela`), supaya Defsa bisa melihat dan melanjutkan manual.
- **Cache analisis OpenSees bersama** (`skrip/cache_analisis.py`, folder `cache/opensees/`, tidak di-commit; di worktree
  disambung oleh `siapkan_worktree.ps1`): `analisis` dan `rancang` 4.6/4.7/4.8 serta `tahap5_tangki.hasil_46_47`
  disimpan ke disk. Kunci = argumen + ukuran model + sidik skrip tahap3/4 dan data, jadi tidak pernah basi. Hitung 5.6
  turun dari 178 ke 9 detik. Skrip baru memanggil versi tanpa argumen (`kl.rancang()`, `td.rancang()`), bukan
  `rancang_dari(hs, ...)`, dan tidak membuat pickle env sendiri. Fungsi berat baru: beri `@cache_analisis.disk`
  (argumen sederhana saja). Paksa hitung ulang: env `TANPA_CACHE=1`.
- **Sesi di worktree** (`.claude/worktrees/...`): `alat/`, `.venv/`, `acuan/privat|pustaka|jurnal` tidak ikut git. Jalankan
  `powershell -ExecutionPolicy Bypass -File skrip\siapkan_worktree.ps1` di awal sesi (junction ke folder utama), lalu
  sambung ulang MCP lewat `/mcp`. Tanpa ini MCP BIMCraft gagal ("Connection closed") karena path `alat/...` relatif.
- QGIS 3.44 LTR dan ProjectLibre terpasang di sistem. PLAXIS 3D V20 hanya untuk cek silang GeoFEM3D.
- Pustaka Python: lihat `requirements.txt`. Pasang ulang semua alat: `powershell -ExecutionPolicy Bypass -File SIAPKAN.ps1`.
- Skill proyek ada di `.claude/skills/` (IfcOpenShell, Bonsai, BIM QTO/clash/validasi, Gantt, QGIS, penulisan ilmiah,
  defsa-yurinda-skill).

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. When the answer is under a Markdown heading, `graphify section "<heading>"` prints that section's text, so the .md need not be opened. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
