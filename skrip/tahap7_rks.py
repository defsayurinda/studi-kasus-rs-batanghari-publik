"""Tahap 7 langkah 7.7: RKS (spesifikasi teknis) per pekerjaan, Word + PDF.

Angka diambil dari dokumen tahap yang sudah disetujui (ANGKA: teks, berkas sumber); pasal acuan di PASAL dengan status
"dicek ke PDF" (halaman PDF di acuan/privat atau acuan/publik) atau "belum ada di acuan". Uji: tests/test_tahap7_rks.py.
"""
from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from format_dokumen import Laporan, perbarui_word

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "07 DED dan RKS" / "7.7 RKS.docx"
PDF = KELUAR.with_suffix(".pdf")
STATUS = "disetujui Defsa 23 Nov 2026"

S6 = "06 Struktur Bawah dan Basement/"
# (teks angka persis seperti di sumber, berkas sumber) -> dicek T-116 di uji
ANGKA = {
    "tiang_n": ("321", "07 DED dan RKS/7.5 Gambar Struktur.md"),  # akhir sesudah 7.3 (Audit Akhir AU-02)
    "tiang_utama": ("253", "07 DED dan RKS/7.5 Gambar Struktur.md"),
    "ujung": ("-27,60", S6 + "Ringkasan Tahap 6.md"),
    "capE": ("30,4 × 13,6 m", S6 + "Ringkasan Tahap 6.md"),
    "capE_h": ("h 2.000", S6 + "Ringkasan Tahap 6.md"),
    "cap_kolom": ("1.000 / 800 / 950", S6 + "Ringkasan Tahap 6.md"),
    "tul_tiang": ("16 D25", S6 + "Ringkasan Tahap 6.md"),
    "spiral": ("D13 40/80 mm", S6 + "Ringkasan Tahap 6.md"),
    "potong": ("-17,76", S6 + "Ringkasan Tahap 6.md"),
    "k_uji": ("489", S6 + "Ringkasan Tahap 6.md"),
    "uji_s": ("3.166", S6 + "6.8 Uji Tiang dan Pelaksanaan.md"),
    "uji_u": ("2.886", S6 + "6.8 Uji Tiang dan Pelaksanaan.md"),
    "uji_alt": ("2.278", S6 + "6.8 Uji Tiang dan Pelaksanaan.md"),
    "tarik": ("2.178", S6 + "6.8 Uji Tiang dan Pelaksanaan.md"),
    "lateral": ("107,9", S6 + "6.8 Uji Tiang dan Pelaksanaan.md"),
    "y_s": ("15,3", S6 + "6.8 Uji Tiang dan Pelaksanaan.md"),
    "y_u": ("26,0", S6 + "6.8 Uji Tiang dan Pelaksanaan.md"),
    "pit_plus": ("25 / 11", "10 Laporan/Audit Akhir.md"),  # 1 per 5 dari 321/253 (6.8: 24 / 11 dari 319/251)
    "q_maks": ("2,688", S6 + "6.8 Uji Tiang dan Pelaksanaan.md"),
    "heave": ("1,25", S6 + "6.8 Uji Tiang dan Pelaksanaan.md"),
    "batas_air": ("+8,6", S6 + "6.8 Uji Tiang dan Pelaksanaan.md"),
    "inc": ("0,18 mm/hari", S6 + "6.8 Uji Tiang dan Pelaksanaan.md"),
    "kepala": ("+10,85", S6 + "6.8 Uji Tiang dan Pelaksanaan.md"),
    "pvd": ("segitiga 1,2 m", S6 + "6.8 Uji Tiang dan Pelaksanaan.md"),
    "urugan": ("+11,50", S6 + "6.8 Uji Tiang dan Pelaksanaan.md"),
    "sisa_u": ("874", S6 + "6.8 Uji Tiang dan Pelaksanaan.md"),
    "delta": ("22,2 mm", S6 + "6.8 Uji Tiang dan Pelaksanaan.md"),
    "zhang": ("4,58 m", S6 + "Ringkasan Tahap 6.md"),
    "fk_tebing": ("1,22 / 1,22 / 0,74 / 1,03 / 0,68", S6 + "Ringkasan Tahap 6.md"),
    "kristalin": ("1 % berat semen", "05 Struktur Tengah/5.5 Desain Pit Lift.md"),
    "fasad": ("6.028 kN", "04 Struktur Atas/Ringkasan Tahap 4.md"),
    "peil": ("+12,85", "07 DED dan RKS/7.0 Telaah dan Daftar Dokumen.md"),
}


