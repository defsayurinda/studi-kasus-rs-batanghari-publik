"""GS-21 Plot data owner di atas grid dan tapak (Tahap 5, langkah 5.0), digambar asli di CADCraft, ber-kop KOP_A3.

Isi: as grid 1-10 / A-G, massa gedung, gedung utilitas, jalur ambulans x 88-94 (sumbu 91, [Asumsi lebar]), zona P4,
batas persil dan sempadan sungai (tahap3_tapak), kotak alat per lantai (layer terpisah), lift dan pit, shaft/lubang,
isocenter MRI dengan lingkaran 12,0 / 8,0 / 1,0 m, dan garis ukur asosiatif jarak MRI-jalur serta tepi tangki-as 8.
Angka dibaca dari tahap5_telaah (data owner); koordinat dalam meter, model space 1 unit = 1 mm.
DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (20 Nov 2026); draf, menunggu persetujuan.
Jalankan: .venv\\Scripts\\python.exe skrip\\tahap5_gambar_plot.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from shapely.geometry import LineString, box

sys.path.insert(0, str(Path(__file__).parent))
import tahap5_telaah as tt  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "05 Struktur Tengah"
DWG = KELUAR / "Gambar" / "DWG" / "GS-21 Plot Data Owner.dwg"
PNG = KELUAR / "Gambar" / "GS-21 Plot Data Owner.png"
PDF = KELUAR / "5.0 Gambar Plot Data Owner.pdf"
SKALA = 500
TANGGAL = "NOVEMBER 2026"
H_LABEL = 1.8            # mm kertas
LEBAR_HURUF = 0.90       # faktor cad_cek (lebar huruf / tinggi)
GEDUNG = {  # garis massa (m) [Data Beban MEP Rinci, Umum; tahap4_beban]
    "podium": [(12, 27), (84, 27), (84, 75), (12, 75)],
    "menara": [(20, 27), (84, 27), (84, 51), (20, 51)],
    "v1": [(36, 51), (84, 51), (84, 75), (36, 75)],     # LT3 tidak dibangun (V1): atap podium utara +21,85
}
# layer per lantai: (nama, warna layar, tebal, jenis garis, keterangan legenda)
LAYER_LANTAI = {
    "LT1": ("M-LT1", 7, 0.35, "Continuous", "Alat LT1 +12,85"),
    "LT2": ("M-LT2", 7, 0.25, "DASHED", "Alat LT2 +17,35"),
    "LT3": ("M-LT3", 7, 0.25, "HIDDEN", "Alat LT3 ruang AHU +21,85"),
    "ATAP-PODIUM": ("M-ATAP-PODIUM", 7, 0.5, "DASHDOT", "Alat atap podium utara +21,85"),
    "ATAP-LT3": ("M-ATAP-LT3", 7, 0.35, "DOT", "Alat atap LT3 barat +26,05"),
    "MENARA": ("M-MENARA", 7, 0.25, "DIVIDE", "Alat menara (LT4-LT6, atap +38,65)"),
}
LABEL_TETAP = {"M-01": (73.0, 64.4), "M-06": (28.0, 49.3)}   # kotak besar/tumpang: label dipasang manual
SKIP = {"O-01", "O-02", "O-03", "R-09"}   # zona gantung/dinding timbal: terlalu lebar, tidak digambar


def lantai_kunci(it):
    s = it["lantai"]
    if it["lembar"] == "Lift":
        return "LIFT"
    if it["lembar"] == "Shaft dan Lubang":
        return "SHAFT"
    if s.startswith("Atap podium utara"):
        return "ATAP-PODIUM"
    if s.startswith("Atap LT3 barat"):
        return "ATAP-LT3"
    if s.startswith("Atap menara") or s.startswith("LT4"):
        return "MENARA"
    if s.startswith("LT3"):
        return "LT3"
    if s.startswith("LT2"):
        return "LT2"
    return "LT1"


def kelompok_item(items):
    """Gabungkan item dengan kotak dan lantai sama: {(lantai, x, y): [kode, ...]}; kode ditulis ringkas."""
    kel = {}
    for it in items:
        if it["kode"] in SKIP:
            continue
        kel.setdefault((lantai_kunci(it), it["x"], it["y"]), []).append(it)
    return kel


def teks_kode(daftar):
    kode = [i["kode"] for i in daftar]
    if len(kode) == 1:
        return kode[0]
    awal = kode[0].split("-")[0]
    return awal + "-" + "/".join(k.split("-", 1)[1] for k in kode)


class Penempat:
    """Menaruh label tanpa menimpa label lain, garis grid, dan tepi kotak (greedy, dalam meter)."""

    def __init__(self, garis, tetap=()):
        self.rects = [tuple(r) for r in tetap]
        self.garis = garis                  # shapely LineString: grid dan tepi kotak
        self.kotak = []                     # semua kotak alat (x0, x1, y0, y1), label luar dilarang menimpanya
        self.h = H_LABEL * SKALA / 1000     # tinggi huruf (m)

    def ukuran(self, baris):
        return max(len(b) for b in baris) * LEBAR_HURUF * self.h + 0.2, len(baris) * self.h * 1.25

    def _tumpang(self, a, b):
        return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

    def tempat(self, kotak, baris, boleh_dalam=True, jarak=0.3):
        x0, x1, y0, y1 = kotak
        w, h = self.ukuran(baris)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        kand = []
        if boleh_dalam and w <= (x1 - x0) and h <= (y1 - y0):
            kand.append((cx, cy))
        for k in (0, 1, 2, 3):          # cincin makin jauh
            d = jarak + k * 1.6
            kand += [(cx, y1 + d + h / 2), (cx, y0 - d - h / 2), (x1 + d + w / 2, cy), (x0 - d - w / 2, cy),
                     (x0 + w / 2, y1 + d + h / 2), (x1 - w / 2, y1 + d + h / 2), (x0 + w / 2, y0 - d - h / 2),
                     (x1 - w / 2, y0 - d - h / 2), (x1 + d + w / 2, y1 - h / 2), (x0 - d - w / 2, y1 - h / 2),
                     (x1 + d + w / 2, y0 + h / 2), (x0 - d - w / 2, y0 + h / 2)]
        terbaik, nilai = None, 1e9
        for (px, py) in kand:
            r = (px - w / 2, py - h / 2, px + w / 2, py + h / 2)
            tab = sum(self._tumpang(r, o) for o in self.rects)
            garis = box(*r).intersects(self.garis)
            dalam = x0 <= r[0] and r[2] <= x1 and y0 <= r[1] and r[3] <= y1
            lain = sum(box(*r).intersects(box(k[0], k[2], k[1], k[3])) for k in self.kotak
                       if k != (x0, x1, y0, y1)) if not dalam else 0
            nilai_k = 1000 * tab + (0 if dalam else 4 * garis + 10 * lain)
            if nilai_k < nilai:
                terbaik, nilai = (px, py, r), nilai_k
            if nilai == 0:
                break
        px, py, r = terbaik
        self.rects.append(r)
        return px, py, nilai


def gambar(status=None, dwg=DWG, png=PNG, pdf=PDF):
    from cad_lembar import STATUS_DRAF, Gambar

    r = tt.ringkas()
    m, j, ak = r["mri"], r["jarak"], r["akibat"]
    iso = m["iso"]
    items = r["item"]
    pit = {p["kode"]: p for p in r["pit"]}
    kel = kelompok_item(items)

    # obstacle garis: grid dan tepi kotak (untuk penempat label)
    gx0, gx1, gy0, gy1 = tt.GRID_X[0], tt.GRID_X[-1], tt.GRID_Y[0], tt.GRID_Y[-1]
    garis = [LineString([(x, gy0 - 5), (x, gy1 + 5)]) for x in tt.GRID_X] + \
            [LineString([(gx0 - 5, y), (gx1 + 5, y)]) for y in tt.GRID_Y]
    from shapely.ops import unary_union
    garis_u = unary_union(garis)

    hm = H_LABEL * SKALA / 1000
    tetap = []   # kotak teks tetap (m)
    # gelembung as grid: lingkaran r = 3,0 mm kertas -> 1,5 m
    rb = 3.0 * SKALA / 1000
    for x in tt.GRID_X:
        for yy in (gy1 + 1.5 + rb, gy0 - 1.5 - rb):
            tetap.append((x - rb, yy - rb, x + rb, yy + rb))
    for y in tt.GRID_Y:
        tetap.append((gx0 - 1.5 - 2 * rb, y - rb, gx0 - 1.5, y + rb))
    pn = Penempat(garis_u, tetap)
    pn.kotak = [(xr[0], xr[1], yr[0], yr[1]) for (_, xr, yr) in kel]

    with Gambar(SKALA) as g:
        # ------------------------------------------------------------ tapak (persil, sempadan, jalan)
        import tahap3_tapak as tp
        g.layer("C-PERSIL", 7, 0.7, "PHANTOM")
        g.pline([(0, 0), (tp.LX, 0), (tp.LX, tp.LY), (0, tp.LY)], "C-PERSIL", tutup=True)
        g.layer("C-SEMPADAN", 3, 0.25)
        g.arsir(list(tp.ruang_sempadan().exterior.coords)[:-1], "C-SEMPADAN", pola="DOTS", skala_pola=0.6, warna=3)
        g.layer("C-JALAN", 8, 0.25)
        g.pline([(-8, 90), (148, 90)], "C-JALAN")
        g.pline([(-8, 102), (148, 102)], "C-JALAN")
        g.pline([(-6, -6), (-6, 90)], "C-JALAN")
        g.teks((70, 96), "JALAN KOLEKTOR", "C-JALAN", 2.0, j="MC", tebal=True)
        g.teks((70, 5.5), "RUANG SEMPADAN SUNGAI (TANPA BANGUNAN)", "C-SEMPADAN", 1.6, j="MC", warna=3)
        tetap_teks = [(70, 96, "JALAN KOLEKTOR", 2.0), (70, 5.5, "RUANG SEMPADAN SUNGAI (TANPA BANGUNAN)", 1.6)]
        for cx, cy, s, hk in tetap_teks:
            w = len(s) * LEBAR_HURUF * hk * SKALA / 1000
            pn.rects.append((cx - w / 2, cy - hk * SKALA / 2000, cx + w / 2, cy + hk * SKALA / 2000))

        # ------------------------------------------------------------ massa, utilitas, jalur, P4
        g.layer("A-MASSA", 7, 0.7)
        g.pline(GEDUNG["podium"], "A-MASSA", tutup=True)
        g.layer("A-MENARA", 7, 0.35, "DASHED")
        g.pline(GEDUNG["menara"], "A-MENARA", tutup=True)
        g.layer("A-V1", 7, 0.35, "DASHDOT")
        g.pline(GEDUNG["v1"], "A-V1", tutup=True)
        g.layer("A-UTILITAS", 7, 0.5)
        ux0, ux1, uy0, uy1 = tt.UTILITAS
        g.pline([(ux0, uy0), (ux1, uy0), (ux1, uy1), (ux0, uy1)], "A-UTILITAS", tutup=True)
        g.layer("C-P4", 7, 0.25)
        p4 = tt.P4
        g.pline([(p4[0], p4[2]), (p4[1], p4[2]), (p4[1], p4[3]), (p4[0], p4[3])], "C-P4", tutup=True)
        g.layer("C-JALUR", 7, 0.5)
        jx0, jx1 = tt.JALUR_X
        jy0, jy1 = tt.JALUR_Y
        g.pline([(jx0, jy0), (jx1, jy0), (jx1, jy1), (jx0, jy1)], "C-JALUR", tutup=True)
        g.layer("C-JALUR-SUMBU", 7, 0.18, "CENTER")
        g.pline([(91, jy0 - 3), (91, jy1 + 3)], "C-JALUR-SUMBU")

        # ------------------------------------------------------------ as grid
        for i, x in enumerate(tt.GRID_X):
            g.layer("S-GRID", 8, 0.13, "CENTER")
            g.pline([(x, gy0 - 1.5), (x, gy1 + 1.5)], "S-GRID")
            g.as_grid(tt.NAMA_X[i], (x, gy1 + 1.5), (x, gy1 + 1.5 + 1e-3), r_kertas=3.0, dua_ujung=False) \
                if False else None
        for i, x in enumerate(tt.GRID_X):
            for y_a, y_b in ((gy1 + 1.5, gy1 + 1.6), (gy0 - 1.5, gy0 - 1.6)):
                g.as_grid(tt.NAMA_X[i], (x, y_a), (x, y_b), r_kertas=3.0, dua_ujung=False)
        for j_, y in enumerate(tt.GRID_Y):
            g.layer("S-GRID", 8, 0.13, "CENTER")
            g.pline([(gx0 - 1.5, y), (gx1 + 1.5, y)], "S-GRID")
            g.as_grid(tt.NAMA_Y[j_], (gx0 - 1.5, y), (gx0 - 1.6, y), r_kertas=3.0, dua_ujung=False)

        # ------------------------------------------------------------ kotak alat per lantai
        urut = sorted(kel.items(), key=lambda kv: (kv[0][1][1] - kv[0][1][0]) * (kv[0][2][1] - kv[0][2][0]), reverse=True)
        for (lv, xr, yr), daftar in urut:
            x0, x1 = xr
            y0, y1 = yr
            if lv in LAYER_LANTAI:
                nama, w_, t_, gr, _ = LAYER_LANTAI[lv]
                g.layer(nama, w_, t_, gr)
                g.pline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], nama, tutup=True)
                baris = [teks_kode(daftar)]
                if baris[0] in LABEL_TETAP:
                    px, py = LABEL_TETAP[baris[0]]
                    w, h = pn.ukuran(baris)
                    pn.rects.append((px - w / 2, py - h / 2, px + w / 2, py + h / 2))
                else:
                    px, py, _ = pn.tempat((x0, x1, y0, y1), baris)
                g.teks((px, py), baris[0], nama, H_LABEL, j="MC")
            elif lv == "LIFT":
                kode = daftar[0]["kode"]
                p = pit[kode]
                g.layer("M-LIFT", 7, 0.5)
                g.pline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "M-LIFT", tutup=True)
                g.pline([(x0 + 0.4, y0 + 0.4), (x1 - 0.4, y0 + 0.4), (x1 - 0.4, y1 - 0.4), (x0 + 0.4, y1 - 0.4)],
                        "M-LIFT", tutup=True, tebal=0.18)
                baris = [kode, f"PIT +{tt.idn(p['dasar'], 2)}"]
                px, py, _ = pn.tempat((x0, x1, y0, y1), baris)
                g.teks((px, py + pn.h * 0.65), baris[0], "M-LIFT", H_LABEL, j="MC", tebal=True)
                g.teks((px, py - pn.h * 0.6), baris[1], "M-LIFT", H_LABEL, j="MC")
            else:  # SHAFT dan lubang
                g.layer("M-SHAFT", 7, 0.35)
                besar = (x1 - x0) >= 3.0 and (y1 - y0) >= 3.0
                if besar:
                    g.pline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "M-SHAFT", tutup=True)
                    g.pline([(x0 + 0.3, y0 + 0.3), (x1 - 0.3, y0 + 0.3), (x1 - 0.3, y1 - 0.3), (x0 + 0.3, y1 - 0.3)],
                            "M-SHAFT", tutup=True, tebal=0.18)
                else:
                    g.arsir([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "M-SHAFT", pola="ANSI37", skala_pola=0.5)
                baris = [teks_kode(daftar)]
                px, py, _ = pn.tempat((x0, x1, y0, y1), baris, boleh_dalam=besar)
                g.teks((px, py), baris[0], "M-SHAFT", H_LABEL, j="MC")

        # ------------------------------------------------------------ MRI: isocenter dan lingkaran
        g.layer("M-MRI-R12", 1, 0.35, "PHANTOM")
        g.layer("M-MRI-R8", 5, 0.35, "DASHED")
        g.layer("M-MRI-R1", 6, 0.5)
        for rad, lay in ((12.0, "M-MRI-R12"), (8.0, "M-MRI-R8"), (1.0, "M-MRI-R1")):
            g.aktif(lay)
            g.cmd("circle", {"center": g.mm(iso), "radius": rad * 1000})
        g.layer("M-MRI-TITIK", 7, 0.35)
        g.cmd("circle", {"center": g.mm(iso), "radius": 250})
        g.pline([(iso[0] - 0.9, iso[1]), (iso[0] + 0.9, iso[1])], "M-MRI-TITIK")
        g.pline([(iso[0], iso[1] - 0.9), (iso[0], iso[1] + 0.9)], "M-MRI-TITIK")
        s_iso = f"ISOCENTER ({tt.idn(iso[0])}; {tt.idn(iso[1])})"
        lx, ly = 89.0, 31.0
        w = len(s_iso) * LEBAR_HURUF * pn.h
        pn.rects.append((lx, ly - 0.3, lx + w, ly + pn.h + 0.3))
        g.tunjuk((iso[0] + 0.2, iso[1] - 0.2), (lx, ly), s_iso, layer="M-MRI-TITIK")

        # ------------------------------------------------------------ garis ukur asosiatif
        g.layer("C-UKURAN", 7, 0.18)
        g.ukur((iso[0], iso[1]), (tt.JALUR_X[0], iso[1]), ((iso[0] + tt.JALUR_X[0]) / 2, iso[1] + 0.4))
        g.ukur((iso[0], iso[1]), (91.0, iso[1]), ((iso[0] + 91.0) / 2, iso[1] - 4.2))
        g.ukur((72.0, 70.0), (68.0, 70.0), (70.0, 70.4))                       # tepi tangki x 72 -> as 8
        g.ukur((64.0, 73.0), (64.0, 75.0), (63.2, 74.0), rot=90)               # tepi tangki y 73 -> as G
        for cx, cy, s in ((iso[0] + 3.0, iso[1] + 1.4, "7,50"), ((iso[0] + 91.0) / 2 + 1.0, iso[1] - 3.2, "10,50"),
                          (70.0, 71.4, "4,00"), (62.8, 74.0, "2,00")):
            w = len(s) * LEBAR_HURUF * 1.8 * SKALA / 1000
            pn.rects.append((cx - w / 2, cy - pn.h / 2, cx + w / 2, cy + pn.h / 2))

        # ------------------------------------------------------------ keterangan elemen utama
        for s, (cx, cy), lay in (("GEDUNG UTILITAS (x 100-134, y 44-76)", ((ux0 + ux1) / 2, uy1 + 2.5), "A-UTILITAS"),
                                 ("MASSA PODIUM", (24.0, 82.5), "A-MASSA")):
            g.teks((cx, cy), s, lay, 1.8, j="MC", tebal=True)
        # zona P4 dan jalur: teks tegak di sisi luar
        g.teks((jx0 + (jx1 - jx0) / 2, jy1 + 4.6), "JALUR AMBULANS", "C-JALUR", 1.6, j="MC", tebal=True)
        g.teks((97.0, jy0 - 3.0), "ZONA P4", "C-P4", 1.6, j="MC", tebal=True)

        # ------------------------------------------------------------ legenda dan catatan
        for lv, (nama, w_, t_, gr, ket) in LAYER_LANTAI.items():
            g.legenda_tambah("garis", ket, garis=gr, tebal=t_)
        g.legenda_tambah("garis", "Lift L-1..L-7 (kotak ganda), dasar pit", tebal=0.5)
        g.legenda_tambah("arsir", "Shaft SH (arsir), lubang LB (ganda)", pola="ANSI37", skala_pola=0.5)
        g.legenda_tambah("garis", "Massa gedung (podium)", tebal=0.7)
        g.legenda_tambah("garis", "Jalur ambulans dan zona P4", tebal=0.5)
        g.legenda_tambah("garis", "Isocenter: R 12,0 m (logam)", garis="PHANTOM", tebal=0.35)
        g.legenda_tambah("garis", "R 8,0 m (lift)", garis="DASHED", tebal=0.35)
        g.legenda_tambah("garis", "R 1,0 m (non-magnetik)", tebal=0.5)
        catatan = [
            f"Data Beban MEP Rinci (24 Mei 2027). Jarak isocenter ke sumbu x 91 = {tt.idn(j['sumbu_jalur'])} m, ke tepi "
            f"lajur x 88 = {tt.idn(j['tepi_barat_lajur'])} m (syarat ≥ 12,0 m): 5.0.",
            "Jalur x 88-94 [Asumsi lebar]; P4 x 94-100 (3.5). Zona gantung O-01..03 dan R-09 tidak digambar.",
        ]
        g.lembar("GS-21", "Plot data owner di atas grid dan tapak", f"1:{SKALA}", pusat=(73.0, 50.5),
                 subjudul="Langkah 5.0: telaah data owner Tahap 5 (5.0 Telaah Data Tahap 5.xlsx)",
                 status=status or STATUS_DRAF, tanggal=TANGGAL, catatan=catatan,
                 judul_kop="PLOT DATA OWNER DAN GRID")
        g.skala_grafis(205, 22, 50)
        g.panah_utara(318, 262, 10)
        pdf = Path(pdf)
        pdf.parent.mkdir(parents=True, exist_ok=True)
        PNG.parent.mkdir(parents=True, exist_ok=True)
        g.simpan(dwg, pdf, png)
    return dwg


if __name__ == "__main__":
    import cad_cek
    sys.stdout.reconfigure(encoding="utf-8")
    d = gambar()
    print(d)
    hasil = cad_cek.cek(d)
    for h in hasil:
        print(h)
    print(f"{len(hasil)} pasangan bertumpuk")
