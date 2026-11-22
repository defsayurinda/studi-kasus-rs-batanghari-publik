# Format laporan (Word) dan Excel

Wajib untuk semua keluaran proyek. Sumber: *Panduan Laporan Praktikum Mekanika Tanah* (Teknik Sipil UNJA),
contoh Defsa `BAB IV_Defsa.docx` (laporan KP), dan `EXCEL IGC 2026 HIMATESI UNJA LOLOS TAHAP 1.xlsx`.
Pembantu kode ada di `skrip/format_dokumen.py`; pakai modul itu, jangan memformat ulang dari nol.

Empat hal yang paling sering salah (catatan Defsa, 19 Nov 2026):
1. Inden subbab, anak subbab, dan butir bertingkat tidak rapi.
2. Ukuran sel Excel tidak proporsional (lebar kolom dan tinggi baris).
3. Lupa *freeze panes* di Excel.
4. Bentuk tabel di Word salah (garis vertikal, keterangan tidak di tempatnya).

## Word

**Halaman dan huruf**
- A4, margin kiri 4 cm, atas 3, kanan 3, bawah 3 (Panduan: 4-3-3-3).
- Times New Roman 12, rata kanan-kiri (*justify*), spasi 1,5, *before/after* 0.
- Istilah asing ditulis miring. Desimal koma, ribuan titik. Berat dan volume 3 desimal; waktu dan persen 2 desimal.

**Bab dan subbab** (maksimal 3 level; nomor level 2 dan 3 tanpa titik di akhir)

| Unsur | Bentuk | Inden | Jarak |
|---|---|---|---|
| Bab | `BAB IV` dan judul di baris berikutnya, kapital, tebal, tengah; selalu halaman baru | - | 24 pt ke subbab pertama |
| Subbab level 2 | `4.1` + tab + judul, tebal | nomor di margin, judul di 1,25 cm (gantung 1,25) | 12 pt antar-subbab level 2 |
| Subbab level 3 | `4.1.1` + tab + judul, tebal | sama dengan level 2 | 6 pt dari level 2 ke 3 dan antar-level 3 |
| Paragraf biasa | - | baris pertama menjorok 1,25 cm | 0 |

**Butir bertingkat** (di bawah subbab level 3)

| Level | Penanda | Posisi penanda | Posisi teks |
|---|---|---|---|
| 4 | `1.` | margin (0 cm) | 0,75 cm |
| 5 | `a.` | 0,75 cm | 1,25 cm |
| 6 | `1)` | 1,25 cm | 1,75 cm |
| 7 | `a)` | 1,75 cm | 2,25 cm |

Paragraf penjelasan di bawah butir mulai sejajar dengan teks butirnya (tanpa inden baris pertama).
Nomor ditulis sebagai teks + tab dengan inden gantung, tidak memakai daftar otomatis Word yang
penomorannya bisa menyambung antardaftar.

**Tabel**
- Keterangan di **atas** tabel: `Tabel 4.1` tebal, judul biasa, 11 pt, spasi 1, rata kiri.
- Isi tabel 11 pt, spasi 1. Kepala tebal, rata tengah, diulang di tiap halaman; baris tidak terpotong antarhalaman.
- **Tanpa garis vertikal**: hanya garis atas, garis bawah kepala, garis antarbaris, dan garis bawah tabel.
- Lebar tabel = lebar teks; lebar kolom ditetapkan per kolom (bukan *autofit*).
- Sumber di **bawah** tabel: `(Sumber: ...)` 10 pt, miring, spasi 1.
- Tabel lebar atau panjang dipindah ke lampiran dengan halaman lanskap; di bab cukup ringkasannya.

**Gambar**: rata tengah; keterangan di **bawah**, `Gambar 4.1` tebal + judul, 11 pt, spasi 1, tengah; sumber 10 pt.

**Rumus**: 12 pt, nomor `(4.1)` di kanan; `Keterangan:` dan daftar simbol 10 pt spasi 1.

**Nomor halaman**: bagian awal angka romawi kecil; mulai BAB I angka arab dari 1. Halaman pertama tiap bab:
nomor di tengah bawah; halaman lain: kanan bawah.

**Urutan dokumen**: sampul, (lembar pengesahan bila perlu), kata pengantar atau ringkasan, daftar isi,
daftar tabel, daftar gambar, BAB I dst., daftar pustaka, lampiran.

## Excel

| Unsur | Bentuk |
|---|---|
| Tata letak | Kolom A dan B sempit (lebar 3) sebagai margin; isi mulai kolom C, baris 2 |
| Huruf | Times New Roman 12; catatan dan keterangan 10 |
| Judul lembar | Baris 2: `LEMBAR n - JUDUL`, kapital, tebal, isi kuning `FFFF00`, rata tengah, digabung selebar tabel, garis tipis |
| Judul bagian | `A.  JUDUL BAGIAN`, tebal, isi kuning, rata kiri, digabung selebar tabel |
| Kepala tabel | Tebal, isi abu `D9D9D9`, rata tengah (horizontal dan vertikal), *wrap text* |
| Isi tabel | Garis tipis semua sisi; vertikal tengah; *wrap text*; teks rata kiri, angka/kode/satuan rata tengah |
| Format angka | `#,##0` atau `#,##0.00` (tampil dengan pemisah sesuai setelan Windows); satuan di kepala kolom |
| Catatan | 10 pt, rata kiri-atas, *wrap*, tanpa garis, digabung selebar tabel |
| Sel isian | Isi kuning muda `FFF2CC`; sel yang diisi AI isi hijau `E2EFDA` (penanda draf AI) |
| **Proporsi sel** | Lebar kolom sesuai isi: No 5-6, kode/satuan 8-12, angka 12-14, teks pendek 18-25, teks panjang 40-60. Tinggi baris dihitung dari jumlah baris teks terbungkus (15,6 pt per baris), bukan dibiarkan default |
| **Freeze panes** | Wajib pada setiap lembar tabel: tepat di bawah baris kepala tabel (dan di kanan kolom kunci bila tabel lebar) |
| Tampilan | *Gridlines* disembunyikan; zoom 85-100% |
| Cetak | A4 lanskap, *fit to width* 1 halaman, baris kepala diulang (*print titles*) |
