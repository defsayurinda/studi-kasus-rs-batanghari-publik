# Rencana Tahap 8: RAB (5D)

Status: draf, disetujui atas delegasi Defsa 22 Nov 2026 (Mode cepat). Data simulasi. 8a dan 8b selesai (T-119a/b, T-120, T-121c/d lolos; T-121a/b gagal toleransi, dijelaskan di Ringkasan Tahap 8).

## Pembagian

| Bagian | Isi | Keluaran |
|---|---|---|
| 8a | Volume otomatis dari model BIM LOD 300 (`model/RSTB-STR-T7-LOD300.ifc`, `model/RSTB-ARS-T7-LOD300.ifc`), tulangan dari rasio kg/m³, harga dasar, AHSP rinci pekerjaan utama, harga satuan ringkas sisanya | `skrip/tahap8_volume.py`, `08 RAB/8a Volume dan AHSP.xlsx` + `.md` |
| 8b | RAB (volume 8a × harga satuan), biaya SMKK, MEP dan pekerjaan di luar model sebagai persentase/lumsum, rekapitulasi, PPN, value engineering | `08 RAB/8b RAB SMKK VE.xlsx` + `.md` |

## Keputusan (atas delegasi Defsa 22 Nov 2026)

| No | Keputusan | Alasan / sumber |
|---|---|---|
| K8-1 | Volume dari Qto IFC (`Qto_*BaseQuantities` BIMCraft), bukan geometri ulang | Qto sudah ada di semua unsur beton/dinding/lantai; geometri ulang berat di laptop panas. Cek silang ke angka tahap lalu (T-119) |
| K8-2 | Volume RAB = volume bersih: balok di bawah pelat (h − 0,20) dan antar muka kolom (L − 0,75), kolom dikurangi tebal pelat 0,20, tiang dikurangi masuk cap 0,15 m | Cara hitung volume lazim RAB; volume kotor (tumpang di joint) hanya untuk T-119 |
| K8-3 | Tulangan dari rasio kg/m³ Tahap 3.6 (kolom 200, balok 180, pelat 100, dinding 140, pile cap 100, pelat LT1 110) [Asumsi]; tiang dari susunan 6.7 (16 D25 + spiral D13 40/80) | `IfcReinforcingBar` di IFC hanya contoh penulangan 7.5 (8.070 batang), tidak lengkap |
| K8-4 | AHSP rinci hanya pekerjaan utama (tiang bor, beton, besi, bekisting, dinding, plester, fasad, dewatering); sisanya harga satuan ringkas | Mode cepat: ±20 % item ≈ 80 % biaya; dicek T-120 |
| K8-5 | Biaya tidak langsung (umum + keuntungan) 12 % dari biaya langsung | Permen PUPR 8/2023 Pasal 11 ayat (3) hal. 9: 10-15 % |
| K8-6 | Koefisien bahan/upah AHSP Cipta Karya: lampiran Permen PUPR 8/2023 di `acuan/` berupa pindaian (tidak terbaca), jadi koefisien berlabel [Asumsi: koefisien umum AHSP CK]; koefisien alat bor dari contoh SE Dirjen Binkon 47/2026 Lampiran II hal. 187-188 | Survei harga SE 47/2026 Lampiran I belum dilakukan |
| K8-7 | Harga dasar [Asumsi: Jambi 2026]; MEP, entourage (mobil, pohon, huruf), air sungai dan lereng alami tidak dihitung di 8a | MEP di luar model ARS/STR; dihitung 8b |

## Cek silang (toleransi ditetapkan sebelum membandingkan)

| Kode | Besaran | Cara 1 | Cara 2 | Toleransi |
|---|---|---|---|---|
| T-119a | Volume beton tiang dan pile cap (m³) | Qto IFC STR 7.3 | T-107 (6.9) + perubahan 7.3 (2 tiang, perlebaran Cap E) | ≤ 1 % |
| T-119b | Volume beton struktur atas per kelompok (kolom, balok, pelat, dinding, tangga) | Qto IFC STR 7.3 | T-84 (4.5-4.8, IFC 4.9) | ≤ 5 % (perubahan Tahap 5 tangki dan 7.3 dijelaskan) |
| T-120 | Porsi biaya item AHSP rinci terhadap biaya langsung 8a | jumlah item rinci | jumlah semua item | ≥ 75 % |
| T-121a | Total RAB 8b (termasuk PPN) | RAB 8b | perkiraan Tahap 3.8 (`tahap3_biaya.rekap`) | -30 % s.d. +50 % [Asumsi: rentang akurasi estimasi konsep; AACE 18R-97 tidak ada di `acuan/`] |
| T-121b | Biaya pondasi + struktur (Rp, tanpa PPN) | RAB 8b divisi II + III | Tahap 3.8 `fondasi_nyata("A")` + `struktur_nyata()` dibagi (1 + PPN) | -30 % s.d. +50 % |
| T-121c | Rekapitulasi RAB | rumus Excel (dihitung Excel) | Python | ≤ 0,01 % |
| T-121d | Item 8a di divisi II-V | jumlah divisi | total 8a `daftar_pekerjaan()` | ≤ Rp 1 |

Toleransi T-121 ditetapkan 22 Nov 2026 sebelum angka 8b dihitung (atas delegasi Defsa).

## Keputusan 8b (atas delegasi Defsa 22 Nov 2026)

| No | Keputusan | Alasan / sumber |
|---|---|---|
| K8-8 | MEP RS = persentase biaya standar Tahap 3.8 (Permen PUPR 22/2018 Ps. 29 huruf a-i, k, l, u, kolom "pakai") + utilitas dasar 6,5 % biaya standar (rentang komponen 5-8 %), dibagi (1 + PPN) karena biaya standar sudah termasuk PPN | Sumber sama dengan 3.8, jadi pembanding T-121 tidak memihak; MEP di luar model ARS/STR |
| K8-9 | SMKK 9 komponen SE 47/2026 Lampiran III bagian B (hal. 236-243 dan 245-276), volume [Asumsi] untuk risiko besar, durasi 24 bulan; asuransi CAR 0,1 % (hal. 260); tanpa BTL | Permen PUPR 8/2023 Ps. 22 ayat (1) dan (3) hal. 12: SMKK biaya tersendiri, bukan Biaya Umum |
| K8-10 | Pematangan lahan (urugan, PVD, pasir, pemantauan) dari Tahap 3.8 `lahan_nyata()` dibagi (1 + PPN); dermaga ditunda (3.8 V3), interior/furnitur di anggaran alkes | Tidak ada di model BIM |
| K8-11 | PPN 11 % (sama 3.8, `tahap3_biaya.PPN`) | [Asumsi: tarif efektif] |
