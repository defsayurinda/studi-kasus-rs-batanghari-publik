"""Gambar isi lembar (grafik, peta, penampang) langsung ke CADCraft sebagai entitas CAD asli.

Renderer matplotlib khusus: setiap garis menjadi POLYLINE, setiap bidang berwarna menjadi HATCH SOLID, arsiran
menjadi HATCH pola ANSI, setiap teks menjadi TEXT Arial. Koordinat dalam mm kertas (A3, titik nol kiri bawah).
Layer: GT-GARIS, GT-ISI, GT-ARSIR, GT-TEKS. Kop dari block KOP_A3 (cad_kop.py), bukan dari renderer ini.
"""
import re

import numpy as np

from matplotlib.backend_bases import GraphicsContextBase, RendererBase
from matplotlib.backends.backend_agg import RendererAgg
from shapely.geometry import LineString, Polygon, box

from cad_kop import tinggi

PT = 25.4 / 72  # mm per poin (figur digambar pada 72 dpi: 1 piksel = 1 poin)
LW_STD = [0.05, 0.09, 0.13, 0.15, 0.18, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.53, 0.6, 0.7, 0.8, 0.9, 1.0, 1.06, 1.2]
TEX = {r"\sigma": "σ", r"\gamma": "γ", r"\phi": "φ", r"\varphi": "φ", r"\Delta": "Δ", r"\alpha": "α",
       r"\beta": "β", r"\tau": "τ", r"\mu": "μ", r"\leq": "≤", r"\geq": "≥", r"\times": "×", r"\prime": "′",
       r"\circ": "°", r"\pm": "±", r"\,": " ", r"\;": " ", r"\ ": " "}
SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def teks_biasa(s):
    """Ubah teks mathtext sederhana ($...$) menjadi Unicode biasa."""
    if "$" not in s:
        return s
    for k, v in TEX.items():
        s = s.replace(k, v)
    s = re.sub(r"\\mathrm\{([^}]*)\}|\\text\{([^}]*)\}", lambda m: m.group(1) or m.group(2), s)
    s = re.sub(r"\^\{([^}]*)\}|\^(\S)", lambda m: (m.group(1) or m.group(2)).translate(SUP), s)
    s = re.sub(r"_\{([^}]*)\}|_(\S)", lambda m: (m.group(1) or m.group(2)).translate(SUB), s)
    return s.replace("$", "").replace("{", "").replace("}", "").replace("\\", "")


def _rgb(c):
    return ",".join(str(int(round(min(max(v, 0), 1) * 255))) for v in c[:3])


def _lw(pt):
    mm = pt * PT
    return min(LW_STD, key=lambda v: abs(v - mm))


