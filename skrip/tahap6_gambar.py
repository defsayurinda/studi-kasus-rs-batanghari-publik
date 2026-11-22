"""Langkah 6.10: gambar pondasi (GS-28..GS-32, GT-16) di CADCraft, ber-kop KOP_A3.

GS-28 denah tiang dan pile cap (319 tiang, 83 cap; sama dengan IFC 6.9). Data: tahap6_bim.caps()/tiang() (dari
tahap6_tata_letak.rancang("a")). Tanpa poche hitam. DATA SIMULASI. Disetujui atas delegasi Defsa 22 Nov 2026.
Jalankan: .venv\\Scripts\\python.exe skrip\\tahap6_gambar.py GS-28 [GS-29 ...]
"""
from __future__ import annotations

import collections
import math
import shutil
import sys
from pathlib import Path

from shapely.geometry import LineString, box
from shapely.strtree import STRtree

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_gambar_ded as t4g  # noqa: E402
import tahap6_bim as b6  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "06 Struktur Bawah dan Basement"
GAMBAR = KELUAR / "Gambar"
DWG = GAMBAR / "DWG"
PLOT = GAMBAR / "_plot"
PDF = GAMBAR / "GS-28..32 dan GT-16 Pondasi.pdf"
TANGGAL = "NOVEMBER 2026"
STATUS = "DISETUJUI 22 NOV 2026"
H = 1.6
GRID_X, GRID_Y, NAMA_X, NAMA_Y = t4g.tb.GRID_X, t4g.tb.GRID_Y, t4g.NAMA_X, t4g.NAMA_Y
idn = b6.idn


CAP_E_TAMBAH = [(37.9, 30.2), (40.9, 30.2)]     # 2 tiang Ø800 baru, perlebaran L-7 (7.3, K7.3-3)
CAP_E_LEBAR = (37.1, 29.4, 41.7)                 # x0, y0, x1; menyatu dengan Cap E di y = bbox y0


def caps73():
    """Daftar cap 6.9 + perlebaran Cap E dari 7.3 (2 tiang, 321 tiang total). Model IFC 6.9 belum memuatnya."""
    cs = b6.caps()
    for c in cs:
        if c["id"] == "Cap E":
            c["pos_dasar"] = list(c["pos"])
            c["pos"] = list(c["pos"]) + CAP_E_TAMBAH
            c["n"] = len(c["pos"])
            c["perlebar"] = CAP_E_LEBAR
    return cs


def kontur(c):
    """Titik tepi cap; Cap E dengan perlebaran berbentuk L (satu garis tepi, tanpa garis bersama)."""
    x0, y0, x1, y1 = c["bbox"]
    if "perlebar" not in c:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    wx0, wy0, wx1 = c["perlebar"]
    return [(x0, y0), (wx0, y0), (wx0, wy0), (wx1, wy0), (wx1, y0), (x1, y0), (x1, y1), (x0, y1)]


def kode_cap(c):
    if c["jenis"] == "inti":
        return "PC-" + c["id"].split()[-1]
    return ("PC" if c["jenis"] == "kolom" else "PU") + str(c["n"])


def rekap_cap(cs=None):
    """Baris tabel per tipe cap: (kode, jenis, n/cap, jml cap, jml tiang, h mm, ukuran terbesar)."""
    cs = cs or b6.caps()
    grup = collections.OrderedDict()
    for c in sorted(cs, key=lambda c: (c["jenis"] != "kolom", c["jenis"] != "inti", c["n"], c["id"])):
        grup.setdefault(kode_cap(c), []).append(c)
    out = []
    for k, L in grup.items():
        w = max(c["bbox"][2] - c["bbox"][0] for c in L)
        d = max(c["bbox"][3] - c["bbox"][1] for c in L)
        out.append((k, L[0]["jenis"], L[0]["n"], len(L), sum(c["n"] for c in L), round(L[0]["h"] * 1000), f"{idn(w, 1)} × {idn(d, 1)}"))
    return out


def simpan(g, dwg):
    PLOT.mkdir(parents=True, exist_ok=True)
    g.simpan(dwg, PLOT / f"{dwg.stem}.pdf", GAMBAR / f"{dwg.stem}.png")


def blok_tiang(g, nama, layer):
    g.layer(layer, 7, 0.18)
    h = [g.cmd("circle", {"center": [0, 0], "radius": 400})["handle"],
         g.cmd("pline", {"vertices": [[-150, 0], [150, 0]]})["handle"],
         g.cmd("pline", {"vertices": [[0, -150], [0, 150]]})["handle"]]
    g.cmd("block", {"name": nama, "base": [0, 0], "handles": h, "keep": "delete"})


