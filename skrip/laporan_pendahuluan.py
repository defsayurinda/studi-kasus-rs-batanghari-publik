"""Susun draf Laporan Pendahuluan (Tahap 0 + Tahap 1) dalam .docx, format FORMAT LAPORAN DAN EXCEL.md.

Tabel diambil dari 'Matriks Tanggapan TOR.xlsx' dan 'Telaah Penyelidikan Tanah.xlsx'; narasi ditulis di sini.
Disusun AI atas permintaan Defsa; disetujui Defsa 19 Nov 2026.
Jalankan:  .venv\\Scripts\\python.exe skrip\\laporan_pendahuluan.py
"""
from collections import Counter
from pathlib import Path

import openpyxl
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from format_dokumen import Laporan, baca_tabel, perbarui_word

AKAR = Path(__file__).resolve().parents[1]
MATRIKS = AKAR / "00 Kerangka Acuan" / "Matriks Tanggapan TOR.xlsx"
TELAAH = AKAR / "01 Penyelidikan Tanah" / "Telaah Penyelidikan Tanah.xlsx"
DENAH = AKAR / "01 Penyelidikan Tanah" / "Denah Titik Penyelidikan.png"
KELUAR = AKAR / "10 Laporan" / "Laporan Pendahuluan.docx"

KATEGORI = ["Tidak dapat dipenuhi", "Perlu kajian", "Setuju bersyarat", "Setuju"]
WARNA_KATEGORI = {"Tidak dapat dipenuhi": "F8CBAD", "Perlu kajian": "FFE699", "Setuju bersyarat": "E2EFDA", "Setuju": "C6E0B4"}
WARNA_PARAH = {"Tinggi": "F8CBAD", "Sedang": "FFE699", "Rendah": "E2EFDA"}


def data():
    m = openpyxl.load_workbook(MATRIKS, data_only=True)
    t = openpyxl.load_workbook(TELAAH, data_only=True)
    return dict(
        tanggapan=baca_tabel(m["Matriks Tanggapan"])[1],
        asumsi=baca_tabel(m["Asumsi dan Data Diminta"])[1],
        acuan=baca_tabel(m["Acuan Normatif"], "Dokumen (dari TOR bagian 8)"),
        temuan=[r for r in baca_tabel(t["Temuan Telaah"])[1] if r[1]],
        usulan=[r for r in baca_tabel(t["Usulan Penyelidikan"])[1] if r[1]],
    )


def sampul(lap):
    d = lap.doc
    def baris(teks, ukuran=12, tebal=False, miring=False, sesudah=0):
        p = d.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(sesudah)
        r = p.add_run(teks)
        r.font.size, r.bold, r.italic = Pt(ukuran), tebal, miring
    for _ in range(4):
        d.add_paragraph()
    baris("LAPORAN PENDAHULUAN", 16, True)
    baris("", 12, sesudah=36)
    baris("JASA KONSULTANSI PERENCANAAN PEMBANGUNAN GEDUNG", 12, True)
    baris("RUMAH SAKIT TEPIAN BATANGHARI", 14, True)
    baris("6 Lantai + 1 Basement, Tepi Utara Sungai Batanghari, Kota Jambi", 12, sesudah=48)
    baris("Pemberi tugas: Yayasan Kesehatan Tepian Batanghari")
    baris("Rujukan: KAK No. 014/YKTB/KAK/X/2026", sesudah=48)
    baris("Disusun oleh:")
    baris("Defsa Yurinda", tebal=True)
    baris("(Studi kasus portofolio perencanaan)", sesudah=60)
    baris("JAMBI", tebal=True)
    baris("NOVEMBER 2026", tebal=True, sesudah=36)
    baris("DOKUMEN SIMULASI untuk studi kasus portofolio. Yayasan, lahan, data tanah, dan semua angka fiktif; "
          "tidak untuk konstruksi. Isi disusun dengan bantuan AI atas permintaan penulis "
          "dan telah diperiksa serta disetujui penulis (lihat Subbab 7.3).", 10, miring=True)


