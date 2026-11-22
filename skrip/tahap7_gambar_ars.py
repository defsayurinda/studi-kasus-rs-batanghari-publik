"""Langkah 7.4: gambar DED arsitektur GA-01..GA-23 di CADCraft, ber-kop KOP_A3.

Sumber geometri: view asli model BIMCraft `RSTB-ARS-T7-LOD300` (denah per lantai, potongan/tampak dari view `section`),
diekspor DXF lalu dibersihkan (tanpa teks BIM, tanpa poche). Anotasi (as grid, ukuran asosiatif, nama ruang + luas,
tag pintu, titik tinggi, garis potong) ditulis ulang sebagai entitas CADCraft. Detail 1:20 digambar di CADCraft dari
dimensi model. DATA SIMULASI untuk studi kasus portofolio. Draf, disetujui atas delegasi Defsa 22 Nov 2026.
Jalankan (satu lembar per proses):
  .venv\\Scripts\\python.exe skrip\\tahap7_gambar_ars.py --data | --ekspor | --lembar GA-04 | --pdf | --semua-cek
"""
from __future__ import annotations

import json
import math
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_beban as tb  # noqa: E402
import tahap7_telaah as tt  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "07 DED dan RKS"
GAMBAR = KELUAR / "Gambar"
DWG = GAMBAR / "DWG"
BIM = GAMBAR / "BIM"
PLOT = GAMBAR / "_plot"
PDF = KELUAR / "7.4 Gambar Arsitektur DED.pdf"
MD = KELUAR / "7.4 Gambar Arsitektur.md"
DATA = BIM / "_data.json"
BIMC = AKAR / "model" / "RSTB-ARS-T7-LOD300.bimc"
STATUS = "DRAF - DELEGASI 22 NOV 2026"
TANGGAL = "NOVEMBER 2026"
GRID_X, GRID_Y = tb.GRID_X, tb.GRID_Y
NAMA_X = [str(i + 1) for i in range(len(GRID_X))]
NAMA_Y = list("ABCDEFG")
LEVEL = dict(tb.LEVEL)
HALAMAN = 12.05
H_ROOM, H_TAG = 1.5, 1.2          # mm kertas
LEBAR_CEK = 0.95                  # lebar huruf (× tinggi) untuk uji tumpang; cad_cek memakai 0,90

# (nomor, nama berkas, skala dipakai) - skala usulan, disetujui atas delegasi Defsa 22 Nov 2026
LEMBAR = {
    "GA-01": ("Daftar Gambar", "-"),
    "GA-02": ("Rencana Tapak", "1:500"),
    "GA-03": ("Kunci Denah", "1:300"),
    "GA-04": ("Denah LT1 Barat", "1:250"),
    "GA-05": ("Denah LT1 Timur", "1:250"),
    "GA-06": ("Denah LT2 Barat", "1:250"),
    "GA-07": ("Denah LT2 Timur", "1:250"),
    "GA-08": ("Denah LT3 Barat", "1:250"),
    "GA-09": ("Denah LT3 Timur", "1:250"),
    "GA-10": ("Denah LT4-LT6 Tipikal", "1:300"),
    "GA-11": ("Denah Atap", "1:300"),
    "GA-12": ("Denah Plafon LT1-LT3", "1:750"),
    "GA-13": ("Tampak Selatan Utara", "1:500"),
    "GA-14": ("Tampak Barat Timur", "1:400"),
    "GA-15": ("Potongan A-A B-B", "1:400"),
    "GA-16": ("Detail Fasad", "1:25"),
    "GA-17": ("Detail Overstek Mahkota", "1:50"),
    "GA-18": ("Detail Tangga Lift", "1:100"),
    "GA-19": ("Detail Toilet", "1:30"),
    "GA-20": ("Detail Kanopi Ramp IGD", "1:150"),
    "GA-21": ("Daftar Pintu Jendela", "-"),
    "GA-22": ("Daftar Finishing Ruang", "-"),
    "GA-23": ("Gedung Utilitas Parkir", "1:300"),
}
JUDUL = {n: j for n, j, *_ in tt.GA}
GU = (100.0, 44.0, 134.0, 76.0)
Y_POT_A, X_POT_B = 35.0, 68.0
PODIUM = tb.PODIUM.bounds
MENARA = tb.MENARA.bounds


def idn(x, n=1):
    return f"{x:,.{n}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def nberkas(no):
    return DWG / f"{no} {LEMBAR[no][0]}.dwg"


def kode_pintu(w, h):
    return {(900, 2100): "P1", (1200, 2100): "P2", (1500, 2100): "P3"}.get((round(w), round(h)),
                                                                          "PL" if round(h) == 2400 else f"P{round(w)}")


# ------------------------------------------------------------------ data model (BIMCraft) dan ekspor DXF
def ambil_data():
    from bimcraft import Sesi
    with Sesi(BIMC) as b:
        lv = {e["guid"]: e["name"] for e in b.alat("query_elements", {"category": "level"})["elements"]}
        q = lambda c: b.alat("query_elements", {"category": c, "limit": 3000})["elements"]  # noqa: E731
        rooms, doors, walls, ceil = q("room"), q("door"), q("wall"), q("ceiling")
        d = {"rooms": [{"id": r["id"], "lv": lv.get(r["level"]), "nama": r["name"], "no": r["number"],
                        "A": r["area_m2"], "p": r["point"], "typ": r["type"], "pr": r["params"]} for r in rooms],
             "doors": [{"id": r["id"], "lv": lv.get(r["level"]), "at": r["at"], "w": r["width"], "h": r["height"],
                        "typ": r["type"], "fam": r.get("family"), "op": r.get("operation")} for r in doors],
             "walls": [{"typ": r["type"], "lv": lv.get(r["level"]), "L": r["length"], "h": r["height"],
                        "t": r["thickness"], "s": r["start"], "e": r["end"], "b": r["base_offset"]}
                       for r in walls if r["type"].startswith(("FS-", "PG-", "DL-", "DT-"))],
             "tipe_dinding": sorted({r["type"] for r in walls}),
             "ceil": [{"lv": lv.get(r["level"]), "b": r["boundary"], "typ": r["type"], "off": r["offset"],
                       "A": r["area_m2"]} for r in ceil if r.get("boundary")],
             "levels": {e["name"]: e["elevation"] for e in b.alat("query_elements", {"category": "level"})["elements"]},
             "jumlah": {"ruang": len(rooms), "pintu": len(doors)}}
    BIM.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return d


def data():
    if not DATA.exists():
        return ambil_data()
    return json.loads(DATA.read_text(encoding="utf-8"))


def dxf(nama):
    return BIM / f"RSTB-ARS-T7 {nama}.dxf"


# potongan/tampak: (nama view, awal, akhir, kedalaman) mm. x DXF = jarak dari awal; y DXF = elevasi mm
VIEW = {
    "TS": ([0, 10000], [150000, 10000], 110000),            # tampak selatan (pandang ke utara)
    "TU": ([150000, 100000], [0, 100000], 110000),          # tampak utara (pandang ke selatan)
    "TB": ([0, 100000], [0, 0], 140000),                    # tampak barat (pandang ke timur): x DXF = 100000 - y
    "TT": ([150000, 0], [150000, 100000], 140000),          # tampak timur (pandang ke barat): x DXF = y
    "AA": ([0, Y_POT_A * 1000], [150000, Y_POT_A * 1000], 20000),
    "BB": ([X_POT_B * 1000, 85000], [X_POT_B * 1000, 15000], 20000),   # pandang ke timur: x DXF = 85000 - y
}
BUANG_LAYER = {"grid", "level", "section", "tag", "room", "roomseparator"}


def ekspor_bim():
    from bimcraft import GalatBIM, Sesi
    BIM.mkdir(parents=True, exist_ok=True)
    with Sesi(BIMC) as b:
        for lv in ("LT1", "LT2", "LT3", "LT4", "LT5", "LT6", "ATAP"):
            b.cmd("export", {"format": "dxf", "view": lv, "path": str(dxf(f"Denah {lv}")), "overwrite": True})
        for nama, (p1, p2, dalam) in VIEW.items():
            try:
                b.cmd("section", {"start": p1, "end": p2, "depth": dalam, "name": f"GA {nama}"})
            except GalatBIM as e:
                if "already named" not in str(e):
                    raise
            b.cmd("export", {"format": "dxf", "view": f"GA {nama}", "path": str(dxf(nama)), "overwrite": True})
        b.simpan(BIMC)


