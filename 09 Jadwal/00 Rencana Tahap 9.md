# Rencana Tahap 9: Jadwal (4D ringkas)

Status: draf, disetujui atas delegasi Defsa 23 Nov 2026 (Mode cepat). Data simulasi. Satu sesi, tanpa simulasi 4D.

## Keluaran

| Keluaran | Berkas |
|---|---|
| Skrip jadwal (CPM sederhana + bobot RAB + kurva S) | `skrip/tahap9_jadwal.py` |
| Gantt + kurva S (satu gambar) | `09 Jadwal/9 Gantt dan Kurva S.png` / `.pdf` |
| Excel 4 lembar (Ringkasan, Kegiatan, Kurva S, Verifikasi dan Acuan), bobot dan kurva S rumus hidup | `09 Jadwal/9 Jadwal dan Kurva S.xlsx` + `.md` |
| Berkas ProjectLibre (MSPDI XML) | `09 Jadwal/9 Jadwal.xml` |
| Ringkasan | `09 Jadwal/Ringkasan Tahap 9.md` |

## Keputusan (atas delegasi Defsa 23 Nov 2026)

| No | Keputusan | Alasan / sumber |
|---|---|---|
| K9-1 | Satuan waktu minggu (6 hari kerja); mulai kontrak 3 Jan 2028 [Asumsi] (semula 4 Jan 2027; digeser K10-8 karena mendahului Laporan Antara Apr 2027); 1 bulan = 52/12 minggu | Kurva S mingguan lazim di laporan kemajuan proyek gedung |
| K9-2 | Bobot kegiatan = biaya RAB 8b (divisi I-VI + SMKK, sebelum PPN) / jumlah, diambil dari `tahap8_rab.rab()`/`rekap()` tanpa hitung ulang volume | PPN merata, tidak mengubah bobot |
| K9-3 | Durasi tiang bor dari produktivitas mesin bor SE Dirjen Binkon 47/2026 Lamp. II hal. 187-188 (`tahap8_volume.koef_bor`, 0,154 jam/m'), 2 rig (P4 RAB), 8 jam efektif/hari [Asumsi] | Satu-satunya produktivitas alat yang bersumber; sisanya [Asumsi: praktik gedung beton 6 lantai] |
| K9-4 | Struktur atas 7 kegiatan per lantai (LT1-LT6 + atap), biaya divisi III dibagi merata per lantai [Asumsi]; siklus 5 minggu podium LT1-LT3, 4 minggu LT4-atap [Asumsi] | Volume beton divisi III ±4.990 m³ → ±710 m³ per lantai ≈ 150-180 m³/minggu dengan 2 tower crane |
| K9-5 | MEP non-lift dibagi instalasi kasar 60 % / alat utama + finishing 40 % [Asumsi]; lift (M-LIF + pintu lift) kegiatan tersendiri setelah atap | Pola pemasangan MEP RS; RAB MEP masih persentase (O8-2) |
| K9-6 | Sewa tower crane (P5), manajemen lapangan (P2, P6, P7) dan SMKK sebagai kegiatan ringkas (hammock): biaya merata sepanjang masa pakainya | Biaya waktu, bukan volume |
| K9-7 | Hubungan kegiatan FS/SS dengan jeda (lag); lintasan kritis dari CPM maju-mundur | Tumpang tindih arsitektur/fasad/MEP dengan struktur |

## Cek silang (toleransi ditetapkan sebelum menghitung)

| Kode | Besaran | Cara 1 | Cara 2 | Toleransi |
|---|---|---|---|---|
| T-122a | Σ bobot kegiatan | rumus Excel (dihitung Excel) | Python | 100 % ± 0,01 % |
| T-122b | Σ biaya kegiatan | jadwal | jumlah RAB 8b I-VII | ≤ Rp 1 |
| T-122c | Kumulatif kurva S minggu akhir | rumus Excel | Python | 100 % ± 0,01 % |
| T-123 | Durasi tiang bor | produktivitas SE 47/2026 | pembanding praktis 1 tiang/rig/hari [Asumsi] | ± 30 % |
| T-124 | Durasi lintasan kritis | CPM | durasi SMKK 24 bulan (RAB 8b) | -15 % s.d. 0 % |
| T-125 | Masa pakai tower crane (struktur LT1 s.d. fasad selesai) | jadwal | sewa 18 bulan (P5 RAB 8b) | ± 15 % |