def ringkasan(lap):
    lap.judul_depan("Ringkasan Eksekutif")
    lap.paragraf("Laporan ini menanggapi Kerangka Acuan Kerja (KAK) dan sepuluh keinginan pemberi tugas, serta menelaah "
                 "laporan penyelidikan tanah PT Tapak Rawa Geoteknik No. TRG/LP/2026/117. Proyek **layak dilanjutkan**, "
                 "tetapi beberapa keinginan pemberi tugas tidak dapat dipenuhi seperti tertulis dan data tanah yang ada "
                 "**belum cukup untuk desain**. Hal yang perlu diputuskan sebelum desain konsep adalah sebagai berikut.")
    lap.daftar([
        "**Kategori risiko IV, bukan II.** Rumah sakit dengan fasilitas bedah dan gawat darurat wajib kategori risiko IV "
        "(SNI 1726:2019 Tabel 3); faktor keutamaan gempa naik dari 1,0 menjadi 1,5.",
        "**Utilitas vital tidak di basement.** Muka air banjir tercatat +11,20 berada di atas seluruh muka tanah, sehingga "
        "genset, trafo, panel, dan pompa harus berada di atas banjir rencana.",
        "**Program ruang baru memuat 138 tempat tidur, bukan 150**, dan luas bruto serta basement terlalu kecil. Luas "
        "realistis ±14.800-17.000 m², sehingga pagu Rp 168 miliar kemungkinan tidak cukup.",
        "**Sisi sungai belum dapat dikunci.** Sempadan sungai belum ditetapkan, puncak tebing hanya 6-14 m dari batas "
        "lahan, dan terdapat bekas longsoran di x = 80-100 m (Januari 2025).",
        "**Galian basement tidak dapat dimulai Januari 2027.** PBG harus terbit sebelum konstruksi (PP 16/2021 Pasal 253), "
        "dan Januari adalah puncak muka air sungai.",
        "**Penyelidikan tanah tambahan diperlukan.** Muka air tanah sebenarnya ±1 m (bukan 3,8 m), lapisan pasir terhubung "
        "ke sungai, terdapat lempung organik yang tidak dilaporkan, dan beberapa parameter keliru.",
    ])


def bab1(lap):
    lap.bab("I", "Pendahuluan", mulai_arab=True)
    lap.subbab("1.1", "Latar Belakang")
    lap.paragraf("Yayasan Kesehatan Tepian Batanghari berencana membangun rumah sakit umum 150 tempat tidur di lahan "
                 "yayasan di tepi utara Sungai Batanghari, Kota Jambi. Rumah sakit ini direncanakan menjadi rujukan wilayah "
                 "seberang dan pendukung layanan gawat darurat sungai, dengan target beroperasi 1 Juli 2028 (KAK bagian 1-2).")
    lap.subbab("1.2", "Maksud dan Tujuan Laporan")
    lap.paragraf("Sesuai KAK bagian 9 butir 1, laporan pendahuluan memuat tanggapan atas KAK dan keinginan pemberi tugas "
                 "serta telaah penyelidikan tanah. Laporan ini menjadi dasar kesepakatan sebelum desain konsep yang "
                 "dilaporkan dalam laporan antara.")
    lap.subbab("1.3", "Dokumen yang Ditelaah")
    lap.paragraf("Dokumen yang ditelaah dalam laporan ini adalah sebagai berikut.")
    lap.daftar([
        "KAK No. 014/YKTB/KAK/X/2026 beserta Lampiran A (muka air sungai), Lampiran B (jarak puncak tebing), dan "
        "Lampiran C (elevasi muka tanah).",
        "Program Ruang versi 2 (Oktober 2026).",
        "Laporan Penyelidikan Tanah PT Tapak Rawa Geoteknik No. TRG/LP/2026/117 beserta data sondir, bor dan SPT, "
        "muka air, dan laboratorium.",
    ])
    lap.subbab("1.4", "Metode Penelaahan")
    lap.paragraf("Setiap butir KAK diberi kategori tanggapan, yaitu setuju, setuju bersyarat, perlu kajian, atau tidak dapat "
                 "dipenuhi, beserta dasar pasal dan dampaknya. Laporan tanah ditelaah dengan empat pertanyaan berikut.")
    lap.daftar(["Cukup: apakah jumlah, jarak, dan kedalaman titik memenuhi SNI 8460:2017 Tabel 2 dan Gambar 1.",
                "Dapat dipercaya: apakah prosedur, kualitas contoh, dan pengukuran air tanah memenuhi standar.",
                "Konsisten: apakah sondir, bor, laboratorium, dan ringkasan laporan saling cocok.",
                "Memenuhi kebutuhan desain: apakah data cukup untuk kelas situs, likuifaksi, galian, tiang, dan tebing."])
    lap.paragraf_butir("Angka penting dihitung ulang dengan cara kedua, dan pasal yang dirujuk dicocokkan dengan dokumen "
                       "acuan. Dokumen yang belum tersedia ditandai.", level=4)


