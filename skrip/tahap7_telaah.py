"""Tahap 7 langkah 7.0: telaah dan daftar dokumen DED dan RKS.

DATA SIMULASI untuk studi kasus portofolio. Disusun AI (22 Nov 2026), keputusan usulan AI disetujui atas delegasi
Defsa 22 Nov 2026. Isi: status Tahap 6 (6.9-6.11), daftar lembar DED tiga disiplin, daftar isi RKS dengan status
acuan, keputusan B-2, dan cek murah (elevasi dan grid model STR 6.9 vs konstanta Tahap 4, luas massa vs program 3.4).
Keluaran: `07 DED dan RKS/7.0 Telaah dan Daftar Dokumen.xlsx` + `.md`.
"""
from __future__ import annotations

import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_beban as tb  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "07 DED dan RKS"
XLSX = KELUAR / "7.0 Telaah dan Daftar Dokumen.xlsx"
MD = KELUAR / "7.0 Telaah dan Daftar Dokumen.md"
IFC_STR = AKAR / "model" / "RSTB-STR-T6-LOD300.ifc"
PROGRAM = AKAR / "03 Desain Konsep" / "3.4 Program Ruang Konsultan.xlsx"
STATUS = "draf, disetujui atas delegasi Defsa 22 Nov 2026"
LABEL = "DATA SIMULASI untuk studi kasus portofolio, tidak untuk konstruksi."
HALAMAN = 12.05

# ---------------------------------------------------------------- status Tahap 6
STATUS_T6 = [
    ["6.9", "Model BIM pondasi LOD 300", "Selesai, di-merge (PR #58)",
     "model/RSTB-STR-T6-LOD300.bimc/.ifc: 319 tiang, 83 cap, Cap E gabungan 54 tiang 30,4 × 13,6 m h 2.000 "
     "(dasar +10,05, kepala tiang +10,20); T-107 lolos"],
    ["6.10", "Gambar pondasi GS-28..GS-32, GT-16", "Sedang dikerjakan (cabang fitur/tahap-6-10-gambar)",
     "B-1: tetap milik Tahap 6; bila belum selesai saat 7.5, dikerjakan di 7.5 dengan nomor yang sama"],
    ["6.11", "Ringkasan Tahap 6", "Belum dikerjakan",
     "Angka pondasi untuk RKS dibaca dari 6.3-6.9 (.md bagian keputusan) sampai ringkasan ada"],
]