def siapkan_dxf(src, dst, kotak=None, dalam=False, geser=(0.0, 0.0), buang_kotak=(), kecil_pintu=300.0, contorno=False):
    """Bersihkan DXF BIMCraft: buang anotasi BIM, goresan teks, poche (HATCH), pintu kecil; potong ke `kotak` (mm);
    geser (m). buang_kotak: kotak (mm) yang membuang entitas yang seluruhnya di dalamnya."""
    import ezdxf
    from ezdxf import bbox
    doc = ezdxf.readfile(str(src))
    ms = doc.modelspace()
    for e in list(ms):
        ly, tp = e.dxf.layer, e.dxftype()
        b = bbox.extents([e])
        hapus = ly in BUANG_LAYER or (tp == "HATCH" and not contorno) or not b.has_data
        if not hapus:
            ukuran = max(b.size.x, b.size.y)
            if ly == "door" and ukuran < kecil_pintu:
                hapus = True
            elif ly in ("wall", "floor") and tp in ("LINE", "LWPOLYLINE") and ukuran < 300.0 and tp == "LINE" and ukuran < 100.0:
                hapus = True
            elif kotak:
                if dalam:
                    hapus = not (b.extmin.x >= kotak[0] and b.extmax.x <= kotak[2] and b.extmin.y >= kotak[1]
                                 and b.extmax.y <= kotak[3])
                else:
                    hapus = not (b.extmax.x >= kotak[0] and b.extmin.x <= kotak[2] and b.extmax.y >= kotak[1]
                                 and b.extmin.y <= kotak[3])
            if not hapus:
                for k in buang_kotak:
                    if b.extmin.x >= k[0] and b.extmax.x <= k[2] and b.extmin.y >= k[1] and b.extmax.y <= k[3]:
                        hapus = True
                        break
        if not hapus and tp == "HATCH":   # tampak/potongan: isian jadi garis tepi (tanpa poche pejal)
            from ezdxf import path as ezpath
            for sub in ezpath.make_path(e).sub_paths():
                pts = [(v.x, v.y) for v in sub.flattening(8)]
                if len(pts) > 1:
                    pl = ms.add_lwpolyline(pts, close=True, dxfattribs={"layer": ly})
                    if geser[0] or geser[1]:
                        pl.translate(geser[0] * 1000, geser[1] * 1000, 0)
            ms.delete_entity(e)
        elif hapus:
            ms.delete_entity(e)
        elif geser[0] or geser[1]:
            e.translate(geser[0] * 1000, geser[1] * 1000, 0)
    doc.saveas(str(dst))
    return len(ms)


# ------------------------------------------------------------------ tata letak teks tanpa tumpang tindih
class Tata:
    """Penempatan teks di model space (m) dengan daftar kotak terpakai; `dx, dy`: geser tempat gambar."""

    def __init__(self, g, dx=0.0, dy=0.0):
        self.g, self.dx, self.dy, self.kotak = g, dx, dy, []
        self.gagal = []

    def _kotak(self, at, s, h, j="MC", rot=0):
        hm = h * self.g.skala / 1000
        w = LEBAR_CEK * hm * len(s)
        x, y = at
        if rot == 90:
            w, hm = hm, w
        if j == "MC":
            return (x - w / 2, y - hm / 2, x + w / 2, y + hm / 2)
        if j == "L":
            return (x, y, x + w, y + hm)
        if j == "BC":
            return (x - w / 2, y, x + w / 2, y + hm)
        return (x, y, x + w, y + hm)

    @staticmethod
    def _tumpang(a, b):
        return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

    def _s(self, k):
        return (k[0] + self.dx, k[1] + self.dy, k[2] + self.dx, k[3] + self.dy)

    def bebas(self, k):
        k = self._s(k)
        return not any(self._tumpang(k, o) for o in self.kotak)

    def tahan(self, k):
        self.kotak.append(self._s(k))

    def teks(self, at, s, layer, h, j="MC", rot=0, tebal=False, coba=((0, 0),)):
        for ox, oy in coba:
            p = (at[0] + ox, at[1] + oy)
            k = self._kotak(p, s, h, j, rot)
            if self.bebas(k):
                self.kotak.append(self._s(k))
                self.g.teks((p[0] + self.dx, p[1] + self.dy), s, layer, h, j=j, rot=rot, tebal=tebal)
                return True
        self.gagal.append(s)
        return False

    def blok(self, at, baris, layer, h, coba, tebal_pertama=False):
        """Beberapa baris teks rata tengah sebagai satu kesatuan; geser seluruh blok bila bertumpuk."""
        hm = h * self.g.skala / 1000
        n = len(baris)
        for ox, oy in coba:
            cx, cy = at[0] + ox, at[1] + oy
            ks = []
            for i, s in enumerate(baris):
                y = cy + ((n - 1) / 2 - i) * hm * 1.25
                ks.append((self._kotak((cx, y), s, h), (cx, y), s))
            if all(self.bebas(k) for k, _, _ in ks):
                for i, (k, p, s) in enumerate(ks):
                    self.kotak.append(self._s(k))
                    self.g.teks((p[0] + self.dx, p[1] + self.dy), s, layer, h, j="MC",
                                tebal=(tebal_pertama and i == 0))
                return True
        self.gagal.append(baris[0])
        return False


COBA_RUANG = [(0, 0), (0, 0.6), (0, -0.6), (0.9, 0), (-0.9, 0), (0.9, 0.7), (-0.9, 0.7), (0.9, -0.7), (-0.9, -0.7),
              (1.6, 0), (-1.6, 0), (0, 1.2), (0, -1.2)]
COBA_TAG = [(0.5, 0.5), (-0.5, 0.5), (0.5, -0.5), (-0.5, -0.5), (0, 0.9), (0, -0.9), (0.9, 0), (-0.9, 0), (0.9, 0.9)]


def bagi(nama, maks):
    return textwrap.wrap(nama, maks) or [nama]


def label_ruang(t, rooms, win, penuh=True):
    """Nama + luas tiap ruang di dalam `win` (x0, y0, x1, y1 m). Ruang kecil: nomor saja bila nama tidak muat."""
    lewat = 0
    for r in sorted(rooms, key=lambda r: -r["A"]):
        x, y = r["p"][0] / 1000, r["p"][1] / 1000
        if not (win[0] <= x <= win[2] and win[1] <= y <= win[3]):
            continue
        sk = t.g.skala
        per_huruf = sk / 1000 * 0.62 * H_ROOM          # m per huruf
        maks = max(7, min(24, int(math.sqrt(r["A"]) * 1.15 / per_huruf)))
        baris = bagi(r["nama"], maks)[:3] + [f"{idn(r['A'])} m²"]
        if not t.blok((x, y), baris, "A-TEKS-RUANG", H_ROOM, COBA_RUANG):
            if not t.blok((x, y), [r["no"].split("-")[-1], f"{idn(r['A'], 0)} m²"], "A-TEKS-RUANG", H_ROOM, COBA_RUANG):
                lewat += 1
    return lewat


def tag_pintu(t, doors, win):
    n = 0
    for d in doors:
        x, y = d["at"][0] / 1000, d["at"][1] / 1000
        if win[0] <= x <= win[2] and win[1] <= y <= win[3]:
            if t.teks((x, y), kode_pintu(d["w"], d["h"]), "A-TEKS-PINTU", H_TAG, coba=COBA_TAG):
                n += 1
    return n


def as_denah(g, x_awal, x_akhir, y_awal, y_akhir, dx=0.0, dy=0.0, atas=True, kiri=True, ukuran=True, y_batas=None):
    """Gelembung as (potongan pendek di luar bangunan) + rantai ukuran + total, pada kotak as yang diberikan."""
    xs = [x for x in GRID_X if x_awal - 1e-6 <= x <= x_akhir + 1e-6]
    ys = [y for y in GRID_Y if y_awal - 1e-6 <= y <= y_akhir + 1e-6]
    P = lambda p: (p[0] + dx, p[1] + dy)  # noqa: E731
    top, bot = ys[-1], ys[0]
    left = xs[0]
    for x in xs:
        g.as_grid(NAMA_X[GRID_X.index(x)], P((x, top + 1.0)), P((x, top + 3.5)), r_kertas=3.0, dua_ujung=False)
    for y in ys:
        g.as_grid(NAMA_Y[GRID_Y.index(y)], P((left - 1.0, y)), P((left - 3.5, y)), r_kertas=3.0, dua_ujung=False)
    if ukuran:
        for a, b in zip(xs[:-1], xs[1:]):
            g.ukur(P((a, top + 7.0)), P((b, top + 7.0)), P(((a + b) / 2, top + 7.0)))
        if len(xs) > 2:
            g.ukur(P((xs[0], top + 9.5)), P((xs[-1], top + 9.5)), P(((xs[0] + xs[-1]) / 2, top + 9.5)))
        for a, b in zip(ys[:-1], ys[1:]):
            g.ukur(P((left - 7.0, a)), P((left - 7.0, b)), P((left - 7.0, (a + b) / 2)), rot=90)
        g.ukur(P((left - 9.5, ys[0])), P((left - 9.5, ys[-1])), P((left - 9.5, (ys[0] + ys[-1]) / 2)), rot=90)


def impor_plan(g, lv, kotak_m, dx=0.0, dy=0.0, dalam=False, buang_kotak=(), nama=None):
    import tahap4_gambar_ded as t4g
    k = tuple(v * 1000 for v in kotak_m)
    tmp = BIM / f"_siap {nama or lv}.dxf"
    siapkan_dxf(dxf(f"Denah {lv}"), tmp, kotak=k, dalam=dalam, geser=(dx, dy), buang_kotak=buang_kotak)
    n = t4g.impor(g, tmp)
    gaya_layer(g)
    return n


def gaya_layer(g):
    """Tebal garis imporan: dinding terpotong tebal, perabot dan arsir tipis."""
    for nama, tebal in (("wall", 0.5), ("floor", 0.18), ("door", 0.25), ("component", 0.13), ("railing", 0.18), ("ceiling", 0.13)):
        try:
            g.cmd("layer.set", {"name": nama, "lineweight": tebal})
        except Exception:
            pass


def titik_lantai(g, t, lv, at, dx=0.0, dy=0.0, teks=None):
    s = teks or f"+{idn(LEVEL[lv], 2)}"
    g.titik_tinggi((at[0] + dx, at[1] + dy), s, "A-ELEVASI")
    t.tahan(t._kotak((at[0] + 0.35, at[1] - 0.3), s, 1.6, "L"))


