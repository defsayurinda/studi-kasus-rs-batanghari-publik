# Draf halaman portofolio: RS Tepian Batanghari (belum terbit)

Status: isi disetujui Defsa 23 Nov 2026 (K10-6), belum terbit. Terbit ke `situs/` (repo `geosr-lab/portofolio`) pada sesi 4 setelah
Defsa menelaah dan `python "90 Catatan Kerja AI/pindai_privasi.py"` bersih. Gambar di bawah ditautkan langsung ke berkas
repo ini; saat terbit, salin ke folder aset situs dengan nama pendek (daftar di bagian akhir).

---

## Rumah Sakit 6 Lantai di Tanah Lunak Tepi Sungai: dari Bor Tanah sampai RAB dan Jadwal

*Studi kasus perencanaan terpadu (data simulasi), alur openBIM: BIMCraft, CADCraft, IfcOpenShell, OpenSees, Blender, Python.*

![Render eksterior dari arah Sungai Batanghari](<../07 DED dan RKS/Render/R-01.png>)

| Angka kunci | |
|---|---|
| Gedung | RS tipe C, 150 TT, gedung utama 6 lantai + gedung utilitas/parkir 4 lantai, 19.328 m² |
| Tanah | lempung lunak, gambut sampai 3,7 m, pasir U5 mudah likuifaksi (kelas situs SF) |
| Pondasi | 321 tiang bor Ø800 sedalam ±38 m, 84 pile cap |
| Dokumen | model IFC federasi, 64 lembar DED, RKS 15 bab |
| Biaya | RAB Rp 286,22 miliar (Rp 14,81 juta/m²), volume otomatis dari model |
| Waktu | jadwal CPM 98 minggu, mulai 3 Jan 2028 |

### Masalah

Rumah sakit tipe C 150 TT di tepi Sungai Batanghari, di atas lempung lunak, gambut sampai 3,7 m, dan pasir yang mudah
likuifaksi, di lahan yang tergenang banjir 50 tahunan. Pagu owner disusun untuk 12.000 m², padahal program ruang
butuh 19.328 m².

### Yang saya kerjakan

1. **Data tanah.** Mengolah data penyelidikan dan menemukan tujuh kesalahan data penyedia sebelum dipakai; menetapkan
   parameter U1-U8, kelas situs SF, dan evaluasi likuifaksi pasir U5 (FS 0,22-0,75).
2. **Desain konsep.** Peil +12,85 dari analisis banjir yang dikoreksi, urugan bertahap dengan PVD, dan menolak
   basement (FK blow-in 0,97-1,14 < 1,25); parkir dipindah ke gedung 4 lantai.
3. **Struktur atas.** Analisis respons spesifik situs dengan tujuh rekaman sintetis, model 3D OpenSees gedung kategori
   risiko IV / KDS D; desain pelat, balok SRPMK, kolom, dan dinding geser.
4. **Pondasi.** 321 tiang bor Ø800 dengan gesekan negatif, serakan lateral akibat likuifaksi, dan penurunan yang
   dikalibrasi uji beban (maksimum 24,6 mm); perkuatan tebing sungai P-2.
5. **BIM dan DED.** Model federasi IFC4 arsitektur-struktur-MEP, cek clash (1.612 → 1.156 pasangan, sisa dinilai),
   64 lembar DED di CADCraft, RKS, dan render Blender langsung dari IFC.
6. **RAB.** Volume otomatis dari Qto IFC, AHSP rinci untuk pekerjaan utama, SMKK, dan rekayasa nilai VE-1..VE-5 hemat
   Rp 11,19 miliar (+ usul VE-6 ±Rp 2,10 miliar).
7. **Jadwal.** CPM 21 kegiatan, 98 minggu, Gantt dan kurva S dengan bobot dari RAB.

### Galeri

![Penampang geoteknik A-A'](<../02 Olah Data Tanah/Gambar/GT-02 Penampang A-A'.png>)
*Penampang geoteknik: lapisan lunak dan pasir U5 yang mudah likuifaksi.*

![Evaluasi likuifaksi pasir U5](<../02 Olah Data Tanah/Gambar/GT-12 Likuifaksi Pasir U5.png>)
*Evaluasi pemicu likuifaksi: seluruh pasir U5 mencair pada gempa rencana.*

![Ragam getar 1 model OpenSees](<../04 Struktur Atas/Gambar/Analisis 3D/02_ragam_1.png>)
*Model 3D OpenSees, ragam 1 (T = 0,684 detik).*

![Deformasi gempa arah X](<../04 Struktur Atas/Gambar/Analisis 3D/05a_deformasi_gempa_X.png>)
*Deformasi akibat gempa statik ekivalen arah X (V = 13.164 kN).*

![Bidang netral tiang bor](<../06 Struktur Bawah dan Basement/Gambar/6.2 Kurva A B Selatan.png>)
*Bidang netral dan gesekan negatif tiang bor Ø800.*

![Peta penurunan pile cap](<../06 Struktur Bawah dan Basement/Gambar/6.6 Peta Penurunan (d).png>)
*Peta penurunan kepala pile cap terkalibrasi uji beban.*

![Model BIM pondasi](<../06 Struktur Bawah dan Basement/Gambar/6.9 Model Pondasi 3D.png>)
*Model BIM pondasi LOD 300: 321 tiang dan 84 pile cap.*

![Render helipad](<../07 DED dan RKS/Render/R-06.png>)
*Render dari IFC federasi: atap dan helipad.*

![Render senja](<../07 DED dan RKS/Render/R-04.png>)
*Render senja: lobi dan gerbang utara.*

![RAB per divisi dan rekayasa nilai](<Gambar/RAB per Divisi dan VE.png>)
*RAB per divisi dan penghematan rekayasa nilai.*

![Gantt dan kurva S](<../09 Jadwal/9 Gantt dan Kurva S.png>)
*Jadwal CPM 98 minggu dan kurva S.*

### Temuan yang mengubah desain

- Banjir rencana penyedia 0,65 m terlalu rendah; peil dinaikkan ke +12,85.
- Data gempa penyedia memuat lapisan Vs palsu di 46-47 m; masukan respons situs dipindah ke batuan SB ±85 m.
- Shaft MEP owner jatuh tepat di kolom (ketahuan dari clash) dan digeser.
- Pagu disusun untuk 12.000 m², padahal program ruang butuh 19.328 m²: yang perlu diputuskan adalah luas, bukan harga
  satuan (biaya per m² hanya 6 % di atas asumsi owner).
- Audit akhir menemukan RKS masih memakai jumlah tiang lama (319); diperbaiki ke 321 sebelum terbit.

### Cara kerja

Setiap angka bersumber SNI/pasal atau berlabel [Asumsi]/[Literatur] dan dicek silang dua cara (T-06 s.d. T-127,
termasuk yang gagal beserta penjelasannya); keputusan dicatat per tahap; semua dokumen dibangun ulang dari skrip Python
dan diuji. Dokumen simulasi untuk portofolio, tidak untuk konstruksi.

**Unduh:** Laporan Akhir (PDF, 52 hal.), Laporan Audit Akhir (PDF), set DED (PDF).

---

Aset untuk `situs/` saat terbit (nama pendek): `R-01.png`, `R-04.png`, `R-06.png`, `gt-02.png`, `gt-12.png`,
`ragam-1.png`, `deformasi-x.png`, `bidang-netral.png`, `penurunan.png`, `pondasi-3d.png`, `rab-ve.png`,
`9-gantt-kurva-s.png`. Perkecil ke lebar ±1.600 px.