# ---------------------------------------------------------------- daftar DED
GA = [  # (nomor, judul, skala, sumber view)
    ("GA-01", "Daftar gambar, catatan umum arsitektur, legenda", "-", "-"),
    ("GA-02", "Rencana tapak dan lansekap (parkir, P4, pagar, tebing)", "1:500", "IFC ARS tapak, plan LT1"),
    ("GA-03", "Kunci denah (key plan)", "1:300", "IFC ARS plan"),
    ("GA-04", "Denah LT1 bagian barat (as 1-5)", "1:100", "plan LT1"),
    ("GA-05", "Denah LT1 bagian timur (as 5-10)", "1:100", "plan LT1"),
    ("GA-06", "Denah LT2 bagian barat", "1:100", "plan LT2"),
    ("GA-07", "Denah LT2 bagian timur", "1:100", "plan LT2"),
    ("GA-08", "Denah LT3 bagian barat", "1:100", "plan LT3"),
    ("GA-09", "Denah LT3 bagian timur", "1:100", "plan LT3"),
    ("GA-10", "Denah LT4-LT6 tipikal rawat inap", "1:100", "plan LT4"),
    ("GA-11", "Denah atap, taman atap V1, dek helipad", "1:100", "plan ATAP / LT4"),
    ("GA-12", "Denah plafon (RCP) LT1-LT3", "1:200", "plan ceiling"),
    ("GA-13", "Tampak selatan dan utara", "1:200", "elevation"),
    ("GA-14", "Tampak barat dan timur", "1:200", "elevation"),
    ("GA-15", "Potongan A-A dan B-B", "1:200", "section"),
    ("GA-16", "Detail fasad tipikal (panel, kaca pita, dinding tirai, angkur)", "1:20", "section + detail CAD"),
    ("GA-17", "Detail overstek podium dan mahkota menara", "1:20", "section + detail CAD"),
    ("GA-18", "Detail tangga darurat dan ruang lift", "1:50", "plan + section inti"),
    ("GA-19", "Detail toilet tipikal dan toilet difabel", "1:20", "plan + elevation"),
    ("GA-20", "Detail kanopi drop-off dan ramp IGD beratap", "1:50", "plan + section"),
    ("GA-21", "Daftar pintu dan jendela", "1:50", "schedule door/window"),
    ("GA-22", "Daftar finishing ruang", "-", "schedule space Pset"),
    ("GA-23", "Gedung utilitas dan parkir: denah dan tampak", "1:200", "plan/elevation GU"),
]
GS_LAMA = [
    ("GS-01", "Respons spesifik situs"), ("GS-02", "Zona beban"), ("GS-03", "Catatan umum"),
    ("GS-04", "Denah struktur LT1"), ("GS-05", "Denah struktur LT2"), ("GS-06", "Denah struktur LT3"),
    ("GS-07", "Denah struktur LT4"), ("GS-08", "Denah struktur LT5"), ("GS-09", "Denah struktur LT6"),
    ("GS-10", "Denah struktur atap"), ("GS-11", "Potongan A-A"), ("GS-12", "Potongan B-B"),
    ("GS-13", "Tabel penampang balok"), ("GS-14", "Tabel kolom HBK"), ("GS-15", "Dinding inti, balok kopel"),
    ("GS-16", "Tangga"), ("GS-17", "Transfer tangki"), ("GS-18", "Shaft, lubang pelat"),
    ("GS-19", "Angkur fasad V3"), ("GS-20", "Potongan memanjang balok-kolom"), ("GS-21", "Plot data owner"),
    ("GS-22", "Denah pelat LT1 dan sloof"), ("GS-23", "Potongan pit lift"), ("GS-24", "Detail zona MRI"),
    ("GS-25", "Tabel dan penampang sloof"), ("GS-26", "Detail kolom tangki"), ("GS-27", "Telaah data pondasi"),
]
GS_BARU = [  # (nomor, judul, langkah)
    ("GS-28", "Denah tiang dan pile cap", "6.10 (B-1)"), ("GS-29", "Pile cap inti dan Cap E pelat", "6.10 (B-1)"),
    ("GS-30", "Pile cap tipikal", "6.10 (B-1)"), ("GS-31", "Detail tiang bor dan penulangan", "6.10 (B-1)"),
    ("GS-32", "Tabel tiang dan cap", "6.10 (B-1)"),
    ("GS-33", "Catatan umum struktur rev. Tahap 7 (mutu S2, f'c 35, selimut, A955M)", "7.5 (B-5, B-10)"),
    ("GS-34", "Pelat turun LB-1 CSSD dan balok tepi", "7.5 (B-8)"),
    ("GS-35", "Perkuatan tebing: berm, pelandaian, tiang Ø600, perbaikan tanah U5", "7.5 (B-2)"),
    ("GS-36", "Landasan chiller M-01 (pegas 25 mm) bila dipakai", "7.5 (B-7)"),
]
GM = [
    ("GM-01", "Denah shaft dan ruang alat LT1-LT3", "1:200"), ("GM-02", "Denah shaft dan ruang alat LT4-atap", "1:200"),
    ("GM-03", "Bukaan pelat dan dinding (sleeve) per lantai", "1:200"),
    ("GM-04", "Ruang alat atap: chiller, AHU, tangki opsi B", "1:100"),
    ("GM-05", "Tabel beban alat per lantai", "-"),
    ("GM-06", "Gedung utilitas: genset, trafo, gas medik, TPS B3", "1:100"),
]
GT_BARU = [("GT-16", "Potongan tebing dan serakan lateral", "6.10 (B-1)")]