class RendererCAD(RendererBase):
    def __init__(self, cad, lebar_pt, tinggi_pt):
        super().__init__()
        self.cad = cad
        self.width, self.height = lebar_pt, tinggi_pt
        self._agg = RendererAgg(int(lebar_pt), int(tinggi_pt), 72)
        self._kini = {}
        self._lt = {}
        self.jumlah = 0
        for nama, warna, lw in (("GT-ISI", 8, 0.0), ("GT-ARSIR", 8, 0.13), ("GT-GARIS", 7, 0.25),
                                ("GT-TEKS", 7, 0.18)):
            cad.cmd("layer.new", {"name": nama, "color": warna, "lineweight": max(lw, 0.05)})

    # --- metrik teks memakai Agg supaya tata letak sama dengan matplotlib
    def get_text_width_height_descent(self, s, prop, ismath):
        return self._agg.get_text_width_height_descent(s, prop, ismath)

    def get_canvas_width_height(self):
        return self.width, self.height

    def points_to_pixels(self, points):
        return points

    def flipy(self):
        return False

    def new_gc(self):
        return GraphicsContextBase()

    def draw_image(self, gc, x, y, im):  # tidak dipakai gambar proyek
        pass

    # --- keadaan CAD (dikirim hanya bila berubah)
    def _set(self, kunci, nilai, perintah, params):
        if self._kini.get(kunci) != nilai:
            self.cad.cmd(perintah, params)
            self._kini[kunci] = nilai

    def _layer(self, nama):
        self._set("layer", nama, "layer.current", {"name": nama})

    def _warna(self, rgb):
        self._set("warna", rgb, "color", {"color": rgb})

    def _tebal(self, mm):
        self._set("lw", mm, "lweight", {"lineweight": mm})

    def _garis_jenis(self, gc):
        off, seq = gc.get_dashes()
        if not seq:
            nama = "Continuous"
        else:
            mm = [max(v * PT, 0.05) for v in seq]
            kunci = tuple(round(v, 2) for v in mm)
            if kunci not in self._lt:
                nama = f"MPL{len(self._lt) + 1}"
                pola = ",".join(f"{v:.2f}" if i % 2 == 0 else f"-{v:.2f}" for i, v in enumerate(kunci))
                self.cad.cmd("linetype", {"text": f"*{nama},garis putus matplotlib\nA,{pola}\n", "load": nama})
                self._lt[kunci] = nama
            nama = self._lt[kunci]
        self._set("lt", nama, "linetype", {"current": nama})

    # --- geometri
    @staticmethod
    def _potong(gc):
        r = gc.get_clip_rectangle()
        if r is None:
            return None
        x0, y0, x1, y1 = r.extents
        return box(x0 - 0.01, y0 - 0.01, x1 + 0.01, y1 + 0.01)

    def _cincin_isi(self, poligon, potong):
        hasil = []
        for p in self._bersih(poligon):
            if len(p) < 3:
                continue
            if potong is None:
                hasil.append([[x * PT, y * PT] for x, y in p])
                continue
            try:
                g = Polygon(p).buffer(0).intersection(potong)
            except Exception:
                continue
            for q in getattr(g, "geoms", [g]):
                if q.is_empty or q.geom_type != "Polygon":
                    continue
                for ring in [q.exterior, *q.interiors]:
                    hasil.append([[x * PT, y * PT] for x, y in list(ring.coords)[:-1]])
        return hasil

    @staticmethod
    def _bersih(daftar):
        """Pecah garis pada titik NaN/Inf (celah data matplotlib)."""
        hasil = []
        for p in daftar:
            ok = np.isfinite(p).all(axis=1)
            if ok.all():
                hasil.append(p)
                continue
            awal = None
            for i, b in enumerate(list(ok) + [False]):
                if b and awal is None:
                    awal = i
                elif not b and awal is not None:
                    hasil.append(p[awal:i])
                    awal = None
        return hasil

    def _garis_potong(self, garis, potong):
        hasil = []
        for p in self._bersih(garis):
            if len(p) < 2:
                continue
            tutup = len(p) > 2 and abs(p[0][0] - p[-1][0]) < 1e-6 and abs(p[0][1] - p[-1][1]) < 1e-6
            if potong is None or LineString(p).within(potong):
                hasil.append(([[x * PT, y * PT] for x, y in (p[:-1] if tutup else p)], tutup))
                continue
            g = LineString(p).intersection(potong)
            for q in getattr(g, "geoms", [g]):
                if q.geom_type == "LineString" and not q.is_empty and q.length > 1e-3:
                    hasil.append(([[x * PT, y * PT] for x, y in q.coords], False))
        return hasil

    def draw_path(self, gc, path, transform, rgbFace=None):
        potong = self._potong(gc)
        if rgbFace is not None and (len(rgbFace) < 4 or rgbFace[3] > 0):
            cincin = self._cincin_isi(path.to_polygons(transform, closed_only=True), potong)
            if cincin:
                alpha = (rgbFace[3] if len(rgbFace) > 3 else 1) * (gc.get_alpha() or 1)
                self._isi(cincin, _rgb(rgbFace), "SOLID", alpha)
        hatch = gc.get_hatch()
        if hatch:
            cincin = self._cincin_isi(path.to_polygons(transform, closed_only=True), potong)
            if cincin:
                self._arsir(cincin, hatch, _rgb(gc.get_hatch_color()))
        lw = gc.get_linewidth()
        warna = gc.get_rgb()
        if lw > 0 and (len(warna) < 4 or warna[3] > 0):
            garis = path.to_polygons(transform, closed_only=False)
            garis = self._garis_potong(garis, potong)
            if garis:
                self._layer("GT-GARIS")
                self._warna(_rgb(warna))
                self._tebal(_lw(lw))
                self._garis_jenis(gc)
                for p, tutup in garis:
                    if len(p) >= 2:
                        self.cad.cmd("pline", {"vertices": p, "closed": tutup})
                        self.jumlah += 1

    def _batas(self, cincin):
        self._set("lt", "Continuous", "linetype", {"current": "Continuous"})
        return [self.cad.cmd("pline", {"vertices": c, "closed": True})["handle"] for c in cincin]

    def _isi(self, cincin, rgb, pola, alpha=1.0):
        self._layer("GT-ISI")
        h = self._batas(cincin)
        self._warna(rgb)
        r = self.cad.cmd("hatch", {"handles": h, "pattern": pola, "associative": False, "style": "normal"})
        self.cad.cmd("erase", {"handles": h})
        if r.get("handles"):  # CADCraft tidak menjaga urutan antar-hatch; paksa urutan pembuatan
            self.cad.cmd("draworder.front", {"handles": r["handles"]})
        if alpha < 0.99 and r.get("handles"):
            self.cad.cmd("properties.set", {"handles": r["handles"], "transparency": int(round((1 - alpha) * 90))})
        self.jumlah += 1

    def _arsir(self, cincin, hatch, rgb):
        n = max(len(hatch), 1)
        c = hatch[0]
        pola, sudut = {"/": ("ANSI31", 0), "\\": ("ANSI31", 90), "x": ("ANSI37", 0), "X": ("ANSI37", 0),
                       "-": ("ANSI31", 45), "|": ("ANSI31", -45), "+": ("NET", 0), ".": ("DOTS", 0),
                       "o": ("DOTS", 0), "O": ("DOTS", 0), "*": ("DOTS", 0)}.get(c, ("ANSI31", 0))
        skala = max(0.2, 1.4 / n) if pola != "DOTS" else max(0.15, 0.8 / n)
        self._layer("GT-ARSIR")
        self._tebal(0.13)
        h = self._batas(cincin)
        self._warna(rgb)
        r = self.cad.cmd("hatch", {"handles": h, "pattern": pola, "scale": skala, "angle": sudut,
                                   "associative": False, "style": "normal"})
        self.cad.cmd("erase", {"handles": h})
        if r.get("handles"):
            self.cad.cmd("draworder.front", {"handles": r["handles"]})
        self.jumlah += 1

    def draw_text(self, gc, x, y, s, prop, angle, ismath=False, mtext=None):
        s = teks_biasa(s).strip("\n")
        if not s.strip():
            return
        r = self._potong(gc)
        if r is not None and not r.buffer(2).contains(box(x, y, x + 0.1, y + 0.1)):
            return
        tebal = prop.get_weight() in ("bold", "heavy", "black", "semibold", "demibold", 600, 700, 800, 900)
        self._layer("GT-TEKS")
        self._warna(_rgb(gc.get_rgb()))
        self._set("gaya", tebal, "style.current", {"name": "ARIAL_TEBAL" if tebal else "ARIAL"})
        self.cad.cmd("text", {"at": [x * PT, y * PT], "text": s, "height": tinggi(prop.get_size_in_points()),
                              "rotation": float(angle) % 360 if angle else 0.0, "justify": "L"})
        self.jumlah += 1


def gambar_ke_cad(fig, cad):
    """Gambar seluruh isi figur ke sesi CADCraft yang aktif."""
    dpi_asal = fig.dpi
    fig.patch.set_visible(False)  # kertas sudah putih; latar figur dan sumbu tidak perlu jadi hatch
    for ax in fig.axes:
        if ax.patch.get_facecolor()[:3] == (1.0, 1.0, 1.0):
            ax.patch.set_visible(False)
    fig.set_dpi(72)
    w, h = fig.get_size_inches() * 72
    r = RendererCAD(cad, w, h)
    fig.draw(r)
    fig.set_dpi(dpi_asal)
    return r.jumlah

