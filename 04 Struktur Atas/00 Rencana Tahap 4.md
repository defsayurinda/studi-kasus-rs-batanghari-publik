# Rencana Tahap 4: Struktur Atas (disetujui Defsa 20 Nov 2026)

## Konteks

Tahap 0-3 dan laporan antara (LA.1-LA.8) sudah disetujui dan di-merge. Keputusan pembiayaan tahap 1 opsi (a) ada di
`origin/main` (6d19f6c, PR #22), sedangkan worktree ini masih di 836beca. Notulen rapat konsep menyatakan Tahap 4 dimulai
setelah paket tahap 1 dan data beban MEP disepakati. Rapat laporan pendahuluan (Tabel 1.2 no. 12) mewajibkan owner
menyerahkan data beban MEP sebelum Tahap 4. Saat ini baru ada `03 Desain Konsep/Data Owner/Data MEP Awal.xlsx`.

Tahap 4 menghasilkan desain struktur atas yang bisa dipertanggungjawabkan. Dasarnya ada tiga:
- spektrum spesifik-situs kelas SF, menggantikan spektrum sementara SE (SDS 0,482, SD1 0,524);
- pembebanan SNI 1727:2020;
- analisis 3D sistem ganda.

Desain unsurnya mengikuti SNI 2847:2019, lalu dituangkan ke model BIMCraft LOD 300 dan gambar CADCraft.

Dasar yang tetap berlaku:
- konsep tidak diulang;
- tahap 1 = paket D/E (50 TT di LT4); menara LT5-LT6, dek parkir, dan isi LT3 menyusul;
- struktur menara didesain penuh 6 lantai.

**Akibatnya, struktur dicek untuk dua konfigurasi:**
- **K1 (tahap 1):** podium LT1-LT3 dan menara sampai atap LT4 sementara;
- **K2 (akhir):** menara 6 lantai, atap helipad, dan dek kantilever.

Desain memakai selubung K1 dan K2. Sambungan kolom dan dinding untuk lantai yang menyusul didetailkan sekarang.

## Cara kerja

- AI mengisi draf atas permintaan Defsa, lalu Defsa memeriksa. Setiap langkah berhenti dengan label **"draf, menunggu
  persetujuan Defsa"**. Defsa boleh menghitung dulu satu unsur contoh per langkah desain (4.6-4.8) sebelum melihat versi AI.
- Pasal SNI selalu dicocokkan ke PDF di `acuan/privat/` (SNI 1726-2019, 1727-2020, 2847-2019, 2052-2017). Bila pasal
  tidak ditemukan, ditulis "belum ada di acuan", bukan ditebak.
- Excel dan Word mengikuti `FORMAT LAPORAN DAN EXCEL.md` (`skrip/format_dokumen.py`). Excel dihitung ulang di Excel lalu
  dicocokkan dengan Python. Gambar dibuat di CADCraft dengan `skrip/cad_lembar.py` (`Gambar`) dan kop `KOP_A3`; hasilnya
  harus lolos `cad_cek` dengan 0 pasangan.
- Kunci di `../02 Siap Terbit/privat/studi-kasus-kunci/` tidak dibuka.
- Git:
  - cabang `fitur/tahap-4-struktur-atas` dari `origin/main` terbaru;
  - PR lewat REST API, pesan berbahasa Indonesia tanpa Co-Authored-By;
  - merge hanya bila Defsa bilang.
- Skill: defsa-yurinda-skill (semua langkah); ifcos-syntax-api, ifcos-impl-creation, dan bonsai-impl-modeling (4.9).

## Langkah

| Langkah | Isi | Keluaran (`04 Struktur Atas/`) |
|---|---|---|
| 4.0 | Persiapan dan permintaan data skenario | catatan + daftar data |
| 4.1 | Spektrum respons spesifik-situs kelas SF | `4.1 Respons Spesifik Situs.xlsx`, GS-01 |
| 4.2 | Pembebanan SNI 1727 dan kombinasi | `4.2 Pembebanan.xlsx`, GS-02 |
| 4.3 | Model analisis 3D, ketidakberaturan, simpangan | `4.3 Analisis Struktur.xlsx` |
| 4.4 | Cek silang analisis (PyNite + hitungan tangan) | `VERIFIKASI.md` |
| 4.5 | Desain pelat (lantai, atap podium, atap helipad) | `4.5 Desain Pelat.xlsx` |
| 4.6 | Desain balok (SRPMK) dan balok khusus atap/helipad | `4.6 Desain Balok.xlsx` |
| 4.7 | Desain kolom dan hubungan balok-kolom | `4.7 Desain Kolom.xlsx` |
| 4.8 | Desain dinding geser, balok kopel, tangga, atap | `4.8 Desain Dinding Geser, Tangga, Atap.xlsx` |
| 4.9 | Model BIMCraft LOD 300 | `model/RSTB-STR-T4-LOD300.bimc/.ifc` |
| 4.10 | Gambar struktur di CADCraft (GS-xx, KOP_A3) | `Gambar/DWG/`, PDF A3 |
| 4.11 | Ringkasan Tahap 4, PROGRES, PR | `Ringkasan Tahap 4.md` |

### 4.0 Persiapan

1. Gabungkan `origin/main` (PR #22) ke cabang kerja.
2. Kirim permintaan ke sesi skenario lewat SendMessage ke `local_278163ac-...` (skenario-tahap-3). Isi permintaan:
   - **Data beban MEP rinci dari owner:** daftar alat dengan berat operasi, tapak, lokasi (lantai/grid), dan beban
     dinamis atau getaran. Cakupannya:
     - chiller, cooling tower, dan tangki air 158 t di atap podium;
     - AHU, genset, trafo, dan panel;
     - lift (mesin, beban rel, pit);
     - alat medis berat: CT, MRI (bila ada, beserta pelindungnya), X-ray, dan sterilisasi CSSD;
     - shaft, lubang pelat, dan jalur pipa;
     - rak kabel atau pipa gantung (kPa).
     Ini sesuai keputusan rapat LP no. 12 dan rapat konsep.
   - **Penyelidikan pelengkap untuk respons situs (paket 12):** profil Vs sampai batuan dasar setara (Vs ≥ 760 m/s).
     Saat ini MASW dan downhole hanya mencapai ±30-40 m. Pilihannya downhole dalam atau HVSR/mikrotremor beberapa titik,
     dengan label simulasi.
   - **Tanggapan owner** atas penataan atap final dan tahap 1 bila ada (opsional).
3. Cek acuan tambahan dan catat yang belum ada: pedoman helipad (beban AW139) dan sumber rekaman gempa.
4. Usul pasang `pystrata` (respons situs ekivalen-linear, sumber terbuka) ke `.venv` dan `requirements.txt`.

**Berhenti: Defsa menyetujui permintaan data dan pemasangan paket.**

### 4.1 Respons spesifik-situs (kelas SF)

- **Dasar:** SNI 1726:2019 Pasal 5.3.1 (SF wajib analisis respons situs) dan Pasal 6.10 (prosedur gerak tanah
  spesifik-situs, batas bawah terhadap spektrum umum). Pasal dicek ke PDF.
- **Input batuan:** Ss 0,334 dan S1 0,264 (Desain Spektra PUPR, 2.6), Mw 7,0 (deagregasi PuSGeN). Dipakai ≥ 5 rekaman
  (jumlah dicek ke pasal) yang diskalakan atau dicocokkan ke spektrum target batuan.
  - **Keputusan Defsa:** sumber rekaman. Pilihan pertama: Defsa mengunduh dari PEER NGA-West2 atau ESM lewat browser
    dengan akunnya sendiri. Cadangannya rekaman sintetis yang dicocokkan spektrum, dengan label [Asumsi].
- **Profil tanah:** unit U1-U7 dari 2.4 dan profil per zona gambut (LA.1); Vs dari 2.5; kurva G/Gmax-redaman dari
  literatur (Darendeli, Vucetic-Dobry), diberi label [Literatur].
- **Likuifaksi U5 (FS 0,22-0,75):** analisis ekivalen-linear tegangan total tidak berlaku setelah pasir mencair.
  Karena itu dihitung dua kasus, U5 utuh dan U5 terdegradasi (kekakuan residu), lalu diambil selubungnya.
- **Cara dua:** analisis 1D nonlinier tegangan total di openseespy (kolom tanah, elemen PressureIndependMultiYield /
  PressureDependMultiYield) untuk 1-2 rekaman.
- **Hasil:** spektrum desain SDS dan SD1 baru sesuai pasal (rasio rata-rata × MCER batuan, dua per tiga, batas bawah),
  lalu KDS ditinjau ulang. Kalau SDS atau SD1 naik, akibatnya untuk sistem dan pra-dimensi dihitung ("so what").
- **Cek silang:**
  - T-65: amplifikasi pystrata vs openseespy 1D;
  - T-66: periode situs dari Σ4H/Vs vs fungsi transfer.
- **Gambar:** GS-01, yaitu profil Vs, spektrum permukaan, dan spektrum desain terhadap SE sementara (`cad_grafik.py`).

**Berhenti: Defsa menyetujui spektrum desain.**

### 4.2 Pembebanan

- **Beban mati dan beban mati tambahan:** finishing, plafon, ME gantung, dinding bata per m², fasad.
- **Beban hidup menurut SNI 1727:2020 Tabel 4.3-1** (nilai dicek ke PDF): ruang operasi/laboratorium, ruang pasien,
  koridor, gudang, ruang mesin, atap. Reduksi beban hidup diterapkan sesuai Pasal 4.7 dan batasnya.
- **Beban alat RS dan MEP:** dari data 4.0, sebagai beban terpusat atau merata pada grid yang sebenarnya. Atap podium
  memikul chiller dan tangki air 158 t (25,8 kPa di 3.6/LA.4), dicek sebagai beban lokal pada balok khusus.
- **Helipad AW139 (6.800 kg):** SNI 1727 Pasal 4.11 (beban helipad merata dan terpusat 1,5 × MTOW pada tapak roda),
  ditambah beban mendarat darurat bila acuannya ada. Dek kantilever 4,7 m disiapkan sebagai beban reaksi pada atap
  menara; desain dek baja menyusul.
- **Beban lain:** hujan (Pasal 8, genangan atap datar), angin (Pasal 26-27, dicek terhadap gempa), gempa dari 4.1.
- **Kombinasi beban:** SNI 1726 Pasal 4.2.2, termasuk ρ, Ev = 0,2 SDS D, dan Ω0 untuk unsur yang perlu.
- **Cek silang:**
  - T-67: berat seismik total, dari model vs dari tabel luas × beban per m²;
  - T-68: beban per m² terhadap angka wajar.
- **Gambar:** GS-02, denah zona beban per lantai.

**Berhenti: Defsa menyetujui pembebanan.**

### 4.3 Model analisis 3D sistem ganda

- **Model openseespy:**
  - kolom dan balok `elasticBeamColumn` dengan kekakuan retak SNI 2847 Tabel 6.6.3.1.1;
  - dinding inti `ShellMITC4` (atau kolom lebar, dipilih setelah uji konvergensi);
  - diafragma kaku per lantai dan tumpuan jepit di atas pile cap (interaksi tanah-struktur di Tahap 6);
  - visualisasi dengan opstool.
- **Geometri:** dari model LOD 200 (`model/RSTB-STR-T3-LOD200.ifc`, grid 8 m) yang dibaca IfcOpenShell, supaya model
  analisis dan BIM tidak berbeda.
- **Analisis:**
  - modal (partisipasi massa ≥ 100 % atau sesuai pasal);
  - gaya lateral ekivalen dan ragam spektrum (Pasal 7.8-7.9) dengan penskalaan geser dasar;
  - torsi tak terduga dan amplifikasi Ax.
- **Pemeriksaan:**
  - ketidakberaturan horizontal dan vertikal (Tabel 13 dan 14), terutama setback podium-menara, torsi inti tak simetris,
    dan kekakuan tingkat lunak di LT1 (lobi tinggi);
  - simpangan antarlantai kategori IV (Tabel 20, Δa = 0,010 hsx, dibagi ρ bila berlaku);
  - stabilitas P-Δ (θ);
  - syarat sistem ganda: rangka memikul ≥ 25 % gaya gempa (Pasal 7.2.5.1);
  - pemisahan gedung utilitas/parkir.
- **Keputusan Defsa bila hasilnya menuntut:** podium dan menara satu kesatuan atau dipisah dilatasi.
- **Konfigurasi:** K1 dan K2 dianalisis keduanya.

### 4.4 Cek silang analisis

- T-69: periode T1, openseespy vs PyNite vs Ta Pers. 7.8-7 (Cu·Ta).
- T-70: geser dasar, ELF manual (Excel) vs openseespy.
- T-71: gaya aksial kolom dalam akibat gravitasi, area tributari (seperti T-44) vs model.
- T-72: simpangan atap, openseespy vs PyNite.
- Toleransi ditetapkan dulu: struktur ≤ 5-10 %.

**Berhenti: Defsa menyetujui hasil analisis (4.3-4.4).**

### 4.5-4.8 Desain unsur (SNI 2847:2019)

Dimulai dari pra-dimensi 3.6:
- pelat 200;
- balok 350 × 600;
- kolom 750 (podium) / 650 (menara);
- dinding inti 350.

Ukuran yang tidak lolos dinaikkan dan akibatnya dicatat. Mutu beton dan baja tulangan ditetapkan di 4.5 (fc' dan
BjTS 420B SNI 2052, dicek); paparan S2 hanya untuk unsur yang menyentuh tanah (Tahap 5-6).

| Langkah | Unsur | Pasal kunci | Cara kedua |
|---|---|---|---|
| 4.5 | Pelat dua arah lantai, atap podium (tangki/chiller), atap menara (helipad), lubang shaft | Pasal 8, tebal min Tabel 8.3.1.1, lendutan, geser pons di beban terpusat | koefisien momen vs model pelat PyNite |
| 4.6 | Balok SRPMK, balok khusus atap tangki, balok tumpuan dek helipad | Pasal 9, 18.6 (Mpr, geser kapasitas, sengkang daerah sendi) | Excel sendiri vs concreteproperties (momen-kelengkungan) |
| 4.7 | Kolom SRPMK, HBK | Pasal 10, 18.7 (ΣMnc ≥ 1,2 ΣMnb, tulangan pengekang), 18.8 | diagram P-M Excel vs concreteproperties |
| 4.8 | Dinding geser khusus, elemen batas, balok kopel, tangga, atap, sambungan lantai menyusul | Pasal 11, 18.10 (cek elemen batas cara perpindahan dan tegangan), Pasal 25 sambungan lewatan/mekanis | dua metode elemen batas; tangga balok miring vs pelat PyNite |

- **Cek silang:** T-73 dan seterusnya, satu per jenis unsur (contoh: kolom dalam K1 dan K2, balok tumpuan tangki, dinding
  inti LT1).
- **Cek wajar:** rasio tulangan (kg/m³ beton per unsur) dan kebutuhan volume dibandingkan dengan biaya 3.8 rev B.
- Setiap langkah 4.5-4.8 berhenti untuk persetujuan Defsa.

### 4.9 Model BIMCraft LOD 300

- **Pembuatan:** dibangun dengan `skrip/bimcraft.py` (`Sesi(berkas)`, CLI 0.12.0) dari tabel desain 4.5-4.8.
- **Isi model:**
  - ukuran unsur final;
  - bukaan shaft MEP;
  - tangga dan atap;
  - tumpuan dek helipad.
- **Pset:** Pset_RSTB_Umum dengan mutu, LOD 300, dan `RSTB_Paket` (tahap 1 / menyusul) agar Tahap 8-9 bisa
  memisahkan paket.
- **Validasi IFC:**
  - IfcOpenShell (hierarki, GlobalId unik);
  - volume dibanding Excel desain (±5 %);
  - clash dasar terhadap shaft MEP.
- **Tampilan:** di jendela BIMCraft 0.11.0 lewat `bimcraft.tampilkan()` (`ke_v011`) dengan view 3D tersimpan; cadangan
  `BUKA MODEL DI BLENDER.cmd`.
- **Syarat:** model utuh, terlihat 3D, dan bisa dilanjutkan manual.

### 4.10 Gambar struktur (CADCraft, KOP_A3)

- **Daftar gambar:** GS-01 dan GS-02 (4.1-4.2), lalu:
  - denah rencana struktur per lantai, termasuk penanda K1/K2;
  - denah atap podium dan atap helipad;
  - potongan portal;
  - tabel dan detail balok, kolom, dinding geser, elemen batas, tangga, sambungan kolom lantai menyusul.
- **Cara membuat:** denah dari ekspor DXF BIMCraft (alur 3.11). Teks, as grid, ukuran asosiatif, dan simbol block ditulis
  asli di CADCraft.
- **Syarat:** `cad_cek` 0 pasangan; PDF A3 dicek visual.

### 4.11 Penutupan

- `Ringkasan Tahap 4.md`, `PROGRES.md`, dan `VERIFIKASI.md` (T-65 dan seterusnya, semua Lolos).
- `pytest` lolos dan pindai privasi.
- Label diganti hanya setelah Defsa menyetujui.

## Tambahan atas arahan Defsa: fasad bergaya RS modern dan DED setara profesional

**A. Fasad dan tampilan gedung (dikerjakan bersama 4.9, sebelum model LOD 300 dikunci)**
- **Konsep fasad RS modern tropis:**
  - **menara rawat inap:** sirip vertikal (louver) aluminium, dengan jendela kamar berirama dan bersudut ke sungai;
  - **podium:** dinding tirai kaca di lobi/IGD dan panel ACP/GRC berwarna netral putih-abu dengan aksen hijau
    (warna kesehatan);
  - **kanopi:** kanopi drop-off besar di lobi, kanopi IGD terpisah dan jelas, ramp beratap (LA.4);
  - **atap:** papan nama RS di mahkota menara, tirai pelindung (screen) chiller di atap podium, tepi dek helipad
    terlihat rapi.
- **Iklim Jambi:** pembayang matahari (sun shading) timur-barat, teritis, dan bukaan ±35 % (V4) dipertahankan.
  Bahan tahan lembap. Biaya fasad tetap di dalam pos fasad 3.8 rev B; selisihnya dicatat.
- **Keluaran fasad:**
  - fasad dimodelkan di BIMCraft (dinding tirai, louver, kanopi, panel), terpisah dari struktur tetapi tergabung dalam
    satu model gabungan;
  - render 3D: tampak dari sungai, dari jalan masuk, malam (bila BIMCraft/Blender bisa);
  - gambar tampak empat sisi dan potongan fasad tipikal di CADCraft (KOP_A3).
- **Dampak ke struktur:** beban fasad (louver, dinding tirai, kanopi kantilever) masuk 4.2. Angkur fasad dan balok tepi
  didesain di 4.6. Kanopi drop-off dan kanopi IGD diberi struktur baja atau beton sendiri.
- **Berhenti:** Defsa memilih satu dari dua atau tiga varian fasad yang ditunjukkan dalam render sebelum dikunci.

**B. Gambar struktur setara DED profesional (4.10; DED lengkap seluruh disiplin tetap di Tahap 7)**
- **Isi set gambar struktur:**
  - daftar gambar dan catatan umum struktur (mutu, selimut, panjang penyaluran, sambungan lewatan, standar);
  - denah balok-pelat per lantai dengan penamaan unsur (B1, K1, S1, SW1);
  - denah kolom dan dinding;
  - potongan portal;
  - tabel penulangan balok/kolom/pelat dengan potongan tipikal tumpuan-lapangan;
  - detail HBK, elemen batas dinding, balok kopel, tangga, lubang shaft, kanopi, tumpuan dek helipad, angkur fasad,
    stek kolom lantai menyusul;
  - BBS (daftar bengkok besi) ringkas untuk unsur tipikal.
- **Standar penyajian:**
  - skala baku (1:100 denah, 1:50 potongan, 1:20/1:10 detail);
  - tebal garis dan layer per unsur, block simbol, ukuran asosiatif;
  - nomor revisi di kop KOP_A3, stempel "TIDAK UNTUK KONSTRUKSI";
  - tanpa teks bertumpuk (`cad_cek` 0).
- **Pemeriksaan:** setiap lembar dibandingkan dengan daftar periksa gambar konsultan (kelengkapan ukuran, as, elevasi,
  catatan, rujukan detail) sebelum diserahkan.
- **Untuk Tahap 7:** daftar lembar DED arsitektur (denah, tampak, potongan, detail fasad, finishing), struktur, dan
  koordinasi MEP disusun sekarang sebagai rencana. Gambar struktur Tahap 4 sudah setara DED, jadi Tahap 7 tinggal
  merakit dan menambah disiplin lain.

## Berkas baru dan yang dipakai ulang

- **Skrip baru**, masing-masing dengan uji di `tests/test_tahap4_*.py`:
  - `skrip/tahap4_spektrum.py`
  - `skrip/tahap4_beban.py`
  - `skrip/tahap4_model.py` (openseespy)
  - `skrip/tahap4_cek_pynite.py`
  - `skrip/tahap4_desain_{pelat,balok,kolom,dinding}.py`
  - `skrip/tahap4_bim.py`
  - `skrip/tahap4_gambar.py`
- **Dipakai ulang:**
  - `skrip/tahap3_struktur.py`: `spektrum()`, `beban_helikopter()`, `aksial_kolom()`, `gaya_geser_dasar()`,
    `pynite_portal()` sebagai titik awal dan pembanding;
  - `skrip/bimcraft.py`: `Sesi`, `ke_v011`, `tampilkan`;
  - `skrip/cad_lembar.py` (`Gambar`), `cad_kop.py`, `cad_grafik.py`, `cad_cek.py`;
  - `skrip/format_dokumen.py`;
  - `skrip/tahap2_kelas_situs.py` dan `tahap2_likuifaksi.py` untuk profil Vs dan FS.

## Usulan PR

| PR | Langkah |
|---|---|
| PR-A | 4.0-4.2 (data, spektrum, beban) |
| PR-B | 4.3-4.4 (analisis) |
| PR-C | 4.5-4.8 (desain) |
| PR-D | 4.9-4.11 (BIM, gambar, ringkasan) |

## Verifikasi

- `.venv\Scripts\python.exe -m pytest -q tests` lolos. Uji mencakup:
  - spektrum SE sementara direproduksi (SDS 0,482, SD1 0,524);
  - kantilever atau portal sederhana openseespy = solusi analitik;
  - contoh soal diagram P-M dan Mpr.
- Validasi metode sebelum dipakai:
  - pystrata pada profil homogen = fungsi transfer analitik;
  - model 3D portal 1 bentang = PyNite.
- VERIFIKASI T-65 dan seterusnya dengan toleransi yang ditetapkan sebelum hitung.
- Excel dihitung ulang di Excel = Python.
- `skrip/cad_cek.py <dwg>` 0 pasangan; render PDF dicek inden, tabel, dan freeze panes.
- IFC divalidasi IfcOpenShell; model terbuka di jendela BIMCraft 0.11.0.

## Keputusan yang dibutuhkan dari Defsa di sepanjang jalan

1. **(4.0)** Isi permintaan data ke sesi skenario dan pemasangan pystrata.
2. **(4.1)** Sumber rekaman gempa: unduh sendiri dari PEER/ESM, atau sintetis.
3. **(4.3)** Podium dan menara satu kesatuan atau dilatasi, bila ketidakberaturan atau simpangan menuntut.
4. **(4.5)** Mutu beton dan baja tulangan.
5. **(Tiap langkah)** Persetujuan hasil sebelum lanjut.