def garis_potong(g, t, a, b, nama, dx=0.0, dy=0.0):
    """Garis potong tebal-putus berujung huruf (dalam lingkaran) di luar tepi bangunan."""
    g.layer("A-POTONG", 7, 0.5, "PHANTOM")
    g.pline([(a[0] + dx, a[1] + dy), (b[0] + dx, b[1] + dy)], "A-POTONG")
    r = 1.1 * g.skala / 1000
    for p in (a, b):
        c = (p[0] + dx, p[1] + dy)
        g.cmd("circle", {"center": g.mm(c), "radius": r * 1000})
        g.teks(c, nama, "A-POTONG", 2.0, j="MC", tebal=True)
        t.tahan((p[0] - r, p[1] - r, p[0] + r, p[1] + r))


# ------------------------------------------------------------------ penutup lembar
def selesai(g, no, pusat, sub, catatan, kop=None, vp=None, utara=False, skala_g=None, judul=None):
    from cad_lembar import Gambar  # noqa: F401
    skala_t = LEMBAR[no][1]
    g.lembar(no, judul or JUDUL[no], skala_t, pusat=pusat,
             status=STATUS, tanggal=TANGGAL, subjudul=sub, catatan=catatan, judul_kop=kop or LEMBAR[no][0].upper(),
             vp=vp)
    if skala_g:
        g.skala_grafis(205, 22, skala_g[0], bagi=skala_g[1])
    if utara:
        g.panah_utara(318, 262, 10)
    PLOT.mkdir(parents=True, exist_ok=True)
    dwg = nberkas(no)
    g.simpan(dwg, PLOT / f"{dwg.stem}.pdf", GAMBAR / f"{dwg.stem}.png")
    return dwg


def tengah(win):
    return ((win[0] + win[2]) / 2, (win[1] + win[3]) / 2)


VP = ((24, 34), (331, 283))      # viewport tinggi penuh (di atas judul gambar)
LEG_DENAH = [("garis", "Dinding terpotong (model BIM)", {"tebal": 0.5}),
             ("garis", "Pintu dan ayunan daun", {"tebal": 0.25}),
             ("garis", "Perabot, kendaraan, pagar", {"tebal": 0.13}),
             ("garis", "As grid (potongan pendek)", {"garis": "CENTER", "tebal": 0.18}),
             ("garis", "Garis potong A-A / B-B", {"garis": "PHANTOM", "tebal": 0.5})]


def legenda(g, daftar):
    for jenis, ket, gaya in daftar:
        g.legenda_tambah(jenis, ket, **gaya)


# ------------------------------------------------------------------ denah GA-04..GA-09
def denah_setengah(no, lv, sisi):
    from cad_lembar import Gambar
    D = data()
    rooms = [r for r in D["rooms"] if r["lv"] == lv]
    doors = [d for d in D["doors"] if d["lv"] == lv]
    barat = sisi == "barat"
    xa, xb = (12.0, 44.0) if barat else (44.0, 84.0)
    kx0, kx1 = (xa - 1.0, 46.0) if barat else (42.0, 100.0 if lv == "LT1" else 86.0)
    win = (kx0, 24.0, kx1, 76.0)
    with Gambar(250) as g:
        impor_plan(g, lv, (kx0, 24.0, kx1, 79.0), nama=no)
        t = Tata(g)
        # tahan ruang untuk simbol sebelum label ruang
        as_denah(g, xa, xb, 27.0, 75.0)
        ay = Y_POT_A
        if lv in ("LT1", "LT2", "LT3"):
            if barat:
                garis_potong(g, t, (kx0 + 0.6, ay), (kx1 - 0.6, ay), "A")
            else:
                garis_potong(g, t, (kx0 + 0.6, ay), (xb + 2.0, ay), "A")
                garis_potong(g, t, (X_POT_B, 78.0), (X_POT_B, 24.8), "B")
        titik_lantai(g, t, lv, (kx0 + 1.5, 25.0))
        if lv == "LT1" and not barat:
            titik_lantai(g, t, lv, (89.0, 38.6), teks=f"HALAMAN +{idn(HALAMAN, 2)}")
            titik_lantai(g, t, lv, (95.5, 52.5), teks="RAMP +12,05 s.d. +12,85")
        n_tag = tag_pintu(t, doors, win)
        lewat = label_ruang(t, rooms, win)
        legenda(g, LEG_DENAH)
        g.legenda_tambah("garis", "Kode pintu P1, P2, P3, PL (GA-21)", tebal=0.13)
        nama_lt = f"{lv} {sisi}"
        cat = [f"Geometri dari view {lv} model BIMCraft RSTB-ARS-T7-LOD300; elevasi lantai +{idn(LEVEL[lv], 2)}, halaman +12,05.",
               "Luas ruang bersih dari model (partisi 100 mm [Asumsi]); daftar finishing di GA-22, pintu di GA-21.",
               f"Skala 1:250: 1:100 pada denah 72 x 48 m tidak muat A3 (butuh A1); dibagi barat (as 1-5) dan timur (as 5-10).",
               "Tag pintu: P1 0,9 x 2,1; P2 1,2 x 2,1; P3 1,5 x 2,1; PL 1,4 x 2,4 (pintu lift/rawat) m."]
        if lewat:
            cat.append(f"{lewat} ruang kecil tidak diberi label (tidak muat); lihat nomor di GA-22.")
        s = selesai(g, no, tengah((kx0 - 10, 20.0, kx1, 86.5)),
                    f"Langkah 7.4: view {lv} model ARS; bagian {sisi} (as {'1-5' if barat else '5-10'}).",
                    cat, vp=VP, utara=True, skala_g=(20, 4))
        return {"tag": n_tag, "label_gagal": t.gagal}


GA_DENAH = {"GA-04": ("LT1", "barat"), "GA-05": ("LT1", "timur"), "GA-06": ("LT2", "barat"), "GA-07": ("LT2", "timur"),
            "GA-08": ("LT3", "barat"), "GA-09": ("LT3", "timur")}


# ------------------------------------------------------------------ CLI
# ------------------------------------------------------------------ tabel di kertas (mm), GA-01/21/22
def tabel_kertas(g, x, y_atas, lebar, kepala, baris, h_teks=2.0, wrap=None, tebal_kepala=True):
    """Tabel garis di paper space. baris: list of list str. wrap: maks huruf per kolom (None = tanpa bungkus)."""
    g.layer("KERTAS-TEKS", 7, 0.25)
    wrap = wrap or [999] * len(lebar)
    isi = [[bagi(str(c), wrap[i]) for i, c in enumerate(r)] for r in baris]
    kep = [bagi(str(c), wrap[i]) for i, c in enumerate(kepala)]
    total = sum(lebar)
    yy = y_atas

    def garis(y):
        g.cmd("pline", {"vertices": [[x, y], [x + total, y]]})

    def baris_(cells, y, tebal=False):
        n = max(len(c) for c in cells)
        h = max(6.0, n * h_teks * 1.35 + 3.0)
        xx = x
        if tebal:
            g.cmd("style.current", {"name": "TNR_TEBAL"})
        for i, c in enumerate(cells):
            for k, s in enumerate(c):
                g.cmd("text", {"at": [xx + 1.5, y - 2.0 - h_teks - k * h_teks * 1.35 + 0.6], "text": s, "height": h_teks})
            xx += lebar[i]
        if tebal:
            g.cmd("style.current", {"name": "TNR"})
        return h
    garis(yy)
    yy -= baris_(kep, yy, True)
    garis(yy)
    for r in isi:
        yy -= baris_(r, yy)
    garis(yy)
    xx = x
    for w in lebar + [0]:
        g.cmd("pline", {"vertices": [[xx, y_atas], [xx, yy]]})
        xx += w
    return yy


def ga01():
    from cad_lembar import Gambar
    with Gambar(100) as g:
        legenda(g, [("garis", "Dinding terpotong", {"tebal": 0.5}), ("garis", "Pintu dan ayunan daun", {"tebal": 0.25}),
                    ("garis", "As grid", {"garis": "CENTER", "tebal": 0.18}), ("garis", "Garis potong", {"garis": "PHANTOM", "tebal": 0.5})])
        cat = ["Gambar ini bagian DED arsitektur 7.4 (A3, skala usulan, disetujui atas delegasi Defsa 22 Nov 2026).",
               "Satuan: ukuran gambar dalam m, elevasi terhadap datum lokal BM-1 = +10,000; lantai LT1 +12,85, halaman +12,05.",
               "Grid struktur modul 8 m: as 1-10 (timur-barat) dan A-G (selatan-utara); podium 72 x 48 m, menara 64 x 24 m.",
               "Geometri dari model BIMCraft RSTB-ARS-T7-LOD300 (LOD 300); finishing dan ukuran lain [Asumsi] ditandai.",
               "DATA SIMULASI untuk studi kasus portofolio, tidak untuk konstruksi."]
        g.lembar("GA-01", JUDUL["GA-01"], "-", pusat=None, status=STATUS, tanggal=TANGGAL, subjudul="Langkah 7.4",
                 catatan=cat, judul_kop="DAFTAR GAMBAR")
        g.cmd("style.current", {"name": "TNR"})
        baris = [[n, JUDUL[n], LEMBAR[n][1], "GA 7.4"] for n in LEMBAR]
        tabel_kertas(g, 28, 280, [18, 195, 22, 24], ["NO", "JUDUL GAMBAR", "SKALA", "BERKAS"], baris, 2.2)
        dwg = nberkas("GA-01")
        PLOT.mkdir(parents=True, exist_ok=True)
        g.simpan(dwg, PLOT / f"{dwg.stem}.pdf", GAMBAR / f"{dwg.stem}.png")
        return {}


