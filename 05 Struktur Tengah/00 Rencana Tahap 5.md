# Rencana Tahap 5: Struktur Tengah (disetujui Defsa 20 Nov 2026)

## Konteks

Tahap 4 struktur atas selesai dan di-merge (PR #26). Evaluasi kunci Tahap 4 di-merge (PR #27): 5 dari 7 butir penuh,
2 sebagian, dan 9 tindak lanjut disetujui Defsa 20 Nov 2026 (`10 Laporan/Evaluasi Kunci Tahap 4.md`).

Lingkup Tahap 5 menurut `00 RANCANGAN.md`: sloof, tie beam, pelat basement. Karena opsi C (3.5) tanpa basement, lingkup
menjadi **struktur di antara kolom LT1 dan kepala pile cap**:
- pelat lantai dasar LT1 (konsep 3.9: tebal 250 mm) dan sloof/tie beam (konsep 400 × 800);
- pit lift (M-3) dan bagian bawah inti;
- penerusan kolom transfer 950/800 dan inti ke kepala pile cap;
- tabel reaksi per kolom untuk Tahap 6.

Pile cap, tiang bor Ø800, gesekan negatif, dan penurunan tetap di Tahap 6.

Tahap 5 juga memuat empat tindak lanjut evaluasi Tahap 4:

| No | Butir | Langkah |
|---|---|---|
| 9 | Telaah data dimulai dengan plot koordinat data owner di atas grid dan rencana tapak | 5.0 |
| 2 | Geser tangki 210 m³ ke atas as balok vs balok transfer 600 × 1.200 + kolom 950/800 (volume, biaya, beban tiang) | 5.1 |
| 3 | Jarak isocenter MRI ke sumbu dan tepi jalur ambulans x 91 (syarat ≥ 12,0 m) | 5.2 |
| 4 | Beban MRI, tulangan non-magnetik radius 1,0 m, getaran lantai, bukaan 2,6 × 2,6 m di pelat LT1 | 5.2-5.3 |
| M-3 | Pit lift +11,25-11,45 di bawah banjir rencana dan tinggi tekan +11,20: kedap dan cek angkat | 5.5 |

Butir lain dari evaluasi tetap di tempatnya: no. 1 chiller dan frekuensi 14,5 Hz (Tahap 7), no. 5 LB-1 (Tahap 7),
no. 6-7 surat owner dan TABG (laporan).

## Cara kerja

- AI menyusun draf atas permintaan Defsa, lalu Defsa memeriksa. Setiap langkah berhenti dengan label **"draf, menunggu
  persetujuan Defsa"**. Defsa boleh menghitung dulu satu unsur contoh (sloof atau pit) sebelum melihat versi AI.
- Pasal SNI dicocokkan ke PDF di `acuan/privat/` (SNI 1726:2019, 1727:2020, 2847:2019, 8460:2017). Pasal yang tidak
  ditemukan ditulis "belum ada di acuan", bukan ditebak. Syarat pabrikan MRI dipakai sebagai [Data owner], bukan SNI.
- Excel dan Word mengikuti `FORMAT LAPORAN DAN EXCEL.md`. Excel dihitung ulang di Excel lalu dicocokkan dengan Python.
- Gambar diambil dari model BIM (arahan Defsa 20 Nov 2026), anotasi di CADCraft dengan `KOP_A3`, `cad_cek` 0 pasangan,
  potongan tanpa poché pejal.
- Kunci di `../02 Siap Terbit/privat/studi-kasus-kunci/` tidak dibuka.
- Model/effort: Opus high (`PERINTAH DAN SKILL.md`); skill defsa-yurinda-skill; modul Pynite, concreteproperties.
- Git: cabang `fitur/tahap-5-struktur-tengah`, pesan Indonesia, merge hanya bila Defsa bilang.
- Cek silang mulai **T-89**; gambar mulai **GS-21**.

## Langkah

| Langkah | Isi | Keluaran (`05 Struktur Tengah/`) |
|---|---|---|
| 5.0 | Persiapan, plot data owner di atas grid dan tapak, telaah data, permintaan data skenario | `5.0 Telaah Data Tahap 5.xlsx`, GS-21 |
| 5.1 | Kajian letak tangki: geser ke atas as balok vs balok/kolom transfer | `5.1 Kajian Letak Tangki.xlsx` |
| 5.2 | MRI: jarak ke jalur ambulans, beban, tulangan non-magnetik, getaran, bukaan | `5.2 Kajian MRI.xlsx` |
| 5.3 | Pelat lantai dasar LT1 (struktural, ditumpu sloof) | `5.3 Desain Pelat LT1.xlsx` |
| 5.4 | Sloof dan tie beam | `5.4 Desain Sloof.xlsx` |
| 5.5 | Pit lift kedap dan cek angkat | `5.5 Desain Pit Lift.xlsx` |
| 5.6 | Penerusan kolom dan inti ke pile cap; tabel reaksi untuk Tahap 6 | `5.6 Reaksi ke Pondasi.xlsx` |
| 5.7 | Model BIMCraft LOD 300 struktur tengah | `model/RSTB-STR-T5-LOD300.bimc/.ifc` |
| 5.8 | Gambar struktur tengah setara DED | `Gambar/DWG/`, PDF A3 |
| 5.9 | Ringkasan Tahap 5, PROGRES, PR | `Ringkasan Tahap 5.md` |

### 5.0 Persiapan dan telaah data (tindak lanjut no. 9)

1. **Plot dulu, baru baca angka.** Semua koordinat data owner Tahap 3-4 diplot di atas grid (as 1-10, A-G, modul 8 m)
   dan rencana tapak (jalan masuk, jalur ambulans x 91, sempadan sungai, gedung utilitas):
   - alat MEP dan medis (`04 Struktur Atas/Data Owner/Data Beban MEP Rinci.xlsx`), termasuk MRI x 77-84 / y 54-60
     dan isocenter (80,5; 57,0);
   - shaft lift L-1..L-7 dengan elevasi pit, shaft SH-1..SH-8 dan lubang LB-1/LB-2;
   - tangki atap x 60-72 / y 67-73 terhadap as balok;
   - lingkaran syarat MRI: 12,0 m (kendaraan), 8,0 m (lift), 1,0 m (tulangan).
   Keluarannya lembar GS-21 (CADCraft) dan tabel "benda di atas atau dekat as" di Excel.
2. **Cek murah tiap data:** satuan, elevasi terhadap peil +12,85 dan halaman +12,05, muka air (+11,20 tinggi tekan
   akuifer desain; banjir rencana dari 3.3), dan pernyataan penyedia yang perlu ditolak (contoh: "pit tidak perlu
   kedap").
3. **Permintaan data ke sesi skenario** (skenario-tahap-3) bila perlu: data Tahap 5 owner (bila ada) dan tanggapan
   owner atas surat teknis Tahap 4. Isi permintaan disetujui Defsa dulu.
4. Daftar acuan yang dibutuhkan dan yang belum ada (mis. pedoman getaran lantai AISC DG11 atau setara, data
   tulangan baja tahan karat/GFRP).

**Berhenti: Defsa menyetujui telaah data dan permintaan data.**

### 5.1 Kajian letak tangki (tindak lanjut no. 2)

Dua opsi dibandingkan pada dasar yang sama (beban tangki 2.168 kN, 30,1 kPa lokal, data 4.0):

| | Opsi A: tetap (keputusan 4.6-4.7) | Opsi B: tangki digeser |
|---|---|---|
| Letak | x 60-72 / y 67-73, reaksi di tengah balok induk x 68 | dudukan tepat di atas as balok/kolom (letak usulan dari plot 5.0) |
| Struktur | balok transfer 600 × 1.200, balok anak tangki 500 × 900, kolom 950/800 menerus LT1-LT3 | balok dan kolom standar (350 × 600, 750), cek ulang 4.5-4.7 lokal |
| Yang dihitung | volume beton dan besi, biaya (harga satuan 3.8) | sama, ditambah biaya pipa dan akibat ke ruang di bawah |
| Beban tiang | reaksi kolom x 60/68/76 ke pile cap | reaksi kolom di letak baru |

- Akibat ke ruang di bawah (LT2), jalur pipa LB-2, dan ruang atap (chiller, tindak lanjut no. 1) dicatat.
- Hasilnya angka: Δ volume (m³), Δ biaya (Rp), Δ reaksi tiang (kN), dan jumlah tiang tambahan di pile cap yang terkena.
- Bila opsi B dipilih, desain 4.5-4.7 yang berubah ditulis ulang lokal (bukan seluruh tahap), model 4.9 dan gambar
  diperbarui di 5.7-5.8.

**Berhenti: Defsa memilih letak tangki. Keputusan ini harus ada sebelum Tahap 6.**

### 5.2 MRI (tindak lanjut no. 3-4)

1. **Jarak isocenter ke jalur ambulans x 91:** dihitung ke sumbu dan ke tepi lajur (lebar dari rencana tapak 3.2),
   dibanding syarat pabrikan ≥ 12,0 m. Juga lift dan bobot imbang (≥ 8,0 m) dan area parkir/bongkar muat.
2. **Bila < 12 m, opsi:**
   - (a) geser ruang MRI ke barat (isocenter x ≤ ±76-79, dicek terhadap zonasi radiologi 3.4);
   - (b) alihkan jalur ambulans ke timur;
   - (c) pelindung magnet tambahan (hanya bila pabrikan mengizinkan; [Data owner]).
   Akibat tiap opsi ke denah, struktur, dan tapak ditulis.
3. **Beban MRI** di pelat LT1: magnet 48,1 kN (4 kaki ±12 kN pada 0,25 × 0,25 m), pelindung baja ±7,3 kN/m' sepanjang
   dinding timur dan utara, sangkar RF 27,5 kN merata, kompresor 3,9 kN (getaran 50 Hz), ditambah beban angkut masuk
   magnet (jalur dan alat angkut).
4. **Tulangan non-magnetik** dalam radius 1,0 m dari isocenter: baja tahan karat atau GFRP; kuat lentur dan sambungan
   ke tulangan biasa dicek. Bila memakai GFRP, acuannya dicari dan bila tidak ada ditulis "belum ada di acuan".
5. **Getaran lantai ≤ 0,5 × 10⁻³ g** [Data owner, dicek di lembar Syarat MRI]: frekuensi alami pelat LT1 dan
   respons terhadap langkah kaki dan kompresor 50 Hz.
6. **Bukaan 2,6 × 2,6 m di pelat LT1:** letak, fungsi, dan tulangan tepi bukaan; masuk desain 5.3.

**Berhenti: Defsa memutuskan letak MRI atau jalur ambulans.**

### 5.3 Pelat lantai dasar LT1

- **Sistem:** pelat struktural ditumpu sloof (tidak bertumpu tanah) karena tanah lunak dan urugan masih turun setelah
  PVD (2.8, 3.3). Celah atau lapisan lunak di bawah pelat dan arah drainasenya dicatat untuk Tahap 6.
- **Beban:** SNI 1727:2020 Tabel 4.3-1 per zona LT1 (UGD, radiologi, rawat jalan, lobi, ruang mesin), alat berat dari
  5.0 (MRI, CT, X-ray, panel), tekanan air ke atas di zona yang lebih rendah (bila ada).
- **Desain:** SNI 2847:2019 Pasal 8 (DDM atau PyNite), tebal 250 mm dicek, kelas paparan S2 + perlindungan asam
  (keputusan 2.7) untuk sisi bawah, selimut sesuai paparan.
- Bagian khusus: zona MRI (5.2), bukaan, tepi pit lift (5.5), lantai turun bila ada.

**Berhenti: Defsa menyetujui pelat LT1.**

### 5.4 Sloof dan tie beam

- **Gaya ikat** antar pile cap menurut SNI 1726:2019 (pasal pengikat pondasi untuk KDS D dan kelas situs SF; nomor
  pasal dicek ke PDF).
- **Lentur:** beban pelat LT1 dan dinding, momen akibat penurunan beda antar pile cap (nilai awal [Asumsi] dari 2.8,
  diperbarui setelah Tahap 6), dan momen kolom yang ditahan sloof bila kepala tiang dianggap sendi.
- **Desain:** SNI 2847:2019 Pasal 9 dan 18.13 (pondasi pada struktur tahan gempa), ukuran konsep 400 × 800 dicek.
- Ujung sloof di kolom transfer 950/800 dan di inti.

**Berhenti: Defsa menyetujui sloof.**

### 5.5 Pit lift kedap (M-3)

- Pernyataan pemasok "pit tidak perlu kedap" ditolak di 4.0: dasar pit +11,25-11,45 di bawah tinggi tekan +11,20
  saat banjir dan di bawah banjir rencana.
- **Cek angkat:** berat pit + pelat + beban mati terhadap gaya angkat air saat muka air tertinggi, FK dari SNI 8460:2017
  (pasal dicek). Bila kurang, tambah tebal atau ikat ke pile cap/tiang.
- **Kedap:** beton kedap (w/c dan kelas paparan), waterstop di sambungan, lapisan kedap, saluran dan pompa sump.
- **Struktur:** dinding dan pelat pit terhadap tekanan tanah + air, reaksi buffer kereta/bobot imbang (data lift
  140/105, 95/72, 168/126 kN).
- Pit L-1..L-4, L-5..L-6, dan L-7 (dasar berbeda) dihitung semua.

**Berhenti: Defsa menyetujui pit lift.**

### 5.6 Penerusan kolom dan inti; reaksi ke pondasi

- Kolom 950/800 (atau ukuran baru bila 5.1 memilih opsi B), kolom biasa, dan dinding inti diteruskan dari LT1 ke kepala
  pile cap: tulangan stek, panjang penyaluran, dan sengkang di daerah sambungan.
- **Tabel reaksi per kolom dan per inti** (D, L, E, kombinasi; K1 dan K2) dari model 3D 4.3 ditambah berat struktur
  tengah. Tabel ini masukan langsung untuk Tahap 6 (jumlah tiang per pile cap).
- Cek silang reaksi total = berat seismik dan beban gravitasi 4.2.

**Berhenti: Defsa menyetujui tabel reaksi.**

### 5.7 Model BIMCraft LOD 300

- Pelat LT1, sloof, pit lift, dan stek kolom ditambahkan ke model 4.9 (`skrip/bimcraft.py`), dengan Pset_RSTB_Umum.
- Clash: pit terhadap sloof, shaft terhadap pelat LT1, bukaan MRI. Volume IFC vs desain (cek silang).

### 5.8 Gambar

- Dari model BIM: denah pelat LT1 dan sloof, potongan pit lift, detail zona MRI, penulangan sloof (tabel), detail
  penerusan kolom transfer. CADCraft `KOP_A3`, mulai GS-21 (GS-21 sudah dipakai lembar plot 5.0 bila disetujui).

### 5.9 Ringkasan dan PR

- `Ringkasan Tahap 5.md`, PROGRES, pytest, pindai privasi, PR satu untuk seluruh Tahap 5 (atau dua: 5.0-5.2 dan 5.3-5.9).

## Cek silang yang direncanakan

Toleransi ditetapkan sebelum hitung dan dicatat di `VERIFIKASI.md`:

| No | Cek | Cara 1 | Cara 2 |
|---|---|---|---|
| T-89 | Jarak MRI ke jalur | koordinat skrip | ukur di DWG CADCraft |
| T-90 | Volume/biaya opsi tangki | skrip | model IFC |
| T-91 | Momen pelat LT1 | DDM | PyNite |
| T-92 | Kapasitas sloof | hitung tangan | concreteproperties |
| T-93 | Gaya angkat pit | hitung tangan | skrip |
| T-94 | Reaksi total ke pondasi | jumlah tabel reaksi | berat 4.2 |
| T-95 | Excel = Python | Excel dihitung ulang | Python |

## Keputusan yang dibutuhkan dari Defsa

1. **(5.0)** Isi permintaan data ke sesi skenario (bila perlu).
2. **(5.1)** Letak tangki: tetap dengan balok/kolom transfer, atau digeser ke atas as balok.
3. **(5.2)** Bila MRI < 12 m dari jalur ambulans: geser MRI, alihkan jalur, atau opsi lain.
4. **(5.2)** Tulangan non-magnetik: baja tahan karat atau GFRP.
5. **(Tiap langkah)** Persetujuan hasil sebelum lanjut.

Lingkup yang lebih kecil bila Defsa ingin cepat: gabungkan 5.7-5.8 ke Tahap 7 (DED) dan tutup Tahap 5 di 5.6.
