# Ringkasan Tahap 6: struktur bawah (tiang bor Ø800, pile cap, tebing, uji, model, gambar)

Status: **langkah 6.0-6.8 disetujui Defsa 21-22 Nov 2026; 6.9-6.11 disetujui atas delegasi Defsa 22 Nov 2026**
(Defsa mendelegasikan keputusan malam 22 Nov 2026). DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek
nyata. Tidak untuk konstruksi.

Rencana tahap: `00 Rencana Tahap 6.md`. Rincian tiap langkah ada di md per langkah; angka di bawah dikutip dari sana,
dari `PROGRES.md`, dan dari `VERIFIKASI.md`. Kunci jawaban tidak dibuka.

## 1. Keputusan per langkah

| Langkah | Keputusan (tanggal) |
|---|---|
| 6.0 Telaah data | Telaah dan permintaan data uji tiang disetujui (21 Nov 2026) |
| 6.1 Tiang tunggal | GEC10 metode utama, U5 hanya statis, FK tarik 2,5 / 1,1; panjang tetap 38,45 m (21 Nov 2026) |
| 6.2 Gesekan negatif | Izin akhir = min(SNI dengan Qn lapisan menurun; GEC10 Qult/2,5); Qn bidang netral hanya untuk cek struktur dan layan (21 Nov 2026) |
| 6.3 Tata letak | Gempa inti 100 % + 30 %, jarak cap inti 2,4 / 3,6 / 4,8 m, varian (a) (21 Nov 2026); **revisi 22 Nov 2026 (atas delegasi):** telapak cap yang bertumpang digabung, berat cap dikurangi apung dimasukkan |
| 6.4 Tebing P-2 | Profil Zhang sebagai beban kinematik 6.5, Youd batas bawah (21 Nov 2026) |
| 6.5 Lateral | Kepala tiang sendi, EI 0,5, U5 pengali p 0,1 (22 Nov 2026) |
| 6.6 Penurunan | Varian (d) kalibrasi uji beban sebagai dasar, (a)/(b) batas atas (22 Nov 2026) |
| 6.7 Desain struktur | f'c tiang 35 MPa 16 D25, spiral D13 40/80 mm; cap kolom 1.000 / 800 / 950 mm (2/3/4 tiang); tulangan cap kolom dipotong di -17,76; pit varian A (22 Nov 2026); **Cap E gabungan didesain sebagai pelat di atas pegas tiang, h 2.000 mm** (atas delegasi) |
| 6.8 Uji dan pelaksanaan | Program uji SNI 8460 9.8 tetap di Tahap 6 (rinci ke RKS Tahap 7), 2 uji statik konstruksi 200 % × izin, 1 tarik, 1 lateral; dewatering sump / parit; T113 CSL ulang + coring (22 Nov 2026) |
| 6.9 Model BIM | Cap C digabung ke Cap E; model LOD 300 319 tiang, 83 cap (atas delegasi, 22 Nov 2026) |
| 6.10 Gambar | GS-28..GS-32 dan GT-16 (atas delegasi, 22 Nov 2026) |

## 2. Angka kunci (keadaan akhir)

| Unsur | Angka | Sumber |
|---|---|---|
| Tiang | Bor Ø800, kepala +12,05 - h cap + 0,15, ujung -27,60; Qult statis/gempa selatan 4.770 / 3.294 kN, utara 4.565 / 3.305 kN | 6.1 |
| Gesekan negatif | Bidang netral -13,71 / -14,00 (statis), -16,72 / -16,50 (pasca-likuifaksi); Q + Qn ±2.930-3.003 kN | 6.2 |
| Jumlah tiang | Gedung utama **251** (cap kolom 143, cap inti 108), utilitas 68, total **319**; 83 cap (Tahap 3: 373 tiang). Desain akhir sesudah 7.3: **321 tiang (253 utama), 84 cap** | 6.3 revisi, 6.9, 7.3 |
| Cap E gabungan | Cap C + Cap E + 4/B, 4/C, 7/B, 7/C: 54 tiang, 30,4 × 13,6 m, h 2.000 (dasar +10,05); pons inti 0,955 (penentu), geser 0,739, STM lokal 0,687; tulangan bawah D32 x 2 lapis @150, y 1 lapis @175 | 6.7 |
| Tebing P-2 | FK Bishop dengan berm + pelandaian: 1,22 / 1,22 / 0,74 / 1,03 / 0,68 (muka rendah / surut / gempa / kh 50 % / pasca-likuifaksi); serakan Zhang 4,58 m, Youd 0,19 m | 6.4 |
| Lateral | Inersia 52,45 kN/tiang (251 tiang), M maks 130,7 kNm (rasio 0,12); Youd 966 kNm (rasio 0,86); Zhang tidak tertahan | 6.5 revisi |
| Penurunan | Varian (d) δ maks 24,6 mm (4/F - 4/G); SL-1 rasio 0,65, SL-2 / SL-3 0,76 / 0,74 | 6.6, 6.7 revisi |
| Uji tiang | TP-1..4 k 489 kN/mm, s 200 % 4,45-5,09 mm, sisa 1,78-2,42 mm; 1.822 kN membuktikan FK 2,0 pada 911 kN saja | 6.8 |
| Pit L-1..4 | t 0,45 FK 1,110 ≥ 1,1 (SNI 8460 9.3.4); berdiri di dalam Cap E | 6.7 |
| Model dan gambar | `model/RSTB-STR-T6-LOD300.*` 319 IfcPile BORED, 83 IfcFooting PILE_CAP; 6 lembar CADCraft cad_cek 0 | 6.9, 6.10 |

