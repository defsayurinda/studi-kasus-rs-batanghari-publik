"""Notulen rapat simulasi presentasi desain konsep (langkah 3.10; format FORMAT LAPORAN DAN EXCEL.md).

Sikap dan keputusan owner/MK/pemilik gudang ditulis sesi skenario tersegel (berkas
'03 Desain Konsep/Data Owner/Tanggapan Owner Rapat Konsep (simulasi).md', label [Simulasi AI - sesi skenario]);
jawaban konsultan disusun AI atas permintaan Defsa dari hasil langkah 3.2-3.9. Disetujui Defsa 19 Nov 2026.
Jalankan:  .venv\\Scripts\\python.exe skrip\\rapat_desain_konsep.py
"""
from pathlib import Path

import tahap3_biaya as bi
import tahap3_peil as pl
import tahap3_struktur as st
from format_dokumen import Laporan, perbarui_word

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "10 Laporan" / "Notulen Rapat Desain Konsep (simulasi).docx"


def fmt(v, d=0):
    s = f"{v:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


def agenda():
    pe = pl.peil_usulan()
    r = bi.rekap()
    rg = bi.ringkasan()
    hemat_str = (st.biaya_relatif("GANDA") - st.biaya_relatif("SRPMK")) * bi.FAKTOR_NYATA
    return [
        ("Tapak dan Sempadan",
         "Ketua yayasan mengira KDB 50 % berarti tapak 6.300 m² dan menanyakan teras pandang di tepi sungai. MK meminta "
         "hitungan lahan perencanaan dilampirkan pada permohonan PBG dan menanyakan siapa yang menyusun kajian stabilitas "
         "tebing serta rencana saluran pembuang yang disyaratkan surat sempadan butir 5.",
         "KDB dihitung dari lahan perencanaan (persil dikurangi rumija dan ruang sempadan, PKKPR persyaratan 2), sehingga "
         "tapak maksimum 5.383 m². Teras pandang dapat dibuat sebagai lansekap ringan tanpa urugan dengan izin pemanfaatan "
         "ruang sempadan. Kajian stabilitas tebing semula di Tahap 6; konsultan dapat memajukan analisis awal dengan data "
         "bor kaki tebing (BT-1K, BT-2K) untuk laporan antara.",
         "Tapak maksimum 5.383 m² diterima. Ruang sempadan tidak diurug, menjadi taman ringan atau teras pandang. Kajian "
         "stabilitas tebing dan rencana saluran pembuang masuk lingkup konsultan dan diserahkan bersama laporan antara."),
        ("Peil dan Urugan",
         "Ketua yayasan keberatan lantai naik ke +12,85 dan menanyakan akses kursi roda. Calon direktur meminta ramp "
         "landai beratap dari drop-off lobi dan IGD serta jalur evakuasi yang tetap terpakai saat halaman tergenang. "
         "Bendahara meminta tanah merah gratis 22 ribu m³ tidak dilepas (ditawarkan sampai Juni). MK mengusulkan "
         "timbunan sementara sambil diuji mutunya.",
         f"Q50 terkoreksi +{fmt(pe['q50'], 2)} dan banjir 2003 +11,65 membuat +11,50 tidak aman untuk IGD dan utilitas. "
         f"Beda tinggi lantai dan halaman {fmt(pe['lantai'] - pe['halaman'], 2)} m dicapai dengan ramp beratap di drop-off; "
         "kemiringannya dicek ke ketentuan aksesibilitas (dokumen acuannya belum ada di folder acuan). Halaman "
         f"+{fmt(pe['halaman'], 2)} di atas Q50; saat Q100 +{fmt(pe['q100'], 2)} halaman tergenang ±0,26 m tetapi "
         "lantai tetap kering, sehingga jalur evakuasi utama dibuat di atas Q100. Timbunan sementara dapat diletakkan di "
         "area yang memang akan diurug, di luar ruang sempadan dan zona labil, dengan tinggi per lapis dibatasi seperti "
         "urugan bertahap (stabilitas lempung lunak, langkah 2.8); timbunan itu sekaligus berfungsi sebagai prapembebanan.",
         "Peil lantai dasar dan utilitas +12,85 serta halaman +12,05 diterima dengan syarat ramp beratap pasien dan "
         "ambulans digambar di konsep. Target urugan 6 minggu dibatalkan; urugan bertahap dengan PVD diterima. Tanah "
         "gratis diterima sebagai timbunan sementara; lokasi dan uji mutunya ditetapkan konsultan paling lambat 30 April "
         "2027."),
        ("Program Ruang dan Luas",
         "Ketua yayasan menegaskan 150 TT adalah janji kepada pemerintah daerah dan bank. Bendahara meminta penjelasan "
         "tertulis mengapa luas naik dari 12.000 menjadi 19.328 m².",
         "Kenaikan berasal dari tiga sumber: TT naik dari 138 (program v2) ke 150, faktor bruto realistis 1,45 (koridor "
         "2,40 m, inti, shaft) dibanding 1,14, dan utilitas serta parkir yang semula di basement kini menjadi gedung "
         f"utilitas + parkir 4.352 m². Rincian per butir disiapkan sebagai lampiran laporan antara.",
         "Target akhir 150 TT tetap. Konsultan menyerahkan rincian kenaikan luas (program ruang KAK dibanding konsep) "
         "sebagai lampiran laporan antara."),
        ("Basement, Parkir, dan Tangki Tanam",
         "Ketua yayasan menanyakan apakah basement benar tidak mungkin walau lebih mahal; bendahara menanyakan biayanya. "
         "Konsultan MEP owner meminta tangki solar dan IPAL tetap ditanam di halaman utara agar halaman rapi dan IPAL "
         "mengalir gravitasi.",
         "Basement dapat dibangun hanya dengan dinding potong menembus pasir U5 (±22 m) atau sumur pelepas permanen, "
         "karena FK blow-in 0,97-1,14 < 1,25 (SNI 8460:2017 Pasal 10.3.6.7.2), ditambah pemberat melawan uplift dan "
         "dewatering di dekat gudang bercerucuk. Biayanya dicatat sebagai informasi di laporan antara. Tangki tanam di "
         "muka air tanah dangkal perlu pengangkuran melawan gaya apung dan ventilasi di atas banjir; saluran keluar IPAL "
         "ke sungai perlu katup balik dan pompa karena muka air banjir dapat lebih tinggi dari saluran.",
         "Basement penuh tidak dilanjutkan; opsi C diterima. Selisih biaya basement dicatat sebagai informasi, bukan opsi. "
         "Lokasi dan cara pemasangan tangki solar, IPAL, dan tangki oksigen dijawab konsultan bersama konsultan MEP sebelum "
         "laporan antara."),
        ("Struktur dan Helipad",
         "Bendahara menanyakan alternatif yang lebih murah dari sistem ganda. Calon direktur menanyakan apakah atap "
         "menara dapat menampung chiller dan tangki air 150 m³ bersama helipad. MK mengingatkan rekomendasi perhubungan "
         "udara wajib sebelum PBG (PKKPR persyaratan 6).",
         f"SRPMK lebih murah ±Rp {fmt(hemat_str / 1000, 1)} M pada struktur atas, kurang dari 1 % perkiraan total, "
         "sedangkan sistem ganda lebih kaku untuk KDS D dan bangunan dengan inti tidak simetris. Atap menara 64 × 24 m; "
         "AW139 panjang keseluruhan 16,66 m, sehingga daerah landasan dan daerah aman mendekati lebar menara dan perlu "
         "dicek terhadap aturan helipad (dokumen acuannya belum ada). Chiller dan tangki air diusulkan di atap podium "
         "agar atap menara khusus helipad.",
         "Kategori risiko IV dan sistem ganda diterima. Helipad didesain untuk AW139. Penataan atap (helipad, chiller, "
         "tangki air) disajikan konsultan bersama konsultan MEP di laporan antara. Yayasan mengurus rekomendasi "
         "perhubungan udara."),
        ("Pondasi",
         "Bendahara menyoroti fondasi Rp 90 M dan 373 tiang sedalam 38 m. MK mendukung tiang bor di dekat gudang dan "
         "menanyakan tiang pancang tekan hidrolik (jack-in) di zona barat yang jauh dari gudang.",
         "Panjang tiang ditentukan lempung lunak dan pasir U5 yang mudah likuifaksi; tiang harus mencapai pasir padat U7, "
         "dan gesekan negatif mengurangi daya dukung izin menjadi 911 kN per tiang. Tiang jack-in bergetar rendah dan "
         "dapat menjadi varian V2 di zona barat bila uji tiang membuktikan tiang dapat ditekan menembus U6.",
         "Tiang bor di dekat gudang diterima. Penghematan pondasi, termasuk varian jack-in, dikaji lewat uji tiang."),
        ("Biaya",
         f"Bendahara menyatakan bank tidak akan menambah sebesar Rp {fmt(r['total'] / 1000, 0)} M; pembicaraan awal "
         "dengan bank memberi tambahan paling banyak ±Rp 60 M, belum pasti dan bergantung studi kelayakan baru. Ketua "
         "yayasan menyebut pagu tahap 1 realistis ±Rp 230 M. MK menilai rentang Rp 360-551 M terlalu lebar dan meminta "
         "sumber harga satuan.",
         "Rentang lebar berasal dari HSBGN Kota Jambi 2026 yang belum ditetapkan dan persentase nonstandar Permen PUPR "
         "22/2018 Pasal 29. Rentang menyempit setelah SK HSBGN dan survei harga (SE 47/2026 Lampiran I). Dengan pagu "
         "±Rp 230 M, tahap 1 hanya dapat memuat sebagian lingkup; konsultan menyusun paketnya.",
         "Perkiraan biaya diterima sebagai orde besaran. Konsultan menyusun paket tahap 1 dalam batas ±Rp 230 M untuk "
         "laporan antara, lengkap dengan rentang biaya dan sumber harga satuan."),
        ("Rekayasa Nilai",
         "Calon direktur menolak V1 bila podium LT3 utara berisi penunjang bedah atau ICU. Ketua yayasan menolak parkir "
         "93 mobil (V5) dan mengusulkan parkir permukaan sementara di halaman utara. Bendahara menanyakan mengapa "
         f"penghematan hanya Rp {fmt(rg['hemat_ve'] / 1000, 0)} M.",
         "Bedah sentral dan ICU di LT2, bukan LT3; podium LT3 utara berisi gizi, laundry, dan sebagian administrasi "
         "(zonasi 3.4) yang dipindah ke sisa LT3, sehingga V1 tidak menyentuh fungsi kritis. Penghematan terbatas karena biaya terbesar terikat pada 150 TT "
         "(luas dan M/E) dan kondisi tapak (fondasi, urugan), bukan pada pilihan desain. Parkir permukaan sementara di "
         "utara layak dikaji di area yang juga diurug, dengan memperhatikan gambut tebal di utara.",
         "V3, V4, V6, dan V7 disetujui. V1 disetujui dengan syarat fungsi yang ditunda bukan penunjang bedah, ICU, atau "
         "IGD. V2 disetujui sesudah uji tiang. V5 disetujui bila kekurangan parkir sampai 120 mobil ditutup parkir "
         "permukaan sementara di utara (dikaji konsultan). Uji tiang awal disetujui prinsipnya dengan dana yayasan "
         "setelah izin dinas; konsultan menyerahkan rincian biaya, jumlah tiang uji, dan jadwal."),
        ("Pembiayaan dan Jadwal",
         "Ketua yayasan tidak mau mengurangi target 150 TT; bendahara menyebut pengurangan TT menurunkan pendapatan dasar "
         "pinjaman. MK menilai lelang April-Mei 2027 tidak mungkin karena DED belum ada dan pembiayaan belum pasti, dan "
         "mengusulkan PVD dan urugan bertahap sebagai paket awal terpisah.",
         "Urugan bertahap dengan PVD membutuhkan ±5 bulan per tahap sebelum konstruksi gedung, sehingga paket awal "
         "urugan + PVD mempercepat jadwal tanpa menunggu DED gedung. Syaratnya gambar urugan, PVD, dan pemantauan "
         "penurunan disiapkan lebih dulu.",
         "D1: opsi bertahap; target akhir 150 TT, tahap 1 dibatasi ±Rp 230 M menunggu keputusan bank, konsultan "
         "menyajikan fungsi dan jumlah TT tahap 1. D6: lelang konstruksi utama ditunda sampai keputusan bank (target Juli "
         "2027); konsultan mengkaji paket awal urugan + PVD. Target operasi 1 Juli 2028 tetap diminta minimal untuk IGD "
         "dan sebagian rawat inap, dievaluasi di penyusunan jadwal."),
        ("Klaim Pemilik Gudang Timur",
         "Kuasa pemilik gudang (hadir tanpa undangan, diizinkan bicara) menyatakan gudang retak sejak uji pompa Desember "
         "2026, meminta ganti rugi sebelum proyek mulai, dan melarang galian di sisi timur. MK menanyakan data kondisi "
         "gudang sebelum uji pompa.",
         "Konsultan memeriksa catatan uji pompa (debit, lama, penurunan muka air di piezometer terdekat gudang) dan "
         "membandingkannya dengan jarak gudang dan waktu munculnya retak, lalu menyusun tanggapan teknis tertulis. "
         "Desain konsep sudah tanpa galian dalam dan memakai tiang bor di dekat gudang. Survei kondisi awal bersama "
         "diperlukan sebagai dasar setiap klaim berikutnya.",
         "Ganti rugi tidak dibahas di rapat ini. Konsultan menyusun tanggapan teknis tertulis atas klaim. Yayasan "
         "mengundang pemilik gudang ke survei kondisi awal bersama yang ditandatangani kedua pihak; surat resmi dikirim "
         "yayasan."),
    ]


