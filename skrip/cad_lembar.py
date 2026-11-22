"""Gambar CAD asli di CADCraft: model space berkoordinat nyata, layout A3 berkop KOP_A3, viewport berskala.

Berbeda dengan gambar_teknik.Kertas (isi disusun di matplotlib lalu disalin), modul ini menggambar langsung dengan
perintah CADCraft: layer per unsur, pline, hatch, dimlinear, text/mtext, mleader, insert block. Alur seperti
praktik AutoCAD konsultan:
  - model space: 1 unit = 1 mm, koordinat proyek (x timur, y utara) dalam meter dikali 1000;
  - layout (paper space) A3 1:1: block KOP_A3, viewport terkunci pada skala gambar, legenda dan catatan di kolom
    kanan, skala grafis, panah utara;
  - keluaran: DWG (bisa diedit di CADCraft), PDF hasil plot layout, PNG pratinjau.
Contoh:
    with Gambar(skala=750) as g:
        g.layer("C-PERSIL", 7, 0.5)
        g.pline([(0, 0), (140, 0), (140, 90), (0, 90)], "C-PERSIL", tutup=True)
        lb = g.lembar("GK-01", "Batasan tapak", "1:750", pusat=(70, 40))
        g.simpan(dwg, pdf, png)
"""
import math
import os
import textwrap
from pathlib import Path

import cad_kop
from cadcraft import Sesi

A3 = cad_kop.A3
KIRI, KANAN, ATAS, BAWAH = cad_kop.KIRI, cad_kop.KANAN, cad_kop.ATAS, cad_kop.BAWAH
XK = cad_kop.XK  # tepi kiri kolom kanan (310)
Y_ETIKET = BAWAH + cad_kop.TINGGI_ETIKET  # tepi atas kop (92)
AREA = (KIRI + 4, BAWAH + 4, XK - 4, A3[1] - ATAS - 4)  # area gambar di kertas (mm)
STATUS_DRAF = "DRAF - MENUNGGU PERSETUJUAN"
STATUS_SETUJU = "DISETUJUI 19 NOV 2026"
PAPER = "ISO A3 (297.00 x 420.00 MM)"
TINGGI = {"judul": 4.0, "sub": 2.2, "label": 2.0, "kecil": 1.6, "catatan": 1.9}  # mm kertas


POLA_GT = Path(__file__).resolve().parents[1] / "templat" / "geoteknik.pat"  # arsir jenis tanah (GT-...)


def tinggi(pt):
    return cad_kop.tinggi(pt)


def prm_hatch(pola, skala=1.0, sudut=0):
    """Parameter perintah hatch; pola GT-... diambil dari templat/geoteknik.pat."""
    prm = {"pattern": pola, "angle": sudut}
    if pola != "SOLID":
        prm["scale"] = skala
    if pola.startswith("GT-"):
        prm["patternText"] = POLA_GT.read_text(encoding="utf-8")
    return prm


