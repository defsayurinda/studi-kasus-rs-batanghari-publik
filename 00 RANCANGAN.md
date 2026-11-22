# Studi Kasus Terpadu: rancangan

Rangkuman diskusi Defsa dengan Claude (sesi 18 November 2026). Berkas ini sumber keputusan proyek;
kalau ada yang berubah, ubah di sini dan catat di `PROGRES.md`.

## 1. Tujuan

- Portofolio utama dan pertama: satu studi kasus utuh dari perencanaan sampai serah terima dan perawatan.
- Sekaligus media belajar teknik sipil dan AI. Defsa insinyurnya, AI asistennya.
- Hasil terbit di GitHub (repo publik + halaman di situs `geosr-lab/portofolio`), bisa dilihat, dipahami, dan diunduh.
- Hasil harus benar dan bisa diverifikasi walaupun dibantu AI.

## 2. Skenario

| Butir | Keputusan |
|---|---|
| Bangunan | Rumah sakit tipe C, 6 lantai + 1 basement |
| Lokasi | Tepi Sungai Batanghari, Jambi (lahan fiktif, bukan persil nyata) |
| Tantangan utama | Kategori risiko IV (SNI 1726), basement di tanah lunak/gambut dengan muka air tinggi, banjir dan tebing sungai, bangunan tua di sebelah, owner rumah sakit yang sering berubah |
| Di luar lingkup | Desain MEP (hanya beban, ruang, dan lubangnya) |
| Data | Simulasi yang sengaja bermasalah (tanah, struktur, keinginan owner, kejadian lapangan), rentang parameter dari literatur Jambi, diberi label sumber |
| Kesulitan | Super sulit, tapi adil: setiap masalah punya bukti di data dan penyelesaian yang bisa dipertanggungjawabkan |
| Petunjuk | Masalah tersembunyi; petunjuk bertingkat boleh diminta kalau macet; kunci dibuka per tahap |
| Kunci jawaban | `02 Siap Terbit/privat/studi-kasus-kunci/`, dibuat di sesi skenario terpisah yang tidak dibaca Defsa |

## 3. Rilis dan tahap

**v1.0 Perencanaan (target sekitar 1 bulan, kerja intensif)**

| No | Tahap | Folder |
|---|---|---|
| 0 | Kerangka acuan: tanggapan TOR owner, program ruang RS, asumsi, daftar SNI | `00 Kerangka Acuan/` |
| 1 | Penyelidikan tanah dan tapak: telaah topografi, sondir, bor, SPT, lab (data simulasi); usulan penyelidikan tambahan | `01 Penyelidikan Tanah/` |
| 2 | Olah data tanah: stratigrafi, parameter desain, kelas situs gempa, potensi likuifaksi, sensitivitas | `02 Olah Data Tanah/` |
| 3 | **Desain konsep (pra-rencana)**: BEP dan template BIM; kajian aturan tapak (KDB, KLB, GSB, sempadan sungai) dan perizinan (PBG); peil lantai terhadap banjir, urugan, drainase; zonasi dan sirkulasi RS; denah tipikal dan basement; grid kolom; pemilihan sistem struktur; pra-dimensi; alternatif pondasi dan metode galian; presentasi konsep ke owner. Model BIM LOD 200 | `03 Desain Konsep/` |
| 4 | Struktur atas: pembebanan (termasuk beban alat RS dan MEP), gempa, analisis, desain balok, kolom, pelat, dinding geser, tangga, atap | `04 Struktur Atas/` |
| 5 | Struktur tengah: sloof, tie beam, pelat basement | `05 Struktur Tengah/` |
| 6 | Struktur bawah dan basement: tiang, pile cap, gesekan negatif akibat urugan, dinding penahan galian, dewatering, uplift, penurunan, stabilitas tebing sungai | `06 Struktur Bawah dan Basement/` |
| 7 | DED dari model BIM dan RKS (spesifikasi teknis); model arsitektur lengkap dan **render akhir setara portofolio** (lihat di bawah) | `07 DED dan RKS/` |
| 8 | RAB (5D): volume bersih dari model (termasuk pekerjaan tanah dan urugan), AHSP SE 47/2026, harga survei Jambi, SMKK, value engineering | `08 RAB/` |
| 9 | Jadwal (4D): kalender kerja, durasi dari volume dan produktivitas, kurva S, simulasi | `09 Jadwal/` |
| 10 | Laporan pendahuluan, antara, akhir; matriks verifikasi; halaman portofolio | `10 Laporan/` |