# ---------------------------------------------------------------- daftar isi RKS
D, B = "dicek ke PDF (rencana 7)", "belum ada di acuan"
RKS = [  # (bab, pekerjaan, acuan, status acuan, butir bawaan)
    ("1", "Syarat umum: lingkup, acuan, mutu, K3/SMKK", "SE 47-2026 Lampiran III (biaya SMKK); PP 16-2021",
     "ada di acuan/publik, pasal dicek saat 7.7", "-"),
    ("2", "Persiapan, urugan + PVD, galian cap, pemantauan gudang", "SNI 8460:2017 (galian, pemantauan)",
     "ada, pasal dicek saat 7.7", "B-11"),
    ("3", "Dewatering galian cap", "SNI 8460:2017; metode 6.8", "ada, pasal dicek saat 7.7",
     "B-4 (batas +8,6; INC-1 ≤ 0,18 mm/hari)"),
    ("4", "Tiang bor Ø800 dan uji tiang", "SNI 8460:2017 9.8.1-9.8.6 (hal. PDF 205-209)", D, "B-3"),
    ("5", "Perkuatan tebing (tiang Ø600, perbaikan tanah U5)", "SNI 8460:2017 (lereng, perbaikan tanah)",
     "ada, pasal dicek saat 7.7", "B-2"),
    ("6", "Beton: material, produksi, perawatan, penerimaan", "SNI 2847:2019 26.4, 26.5, 26.12 (hal. PDF 640-681)",
     D, "B-5 (S2, asam)"),
    ("7", "Baja tulangan", "SNI 2052:2017; SNI 2847:2019 26.6; ASTM A955M", "SNI ada; ASTM A955M " + B, "B-10"),
    ("8", "Bekisting dan inspeksi", "SNI 2847:2019 26.11, 26.13", D, "-"),
    ("9", "Uji material beton (silinder, slump)", "SNI uji tekan silinder, SNI slump", B, "-"),
    ("10", "Kedap air pit dan pelat LT1", "spesifikasi produk", B, "B-10"),
    ("11", "Pekerjaan arsitektur: dinding, lantai, plafon, pintu-jendela", "SNI arsitektur; Permenkes 06-2026 RS",
     "SNI " + B + "; Permenkes ada, pasal dicek saat 7.7", "-"),
    ("12", "Fasad: panel, kaca, dinding tirai, angkur", "SNI 1727:2020 (beban angin); SNI kaca", "SNI 1727 ada; SNI kaca " + B,
     "B-6"),
    ("13", "Proteksi kebakaran dan aksesibilitas", "SNI proteksi kebakaran, aksesibilitas; Permenkes 06-2026",
     "SNI " + B + "; Permenkes ada, pasal dicek saat 7.7", "-"),
    ("14", "MEP dasar: bukaan, sleeve, landasan alat, pegas chiller", "SNI 1726:2019 Pasal 13 (komponen nonstruktural)",
     "ada, pasal dicek saat 7.7", "B-7"),
    ("15", "Toleransi, penerimaan, dokumen akhir", "SNI 2847:2019 26.13; SNI 8460:2017 9.8", D, "-"),
    ("L-1", "Lampiran: program uji tiang", "6.8 Uji Tiang dan Pelaksanaan", "dokumen tahap", "B-3"),
    ("L-2", "Lampiran: rencana dewatering dan pemantauan", "6.8; 2.8", "dokumen tahap", "B-4"),
]

ACUAN_CARI = [
    "SNI uji kuat tekan silinder beton", "SNI uji slump beton", "ASTM A955M (baja tahan karat tulangan)",
    "SNI pekerjaan arsitektur/kaca bangunan", "SNI proteksi kebakaran gedung", "Peraturan aksesibilitas bangunan gedung",
    "Spesifikasi produk kedap air (lembar data pabrik)", "Pedoman getaran alat (rasio frekuensi chiller, B-7)",
    "Pedoman lebar koridor RS (dibandingkan ke Permenkes 06-2026)",
]

