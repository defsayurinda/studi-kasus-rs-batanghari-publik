"""Notulen rapat simulasi pembahasan Laporan Pendahuluan (format FORMAT LAPORAN DAN EXCEL.md).

Rapat disimulasikan AI atas permintaan Defsa (AI memerankan pemberi tugas dan konsultan); keputusan berlabel
[Simulasi AI] dan dapat diganti bila sesi skenario menetapkan sikap owner yang berbeda.
Jalankan:  .venv\\Scripts\\python.exe skrip\\rapat_laporan_pendahuluan.py
"""
from pathlib import Path

from format_dokumen import Laporan, perbarui_word

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "10 Laporan" / "Notulen Rapat Laporan Pendahuluan (simulasi).docx"

# (judul agenda, pertanyaan/sikap owner, jawaban konsultan, kesepakatan)
AGENDA = [
    ("Kategori Risiko Struktur",
     "Owner meminta struktur direncanakan seperti kantor (kategori risiko II) karena bukan RS rujukan provinsi dan "
     "pagu tidak dapat ditambah; owner menduga biaya struktur naik puluhan miliar.",
     "Kategori risiko ditentukan oleh fungsi, bukan status rujukan. SNI 1726:2019 Tabel 3 (hal. 25) memasukkan rumah sakit "
     "yang memiliki fasilitas bedah dan unit gawat darurat ke kategori IV, dengan Ie = 1,50 (Tabel 4 hal. 25) dan batas "
     "simpangan 0,010 hsx, bukan 0,020 hsx (Tabel 20 hal. 88). Desain kategori II tidak akan lolos PBG. Kenaikan gaya gempa "
     "50% tidak sama dengan kenaikan biaya 50%, karena hanya sebagian elemen struktur dikendalikan gempa dan struktur "
     "hanya sebagian dari biaya gedung. Besarnya akan dihitung, bukan ditebak.",
     "Kategori risiko IV disetujui. Konsultan menyajikan perbandingan biaya struktur dua sistem pada desain konsep "
     "(Tahap 3), dan penghematan dicari lewat sistem struktur, grid, dan rekayasa nilai."),
    ("Utilitas Vital dan Parkir di Basement",
     "Owner ingin halaman bersih sehingga genset, trafo, panel, pompa, dan 120 mobil semuanya di basement.",
     "Banjir tercatat +11,20 berada di atas seluruh muka tanah (+8,75 s.d. +10,60). Utilitas di basement berarti RS padam "
     "saat banjir, padahal kategori IV mensyaratkan fasilitas tetap berfungsi saat darurat. Air tanah juga ±1 m dari "
     "muka tanah dan lapisan pasir terhubung ke sungai, sehingga basement penuh mahal dan berisiko. Utilitas dapat "
     "ditempatkan di lantai dasar yang ditinggikan atau gedung utilitas, dengan tampilan halaman tetap rapi.",
     "Utilitas vital dipindah ke atas banjir rencana ditambah jagaan. Pilihan parkir (basement penuh, basement parsial, "
     "parkir permukaan, gedung parkir) dibandingkan biaya dan risikonya di Tahap 3 sebelum diputuskan."),
    ("Kapasitas Tempat Tidur, Luas, dan Pagu",
     "Owner terkejut program ruang hanya 138 tempat tidur dan meminta 150 tetap dipenuhi tanpa menambah pagu.",
     "Program ruang versi 2 berisi 138 tempat tidur dan faktor luas bruto 1,14, sehingga luas 12.000 m² terlalu kecil. "
     "Perkiraan realistis ±14.800-17.000 m². Dengan pagu tetap, konsultan menyiapkan opsi pengurangan lingkup: basement "
     "parsial atau tanpa basement, dermaga menyusul, dan rekayasa nilai, lalu menyajikan biaya tiap opsi.",
     "Target 150 tempat tidur dipertahankan. Program ruang versi konsultan disusun di Tahap 3. Pagu tetap Rp 168 miliar; "
     "owner akan memilih opsi pengurangan lingkup setelah melihat perkiraan biaya di desain konsep."),
    ("Sisi Sungai, Sempadan, dan Dermaga",
     "Owner ingin gedung sedekat mungkin ke sungai dengan GSB 5 m dan dermaga ambulans air langsung ke IGD.",
     "Sempadan sungai belum ditetapkan instansi berwenang. Puncak tebing hanya 6-14 m dari batas lahan, ada bekas longsoran "
     "di x = 80-100 m (Januari 2025), dan belum ada data tanah di tebing. Muka air sungai berubah ±7,2 m, sehingga dermaga "
     "tetap tidak praktis. GSB selatan baru dapat ditetapkan setelah sempadan resmi dan analisis stabilitas tebing.",
     "Owner mengajukan penetapan sempadan sungai. Desain konsep memakai skenario sempadan konservatif. Teras pandang "
     "sebagai lansekap ringan. Dermaga dikaji sebagai ponton apung dan dapat dijadikan tahap berikutnya."),
    ("Jadwal dan Peletakan Batu Pertama",
     "Owner ingin peletakan batu pertama 6 Januari 2027 langsung diikuti galian basement karena sudah diumumkan ke publik.",
     "PBG wajib terbit sebelum pelaksanaan konstruksi (PP 16/2021 Pasal 253). Januari adalah puncak muka air sungai "
     "(rata-rata +8,60), waktu terburuk untuk galian di dekat sungai dan gudang tetangga. Galian tanpa desain dan PBG "
     "melanggar aturan dan berisiko merusak gudang.",
     "Peletakan batu pertama 6 Januari 2027 tetap diadakan sebagai seremoni tanpa galian. Galian dimulai setelah PBG "
     "terbit dan pada musim kering. Target operasi 1 Juli 2028 dievaluasi pada penyusunan jadwal (Tahap 9)."),
    ("Penyelidikan Tanah Tambahan",
     "Owner keberatan membayar penyelidikan lagi karena sudah membayar PT Tapak Rawa Geoteknik.",
     "Laporan yang ada tidak dapat dipakai untuk desain: muka air tanah ±1 m (bukan 3,8 m), lapisan pasir terhubung ke "
     "sungai, ada lempung organik yang tidak dilaporkan, dan cu, Cc, serta k keliru. Kekeliruan isi laporan dapat diminta "
     "diperbaiki oleh penyedia sebelumnya. Data yang memang belum ada (vs, CPTu, uji pompa, titik tebing) adalah lingkup baru.",
     "Owner meminta PT Tapak Rawa Geoteknik merevisi laporan atas temuan yang menjadi kesalahan mereka. Paket penyelidikan "
     "berprioritas 'Wajib sebelum desain' disetujui prinsipnya; konsultan menyerahkan rincian biaya dan waktu."),
    ("Gudang Tetangga di Sisi Timur",
     "Owner tidak ingin ada klaim dari pemilik gudang.",
     "Gudang berpondasi cerucuk kayu ±4 m dari batas. Penurunan muka air tanah akibat dewatering dapat membuat cerucuk "
     "lapuk dan tanah turun. Pencegahannya adalah survei kondisi awal, dinding galian kedap air, dewatering terbatas di "
     "dalam galian, tiang bor di dekat batas, serta pemantauan selama konstruksi.",
     "Owner meminta izin pemilik gudang untuk survei kondisi awal. Metode galian kedap air menjadi syarat desain."),
    ("Data dari Owner: MEP dan Helipad",
     "Owner menanyakan apakah desain struktur dapat dimulai tanpa data MEP dan tipe helikopter.",
     "Beban dan ruang genset, trafo, tangki, chiller, serta alat medis berat menentukan pelat dan balok. Beban helipad "
     "bergantung pada berat lepas landas helikopter rencana. Tanpa data itu desain memakai asumsi dan berisiko diulang.",
     "Owner menunjuk konsultan MEP atau menyerahkan data beban dan ruang MEP sebelum Tahap 4, dan menetapkan tipe "
     "helikopter rencana sebelum desain pelat atap."),
]