def a(kunci):
    return ANGKA[kunci][0]


SNI2847 = "SNI 2847:2019"
SNI8460 = "SNI 8460:2017"
# (bab, acuan, pasal, halaman PDF atau "-", status)
DICEK, BELUM = "dicek ke PDF", "belum ada di acuan"
PASAL = [
    ("I", "SE Dirjen Binkon 47/2026 Lampiran III", "biaya SMKK", "-", "ada di acuan/publik; pasal dirujuk di RAB Tahap 8"),
    ("II", SNI8460, "6.9 PVD", "122", DICEK),
    ("II", SNI8460, "11.5 penurunan sekitar galian; 11.6 instrumentasi", "280-281", DICEK),
    ("III", SNI8460, "Pasal 11 (dampak dewatering ke fondasi eksisting)", "277, 279", DICEK),
    ("III", "kriteria drawdown dan debit galian dangkal", "-", "-", BELUM),
    ("IV", SNI8460, "9.8.1 uji aksial tekan", "206-207", DICEK),
    ("IV", SNI8460, "9.8.2 tarik; 9.8.3 lateral", "207-208", DICEK),
    ("IV", SNI8460, "9.8.4 PDA; 9.8.5-9.8.6 integritas (CSL, PIT)", "208-209", DICEK),
    ("IV", SNI2847, "Tabel 20.6.1.3.1 selimut 75 mm kontak tanah", "482", DICEK),
    ("V", SNI8460, "7.5 kriteria perancangan lereng; 7.8 instrumentasi", "150, 156", DICEK),
    ("V", SNI8460, "6.6 jet grouting; 6.7 deep mixing", "92, 102", DICEK),
    ("V", "Youd 2002, Zhang 2004, Idriss-Boulanger 2008", "-", "-", BELUM),
    ("VI", SNI2847, "Tabel 19.3.2.1 paparan S2 (w/cm 0,45, f'c ≥ 31)", "464", DICEK),
    ("VI", SNI2847, "26.4 material beton; 26.5 produksi", "640-652", DICEK),
    ("VI", SNI2847, "26.5.3.2 perawatan ≥ 7 hari, ≥ 10 °C", "654", DICEK),
    ("VII", "SNI 2052:2017", "BjTS 420B", "7", DICEK),
    ("VII", SNI2847, "26.6 tulangan (penempatan, bengkok, las)", "660-664", DICEK),
    ("VII", "ASTM A955M (baja tahan karat)", "-", "-", BELUM),
    ("VIII", SNI2847, "26.11 bekisting; 26.13 inspeksi", "672, 681", DICEK),
    ("IX", SNI2847, "26.12.3.1 penerimaan kuat tekan (ASTM C172M, C31M, C39M)", "677", DICEK),
    ("IX", "SNI uji kuat tekan silinder, SNI slump", "-", "-", BELUM),
    ("X", SNI2847, "24.3.2, 24.3.5 kontrol spasi tulangan kedap", "573-574", DICEK),
    ("X", "aditif kristalin, membran HDPE (lembar data pabrik); ACI 350, EN 1992-3", "-", "-", BELUM),
    ("XI", "SNI pekerjaan arsitektur; pedoman teknis bangunan RS pengganti PMK 40/2022", "-", "-", BELUM),
    ("XII", "SNI 1727:2020", "Pasal 30 beban angin komponen dan klading", "223", DICEK),
    ("XII", "SNI kaca bangunan", "-", "-", BELUM),
    ("XIII", "SNI proteksi kebakaran, SNI 03-1746-2000, Permen PUPR 14/2017", "-", "-", BELUM),
    ("XIV", "SNI 1726:2019", "Pasal 13: komponen di atas isolator getaran wajib snubber", "139", DICEK),
    ("XIV", "pedoman getaran alat (rasio frekuensi chiller)", "-", "-", BELUM),
    ("XV", SNI2847, "26.13 inspeksi", "681", DICEK),
]

