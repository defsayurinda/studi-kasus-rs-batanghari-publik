"""Langkah 3.5: opsi parkir dan basement, metode galian, dan syarat geoteknik terangka.

Dasar: surat owner butir 4 (120 mobil, 300 motor, 4 ambulans), keputusan rapat no. 3 (bandingkan opsi parkir),
langkah 2.3 (blow-in, SNI 8460:2017 Pasal 10.3.6.7.2: FK ≥ 1,25; profil BH-5, BH-3, CPTu-6), langkah 2.8 (batas muka
air gudang +8,6), langkah 3.2 (KDB, KTB, amplop), 3.3 (Q100 +12,31, halaman +12,05), 3.4 (massa).
Rasio luas parkir per kendaraan berlabel [Asumsi]: pedoman parkir belum ada di acuan/.
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 19 Nov 2026.
"""
from pathlib import Path

from shapely.geometry import box
from shapely.ops import unary_union

import tahap2_air_tanah as at
import tahap3_peil as pl
import tahap3_program as pr
import tahap3_tapak as tp

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "03 Desain Konsep"
BERKAS = KELUAR / "3.5 Opsi Parkir dan Basement.xlsx"
PDF = KELUAR / "3.5 Gambar Parkir dan Basement.pdf"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = "DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026."

KEBUTUHAN = {"mobil": 120, "motor": 300, "ambulans": 4}  # surat owner 034 butir 4
LUAS_PER = {"mobil": 25.0, "motor": 2.5, "ambulans": 40.0}  # m² termasuk jalur [Asumsi; pedoman parkir belum ada]
LUAS_PER_BASEMENT = 30.0  # m²/mobil di basement (kolom, ramp, inti) [Asumsi]
GAMMA_W = 9.81

# Basement 1 lapis di bawah podium: lantai B1 +9,05 (template BIM), pelat 0,60 + lantai kerja 0,10 [Asumsi]
ELEV_B1 = 9.05
ELEV_DASAR_GALIAN = ELEV_B1 - 0.70
H_DESAIN = {"2.3 operasi": 11.20, "3.3 Q100": None}  # Q100 diisi dari langkah 3.3


def tinggi_tekan():
    h = dict(H_DESAIN)
    h["3.3 Q100"] = round(pl.muka_air(100), 2)
    return h


def blowin():
    """FK blow-in di dasar galian basement untuk tiga profil 2.3 dan dua tinggi tekan; dasar galian minimum FK 1,25."""
    hasil = []
    for prof in at.PROFIL:
        for nama, h in tinggi_tekan().items():
            hasil.append({"profil": prof, "tinggi_tekan": nama, "h": h,
                          "fk": at.fk_blowin(prof, ELEV_DASAR_GALIAN, h),
                          "dasar_min": at.elev_dasar_min(prof, h)})
    return hasil


def uplift():
    """Tekanan angkat pada pelat basement saat muka air setinggi Q100 (kPa) dan berat pelat 0,6 m (kPa)."""
    h = tinggi_tekan()["3.3 Q100"]
    u = GAMMA_W * (h - ELEV_DASAR_GALIAN)
    return {"u": u, "berat_pelat": 24.0 * 0.60, "selisih": u - 24.0 * 0.60}


# ------------------------------------------------------------------ parkir permukaan dan gedung parkir
GEDUNG_UP = {"x": (100.0, 134.0), "y": (44.0, 76.0), "lantai": 4}  # opsi C: utilitas LT1 + parkir LT2-LT4
ZONA_PARKIR = {  # (x0, x1, y0, y1, jenis) permukaan, di luar massa, sempadan, rumija, kolam, jalur ambulans
    "P1 utara barat": (1.0, 44.0, 77.0, 88.0, "mobil"),
    "P2 utara tengah": (64.0, 88.0, 77.0, 88.0, "mobil"),
    "P3 barat (motor)": (1.0, 11.0, 27.0, 75.0, "motor"),
    "P4 timur (motor dan ambulans)": (94.0, 100.0, 44.0, 76.0, "motor"),
    "P5 selatan (motor)": (12.0, 44.0, 19.0, 26.0, "motor"),
}