KEPUTUSAN = [
    ["Kajian stabilitas tebing dan rencana saluran pembuang", "Konsultan", "Laporan antara"],
    ["Lokasi timbunan sementara dan uji mutu tanah gratis", "Konsultan", "30 Apr 2027"],
    ["Ramp beratap pasien dan ambulans di gambar konsep", "Konsultan", "Laporan antara"],
    ["Rincian kenaikan luas (KAK dibanding konsep)", "Konsultan", "Laporan antara"],
    ["Lokasi tangki solar, IPAL, dan tangki oksigen", "Konsultan + konsultan MEP", "Laporan antara"],
    ["Penataan atap: helipad, chiller, tangki air", "Konsultan + konsultan MEP", "Laporan antara"],
    ["Rekomendasi perhubungan udara", "Yayasan", "Sebelum PBG"],
    ["Paket tahap 1 ±Rp 230 M dengan rentang dan sumber harga", "Konsultan", "Laporan antara"],
    ["Kajian parkir permukaan sementara di utara (V5)", "Konsultan", "Laporan antara"],
    ["Rincian uji tiang awal (biaya, jumlah, jadwal)", "Konsultan", "30 Apr 2027"],
    ["Kajian paket awal urugan + PVD", "Konsultan, MK", "Laporan antara"],
    ["Tanggapan teknis klaim gudang dan undangan survei bersama", "Konsultan → Yayasan", "20 Apr 2027"],
    ["Keputusan bank atas tambahan pinjaman", "Yayasan", "Juli 2027"],
]