# ------------------------------------------------------------------ GA-02 tapak, GA-03 kunci denah
def ga02():
    from cad_lembar import Gambar
    bk = [(12000, 27000, 84000, 75000), (GU[0] * 1000, GU[1] * 1000, GU[2] * 1000, GU[3] * 1000)]
    with Gambar(500) as g:
        impor_plan(g, "LT1", (-2, -12, 142, 94), buang_kotak=bk, nama="GA-02")
        t = Tata(g)
        g.layer("C-PERSIL", 7, 0.5, "PHANTOM")
        g.pline([(0, 0), (140, 0), (140, 90), (0, 90)], "C-PERSIL", tutup=True)
        g.layer("A-MASSA", 7, 0.7)
        g.pline([(PODIUM[0], PODIUM[1]), (PODIUM[2], PODIUM[1]), (PODIUM[2], PODIUM[3]), (PODIUM[0], PODIUM[3])], "A-MASSA", tutup=True)
        g.pline([(GU[0], GU[1]), (GU[2], GU[1]), (GU[2], GU[3]), (GU[0], GU[3])], "A-MASSA", tutup=True)
        g.layer("A-MENARA", 7, 0.35, "DASHED")
        g.pline([(MENARA[0], MENARA[1]), (MENARA[2], MENARA[1]), (MENARA[2], MENARA[3]), (MENARA[0], MENARA[3])], "A-MENARA", tutup=True)
        T = lambda p, s, rot=0, tb=False, h=2.0: t.teks(p, s, "C-TEKS", h, rot=rot, tebal=tb)  # noqa: E731
        T((48, 61), "RUMAH SAKIT: PODIUM LT1-LT3", tb=True)
        T((52, 39), "MENARA LT4-LT6 (GARIS PUTUS)")
        T((117, 60), "GEDUNG UTILITAS", tb=True)
        T((113, 23), "PARKIR MOBIL")
        T((4, 49), "PARKIR MOTOR P4 (76)", rot=90)
        T((53, 83.5), "KANOPI LOBI")
        T((88.3, 40), "DROP-OFF", h=1.6)
        T((101.5, 50), "RAMP IGD", rot=90, h=1.6)
        T((54, 92.5), "GERBANG UTAMA")
        T((95.5, 92.5), "GERBANG AMBULANS", h=1.6)
        T((70, -6), "SUNGAI BATANGHARI", tb=True)
        T((70, -2), "LERENG TEPI SUNGAI (PUNCAK +12,05)", h=1.6)
        g.titik_tinggi((70, 15), "HALAMAN +12,05", "C-TEKS")
        g.ukur((0, -9), (140, -9), (70, -9))
        g.ukur((-6, 0), (-6, 90), (-6, 45), rot=90)
        g.layer("C-TEKS", 7, 0.18)
        legenda(g, [("garis", "Batas persil", {"garis": "PHANTOM", "tebal": 0.5}), ("garis", "Massa bangunan LT1", {"tebal": 0.7}),
                    ("garis", "Menara di atas podium", {"garis": "DASHED", "tebal": 0.35}), ("garis", "Jalan, parkir, pagar, lanskap", {"tebal": 0.18})])
        cat = ["Tapak dari view LT1 model ARS; denah di dalam massa tidak digambar (lihat GA-04..09, GA-23).",
               "Persil 140 x 90 m (TOR 4.1); parkir motor P4 76 unit di sisi barat; keputusan 7.1.",
               "Puncak lereng +12,05; muka air sungai rata-rata bulanan dari data 3.1; skala 1:500."]
        selesai(g, "GA-02", (70, 41), "Langkah 7.4: tapak, parkir, akses, tebing, sungai.", cat, vp=VP, utara=True, skala_g=(50, 5))
        return {"gagal": t.gagal}


def ga03():
    from cad_lembar import Gambar
    with Gambar(300) as g:
        impor_plan(g, "LT1", (4, 20, 88, 86), nama="GA-03")
        t = Tata(g)
        as_denah(g, 12, 84, 27, 75, ukuran=False)
        g.ukur((12, 82), (84, 82), (48, 82))
        g.layer("A-ZONA", 7, 0.35, "DASHED")
        for no, (x0, x1) in (("GA-04", (12, 46)), ("GA-05", (42, 86))):
            g.pline([(x0, 24.5), (x1, 24.5), (x1, 77), (x0, 77)], "A-ZONA", tutup=True)
            t.teks(((x0 + x1) / 2, 22.8), no, "A-TEKS", 3.0, tebal=True)
        g.layer("A-POTONG", 7, 0.5, "PHANTOM")
        garis_potong(g, t, (6, Y_POT_A), (88, Y_POT_A), "A")
        garis_potong(g, t, (X_POT_B, 22), (X_POT_B, 86), "B")
        legenda(g, [("garis", "Dinding terpotong LT1", {"tebal": 0.5}), ("garis", "Zona lembar denah", {"garis": "DASHED", "tebal": 0.35}),
                    ("garis", "Garis potong A-A / B-B (GA-15)", {"garis": "PHANTOM", "tebal": 0.5})])
        cat = ["Kunci denah LT1; LT2 dan LT3 dibagi sama (GA-06..09), LT4-LT6 pada GA-10.",
               "Potongan A-A pada as B, B-B pada as 8 (sama dengan potongan struktur Tahap 4)."]
        selesai(g, "GA-03", (46, 53), "Langkah 7.4: kunci denah dan garis potong.", cat, vp=VP, utara=True, skala_g=(20, 4))
        return {}


# ------------------------------------------------------------------ GA-10 tipikal, GA-11 atap, GA-12 RCP, GA-23 utilitas
def ga10():
    from cad_lembar import Gambar
    D = data()
    with Gambar(300) as g:
        t = Tata(g)
        for lv, dy in (("LT4", 0.0), ("LT6", -40.0)):
            rooms = [r for r in D["rooms"] if r["lv"] == lv]
            doors = [d for d in D["doors"] if d["lv"] == lv]
            win = (18.0, 25.0, 86.0, 53.0)
            impor_plan(g, lv, win, dy=dy, dalam=True, nama=f"GA-10 {lv}")
            as_denah(g, 20, 84, 27, 51, dy=dy)
            t.dy = dy
            titik_lantai(g, t, lv, (19.0, 25.8), dy=dy)
            tag_pintu(t, doors, win)
            label_ruang(t, rooms, win)
            t.dy = 0.0
            g.teks((52, 23.3 + dy), f"DENAH {lv} (+{idn(LEVEL[lv], 2)})", "A-TEKS", 3.0, j="MC", tebal=True)
        legenda(g, LEG_DENAH[:4])
        cat = ["Menara 64 x 24 m, tinggi lantai 4,20 m: LT4 (atas) dan LT6 (bawah) digambar; LT5 mengikuti (37 ruang, tata sama).",
               "Skala 1:300 (1:150 tidak muat A3: 427 mm lebar); elevasi LT4 +26,05; LT5 +30,25; LT6 +34,45.",
               "Luas ruang bersih dari model; tag pintu P1, P2, P3, PL (GA-21); finishing GA-22."]
        selesai(g, "GA-10", (52, 22.3), "Langkah 7.4: view LT4 dan LT6 model ARS.", cat, vp=VP, utara=True, skala_g=(20, 4))
        return {"gagal": t.gagal}


def ga11():
    from cad_lembar import Gambar
    with Gambar(300) as g:
        tw = (MENARA[0] * 1000, MENARA[1] * 1000, MENARA[2] * 1000, MENARA[3] * 1000)
        impor_plan(g, "LT4", (10, 20, 90, 80), buang_kotak=[tw], nama="GA-11 a")
        impor_plan(g, "ATAP", (10, 20, 90, 80), nama="GA-11 b")
        t = Tata(g)
        as_denah(g, 12, 84, 27, 75, ukuran=False)
        g.ukur((12, 82), (84, 82), (48, 82))
        T = lambda p, s, tb=False, h=2.2: t.teks(p, s, "A-TEKS", h, tebal=tb)  # noqa: E731
        T((52, 39), "DEK HELIPAD (HELIDEK)", True)
        T((52, 60), "TAMAN ATAP V1 (PODIUM +26,05)", True)
        T((52, 45.5), "ATAP MENARA +38,65", False, 1.8)
        g.titik_tinggi((20.5, 54), "+26,05 ATAP PODIUM", "A-ELEVASI")
        g.titik_tinggi((20.5, 52.2), "+38,65 ATAP MENARA", "A-ELEVASI")
        legenda(g, [("garis", "Konstruksi atap (view ATAP)", {"tebal": 0.5}), ("garis", "Podium +26,05 (view LT4)", {"tebal": 0.25})])
        cat = ["Atap menara dari view ATAP, taman atap pada podium dari view LT4 (menara di-masking); skala 1:300 (1:100 tidak muat A3).",
               "Helideck dan taman atap V1 sesuai keputusan 7.1; kemiringan dan drainase atap [Asumsi, belum digambar]."]
        selesai(g, "GA-11", (50, 50), "Langkah 7.4: denah atap, taman atap, dek helipad.", cat, vp=VP, utara=True, skala_g=(20, 4))
        return {"gagal": t.gagal}