def bab2(lap):
    lap.bab("II", "Gambaran Proyek dan Tapak")
    lap.subbab("2.1", "Data Proyek dan Tapak")
    lap.paragraf("Data utama proyek dan tapak dari KAK dirangkum pada Tabel 2.1.")
    lap.tabel("Data Proyek dan Tapak", ["Butir", "Data", "Sumber"], [
        ["Lahan", "±1,26 ha (140 m × 90 m); koordinat lokal, BM-1 = +10,000 di sudut barat daya", "KAK 4.1"],
        ["Batas lahan", "Selatan tebing sungai; timur gudang lama 2 lantai (±4 m, cerucuk kayu); barat jalan 6 m; utara jalan kolektor 12 m", "KAK 4.1"],
        ["Muka tanah asli", "+8,75 (utara) s.d. +10,60 (selatan); lahan miring ke utara", "KAK Lamp. C"],
        ["Muka air sungai", "+4,00 (kemarau) s.d. +11,20 (banjir Januari, maksimum 2014-2025)", "KAK 4.3, Lamp. A"],
        ["Tebing sungai", "Puncak +10,2 s.d. +10,4; 6-14 m dari batas lahan; tinggi ±6 m; bekas longsoran x = 80-100 m", "KAK Lamp. B"],
        ["Tata ruang", "KDB 60%, KLB 3,0, KDH 15%, maksimum 8 lantai; GSB utara 10 m, barat 5 m (sementara)", "KAK 4.2"],
        ["Bangunan", "6 lantai + 1 basement; 150 tempat tidur; klasifikasi madya untuk 4 pelayanan", "KAK 3, 5"],
        ["Pagu fisik", "Rp 168 miliar termasuk PPN (12.000 m² × Rp 14 juta/m²), tidak dapat ditambah", "KAK 6"],
    ], [3.2, 8.6, 2.2], rata=list("llc"), sumber="KAK No. 014/YKTB/KAK/X/2026")
    lap.subbab("2.2", "Kondisi Tapak")
    lap.paragraf("Muka air banjir tercatat +11,20 lebih tinggi daripada puncak tebing dan seluruh muka tanah asli, sehingga "
                 "saat banjir lahan tergenang 0,60-2,45 m. Lahan miring ke utara, menjauhi sungai, sehingga air yang melimpasi "
                 "tebing menggenang di bagian utara. Bagian utara ini juga yang dicadangkan untuk gedung tahap 2.")
    lap.paragraf("Garis sempadan sungai belum ditetapkan oleh instansi berwenang, padahal sempadan itulah yang membatasi "
                 "posisi massa bangunan di sisi selatan. Gudang tetangga di sisi timur berpondasi cerucuk kayu dan peka "
                 "terhadap penurunan muka air tanah akibat *dewatering*.")


def bab3(lap, dt):
    lap.bab("III", "Tanggapan atas KAK")
    data = dt["tanggapan"]
    hit = Counter(r[5] for r in data)
    lap.subbab("3.1", "Rekapitulasi Tanggapan")
    lap.paragraf(f"Sebanyak {len(data)} butir KAK dan keinginan pemberi tugas ditanggapi. Rekapitulasinya disajikan pada "
                 "Tabel 3.1, sedangkan matriks lengkapnya pada Lampiran A.")
    lap.tabel("Rekapitulasi Kategori Tanggapan KAK", ["Kategori", "Jumlah butir", "Arti"], [
        [k, hit.get(k, 0), a] for k, a in zip(KATEGORI, [
            "Bertentangan dengan peraturan atau tidak aman; perlu keputusan pemberi tugas",
            "Belum dapat diputuskan tanpa data atau analisis tambahan",
            "Dapat dipenuhi dengan syarat yang disebutkan",
            "Dapat dipenuhi seperti tertulis"])
    ], [4.0, 2.6, 7.4], rata=list("lcl"), warna={0: WARNA_KATEGORI})
    lap.subbab("3.2", "Butir yang Tidak Dapat Dipenuhi")
    lap.paragraf("Butir berikut tidak dapat dipenuhi seperti tertulis. Usulan konsultan disertakan pada setiap butir.")
    for i, r in enumerate([r for r in data if r[5] == "Tidak dapat dipenuhi"], start=1):
        lap.butir(f"{i}.", f"**{r[2]}**: {r[3]}")
        lap.paragraf_butir(f"{r[8]} Dasar: {r[6]}.")
    lap.subbab("3.3", "Butir yang Perlu Kajian")
    lap.paragraf("Butir berikut memerlukan data atau analisis tambahan sebelum dapat diputuskan.")
    for i, r in enumerate([r for r in data if r[5] == "Perlu kajian"], start=1):
        lap.butir(f"{i}.", f"**{r[2]}**: {r[8]}")
    lap.subbab("3.4", "Telaah Program Ruang")
    lap.paragraf("Luas setiap baris dan total luas bersih 8.586 m² dalam Program Ruang versi 2 sudah benar. Namun, jumlah "
                 "tempat tidur hanya 138 (kurang 12), faktor luas bruto 1,14 terlalu kecil untuk rumah sakit, dan basement "
                 "2.800 m² tidak cukup untuk 120 mobil dan utilitas. Perkiraan luas lantai total adalah ±14.800-17.000 m² "
                 "[Asumsi: faktor bruto 1,4-1,6; parkir 25-30 m²/mobil].")