KEPUTUSAN = [
    ["K7-1", "B-2 serakan Zhang 4,58 m",
     "Perkuatan tebing di batas lahan: berm + pelandaian + satu baris tiang bor Ø600 (rincian 6.4) dan perbaikan tanah "
     "U5 di jalur tebing sampai di belakang baris tiang y 26,3 m; dimensi akhir di 7.3 bila perlu, gambar GS-35 (7.5), "
     "metode RKS bab 5 (7.7)", "Tiang gedung Ø800 tidak menahan (rasio M 8,4-8,5); geser garis tiang tidak menolong (6.4)"],
    ["K7-2", "B-1 gambar pondasi 6.10 belum ada",
     "Tetap di Tahap 6; bila belum selesai saat 7.5, GS-28..32 dan GT-16 dikerjakan di 7.5 dari model 6.9",
     "Nomor dan isi sudah direncanakan di Tahap 6"],
    ["K7-3", "Pembagian denah arsitektur", "1:100, podium dibagi dua lembar (as 1-5 / 5-10), kunci denah 1:300",
     "Podium 72 m tidak muat A3 pada 1:100"],
    ["K7-4", "Model ARS 7.1", "Model ARS hanya unsur arsitektur (struktur di STR 6.9), level dan grid sama dengan STR; "
     "digabung di 7.2", "Clash 7.2 bermakna, tanpa unsur ganda"],
    ["K7-5", "Tempat P4 76 motor", "Sisi barat tapak x 1-7 m, y 35-63,5 m (2 baris × 38)",
     "P4 lama 94-100 × 44-76 dimakan lajur ambulans 5.2; sisi timur dekat GU sudah dipakai jalan masuk dan lajur"],
]


def cek_murah():
    """Elevasi storey dan grid model STR 6.9 vs tahap4_beban; luas massa vs program 3.4."""
    import ifcopenshell
    f = ifcopenshell.open(str(IFC_STR))
    # satuan panjang IFC BIMCraft: mm
    lv = {s.Name: round(float(s.Elevation or 0.0), 1) for s in f.by_type("IfcBuildingStorey")}
    baris_lv = []
    for nama, z in tb.LEVEL.items():
        zi = lv.get(nama)
        selisih = None if zi is None else round(abs(zi - z * 1000), 1)
        baris_lv.append([nama, z, None if zi is None else zi / 1000, selisih])
    sumbu = [a for a in f.by_type("IfcGridAxis")]
    posisi = []
    for a in sumbu:
        pts = a.AxisCurve.Points
        (x0, y0), (x1, y1) = pts[0].Coordinates[:2], pts[-1].Coordinates[:2]
        posisi.append((a.AxisTag, x0, y0, x1, y1))
    gx = sorted({round(p[1] / 1000, 3) for p in posisi if abs(p[1] - p[3]) < 1})
    gy = sorted({round(p[2] / 1000, 3) for p in posisi if abs(p[2] - p[4]) < 1})
    wb = openpyxl.load_workbook(PROGRAM, data_only=True)
    rekap = {}
    for r in wb["Rekap Lantai"].iter_rows(values_only=True):
        if r and isinstance(r[0], str) and r[0][:2] in ("LT", "GU") and isinstance(r[1], (int, float)):
            rekap[r[0]] = (float(r[1]), float(r[2]), float(r[3]))
    return {"level": baris_lv, "grid_x": gx, "grid_y": gy, "grid_x_t4": list(tb.GRID_X), "grid_y_t4": list(tb.GRID_Y),
            "rekap": rekap, "n_storey": len(lv)}


def idn(v, d=1):
    return f"{v:,.{d}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _cek_grid(cm):
    def beda(a, b):
        return max((abs(x - y) for x, y in zip(a, b)), default=None) if len(a) == len(b) else None
    return beda(cm["grid_x"], cm["grid_x_t4"]), beda(cm["grid_y"], cm["grid_y_t4"])