KEPUTUSAN = [
    ("K7.7-1", "Kriteria uji lateral", "Syarat SNI 9.8.3 (10 mm pada 100 %, 25 mm pada 200 %) dipakai sebagai kriteria "
     f"penerimaan. Bila y 100 % > 10 mm, tidak otomatis ditolak: dibandingkan dengan prediksi 6.5 ({a('y_s')} mm "
     f"selatan, {a('y_u')} mm utara) dan momen tiang dicek ulang oleh perencana", "Model 6.5 sudah memprediksi > 10 mm; "
     "tiang tetap kuat (rasio M 0,12)"),
    ("K7.7-2", "k urugan belum diuji", "Uji permeabilitas lapangan (uji resapan/slug) di 3 titik urugan sebelum galian cap; "
     "debit desain sementara skenario k 1e-4 m/s", "6.8 memakai tiga skenario [Asumsi]"),
    ("K7.7-3", "Kapasitas pompa", f"Tiap galian Cap E dan pit: 2 pompa aktif masing-masing ≥ 2 × Q desain "
     f"({a('q_maks')} m³/jam) + 1 cadangan [Asumsi: faktor 2]", "Debit kecil; cadangan untuk hujan"),
    ("K7.7-4", "Ambang berhenti kerja tebing", f"INC-1 laju > {a('inc')} selama 3 hari berturut: galian dan urugan "
     "dalam 30 m dari puncak tebing dihentikan dan perencana dipanggil", "Laju sekarang 0,177, margin tipis"),
    ("K7.7-5", "Perbaikan tanah U5", "Deep mixing (SNI 8460 6.7) sebagai acuan metode; dimensi, f'c tanah-semen, dan "
     "letak dari 7.3 dan GS-35; jet grouting (6.6) alternatif bila terhalang", "Deep mixing tidak menggetarkan gudang"),
    ("K7.7-6", "Mutu beton", "f'c 35 MPa untuk tiang, pile cap, sloof, pelat LT1 (paparan S2); struktur atas mengikuti "
     "gambar GS", "Keputusan 5.3 dan 6.7"),
]


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
    baris("RENCANA KERJA DAN SYARAT-SYARAT (RKS)", 16, True)
    baris("Spesifikasi Teknis", 12, sesudah=36)
    baris("PEMBANGUNAN GEDUNG RUMAH SAKIT TEPIAN BATANGHARI", 12, True)
    baris("Rumah sakit tipe C, 6 lantai, tepi Sungai Batanghari, Jambi", 12, sesudah=48)
    baris("Disusun oleh:")
    baris("Defsa Yurinda", tebal=True)
    baris("(Studi kasus portofolio perencanaan)", sesudah=60)
    baris("JAMBI", tebal=True)
    baris("2027", tebal=True, sesudah=36)
    baris("DOKUMEN SIMULASI untuk studi kasus portofolio. Data dan angka fiktif; TIDAK UNTUK KONSTRUKSI. Disusun AI atas "
          f"permintaan Defsa; status: {STATUS}.", 10, miring=True)


def pengantar(lap):
    lap.judul_depan("Ringkasan")
    lap.paragraf("RKS ini mengatur mutu bahan, cara kerja, pengujian, dan penerimaan pekerjaan struktur bawah, struktur, "
                 "arsitektur, fasad, kedap air, dan MEP dasar. Angka teknis dikutip dari dokumen tahap yang sudah disetujui "
                 "(rujukan berkas di tiap pasal); pasal acuan dicek ke PDF di folder acuan, dan yang tidak tersedia ditulis "
                 "\"belum ada di acuan\" (Lampiran C).")
    lap.daftar([
        f"**Pondasi:** {a('tiang_n')} tiang bor Ø800 ({a('tiang_utama')} gedung utama), ujung {a('ujung')}, "
        f"{a('tul_tiang')}, f'c 35 MPa; Cap E gabungan {a('capE')} {a('capE_h')}.",
        f"**Uji tiang:** 2 uji statik konstruksi ({a('uji_s')} / {a('uji_u')} kN), 1 tarik ({a('tarik')} kN), "
        f"1 lateral ({a('lateral')} kN), PIT tambahan, CSL ulang T113 + coring.",
        f"**Dewatering:** sump/parit, muka air di sisi gudang timur tidak di bawah {a('batas_air')}; berhenti kerja bila "
        f"INC-1 > {a('inc')}.",
        f"**Tebing:** serakan lateral Zhang {a('zhang')} ditangani perkuatan tebing (berm, baris tiang Ø600, perbaikan "
        "tanah U5).",
    ])


