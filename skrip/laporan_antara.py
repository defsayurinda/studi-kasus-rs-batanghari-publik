"""Susun Laporan Antara (.docx + PDF) sesudah Tahap 2-3 dan LA.1-LA.6, format FORMAT LAPORAN DAN EXCEL.md.

TOR Bagian 7 butir 2: laporan antara berisi konsep struktur dan pondasi serta parameter tanah desain. Angka diambil dari
skrip langkah 2.x, 3.x, dan LA.x (tidak diketik ulang); hasil LA.2 dan LA.3 dikutip dari ringkasan langkahnya (PR #19, #21).
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 20 Nov 2026 (LA.7).
Jalankan:  .venv\\Scripts\\python.exe skrip\\laporan_antara.py
"""
from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

import la1_zona as l1
import la5_lapangan as l5
import la6_biaya as l6
import la_utilitas as lu
import tahap3_basement as bs
import tahap3_biaya as bi
import tahap3_peil as pl
import tahap3_pondasi as fd
import tahap3_program as pr
import tahap3_struktur as st
import tahap3_tapak as tp
from format_dokumen import Laporan, perbarui_word
from tahap3_presentasi import _potong

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "10 Laporan" / "Laporan Antara.docx"
PDF = KELUAR.with_suffix(".pdf")
GB = AKAR / "03 Desain Konsep" / "Gambar"
STATUS = "disetujui Defsa 20 Nov 2026"