def bab4(lap, dt):
    lap.bab("IV", "Telaah Penyelidikan Tanah")
    lap.subbab("4.1", "Data yang Diterima")
    lap.paragraf("Data penyelidikan terdiri atas enam sondir mekanis 2,5 ton (S-01 s.d. S-06), tiga bor mesin dengan SPT tiap "
                 "2 m sampai 40 m (BH-1 s.d. BH-3), 15 contoh tak terganggu, uji laboratorium, serta satu pipa tegak dan satu "
                 "*piezometer* yang dibaca September-November 2026. Lokasi titik ditunjukkan pada Gambar 4.1.")
    if DENAH.exists():
        lap.gambar(DENAH, "Denah Titik Penyelidikan Tanah", lebar_cm=14.0)
    lap.subbab("4.2", "Susunan Lapisan Tanah")
    lap.paragraf("Susunan lapisan dari log bor beserta catatan telaah disajikan pada Tabel 4.1.")
    lap.tabel("Susunan Lapisan dan Catatan Telaah", ["Kedalaman (m)", "Uraian", "N-SPT", "Catatan telaah"], [
        ["0-±1,9", "Urugan dan lempung kelanauan teguh", "-", "-"],
        ["±1,1-4,0 (BH-3)", "Lempung organik berserat, sangat lunak", "0", "Tidak disebut di laporan"],
        ["±1,9-9,5", "Lempung kelanauan sangat lunak sampai lunak (CH)", "2-3", "cu UU 6-19 kPa"],
        ["±9,5-19", "Pasir halus kelanauan, lepas sampai agak padat (SM/SP-SM)", "8-20", "Akuifer terhubung sungai"],
        ["±19-33", "Lempung kelanauan kaku sampai sangat kaku", "10-28", "Tidak ada contoh tak terganggu"],
        [">33", "Pasir halus-sedang padat sampai sangat padat", ">45", "Bor berakhir 40 m"],
    ], [2.6, 5.6, 1.6, 4.2], rata=list("clcl"), sumber="Log bor BH-1 s.d. BH-3 dan hasil telaah")
    lap.subbab("4.3", "Temuan Utama")
    lap.anak_subbab("4.3.1", "Muka Air Tanah dan Akuifer Pasir")
    lap.paragraf("Muka air tanah rencana 3,80 m dalam laporan berasal dari satu bacaan BH-2 dua jam setelah pengeboran, "
                 "padahal pipa tegak SP-1 selama dua bulan menunjukkan muka air 0,79-1,49 m di bawah muka tanah dan terus "
                 "naik. Piezometer PZ-1 di lapisan pasir naik dari +4,91 ke +7,26 mengikuti sungai (+4,1 ke +7,6). Lapisan "
                 "pasir 10-19 m merupakan akuifer tertekan yang terhubung ke sungai, sehingga saat banjir tekanannya bekerja "
                 "di bawah dasar basement dan berisiko mengangkat dasar galian (FHWA GEC 5 Pasal 12.5.1).")
    lap.anak_subbab("4.3.2", "Lapisan Organik dan Benda Terkubur")
    lap.paragraf("BH-3 menemukan lempung organik berserat setebal ±2,8 m dengan kadar organik 77-84%, dan rasio gesekan "
                 "sondir S-04 serta S-05 menunjukkan zona serupa di bagian utara. Bila tebalnya lebih dari 3 m, situs masuk "
                 "kelas SF (SNI 1726:2019 Tabel 5). Penolakan sondir S-03 pada 8,4 m kemungkinan besar disebabkan batang kayu "
                 "terkubur, karena BH-2 yang berjarak ±11 m mencatat kayu lapuk pada 8,4-8,7 m dengan lempung lunak di "
                 "bawahnya. Saran tiang 9 m di zona S-03 tidak dapat diterima.")
    lap.anak_subbab("4.3.3", "Parameter Tanah")
    lap.paragraf("Tiga parameter utama dalam laporan keliru, yaitu kuat geser lempung lunak, indeks kompresi, dan "
                 "permeabilitas pasir. Akibatnya, rekomendasi turap baja dengan *dewatering* ringan tidak berdasar. "
                 "Hasil cek silang disajikan pada Tabel 4.2.")
    lap.tabel("Cek Silang Angka Kunci", ["Parameter", "Laporan", "Cek silang", "Status"], [
        ["cu lempung lunak", "29 kPa (qc/10)", "UU rata-rata 12,5 kPa (5,7-18,7); (qc − σv0)/Nk = 8-16 kPa", "Tidak lolos"],
        ["Cc lempung lunak", "0,61", "Kemiringan e-log σ' cocok; tanpa contoh rusak 0,70", "Pemilihan contoh keliru"],
        ["k pasir", "1,2 × 10⁻⁸ m/s", "Hazen, D10 ≈ 0,084 mm: 3-8 × 10⁻⁵ m/s", "Tidak lolos"],
        ["Muka air tanah", "3,80 m", "SP-1: 0,79-1,49 m; BH-3: 1,10 m", "Tidak lolos"],
        ["N-SPT", "N2 + N3", "Dijumlah ulang 60 baris", "Lolos"],
    ], [2.8, 2.6, 5.8, 2.8], rata=list("llll"), sumber="VERIFIKASI.md T-01 s.d. T-05")
    lap.subbab("4.4", "Rekapitulasi Temuan")
    tem = dt["temuan"]
    kel = ["1 Cukup", "2 Dipercaya", "3 Konsisten", "4 Kebutuhan desain"]
    hit = Counter((r[1], r[6]) for r in tem)
    lap.paragraf(f"Telaah menghasilkan {len(tem)} temuan yang direkapitulasi pada Tabel 4.3. Keparahan tinggi berarti temuan "
                 "tersebut mengubah keputusan desain atau keselamatan. Daftar lengkap temuan disajikan pada Lampiran B.")
    lap.tabel("Rekapitulasi Temuan Telaah", ["Kelompok", "Tinggi", "Sedang", "Rendah", "Jumlah"],
              [[k.split(" ", 1)[1].capitalize(), hit[(k, "Tinggi")], hit[(k, "Sedang")], hit[(k, "Rendah")],
                sum(hit[(k, p)] for p in ["Tinggi", "Sedang", "Rendah"])] for k in kel]
              + [["**Jumlah**", *[sum(hit[(k, p)] for k in kel) for p in ["Tinggi", "Sedang", "Rendah"]], len(tem)]],
              [5.0, 2.25, 2.25, 2.25, 2.25], rata=list("lcccc"))


