"""Langkah 5.8: gambar struktur tengah (GS-22 s.d. GS-26) di CADCraft, ber-kop KOP_A3, status DRAF.

GS-22 denah pelat LT1 dan sloof: geometri dari model BIMCraft `RSTB-STR-T5-LOD300` (5.7), tampak LT1 diekspor DXF lalu
dibersihkan (tanpa teks BIM, tanpa poche); anotasi asli CADCraft. GS-23 s.d. GS-26: detail digambar di CADCraft dari
hasil desain 5.3-5.6a (angka dari skrip desain dan md; tulangan tidak dimodelkan di LOD 300). Potongan beton hanya
arsir ANSI31 tipis, tanpa poche hitam. DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa
(21 Nov 2026); draf, menunggu persetujuan. Kunci jawaban tidak dibuka.
Jalankan: .venv\\Scripts\\python.exe skrip\\tahap5_gambar_ded.py [--ekspor] [GS-22 GS-24 ...]
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from shapely.geometry import box

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_gambar_ded as t4g  # noqa: E402
import tahap5_bim as t5  # noqa: E402
import tahap5_penerusan as pe  # noqa: E402
import tahap5_pit_lift as pit  # noqa: E402
import tahap5_sloof as sl  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "05 Struktur Tengah"
GAMBAR = KELUAR / "Gambar"
DWG = GAMBAR / "DWG"
BIM = GAMBAR / "BIM"
PLOT = GAMBAR / "_plot"
PDF = KELUAR / "5.8 Gambar Struktur Tengah.pdf"
TANGGAL = "NOVEMBER 2026"
STATUS = "DISETUJUI 21 NOV 2026"
H = 1.6                      # mm kertas, teks kecil
GRID_X, GRID_Y, NAMA_X, NAMA_Y = t4g.tb.GRID_X, t4g.tb.GRID_Y, t4g.NAMA_X, t4g.NAMA_Y
idn = t5.idn

# angka dari md (diuji terhadap md di tests/test_tahap5_gambar_ded.py)
PIT_TUL = {  # 5.5 bagian C: (atas, bawah) pelat; Opsi A, tanpa angkur
    "L-1..4": ("D13-175", "D13-100"), "L-5..6": ("D13-175", "D13-175"), "L-7": ("D13-175", "D13-100")}
DINDING_TUL = ("D13-250 luar", "D13-275 dalam", "D13-250 tiap muka")
AIR = (("Q100", 12.31), ("Q50", 11.85), ("TEKAN", 11.20))   # 5.5 bagian A
MRI = {"x": (79.5, 81.5), "y": (56.0, 58.0), "batang": 3.16, "lewat": 0.58, "jarak": 0.2, "n": 11, "massa": "144,60"}
STEK = {"ldh": 375, "ld": 919, "ldc": 397, "kait": 1093, "lurus": 1125}   # 5.6a, 20 D22 ke cap 1.200
KOLOM_TB = {"LT2": {"rho": "1,19", "pm": "0,897", "ve": "666"}, "LT3": {"rho": "3,30", "pm": "0,991", "ve": "949"}}


def judul(g, at, s, h=2.0):
    g.teks(at, s, "S-TEKS", h, j="BC", tebal=True)


def rect(g, x0, z0, x1, z1, layer, pola=None, sk=1.0):
    pts = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    if pola:
        g.arsir(pts, layer, pola, sk)
    else:
        g.pline(pts, layer, tutup=True)


def simpan(g, dwg):
    PLOT.mkdir(parents=True, exist_ok=True)
    g.simpan(dwg, PLOT / f"{dwg.stem}.pdf", GAMBAR / f"{dwg.stem}.png")


def lembar(g, no, jd, skala, pusat, sub, catatan, kop, utara=False):
    g.lembar(no, jd, f"1:{skala}", pusat=pusat, status=STATUS, tanggal=TANGGAL, subjudul=sub, catatan=catatan,
             judul_kop=kop)
    g.skala_grafis(205, 22, 2 if skala <= 25 else (5 if skala <= 50 else 20), bagi=4 if skala <= 25 or skala > 50 else 5)
    if utara:   # panah utara hanya di lembar denah
        g.panah_utara(318, 262, 10)


# ------------------------------------------------------------------ GS-22 denah pelat LT1 dan sloof
def dxf_lt1():
    return BIM / "RSTB-STR-T5 Denah LT1.dxf"


def ekspor_bim():
    from bimcraft import Sesi
    BIM.mkdir(parents=True, exist_ok=True)
    with Sesi(t5.BIMC) as b:
        b.cmd("export", {"format": "dxf", "view": "LT1", "path": str(dxf_lt1()), "overwrite": True})
    t4g.bersihkan_dxf(dxf_lt1(), tanpa_besi=True)


def gs22():
    from cad_lembar import Gambar
    if not dxf_lt1().exists():
        ekspor_bim()
    skala = 300
    x0, x1, y0, y1 = GRID_X[0], GRID_X[-1], GRID_Y[0], GRID_Y[-1]
    seg, _ = t5.sloof_segmen()
    pits = {k: t5.pit_geom(k, p) for k, p in pit.data_lift().items()}
    pit_zona = [box(*pits[k][0].bounds).buffer(0.3) for k in pits]
    with Gambar(skala) as g:
        t4g.impor(g, dxf_lt1())
        g.legenda_tambah("garis", "Pelat LT1, sloof, kolom, inti (model BIM 5.7)", tebal=0.35)
        g.legenda_tambah("garis", "As grid", garis="CENTER", tebal=0.18)
        g.legenda_tambah("arsir", "Zona baja tahan karat MRI (GS-24)", pola="ANSI37", skala_pola=0.5)
        g.legenda_tambah("garis", "Pit lift L-1..4, L-5..6, L-7 (GS-23)", tebal=0.5)
        g.legenda_tambah("garis", "Garis potong pit P1-P3 (GS-23)", tebal=0.5)
        for i, x in enumerate(GRID_X):
            g.as_grid(NAMA_X[i], (x, y1 + 1.5), (x, y1 + 5.0), r_kertas=3.0, dua_ujung=False)
            g.as_grid(NAMA_X[i], (x, y0 - 1.5), (x, y0 - 5.0), r_kertas=3.0, dua_ujung=False)
        for j, y in enumerate(GRID_Y):
            g.as_grid(NAMA_Y[j], (x0 - 1.5, y), (x0 - 5.0, y), r_kertas=3.0, dua_ujung=False)
        for a, b in zip(GRID_X[:-1], GRID_X[1:]):
            g.ukur((a, y1 + 8.5), (b, y1 + 8.5), ((a + b) / 2, y1 + 8.5))
        g.ukur((x0, y1 + 11.5), (x1, y1 + 11.5), ((x0 + x1) / 2, y1 + 11.5))
        for a, b in zip(GRID_Y[:-1], GRID_Y[1:]):
            g.ukur((x0 - 8.5, a), (x0 - 8.5, b), (x0 - 8.5, (a + b) / 2), rot=90)
        g.ukur((x0 - 11.5, y0), (x0 - 11.5, y1), (x0 - 11.5, (y0 + y1) / 2), rot=90)
        # label sloof di tengah segmen (di luar pit)
        g.layer("S-TEKS-SLOOF", 7, 0.18)
        for (ax, ay), (bx, by), tipe in seg:
            xm, ym = (ax + bx) / 2, (ay + by) / 2
            if abs(ay - by) < 1e-6:
                p, rot = (xm, ay + 0.55), 0
            else:
                p, rot = (ax - 0.55, ym), 90
            if any(z.contains(t4g.Point(*p)) for z in pit_zona):
                continue
            g.teks(p, tipe, "S-TEKS-SLOOF", 1.6, j="BC", rot=rot)
        # pit, zona MRI, kolom tangki
        g.layer("S-PIT", 7, 0.5)
        for k, (luar, dalam) in pits.items():
            b = luar.bounds
            g.pline([(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])], "S-PIT", tutup=True)
            c = luar.centroid
            if k == "L-1..4":   # pusat pit penuh simbol bukaan BIM: label dengan penunjuk
                g.tunjuk((b[2], 38.0), (60.8, 37.2), "PIT " + k, layer="S-PIT")
            else:
                g.teks((c.x, c.y), "PIT " + k, "S-PIT", 1.6, j="MC", tebal=True)
        mx, my = MRI["x"], MRI["y"]
        g.arsir([(mx[0], my[0]), (mx[1], my[0]), (mx[1], my[1]), (mx[0], my[1])], "S-MRI", "ANSI37", 0.5)
        g.tunjuk((81.5, 58.0), (84.6, 62.2), "MRI GS-24", layer="S-MRI")
        g.layer("S-TEKS-KOLOM", 7, 0.18)
        for x, y in t5.tn.KOLOM:
            g.teks((x + 0.55, y + 0.55), "K-TB", "S-TEKS-KOLOM", 1.6, j="L")
        g.teks((12.7, 33.0), "PELAT LT1 t 250", "S-TEKS", 1.5, j="L", tebal=True)
        g.teks((12.7, 32.2), "fc' 35 MPa", "S-TEKS", 1.5, j="L", tebal=True)
        # garis potong pit (ke GS-23)
        g.layer("S-POTONG", 7, 0.5)
        for nm, t1, t2, l1, l2 in (
                ("P1", ((48.4, 39.0), (50.0, 39.0)), ((58.0, 39.0), (59.0, 39.0)), ((48.4, 40.3), "BL"), ((58.9, 40.3), "BR")),
                ("P2", ((50.9, 44.75), (52.5, 44.75)), ((58.5, 44.75), (60.1, 44.75)), ((50.9, 44.2), "TL"), ((60.1, 44.2), "TR")),
                ("P3", ((39.4, 28.6), (39.4, 29.4)), ((39.4, 34.0), (39.4, 34.8)), ((39.9, 28.6), "ML"), ((39.9, 34.8), "ML"))):
            g.pline(list(t1), "S-POTONG")
            g.pline(list(t2), "S-POTONG")
            for pt, j in (l1, l2):
                g.teks(pt, nm, "S-POTONG", 1.8, j=j, tebal=True)
        g.titik_tinggi((14.0, 29.0), "+12,85 LT1", "S-ELEVASI")
        catatan = [
            "Geometri dari model BIM RSTB-STR-T5-LOD300 (5.7), tampak LT1 diekspor DXF; anotasi CADCraft.",
            "Pelat LT1 t 250 fc' 35 (5.3 Desain Pelat LT1.md); sloof 122 segmen: SL-1 400 × 900 (dalam), SL-2 400 × 800 "
            "(tepi), SL-3 400 × 800 (as 10, dekat MRI) (5.4 Desain Sloof.md); SL-1 as 6 di dalam inti lift dihapus.",
            "Pit L-1..4, L-5..6, L-7 dan potongan P1-P3: GS-23 (5.5). Zona baja tahan karat MRI x 79,5-81,5 / y 56-58: GS-24 "
            "(5.2, 5.3).",
            "Penampang dan tulangan sloof: GS-25. Kolom tangki K-TB 800 dan stek ke pile cap: GS-26 (5.6a).",
            "Ukuran dalam meter; elevasi terhadap BM-1 = +10,000; LT1 +12,85."]
        xc, yc = (x0 - 12 + x1 + 7) / 2, (y0 - 7 + y1 + 12.5) / 2
        lembar(g, "GS-22", "Denah pelat LT1 dan sloof", skala, (xc, yc),
               "Langkah 5.8: denah dari model BIMCraft LOD 300 (5.7); kode sloof dari desain 5.4", catatan,
               "DENAH LT1 DAN SLOOF", utara=True)
        simpan(g, DWG / "GS-22 Denah Pelat LT1 dan Sloof.dwg")
    return DWG / "GS-22 Denah Pelat LT1 dan Sloof.dwg"


# ------------------------------------------------------------------ GS-23 potongan pit lift (1:50)
def potong_pit(g, ox, nama, w, kode, beam=False):
    """Potongan pit lebar dalam w (m) berpusat di ox; elevasi dalam m sebagai koordinat tegak (oy = 0 baris 1)."""
    p = pit.data_lift()[kode]
    t = pe.T_PIT[kode]
    zd, zb, za, zl = p["dasar"], p["dasar"] - t, pit.ATAS, pit.LT1
    tw = pit.TW
    xl, xr = ox - w / 2 - tw, ox + w / 2 + tw        # muka luar dinding
    out, out_r = 0.9, 0.4
    g.layer("S-BETON", 7, 0.5)
    rect(g, xl, zb, xr, zd, "S-BETON", "ANSI31")       # pelat dasar
    rect(g, xl, zd, ox - w / 2, za, "S-BETON", "ANSI31")   # dinding kiri
    rect(g, ox + w / 2, zd, xr, za, "S-BETON", "ANSI31")
    rect(g, xl - out, za, ox - w / 2, zl, "S-BETON", "ANSI31")   # pelat LT1 (bukaan = ruang dalam)
    rect(g, ox + w / 2, za, xr + out_r, zl, "S-BETON", "ANSI31")
    if beam:
        bb, bh = pe.BALOK_PG
        rect(g, xl - bb, zl - bh, xl, zl, "S-BETON", "ANSI31")
        rect(g, xr, zl - bh, xr + bb, zl, "S-BETON", "ANSI31")
    # tulangan
    g.layer("S-TUL", 7, 0.35)
    zb_t, zt_t = zb + 0.05 + 0.0065, zd - 0.04 - 0.0065
    g.pline([(xl + 0.05, zb_t), (xr - 0.05, zb_t)], "S-TUL")
    g.pline([(xl + 0.05, zt_t), (xr - 0.05, zt_t)], "S-TUL")
    for xs, sgn in ((xl + 0.05 + 0.0065, 1), (xl + tw - 0.04 - 0.0065, 1)):
        g.pline([(xs, zb_t), (xs, za - 0.04)], "S-TUL")
    for xs in (xr - 0.05 - 0.0065, xr - tw + 0.04 + 0.0065):
        g.pline([(xs, zb_t), (xs, za - 0.04)], "S-TUL")
    # tulangan horizontal dinding (titik) tiap 0,25 m
    z = zd + 0.15
    while z < za - 0.1:
        for xs in (xl + 0.05 + 0.0065, xl + tw - 0.04 - 0.0065, xr - 0.05 - 0.0065, xr - tw + 0.04 + 0.0065):
            t4g._bulat(g, (xs, z), 0.03, "S-TUL")
        z += 0.25
    # sambungan kicker dan muka air
    g.layer("S-KICKER", 7, 0.18, "DASHED")
    for xa, xb in ((xl, xl + tw), (xr - tw, xr)):
        g.pline([(xa, zd + 0.15), (xb, zd + 0.15)], "S-KICKER")
    g.layer("S-AIR", 7, 0.18, "DASHDOT")
    bw = xl - (pe.BALOK_PG[0] if beam else 0)   # air di luar balok penggantung
    for nm, z in AIR:
        g.pline([(bw - out, z), (bw, z)], "S-AIR")
        g.teks((bw - out, z + 0.04), f"{nm} +{idn(z, 2)}", "S-AIR", H, j="L")
    # ukuran dan elevasi
    g.ukur((ox - w / 2, zl + 0.45), (ox + w / 2, zl + 0.45), (ox, zl + 0.45))
    g.ukur((xr + out_r + 0.25, zb), (xr + out_r + 0.25, zd), (xr + out_r + 0.25, (zb + zd) / 2), rot=90)
    g.ukur((xr + out_r + 0.25, zd), (xr + out_r + 0.25, za), (xr + out_r + 0.25, (zd + za) / 2), rot=90)
    g.ukur((ox + w / 2, zb - 0.3), (xr, zb - 0.3), ((ox + w / 2 + xr) / 2, zb - 0.3))
    g.layer("S-ELEVASI", 7, 0.18)
    xe = ox - w / 2 + 0.35
    g.titik_tinggi((xe, zb), f"+{idn(zb, 2)}", "S-ELEVASI", teks_at=(xe + 0.1, zb - 0.2))
    g.titik_tinggi((xe, zd), f"+{idn(zd, 2)}", "S-ELEVASI", teks_at=(xe + 0.1, zd + 0.1))
    g.titik_tinggi((xe, za), f"+{idn(za, 2)}", "S-ELEVASI")
    g.titik_tinggi((xl - out + 0.2, zl), f"+{idn(zl, 2)} LT1", "S-ELEVASI", teks_at=(xl - out + 0.35, zl + 0.12))
    # tag tulangan
    for s, (px, pz), (lx, lz) in (("1", (ox - 0.2, zb_t), (ox - 0.2, zd + 0.45)),
                                  ("2", (ox + 0.5, zt_t), (ox + 0.5, zd + 0.45)),
                                  ("3", (xl + 0.05 + 0.0065, zd + 0.6), (ox - w / 2 + 0.55, zd + 0.85)),
                                  ("4", (xr - tw + 0.04 + 0.0065, zd + 0.4), (ox + w / 2 - 0.55, zd + 0.85))):
        g.tunjuk((px, pz), (lx, lz), s, layer="S-TAG")
    atas, bawah = PIT_TUL[kode]
    baris = [f"1 PELAT BAWAH {bawah}", f"2 PELAT ATAS {atas}", f"3 DINDING VERT. {DINDING_TUL[0]}, {DINDING_TUL[1]}",
             f"4 HORIZ. {DINDING_TUL[2]}", f"PELAT t {idn(t, 2)} m; DINDING 0,30 m; fc' 35"]
    for k, s in enumerate(baris):
        g.teks((ox, zb - 0.55 - 0.15 * k), s, "S-TEKS", H, j="TC")
    ju = f"POTONGAN P{ {'L-1..4': 1, 'L-5..6': 2, 'L-7': 3}[kode] }: PIT {kode} ({idn(w, 1)} m)"
    judul(g, (ox, zl + 0.9), ju)


def gs23():
    from cad_lembar import Gambar
    with Gambar(50) as g:
        potong_pit(g, 3.8, "P1", 5.2, "L-1..4")
        potong_pit(g, 11.4, "P2", 4.6, "L-5..6")
        d3 = -6.5
        # baris 2: geser tegak dengan menggeser elevasi (hanya koordinat; ukuran dan elevasi teks tetap benar)
        potong_pit_baris2(g, 3.4, 3.4, "L-7", d3)
        kepala = ["PIT", "PELAT\nt (m)", "ATAS", "BAWAH", "DINDING\nVERTIKAL", "DINDING\nHORIZ."]
        baris = [[k, idn(pe.T_PIT[k], 2), PIT_TUL[k][0], PIT_TUL[k][1], "D13-250 luar\nD13-275 dalam",
                  "D13-250\ntiap muka"] for k in PIT_TUL]
        t4g.tabel(g, 6.8, 12.85 + d3, [20, 14, 22, 22, 36, 26], kepala, baris)
        g.legenda_tambah("arsir", "Beton terpotong (ANSI31 tipis)", pola="ANSI31")
        g.legenda_tambah("garis", "Tulangan (batang dan titik)", tebal=0.35)
        g.legenda_tambah("garis", "Sambungan kicker 150 (waterstop)", garis="DASHED", tebal=0.18)
        g.legenda_tambah("garis", "Muka air Q100, Q50, tekan", garis="DASHDOT", tebal=0.18)
        catatan = [
            "Opsi A (keputusan Defsa 21 Nov 2026): pelat dasar L-1..4 t 0,45; L-5..6 dan L-7 t 0,40; tanpa angkur "
            "(angkur Opsi B tidak dipilih). Sumber: 5.5 Desain Pit Lift.md bagian C dan Keputusan.",
            "Dinding 0,30 sampai sisi bawah pelat LT1 +12,60; fc' 35 MPa; selimut 50 mm sisi tanah, 40 mm sisi dalam.",
            "Muka air: Q100 +12,31, Q50 +11,85, tekan +11,20 (5.5 bagian A). Waterstop di sambungan pelat dasar-dinding "
            "(kicker 150) dan dinding-pelat LT1; aditif kristalin.",
            "L-7: 2 balok penggantung 400 × 800 bentang 8 m, 5 D29, di muka luar dinding pit (5.5 bagian C, 5.7).",
            "Pelat LT1 dan sloof di luar pit tidak dirinci: GS-22, GS-25."]
        lembar(g, "GS-23", "Potongan pit lift", 50, (7.2, 8.6),
               "Langkah 5.8: detail pit dari desain 5.5 (skala 1:50)", catatan, "POTONGAN PIT LIFT")
        simpan(g, DWG / "GS-23 Potongan Pit Lift.dwg")
    return DWG / "GS-23 Potongan Pit Lift.dwg"


def potong_pit_baris2(g, ox, w, kode, dz):
    """Potongan L-7 di baris kedua: seluruh koordinat tegak digeser dz; teks elevasi memakai nilai asli."""
    asli = {n: getattr(g, n) for n in ("pline", "teks", "ukur", "tunjuk", "titik_tinggi")}

    def sh(p):
        return (p[0], p[1] + dz)

    g.pline = lambda pts, layer, **k: asli["pline"]([sh(q) for q in pts], layer, **k)
    g.teks = lambda at, *a, **k: asli["teks"](sh(at), *a, **k)
    g.ukur = lambda p1, p2, at, **k: asli["ukur"](sh(p1), sh(p2), sh(at), **k)
    g.tunjuk = lambda a, b, s, **k: asli["tunjuk"](sh(a), sh(b), s, **k)

    def tt(at, s, *a, **k):   # titik_tinggi memanggil self.teks: pakai teks asli agar tidak digeser dua kali
        g.teks = asli["teks"]
        try:
            if k.get("teks_at"):
                k["teks_at"] = sh(k["teks_at"])
            asli["titik_tinggi"](sh(at), s, *a, **k)
        finally:
            g.teks = lambda at2, *a2, **k2: asli["teks"](sh(at2), *a2, **k2)
    g.titik_tinggi = tt
    try:
        potong_pit(g, ox, "P3", w, kode, beam=True)
    finally:
        for n, f in asli.items():
            setattr(g, n, f)


# ------------------------------------------------------------------ GS-24 zona MRI (1:25)
def gs24():
    from cad_lembar import Gambar
    sk = 25
    mx0, mx1 = MRI["x"]
    my0, my1 = MRI["y"]
    L = MRI["lewat"]
    sp = MRI["jarak"]
    with Gambar(sk) as g:
        # denah zona (koordinat proyek)
        g.layer("S-ZONA", 7, 0.5, "DASHED")
        g.pline([(mx0, my0), (mx1, my0), (mx1, my1), (mx0, my1)], "S-ZONA", tutup=True)
        g.layer("S-TUL-SS", 7, 0.5)
        g.layer("S-TUL-SSY", 7, 0.35, "DASHED")
        g.layer("S-TUL-BJ", 7, 0.25)
        for i in range(MRI["n"]):
            y = my0 + sp * i
            g.pline([(mx0 - L, y), (mx1 + L, y)], "S-TUL-SS")
            g.pline([(mx0 - L, y + 0.05), (mx0, y + 0.05)], "S-TUL-BJ")
            g.pline([(mx1, y + 0.05), (mx1 + L, y + 0.05)], "S-TUL-BJ")
            x = mx0 + sp * i
            g.pline([(x, my0 - L), (x, my1 + L)], "S-TUL-SSY")
        g.ukur((mx0, my0 - L - 0.3), (mx1, my0 - L - 0.3), ((mx0 + mx1) / 2, my0 - L - 0.3))
        g.ukur((mx0 - L, my1 + L + 0.3), (mx0, my1 + L + 0.3), (mx0 - L / 2, my1 + L + 0.3))
        g.ukur((mx1 + L + 0.3, my0), (mx1 + L + 0.3, my1), (mx1 + L + 0.3, (my0 + my1) / 2), rot=90)
        g.teks(((mx0 + mx1) / 2, my1 + L + 0.5), "x 79,5-81,5 / y 56-58; A955M tiap arah", "S-TEKS", H, j="BC")
        judul(g, ((mx0 + mx1) / 2, my1 + L + 0.95), "DENAH ZONA BAJA TAHAN KARAT")
        # potongan di bawah denah: elevasi asli z0, digeser DZ ke koordinat gambar
        ox = 84.3
        z_l0, z_b0 = pit.LT1, pit.ATAS
        DZ = 44.1
        zl, zb = z_l0 + DZ, z_b0 + DZ
        g.layer("S-BETON", 7, 0.5)
        rect(g, ox - 1.6, zb, ox + 1.6, zl, "S-BETON", "ANSI31")
        g.layer("S-TUL-SS", 7, 0.5)
        zbw, zbw2 = zb + 0.05 + 0.0065, zb + 0.05 + 0.013 + 0.0065
        zt1, zt2 = zl - 0.02 - 0.0065, zl - 0.02 - 0.013 - 0.0065
        for z in (zbw, zt1):
            g.pline([(ox - 1.58, z), (ox + 1.58, z)], "S-TUL-SS")
        g.layer("S-TUL-BJ", 7, 0.25)
        for z in (zbw, zt1):
            g.pline([(ox - 1.6, z + 0.03), (ox - 1.0, z + 0.03)], "S-TUL-BJ")
            g.pline([(ox + 1.0, z + 0.03), (ox + 1.6, z + 0.03)], "S-TUL-BJ")
        for i in range(MRI["n"]):
            for z in (zbw2, zt2):
                t4g._bulat(g, (ox - 1.0 + sp * i, z), 0.025, "S-TUL-SS")
        g.layer("S-ZONA", 7, 0.18, "DASHED")
        for x in (ox - 1.0, ox + 1.0):
            g.pline([(x, zb - 0.45), (x, zl + 0.45)], "S-ZONA")
        g.ukur((ox - 1.0, zl + 0.3), (ox + 1.0, zl + 0.3), (ox, zl + 0.3))
        g.ukur((ox - 1.58, zb - 0.3), (ox + 1.58, zb - 0.3), (ox, zb - 0.3))
        judul(g, (ox, zl + 0.8), "POTONGAN ZONA TAHAN KARAT")
        g.titik_tinggi((ox - 1.55, zl), f"+{idn(z_l0, 2)} LT1", "S-ELEVASI", teks_at=(ox - 1.4, zl + 0.1))
        g.titik_tinggi((ox - 1.55, zb), f"+{idn(z_b0, 2)}", "S-ELEVASI", teks_at=(ox - 1.4, zb - 0.2))
        ket = ["A955M fy 420 [Asumsi mutu]; D13-200 tiap arah",
               "11 batang per arah, 2 lapis (atas dan bawah)",
               f"Batang {idn(MRI['batang'], 2)} m = 2,0 + 2 × lewatan {int(MRI['lewat'] * 1000)} mm (kelas B)",
               "Lewatan seluruhnya di luar zona; ld 439,5 mm",
               "Selimut bawah 50, atas 20 mm; pelat t 250 monolit",
               "Kawat ikat dan kursi tahan karat/plastik [Asumsi]"]
        for k, t in enumerate(ket):
            g.teks((ox, zb - 0.65 - 0.1 * k), t, "S-TEKS", H, j="TC")
        g.legenda_tambah("garis", "Batang tahan karat A955M arah x", tebal=0.5)
        g.legenda_tambah("garis", "Batang tahan karat A955M arah y", garis="DASHED", tebal=0.35)
        g.legenda_tambah("garis", "Batang baja karbon D13-200 (lewatan)", tebal=0.25)
        g.legenda_tambah("garis", "Batas zona 2,0 × 2,0 m", garis="DASHED", tebal=0.5)
        catatan = [
            "Zona 2,0 × 2,0 m di pelat panel 9-10/D-E (x 79,5-81,5, y 56-58), isocenter (80,5; 57,0). Sumber: 5.2 Kajian "
            "MRI.md (keputusan), 5.3 Desain Pelat LT1.md (bagian baja tahan karat).",
            "44 batang (11 per lapis × 4 lapis), massa 144,60 kg (D13 1,04 kg/m, SNI 2052:2017).",
            "Sloof terdekat as E y 59: muka 1,8 m dari isocenter, baja karbon biasa (5.4).",
            "Denah zona dan potongan sama-sama 1:25 (satu skala satu layout); potongan di kanan denah, "
            "elevasi di teks adalah elevasi sebenarnya."]
        lembar(g, "GS-24", "Detail zona MRI baja tahan karat", sk, (82.4, 57.45),
               "Langkah 5.8: detail dari desain 5.2-5.3 (skala 1:25)", catatan, "DETAIL ZONA MRI", utara=True)
        simpan(g, DWG / "GS-24 Detail Zona MRI.dwg")
    return DWG / "GS-24 Detail Zona MRI.dwg"


# ------------------------------------------------------------------ GS-25 sloof (1:20)
def sloof_data():
    dk = sl.data_kolom()
    return {t: sl.desain(t, *pe.UKURAN_SLOOF[t], dk=dk) for t in sl.TIPE}


def penampang(g, ox, d, tipe):
    b, h = d["b"], d["h"]
    sa, sb, ss = sl.SEL_ATAS, sl.SEL_BAWAH, sl.SEL_SAMPING
    ds = d["ds"] / 1000
    g.layer("S-BETON", 7, 0.5)
    rect(g, ox, -h, ox + b, 0, "S-BETON")
    g.layer("S-SENGKANG", 7, 0.25)
    xa, xb, za, zb = ox + ss, ox + b - ss, -sa, -h + sb
    rect(g, xa, zb, xb, za, "S-SENGKANG")
    g.layer("S-TUL", 7, 0.35)

    def batang(t, dari_atas):
        n, n1, db = t["n"], t["n1"], t["db"] / 1000
        sbers = max(0.025, db)
        x0, x1 = xa + ds + db / 2, xb - ds - db / 2
        xs = [x0 + (x1 - x0) * i / (n1 - 1) for i in range(n1)]
        sisa, k = n, 0
        while sisa > 0:
            m = min(n1, sisa)
            st = (n1 - m) // 2
            z = (-(sa + ds + db / 2) - k * (db + sbers)) if dari_atas else (-h + sb + ds + db / 2 + k * (db + sbers))
            for x in xs[st:st + m]:
                t4g._bulat(g, (x, z), db, "S-TUL")
            sisa -= m
            k += 1
    batang(d["atas"], True)
    batang(d["bawah"], False)
    if d["kaki"] > 2:   # kaki ikat tegak di antara batang samping
        for i in range(d["kaki"] - 2):
            x = xa + (xb - xa) * (i + 1) / (d["kaki"] - 1)
            g.pline([(x, za), (x, zb)], "S-SENGKANG")
    g.ukur((ox, 0.28), (ox + b, 0.28), (ox + b / 2, 0.28))
    g.ukur((ox - 0.3, -h), (ox - 0.3, 0), (ox - 0.3, -h / 2), rot=90)
    judul(g, (ox + b / 2, 0.55), f"{tipe} {int(b * 1000)} × {int(h * 1000)}")
    ta, tb_ = d["atas"], d["bawah"]
    baris = [f"ATAS {ta['n']} D{ta['db']} ({ta['n1']} + {ta['n'] - ta['n1']}, {ta['lapis']} LAPIS)",
             f"BAWAH {tb_['n']} D{tb_['db']} ({tb_['n1']} + {tb_['n'] - tb_['n1']}, {tb_['lapis']} LAPIS)",
             f"SENGKANG D{d['ds']} {d['kaki']} KAKI",
             f"{int(d['s_ujung'] * 1000)} mm DI {idn(d['l_ujung'], 1)} m UJUNG",
             f"{int(d['s_tengah'] * 1000)} mm DI TENGAH BENTANG",
             f"SELIMUT {int(sb * 1000)} BAWAH/SAMPING, {int(sa * 1000)} ATAS"]
    for k, s in enumerate(baris):
        g.teks((ox + b / 2, -h - 0.3 - 0.07 * k), s, "S-TEKS", H, j="TC")


def gs25():
    from cad_lembar import Gambar
    dat = sloof_data()
    with Gambar(20) as g:
        for i, tipe in enumerate(sl.TIPE):
            penampang(g, 0.6 + 2.3 * i, dat[tipe], tipe)
        kepala = ["TIPE", "LETAK", "b × h", "ATAS", "BAWAH", "SENGKANG\nUJUNG", "SENGKANG\nTENGAH"]
        letak = {"SL-1": "dalam", "SL-2": "tepi", "SL-3": "as 10 (MRI)"}
        baris = []
        for tp in sl.TIPE:
            d = dat[tp]
            baris.append([tp, letak[tp], f"{int(d['b'] * 1000)} × {int(d['h'] * 1000)}",
                          f"{d['atas']['n']} D{d['atas']['db']}", f"{d['bawah']['n']} D{d['bawah']['db']}",
                          f"{d['kaki']} kaki D{d['ds']}-{int(d['s_ujung'] * 1000)}",
                          f"{d['kaki']} kaki D{d['ds']}-{int(d['s_tengah'] * 1000)}"])
        t4g.tabel(g, 0.6, -2.2, [22, 30, 28, 28, 28, 40, 40], kepala, baris)
        g.legenda_tambah("garis", "Beton sloof", tebal=0.5)
        g.legenda_tambah("garis", "Sengkang dan kaki ikat", tebal=0.25)
        g.legenda_tambah("arsir", "Batang longitudinal (skala batang)", pola="SOLID")
        catatan = [
            "Sloof fc' 35 MPa, BjTS 420B; SL-1 400 × 900 (keputusan Defsa 21 Nov 2026), SL-2 dan SL-3 400 × 800. "
            "Sumber: 5.4 Desain Sloof.md (tabel desain, kandidat ukuran, keputusan).",
            "Sengkang SL-1 400 × 900 dari skrip tahap5_sloof (md memuat sengkang untuk 400 × 800).",
            "Sengkang pengekang di 2h dari muka kolom (SNI 2847:2019 18.6.4); Ve dari Mpr 1,25 fy, Vc = 0.",
            "Ujung: kait 90° ke kolom tepi (ldh 381 mm; tersedia 697-897); kolom dalam menerus. Ujung di inti: "
            "menunggu pile cap inti Tahap 6.",
            "Sloof baja karbon biasa; zona tahan karat tidak tersentuh sloof (jarak terdekat 1,8 m)."]
        lembar(g, "GS-25", "Tabel dan penampang sloof", 20, (3.05, -1.15),
               "Langkah 5.8: sloof dari desain 5.4 (skala 1:20)", catatan, "PENAMPANG SLOOF")
        simpan(g, DWG / "GS-25 Tabel dan Penampang Sloof.dwg")
    return DWG / "GS-25 Tabel dan Penampang Sloof.dwg"


# ------------------------------------------------------------------ GS-26 kolom tangki (1:25)
def kolom_tb(g, ox, lv, k):
    b = t5.B_KOLOM_B
    n, m, db, s = k["n"], k["m"], k["db"] / 1000, k["s_lo"]
    sel = sl.SEL_KOL
    g.layer("S-BETON", 7, 0.5)
    rect(g, ox, 0, ox + b, b, "S-BETON")
    g.layer("S-SENGKANG", 7, 0.25)
    rect(g, ox + 0.04, 0.04, ox + b - 0.04, b - 0.04, "S-SENGKANG")
    pos = [sel + db / 2 + (b - 2 * sel - db) * i / (m - 1) for i in range(m)]
    for p in pos[1:-1]:
        g.pline([(ox + p, 0.04), (ox + p, b - 0.04)], "S-SENGKANG")
        g.pline([(ox + 0.04, p), (ox + b - 0.04, p)], "S-SENGKANG")
    g.layer("S-TUL", 7, 0.35)
    for i, p in enumerate(pos):
        for j, q in enumerate(pos):
            if i in (0, m - 1) or j in (0, m - 1):
                t4g._bulat(g, (ox + p, q), db, "S-TUL")
    g.ukur((ox, -0.25), (ox + b, -0.25), (ox + b / 2, -0.25))
    judul(g, (ox + b / 2, b + 0.45), f"K-TB {lv} {int(b * 1000)} × {int(b * 1000)}")
    ket = [f"{n} D{k['db']} (RHO {KOLOM_TB[lv]['rho']} %)", f"SENGKANG D13-{s} {m} KAKI",
           f"LO {k['lo']} mm; P-M {KOLOM_TB[lv]['pm']}"]
    for i, t in enumerate(ket):
        g.teks((ox + b / 2, -0.55 - 0.08 * i), t, "S-TEKS", H, j="TC")


def stek(g, ox):
    b, cap = t5.B_KOLOM_B, pe.T_CAP
    z1r = pe.HALAMAN                  # elevasi sebenarnya (teks); koordinat gambar digeser dz
    dz = -12.65
    z1 = z1r + dz
    z0 = z1 - cap
    w = 1.0                           # cap ditampilkan ox - w .. ox + b + w (dipotong)
    g.layer("S-BETON", 7, 0.5)
    rect(g, ox - w, z0, ox + b + w, z1, "S-BETON", "ANSI31")
    rect(g, ox, z1, ox + b, z1 + 1.1, "S-BETON")
    g.layer("S-SENGKANG", 7, 0.25)
    for i in range(9):    # sengkang di cap D13-125, 9 baris
        g.pline([(ox + 0.04, z1 - 0.1 - 0.125 * i), (ox + b - 0.04, z1 - 0.1 - 0.125 * i)], "S-SENGKANG")
    for i in range(7):    # di lo 800
        g.pline([(ox + 0.04, z1 + 0.05 + 0.125 * i), (ox + b - 0.04, z1 + 0.05 + 0.125 * i)], "S-SENGKANG")
    g.layer("S-TUL", 7, 0.5)
    zb = z0 + pe.SEL_CAP + pe.DB_CAP
    for xs, d in ((ox + 0.053 + 0.011, 1), (ox + b - 0.053 - 0.011, -1)):
        g.pline([(xs, z1 + 1.05), (xs, zb), (xs + d * 0.264, zb)], "S-TUL", tebal=0.7)   # stek D22 tebal
    g.pline([(ox - w + 0.05, z0 + pe.SEL_CAP + 0.016), (ox + b + w - 0.05, z0 + pe.SEL_CAP + 0.016)], "S-TUL")
    g.layer("S-HALAMAN", 7, 0.18, "DASHED")
    g.pline([(ox - w, z1), (ox + b + w, z1)], "S-HALAMAN")
    g.ukur((ox - w - 0.3, z0), (ox - w - 0.3, z1), (ox - w - 0.3, (z0 + z1) / 2), rot=90)
    g.ukur((ox - w - 0.65, zb), (ox - w - 0.65, z1 + 1.05), (ox - w - 0.65, (zb + z1 + 1.05) / 2), rot=90)
    g.ukur((ox, z1 + 1.35), (ox + b, z1 + 1.35), (ox + b / 2, z1 + 1.35))
    g.titik_tinggi((ox + b + w + 0.25, z1), f"+{idn(z1r, 2)}", "S-ELEVASI", teks_at=(ox + b + w + 0.4, z1 + 0.05))
    g.titik_tinggi((ox + b + w + 0.25, z0), f"+{idn(z1r - cap, 2)}", "S-ELEVASI", teks_at=(ox + b + w + 0.4, z0 - 0.2))
    judul(g, (ox + b / 2, z1 + 1.75), "STEK KOLOM TB KE PILE CAP")
    ket = [f"20 D22: ldh PERLU {STEK['ldh']}, TERSEDIA KAIT {idn(STEK['kait'], 0)} mm",
           f"ld LURUS PERLU {STEK['ld']}, TERSEDIA {idn(STEK['lurus'], 0)} mm",
           f"ldc {STEK['ldc']} mm; SENGKANG DI CAP D13-125 (9 BARIS)", "TEBAL CAP 1.200 mm (TAHAP 6)"]
    for i, t in enumerate(ket):
        g.teks((ox + b / 2, z0 - 0.3 - 0.08 * i), t, "S-TEKS", H, j="TC")


def gs26():
    from cad_lembar import Gambar
    with Gambar(25) as g:
        kolom_tb(g, 0.0, "LT2", t5.BESI_TANGKI["LT2"])
        kolom_tb(g, 1.9, "LT3", t5.BESI_TANGKI["LT3"])
        stek(g, 4.6)
        kepala = ["KOLOM", "b (mm)", "TULANGAN", "RHO", "SENGKANG DI lo", "P-M", "Ve (kN)"]
        baris = [[f"K-TB {lv}", "800", f"{k['n']} D{k['db']}", f"{KOLOM_TB[lv]['rho']} %",
                  f"D13-{k['s_lo']} ({k['m']} kaki), lo {k['lo']}", KOLOM_TB[lv]["pm"], KOLOM_TB[lv]["ve"]]
                 for lv, k in t5.BESI_TANGKI.items()]
        t4g.tabel(g, 0.0, -2.9, [24, 16, 24, 18, 52, 14, 18], kepala, baris)
        g.legenda_tambah("garis", "Beton kolom tangki dan sengkang", tebal=0.5)
        g.legenda_tambah("arsir", "Pile cap (tebal 1.200; ANSI31 tipis)", pola="ANSI31")
        g.legenda_tambah("garis", "Stek kolom dengan kait 90°", tebal=0.5)
        catatan = [
            "Kolom tangki 800 seragam (keputusan Defsa 21 Nov 2026): K-TB LT2 20 D22, D13-125 6 kaki; K-TB LT3 32 D29, "
            "D13-150 9 kaki; lo 800. Sumber: 5.6a Kolom Tangki Opsi B.md (hasil per kelompok, stek ke pile cap).",
            "Enam kolom: x 60, 68, 76 / y 67, 75 (tahap5_tangki.KOLOM). Muka pile cap +12,05, tebal 1.200 [Asumsi 3.7].",
            "Panjang penyaluran stek (SNI 2847:2019 18.8.5.1, 25.4.2): ldh 375, ld 919, ldc 397 mm; tersedia 1.093 / 1.125 mm.",
            "Pile cap dan tiang didesain di Tahap 6; gambar stek hanya menunjukkan penyaluran ke cap."]
        lembar(g, "GS-26", "Detail kolom tangki dan stek ke pile cap", 25, (3.45, -1.2),
               "Langkah 5.8: kolom tangki dari desain 5.6a (skala 1:25)", catatan, "DETAIL KOLOM TANGKI")
        simpan(g, DWG / "GS-26 Detail Kolom Tangki.dwg")
    return DWG / "GS-26 Detail Kolom Tangki.dwg"


# ------------------------------------------------------------------ semua lembar
LEMBAR = {"GS-22": gs22, "GS-23": gs23, "GS-24": gs24, "GS-25": gs25, "GS-26": gs26}


def gabung_pdf(keluar=PDF):
    import pypdfium2 as pdfium
    hasil = pdfium.PdfDocument.new()
    for p in sorted(PLOT.glob("GS-*.pdf")):
        src = pdfium.PdfDocument(str(p))
        hasil.import_pages(src)
        src.close()
    hasil.save(str(keluar))
    hasil.close()
    shutil.rmtree(PLOT, ignore_errors=True)
    return keluar


def buat(nomor_=None, ekspor=False):
    import cad_cek
    if ekspor:
        ekspor_bim()
    hasil = {}
    for no, f in LEMBAR.items():
        if nomor_ and no not in nomor_:
            continue
        dwg = f()
        hasil[no] = {"dwg": dwg, "tumpuk": cad_cek.cek(dwg)}
        print(no, dwg.name, len(hasil[no]["tumpuk"]), "pasangan", flush=True)
    if not nomor_:
        gabung_pdf()
    return hasil


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    arg = [a for a in sys.argv[1:] if a.startswith("GS-")]
    buat(arg or None, ekspor="--ekspor" in sys.argv)