KEPUTUSAN = [
    ["Kategori risiko IV untuk seluruh gedung", "Owner, Konsultan", "Disepakati"],
    ["Utilitas vital di atas banjir rencana + jagaan", "Konsultan", "Tahap 3"],
    ["Perbandingan opsi parkir dan basement", "Konsultan", "Tahap 3"],
    ["Target 150 tempat tidur; program ruang versi konsultan", "Konsultan", "Tahap 3"],
    ["Opsi pengurangan lingkup bila pagu tetap", "Konsultan → Owner", "Tahap 3"],
    ["Permohonan penetapan sempadan sungai dan KKPR", "Owner", "Sebelum Tahap 3 selesai"],
    ["Data hidrologi banjir rencana", "Owner", "Sebelum Tahap 3 selesai"],
    ["Peletakan batu pertama 6 Jan 2027 tanpa galian", "Owner", "6 Januari 2027"],
    ["Revisi laporan tanah oleh PT Tapak Rawa Geoteknik", "Owner → PT TRG", "Desember 2026"],
    ["Rincian biaya dan waktu penyelidikan tambahan", "Konsultan", "Desember 2026"],
    ["Izin survei kondisi awal gudang timur", "Owner → pemilik gudang", "Desember 2026"],
    ["Data MEP dan tipe helikopter rencana", "Owner", "Sebelum Tahap 4"],
]