def bab5(lap, dt):
    lap.bab("V", "Usulan Penyelidikan Tambahan")
    lap.subbab("5.1", "Dasar Usulan")
    lap.paragraf("SNI 8460:2017 Pasal 5.7.1 mewajibkan laporan penyelidikan tanah mengusulkan penyelidikan lanjutan beserta "
                 "alasan dan programnya. Laporan PT Tapak Rawa Geoteknik tidak memuat usulan tersebut, sehingga konsultan "
                 "mengusulkan program pada Tabel 5.1. Rincian lokasi, kedalaman, dan alasan disajikan pada Lampiran C.")
    lap.subbab("5.2", "Program Penyelidikan")
    lap.tabel("Program Penyelidikan Tambahan", ["No", "Jenis uji", "Jumlah", "Prioritas"],
              [[r[0], r[1], r[4], r[7]] for r in dt["usulan"]], [1.0, 8.4, 2.0, 2.6], rata=list("clcl"))
    lap.paragraf("Biaya dan waktu penyelidikan tambahan diajukan terpisah setelah pemberi tugas menyetujui lingkupnya. "
                 "Pemantauan air tanah perlu melewati puncak banjir Januari, sehingga sebagian data baru lengkap sekitar "
                 "Maret 2027.")


def bab6(lap, dt):
    lap.bab("VI", "Data, Asumsi, dan Rencana Kerja")
    lap.subbab("6.1", "Data yang Diminta dari Pemberi Tugas")
    diminta = [r for r in dt["asumsi"] if r[1] == "Data diminta"]
    lap.tabel("Data yang Diminta dari Pemberi Tugas", ["No", "Data", "Ditujukan ke", "Batas waktu"],
              [[i, r[2], r[5], r[6]] for i, r in enumerate(diminta, start=1)], [1.0, 7.4, 3.2, 2.4], rata=list("clll"))
    lap.subbab("6.2", "Asumsi Sementara")
    asumsi = [r for r in dt["asumsi"] if r[1] == "Asumsi"]
    lap.tabel("Asumsi Sementara Konsultan", ["No", "Asumsi", "Diganti oleh"],
              [[i, r[2], r[6]] for i, r in enumerate(asumsi, start=1)], [1.0, 9.0, 4.0], rata=list("cll"))
    lap.paragraf("Selain asumsi pada Tabel 6.2, muka air tanah desain sementara diambil di muka tanah asli, dan parameter "
                 "cu, Cc, serta k dari laporan tanah tidak dipakai sampai penyelidikan tambahan selesai.")
    lap.subbab("6.3", "Rencana Kerja")
    lap.tabel("Tahap Pekerjaan Berikutnya", ["Tahap", "Kegiatan", "Keluaran"], [
        ["2 Olah data tanah", "Stratigrafi, parameter desain, kelas situs, likuifaksi, sensitivitas", "Parameter tanah desain"],
        ["3 Desain konsep", "BEP dan templat BIM, aturan tapak dan PBG, peil banjir, zonasi, grid, sistem struktur, alternatif pondasi dan galian", "Laporan antara, model BIM LOD 200"],
        ["4-6 Struktur", "Struktur atas (kategori risiko IV), tengah, bawah dan basement, stabilitas tebing", "Perhitungan struktur dan geoteknik"],
        ["7 DED dan RKS", "Gambar kerja dari model BIM dan spesifikasi teknis", "DED dan RKS"],
        ["8 RAB", "Volume dari model, AHSP SE 47/2026, survei harga Jambi, rekayasa nilai", "RAB"],
        ["9 Jadwal", "Kalender kerja, kurva S, simulasi 4D, galian pada musim kering", "Jadwal pelaksanaan"],
        ["10 Laporan", "Laporan antara dan laporan akhir", "Laporan akhir"],
    ], [3.0, 7.2, 3.8], rata=list("lll"))
    lap.subbab("6.4", "Tinjauan Jadwal")
    lap.paragraf("Jadwal KAK, yaitu DED selesai Maret 2027 dan peletakan batu pertama 6 Januari 2027 yang langsung diikuti "
                 "galian, tidak sejalan dengan kebutuhan penyelidikan tambahan, PBG, dan musim banjir. Urutan yang diusulkan "
                 "adalah penyelidikan tambahan, desain konsep, DED, PBG, lelang, lalu galian pada musim kering (Juni-September). "
                 "Peletakan batu pertama tetap dapat dilaksanakan sebagai seremoni tanpa galian.")