def f(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


def m(v):
    return f(v / 1000, 1)


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
    baris("LAPORAN ANTARA", 16, True)
    baris("", 12, sesudah=36)
    baris("JASA KONSULTANSI PERENCANAAN PEMBANGUNAN GEDUNG", 12, True)
    baris("RUMAH SAKIT TEPIAN BATANGHARI", 14, True)
    baris("Konsep Struktur dan Pondasi serta Parameter Tanah Desain", 12, sesudah=48)
    baris("Pemberi tugas: Yayasan Kesehatan Tepian Batanghari")
    baris("Rujukan: KAK No. 014/YKTB/KAK/X/2026, Bagian 7 butir 2", sesudah=48)
    baris("Disusun oleh:")
    baris("Defsa Yurinda", tebal=True)
    baris("(Studi kasus portofolio perencanaan)", sesudah=60)
    baris("JAMBI", tebal=True)
    baris("APRIL 2027", tebal=True, sesudah=36)
    baris("DOKUMEN SIMULASI untuk studi kasus portofolio. Yayasan, lahan, data tanah, dan semua angka fiktif; tidak untuk "
          f"konstruksi. Isi disusun dengan bantuan AI atas permintaan penulis; status: {STATUS} (lihat Subbab 8.4).", 10,
          miring=True)


def ringkasan(lap):
    rb = l6.rev_b()
    p = {x["kode"]: x for x in l6.paket()[0]}
    pe = pl.peil_usulan()
    lap.judul_depan("Ringkasan Eksekutif")
    lap.paragraf("Laporan antara ini menyajikan parameter tanah desain, konsep tapak, struktur, dan pondasi Rumah Sakit "
                 "Tepian Batanghari, serta menjawab 13 tindak lanjut rapat presentasi desain konsep (5 April 2027). "
                 "Hal pokok yang perlu diketahui pemberi tugas adalah sebagai berikut.")
    lap.daftar([
        f"**Tanah lunak dan banjir menentukan.** Lantai dasar dan utilitas pada +{f(pe['lantai'])}, halaman "
        f"+{f(pe['halaman'])} (Q50 terkoreksi +{f(pe['q50'])}, Q100 +{f(pe['q100'])}). Urugan dilakukan bertahap dengan PVD "
        f"selama ±{f(l5.paket_urugan()['durasi_rata'], 0)}-{f(l5.paket_urugan()['durasi_maks'], 0)} bulan.",
        "**Tanpa basement.** Gedung utilitas dan parkir 4 lantai di atas banjir; basement penuh tidak aman terhadap "
        "blow-in dan gaya angkat.",
        "**Struktur kategori risiko IV, KDS D, sistem ganda.** Grid 8 m, helipad disiapkan untuk AW139.",
        f"**Pondasi tiang bor Ø800 sampai pasir padat ±38 m**, {fd.opsi('A', True)['n_utama'] + fd.opsi('A', True)['n_gu']} "
        "tiang, dihitung per zona gambut; uji tiang sesuai SNI 8460:2017 Pasal 9.8.",
        f"**Biaya.** Perkiraan rev B ±Rp {m(rb['total_rev_b'])} M; setelah rekayasa nilai yang disetujui ±Rp "
        f"{m(rb['setelah_ve'])} M. Paket tahap 1 terkecil yang tetap beroperasi 50 TT ±Rp {m(p['E']['biaya'])}-"
        f"{m(p['D']['biaya'])} M, di atas batas ±Rp 230 M.",
        "**Keputusan yang diminta:** pembiayaan tahap 1, persetujuan uji tiang awal, perkuatan tebing, dan paket awal "
        "urugan + PVD (Subbab 8.2).",
    ])


def bab1(lap):
    lap.bab("I", "Pendahuluan", mulai_arab=True)
    lap.subbab("1.1", "Dasar")
    lap.paragraf("KAK Bagian 7 butir 2 meminta laporan antara berisi konsep struktur dan pondasi serta parameter tanah "
                 "desain. Laporan ini disusun sesudah olah data tanah (Tahap 2), desain konsep (Tahap 3), rapat presentasi "
                 "desain konsep 5 April 2027, dan kajian lanjutan LA.1-LA.6.")
    lap.subbab("1.2", "Maksud")
    lap.paragraf("Laporan ini menetapkan dasar teknis untuk desain struktur atas, struktur tengah, dan struktur bawah "
                 "(Tahap 4-6), serta menyajikan biaya dan pilihan pentahapan yang perlu diputuskan pemberi tugas sebelum "
                 "desain rinci.")
    lap.subbab("1.3", "Dokumen dan Data")
    lap.daftar([
        "Laporan pendahuluan dan notulen rapat pembahasannya (November 2026).",
        "Data penyelidikan tanah tambahan paket 1-11 (bor, CPTu, SPT, laboratorium, uji pompa, piezometer, kimia, tebing, "
        "survei gudang timur).",
        "Data owner dan instansi 8 Maret 2027: penetapan sempadan sungai, PKKPR, data hidrologi banjir, data MEP awal, "
        "surat arahan yayasan dengan lampiran surat Kantor SAR.",
        "Notulen rapat presentasi desain konsep 5 April 2027.",
    ])
    lap.subbab("1.4", "Batasan")
    lap.paragraf("Harga satuan, HSBGN Kota Jambi 2026, dan beberapa ukuran yang acuannya belum tersedia (aksesibilitas, "
                 "helipad, jarak tangki gas) berlabel asumsi sampai dokumennya tersedia. Data seluruhnya simulasi.")


def bab2(lap):
    lap.bab("II", "Data Baru Sejak Laporan Pendahuluan")
    lap.subbab("2.1", "Penyelidikan Tanah Tambahan")
    lap.paragraf("Penyelidikan tambahan memastikan muka air tanah dangkal (0,3-1,5 m), akuifer pasir U5 tertekan yang "
                 "terhubung sungai, lensa gambut yang menebal ke utara sampai 3,3-3,7 m, pasir U5 yang mudah likuifaksi, "
                 "tanah asam dan bersulfat, tebing P-2 bekas longsoran, serta gudang timur yang sudah turun perlahan.")
    lap.subbab("2.2", "Data Owner dan Instansi")
    lap.paragraf("Setiap berkas ditelaah sebelum dipakai. Kejanggalan yang ditemukan dan koreksinya dirangkum pada Tabel 2.1.")
    lap.tabel("Kejanggalan Data Owner dan Koreksinya", ["No", "Berkas", "Kejanggalan", "Koreksi"], [
        [1, "Surat sempadan", "STA diukur dari sudut tenggara ke barat", "x = 140 - STA"],
        [2, "Surat owner butir 1", "KDB dihitung dari luas persil (6.300 m²)", f"KDB dari lahan perencanaan: {f(tp.ringkasan()['kdb_maks'], 0)} m²"],
        [3, "Data hidrologi", "nol papan ≤ 2007 memakai arsip; 1999 hanya 6 bulan", "+0,35 m; 1999 dibuang"],
        [4, "Data hidrologi", "peil = Q50 + 0,30", "lantai ≥ Q100 + jagaan"],
        [5, "Data MEP", "gedung utilitas +11,30; tangki dan IPAL tanam di utara", "+12,85; tangki di atas tanah; IPAL dipindah"],
        [6, "Surat owner butir 5", "helikopter H145, lampiran SAR AW139", "AW139"],
        [7, "Surat owner butir 2-3", "lantai +11,50; urugan 6 minggu termasuk sempadan", "ditolak; urugan bertahap"],
    ], [1.0, 3.2, 5.0, 4.8], rata=list("clll"))


def bab3(lap):
    lap.bab("III", "Parameter Tanah Desain")
    lap.subbab("3.1", "Susunan Lapisan dan Parameter")
    lap.paragraf("Parameter desain per unit ditetapkan pada langkah 2.4 (nilai rata-rata dikurangi setengah simpangan baku) "
                 "dan disetujui pemberi tugas melalui konsultan. Ringkasannya pada Tabel 3.1.")
    lap.tabel("Parameter Tanah Desain per Unit", ["Unit", "Jenis", "γ (kN/m³)", "Parameter kuat", "Kompresibilitas"], [
        ["U1", "Urugan dan tanah penutup", "17,0", "-", "-"],
        ["U2", "Kerak lempung teguh", "17,8", "su 35 kPa", "Cc 0,38"],
        ["U3", "Gambut dan lempung organik", "10,7", "-", "Cc 3,5; Cα 0,21"],
        ["U4", "Lempung lunak", "15,2", "su = 5,2 + 1,09 z kPa", "Cc 0,75; cv 1,8 m²/th"],
        ["U5", "Pasir halus lepas-agak padat", "19,0", "φ' 33°; N60 ±12", "k ±8 × 10⁻⁵ m/s"],
        ["U6", "Lempung kaku", "19,1", "su 85 kPa", "Cc 0,37"],
        ["U7", "Pasir padat", "20,0", "N60 ±30", "-"],
    ], [1.2, 4.2, 1.8, 3.4, 3.4], rata=list("clcll"), sumber="Langkah 2.4 dan 2.8.")
    lap.subbab("3.2", "Air Tanah, Kelas Situs, Likuifaksi, dan Kimia")
    lap.daftar([
        "Tinggi tekan akuifer pasir U5 desain +11,20; kondisi artesis di utara (PZ-4B +0,53 m di atas muka tanah).",
        "Kelas situs SF (pasir U5 mudah likuifaksi, FS 0,22-0,75); spektrum sementara kelas SE dipakai pada konsep, "
        "analisis respons spesifik-situs di Tahap 4.",
        "Beton yang menyentuh gambut/lempung minimal kelas paparan S2 dengan perlindungan asam (pH 3,7-4,0).",
    ])
    lap.subbab("3.3", "Zona Gambut dan Profil per Zona")
    zz = l1.daya_dukung_zona()
    lap.paragraf("Tebal gambut diinterpolasi dari titik penyelidikan. Profil desain dibagi tiga zona (LA.1) seperti Tabel 3.2.")
    lap.tabel("Profil Desain per Zona Gambut", ["Zona", "Titik", "Gambut U3", "Urugan (m)", "Izin tiang Ø800 (kN)"], [
        [z, zz[z]["titik"], {"SELATAN": "< 0,5 m", "TENGAH": "0,5-2,0 m", "UTARA": "≥ 2,0 m"}[z], f(zz[z]["urugan"]),
         f(zz[z]["izin"], 0)] for z in zz], [2.6, 2.0, 2.8, 2.6, 4.0], rata=list("ccccc"), sumber="LA.1.")


def bab4(lap):
    pe = pl.peil_usulan()
    t = tp.ringkasan()
    tb = l5.timbunan()
    u = l5.paket_urugan()
    lap.bab("IV", "Konsep Tapak, Peil, Urugan, Drainase, dan Tebing")
    lap.subbab("4.1", "Amplop Tapak")
    lap.paragraf(f"Lahan perencanaan {f(t['lahan_perencanaan'], 0)} m² (persil dikurangi rumija dan ruang sempadan), "
                 f"sehingga tapak maksimum {f(t['kdb_maks'], 0)} m², luas lantai maksimum {f(t['klb_maks'], 0)} m², dan "
                 f"hijau minimum {f(t['kdh_min'], 0)} m². Tapak rencana {f(pr.cek_massa()['tapak'], 0)} m² dan luas lantai "
                 f"{f(pr.cek_massa()['luas_lantai'], 0)} m² memenuhi batas tersebut.")
    lap.gambar(_potong(GB / "GK-03 Rencana Tapak dan Massa.png"), "Rencana Tapak dan Massa (GK-03)", 15.0, sumber="Potongan area gambar; lembar A3 lengkap di PDF gambar.")
    lap.subbab("4.2", "Banjir Rencana dan Peil")
    lap.paragraf(f"Deret muka air maksimum tahunan dikoreksi (nol papan +0,35 m sebelum 2008, 1999 dibuang). Gumbel memberi "
                 f"Q50 +{f(pe['q50'])} dan Q100 +{f(pe['q100'])}; Log-Pearson III Q50 +11,48 dan Q100 +11,83 (LA.2). "
                 "Uji Chi-kuadrat dan Smirnov-Kolmogorov menerima keduanya; Gumbel dipakai karena konservatif dan sama dengan "
                 f"Q50 instansi. Peil lantai dan utilitas +{f(pe['lantai'])}, halaman +{f(pe['halaman'])}.")
    lap.subbab("4.3", "Urugan Bertahap dan Timbunan Sementara")
    lap.paragraf(f"Urugan padat ±{f(pl.volume_urugan(11.5)['v_padat'] / 1000, 1)}-{f(tb['v_padat'] / 1000, 1)} ribu m³. "
                 f"Tebal per tahap dibatasi {f(tb['h1'])} m agar lempung lunak tidak runtuh; dengan PVD segitiga 1,2 m tiap "
                 f"tahap ±{f(u['bulan_per_tahap'], 1)} bulan, sehingga urugan memerlukan {u['tahap_rata']}-{u['tahap_maks']} "
                 f"tahap. Tanah gratis yang dapat diterima ±{f(min(22000, tb['kapasitas_tahap1']), 0)} m³ sebagai urugan "
                 f"tahap 1 setelah PVD terpasang; sisanya ±{f(tb['sisa_ditolak'], 0)} m³ tidak dapat ditimbun di lokasi.")
    lap.paragraf("Cadangan gedung tahap 2 di utara berada di atas gambut 2-3,7 m. Urugan bertahap dengan PVD sekarang sudah "
                 "mencakup area itu, sehingga penurunannya selesai sebelum gedung tahap 2 dibangun; pondasinya kelak tiang "
                 "sampai U7 dengan gesekan negatif profil utara (LA.1).")
    lap.subbab("4.4", "Drainase dan Tebing")
    lap.paragraf("Kolam retensi menampung limpasan Q10 ±650 m³. Saluran pembuang ke sungai di x 128 (di luar zona labil) "
                 "dengan pipa Ø400, pintu klep +9,70, dan pompa 3 × 59 L/s (LA.3).")
    lap.paragraf("Analisis tebing P-2 (Bishop dan Fellenius, analisis balik dari kondisi tebing berdiri) memberi FK statis "
                 "1,01, surut cepat 0,92-1,00, dan gempa 0,48-0,72, di bawah FK izin SNI 8460:2017 Tabel 25 hal. 134. "
                 "Konsep perkuatan: pelandaian 1V:2H, berm bronjong di puncak +6,50, dan baris tiang atau turap di batas lahan "
                 "untuk gaya geser ≥ 209 kN/m. Batas urugan 1,0 m di jalur penyangga x 70-110 dipertahankan (LA.3).")
    lap.gambar(_potong(GB / "GK-11 Stabilitas Tebing.png"), "Stabilitas Tebing P-2 (GK-11)", 15.0,
               sumber="Potongan area gambar; lembar A3 lengkap di PDF gambar.")
    lap.subbab("4.5", "Utilitas Halaman dan Dermaga")
    d = lu.dermaga()
    ts = lu.tangki_solar()
    lap.daftar([
        f"Tangki solar tidak ditanam: tangki kosong mengapung (FK angkat {f(ts['fk_tanpa_pemberat'])}); dipasang di atas "
        "tanah dalam tanggul pada pelat +12,85. Tangki oksigen 10 m dari tangki solar. IPAL di luar zona gambut.",
        f"Dermaga: beda tinggi IGD dan air rendah {f(d['beda_tinggi'])} m, sehingga ramp 1:12 sepanjang "
        f"{f(d['ramp_1_12'], 0)} m tidak mungkin. Usulan ponton, jembatan berengsel {f(d['gangway'], 1)} m, dan lif brankar di "
        "puncak tebing x 8-22, dibangun pada tahap 2.",
        "Ramp beratap lobi 9,6 m dan ramp ambulans IGD 8,0 m menghubungkan halaman +12,05 dengan lantai +12,85.",
    ])
    lap.gambar(_potong(GB / "GK-12 Utilitas Halaman dan Atap.png"), "Utilitas Halaman dan Atap (GK-12)", 15.0, sumber="Potongan area gambar; lembar A3 lengkap di PDF gambar.")


def bab5(lap):
    sp = st.spektrum()
    h = lu.helipad()
    p = st.PRA["GANDA"]
    lap.bab("V", "Konsep Struktur")
    lap.subbab("5.1", "Sistem Struktur")
    lap.paragraf(f"Rumah sakit dengan bedah dan gawat darurat termasuk kategori risiko IV (Ie 1,5). Dengan SDS {f(sp['SDS'], 3)} "
                 f"dan SD1 {f(sp['SD1'], 3)} (sementara), kategori desain seismik {sp['KDS']}. Sistem ganda dinding geser dan "
                 "rangka pemikul momen khusus dipilih karena lebih kaku untuk inti yang tidak simetris; biaya struktur lebih "
                 f"tinggi {f(st.ringkasan()['selisih_biaya'] * 100, 1)} % dari SRPMK tetapi kurang dari 1 % biaya total.")
    lap.tabel("Pra-dimensi Unsur Struktur", ["Unsur", "Ukuran (mm)", "Dasar"], [
        ["Pelat", f"{p['pelat']}", "SNI 2847 Tabel 8.3.1.2"],
        ["Balok", f"{p['balok'][0]} × {p['balok'][1]}", "SNI 2847 Tabel 9.3.1.1"],
        ["Kolom podium / menara", f"{p['kolom_podium']} / {p['kolom_menara']}", "aksial ≤ 0,35 f'c Ag"],
        ["Dinding inti", f"{p['dinding']}", "sistem ganda"],
    ], [5.0, 4.0, 5.0], rata=list("lcl"), sumber="Langkah 3.6; diperiksa ulang di Tahap 4.")
    lap.gambar(_potong(GB / "GK-06 Rencana Struktur.png"), "Rencana Struktur Lantai 2 (GK-06)", 15.0, sumber="Potongan area gambar; lembar A3 lengkap di PDF gambar.")
    lap.subbab("5.2", "Atap dan Helipad")
    lap.paragraf(f"Helikopter rencana AW139 (6.800 kg, panjang 16,66 m). FATO {f(h['fato'], 1)} m ditambah area aman menjadi "
                 f"{f(h['area_aman'], 1)} m, lebih lebar dari menara 24 m, sehingga dek helipad baja kelak menjorok "
                 f"{f(h['kantilever'], 1)} m tiap sisi. Struktur atap disiapkan sekarang; dek dibangun kemudian. Chiller dan "
                 f"tangki air 158 t pindah ke atap podium ({f(h['beban_tangki_kPa'], 1)} kPa, balok khusus di Tahap 4).")
    lap.subbab("5.3", "Model BIM")
    lap.paragraf("Model gabungan LOD 200 (struktur, pondasi, dinding luar, jendela, ruang, halaman) di BIMCraft dan IFC4 "
                 "telah divalidasi; volume model cocok dengan pra-dimensi dalam 0-7,6 %.")
    lap.gambar(GB / "3.11 Model Konsep 3D.png", "Model Konsep LOD 200", 14.0)
    lap.gambar(_potong(GB / "GK-10 Potongan Konsep A-A.png"), "Potongan Konsep A-A (GK-10)", 15.0, sumber="Potongan area gambar; lembar A3 lengkap di PDF gambar.")


def bab6(lap):
    z = fd.opsi("A", True)
    j = l5.uji_tiang()
    g = l5.ringkas_gudang()
    lap.bab("VI", "Konsep Pondasi")
    lap.subbab("6.1", "Tiang Bor per Zona")
    lap.paragraf("Tiang menembus lempung lunak dan pasir U5 yang mudah likuifaksi sampai pasir padat U7 (±38 m). Gesekan "
                 "U1-U5 tidak dihitung; gesekan negatif akibat urugan dan likuifaksi diperlakukan sebagai beban (SNI "
                 "8460:2017 hal. 204, 295). Tiang bor tidak bergetar, sehingga aman bagi gudang bercerucuk di timur. Dengan "
                 f"profil per zona gambut diperlukan {z['n_utama'] + z['n_gu']} tiang (pemberi tugas memilih massa tetap di "
                 "tempat, LA.1).")
    lap.gambar(_potong(GB / "GK-07 Rencana Pondasi.png"), "Rencana Pondasi (GK-07)", 15.0, sumber="Potongan area gambar; lembar A3 lengkap di PDF gambar.")
    lap.subbab("6.2", "Uji Tiang")
    lap.tabel("Program Uji Tiang", ["Uji", "Jumlah", "Dasar"], [
        ["Tekan statik (sebelum konstruksi, terinstrumentasi)", j["pra"], "SNI 8460:2017 Pasal 9.8.1 hal. 188-189"],
        ["Tekan statik (saat konstruksi)", j["konstruksi"], "idem"],
        ["Lateral", j["lateral"], "Pasal 9.8.3 hal. 189"],
        ["Integritas CSL", j["csl"], "Pasal 9.8.5 hal. 190"],
        ["Tiang spun percobaan + PDA (V2)", j["trial_v2"], "Pasal 9.8.4 hal. 190"],
    ], [6.4, 2.0, 5.6], rata=list("lcl"),
              sumber=f"LA.5; beban uji {f(j['beban_uji'], 0)} kN (200 % beban rencana), batas deformasi 25 mm.")
    lap.subbab("6.3", "Gudang Timur")
    lap.paragraf(f"Uji pompa Desember 2026 menurunkan tinggi tekan pasir di dinding gudang ±{f(g['tarikan']['s'])} m selama "
                 f"{f(g['tarikan']['lama_hari'], 0)} hari; penurunan lempung yang mungkin ≤ {f(g['penurunan']['penurunan_mm'], 1)} "
                 "mm. Patok dan pengukur retak yang dipasang sebelum uji pompa tidak menunjukkan pengaruhnya. Tanggapan "
                 "teknis tertulis ada di Lampiran B. Selama konstruksi muka air sisi gudang dijaga ≥ +8,60.")


def bab7(lap):
    rb = l6.rev_b()
    pk = l6.paket()[0]
    lap.bab("VII", "Biaya dan Pentahapan")
    lap.subbab("7.1", "Kenaikan Luas")
    luas, _ = l6.rincian_luas()
    lap.tabel("Rincian Kenaikan Luas", ["Langkah", "Luas (m²)"], [[n, f(v, 0)] for n, v in luas] +
              [["Jumlah", f(pr.cek_massa()["luas_lantai"], 0)]], [11.0, 3.0], rata=list("lc"), sumber="LA.6.")
    lap.subbab("7.2", "Perkiraan Biaya")
    lap.paragraf(f"Perkiraan memakai cara Permen PUPR 22/2018 sebagai pedoman. Perkiraan rev B ±Rp {m(rb['total_rev_b'])} M "
                 f"({f(rb['total_rev_b'] / bi.PAGU)} × pagu Rp 168 M). Setelah rekayasa nilai yang disetujui rapat (V1, V3-V7) "
                 f"±Rp {m(rb['setelah_ve'])} M; bila tiang hibrida (V2) lolos uji tiang ±Rp {m(rb['setelah_v2'])} M. Basement "
                 f"penuh, sebagai informasi, menambah ±Rp {m(l6.basement_penuh()['selisih_bersih'])} M bersih.")
    lap.subbab("7.3", "Paket Tahap 1")
    lap.tabel("Paket Tahap 1 terhadap Batas ±Rp 230 M", ["Paket", "Isi", "Tahap 1 (Rp M)", "TT"],
              [[p["kode"], p["uraian"], m(p["biaya"]), p["tt"]] for p in pk], [1.8, 8.0, 2.6, 1.6], rata=list("clcc"),
              sumber="LA.6; harga [Asumsi], rentang ±20 %.")
    lap.paragraf("Paket terkecil yang tetap beroperasi 50 tempat tidur masih di atas batas karena biaya bersama fondasi "
                 "tiang, urugan dengan PVD, perkuatan tebing, dan uji tiang (±Rp 106 M) harus dibangun di tahap 1. Penyebabnya "
                 "kondisi tapak, bukan luas gedung.")


def bab8(lap):
    lap.bab("VIII", "Tanggapan Rapat, Keputusan, dan Kesimpulan")
    lap.subbab("8.1", "Tanggapan atas Tindak Lanjut Rapat Konsep")
    lap.tabel("Status Tindak Lanjut Rapat Konsep", ["No", "Tindak lanjut", "Jawaban", "Bab"], [
        [1, "Kajian tebing dan saluran pembuang", "FK < izin; perkuatan konsep; outlet x 128", "IV"],
        [2, "Timbunan sementara dan uji mutu", "±11.300 m³ di lokasi; 12 set uji", "IV"],
        [3, "Ramp beratap", "lobi 9,6 m, IGD 8,0 m", "IV"],
        [4, "Rincian kenaikan luas", "Tabel 7.1", "VII"],
        [5, "Tangki solar, IPAL, O2", "di atas tanah, di luar zona gambut", "IV"],
        [6, "Penataan atap", "helipad di menara, chiller dan tangki di podium", "V"],
        [7, "Rekomendasi perhubungan udara", "urusan yayasan", "-"],
        [8, "Paket tahap 1 ±Rp 230 M", "tidak tercapai; pilihan di 8.2", "VII"],
        [9, "Parkir permukaan sementara (V5)", "layak, 675 m², 27 mobil", "VII"],
        [10, "Rincian uji tiang", "Tabel 6.1", "VI"],
        [11, "Paket awal urugan + PVD", "4-5 tahap, ±20-26 bulan", "IV"],
        [12, "Tanggapan klaim gudang", "Lampiran B", "VI"],
        [13, "Keputusan bank", "urusan yayasan", "-"],
    ], [1.0, 5.0, 6.4, 1.6], rata=list("cllc"), sumber="Notulen rapat konsep 5 April 2027, Tabel 1.2.")
    lap.subbab("8.2", "Keputusan yang Diminta dari Pemberi Tugas")
    lap.daftar([
        "Pembiayaan tahap 1: (a) ±Rp 300-325 M, (b) tahap 1 diperkecil menjadi gedung 50 TT tersendiri dengan desain "
        "konsep diulang, atau (c) menunda sampai pembiayaan cukup.",
        "Persetujuan uji tiang awal (4 uji statik terinstrumentasi, tiang spun percobaan V2) dan izin dinas.",
        "Persetujuan konsep perkuatan tebing P-2 dan pengajuannya bersama permohonan PBG.",
        "Persetujuan paket awal urugan + PVD sebagai kontrak terpisah agar urugan dapat dimulai lebih dulu.",
        "Penyerahan data beban MEP rinci dan pelaksanaan survei kondisi awal gudang bersama pemiliknya.",
    ])
    lap.subbab("8.3", "Kesimpulan")
    lap.paragraf("Konsep struktur dan pondasi siap dilanjutkan ke desain rinci (Tahap 4-6) setelah pemberi tugas memilih "
                 "pembiayaan tahap 1. Bila pilihan (b), desain konsep perlu diulang sebelum Tahap 4.")
    lap.subbab("8.4", "Catatan Penyusunan")
    lap.paragraf("Laporan ini bagian dari studi kasus portofolio dengan data simulasi. Isi disusun dengan bantuan AI (Claude) "
                 "atas permintaan penulis dari hasil langkah 2.x, 3.x, dan LA.1-LA.6 yang disetujui penulis. "
                 f"Status laporan: {STATUS}.")


def lampiran(lap):
    lap.lampiran("A", "Daftar Gambar Konsep")
    lap.tabel("Daftar Gambar Konsep", ["No", "Gambar", "Isi"], [
        ["GK-01", "Batasan tapak", "sempadan, rumija, zona labil, gambut"],
        ["GK-02", "Peil dan urugan", "rencana urugan dan potongan"],
        ["GK-03", "Rencana tapak dan massa", "podium, menara, gedung utilitas"],
        ["GK-04", "Zonasi lantai", "LT1-LT6"],
        ["GK-05", "Parkir dan basement", "opsi C, potongan basement"],
        ["GK-06", "Rencana struktur", "grid, kolom, inti"],
        ["GK-07", "Rencana pondasi", "tiang bor"],
        ["GK-08", "Opsi pengurangan lingkup", "V1-V7"],
        ["GK-09", "Denah konsep LT1", "dari model BIMCraft"],
        ["GK-10", "Potongan konsep A-A", "dari model BIMCraft"],
        ["GK-11", "Penampang tebing", "LA.3"],
        ["GK-12", "Utilitas halaman dan atap", "LA.4"],
    ], [2.0, 5.0, 7.0], rata=list("cll"))
    lap.lampiran("B", "Tanggapan Teknis atas Klaim Gudang Timur")
    lap.paragraf("Tanggapan lengkap ada pada berkas terpisah '10 Laporan/Tanggapan Teknis Klaim Gudang Timur.docx' (LA.5). "
                 "Ringkasannya: data kondisi awal (patok, pengukur retak, inventaris retak) tidak menunjukkan retak atau "
                 "penurunan yang disebabkan uji pompa Desember 2026.")


def main():
    lap = Laporan()
    sampul(lap)
    lap.bagian_awal()
    ringkasan(lap)
    lap.daftar_isi()
    lap.daftar_tabel()
    lap.daftar_gambar()
    bab1(lap)
    bab2(lap)
    bab3(lap)
    bab4(lap)
    bab5(lap)
    bab6(lap)
    bab7(lap)
    bab8(lap)
    lampiran(lap)
    lap.simpan(KELUAR)
    ok, pesan = perbarui_word(KELUAR, PDF)
    print("ditulis:", KELUAR, "| field dan PDF lewat Word" if ok else f"| Word gagal: {pesan[:200]}")
    return KELUAR


if __name__ == "__main__":
    main()