def main():
    lap = Laporan()
    lap.bab("", "Notulen Rapat Pembahasan Laporan Pendahuluan", mulai_arab=True)
    lap.bab_aktif = "1"
    lap.paragraf("*DOKUMEN SIMULASI untuk studi kasus portofolio. Rapat disimulasikan AI atas permintaan Defsa; AI "
                 "memerankan pemberi tugas dan konsultan. Keputusan berlabel [Simulasi AI]; notulen disetujui Defsa 19 Nov 2026.*",
                 inden=False)
    lap.subbab("1.1", "Data Rapat")
    lap.tabel("Data Rapat", ["Butir", "Keterangan"], [
        ["Acara", "Pembahasan Laporan Pendahuluan, November 2026"],
        ["Tempat", "Ruang rapat Yayasan Kesehatan Tepian Batanghari (simulasi)"],
        ["Peserta", "Ketua Yayasan, Bendahara Yayasan, calon Direktur RS, Konsultan Perencana"],
        ["Bahan", "Laporan Pendahuluan, Matriks Tanggapan TOR, Telaah Penyelidikan Tanah"],
    ], [3.5, 10.5], rata=list("ll"))
    lap.subbab("1.2", "Pembahasan")
    for i, (judul, owner, konsultan, sepakat) in enumerate(AGENDA, start=1):
        lap.anak_subbab(f"1.2.{i}", judul)
        lap.butir("1.", f"**Pemberi tugas:** {owner}")
        lap.butir("2.", f"**Konsultan:** {konsultan}")
        lap.butir("3.", f"**Kesepakatan [Simulasi AI]:** {sepakat}")
    lap.subbab("1.3", "Keputusan dan Tindak Lanjut")
    lap.paragraf("Keputusan dan tindak lanjut rapat dirangkum pada Tabel 1.2.")
    lap.tabel("Keputusan dan Tindak Lanjut Rapat", ["No", "Keputusan / tindak lanjut", "Penanggung jawab", "Batas waktu"],
              [[i] + r for i, r in enumerate(KEPUTUSAN, start=1)], [1.0, 7.4, 3.2, 2.4], rata=list("clll"))
    lap.subbab("1.4", "Penutup")
    lap.paragraf("Rapat menyepakati bahwa laporan pendahuluan diterima dengan catatan di atas, dan pekerjaan dilanjutkan ke "
                 "olah data tanah (Tahap 2) setelah data penyelidikan tambahan tersedia, sejalan dengan persiapan desain "
                 "konsep (Tahap 3).")
    lap.simpan(KELUAR)
    ok, pesan = perbarui_word(KELUAR)
    print("ditulis:", KELUAR, "| field diperbarui" if ok else f"| Word gagal: {pesan[:200]}")


if __name__ == "__main__":
    main()
