# Ringkasan Tahap 2: olah data tanah

> DATA SIMULASI untuk studi kasus portofolio. **Disusun AI atas permintaan Defsa (19 Nov 2026), disetujui Defsa 19 Nov
> 2026.** Kunci jawaban tidak dibuka saat langkah 2.1-2.7 disusun. Rincian ada di berkas Excel dan gambar GT-01 s.d.
> GT-15 di folder ini (DWG CADCraft di `Gambar/DWG/`, satu kop `KOP_A3`); cek silang di `VERIFIKASI.md` (T-06 s.d. T-33).
> Langkah 2.8 (penyelesaian) disusun sesudah kunci dibuka dan **disetujui Defsa 19 Nov 2026**.

## Keputusan Defsa (19 Nov 2026: keempat usulan disetujui)

| No | Usulan | Dasar | Berkas |
|---|---|---|---|
| 1 | Tinggi tekan akuifer pasir U5 untuk desain operasi **+11,20**; muka air dangkal normal 0,3-1,5 m di bawah muka tanah, banjir +11,20 | Hidrograf Sep 2026-Mar 2027, regresi berjeda, TOR Lampiran A | `2.3 Air Tanah.xlsx` |
| 2 | Nilai parameter desain per unit U1-U8 (rata-rata ∓ 0,5 sd) | Lab, CPTu, SPT terkoreksi | `2.4 Parameter Tanah.xlsx` lembar Ringkasan |
| 3 | **Kelas situs SF** (bukan SE) | Pasir U5 mudah likuifaksi, Ta > 0,5 detik | `2.5 Kelas Situs.xlsx`, `2.6 Likuifaksi.xlsx` |
| 4 | Beton yang menyentuh gambut/lempung minimal kelas paparan S2; perlindungan tambahan terhadap asam | pH 3,7-4,0, sulfat S1-S2 | `2.7 Kimia Tebing Gudang.xlsx` |

## Hasil per langkah

| Langkah | Hasil utama |
|---|---|
| 2.1 Koreksi data | ER palu per bor (rig A 81-86 %, rig B 53 %); N60 204 uji; qt CPTu (koreksi lempung ±11-12 %); mutu contoh Lunne (BH-2 UD-2 dan BH-7 UD-3 buruk) |
| 2.2 Stratigrafi | Unit U1-U8; gambut U3 tidak ada di selatan, menebal ke utara sampai 3,3-3,7 m; pasir U5 9-19 m, lebih dangkal di sisi tebing |
| 2.3 Air tanah | Akuifer U5 tertekan, k ≈ 8 × 10⁻⁵ m/s, diisi ulang sungai; blow-in: galian dasar ±+6 hanya aman Jun-Okt atau dengan sumur pelepas |
| 2.4 Parameter | U4: su = 5,2 + 1,09 z kPa, Cc 0,75, cv 1,8 m²/th; U3: Cc 3,5, Cα 0,21; U5: φ' 33° |
| 2.5 Kelas situs | v̄s30 139-171 m/s, N̄ 3,5-6,6, s̄u 22-25 kPa (SE); menjadi SF setelah 2.6 |
| 2.6 Likuifaksi | amax 0,342 g, Mw 7,0; FS 0,22-0,75 di seluruh U5 (Boulanger-Idriss 2014) |
| 2.7 Kimia, tebing, gudang | Gambut asam dan bersulfat; tebing P-2 longsoran lama, sungai memotong U5; gudang sudah turun 0,8-1,9 mm/bulan, sudut timur laut miring 1/54 |
| 2.8 Penurunan dan pelengkap | Urugan ke +11,50 (0,95-2,68 m): penurunan primer 0,15-0,39 m di selatan, 1,05-1,18 m di utara (+ sekunder 0,06-0,23 m/50 th); t90 tanpa PVD ±7,5 th, PVD segitiga 1,2 m ±5 bulan; beban urugan > 3 su (urugan bertahap); e0 BH-8 UD-2 dikoreksi 2,09, γ BH-3 = γd(1 + w); PZ-4B artesis +0,53 m (juga saat tidak banjir); batas muka air sisi gudang ±+8,6; koreksi tren latar uji pompa tidak mengubah k |

## Kesalahan data penyedia yang ditemukan

1. σ'p lab BH-5 UD-1 100 kPa (seharusnya ±44 kPa).
2. t50 disipasi CPTu-5 9 m dan CPTu-8 24 m dibaca dengan patokan salah.
3. Bacaan downhole 23 m dan uji bertahap PW-1 menit 400 salah baca.
4. Data CPTu-4 0-1 m berada di lubang awal; u2 sampai 4,5 m tidak andal.
5. Sulfat T-2 dilaporkan dalam % SO₃ (satuan berbeda).
6. Batimetri P-3 dikonversi dengan muka air hari lain (0,41 m terlalu tinggi).
7. Patok GT-7 bengkok (loncatan -11,5 mm bukan penurunan); PZ-3A melonjak setelah petir.

## Akibat untuk tahap berikutnya

- **Tahap 3 (konsep):** peil dan urugan halaman ditentukan bersama penurunan 0,2-1,2 m (PVD + prapembebanan sejak
  awal jadwal, urugan ringan atau galian-ganti gambut di utara, sambungan fleksibel); gedung menjauh dari tebing P-2 (longsoran lama, puncak 6,5 m dari batas lahan); hindari zona
  gambut > 3 m di utara atau ganti tanahnya; kedalaman basement dibatasi blow-in dan jadwal musim; sempadan sungai
  (Permen PUPR 28/2015 belum ada di acuan).
- **Tahap 4 (struktur atas):** kategori risiko IV, kelas situs SF: spektrum dari analisis respons spesifik-situs.
- **Tahap 6 (bawah tanah):** tiang menembus U5 ke U6/U7 dengan gesekan U5 diabaikan saat gempa; downdrag akibat
  urugan dan likuifaksi; dewatering terkendali dekat gudang timur (cerucuk gelam lapuk); stabilitas tebing dan
  penyebaran lateral.
- **Tahap 7 (RKS):** batas muka air ±+8,6 di sisi gudang timur selama konstruksi; beton kelas S2 dan perlindungan asam; tiang baja dengan tambahan tebal korosi.

## Acuan yang masih kurang

Kruseman dan de Ridder (uji pompa), Schneider (nilai karakteristik), acuan paparan asam beton (EN 206/ACI 201.2R),
Permen PUPR 28/2015 (sempadan sungai). Lihat `acuan/README.md`.