**Render akhir dan arsitektur Tahap 7 (arahan Defsa 20 Nov 2026): hasil harus bagus, lengkap, dan keren untuk
portofolio.** Acuan gaya: foto `acuan/privat/Referensi Fasad RS dari Defsa.jpg` (hanya acuan) dan purwarupa
`model/RSTB-ARS-T4-Fasad-V4.bimc` (render `04 Struktur Atas/Gambar/4.10 Fasad V4 *.png`). Isi minimum:
- fasad menara panel putih berjendela pita, pita kaca biru vertikal, dinding tirai; podium panel abu; mahkota menara;
- nama "RUMAH SAKIT TEPIAN BATANGHARI" dan logo "H" yang terbaca jelas, papan nama di gerbang dan lobi, penanda IGD;
- lingkungan lengkap: halaman, taman dalam atap V1, pohon, parkir dan mobil, jalan masuk dan drop-off berkanopi, ramp
  IGD beratap, pagar dan gerbang, lampu jalan, tepi sungai dan tebing, gedung utilitas, dek helipad;
- render fotorealistis beberapa sudut (siang, senja, mata burung, depan lobi, IGD) dengan pencahayaan, bayangan, dan
  langit; tidak hanya render BIMCraft yang datar. Alat: Blender + Bonsai (IFC dari BIMCraft) atau penampil lain yang
  hasilnya lebih baik, dengan sumber model tetap BIM.
- Struktur tidak diubah oleh fasad; beban fasad akhir dicek ulang terhadap rincian 4.10 (angkur, balok tepi).

Jenjang laporan sesuai TOR owner: **laporan pendahuluan** setelah Tahap 0–1, **laporan antara** (konsep struktur
dan pondasi, parameter tanah desain) setelah Tahap 2–3, **laporan akhir** (DED, RAB, RKS, jadwal, model BIM,
perhitungan) setelah Tahap 4–9. Ketiganya disusun di `10 Laporan/`.

**v2.0 Pelaksanaan sampai perawatan (menyusul):** dokumen tender (dokumen pemilihan, BoQ kosong), metode kerja dan K3,
pelaksanaan simulasi (uji tiang PDA/loading test, monitoring galian, temuan lapangan, change order,
laporan mingguan), as-built, serah terima PHO/FHO, masa pemeliharaan, manual perawatan (BIM 7D, COBie).

## 4. Siklus kerja tiap tahap (satu sesi per tahap)

1. Buka sesi baru, beri nama `SK-0X <nama tahap>`, mulai dengan: *"Baca PROGRES.md, kita lanjut tahap X."*
2. Belajar konsep tahap itu (AI sebagai tutor).
3. Terima dokumen/data tahap.
4. Defsa mengerjakan inti sendiri (Excel, BIMCraft, Python).
5. AI memeriksa dan membuat cek silang; isi `VERIFIKASI.md`.
6. Rapat simulasi bila ada kejadian (AI berperan owner, MK, atau reviewer).
7. Buka kunci tahap, bahas masalah yang terlewat.
8. Tulis ringkasan tahap, perbarui `PROGRES.md`, commit.

## 5. Peran AI dan Defsa

| AI | Defsa |
|---|---|
| Tutor konsep, pemeriksa hitungan dan pasal SNI, asisten hitung (Excel/Python), cek silang, pembangkit data skenario, pemeran owner/MK/reviewer, penulis draf, pembangun halaman situs | Keputusan teknis, pemodelan inti di BIMCraft, hitungan inti sebelum melihat versi AI, pemahaman sampai bisa menjelaskan tanpa AI, persetujuan angka akhir |

## 6. Alat (openBIM, sebagian besar open source)