def bab7(lap):
    lap.bab("VII", "Kesimpulan dan Tindak Lanjut")
    lap.subbab("7.1", "Kesimpulan")
    lap.daftar([
        "Proyek layak dilanjutkan dengan penyesuaian pada kategori risiko, letak utilitas, program ruang, dan jadwal.",
        "Laporan penyelidikan tanah belum dapat dipakai langsung untuk desain; empat parameter kunci keliru dan dua kondisi "
        "berbahaya tidak dilaporkan.",
        "Penyelidikan tambahan wajib dilakukan sebelum parameter tanah desain ditetapkan dalam laporan antara.",
    ])
    lap.subbab("7.2", "Keputusan yang Diminta dari Pemberi Tugas")
    lap.daftar([
        "Menyetujui kategori risiko IV untuk seluruh gedung.",
        "Menyetujui pemindahan utilitas vital ke atas banjir rencana dan memilih alternatif parkir yang dikaji di desain konsep.",
        "Menetapkan 150 tempat tidur dengan program ruang yang dikoreksi, atau menyesuaikan target tempat tidur.",
        "Menetapkan lingkup yang boleh dikurangi bila pagu Rp 168 miliar tetap.",
        "Mengurus KKPR, penetapan sempadan sungai, dan data hidrologi banjir rencana.",
        "Menyetujui program penyelidikan tanah tambahan dan izin survei kondisi gudang tetangga.",
        "Menyetujui urutan jadwal: galian basement setelah PBG dan pada musim kering.",
        "Menunjuk konsultan MEP atau menyerahkan data beban dan ruang MEP sebelum desain struktur.",
    ])
    lap.subbab("7.3", "Catatan Penyusunan")
    lap.paragraf("Laporan ini bagian dari studi kasus portofolio dengan data simulasi. Matriks tanggapan (Tahap 0) dan telaah "
                 "tanah (Tahap 1) disusun dengan bantuan AI (Claude) atas permintaan penulis, lalu dipelajari serta "
                 "disetujui penulis pada 19 November 2026. Pasal dicocokkan ke dokumen di folder acuan; dokumen yang belum tersedia (peraturan "
                 "sempadan sungai, KRIS, heliport, proteksi kebakaran, SNI 4153, dan SNI 2827) ditandai dan pasalnya belum "
                 "dikutip.")