## 3. Cek silang (VERIFIKASI.md)

| No | Langkah | Hasil |
|---|---|---|
| T-98 | 6.0 telaah | Lolos |
| T-99 | 6.1 daya dukung | Lolos |
| T-100 | 6.2 gesekan negatif | Lolos |
| T-101 | 6.3 tata letak (revisi gabung + berat cap) | Lolos |
| T-102 | 6.4 tebing | **Gagal** butir (a): Bishop vs Spencer 6,94 % > 5 % pada kh 50 % tanpa perkuatan (Spencer lebih tinggi) |
| T-103 | 6.5 lateral | Lolos |
| T-104 | 6.6 penurunan | Lolos (GeoFEM3D 24,4 % dari batas 25 %, tipis) |
| T-105 | 6.7 struktur (termasuk pelat vs cap kaku) | Lolos |
| T-106 | 6.8 uji dan dewatering | **Gagal** butir (c): sumur ekuivalen vs aliran 1-D 211 % > 100 %; debit desain dari sumur ekuivalen (konservatif) |
| T-107 | 6.9 IFC vs rencana | Lolos (jumlah 0 selisih, volume tiang -0,17 %) |

Nomor rencana bergeser: Excel = Python menjadi T-108 (dipenuhi tiap langkah lewat butir (b) di T-99..T-107).

## 4. Temuan dan yang masih terbuka (dibawa ke Tahap 7, lihat `07 DED dan RKS/00 Rencana Tahap 7.md`)

1. **Serakan lateral Zhang 4,58 m tidak tertahan tiang Ø800.** Perbaikan tanah U5 di jalur tebing atau tiang batas
   Ø600 menjadi syarat; perkuatan tebing belum digambar (GT-16 hanya berm + pelandaian, FK gempa 0,74 dan
   pasca-likuifaksi 0,68 di bawah izin).
2. **Dua kesalahan sistematis 6.3 ditemukan di 6.9** dan sudah diperbaiki: telapak cap bertumpang (Cap C di dalam Cap E)
   dan berat cap tidak masuk beban tiang. Jumlah tiang gedung utama berubah 244 → 251.
3. Pit L-5..6 dan L-7 sebagian di luar telapak Cap E (clash cap-pit 6); dirapikan di koordinasi 7.2.
4. Tulangan atas/samping cap kolom dan cap inti selain E di gambar berlabel [Asumsi] (tidak dihitung 6.7).
5. Uji tiang: beban uji akhir 3.166 / 2.886 kN, uji tarik dan lateral, dan kriteria lateral (model 6.5 y 15-26 mm >
   10 mm SNI 9.8.3) masuk RKS 7.7.
6. Acuan yang belum ada di `acuan/`: Fellenius, GEC12, Youd 2002, Zhang 2004, Idriss-Boulanger 2008, Spencer, Chin,
   Dupuit-Sichardt; k urugan belum diuji (asumsi tiga skenario).

## 5. Pelajaran proses

- Cek tumpang telapak dan berat sendiri harus masuk pada langkah tata letak, bukan ditemukan saat model BIM.
- Model STM per tiang tidak cocok untuk cap selebar rakit (rasio tidak monoton terhadap tebal); pelat di atas pegas
  tiang memberi hasil yang wajar dan reaksi tiang dalam 13 % dari cap kaku.
- Rantai 6.3 → 6.9 dijalankan ulang tiga kali (±2,3 jam). Cache per langkah dan uji per berkas menjaga waktunya.