def buat_excel(cm):
    from format_dokumen import AI, Lembar, set_font_bawaan
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    dx, dy = _cek_grid(cm)

    lb = Lembar(wb.create_sheet("Ringkasan"), 1, "Ringkasan telaah dan daftar dokumen Tahap 7", [6, 92, 22, 34])
    lb.catatan(f"STATUS: {STATUS}. {LABEL}")
    lb.kosong()
    lb.bagian("A", "Daftar lembar")
    lb.tabel(["No", "Isi lembar", "Lembar", "Status"], [
        [1, "Ringkasan dan temuan", "Ringkasan", STATUS], [2, "Status langkah 6.9-6.11", "Status Tahap 6", STATUS],
        [3, f"Daftar lembar DED: {len(GA)} GA, {len(GS_LAMA) + len(GS_BARU)} GS, {len(GM)} GM, 1 GT", "Daftar DED", STATUS],
        [4, f"Daftar isi RKS ({len(RKS)} bab/lampiran) dan status acuan", "Daftar RKS", STATUS],
        [5, "Acuan yang belum ada dan perlu dicari", "Acuan", STATUS],
        [6, "Keputusan Tahap 7 langkah 7.0", "Keputusan", STATUS],
        [7, "Cek murah: elevasi, grid, luas massa vs program", "Cek Murah", STATUS],
    ], rata=list("clll"), beku=False)
    lb.kosong()
    lb.bagian("B", "Temuan utama")
    lb.tabel(["Kode", "Temuan", "Lembar", "Status"], [[t[0], t[1], t[2], STATUS] for t in temuan(cm)],
             rata=list("clll"), fill_kolom={1: AI})

    lb = Lembar(wb.create_sheet("Status Tahap 6"), 2, "Status langkah 6.9-6.11", [8, 34, 28, 90])
    lb.catatan("Sumber: PROGRES.md (22 Nov 2026), folder model/ dan 06 Struktur Bawah dan Basement/.")
    lb.tabel(["Langkah", "Isi", "Status", "Keterangan"], STATUS_T6, rata=list("cllll"))

    lb = Lembar(wb.create_sheet("Daftar DED"), 3, "Daftar lembar DED tiga disiplin", [10, 70, 10, 30, 28])
    lb.catatan("A3, kop KOP_A3, cap STUDI KASUS PORTOFOLIO - TIDAK UNTUK KONSTRUKSI. Gambar dari model IFC; anotasi di "
               "CADCraft (ATURAN GAMBAR CADCRAFT.md).")
    baris = [[n, j, s, v, "7.4 baru"] for n, j, s, v in GA]
    baris += [[n, j, "-", "DWG ada", "ada (Tahap 4-6), dirakit 7.5"] for n, j in GS_LAMA]
    baris += [[n, j, "-", "model 6.9 / 7.3", l] for n, j, l in GS_BARU + GT_BARU]
    baris += [[n, j, s, "IFC federasi 7.2", "7.6 baru"] for n, j, s in GM]
    lb.tabel(["Nomor", "Judul", "Skala", "Sumber", "Status / langkah"], baris, rata=list("clccl"))

    lb = Lembar(wb.create_sheet("Daftar RKS"), 4, "Daftar isi RKS dan status acuan", [6, 52, 52, 40, 26])
    lb.catatan("Status 'dicek ke PDF' = pasal sudah ditemukan saat rencana Tahap 7; 'belum ada di acuan' = ditulis "
               "demikian di RKS, tidak ditebak (aturan proyek). T-115 dicek saat 7.7.")
    lb.tabel(["Bab", "Pekerjaan", "Acuan", "Status acuan", "Bawaan"], [list(r) for r in RKS], rata=list("cllll"),
             fill_kolom={3: AI})

    lb = Lembar(wb.create_sheet("Acuan"), 5, "Acuan yang belum ada di acuan/", [6, 80, 40])
    lb.catatan("Isi acuan/privat: SNI 1726:2019, 1727:2020, 2052:2017, 2847:2019, 8460:2017, RSNI3 2052:2024 draf. "
               "acuan/publik: PP 16-2021, Permen PUPR 22-2018 dan 08-2023, Permenkes 06-2026 RS, SE 47-2026 AHSP.")
    lb.tabel(["No", "Dokumen dicari", "Dipakai di"], [[i + 1, a, "RKS 7.7" if i < 7 else "7.3 / 7.1"]
                                                     for i, a in enumerate(ACUAN_CARI)], rata=list("cll"))

    lb = Lembar(wb.create_sheet("Keputusan"), 6, "Keputusan langkah 7.0", [8, 34, 80, 60])
    lb.catatan(f"Status: {STATUS} (Defsa mendelegasikan keputusan rencana Tahap 7; boleh diubah di awal langkah terkait).")
    lb.tabel(["Kode", "Butir", "Keputusan (usulan AI dipakai)", "Alasan"], KEPUTUSAN, rata=list("clll"),
             fill_kolom={2: AI})

    lb = Lembar(wb.create_sheet("Cek Murah"), 7, "Cek murah elevasi, grid, dan luas", [14, 22, 22, 22, 30])
    lb.catatan(f"Model STR: {IFC_STR.name} ({cm['n_storey']} storey). Toleransi elevasi dan grid ≤ 1 mm (T-110).")
    lb.bagian("A", "Elevasi storey (m)")
    lb.tabel(["Level", "tahap4_beban", "IFC STR 6.9", "Selisih (mm)", "Hasil"],
             [[n, z, zi, s, "lolos" if s is not None and s <= 1 else "periksa"] for n, z, zi, s in cm["level"]],
             rata=list("ccccc"), fmt=[None, "0.00", "0.00", "0.0", None], beku=False)
    lb.kosong()
    lb.bagian("B", "Grid (m)")
    lb.tabel(["Arah", "tahap4_beban", "IFC STR 6.9", "Selisih maks (m)", "Hasil"], [
        ["X (as 1-10)", "; ".join(idn(v, 1) for v in cm["grid_x_t4"]), "; ".join(idn(v, 1) for v in cm["grid_x"]),
         dx, "lolos" if dx is not None and dx <= 0.001 else "periksa"],
        ["Y (as A-G)", "; ".join(idn(v, 1) for v in cm["grid_y_t4"]), "; ".join(idn(v, 1) for v in cm["grid_y"]),
         dy, "lolos" if dy is not None and dy <= 0.001 else "periksa"]], rata=list("cllcc"), beku=False)
    lb.kosong()
    lb.bagian("C", "Luas massa vs program 3.4 (m²)")
    lb.tabel(["Lantai", "Bersih", "Bruto (1,45 × bersih)", "Luas massa", "Bruto / massa"],
             [[k, b, br, m, round(br / m, 3)] for k, (b, br, m) in cm["rekap"].items()], rata=list("ccccc"),
             fmt=[None, "#,##0.0", "#,##0.0", "#,##0.0", "0.000"], beku=False)
    KELUAR.mkdir(exist_ok=True)
    wb.save(XLSX)