def kapasitas_permukaan():
    hasil = []
    for nama, (x0, x1, y0, y1, jenis) in ZONA_PARKIR.items():
        luas = (x1 - x0) * (y1 - y0)
        hasil.append({"zona": nama, "luas": luas, "jenis": jenis, "jumlah": int(luas // LUAS_PER[jenis])})
    return hasil


def mobil_gedung_parkir():
    """Mobil di gedung utilitas + parkir: luas 4 lantai dikurangi luas bruto program utilitas (3.4), 30 m²/mobil."""
    up = GEDUNG_UP
    luas = (up["x"][1] - up["x"][0]) * (up["y"][1] - up["y"][0])
    return int((up["lantai"] * luas - pr.rekap_lantai()["GU"]["bruto"]) // LUAS_PER_BASEMENT)


def opsi():
    pod = pr.poligon("PODIUM").area
    perm = kapasitas_permukaan()
    mobil_perm = sum(z["jumlah"] for z in perm if z["jenis"] == "mobil")
    motor_perm = sum(z["jumlah"] for z in perm if z["jenis"] == "motor")
    up = GEDUNG_UP
    luas_up = (up["x"][1] - up["x"][0]) * (up["y"][1] - up["y"][0])
    mobil_up = mobil_gedung_parkir()
    fk = blowin()
    fk_min = min(r["fk"] for r in fk)
    fk_maks = max(r["fk"] for r in fk)
    gali = pod * (9.6 - ELEV_DASAR_GALIAN)  # muka tanah rata-rata podium ±9,6 (TOR Lampiran C)
    keliling = 2 * (72 + 48)
    return [
        {"opsi": "A", "nama": "Basement penuh 1 lapis di bawah podium", "mobil": int(pod // LUAS_PER_BASEMENT)
         + mobil_perm, "motor": motor_perm, "fk": (fk_min, fk_maks), "galian": gali, "dinding": keliling,
         "catatan": "FK blow-in < 1,25: sumur pelepas permanen atau dinding potong menembus U5 (±22 m); uplift; "
                    "ramp masuk harus di atas +12,85 (banjir); dewatering dekat gudang"},
        {"opsi": "B", "nama": "Basement parsial (setengah podium barat)", "mobil": int(pod / 2 // LUAS_PER_BASEMENT)
         + mobil_perm, "motor": motor_perm, "fk": (fk_min, fk_maks), "galian": gali / 2, "dinding": 2 * (36 + 48),
         "catatan": "Masalah geoteknik sama dengan A; kapasitas mobil kurang"},
        {"opsi": "C", "nama": "Tanpa basement: gedung utilitas + parkir 4 lantai, motor di permukaan",
         "mobil": mobil_up + mobil_perm, "motor": motor_perm, "fk": None, "galian": 0.0, "dinding": 0.0,
         "catatan": f"LT1 utilitas +12,85 (sisa utilitas di LT2), parkir LT2-LT4 {mobil_up} mobil; tanpa galian dalam; "
                    "tapak gedung bertambah, tetap ≤ KDB"},
        {"opsi": "D", "nama": "Parkir permukaan saja", "mobil": mobil_perm, "motor": motor_perm, "fk": None,
         "galian": 0.0, "dinding": 0.0, "catatan": "Kapasitas mobil jauh di bawah kebutuhan 120"},
    ]


def cek_opsi_c():
    """Tapak dan luas lantai opsi C terhadap PKKPR (gedung utilitas 32 × 24 diganti gedung utilitas + parkir)."""
    up = GEDUNG_UP
    luas_up = (up["x"][1] - up["x"][0]) * (up["y"][1] - up["y"][0])
    t = tp.ringkasan()
    tapak = pr.poligon("PODIUM").area + luas_up
    lantai = 3 * pr.poligon("PODIUM").area + 3 * pr.poligon("MENARA").area + up["lantai"] * luas_up
    g = box(up["x"][0], up["y"][0], up["x"][1], up["y"][1])
    return {"tapak": tapak, "kdb": t["kdb_maks"], "lantai": lantai, "klb": t["klb_maks"],
            "dalam_amplop": tp.amplop(4).buffer(1e-6).contains(g), "jarak_gudang": tp.GUDANG[0] - up["x"][1],
            "luas_up": luas_up}



def cek_kdh():
    """Ruang hijau yang tersisa (di luar sempadan) setelah tapak opsi C, parkir, jalan, kolam, IPAL ≥ KDH 20 %."""
    import tahap3_zonasi as zn

    t = tp.ringkasan()
    up = GEDUNG_UP
    tapak = cek_opsi_c()["tapak"]
    parkir = sum(z["luas"] for z in kapasitas_permukaan())
    jalan = 6 * 58 + 16 * 6 + 3 * 25  # jalur ambulans x 88-94, drop-off lobi, jalan inspeksi [Asumsi lebar]
    kolam = (zn.RETENSI[1] - zn.RETENSI[0]) * (zn.RETENSI[3] - zn.RETENSI[2])
    ipal = (zn.IPAL[1] - zn.IPAL[0]) * (zn.IPAL[3] - zn.IPAL[2])
    hijau = t["lahan_perencanaan"] - tapak - parkir - jalan - kolam - ipal
    return {"hijau": hijau, "kdh_min": t["kdh_min"], "parkir": parkir, "jalan": jalan, "kolam": kolam, "ipal": ipal,
            "luas_up": (up["x"][1] - up["x"][0]) * (up["y"][1] - up["y"][0])}


def fmt(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


# ------------------------------------------------------------------ Excel
def buat_excel(keluar=BERKAS):
    import openpyxl

    from format_dokumen import AI, Lembar, set_font_bawaan

    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    bl, up_, op = blowin(), uplift(), opsi()
    c, k = cek_opsi_c(), cek_kdh()

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk opsi parkir dan basement (langkah 3.5)", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        "Kebutuhan dari surat owner 034 butir 4 (120 mobil, 300 motor, 4 ambulans); keputusan rapat no. 3: bandingkan "
        "basement penuh, parsial, parkir permukaan, gedung parkir.",
        "Blow-in: SNI 8460:2017 Pasal 10.3.6.7.2 hal. 211, FK ≥ 1,25 (rumus dan profil langkah 2.3). Tinggi tekan "
        "akuifer U5: +11,20 (desain operasi 2.3) dan +12,31 (Q100 sungai, 3.3).",
        f"Basement 1 lapis: lantai B1 +{fmt(ELEV_B1)}, dasar galian +{fmt(ELEV_DASAR_GALIAN)} (pelat 0,60 + lantai kerja "
        "0,10 [Asumsi]).",
        "Luas per kendaraan (mobil 25 m² permukaan, 30 m² basement/gedung parkir, motor 2,5 m², ambulans 40 m²) "
        "berlabel [Asumsi]: pedoman parkir belum ada di acuan/; analisis dampak lalu lintas wajib sebelum PBG (PKKPR 5).",
        "Gambar: GK-05 '3.5 Gambar Parkir dan Basement.pdf'.",
    ])], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Blow-in"), 2, "Keamanan dasar galian basement terhadap blow-in",
                [24, 18, 14, 14, 18, 30])
    lb.catatan(LABEL + " FK = σv tanah kedap di atas pasir U5 / tekanan air di puncak U5.")
    lb.tabel(["Profil (2.3)", "Tinggi tekan", "h (m lokal)", "FK di dasar galian", "Dasar galian min untuk FK 1,25",
              "Penilaian"],
             [[r["profil"], r["tinggi_tekan"], r["h"], round(r["fk"], 2),
               "tidak ada (artesis)" if r["dasar_min"] is None else round(r["dasar_min"], 2),
               "TIDAK AMAN" if r["fk"] < 1.25 else "aman"] for r in bl],
             rata=list("lcccccl"[:6]), fmt=[None, None, "0.00", "0.00", None, None], fill_kolom={3: AI, 4: AI, 5: AI})
    lb.kosong()
    lb.bagian("B", "Uplift pelat basement saat Q100")
    lb.tabel(["Butir", "Nilai", "Satuan", "Keterangan"], [
        ["Tekanan air di bawah pelat", round(up_["u"], 1), "kPa", "γw (Q100 - dasar galian)"],
        ["Berat pelat 0,60 m", round(up_["berat_pelat"], 1), "kPa", "24 kN/m³"],
        ["Kekurangan penahan uplift", round(up_["selisih"], 1), "kPa", "perlu tiang tarik atau pelat lebih tebal"],
    ], rata=list("lccl"), fmt=[None, "0.0", None, None], fill_kolom={1: AI}, beku=False)

    lb = Lembar(wb.create_sheet("Parkir"), 3, "Kebutuhan dan kapasitas parkir", [26, 14, 12, 14, 30])
    lb.catatan(LABEL)
    lb.tabel(["Zona / kebutuhan", "Luas (m²)", "Jenis", "Kapasitas", "Keterangan"],
             [[z["zona"], z["luas"], z["jenis"], z["jumlah"], f"{LUAS_PER[z['jenis']]:.1f} m² per kendaraan [Asumsi]"]
              for z in kapasitas_permukaan()]
             + [["Gedung parkir LT2-LT4 (dikurangi sisa utilitas)", 4 * c["luas_up"] - pr.rekap_lantai()["GU"]["bruto"],
                 "mobil", mobil_gedung_parkir(), f"{LUAS_PER_BASEMENT:.0f} m² per mobil [Asumsi]"],
                ["Kebutuhan (surat owner butir 4)", None, "mobil / motor / ambulans",
                 None, f"{KEBUTUHAN['mobil']} / {KEBUTUHAN['motor']} / {KEBUTUHAN['ambulans']}"]],
             rata=list("lccc") + ["l"], fmt=[None, "#,##0", None, "0", None], fill_kolom={3: AI})

    lb = Lembar(wb.create_sheet("Opsi"), 4, "Perbandingan opsi parkir dan basement", [6, 40, 10, 10, 16, 14, 12, 60])
    lb.catatan(LABEL + " Biaya per opsi dihitung di langkah 3.8.")
    lb.tabel(["Opsi", "Uraian", "Mobil", "Motor", "FK blow-in", "Galian (m³)", "Dinding (m)", "Catatan"],
             [[o["opsi"], o["nama"], o["mobil"], o["motor"],
               "-" if o["fk"] is None else f"{fmt(o['fk'][0])}-{fmt(o['fk'][1])}", round(o["galian"]),
               o["dinding"], o["catatan"]] for o in op],
             rata=list("clcccccl"), fmt=[None, None, "0", "0", None, "#,##0", "#,##0", None], fill=AI)
    lb.kosong()
    lb.bagian("B", "Usulan dan syarat")
    lb.tabel(["No", "Butir", "", "", "", "", "", "Nilai / syarat"], [
        [1, "Usulan", "", "", "", "", "", "Opsi C: tanpa basement; gedung utilitas + parkir 4 lantai (34 × 32 m); disetujui Defsa 19 Nov 2026"],
        [2, "Tapak opsi C ≤ KDB", "", "", "", "", "", f"{fmt(c['tapak'], 0)} ≤ {fmt(c['kdb'], 0)} m²"],
        [3, "Luas lantai ≤ KLB", "", "", "", "", "", f"{fmt(c['lantai'], 0)} ≤ {fmt(c['klb'], 0)} m²"],
        [4, "Ruang hijau ≥ KDH", "", "", "", "", "", f"{fmt(k['hijau'], 0)} ≥ {fmt(k['kdh_min'], 0)} m²"],
        [5, "Jarak gedung parkir ke gudang", "", "", "", "", "", f"{fmt(c['jarak_gudang'], 1)} m (≥ 4 m PKKPR ≤ 4 lantai)"],
        [6, "Galian tangki air tanam dan IPAL", "", "", "", "", "", "dangkal (±3 m), di musim kering, dinding turap; "
         "muka air di sisi gudang ≥ +8,6 (2.8)"],
        [7, "Bila owner tetap meminta basement", "", "", "", "", "", "sumur pelepas tekanan permanen ke U5 atau dinding "
         "potong ke U6 (±22 m), tiang tarik, ramp di atas +12,85; galian hanya Jun-Okt"],
    ], rata=list("cl") + ["l"] * 6, fill_kolom={7: AI}, beku=False)
    wb.save(keluar)
    return keluar


# ------------------------------------------------------------------ gambar GK-05
POT_Y0 = -150.0  # letak potongan basement di model space (1:250, tanpa pembesaran)


def gambar_cad(status=None):
    import tahap3_zonasi as zn
    from cad_lembar import STATUS_SETUJU, Gambar

    def k(x0, x1, y0, y1):
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    c = cek_opsi_c()
    dwg = KELUAR / "Gambar" / "DWG" / "GK-05 Parkir dan Basement.dwg"
    png = KELUAR / "Gambar" / "GK-05 Parkir dan Basement.png"
    with Gambar(750) as g:
        # denah tapak parkir (opsi C)
        g.layer("C-SEMPADAN", 3, 0.25)
        g.arsir(list(tp.ruang_sempadan().exterior.coords)[:-1], "C-SEMPADAN", pola="DOTS", skala_pola=0.6)
        g.legenda_tambah("arsir", "Ruang sempadan sungai", pola="DOTS", skala_pola=0.6)
        pd, mn = pr.MASSA["PODIUM"], pr.MASSA["MENARA"]
        g.layer("A-MASSA", 7, 0.7)
        g.pline(k(*pd["x"], *pd["y"]), "A-MASSA", tutup=True)
        g.pline(k(*GEDUNG_UP["x"], *GEDUNG_UP["y"]), "A-MASSA", tutup=True)
        g.legenda_tambah("garis", "Massa bangunan (podium, gedung utilitas + parkir)", tebal=0.7)
        g.layer("A-MASSA-MENARA", 7, 0.35, "DASHED")
        g.pline(k(*mn["x"], *mn["y"]), "A-MASSA-MENARA", tutup=True)
        g.layer("A-TEKS", 7, 0.25)
        g.teks((48, 53), "PODIUM (TANPA BASEMENT)", "A-TEKS", 2.4, j="MC", tebal=True)
        ux = sum(GEDUNG_UP["x"]) / 2
        g.teks((ux, 62), "GEDUNG UTILITAS", "A-TEKS", 2.0, j="MC", tebal=True)
        g.teks((ux, 59), "DAN PARKIR 4 LANTAI", "A-TEKS", 2.0, j="MC", tebal=True)
        g.teks((ux, 55.5), f"LT1 UTILITAS; LT2-LT4 ± {mobil_gedung_parkir()} MOBIL", "A-TEKS", 1.5,
               j="MC")
        g.layer("C-PARKIR", 7, 0.25)
        for z in kapasitas_permukaan():
            x0, x1, y0, y1, jenis = ZONA_PARKIR[z["zona"]]
            label = f"{z['zona'].split()[0]} {z['jumlah']} {'MOBIL' if jenis == 'mobil' else 'MOTOR'}"
            tegak = (x1 - x0) < (y1 - y0)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            w, h = len(label) * 0.95 * 1.6 * 0.75 + 1.0, 1.6 * 0.75 + 1.0
            lub = (k(cx - h / 2, cx + h / 2, cy - w / 2, cy + w / 2) if tegak else k(cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2))
            g.arsir_lubang(k(x0, x1, y0, y1), [lub], "C-PARKIR", pola="ANSI37" if jenis == "mobil" else "ANSI31",
                           skala_pola=1.0)
            g.pline(k(x0, x1, y0, y1), "C-PARKIR", tutup=True)
            g.teks((cx, cy), label, "C-PARKIR", 1.6, j="MC", rot=90 if tegak else 0)
        g.legenda_tambah("arsir", "Parkir mobil permukaan", pola="ANSI37", skala_pola=1.0)
        g.legenda_tambah("arsir", "Parkir motor permukaan", pola="ANSI31", skala_pola=1.0)
        g.layer("C-KOLAM", 7, 0.35)
        g.pline(k(*zn.RETENSI), "C-KOLAM", tutup=True)
        g.teks(((zn.RETENSI[0] + zn.RETENSI[1]) / 2, (zn.RETENSI[2] + zn.RETENSI[3]) / 2), "KOLAM RETENSI",
               "C-KOLAM", 1.5, j="MC")
        g.layer("C-PERSIL", 7, 0.7, "PHANTOM")
        g.pline(k(0, 140, 0, 90), "C-PERSIL", tutup=True)
        g.teks((70, 96.5), "JALAN KOLEKTOR", "C-TEKS", 2.2, j="MC", tebal=True)
        # potongan basement opsi A (skala 1:300 di viewport kedua)
        prof = at.PROFIL["Tengah tapak (BH-5)"]
        elev0, lap = prof
        y = POT_Y0
        x0, x1 = 0.0, 60.0
        batas = [elev0] + [elev0 - b for b, _ in lap]
        pola_unit = {"U1": ("ANSI37", 0.25), "U2": ("ANSI33", 0.25), "U4": ("ANSI32", 0.4)}
        gx0, gx1 = 6.0, 54.0
        for (b, u), atas, bawah in zip(lap, batas[:-1], batas[1:]):
            g.layer(f"G-{u}", 7, 0.18)
            lub = []
            if bawah < ELEV_DASAR_GALIAN < atas or bawah >= ELEV_DASAR_GALIAN:  # rongga galian tanpa arsir
                lub = [k(gx0, gx1, y + max(bawah, ELEV_DASAR_GALIAN), y + atas)]
                if bawah >= ELEV_DASAR_GALIAN:
                    g.arsir_lubang(k(x0, gx0, y + bawah, y + atas), [], f"G-{u}", pola=pola_unit[u][0],
                                   skala_pola=pola_unit[u][1])
                    g.arsir_lubang(k(gx1, x1, y + bawah, y + atas), [], f"G-{u}", pola=pola_unit[u][0],
                                   skala_pola=pola_unit[u][1])
                    lub = None
            if lub is not None:
                g.arsir_lubang(k(x0, x1, y + bawah, y + atas), lub, f"G-{u}", pola=pola_unit[u][0],
                               skala_pola=pola_unit[u][1])
            g.teks((x1 + 1.0, y + (atas + bawah) / 2 - 0.2), f"{u}", f"G-{u}", 0.640)
        g.layer("G-U5", 7, 0.18)
        g.arsir(k(x0, x1, y + batas[-1] - 4.0, y + batas[-1]), "G-U5", pola="DOTS", skala_pola=0.25)
        g.teks((x1 + 1.0, y + batas[-1] - 2.3), "U5 PASIR (AKUIFER)", "G-U5", 0.640)
        g.layer("G-GALIAN", 7, 0.5)
        g.pline([(gx0, y + 12.05), (gx0, y + ELEV_DASAR_GALIAN), (gx1, y + ELEV_DASAR_GALIAN), (gx1, y + 12.05)],
                "G-GALIAN", tebal=0.6)
        g.teks(((gx0 + gx1) / 2, y + ELEV_DASAR_GALIAN + 0.45),
               f"DASAR GALIAN BASEMENT +{ELEV_DASAR_GALIAN:.2f}".replace(".", ","), "G-GALIAN", 0.6, j="MC", tebal=True)
        g.layer("G-AIR", 7, 0.25, "HIDDEN")
        for nama, h in tinggi_tekan().items():
            g.pline([(x0 - 2, y + h), (x1 + 2, y + h)], "G-AIR")
            g.teks((x1 + 3, y + h - 0.15), f"TINGGI TEKAN U5 +{h:.2f} ({nama.upper()})".replace(".", ","), "G-AIR", 0.600)
        fk = blowin()
        fk_txt = f"FK BLOW-IN {min(r['fk'] for r in fk):.2f}-{max(r['fk'] for r in fk):.2f} < 1,25".replace(".", ",")
        g.teks((x1 + 3, y + 5.2), fk_txt, "G-GALIAN", 0.800, tebal=True)
        g.teks((x1 + 3, y + 4.4), "(SNI 8460:2017 PASAL 10.3.6.7.2)", "G-GALIAN", 0.600)
        g.layer("G-SKALA", 7, 0.18)
        for el in range(-2, 14, 2):
            g.pline([(x0 - 6, y + el), (x0 - 5.4, y + el)], "G-SKALA")
            g.teks((x0 - 6.4, y + el), f"+{el},00" if el >= 0 else f"{el},00", "G-SKALA", 0.520, j="MR")
        g.pline([(x0 - 5.4, y - 2), (x0 - 5.4, y + 14)], "G-SKALA")
        g.lembar("GK-05", "Parkir dan basement", "1:750", pusat=(70, 44), vp=((24, 150), (331, 283)),
                 subjudul="Langkah 3.5: opsi C tanpa basement; potongan menunjukkan alasan geoteknik (langkah 2.3, 3.3)",
                 status=status or STATUS_SETUJU,
                 catatan=[
                     f"Parkir: {opsi()[2]['mobil']} mobil (gedung parkir + P1, P2), {opsi()[2]['motor']} motor, "
                     "4 ambulans di drop-off IGD.",
                     f"Tapak {fmt(c['tapak'], 0)} m² ≤ KDB; hijau ≥ KDH (lembar Opsi).",
                     "Basement ditolak: FK blow-in < 1,25 dan uplift Q100 38,8 kPa.",
                     "Luas per kendaraan [Asumsi]; andalalin sebelum PBG.",
                 ])
        g.viewport_tambahan((24, 52), (331, 140), pusat=(36.5, POT_Y0 + 5.0), skala=300,
                            judul="Potongan basement opsi A (BH-5)", teks_skala="SKALA 1:300")
        g.skala_grafis(205, 22, 50)
        g.panah_utara(318, 262, 10)
        g.simpan(dwg, PDF, png)
    return dwg


def buat():
    buat_excel()
    gambar_cad()
    return BERKAS, PDF

if __name__ == "__main__":
    for r in blowin():
        print(r)
    print(uplift())
    for z in kapasitas_permukaan():
        print(z)
    for o in opsi():
        print(o["opsi"], o["nama"], "mobil", o["mobil"], "motor", o["motor"], "galian", round(o["galian"]))
    print(cek_opsi_c())