| Kebutuhan | Alat | Lokasi |
|---|---|---|
| Pemodelan BIM utama | BIMCraft 0.12.0 (meniru alur Revit, bisa dikendalikan AI lewat MCP) | `alat/bimcraft/` |
| 4D, 5D, gambar, cadangan pemodelan | Blender 5.2.4 LTS + Bonsai 0.9.0 | `alat/blender/` |
| Alternatif BIM dan FEM | FreeCAD 1.1.4 | `alat/freecad/` |
| Peta lokasi | QGIS 3.44 LTR | dipasang di sistem |
| Jadwal | ProjectLibre | dipasang di sistem |
| Analisis struktur | OpenSeesPy + opstool (utama), PyNite (cek silang), awatif.co/app (GUI web, statik linear) | `.venv` |
| Desain beton | Excel/Python sendiri (SNI 2847), concreteproperties, sectionproperties | `.venv` |
| Geoteknik | GeoFEM3D (buatan Defsa), groundhog, openpile, pygef, PySlope; PLAXIS 3D hanya cek silang | `.venv`, `GeoFEM3D/` |
| BIM lewat skrip | IfcOpenShell | `.venv` |
| Gambar 2D | LibreCAD | dipasang di sistem |
| Laporan | Word, Excel | dipasang di sistem |

Penghubung antaralat: IFC. Alur: BIMCraft (model, DED, tulangan, volume) → IFC → Bonsai (4D/5D) dan
Python (tiang, tanah, bekisting, RAB). Kunci satu versi BIMCraft selama proyek.

Tidak ada pengganti SAP2000/ETABS open source yang setara. Analisis memakai OpenSeesPy dan desain SNI disusun sendiri.

## 7. Validasi

- Bedakan verifikasi (hitungan benar) dan validasi (metode cocok dengan kenyataan). Metode divalidasi
  dengan contoh soal buku dan solusi analitik sebelum dipakai.
- Setiap angka penting dihitung minimal dua cara (lihat contoh di `VERIFIKASI.md`). Batas toleransi
  ditetapkan sebelum menghitung: struktur ≤5–10%, geoteknik ≤15–20%.
- Cek akal sehat: rasio besi, beban per m², ukuran kolom, harga per m² terhadap HSBGN.
- Skrip Python punya uji pytest di `tests/`.
- Pengaman AI: tidak ada angka tanpa sumber (pasal SNI/halaman buku, dicek ke dokumen di `acuan/`),
  Defsa menghitung inti lebih dulu, reviewer AI di sesi segar tanpa konteks, AI bukan sumber akhir.
- Tinjauan dosen untuk parameter tanah, basement, dan pondasi di akhir v1.0.

## 8. Publikasi

- Selama dikerjakan: repo Git privat. Setelah selesai: repo publik + halaman di situs portofolio.
- Berkas besar (>20 MB: IFC, PDF DED, video 4D) lewat GitHub Releases.
- Lisensi: kode MIT; gambar, laporan, data CC BY 4.0. DOI Zenodo opsional.
- Setiap lembar gambar diberi cap "STUDI KASUS PORTOFOLIO — TIDAK UNTUK KONSTRUKSI".
- `DISCLAIMER.md`: sifat proyek (skenario simulasi), tidak untuk konstruksi, penggunaan AI (spesifik),
  perangkat lunak yang dipakai.
- Pindai privasi sebelum terbit (`python "90 Catatan Kerja AI/pindai_privasi.py"`).
- Opsional setelah selesai: skenario dan kunci jawaban diterbitkan sebagai paket latihan.

## 9. Perubahan rancangan

- 18 Nov 2026: Tahap 3 Desain Konsep disisipkan (sebelumnya alur loncat dari olah data tanah ke struktur atas);
  tahap sesudahnya bergeser satu nomor. RKS dipindah dari v2.0 ke Tahap 7 karena TOR meminta RKS di laporan akhir.
  Jenjang laporan pendahuluan/antara/akhir, kajian perizinan, peil banjir, urugan, likuifaksi, dan tebing sungai
  ditambahkan ke tahap yang sesuai.

## 10. Keputusan yang masih terbuka

- Nama proyek dan repo (usulan: `studi-kasus-rs-batanghari`).
- Dokumen acuan yang belum ada (lihat `acuan/README.md`).
- Dosen peninjau.
