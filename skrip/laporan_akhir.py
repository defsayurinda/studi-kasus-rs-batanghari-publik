"""Susun Laporan Akhir (.docx + PDF) Tahap 10, format FORMAT LAPORAN DAN EXCEL.md.

Angka dikutip dari Ringkasan Tahap 2-9 (K10-1, Mode cepat: tidak dihitung ulang). Disusun AI atas delegasi Defsa
(23 Nov 2026). Jalankan:  .venv\\Scripts\\python.exe skrip\\laporan_akhir.py
"""
from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from format_dokumen import Laporan, perbarui_word

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "10 Laporan" / "Laporan Akhir.docx"
PDF = KELUAR.with_suffix(".pdf")
RENDER = AKAR / "07 DED dan RKS" / "Render" / "R-01.png"
GANTT = AKAR / "09 Jadwal" / "9 Gantt dan Kurva S.png"
STATUS = "disetujui Defsa 23 Nov 2026 (disusun atas delegasi, ditelaah Defsa)"

# Angka kunci (dikutip, dicek oleh tests/test_laporan_akhir.py terhadap ringkasan tahap: T-126)
RAB_TOTAL = "286,22"
RAB_SEBELUM_PPN = "257,86"
DURASI_MINGGU = 98
TIANG, CAP = 321, 84
LUAS = "19.328"
RAB = [  # divisi, Rp miliar, porsi (Ringkasan Tahap 8 bagian 1)
    ("I Persiapan", "8,55", "3,3 %"),
    ("II Tanah dan pondasi (321 tiang bor Ø800, 84 cap)", "48,40", "18,8 %"),
    ("III Struktur atas", "26,44", "10,3 %"),
    ("IV Arsitektur", "42,37", "16,4 %"),
    ("V Tapak dan pematangan lahan", "16,61", "6,4 %"),
    ("VI MEP RS (Permen PUPR 22/2018 Ps. 29)", "112,72", "43,7 %"),
    ("VII SMKK (SE 47/2026 Lamp. III)", "2,76", "1,1 %"),
]
VE = [  # kode, uraian, hemat Rp miliar, syarat (Ringkasan Tahap 8 bagian 2, Tahap 9 T-125)
    ("VE-1", "Spiral tiang D13-80 menjadi D13-150 di bawah 6 m atas", "1,92", "cek perencana SNI 2847"),
    ("VE-2", "Curtain wall sistem stick", "2,80", "persetujuan owner"),
    ("VE-3", "Acian langsung pada bata ringan", "3,07", "persetujuan owner"),
    ("VE-4", "Dek helipad pada tahap 2", "3,20", "persetujuan owner"),
    ("VE-5", "Lantai rawat inap HT", "0,20", "persetujuan owner"),
    ("VE-6 (usul)", "Sewa tower crane 2 × 11 bulan, bukan 2 × 18 bulan", "1,89", "T-125; sebelum PPN"),
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
    baris("LAPORAN AKHIR", 16, True)
    baris("", 12, sesudah=36)
    baris("JASA KONSULTANSI PERENCANAAN PEMBANGUNAN GEDUNG", 12, True)
    baris("RUMAH SAKIT TEPIAN BATANGHARI", 14, True)
    baris("Geoteknik, Struktur, BIM/DED, RAB, dan Jadwal", 12, sesudah=48)
    baris("Pemberi tugas: Yayasan Kesehatan Tepian Batanghari")
    baris("Rujukan: KAK No. 014/YKTB/KAK/X/2026", sesudah=48)
    baris("Disusun oleh:")
    baris("Defsa Yurinda", tebal=True)
    baris("(Studi kasus portofolio perencanaan)", sesudah=60)
    baris("JAMBI", tebal=True)
    baris("AGUSTUS 2027", tebal=True, sesudah=36)
    baris("DOKUMEN SIMULASI untuk studi kasus portofolio. Yayasan, lahan, data tanah, dan semua angka fiktif; tidak untuk "
          f"konstruksi. Isi disusun dengan bantuan AI atas permintaan penulis; status: {STATUS} (lihat Subbab 9.4).", 10,
          miring=True)


def ringkasan(lap):
    lap.judul_depan("Ringkasan Eksekutif")
    lap.paragraf("Laporan akhir ini merangkum seluruh perencanaan Rumah Sakit Tepian Batanghari (tipe C, 150 TT, gedung "
                 f"utama 6 lantai dan gedung utilitas/parkir 4 lantai, luas kotor {LUAS} m²) di tepi Sungai Batanghari: "
                 "data dan parameter tanah, desain konsep, struktur atas, tengah, dan bawah, model BIM dan DED, RAB, "
                 "serta jadwal pelaksanaan. Hal pokok bagi pemberi tugas sebagai berikut.")
    lap.daftar([
        "**Tanah menentukan desain.** Lempung lunak, gambut sampai 3,7 m, dan pasir U5 yang mudah likuifaksi (kelas "
        "situs SF). Peil lantai +12,85 di atas Q50 terkoreksi +11,85; urugan bertahap dengan PVD; tanpa basement.",
        "**Struktur kategori risiko IV, KDS D, sistem ganda** dengan spektrum spesifik-situs (SDS 0,386, SD1 0,459); "
        "simpangan maksimum 46 % batas.",
        f"**Pondasi {TIANG} tiang bor Ø800 sampai ±38 m pada {CAP} pile cap**, gesekan negatif dan likuifaksi "
        "diperhitungkan; perkuatan tebing P-2 di batas lahan.",
        "**DED 64 lembar** (arsitektur 23, struktur 35, MEP dasar 6) dan RKS 15 bab, semuanya dari model BIM federasi "
        "IFC4 yang sudah dicek clash.",
        f"**RAB Rp {RAB_TOTAL} miliar** termasuk PPN 11 % (Rp 14,81 juta/m²). Pagu Rp 168 miliar terlampaui karena luas, "
        "bukan harga satuan. Rekayasa nilai VE-1..VE-5 hemat Rp 11,19 miliar, usul VE-6 tower crane ±Rp 2,10 miliar.",
        f"**Jadwal {DURASI_MINGGU} minggu (22,6 bulan)**, lintasan kritis pondasi, struktur LT1-LT2, MEP, dan uji fungsi.",
        "**Keputusan yang diminta:** pagu ±Rp 275 miliar dengan VE, atau pembangunan bertahap (Subbab 9.1).",
    ])


T2, T3, T4, T5, T6, T7 = ("02 Olah Data Tanah/", "03 Desain Konsep/", "04 Struktur Atas/", "05 Struktur Tengah/",
                          "06 Struktur Bawah dan Basement/", "07 DED dan RKS/")
POTONG = AKAR / "cache" / "laporan_gambar"   # lembar CAD dipotong ke area gambar (tanpa kolom keterangan); tidak di-commit
GRAFIK_RAB = AKAR / "10 Laporan" / "Gambar" / "RAB per Divisi dan VE.png"

# (berkas, judul, potong lembar A3, lebar cm); sumber = folder berkas
GAMBAR = {
    "2.3": [
        (T2 + "Gambar/GT-02 Penampang A-A'.png", "Penampang Geoteknik A-A' (GT-02): stratigrafi U1-U8 dan muka air", True, 15),
        (T2 + "Gambar/GT-09 Profil Parameter Lempung.png", "Profil Parameter Lempung Lunak U4 (GT-09): su, σ'p, Cc terhadap kedalaman", True, 15),
        (T2 + "Gambar/GT-11 Profil Vs dan Kelas Situs.png", "Profil Vs dan Kelas Situs SF (GT-11)", True, 15),
        (T2 + "Gambar/GT-12 Likuifaksi Pasir U5.png", "Evaluasi Pemicu Likuifaksi Pasir U5 (GT-12): FS 0,22-0,75", True, 15),
        (T2 + "Gambar/GT-15 Penurunan Akibat Urugan.png", "Penurunan Akibat Urugan dan Konsolidasi dengan PVD (GT-15)", True, 15),
    ],
    "3.1": [
        (T3 + "Gambar/3.11 Model Konsep 3D.png", "Model Konsep 3D Gedung Utama dan Gedung Utilitas/Parkir di atas Tiang", False, 14),
        (T3 + "Gambar/GK-02 Peil dan Urugan.png", "Peil Lantai +12,85 dan Rencana Urugan (GK-02)", True, 15),
        (T3 + "Gambar/GK-03 Rencana Tapak dan Massa.png", "Rencana Tapak dan Massa Bangunan (GK-03)", True, 15),
        (T3 + "Gambar/GK-11 Stabilitas Tebing.png", "Stabilitas Tebing P-2 dan Saluran Pembuang (GK-11)", True, 15),
    ],
    "4.3": [
        (T4 + "Gambar/GS-01 Respons Spesifik Situs.png", "Analisis Respons Spesifik Situs (GS-01): profil Vs, spektrum permukaan, spektrum desain", True, 15),
        (T4 + "Rekaman Gempa/sintetis/Spektrum Rekaman Sintetis.png", "Spektrum Tujuh Rekaman Sintetis terhadap Target MCER Batuan SB", False, 14),
        (T4 + "Gambar/Analisis 3D/01_model_3d.png", "Model Analisis 3D Struktur Atas: kolom, balok, dan inti dinding geser", False, 15),
        (T4 + "Gambar/Analisis 3D/02_ragam_1.png", "Ragam Getar 1: T = 0,684 detik, translasi arah X", False, 15),
        (T4 + "Gambar/Analisis 3D/05a_deformasi_gempa_X.png", "Deformasi Akibat Gempa Statik Ekivalen Arah X (V = 13.164 kN)", False, 15),
        (T4 + "Gambar/Analisis 3D/06a_momen_portal.png", "Diagram Momen Lentur Portal Tipikal akibat Gempa Arah X", False, 15),
        (T4 + "Gambar/4.9 Model LOD 300 3D.png", "Model BIM Struktur Atas LOD 300", False, 13),
        (T5 + "Gambar/5.7 Model LOD 300 3D.png", "Model BIM Struktur Tengah LOD 300 (pelat LT1, sloof, pit, tangki)", False, 13),
    ],
    "5.1": [
        (T6 + "Gambar/6.2 Kurva A B Selatan.png", "Bidang Netral dan Gesekan Negatif Tiang Bor Ø800, Zona Selatan", False, 14),
        (T6 + "Gambar/6.4 Profil Serakan Lateral.png", "Profil Serakan Lateral Akibat Likuifaksi U5", False, 15),
        (T6 + "Gambar/6.5 Profil Kinematik.png", "Respons Kinematik Tiang: perpindahan, momen, dan geser terhadap elevasi", False, 15),
        (T6 + "Gambar/6.6 Peta Penurunan (d).png", "Peta Penurunan Total Kepala Pile Cap, Varian (d) Terkalibrasi Uji Beban (maks 24,6 mm)", False, 14),
        (T6 + "Gambar/6.7 Cap E Pelat Momen.png", "Momen Pelat Pile Cap Inti E (analisis pelat di atas tiang)", False, 11),
        (T6 + "Gambar/6.9 Model Pondasi 3D.png", "Model BIM Pondasi LOD 300: tiang bor dan pile cap", False, 14),
        (T6 + "Gambar/GT-16 Potongan Tebing P-2.png", "Potongan Tebing P-2 dan Bidang Kritis dengan Perkuatan (GT-16)", True, 15),
    ],
    "6.1": [
        (T7 + "Gambar/7.1 Model ARS 3D Udara.png", "Model Arsitektur LOD 300 dari Udara (IFC)", False, 15),
        (T7 + "Render/R-06.png", "Render R-06: udara dekat, helipad AW139 dan atap podium", False, 15),
        (T7 + "Render/R-03.png", "Render R-03: udara, konteks tapak, gedung utama, gedung parkir, dan jalan", False, 15),
        (T7 + "Render/R-04.png", "Render R-04: senja, lobi dan gerbang utara", False, 15),
        (T7 + "Render/R-08.png", "Render R-08: gedung dari seberang Sungai Batanghari", False, 15),
        (T7 + "Gambar/GA-13 Tampak Selatan Utara.png", "Tampak Selatan dan Utara (GA-13)", True, 15),
    ],
}


def gambar_siap(rel, potong):
    """Lembar CAD A3 dipotong ke area gambar (kolom keterangan kanan dibuang) agar terbaca di halaman laporan."""
    p = AKAR / rel
    if not potong:
        return p
    from PIL import Image
    POTONG.mkdir(parents=True, exist_ok=True)
    out = POTONG / p.name
    if not out.exists() or out.stat().st_mtime < p.stat().st_mtime:
        im = Image.open(p)
        w, h = im.size
        im.crop((int(0.012 * w), int(0.015 * h), int(0.776 * w), int(0.985 * h))).save(out)
    return out


def galeri(lap, kunci, judul, pengantar):
    lap.subbab(kunci, judul)
    lap.paragraf(pengantar)
    for rel, jdl, potong, lebar in GAMBAR[kunci]:
        if (AKAR / rel).exists():
            # lembar CAD selebar teks agar terbaca; plot/render 13,5 cm agar dua per halaman bila muat
            lap.gambar(gambar_siap(rel, potong), jdl, min(lebar, 14.0 if potong else 13.5),
                       sumber=f"{Path(rel).parent.as_posix()}/{Path(rel).name}.")


def grafik_rab():
    """Grafik batang RAB per divisi dan penghematan VE (angka dari konstanta RAB/VE, tidak dihitung ulang)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    f = lambda s: float(s.replace(".", "").replace(",", "."))  # noqa: E731
    GRAFIK_RAB.parent.mkdir(parents=True, exist_ok=True)
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.5, 1]})
    nama = [r[0].split(" (")[0] for r in RAB][::-1]
    nilai = [f(r[1]) for r in RAB][::-1]
    a.barh(nama, nilai, color="#3b6ea5")
    for y, v in enumerate(nilai):
        a.text(v + 1, y, f"{v:.2f}".replace(".", ","), va="center", fontsize=9)
    a.set_xlabel("Rp miliar (sebelum PPN)")
    a.set_title(f"RAB per divisi, jumlah Rp {RAB_SEBELUM_PPN} miliar", fontsize=10)
    a.set_xlim(0, max(nilai) * 1.18)
    kode = [v[0].replace(" (usul)", "*") for v in VE]
    hemat = [f(v[2]) for v in VE]
    b.bar(kode, hemat, color=["#5a9e6f"] * 5 + ["#b0b0b0"])
    for x, v in enumerate(hemat):
        b.text(x, v + 0.05, f"{v:.2f}".replace(".", ","), ha="center", fontsize=9)
    b.set_ylabel("Hemat (Rp miliar)")
    b.set_title("Rekayasa nilai (* usul, sebelum PPN)", fontsize=10)
    for ax in (a, b):
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=9)
    fig.text(0.99, 0.01, "DATA SIMULASI. Sumber: Ringkasan Tahap 8, T-125.", ha="right", fontsize=7, color="#666")
    fig.tight_layout()
    fig.savefig(GRAFIK_RAB, dpi=200)
    plt.close(fig)
    return GRAFIK_RAB


def bab1(lap):
    lap.bab("I", "Pendahuluan", mulai_arab=True)
    lap.subbab("1.1", "Dasar dan Lingkup")
    lap.paragraf("KAK meminta perencanaan lengkap gedung rumah sakit tipe C: penyelidikan dan olah data tanah, desain "
                 "konsep, perencanaan struktur, DED, RKS, RAB, dan jadwal. Laporan Pendahuluan dan Laporan Antara (April "
                 "2027) sudah disampaikan; laporan ini menutup seluruh tahap.")
    lap.subbab("1.2", "Alur Kerja")
    lap.tabel("Tahap Perencanaan dan Keluarannya", ["Tahap", "Isi", "Keluaran utama"], [
        ["0-1", "Kerangka acuan, penyelidikan tanah", "laporan penyelidikan, telaah data"],
        ["2", "Olah data tanah", "parameter U1-U8, kelas situs, gambar GT-01..GT-16"],
        ["3", "Desain konsep", "peil, program ruang, konsep struktur dan pondasi, GK-01..GK-12"],
        ["4-5", "Struktur atas dan tengah", "analisis 3D, desain unsur, model LOD 300/350"],
        ["6", "Struktur bawah", "tiang bor, pile cap, tebing, program uji tiang"],
        ["7", "BIM, DED, RKS, render", "model federasi, 64 lembar DED, RKS, R-01..R-08"],
        ["8", "RAB", "volume dari model, AHSP, RAB 6 divisi + SMKK, VE"],
        ["9", "Jadwal", "CPM 21 kegiatan, Gantt, kurva S, XML ProjectLibre"],
        ["10", "Laporan akhir", "laporan ini, halaman portofolio"],
    ], [1.6, 5.4, 7.0], rata=list("cll"))
    lap.subbab("1.3", "Cara Kerja openBIM")
    lap.paragraf("Model dibangun di BIMCraft dan dipertukarkan sebagai IFC4 (dicek IfcOpenShell). Gambar DED digambar "
                 "di CADCraft dari geometri yang diekspor model, dengan satu kop A3. Volume RAB diambil otomatis dari "
                 "Qto IFC. Setiap angka penting dicek silang dua cara dan dicatat di VERIFIKASI.md (T-06 s.d. T-125).")


def bab2(lap):
    lap.bab("II", "Data dan Geoteknik")
    lap.subbab("2.1", "Kondisi Tanah dan Air Tanah")
    lap.tabel("Hasil Olah Data Tanah", ["Butir", "Hasil"], [
        ["Stratigrafi", "U1-U8; gambut U3 menebal ke utara sampai 3,3-3,7 m; pasir U5 pada 9-19 m"],
        ["Air tanah", "akuifer U5 tertekan, k ≈ 8 × 10⁻⁵ m/s; tinggi tekan desain +11,20"],
        ["Parameter", "U4: su = 5,2 + 1,09 z kPa, Cc 0,75; U3: Cc 3,5; U5: φ' 33°"],
        ["Kelas situs", "SF (v̄s30 139-171 m/s, U5 mudah likuifaksi)"],
        ["Likuifaksi", "amax 0,342 g, Mw 7,0; FS 0,22-0,75 di seluruh U5"],
        ["Kimia", "gambut pH 3,7-4,0, sulfat S1-S2: beton kontak tanah minimal S2"],
        ["Penurunan urugan", "primer 0,15-0,39 m (selatan) s.d. 1,05-1,18 m (utara); PVD 1,2 m ±5 bulan"],
    ], [3.5, 10.5], rata=list("ll"), sumber="Ringkasan Tahap 2.")
    lap.subbab("2.2", "Kesalahan Data Penyedia")
    lap.paragraf("Tujuh kesalahan data penyelidikan ditemukan dan dikoreksi sebelum dipakai, antara lain σ'p BH-5 UD-1, "
                 "t50 disipasi CPTu-5/8, satuan sulfat T-2, dan batimetri P-3. Pada Tahap 4 juga ditemukan lapisan Vs "
                 "167 m/s di 46-47 m yang hanya loncatan pemicu; masukan respons situs memakai batuan SB di ±85 m.")
    galeri(lap, "2.3", "Gambar Hasil Analisis Geoteknik",
           "Gambar berikut diambil dari lembar GT Tahap 2 (CADCraft, dipotong ke area gambar). Penampang dan profil "
           "parameter menjadi dasar desain pondasi; evaluasi likuifaksi menunjukkan seluruh pasir U5 mencair pada gempa "
           "rencana, dan analisis urugan menentukan PVD serta urugan bertahap.")


def bab3(lap):
    lap.bab("III", "Desain Konsep")
    lap.tabel("Keputusan Desain Konsep", ["Butir", "Keputusan"], [
        ["Peil", "Q50 terkoreksi +11,85; lantai dan utilitas +12,85; halaman +12,05"],
        ["Urugan", "30-38 ribu m³, bertahap ±1 m dengan PVD segitiga 1,2 m"],
        ["Program", f"150 TT, {LUAS} m² (gedung utama 14.976 + utilitas/parkir 4.352)"],
        ["Parkir", "basement ditolak (FK blow-in 0,97-1,14 < 1,25); gedung parkir 4 lantai"],
        ["Struktur", "kategori IV, KDS D, sistem ganda, grid 8 m, helipad AW139"],
        ["Biaya konsep", "±Rp 451 miliar; pembiayaan bertahap disepakati di rapat konsep"],
    ], [3.5, 10.5], rata=list("ll"), sumber="Ringkasan Tahap 3.")
    galeri(lap, "3.1", "Gambar Desain Konsep",
           "Model konsep dan lembar GK menunjukkan keputusan pokok: lantai dinaikkan ke +12,85 di atas banjir Q50 "
           "terkoreksi, gedung parkir di atas tanah menggantikan basement, dan tebing sungai diperkuat.")


def bab4(lap):
    lap.bab("IV", "Struktur Atas dan Tengah")
    lap.subbab("4.1", "Gempa dan Analisis")
    lap.paragraf("Tujuh rekaman sintetis dicocokkan ke MCER batuan SB dan dirambatkan lewat kolom tanah (pystrata, "
                 "OpenSees). Spektrum spesifik-situs dibatasi 80 % spektrum SE: SDS 0,386, SD1 0,459, KDS D. Berat "
                 "seismik gedung utama 159.156 kN, geser dasar 13.164 kN; T1 0,684/0,592 detik; simpangan maksimum 46 % "
                 "batas 0,010 hsx. Torsi 1b arah Y diterima dengan ρ 1,3.")
    lap.subbab("4.2", "Unsur Struktur")
    lap.tabel("Ukuran Unsur Struktur", ["Unsur", "Ukuran / tulangan", "Acuan"], [
        ["Pelat lantai", "200 mm, D10-125 s.d. D10-200", "SNI 2847 Ps. 8.10"],
        ["Balok SRPMK", "350 × 600; transfer tangki 450 × 800 (opsi B)", "SNI 2847 Ps. 18.6"],
        ["Kolom", "750 / 650; kolom tangki 800", "SNI 2847 Ps. 18.7"],
        ["Dinding geser", "350 mm, fc' 35, tanpa elemen batas khusus", "SNI 2847 Ps. 18.10"],
        ["Pelat LT1", "250 mm, D13-200, fc' 35 (paparan S2); panel MRI baja tahan karat", "SNI 2847"],
        ["Sloof", "SL-1 400 × 900; SL-2/SL-3 400 × 800", "SNI 2847, 5.4"],
        ["Pit lift", "pelat dasar 0,45 m, FK angkat 1,11 pada Q100", "SNI 8460 Ps. 9.3.4"],
    ], [3.2, 7.2, 3.6], rata=list("lll"), sumber="Ringkasan Tahap 4 dan 5.")
    galeri(lap, "4.3", "Gambar Hasil Analisis Struktur",
           "Rangkaian gambar mengikuti alur analisis: rekaman gempa dicocokkan ke target, dirambatkan menjadi spektrum "
           "spesifik situs, lalu dipakai pada model 3D OpenSees untuk ragam getar, deformasi, dan gaya dalam. Hasil "
           "desain dimodelkan ke BIM LOD 300.")


def bab5(lap):
    lap.bab("V", "Struktur Bawah")
    lap.tabel("Angka Kunci Pondasi", ["Butir", "Hasil"], [
        ["Tiang", f"bor Ø800, f'c 35, 16 D25, spiral D13 40/80; ujung -27,60 (±38 m); {TIANG} tiang, {CAP} cap"],
        ["Daya dukung", "Qult statis/gempa 4.770/3.294 kN (selatan); izin 911 kN; GEC10 + SNI 8460"],
        ["Gesekan negatif", "bidang netral -13,7 s.d. -16,7; Q + Qn ±2.930-3.003 kN"],
        ["Cap E inti", "gabungan 30,4 × 13,6 m, h 2.000 mm, diperlebar untuk pit L-7 (+2 tiang)"],
        ["Penurunan", "maksimum 24,6 mm (kalibrasi uji beban)"],
        ["Tebing P-2", "berm + pelandaian + baris tiang Ø600 dan perbaikan U5; FK gempa 0,74 tanpa perkuatan"],
        ["Uji tiang", "4 uji statik awal, 2 uji konstruksi 200 %, 1 tarik, 1 lateral (SNI 8460 Ps. 9.8)"],
    ], [3.5, 10.5], rata=list("ll"), sumber="Ringkasan Tahap 6 dan 7 (7.3).")
    galeri(lap, "5.1", "Gambar Hasil Analisis Pondasi",
           "Tiang bor menanggung gesekan negatif dari urugan dan gambut, serakan lateral akibat likuifaksi U5, dan beban "
           "gempa inersia. Gambar berikut menunjukkan bidang netral, respons kinematik tiang, peta penurunan "
           "terkalibrasi uji beban, momen pile cap inti, model BIM pondasi, dan perkuatan tebing.")


def bab6(lap):
    lap.bab("VI", "BIM, DED, dan RKS")
    lap.paragraf("Model arsitektur LOD 300 (1.414 dinding, 224 pintu, 235 ruang) dan struktur LOD 300 (321 IfcPile, 84 "
                 "pile cap) digabung dengan alat MEP dalam model federasi. Clash turun dari 1.612 ke 1.156 pasangan "
                 "(sisa sudah dinilai); shaft dan jalur IGD diperbaiki sehingga jarak MRI ke lajur ambulans 12,0 m.")
    lap.tabel("Dokumen DED", ["Disiplin", "Lembar", "Isi"], [
        ["Arsitektur", "GA-01..GA-23", "denah, tampak, potongan, rencana tapak"],
        ["Struktur", "GS-01..GS-35", "spektrum, beban, denah dan detail balok, kolom, pelat, pondasi, tebing"],
        ["MEP dasar", "GM-01..GM-06", "shaft, ruang alat, bukaan, beban alat"],
        ["RKS", "15 bab + 3 lampiran", "program uji tiang, ambang pemantauan, pasal acuan"],
    ], [3.0, 3.5, 7.5], rata=list("lll"), sumber="Ringkasan Tahap 7.")
    if RENDER.exists():
        lap.gambar(RENDER, "Render Eksterior R-01 (versi revisi, Blender Cycles dari IFC federasi, 3.200 × 1.800 px)", 15,
                   sumber="07 DED dan RKS/Render.")
    galeri(lap, "6.1", "Model dan Visualisasi",
           "Render dibuat dengan Blender Cycles langsung dari IFC federasi, sehingga yang terlihat sama dengan model "
           "yang dipakai untuk Qto RAB. Lembar tampak GA-13 adalah contoh gambar DED dari model.")


def bab7(lap):
    lap.bab("VII", "RAB dan Rekayasa Nilai")
    lap.subbab("7.1", "Rekapitulasi")
    lap.paragraf("Volume diambil otomatis dari Qto IFC (beton 14.435,7 m³, besi 1.881,6 t, bekisting 29.319 m²). AHSP "
                 "rinci 12 item mencakup 85,1 % biaya, BTL 12 % (Permen PUPR 8/2023 Ps. 11(3)); harga [Asumsi: Jambi 2026].")
    lap.tabel("Rekapitulasi RAB", ["Divisi", "Rp miliar", "Porsi"],
              [list(r) for r in RAB] + [["Jumlah", RAB_SEBELUM_PPN, "100 %"], ["PPN 11 %", "28,36", ""],
                                         ["**Total dibulatkan**", f"**{RAB_TOTAL}**", "Rp 14,81 juta/m²"]],
              [8.5, 2.5, 3.0], rata=list("lrr"), sumber="Ringkasan Tahap 8.")
    lap.subbab("7.2", "Pagu dan Rekayasa Nilai")
    lap.paragraf("Pagu Rp 168 miliar disusun untuk 12.000 m² × Rp 14 juta. Biaya per m² RAB hanya 6 % di atas asumsi itu; "
                 f"selisih Rp 118,2 miliar berasal dari luas {LUAS} m². Pagu cukup untuk ±11.345 m².")
    lap.tabel("Usulan Rekayasa Nilai", ["Kode", "Uraian", "Hemat (Rp miliar)", "Syarat"], [list(v) for v in VE],
              [2.2, 6.3, 2.3, 3.2], rata=list("llrl"), sumber="Ringkasan Tahap 8; VE-6 dari T-125 Tahap 9.")
    lap.gambar(grafik_rab(), "RAB per Divisi dan Penghematan Rekayasa Nilai", 15.5,
               sumber="Ringkasan Tahap 8 dan T-125; grafik oleh skrip/laporan_akhir.py.")
    lap.paragraf("VE-1..VE-5 menurunkan RAB menjadi Rp 275,0 miliar; dengan VE-6 (±Rp 2,10 miliar termasuk PPN) menjadi "
                 "±Rp 272,9 miliar. RAB 8b tidak diubah sampai owner memutuskan.")


def bab8(lap):
    lap.bab("VIII", "Jadwal Pelaksanaan", lanskap=True)
    lap.paragraf(f"Jadwal CPM 21 kegiatan, mulai 3 Jan 2028 [Asumsi], dengan bobot dari RAB sebelum PPN (Rp {RAB_SEBELUM_PPN} miliar). Durasi "
                 f"{DURASI_MINGGU} minggu (22,6 bulan), cadangan ±1,4 bulan terhadap SMKK 24 bulan. Lintasan kritis: "
                 "persiapan, pematangan lahan, tiang bor (20 minggu, 2 rig), galian dan cap, struktur LT1-LT2, MEP "
                 "instalasi kasar dan alat utama, uji fungsi. Kurva S mencapai 26 % di minggu 26 dan 56 % di minggu 52.")
    if GANTT.exists():
        lap.gambar(GANTT, "Gantt dan Kurva S", 24, sumber="09 Jadwal/9 Gantt dan Kurva S.png.")
    lap.paragraf("Tower crane hanya dipakai 9,9 bulan, sedangkan RAB menyewa 18 bulan (T-125 gagal): dasar usul VE-6. "
                 "Risiko jadwal terbesar adalah produktivitas tiang bor (+7 minggu bila 1 tiang/rig/hari, T-123).")


def bab9(lap):
    lap.bab("IX", "Keputusan, Butir Terbuka, dan Kesimpulan", lanskap=False)
    lap.subbab("9.1", "Keputusan yang Diminta dari Pemberi Tugas")
    lap.daftar([
        "Pagu: (a) dinaikkan ke ±Rp 275 miliar dengan VE-1..VE-5 (±Rp 273 miliar bila VE-6 diterima), atau (b) "
        "dibangun bertahap dengan opsi lingkup 3.8 (V1 podium LT3, V5 LT4 parkir, V6 LT6 cangkang).",
        "Persetujuan VE-2..VE-6; VE-1 setelah cek tulangan transversal tiang oleh perencana.",
        "Persetujuan program uji tiang awal dan perkuatan tebing P-2 bersama permohonan PBG.",
        "Penunjukan konsultan MEP untuk RAB dan jadwal MEP rinci.",
    ])
    lap.subbab("9.2", "Butir Terbuka")
    lap.tabel("Butir Terbuka", ["No", "Butir", "Tindak lanjut"], [
        ["O-3", "Dimensi akhir perkuatan tebing B-2", "gambar rinci sebelum tender"],
        ["O-5", "Temuan koordinasi MEP (pompa, chiller, SH-7)", "konsultan MEP"],
        ["O-6", "Acuan belum ada (Permen PUPR 14/2017, SNI uji material)", "lengkapi acuan/"],
        ["O-2 / O-4 / O-8", "Tulangan perlebaran Cap E, GA-11 atap, Pset IFC tambahan", "di luar lingkup portofolio (tidak mengubah angka)"],
        ["O-10", "Seluruh uji Tahap 7-10 belum dijalankan", "setelah pendingin laptop diperbaiki"],
        ["O8-1", "Survei harga SE 47/2026 Lampiran I", "harga masih [Asumsi]"],
        ["O8-2 / O9-2", "MEP masih persentase", "RAB dan jadwal MEP rinci"],
        ["O9-1", "Durasi selain tiang bor [Asumsi]", "metode pelaksanaan kontraktor"],
    ], [2.4, 7.0, 4.6], rata=list("lll"), sumber="Ringkasan Tahap 7-9.")
    lap.subbab("9.3", "Kesimpulan")
    lap.paragraf("Perencanaan siap ditenderkan setelah owner memutuskan pagu atau pentahapan. Angka terbesar yang belum "
                 "pasti adalah MEP (43,7 % biaya) dan harga satuan; desain struktur dan pondasi tidak bergantung pada "
                 "keputusan pagu kecuali bila lingkup dikurangi.")
    lap.subbab("9.4", "Catatan Penyusunan")
    lap.paragraf("Laporan ini bagian dari studi kasus portofolio dengan data simulasi. Isi disusun dengan bantuan AI (Claude) "
                 "dari Ringkasan Tahap 2-9; angka tidak dihitung ulang (K10-1). Cek silang gagal yang dijelaskan: "
                 f"T-113, T-121a/b, T-125. Status laporan: {STATUS}.")


DED = [  # lembar DED terpilih untuk Lampiran B (lanskap, satu lembar per halaman)
    (T7 + "Gambar/GA-02 Rencana Tapak.png", "Rencana Tapak (GA-02)"),
    (T7 + "Gambar/GA-04 Denah LT1 Barat.png", "Denah Lantai 1 Barat (GA-04)"),
    (T7 + "Gambar/GA-15 Potongan A-A B-B.png", "Potongan A-A dan B-B (GA-15)"),
    (T7 + "Gambar/GA-16 Detail Fasad.png", "Detail Fasad (GA-16)"),
    (T4 + "Gambar/GS-04 Denah Struktur LT1.png", "Denah Struktur Lantai 1 (GS-04)"),
    (T4 + "Gambar/GS-11 Potongan A-A.png", "Potongan Struktur A-A (GS-11)"),
    (T4 + "Gambar/GS-15 Dinding Inti Balok Kopel.png", "Dinding Inti dan Balok Kopel (GS-15)"),
    (T6 + "Gambar/GS-28 Denah Tiang dan Pile Cap.png", "Denah Tiang dan Pile Cap, 321 Tiang (GS-28)"),
    (T6 + "Gambar/GS-31 Detail Tiang Bor.png", "Detail Tiang Bor Ø800 (GS-31)"),
    (T7 + "Gambar/GM-03 Ruang Alat Atap Podium.png", "Ruang Alat Atap Podium dan Rel Chiller (GM-03)"),
]


def lampiran(lap):
    lap.lampiran("A", "Daftar Keluaran per Tahap")
    lap.tabel("Daftar Keluaran", ["Tahap", "Berkas utama"], [
        ["2", "02 Olah Data Tanah/Ringkasan Tahap 2.md, 2.x *.xlsx, GT-01..GT-16"],
        ["3", "03 Desain Konsep/Ringkasan Tahap 3.md, GK-01..GK-12, Laporan Antara"],
        ["4-5", "04 Struktur Atas, 05 Struktur Tengah: Ringkasan, GS-01..GS-26"],
        ["6", "06 Struktur Bawah dan Basement: Ringkasan, GS-28..GS-32"],
        ["7", "07 DED dan RKS: model RSTB-FED-T7.ifc, 7.4/7.5/7.6 DED .pdf, 7.7 RKS, Render"],
        ["8", "08 RAB: 8a Volume dan AHSP.xlsx, 8b RAB SMKK VE.xlsx"],
        ["9", "09 Jadwal: 9 Jadwal dan Kurva S.xlsx, 9 Jadwal.xml"],
        ["10", "10 Laporan: Laporan Akhir, Audit Akhir (16 temuan, B1-B6), Halaman Portofolio"],
    ], [2.0, 12.0], rata=list("cl"))
    lap.lampiran("B", "Lembar DED Terpilih", lanskap=True)
    lap.paragraf("Sepuluh lembar berikut dipilih dari 64 lembar DED (arsitektur, struktur, MEP dasar) untuk menunjukkan "
                 "isi dan mutu gambar kerja. Set lengkap ada di 7.4/7.5/7.6 Gambar ... DED.pdf; semua lembar digambar di "
                 "CADCraft dengan satu kop A3, dan denah/potongan diturunkan dari model IFC.")
    for rel, jdl in DED:
        if (AKAR / rel).exists():
            lap.gambar(AKAR / rel, jdl, 19.5, sumber=f"{Path(rel).parent.as_posix()}/{Path(rel).name}.")


def main():
    lap = Laporan()
    sampul(lap)
    lap.bagian_awal()
    ringkasan(lap)
    lap.daftar_isi()
    lap.daftar_tabel()
    lap.daftar_gambar()
    for b in (bab1, bab2, bab3, bab4, bab5, bab6, bab7, bab8, bab9, lampiran):
        b(lap)
    lap.simpan(KELUAR)
    ok, pesan = perbarui_word(KELUAR, PDF)
    print("ditulis:", KELUAR, "| field dan PDF lewat Word" if ok else f"| Word gagal: {pesan[:200]}")
    return KELUAR


if __name__ == "__main__":
    main()