def main():
    lap = Laporan()
    lap.bab("", "Notulen Rapat Presentasi Desain Konsep", mulai_arab=True)
    lap.bab_aktif = "1"
    lap.paragraf("*DOKUMEN SIMULASI untuk studi kasus portofolio. Sikap dan keputusan pemberi tugas, MK, dan pemilik "
                 "gudang ditulis sesi skenario tersegel [Simulasi AI - sesi skenario]; jawaban konsultan disusun AI atas "
                 "permintaan Defsa dari hasil langkah 3.2-3.9. Disetujui Defsa 19 Nov 2026.*", inden=False)
    lap.subbab("1.1", "Data Rapat")
    lap.tabel("Data Rapat", ["Butir", "Keterangan"], [
        ["Acara", "Presentasi Desain Konsep, 5 April 2027"],
        ["Tempat", "Ruang rapat Yayasan Kesehatan Tepian Batanghari (simulasi)"],
        ["Peserta", "Ketua Yayasan, Bendahara Yayasan, calon Direktur RS, konsultan MEP pihak owner, Manajemen "
                    "Konstruksi, Konsultan Perencana; kuasa pemilik gudang timur (tidak diundang)"],
        ["Bahan", "3.10 Presentasi Desain Konsep; Excel 3.2-3.9; gambar GK-01 s.d. GK-08; model BIM LOD 200"],
    ], [3.5, 10.5], rata=list("ll"))
    lap.subbab("1.2", "Pembahasan")
    for i, (judul, owner, konsultan, sepakat) in enumerate(agenda(), start=1):
        lap.anak_subbab(f"1.2.{i}", judul)
        lap.butir("1.", f"**Pemberi tugas dan MK:** {owner}")
        lap.butir("2.", f"**Konsultan:** {konsultan}")
        lap.butir("3.", f"**Keputusan [Simulasi AI - sesi skenario]:** {sepakat}")
    lap.subbab("1.3", "Keputusan dan Tindak Lanjut")
    lap.paragraf("Tindak lanjut rapat dirangkum pada Tabel 1.2.")
    lap.tabel("Keputusan dan Tindak Lanjut Rapat", ["No", "Tindak lanjut", "Penanggung jawab", "Batas waktu"],
              [[i] + r for i, r in enumerate(KEPUTUSAN, start=1)], [1.0, 6.5, 3.7, 2.8], rata=list("clll"))
    lap.subbab("1.4", "Penutup")
    lap.paragraf("Desain konsep diterima dengan catatan di atas. Pembiayaan bertahap dengan tahap 1 ±Rp 230 M menjadi dasar "
                 "penyusunan laporan antara; desain struktur atas (Tahap 4) dimulai setelah paket tahap 1 dan data beban "
                 "MEP disepakati.")
    lap.simpan(KELUAR)
    ok, pesan = perbarui_word(KELUAR)
    print("ditulis:", KELUAR, "| field diperbarui" if ok else f"| Word gagal: {pesan[:200]}")


if __name__ == "__main__":
    main()