def temuan(cm):
    dx, dy = _cek_grid(cm)
    lv_maks = max((s for *_, s in cm["level"] if s is not None), default=None)
    r = cm["rekap"]
    t = [
        ["T7-0.1", "6.9 selesai (319 tiang, 83 cap, Cap E h 2.000); 6.10 gambar pondasi dan 6.11 ringkasan belum: B-1 "
                   "tetap terbuka, angka RKS dari .md 6.3-6.9", "Status Tahap 6"],
        ["T7-0.2", f"Daftar DED: {len(GA)} lembar GA baru, GS-01..27 ada, GS-28..32 + GT-16 milik 6.10, GS-33..36 "
                   f"baru 7.5, {len(GM)} lembar GM", "Daftar DED"],
        ["T7-0.3", f"RKS {len(RKS)} bab/lampiran; {sum(1 for x in RKS if B in x[3])} bab memuat acuan yang belum ada "
                   f"({len(ACUAN_CARI)} dokumen dicari)", "Daftar RKS"],
        ["T7-0.4", f"Elevasi storey STR 6.9 vs tahap4_beban: selisih maks {lv_maks} mm; grid X {dx} m, Y {dy} m",
         "Cek Murah"],
    ]
    if "LT2" in r and "LT4" in r:
        t.append(["T7-0.5", f"Bruto program / massa: LT1 {idn(r['LT1'][1] / r['LT1'][2], 3)}, LT2 "
                            f"{idn(r['LT2'][1] / r['LT2'][2], 3)}, LT3 {idn(r['LT3'][1] / r['LT3'][2], 3)}, LT4-6 "
                            f"{idn(r['LT4'][1] / r['LT4'][2], 3)}; LT2-LT6 berlebih luas (ruang cadangan/sirkulasi) "
                            f"dicatat untuk T-109 di 7.1", "Cek Murah"])
    t.append(["T7-0.6", "B-2 diputuskan: perkuatan tebing Ø600 + perbaikan tanah U5 (GS-35, RKS bab 5)", "Keputusan"])
    return t


