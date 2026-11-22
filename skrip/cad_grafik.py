"""Lembar gambar Tahap 2 digambar langsung di CADCraft (gaya kop KOP_A3 baru, cetak hitam-putih).

`LembarCAD` menggantikan `gambar_teknik.Kertas`: skrip gambar menyusun isi (data, seri, label) seperti biasa, lalu
`simpan()` menggambar ulang setiap unsur sebagai entitas CAD asli dengan aturan gambar proyek, bukan menyalin
tampilan matplotlib:
  - sumbu bertanda `ax._cad = {"skala": 500, "vertikal": 250}` (peta, penampang) digambar di MODEL SPACE berkoordinat
    nyata (1 unit = 1 mm; x, y lokal dalam meter x 1000; penampang: elevasi x 1000 x skala_h/skala_v), lalu
    ditampilkan lewat viewport terkunci berskala. Tepi peta: bingkai dan grid koordinat; penampang: mistar elevasi dan
    jarak. Legenda masuk kotak KETERANGAN;
  - sumbu lain menjadi lembar grafik di paper space: bingkai, garis skala bertanda (tick dalam), grid titik, teks
    satuan, kurva pline per seri pada layer sendiri, legenda berbingkai (wipeout) di dalam grafik;
  - bidang berwarna menjadi arsir standar: unit tanah memakai pola GT-... (templat/geoteknik.pat), air GT-AIR,
    lainnya pola ANSI tetap per warna. Seri yang hanya dibedakan warna diberi simbol penanda supaya terbaca saat
    dicetak hitam-putih;
  - huruf Times New Roman dengan tinggi berjenjang tetap (judul panel, label sumbu, angka skala, keterangan).
Kop, judul gambar berlingkaran, legenda, dan catatan memakai cad_lembar.Gambar.lembar().
"""
import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection, PathCollection, PolyCollection
from matplotlib.contour import ContourSet
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.text import Annotation
from shapely.geometry import LineString, Polygon, box

import cad_kop
from cad_lembar import AREA, STATUS_SETUJU, Gambar, prm_hatch, tinggi
from cad_cek import LEBAR_HURUF
from cad_render import teks_biasa

MM = 25.4
A3 = cad_kop.A3
LAMA = (22, 18, 305, 270)  # isi kertas lama (Kertas, kolom kanan 100 mm), tanpa judul utama
BARU = (AREA[0], AREA[1] + 26, AREA[2], AREA[3])  # area gambar baru di atas judul berlingkaran
TINGGI_TEKS = ((7.5, 2.2), (6.5, 1.9), (5.5, 1.6), (4.6, 1.4), (0, 1.15))  # (pt matplotlib >=, mm kertas)
LW = (0.09, 0.13, 0.18, 0.25, 0.35, 0.5, 0.7)
POLA_UNIT = {"U1": "GT-URUGAN", "U2": "GT-LEMPUNG-TEGUH", "U3": "GT-GAMBUT", "U4": "GT-LEMPUNG-LUNAK",
             "U5": "GT-PASIR-LEPAS", "U6": "GT-LEMPUNG-KAKU", "U7": "GT-PASIR-PADAT", "U8": "GT-LEMPUNG-KERAS"}
POLA_LAIN = [("ANSI31", 0.5), ("DOTS", 0.5), ("ANSI37", 0.5), ("LINE", 0.5), ("ANSI32", 0.5), ("NET", 0.5),
             ("CROSS", 0.4), ("HONEY", 0.4)]
JUDUL_KOP = {"GT-01": "DENAH PENYELIDIKAN", "GT-02": "PENAMPANG A-A'", "GT-03": "PENAMPANG B-B'",
             "GT-04": "PENAMPANG C-C'", "GT-05": "PETA TEBAL U3", "GT-06": "HIDROGRAF AIR TANAH",
             "GT-07": "UJI PEMOMPAAN PW-1", "GT-08": "BATAS GALIAN BLOW-IN", "GT-09": "PARAMETER LEMPUNG",
             "GT-10": "PARAMETER PASIR & CU", "GT-11": "VS DAN KELAS SITUS", "GT-12": "LIKUIFAKSI PASIR U5",
             "GT-13": "PENAMPANG TEBING", "GT-14": "KONDISI AWAL GUDANG", "GT-15": "PENURUNAN URUGAN"}
SIMBOL_CADANGAN = ["^", "s", "D", "v", "o", "x", "+", "<", ">"]


def _warna_unit():
    import tahap2_stratigrafi as st

    peta = {v[2].lower(): (u, POLA_UNIT[u]) for u, v in st.UNIT.items()}
    peta["#b03a2e"] = ("LONGSOR", "GT-LONGSOR")
    peta["#ff0000"] = ("LONGSOR", "GT-LONGSOR")
    return peta


def _hex(rgba):
    return "#" + "".join(f"{int(round(min(max(v, 0), 1) * 255)):02x}" for v in rgba[:3])


def _rgb(rgba):
    return ",".join(str(int(round(min(max(v, 0), 1) * 255))) for v in rgba[:3])


def _lw(pt, minimum=0.13):
    return min(LW, key=lambda v: abs(v - max(pt * 0.3528, minimum)))


def _jenis_garis(seq):
    """Pola putus matplotlib (offset, seq) -> jenis garis CAD standar."""
    if not seq:
        return "Continuous"
    seq = [float(v) for v in seq]
    if len(seq) >= 4:
        return "DASHDOT"
    if seq[0] < 1.6:
        return "DOT"
    if seq[0] <= 4.5:
        return "HIDDEN"
    return "DASHED"


def _tinggi_teks(pt):
    return next(h for batas, h in TINGGI_TEKS if pt >= batas)


def _teks(s):
    s = re.sub(r"\\mathdefault\{([^}]*)\}", r"\1", str(s))
    s = teks_biasa(s).replace("−", "-")
    if re.fullmatch(r"[-+]?\d+\.\d+", s.strip()):
        s = s.replace(".", ",")
    return s


def _air(rgba):
    r, g, b = rgba[:3]
    return b > r + 0.08 and min(r, g, b) > 0.6


def _putih(rgba):
    return len(rgba) > 3 and rgba[3] == 0 or min(rgba[:3]) > 0.97


def _muda(rgba):
    return min(matplotlib.colors.to_rgba(rgba)[:3]) > 0.68


def _nama_layer(s, awalan):
    s = re.sub(r"[^A-Z0-9]+", "-", _teks(s).upper()).strip("-")[:28]
    return f"{awalan}-{s}" if s else f"{awalan}-DATA"


# ======================================================================================== pengganti Kertas
class LembarCAD:
    """Satu lembar A3. API sama dengan gambar_teknik.Kertas (sumbu, teks, etiket, skala_grafis, panah_utara,
    simpan), ditambah catatan(), legenda(), legenda_unit() untuk kotak KETERANGAN."""

    KIRI, KANAN, ATAS, BAWAH = 20, 10, 10, 10
    LEBAR_KOLOM = 100

    def __init__(self):
        self.fig = plt.figure(figsize=(A3[0] / MM, A3[1] / MM))
        self.kertas = self.fig.add_axes([0, 0, 1, 1])
        self.kertas.set_xlim(0, A3[0])
        self.kertas.set_ylim(0, A3[1])
        self.kertas.axis("off")
        self.xk = A3[0] - self.KANAN - self.LEBAR_KOLOM  # 310 (tata letak lama)
        self.area = (self.KIRI, self.BAWAH, self.xk, A3[1] - self.ATAS)
        self.atribut = None
        self.butir_catatan = []
        self.butir_legenda = []
        self.unit = None
        self.skala_ = []
        self.utara_ = []

    def sumbu(self, x, y, w, h):
        return self.fig.add_axes([x / A3[0], y / A3[1], w / A3[0], h / A3[1]])

    def teks(self, x, y, s, **kw):
        kw.setdefault("fontsize", 7)
        return self.kertas.text(x, y, s, **kw)

    def catatan(self, butir):
        self.butir_catatan = list(butir)

    def legenda(self, jenis, keterangan, **gaya):
        """jenis: 'arsir' (pola, skala_pola) | 'garis' (garis, tebal) | 'simbol' (simbol, isi, ukuran)."""
        self.butir_legenda.append((jenis, keterangan, gaya))

    def legenda_unit(self, unit):
        self.unit = list(unit)

    def etiket(self, judul, nomor, skala, lembar, revisi="A", tanggal="APRIL 2027", status=None):
        self.atribut = dict(judul=judul, nomor=nomor, skala=skala, lembar=lembar, revisi=revisi, tanggal=tanggal,
                            status=status or STATUS_SETUJU)
        return 92

    def skala_grafis(self, x, y, panjang_m, skala, bagi=5, judul=None):
        self.skala_.append((x, y, panjang_m, skala, bagi, judul))

    def panah_utara(self, x, y, ukuran=12):
        self.utara_.append((x, y, ukuran))

    def simpan(self, pdf=None, png=None):
        if self.atribut is None:
            raise ValueError("etiket() belum dipanggil")
        png = Path(png)
        dwg = png.parent / "DWG" / f"{png.stem}.dwg"
        halaman = dwg.with_suffix(".pdf")
        try:
            Penggambar(self).buat(dwg, halaman, png)
        finally:
            plt.close(self.fig)
        if pdf is not None:
            pdf.tambah(halaman)
        return dwg