def bab1(lap):
    lap.bab("I", "Syarat Umum", mulai_arab=True)
    lap.subbab("1.1", "Lingkup Pekerjaan")
    lap.paragraf("Pekerjaan meliputi persiapan dan pekerjaan tanah, dewatering galian cap, tiang bor dan pengujiannya, "
                 "perkuatan tebing, beton bertulang, kedap air, arsitektur, fasad, proteksi kebakaran dan aksesibilitas "
                 "(syarat ruang), serta pekerjaan MEP dasar yang menyangkut struktur (bukaan, sleeve, landasan alat). "
                 "Desain sistem MEP di luar lingkup dokumen ini.")
    lap.subbab("1.2", "Urutan Dokumen")
    lap.paragraf("Bila terdapat perbedaan, urutan yang berlaku: (1) adendum, (2) RKS ini, (3) gambar DED (GA, GS, GM), "
                 "(4) model BIM (IFC) sebagai acuan geometri dan volume. Ukuran dari gambar tidak boleh diskala; ukuran "
                 "yang tidak ada ditanyakan ke perencana.")
    lap.subbab("1.3", "Mutu dan Pengendalian")
    lap.daftar([
        "Penyedia jasa menyerahkan rencana mutu kontrak (RMK), metode kerja, dan jadwal uji sebelum mulai.",
        "Bahan diserahkan contoh dan sertifikat pabrik; bahan yang ditolak dikeluarkan dari lapangan dalam 2 × 24 jam.",
        "Setiap uji disaksikan pengawas; hasil diserahkan paling lambat 3 hari kerja setelah uji.",
    ])
    lap.subbab("1.4", "Keselamatan Konstruksi")
    lap.paragraf("Penyedia jasa menerapkan SMKK; biaya SMKK dihitung menurut SE Dirjen Bina Konstruksi 47/2026 "
                 "Lampiran III (di RAB Tahap 8). Pekerjaan tepi tebing, galian, dan lubang bor terbuka diberi pagar dan "
                 "rambu; lubang bor yang ditinggal ditutup.")


def bab2(lap):
    lap.bab("II", "Persiapan dan Pekerjaan Tanah")
    lap.subbab("2.1", "Survei Kondisi Bangunan Sekitar")
    lap.paragraf("Sebelum pekerjaan dalam 20 m dari gudang timur: survei kondisi (retak lama dengan foto dan lebar, patok "
                 "penurunan, kemiringan), pemasangan piezometer dan inklinometer INC-3, pemberitahuan ke pemilik 3 hari "
                 "sebelumnya. Survei diulang setelah tiap tahap urugan dan galian.")
    lap.subbab("2.2", "Urugan dan PVD")
    lap.daftar([
        f"Urugan bertahap ±1 m, dipadatkan, sampai {a('urugan')}; PVD pola {a('pvd')} sampai dasar lempung lunak "
        f"({SNI8460} 6.9).",
        "Pelat penurunan dan piezometer dibaca mingguan; tahap berikutnya dimulai setelah derajat konsolidasi tahap "
        "sebelumnya memenuhi rencana 2.8.",
        f"Sisa penurunan setelah tiang (utara sampai {a('sisa_u')} mm) diperhitungkan pada pelat halaman dan sambungan "
        "utilitas: sambungan fleksibel di tepi gedung.",
    ])
    lap.subbab("2.3", "Galian Pile Cap dan Pit")
    lap.daftar([
        "Galian per zona: selatan lebih dulu, utara terakhir. Ruang kerja 1,0 m tiap sisi cap.",
        "Galian ≤ 1,0 m: tegak sementara atau lereng 1:1 bila kering; lebih dalam dari itu memakai lereng 1:1,5 atau "
        "turap sementara.",
        f"Dasar galian +10,05 (Cap E) sampai +11,25; kepala tiang dipapas sampai elevasi rencana (cap kolom "
        f"{a('kepala')}), beton rusak dibuang sampai beton sehat.",
    ])
    lap.subbab("2.4", "Pemantauan")
    lap.paragraf(f"Instrumen dan frekuensi pembacaan mengikuti {SNI8460} 11.6 (hal. PDF 281): patok gudang, piezometer, "
                 "inklinometer INC-1..3, pelat penurunan. Ambang dan tindakan ada di Lampiran B.")