class Penempat:
    def __init__(self, obst):
        self.o = list(obst)
        self.t = STRtree(self.o)

    def bebas(self, r):
        return len(self.t.query(r, predicate="intersects")) == 0

    def tambah(self, r):
        self.o.append(r)
        self.t = STRtree(self.o)

    def cari(self, bbox, w, h):
        x0, y0, x1, y1 = bbox
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        kand = [(cx, cy)]
        for gap in (0.3, 0.9, 1.8):
            for dx in (0, -w * 0.6, w * 0.6):
                kand += [(cx + dx, y1 + gap + h / 2), (cx + dx, y0 - gap - h / 2)]
            for dy in (0, -h, h):
                kand += [(x1 + gap + w / 2, cy + dy), (x0 - gap - w / 2, cy + dy)]
        for x, y in kand:
            r = box(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
            if self.bebas(r):
                self.tambah(r)
                return x, y
        return None


# ------------------------------------------------------------------ GS-28
def gs28():
    from cad_lembar import Gambar
    cs = caps73()
    ts = b6.tiang(cs)
    SK = 500
    hm = H * SK / 1000
    with Gambar(SK) as g:
        blok_tiang(g, "TIANG_UTAMA", "S-TIANG-UTAMA")
        blok_tiang(g, "TIANG_UTIL", "S-TIANG-UTIL")
        g.layer("S-CAP", 7, 0.35)
        g.layer("S-CAP-INTI", 7, 0.6)
        g.layer("S-CAP-UTIL", 7, 0.25)
        obst = []
        for t in ts:
            g.aktif("S-TIANG-UTAMA" if t["gedung"] == "utama" else "S-TIANG-UTIL")
            g.cmd("insert", {"name": "TIANG_UTAMA" if t["gedung"] == "utama" else "TIANG_UTIL", "at": g.mm((t["x"], t["y"]))})
            obst.append(box(t["x"] - 0.4, t["y"] - 0.4, t["x"] + 0.4, t["y"] + 0.4))
        for c in cs:
            x0, y0, x1, y1 = c["bbox"]
            lay = "S-CAP-INTI" if c["jenis"] == "inti" else "S-CAP-UTIL" if c["jenis"] == "utilitas" else "S-CAP"
            g.pline(kontur(c), lay, tutup=True)
            obst.append(LineString(kontur(c) + [kontur(c)[0]]).buffer(0.12))
        # as grid: potongan pendek di luar massa, gelembung di luar
        gx0, gx1, gy0, gy1 = GRID_X[0], GRID_X[-1], GRID_Y[0], GRID_Y[-1]
        rb = 3.0 * SK / 1000
        for i, x in enumerate(GRID_X):
            g.as_grid(NAMA_X[i], (x, 77.3), (x, 78.8), r_kertas=3.0, dua_ujung=False)
            g.as_grid(NAMA_X[i], (x, 24.6), (x, 23.1), r_kertas=3.0, dua_ujung=False)
        for j, y in enumerate(GRID_Y):
            g.as_grid(NAMA_Y[j], (9.2, y), (7.7, y), r_kertas=3.0, dua_ujung=False)
        # ukuran asosiatif antar-as
        for a, b in zip(GRID_X, GRID_X[1:]):
            g.ukur((a, 81.9), (b, 81.9), ((a + b) / 2, 84.0))
        g.ukur((gx0, 81.9), (gx1, 81.9), ((gx0 + gx1) / 2, 88.0))
        for a, b in zip(GRID_Y, GRID_Y[1:]):
            g.ukur((4.6, a), (4.6, b), (2.8, (a + b) / 2), rot=90)
        g.ukur((4.6, gy0), (4.6, gy1), (0.4, (gy0 + gy1) / 2), rot=90)
        for x, y in [(gx0 - 0.0, 0.0)]:
            pass
        g.layer("S-TEKS", 7, 0.18)
        g.teks((118.0, 80.0), "GEDUNG UTILITAS + PARKIR", "S-TEKS", H, j="MC", tebal=True)
        g.teks((48.0, 17.5), "GEDUNG UTAMA", "S-TEKS", H, j="MC", tebal=True)
        pn = Penempat(obst + [box(100, 79.2, 136, 80.8)] + [box(x - rb, 77.3, x + rb, 81.9) for x in GRID_X]
                      + [box(x - rb, 20.0, x + rb, 24.6) for x in GRID_X])
        for c in cs:
            s = kode_cap(c)
            w, h_ = 0.95 * 0.9 * hm * len(s) + 0.2, hm * 1.2
            p = pn.cari(c["bbox"], w, h_)
            if p is None:
                raise RuntimeError(f"label {c['id']} tidak muat")
            g.teks(p, s, "S-TEKS", H, j="MC")
        # tabel kunci tipe cap di bawah denah
        rek = rekap_cap(cs)
        baris = [[k, {"kolom": "kolom", "inti": "inti", "utilitas": "utilitas"}[j], n, nc, nt, hh, uk] for k, j, n, nc, nt, hh, uk in rek]
        baris.append(["JUMLAH", "", "", sum(r[3] for r in rek), sum(r[4] for r in rek), "", ""])
        t4g.tabel(g, 12.0, 12.0, [20, 20, 20, 20, 22, 22, 32], ["KODE", "JENIS", "TIANG/CAP", "JML CAP", "JML TIANG", "h (mm)", "UKURAN (m)"], baris)
        g.legenda_tambah("garis", f"Tiang bor Ø800 gedung utama ({sum(1 for t in ts if t['gedung'] == 'utama')})", tebal=0.18)
        g.legenda_tambah("garis", f"Tiang bor Ø800 utilitas + parkir ({sum(1 for t in ts if t['gedung'] == 'utilitas')})", tebal=0.18)
        g.legenda_tambah("garis", "Pile cap kolom (PC2/3/4/6)", tebal=0.35)
        g.legenda_tambah("garis", "Pile cap inti (PC-A..G), PC-E gabungan", tebal=0.6)
        g.legenda_tambah("garis", f"Pile cap utilitas (PU2/PU4, {sum(1 for c in cs if c['jenis'] == 'utilitas')})", tebal=0.25)
        catatan = [
            f"{len(ts)} tiang bor Ø800 dan {len(cs)} pile cap: model IFC 6.9 (RSTB-STR-T6-LOD300, 319 tiang) + 2 tiang dan perlebaran Cap E dari 7.3 (IFC 6.9 belum memuatnya).",
            "Muka cap +12,05; ujung tiang -27,60; kepala tiang = dasar cap + 0,15. Tebal cap kolom 1.000/800/950 mm (2/3/4 tiang), inti 1.200, Cap E 2.000 (6.7).",
            "Cap E gabungan (Cap C digabung, keputusan Defsa 22 Nov 2026): 54 tiang, 30,4 × 13,6 m, ditambah perlebaran L-7 x 37,1-41,7, y 29,4-32,2 dengan 2 tiang (7.3): 56 tiang. Tipe dan tulangan: GS-29..GS-32.",
            "Tiang utilitas + parkir 68 tidak berubah (3.7 [Asumsi]). Data simulasi."]
        g.lembar("GS-28", "Denah tiang dan pile cap", f"1:{SK}", pusat=None, status=STATUS, tanggal=TANGGAL,
                 subjudul="Langkah 6.10: denah pondasi dari 6.3 dan 6.9 (skala 1:500)", catatan=catatan, judul_kop="DENAH TIANG DAN PILE CAP")
        g.viewport_tambahan((26, 40), (331, 283), (69.5, 38.0), SK, None, None)
        g.skala_grafis(205, 22, 20, bagi=4)
        g.panah_utara(318, 262, 10)
        simpan(g, DWG / "GS-28 Denah Tiang dan Pile Cap.dwg")
    return DWG / "GS-28 Denah Tiang dan Pile Cap.dwg"


# ------------------------------------------------------------------ helper umum
def telapak_cap(g, c, SK, bars=(), kolom=()):
    """Denah cap: tepi, tiang (block), ukuran chain kiri/atas, total kanan. bars: [(huruf, 'x'|'y', koordinat, putus)]."""
    x0, y0, x1, y1 = c["bbox"]
    lay = "S-CAP-INTI" if c["jenis"] == "inti" else "S-CAP"
    g.layer(lay, 7, 0.6 if c["jenis"] == "inti" else 0.35)
    g.pline(kontur(c), lay, tutup=True)
    g.aktif("S-TIANG-UTAMA")
    for x, y in c["pos"]:
        g.cmd("insert", {"name": "TIANG_UTAMA", "at": g.mm((x, y))})
    dasar = c.get("pos_dasar", c["pos"])
    xs = sorted({round(p[0], 3) for p in dasar})
    ys = sorted({round(p[1], 3) for p in dasar})
    for a, b in zip(xs, xs[1:]):
        g.ukur((a, y1), (b, y1), ((a + b) / 2, y1 + 1.5))
    g.ukur((x0, y1), (x1, y1), ((x0 + x1) / 2, y1 + 2.6))
    for a, b in zip(ys, ys[1:]):
        g.ukur((x0, a), (x0, b), (x0 - 1.4, (a + b) / 2), rot=90)
    g.ukur((x1, y0), (x1, y1), (x1 + 1.4, (y0 + y1) / 2), rot=90)
    g.layer("S-TUL", 7, 0.35)
    hm = H * SK / 1000
    for huruf, arah, v, putus in bars:
        gaya = "DASHED" if putus else None
        if arah == "x":
            g.pline([(x0 + 0.075, v), (x1 - 0.075, v)], "S-TUL", garis=gaya)
            g.teks((x1 + 0.35, v - hm / 2), huruf, "S-TEKS", H, j="L", tebal=True)
        else:
            g.pline([(v, y0 + 0.075), (v, y1 - 0.075)], "S-TUL", garis=gaya)
            g.teks((v, y1 + 0.35), huruf, "S-TEKS", H, j="BC", tebal=True)
    g.layer("S-KOLOM", 7, 0.25)
    for kx, ky, w in kolom:
        g.pline([(kx - w / 2, ky - w / 2), (kx + w / 2, ky - w / 2), (kx + w / 2, ky + w / 2), (kx - w / 2, ky + w / 2)], "S-KOLOM", tutup=True)


def blok_semua(g):
    blok_tiang(g, "TIANG_UTAMA", "S-TIANG-UTAMA")
    g.layer("S-TEKS", 7, 0.18)


# ------------------------------------------------------------------ GS-29 pile cap inti
E_TUL = {"1": "D32-150, 2 LAPIS (BAWAH, ARAH X)", "2": "D32-175, 1 LAPIS (BAWAH, ARAH Y)",
         "3": "D32-125, 1 LAPIS (ATAS, ARAH X)", "4": "D32-200, 1 LAPIS (ATAS, ARAH Y)"}   # 6.7 bagian 4
A_TUL = "D25-200 DUA ARAH, BAWAH DAN ATAS"   # [Asumsi: minimum susut 0,0018 b h per muka, SNI 2847:2019 24.4.3.2]


def gs29():
    from cad_lembar import Gambar
    import tahap6_tata_letak as tl
    cs = caps73()
    ce = next(c for c in cs if c["id"] == "Cap E")
    ca = next(c for c in cs if c["id"] == "Cap A")
    kolom = [(t["x"], t["y"], 0.8) for t in next(c for c in tl.rancang("a")[1] if c["kode"] == "E")["titik"] if not t["nama"].startswith("INTI")]
    SK = 150
    hm = H * SK / 1000
    with Gambar(SK) as g:
        blok_semua(g)
        x0, y0, x1, y1 = ce["bbox"]
        xs = sorted({round(p[0], 3) for p in ce["pos_dasar"]})
        ys = sorted({round(p[1], 3) for p in ce["pos_dasar"]})
        telapak_cap(g, ce, SK, bars=[("1", "x", ys[1] - 1.2, False), ("3", "x", ys[1] + 1.2, True),
                                     ("2", "y", (xs[0] + xs[1]) / 2, False), ("4", "y", (xs[1] + xs[2]) / 2, True)], kolom=kolom)
        wx0, wy0, wx1 = ce["perlebar"]
        g.ukur((wx0, wy0), (wx0, y0), (wx0 - 1.4, (wy0 + y0) / 2), rot=90)
        g.teks((wx1 + 0.6, wy0 + 0.8), "PERLEBARAN L-7 (7.3) 4,6 x 2,8 m + 2 TIANG", "S-TEKS", H, j="L", tebal=True)
        g.layer("S-INTI", 7, 0.35, "DASHDOT")
        g.pline([(50.0, 35.0), (58.0, 35.0), (58.0, 43.0), (50.0, 43.0)], "S-INTI", tutup=True)
        g.layer("M-PIT", 7, 0.25, "DASHED")
        g.pline([(51.1, 35.6), (56.9, 35.6), (56.9, 42.4), (51.1, 42.4)], "M-PIT", tutup=True)
        g.layer("S-POTONG", 7, 0.5, "DASHDOT")
        g.pline([(x0 - 0.5, ys[1]), (x1, ys[1])], "S-POTONG")
        g.teks((x0 - 0.62, ys[1] - hm / 2), "A", "S-TEKS", H, j="R", tebal=True)
        g.teks((x1 + 0.3, ys[1] - hm / 2), "A", "S-TEKS", H, j="L", tebal=True)
        # potongan A-A memanjang (y = elevasi z)
        zb, zt = 12.05 - 2.0, 12.05
        g.layer("S-CAP-INTI", 7, 0.6)
        g.pline([(x0, zb), (x1, zb), (x1, zt), (x0, zt)], "S-CAP-INTI", tutup=True)
        g.layer("S-TIANG-UTAMA", 7, 0.18)
        for x in xs:
            g.pline([(x - 0.4, zb + 0.15), (x - 0.4, 6.4)], "S-TIANG-UTAMA")
            g.pline([(x + 0.4, zb + 0.15), (x + 0.4, 6.4)], "S-TIANG-UTAMA")
        g.pline([(x0, 6.4), (x1, 6.4)], "S-TIANG-UTAMA", garis="DASHED")
        g.layer("S-TUL", 7, 0.35)
        for z in (zb + 0.091, zb + 0.148):
            g.pline([(x0 + 0.075, z), (x1 - 0.075, z)], "S-TUL")
        g.pline([(x0 + 0.075, zt - 0.091), (x1 - 0.075, zt - 0.091)], "S-TUL", garis="DASHED")
        g.teks(((x0 + x1) / 2, 5.9), "TIANG TERUS KE -27,60 (DIPUTUS)", "S-TEKS", H, j="MC")
        g.ukur((x0, zb), (x0, zt), (x0 - 1.4, (zb + zt) / 2), rot=90)
        for a, b in zip(xs, xs[1:]):
            g.ukur((a, zt), (b, zt), ((a + b) / 2, zt + 1.3))
        g.titik_tinggi((xs[1] + 1.8, zb), "+10,05 DASAR CAP", "S-TEKS", teks_at=(xs[1] + 2.0, zb - 0.6))
        g.titik_tinggi((xs[5] + 1.8, zt), "+12,05 MUKA CAP", "S-TEKS", teks_at=(xs[5] + 2.0, zt + 0.35))
        g.teks((x0 + 0.3, 5.2), "TULANGAN 1-4: LIHAT DENAH; KEPALA TIANG +10,20", "S-TEKS", H, j="L")
        # Cap A
        telapak_cap(g, ca, SK)
        ax0, ay0, ax1, ay1 = ca["bbox"]
        g.layer("S-TUL", 7, 0.35)
        g.pline([(ax0 + 0.075, ay0 + 1.2), (ax1 - 0.075, ay0 + 1.2)], "S-TUL")
        g.pline([(ax0 + 1.0, ay0 + 0.075), (ax0 + 1.0, ay1 - 0.075)], "S-TUL")
        g.teks(((ax0 + ax1) / 2, ay0 - 0.7), A_TUL, "S-TEKS", H, j="MC")
        g.legenda_tambah("garis", "Pile cap inti (tepi)", tebal=0.6)
        g.legenda_tambah("garis", "Tiang bor Ø800 (blok)", tebal=0.18)
        g.legenda_tambah("garis", "Tulangan bawah (1, 2)", tebal=0.35)
        g.legenda_tambah("garis", "Tulangan atas (3, 4), putus-putus", garis="DASHED", tebal=0.35)
        g.legenda_tambah("garis", "Kolom 0,8 m; inti lif 4 × 8 m (titik-garis); pit (putus)", tebal=0.25)
        catatan = [
            "Cap E gabungan (Cap C + Cap E, keputusan Defsa 22 Nov 2026): 54 tiang + perlebaran L-7 dari 7.3 (4,6 × 2,8 m, 2 tiang baru, menyatu, h 2.000, tulangan perlebaran [Asumsi sama dengan Cap E]) = 56 tiang, 30,4 × 13,6 m, h 2.000 mm, pelat tebal di atas pegas tiang (6.7 bagian 4), f'c 35 MPa, fy 420 MPa, selimut 75 mm; tanpa tulangan pons.",
            "Tulangan Cap E (6.7), nomor pada denah: " + "; ".join(f"{k} {v.split(' (')[0]}" for k, v in E_TUL.items()) + ". Digambar satu batang contoh, dipasang merata.",
            "Dasar Cap E +10,05, kepala tiang +10,20, muka +12,05; pit L-1..4 berdiri di Cap E. Inti lif 4 × 8 m [Asumsi 6.7].",
            "Cap A 14 tiang h 1.200: tulangan minimum susut D25-200 [Asumsi, tidak dihitung di 6.7; hanya pons tiang rasio 0,50].",
            "Potongan A-A melalui baris tiang ke-2 (y = 35,41 m). Jarak tiang 3,6 × 2,4 m; tepi cap 0,80 m dari as tiang."]
        g.lembar("GS-29", "Pile cap inti: Cap E gabungan dan Cap A", f"1:{SK}", pusat=None, status=STATUS, tanggal=TANGGAL,
                 subjudul="Langkah 6.10: dari 6.7 (skala 1:150)", catatan=catatan, judul_kop="PILE CAP INTI E DAN A")
        g.viewport_tambahan((26, 150), (258, 283), (48.6, 39.0), SK, "Denah pile cap E gabungan (56 tiang, h 2.000)", f"SKALA 1:{SK}")
        g.viewport_tambahan((262, 146), (331, 283), (20.9, 40.2), SK, "Denah pile cap A (14 tiang, h 1.200)", f"SKALA 1:{SK}")
        g.viewport_tambahan((26, 62), (258, 135), (48.6, 10.1), SK, "Potongan A-A pile cap E", f"SKALA 1:{SK}")
        g.skala_grafis(205, 22, 5, bagi=5)
        simpan(g, DWG / "GS-29 Pile Cap Inti.dwg")
    return DWG / "GS-29 Pile Cap Inti.dwg"


# ------------------------------------------------------------------ GS-30 pile cap tipikal
TUL_KOLOM = {2: (6, 9), 3: (8, 10), 4: (13, 13)}      # D32 batang x, y (6.7 bagian 3, tabel lentur dan stek)


def d16_susut(h_mm):
    """Jarak D16 (mm) untuk As susut 0,0018 b h per muka, b 1.000 mm (SNI 2847:2019 24.4.3.2) [Asumsi: tulangan atas/samping]."""
    perlu = 0.0018 * 1000 * h_mm
    return int(201.06 * 1000 / perlu // 25 * 25)


def _tipikal(cs):
    return {n: next(c for c in cs if c["jenis"] == "kolom" and c["n"] == n) for n in (2, 3, 4)}


def gs30():
    from cad_lembar import Gambar
    cs = b6.caps()
    tip = _tipikal(cs)
    SK = 50
    with Gambar(SK) as g:
        blok_semua(g)
        for k, n in enumerate((2, 3, 4)):
            c = tip[n]
            h = c["h"]
            x0, y0, x1, y1 = c["bbox"]
            ox, oy = 0.9 + 5.0 * k, 6.0
            sx, sy = ox - x0, oy - y0
            pos = [(x + sx, y + sy) for x, y in c["pos"]]
            bx0, by0, bx1, by1 = ox, oy, ox + (x1 - x0), oy + (y1 - y0)
            g.layer("S-CAP", 7, 0.5)
            g.pline([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], "S-CAP", tutup=True)
            g.aktif("S-TIANG-UTAMA")
            for x, y in pos:
                g.cmd("insert", {"name": "TIANG_UTAMA", "at": g.mm((x, y))})
            nx, ny = TUL_KOLOM[n]
            g.layer("S-TUL", 7, 0.35)
            for i in range(nx):
                y = by0 + 0.075 + (by1 - by0 - 0.15) * i / (nx - 1)
                g.pline([(bx0 + 0.075, y), (bx1 - 0.075, y)], "S-TUL")
            xp = sorted({round(p[0], 3) for p in pos})
            for a, b in zip(xp, xp[1:]):
                g.ukur((a, by1), (b, by1), ((a + b) / 2, by1 + 0.6))
            g.ukur((bx0, by1), (bx1, by1), ((bx0 + bx1) / 2, by1 + 1.2))
            g.ukur((bx0, by0), (bx0, by1), (bx0 - 0.5, (by0 + by1) / 2), rot=90)
            g.teks(((bx0 + bx1) / 2, by0 - 0.4), f"PC{n}: {n} TIANG, h {round(h * 1000):,}".replace(",", "."), "S-TEKS", H, j="MC", tebal=True)
            # potongan melalui baris tiang
            zt = 4.2
            zb = zt - h
            g.layer("S-CAP", 7, 0.5)
            g.pline([(bx0, zb), (bx1, zb), (bx1, zt), (bx0, zt)], "S-CAP", tutup=True)
            g.layer("S-TIANG-UTAMA", 7, 0.18)
            for x in xp[:2] if n != 3 else xp[:2]:
                g.pline([(x - 0.4, zb + 0.15), (x - 0.4, zb - 0.8)], "S-TIANG-UTAMA")
                g.pline([(x + 0.4, zb + 0.15), (x + 0.4, zb - 0.8)], "S-TIANG-UTAMA")
            g.pline([(bx0, zb - 0.8), (bx1, zb - 0.8)], "S-TIANG-UTAMA", garis="DASHED")
            g.layer("S-TUL", 7, 0.35)
            g.pline([(bx0 + 0.075, zb + 0.091), (bx1 - 0.075, zb + 0.091)], "S-TUL")
            for i in range(ny):
                t4g._bulat(g, (bx0 + 0.075 + (bx1 - bx0 - 0.15) * i / (ny - 1), zb + 0.091 + 0.032), 0.032, "S-TUL")
            g.pline([(bx0 + 0.075, zt - 0.083), (bx1 - 0.075, zt - 0.083)], "S-TUL", garis="DASHED")
            g.ukur((bx0, zb), (bx0, zt), (bx0 - 0.5, (zb + zt) / 2), rot=90)
            g.ukur((bx0, zt), (bx1, zt), ((bx0 + bx1) / 2, zt + 0.6))
            sp = d16_susut(round(h * 1000))
            for r, s in enumerate([f"BAWAH X: {nx} D32; BAWAH Y: {ny} D32", f"ATAS DAN SAMPING: D16-{sp} [ASUMSI]",
                                   "SELIMUT 75; f'c 35; fy 420", "KEPALA TIANG = DASAR CAP + 0,15"]):
                g.teks((bx0, 1.5 - 0.3 * r), s, "S-TEKS", H, j="L")
        g.legenda_tambah("garis", "Pile cap kolom", tebal=0.5)
        g.legenda_tambah("garis", "Tiang bor Ø800 (blok)", tebal=0.18)
        g.legenda_tambah("garis", "Tulangan bawah D32", tebal=0.35)
        g.legenda_tambah("garis", "Tulangan atas (putus-putus)", garis="DASHED", tebal=0.35)
        catatan = [
            "Tebal cap kolom 1.000 / 800 / 950 mm untuk 2 / 3 / 4 tiang (keputusan Defsa 22 Nov 2026, 6.7); tiang masuk cap 150 mm; kepala tiang = dasar cap + 0,15.",
            "Tulangan bawah D32 jumlah batang x / y: 2 tiang 6 / 9, 3 tiang 8 / 10, 4 tiang 13 / 13 (6.7 bagian 3, SNI 2847:2019 Pasal 13.4).",
            "Tulangan atas dan samping tidak dihitung di 6.7: dipasang D16 pada As susut 0,0018 b h per muka (SNI 2847:2019 24.4.3.2) [Asumsi].",
            "Stek kolom dan kait: ldh D25 426 mm, h min stek 565 mm terpenuhi (6.7). Bentuk denah = cap tipikal pertama tiap tipe di model 6.9.",
            "Cap 6 tiang (PC6, 1 buah, as 3/C, h 1.200 [Asumsi]) mengikuti tata letak GS-28."]
        g.lembar("GS-30", "Pile cap tipikal 2, 3 dan 4 tiang", f"1:{SK}", pusat=None, status=STATUS, tanggal=TANGGAL,
                 subjudul="Langkah 6.10: dari 6.7 bagian 3 (skala 1:50); potongan melalui baris tiang", catatan=catatan, judul_kop="PILE CAP TIPIKAL 2/3/4 TIANG")
        g.viewport_tambahan((26, 40), (331, 283), (7.675, 5.8), SK, None, None)
        g.skala_grafis(205, 22, 2, bagi=4)
        simpan(g, DWG / "GS-30 Pile Cap Tipikal.dwg")
    return DWG / "GS-30 Pile Cap Tipikal.dwg"


# ------------------------------------------------------------------ GS-31 detail tiang bor
import contextlib  # noqa: E402


_DIM = {"DIMTXT": 1.8, "DIMASZ": 1.6, "DIMEXO": 1.0, "DIMEXE": 1.2, "DIMGAP": 0.6, "DIMTAD": 1, "DIMDEC": 2, "DIMDSEP": ",",
        "DIMLFAC": 0.001, "DIMTXSTY": "TNR_TEBAL", "DIMTSZ": 1.0, "DIMTIH": 0, "DIMTOH": 0, "DIMZIN": 0, "DIMTFILL": 1}


@contextlib.contextmanager
def skl(g, s):
    """Skala gambar sementara (teks dan ukuran) untuk viewport berskala lain; satu gaya ukur per skala."""
    lama = g.skala
    g.skala = s
    g.cmd("dimstyle", {"name": f"PROYEK{s}", "current": True, "DIMSCALE": s, **_DIM})
    try:
        yield
    finally:
        g.skala = lama
        g.cmd("dimstyle", {"name": f"PROYEK{lama}", "current": True, "DIMSCALE": lama, **_DIM})


def gs31():
    from cad_lembar import Gambar
    with Gambar(50) as g:
        g.layer("S-TEKS", 7, 0.18)
        # ---- VP1 elevasi (V 1:250, lebar dilebihkan)
        with skl(g, 250):
            top, kep, zr, zt_, zu = 12.05, 11.25, -14.91, -17.76, -27.60
            g.layer("S-CAP", 7, 0.5)
            g.pline([(-3.5, 11.10), (3.5, 11.10), (3.5, top), (-3.5, top)], "S-CAP", tutup=True)
            g.layer("S-TIANG", 7, 0.5)
            g.pline([(-1.6, kep), (-1.6, zu), (1.6, zu), (1.6, kep)], "S-TIANG")
            g.layer("S-SENGKANG", 7, 0.25)
            g.layer("S-BATAS", 7, 0.25, "DASHED")
            g.pline([(-1.6, zr), (1.6, zr)], "S-BATAS")
            g.pline([(-1.6, zt_), (1.6, zt_)], "S-BATAS")
            g.layer("S-TUL", 7, 0.5)
            g.pline([(-1.0, kep - 0.2), (-1.0, zu + 0.2)], "S-TUL")
            g.pline([(1.0, kep - 0.2), (1.0, zt_)], "S-TUL")
            g.arsir([(-1.6, kep), (1.6, kep), (1.6, zr), (-1.6, zr)], "S-SENGKANG", "ANSI37", 0.35, tepi=False)
            g.arsir([(-1.6, zr), (1.6, zr), (1.6, zu), (-1.6, zu)], "S-SENGKANG", "ANSI31", 0.35, tepi=False)
            for z, s in [(top, "+12,05 MUKA CAP"), (kep, "+11,25 KEPALA TIANG (CAP h 950)"), (zr, "-14,91 UJUNG ZONA RAPAT"),
                         (zt_, "-17,76 UJUNG TULANGAN CAP KOLOM"), (zu, "-27,60 UJUNG TIANG")]:
                xk = 4.0 if z in (top, kep) else 2.4
                g.pline([(1.6 if z != top else 3.5, z), (xk - 0.2, z)], "S-TEKS")
                g.teks((xk, z - 0.2), s, "S-TEKS", H, j="L")
            g.teks((2.4, -5.0), "ZONA RAPAT: SPIRAL D13-40", "S-TEKS", H, j="L", tebal=True)
            g.teks((2.4, -22.0), "SPIRAL D13-80", "S-TEKS", H, j="L", tebal=True)
            g.teks((2.4, -9.0), "16 D25 MEMANJANG", "S-TEKS", H, j="L")
            g.teks((2.4, -24.3), "D25 CAP INTI: PENUH", "S-TEKS", H, j="L")
            g.teks((2.4, -25.2), "CAP KOLOM: -17,76", "S-TEKS", H, j="L")
            g.ukur((-1.6, kep), (-1.6, zr), (-5.0, (kep + zr) / 2), rot=90)
            g.ukur((-1.6, zr), (-1.6, zu), (-5.0, (zr + zu) / 2), rot=90)
            g.ukur((-1.6, kep), (-1.6, zu), (-6.6, (kep + zu) / 2), rot=90)
        # ---- VP2 penampang 1:20
        with skl(g, 20):
            cx = 200.0
            g.layer("S-BETON", 7, 0.5)
            g.cmd("circle", {"center": g.mm((cx, 0)), "radius": 400})
            g.layer("S-SENGKANG", 7, 0.25)
            g.cmd("circle", {"center": g.mm((cx, 0)), "radius": 325})
            g.layer("S-TUL", 7, 0.35)
            for i in range(16):
                t = 2 * math.pi * i / 16
                t4g._bulat(g, (cx + 0.306 * math.cos(t), 0.306 * math.sin(t)), 0.025, "S-TUL")
            g.ukur((cx - 0.4, 0), (cx + 0.4, 0), (cx, -0.5), rot=0)
            for (px, py), (tx, ty), s in [((cx + 0.2164, 0.2164), (cx + 0.55, 0.5), "16 D25"),
                                          ((cx + 0.3265, 0.0), (cx + 0.55, 0.12), "SPIRAL D13"),
                                          ((cx + 0.4, -0.1), (cx + 0.55, -0.25), "SELIMUT 75")]:
                g.pline([(px, py), (tx, ty), (tx + 0.04, ty)], "S-TEKS")
                g.teks((tx + 0.07, ty - 0.012), s, "S-TEKS", H, j="L")
        # ---- VP3 kepala tiang 1:50
        with skl(g, 50):
            cx, zt, zb = 100.0, 12.05, 11.10
            g.layer("S-CAP", 7, 0.5)
            g.pline([(cx - 2, zb), (cx + 2, zb), (cx + 2, zt), (cx - 2, zt)], "S-CAP", tutup=True)
            for x in (cx - 1.2, cx + 1.2):
                g.layer("S-TIANG", 7, 0.5)
                g.pline([(x - 0.4, zb + 0.15), (x - 0.4, 8.0)], "S-TIANG")
                g.pline([(x + 0.4, zb + 0.15), (x + 0.4, 8.0)], "S-TIANG")
                g.layer("S-SENGKANG", 7, 0.18)
                for k in range(15):
                    z = zb + 0.15 - 0.04 * (k + 1)
                    g.pline([(x - 0.325, z), (x + 0.325, z)], "S-SENGKANG")
                g.layer("S-TUL", 7, 0.5)
                for s_ in (-1, 1):
                    xb = x + s_ * 0.3
                    g.pline([(xb, 8.0), (xb, 11.90), (xb - s_ * 0.3, 11.90)], "S-TUL")
            g.pline([(cx - 2, 8.0), (cx + 2, 8.0)], "S-TIANG", garis="DASHED")
            g.pline([(cx - 1.925, zb + 0.091), (cx + 1.925, zb + 0.091)], "S-TUL")
            for i in range(13):
                t4g._bulat(g, (cx - 1.925 + 3.85 * i / 12, zb + 0.123), 0.032, "S-TUL")
            g.pline([(cx - 1.925, zt - 0.083), (cx + 1.925, zt - 0.083)], "S-TUL", garis="DASHED")
            g.ukur((cx - 2, zb), (cx - 2, zt), (cx - 2.4, (zb + zt) / 2), rot=90)
            g.ukur((cx - 2, zt), (cx + 2, zt), (cx, zt + 0.5))
            for r, s in enumerate(["TULANGAN BAWAH D32, 13 BATANG TIAP ARAH (CAP 4 TIANG)", "TULANGAN ATAS D16-100 [ASUMSI]",
                                   "TIANG 16 D25, KAIT 90° KE CAP (ldh 426; TERSEDIA 725)", "SPIRAL D13-40 (ZONA RAPAT), 15 PUTARAN DIGAMBAR",
                                   "KEPALA TIANG = DASAR CAP + 0,15 (+11,25)"]):
                g.teks((cx - 2.5, 7.6 - 0.3 * r), s, "S-TEKS", H, j="L")
        # ---- VP4 Cap E tebal 1:25
        with skl(g, 25):
            cx, zt, zb = 300.0, 12.05, 10.05
            g.layer("S-CAP", 7, 0.5)
            g.pline([(cx - 0.6, zb), (cx + 0.6, zb), (cx + 0.6, zt), (cx - 0.6, zt)], "S-CAP", tutup=True)
            g.layer("S-TIANG", 7, 0.5)
            g.pline([(cx - 0.4, zb + 0.15), (cx - 0.4, 8.95)], "S-TIANG")
            g.pline([(cx + 0.4, zb + 0.15), (cx + 0.4, 8.95)], "S-TIANG")
            g.layer("S-TUL", 7, 0.35)
            for z in (zb + 0.091, zb + 0.148):
                g.pline([(cx - 0.525, z), (cx + 0.525, z)], "S-TUL")
            for i in range(6):
                t4g._bulat(g, (cx - 0.525 + 1.05 * i / 5, zb + 0.205), 0.032, "S-TUL")
            g.pline([(cx - 0.525, zt - 0.091), (cx + 0.525, zt - 0.091)], "S-TUL", garis="DASHED")
            for i in range(5):
                t4g._bulat(g, (cx - 0.525 + 1.05 * i / 4, zt - 0.148), 0.032, "S-TUL")
            g.ukur((cx - 0.6, zb), (cx - 0.6, zt), (cx - 0.8, (zb + zt) / 2), rot=90)
            for r, s in enumerate(["ATAS Y: D32-200", "ATAS X: D32-125", "BAWAH Y: D32-175", "BAWAH X: D32-150, 2 LAPIS"]):
                g.teks((cx - 0.6, zt + 0.1 + 0.075 * r), s, "S-TEKS", H, j="L")
        g.legenda_tambah("garis", "Beton (tepi, tanpa poche)", tebal=0.5)
        g.legenda_tambah("garis", "Tulangan utama D25 / D32 / D16", tebal=0.5)
        g.legenda_tambah("arsir", "Zona rapat spiral D13-40", pola="ANSI37", skala_pola=0.35)
        g.legenda_tambah("arsir", "Zona spiral D13-80", pola="ANSI31", skala_pola=0.35)
        g.legenda_tambah("garis", "Batas zona / tulangan atas", garis="DASHED", tebal=0.25)
        catatan = [
            "Tiang bor Ø800, f'c 35 MPa, 16 D25 (rasio 0,83), spiral D13 fyt 420: 40 mm dari kepala sampai -14,91 (zona rapat 25,76 m selatan), 80 mm di bawahnya; selimut 75 mm (SNI 2847:2019 Tabel 20.6.1.3.1; 18.13.4).",
            "Tulangan D25 cap inti penuh sampai -27,60; cap kolom sampai -17,76 (ld 1.044 mm). Keputusan Defsa 22 Nov 2026 (6.7).",
            "Elevasi tiang: ujung -27,60; kepala = dasar cap + 0,15 (contoh cap kolom 4 tiang h 950: +11,25). Elevasi elevasi terhadap BM-1 = +10,000.",
            "Elevasi tiang digambar V 1:250 dengan lebar tiang dilebihkan 4 kali; penampang 1:20; kepala 1:50; Cap E 1:25.",
            "Tulangan atas cap D16 adalah [Asumsi] (tidak dihitung di 6.7). Cap E 2.000: D32 bawah 150 / 175, atas 125 / 200 (6.7 bagian 4)."]
        g.lembar("GS-31", "Detail tiang bor dan penulangan", "SESUAI GAMBAR", pusat=None, status=STATUS, tanggal=TANGGAL,
                 subjudul="Langkah 6.10: dari 6.7 dan 6.8 (1:250 V, 1:20, 1:50, 1:25)", catatan=catatan, judul_kop="DETAIL TIANG BOR")
        g.viewport_tambahan((26, 56), (110, 283), (3.0, -14.0), 250, "Elevasi tiang (V 1:250)", "SKALA 1:250 (LEBAR DILEBIHKAN)")
        g.viewport_tambahan((114, 215), (222, 283), (200.45, 0.0), 20, "Penampang tiang", "SKALA 1:20")
        g.viewport_tambahan((114, 56), (222, 205), (99.9, 9.75), 50, "Kepala tiang dan cap kolom", "SKALA 1:50")
        g.viewport_tambahan((226, 56), (331, 200), (300.0, 10.7), 25, "Tebal Cap E (lajur 1,2 m)", "SKALA 1:25")
        simpan(g, DWG / "GS-31 Detail Tiang Bor.dwg")
    return DWG / "GS-31 Detail Tiang Bor.dwg"


# ------------------------------------------------------------------ GS-32 tabel
TUL_CAP = {"PC2": "BAWAH 6 D32 (X) / 9 D32 (Y)", "PC3": "BAWAH 8 D32 (X) / 10 D32 (Y)", "PC4": "BAWAH 13 D32 TIAP ARAH",
           "PC6": "TIDAK DIHITUNG DI 6.7", "PC-E": "D32-150 2 LAPIS / D32-175", "PU2": "LINGKUP 3.7 (TIDAK 6.7)", "PU4": "LINGKUP 3.7 (TIDAK 6.7)"}


def tabel_cap(cs=None):
    """Baris GS-32 per tipe cap (dari rekap_cap): kode, jenis, tiang/cap, jml cap, jml tiang, h, ukuran, tulangan."""
    out = []
    for k, j, n, nc, nt, hh, uk in rekap_cap(cs):
        out.append([k, j, n, nc, nt, hh, uk, TUL_CAP.get(k, "D25-200 DUA ARAH [ASUMSI]")])
    return out


def gs32():
    from cad_lembar import Gambar
    cs = caps73()
    rek = tabel_cap(cs)
    SK = 100
    r = b6.rencana(cs)
    with Gambar(SK) as g:
        g.layer("S-TEKS", 7, 0.18)
        g.teks((1.0, 25.0), "TABEL 1: TIPE PILE CAP", "S-TEKS", 2.0, j="L", tebal=True)
        baris = [list(map(str, x)) for x in rek] + [["JUMLAH", "", "", str(sum(x[3] for x in rek)), str(sum(x[4] for x in rek)), "", "", ""]]
        yb = t4g.tabel(g, 1.0, 24.0, [16, 17, 17, 14, 16, 14, 24, 52], ["KODE", "JENIS", "TIANG/CAP", "JML CAP", "JML TIANG", "h (mm)", "UKURAN (m)", "TULANGAN"], baris)
        g.teks((1.0, yb - 1.6), "TABEL 2: TIANG BOR Ø800", "S-TEKS", 2.0, j="L", tebal=True)
        tiang = [["Diameter / luas", "800 mm / 0,503 m²"], ["Mutu", "f'c 35 MPa, fy 420 MPa"], ["Tulangan memanjang", "16 D25 (rasio 0,83)"],
                 ["Spiral", "D13-40 sampai -14,91; D13-80 di bawahnya"], ["Selimut", "75 mm ke spiral"],
                 ["Ujung tiang / panjang", "-27,60 m; 38,85 m (kepala +11,25)"], ["Tulangan terpotong", "cap kolom -17,76; cap inti penuh"],
                 ["Jumlah", f"{r['n_tiang']} (utama {r['n_utama']}, utilitas {r['n_util']})"]]
        yb2 = t4g.tabel(g, 1.0, yb - 3.0, [50, 98], ["BESARAN", "NILAI"], tiang)
        g.teks((1.0, yb2 - 1.6), "TABEL 3: REKAP VOLUME BETON (BRUTO)", "S-TEKS", 2.0, j="L", tebal=True)
        t4g.tabel(g, 1.0, yb2 - 3.0, [50, 50, 48], ["BESARAN", "NILAI", "SATUAN"],
                  [["Volume tiang", idn(r["v_tiang"], 0), "m³"], ["Volume pile cap (selubung)", idn(r["v_cap"], 0), "m³"]])
        catatan = [
            f"{r['n_tiang']} tiang dan {r['n_cap']} cap = model IFC 6.9 (319 tiang) + 2 tiang perlebaran Cap E dari 7.3 (IFC 6.9 belum memuatnya); jumlah per tipe dari 6.3 rancang a.",
            "Tulangan cap: 6.7 bagian 3 dan 4; cap inti selain E dan cap utilitas tidak dihitung di 6.7: [Asumsi] minimum susut D25-200.",
            "Volume tiang = π D²/4 × panjang tiap tiang (kepala = dasar cap + 0,15 sampai -27,60); volume cap = selubung denah × h (kasar, termasuk ruang antar tiang)."]
        g.lembar("GS-32", "Tabel tiang dan pile cap", f"TANPA SKALA", pusat=None, status=STATUS, tanggal=TANGGAL,
                 subjudul="Langkah 6.10: tabel dari 6.3, 6.7 dan 6.9", catatan=catatan, judul_kop="TABEL TIANG DAN PILE CAP")
        g.viewport_tambahan((26, 40), (331, 283), (14.5, 12.0), SK, None, None)
        simpan(g, DWG / "GS-32 Tabel Tiang dan Pile Cap.dwg")
    return DWG / "GS-32 Tabel Tiang dan Pile Cap.dwg"


# ------------------------------------------------------------------ GT-16 potongan tebing P-2
def fk_tebing():
    """FK Bishop persil per kasus dan konfigurasi dari cache 6.4 (TAHAP6_TEBING_CACHE=1; hitung bila cache belum ada)."""
    import os
    os.environ.setdefault("TAHAP6_TEBING_CACHE", "1")
    import tahap6_tebing as tb
    return tb, tb.semua()


def baris_fk(tb, h):
    nama = {"a": "(a) Muka air rendah +4,00", "a0": "(a0) Statis muka normal +6,37", "b": "(b) Surut cepat Q50 ke +4,00",
            "c": "(c) Gempa kh 0,171, muka normal", "c2": "(c') Gempa kh 0,085 (50 %)", "d": "(d) Pasca-likuifaksi (Sr)"}
    out = []
    for ks in tb.kasus():
        t, p = h["fk"][(ks["kode"], "tanpa")]["persil"]["bishop"], h["fk"][(ks["kode"], "perkuatan")]["persil"]["bishop"]
        out.append([nama[ks["kode"]], idn(ks["izin"], 2), idn(t, 2), idn(p, 2), "YA" if p >= ks["izin"] else "TIDAK"])
    return out


def gt16():
    import numpy as np
    from cad_lembar import Gambar
    import la_tebing as lt
    tb, h = fk_tebing()
    pot, pot0 = tb.pot_konf("perkuatan"), tb.pot_konf("tanpa")
    X0, X1, ZB = -42.0, 45.0, -30.0
    SK = 300
    xx = np.linspace(X0, X1, 175)
    with Gambar(SK) as g:
        pola = {"U2": "GT-LEMPUNG-TEGUH", "U4": "GT-LEMPUNG-LUNAK", "U5": "GT-PASIR-LEPAS", "U6": "GT-LEMPUNG-KAKU"}
        nama = {"U2": "U2 lempung teguh", "U4": "U4 lempung lunak", "U5": "U5 pasir lepas", "U6": "U6 lempung kaku"}
        atas = 12.0
        for kode, bawah in pot0.lapis:
            pg = lt._poligon_lapis(pot0, X0, X1, atas, max(bawah, ZB))
            if pg:
                g.layer(f"G-{kode}", 7, 0.18)
                g.arsir(pg, f"G-{kode}", pola=pola[kode], skala_pola=0.5)
                g.legenda_tambah("arsir", nama[kode], pola=pola[kode], skala_pola=0.5)
            atas = bawah
        # urugan halaman +12,05 dan jalur penyangga (beban 6.4)
        zg = lambda x: float(pot0.tanah0(x))
        g.layer("G-URUGAN", 7, 0.18)
        xs_u = [x for x in np.linspace(X0, -15.5, 40)]
        poli = [(float(x), zg(x)) for x in xs_u] + [(-15.5, zg(-15.5) + 1.0), (-25.5, zg(-25.5) + 1.0), (-25.5, 12.05), (X0, 12.05)]
        g.arsir(poli, "G-URUGAN", pola="GT-URUGAN", skala_pola=0.5)
        g.legenda_tambah("arsir", "Urugan halaman dan jalur", pola="GT-URUGAN", skala_pola=0.5)
        # air muka rendah +4,00
        xc = float(xx[np.argmax((pot0.tanah0(xx) < 4.0) & (xx > 0))])
        air = [(xc, 4.0), (X1, 4.0)] + [(float(x), zg(x)) for x in xx[::-1] if x >= xc]
        g.layer("G-AIR", 7, 0.18)
        g.arsir(air, "G-AIR", pola="GT-AIR", skala_pola=0.5)
        g.legenda_tambah("arsir", "Air sungai +4,00", pola="GT-AIR", skala_pola=0.5)
        # muka tanah
        g.layer("G-TANAH", 7, 0.7)
        g.pline([(float(x), float(pot.tanah0(x))) for x in xx], "G-TANAH")
        g.layer("G-TANAH0", 7, 0.35, "DASHED")
        g.pline([(float(x), zg(x)) for x in xx], "G-TANAH0")
        g.layer("G-BERM", 7, 0.7)
        g.pline([tuple(p) for p in pot.berm], "G-BERM")
        g.legenda_tambah("garis", "Muka tanah dengan perkuatan", tebal=0.7)
        g.legenda_tambah("garis", "Muka tanah asli tanpa perkuatan", garis="DASHED", tebal=0.35)
        # bidang kritis Bishop persil, perkuatan
        gaya = {"a": (None, 0.5), "c": ("DASHED", 0.5), "d": ("DASHDOT", 0.5)}
        ket = {"a": "(a) +4,00", "c": "(c) gempa", "d": "(d) likuifaksi"}
        g.layer("G-KRITIS", 7, 0.5)
        for kode, (ls, tb_) in gaya.items():
            r = h["fk"][(kode, "perkuatan")]["persil"]
            xo, yo, rr, _ = r["bidang"]
            th = np.linspace(math.radians(185), math.radians(355), 200)
            px, py = xo + rr * np.cos(th), yo + rr * np.sin(th)
            seg = []
            for x, y in zip(px, py):
                if X0 <= x <= X1 and y < zg(x) - 0.05 and y > ZB:
                    seg.append((float(x), float(y)))
                elif len(seg) > 1:
                    g.pline(seg, "G-KRITIS", tebal=tb_, garis=ls)
                    seg = []
                else:
                    seg = []
            if len(seg) > 1:
                g.pline(seg, "G-KRITIS", tebal=tb_, garis=ls)
            g.legenda_tambah("garis", f"Kritis {ket[kode]}: FK {idn(r['bishop'], 2)}", garis=ls or "Continuous", tebal=0.5)
        # tiang gedung, batas lahan
        g.layer("S-TIANG", 7, 0.5)
        g.pline([(-26.7, 11.25), (-26.7, -27.6), (-25.9, -27.6), (-25.9, 11.25)], "S-TIANG")
        g.layer("C-BATAS", 7, 0.5, "PHANTOM")
        g.pline([(0.0, ZB), (0.0, 15.0)], "C-BATAS")
        g.layer("G-AIR-GARIS", 7, 0.25, "DASHED")
        g.layer("S-TEKS", 7, 0.18)
        for z, s in ((11.85, "MA +11,85 (Q50)"), (6.37, "MA +6,37 (NORMAL)"), (4.0, "MA +4,00 (RENDAH)")):
            g.pline([(26.0, z), (X1, z)], "G-AIR-GARIS")
            g.teks((X1 - 0.3, z + 0.25), s, "S-TEKS", H, j="R")
        g.teks((0.5, 15.2), "BATAS LAHAN", "S-TEKS", H, j="L", tebal=True)
        g.teks((-25.4, 16.0), "TIANG GEDUNG UTAMA Ø800, UJUNG -27,60 (x = -26,3)", "S-TEKS", H, j="L")
        g.teks((8.0, 10.6), "BERM BRONJONG + PELANDAIAN 1V:2H", "S-TEKS", H, j="L")
        g.titik_tinggi((-41.0, 12.05), "+12,05 HALAMAN", "S-TEKS", teks_at=(-40.0, 12.3))
        g.ukur((-26.3, 13.0), (0.0, 13.0), (-13.15, 14.0))
        # tabel hasil
        g.teks((X0 + 0.5, -32.2), "HASIL STABILITAS P-2 DI BATAS LAHAN (BISHOP, PERSIL; 6.4)", "S-TEKS", 2.0, j="L", tebal=True)
        t4g.tabel(g, X0 + 0.5, -33.4, [58, 22, 24, 30, 24], ["KASUS", "FK IZIN", "FK TANPA", "FK PERKUATAN", "MEMENUHI"], baris_fk(tb, h))
        catatan = [
            "Potongan P-2 (LA.3, 6.4): k su 1,64 dan bidang licin 1,40; berm bronjong + pelandaian 1V:2H (LA.3).",
            "Bidang kritis Bishop masuk persil. Berm + pelandaian saja belum cukup untuk (c) dan (d): FK di bawah 1,1.",
            "Perkuatan batas lahan (tiang bor Ø600 atau turap) belum diputuskan (6.4); tidak digambar.",
            "Beban: halaman +12,05, jalur penyangga 1,0 m (-25,5 s.d. -15,5)."]
        g.lembar("GT-16", "Potongan tebing P-2 dan bidang kritis", f"1:{SK}", pusat=None, status=STATUS, tanggal=TANGGAL,
                 subjudul="Langkah 6.10: dari 6.4 (skala 1:300)", catatan=catatan, judul_kop="POTONGAN TEBING P-2")
        g.viewport_tambahan((26, 40), (331, 283), (1.5, -19.5), SK, None, None)
        g.skala_grafis(205, 22, 20, bagi=4)
        simpan(g, DWG / "GT-16 Potongan Tebing P-2.dwg")
    return DWG / "GT-16 Potongan Tebing P-2.dwg"


LEMBAR = {"GS-28": gs28, "GS-29": gs29, "GS-30": gs30, "GS-31": gs31, "GS-32": gs32, "GT-16": gt16}


def gabung_pdf(keluar=PDF):
    import pypdfium2 as pdfium
    hasil = pdfium.PdfDocument.new()
    for p in sorted(PLOT.glob("*.pdf")):
        src = pdfium.PdfDocument(str(p))
        hasil.import_pages(src)
        src.close()
    hasil.save(str(keluar))
    hasil.close()
    shutil.rmtree(PLOT, ignore_errors=True)
    return keluar


def buat(nomor_=None):
    import cad_cek
    for no, f in LEMBAR.items():
        if nomor_ and no not in nomor_:
            continue
        dwg = f()
        print(no, dwg.name, len(cad_cek.cek(dwg)), "pasangan", flush=True)
    if not nomor_:
        gabung_pdf()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    buat([a for a in sys.argv[1:] if a[:3] in ("GS-", "GT-")] or None)