def lampiran(lap, dt):
    lap.lampiran("A", "Matriks Tanggapan KAK", lanskap=True)
    lap.tabel("Matriks Tanggapan KAK", ["No", "Butir KAK", "Kategori", "Temuan", "Usulan konsultan"],
              [[r[0], f"{r[1]} {r[2]}", r[5], r[4], r[8]] for r in dt["tanggapan"]],
              [1.0, 3.2, 2.6, 8.2, 7.7], rata=list("cllll"), warna={2: WARNA_KATEGORI}, ukuran=10,
              sumber="Matriks Tanggapan TOR.xlsx, lembar 1")
    lap.lampiran("B", "Daftar Temuan Telaah Penyelidikan Tanah", lanskap=True)
    lap.tabel("Temuan Telaah Penyelidikan Tanah", ["No", "Kelompok", "Temuan", "Acuan", "Keparahan"],
              [[r[0], r[1].split(" ", 1)[1].capitalize(), r[3], r[4], r[6]] for r in dt["temuan"]],
              [1.0, 2.8, 11.4, 5.4, 2.1], rata=list("cllcc"[:3] + "lc"), warna={4: WARNA_PARAH}, ukuran=10,
              sumber="Telaah Penyelidikan Tanah.xlsx, lembar 3")
    lap.lampiran("C", "Program Penyelidikan Tambahan", lanskap=True)
    lap.tabel("Rincian Program Penyelidikan Tambahan", ["No", "Jenis uji", "Lokasi", "Kedalaman (m)", "Jumlah", "Alasan", "Prioritas"],
              [[r[0], r[1], r[2], r[3], r[4], r[5], r[7]] for r in dt["usulan"]],
              [1.0, 5.4, 4.6, 2.0, 1.8, 4.9, 3.0], rata=list("cllccll"), ukuran=10,
              sumber="Telaah Penyelidikan Tanah.xlsx, lembar 5")
    lap.lampiran("D", "Acuan Normatif")
    kepala, baris = dt["acuan"]
    lap.tabel("Acuan Normatif", ["Dokumen", "Status berlaku", "Pengganti / catatan", "Ada di acuan/"],
              [[r[0], r[1], r[2], r[4]] for r in baris], [5.0, 2.8, 4.2, 2.0], rata=list("lllc"), ukuran=10,
              sumber="Matriks Tanggapan TOR.xlsx, lembar 4")


def main():
    dt = data()
    lap = Laporan()
    sampul(lap)
    lap.bagian_awal()
    ringkasan(lap)
    lap.daftar_isi()
    lap.daftar_tabel()
    lap.daftar_gambar()
    bab1(lap)
    bab2(lap)
    bab3(lap, dt)
    bab4(lap, dt)
    bab5(lap, dt)
    bab6(lap, dt)
    bab7(lap)
    lampiran(lap, dt)
    lap.simpan(KELUAR)
    ok, pesan = perbarui_word(KELUAR)
    print("ditulis:", KELUAR, "| field diperbarui lewat Word" if ok else f"| Word gagal: {pesan[:200]}")


if __name__ == "__main__":
    main()