def bab3(lap):
    lap.bab("III", "Dewatering Galian Cap")
    lap.subbab("3.1", "Metode")
    lap.daftar([
        "Cap kolom: sump terbuka dan parit pompa di dalam galian.",
        "Cap E dan pit lift: parit keliling dengan sump, pompa aktif dan pompa cadangan (K7.7-3).",
        "Muka air dijaga ≥ dasar galian - 0,5 m selama pembesian dan pengecoran, dan tidak lebih rendah dari "
        f"{a('batas_air')} di sisi gudang timur (kepala cerucuk gelam +8,62).",
        "Sumur dangkal, pengisian ulang, atau turap hanya bila ambang pemantauan dilampaui.",
    ])
    lap.subbab("3.2", "Data dan Syarat")
    lap.daftar([
        f"Debit desain terbesar {a('q_maks')} m³/jam (Cap E utara, skenario k 1e-4 m/s; 6.8 bagian 3). k urugan diuji "
        "di lapangan sebelum galian (K7.7-2).",
        f"Heave artesis: FS terkecil {a('heave')} (Cap E utara); galian tidak boleh lebih dalam dari rencana.",
        f"Tinjauan dampak dewatering ke fondasi eksisting wajib ({SNI8460} Pasal 11, hal. PDF 277, 279). Kriteria "
        "drawdown dan debit galian dangkal: belum ada di acuan.",
        "Air buangan dialirkan lewat bak pengendap sebelum ke saluran kota; tidak dibuang ke tebing.",
    ])


def bab4(lap):
    lap.bab("IV", "Tiang Bor dan Uji Tiang")
    lap.subbab("4.1", "Data Tiang")
    lap.tabel("Data Tiang Bor", ["Butir", "Ketentuan", "Sumber"], [
        ["Jumlah", f"{a('tiang_n')} tiang ({a('tiang_utama')} gedung utama, 68 utilitas)", "Ringkasan Tahap 6, 7.3, 7.5"],
        ["Diameter, ujung", f"Ø800 mm, ujung {a('ujung')}, kepala = +12,05 - h cap + 0,15", "6.1, Ringkasan Tahap 6"],
        ["Beton", "f'c 35 MPa, paparan S2 + perlindungan asam, selimut 75 mm ke spiral", "6.7; SNI 2847 Tabel 20.6.1.3.1"],
        ["Tulangan", f"{a('tul_tiang')} BjTS 420B; spiral {a('spiral')}; cap kolom dipotong di {a('potong')}, "
         "cap inti penuh", "6.7"],
        ["Pile cap", f"Kolom h {a('cap_kolom')} mm (2/3/4 tiang); Cap E {a('capE')}, {a('capE_h')}", "6.7"],
    ], [3.0, 7.5, 3.5], rata=list("lll"))
    lap.subbab("4.2", "Pelaksanaan")
    lap.daftar([
        "Lubang dibor dengan casing sementara melewati urugan, gambut, dan U5; di bawahnya distabilkan polimer atau "
        "bentonit dengan sifat lumpur dicek tiap lubang.",
        "Dasar lubang dibersihkan dan diukur; tulangan dipasang dengan penahan jarak selimut; CSL tube dipasang di tiang "
        "yang ditetapkan.",
        "Beton dicor dengan tremie tanpa putus; ujung tremie selalu terbenam ≥ 1,5 m; beton dibuang di atas elevasi "
        "papas sampai beton sehat.",
        "Tiang yang sudah dicor tidak dilewati alat berat dalam radius 6 m sebelum umur 7 hari.",
    ])
    lap.subbab("4.3", "Program Uji")
    lap.paragraf(f"Program uji mengikuti {SNI8460} 9.8 (hal. PDF 205-209) dan 6.8; rincian di Lampiran A.")
    lap.daftar([
        f"Uji statik tekan tambahan 2 tiang saat konstruksi: selatan {a('uji_s')} kN, utara {a('uji_u')} kN (200 % × "
        f"izin); alternatif minimum {a('uji_alt')} kN bila beban kentledge tidak memungkinkan. Kriteria: s ≤ 25 mm pada "
        "200 %, permanen ≤ 12 mm (9.8.1).",
        f"Uji tarik 1 tiang di Cap D, {a('tarik')} kN; deformasi ≤ PL/EA + 4 mm, maks 25 mm (9.8.2).",
        f"Uji lateral 1 tiang kepala bebas, {a('lateral')} kN; kriteria 9.8.3 dengan evaluasi K7.7-1.",
        f"PIT tambahan {a('pit_plus')} tiang ({a('tiang_n')} / {a('tiang_utama')}); CSL 1 per 20 dan PDA sudah terpenuhi; T218 dan T088 PDA "
        "diulang (palu 9 t, umur ≥ 28 hari).",
        "T113: CSL ulang dan coring dari kepala; bila cacat terkonfirmasi, grouting atau tiang pengganti dan cap "
        "diperlebar (6.8 bagian 2).",
    ])