class Gambar:
    """Satu berkas DWG: isi model space + satu atau lebih layout A3."""

    def __init__(self, skala):
        self.skala = skala
        self.cad = Sesi(jendela=False)  # dibangun di sesi sendiri; hasil dibuka di jendela CADCraft saat simpan
        self.cad.baru(metric=True)
        cad_kop.siapkan_gaya(self.cad)
        self._layer = None
        self._layers = set()
        self.legenda = []  # (jenis, gaya, keterangan) untuk layout
        self.cmd("linetype", {"load": "*"})
        self.cmd("ltscale", {"scale": 0.3})
        self.cmd("setvar", {"name": "PSLTSCALE", "value": 1})
        self.cmd("dimstyle", {"name": "PROYEK", "current": True, "DIMSCALE": skala, "DIMTXT": 1.8, "DIMASZ": 1.6,
                              "DIMEXO": 1.0, "DIMEXE": 1.2, "DIMGAP": 0.6, "DIMTAD": 1, "DIMDEC": 2, "DIMDSEP": ",",
                              "DIMLFAC": 0.001, "DIMTXSTY": "TNR_TEBAL", "DIMTSZ": 1.0, "DIMTIH": 0, "DIMTOH": 0, "DIMZIN": 0, "DIMTFILL": 1})
        self.cmd("mleaderstyle", {"name": "PROYEK", "arrowSize": 1.6 * skala, "textHeight": TINGGI["label"] * skala,
                                  "landingGap": 0.6 * skala, "textStyle": "TNR", "current": True})

    # ------------------------------------------------------------- dasar
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.cad.tutup()

    def cmd(self, perintah, params=None):
        return self.cad.cmd(perintah, params)

    @staticmethod
    def mm(p):
        return [round(p[0] * 1000, 1), round(p[1] * 1000, 1)]

    def layer(self, nama, warna=7, tebal=0.25, garis="Continuous", plot=True):
        if nama not in self._layers:
            self.cmd("layer.new", {"name": nama, "color": warna, "linetype": garis, "lineweight": tebal})
            if not plot:
                self.cmd("layer.set", {"name": nama, "plot": False})
            self._layers.add(nama)
        self.aktif(nama)

    def aktif(self, nama):
        if nama not in self._layers:  # layer belum dibuat: buat dengan gaya bawaan
            self.cmd("layer.new", {"name": nama, "color": 7, "lineweight": 0.18})
            self._layers.add(nama)
        if self._layer != nama:
            self.cmd("layer.current", {"name": nama})
            self._layer = nama

    def _gaya(self, warna=None, tebal=None, garis=None):
        self.cmd("color", {"color": warna if warna is not None else "ByLayer"})
        self.cmd("lweight", {"lineweight": tebal if tebal is not None else "ByLayer"})
        self.cmd("linetype", {"current": garis or "ByLayer"})

    # ------------------------------------------------------------- model space (koordinat meter)
    def pline(self, pts, layer, tutup=False, warna=None, tebal=None, garis=None):
        self.aktif(layer)
        if warna is not None or tebal is not None or garis is not None:
            self._gaya(warna, tebal, garis)
        r = self.cmd("pline", {"vertices": [self.mm(p) for p in pts], "closed": tutup})
        if warna is not None or tebal is not None or garis is not None:
            self._gaya()
        return r["handle"]

    def arsir(self, pts, layer, pola="SOLID", skala_pola=1.0, sudut=0, warna=None, tepi=True):
        """Poligon tertutup (tepi) + hatch. skala_pola dalam satuan kertas (dikali skala gambar)."""
        self.aktif(layer)
        h = self.pline(pts, layer, tutup=True)
        if warna is not None:
            self.cmd("color", {"color": warna})
        r = self.cmd("hatch", {"handles": [h], "associative": True,
                               **prm_hatch(pola, skala_pola * self.skala, sudut)})
        self.cmd("color", {"color": "ByLayer"})
        self.cmd("draworder.back", {"handles": [r["handle"]]})
        if not tepi:
            self.cmd("erase", {"handles": [h]})
        return r["handle"]

    def arsir_lubang(self, pts, lubang, layer, pola="ANSI31", skala_pola=1.0, sudut=0):
        """Arsir poligon dengan lubang (kotak teks) agar arsir tidak menembus tulisan; tepi lubang dihapus."""
        self.aktif(layer)
        luar = self.pline(pts, layer, tutup=True)
        dalam = [self.pline(k, layer, tutup=True) for k in lubang]
        prm = {"handles": [luar] + dalam, "pattern": pola, "angle": sudut, "style": "normal", "associative": False}
        if pola != "SOLID":
            prm["scale"] = skala_pola * self.skala
        r = self.cmd("hatch", prm)
        self.cmd("draworder.back", {"handles": [r["handle"]]})
        if dalam:
            self.cmd("erase", {"handles": dalam})
        return r["handle"]

    @staticmethod
    def kotak_teks(at, s, h, j="MC", rot=0, skala=750, lebar_huruf=0.62):
        """Perkiraan kotak teks di model space (m) untuk tinggi kertas h (mm) pada skala gambar."""
        hm = h * skala / 1000
        w = lebar_huruf * hm * len(s)
        x, y = at
        if j == "MC":
            return (x - w / 2, y - hm / 2, x + w / 2, y + hm / 2)
        return (x, y, x + w, y + hm)

    def teks(self, at, s, layer, h=TINGGI["label"], j="L", rot=0, tebal=False, warna=None):
        self.aktif(layer)
        if tebal:
            self.cmd("style.current", {"name": "TNR_TEBAL"})
        if warna is not None:
            self.cmd("color", {"color": warna})
        r = self.cmd("text", {"at": self.mm(at), "text": s, "height": h * self.skala, "justify": j, "rotation": rot})
        if tebal:
            self.cmd("style.current", {"name": "TNR"})
        if warna is not None:
            self.cmd("color", {"color": "ByLayer"})
        return r["handle"]

    def mteks(self, at, s, layer, lebar_m, h=TINGGI["label"], j="TL"):
        self.aktif(layer)
        return self.cmd("mtext", {"at": self.mm(at), "text": s, "height": h * self.skala, "width": lebar_m * 1000,
                                  "justify": j})["handle"]

    def ukur(self, p1, p2, at, layer="C-UKURAN", teks=None, rot=None):
        self.layer(layer, 7, 0.18)
        prm = {"p1": self.mm(p1), "p2": self.mm(p2), "at": self.mm(at)}
        if teks:  # hanya untuk keterangan tambahan; angka ukur tetap dari geometri (<> = nilai terukur)
            prm["text"] = teks if "<>" in teks else f"<> {teks}"
        if rot is not None:
            prm["rotation"] = rot
        return self.cmd("dimlinear", prm)["handle"]

    def tunjuk(self, panah, letak, s, layer="C-TEKS"):
        self.layer(layer, 7, 0.18)
        return self.cmd("mleader", {"points": [self.mm(panah), self.mm(letak)], "text": s})["handle"]

    def titik_tinggi(self, at, s, layer="C-TEKS", teks_at=None):
        """Simbol titik (segitiga) + teks elevasi (teks_at: letak teks bila bukan di kanan simbol)."""
        self.layer(layer, 7, 0.18)
        d = 1.2 * self.skala / 1000
        x, y = at
        if "TITIK_TINGGI" not in self._layers:  # block simbol, dibuat sekali di titik nol
            dm = d * 1000
            h = self.cmd("pline", {"vertices": [[0, 0], [-dm * 0.6, -dm], [dm * 0.6, -dm]], "closed": True})["handle"]
            hh = self.cmd("hatch", {"handles": [h], "pattern": "SOLID"})["handle"]
            self.cmd("block", {"name": "TITIK_TINGGI", "base": [0, 0], "handles": [h, hh], "keep": "delete"})
            self._layers.add("TITIK_TINGGI")
        self.cmd("insert", {"name": "TITIK_TINGGI", "at": self.mm((x, y))})
        self.teks(teks_at or (x + d, y - d * 0.4), s, layer, TINGGI["kecil"])

    def grid_koordinat(self, x0, x1, y0, y1, jarak, layer="C-GRID", label=True):
        """Tanda silang koordinat tiap `jarak` m dan label di tepi bawah/kiri."""
        self.layer(layer, 8, 0.13)
        d = 1.0 * self.skala / 1000
        nama = self.blok_silang(d)
        for x in range(int(x0), int(x1) + 1, jarak):
            for y in range(int(y0), int(y1) + 1, jarak):
                self.cmd("insert", {"name": nama, "at": self.mm((x, y))})
            if label:
                self.teks((x, y0 - 2.6 * d), f"x {x}", layer, TINGGI["kecil"], j="TC", warna=8)
        for y in range(int(y0), int(y1) + 1, jarak) if label else []:
            self.teks((x0 - 2.6 * d, y), f"y {y}", layer, TINGGI["kecil"], j="MR", warna=8)

    def as_grid(self, nama, p1, p2, layer="S-GRID", r_kertas=4.0, dua_ujung=True):
        """Garis as (CENTER) dengan gelembung lingkaran berisi nama di ujung, seperti gambar struktur drafter."""
        self.layer(layer, 7, 0.18, "CENTER")
        self.pline([p1, p2], layer)
        self.layer(layer + "-GELEMBUNG", 7, 0.25)
        r = r_kertas * self.skala / 1000
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        n = math.hypot(dx, dy)
        ux, uy = dx / n, dy / n
        for ujung, arah in ((p2, 1), (p1, -1)) if dua_ujung else ((p2, 1),):
            c = (ujung[0] + arah * ux * r, ujung[1] + arah * uy * r)
            self.cmd("circle", {"center": self.mm(c), "radius": r * 1000})
            self.teks(c, nama, layer + "-GELEMBUNG", r_kertas * 0.9, j="MC", tebal=True)

    def legenda_tambah(self, jenis, keterangan, **gaya):
        """jenis: 'arsir' (pola, warna, skala_pola), 'garis' (warna, garis, tebal), 'simbol'."""
        self.legenda.append((jenis, gaya, keterangan))

    # ------------------------------------------------------------- layout (paper space, mm kertas)
    def lembar(self, nomor, judul, teks_skala, pusat, subjudul="", lembar="1 / 1", status=STATUS_DRAF,
               catatan=(), area=AREA, tanggal="APRIL 2027", revisi="A", vp=None, viewports=None, judul_kop=None):
        """Layout A3 gaya contoh Defsa: kop KOP_A3, viewport berskala, legenda + catatan di kotak KETERANGAN,
        judul gambar (lingkaran + garis bawah + skala) di kiri bawah. Cetak hitam-putih (monochrome.ctb).
        pusat=None: tanpa viewport bawaan; viewports = [(p1, p2, pusat_mm, skala)] untuk beberapa viewport."""
        c = self.cmd
        c("layout.new", {"name": nomor, "viewport": False})
        for kosong in ("Layout1", "Layout2"):
            try:
                c("layout.delete", {"name": kosong})
            except Exception:
                pass
        c("layout.set", {"name": nomor})
        self.layout_aktif = nomor
        c("pagesetup", {"device": "CADCraft PDF", "paper": PAPER, "landscape": True, "margins": [0, 0, 0, 0],
                        "scale": "1:1", "plotArea": "layout", "lineweights": True, "plotStyleTable": "monochrome.ctb",
                        "displayPlotStyles": True})
        self._layer = None
        self.layer("KOP", 7, 0.35)
        c("insert", {"name": cad_kop.NAMA, "file": str(cad_kop.TEMPLAT), "at": [0, 0], "attribs": {
            "STATUS": status, "JUDUL": (judul_kop or judul).upper(), "NO_GAMBAR": nomor, "SKALA": teks_skala,
            "REV": revisi, "LEMBAR": lembar, "TANGGAL": tanggal.upper(), "DIGAMBAR": "D. YURINDA",
            "DIPERIKSA": "D. YURINDA", "DISETUJUI": "D. YURINDA" if str(status).startswith("DISETUJUI") else "-"}})
        self.layer("VIEWPORT", 8, 0.13, plot=False)
        x0, y0, x1, y1 = area
        vp_handle = None
        if pusat is not None:
            p1, p2 = vp or ((x0, y0 + 24), (x1, y1))
            v = c("mview", {"p1": list(p1), "p2": list(p2)})
            vp_handle = v["viewports"][0]
            c("viewport.set", {"handle": vp_handle, "scale": f"1:{self.skala}", "center": self.mm(pusat),
                               "locked": True})
        for p1, p2, pusat_mm, skala in viewports or ():
            v = c("mview", {"p1": list(p1), "p2": list(p2)})
            vp_handle = v["viewports"][0]
            c("viewport.set", {"handle": vp_handle, "scale": f"1:{skala}", "center": list(pusat_mm), "locked": True})
        self.layer("KERTAS-TEKS", 7, 0.35)
        self._judul_gambar(x0 + 2, y0 + 3, judul, teks_skala, subjudul, nomor)
        yy = cad_kop.KETERANGAN[3] - 4
        if self.legenda:
            yy = self._legenda(yy)
        if catatan:
            self._catatan(yy - 2, catatan)
        return vp_handle

    def viewport_tambahan(self, p1, p2, pusat, skala=None, judul=None, teks_skala=None):
        """Viewport kedua di layout aktif (mis. potongan), dengan label judul kecil bergaris bawah di bawahnya."""
        c = self.cmd
        self.layer("VIEWPORT", 8, 0.13, plot=False)
        v = c("mview", {"p1": list(p1), "p2": list(p2)})
        c("viewport.set", {"handle": v["viewports"][0], "scale": f"1:{skala or self.skala}",
                           "center": self.mm(pusat), "locked": True})
        self.layer("KERTAS-TEKS", 7, 0.35)
        if judul:
            x, y = p1[0] + 2, p1[1] - 4.5
            c("style.current", {"name": "TNR_TEBAL"})
            c("text", {"at": [x, y], "text": judul.upper(), "height": tinggi(10)})
            c("lweight", {"lineweight": 0.5})
            c("pline", {"vertices": [[x, y - 1.2], [x + min(70.0, p2[0] - p1[0] - 4), y - 1.2]]})
            c("lweight", {"lineweight": "ByLayer"})
            c("style.current", {"name": "TNR"})
            if teks_skala:
                c("text", {"at": [x, y - 5], "text": teks_skala, "height": tinggi(8)})
        return v["viewports"][0]

    def _judul_gambar(self, x, y, judul, teks_skala, subjudul, nomor=""):
        """Lingkaran + JUDUL bergaris bawah + SKALA, seperti contoh gambar Defsa."""
        c = self.cmd
        r = 8
        c("circle", {"center": [x + r, y + r], "radius": r})
        c("style.current", {"name": "TNR_TEBAL"})
        if nomor:
            c("text", {"at": [x + r, y + r], "text": nomor, "height": tinggi(9), "justify": "MC"})
        c("text", {"at": [x + 2 * r + 4, y + r + 1.5], "text": judul.upper(), "height": tinggi(12)})
        panjang = max(95, len(judul) * tinggi(12) * 0.78 + 6)  # garis bawah sepanjang judul
        c("lweight", {"lineweight": 0.5})
        c("pline", {"vertices": [[x + 2 * r + 2, y + r], [x + 2 * r + panjang, y + r]]})
        c("lweight", {"lineweight": "ByLayer"})
        teks_s = teks_skala if teks_skala.upper().startswith("TANPA") else f"SKALA {teks_skala}"
        c("text", {"at": [x + 2 * r + 4, y + r - 5.5], "text": teks_s.upper(), "height": tinggi(10)})
        c("style.current", {"name": "TNR"})
        if subjudul:
            for k, s in enumerate(textwrap.wrap(subjudul, 95)[:2]):
                c("text", {"at": [x + 2 * r + 4, y - 1 - 3 * k], "text": s, "height": tinggi(6.5)})

    def _legenda(self, y_atas):
        c = self.cmd
        x = cad_kop.KETERANGAN[0] + 3
        c("style.current", {"name": "TNR_TEBAL"})
        c("text", {"at": [x, y_atas - 3], "text": "LEGENDA :", "height": tinggi(8.5)})
        c("style.current", {"name": "TNR"})
        yy = y_atas - 9
        for jenis, g, ket in self.legenda:
            kotak = [[x, yy - 1.8], [x + 10, yy - 1.8], [x + 10, yy + 1.8], [x, yy + 1.8]]
            if jenis == "arsir":
                h = c("pline", {"vertices": kotak, "closed": True})["handle"]
                c("hatch", {"handles": [h], **prm_hatch(g.get("pola", "SOLID"), g.get("skala_pola", 1.0),
                                                        g.get("sudut", 0))})
            elif jenis == "fungsi":  # contoh digambar oleh pemanggil: f(x0, x1, y)
                g["f"](x, x + 10, yy)
                c("layer.current", {"name": "KERTAS-TEKS"})
            elif jenis == "garis":
                c("linetype", {"current": g.get("garis", "ByLayer")})
                c("lweight", {"lineweight": g.get("tebal", 0.35)})
                c("pline", {"vertices": [[x, yy], [x + 10, yy]]})
                c("linetype", {"current": "ByLayer"})
                c("lweight", {"lineweight": "ByLayer"})
            for k, s in enumerate(textwrap.wrap(ket.upper(), 36)):
                c("text", {"at": [x + 13, yy - 0.9 - 2.6 * k], "text": s, "height": tinggi(6)})
            yy -= 5.0 + 2.6 * (len(textwrap.wrap(ket.upper(), 36)) - 1)
        return yy

    def _catatan(self, y_atas, butir):
        """Catatan bernomor di kotak KETERANGAN; huruf diperkecil bertahap (6 -> 5 pt) bila tidak muat."""
        c = self.cmd
        x = cad_kop.KETERANGAN[0] + 3
        ruang = y_atas - 8.5 - (cad_kop.KETERANGAN[1] + 1.5)
        for pt, lebar, jarak, sela in ((6, 50, 2.5, 0.9), (5.5, 55, 2.25, 0.7), (5, 61, 2.05, 0.6)):
            baris = [textwrap.wrap(b, lebar) for b in butir]
            if sum(len(b) * jarak + sela for b in baris) - sela <= ruang:
                break
        else:
            raise ValueError("catatan tidak muat di kotak KETERANGAN; persingkat")
        c("style.current", {"name": "TNR_TEBAL"})
        c("text", {"at": [x, y_atas - 3], "text": "CATATAN :", "height": tinggi(8.5)})
        c("style.current", {"name": "TNR"})
        yy = y_atas - 8.5
        for i, b in enumerate(baris, start=1):
            c("text", {"at": [x, yy], "text": f"{i}.", "height": tinggi(pt)})
            for s in b:
                c("text", {"at": [x + 4, yy], "text": s, "height": tinggi(pt)})
                yy -= jarak
            yy -= sela

    def skala_grafis(self, x, y, panjang_m, bagi=5):
        """Skala batang di paper space (mm kertas) untuk skala gambar ini."""
        c = self.cmd
        mm = panjang_m / self.skala * 1000
        for i in range(bagi):
            h = c("pline", {"vertices": [[x + i * mm / bagi, y], [x + (i + 1) * mm / bagi, y],
                                         [x + (i + 1) * mm / bagi, y + 1.6], [x + i * mm / bagi, y + 1.6]],
                            "closed": True})["handle"]
            if i % 2 == 0:
                c("hatch", {"handles": [h], "pattern": "SOLID"})
        for i in range(bagi + 1):
            c("text", {"at": [x + i * mm / bagi, y + 2.6], "text": f"{panjang_m * i / bagi:g}",
                       "height": tinggi(5.5), "justify": "BC"})
        c("text", {"at": [x + mm + 2, y + 0.2], "text": "m", "height": tinggi(5.5)})
        c("text", {"at": [x, y - 3.4], "text": "SKALA GRAFIS", "height": tinggi(6), "justify": "L"})

    def panah_utara(self, x, y, ukuran=12):
        """Panah utara sebagai block PANAH_UTARA (paper space), seperti simbol pustaka drafter."""
        c = self.cmd
        h = []
        kiri = c("pline", {"vertices": [[0, ukuran], [-ukuran * 0.3, 0], [0, ukuran * 0.25]], "closed": True})["handle"]
        h.append(kiri)
        h.append(c("hatch", {"handles": [kiri], "pattern": "SOLID"})["handle"])
        h.append(c("pline", {"vertices": [[0, ukuran], [ukuran * 0.3, 0], [0, ukuran * 0.25]], "closed": True})["handle"])
        c("style.current", {"name": "TNR_TEBAL"})
        h.append(c("text", {"at": [0, ukuran + 1.5], "text": "U", "height": tinggi(9), "justify": "BC"})["handle"])
        c("style.current", {"name": "TNR"})
        c("block", {"name": "PANAH_UTARA", "base": [0, 0], "handles": h, "keep": "delete"})
        c("insert", {"name": "PANAH_UTARA", "at": [x, y]})

    def blok_silang(self, d):
        """Block GRID_SILANG (tanda + koordinat) di model space; dibuat sekali."""
        if "GRID_SILANG" not in self._layers:
            h = [self.cmd("pline", {"vertices": [[-d * 1000, 0], [d * 1000, 0]]})["handle"],
                 self.cmd("pline", {"vertices": [[0, -d * 1000], [0, d * 1000]]})["handle"]]
            self.cmd("block", {"name": "GRID_SILANG", "base": [0, 0], "handles": h, "keep": "delete"})
            self._layers.add("GRID_SILANG")
        return "GRID_SILANG"

    def kertas_teks(self, at, s, h=TINGGI["kecil"], j="L"):
        return self.cmd("text", {"at": list(at), "text": s, "height": h, "justify": j})

    # ------------------------------------------------------------- keluaran
    def simpan(self, dwg, pdf=None, png=None, layout=None):
        dwg = Path(dwg)
        dwg.parent.mkdir(parents=True, exist_ok=True)
        self.cad.simpan(dwg)
        if pdf:
            self.cmd("plot", {"path": str(pdf), "layout": layout or self.layout_aktif, "device": "CADCraft PDF",
                              "paper": PAPER, "landscape": True, "scale": "1:1", "lineweights": True,
                              "plotTransparency": True})
        if png and pdf:
            import pypdfium2 as pdfium
            d = pdfium.PdfDocument(str(pdf))
            d[0].render(scale=200 / 72).to_pil().save(str(png))
            d.close()
        dwg.with_suffix(".bak").unlink(missing_ok=True)
        if os.environ.get("CADCRAFT_JENDELA") == "1":  # tampilkan hasil di aplikasi CADCraft yang terbuka
            with Sesi(jendela=True) as w:
                w.buka(dwg.resolve())
        return dwg