def ga12():
    from shapely.geometry import Polygon
    from cad_lembar import Gambar
    D = data()
    with Gambar(750) as g:
        t = Tata(g)
        pos = {"LT1": (0.0, 0.0), "LT2": (80.0, 0.0), "LT3": (0.0, -62.0)}
        win = (11.0, 26.0, 85.0, 76.0)
        for lv, (dx, dy) in pos.items():
            impor_plan(g, lv, win, dx=dx, dy=dy, dalam=True, nama=f"GA-12 {lv}")
            g.layer("A-PLAFON", 7, 0.25)
            t.dy, t.dx = dy, dx
            for c in (c for c in D["ceil"] if c["lv"] == lv):
                pts = [(p[0] / 1000 + dx, p[1] / 1000 + dy) for p in c["b"]]
                g.pline(pts, "A-PLAFON", tutup=True)
                cen = Polygon(c["b"]).representative_point()
                t.teks((cen.x / 1000, cen.y / 1000), f"{c['typ'].split('-')[-1][:6]} {idn(c['off'] / 1000, 2)}", "A-TEKS-PLAFON", 1.3,
                       coba=[(0, 0), (0, 1.2), (0, -1.2), (2, 0), (-2, 0), (2, 1.5), (-2, -1.5)])
            t.dx = t.dy = 0.0
            as_denah(g, 12, 84, 27, 75, dx=dx, dy=dy, ukuran=False)
            g.teks((48 + dx, 22.0 + dy), f"RCP {lv} (+{idn(LEVEL[lv], 2)})", "A-TEKS", 2.6, j="MC", tebal=True)
        legenda(g, [("garis", "Dinding terpotong", {"tebal": 0.25}), ("garis", "Batas plafon per ruang", {"tebal": 0.25})])
        cat = ["Batas plafon dan tinggi bawah plafon dari elemen plafon model (m di atas lantai); tipe PL-... (GA-22).",
               "Skala 1:750 agar tiga lantai muat satu A3 (1:200 butuh A1); titik lampu dan diffuser belum ada (MEP di Tahap 8)."]
        selesai(g, "GA-12", (82.0, 24.0), "Langkah 7.4: plafon LT1-LT3 dari elemen plafon model.", cat, vp=VP, skala_g=(50, 5))
        return {"gagal": t.gagal}


def ga23():
    from cad_lembar import Gambar
    D = data()
    with Gambar(300) as g:
        t = Tata(g)
        pos = {"LT1": (0.0, 0.0), "LT2": (46.0, 0.0), "LT3": (0.0, -43.0), "LT4": (46.0, -43.0)}
        for lv, (dx, dy) in pos.items():
            win = (GU[0] - 2, GU[1] - 2, GU[2] + 2, GU[3] + 2)
            ox = dx - GU[0] + 6
            impor_plan(g, lv, win, dx=ox, dy=dy, dalam=True, nama=f"GA-23 {lv}")
            g.ukur((GU[0] + ox, GU[1] - 3 + dy), (GU[2] + ox, GU[1] - 3 + dy), ((GU[0] + GU[2]) / 2 + ox, GU[1] - 3 + dy))
            g.ukur((GU[0] - 3 + ox, GU[1] + dy), (GU[0] - 3 + ox, GU[3] + dy), (GU[0] - 3 + ox, (GU[1] + GU[3]) / 2 + dy), rot=90)
            rooms = [r for r in D["rooms"] if r["lv"] == lv and GU[0] <= r["p"][0] / 1000 <= GU[2] and GU[1] <= r["p"][1] / 1000 <= GU[3]]
            t.dx, t.dy = ox, dy
            label_ruang(t, rooms, GU)
            t.dx = t.dy = 0.0
            g.teks((GU[0] + 17 + ox, GU[3] + 2.5 + dy), f"GEDUNG UTILITAS {lv} (+{idn(LEVEL[lv], 2)})", "A-TEKS", 2.4, j="MC", tebal=True)
        legenda(g, [("garis", "Dinding terpotong", {"tebal": 0.5}), ("garis", "Kendaraan, perabot", {"tebal": 0.13})])
        cat = ["Gedung utilitas 34 x 32 m (x 100-134, y 44-76): LT1-LT2 utilitas, LT3-LT4 parkir terbuka bertingkat.",
               "Skala 1:300 (1:200 empat lantai tidak muat A3); lokasi parkir mobil di tapak: GA-02."]
        selesai(g, "GA-23", (28, 28), "Langkah 7.4: gedung utilitas LT1-LT4 dan parkir.", cat, vp=VP, skala_g=(20, 4))
        return {"gagal": t.gagal}


# ------------------------------------------------------------------ GA-13..15 tampak dan potongan
LEVELS_T = [("LT1", 12.85), ("LT2", 17.35), ("LT3", 21.85), ("LT4", 26.05), ("LT5", 30.25), ("LT6", 34.45), ("ATAP", 38.65)]


def _along(key, w):
    return {"TS": w, "TU": 150 - w, "TB": 100 - w, "TT": w, "AA": w, "BB": 85 - w}[key]


def _muka(key, w):
    """True bila dinding fasad `w` menghadap pengamat pada view `key` (selatan, utara, barat, timur)."""
    sx, sy, ex, ey = w["s"][0] / 1000, w["s"][1] / 1000, w["e"][0] / 1000, w["e"][1] / 1000
    xm, ym = (sx + ex) / 2, (sy + ey) / 2
    hor, ver = abs(sy - ey) < 0.01, abs(sx - ex) < 0.01
    tinggi = w["lv"] in ("LT4", "LT5", "LT6", "ATAP")
    if xm > GU[0] - 5:   # gedung utilitas digambar terpisah di GA-23, jangan menutupi tampak gedung utama
        return False
    if key == "TS":
        return hor and ym < 45
    if key == "TU":
        return hor and (ym > 60 or (ym > 45 and tinggi))
    if key == "TB":
        return ver and xm < 50
    if key == "TT":
        return ver and xm > 50
    return False


def tampak_model(g, key, dy):
    """Tampak dari elemen dinding fasad model ARS (BIM view hanya memberi unsur terpotong): proyeksi tiap dinding
    ke bidang tampak, sebagai persegi panjang polyline per tipe (panel / kaca)."""
    n = 0
    for w in data()["walls"]:
        if not w["typ"].startswith("FS-") or not _muka(key, w):
            continue
        sx, sy, ex, ey = (v / 1000 for v in (*w["s"], *w["e"]))
        horiz = abs(sy - ey) < 0.01
        a, b = (_along(key, sx), _along(key, ex)) if horiz else (_along(key, sy), _along(key, ey))
        z0 = LEVEL[w["lv"]] + w["b"] / 1000
        z1 = z0 + w["h"] / 1000
        kaca = "Kaca" in w["typ"]
        ly = "A-FASAD-KACA" if kaca else "A-FASAD-PANEL"
        g.layer(ly, 7, 0.13 if kaca else 0.25)
        g.pline([(min(a, b), z0 + dy), (max(a, b), z0 + dy), (max(a, b), z1 + dy), (min(a, b), z1 + dy)], ly, tutup=True)
        n += 1
    g.layer("A-TANAH", 7, 0.7)
    return n


def blok_tampak(g, t, key, dy, x_awal, x_akhir, judul, bubbles, xmin, xmax):
    """Impor view, level/elevasi, gelembung as dan ukuran tinggi. xmin/xmax: x DXF (m) dari bangunan."""
    import tahap4_gambar_ded as t4g
    if key in ("TS", "TU", "TB", "TT"):
        tampak_model(g, key, dy)
        g.pline([(xmin - 4, HALAMAN + dy), (xmax + 4, HALAMAN + dy)], "A-TANAH")
    else:
        tmp = BIM / f"_siap {key} {dy:.0f}.dxf"
        siapkan_dxf(dxf(key), tmp, kotak=(x_awal * 1000, 5000, x_akhir * 1000, 44000), geser=(0.0, dy), contorno=True)
        t4g.impor(g, tmp)
        gaya_layer(g)
    g.layer("A-LEVEL", 7, 0.18, "CENTER")
    for nm, z in LEVELS_T:
        g.pline([(xmin - 6, z + dy), (xmax + 1, z + dy)], "A-LEVEL")
        g.titik_tinggi((xmin - 15, z + dy), f"{nm} +{idn(z, 2)}", "A-ELEVASI")
    g.titik_tinggi((xmin - 15, HALAMAN + dy - 2.0), f"HALAMAN +{idn(HALAMAN, 2)}", "A-ELEVASI")
    for nm, w in bubbles:
        x = _along(key, w)
        g.as_grid(nm, (x, 40.5 + dy), (x, 42.0 + dy), r_kertas=3.0, dua_ujung=False)
    g.ukur((xmax + 3, LEVEL["LT1"] + dy), (xmax + 3, LEVEL["ATAP"] + dy), (xmax + 3, (LEVEL["LT1"] + LEVEL["ATAP"]) / 2 + dy), rot=90)
    g.teks(((xmin + xmax) / 2, 6.0 + dy), judul, "A-TEKS", 3.0, j="MC", tebal=True)


GRID_NOMOR = [(NAMA_X[i], x) for i, x in enumerate(GRID_X)]
GRID_HURUF = [(NAMA_Y[i], y) for i, y in enumerate(GRID_Y)]


def _sheet_tampak(no, skala, pasangan, cat, sub, vp_pusat):
    from cad_lembar import Gambar
    with Gambar(skala) as g:
        t = Tata(g)
        for key, dy, judul, a, b, bub, xmin, xmax in pasangan:
            blok_tampak(g, t, key, dy, a, b, judul, bub, xmin, xmax)
        legenda(g, [("garis", "Garis luar dan bukaan (view BIM)", {"tebal": 0.25}), ("garis", "Level lantai", {"garis": "CENTER", "tebal": 0.18}),
                    ("garis", "As grid (gelembung)", {"tebal": 0.25})])
        selesai(g, no, vp_pusat, sub, cat, vp=VP)
        return {}