# ======================================================================================== penggambar
class Penggambar:
    def __init__(self, k):
        self.k = k
        self.fig = k.fig
        self.pola_warna = _warna_unit()
        self.pola_bebas = {}
        self.simbol_warna = {}
        self._kini = {}
        self.wilayah = []  # (ax, bbox kertas lama, kotak viewport baru) untuk sumbu model
        self.kumpul = None  # handle hatch yang perlu dibawa ke depan (contoh legenda di atas wipeout)
        self.blok = set()  # nama block simbol yang sudah didefinisikan
        self.terpasang = {}  # kotak teks per ruang ('model' / 'kertas') untuk mencegah teks bertumpuk
        self.ruang_aktif = "model"
        self.berlatar = ([], [])  # (wipeout, teks) yang dibawa ke depan setelah garis dan arsir
        self.hindari_garis = False  # peta: label tidak boleh dicoret garis (wipeout tidak berlaku lewat viewport)
        self.garis = []
        self._isi_blok = []

    # ---------------------------------------------------------------- dasar CAD
    def c(self, perintah, prm=None):
        return self.g.cmd(perintah, prm)

    def _set(self, kunci, nilai, perintah, prm):
        if self._kini.get(kunci) != nilai:
            self.c(perintah, prm)
            self._kini[kunci] = nilai

    def lapis(self, nama, warna=7, tebal=0.25):
        if self._kini.get("layer") != nama:
            self.g.layer(nama, warna, tebal)
            self._kini["layer"] = nama

    def gaya(self, warna="ByLayer", tebal="ByLayer", garis="ByLayer"):
        self._set("warna", warna, "color", {"color": warna})
        self._set("lw", tebal, "lweight", {"lineweight": tebal})
        self._set("lt", garis, "linetype", {"current": garis})

    def huruf(self, tebal=False):
        self._set("gaya", tebal, "style.current", {"name": "TNR_TEBAL" if tebal else "TNR"})

    def reset(self):
        self._kini = {}
        self.g._layer = None

    def pline(self, pts, tutup=False):
        pts = [[round(float(x), 3), round(float(y), 3)] for x, y in pts]
        if len(pts) < 2:
            return None
        if self.hindari_garis and self._kini.get("layer") != "ARSIR-BATAS":
            self.garis.append(LineString(pts + ([pts[0]] if tutup else [])))
        return self.c("pline", {"vertices": pts, "closed": tutup})["handle"]

    def arsir(self, cincin, pola, skala, sudut=0, belakang=True):
        """cincin: daftar poligon (koordinat ruang aktif). Hatch asosiatif; batasnya pline di layer ARSIR-BATAS
        (tidak dicetak), seperti praktik drafter."""
        lapisan = self._kini.get("layer")
        warna, tebal = self._kini.get("warna", "ByLayer"), self._kini.get("lw", "ByLayer")
        self.g.layer("ARSIR-BATAS", 8, 0.09, plot=False)
        self._kini["layer"] = "ARSIR-BATAS"
        self.gaya("ByLayer", "ByLayer", "Continuous")
        h = [self.pline(p, True) for p in cincin if len(p) >= 3]
        h = [x for x in h if x]
        if lapisan:
            self._kini.pop("layer", None)
            self.lapis(lapisan)
        self.gaya(warna, tebal, "Continuous")
        if not h:
            return None
        r = self.c("hatch", {"handles": h, "associative": True, "style": "normal", **prm_hatch(pola, skala, sudut)})
        hh = r.get("handles") or [r.get("handle")]
        if self.kumpul is not None:
            self.kumpul += [x for x in hh if x]
        if belakang:
            self.c("draworder.back", {"handles": [x for x in hh if x]})
        return hh

    @staticmethod
    def _kotak_teks(x, y, h, n, j, rot, lebar=None):
        """Kotak teks: kiri dari titik tangkap dan lebar huruf nyata (±0,42-0,55 h, Times), panjang `lebar` x h per huruf
        (bawaan cad_cek.LEBAR_HURUF, sama dengan cara cad_cek.py membaca titik sisip TEXT)."""
        nyata = 0.42 * h * n  # lebar nyata terkecil (huruf kecil Times); kiri kotak dihitung konservatif
        w = (lebar or LEBAR_HURUF) * h * n
        hz = j[-1] if j and j[-1] in "LCR" else "L"
        v = j[0] if len(j) == 2 else "B"
        kiri = {"L": 0, "C": -nyata / 2, "R": -nyata}[hz]
        bawah = {"B": 0.33 * h if len(j) == 2 else 0, "M": -h / 2, "T": -h}.get(v, 0)  # BL/BC/BR: dasar huruf turun
        if abs((rot or 0) % 360 - 90) < 1:  # tegak: arah teks ke atas
            return x - h - bawah, y + kiri, x - bawah, y + kiri + w
        return x + kiri, y + bawah, x + kiri + w, y + bawah + h

    def _tempatkan(self, item, h, rot, latar=False):
        """Tulis satu blok teks (item = [(x, y, baris, justify)]) dengan geseran bersama bila blok menumpuk teks
        lain di ruang yang sama (atau, di peta, dicoret garis); setiap baris diberi wipeout bila `latar`."""
        tegak = abs((rot or 0) % 360 - 90) < 1
        ruang = self.terpasang.setdefault(self.ruang_aktif, [])

        def kotak_kotak(ddx, ddy):
            return [self._kotak_teks(x + ddx, y + ddy, h, len(b), j, rot) for x, y, b, j in item]

        def tabrak(kk):
            if latar and self.hindari_garis and self.garis:
                for k in kk:
                    kotak_ = box(k[0] - h * 0.3, k[1] - h * 0.3, k[2] + (k[2] - k[0]) * 0.05 + h * 0.3,
                                 k[3] + h * 0.3)
                    if any(kotak_.intersects(gr) for gr in self.garis):
                        return True
            for k in kk:
                for q in ruang:
                    dx, dy = (k[2] - k[0]) * 0.06, (k[3] - k[1]) * 0.06
                    ex, ey = (q[2] - q[0]) * 0.06, (q[3] - q[1]) * 0.06
                    if k[0] + dx < q[2] - ex and q[0] + ex < k[2] - dx and k[1] + dy < q[3] - ey and \
                            q[1] + ey < k[3] - dy:
                        return True
            return False
        geser = (0, 0)
        kk = kotak_kotak(0, 0)
        if tabrak(kk):
            w = LEBAR_HURUF * h * max(len(b) for _, _, b, _ in item)
            tinggi_blok = 1.45 * h * len(item)
            langkah = [0.6, -0.6, 1.2, -1.2, 1.8, -1.8, 2.4, -2.4]
            langkah += [d_ * tinggi_blok / h for d_ in (1.1, -1.1, 1.6, -1.6)]
            calon = [((g_ * h, 0) if tegak else (0, g_ * h)) for g_ in langkah]
            calon += [((0, g_ * w) if tegak else (g_ * w, 0)) for g_ in (-0.3, 0.3, -0.6, 0.6, -1.0, 1.0)]
            calon += [((dy * h, g_ * w) if tegak else (g_ * w, dy * h)) for g_ in (-0.6, 0.6) for dy in (1.2, -1.2)]
            for c_ in calon:
                k2 = kotak_kotak(*c_)
                if not tabrak(k2):
                    geser, kk = c_, k2
                    break
        ruang.extend(kk)
        for x, y, b, j in item:
            px, py = x + geser[0], y + geser[1]
            if latar:  # wipeout di belakang teks: arsir dan garis tidak memotong tulisan
                x0, y0, x1, y1 = self._kotak_teks(px, py, h, len(b), j, rot, lebar=0.58)
                r = self.c("wipeout", {"points": [[x0 - h * 0.25, y0 - h * 0.3], [x1 + h * 0.25, y0 - h * 0.3],
                                                  [x1 + h * 0.25, y1 + h * 0.3], [x0 - h * 0.25, y1 + h * 0.3]]})
                self.berlatar[0].append(r.get("handle"))
            r = self.c("text", {"at": [round(px, 3), round(py, 3)], "text": b, "height": h, "justify": j,
                                "rotation": rot})
            if latar:
                self.berlatar[1].append(r.get("handle"))

    def tulis(self, at, s, h, j="L", rot=0.0, tebal=False, latar=False):
        s = _teks(s)
        if not s.strip():
            return
        self.huruf(tebal)
        baris = s.split("\n")
        if len(baris) == 1 or rot % 360:
            self._tempatkan([(at[0], at[1] - i * 1.45 * h, b, j) for i, b in enumerate(baris)], h, rot, latar)
            return
        v = j[0] if len(j) == 2 else "B"
        hz = j[-1] if j[-1] in "LCR" else "L"
        n, step = len(baris), 1.45 * h
        item = []
        for i, b in enumerate(baris):
            if v == "T":
                y = at[1] - h - i * step
            elif v == "M":
                y = at[1] + ((n - 1) * step + h) / 2 - h - i * step
            else:
                y = at[1] + (n - 1 - i) * step
            item.append((at[0], y, b, hz))
        self._tempatkan(item, h, 0, latar)

    def simbol(self, jenis, x, y, d, isi):
        """Simbol penanda titik data (block SB-<jenis>, diameter 1) disisipkan berskala d di (x, y)."""
        kode = {"o": "BULAT", ".": "TITIK", ",": "TITIK", "s": "KOTAK", "D": "BELAH", "d": "BELAH-TIPIS",
                "^": "SEGITIGA", "v": "SEGITIGA-BALIK", "<": "SEGITIGA-KIRI", ">": "SEGITIGA-KANAN", "x": "SILANG",
                "X": "SILANG", "+": "PLUS", "P": "PLUS", "|": "GARIS-TEGAK", "_": "GARIS-DATAR"}.get(jenis, "SILANG")
        nama = f"SB-{kode}" + ("-ISI" if isi and kode not in ("SILANG", "PLUS", "GARIS-TEGAK", "GARIS-DATAR", "TITIK")
                               else "")
        if nama not in self.blok:
            kini = dict(self._kini)
            self.c("layer.current", {"name": "0"})
            self.g._layer = "0"
            self._kini = {"layer": "0"}
            self.gaya("ByBlock", "ByBlock", "ByBlock")
            self._isi_blok = []
            self._bentuk_simbol(jenis, 0.0, 0.0, 1.0, isi)
            self.c("block", {"name": nama, "base": [0, 0], "handles": [h for h in self._isi_blok if h],
                             "keep": "delete"})
            self.blok.add(nama)
            self._kini = {}
            if kini.get("layer"):
                self.lapis(kini["layer"])
            self.gaya(kini.get("warna", "ByLayer"), kini.get("lw", "ByLayer"), kini.get("lt", "ByLayer"))
        r = self.c("insert", {"name": nama, "at": [round(x, 3), round(y, 3)], "scale": round(d, 4)})
        if self.hindari_garis:  # titik data ikut dihindari label dan legenda
            self.garis.append(box(x - d / 2, y - d / 2, x + d / 2, y + d / 2).exterior)
        if self.kumpul is not None:
            self.kumpul.append(r.get("handle"))

    def _bentuk_simbol(self, jenis, x, y, d, isi):
        """Geometri simbol (dipakai untuk isi block SB-...)."""
        r = d / 2
        if jenis in ("o", ".", ",", "8", "h", "H", "p", "*"):
            if jenis in (".", ","):
                r = max(r * 0.6, d * 0.15)
                isi = True
            if isi:
                self._isi_blok.append(self.c("donut", {"center": [x, y], "inside": 0, "outside": 2 * r})["handle"])
            else:
                self._isi_blok.append(self.c("circle", {"center": [x, y], "radius": r})["handle"])
            return
        bentuk = {"s": [(-1, -1), (1, -1), (1, 1), (-1, 1)], "D": [(0, -1.3), (1, 0), (0, 1.3), (-1, 0)],
                  "d": [(0, -1.3), (0.7, 0), (0, 1.3), (-0.7, 0)], "^": [(-1, -0.8), (1, -0.8), (0, 1.1)],
                  "v": [(-1, 0.8), (1, 0.8), (0, -1.1)], "<": [(0.8, -1), (0.8, 1), (-1.1, 0)],
                  ">": [(-0.8, -1), (-0.8, 1), (1.1, 0)]}
        if jenis in bentuk:
            k = 0.8 if jenis == "s" else 1.0
            h = self.pline([(x + a * r * k, y + b * r * k) for a, b in bentuk[jenis]], True)
            self._isi_blok.append(h)
            if isi and h:
                self._isi_blok.append(self.c("hatch", {"handles": [h], "pattern": "SOLID", "associative": True})["handle"])
            return
        silang = {"x": [((-1, -1), (1, 1)), ((-1, 1), (1, -1))], "X": [((-1, -1), (1, 1)), ((-1, 1), (1, -1))],
                  "+": [((-1, 0), (1, 0)), ((0, -1), (0, 1))], "P": [((-1, 0), (1, 0)), ((0, -1), (0, 1))],
                  "|": [((0, -1.4), (0, 1.4))], "_": [((-1.4, 0), (1.4, 0))]}
        for (a, b), (e, f) in silang.get(jenis, [((-1, -1), (1, 1)), ((-1, 1), (1, -1))]):
            self._isi_blok.append(self.pline([(x + a * r, y + b * r), (x + e * r, y + f * r)]))

    # ---------------------------------------------------------------- pemetaan koordinat
    @staticmethod
    def _peta_lama(x, y):
        bx = BARU[0] + (x - LAMA[0]) * (BARU[2] - BARU[0]) / (LAMA[2] - LAMA[0])
        by = BARU[1] + (y - LAMA[1]) * (BARU[3] - BARU[1]) / (LAMA[3] - LAMA[1])
        return bx, by

    def kertas_baru(self, x, y):
        """Titik kertas lama (mm) -> kertas baru; dekat sumbu model mengikuti viewport-nya."""
        calon = []
        for ax, (a0, b0, a1, b1), (p0, q0, p1, q1) in self.wilayah:
            jarak = max(a0 - x, 0, x - a1) + max(b0 - y, 0, y - b1)
            if jarak <= 14:
                calon.append((jarak, (a0, b0, a1, b1), (p0, q0, p1, q1)))
        if calon:
            _, (a0, b0, a1, b1), (p0, q0, p1, q1) = min(calon, key=lambda c: c[0])
            return p0 + (x - a0) * (p1 - p0) / (a1 - a0), q0 + (y - b0) * (q1 - q0) / (b1 - b0)
        return self._peta_lama(x, y)

    def _px_ke_mm(self, p):
        p = np.asarray(p, float).reshape(-1, 2)
        return p / self.fig.dpi * MM

    def peta_kertas(self, p):
        return [self.kertas_baru(x, y) for x, y in self._px_ke_mm(p)]

    def ruang(self, ax):
        """Fungsi display -> koordinat ruang gambar, dan faktor tinggi (kertas mm -> unit ruang)."""
        cfg = getattr(ax, "_cad", None)
        if not cfg:
            return self.peta_kertas, 1.0
        inv = ax.transData.inverted()
        ex = cfg["skala"] / cfg.get("vertikal", cfg["skala"])
        oy = cfg["_oy"]

        def f(p):
            d = inv.transform(np.asarray(p, float).reshape(-1, 2))
            return [(x * 1000, y * ex * 1000 + oy) for x, y in d]
        return f, float(cfg["skala"])

    # ---------------------------------------------------------------- arsir dan simbol per warna
    def pola(self, rgba, hatch=None):
        """(pola, skala, nama) untuk bidang berwarna; None = tidak diarsir."""
        if rgba is None:
            return None
        rgba = tuple(rgba)
        kunci = _hex(rgba)
        if kunci in self.pola_warna:
            u, p = self.pola_warna[kunci]
            return p, 1.0, u
        if hatch:
            ch = hatch[0]
            p = {"/": "ANSI31", "\\": "ANSI31", "x": "ANSI37", "X": "ANSI37", "-": "LINE", "|": "LINE",
                 "+": "NET", ".": "DOTS", "o": "DOTS", "O": "DOTS", "*": "DOTS"}.get(ch, "ANSI31")
            return p, 0.45, "ARSIR"
        if _putih(rgba) or (len(rgba) > 3 and rgba[3] < 0.05):
            return None
        if _air(rgba):
            return "GT-AIR", 1.0, "AIR"
        if min(rgba[:3]) > 0.8:  # latar muda (rentang, jendela waktu): titik jarang
            return "DOTS", 1.6, "LATAR"
        if kunci not in self.pola_bebas:
            self.pola_bebas[kunci] = POLA_LAIN[len(self.pola_bebas) % len(POLA_LAIN)]
        p, s = self.pola_bebas[kunci]
        return p, s, "ISI"

    def siapkan_simbol(self, ax):
        """Seri berlegenda yang sama jenis garis dan simbolnya (hanya beda warna) diberi simbol per warna supaya
        tetap terbedakan saat dicetak hitam-putih. Garis warna muda (latar) tidak diberi simbol."""
        seri = [ln for ln in ax.lines if not ln.get_label().startswith("_") and ln.get_visible()
                and not _muda(ln.get_color())]
        kunci = {}
        for ln in seri:
            m = ln.get_marker() if ln.get_marker() not in ("None", None, "", " ") else ""
            m = {"x": "o", "+": "o", ".": "o", ",": "o"}.get(m, m)
            k = (_jenis_garis(ln._unscaled_dash_pattern[1]) if ln.get_linestyle() not in ("None", "", " ") else "-", m)
            kunci.setdefault(k, []).append(ln)
        terpakai = {ln.get_marker() for ln in ax.lines}
        bebas = [m for m in SIMBOL_CADANGAN if m not in terpakai] + SIMBOL_CADANGAN
        for daftar in kunci.values():
            if len({_hex(matplotlib.colors.to_rgba(ln.get_color())) for ln in daftar}) < 2:
                continue
            for ln in daftar:
                w = _hex(matplotlib.colors.to_rgba(ln.get_color()))
                if w not in self.simbol_warna:
                    self.simbol_warna[w] = bebas.pop(0)

    def penanda(self, line):
        """(simbol di titik data, simbol di sepanjang garis, paksa_isi) untuk satu Line2D."""
        m = line.get_marker()
        m = None if m in ("None", None, "", " ") else m
        w = self.simbol_warna.get(_hex(matplotlib.colors.to_rgba(line.get_color())))
        berlabel = not line.get_label().startswith("_")
        if not w:
            return m, None, None
        if m is None:
            return None, (w if berlabel else None), None
        if m in (".", ",", "x", "X", "+", "P", "|", "_"):
            return w, None, False
        return w, None, None

    # ---------------------------------------------------------------- unsur sumbu
    def _potong_garis(self, pts, bb):
        pts = np.asarray(pts, float)
        hasil, awal = [], None
        ok = np.isfinite(pts).all(axis=1)
        for i, b in enumerate(list(ok) + [False]):
            if b and awal is None:
                awal = i
            elif not b and awal is not None:
                if i - awal >= 2:
                    hasil.append(pts[awal:i])
                awal = None
        keluar = []
        for p in hasil:
            ls = LineString(p)
            if ls.within(bb):
                keluar.append(p)
                continue
            g = ls.intersection(bb)
            for q in getattr(g, "geoms", [g]):
                if q.geom_type == "LineString" and not q.is_empty and q.length > 0.2:
                    keluar.append(np.array(q.coords))
        return keluar

    def _potong_poligon(self, poligon, bb):
        hasil = []
        x0, y0, x1, y1 = bb.bounds
        for p in poligon:
            p = np.asarray(p, float)
            p = np.where(np.isnan(p), -np.inf, p)  # titik nol di sumbu log
            if len(p) < 3:
                continue
            p = np.column_stack([np.clip(p[:, 0], x0 - 1, x1 + 1), np.clip(p[:, 1], y0 - 1, y1 + 1)])
            try:
                g = Polygon(p).buffer(0).intersection(bb)
            except Exception:
                continue
            for q in getattr(g, "geoms", [g]):
                if q.geom_type == "Polygon" and not q.is_empty and q.area > 0.5:
                    hasil.append(np.array(q.exterior.coords)[:-1])
                    hasil += [np.array(r.coords)[:-1] for r in q.interiors]
        return hasil

    def _bidang(self, ax, T, f, poligon, rgba, hatch, tepi_rgba, tepi_lw, tepi_seq, layer):
        bb = self._bb(ax)
        if rgba is not None and len(rgba) > 3 and rgba[3] < 0.6 and not hatch:
            if getattr(ax, "_cad", None):
                rgba = None
            elif _hex(rgba) in self.pola_warna:  # pita unit tanah di grafik: arsir unit itu
                pass
            else:
                a = rgba[3]
                rgba = tuple(1 - (1 - v) * a for v in rgba[:3]) + (1.0,)
        cincin = self._potong_poligon(poligon, bb)
        if not cincin:
            return
        pl = self.pola(rgba, hatch)
        if pl:
            p, s, nama = pl
            self.lapis(f"{layer}-{nama}" if nama not in ("ISI", "ARSIR") else layer, 8, 0.13)
            self.gaya(_rgb(rgba) if rgba is not None and not _putih(rgba) else 8, 0.13, "Continuous")
            self.arsir([T(c) for c in cincin], p, s * f)
        if tepi_rgba is not None and tepi_lw > 0 and not (len(tepi_rgba) > 3 and tepi_rgba[3] < 0.05):
            self.lapis(layer, 7, 0.25)
            self.gaya(_rgb(tepi_rgba), _lw(tepi_lw), _jenis_garis(tepi_seq))
            for c in cincin:
                self.pline(T(c), True)

    def _bb(self, ax):
        b = ax.bbox
        return box(b.x0 - 0.5, b.y0 - 0.5, b.x1 + 0.5, b.y1 + 0.5)

    def gambar_isi(self, ax, awalan):
        T, f = self.ruang(ax)
        bb = self._bb(ax)
        self.siapkan_simbol(ax)
        artis = sorted(ax.get_children(), key=lambda a: a.get_zorder())
        for a in artis:
            if not a.get_visible() or a in (ax.patch,) or a.__class__.__name__ in ("Spine", "XAxis", "YAxis"):
                continue
            nama = a.get_label() if not str(a.get_label()).startswith("_") else ""
            layer = _nama_layer(nama, awalan) if nama else f"{awalan}-DATA"
            if isinstance(a, ContourSet):
                self._kontur(a, T, f, bb, awalan)
            elif isinstance(a, PolyCollection) or (isinstance(a, PathCollection) is False and
                                                   type(a).__name__ == "FillBetweenPolyCollection"):
                for i, p in enumerate(a.get_paths()):
                    fc = a.get_facecolor()
                    ec = a.get_edgecolor()
                    lw = a.get_linewidth()
                    poli = p.to_polygons(a.get_transform(), closed_only=True)
                    self._bidang(ax, T, f, poli, fc[i % len(fc)] if len(fc) else None, a.get_hatch(),
                                 ec[i % len(ec)] if len(ec) else None, lw[i % len(lw)] if len(lw) else 0,
                                 a.get_linestyle()[0][1] if a.get_linestyle() else None, layer)
            elif isinstance(a, PathCollection):
                self._sebar(a, T, f, bb, layer)
            elif isinstance(a, LineCollection):
                self.lapis(layer, 7, 0.18)
                warna = a.get_colors()
                lws = a.get_linewidths()
                lss = a.get_linestyles()
                for i, seg in enumerate(a.get_segments()):
                    d = a.get_transform().transform(seg)
                    self.gaya(_rgb(warna[i % len(warna)]), _lw(lws[i % len(lws)]),
                              _jenis_garis(lss[i % len(lss)][1]))
                    for p in self._potong_garis(d, bb):
                        self.pline(T(p))
            elif isinstance(a, Patch):
                if isinstance(a, Rectangle) and not a.get_angle():  # sudut nol di sumbu log: pakai titik sudut
                    x, y = a.get_xy()
                    w, h = a.get_width(), a.get_height()
                    with np.errstate(all="ignore"):
                        poli = [a.get_data_transform().transform([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])]
                else:
                    poli = a.get_path().to_polygons(a.get_transform(), closed_only=True)
                ec = a.get_edgecolor() if a.get_linewidth() > 0 else None
                fc = a.get_facecolor() if a.get_fill() else None
                lw_tepi = a.get_linewidth()
                if (ec is None or ec[3] < 0.05) and isinstance(a, Rectangle) and a.get_label() == "_nolegend_"                         and fc is not None and not _putih(fc) and not getattr(ax, "_cad", None):
                    ec, lw_tepi = (0, 0, 0, 1), 0.5  # batang grafik bergaris tepi
                self._bidang(ax, T, f, poli, fc, a.get_hatch(), ec, lw_tepi,
                             a._unscaled_dash_pattern[1], layer)
            elif isinstance(a, Line2D):
                self._garis(a, T, f, bb, layer)
        for t in ax.texts:
            if t.get_visible() and t.get_text().strip():
                self.teks_mpl(t, T, f, f"{awalan}-TEKS", ax)
        for daftar in self.berlatar:  # urutan gambar: wipeout di atas garis, teks paling depan
            daftar = [x for x in daftar if x]
            if daftar:
                self.c("draworder.front", {"handles": daftar})
        self.berlatar = ([], [])

    def _kontur(self, cs, T, f, bb, awalan):
        if cs.filled:
            hatches = cs.hatches or [None]
            for i, p in enumerate(cs.get_paths()):
                h = hatches[i % len(hatches)]
                if not h:
                    continue
                poli = p.to_polygons(cs.get_transform(), closed_only=True)
                cincin = self._potong_poligon(poli, bb)
                if cincin:
                    self.lapis(f"{awalan}-KONTUR-ARSIR", 8, 0.13)
                    self.gaya(8, 0.13, "Continuous")
                    self.arsir([T(c) for c in cincin], "ANSI31", 0.45 * f)
            return
        warna = cs.get_edgecolor()
        lws = cs.get_linewidths()
        for i, p in enumerate(cs.get_paths()):
            self.lapis(f"{awalan}-KONTUR", 7, 0.18)
            self.gaya(_rgb(warna[i % len(warna)]), _lw(lws[i % len(lws)]), "Continuous")
            for q in p.to_polygons(cs.get_transform(), closed_only=False):
                for s in self._potong_garis(q, bb):
                    self.pline(T(s))

    def _sebar(self, a, T, f, bb, layer):
        off = a.get_offset_transform().transform(a.get_offsets())
        ukuran = a.get_sizes()
        fc = a.get_facecolor()
        self.lapis(layer, 7, 0.18)
        for i, (x, y) in enumerate(off):
            if not bb.contains(box(x, y, x + 0.01, y + 0.01)):
                continue
            d = np.sqrt(ukuran[i % len(ukuran)] if len(ukuran) else 20) * 0.3528 * 0.85 * f
            isi = len(fc) and not _putih(fc[i % len(fc)])
            self.gaya(_rgb(fc[i % len(fc)]) if len(fc) else 7, 0.18, "Continuous")
            (px, py), = T([(x, y)])
            self.simbol("o", px, py, d, isi)

    def _garis(self, ln, T, f, bb, layer):
        try:
            d = ln.get_transform().transform(ln.get_path().vertices)
        except Exception:
            return
        warna = _rgb(matplotlib.colors.to_rgba(ln.get_color()))
        self.lapis(layer, 7, 0.25)
        ada_garis = ln.get_linestyle() not in ("None", "", " ") and ln.get_linewidth() > 0
        potongan = self._potong_garis(d, bb) if ada_garis else []
        if ada_garis:
            tebal = 0.09 if _muda(ln.get_color()) else _lw(ln.get_linewidth())
            self.gaya(warna, tebal, _jenis_garis(ln._unscaled_dash_pattern[1]))
            for p in potongan:
                self.pline(T(p))
        m, tambahan, paksa = self.penanda(ln)
        ms = ln.get_markersize() * 0.3528 * 0.85
        if ln.get_marker() in (".", ",") and m != ln.get_marker():
            ms = max(ms, 1.0)
        mfc = ln.get_markerfacecolor()
        isi = not (isinstance(mfc, str) and mfc in ("none", "None")) and not _putih(matplotlib.colors.to_rgba(mfc))
        if paksa is not None:
            isi = paksa
        if m:
            self.gaya(warna, 0.18, "Continuous")
            for x, y in d:
                if np.isfinite([x, y]).all() and bb.contains(box(x, y, x + 0.01, y + 0.01)):
                    (px, py), = T([(x, y)])
                    self.simbol(m, px, py, max(ms, 0.6) * f, isi)
        elif tambahan and potongan:
            self.gaya(warna, 0.18, "Continuous")
            for p in potongan:
                ls = LineString(p)
                n = max(2, min(9, int(ls.length / (25 / MM * self.fig.dpi)) + 1))
                for t in np.linspace(0.06, 0.94, n):
                    q = ls.interpolate(t, normalized=True)
                    (px, py), = T([(q.x, q.y)])
                    self.simbol(tambahan, px, py, 1.3 * f, False)

    # ---------------------------------------------------------------- teks matplotlib
    def teks_mpl(self, t, T, f, layer, ax=None, tinggi_mm=None, tebal=None):
        try:
            from matplotlib.text import Text
            bb = Text.get_window_extent(t, self.renderer)  # Annotation: tanpa panah
        except Exception:
            return
        if ax is not None and ax.get_clip_on() and t.get_clip_on():
            ab = ax.bbox
            if bb.x1 < ab.x0 - 4 or bb.x0 > ab.x1 + 4 or bb.y1 < ab.y0 - 4 or bb.y0 > ab.y1 + 4:
                return
        rot = t.get_rotation() % 360
        ha, va = t.get_horizontalalignment(), t.get_verticalalignment()
        h = (tinggi_mm or _tinggi_teks(t.get_fontsize())) * f
        tb = tebal if tebal is not None else t.get_fontweight() in ("bold", "heavy", "semibold", 600, 700, 800)
        self.lapis(layer, 7, 0.18)
        w = matplotlib.colors.to_rgba(t.get_color())
        self.gaya(_rgb(w) if not _putih(w) else 7, "ByLayer", "Continuous")
        latar = layer.endswith("-TEKS") and layer != "KERTAS-TEKS"  # teks di dalam gambar
        jaga_garis = self.hindari_garis
        if t.get_horizontalalignment() == "center" and self.ruang_aktif == "model":  # huruf di lingkaran potongan
            self.hindari_garis = False
        if isinstance(t, Annotation) and t.arrow_patch is not None:
            self._panah(t, bb, T, f)
        if rot not in (0, 360) and abs(rot - 90) > 1:
            (x, y), = T([((bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2)])
            self.tulis((x, y), t.get_text(), h, "MC", rot, tb, latar)
            self.hindari_garis = jaga_garis
            return
        if abs(rot - 90) <= 1:
            (x, y), = T([((bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2)])
            self.tulis((x, y), t.get_text(), h, "MC", 90, tb, latar)
            self.hindari_garis = jaga_garis
            return
        x = {"left": bb.x0, "center": (bb.x0 + bb.x1) / 2, "right": bb.x1}[ha]
        y = {"top": bb.y1, "bottom": bb.y0, "baseline": bb.y0, "center": (bb.y0 + bb.y1) / 2,
             "center_baseline": (bb.y0 + bb.y1) / 2}[va]
        j = {"top": "T", "bottom": "B", "baseline": "B", "center": "M", "center_baseline": "M"}[va] + \
            {"left": "L", "center": "C", "right": "R"}[ha]
        (px, py), = T([(x, y)])
        self.tulis((px, py), t.get_text(), h, j, 0, tb, latar)
        self.hindari_garis = jaga_garis

    def _panah(self, t, bb, T, f):
        try:
            ujung = np.array(t._get_xy_transform(self.renderer, t.xycoords).transform(t.xy), float)
        except Exception:
            return
        pusat = np.array([(bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2])
        kandidat = [np.array([x, y]) for x in (bb.x0, (bb.x0 + bb.x1) / 2, bb.x1) for y in (bb.y0, bb.y1)]
        awal = min(kandidat, key=lambda p: np.linalg.norm(p - ujung))
        if np.linalg.norm(awal - ujung) < 3:
            return
        del pusat
        (ax_, ay_), (bx, by) = T([tuple(awal), tuple(ujung)])
        self.pline([(ax_, ay_), (bx, by)])
        arah = np.array([bx - ax_, by - ay_])
        arah = arah / (np.linalg.norm(arah) or 1)
        n = np.array([-arah[1], arah[0]])
        L = 1.4 * f
        p1 = np.array([bx, by]) - arah * L + n * L * 0.3
        p2 = np.array([bx, by]) - arah * L - n * L * 0.3
        h = self.pline([(bx, by), tuple(p1), tuple(p2)], True)
        if h:
            self.c("hatch", {"handles": [h], "pattern": "SOLID", "associative": False})

    # ---------------------------------------------------------------- sumbu grafik (paper space)
    def bingkai_grafik(self, ax):
        T = self.peta_kertas
        b = ax.bbox
        x0, y0 = T([(b.x0, b.y0)])[0]
        x1, y1 = T([(b.x1, b.y1)])[0]
        self.lapis("G-BINGKAI", 7, 0.35)
        self.gaya("ByLayer", "ByLayer", "Continuous")
        self.pline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], True)
        grid_x = any(g.get_visible() for g in ax.get_xgridlines())
        grid_y = any(g.get_visible() for g in ax.get_ygridlines())
        for sb, utama, grid in ((ax.xaxis, True, grid_x), (ax.yaxis, True, grid_y)):
            mayor = sb.get_majorticklocs()
            minor = sb.get_minorticklocs() if sb.get_scale() == "log" else []
            for nilai, panjang, gr in [(v, 1.4, grid) for v in mayor] + [(v, 0.8, False) for v in minor]:
                if sb is ax.xaxis:
                    d = ax.transData.transform([(nilai, ax.get_ylim()[0])])[0]
                    if not b.x0 - 0.5 <= d[0] <= b.x1 + 0.5:
                        continue
                    (px, _), = T([d])
                    if gr and abs(px - x0) > 0.3 and abs(px - x1) > 0.3:
                        self.lapis("G-GRID", 8, 0.09)
                        self.gaya("ByLayer", "ByLayer", "DOT")
                        self.pline([(px, y0), (px, y1)])
                    self.lapis("G-SKALA", 7, 0.25)
                    self.gaya("ByLayer", "ByLayer", "Continuous")
                    self.pline([(px, y0), (px, y0 + panjang)])
                    self.pline([(px, y1), (px, y1 - panjang)])
                else:
                    d = ax.transData.transform([(ax.get_xlim()[0], nilai)])[0]
                    if not b.y0 - 0.5 <= d[1] <= b.y1 + 0.5:
                        continue
                    (_, py), = T([d])
                    if gr and abs(py - y0) > 0.3 and abs(py - y1) > 0.3:
                        self.lapis("G-GRID", 8, 0.09)
                        self.gaya("ByLayer", "ByLayer", "DOT")
                        self.pline([(x0, py), (x1, py)])
                    self.lapis("G-SKALA", 7, 0.25)
                    self.gaya("ByLayer", "ByLayer", "Continuous")
                    self.pline([(x0, py), (x0 + panjang, py)])
                    self.pline([(x1, py), (x1 - panjang, py)])
        self.label_sumbu(ax, T, 1.0, "G")

    def label_sumbu(self, ax, T, f, awalan, angka=True):
        if angka:
            for sb, (a, b) in ((ax.xaxis, sorted(ax.get_xlim())), (ax.yaxis, sorted(ax.get_ylim()))):
                tol = (b - a) * 1e-6
                for v, t in zip(sb.get_majorticklocs(), sb.get_majorticklabels()):
                    if a - tol <= v <= b + tol and t.get_visible() and t.get_text().strip():
                        self.teks_mpl(t, T, f, f"{awalan}-SKALA", tinggi_mm=1.6)
        for t in (ax.xaxis.label, ax.yaxis.label):
            if t.get_visible() and t.get_text().strip():
                self.teks_mpl(t, T, f, f"{awalan}-SKALA", tinggi_mm=1.8)

    def judul_sumbu(self, ax):
        for t in (ax._left_title, ax.title, ax._right_title):
            if t.get_text().strip():
                self.teks_mpl(t, self.peta_kertas, 1.0, "G-JUDUL", tinggi_mm=2.2, tebal=True)

    def legenda_grafik(self, ax):
        """Legenda grafik ditata ulang di CAD: jarak baris tetap (1,8 x tinggi huruf), lebar kolom dari panjang teks,
        lalu diletakkan di sudut/tepi dalam bingkai yang paling sedikit menimpa kurva dan teks (kiri-kanan atas-bawah,
        tengah); bila semua menimpa, di posisi dengan tumpang tindih terkecil."""
        leg = ax.get_legend()
        if leg is None or not leg.get_visible():
            return
        T = self.peta_kertas
        pasangan = [(h, t) for h, t in zip(leg.legend_handles, leg.texts) if t.get_text().strip()]
        if not pasangan:
            return
        hl = max(_tinggi_teks(leg.texts[0].get_fontsize()), 1.3)
        baris_h, contoh_w, sela, tepi = 1.8 * hl, 6.0, 1.2, 1.0
        ncol = max(1, getattr(leg, "_ncols", 1))
        nbaris = math.ceil(len(pasangan) / ncol)
        kolom = [pasangan[i * nbaris:(i + 1) * nbaris] for i in range(ncol)]
        lebar_kol = [contoh_w + sela + max(len(_teks(t.get_text())) for _, t in k) * 0.8 * hl + 2.0 for k in kolom if k]
        W = 2 * tepi + sum(lebar_kol)
        H = 2 * tepi + nbaris * baris_h
        b = ax.bbox
        (ax0, ay0), (ax1, ay1) = T([(b.x0, b.y0), (b.x1, b.y1)])
        ax0, ax1 = min(ax0, ax1), max(ax0, ax1)
        ay0, ay1 = min(ay0, ay1), max(ay0, ay1)
        jarak = 1.2
        posisi = {"KA": (ax1 - jarak - W, ay1 - jarak - H), "KI": (ax0 + jarak, ay1 - jarak - H),
                  "KB": (ax1 - jarak - W, ay0 + jarak), "IB": (ax0 + jarak, ay0 + jarak),
                  "TA": ((ax0 + ax1 - W) / 2, ay1 - jarak - H), "TB": ((ax0 + ax1 - W) / 2, ay0 + jarak),
                  "TKA": (ax1 - jarak - W, (ay0 + ay1 - H) / 2), "TKI": (ax0 + jarak, (ay0 + ay1 - H) / 2)}
        for i in range(7):  # kisi calon posisi di dalam bingkai: cari ruang kosong
            for j in range(7):
                posisi[f"K{i}{j}"] = (ax0 + jarak + (ax1 - ax0 - 2 * jarak - W) * i / 6,
                                      ay0 + jarak + (ay1 - ay0 - 2 * jarak - H) * j / 6)
        lb = leg.get_window_extent(self.renderer)
        (lx, ly), = T([((lb.x0 + lb.x1) / 2, (lb.y0 + lb.y1) / 2)])
        urutan = sorted(posisi, key=lambda k: (k.startswith("K") and k[1:].isdigit(),
                                               math.hypot(posisi[k][0] + W / 2 - lx, posisi[k][1] + H / 2 - ly)))
        teks_ada = self.terpasang.get(self.ruang_aktif, [])

        def skor(k):
            x0, y0 = posisi[k]
            kotak_ = box(x0, y0, x0 + W, y0 + H)
            garis = sum(kotak_.intersection(g).length for g in self.garis if kotak_.intersects(g))
            teks = sum(1 for q in teks_ada if box(*q).intersects(kotak_))
            return garis + 20 * teks
        nilai = {k: skor(k) for k in urutan}
        terbaik = min(urutan, key=lambda k: (round(nilai[k], 1), urutan.index(k)))
        x0, y0 = posisi[terbaik]
        x1, y1 = x0 + W, y0 + H
        self.lapis("G-LEGENDA", 7, 0.18)
        self.gaya("ByLayer", "ByLayer", "Continuous")
        self.c("wipeout", {"points": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]})
        self.pline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], True)
        self.kumpul = []
        xk = x0 + tepi
        for k, lk in zip(kolom, lebar_kol):
            for i, (h, t) in enumerate(k):
                cy = y1 - tepi - (i + 0.5) * baris_h
                self.contoh(h, xk, xk + contoh_w, cy, 1.0)
                self.lapis("G-LEGENDA", 7, 0.18)
                self.gaya("ByLayer", "ByLayer", "Continuous")
                self.huruf(False)
                r = self.c("text", {"at": [round(xk + contoh_w + sela, 3), round(cy, 3)], "text": _teks(t.get_text()),
                                    "height": hl, "justify": "ML"})
                self.kumpul.append(r.get("handle"))
                teks_ada.append(self._kotak_teks(xk + contoh_w + sela, cy, hl, len(_teks(t.get_text())), "ML", 0))
            xk += lk
        if self.kumpul:
            self.c("draworder.front", {"handles": [x for x in self.kumpul if x]})
        self.kumpul = None

    def contoh(self, h, x0, x1, y, f):
        """Contoh gaya seri (garis/simbol/arsir) selebar x0-x1 pada ketinggian y."""
        if isinstance(h, Line2D):
            w = _rgb(matplotlib.colors.to_rgba(h.get_color()))
            if h.get_linestyle() not in ("None", "", " ") and h.get_linewidth() > 0:
                self.gaya(w, _lw(h.get_linewidth()), _jenis_garis(h._unscaled_dash_pattern[1]))
                self.pline([(x0, y), (x1, y)])
            m, tambahan, paksa = self.penanda(h)
            mfc = h.get_markerfacecolor()
            isi = not (isinstance(mfc, str) and mfc in ("none", "None")) and not _putih(
                matplotlib.colors.to_rgba(mfc))
            ms = max(h.get_markersize() * 0.3528 * 0.85, 0.6)
            if paksa is not None:
                isi = paksa
            if h.get_marker() in (".", ",") and m != h.get_marker():
                ms = max(ms, 1.0)
            if not m and tambahan:
                m, ms, isi = tambahan, 1.3, False
            if m:
                self.gaya(w, 0.18, "Continuous")
                self.simbol(m, (x0 + x1) / 2, y, ms * f, isi)
        elif isinstance(h, Patch):
            hh = 0.75 * f
            kotak = [(x0, y - hh), (x1, y - hh), (x1, y + hh), (x0, y + hh)]
            pl = self.pola(h.get_facecolor() if h.get_fill() else None, h.get_hatch())
            if pl:
                self.gaya(_rgb(h.get_facecolor()), 0.13, "Continuous")
                self.arsir([kotak], pl[0], pl[1] * f, belakang=False)
            self.gaya(7, 0.18, "Continuous" if h.get_linewidth() >= 0 else "Continuous")
            ec = h.get_edgecolor()
            if h.get_linewidth() > 0 and not (len(ec) > 3 and ec[3] < 0.05):
                self.gaya(_rgb(ec), _lw(h.get_linewidth()), _jenis_garis(h._unscaled_dash_pattern[1]))
            else:
                self.gaya(7, 0.13, "Continuous")
            self.pline(kotak, True)
        elif isinstance(h, PathCollection):
            fc = h.get_facecolor()
            self.gaya(_rgb(fc[0]) if len(fc) else 7, 0.18, "Continuous")
            self.simbol("o", (x0 + x1) / 2, y, 1.2 * f, len(fc) and not _putih(fc[0]))

    # ---------------------------------------------------------------- sumbu model (model space)
    def siapkan_model(self, ax, i):
        cfg = ax._cad
        cfg["_oy"] = -i * 150_000.0 if i else 0.0
        if cfg.get("y_nyata", True) and i:
            cfg["_oy"] = -i * 150_000.0
        ex = cfg["skala"] / cfg.get("vertikal", cfg["skala"])
        (xa, xb), (ya, yb) = sorted(ax.get_xlim()), sorted(ax.get_ylim())
        pos = ax.get_position()
        a0, b0 = pos.x0 * A3[0], pos.y0 * A3[1]
        a1, b1 = pos.x1 * A3[0], pos.y1 * A3[1]
        cx, cy = self._peta_lama((a0 + a1) / 2, (b0 + b1) / 2)
        w = (xb - xa) * 1000 / cfg["skala"]
        h = (yb - ya) * ex * 1000 / cfg["skala"]
        ml, mb, mr, mt = cfg.get("tepi", (13, 11, 13 if cfg.get("jenis") == "penampang" else 3, 3))
        p0, q0 = cx - w / 2, cy - h / 2
        geser_x = max(0, BARU[0] + ml - p0) - max(0, p0 + w + mr - BARU[2])
        geser_y = max(0, BARU[1] + mb - q0) - max(0, q0 + h + mt - BARU[3])
        p0, q0 = p0 + geser_x, q0 + geser_y
        kotak = (p0, q0, p0 + w, q0 + h)
        self.wilayah.append((ax, (a0, b0, a1, b1), kotak))
        pusat = ((xa + xb) / 2 * 1000 - (ml - mr) / 2 * cfg["skala"],
                 (ya + yb) / 2 * ex * 1000 + cfg["_oy"] - (mb - mt) / 2 * cfg["skala"])
        vp = ((p0 - ml, q0 - mb), (p0 + w + mr, q0 + h + mt), pusat, cfg["skala"])
        return vp

    def tepi_model(self, ax):
        """Bingkai/grid koordinat (peta) atau mistar elevasi dan jarak (penampang) di model space."""
        cfg = ax._cad
        T, f = self.ruang(ax)
        (xa, xb), (ya, yb) = sorted(ax.get_xlim()), sorted(ax.get_ylim())
        ex = cfg["skala"] / cfg.get("vertikal", cfg["skala"])
        oy = cfg["_oy"]

        def M(x, y):
            return x * 1000, y * ex * 1000 + oy
        xt = [v for v in ax.get_xticks() if xa - 1e-6 <= v <= xb + 1e-6]
        yt = [v for v in ax.get_yticks() if ya - 1e-6 <= v <= yb + 1e-6]
        d = 1.2 * f
        h = 1.6 * f
        if cfg.get("jenis", "peta") == "peta":
            self.lapis("M-BINGKAI", 7, 0.25)
            self.gaya("ByLayer", "ByLayer", "Continuous")
            self.pline([M(xa, ya), M(xb, ya), M(xb, yb), M(xa, yb)], True)
            self.lapis("M-GRID", 8, 0.13)
            nama = self.g.blok_silang(d / 1000)
            self._kini.pop("layer", None)
            self.lapis("M-GRID", 8, 0.13)
            for x in xt:
                for y in yt:
                    px, py = M(x, y)
                    self.c("insert", {"name": nama, "at": [px, py]})
                    if self.hindari_garis:
                        self.garis += [LineString([(px - d, py), (px + d, py)]), LineString([(px, py - d), (px, py + d)])]
            self.lapis("M-GRID-TEKS", 7, 0.18)
            for x in xt:
                px, py = M(x, ya)
                self.pline([(px, py), (px, py - d)])
                self.tulis((px, py - d - 0.6 * f), f"{x:g}", h, "TC")
            for y in yt:
                px, py = M(xa, y)
                self.pline([(px, py), (px - d, py)])
                self.tulis((px - d - 0.6 * f, py), f"{y:g}", h, "MR")
        else:
            self.lapis("M-MISTAR", 7, 0.25)
            self.gaya("ByLayer", "ByLayer", "Continuous")
            for xx, arah in ((xa, -1), (xb, 1)):
                self.pline([M(xx, ya), M(xx, yb)])
                for y in yt:
                    px, py = M(xx, y)
                    self.pline([(px, py), (px + arah * d, py)])
                    self.tulis((px + arah * (d + 0.6 * f), py), f"{y:+.2f}".replace(".", ",").replace("+0,00", "±0,00"),
                               h, "MR" if arah < 0 else "ML")
            self.pline([M(xa, ya), M(xb, ya)])
            for x in xt:
                px, py = M(x, ya)
                self.pline([(px, py), (px, py - d)])
                self.tulis((px, py - d - 0.6 * f), f"{x:g}", h, "TC")
            if cfg.get("grid_elevasi", True):
                self.lapis("M-GRID", 8, 0.09)
                self.gaya("ByLayer", "ByLayer", "DOT")
                for y in yt:
                    self.pline([M(xa, y), M(xb, y)])
                self.gaya("ByLayer", "ByLayer", "Continuous")
        for t in (ax.xaxis.label, ax.yaxis.label):
            if t.get_text().strip():
                self.lapis("M-GRID-TEKS", 7, 0.18)
                if t is ax.xaxis.label:
                    px, py = M((xa + xb) / 2, ya)
                    self.tulis((px, py - d - 0.6 * f - 2.6 * f), t.get_text(), 1.8 * f, "TC")
                else:
                    px, py = M(xa, (ya + yb) / 2)
                    self.tulis((px - 10.5 * f, py), t.get_text(), 1.8 * f, "MC", 90)

    def legenda_model(self, ax):
        leg = ax.get_legend()
        if leg is None:
            return
        for h, t in zip(leg.legend_handles, leg.texts):
            self.g.legenda_tambah("fungsi", _teks(t.get_text()), f=lambda x0, x1, y, h=h: (
                self.lapis("LEGENDA", 7, 0.18), self.contoh(h, x0, x1, y, 1.0), self.gaya()))

    # ---------------------------------------------------------------- unsur kertas lama
    def isi_kertas(self):
        ker = self.k.kertas
        teks = [t for t in ker.texts if t.get_visible() and t.get_text().strip()]
        judul = [t for t in teks if t.get_fontsize() >= 10]
        sub = []
        for t in judul:
            x, y = t.get_position()
            sub += [u for u in teks if u is not t and abs(u.get_position()[0] - x) < 1 and 0 < y - u.get_position()[1] < 7]
        for t in teks:
            x, y = t.get_position()
            if t in judul or t in sub or x >= self.k.xk:
                continue
            self.teks_mpl(t, self.peta_kertas, 1.0, "KERTAS-TEKS")
        return " ".join(_teks(t.get_text()) for t in sub)

    def skala_batang(self, x, y, panjang_m, skala, bagi, judul):
        mm = panjang_m / skala * 1000
        self.lapis("KERTAS-SKALA", 7, 0.25)
        self.gaya("ByLayer", "ByLayer", "Continuous")
        for i in range(bagi):
            hh = self.pline([(x + i * mm / bagi, y), (x + (i + 1) * mm / bagi, y), (x + (i + 1) * mm / bagi, y + 1.6),
                             (x + i * mm / bagi, y + 1.6)], True)
            if i % 2 == 0:
                self.c("hatch", {"handles": [hh], "pattern": "SOLID", "associative": False})
        for i in range(bagi + 1):
            self.tulis((x + i * mm / bagi, y + 2.4), f"{panjang_m * i / bagi:g}", 1.4, "BC")
        self.tulis((x + mm + 1.5, y + 0.2), "m", 1.4)
        self.tulis((x, y - 3.0), _teks(judul or f"Skala grafis 1:{skala}").upper(), 1.6)

    def panah_utara(self, x, y, ukuran):
        self.lapis("KERTAS-SKALA", 7, 0.25)
        self.gaya("ByLayer", "ByLayer", "Continuous")
        self.huruf(False)
        self.g.panah_utara(x, y, ukuran)  # block PANAH_UTARA
        self._kini.pop("gaya", None)

    # ---------------------------------------------------------------- legenda KETERANGAN
    def legenda_keterangan(self):
        g = self.g
        if self.k.unit:
            import tahap2_stratigrafi as st

            for u in self.k.unit:
                nama, uscs, *_ = st.UNIT[u]
                g.legenda_tambah("arsir", f"{u} {nama} ({uscs})", pola=POLA_UNIT[u], skala_pola=1.0)
        for jenis, ket, gy in self.k.butir_legenda:
            if jenis == "simbol":
                g.legenda_tambah("fungsi", ket, f=lambda x0, x1, y, gy=gy: (
                    self.lapis("LEGENDA", 7, 0.18), self.gaya(7, 0.18, "Continuous"),
                    self.simbol(gy.get("simbol", "o"), (x0 + x1) / 2, y, gy.get("ukuran", 1.8), gy.get("isi", True)),
                    self.gaya()))
            else:
                g.legenda_tambah(jenis, ket, **gy)

    # ---------------------------------------------------------------- utama
    def buat(self, dwg, halaman, png):
        self.fig.canvas.draw()
        self.renderer = self.fig.canvas.get_renderer()
        k = self.k
        semua = [ax for ax in self.fig.axes if ax is not k.kertas]
        model = [ax for ax in semua if getattr(ax, "_cad", None)]
        grafik = [ax for ax in semua if not getattr(ax, "_cad", None)]
        skala = model[0]._cad["skala"] if model else 100
        a = k.atribut
        with Gambar(skala) as g:
            self.g = g
            g.cmd("wipeout", {"frames": "off"})
            vps = [self.siapkan_model(ax, i) for i, ax in enumerate(model)]
            for ax in model:
                self.hindari_garis = ax._cad.get("jenis", "peta") == "peta"
                self.garis = []
                self.tepi_model(ax)  # mistar/grid dulu: label isi yang menabrak angka mistar yang digeser
                self.gambar_isi(ax, "M")
                self.hindari_garis = False
                self.legenda_model(ax)
            self.reset()
            self.c("layer.current", {"name": "0"})
            self.gaya()
            self.legenda_keterangan()
            g.lembar(a["nomor"], a["judul"], a["skala"].upper(), None, subjudul="", lembar=a["lembar"],
                     status=a["status"], catatan=k.butir_catatan, tanggal=a["tanggal"], revisi=a["revisi"],
                     viewports=vps, judul_kop=JUDUL_KOP.get(a["nomor"]))
            self.reset()
            self.ruang_aktif = "kertas"
            sub = self.isi_kertas()
            if sub:
                self.huruf(False)
                self.lapis("KERTAS-TEKS", 7, 0.35)
                self.gaya()
                import textwrap

                for i, s in enumerate(textwrap.wrap(sub, 95)[:2]):
                    self.c("text", {"at": [AREA[0] + 22, AREA[1] + 2 - 3 * i], "text": s, "height": tinggi(6.5)})
            for ax in grafik:
                self.hindari_garis, self.garis = True, []  # label dan legenda tidak boleh menyentuh kurva
                self.gambar_isi(ax, "G")
                self.hindari_garis = False
                self.bingkai_grafik(ax)
                self.legenda_grafik(ax)
                self.judul_sumbu(ax)
                self.garis = []
            for ax in model:
                self.judul_sumbu(ax)
            for x, y, pj, sk, bagi, judul in k.skala_:
                bx, by = self.kertas_baru(x, y)
                self.skala_batang(bx, by, pj, sk, bagi, judul)
            for x, y, u in k.utara_:
                bx, by = self.kertas_baru(x, y)
                self.panah_utara(bx, by, u * 0.9)
            self.reset()
            self.c("layer.current", {"name": "0"})
            self.gaya()
            self.huruf(False)
            g.simpan(dwg, halaman, png)
        return dwg