def tulis_md(cm):
    dx, dy = _cek_grid(cm)
    L = [f"# 7.0 Telaah dan Daftar Dokumen Tahap 7", "", f"Status: **{STATUS}**. {LABEL}", "",
         "Skrip `skrip/tahap7_telaah.py`, Excel `7.0 Telaah dan Daftar Dokumen.xlsx` (7 lembar).", "",
         "## 1. Status Tahap 6", "", "| Langkah | Isi | Status | Keterangan |", "|---|---|---|---|"]
    L += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in STATUS_T6]
    L += ["", "## 2. Temuan", "", "| Kode | Temuan |", "|---|---|"] + [f"| {a} | {b} |" for a, b, _ in temuan(cm)]
    L += ["", "## 3. Daftar lembar DED", "", f"- Arsitektur GA-01..GA-{len(GA):02d} (7.4):"]
    L += [f"  - {n} {j} ({s})" for n, j, s, _ in GA]
    L += [f"- Struktur: GS-01..GS-27 ada (dirakit 7.5); baru:"] + [f"  - {n} {j} [{l}]" for n, j, l in GS_BARU]
    L += [f"- Geoteknik: GT-16 potongan tebing [6.10]", f"- MEP dasar GM-01..GM-{len(GM):02d} (7.6):"]
    L += [f"  - {n} {j} ({s})" for n, j, s in GM]
    L += ["", "## 4. Daftar isi RKS", "", "| Bab | Pekerjaan | Acuan | Status acuan | Bawaan |", "|---|---|---|---|---|"]
    L += [f"| {' | '.join(r)} |" for r in RKS]
    L += ["", "Acuan yang dicari: " + "; ".join(ACUAN_CARI) + ".", "", "## 5. Keputusan",
          "", "| Kode | Butir | Keputusan | Alasan |", "|---|---|---|---|"] + [f"| {' | '.join(k)} |" for k in KEPUTUSAN]
    L += ["", "## 6. Cek murah", "", "| Level | tahap4_beban (m) | IFC STR 6.9 (m) | Selisih (mm) |", "|---|---|---|---|"]
    L += [f"| {n} | {idn(z, 2)} | {'-' if zi is None else idn(zi, 2)} | {'-' if s is None else idn(s, 1)} |"
          for n, z, zi, s in cm["level"]]
    L += ["", f"Grid: selisih maks X {dx} m, Y {dy} m (toleransi 0,001 m). Peil LT1 +12,85, halaman +12,05.", "",
          "| Lantai | Bersih (m²) | Bruto (m²) | Massa (m²) | Bruto/massa |", "|---|---|---|---|---|"]
    L += [f"| {k} | {idn(b)} | {idn(br)} | {idn(m)} | {idn(br / m, 3)} |" for k, (b, br, m) in cm["rekap"].items()]
    L += ["", "Langkah berikutnya: 7.1 model arsitektur LOD 300 (dikerjakan di sesi yang sama).", ""]
    MD.write_text("\n".join(L), encoding="utf-8")


def jalankan():
    cm = cek_murah()
    buat_excel(cm)
    tulis_md(cm)
    return cm


if __name__ == "__main__":
    c = jalankan()
    print(c["level"], _cek_grid(c), c["n_storey"])