def ga13():
    cat = ["Tampak dari view section model ARS (tampak selatan pandang ke utara, utara pandang ke selatan); gedung utilitas ikut terlihat.",
           "Skala 1:500: 1:200 butuh A1 (podium 72 m = 360 mm). Finishing: panel putih menara, kaca biru, kaca pita, dinding tirai, papan nama RS (7.1).",
           "Tinggi lantai 4,50/4,50/4,20/4,20/4,20/4,20 m; atap +38,65."]
    return _sheet_tampak("GA-13", 500, [
        ("TS", 0.0, "TAMPAK SELATAN", 5, 138, GRID_NOMOR, 12, 84),
        ("TU", -52.0, "TAMPAK UTARA", 5, 138, GRID_NOMOR, 66, 138)],
        cat, "Langkah 7.4: tampak selatan dan utara.", (71.5, -4))


def ga14():
    cat = ["Tampak barat (pandang ke timur) dan timur (pandang ke barat) dari view section model ARS.",
           "Skala 1:400 (1:200 butuh A1). Gelembung A-G sesuai sisi pandang; elevasi level pada sisi kiri."]
    return _sheet_tampak("GA-14", 400, [
        ("TB", 0.0, "TAMPAK BARAT", 10, 80, GRID_HURUF, 25, 73),
        ("TT", -52.0, "TAMPAK TIMUR", 10, 80, GRID_HURUF, 27, 75)],
        cat, "Langkah 7.4: tampak barat dan timur.", (45, -4))


def ga15():
    cat = ["Potongan A-A (as B, y = 35 m, pandang utara) dan B-B (as 8, x = 68 m, pandang timur) dari view section model ARS (kedalaman 20 m).",
           "Beton tanpa poche pejal; hanya unsur terpotong dan terlihat dalam kedalaman 20 m yang tampil.",
           "Skala 1:400 (1:200 butuh A1)."]
    return _sheet_tampak("GA-15", 400, [
        ("AA", 0.0, "POTONGAN A-A", 8, 92, GRID_NOMOR, 12, 84),
        ("BB", -52.0, "POTONGAN B-B", 0, 70, GRID_HURUF, 10, 58)],
        cat, "Langkah 7.4: potongan A-A dan B-B.", (49, -4))


# ------------------------------------------------------------------ detail CAD (model space, m)
def kotak_(g, x0, z0, x1, z1, layer, pola=None, sk=1.0):
    pts = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    if pola:
        g.arsir(pts, layer, pola, sk)
    else:
        g.pline(pts, layer, tutup=True)


def ukur_v(g, x, z0, z1, xo):
    g.ukur((x, z0), (x, z1), (xo, (z0 + z1) / 2), rot=90)


def ukur_h(g, x0, x1, z, zo):
    g.ukur((x0, z), (x1, z), ((x0 + x1) / 2, zo))


def _detail(no, skala, isi, cat, sub, pusat, legenda_):
    from cad_lembar import Gambar
    with Gambar(skala) as g:
        t = Tata(g)
        isi(g, t)
        legenda(g, legenda_)
        selesai(g, no, pusat, sub, cat, vp=VP)
        return {"gagal": t.gagal}


LEG_DET = [("arsir", "Beton (garis tepi + arsir tipis)", {"pola": "ANSI31", "skala_pola": 0.5}),
           ("arsir", "Panel fasad", {"pola": "ANSI37", "skala_pola": 0.5}),
           ("garis", "Kaca (garis ganda)", {"tebal": 0.18})]


def ga16():
    """Detail fasad tipikal menara: lantai 4,20 m; panel 0-1,10, kaca pita 1,10-2,90, panel 2,90-lantai atas (model 7.1)."""
    def isi(g, t):
        for ly, w in (("S-BETON", 0.35), ("A-PANEL", 0.35), ("A-KACA", 0.18), ("A-TEKS", 0.18)):
            g.layer(ly, 7, w)
        h = 4.2
        kotak_(g, -1.2, -0.15, 0.6, 0.0, "S-BETON", "ANSI31", 0.5)            # pelat lantai bawah [Asumsi 150 mm]
        kotak_(g, -1.2, h - 0.15, 0.6, h, "S-BETON", "ANSI31", 0.5)           # pelat lantai atas
        kotak_(g, 0.3, h - 0.65, 0.6, h - 0.15, "S-BETON", "ANSI31", 0.5)     # balok tepi 300 x 500 [Asumsi]
        kotak_(g, 0.6, 0.0, 0.65, 1.1, "A-PANEL", "ANSI37", 0.5)              # panel bawah 50 mm
        kotak_(g, 0.6, 2.9, 0.65, h - 0.15, "A-PANEL", "ANSI37", 0.5)         # panel atas
        g.pline([(0.6, 1.1), (0.6, 2.9)], "A-KACA")                            # kaca pita 30 mm
        g.pline([(0.63, 1.1), (0.63, 2.9)], "A-KACA")
        kotak_(g, 0.6, 1.05, 0.66, 1.1, "A-PANEL")                             # bingkai alumunium [Asumsi]
        kotak_(g, 0.6, 2.9, 0.66, 2.95, "A-PANEL")
        g.pline([(-1.2, 0.0), (0.3, 0.0)], "S-BETON")
        g.pline([(-1.2, h - 0.15), (0.3, h - 0.15)], "S-BETON")
        ukur_v(g, 1.4, 0.0, 1.1, 1.9)
        ukur_v(g, 1.4, 1.1, 2.9, 1.9)
        ukur_v(g, 1.4, 2.9, h, 1.9)
        ukur_v(g, 2.6, 0.0, h, 3.1)
        ukur_h(g, 0.0, 0.65, -0.5, -0.9)
        g.tunjuk((0.65, 0.5), (2.9, 0.3), "PANEL FASAD 50 mm", "A-TEKS")
        g.tunjuk((0.63, 2.0), (2.9, 1.8), "KACA PITA 30 mm", "A-TEKS")
        g.tunjuk((0.4, h - 0.4), (-2.4, h - 0.9), "BALOK TEPI 300 x 500", "A-TEKS")
        g.tunjuk((-0.5, h - 0.07), (-2.4, h + 0.4), "PELAT LANTAI 150", "A-TEKS")
        g.titik_tinggi((-3.0, 0.0), "+26,05 (LT4)", "A-ELEVASI")
        g.titik_tinggi((-3.0, h), "+30,25 (LT5)", "A-ELEVASI")
    cat = ["Potongan fasad tipikal menara (LT4-LT6, lantai 4,20 m): panel 0-1,10 m, kaca pita 1,10-2,90 m, panel atas; tebal panel 50 mm, kaca 30 mm (tipe dinding model 7.1).",
           "Tebal pelat 150, balok tepi 300 x 500, bingkai: [Asumsi], mengikuti pradimensi struktur Tahap 3-4; angkur dan sealant belum didetailkan.",
           "Podium memakai panel abu dengan pembagian sama; dinding tirai tengah menara kaca biru penuh tinggi lantai."]
    return _detail("GA-16", 25, isi, cat, "Langkah 7.4: detail dari dimensi model.", (0.3, 1.3), LEG_DET)


def ga17():
    """Detail overstek podium (konsol 0,9 m, +3,60..+3,90 di atas LT1) dan mahkota menara (parapet 1,8 m di atas ATAP)."""
    def isi(g, t):
        for ly, w in (("S-BETON", 0.35), ("A-PANEL", 0.35), ("A-TEKS", 0.18)):
            g.layer(ly, 7, w)
        kotak_(g, -0.6, -0.15, 0.5, 0.0, "S-BETON", "ANSI31", 1.0)                 # pelat LT1 (+12,85)
        kotak_(g, 0.5, 0.0, 0.55, 4.5, "A-PANEL", "ANSI37", 1.0)                   # dinding panel abu podium
        kotak_(g, -0.6, 4.35, 0.5, 4.5, "S-BETON", "ANSI31", 1.0)                  # pelat LT2
        kotak_(g, 0.55, 3.6, 1.45, 3.9, "S-BETON", "ANSI31", 1.0)                  # konsol overstek 0,9 m
        ukur_h(g, 0.55, 1.45, 3.3, 3.0)
        ukur_v(g, 1.9, 3.6, 3.9, 2.3)
        ukur_v(g, 2.8, 0.0, 3.6, 3.2)
        g.tunjuk((1.0, 3.9), (1.2, 5.4), "KONSOL OVERSTEK PODIUM", "A-TEKS")
        g.tunjuk((0.52, 2.0), (-1.0, 2.6), "PANEL ABU 50 mm", "A-TEKS")
        g.titik_tinggi((-3.0, 0.0), "+12,85 (LT1)", "A-ELEVASI")
        g.titik_tinggi((-3.0, 3.75), "+16,60 s.d. +16,75 KONSOL", "A-ELEVASI")
        g.pline([(-3.2, 0.0), (0.0, 0.0)], "A-TEKS")
        g.pline([(-3.2, 3.75), (0.55, 3.75)], "A-TEKS")
        x0 = 8.0                                                                    # mahkota menara
        kotak_(g, x0 - 0.8, -0.15, x0 + 0.3, 0.0, "S-BETON", "ANSI31", 1.0)       # pelat atap +38,65 [Asumsi 150]
        kotak_(g, x0 + 0.3, 0.0, x0 + 0.35, 1.8, "A-PANEL", "ANSI37", 1.0)        # parapet panel putih 1,8 m
        ukur_v(g, x0 + 1.2, 0.0, 1.8, x0 + 1.6)
        g.tunjuk((x0 + 0.33, 0.9), (x0 + 2.0, 2.4), "PARAPET PANEL PUTIH H 1,80", "A-TEKS")
        g.tunjuk((x0 - 0.3, -0.07), (x0 - 1.5, -1.0), "PELAT ATAP", "A-TEKS")
        g.titik_tinggi((x0 - 3.2, 0.0), "+38,65 (ATAP)", "A-ELEVASI")
        g.pline([(x0 - 3.4, 0.0), (x0 - 0.8, 0.0)], "A-TEKS")
        t.teks((x0 + 1.0, -2.2), "MAHKOTA MENARA", "A-TEKS", 2.5, tebal=True)
        t.teks((-0.2, -2.2), "OVERSTEK PODIUM", "A-TEKS", 2.5, tebal=True)
    cat = ["Overstek podium: konsol lebar 0,90 m, tebal 0,30 m (+3,60 s.d. +3,90 di atas LT1) di sisi utara dan selatan podium (model 7.1; tebal dari selisih OVERSTEK).",
           "Mahkota menara: parapet panel putih setinggi 1,80 m di atas ATAP +38,65; huruf nama RS dan logo H dipasang pada parapet.",
           "Skala 1:50 agar kedua detail muat satu A3 (1:20 butuh dua lembar). Tebal pelat 150 mm [Asumsi]; angkur panel dan flashing belum didetailkan."]
    return _detail("GA-17", 50, isi, cat, "Langkah 7.4: detail dari dimensi model.", (4.0, 2.0), LEG_DET)