def bab5(lap):
    lap.bab("V", "Perkuatan Tebing Sungai")
    lap.subbab("5.1", "Dasar")
    lap.paragraf(f"FK tebing P-2 dengan berm + pelandaian saja {a('fk_tebing')} (muka rendah / surut / gempa / kh 50 % / "
                 f"pasca-likuifaksi; 6.4) dan serakan lateral Zhang {a('zhang')} tidak tertahan tiang Ø800. Perkuatan "
                 f"(K7-1): berm + pelandaian, satu baris tiang bor Ø600 di batas lahan, dan perbaikan tanah U5 di jalur "
                 f"tebing sampai di belakang baris tiang y 26,3 m. Kriteria lereng {SNI8460} 7.5 (hal. PDF 150).")
    lap.subbab("5.2", "Pelaksanaan")
    lap.daftar([
        "Urutan: berm dan pelandaian di muka air rendah, tiang Ø600, lalu perbaikan tanah U5, sebelum urugan tahap 2 "
        "di zona selatan.",
        f"Perbaikan tanah U5 dengan deep mixing ({SNI8460} 6.7, hal. PDF 102) atau jet grouting (6.6, hal. PDF 92) "
        "(K7.7-5). Dimensi, pola, dan kuat tekan tanah-semen sesuai GS-35 dan 7.3; uji coring dan kuat tekan bebas 1 "
        "per 100 kolom.",
        f"Instrumentasi lereng {SNI8460} 7.8 (hal. PDF 156): INC-1, INC-2 dan patok puncak tebing; ambang K7.7-4.",
        "Metode serakan (Youd 2002, Zhang 2004, Idriss-Boulanger 2008): belum ada di acuan, label [Literatur].",
    ])


def bab6(lap):
    lap.bab("VI", "Pekerjaan Beton")
    lap.subbab("6.1", "Mutu dan Campuran")
    lap.tabel("Mutu Beton per Unsur", ["Unsur", "f'c (MPa)", "Paparan", "Syarat campuran"], [
        ["Tiang bor, pile cap, sloof, pelat LT1, pit", "35", "S2 + asam", "w/cm ≤ 0,45; f'c ≥ 31 (Tabel 19.3.2.1)"],
        ["Dinding geser", "35", "-", "Ringkasan Tahap 4"],
        ["Balok, kolom, pelat atas", "sesuai GS", "-", "gambar GS Tahap 4"],
        ["Lantai kerja", "10 [Asumsi]", "-", "tebal 50-100 mm"],
    ], [5.0, 2.0, 2.2, 4.8], rata=list("lccl"))
    lap.subbab("6.2", "Produksi, Pengecoran, dan Perawatan")
    lap.daftar([
        f"Beton siap pakai dari batching plant bersertifikat; material dan campuran memenuhi {SNI2847} 26.4 (hal. PDF "
        "640-651), rancangan campuran diserahkan dan diuji coba sebelum dipakai.",
        "Beton dicor ≤ 90 menit sejak dicampur [Asumsi]; dipadatkan dengan vibrator; sambungan konstruksi hanya di letak "
        "yang ditetapkan gambar (26.5.6).",
        f"Perawatan lembab ≥ 7 hari dengan suhu ≥ 10 °C ({SNI2847} 26.5.3.2, hal. PDF 654); cap tebal (Cap E h 2.000) "
        "diberi pemantauan suhu inti dan permukaan [Asumsi: beda ≤ 20 °C].",
    ])


def bab7(lap):
    lap.bab("VII", "Baja Tulangan")
    lap.daftar([
        "Tulangan ulir BjTS 420B (SNI 2052:2017, hal. PDF 7); sertifikat pabrik per lot dan uji tarik-lentur 1 contoh "
        "per 25 ton per diameter [Asumsi].",
        f"Penempatan, bengkokan, dan las mengikuti {SNI2847} 26.6 (hal. PDF 660-664); las tulangan hanya bila ditunjukkan "
        "gambar.",
        "Zona MRI 2 × 2 m pelat panel 9-10/D-E: baja tahan karat ASTM A955M (keputusan 5.2); standar belum ada di acuan, "
        "sertifikat pabrik wajib.",
        "Selimut ditahan beton decking setebal selimut; kawat ikat tidak boleh masuk selimut.",
    ])


def bab8(lap):
    lap.bab("VIII", "Bekisting dan Inspeksi")
    lap.daftar([
        f"Bekisting kaku, rapat, dan dirancang penyedia jasa ({SNI2847} 26.11, hal. PDF 672); bongkar setelah kuat "
        "beton cukup menurut metode yang disetujui.",
        f"Inspeksi sebelum cor: tulangan, selimut, sleeve, angkur, dan elevasi; formulir izin cor ditandatangani "
        f"pengawas ({SNI2847} 26.13, hal. PDF 681).",
    ])


