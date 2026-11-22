# Ringkasan Tahap 8: RAB (5D)

Status: **disetujui Defsa 23 Nov 2026** (dikerjakan atas delegasi 22 Nov 2026, Mode cepat; ringkasan ditelaah Defsa). Data simulasi studi kasus. Harga [Asumsi: Jambi 2026], belum survei harga.

## 1. Hasil

| Bagian | Isi | Keluaran |
|---|---|---|
| 8a | Volume otomatis dari Qto IFC STR 7.3 / ARS 7.1, AHSP rinci 12 item (85,1 % biaya), BTL 12 % | `skrip/tahap8_volume.py`, `8a Volume dan AHSP.xlsx` + `.md` |
| 8b | RAB 6 divisi + SMKK, PPN, rekap rumus Excel, VE 5 butir, T-121 | `skrip/tahap8_rab.py`, `8b RAB SMKK VE.xlsx` + `.md` |

| Divisi | Rp miliar | Porsi |
|---|---:|---:|
| I Persiapan | 8,55 | 3,3 % |
| II Tanah dan pondasi (321 tiang bor Ø800, 84 cap) | 48,40 | 18,8 % |
| III Struktur atas | 26,44 | 10,3 % |
| IV Arsitektur (fasad, dinding, lantai, plafon) | 42,37 | 16,4 % |
| V Tapak dan pematangan lahan | 16,61 | 6,4 % |
| VI MEP RS (persen Permen PUPR 22/2018 Ps. 29) | 112,72 | 43,7 % |
| VII SMKK (9 komponen SE 47/2026) | 2,76 | 1,1 % |
| Jumlah | 257,86 | |
| PPN 11 % | 28,36 | |
| **Total dibulatkan** | **286,22** | **Rp 14,81 juta/m² (19.328 m²)** |

## 2. Pagu dan value engineering

- Pagu owner Rp 168 miliar = 12.000 m² × Rp 14 juta (TOR). RAB Rp 286,2 miliar: selisih Rp 118,2 miliar.
- Biaya per m² (Rp 14,81 juta) hanya 6 % di atas asumsi owner; penyebab selisih adalah **luas**: program ruang RS + gedung parkir menghasilkan 19.328 m² kotor, bukan 12.000 m². Pagu cukup untuk ±11.345 m².
- VE (tanpa analisis struktur ulang): VE-1 spiral tiang D13-80 → D13-150 di bawah 6 m atas (Rp 1,92 miliar, syarat cek perencana SNI 2847), VE-2 curtain wall stick (Rp 2,80 miliar), VE-3 acian langsung bata ringan (Rp 3,07 miliar), VE-4 dek helipad tahap 2 (Rp 3,20 miliar), VE-5 lantai rawat inap HT (Rp 0,20 miliar). Total Rp 11,19 miliar (3,9 %) → Rp 275,0 miliar.
- Rekomendasi (atas delegasi Defsa): owner menaikkan pagu ke ±Rp 275 miliar dengan VE-1..VE-5, atau membangun bertahap memakai opsi lingkup 3.8 (V1 podium LT3, V5 LT4 parkir, V6 LT6 cangkang). Keputusan pada owner.

## 3. Cek silang

| Kode | Hasil | Catatan |
|---|---|---|
| T-119a/b | lolos | volume IFC vs tahap lalu |
| T-120 | lolos | AHSP rinci 85,1 % biaya |
| T-121a | **gagal** (-36,6 %; batas -30 s.d. +50 %) | Perkiraan konsep 3.8 (Rp 451 miliar) menumpuk nonstandar Ps. 29 termasuk interior 15 % dan lingkungan 5 % di atas biaya standar HSBGN yang sudah memuat struktur/arsitektur, ditambah fondasi dalam Rp 77,6 miliar dan kontinjensi 5 %. RAB menghitung volume nyata; interior/furnitur ada di anggaran alkes (K8-10) |
| T-121b | **gagal** (-38,8 %) | 3.8 memakai 373 tiang (3.7) dengan ±Rp 177 juta/tiang; desain akhir 321 tiang (6.7/7.3) dengan ±Rp 107 juta/tiang (bor + besi). Struktur 3.8 Rp 40,9 miliar tanpa PPN (termasuk pelat dasar + sloof) vs 8b divisi III Rp 26,4 miliar (pelat dasar, sloof di divisi II) |
| T-121c | lolos | total rumus Excel = Python (selisih 0,0000 %) |
| T-121d | lolos | 38 kode item 8a utuh di divisi II-V (Rp 113,23 miliar, selisih Rp 0) |

Kegagalan T-121a/b tidak mengubah RAB: estimasi konsep 3.8 terbukti konservatif dan kini digantikan RAB dari model. Pelajaran: estimasi konsep fondasi dalam perlu harga per tiang dari AHSP, bukan harga lumsum.

## 4. Butir terbuka

- O8-1: survei harga SE 47/2026 Lampiran I (semua harga masih [Asumsi: Jambi 2026]).
- O8-2: MEP masih persentase; RAB MEP rinci menunggu konsultan MEP (model MEP 7.2 hanya koordinasi).
- O8-3: VE-1 perlu cek tulangan transversal tiang oleh perencana; VE-2..VE-5 perlu persetujuan owner.
- O8-4: keputusan owner tentang pagu/lingkup (dibawa ke Tahap 10 laporan).
- Langkah berikutnya: Tahap 9 Jadwal (satu Gantt + kurva S dari bobot RAB 8b).