def ga18():
    from cad_lembar import Gambar
    import tahap7_arsitektur as ar
    D = data()
    with Gambar(100) as g:
        t = Tata(g)
        inti = {n: (j, o, d) for n, j, o, d in ar.inti_lantai("LT2")}
        stair, lift = inti["Tangga x22 y39"][1], inti["Inti lif x50-58 y35-43"][1]
        plac = [("TANGGA DARURAT x22 y39", stair, 0.0), ("INTI LIFT x50-58 y35-43", lift, -16.0)]
        for nama, poli, ox in plac:
            b = poli.bounds
            win = (b[0] - 3, b[1] - 3, b[2] + 3, b[3] + 3)
            impor_plan(g, "LT2", win, dx=ox, dalam=True, nama=f"GA-18 {nama[:6]}")
            g.ukur((b[0] + ox, b[1] - 1.5), (b[2] + ox, b[1] - 1.5), ((b[0] + b[2]) / 2 + ox, b[1] - 1.5))
            g.ukur((b[0] - 1.5 + ox, b[1]), (b[0] - 1.5 + ox, b[3]), (b[0] - 1.5 + ox, (b[1] + b[3]) / 2), rot=90)
            t.dx = ox
            rooms = [r for r in D["rooms"] if r["lv"] == "LT2" and b[0] <= r["p"][0] / 1000 <= b[2] and b[1] <= r["p"][1] / 1000 <= b[3]]
            label_ruang(t, rooms, win)
            t.teks(((b[0] + b[2]) / 2, b[1] - 3.2), nama, "A-TEKS", 2.2, tebal=True)
            t.dx = 0.0
        legenda(g, [("garis", "Dinding inti terpotong (STR 7.2)", {"tebal": 0.5}), ("garis", "Pintu dan ayunan", {"tebal": 0.25})])
        cat = ["Denah LT2 inti tangga darurat (4,35 x 6,35 m) dan inti lift (8,35 x 8,35 m) dari view LT2 model ARS; anak tangga dan kereta lift tidak dimodelkan di ARS (ada di model STR).",
               "Skala 1:100 (1:50 untuk dua inti dalam satu A3 tidak muat); potongan tangga: lihat GA-15 dan GS tahap 4-5."]
        selesai(g, "GA-18", (9.0, 39.0), "Langkah 7.4: denah inti tangga dan lift.", cat, vp=VP, skala_g=(10, 5))
        return {"gagal": t.gagal}


def ga19():
    def isi(g, t):
        for ly, w in (("A-DINDING", 0.5), ("A-FIXTURE", 0.25), ("A-TEKS", 0.18)):
            g.layer(ly, 7, w)
        # toilet umum tipikal (model: ruang 4,4 x 4,75 m, partisi 100)
        kotak_(g, 0, 0, 4.4, 4.75, "A-DINDING")
        for i in range(3):       # tiga bilik kloset 1,0 x 1,5
            x = 0.1 + i * 1.1
            kotak_(g, x, 3.15, x + 1.0, 4.65, "A-FIXTURE")
            kotak_(g, x + 0.3, 4.05, x + 0.7, 4.6, "A-FIXTURE")
            g.pline([(x + 0.1, 3.15), (x + 0.9, 3.15)], "A-FIXTURE")
        for k in range(2):       # wastafel
            kotak_(g, 0.4 + k * 1.0, 0.2, 0.9 + k * 1.0, 0.7, "A-FIXTURE")
        ukur_h(g, 0, 4.4, -0.6, -1.1)
        ukur_v(g, -0.5, 0, 4.75, -1.0)
        t.teks((2.2, 2.0), "TOILET UMUM (TIPIKAL)", "A-TEKS", 2.0, tebal=True)
        t.teks((2.2, 1.4), "3 BILIK 1,0 x 1,5 m + 2 WASTAFEL", "A-TEKS", 1.6)
        # toilet difabel
        ox = 7.0
        kotak_(g, ox, 0, ox + 2.4, 2.4, "A-DINDING")
        kotak_(g, ox + 1.8, 1.6, ox + 2.3, 2.3, "A-FIXTURE")
        kotak_(g, ox + 0.1, 0.1, ox + 0.6, 0.6, "A-FIXTURE")
        g.pline([(ox + 1.5, 2.4 - 0.05), (ox + 1.5, 1.5)], "A-FIXTURE")
        g.pline([(ox + 2.35, 1.4), (ox + 2.35, 2.3)], "A-FIXTURE")
        g.cmd("circle", {"center": g.mm((ox + 1.0, 1.2)), "radius": 750})
        ukur_h(g, ox, ox + 2.4, -0.6, -1.1)
        ukur_v(g, ox - 0.5, 0, 2.4, ox - 1.0)
        t.teks((ox + 1.2, 3.1), "TOILET DIFABEL", "A-TEKS", 2.0, tebal=True)
        t.teks((ox + 1.2, 2.7), "RUANG PUTAR D 1,50 m", "A-TEKS", 1.6)
    cat = ["Toilet umum tipikal mengikuti ruang toilet model (20,9 m2); toilet difabel 2,4 x 2,4 m dengan ruang putar kursi roda D 1,50 m dan batang pegangan.",
           "Dimensi bilik dan fixture [Asumsi]: pedoman toilet difabel (Permen PUPR 14/2017) belum ada di acuan/; fixture belum dimodelkan di ARS (lingkup 7.1).",
           "Skala 1:30 (satu A3 memuat kedua toilet; 1:20 tidak muat). Tampak dinding dan detail keramik belum digambar."]
    return _detail("GA-19", 30, isi, cat, "Langkah 7.4: detail toilet dari ruang model.", (5.5, 1.8),
                   [("garis", "Dinding", {"tebal": 0.5}), ("garis", "Fixture (kloset, wastafel, pegangan)", {"tebal": 0.25})])


def ga20():
    import tahap7_arsitektur as ar
    from cad_lembar import Gambar
    win = (82.0, 32.0, 100.0, 58.0)
    with Gambar(150) as g:
        t = Tata(g)
        impor_plan(g, "LT1", win, nama="GA-20")
        kan = (ar.DROPOFF[0], ar.DROPOFF[1], ar.APRON[2], ar.APRON[3])
        g.layer("A-KANOPI", 7, 0.25, "DASHED")
        for r in (kan, ar.RAMP_IGD):
            g.pline([(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])], "A-KANOPI", tutup=True)
        t.teks((88.3, 40.0), "DROP-OFF + APRON (KANOPI +17,25)", "A-TEKS", 1.6, tebal=True)
        t.teks((96.9, 50.0), "RAMP IGD 8,33 %", "A-TEKS", 1.6, rot=90, tebal=True)
        g.titik_tinggi((89.0, 36.0), "+12,85", "A-ELEVASI")
        g.titik_tinggi((95.5, 54.3), "+12,05", "A-ELEVASI")
        g.ukur((ar.RAMP_IGD[0], 56.5), (ar.RAMP_IGD[2], 56.5), (95.5, 56.5))
        g.ukur((101.0, ar.RAMP_IGD[1]), (101.0, ar.RAMP_IGD[3]), (101.0, 50.2), rot=90)
        # profil ramp (sumbu mendatar = jarak dari kaki ramp y 55 ke apron y 45,4)
        px, pz = 103.0, 36.0
        g.layer("A-PROFIL", 7, 0.5)
        g.pline([(px, pz), (px + 9.6, pz + 0.8), (px + 9.6 + 3.0, pz + 0.8)], "A-PROFIL")
        g.pline([(px - 1.5, pz), (px, pz)], "A-PROFIL")
        g.pline([(px + 9.6 + 3.0, pz + 0.8), (px + 9.6 + 3.0, pz + 0.8 + 4.4)], "A-PROFIL")
        g.layer("A-KANOPI", 7, 0.25, "DASHED")
        g.pline([(px + 6.0, pz + 0.8 + 4.4), (px + 12.6, pz + 0.8 + 4.4)], "A-KANOPI")
        g.ukur((px, pz - 0.6), (px + 9.6, pz - 0.6), (px + 4.8, pz - 0.6))
        g.ukur((px + 9.6, pz), (px + 9.6, pz + 0.8), (px + 10.4, pz + 0.4), rot=90)
        t.teks((px + 4.8, pz + 3.5), "PROFIL RAMP (JARAK 9,60 m; NAIK 0,80 m)", "A-TEKS", 1.6, tebal=True)
        t.teks((px + 9.0, pz + 5.8), "KANOPI +17,25", "A-TEKS", 1.4)
        legenda(g, [("garis", "Dinding, pagar, kolom terpotong", {"tebal": 0.5}), ("garis", "Batas kanopi dan ramp", {"garis": "DASHED", "tebal": 0.25}),
                    ("garis", "Profil ramp", {"tebal": 0.5})])
        cat = ["Kanopi drop-off + apron 80 m2 (+ pelataran) dan ramp IGD 9,6 m naik 0,8 m (8,33 %) dari halaman +12,05 ke lantai +12,85 (model 7.1); pelat kanopi 200 mm, tiang 300 mm.",
               "Skala 1:150: ramp 22 m (1:50 tidak muat A3); profil digambar pada skala sama di kanan denah. Kemiringan 8,33 % melebihi 1:12 untuk ramp difabel; ramp untuk brankar [Asumsi pedoman belum ada di acuan/]."]
        selesai(g, "GA-20", (98.5, 45.0), "Langkah 7.4: denah dan profil ramp IGD.", cat, vp=VP, utara=True, skala_g=(10, 5))
        return {"gagal": t.gagal}