def bab9(lap):
    lap.bab("IX", "Pengujian Beton")
    lap.daftar([
        "Benda uji silinder diambil, dirawat, dan diuji menurut ASTM C172M, C31M, C39M "
        f"({SNI2847} 26.12.3.1 a, hal. PDF 677).",
        "Penerimaan: tiap rata-rata tiga uji berurutan ≥ f'c, dan tidak ada hasil kurang dari f'c - 3,5 MPa "
        "(f'c ≤ 35 MPa) (26.12.3.1 b).",
        "Bila tidak memenuhi: langkah perbaikan campuran (26.12.3.1 c) dan evaluasi beton terpasang dengan core.",
        "SNI uji kuat tekan silinder dan SNI slump: belum ada di acuan; slump diuji tiap truk.",
    ])


def bab10(lap):
    lap.bab("X", "Kedap Air Pit Lift dan Pelat LT1")
    lap.daftar([
        f"Beton kedap dengan aditif kristalin {a('kristalin')} dan waterstop di sambungan pit (keputusan 5.5).",
        "Membran HDPE pra-pasang di bawah lantai kerja dan dinding luar pit.",
        f"Kontrol spasi tulangan sisi tanah {SNI2847} 24.3.2 dan 24.3.5 (hal. PDF 573-574).",
        "Produk aditif dan membran: lembar data pabrik belum ada di acuan; ACI 350 dan EN 1992-3 (lebar retak 0,2 mm) "
        "belum ada di acuan. Uji genang pit 48 jam [Asumsi] sebelum serah terima.",
    ])


def bab11(lap):
    lap.bab("XI", "Pekerjaan Arsitektur")
    lap.daftar([
        f"Peil lantai LT1 {a('peil')}; level dan grid mengikuti model ARS 7.1 dan STR 6.9.",
        "Dinding, lantai, plafon, pintu, dan jendela sesuai daftar finishing dan daftar pintu-jendela gambar GA.",
        "Ruang klinis (OK, ICU, CSSD): lantai vinil homogen tanpa sambungan, plafon kedap, sudut melengkung [Asumsi].",
        "SNI pekerjaan arsitektur dan pedoman teknis bangunan RS pengganti PMK 40/2022: belum ada di acuan; Permenkes "
        "6/2026 (ada di acuan) mengatur klasifikasi RS, bukan rincian bahan.",
    ])


def bab12(lap):
    lap.bab("XII", "Fasad")
    lap.daftar([
        "Fasad V4: panel putih berjendela pita, pita kaca biru, dinding tirai, podium panel abu, mahkota menara "
        "(keputusan rencana 7 no. 3).",
        "Beban angin komponen dan klading SNI 1727:2020 Pasal 30 (hal. PDF 223); gambar "
        "kerja dan hitungan angkur dari pemasok diserahkan dan disetujui.",
        f"Berat fasad akhir dibandingkan dengan {a('fasad')} (4.10, V3); bila naik > 5 % angkur dan balok tepi dicek "
        "ulang (T-112). Overstek digantung pada konsol balok tepi (+3,60 sampai +3,90 dari lantai).",
        "SNI kaca bangunan: belum ada di acuan; kaca pengaman berlapis untuk bidang di atas jalan [Asumsi].",
    ])


def bab13(lap):
    lap.bab("XIII", "Proteksi Kebakaran dan Aksesibilitas")
    lap.paragraf("Tangga darurat, kompartemen, jalur evakuasi, dan fasilitas aksesibilitas mengikuti gambar GA. Acuan "
                 "(SNI proteksi kebakaran, SNI 03-1746-2000 sarana jalan ke luar, Permen PU 26/PRT/M/2008, Permen PUPR "
                 "14/2017): belum ada di acuan; dicek oleh pengkaji teknis sebelum PBG.")


def bab14(lap):
    lap.bab("XIV", "MEP Dasar yang Menyangkut Struktur")
    lap.daftar([
        "Bukaan dan sleeve hanya di letak gambar GM dan GS; bukaan baru di balok, kolom, atau dinding geser harus disetujui "
        "perencana struktur.",
        "Landasan alat (chiller, AHU, genset) dicor bersama atau dijangkar ke pelat sesuai gambar.",
        "Chiller M-01 di atas pegas 25 mm (keputusan rencana 7 no. 5, menunggu 7.3). Komponen di atas isolator getaran "
        "wajib bumper/snubber tiap arah horizontal dan penahan vertikal (SNI 1726:2019 Pasal 13, hal. PDF 139). "
        "Pedoman getaran alat: belum ada di acuan.",
    ])


