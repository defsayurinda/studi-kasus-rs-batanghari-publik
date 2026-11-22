# Progres Studi Kasus Terpadu

Perbarui di akhir setiap sesi: apa yang selesai, posisi sekarang, langkah berikutnya, keputusan baru.

## Posisi sekarang

Tahap 0 dan Tahap 1 **selesai dan disetujui Defsa (19 Nov 2026)**: matriks tanggapan TOR, telaah penyelidikan tanah
(26 temuan, 12 usulan), laporan pendahuluan (`10 Laporan/Laporan Pendahuluan.docx`), dan notulen rapat simulasi.
Semua disusun AI atas permintaan Defsa, lalu dipelajari dan disetujui Defsa (catatan di `DISCLAIMER.md`).
Data penyelidikan tambahan (paket 1-11, simulasi) sudah ada di `01 Penyelidikan Tanah/Penyelidikan Tambahan/`.
Tahap 2 (langkah 2.1-2.7) **selesai dan disetujui Defsa (19 Nov 2026)**, termasuk empat keputusan: tinggi tekan akuifer desain +11,20, parameter desain per unit, kelas situs SF, beton kelas paparan S2 + perlindungan asam. Ringkasan di `02 Olah Data Tanah/Ringkasan Tahap 2.md`.
PR #9 di-merge; kunci Tahap 2 dibuka dan dibandingkan (`10 Laporan/Evaluasi Kunci Tahap 2.md`: 11 dari 15 butir penuh, 4 sebagian).
Tindak lanjut evaluasi selesai di langkah 2.8 (penurunan urugan, PVD, cek fase, artesis, batas muka air gudang;
**disetujui Defsa 19 Nov 2026**). Seluruh gambar GT-01 s.d. GT-15 kini digambar di CADCraft (DWG di
`02 Olah Data Tanah/Gambar/DWG/`) dengan satu kop `KOP_A3` (`templat/KOP A3.dwg`), atas arahan Defsa 19 Nov 2026.
PR #11 (2.8 + CADCraft) dan PR #12 (bersihkan `.bak`) di-merge 19 Nov 2026.
**Tahap 3 desain konsep dimulai (19 Nov 2026), cabang `fitur/tahap-3-konsep`.** Rencana disetujui Defsa: langkah
3.0-3.11 (lihat bagian "Rencana Tahap 3" di bawah). AI mengisi draf atas permintaan Defsa, Defsa memeriksa dan
menyetujui; data/kejadian Tahap 3 dibangkitkan sesi skenario tersegel terpisah. Langkah 3.0 selesai; langkah 3.1
(BEP + template BIMCraft) **disetujui Defsa 19 Nov 2026**; langkah 3.2 (kajian tapak) **disetujui Defsa 19 Nov 2026**; langkah 3.3 (peil, urugan, drainase) **disetujui Defsa 19 Nov 2026** (peil lantai +12,85, halaman +12,05); langkah 3.4 (program ruang, massa, zonasi) **disetujui Defsa 19 Nov 2026**; langkah 3.5 (parkir dan basement) **disetujui Defsa 19 Nov 2026** (opsi C, tanpa basement); langkah 3.6 (grid, sistem struktur, pra-dimensi) **disetujui Defsa 19 Nov 2026: sistem ganda**; langkah 3.7 (pondasi) **disetujui Defsa 19 Nov 2026: opsi A tiang bor Ø800**; langkah 3.8 (perkiraan biaya) **disetujui Defsa 19 Nov 2026**; langkah 3.9 (model BIM LOD 200) **disetujui Defsa 19 Nov 2026**; langkah 3.10 (presentasi dan rapat konsep) **disetujui Defsa 19 Nov 2026**; langkah 3.11 (ringkasan + gambar konsep dari BIMCraft) **disetujui Defsa 19 Nov 2026**. **Tahap 3 selesai.** MCP BIMCraft diperbaiki (server headless + junction
worktree `skrip/siapkan_worktree.ps1`); sambung ulang lewat `/mcp` setelah membuka sesi.
**Tahap 4 struktur atas dimulai (20 Nov 2026), cabang `fitur/tahap-4-struktur-atas`.** Rencana 4.0-4.11
**disetujui Defsa 20 Nov 2026**, dengan tambahan arahan Defsa: fasad bergaya RS modern dan gambar setara DED
profesional (lihat bagian "Rencana Tahap 4"). Langkah 4.0 **disetujui Defsa 20 Nov 2026**: permintaan data dikirim ke sesi skenario, pystrata 0.8.1 terpasang;
Defsa memilih rekaman sintetis (PEER hanya menerima email kampus/perusahaan): 7 rekaman `SIN-01..07` dicocokkan ke MCER batuan SB (rata-rata 0,985-1,032 × target, T-65 Lolos; disetujui Defsa 20 Nov 2026 bersama 4.1). Data skenario Tahap 4 (PR #24, belum di-merge ke `main`) digabung ke cabang Tahap 4.
**Langkah 4.0 telaah data (draf, menunggu persetujuan Defsa)**: `04 Struktur Atas/4.0 Telaah Data Tahap 4.xlsx`
(skrip `tahap4_telaah.py`). Vs/HVSR: V-1 lapisan Vs 167 m/s di 46-47 m palsu (loncatan sakelar pemicu 3,99 ms);
V-2 batuan dasar teknis 33 m penyedia ditolak (SNI 1726 Pasal 6.10.1.1: masukan batuan SB, Tabel 5 v̄s 750-1.500);
V-3 f0 penyedia 2,5 Hz adalah resonansi lempung U4, bukan frekuensi dasar; V-4 H-4 puncak mesin; V-6 lapisan keras
dataran banjir 85 m (bukan rata-rata 70 m yang mencampur perbukitan); V-7 Vs30 156 cocok. MEP: M-1 ringkasan atap
memakai angka lama (benar 2.676 kN, bukan 1.748; tangki 30,1 kPa lokal); M-2 chiller tanpa peredam di atas ruang
LT2/dekat MRI; M-3 pit lift +11,25 di bawah banjir rencana (perlu kedap, Tahap 5); M-8 berat chiller baru dipakai;
M-10 tangki 210 m³. **Keputusan Defsa 20 Nov 2026 (M-4):** evakuasi udara mulai tahap 2; atap tahap 1 di atas LT4 tetap baja ringan
sementara tanpa helipad (owner perlu diberi tahu). **Masih perlu keputusan:** M-5 ruang AHU LT3 harus masuk tahap 1 (AHU OK/ICU/CSSD); M-6 kipas atap di area aman helipad; M-7 jarak
isocenter MRI ke jalur ambulans < 12 m perlu dicek.
**Langkah 4.1 respons spesifik-situs (disetujui Defsa 20 Nov 2026: opsi a)**: `4.1 Respons Spesifik Situs.xlsx`,
GS-01, skrip `tahap4_respons_situs.py` (pystrata EL, 3 zona × U5 utuh/terdegradasi + kepekaan kedalaman keras dan Vs
batuan) dan `tahap4_kolom_ops.py` (openseespy 1D nonlinier, T-66). 2/3 SaM di bawah 80 % SE kecuali T ±1,5-1,8 s;
usulan SDS 0,386 (batas 80 % SE), SD1 0,459, SMS 0,578, SM1 0,688, KDS tetap D. Akibat: plateau -20 % terhadap SE
sementara. Periode situs 0,74-0,77 s cocok HVSR (T-67). Keterbatasan: regangan EL 1,4-2,8 %, rekaman sintetis.
Defsa memilih opsi (a): spektrum spesifik-situs sesuai SNI (SDS 0,386, SD1 0,459); simpangan juga dicek dengan SE di 4.3.
**Langkah 4.2 pembebanan (disetujui Defsa 20 Nov 2026)**: `4.2 Pembebanan.xlsx`, GS-02 (zona beban), skrip
`tahap4_beban.py`. Beban mati tambahan dari SNI 1727 Tabel C3.1-1 (lantai 2,27 kPa + gantung MEP 0,35-0,80; atap 1,69),
beban hidup Tabel 4.3-1 (operasi/lab 2,87; pasien 1,92; koridor 3,83; aula/ruang AHU 4,79 [Asumsi]; helipad 2,87 atau
2 × 50,0 kN), alat MEP dari telaah 4.0 (atap podium 2.676 kN, tangki 30,1 kPa lokal), hujan 0,735 kPa [Asumsi ds + dh].
Berat seismik K2 159.156 kN (12,1 kPa rata-rata), Ta 0,559 s, Cs 0,0827, V 13.164 kN; K1 (tahap 1) W 108.411 kN,
V 8.967 kN. Angin tidak menentukan (V setara gempa ±103 m/s; Buku Peta Angin Indonesia belum ada, V 30 m/s [Asumsi]).
Kombinasi SNI 1726 4.2.2 dengan Ev 0,077D, ρ 1,3 sementara, Ω0 2,5. T-68 (volume beton vs IFC LOD 200, -5,8 %) dan
T-69 (Excel = Python) Lolos. Catatan: void LT3 zonasi 3.4 bertabrakan dengan inti lif (dibereskan di 4.9).
**Langkah 4.3-4.4 analisis 3D (disetujui Defsa 20 Nov 2026)**: `4.3 Analisis Struktur.xlsx`, skrip
`tahap4_model.py` (openseespy: kolom/balok retak, inti kotak Timoshenko, diafragma kaku, jepit di LT1). K2: T1 0,684 s
(X) dan 0,592 s (Y) < Cu Ta 0,782; ragam spektrum 56 % ELF, skala 1,78/1,80 ke V 13.164 kN; simpangan maks 26 %
(pusat massa), 46 % (tepi + torsi tak terduga × Ax) dari 0,010 hsx; θ <= 0,005. Ketidakberaturan: torsi berlebihan 1b
arah Y (1,48; K1 1,51), sudut dalam (V1), geometri vertikal (podium-menara); vertikal 1a/1b/2 dikecualikan Pasal
7.3.2.2. Akibat: ρ 1,3, Ax s.d. 1,41 (K1 1,56), torsi tak terduga di gaya desain, +25 % kolektor, ragam spektrum
wajib. Dinding ujung menara diuji (1,48 → 1,40), tidak diusulkan. Porsi rangka 5-7 % < 25 %: rangka didesain juga untuk
25 % gaya pada model rangka saja (4.6-4.7). Cek silang T-70 s.d. T-72 Lolos. **Keputusan Defsa 20 Nov 2026:** tipe 1b
diterima dengan akibatnya.
**Langkah 4.5 desain pelat (disetujui Defsa 20 Nov 2026, termasuk balok anak tangki dan D13 atap helipad)**: `4.5 Desain Pelat.xlsx`, skrip `tahap4_pelat.py`.
Pelat 200 mm (hmin 178-180 mm, Tabel 8.3.1.2 b, αf 1,96), fc' 30, BjTS 420B, selimut 20 mm; metode desain langsung
SNI 2847 Pasal 8.10 untuk 7 tipe panel (Lo 0,96-4,79 kPa). Tulangan D10-125 s.d. D10-200 (As min 0,0018 Ag), negatif
dalam lajur tengah P4 D13-175; geser satu arah dan pons roda helipad memenuhi. Usulan khusus: pelat 250 mm + balok anak
y 71 di bawah tangki 210 m³ (atas D13-150, bawah D10-125); atap menara tulangan bawah D13-200 dua arah (momen roda
helipad 32,6 kNm/m dari PyNite); tulangan tepi bukaan shaft. T-73 (DDM vs PyNite, -19 %) Lolos.
**Langkah 4.6 desain balok (disetujui Defsa 20 Nov 2026)**: `4.6 Desain Balok.xlsx`, skrip `tahap4_balok.py`,
uji `tests/test_tahap4_balok.py`. Gaya dari model 3D K1 ∪ K2 (gravitasi q L/3 + berat badan + dinding/parapet + beban
titik tangki dan dek helipad; gempa ELF V 13.164 kN, 0,05 Ax, 100/30 %, ρ 1,3, Ev; rangka saja 25 %), momen di muka
kolom. Ukuran kelompok dinaikkan otomatis bila ρ > 0,020 [Asumsi praktis], > 2 lapis, atau batas geser/torsi gagal
(model dihitung ulang dengan ukuran baru, 6 iterasi). Hasil: **semua balok SRPMK tetap 350 × 600** (usulan 400 × 700
podium LT3 tidak perlu: di muka kolom M- 477 kNm → 6D25 dua lapis, ρ 0,016); atas 3D25-6D25/4D29, bawah 2D29-4D22,
sengkang 2-3 kaki D10, s sendi 100-125 mm sepanjang 2h. Balok tepi: torsi kompatibilitas 13-24 kNm > φTth 7,9 →
ditulangi (At/s, Al, tulangan samping). **Temuan tangki:** reaksi balok anak tangki ±1.412 kN (D) jatuh di tengah
balok induk x 68 → balok induk x 68 600 × 1.200 (7D29/15D25, 6 kaki D10-100, Ve 2.069 kN), x 60/76 450 × 800,
y 67 400 × 700; balok anak tangki 500 × 900 (7D29/8D25, 4 kaki D10-100). Rel chiller 300 × 500. Tiang dek helipad
Pu 156 kN di tengah balok atap tepi (roda menentukan). Tambahan berat 159 kN = 0,10 % W (4.2/4.3 tidak diulang).
T-74 (concreteproperties -3,5/-2,3 %), T-75 (koefisien 6.5.2 vs PyNite -11,9 %), T-76 (Excel = Python ≤ 0,13 kN) Lolos.
**Keputusan Defsa 20 Nov 2026:** balok induk transfer 600 × 1.200 di x 68 diterima (tangki tetap, tanpa kolom
tambahan). Seluruh 4.6 disetujui Defsa 20 Nov 2026.
**Langkah 4.7 desain kolom dan HBK (disetujui Defsa 20 Nov 2026)**: `4.7 Desain Kolom dan HBK.xlsx`, skrip
`tahap4_kolom.py`, uji `tests/test_tahap4_kolom.py`. Gaya dari model 3D K1 ∪ K2 dengan ukuran balok 4.6; beban pelat
segitiga sungguhan (q L²/4 per sisi, bukan q L/3) agar aksial tidak berlebih; berat kolom; rangka saja 25 %. Kolom
fc' 35, ukuran 3.6 tetap. P-M dua arah Bresler α = 1, ΣMnc >= 1,2 ΣMnb di semua joint (Mnb dengan tulangan pelat
dalam lebar efektif; tanpa pengecualian joint atap karena SNI 18.7.3.2 tidak memuatnya), Ve kapasitas, Ash Tabel
18.7.5.4, HBK γ 1,0 (balok 350 tidak menutup 3/4 muka kolom). Hasil: K-P LT2 12D25, K-P LT3 24D22, K-P LT4 20D22
(750); K-M LT5-LT6 12D22, K-M atap 24D22 (650; atap dan LT3 ditentukan ΣMnc); sengkang lo D13-100/150 dengan semua batang ditopang,
lo 650-750 mm. **Keputusan Defsa 20 Nov 2026: kolom transfer tangki diperbesar (usulan diterima):** draf awal dengan 750 gagal (x 68 ΣMnc/ΣMnb 0,69, geser joint
1,56; x 60/76 geser joint 1,12). Kolom diperbesar menerus LT1-LT3: x 68 (y 67/75) 950 × 950, x 60/76 (y 67/75)
800 × 800 (`tahap4_model.UKURAN_KOLOM`, kosong di 4.3 sehingga 4.3 tidak berubah); model 3D dihitung ulang. Hasil
kolom transfer: K-T LT2 20D22, K-T LT3 24D29 (800); K-T68 LT2 24D22, K-T68 LT3 36D32 (950). Semua 10 kelompok
memenuhi (geser joint maks 0,99, ΣMnc/ΣMnb min 1,21). T-77 (concreteproperties 0,02 %; Bresler konservatif 21 %),
T-78 (statika 0 %), T-79 (Excel = Python ≤ 0,07) Lolos. Kolom 950/800 perlu diteruskan ke basement dan pondasi
(Tahap 6).
Seluruh 4.7 disetujui Defsa 20 Nov 2026.
Belum: gambar balok dan kolom (4.10).
**Langkah 4.8 dinding geser, balok kopel, tangga, atap (disetujui Defsa 20 Nov 2026)**: `4.8 Desain Dinding Geser,
Tangga, Atap.xlsx`, skrip `tahap4_dinding.py`, uji `tests/test_tahap4_dinding.py` (`tahap4_model.bangun` kini juga
mengembalikan daftar elemen inti, perilaku lama tetap). Gaya dari model 3D K1 ∪ K2 (ukuran balok 4.6, kolom 4.7, ELF
0,05 Ax, 100/30 %, ρ 1,3, Ev); aksial gravitasi inti tributari sendiri (dinding, lajur pelat 1,0 m, tangga) [Asumsi].
Dinding 350, fc' 35; pintu inti [Asumsi]: lif 2 × 1,4 m, tangga 1,2 m, di dinding selatan, tinggi 2,4 m; penampang dan
geser memakai dinding terpotong pintu, sayap efektif 18.10.5.2. Hasil (semua memenuhi, P-M ≤ 1,00, geser ≤ 0,97):
inti lif W-L LT1-LT2 badan D16-150 / D13-200 dua lapis + batas 16D16 di tiap sudut dan sisi pintu; LT3 D16-200/D16-300
+ 4D29; naik ke atas turun sampai D13-300 + 4D16. Inti tangga menara W-TM LT2 D13-150 + 8D19; podium W-TP LT2 D19-300
+ 4D29. **Elemen batas khusus tidak diperlukan**: cara perpindahan c 0,13-0,25 m << c batas 0,97-1,86 m (δu/hw dipakai
0,005); cara tegangan σ maks 6,86 MPa (W-L LT2) < 0,2 fc' 7,0 (tipis). Zona batas dengan ρ > 2,8/fy diberi sengkang
18.10.6.5 (D10/D13-75 s.d. 150 zona sendi). φ geser 0,60 di beberapa tingkat atas (Vn < geser saat Mn). Ve ACI 318-19
(Ωv ωv, informasi; SNI 2847:2019 belum memuatnya) sampai 1,98 φVn: bila SNI baru mengadopsi, tulangan horizontal
LT2-LT5 perlu naik. Balok kopel ambang pintu: lif 1.400 × 1.800 diagonal 9D25 per kelompok (Vu 2.250 kN), tangga menara
1.200 × 2.100 sebagai balok 9D19 + sengkang D13-125, tangga podium diagonal 8D25 (Vu 2.049 kN). Tangga pelat 250 mm
(ℓ/24, ℓ 6,0 m), bawah D13-125, atas D13-275, tanjakan 173-175 mm. Atap sementara tahap 1: hisap 0,60 kPa, tarik angkur
15 kN per kolom ≤ φ 135 kN (4 M16, hef 150). T-80 (concreteproperties -0,16 %), T-81 (PyNite 0 %), T-82 (Excel =
Python ≤ 0,015) Lolos. Yang perlu diputuskan Defsa: letak dan lebar pintu inti (asumsi menentukan balok kopel dan
penampang), dan apakah σ 6,86 MPa yang tipis di bawah 7,0 cukup atau dipasang elemen batas khusus di LT1-LT2 inti lif
sebagai cadangan.
**Keputusan Defsa 20 Nov 2026:** 4.8 disetujui apa adanya: asumsi pintu inti diterima, tanpa elemen batas khusus
(σ 6,86 < 7,0 MPa). Berikutnya 4.9 model BIMCraft LOD 300.
**Langkah 4.9 model BIMCraft LOD 300 (draf, menunggu persetujuan Defsa)**: `04 Struktur Atas/4.9 Model BIM LOD 300.md`,
skrip `tahap4_bim.py`, uji `tests/test_tahap4_bim.py`, model `model/RSTB-STR-T4-LOD300.bimc/.ifc` (+ `-v0.11.bimc`
untuk jendela 0.11.0; agen tidak boleh membuka proyek di jendela Defsa, jadi File > Open manual). Ukuran dari skrip
desain 4.5-4.8: 300 kolom, 510 balok (transfer tangki, anak tangki, 8 rel chiller), 8 pelat, 124 dinding inti dengan
37 pintu, 100 pelat tangga 250, 8 shaft MEP + ruang lif, 36 tumpuan dek helipad HEB 200 [Asumsi]. Pset_RSTB_Umum:
LOD 300, mutu, paket (tahap 1 = K1 3.627 m³; menyusul 1.606 m³). T-83 (hierarki/GlobalId/Pset) dan T-84 (volume IFC
vs desain: 0 / 0 / -0,5 / 0 / 0 %) Lolos; T-85 clash: **SH-4 owner tepat di as 7/C** (kolom + 4 balok LT3), usulan
geser ke x 60,6-63,0, y 43,6-46,0. Void LT3 vs inti lif: void di bawah menara dihapus, taman dalam ke atap V1 barat.
Fasad 3 varian (`model/RSTB-ARS-T4-Fasad-V1..V3.bimc`, render `Gambar/4.9 Fasad V*.png`). Yang perlu diputuskan Defsa:
letak SH-4, varian fasad, penyelesaian void LT3.
**Keputusan Defsa 20 Nov 2026:** 4.9 disetujui. (1) SH-4 digeser ke x 60,6-63,0, y 43,6-46,0 (model dibangun ulang,
T-85 0 clash); (2) fasad **V3** (kaca + overstek 0,9 m utara-selatan, terakota barat-timur), V1/V2 arsip tak dipakai;
(3) void LT3 di bawah menara dihapus, taman dalam ke atap V1 barat (catat di revisi zonasi). Berikutnya 4.10 gambar
DED di CADCraft (fasad V3 dirinci: beban angkur overstek dan terakota ke tepi pelat, cek terhadap asumsi 4.2).
**Langkah 4.10 gambar setara DED + rincian fasad V3 (disetujui Defsa 20 Nov 2026)**: `04 Struktur Atas/4.10 Gambar
DED Struktur Atas.md`, PDF `4.10 Gambar Struktur Atas DED.pdf` (18 lembar GS-03..GS-20), DWG di `Gambar/DWG/`, skrip
`tahap4_gambar_ded.py`, `tahap4_besi.py`, `tahap4_fasad.py` (uji `test_tahap4_gambar_ded.py`, `test_tahap4_besi.py`,
`test_tahap4_fasad.py`), Excel `4.10 Rincian Fasad V3.xlsx`. **Arahan Defsa 20 Nov 2026: gambar diambil dari model BIM
(alur BIM 1D-7D), besi memakai fitur BIMCraft, potongan tidak hitam pejal**: model berbesi
`model/RSTB-STR-T4-LOD350.bimc` (`reinforce`/`rebar`, 143.769 batang ±375 t; 82 MB, tidak di git, dibangun ulang
skrip); denah, potongan, penampang balok/kolom, tangga, dan potongan memanjang diekspor DXF dari model itu, poché pejal
dan goresan teks BIMCraft dibuang (`ezdxf`, ditambah ke requirements), anotasi asli CADCraft; tabel tulangan dari skrip
4.5-4.8. Dinding inti belum dibesi di model (GS-15 digambar CADCraft); pelat LT2/LT3 tanpa mesh di model (batas 1.000
batang per perintah BIMCraft). `cad_cek` 0 pasangan semua DWG (`cad_cek.py` kini membaca skala teks ukur dari
gambar; sebelumnya selalu 1:750). Fasad V3: berat 6.028 kN < asumsi 4.2 14.821 kN (-5,5 % W, 4.2 konservatif);
angkur 4 M16 hef 150 interaksi U-S 0,41, B-T 0,88; Fp 0,87 Wp; Dpl 31 mm (slot ±35). T-86..T-88 Lolos.
**Keputusan Defsa 20 Nov 2026:** torsi keseimbangan terakota pada balok tepi 31,0 kNm (> Tu 4.6) diselesaikan dengan
sengkang balok tepi rapat D10-75/100 (GS-13 tanda *; opsi a), bidang terakota tetap 0,6 m dari as.
Elevasi overstek: detail GS-19 di bawah balok tepi, model 4.9 +3,00; **keputusan Defsa 20 Nov 2026: model
disesuaikan di Tahap 7.** Seluruh 4.10 disetujui Defsa 20 Nov 2026 (kop gambar dibangun ulang).
**Langkah 4.11 ringkasan (disetujui Defsa 20 Nov 2026; Tahap 4 selesai, PR #26 di-merge)**: `04 Struktur Atas/Ringkasan Tahap 4.md` (12 keputusan,
6 temuan, butir yang dibawa ke Tahap 5-7). Pytest 213 lulus dan pindai privasi berkas cabang bersih. Belum ada PR
Tahap 4 yang dibuka (PR-A..C tidak pernah dibuat), jadi PR-D memuat seluruh Tahap 4.0-4.11 dari cabang
`fitur/tahap-4-respons-situs` (termasuk data skenario PR #24). Kunci Tahap 4 dibuka 20 Nov 2026 (cabang `fitur/evaluasi-tahap-4`): `10 Laporan/Evaluasi Kunci Tahap 4.md`, T4-1 s.d.
T4-7 5 penuh, 2 sebagian (T4-1 chiller/frekuensi 14,5 Hz dan letak tangki, T4-3 jarak MRI ke jalur ambulans), D4-K 10/12;
9 tindak lanjut **disetujui Defsa 20 Nov 2026** (no. 8 koreksi Ringkasan M-5 sudah dikerjakan). Berikutnya: Tahap 5
struktur tengah di sesi baru; mulai dengan tindak lanjut no. 2-4 dan 9 (geser tangki vs transfer, MRI, plot data di atas grid).
**Tahap 5 struktur tengah: rencana disetujui Defsa 20 Nov 2026**, cabang
`fitur/tahap-5-struktur-tengah`, berkas `05 Struktur Tengah/00 Rencana Tahap 5.md`. Langkah 5.0-5.9: telaah data
dimulai dengan plot data owner di atas grid dan tapak (no. 9), kajian letak tangki geser vs transfer (no. 2), MRI
jarak ke jalur ambulans x 91/beban/tulangan non-magnetik/getaran/bukaan (no. 3-4), pelat LT1 struktural, sloof, pit
lift kedap (M-3), reaksi ke pondasi untuk Tahap 6, BIM, gambar, ringkasan. Cek silang mulai T-89, gambar GS-21.
Langkah berikutnya: 5.0 telaah data (plot data owner di atas grid dan tapak).

## Rencana Tahap 4 (disetujui Defsa 20 Nov 2026)

Dasar: pembiayaan tahap 1 opsi (a) (PR #22), konsep tidak diulang. Tahap 1 = paket D/E (50 TT di LT4); menara LT5-LT6,
dek parkir, dan isi LT3 menyusul. Struktur menara tetap didesain penuh 6 lantai. Dua konfigurasi dicek: K1 (tahap 1,
menara sampai atap LT4 sementara) dan K2 (akhir, 6 lantai + helipad + dek kantilever); desain memakai selubungnya.
Rencana lengkap: `04 Struktur Atas/00 Rencana Tahap 4.md`.

| Langkah | Isi | Berkas utama (`04 Struktur Atas/`) |
|---|---|---|
| 4.0 | Persiapan; minta data beban MEP rinci dan profil Vs dalam ke sesi skenario; pasang pystrata | `00 Rencana Tahap 4.md`, `4.0 Permintaan Data.md` |
| 4.1 | Respons spesifik-situs kelas SF (pystrata + openseespy 1D, U5 utuh/terdegradasi) | `4.1 Respons Spesifik Situs.xlsx`, GS-01 |
| 4.2 | Pembebanan SNI 1727:2020 (alat RS, MEP, atap podium 158 t, helipad AW139, fasad), kombinasi SNI 1726 | `4.2 Pembebanan.xlsx`, GS-02 |
| 4.3 | Model 3D openseespy, ketidakberaturan podium-menara, simpangan kategori IV, K1 dan K2 | `4.3 Analisis Struktur.xlsx` |
| 4.4 | Cek silang analisis (PyNite, ELF tangan) | `VERIFIKASI.md` |
| 4.5-4.8 | Desain pelat, balok, kolom/HBK, dinding geser/balok kopel, tangga, atap (SNI 2847:2019) | `4.5`-`4.8 *.xlsx` |
| 4.9 | Model BIMCraft LOD 300 + fasad RS modern (2-3 varian, Defsa memilih) | `model/RSTB-STR-T4-LOD300` |
| 4.10 | Gambar struktur setara DED (CADCraft, KOP_A3), tampak dan potongan fasad | `Gambar/DWG/`, PDF A3 |
| 4.11 | Ringkasan Tahap 4, PROGRES, PR | `Ringkasan Tahap 4.md` |

PR yang diusulkan: PR-A (4.0-4.2), PR-B (4.3-4.4), PR-C (4.5-4.8), PR-D (4.9-4.11). Cek silang mulai T-65.

## Pelajaran untuk tahap berikutnya (evaluasi Tahap 0-2)

1. **Hitung akibatnya, bukan hanya parameternya.** Setiap tahap ditutup dengan hitungan "so what" (mis. penurunan
   akibat urugan 0,2-1,2 m), bukan hanya nilai parameter. Ini yang paling sering membuat butir kunci jadi "sebagian".
2. **Cek murah untuk setiap data:** hubungan fase S = w Gs / e0, satuan (SO₃ vs SO₄), tinggi tekan dibanding muka
   tanah (artesis), muka air saat ukur (batimetri), kejanggalan alat (patok bengkok, pipa diperpanjang). Catat semua
   kejanggalan data tambahan secara eksplisit, termasuk yang tidak dipakai (contoh perolehan rendah).
3. **Kuantifikasi syarat konstruksi:** batas yang diusulkan (mis. muka air ≥ +8,6 di sisi gudang) diberi angka dan
   sumber, siap masuk RKS.
4. **Excel dihitung ulang di Excel dan dicocokkan dengan Python** sebelum diserahkan; kesalahan rujukan kolom rumus
   hanya tertangkap dengan cara ini.
5. **Label status jujur:** hasil baru selalu "draf, menunggu persetujuan Defsa" sampai Defsa menyetujui.
6. **Gambar di CADCraft dengan satu kop** (`KOP_A3`), DWG + PDF A3 1:1; render dicek visual sebelum diserahkan.
7. **Setelah merge, tarik `main` ke folder utama** supaya berkas terlihat di folder Defsa (bukan hanya di worktree).

## Rencana Tahap 3 (disetujui Defsa 19 Nov 2026)

| Langkah | Isi | Berkas utama (`03 Desain Konsep/`) |
|---|---|---|
| 3.0 | Tutup 2.8 (label disetujui), minta data skenario Tahap 3, cek acuan yang kurang | - |
| 3.1 | BEP dan template BIM (LOD, penamaan, koordinat BM-1, IFC, IDS) | `3.1 BEP.docx` |
| 3.2 | Aturan tapak dan perizinan (KDB, KLB, KDH, GSB, sempadan sungai konservatif, PBG) | `3.2 Kajian Tapak.xlsx` |
| 3.3 | Peil lantai, urugan, PVD + prapembebanan, drainase | `3.3 Peil dan Urugan.xlsx` |
| 3.4 | Program ruang versi konsultan (150 TT), zonasi, sirkulasi, denah skematik | `3.4 Program Ruang Konsultan.xlsx` |
| 3.5 | Opsi parkir/basement dan metode galian (blow-in, uplift, dinding kedap, gudang ±+8,6) | `3.5 Opsi Basement.xlsx` |
| 3.6 | Grid kolom, dua sistem struktur, pra-dimensi, beda biaya struktur | `3.6 Pra-dimensi.xlsx` |
| 3.7 | Alternatif pondasi (tiang ke U6/U7, NSF, korosi) | `3.7 Alternatif Pondasi.xlsx` |
| 3.8 | Perkiraan biaya per opsi vs pagu Rp 168 M, opsi pengurangan lingkup | `3.8 Perkiraan Biaya.xlsx` |
| 3.9 | Model BIM LOD 200 (IFC) dan validasinya | `model/` |
| 3.10 | Presentasi konsep dan rapat simulasi | notulen [Simulasi AI] |
| 3.11 | Ringkasan Tahap 3, gambar konsep di CADCraft (KOP_A3), PR | `Ringkasan Tahap 3.md` |

PR yang diusulkan: PR-A (3.0-3.3), PR-B (3.4-3.7), PR-C (3.8-3.11). Cek silang mulai T-34 di `VERIFIKASI.md`.

## Selesai

- 20 Nov 2026: sesi skenario tersegel membangkitkan data Tahap 4 (simulasi) atas permintaan 4.0: paket A data beban
  MEP rinci + surat owner 26 Mei 2027 di `04 Struktur Atas/Data Owner/`; paket B bor dalam BH-9 + downhole, HVSR 5 titik,
  dan informasi regional (25 Juni 2027) di `01 Penyelidikan Tanah/Penyelidikan Tambahan/Geofisika Vs Dalam.xlsx`.
  Data wajib ditelaah sebelum dipakai di 4.1-4.2.

- 20 Nov 2026: **keputusan pembiayaan tahap 1 opsi (a)** (laporan antara Subbab 8.2), dipilih Defsa sebagai keputusan
  yayasan dalam simulasi: tahap 1 ±Rp 300-325 M dengan konsep yang ada (paket D/E: 50 TT di LT4, menara LT5-LT6, dek
  parkir, isi LT3 menyusul; V2 bila uji tiang berhasil). Desain konsep tidak diulang. Berikutnya Tahap 4 (struktur
  atas): perlu data beban MEP rinci dari owner (sesi skenario) dan analisis respons spesifik-situs kelas SF.

- 20 Nov 2026, **laporan antara selesai (LA.8)**: Defsa menyetujui LA.2, LA.3, LA.7 dan meminta semua di-merge. PR #19
  (LA.2) dan #21 (LA.3, konflik catatan diselesaikan dengan menyimpan kedua entri) di-merge; `main` digabung ke
  `fitur/laporan-antara`. Label LA.2/LA.3/LA.7 → disetujui Defsa 20 Nov 2026; Excel 3.3 rev B (Excel = Python),
  LA.3 Excel + GK-11 (cad_cek 0) dibangun ulang. Laporan Antara dibangun ulang dengan GK-11 dan konsekuensi gedung
  tahap 2 (21 tindak lanjut terjawab). VERIFIKASI diurutkan T-52 s.d. T-64. `pytest` 140 lolos.

- 19 Nov 2026, laporan antara LA.7 (**disetujui Defsa 20 Nov 2026**): `10 Laporan/Laporan Antara.docx` + PDF (24 hal.):
  ringkasan eksekutif, BAB I-VIII (data baru, parameter tanah desain dan profil per zona, tapak/peil/urugan/drainase/
  tebing, struktur dan helipad, pondasi dan uji tiang, biaya dan paket tahap 1, tanggapan 13 tindak lanjut rapat,
  keputusan yang diminta), lampiran daftar gambar dan ringkasan klaim gudang. Gambar dipotong dari lembar A3. Hasil LA.2
  dan LA.3 dikutip dari PR #19/#21 yang belum di-merge.

- 19 Nov 2026, laporan antara LA.6 (**disetujui Defsa 19 Nov 2026**): kenaikan luas 12.000 → 19.328 m² = owner di atas
  tanah 9.200 + program 898 + faktor bruto 1,07 → 1,45 3.567 + basement 2.800 + dek parkir 247 + sisa massa 2.616.
  Basement penuh (informasi) ±Rp 57,7 M, bersih ±Rp 37,4 M setelah dek parkir tidak perlu. Biaya rev B Rp 460,3 M
  (3.8 + tiang per zona, uji tiang, tebing, penyiapan atap helipad); setelah V1, V3-V7 Rp 413,0 M; potensi V2 → 388,6 M.
  Paket tahap 1 berjenjang A-E; paket terkecil 50 TT (D, menara LT5-LT6 + dek parkir + isi LT3 ditunda) Rp 323 M, dengan
  V2 Rp 299 M, masih Rp 69-93 M di atas ±Rp 230 M karena biaya bersama fondasi/urugan/tebing ±Rp 106 M. Pilihan owner
  dibawa ke laporan antara: pembiayaan ±Rp 300-325 M, tahap 1 diperkecil (desain ulang), atau menunda. T-64.

- 19 Nov 2026, laporan antara LA.5 (**disetujui Defsa 19 Nov 2026**): klaim gudang: uji pompa PW-1 (8 Des 2026, 3 hari)
  menurunkan tinggi tekan pasir U5 di dinding gudang ±0,31-0,38 m (T-63), penurunan lempung ≤ 0,8 mm; patok periode
  pompa ≤ 2,0 mm naik-turun (derau), penurunan baru Feb-Mar setelah surut banjir; retak R-2/R-4 ditambal 2018; pengukur
  retak tidak bergerak. Memo `10 Laporan/Tanggapan Teknis Klaim Gudang Timur.docx`. Tanah gratis: tahap 1 menampung
  ±11.300 m³ (h1 1,05 m × 10.769 m², setelah PVD), sisa ±10.700 m³ di luar lokasi; 12 set uji mutu [Asumsi]. Urugan
  4-5 tahap × 5,1 bulan = 20-26 bulan; gedung bertiang paralel di atas platform tahap 1. Uji tiang SNI 8460 Pasal 9.8:
  6 uji tekan statik (4 terinstrumentasi sebelum konstruksi), beban uji 1.822 kN, 1 lateral, 20 CSL; V2: 3 spun + PDA.

- 19 Nov 2026, laporan antara LA.4 (**disetujui Defsa 19 Nov 2026**): dermaga: beda tinggi IGD - air rendah 8,85 m
  (+12,85 - +4,00), ramp 1:12 106 m tidak muat, diganti ponton + jembatan berengsel 17,4 m + lif brankar di puncak
  tebing x 8-22 dan selasar ke IGD. Helipad AW139: FATO 25,0 m, dengan area aman 33,3 m > lebar menara 24 m, dek
  kantilever 4,7 m tiap sisi; chiller dan tangki air 158 t (25,8 kPa) pindah ke atap podium (1.920 m² ≥ 520 m²).
  Tangki solar tanam FK angkat 0,07 (perlu 13,2 m³ pemberat per tangki), diusulkan di atas tanah dalam tanggul di
  x 114-128, y 40,5-43,5 (+12,85); tangki O2 x 100-104, jarak 10 m. GK-12. Ukuran FATO, ramp, jarak O2 [Asumsi].

- 19 Nov 2026, laporan antara LA.1 (**disetujui Defsa 19 Nov 2026: opsi (a) massa tetap di tempat, tiang per zona**; rencana LA.1-LA.8 disetujui Defsa): profil per
  zona gambut (BH-5 < 0,5 m, BH-7 0,5-2,0 m, BH-3 ≥ 2,0 m). Izin tiang bor Ø800 911 / 895 / 877 kN (NSF statis 452 /
  484 / 487 kN); tiang opsi A 373 → 381 (+±Rp 1,5 M dengan BTL, PPN, kontinjensi). Zona baik (gambut < 1 m, dalam
  amplop) 4.879 m²: letak 3.4 hanya 47 % tapak di zona baik; opsi (b) podium 88 × 40 m di x 46-134, y 26-66 dan GU di
  barat daya 78 %, tetapi Tahap 3.4-3.9 harus diulang. Parkir semua di permukaan kurang ±1.100 m² lahan (KDH tetap),
  jadi gedung parkir tetap perlu; V5 layak dengan parkir permukaan sementara 675 m² (27 mobil). Keputusan Defsa: opsi (a);
  tiang per zona (381) dipakai di LA.6 (biaya 3.8 rev B) dan model. LA.2 (hidrologi) dan LA.3 (tebing) diusulkan sebagai sesi terpisah.

- 19 Nov 2026, laporan antara **LA.3 (disetujui Defsa 20 Nov 2026)**: stabilitas tebing dan saluran pembuang
  (`skrip/la_tebing.py`, `03 Desain Konsep/LA.3 Stabilitas Tebing.xlsx`, GK-11). Bishop + Fellenius, keseimbangan momen
  umum (lingkaran dan lingkaran terpotong bidang licin), pencarian grid. FK izin SNI 8460:2017 Tabel 25 hal. 134 (1,5),
  surut 1,25 [Asumsi], gempa > 1,1 (Pasal 7.5.1.1 hal. 133), kh = 0,5 amax = 0,171 (Pasal 12.2.7 hal. 279). Parameter
  2.4 apa adanya memberi FK < 1 di semua potongan (tebing berdiri), jadi analisis balik dua langkah: su lempung × 1,64
  (P-1, P-3 FK eksisting ≥ 1), bidang licin × 1,40 (P-2 puncak mundur FK 1,0). P-2: statis 1,01/1,01, surut 1,00/0,92,
  gempa 0,72/0,48 (Bishop/Fellenius) → perlu perkuatan. Berm saja tidak efektif (bidang kritis di lereng atas 48°);
  konsep: pelandaian 1V:2H + berm bronjong puncak +6,50 (±6,6 m³/m) + baris tiang/turap di batas lahan geser ≥ 209 kN/m
  (gempa menentukan). Urugan jalur penyangga 0/1/1,5 m: FK 1,70/1,48/1,35 (batas 1,0 m dipertahankan). Podium y 27 tidak
  perlu digeser. Saluran: outlet x 128 (18 m dari zona labil), pipa Ø400, klep +9,70, pompa 3 × 59 L/s ±7,2 kW.
  Catatan sisa: bidang licin di persil [Asumsi sampai jarak -10 m], kajian pasca-likuifaksi U5 dan desain tiang di Tahap 6;
  CPTu/vane di tebing untuk memastikan faktor analisis balik. T-57 s.d. T-60 Lolos; pytest 111 lolos; cad_cek GK-11 0.
- 19 Nov 2026: laporan antara LA.2 (**disetujui Defsa 20 Nov 2026**): `3.3 Peil dan Urugan.xlsx` rev B
  lembar 8 "LP3 dan Uji". Log-Pearson III dua cara (faktor K Kite vs `pearson3` eksak, T-52, ≤ 0,09 %): Q50 +11,48,
  Q100 +11,83 (Gumbel Yn-Sn +11,85/+12,31). Chi-kuadrat dan Smirnov-Kolmogorov menerima ketiga distribusi; Dmaks
  terkecil Gumbel Yn-Sn, jadi Gumbel Yn-Sn tetap dipakai (konservatif, sama dengan Q50 Balai). Peil lantai +12,85
  dan halaman +12,05 memenuhi semua metode (sisa lantai terkecil 0,04 m); peil tidak diubah. Catatan: syarat Cs-Ck
  Gumbel tidak terpenuhi (Cs 0,76, Ck 3,56); LP3 menjadi pembanding. Skrip `tahap3_peil.py --excel`.
- 19 Nov 2026: kunci Tahap 3 dibuka atas permintaan Defsa; hasil di `10 Laporan/Evaluasi Kunci Tahap 3.md` (6 dari 10
  butir penuh, 4 sebagian; D3-K 10/11; rapat R3: 4 penuh, 4 sebagian). Kekurangan utama: podium dan gedung utilitas
  di atas gambut ≥ 1 m (48 % dan 67 % tapak), NSF 3.7 memakai profil BH-5 tanpa gambut, LP3 tidak dihitung, dermaga
  dan FATO belum diukur, klaim gudang belum dijawab dengan data 2.7. Delapan tindak lanjut tambahan masuk laporan antara.
  Tinjauan cabang gambar GT: lolos (104 uji, cad_cek 0), 3 cacat legenda grafik (GT-06, GT-12, GT-15) diminta
  diperbaiki sesi gambar GT sebelum merge.
- 20 Nov 2026: kunci Tahap 4 dibuka atas permintaan Defsa; hasil di `10 Laporan/Evaluasi Kunci Tahap 4.md` (5 dari 7
  butir penuh, 2 sebagian; D4-K 10/12; K4-1 terjawab tanpa dipicu). Kekurangan utama: telaah 4.0 tidak memplot data MEP
  di atas grid (SH-4 baru ketahuan dari clash 4.9), chiller dan MRI berhenti di "ditanyakan", cek frekuensi 14,5 Hz
  tidak dikerjakan, opsi geser tangki tidak dibandingkan dengan balok/kolom transfer. Sembilan tindak lanjut disetujui Defsa.

- 19 Nov 2026, **penutupan Tahap 3** (3.11 disetujui Defsa): pemeriksaan akhir. 46 berkas keluaran 3.1-3.11 lengkap; 12
  berkas uji Tahap 3 ada; T-34 s.d. T-51 semua Lolos; GK-01 s.d. GK-10 `cad_cek` 0 pasangan; 21 angka Ringkasan Tahap 3
  cocok dengan skrip. Diperbaiki: Excel 3.6 dan GK-06 masih berlabel draf (dibangun ulang); model pra-dimensi, LOD 200,
  dan konsep masih menyimpan RSTB_Status 'draf AI' di 442 elemen (dibangun ulang; view POTONGAN A-A dipasang lagi).
  Sisa catatan: 172 jendela tanpa Pset_RSTB_Umum (kategori window belum diberi parameter di template). `pytest` 100 lolos.
  Berikutnya sesuai 00 RANCANGAN: laporan antara (konsep struktur dan pondasi, parameter tanah desain) dengan 13
  tindak lanjut rapat konsep, lalu Tahap 4.

- 19 Nov 2026: penyebab jendela BIMCraft gagal ditemukan: **BIMCraft 0.12.0** berhenti acak 2-19 detik setelah jendela
  muncul (semua backend grafis, pengaturan bawaan maupun kosong, Cowork/GPU 3D dimatikan; Windows 11 build 26300, mirip
  issue #14 di repo BIMCraft). **BIMCraft 0.11.0** (unduhan resmi, izin Defsa) stabil 8/8 percobaan > 25 detik. Jendela kini
  0.11.0 (`BUKA BIMCRAFT.cmd`, MCP `bimcraft-jendela`); model tetap dibangun CLI 0.12.0 lalu diimpor 0.11.0 dari IFC
  (`bimcraft.ke_v011`) karena 0.11.0 hanya membaca .bimc format ≤ 17. `model/RSTB-T3-Konsep-v0.11.bimc` terbuka di
  jendela dengan view "3D KONSEP TENGGARA"; skrip tersambung ke jendela (56 dinding, 172 jendela, 31 ruang).
- 19 Nov 2026: jendela BIMCraft 0.12.0 berhenti sendiri (kode keluar 3) sesaat setelah "window up" di semua backend
  grafis, juga saat dibuka Defsa dengan klik ganda dan dengan folder pengaturan kosong; jadi masalah aplikasi di laptop
  ini, bukan model atau sesi. Jalan lain untuk melihat 3D dan mengedit manual: `BUKA MODEL DI BLENDER.cmd` (Blender +
  Bonsai memuat `model/RSTB-T3-Konsep.ifc`, 1.492 objek; jendela tetap terbuka). Model tetap dibangun di BIMCraft lewat
  CLI; jendela BIMCraft dipakai lagi bila versi baru memperbaikinya.
- 19 Nov 2026, langkah 3.11 (lanjutan, arahan Defsa: model BIMCraft harus utuh, terlihat 3D, bisa dilanjut manual):
  `model/RSTB-T3-Konsep.bimc` = struktur LOD 200 + dinding luar bata 150 + 172 jendela 5,0 × 2,4 m (bukaan ±35 %, V4)
  + 31 ruang + halaman urugan +12,05; view 3D "3D KONSEP TENGGARA" tersimpan; tampak 3D di
  `Gambar/3.11 Model Konsep 3D.png`. `BUKA BIMCRAFT.cmd` kini membuka model ini. Jendela BIMCraft yang diluncurkan dari
  sesi Claude (Bash, Explorer, maupun tab terminal) berhenti sesaat setelah "window up" (log `%APPDATA%\BIMCraft  bimcraft.log`, semua backend grafis); Defsa membuka sendiri dengan klik ganda, lalu skrip membangun langsung di
  jendela itu (`tahap3_model_konsep.bangun` memakai jendela bila aktif).
- 19 Nov 2026, Tahap 3 langkah 3.11 (disetujui Defsa 19 Nov 2026): `03 Desain Konsep/Ringkasan Tahap 3.md`; gambar
  konsep GK-09 denah LT1 dan GK-10 potongan A-A (as D). Alur BIMCraft → CADCraft: tampak model (massa 3.4, struktur
  LOD 200 3.9) diekspor BIMCraft ke DXF (`Gambar/BIM/`), diimpor ke CADCraft. Teks BIMCraft keluar sebagai garis, jadi
  lapisan teks/grid dihapus dan diganti teks, as grid, ukuran asosiatif, titik tinggi asli CADCraft; cad_cek 0
  pasangan. View "POTONGAN A-A" tersimpan di model LOD 200. Catatan alat: ekspor DXF potongan BIMCraft hanya memuat
  unsur terpotong (unsur terlihat hanya di PNG).
- 19 Nov 2026, Tahap 3 langkah 3.10 (disetujui Defsa 19 Nov 2026): presentasi konsep 12 slide (PPTX + PDF, angka
  langsung dari skrip) dan rapat simulasi 5 April 2027. Owner/MK diperankan sesi skenario tersegel
  (`Data Owner/Tanggapan Owner Rapat Konsep (simulasi).md`). Keputusan: tapak 5.383 m², peil +12,85/+12,05 dengan
  ramp beratap, urugan bertahap + PVD (tanah gratis jadi timbunan sementara), opsi C tanpa basement, sistem ganda,
  helipad AW139, tiang bor; **pembiayaan bertahap: target 150 TT tetap, tahap 1 ±Rp 230 M** menunggu bank (Juli 2027);
  V3, V4, V6, V7 disetujui, V1/V2/V5 bersyarat; lelang utama ditunda; kejadian baru: klaim retak gudang timur sejak
  uji pompa Des 2026. 13 tindak lanjut (Tabel 1.2 notulen) menjadi bahan 3.11 dan laporan antara.
- 19 Nov 2026, Tahap 3 langkah 3.9 (disetujui Defsa 19 Nov 2026): model `model/RSTB-STR-T3-LOD200.bimc/.ifc` =
  struktur 3.6 + pelat lantai dasar 250 dan sloof 400 × 800, 102 pile cap, 373 tiang bor Ø800 (kolom bulat di BIMCraft,
  diubah ke IfcPile BORED dengan IfcOpenShell), gedung utilitas + parkir (kolom 600, balok 350 × 600, pelat 200
  [Asumsi]). Validasi IFC lolos (hierarki, elemen di lantai, RSTB_LOD 200, GlobalId unik; B1 kosong sisa template).
  Volume struktur atas cocok 3.6 dalam 0-7,6 %; tiang -0,2 %; pile cap +11 % dan pelat LT1 +18 % dari anggapan 3.8
  (±Rp 2,2 M, di dalam kontinjensi). Model massa 3.4 tetap terpisah (31 IfcSpace). T-50, T-51.
- 19 Nov 2026, Tahap 3 langkah 3.8 (disetujui Defsa 19 Nov 2026): metode Permen PUPR 22/2018 (Pasal 21, 27, 29, 31)
  sebagai pedoman (owner yayasan). Luas 19.328 m² (pagu dasar 12.000 m²). Perkiraan ±Rp 451 M = 2,69 × pagu Rp 168 M
  (rentang 360-551 M); fondasi nyata Rp 90 M jauh di atas porsi standar, struktur sistem ganda masuk porsi 25-35 %.
  Nonstandar 151 % biaya standar (batas gedung negara 150 %). Rekayasa nilai V1-V7 hemat ±Rp 72 M, sisa ±Rp 379 M:
  pagu tetap tidak cukup, owner perlu memilih tambah pagu, bertahap, atau kurangi TT (dibawa ke 3.10). HSBGN Jambi,
  koef lantai, harga satuan [Asumsi] sampai SK wali kota dan survei harga. GK-08; T-48, T-49.
- 19 Nov 2026, Tahap 3 langkah 3.7 (draf AI atas permintaan Defsa): tiang ke pasir padat U7 (±38 m), gesekan U1-U5
  diabaikan, NSF statis dan likuifaksi (SNI 8460 hal. 204, 295). Bor Ø800: Qult 3.407 kN, izin 911 kN. Opsi A bor Ø800
  373 tiang ±Rp 66 M (indeks); C hibrida spun + bor dekat gudang ±Rp 45 M; usulan A,
  C sebagai rekayasa nilai setelah uji tiang. Biaya pondasi besar dibanding pagu: dibawa ke 3.8. GK-07; T-46, T-47.
- 19 Nov 2026, Tahap 3 langkah 3,6 (draf AI atas permintaan Defsa): grid modul 8 m (as 1-10, A-G); menara digeser ke
  x 20-84, y 27-51 (64 × 24 m) agar kolom menerus, Gempa sementara (kelas SE untuk SF): SDS 0,482,
  SD1 0,524, KDS D, Alternatif SRPMK (R 8) vs sistem ganda (R 7); usulan sistem ganda (simpangan
  0,010 hsx, torsi, situs SF), biaya rangka ±16 % lebih tinggi (indeks). Pra-dimensi: pelat 200, balok 350 × 600,
  kolom 750 (podium) / 650 (menara), dinding inti 350. Pu kolom dalam ±6.430 kN, cocok PyNite (T-44). Helipad AW139
  2 × 50 kN. GK-06, model struktur BIMCraft (318 kolom, 90 balok). GK-03 rev C, GK-04 rev B, model massa diperbarui.
- 19 Nov 2026, Tahap 3 langkah 3.5 (draf AI atas permintaan Defsa): basement 1 lapis (dasar galian +8,35) gagal
  blow-in di semua profil (FK 0,97-1,14 < 1,25, SNI 8460 Pasal 10.3.6.7.2) dan uplift Q100 38,8 kPa > berat pelat 14,4.
  Opsi C (disetujui): tanpa basement; gedung utilitas + parkir 4 lantai 34 × 32 m (LT1 utilitas +12,85, sisa utilitas
  di LT2, parkir LT2-LT4 101 mobil) + parkir permukaan: total 129 mobil, 357 motor, 4 ambulans; tapak 4.544 ≤ KDB 5.383, hijau 3.578 ≥ KDH 2.153.
  Massa gedung utilitas di 3.4 (GK-03, model BIM, Excel) sudah diganti. GK-05 di CADCraft; T-43.
- 19 Nov 2026: BIMCraft setara CADCraft: `skrip/bimcraft.py`, `BUKA BIMCRAFT.cmd`; model massa berisi grid, 29 ruang,
  tag, Pset. GUI yang diluncurkan dari sesi Claude ditutup lingkungan, jadi jendela dibuka Defsa.
- 19 Nov 2026, Tahap 3 langkah 3.4 (draf AI atas permintaan Defsa): program ruang versi konsultan 150 TT (owner 138),
  bersih 9.534 m², bruto ±13.800 m² (faktor 1,45 [Asumsi]); utilitas ke gedung utilitas +12,85. Massa: podium 72 × 48 m
  (LT1-LT3), menara rawat inap 64 × 20 m (LT4-LT6) menghadap sungai, gedung utilitas 32 × 24 m 2 lantai; tapak 4.224 m²
  (KDB 5.383), luas lantai 15.744 m² (KLB 25.838); tangga darurat berjarak 24 m (PMK 40/2022 hal. 12). Model massa
  BIMCraft `model/RSTB-ARS-T3-Massa.bimc` + IFC; GK-03 (rencana tapak), GK-04 (zonasi). Kolam retensi dipindah ke luar
  zona labil. Template BIM dan BEP revisi B memakai LT1 +12,85. PMK 40/2022 lampiran berupa pindaian: dibaca dengan
  render halaman; standar luas per ruang tidak ada di acuan.
- 19 Nov 2026. Tahap 3 langkah 3.3 (draf AI atas permintaan Defsa): `3.3 Peil dan Urugan.xlsx` (7 lembar). GK-02 di
  CADCraft (denah grading + potongan A-A). uji `tests/test_tahap3_peil.py`. T-37 s.d. T-40. Nol papan duga 1990-2007 +0.35 m
  dan 1999 dibuang: Q50 +11.85 (= Balai). Q100 +12.31. banjir 2003 +11.65 (bukan +11.20 TOR). Usulan peil
  lantai dasar dan utilitas +12.85. halaman +12.05. Urugan padat 30.358-37.660 m³
  (tawaran owner 22.000 m³ tidak cukup), bertahap ±1,0 m dengan PVD ±5 bulan per tahap; retensi ±650 m³ (Q10).
  Akibat: LT1 template BIM perlu diganti, tinggi tekan desain +11,20 (2.3) ditinjau ulang di Tahap 6.
- 19 Nov 2026: gaya gambar mengikuti contoh Defsa (kop KETERANGAN, Times, hitam-putih); DWG seperti buatan drafter
  (garis ukur asosiatif, block, arsir asosiatif); `skrip/cad_cek.py` memeriksa teks bertumpuk. Gambar dibangun di sesi
  CADCraft tersendiri lalu dibuka di jendela CADCraft (perintah ke jendela bisa salah dokumen bila jendela dipakai).
- 19 Nov 2026: GT-01 s.d. GT-15 digambar ulang sebagai gambar CAD asli dengan kop gaya baru (arahan Defsa: tidak
  lagi isi matplotlib disalin). Modul `skrip/cad_grafik.py` (`LembarCAD`, dipakai lewat `gambar_teknik.Kertas`):
  denah, peta, dan penampang di model space berkoordinat nyata (1 unit = 1 mm) lewat viewport terkunci berskala
  (GT-01/05 1:750, GT-02..04 H 1:500 V 1:250, GT-13 1:400, GT-14 denah 1:300, GT-15 peta 1:1000), dengan grid
  koordinat atau mistar elevasi; grafik di layout dengan bingkai, garis skala, kurva per layer, dan legenda. Arsir unit
  tanah U1-U8, air, dan longsoran di `templat/geoteknik.pat` (legenda konsisten). Cetak hitam-putih: seri yang hanya
  berbeda warna diberi simbol penanda (block `SB-...`); arsir asosiatif; teks di dalam gambar berlatar wipeout,
  label peta digeser bila dicoret garis (wipeout tidak berlaku lewat viewport di CADCraft); `cad_cek.py` 0 pasangan di
  ke-15 DWG. Judul di kop disingkat (maks 20 huruf, `JUDUL_KOP`); judul lengkap di judul
  berlingkaran. Isi teknis dan catatan sama; status DISETUJUI 19 NOV 2026. Bangun ulang:
  `skrip/tahap2_gambar_cad.py` (dibangun di sesi CADCraft sendiri, hasil dibuka di jendela). Uji `tests/test_cad_grafik.py`.

- 19 Nov 2026, Tahap 3 langkah 3.2 (draf AI atas permintaan Defsa): `3.2 Kajian Tapak.xlsx` (6 lembar), GK-01
  di CADCraft, uji `tests/test_tahap3_tapak.py`, T-35/T-36. STA surat sempadan dari sudut tenggara (x = 140 - STA);
  sempadan 6,0-15,5 m dari batas selatan, zona labil x 70-110 (+10 m). Lahan perencanaan 10.766 m²: KDB maks 5.383 m²
  (owner minta 6.300), KLB 25.838 m², KDH 2.153 m², KTB 5.383 m²; amplop menara 7.950 m². Telaah data owner 18 temuan
  untuk 3.3-3.6: Q50 +13,69 dpl = +11,85 lokal (di atas lantai +11,80), nol papan duga 1990-2007 salah 0,35 m,
  utilitas +11,30, urugan di sempadan dilarang, helikopter rencana AW139 (bukan H145). `format_dokumen.hitung_ulang_excel`
  ditambahkan (Excel COM).
- 19 Nov 2026: sesi skenario tersegel membangkitkan data owner dan instansi untuk Tahap 3 (simulasi, 8 Mar 2027) di
  `03 Desain Konsep/Data Owner/`: penetapan garis sempadan sungai, PKKPR, data hidrologi banjir, data MEP awal, dan
  surat owner berisi arahan baru (dengan lampiran surat Kantor SAR). Daftar berkas di `00 Daftar Data Owner Tahap 3.md`.
  Kunci tidak dibuka di sesi kerja. PR #13 di-merge atas perintah Defsa.
- 19 Nov 2026, Tahap 3 langkah 3.1 (draf AI atas permintaan Defsa): `03 Desain Konsep/3.1 BEP.docx` + PDF (BAB I-VII,
  Lampiran A), template `model/RSTB-TPL-Template.bimc` + IFC4 (8 level sementara B1 +8,00 s.d. ATAP +37,60, elevasi
  model = datum lokal; material beton S2; 10 tipe; Pset_RSTB_Umum), uji `tests/test_tahap3_bep.py`, cek silang T-34.
  Keterbatasan BIMCraft 0.12.0: material kolom beton tidak terekspor ke IFC (diisi skrip pasca-ekspor di 3.9).
- 19 Nov 2026: MCP BIMCraft gagal karena worktree tidak punya `alat/` (path relatif) dan `--connect` butuh jendela.
  Server `bimcraft` kini headless, `bimcraft-jendela` untuk GUI; `skrip/siapkan_worktree.ps1` membuat junction.
- 19 Nov 2026: Defsa menyetujui langkah 2.8. Label di Excel 2.8, GT-15 (kop DISETUJUI 19 NOV 2026), Ringkasan Tahap 2,
  Evaluasi Kunci Tahap 2, DISCLAIMER, dan VERIFIKASI T-30 diganti menjadi 'disetujui Defsa 19 Nov 2026'.

- 19 Nov 2026: Tahap 2 langkah 2.8 (penyelesaian setelah kunci dibuka): `2.8 Penurunan dan Pelengkap.xlsx`, GT-15,
  VERIFIKASI T-30 s.d. T-33, uji `tests/test_tahap2_pelengkap.py`. Gambar dipindah ke CADCraft: `skrip/cadcraft.py`
  (klien MCP), `cad_kop.py` (template kop), `cad_render.py` (isi lembar → entitas CAD), `tahap2_gambar_cad.py`.

- 18 Nov 2026: diskusi rancangan, hasilnya di `00 RANCANGAN.md`.
- 18 Nov 2026: workspace dibuat; BIMCraft 0.12.0, Blender 5.2.4 + Bonsai 0.9.0, FreeCAD 1.1.4 (portable di `alat/`),
  QGIS 3.44 LTR dan ProjectLibre (sistem), `.venv` dengan pustaka di `requirements.txt`, 16 skill di `.claude/skills/`,
  dokumen acuan awal di `acuan/`.
- 18 Nov 2026: sesi skenario tersegel (terpisah, tidak dibaca Defsa) membuat dokumen tahap awal:
  `00 Kerangka Acuan/TOR Owner.md`, `00 Kerangka Acuan/Program Ruang.xlsx`,
  `01 Penyelidikan Tanah/` (`Sondir.xlsx`, `Bor dan SPT.xlsx`, `Laboratorium.xlsx`,
  `Ringkasan Laporan Penyelidikan Tanah.md`). Semua data simulasi. Kunci jawaban, pembangkit data, ujinya, dan
  daftar rentang literatur tersimpan di `../02 Siap Terbit/privat/studi-kasus-kunci/` (jangan dibuka di sesi kerja).
- 18 Nov 2026: `00 PANDUAN SINGKAT.pdf` (8 hal., dengan gambar dan tabel skill per tahap) berisi ringkasan proyek, cara memulai, dan saran pengaturan
  model/effort/skill. Sumbernya `00 PANDUAN SINGKAT.html`.
- 18 Nov 2026: uji alat dengan portal kecil, lolos. Rincian di `../80 Coba Open Source/bimcraft-bonsai/HASIL UJI.md`.
- 18 Nov 2026, sesi Tahap 0: belajar konsep telaah KAK dan laporan pendahuluan (dengan latihan KAK sekolah).
  `00 Kerangka Acuan/Matriks Tanggapan TOR.xlsx` berisi 22 butir tanggapan, telaah program ruang, asumsi dan data
  yang diminta, serta daftar acuan normatif. **Draf diisi AI atas permintaan Defsa** (sel hijau), belum disetujui
  Defsa; catat ini di `DISCLAIMER.md` nanti. Kunci jawaban tidak dibuka.
- 19 Nov 2026: nama proyek dan repo ditetapkan. Repo privat `defsayurinda/studi-kasus-rs-batanghari` dibuat;
  `main` di-push, hasil Tahap 0 lewat PR #1.

- 19 Nov 2026: kunci Tahap 0-1 dibuka atas permintaan Defsa; hasil di `10 Laporan/Evaluasi Kunci Tahap 0-1.md`
  (5 dari 9 butir penuh, 4 sebagian; kekurangan utama: kuantifikasi biaya, jarak sempadan, ekstrapolasi akuifer).
  Sesi skenario `skenario-data-tambahan` dimulai untuk membangkitkan data penyelidikan tambahan.
- 19 Nov 2026: Defsa membaca, mempelajari, dan menyetujui seluruh hasil Tahap 0, Tahap 1, laporan pendahuluan, dan
  notulen. Label draf di dokumen diganti menjadi 'disetujui Defsa 19 Nov 2026'.
- 19 Nov 2026: rapat simulasi pembahasan laporan pendahuluan, dijalankan AI atas permintaan Defsa (AI memerankan
  owner dan konsultan). Notulen dan 12 keputusan di `10 Laporan/Notulen Rapat Laporan Pendahuluan (simulasi).docx`
  (berlabel [Simulasi AI]). Inti: kategori IV disetujui, utilitas di atas banjir, 150 TT dengan pagu tetap (opsi
  pengurangan lingkup di Tahap 3), peletakan batu pertama tanpa galian, revisi laporan tanah oleh PT TRG, paket
  penyelidikan 'wajib sebelum desain' disetujui prinsipnya.
- 19 Nov 2026: Defsa memberi format wajib laporan dan Excel (contoh BAB IV laporan KP, Excel IGC 2026, Panduan
  Laporan Mekanika Tanah UNJA). Aturannya di `FORMAT LAPORAN DAN EXCEL.md`, pembantunya `skrip/format_dokumen.py`.
  Matriks Tahap 0, lembar telaah Tahap 1, dan laporan pendahuluan (kini BAB I-VII + Lampiran A-D, 31 hal.) sudah
  dibuat ulang dalam format itu.
- 19 Nov 2026: draf laporan pendahuluan (.docx) disusun AI atas permintaan Defsa dari matriks Tahap 0 dan telaah
  Tahap 1. Jalankan ulang `skrip/laporan_pendahuluan.py` setelah Excel diubah; perbarui daftar isi di Word (Update Field).
- 19 Nov 2026, sesi Tahap 1: belajar konsep telaah (empat pertanyaan: cukup, dipercaya, konsisten, kebutuhan desain;
  SNI 8460:2017 Tabel 2, Gambar 1, Pasal 5.3-5.7; SNI 1726:2019 Pasal 5.1, 6.7). Atas permintaan Defsa, AI mengisi
  draf telaah dan usulan (skrip `skrip/tahap1_lembar_telaah.py` dan `skrip/tahap1_isi_telaah_ai.py`). Kunci jawaban
  tidak dibuka. Catat di `DISCLAIMER.md` nanti.
- 19 Nov 2026: sesi skenario tersegel membangkitkan data simulasi penyelidikan tambahan paket 1-11 (bor + SPT dengan
  energi palu, CPTu + disipasi, bor tangan gambut, MASW + downhole, laboratorium, uji pompa, piezometer sampai Maret
  2027, kimia, survei tebing, survei gudang timur) di `01 Penyelidikan Tanah/Penyelidikan Tambahan/`, berformat wajib.
  Paket 12 (uji beban tiang) menyusul saat konstruksi. Kunci tidak dibuka di sesi kerja.

- 19 Nov 2026, sesi Tahap 2 (SK-02): langkah 2.1 koreksi dan mutu data, **diisi AI atas permintaan Defsa**
  (`02 Olah Data Tanah/2.1 Koreksi Data.xlsx`, skrip `tahap2_koreksi_data.py` dan `tahap2_mutu_contoh.py`, cek silang
  T-06 s.d. T-12). ER desain: BH-4 86 %, BH-5 85 %, BH-6 81 %, rig B 53 %, bor lama 53 % [Asumsi]. N60 204 uji
  (BH-2 12-18 m dan BH-8 1,5 m tidak dipakai). qt CPTu: koreksi lempung lunak ±11-12 %; CPTu-4 0-4,5 m tidak andal;
  lonjakan qc CPTu-1 8,3 m menguatkan kayu terkubur. Mutu contoh (Lunne): buruk BH-2 UD-2 dan BH-7 UD-3; σ'p lab
  BH-5 UD-1 tidak cocok dengan kurva. Kunci jawaban tidak dibuka.

- 19 Nov 2026, sesi Tahap 2: langkah 2.2 stratigrafi, **diisi AI atas permintaan Defsa** (`2.2 Stratigrafi.xlsx`,
  `2.2 Gambar Geoteknik.pdf` 5 lembar A3 berkop: denah, penampang A-A', B-B', C-C', peta tebal organik; cek silang
  T-13, T-14). Delapan unit U1-U8. Lapisan organik U3 tidak ada di selatan (y < ±42 m), menebal ke utara sampai
  3,3-3,7 m (≥ 3 m di sudut utara: cek SF di 2.5). Pasir U5 lebih tinggi di sisi tebing. Defsa minta semua keluaran
  berstandar profesional (gambar berkop, legenda, skala).
- Catatan untuk 2.7: batimetri P-3 diukur 3 Des 2026 (muka air +7,64) tetapi ringkasan memakai muka air acuan +8,05
  (14 Des); periksa konversi elevasi dasar sungai P-3.

- 19 Nov 2026, sesi Tahap 2: langkah 2.3 air tanah, **diisi AI atas permintaan Defsa** (`2.3 Air Tanah.xlsx`,
  `2.3 Gambar Air Tanah.pdf` GT-06 s.d. GT-08, cek silang T-15 s.d. T-17). Akuifer U5 tertekan, k ≈ 8 × 10⁻⁵ m/s,
  S ≈ 1,4 × 10⁻⁴, diisi ulang sungai (tunak ±4 jam). Piezometer pasir mengikuti sungai dengan jeda 3-7 hari.
  Usulan: tinggi tekan akuifer desain +11,20; MAT dangkal 0,3-1,5 m di bawah muka tanah, banjir +11,20. Blow-in
  (SNI 8460 Pasal 10.3.6.7.2, FK ≥ 1,25): galian dasar ±+6 hanya aman Jun-Okt atau dengan sumur pelepas tekanan.
- Catatan untuk 2.4: t50 disipasi CPTu-5 9 m dan CPTu-8 24 m dibaca penyedia dengan u akhir sebagai patokan
  (uji belum setimbang); hitung ulang dengan u0 dari piezometer/hidrostatik.

- 19 Nov 2026, sesi Tahap 2: langkah 2.4 parameter tanah, **diisi AI atas permintaan Defsa** (`2.4 Parameter Tanah.xlsx`,
  `2.4 Gambar Parameter.pdf` GT-09 dan GT-10, cek silang T-18 s.d. T-21). Usulan desain U4: γ 15,2; su = 5,2 + 1,09 z
  kPa (Nkt 12 dari kalibrasi); Cc 0,75, Cr 0,075, e0 2,05; σ'p = σ'v0 + POP (18 kPa di 3 m, 0 di 8,5 m); cv 1,8 dan
  ch 4,5 m²/th; Cα 0,03. U3 gambut: e0 6,0, Cc 3,5, Cα 0,21. U5: (N1)60 12, φ' 33°, k 8 × 10⁻⁵. U6: su 85, σ'p ±400.
  Nilai karakteristik rata-rata ∓ 0,5 sd [Literatur Schneider; belum ada di acuan]. σ'p lab BH-5 UD-1 keliru (44, bukan
  100); t50 penyedia CPTu-5 9 m dan CPTu-8 24 m keliru.

- 19 Nov 2026, sesi Tahap 2: langkah 2.5 kelas situs, **diisi AI atas permintaan Defsa** (`2.5 Kelas Situs.xlsx`,
  `2.5 Gambar Kelas Situs.pdf` GT-11, cek silang T-22 s.d. T-24). SE menurut ketiga parameter (v̄s30 139-171 m/s,
  N̄ 3,5-6,6, s̄u 22-25 kPa) dan Pasal 5.3.2. SF bila U5 mudah likuifaksi (2.6; T gedung > 0,5 s sehingga tanpa
  pengecualian) atau gedung di zona gambut > 3 m (tepi utara, lahan gedung tahap 2). Bacaan downhole 23 m salah.

- 19 Nov 2026, sesi Tahap 2: langkah 2.6 likuifaksi, **diisi AI atas permintaan Defsa** (`2.6 Likuifaksi.xlsx`,
  `2.6 Gambar Likuifaksi.pdf` GT-12, cek silang T-25 s.d. T-27). Atas izin Defsa diunduh Boulanger-Idriss 2014
  (UCD/CGM-14/01) ke `acuan/pustaka/`; PGA Kota Jambi dari Desain Spektra Indonesia PUPR (0,164 g; Ss 0,334; S1 0,264).
  amax = PGAM 0,342 g (FPGA SE 2,08), Mw 7,0 (deagregasi PuSGeN). Pasir U5 MUDAH LIKUIFAKSI di seluruh tapak (FS SPT
  0,25-0,72; CPT 0,22-0,75), tidak peka asumsi. Kelas situs menjadi SF (Ta 0,53-0,82 s > 0,5 s): wajib respons
  spesifik-situs (Tahap 4); tiang menembus U5, downdrag, penyebaran lateral ke sungai (2.7, Tahap 6).

- 19 Nov 2026, sesi Tahap 2: langkah 2.7 kimia, tebing, gudang timur, **diisi AI atas permintaan Defsa**
  (`2.7 Kimia Tebing Gudang.xlsx`, `2.7 Gambar Tebing dan Gudang.pdf` GT-13 dan GT-14, `Ringkasan Tahap 2.md`, cek silang
  T-28 dan T-29). Gambut asam (pH 3,7-4,0) dan bersulfat (S1-S2, T-2 berbeda satuan); P-2 longsoran lama (bidang licin
  BT-2, massa longsoran BT-2K), sungai memotong U5; batimetri P-3 dikoreksi -0,41 m; gudang timur sudah turun
  0,8-1,9 mm/bulan dan miring 1/54 sebelum proyek (catatan kondisi awal untuk klaim).

- 19 Nov 2026: Defsa menyetujui seluruh hasil Tahap 2 dan keempat usulan (tinggi tekan akuifer +11,20; parameter
  desain; kelas situs SF; beton S2 + perlindungan asam). Label draf di Excel, gambar (kop: DISETUJUI 19 NOV 2026),
  ringkasan, dan DISCLAIMER diganti menjadi 'disetujui Defsa 19 Nov 2026'. PR #9 di-merge atas perintah Defsa.

- 19 Nov 2026: kunci Tahap 2 dibuka atas permintaan Defsa; hasil di `10 Laporan/Evaluasi Kunci Tahap 2.md` (11 dari
  15 butir penuh, 4 sebagian; kejanggalan data tambahan 13 dari 16). Kekurangan utama: penurunan akibat urugan +11,50
  belum dihitung (kunci 0,2-1,2 m), e0 BH-8 UD-2 tidak dicek (S = 0,89), kondisi artesis utara tidak dinyatakan, batas
  muka air di sisi gudang belum dikuantifikasi. Hanya bagian Tahap 2 yang dibaca; judul Tahap 3 sempat terlihat.

### Render v2 dipasang (A1-A2, 23 Nov 2026, draf atas delegasi Defsa)

- Hasil Colab (`drive-download-...zip`, R-01..R-08, 3.200 × 1.800 px) menggantikan v1 di `07 DED dan RKS/Render/`; cabang
  `fitur/tahap-7-8-render-v2` di-merge. Dipilih: R-01 (sampul), R-06, R-03, R-04, R-08; tidak: R-02, R-05, R-07.
- `Ringkasan Tahap 7.md` bagian 3 terisi, O-1 ditutup, T-117 dicatat (blend dasar sama, 0 selisih); `7.8 Render.md`
  dan `VERIFIKASI.md` diperbarui. R-01 v2 ada di Laporan Akhir (hal. 6 PDF, dicek PyMuPDF); `test_laporan_akhir.py` 3 lolos.
- Video 6 shot tidak dikejar. Sisa: A3-A7, B, C, D di `SERAH TERIMA.md` bagian 2.

### Sesi 4: GitHub dan situs (23 Nov 2026)

- D1 selesai: `README.md` repo studi kasus (PR #84, merge).
- D3 siap pratinjau: karya `rs-batanghari` di `situs/` (cabang `fitur/karya-rs-batanghari`, commit lokal, belum di-push); aset di `02 Siap Terbit/publik/rs-batanghari/`. Menunggu persetujuan Defsa atas pratinjau sebelum push/merge.
- D4 menunggu situs terbit; D5: PR #31 (data owner Tahap 5) tidak ditutup karena `skrip/tahap5_telaah.py` masih merujuk berkasnya (belum ada di main); rilis v1.0 menunggu keputusan; D2 (visibilitas repo) belum ditanyakan.

## Langkah berikutnya

1. Dokumen acuan: semua SNI v1.0 sudah ada (18 Nov). AHSP memakai SE Dirjen Binkon 47/2026. Harga satuan Jambi tidak
   tersedia daring: rencananya survei harga sendiri (SE 47/2026 Lampiran I) + kalibrasi IKK BPS 2025. Sisa yang perlu
   diunduh lewat browser ada di bagian "Belum ada" `acuan/README.md`.
2. (Selesai 19 Nov) Nama proyek dan repo: `studi-kasus-rs-batanghari`, privat.
3. (Selesai 19 Nov) Tahap 0 dan Tahap 1 disetujui Defsa dan dibandingkan dengan kunci. Tindak lanjut evaluasi
   (revisi laporan pendahuluan, acuan yang perlu diunduh) ada di `10 Laporan/Evaluasi Kunci Tahap 0-1.md`.
4. Data penyelidikan tambahan sedang dibangkitkan sesi skenario (PR terpisah). Setelah di-merge, mulai Tahap 2 di sesi
   baru `SK-02 Olah Data Tanah`; bawa tindak lanjut no. 2-3 dari evaluasi.
5. Celah acuan yang ditemukan di Tahap 0: lampiran PMK 40/2022 berupa gambar (perlu OCR atau dibaca manual);
   peraturan sempadan sungai (Permen PUPR 28/2015), KRIS, heliport, dan proteksi kebakaran belum ada di `acuan/`.
6. Data dan kejadian untuk Tahap 3 (desain konsep) dan seterusnya dibangkitkan saat tahapnya dimulai (minta ke sesi
   skenario). Sebelum memodelkan di Tahap 3: buat BEP dan template BIMCraft.

## Keputusan baru

- 20 Nov 2026, arahan Defsa untuk tampilan akhir RS (berlaku di DED arsitektur Tahap 7): gedung seperti foto acuan
  `acuan/privat/Referensi Fasad RS dari Defsa.jpg` (foto internet, hanya acuan, tidak di-commit): menara blok tinggi
  berpanel putih-abu dengan pita kaca vertikal biru dan dinding tirai kaca, logo "H" biru di puncak menara, podium
  lebar berpanel abu bergaris horizontal, dan **nama rumah sakit terpasang di gedung** (RUMAH SAKIT TEPIAN BATANGHARI).
  Berbeda dari fasad V3 (kaca + overstek U-S, terakota B-T) yang disetujui di 4.9-4.10: perlu diputuskan apakah V3
  diganti. Bila diganti, rincian angkur 4.10 (GS-19) dan sengkang rapat balok tepi (torsi terakota) dihitung ulang;
  panel ringan kemungkinan menghapus kebutuhan sengkang rapat.
  **Keputusan Defsa 20 Nov 2026:** fasad, papan nama, dan lingkungan mengikuti foto; struktur tetap sama. Dibuat model
  fasad V4 `model/RSTB-ARS-T4-Fasad-V4.bimc` (`tahap4_fasad_v4.py`, render `04 Struktur Atas/Gambar/4.10 Fasad V4
  *.png`): panel putih berjendela pita, kaca biru vertikal dan tirai, logo H, nama di mahkota menara, taman, parkir,
  pohon. **Koreksi Defsa 20 Nov 2026: foto dan V4 hanya acuan, fasad V3 tidak diganti sekarang**; yang penting
  arsitektur Tahap 7 dan render akhir bagus, lengkap, dan keren untuk portofolio (syarat di `00 RANCANGAN.md` bagian 3).
  V4 disimpan sebagai purwarupa render. Angkur dan sengkang 4.10 tetap.

- 19 Nov 2026, Tahap 2 (disetujui Defsa): tinggi tekan akuifer U5 desain operasi +11,20; MAT dangkal normal 0,3-1,5 m
  di bawah muka tanah, banjir +11,20; parameter desain per `2.4 Parameter Tanah.xlsx` lembar Ringkasan; kelas situs SF
  (spektrum dari respons spesifik-situs di Tahap 4); beton yang menyentuh gambut/lempung kelas S2 + perlindungan asam.

- 19 Nov 2026, Tahap 1 (disetujui Defsa): laporan tanah tidak dipakai langsung. MAT desain sementara di muka
  tanah; cu, Cc, k laporan tidak dipakai; saran tiang 9 m di zona S-03 dan "dewatering ringan" ditolak. Parameter
  desain ditetapkan di Tahap 2 setelah data tambahan.

- 18 Nov 2026, dari uji alat:
  - Volume RAB dihitung dengan skrip volume bersih (aturan potong di pertemuan), bukan langsung dari tabel BIMCraft,
    karena tumpang tindih tidak dikurangi (3,1% dobel di portal uji).
  - 5D: satu item biaya per kategori elemen; kolom dan balok memakai `GrossVolume`, pelat dan telapak `NetVolume`.
  - 4D: buat kalender kerja proyek (IfcWorkCalendar) sebelum menjadwalkan.
  - Buat tipe pelat sendiri; tipe bawaan BIMCraft tebal 200 mm.
- 18 Nov 2026, dari dokumen acuan:
  - PMK 40/2022 sudah dicabut oleh Permenkes 6/2026. Permenkes 6/2026 memakai klasifikasi pelayanan (dasar, madya,
    utama, paripurna), bukan "tipe C". Istilah dan program ruang RS ditetapkan ulang di Tahap 0.
- 18 Nov 2026, perbaikan alur: Tahap 3 Desain Konsep disisipkan; tahap sesudahnya bergeser (4 struktur atas,
  5 tengah, 6 bawah + basement, 7 DED dan RKS, 8 RAB, 9 jadwal, 10 laporan). RKS masuk v1.0, jenjang laporan
  pendahuluan/antara/akhir mengikuti TOR. Rincian di `00 RANCANGAN.md` bagian 3 dan 9.

## 20 Nov 2026: Tahap 5 langkah 5.0 telaah data (disetujui Defsa 20 Nov 2026)

- `05 Struktur Tengah/5.0 Telaah Data Tahap 5.md` (temuan), `.xlsx` (`skrip/tahap5_telaah.py`, 9 uji), GS-21 plot data owner (`skrip/tahap5_gambar_plot.py`, cad_cek 0).
- Temuan kunci: isocenter MRI 7,5 m ke tepi lajur ambulans x 88 (syarat 12 m); pit lift angkat Q100 14,3 kPa > pelat 0,40 m 9,6 kPa; tangki tepi x 72 di tengah bentang; Ringkasan Atap owner kurang 53%.
- Disetujui Defsa 20 Nov 2026 (temuan dan permintaan data). Langkah berikutnya: 5.1 kajian letak tangki.

## 21 Nov 2026: Tahap 5 langkah 5.1 kajian letak tangki (disetujui Defsa 21 Nov 2026: opsi B)

- `05 Struktur Tengah/5.1 Kajian Letak Tangki.xlsx` dan `.md` (`skrip/tahap5_tangki.py`, 9 uji), cek silang T-90 lolos.
- Opsi A tetap (12 × 6 m, x 60-72 / y 67-73) vs opsi B (8 × 8 × 3,5 m, bay as 7-8 / F-G, tepi di as, pelat dua arah 350).
- B: balok x 68 450 × 800 (A 600 × 1.200), kolom 750 (A 950/800), beton −14,3 m³, besi −1,8 t, tiang −1, biaya −322 juta
  (termasuk TL + PPN), tinggi bersih LT2 3,70 m (A 3,30). Kekurangan B: tangki 3,5 m tepat di tepi utara (fasad);
  kolom B baru dicek aksial (P-M dan kolom kuat balok lemah wajib bila B dipilih).
- `balok_menerus` (tahap4_balok) mendapat argumen opsional `k_rot` (pegas putar ujung); perilaku lama tetap.
- **Keputusan Defsa 21 Nov 2026: opsi B.** P-M kolom 750 dicek di 5.6. Langkah berikutnya: 5.2 MRI.

## 21 Nov 2026: Tahap 5 langkah 5.2 kajian MRI (disetujui Defsa 21 Nov 2026: opsi 2, baja tahan karat)

- `05 Struktur Tengah/5.2 Kajian MRI.xlsx` dan `.md` (`skrip/tahap5_mri.py`, 10 uji), cek silang T-91 lolos (a 0 %, b fn 11,23 vs Rayleigh PyNite 10,05 Hz −10,6 % < 15 %, c 0 %).
- Jarak isocenter ke tepi lajur 7,5 m < 12,0. Opsi 1 geser MRI: isocenter x 76,0 tepat di as 9 (margin 0), sloof as 9 non-magnetik, kolom 9/E di dalam ruang MRI 2,0 m dari isocenter, tumpang tindih radiologi 9 m², koridor magnet 4,5 m. Opsi 2 pindah lajur ke x 92,5-98,5: P4 hilang (76 motor; total 281 < 300, kurang 19). Opsi 3 pelindung: data pabrikan belum ada.
- Beban: kaki magnet 192 kPa (pons rasio 0,03), pelindung 7,17 kN/m', RF 0,655 kPa, L 2,87 kPa (SNI 1727 Tabel 4.3-1).
- Non-magnetik: (a) beton polos tidak sesuai bila LT1 ditumpu sloof (SNI 2847 14.1.3); (b) baja tahan karat A955M diizinkan SNI 2847 20.2.1.3 (pelat 148 kg; opsi 1 279 kg); (c) GFRP tidak diatur SNI, ACI 440 belum ada di acuan.
- Getaran (penyaring SDOF, pedoman belum ada di acuan): fn panel 11,2 Hz; gaya dinamis izin di pelat M-04 41 N, R-06 50 N; dengan pegas 25 mm sumber izin 1,9 kN / 6,6 kN. R-06 wajib di atas pegas.
- Bukaan magnet 2,6 × 2,6 m menurut data owner di DINDING timur (as 10), bukan pelat LT1: tidak bentrok balok (sisi bawah +16,75) dan tidak ada dinding geser di D-E.
- **Keputusan Defsa 21 Nov 2026: opsi 2** (jalur ambulans x 92,5-98,5; MRI tetap) dan **baja tahan karat A955M** di zona 2 × 2 m pelat 9-10/D-E. P4 (76 motor) dicarikan tempat di Tahap 7; R-06 di atas pegas; sambungan isolasi panel MRI, beban transit magnet, pons di 5.3. Langkah berikutnya: 5.3 pelat LT1.

## 21 Nov 2026: Tahap 5 langkah 5.3 desain pelat LT1 (disetujui Defsa 21 Nov 2026: semua usulan AI)

- `05 Struktur Tengah/5.3 Desain Pelat LT1.xlsx` dan `.md` (`skrip/tahap5_pelat_lt1.py`, 14 uji), cek silang T-92 lolos (a 0 %, b PyNite vs Navier 1,07 % < 5 %, c 0 %, d 0 %).
- Temuan: paparan S2 (2.7) menuntut fc' >= 31 MPa dan w/cm <= 0,45 (SNI 2847:2019 Tabel 19.3.2.1); draf memakai fc' 35 untuk pelat LT1 dan sloof.
- PL-1 (Lo 4,79): hmin 177 < 250, D13-200 atas dan bawah di semua lajur. Panel MRI D13-200 cukup (Mu+ 37,3 / phiMn 44,1); transit magnet tidak menentukan, pelat penyebar tidak perlu; pons kaki 0,030, roda 0,052.
- SH-6 menembus LT1 (2,33 m dari isocenter, di luar zona tahan karat): 2 D13 tambahan tiap sisi. Baja tahan karat 144,6 kg (lewatan 580 mm di luar zona).
- Getaran: A monolit 250 fn 11,67 Hz (usulan AI); B 300 resonansi dengan M-01 14,5 Hz; C isolasi menurunkan F izin M-04 ke 15,4 N.
- **Keputusan Defsa 21 Nov 2026:** fc' 35 MPa (S2), selimut bawah 50 mm, panel MRI opsi A monolit 250, beban arsip 7,18 kPa dibatasi pada zonanya (Tahap 7). Langkah berikutnya: 5.4 sloof dan tie beam.

## 21 Nov 2026: Tahap 5 langkah 5.4 desain sloof (disetujui Defsa 21 Nov 2026: semua usulan AI)

- `05 Struktur Tengah/5.4 Desain Sloof.xlsx` dan `.md` (`skrip/tahap5_sloof.py`, 14 uji), cek silang T-93 lolos (a 0 %, b 0,13 %, c 0 %, d 0 %).
- Gaya ikat SNI 1726:2019 7.13.7.2 / 7.13.8.3.5: Ftie 235 kN (K-P), rasio 0,09, tidak menentukan. Serakan lateral: data belum ada.
- Penurunan beda δ 16 mm [Asumsi: Tabel 22, RK IV 0,002L]: M 249 kNm (0,35 Ig); tidak menentukan bila T tidak masuk kombinasi gempa.
- Kepala tiang sendi: momen dasar kolom gempa ke sloof (maks 1.047 kNm kolom tangki). SL-1 400 × 800 tidak memenuhi (ρ 2,88 % > 2,5 %) di ujung kolom tepi tangki; 400 × 900 memenuhi. SL-2, SL-3 400 × 800 memenuhi. Ujung di inti 350 kurang ldh: angkur ke pile cap inti (Tahap 6).
- MRI: muka sloof terdekat 1,8 m dari isocenter (> 1,0 m): baja karbon biasa.
- **Keputusan Defsa 21 Nov 2026:** SL-1 400 × 900 (10 D29 / 8 D25), SL-2 dan SL-3 400 × 800; δ desain 16 mm; T tidak di kombinasi gempa; kepala tiang sendi sampai Tahap 6. Langkah berikutnya: 5.5 pit lift.

## 21 Nov 2026: Tahap 5 langkah 5.5 desain pit lift (disetujui Defsa 21 Nov 2026)

- `05 Struktur Tengah/5.5 Desain Pit Lift.xlsx` dan `.md` (`skrip/tahap5_pit_lift.py`, 14 uji), cek silang T-94 lolos (a 0,00 %, b 3,47 %, c 0,00 %, d 0,00 %).
- Angkat (SNI 8460:2017 9.3.4, Q100 +12,31, pelat 0,40, dinding 0,30): L-1..4 U 565 / W 602 kN, FK utuh 1,07 < 1,1 (pelat lepas 0,66); L-5..6 FK 1,42; L-7 FK 1,37. Tahap konstruksi (pelat saja, muka air +11,20) FK 2,75 / 6,42 / 3,85.
- Opsi A: L-1..4 t >= 0,439 m, pakai 0,45 (+2,0 m3); L-5..6 dan L-7 cukup 0,40. Opsi B: R = 1,5 U - W = 246 kN (L-1..4), As stek 1.040 mm2.
- Struktur L-1..4: pelat atas D13-175, bawah D13-100 (buffer menentukan, pons rasio 0,32); dinding D13-250 luar / D13-275 dalam, horizontal D13-250; spasi kedap 24.3.2.
- L-7 di tengah bay: balok penggantung 400 x 800 (5 D29, beton 5,1 m3) vs pile cap + 2 tiang O800. L-5..6 berimpit sloof as C.
- Belum ada di acuan: kelas W2, pengangkuran izin (SNI 8460 pasal 10), ACI 350 / EN 1992-3, EN 81-20, produk membran/aditif.
- **Keputusan Defsa 21 Nov 2026:** Opsi A (pelat dasar pit L-1..4 0,45 m, FK 1,11; L-5..6 dan L-7 0,40); L-7 ditumpu 2 balok penggantung 400 × 800 ke sloof (5 D29); kedap aditif kristalin + waterstop (spesifikasi produk di RKS Tahap 7). Langkah berikutnya: 5.6 penerusan kolom dan inti ke pile cap, tabel reaksi untuk Tahap 6.

## 21 Nov 2026: Tahap 5 langkah 5.6 penerusan kolom dan inti, reaksi ke pondasi (disetujui Defsa 21 Nov 2026: semua usulan AI)

- `05 Struktur Tengah/5.6 Reaksi ke Pondasi.xlsx` (15 lembar, termasuk "Ringkasan Tahap 6") dan `.md` (`skrip/tahap5_penerusan.py`, 14 uji), cek silang T-95 lolos (a 0,73 / 2,53 / 0,00 %, b 0,00 %, c 0,00 %, d cocok).
- Reaksi per titik (77 titik: kolom LT1 + 7 inti), K1 ∪ K2, kasus E (bukan R); layan SNI 1726:2019 4.2.3, ultimit 4.2.2 dengan Ev dan ρ. Tambahan struktur tengah 58.034 kN (pelat, sloof, stek, pit L-1..4 t 0,45 ke inti, L-7 lewat 2 balok penggantung ke sloof x 36/44).
- Pmax layan terbesar kolom 4/B 5.825 kN; Pu maks inti lift 13.006 kN (Mux 92.865, Muy 125.471 kNm); tidak ada tarik (Pu min 599 kN di 10/G). ΔP sloof (kepala tiang sendi) maks 37,4 kN.
- Stek kolom dan inti ke cap 1.200 cukup (W-TP D29 perlu kait); angkur sloof di inti: kait 90° turun ke cap, ldh 381, T Mpr SL-1 atas 3.468 kN, cap minimum 488 mm.
- Temuan: Σ D inti 4.8 tumpang 6,3 % (konservatif); sloof SL-1 as 6 melintas di dalam inti lift; P-M kolom tangki 750 (janji 5.1) belum dicek. 
- **Keputusan Defsa 21 Nov 2026:** reaksi Tahap 6 dengan ΔP sloof, amplop K1 dan K2, kasus E (bukan R); pile cap inti 1.200 mm; tumpang tributari inti dipertahankan; sloof SL-1 as 6 di dalam inti lift dihapus, kolom (52,35) dan (52,43) masuk pile cap inti; desain sloof tetap 5.4. Langkah berikutnya: tambahan 5.6 P-M kolom tangki opsi B 750-800 (kolom kuat balok lemah, stek), lalu 5.7 model BIMCraft.

## 21 Nov 2026: tambahan 5.6a desain ulang kolom tangki opsi B (disetujui Defsa 21 Nov 2026: 800 seragam)

- `05 Struktur Tengah/5.6a Kolom Tangki Opsi B.xlsx` (9 lembar) dan `.md` (`skrip/tahap5_kolom_tangki.py`, 11 uji), cek silang T-96 lolos (a 0,04 %, b 0,00 % (rumus sama dengan `kl.momen_balok`, bukan pembanding independen), c -1,59 %, d 0,09 %).
- Gaya: semua kombinasi 4.7 (K1 ∪ K2, kasus E dan R), aksial + ΔD opsi B (5.1); momen dari model 4.7 opsi A [Asumsi: konservatif, kolom A lebih kaku]. Balok LT3 diganti balok opsi B (x 68 450 × 800, x 60 400 × 700, y 67, y 75); As pelat tangki 0,35 ikut ΣMnb (lebih ketat dari metode 4.7).
- Kolom 750 (b_B 5.1): LT2 20 D22 lolos (P-M 0,98); LT3 32 D29 (ρ 3,76 %) **gagal**: P-M 1,09, ΣMnc/ΣMnb 1,15 < 1,2, geser joint 1,12. Penyebab: momen model A dari kolom (68;75) 950.
- Kolom 800 seragam: LT2 20 D22 (P-M 0,90), LT3 32 D29 (ρ 3,30 %, P-M 0,99, SCWB 1,27, joint 0,98); sengkang D13-125 (LT2) / D13-150 (LT3), lo 800. Stek ke cap 1.200 cukup (ldh 375, ld 919 mm).
- Dampak ke 5.6: 750 tidak mengubah reaksi; 800 menambah 17,5 kN per kolom, Pu maks +24,5 kN (1,27 %), beton +4,18 m³.
- Yang dipilih Defsa: (1) 800 seragam (usulan AI) atau 750 dengan analisis ulang model B; (2) susunan tulangan; (3) bila 800: perbarui b_B 5.1, Ringkasan Tahap 6, jalankan ulang 5.6. Langkah berikutnya setelah keputusan: 5.7 model BIMCraft.
- **Keputusan Defsa 21 Nov 2026: kolom tangki 800 seragam** (LT2 20 D22 D13-125, LT3 32 D29 D13-150, lo 800). Diterapkan: 5.1 (beton B 78,1 m³, besi 15,6 t, Δ biaya dengan BTL + PPN -291,9 juta), 5.6 (Pu maks kolom tangki 3.795 kN, Σ tambahan 58.040,1 kN, Ringkasan Tahap 6 dibangun ulang), 5.4 (tabel K-T B 800, desain sloof tetap). Langkah berikutnya: 5.7 model BIMCraft.

## 21 Nov 2026: Tahap 5 langkah 5.7 model BIMCraft LOD 300 (disetujui Defsa 21 Nov 2026)

- `model/RSTB-STR-T5-LOD300.bimc/.ifc` (+ `-v0.11.bimc` untuk jendela), `skrip/tahap5_bim.py` (`--bangun`, ±30 s), 9 uji `tests/test_tahap5_bim.py` lolos, md `05 Struktur Tengah/5.7 Model BIMCraft.md`, render `Gambar/5.7 Model LOD 300 3D.png`.
- Model 4.9 + pelat LT1 250 fc' 35 (zona MRI ditandai di Pset), 122 sloof (SL-1 400 × 900, SL-2/SL-3 400 × 800; SL-1 as 6 di inti lift dihapus), pit L-1..4 0,45 / L-5..6 dan L-7 0,40 dengan dinding 0,30, 2 balok penggantung L-7 400 × 800, 70 stek kolom + 28 stek dinding inti ke muka cap +12,05, tangki opsi B (pelat 350, balok x 68 450 × 800, x 60 / y 67 / y 75 400 × 700, 6 kolom 800 LT1-LT3), besi kolom tangki 20 D22 D13-125 / 32 D29 D13-150 (5.244 batang, 10,5 t).
- Validasi IFC lolos (Pset 0 dari 1.306 kurang), T-97 volume IFC vs rencana 0,00 % (pelat -0,40 %), clash dasar 0.
- Asumsi yang perlu dilihat Defsa: balok penggantung L-7 digeser 0,5 m ke muka luar dinding pit (5.6 memakai tepi shaft); pit L-1..4 satu bak 5,2 × 6,2 m; stek tanpa besi di model; ukuran balok opsi B diketik dari tabel 5.1.
- Jendela BIMCraft: agen tidak boleh membuka proyek di jendela; buka manual File > Open `model/RSTB-STR-T5-LOD300-v0.11.bimc`. Langkah berikutnya setelah persetujuan: 5.8 gambar CADCraft.
- **Keputusan Defsa 21 Nov 2026:** model 5.7 disetujui dan di-merge (PR #40), termasuk balok penggantung L-7 digeser 0,5 m. Temuan untuk Tahap 6: model fondasi LOD 200 Tahap 3 punya 30 pasang tiang Ø800 berjarak pusat < 2,0 m (terdekat 0,83 m) di sekitar inti; cap inti dan cap kolom digabung dan jarak minimum tiang dicek di Tahap 6. Langkah berikutnya: 5.8 gambar CADCraft.

## 21 Nov 2026: Tahap 5 langkah 5.8 gambar struktur tengah (disetujui Defsa 21 Nov 2026)

- `skrip/tahap5_gambar_ded.py`, 9 uji `tests/test_tahap5_gambar_ded.py` lolos, md `05 Struktur Tengah/5.8 Gambar Struktur Tengah.md`, PDF `5.8 Gambar Struktur Tengah.pdf` (5 halaman).
- Lembar CADCraft ber-kop KOP_A3: GS-22 denah pelat LT1 dan sloof 1:300 (dari model BIM 5.7), GS-23 potongan pit lift 1:50, GS-24 zona MRI baja tahan karat 1:25, GS-25 sloof 1:20, GS-26 kolom tangki 800 dan stek ke cap 1:25. cad_cek 0 pasangan untuk kelima DWG.
- Perlu dilihat Defsa: sengkang SL-1 400 × 900 dari skrip (tidak ada di tabel 5.4); GS-24 satu skala 1:25; judul kop GS-22 sedikit keluar kotak (kosmetik).
- Langkah berikutnya setelah persetujuan: 5.9 ringkasan Tahap 5.
- **Keputusan Defsa 21 Nov 2026:** GS-22 s.d. GS-26 disetujui (PR #41). Tiga catatan kosmetik diperbaiki di 5.9: judul kop GS-22 "DENAH LT1 DAN SLOOF", stek D22 GS-26 lineweight 0,70, panah utara hanya di GS-22 dan GS-24; kelima lembar dibangun ulang dengan status DISETUJUI 21 NOV 2026.

## 21 Nov 2026: Tahap 5 langkah 5.9 ringkasan (Tahap 5 selesai; ringkasan di-merge atas arahan Defsa)

- `05 Struktur Tengah/Ringkasan Tahap 5.md`: keputusan Defsa 5.0-5.8, angka kunci, cek silang T-90 s.d. T-97 (semua lolos; T-89 jarak MRI di DWG tidak dicatat terpisah, tercakup T-91 a), temuan untuk Tahap 6, acuan yang belum ada, daftar berkas.
- Temuan utama untuk Tahap 6: 30 pasang tiang LOD 200 < 2,0 m di sekitar inti (gabung cap, cek jarak), reaksi 77 titik di lembar "Ringkasan Tahap 6" 5.6, pile cap inti 1.200, kepala tiang sendi, δ 16 mm dibandingkan dengan penurunan Tahap 6.
- **Tahap 5 selesai.** Langkah berikutnya: Tahap 6 pondasi (rencana tahap di sesi baru; mulai dari temuan jarak tiang dan Ringkasan Tahap 6).

## 21 Nov 2026: rencana Tahap 6 pondasi (disetujui Defsa 21 Nov 2026)

- `06 Struktur Bawah dan Basement/00 Rencana Tahap 6.md`: langkah 6.0-6.11 (telaah data, daya dukung tiang tunggal Ø800, gesekan negatif urugan + likuifaksi U5, tata letak tiang dan gabung cap inti, tebing dan serakan lateral, tiang lateral sendi/jepit, penurunan vs δ 16 mm, desain tiang dan pile cap, uji tiang dan pelaksanaan, model LOD 300, gambar, ringkasan).
- Bawaan Tahap 5 B-1..B-8 dipetakan ke langkah; Defsa menghitung tiang tunggal (6.1) dan cap inti (6.3) dulu; cek silang T-98..T-107; gambar GS-27..GS-32, tebing GT-16; 8 keputusan Defsa (termasuk lingkup gedung utilitas + parkir).
- Langkah berikutnya: 6.0 telaah data Tahap 6 (plot tiang LOD 200 + 77 reaksi, GS-27, permintaan data uji tiang).

## 21 Nov 2026: Tahap 6 langkah 6.0 telaah data (disetujui Defsa 21 Nov 2026)

- `06 Struktur Bawah dan Basement/6.0 Telaah Data Tahap 6.xlsx` (9 lembar) dan `.md`, `skrip/tahap6_telaah.py`, 7 uji `tests/test_tahap6_telaah.py` lolos, GS-27 telaah data pondasi 1:600 (CADCraft KOP_A3, cad_cek 0), PDF `6.0 Gambar Telaah Data.pdf`.
- 373 tiang (305 utama, 68 utilitas + parkir); 39 pasang < 2,4 m (3D), 30 < 2,0 m, terdekat 0,83 m, semuanya antar cap berbeda: 14 cap kolom harus digabung ke cap inti (zona G1-G14). 77 reaksi cocok ke kelompok tiang (selisih 0,00 m); kelompok utilitas tanpa reaksi.
- Σ Pmax layan 275.232 kN vs Σ (D+L) 5.6 274.984 kN (0,09 %). Kepala tiang +10,85; air desain +11,20 (0,35 m di atas), Q50 +11,85, Q100 +12,31 di atas muka cap: gaya angkat cap 3,4-14,3 kPa vs berat cap 28,3 kPa.
- T-98 lolos (IFC 373 IfcPile, DWG; jumlah dan pasangan 0 selisih, jarak terdekat ≤ 0,1 mm).
- Temuan 5.6: lembar Tambahan per Titik, 6 baris kolom tangki opsi B (7-9/F-G) Σ kategori ≠ D + L (Σ 58.040,1 vs D + L 57.800,6 kN); reaksi Tahap 6 memakai D + L.
- Acuan belum ada: pedoman serakan lateral, Fellenius (bidang netral). Sisa penurunan setelah PVD dihitung ulang di 6.6.
- **Keputusan Defsa 21 Nov 2026:** telaah 6.0 dan usulan AI disetujui: isi permintaan data uji tiang + pemantauan urugan (dikirim ke sesi skenario sebelum 6.1), gedung utilitas + parkir ikut Tahap 6 dengan beban 3.7 [Asumsi] sampai ada reaksi, 14 cap kolom digabung ke cap inti (6.3). Keluaran dibangun ulang berstatus disetujui. Langkah berikutnya: kirim permintaan data, lalu 6.1 (Defsa menghitung tiang tunggal Ø800 dulu).

## 21 Nov 2026: data simulasi uji tiang dan pemantauan untuk Tahap 6 (sesi skenario)

- Permintaan data 6.0 butir 1-4 + data gudang dijawab sesi skenario: `06 Struktur Bawah dan Basement/Data Uji/`
  (`00 Daftar Data Uji Tahap 6.md`, `Uji Beban Statis Tiang.xlsx`, `PDA dan Integritas Tiang.xlsx`,
  `Pemantauan Urugan dan PVD.xlsx`, `Data Gudang Timur dari Pemilik.xlsx`), tanggal simulasi 26 Juli 2027.
- Isi: 4 tiang uji Ø800 (TP-1/TP-2 utara, TP-3/TP-4 selatan) siklik sampai 200 % × 911 kN, regangan 7 level di TP-1/TP-3;
  PDA 2 tiang uji + 8 tiang kerja, PIT 40, CSL 24, silinder; 11 pelat penurunan, 6 piezometer U4/U5, 3 inklinometer
  (tebing P-1, P-2, batas gudang) 26 Feb-20 Jul 2027; beban dan cerucuk gudang dari pemilik.
- Laporan faktual tanpa interpretasi; Defsa menelaah sendiri sebelum dipakai di 6.1. Langkah berikutnya: 6.1 (Defsa
  menghitung tiang tunggal Ø800 dulu, lalu memakai data uji ini untuk cek).
- **Visual model analisis Tahap 4 (21 Nov 2026, draf):** `skrip/tahap4_visual_model.py` membuat 8 PNG 3D (pyvista, ≥3000 px) di `04 Struktur Atas/Gambar/Analisis 3D/`: model, ragam 1-3 (T 0,684/0,592/0,512 s, sama dengan 4.3), deformasi gempa statik X/Y, momen dan geser portal y = 27 m. Uji: `tests/test_tahap4_visual_model.py`.

## 21 Nov 2026: Tahap 6 langkah 6.1 daya dukung tiang tunggal Ø800 (disetujui Defsa 21 Nov 2026)

- Permintaan data uji tiang + pemantauan dikirim manual oleh Defsa ke sesi skenario (`6.1 Permintaan Data.md`).
- Defsa meminta AI menghitung langsung. `skrip/tahap6_tiang_tunggal.py`, 8 uji `tests/test_tahap6_tiang_tunggal.py` lolos, `6.1 Daya Dukung Tiang.xlsx` + `.md`, T-99 di VERIFIKASI (a 0,00003 %, b 0,0 %, c sebaran 9,7 %).
- U1-U4 tidak menyumbang tahanan, U5 hanya kasus statis. Qult statis/gempa GEC10: selatan 4.770/3.294 kN, utara 4.565/3.305 kN; izin tanpa NSF 1.777-2.171 kN; izin setara Tahap 3 (dikurangi NSF) 1.283-1.555 kN ≥ 911 kN. Setelan Tahap 3 mereproduksi 910,8 kN.
- Usulan panjang sementara: selatan 37,5 m, utara 36,5 m (Tahap 3: 38,45 / 38,24); penentu sebenarnya NSF 6.2.
- Perlu diputuskan Defsa: metode utama, perlakuan U5, panjang tiang (tetap 38,45 atau memendek), FK tarik 2,5/1,1 [Asumsi].
- **Keputusan Defsa 21 Nov 2026:** draf 6.1 disetujui (metode A GEC10 utama, U5 hanya statis, FK tarik 2,5/1,1); panjang tiang tetap 38,45 m sampai gesekan negatif 6.2 dan uji beban awal. Langkah berikutnya: 6.2 gesekan negatif (urugan + PVD dan likuifaksi U5; acuan Fellenius belum ada).
- Data uji tiang dari sesi skenario (`Data Uji/`, PR #46) masuk setelah 6.1 disusun dan belum dipakai; dicocokkan ke Qult 6.1 di awal 6.2 (atau 6.8).

## 21 Nov 2026: Tahap 6 langkah 6.2 gesekan negatif dan bidang netral (disetujui Defsa 21 Nov 2026)

- `skrip/tahap6_nsf.py`, 8 uji `tests/test_tahap6_nsf.py`, `6.2 Gesekan Negatif.xlsx` + `.md`, kurva A/B selatan dan utara (`Gambar/`), T-100 di VERIFIKASI (lolos; CAPWAP 23 % dari batas 25 %).
- Acuan: SNI 8460 Pasal 9.7.2.1 hal. 204 (seret sebagai beban), GEC10 §10.6.2 hal. 10-47/48 (bidang netral), §10.7 hal. 10-52 (seret pasca-likuifaksi 50 % β), NHI-06-089 §9.8 dan Davisson hal. 275-276. GEC12 dan Fellenius belum ada di acuan/.
- Bidang netral (Q 911 kN): selatan -13,71 / -16,72 m (statis / pasca-likuifaksi), utara -14,00 / -16,50 m; Q + Qn ±2.930-3.000 kN ≤ 6.665 kN beton polos (f'c 30 [Asumsi]).
- **Keputusan Defsa 21 Nov 2026:** izin akhir = min(SNI dengan Qn lapisan menurun saja; GEC10 Qult/2,5). Qn bidang netral hanya untuk cek struktur dan layan (mengurangkannya dari Qult adalah hitungan ganda). Panjang tetap 38,45 m.
- Temuan: penurunan tiang di bidang netral utara ±20 mm > δ 16 mm (selatan ±13 mm), karena sisa penurunan setelah tiang besar (utara 874, selatan 271 mm; urugan ke +11,50 sesudah tiang). Dibawa ke 6.6 (pra-beban, perpanjang tiang, atau terima). Uji 200 % hanya membuktikan FK 2,0; FK 2,5 perlu uji ≥ 2.278 kN (6.8). Anomali: T218 PDA, TP-2 CSL dasar, SPL-05 dipasang ulang 12 Mei (offset 239 mm [Asumsi]).
- Langkah berikutnya: 6.3 jumlah dan tata letak tiang, gabung cap inti (Defsa menghitung cap inti dulu).

## 21 Nov 2026: Tahap 6 langkah 6.3 jumlah dan tata letak tiang (disetujui Defsa 21 Nov 2026)

- `skrip/tahap6_tata_letak.py`, 8 uji `tests/test_tahap6_tata_letak.py`, `6.3 Tata Letak Tiang.xlsx` (cap inti dengan rumus hidup) + `.md`, T-101 di VERIFIKASI (lolos).
- Gedung utama: 244 tiang (cap kolom 152 vs 197 Tahap 3; tujuh cap inti 92 vs 108) vs 305 Tahap 3, selisih -61 tiang dan -2.345 m panjang; utilitas 68 tidak berubah. Izin 6.2 (selatan 1.583, utara/tengah 1.443 kN) membuat cap kolom lebih sedikit; gempa inti yang menentukan cap inti.
- Temuan 1.710 kN: INTI-LIF masuk Cap E (INTI-LIF + 6/B + 6/C, 32 tiang 4 x 8, Pmax 1.560 kN/tiang). Varian (b) selatan 40,00 m menurunkan n layan (14 ke 13) tetapi jumlah akhir tetap 244 (gempa inti menentukan), +181 m panjang.
- Gempa inti: 100 % + 30 % (SNI 1726 Pasal 7.5.3 a) dengan Pu maks (konservatif); 100 % + 100 % serentak memberi 113 tiang inti dan cap C dan E bentrok. Jarak cap inti 2,4/3,6/4,8 m; η blok 1,0 (NHI-06-089 Pers. 9-18), Converse-Labarre 0,67-0,88 (pembanding). Tengah memakai sifat utara [Asumsi].
- **Keputusan Defsa 21 Nov 2026:** draf 6.3 disetujui: gempa inti 100 % + 30 %, jarak cap inti 2,4/3,6/4,8 m, varian (a) tambah tiang (panjang tetap 38,45 m, 244 tiang gedung utama). Pu/Mu per kombinasi gempa dari 5.6 diminta bila ada (sekarang Pu maks, konservatif). Langkah berikutnya: 6.4 stabilitas tebing sungai dan serakan lateral.

## 21 Nov 2026: Tahap 6 langkah 6.4 stabilitas tebing P-2 dan serakan lateral (disetujui Defsa 21 Nov 2026)

- Defsa meminta AI menghitung (lembar data `6.4 Lembar Isian Tebing.md`). `skrip/tahap6_tebing.py`, 8 uji `tests/test_tahap6_tebing.py`, `6.4 Stabilitas Tebing.xlsx` + `.md`, gambar bidang kritis dan profil serakan (`Gambar/`), T-102 di VERIFIKASI (GAGAL butir a: Bishop vs Spencer 6,94 % > 5 % hanya kasus kh 50 % tanpa perkuatan, Spencer lebih tinggi; pyslope 0,03 %, Excel 0,007 %).
- Puncak P-2 4,5 m dari batas lahan (bukan 6,5 m, survei Feb 2027). INC-1 bergerak 18,6 mm (0,18 mm/hari) di +5,60, cocok dengan bidang licin +5,43. Garis tiang terdekat: baris selatan gedung utama y 26,3 m.
- FK persil Bishop (berm + pelandaian LA.3): muka rendah +4,00 1,22, surut 1,22, gempa 0,74, kh 50 % 1,03, pasca-likuifaksi (Sr U5 14,8 kPa, Idriss-Boulanger 2008) 0,68; tidak ada yang memenuhi. Geser perlu di batas lahan 24 / 3 / 209 / 29 / 790 kN/m. Saran: berm + pelandaian + baris tiang bor Ø600 batas lahan (@0,96 m atau dua baris, ±9,6 m); dolken tidak cukup; geser garis tiang gedung tidak menolong.
- Temuan: bidang pasca-likuifaksi masuk ±34 m ke persil, melewati baris tiang y 26,3 (perbaikan tanah U5 di jalur tebing atau tiang gedung menahan beban kinematik); berm LA.3 FK 0,95 di muka sungai saat muka rendah (bentuk berm perlu diubah). GeoFEM3D tidak dipakai (belum bisa lereng). Acuan Youd, Zhang, Idriss-Boulanger, Spencer belum ada di acuan/ (label [Literatur]).
- Serakan lateral di garis tiang: Youd 2002 0,19 m (R 50 km [Asumsi], sangat peka R), Zhang 2004 4,58 m (LDI 2,88 m); profil Zhang +1,01 ke atas 4,58 m, -2,0 3,02 m, -6,0 1,20 m, -9,18 ke bawah 0.
- **Keputusan Defsa 21 Nov 2026:** draf 6.4 disetujui; profil Zhang dipakai sebagai beban kinematik 6.5, Youd sebagai batas bawah. Langkah berikutnya: 6.5 tiang lateral dan kepala tiang (beban inersia + kinematik Zhang, p-y openpile, sendi vs jepit).

## 22 Nov 2026: Tahap 6 langkah 6.5 tiang lateral Ø800 dan kepala tiang (disetujui Defsa 22 Nov 2026)

- Defsa meminta AI menghitung (lembar data `6.5 Lembar Isian Lateral.md`). `skrip/tahap6_lateral.py` (balok elemen hingga 800 elemen di atas pegas p-y nonlinier dengan perpindahan tanah bebas; cache `%TEMP%\tahap6_lateral_hasil.pkl`, `TAHAP6_LATERAL_CACHE=1`), 8 uji `tests/test_tahap6_lateral.py`, `6.5 Tiang Lateral.xlsx` + `.md`, PNG profil inersia dan kinematik (`Gambar/`), T-103 di VERIFIKASI (lolos: openpile 3,21 %, pembanding orde 12,8 %, Excel 0,00 %).
- Selatan, EI 0,5 EI bruto, U5 pengali p 0,1: inersia X 53,95 kN/tiang sendi y0 15,3 mm, M maks 135 kNm (+6,43); jepit y0 3,8 mm, M kepala 137 kNm. Utara sendi 26,0 mm / 177 kNm. φMn Ø800 16D25 [Asumsi] pada P 1.560 kN = 1.122 kNm.
- Kinematik: Youd 0,19 m M maks 966 kNm (rasio 0,86), V 366 kN; Zhang 4,58 m M maks ±9.500 kNm (rasio 8,4-8,5), V ±2.000-2.200 kN di U6 tepat di bawah U5 (±-10 m). Batas perpindahan tanah yang tertahan 0,22 m. Tiang Ø800 tidak menahan Zhang: perbaikan tanah U5 di jalur tebing atau tiang batas Ø600 (6.4) menjadi syarat.
- openpile 0.3.3 tidak cocok dengan venv (pydantic 2, numpy 2.5): skrip memasang pustaka lama ke `%TEMP%\pydantic1` dan menjalankan pembanding di subproses; salinan openpile ditambal (pu Matlock 9 su D sesuai GEC9 Pers. A-2 hal. 222, kurva 60 titik).
- **Keputusan Defsa 22 Nov 2026:** draf 6.5 disetujui; kepala tiang sendi (sloof 5.4 tidak dicek ulang, B-4 tutup); U5 pengali p 0,1. Masih terbuka: penanganan serakan (perbaikan tanah U5 / tiang batas Ø600), dibawa ke perkuatan tebing dan 6.7.
- Langkah berikutnya: 6.6 penurunan kelompok dan penurunan beda (B-5).

## 22 Nov 2026: Tahap 6 langkah 6.6 penurunan kelompok dan penurunan beda (disetujui Defsa 22 Nov 2026: varian d)

- Defsa meminta AI menghitung (lembar data `6.6 Lembar Isian Penurunan.md`). `skrip/tahap6_penurunan.py` (+ `tahap6_geofem_jalan.py`; cache `%TEMP%\tahap6_penurunan_*.pkl`, `TAHAP6_PENURUNAN_CACHE=1`), 10 uji `tests/test_tahap6_penurunan.py`, `6.6 Penurunan Pondasi.xlsx` + `.md`, peta penurunan (c) dan (d) di `Gambar/`, T-104 di VERIFIKASI (lolos: Excel 1e-13 %, GeoFEM3D 24,98 % dari batas 25 %, Δe 8,4 %, uji beban 9,2 %).
- Varian (a) rakit D/3 di atas ujung / (b) rakit di bidang netral, Boussinesq semua cap: s total 55-280 mm, δ maks 123 mm, 53 dari 86 pasangan > 16 mm. Tidak cocok dengan uji beban statik (tiang tunggal 1.400 kN ±3 mm; cap 4 tiang 240 mm = 80x): rakit seluas cap kecil memberi ±550 kPa di U6 melewati σ'p. Dipakai sebagai batas atas.
- Varian (d) usulan AI: s NP 6.2 + 2,0 x Q0/k (k 489 kN/mm TP-1..4) x √n + rakit gedung 73,2 x 46,6 m (σ'p = 2,2 σ'v0): s total 24-68 mm, δ maks 22,2 mm (4/F-4/G, 1/361), 11 pasangan > 16 mm; M SL-1 491 kNm rasio 0,61; 400 x 800 345 kNm belum dicek.
- Diperbaiki: OCR U6 lembar isian 2,14-2,41 (3,8/4,0 adalah cv). Temuan: rasio SL-1 kode 5.4 0,534 vs teks 0,48. GeoFEM3D: Cap E 23,8 vs 19,4 mm, 4/C 44,4 vs 35,5 mm (elastis setara).
- Perlu diputuskan Defsa: varian dasar (d atau a/b), δ desain sloof 22,2 mm, cek SL-2/SL-3 di 6.7.
- **Keputusan Defsa 22 Nov 2026:** varian (d) disetujui sebagai dasar desain; δ desain sloof 22,2 mm; (a)/(b) batas atas; B-5 tutup. Langkah berikutnya: 6.7 desain struktur tiang dan pile cap (cek juga sloof SL-2/SL-3 400 × 800 dengan M 345 kNm).

## 22 Nov 2026: Tahap 6 langkah 6.7 desain struktur tiang dan pile cap (draf, menunggu persetujuan Defsa)

- Defsa meminta AI menghitung (lembar data `6.7 Lembar Isian Tiang dan Cap.md`). `skrip/tahap6_struktur.py`, 8 uji `tests/test_tahap6_struktur.py` lolos, `6.7 Desain Tiang dan Pile Cap.xlsx` + `.md`, T-105 di VERIFIKASI (lolos; butir a hampir tautologis, c tie STM vs balok 11,3 %).
- Koreksi acuan: pasal tiang SNI 2847 adalah 18.13.4 (18.13.5 tidak ada); SNI 8460 9.3.3 b / 9.3.4 hal. 197 untuk gaya angkat (FK 1,5 dengan angkur, 1,1 beban mati saja); 10.6 hanya angkur tanah. Stek K-P D25 ldh 426 / ld 1.044 (375/919 milik K-T B D22).
- Tiang Ø800 D25 spiral D13 selimut 75: minimum 12 D25 (f'c 30) / 11 D25 (f'c 35), penentu Youd 966 kNm pada 1.560 kN; 16 D25 rasio 0,86/0,83. Spiral 40/80 mm (f'c 35), zona rapat 25,76 m (SNI 1726 7.13.8.3.3). Tulangan cap inti penuh; cap kolom sampai -17,76.
- Cap kolom h minimum 1.000 / 800 / 950 (2/3/4 tiang, pons kolom 0,92-0,95); h 1.200 seragam rasio ≤ 0,65. Cap E h 1.200: strut STM rasio 1,04 (gagal 4 %), As lentur 293.000 mm² arah x (ρ 1,48 %); usulan 1.500 (rasio 0,81). Hasil STM tidak monoton terhadap h (1.800-2.000 naik ke 1,32, peka asumsi lebar zona angkur): perlu ditelaah.
- Pit L-1..4 t 0,45 FK 1,110 ≥ 1,1 (lolos tipis); tapak menjorok 1,33 m melewati tepi timur Cap E, dasar pit +10,80 bentrok dengan cap. Sloof δ 22,2 mm: SL-2 0,724, SL-3 0,700 (tanpa tambahan).
- Perlu diputuskan Defsa: f'c tiang 35/30, tebal Cap E (1.200 vs 1.500, B-3), pit (perlebar Cap E / berdiri di cap), potong tulangan cap kolom, h cap kolom minimum atau seragam, ukuran inti dan kolom K-P (750 vs 800). Serakan Zhang masih terbuka.
- **Keputusan Defsa 22 Nov 2026:** tebal Cap E 1.500 mm (STM 0,81; mengubah B-3 khusus Cap E, cap inti lain 1.200). Akibat dicatat di md bagian 8 (kepala tiang Cap E +10,70, berat +2 %, pit berdiri di cap). Keputusan lain 6.7 masih menunggu.
- **Keputusan Defsa 22 Nov 2026:** draf 6.7 disetujui dengan usulan AI: f'c tiang 35 MPa 16 D25, tulangan cap kolom dipotong di -17,76 (cap inti penuh), spiral D13 40/80 mm sampai -14,91, cap kolom h 1.000/800/950 (2/3/4 tiang), pit varian A FK 1,110 berdiri di Cap E. Serakan Zhang tetap terbuka. Langkah berikutnya: 6.8 uji tiang dan metode pelaksanaan.

## 22 Nov 2026: Tahap 6 langkah 6.8 uji tiang dan metode pelaksanaan (draf, menunggu persetujuan Defsa)

- Defsa meminta AI menghitung (lembar data `6.8 Lembar Isian Uji dan Pelaksanaan.md`). `skrip/tahap6_pelaksanaan.py`, 8 uji `tests/test_tahap6_pelaksanaan.py` lolos, `6.8 Uji Tiang dan Pelaksanaan.xlsx` + `.md`, T-106 di VERIFIKASI (GAGAL butir c: sumur ekuivalen vs aliran 1-D 211 % > 100 %; aliran 1-D batas bawah, debit desain dari sumur ekuivalen; toleransi tidak dilonggarkan). Nomor cek silang rencana bergeser: IFC T-107, Excel = Python T-108.
- Uji statik TP-1..4: k 489,3 kN/mm, s 200 % 4,45-5,09 mm (≤ 25), sisa 1,78-2,42 mm (≤ 12), Davisson tidak tercapai; 1.822 kN hanya membuktikan FK 2,0 pada 911 kN. Izin 6.2 perlu uji 3.166 / 2.886 kN; Pu 3.254 belum teruji.
- Program SNI 8460 9.8: statik tambahan 2 (konstruksi, letak Cap E / 7/D / Cap A), tarik 1 (Cap D, 2.178 kN usulan), lateral 1 (2 × 53,95 kN), PIT +23 / +9, CSL dan PDA cukup. Temuan: model 6.5 y 15,3 / 26,0 mm > batas lateral 10 mm (9.8.3). T113 CSL D: CSL ulang + coring, grouting atau tiang pengganti.
- Dewatering: k urugan tidak ada (skenario 1e-6..1e-4 m/s), debit ≤ 2,5 m³/jam (Cap E), muka air urugan tidak turun di bawah +9,23 > +8,6 batas cerucuk gudang; heave FS 1,34-1,55. Sump terbuka cap kolom, parit keliling + sump Cap E dan pit. INC-1 0,177 vs 0,18 mm/hari (margin tipis).
- Perlu diputuskan Defsa: lingkup (Tahap 6 vs RKS Tahap 7), 2 uji statik konstruksi, uji tarik/lateral dan kriteria lateral, dewatering, T113.
- **Keputusan Defsa 22 Nov 2026:** draf 6.8 disetujui dengan usulan AI semua butir (program uji di Tahap 6, rinci ke RKS Tahap 7; 2 uji statik konstruksi 200 % × izin; uji tarik Cap D 2.178 kN dan lateral 2 × 53,95 kN; dewatering sump/parit; T113 CSL ulang + coring). Langkah berikutnya: 6.9 model BIMCraft LOD 300 pondasi (bawa akibat Cap E 1.500: kepala tiang +10,70, pit di dalam cap; kepala tiang cap kolom = +12,05 - h + 0,15).

- **Keputusan Defsa 22 Nov 2026 (6.9):** Cap C (14 tiang) bertumpang 102,4 m² dengan telapak Cap E (6.3 hanya cek jarak tiang); Cap C digabung ke Cap E. 6.3, 6.7, 6.8, 6.9 dihitung ulang; 6.5/6.6 dicatat dampaknya tanpa hitung ulang berat.
- **Keputusan Defsa 22 Nov 2026 (6.9):** Cap E gabungan tetap 32 tiang (gedung utama 230); Cap E didesain sebagai pelat di atas tiang (h 1.800 usulan), STM lokal di sekitar inti saja. 6.5 dan 6.6 dijalankan ulang untuk 230 tiang.

### Revisi 22 Nov 2026 (berat cap dimasukkan, temuan 6.9; usulan AI, disetujui atas delegasi Defsa 22 Nov 2026) - STATUS: draf
- **6.3** (`tahap6_tata_letak.py`): berat cap W = A h 24 kN/m³ dikurangi apung 9,81 A (11,20 - dasar cap) [Asumsi muka air desain 6.0]; layan + W, gempa Pu maks + 1,2 W, Pu min + 0,9 W; h dari 6.7 (cap kolom 2/3/4 tiang 1,0/0,8/0,95; cap inti 1,2; Cap E 2,0; cap 5-6 tiang 1,2 [Asumsi]). Algoritma jumlah tiang tetap, cek tidak dihapus; cap inti yang tak muat di antara cap kolom yang bertambah dicari tanpa cap kolom lalu digabung (gabung_cap). Hasil gedung utama 230 menjadi 251 tiang (+9,1 %; total dengan utilitas 298 menjadi 319): cap kolom 152 menjadi 143 tiang (56 menjadi 52 cap; 2/3/4/6 tiang 28/16/12/0 menjadi 27/13/11/1), cap inti 78 menjadi 108. Cap E gabungan = Cap C + Cap E + 4/B, 4/C, 7/B, 7/C: 54 tiang, 30,4 × 13,6 m. Varian (b) 40 m: Cap E tak lolos berberat cap (hanya dilaporkan). Hasil rancangan di-cache di `cache/tahap6_rancang_*.pkl`. T-101 lolos.
- **6.7**: Cap E pelat (OpenSees ShellMITC4, pegas tiang k/(FJ√n)) memakai berat cap 6.3 (tidak dihitung dua kali). h 1.800 gagal pons inti 1,079; 1.900 masih gagal tipis (1,014); **h 2.000 lolos** (pons inti 0,955; geser 0,74; tulangan bawah x 2 lapis D32-150, y 1 lapis D32-175; atas x D32-125, y D32-200). Keputusan (usulan AI, disetujui atas delegasi Defsa 22 Nov 2026): Cap E h 2.000 mm, tanpa tulangan pons. Reaksi pelat vs cap kaku: Σ 0,0000 %, maksimum -12,7 % (2.438 vs 2.794 kN). Cap kolom 2/3/4 tiang tidak gagal (usul 950/750/950 mm di bawah h 6.3). SL-2/SL-3 pada δ 24,6 mm: rasio 0,76/0,74.
- **6.5**: inersia dibagi 251 tiang: X 52,45 kN, Y 35,73 kN; M maks 130,7 kNm (rasio 0,12 terhadap φMn 1.122), 16 D25 lolos.
- **6.6**: dihitung ulang (58 cap); varian (d) δ maks 24,6 mm (4/F - 4/G), SL-1 545 kNm rasio 0,65; GeoFEM3D diulang (Cap E, 3/C; selisih 24,4 % vs batas 25 %).
- **6.8**: dasar Cap E +10,05 (h 2.000), galian dan dewatering Cap E 30,4 × 13,6 m diperbarui; program uji tiang 251 / 319 tiang. T-106 (c) 211 % tetap sama seperti sebelumnya (GAGAL, orde besaran).
- **6.9**: model dibangun ulang (319 tiang, 83 cap, Cap E h 2.000, kepala tiang +10,20), T-107 lolos, render dilihat.
- **Revisi 6.9 (22 Nov 2026), status: disetujui atas delegasi Defsa 22 Nov 2026:** Cap E gabungan 54 tiang, 30,4 × 13,6 m, pelat h 2.000 mm (dasar +10,05, kepala tiang +10,20); gedung utama 251 tiang, total 319 (sebelumnya 230/298); berat cap masuk 6.3 (temuan 6.9). Model 6.9 dibangun ulang (319 tiang, 83 cap), T-107 lolos; T-104, T-105 lolos; T-106 (c) 211 % tetap seperti sebelumnya. 6.6: δ maks varian (d) 24,6 mm, SL-1 rasio 0,65. 6.5 tidak diulang (jumlah tiang 251 tetap).
## 22 Nov 2026: rencana Tahap 7 DED dan RKS (disetujui atas delegasi Defsa 22 Nov 2026)

- `07 DED dan RKS/00 Rencana Tahap 7.md`: langkah 7.0-7.9 (telaah dan daftar dokumen, model arsitektur lengkap LOD 300, federasi dan clash, cek struktur tambahan fasad/chiller/LB-1, DED arsitektur GA, struktur GS-33.., MEP dasar GM, RKS, render akhir R-01..R-08 Blender + Bonsai, ringkasan). Disusun paralel dengan 6.9, tanpa angka 6.9.
- Bawaan B-1..B-12 dari Tahap 2-6 (gambar pondasi 6.10, serakan Zhang, uji tiang 6.8, dewatering + batas +8,6, S2, overstek, chiller 14,5 Hz, LB-1, P4, kedap/A955M, sisa penurunan 874 mm, surat tanggapan). Pasal RKS yang sudah dicek: SNI 2847 Pasal 26 (hal. PDF 640-681), SNI 8460 9.8 (hal. PDF 205-209); SNI uji material, arsitektur, kebakaran, aksesibilitas belum ada di acuan.
- Cek silang T-109..T-118 dengan toleransi. 13 keputusan: Defsa sedang tidur dan mendelegasikan; usulan AI dipakai (antara lain serakan Zhang ditangani perkuatan tebing Ø600 + perbaikan tanah U5, fasad V4 dikunci, chiller pegas 25 mm bila frekuensi cukup, LB-1 balok tepi, render 8 sudut Cycles). Boleh diubah Defsa di awal langkah terkait.
- Langkah berikutnya: tunggu 6.9-6.11 selesai, lalu 7.0 telaah dan daftar dokumen (sesi baru).
- 6.10 Gambar pondasi selesai (disetujui atas delegasi Defsa 22 Nov 2026): GS-28..32 dan GT-16 di CADCraft, cad_cek 0, 319 tiang / 83 cap sama dengan IFC 6.9; lihat `06 Struktur Bawah dan Basement/6.10 Gambar Pondasi.md`.

## 22 Nov 2026: Tahap 6 langkah 6.11 ringkasan (disetujui atas delegasi Defsa 22 Nov 2026)

- Seluruh uji 420 lolos (21 menit). `06 Struktur Bawah dan Basement/Ringkasan Tahap 6.md`: keputusan per langkah, angka kunci akhir (251/319 tiang, 83 cap, Cap E 54 tiang h 2.000), T-98..T-107 (T-102 dan T-106 gagal satu butir, dicatat), temuan terbuka ke Tahap 7 (serakan Zhang, pit L-5..7, tulangan cap [Asumsi], uji tiang ke RKS). **Tahap 6 selesai.** Langkah berikutnya: Tahap 7 (7.1 model arsitektur sedang berjalan).
## 22 Nov 2026: Tahap 7 langkah 7.0 dan 7.1 (draf, disetujui atas delegasi Defsa 22 Nov 2026)

- **7.0** `skrip/tahap7_telaah.py`, `7.0 Telaah dan Daftar Dokumen.xlsx` + `.md`: 6.9 selesai (PR #58), 6.10 sedang dikerjakan (`fitur/tahap-6-10-gambar`), 6.11 belum. Daftar DED: GA-01..23, GS-01..27 ada, GS-28..32 + GT-16 (6.10), GS-33..36 baru (7.5), GM-01..06. RKS 15 bab + 2 lampiran dengan status acuan; 9 acuan dicari. Keputusan K7-1 (B-2: perkuatan tebing Ø600 + perbaikan tanah U5), K7-2..K7-5. Cek murah elevasi/grid STR vs tahap4_beban 0,0 mm.
- **7.1** `skrip/tahap7_arsitektur.py` (subagen Sonnet), `model/RSTB-ARS-T7-LOD300.bimc/.ifc` + `-v0.11.bimc`, `7.1 Model Arsitektur.md`, render `07 DED dan RKS/Gambar/7.1 Model ARS 3D Depan/Udara.png` (dilihat). Model ARS saja (struktur di STR 6.9): 1.414 dinding, 224 pintu (P1/P2/P3/PL), 235 ruang bernama, 171 plafon, fasad V4, overstek +3,60-+3,90, tapak (P4 76 motor sisi barat x 1-7, y 35-63,5), taman atap, helipad, GU, tebing dan sungai. T-110 lolos (0,000 mm); T-109 (a)(b) lolos, (c) GAGAL karena Rekap 3.4 memakai 3.456 m² untuk LT2/LT3 (perlu koreksi Rekap).
- Catatan: tata letak interior skematik otomatis (ruang ber-takik di inti); lubang shaft tertutup lapis lantai ARS, diselesaikan di 7.2.
- Langkah berikutnya: 7.2 federasi ARS + STR 6.9 dan clash (sesi baru).

## 22 Nov 2026: Tahap 7 langkah 7.7 RKS (disetujui atas delegasi Defsa 22 Nov 2026)

- `skrip/tahap7_rks.py`, 3 uji `tests/test_tahap7_rks.py` lolos, `07 DED dan RKS/7.7 RKS.docx` + `.pdf` (25 hal.; format panduan UNJA lewat `format_dokumen`, dicek di PDF). 15 bab (umum, tanah + PVD, dewatering, tiang bor dan uji, perkuatan tebing, beton, tulangan, bekisting, uji beton, kedap, arsitektur, fasad, kebakaran/aksesibilitas, MEP dasar, toleransi) + Lampiran A program uji, B ambang pemantauan, C pasal dan keputusan.
- Angka dari Ringkasan Tahap 6 dan 6.8 (uji 3.166/2.886/2.178/107,9 kN, PIT +24/+11, T113 CSL ulang + coring, dewatering ≤ 2,688 m³/jam, batas +8,6, INC-1 0,18 mm/hari). T-115 (30 pasal: 20 dicek ke PDF, 9 belum ada di acuan, 1 acuan/publik) dan T-116 (32 angka, 0 selisih) lolos.
- Keputusan K7.7-1..6 atas delegasi: kriteria lateral SNI 9.8.3 dengan evaluasi terhadap prediksi 6.5, uji k urugan sebelum galian, pompa 2 × Q + cadangan [Asumsi], berhenti kerja bila INC-1 > 0,18 mm/hari 3 hari, deep mixing untuk U5, f'c 35 unsur kontak tanah. Toleransi pelaksanaan tiang berlabel [Asumsi] (acuan belum ada).
## 22 Nov 2026: Tahap 7 langkah 7.2 federasi dan clash (draf, disetujui atas delegasi Defsa 22 Nov 2026)

- `skrip/tahap7_federasi.py`, `model/RSTB-FED-T7.ifc` (ARS + 1.708 unsur STR 6.9 tanpa tulangan dan pintu STR kembar + 7 alat MEP + 31 ruang shaft), `7.2 Koordinasi dan Clash.xlsx` + `.md`, `tests/test_tahap7_federasi.py`. Clash metode 2,5D (backend clash ifcopenshell 0.9 tidak ada): 1.612 → 1.156 pasangan.
- Diperbaiki di model ARS (`tahap7_arsitektur.py`, dibangun ulang, T-109/T-110 lolos): shaft STR jadi rintangan + selubung bata 100, ruang shaft/lift tanpa lapis lantai, lubang shaft di lapis atap (K-03 392 → 0); jalan IGD ke lajur 5.2 opsi 2 x 92,5-98,5 dan drop-off y 34,6-45,4 (jarak MRI 4,1 → 12,0 m).
- Rekap 3.4 luas massa dikoreksi di `tahap3_program.py` (LT2 2.832, LT3 2.304 m²); 3.4 Program Ruang Konsultan.xlsx dibuat ulang.
- **T-111 belum lolos:** K-01 balok BL-350x600 as 6 bentang B-C melintas di ruang luncur lift L-1..4 → 7.3. Ditanyakan juga: A-04 chiller (B-7, 7.3), A-08 akses motor P4 (7.4). Validasi IFC 16/20 (temuan Pset_WallCommon/PileCommon STR, Pset lapis lantai/plafon ARS).
- Uji Blender (`skrip/tahap7_uji_blender.py`): impor 10 s, Eevee 27 s, jumlah unsur = ifcopenshell (pratinjau T-117); catatan 7.8: tiang tampak di bawah tapak, 53 % objek tanpa material, langit/cahaya datar.
- Langkah berikutnya: 7.3 cek struktur tambahan (tutup K-01 dulu, lalu ulang `tahap7_federasi.py`).
- 7.2 susulan (permintaan sesi induk): K-04b pit lift sebagian di luar telapak Cap E masuk daftar clash (pit L-5..6 2,01 m², pit L-7 8,54 m² di luar cap; di model ada 2 pelat pit, bukan 6), ditanyakan ke 7.3/7.5.

## 22 Nov 2026: Tahap 7 langkah 7.3 cek struktur tambahan (draf, disetujui atas delegasi Defsa 22 Nov 2026)

- `skrip/tahap7_cek_struktur.py` (`--bangun` membangun model), `07 DED dan RKS/7.3 Cek Struktur Tambahan.xlsx` + `.md`, `tests/test_tahap7_cek_struktur.py` (4 uji), model `model/RSTB-STR-T7-LOD300.bimc/.ifc` (+ `-v0.11.bimc`) dari STR 6.9.
- **K-01**: 6 balok BL-350x600 as 6 di inti lift (LT2-ATAP) dihapus. Model OpenSees 4.3 tanpa balok berubah maks 0,22 % (T-113b, batas 1 %): hasil Tahap 4-6 tetap; skrip tahap 4 tidak diubah (cache tidak basi).
- **A-04/B-7 chiller**: frekuensi lantai atap 4,1 Hz (Rayleigh tangan, batas bawah) / 5,6 Hz (grillage OpenSees), jauh di bawah 1,4 × 14,5 = 20,3 Hz. T-113 gagal toleransi 10 % (-28 %, ragam berbeda; keputusan tidak peka). Keputusan rencana 5: chiller dipindah ke y ≥ 63, unit diputar (x 68,4-81,2, y 63,5-74,5; orientasi asli tidak muat, 12,8 > 12,0 m), di atas rehab medik/isolasi/koridor (bukan kamar operasi 4), tetap di atas pegas δ 25 mm. 8 rel lama dihapus, 7 rel baru 300 × 500 arah y (y 59-67-75) + balok induk x 76; pompa M-04 ke x 60-68, y 62-66 [Asumsi].
- **K-04b**: L-5..6 menjorok 0,39 m sebagai kantilever pelat dasar pit (Mu 4,0 ≤ φMn min 91 kNm/m). L-7: perlebaran Cap E tanpa tiang gagal (P layan 1.509 > izin 1.443; Cap E sudah rasio 1,00), jadi perlebaran x 37,1-41,7 y 29,4-32,2 h 2.000 + **2 tiang Ø800 baru** (509 kN/tiang, rasio 0,35). Tiang gedung utama 251 → 253, total 319 → 321, cap 83 → 84.
- **T-112** lolos: fasad V4 2.989 kN vs V3 6.028 kN (-50 %; panel GRC 1,0 kPa 5.747 kN); angkur dan balok tepi 4.10 tetap. **LB-1**: balok tepi x 70 (350 × 600, 8 m), y 52 dan y 56 (300 × 600, 6 m) lolos; isian screed 250 mm [Asumsi].
- Federasi 7.2 diulang dengan STR 7.3: **T-111 lolos** (0 kritis terbuka; K-01 25 → 0, 1.156 → 1.132 pasangan), A-04 diperbaiki, K-04b diterima.
- Belum: render STR 7.3 dan pemeriksaan visual Bonsai, tulangan unsur baru (7.5), GA atap dengan letak chiller/pompa baru (7.4), ARS 7.1 belum memuat letak alat baru (alat MEP ada di federasi).
- Langkah berikutnya: 7.4-7.6 DED (sesi baru).

## 22 Nov 2026: Tahap 7 langkah 7.4 DED arsitektur (draf, disetujui atas delegasi Defsa 22 Nov 2026)

- `skrip/tahap7_gambar_ars.py` (subagen Sonnet; satu lembar per run, CLI `--lembar GA-xx`, `--pdf`, `--cek`, `--t114`), 23 lembar GA-01..GA-23 DWG + PNG, set `07 DED dan RKS/7.4 Gambar Arsitektur DED.pdf`, `7.4 Gambar Arsitektur.md`. cad_cek 0 pasangan di 23 DWG; T-114 lolos (53 ukuran, 0,000 mm); 4 uji lolos.
- Keputusan skala (A3 viewport 307 × 249 mm): denah LT1-LT3 1:250 dibagi barat/timur, LT4-6 dan atap 1:300, RCP 1:750, tampak 1:500/1:400, potongan 1:400, detail 1:25-1:150 (rencana 1:100/1:20 butuh A1; set A1 bisa dibangun dari tabel `LEMBAR`).
- Tampak diproyeksikan dari dinding fasad model (DXF section BIMCraft hanya unsur terpotong); gedung utilitas dikeluarkan dari tampak gedung utama (GA-23 terpisah). Dilihat: GA-04, GA-14 (sesi), GA-04/10/13/15/16/20 (subagen).
- Terbuka: label ruang melintas partisi di 1:250-1:300; toilet/ramp tanpa acuan (Permen PUPR 14/2017 belum ada); anak tangga, fixture, titik lampu belum di ARS. DXF antara `Gambar/BIM/` dan `_plot/` tidak di-commit (dibangun ulang `--ekspor`).
- Langkah berikutnya: 7.5 DED struktur (rakit GS-01..32 + GS-33..36) dan 7.6 MEP dasar, sesi baru.
- 7.5 DED struktur selesai (disetujui atas delegasi Defsa 22 Nov 2026): GS-33 LB-1, GS-34 rel chiller, GS-35 catatan umum (+ skema B-2); GS-28/29/32 diperbarui untuk Cap E diperlebar + 2 tiang (321 tiang; IFC 6.9 belum memuat); set `7.5 Gambar Struktur DED.pdf` 35 halaman, tak ada lembar hilang; `07 DED dan RKS/7.5 Gambar Struktur.md`. Langkah berikutnya: 7.6 MEP dasar.

## 22 Nov 2026: Tahap 7 langkah 7.6 DED MEP dasar (draf, disetujui atas delegasi Defsa 22 Nov 2026)

- `skrip/tahap7_gambar_mep.py` (satu lembar per run, `--cek`, `--pdf`, `--data`), GM-01..GM-06 di CADCraft (KOP_A3, cad_cek 0), set `07 DED dan RKS/7.6 Gambar MEP Dasar DED.pdf` (6 halaman), `7.6 MEP Dasar.md`; 4 uji lolos.
- Koordinasi saja (keputusan rencana 8): shaft dan lubang pelat (IFC STR 7.3 = `tahap4_bim.SHAFT` untuk 8 shaft + void lift), bukaan pintu 7 inti, ruang alat atap podium (letak 7.3), zona MRI (lingkar 12,0 m), beban alat per lantai (LT3 3.010,3 kN termasuk atap podium).
- Temuan ke konsultan MEP: jarak pompa M-04 ke chiller 0,4 m (< zona servis 1,0 m [Asumsi], usul geser pompa ke x 59,4-67,4); chiller 0,5 m dari tepi podium utara; SH-7 di pelat turun LB-1.
- Langkah berikutnya: 7.8 render (sesi baru).
## 22 Nov 2026: Tahap 7 langkah 7.8 render akhir (draf, menunggu Defsa memilih render)

- `skrip/tahap7_render.py` (Blender 5.2.4 + Bonsai, Cycles GPU, satu kamera per proses), 8 render R-01..R-08 3.200 × 1.800 px di `07 DED dan RKS/Render/`, adegan `render/RSTB-Render-T7.blend`, `07 DED dan RKS/7.8 Render.md`, `tests/test_tahap7_render.py` (3 uji lolos). T-117 lolos (20 kelas, 5.029 unsur, 0 selisih).
- Perbaikan model: huruf papan nama terpotong dek helipad (dek ATAP +0,7 menjorok 3,9 m) → dipindah ke pita LT6 +2,4..3,8 (`tahap7_arsitektur.py`); ARS + v0.11 + federasi dibangun ulang (1.132 pasangan, 0 kritis; uji ARS/federasi 10 lolos).
- Kelemahan: tanpa figur orang, lampu senja lemah (R-02/R-07), kilau air R-03. Usul AI: R-01, R-06, R-03, R-08.
- Langkah berikutnya: Defsa memilih render (titik berhenti 7.8), lalu 7.9 ringkasan dan PR (sesi baru).

## 22 Nov 2026: Tahap 7 langkah 7.9 ringkasan (draf; 7.0-7.7 disetujui atas delegasi Defsa 22 Nov 2026)

- `07 DED dan RKS/Ringkasan Tahap 7.md`: hasil 7.0-7.7, keputusan K7-1..K7-11 + K7.7-1..6, daftar dokumen DED 64 lembar (GA-01..23, GS-01..35, GM-01..06; Rev. 0, GS-28/29/32 Rev. 1 karena Cap E diperlebar), butir terbuka O-1..O-10, Lampiran A surat tanggapan B-12 (owner/MEP: atap, chiller, MRI, AHU LT3, helipad tahap 2, pit lift; TABG: kelas situs SF).
- **7.8 render belum selesai:** R-01..R-08 versi pertama ada di `main` (PR #70); revisi archviz (Poly Haven, detail, video 6 shot) di `fitur/tahap-7-8-render-v2`, dirender di Google Colab karena laptop mati kepanasan (pendingin hasil servis 7 Nov tidak menempel). Bagian 3 ringkasan diisi setelah render jadi.
- Seluruh uji Tahap 7 belum dijalankan (laptop panas; O-10).
- Langkah berikutnya: selesaikan 7.8 (render Colab, Defsa memilih render), isi bagian 3 Ringkasan Tahap 7, lalu Tahap 8.

## 22 Nov 2026: Tahap 8a volume dari model BIM dan AHSP (draf, disetujui atas delegasi Defsa 22 Nov 2026)

- `08 RAB/00 Rencana Tahap 8.md` (8a/8b, K8-1..K8-7, cek silang T-119..T-120), `skrip/tahap8_volume.py`, `08 RAB/8a Volume dan AHSP.xlsx` (6 lembar, AHSP rumus hidup, dihitung di Excel) + `.md`, `tests/test_tahap8_volume.py` (4 uji lolos).
- Volume dari Qto IFC STR 7.3 dan ARS 7.1: beton bersih 14.435,7 m³ (tiang 6.200,3; 321 tiang 12.383 m'), besi 1.881,6 t (rasio kg/m³ Tahap 3.6 + tiang 6.7), bekisting 29.319 m², bata ringan 16.329 m², fasad kaca 2.885 m², panel 4.591 m².
- AHSP rinci 12 item (tiang bor, beton fc' 35/30, besi, bekisting, bata, plester, fasad kaca/panel, dewatering); BTL 12 % (Permen PUPR 8/2023 Ps. 11(3)); alat bor dari SE 47/2026 Lamp. II hal. 187-188; koefisien lain [Asumsi] karena lampiran AHSP Permen 8/2023 di `acuan/` berupa pindaian; harga [Asumsi: Jambi 2026].
- T-119a/b lolos, T-120 lolos (12 item rinci = 85,1 % biaya). Biaya 8a Rp 113,2 miliar tanpa MEP/SMKK/PPN; berisiko melewati pagu Rp 168 miliar bila MEP ±30-40 %: bahas di VE 8b. Besi tiang (spiral D13 40/80) 31 % biaya 8a: cek di VE.
- Excel belum dirender ke PDF untuk cek format (laptop panas).
- Langkah berikutnya: 8b RAB, SMKK, MEP (persen/lumsum), PPN, rekap, VE (sesi baru).

## 22-23 Nov 2026: Tahap 8b RAB, SMKK, VE (draf, disetujui atas delegasi Defsa 22 Nov 2026; Tahap 8 selesai, menunggu telaah Defsa)

- `skrip/tahap8_rab.py` (pakai ulang `tahap8_volume.daftar_pekerjaan()`/`volume_struktur()` dan `tahap3_biaya`), `tests/test_tahap8_rab.py` (4 uji lolos), `08 RAB/8b RAB SMKK VE.xlsx` (5 lembar, rekap rumus, dihitung Excel, dicek ke PDF) + `.md`, `08 RAB/Ringkasan Tahap 8.md`; K8-8..K8-11 di rencana Tahap 8.
- RAB 6 divisi + SMKK: persiapan 8,55; pondasi 48,40; struktur atas 26,44; arsitektur 42,37; tapak + lahan 16,61; MEP RS 112,72 (persen Permen PUPR 22/2018 Ps. 29, 43,7 %); SMKK 2,76 (9 komponen SE 47/2026 Lamp. III, CAR 0,1 %; Permen PUPR 8/2023 Ps. 22); PPN 11 %. Total Rp 286,22 miliar = Rp 14,81 juta/m² (19.328 m²).
- Pagu Rp 168 miliar terlampaui Rp 118,2 miliar karena luas (19.328 vs 12.000 m²), bukan harga per m². VE-1..VE-5 hemat Rp 11,19 miliar (3,9 %) → Rp 275,0 miliar; rekomendasi pagu ±Rp 275 miliar atau bertahap (opsi 3.8 V1/V5/V6).
- T-121c/d lolos; T-121a/b gagal toleransi (-36,6 % / -38,8 % terhadap konsep 3.8; sebab dijelaskan di Ringkasan Tahap 8).
- Langkah berikutnya: Tahap 9 Jadwal (satu Gantt + kurva S dari bobot RAB 8b), sesi baru.
## 23 Nov 2026: Tahap 9 Jadwal dan Kurva S (draf, disetujui atas delegasi Defsa 23 Nov 2026; Tahap 9 selesai, menunggu telaah Defsa)

- `09 Jadwal/00 Rencana Tahap 9.md` (K9-1..K9-7, T-122..T-125), `skrip/tahap9_jadwal.py` (CPM, bobot dari `tahap8_rab.rekap()`, tiang bor dari `tahap8_volume.koef_bor`), `9 Gantt dan Kurva S.png/.pdf`, `9 Jadwal dan Kurva S.xlsx` (4 lembar, rumus hidup, dihitung Excel) + `.md`, `9 Jadwal.xml` (ProjectLibre), `Ringkasan Tahap 9.md`, `tests/test_tahap9_jadwal.py` (3 uji lolos).
- 21 kegiatan, mulai 4 Jan 2027 [Asumsi], durasi 98 minggu (22,6 bulan); lintasan kritis PER-LHN-TB(20 mgg)-GAL-STR1-STR2-MEP1-MEP2-UJI.
- T-122a/b/c, T-123, T-124 lolos; T-125 gagal (tower crane dipakai 9,9 bulan vs sewa 18 bulan RAB 8b) → usul VE-6 sewa 2 × 11 bulan, hemat ±Rp 1,89 miliar sebelum PPN (RAB 8b tidak diubah).
- Excel belum dirender ke PDF (laptop panas). Langkah berikutnya: Tahap 10 Laporan Akhir + halaman portofolio (sesi baru).

## 23 Nov 2026: Tahap 10 Laporan Akhir (draf, disetujui atas delegasi Defsa 23 Nov 2026; menunggu telaah Defsa)

- `10 Laporan/00 Rencana Tahap 10.md` (K10-1..K10-7, T-126/T-127), `skrip/laporan_akhir.py`, `10 Laporan/Laporan Akhir.docx/.pdf` (9 bab + lampiran; angka dikutip dari Ringkasan Tahap 2-9, tidak dihitung ulang), `tests/test_laporan_akhir.py` (3 uji lolos), T-126/T-127 lolos.
- Isi: geoteknik (SF, likuifaksi), konsep (peil +12,85, tanpa basement), struktur, 321 tiang/84 cap, DED 64 lembar, RAB Rp 286,22 miliar + VE-1..VE-5 dan usul VE-6, jadwal 98 minggu + Gantt/kurva S, keputusan pagu owner, butir terbuka O-x/O8-x/O9-x/O10-1.
- `10 Laporan/Halaman Portofolio.md`: draf halaman portofolio (K10-6), belum terbit ke `situs/`.
- Belum: cek visual PDF (poppler/PyMuPDF tidak terpasang; dibangun dengan Word, gaya `format_dokumen`); render v2 (O-1) belum menggantikan R-01; O10-1 tanggal mulai jadwal 4 Jan 2027 mendahului Laporan Antara (Apr 2027), perlu digeser.
- Langkah berikutnya: Defsa menelaah Laporan Akhir + draf halaman; pilih render v2; terbitkan halaman ke `situs/` setelah pindai privasi.

## 23 Nov 2026: Tahap 10 lanjutan (atas delegasi Defsa)

- PDF Laporan Akhir dicek visual (PyMuPDF dipasang di `.venv`): format tabel/inden rapi; Bab VIII dibuat lanskap agar Gantt terbaca (K10-9), 20 halaman.
- O10-1 ditutup (K10-8): mulai konstruksi `tahap9_jadwal.MULAI` digeser 4 Jan 2027 → 3 Jan 2028, selesai 19 Nov 2029; durasi 98 minggu dan T-122..T-125 tidak berubah; Gantt, Excel, XML Tahap 9 dibangun ulang. Uji `test_laporan_akhir` + `test_tahap9_jadwal` 6 lolos.
- Sisa: render v2 (O-1) mengganti R-01, telaah Defsa, terbitkan `10 Laporan/Halaman Portofolio.md` ke `situs/` setelah pindai privasi.

## 23 Nov 2026: serah terima penyelesaian 100 %

- `SERAH TERIMA.md` ditimpa: daftar sisa A (isi), B (audit), C (perapian laptop, awas junction), D (GitHub/situs), 4 sesi dengan model/effort dan prompt siap tempel.

## 23 Nov 2026: sesi 2 audit akhir B1-B6, A4, A5, A7 (draf atas delegasi Defsa; menunggu telaah Defsa)

- `10 Laporan/Audit Akhir.md` + `.docx`/`.pdf` (22 hal., dibangun `skrip/audit_akhir.py` dari md; uji `tests/test_audit_akhir.py`), lampiran halaman Excel di `10 Laporan/Lampiran Audit/`. 16 butir: 1 tinggi, 3 sedang, 7 rendah, 5 sesuai.
- **AU-02 (tinggi)**: RKS 7.7 masih 319 tiang (251 utama); diperbaiki ke 321 (253), sumber `7.5 Gambar Struktur.md`; PIT tambahan 24 / 11 → **25 / 11** (K-AU1). RKS dibangun ulang.
- Laporan Akhir Bab IX: O-1 dihapus, O-2 / O-4 / O-8 ditambah; dibangun ulang. 6.10 dan Ringkasan Tahap 6 diberi catatan angka akhir 321 / 253 / 84.
- A5: O-2 ditutup; O-4, O-8 di luar lingkup (K-AU2). A4: Excel 8a/8b/9 dirender ke PDF, lolos dengan 3 catatan tampilan; O9-3 ditutup. T-27 ditandai tidak dilakukan (K-AU3). A7: status Tahap 7 dan 10 diseragamkan "menunggu telaah Defsa".
- Angka kunci lain konsisten (19.328 m², Rp 286,22 miliar, VE Rp 11,19 miliar, 98 minggu, 3 Jan 2028); `acuan/privat` tidak pernah di riwayat git.
- Uji: `test_audit_akhir`, `test_tahap7_rks`, `test_laporan_akhir` 8 lolos. Seluruh `pytest` belum (laptop panas, O-10).
- Langkah berikutnya: Defsa menelaah `10 Laporan/Audit Akhir.pdf` Bab VIII.2; sesi 3 perapian laptop, sesi 4 GitHub dan situs (`SERAH TERIMA.md` 4.3, 4.4).

## 23 Nov 2026: Laporan Akhir dilengkapi gambar hasil analisis (atas permintaan Defsa; menunggu telaah Defsa)

- `skrip/laporan_akhir.py`: subbab galeri 2.3, 3.1, 4.3, 5.1, 6.1 (30 gambar dari Tahap 2-7: penampang dan profil tanah, likuifaksi, urugan, konsep, respons situs, rekaman gempa, model 3D OpenSees, ragam, deformasi, momen, gesekan negatif, serakan lateral, kinematik tiang, peta penurunan, Cap E, model BIM, render R-03/04/06/08, tampak GA-13) + grafik baru `10 Laporan/Gambar/RAB per Divisi dan VE.png` (Bab VII). Lembar CAD A3 dipotong ke area gambar di `cache/laporan_gambar/` (tidak di-commit).
- Laporan Akhir 20 → 40 halaman; angka tidak berubah (T-126/T-127 tetap). Uji `test_laporan_akhir` lolos.

## 23 Nov 2026: Laporan Akhir dirapikan, lampiran DED, Excel AU-09, halaman portofolio (menunggu telaah Defsa)

- Laporan Akhir 52 halaman: lembar CAD selebar teks (14 cm), plot/render 13,5 cm; Lampiran A ditambah baris Tahap 10; **Lampiran B baru (lanskap): 10 lembar DED terpilih** (GA-02, GA-04, GA-15, GA-16, GS-04, GS-11, GS-15, GS-28, GS-31, GM-03); sumber gambar menyebut nama berkas.
- AU-09 diperbaiki: `tahap9_jadwal.py` durasi minggu bulat + lembar Kegiatan A3; `tahap8_rab.py` lembar Value Engineering A3; kedua Excel dibangun ulang (98 minggu, T-122..T-125 sama). Audit Akhir diperbarui (6 diperbaiki, 5 ditutup/ditandai), lampiran Excel diperbarui.
- `10 Laporan/Halaman Portofolio.md` ditulis ulang: tabel angka kunci, 7 butir pekerjaan, galeri 11 gambar (tautan ke berkas repo), temuan, daftar aset untuk `situs/`.
- Uji: test_laporan_akhir, test_audit_akhir, test_tahap9_jadwal, test_tahap8_rab 12 lolos.

## 23 Nov 2026: Tahap 7-10 dan audit **disetujui Defsa 23 Nov 2026**

- Defsa menelaah dan menyetujui semua ("telaah dan saya acc semua"): Ringkasan Tahap 7, 8, 9, Rencana Tahap 10, Laporan Akhir, Audit Akhir (K-AU1..K-AU4), Halaman Portofolio (isi; belum terbit).
- Label di md dan konstanta `STATUS` (`tahap7_rks`, `tahap8_volume`/`tahap8_rab`, `tahap9_jadwal`, `laporan_akhir`) diubah; RKS, 8a, 8b, 9, Laporan Akhir, Audit dibangun ulang (hanya label berubah).
- Langkah berikutnya: sesi 4 GitHub dan situs (`SERAH TERIMA.md` 4.4), lalu sesi 3 perapian laptop (4.3) paling akhir.