# ------------------------------------------------------------------ daftar pintu/jendela dan finishing
def ga21():
    from cad_lembar import Gambar
    D = data()
    tipe = {}
    for d in D["doors"]:
        k = kode_pintu(d["w"], d["h"])
        r = tipe.setdefault(k, {"w": d["w"], "h": d["h"], "fam": d.get("fam") or "pintu lift/rawat", "per": {}})
        r["per"][d["lv"]] = r["per"].get(d["lv"], 0) + 1
    lv = ["LT1", "LT2", "LT3", "LT4", "LT5", "LT6"]
    baris = [[k, f"{idn(r['w'] / 1000, 2)} x {idn(r['h'] / 1000, 2)}", str(r["fam"])] + [str(r["per"].get(l, "-")) for l in lv] +
             [str(sum(r["per"].values()))] for k, r in sorted(tipe.items())]
    baris.append(["JUMLAH", "", ""] + [str(sum(r["per"].get(l, 0) for r in tipe.values())) for l in lv] + [str(len(D["doors"]))])
    kaca = {}
    for w in D["walls"]:
        if w["typ"] in ("FS-KacaPita", "FS-KacaBiru"):
            x = kaca.setdefault(w["typ"], {"n": 0, "L": 0.0, "A": 0.0, "h": w["h"]})
            x["n"] += 1
            x["L"] += w["L"]
            x["A"] += w["L"] * w["h"]
    jb = [[k, "pita setinggi 1,80 m (sill 1,10)" if "Pita" in k else "kaca tirai tinggi lantai", str(v["n"]), idn(v["L"] / 1000, 1),
           idn(v["A"] / 1e6, 1)] for k, v in sorted(kaca.items())]
    with Gambar(100) as g:
        legenda(g, [("garis", "Tabel pintu: dari elemen pintu model", {"tebal": 0.25})])
        cat = [f"{len(D['doors'])} pintu dari model ARS (224 pintu); kode P1-P3 pintu panel/ruang, PL pintu lift/rawat 1,4 x 2,4 m.",
               "Jendela: bukaan kaca fasad dimodelkan sebagai dinding kaca (FS-KacaPita, FS-KacaBiru); jendela interior tidak dimodelkan (lingkup 7.1).",
               "Merek, bahan daun/kusen dan hardware: lihat RKS 7.7 [Asumsi sebelum pemilihan produk]."]
        g.lembar("GA-21", JUDUL["GA-21"], "-", pusat=None, status=STATUS, tanggal=TANGGAL, subjudul="Langkah 7.4: dari model ARS",
                 catatan=cat, judul_kop="DAFTAR PINTU DAN JENDELA")
        g.cmd("style.current", {"name": "TNR"})
        yy = tabel_kertas(g, 28, 278, [16, 28, 50, 18, 18, 18, 18, 18, 18, 22],
                          ["KODE", "UKURAN (m)", "KELUARGA", "LT1", "LT2", "LT3", "LT4", "LT5", "LT6", "JUMLAH"], baris, 2.2)
        g.cmd("style.current", {"name": "TNR_TEBAL"})
        g.cmd("text", {"at": [28, yy - 8], "text": "BUKAAN KACA FASAD (JENDELA) DARI MODEL", "height": 2.6})
        g.cmd("style.current", {"name": "TNR"})
        tabel_kertas(g, 28, yy - 12, [40, 90, 40, 40, 40], ["TIPE DINDING", "KETERANGAN", "SEGMEN", "PANJANG (m)", "LUAS (m2)"], jb, 2.2)
        dwg = nberkas("GA-21")
        PLOT.mkdir(parents=True, exist_ok=True)
        g.simpan(dwg, PLOT / f"{dwg.stem}.pdf", GAMBAR / f"{dwg.stem}.png")
        return {"pintu": {k: sum(r["per"].values()) for k, r in tipe.items()}, "kaca": kaca}


def ga22():
    from cad_lembar import Gambar
    D = data()
    grup = {}
    for r in D["rooms"]:
        p = r["pr"]
        k = (p.get("RSTB_FinLantai", "-"), p.get("RSTB_FinDinding", "-"), p.get("RSTB_FinPlafon", "-"))
        x = grup.setdefault(k, {"n": 0, "A": 0.0, "z": set()})
        x["n"] += 1
        x["A"] += r["A"]
        x["z"].add(p.get("RSTB_Zona", "-"))
    baris = []
    for i, (k, v) in enumerate(sorted(grup.items(), key=lambda kv: -kv[1]["A"]), start=1):
        baris.append([f"F{i}", k[0].replace(" [Asumsi]", ""), k[1].replace(" [Asumsi]", ""), k[2].replace(" [Asumsi]", ""),
                      str(v["n"]), idn(v["A"], 1), ", ".join(sorted(v["z"]))[:60]])
    with Gambar(100) as g:
        cat = ["Finishing per kelompok ruang dari Pset RSTB (FinLantai, FinDinding, FinPlafon) pada elemen ruang model ARS; seluruh nilai [Asumsi] 7.1.",
               f"{len(D['rooms'])} ruang (termasuk gedung utilitas); luas bersih dari model. Spesifikasi bahan: RKS 7.7."]
        g.lembar("GA-22", JUDUL["GA-22"], "-", pusat=None, status=STATUS, tanggal=TANGGAL, subjudul="Langkah 7.4: dari Pset ruang model",
                 catatan=cat, judul_kop="DAFTAR FINISHING RUANG")
        g.cmd("style.current", {"name": "TNR"})
        tabel_kertas(g, 28, 280, [12, 56, 62, 46, 16, 22, 80],
                     ["KODE", "LANTAI", "DINDING", "PLAFON", "RUANG", "LUAS (m2)", "ZONA"], baris, 1.9, wrap=[99, 30, 34, 26, 99, 99, 44])
        dwg = nberkas("GA-22")
        PLOT.mkdir(parents=True, exist_ok=True)
        g.simpan(dwg, PLOT / f"{dwg.stem}.pdf", GAMBAR / f"{dwg.stem}.png")
        return {"kelompok": len(grup)}



# ------------------------------------------------------------------ pemeriksaan, PDF, T-114
def cek_semua():
    import cad_cek
    return {no: len(cad_cek.cek(str(nberkas(no)))) for no in LEMBAR if nberkas(no).exists()}


def gabung_pdf():
    from pypdf import PdfWriter
    w = PdfWriter()
    for no in LEMBAR:
        f = PLOT / f"{nberkas(no).stem}.pdf"
        if f.exists():
            w.append(str(f))
    w.write(str(PDF))
    return len(w.pages)


def t114():
    """T-114: nilai garis ukur asosiatif di DWG denah vs jarak as grid di IFC (batas 1 mm)."""
    import ifcopenshell
    from cadcraft import Sesi
    f = ifcopenshell.open(str(BIMC.with_suffix(".ifc")))
    pts = [[p.Coordinates for p in a.AxisCurve.Points] for a in f.by_type("IfcGridAxis")]
    xs = sorted({c[0][0] for c in pts if c[0][0] == c[1][0]})
    ys = sorted({c[0][1] for c in pts if c[0][1] == c[1][1]})
    selisih = sorted({abs(a - b) for L in (xs, ys) for a in L for b in L if a != b})
    hasil = []
    with Sesi() as c:
        for no in ("GA-03", "GA-04", "GA-05", "GA-10", "GA-11"):
            c.buka(str(nberkas(no)))
            c.cmd("layout.set", {"name": "Model"})
            ds = c.alat("query_entities", {"type": "Dimension", "limit": 5000}).get("entities", [])
            for d in ds:
                m = d.get("geometry", {}).get("measurement")
                if m is None:
                    continue
                ifc = min(selisih, key=lambda v: abs(v - m))
                hasil.append((no, round(m, 2), ifc, round(abs(m - ifc), 3)))
    return hasil, (xs, ys)


def jalankan(no):
    if no in GA_DENAH:
        return denah_setengah(no, *GA_DENAH[no])
    return globals()[no.lower().replace("-", "")]()


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--data" in a:
        print(ambil_data()["jumlah"])
    elif "--ekspor" in a:
        ekspor_bim()
    elif "--cek" in a:
        print(cek_semua())
    elif "--pdf" in a:
        print(gabung_pdf())
    elif "--t114" in a:
        h, _ = t114()
        print(len(h), max(x[3] for x in h), h[:6])
    elif "--semua" in a:
        for no in LEMBAR:
            print(no, jalankan(no), flush=True)
    elif "--lembar" in a:
        no = a[a.index("--lembar") + 1]
        print(no, jalankan(no))