def bab15(lap):
    lap.bab("XV", "Toleransi, Penerimaan, dan Dokumen Akhir")
    lap.tabel("Toleransi Pelaksanaan", ["Unsur", "Toleransi", "Dasar"], [
        ["Posisi kepala tiang", "75 mm [Asumsi]", "praktik; acuan belum ada"],
        ["Kemiringan tiang", "1:100 [Asumsi]", "praktik; acuan belum ada"],
        ["Elevasi kepala tiang", "± 25 mm [Asumsi]", "praktik"],
        ["Selimut", "- 10 mm / + 12 mm [Asumsi]", "praktik; dicek saat inspeksi 26.13"],
        ["Penurunan beda sloof", f"≤ δ desain {a('delta')}", "6.6 varian (d)"],
    ], [4.0, 4.5, 5.5], rata=list("lcl"))
    lap.paragraf("Dokumen akhir: catatan bor per tiang, hasil uji (statik, PDA, PIT, CSL, beton, tulangan), data "
                 "pemantauan, gambar terpasang (as-built), dan model IFC terpasang.")


def lampiran(lap):
    lap.lampiran("A", "Program Uji Tiang")
    lap.tabel("Program Uji Tiang SNI 8460 9.8", ["Uji", "Jumlah tambahan", "Beban", "Letak"], [
        ["Statik tekan", "2 (konstruksi)", f"{a('uji_s')} / {a('uji_u')} kN", "selatan 9/B, utara Cap E"],
        ["Statik tarik", "1", f"{a('tarik')} kN", "Cap D (43,2; 68,4)"],
        ["Lateral", "1", f"{a('lateral')} kN", "zona selatan [Asumsi]"],
        ["PIT", a("pit_plus"), "-", "acak per zona"],
        ["CSL", "0 + T113 ulang", "-", "T113 (46,4; 41,8)"],
        ["PDA", "0 (T218, T088 diulang)", "palu 9 t", "-"],
    ], [2.6, 3.4, 3.6, 4.4], rata=list("lccl"), sumber="6.8 Uji Tiang dan Pelaksanaan, bagian 2")
    lap.lampiran("B", "Ambang Pemantauan dan Tindakan")
    lap.tabel("Ambang Pemantauan", ["Instrumen", "Ambang", "Tindakan"], [
        ["INC-1 tebing", f"laju > {a('inc')} 3 hari", "hentikan galian dan urugan 30 m dari puncak tebing (K7.7-4)"],
        ["Piezometer sisi gudang", f"muka air < {a('batas_air')}", "kurangi pompa, pengisian ulang"],
        ["Patok gudang", "penurunan > 10 mm atau retak baru [Asumsi]", "hentikan dewatering terdekat, lapor"],
        ["Galian Cap E", "air naik dari dasar (heave)", "isi kembali galian, turunkan tinggi tekan"],
    ], [3.5, 4.0, 6.5], rata=list("lll"), sumber="6.8; 2.8; keputusan RKS")
    lap.lampiran("C", "Daftar Pasal Acuan dan Keputusan")
    lap.tabel("Daftar Pasal Acuan per Bab", ["Bab", "Acuan", "Pasal", "Hal. PDF", "Status"],
              [list(p) for p in PASAL], [1.2, 3.6, 4.6, 1.6, 3.0], rata=list("cllcl"), ukuran=10)
    lap.tabel("Keputusan RKS (atas delegasi Defsa 22 Nov 2026)", ["Kode", "Butir", "Keputusan", "Alasan"],
              [list(k) for k in KEPUTUSAN], [1.6, 2.6, 6.4, 3.4], rata=list("clll"), ukuran=10)


def main(pdf=True):
    lap = Laporan()
    sampul(lap)
    lap.bagian_awal()
    pengantar(lap)
    lap.daftar_isi()
    lap.daftar_tabel()
    for f in (bab1, bab2, bab3, bab4, bab5, bab6, bab7, bab8, bab9, bab10, bab11, bab12, bab13, bab14, bab15, lampiran):
        f(lap)
    lap.simpan(KELUAR)
    if pdf:
        ok, pesan = perbarui_word(KELUAR, PDF)
        print("ditulis:", KELUAR, "| field dan PDF lewat Word" if ok else f"| Word gagal: {pesan[:200]}")
    return KELUAR


if __name__ == "__main__":
    main()
