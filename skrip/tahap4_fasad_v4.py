"""Fasad V4 mengikuti foto acuan Defsa (20 Nov 2026): tampilan, papan nama, dan lingkungan; struktur tetap.

Arahan Defsa: "fasadnya, papan nama, lingkungan dll [seperti foto], untuk struktur tetap sama". Foto acuan (internet,
hanya acuan, tidak di-commit): `acuan/privat/Referensi Fasad RS dari Defsa.jpg`. Model dibangun di atas salinan model
struktur LOD 300 (4.9) tanpa mengubah unsur struktur:
  menara  panel putih dengan jendela pita, pita kaca biru vertikal, dinding tirai kaca biru di tengah sisi panjang;
  podium  panel abu dengan jendela pita; mahkota menara panel abu tua setinggi parapet;
  nama    logo "H" biru dan huruf "RUMAH SAKIT TEPIAN BATANGHARI" (family generik, huruf blok 5 × 7) di menara;
  tapak   halaman rumput +12,05, parkir aspal di tenggara dengan mobil, pohon di tepi sungai, parkir, dan jalan.
Keluaran: `model/RSTB-ARS-T4-Fasad-V4.bimc` dan render `04 Struktur Atas/Gambar/4.10 Fasad V4 *.png`.
DATA SIMULASI. Disusun AI atas permintaan Defsa (20 Nov 2026). Status: purwarupa render untuk Tahap 7, bukan
pengganti fasad V3 (koreksi Defsa 20 Nov 2026: foto hanya acuan). Berat fasad V4
(panel ringan dan kaca) lebih ringan dari V3; detail angkur fasad dan sengkang balok tepi 4.10 tetap (konservatif).
"""
from __future__ import annotations

import sys
from pathlib import Path

from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_beban as tb  # noqa: E402
import tahap4_bim as bim  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
BIMC = AKAR / "model" / "RSTB-ARS-T4-Fasad-V4.bimc"
GAMBAR = AKAR / "04 Struktur Atas" / "Gambar"
NAMA_RS = "RUMAH SAKIT TEPIAN BATANGHARI"
HALAMAN = 12.05 - tb.LEVEL["LT1"]          # m, halaman +12,05 terhadap LT1 (3.3)
PERSIL = (0.0, 0.0, 140.0, 90.0)           # 3.2 (TOR 4.1)
PARKIR = (90.0, 6.0, 136.0, 40.0)          # [Asumsi tata letak: tenggara, di depan gedung utilitas]
JALAN = [(84.6, 40.0, 92.0, 90.0)]         # jalan masuk dari jalan utara ke parkir dan IGD [Asumsi]
MENARA_X = (tb.MENARA.bounds[0], tb.MENARA.bounds[2])
STRIP_X = [(31.6, 34.4), (69.6, 72.4)]    # pita kaca biru vertikal sisi panjang menara
TIRAI_X = (44.0, 60.0)                     # dinding tirai kaca di tengah sisi panjang
STRIP_Y = [(37.6, 40.4)]                   # pita kaca di sisi pendek menara
WARNA = {"Panel putih": ("#E9E9E5", 0), "Panel abu": ("#A7ACAF", 0), "Panel abu tua": ("#5D6367", 0),
         "Kaca biru": ("#3F6E96", 35), "Kaca pita": ("#6F93AE", 45), "Logo biru": ("#1F5AA6", 0),
         "Huruf putih": ("#FAFAFA", 0), "Rumput": ("#6E9A4A", 0), "Aspal": ("#4A4C4F", 0), "Batang": ("#6B4F35", 0),
         "Daun": ("#3E7B3A", 0), "Mobil putih": ("#EDEDED", 0), "Mobil hitam": ("#222222", 0),
         "Mobil merah": ("#9B2D2A", 0), "Mobil abu": ("#8C9196", 0), "Mobil hijau": ("#2F6B5A", 0)}

# huruf blok 5 × 7 (baris atas ke bawah) untuk papan nama
FONT = {
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    " ": ["00000"] * 7,
}
SEL_HURUF, MAJU = 200, 1200                 # mm: sel huruf, jarak antarhuruf (huruf 1.000 × 1.400)


def kotak_huruf(teks, sel=SEL_HURUF, maju=MAJU):
    """Persegi (x0, z0, x1, z1) mm huruf blok, baris dirangkai per deret sel; teks berpusat di x = 0."""
    lebar = len(teks) * maju - (maju - 5 * sel)
    out = []
    for i, c in enumerate(teks):
        x0 = -lebar / 2 + i * maju
        for r, baris in enumerate(FONT[c]):
            z0 = (6 - r) * sel
            j = 0
            while j < 5:
                if baris[j] == "1":
                    k = j
                    while k < 5 and baris[k] == "1":
                        k += 1
                    out.append((x0 + j * sel, z0, x0 + k * sel, z0 + sel))
                    j = k
                else:
                    j += 1
    return out, lebar


def _kotak(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def zona_sisi(p0, p1):
    """Bagi satu sisi bidang fasad (m) menjadi (a, b, jenis): 'tirai', 'strip', 'pita_putih' (menara), 'pita_abu'."""
    datar = abs(p0[1] - p1[1]) < 1e-6
    u0, u1 = (p0[0], p1[0]) if datar else (p0[1], p1[1])
    lo, hi = min(u0, u1), max(u0, u1)
    potong = {lo, hi}
    khusus = STRIP_X + [TIRAI_X] if datar else STRIP_Y
    for a, b in khusus:
        potong |= {v for v in (a, b) if lo < v < hi}
    if not datar:
        potong |= {v for v in (tb.MENARA.bounds[3] + bim.FASAD_JARAK,) if lo < v < hi}
    if datar:
        potong |= {v for v in (MENARA_X[0] - bim.FASAD_JARAK,) if lo < v < hi}
    titik = sorted(potong)
    menara = tb.MENARA.buffer(bim.FASAD_JARAK + 0.05, join_style=2)
    out = []
    for a, b in zip(titik[:-1], titik[1:]):
        m = (a + b) / 2
        pm = Point(m, p0[1]) if datar else Point(p0[0], m)
        if not menara.contains(pm):
            jenis = "pita_abu"
        elif datar and TIRAI_X[0] <= m <= TIRAI_X[1]:
            jenis = "tirai"
        elif any(x0 <= m <= x1 for x0, x1 in (STRIP_X if datar else STRIP_Y)):
            jenis = "strip"
        else:
            jenis = "pita_putih"
        q0 = (a, p0[1]) if datar else (p0[0], a)
        q1 = (b, p0[1]) if datar else (p0[0], b)
        if (u1 < u0):   # pertahankan arah sisi (muka luar di kiri arah gambar BIMCraft)
            q0, q1 = q1, q0
        out.append((q0, q1, jenis))
    if u1 < u0:
        out.reverse()
    return out


def bangun(sumber=None, render=True):
    from bimcraft import Sesi
    mm = bim.mm
    hitung = {"dinding": 0, "pohon": 0, "mobil": 0}
    with Sesi(sumber or bim.BIMC) as b:
        for nama, (warna, tr) in WARNA.items():
            b.cmd("material", {"name": nama, "color": warna, "transparency": tr})
        for nama, bahan, t in (("FS-PanelPutih", "Panel putih", 50), ("FS-PanelAbu", "Panel abu", 50),
                               ("FS-PanelAbuTua", "Panel abu tua", 50), ("FS-KacaBiru", "Kaca biru", 30),
                               ("FS-KacaPita", "Kaca pita", 30)):
            b.cmd("type", {"category": "wall", "name": nama,
                           "layers": [{"function": "finish", "material": bahan, "thickness": t}]})
        for nama, bahan in (("TP-Rumput", "Rumput"), ("TP-Aspal", "Aspal")):
            b.cmd("type", {"category": "floor", "name": nama,
                           "layers": [{"function": "finish", "material": bahan, "thickness": 100}]})

        def dinding(q0, q1, tipe, lv, base, h):
            b.cmd("wall", {"points": [mm(*q0), mm(*q1)], "type": tipe, "level": lv, "base_offset": round(base),
                           "height": round(h)})
            hitung["dinding"] += 1

        # fasad per sisi per tingkat
        for poli, a, c in bim._pita():
            tingkat = tb.URUT[tb.URUT.index(a):tb.URUT.index(c) + 1]
            for p0, p1 in bim._sisi(poli):
                for q0, q1, jenis in zona_sisi(p0, p1):
                    for lo, hi in zip(tingkat[:-1], tingkat[1:]):
                        h = (tb.LEVEL[hi] - tb.LEVEL[lo]) * 1000
                        if jenis in ("tirai", "strip"):
                            dinding(q0, q1, "FS-KacaBiru", lo, 0, h)
                        else:
                            panel = "FS-PanelPutih" if jenis == "pita_putih" else "FS-PanelAbu"
                            dinding(q0, q1, panel, lo, 0, 1100)
                            dinding(q0, q1, "FS-KacaPita", lo, 1100, 1800)
                            dinding(q0, q1, panel, lo, 2900, h - 2900)
        # mahkota menara: panel abu tua setinggi 1,8 m di atas atap
        for p0, p1 in bim._sisi(tb.MENARA):
            dinding(p0, p1, "FS-PanelPutih", "ATAP", 0, 1800)   # pita mahkota putih, nama biru seperti logo foto

        # logo H dan papan nama (family generik, menghadap selatan: +y family ke dalam gedung)
        h_kotak = [(-1500, 0, -900, 3000), (900, 0, 1500, 3000), (-900, 1200, 900, 1800)]
        b.cmd("family", {"name": "RSTB Logo H", "category": "generic", "forms": [
            {"plane": "xz", "profile": _kotak(-1600, -100, 1600, 3100), "from": -150, "to": 150, "material": "Logo biru"}] +
            [{"plane": "xz", "profile": _kotak(x0, z0, x1, z1), "from": f, "to": t, "material": "Huruf putih"}
             for f, t in ((-250, -150), (150, 250))
             for x0, z0, x1, z1 in h_kotak], "types": {"Standar": {}}})
        # papan nama: satu family per huruf (batas 256 bentuk per family), ditempatkan berderet
        y_muka = (tb.MENARA.bounds[1] - bim.FASAD_JARAK) * 1000
        lebar = len(NAMA_RS) * MAJU - (MAJU - 5 * SEL_HURUF)
        for c in sorted(set(NAMA_RS) - {" "}):
            kotak, _ = kotak_huruf(c)
            b.cmd("family", {"name": f"RSTB Huruf {c}", "category": "generic", "forms": [
                {"plane": "xz", "profile": _kotak(x0, z0, x1, z1), "from": -150, "to": 150, "material": "Logo biru"}
                for x0, z0, x1, z1 in kotak], "types": {"Standar": {}}})
        for i, c in enumerate(NAMA_RS):
            if c != " ":
                x = 55000 - lebar / 2 + i * MAJU + 2.5 * SEL_HURUF
                b.cmd("component", {"family": f"RSTB Huruf {c}", "at": [round(x), round(y_muka - 200)], "level": "ATAP",
                                    "offset": 200})
        b.cmd("component", {"family": "RSTB Logo H", "at": [24500, round(y_muka - 300)], "level": "LT6", "offset": 700})
        x_timur = (MENARA_X[1] + bim.FASAD_JARAK) * 1000
        b.cmd("component", {"family": "RSTB Logo H", "at": [round(x_timur + 300), 39000], "level": "LT6", "offset": 700,
                            "angle": 90})

        # tapak: rumput, parkir aspal, jalan masuk
        bang = [mm(*p) for p in list(tb.PODIUM.buffer(bim.FASAD_JARAK, join_style=2).exterior.coords)[:-1]]
        b.cmd("floor", {"boundary": [mm(*p) for p in _kotak(*PERSIL)], "openings": [bang], "level": "LT1",
                        "offset": round(HALAMAN * 1000) - 100, "type": "TP-Rumput"})
        for k in [PARKIR] + JALAN:
            b.cmd("floor", {"boundary": [mm(*p) for p in _kotak(*k)], "level": "LT1",
                            "offset": round(HALAMAN * 1000) - 60, "type": "TP-Aspal"})
        # pohon dan mobil (family generik)
        b.cmd("family", {"name": "RSTB Pohon", "category": "generic", "forms": [
            {"circle": {"centre": [0, 0], "radius": 160}, "from": 0, "to": 2600, "material": "Batang"},
            {"circle": {"centre": [0, 0], "radius": 1500}, "from": 2400, "to": 3600, "material": "Daun"},
            {"circle": {"centre": [0, 0], "radius": 2000}, "from": 3600, "to": 4800, "material": "Daun"},
            {"circle": {"centre": [0, 0], "radius": 1300}, "from": 4800, "to": 5800, "material": "Daun"}], "types": {"Standar": {}}})
        b.cmd("family", {"name": "RSTB Mobil", "category": "generic",
                         "parameters": [{"name": "Warna", "kind": "material", "value": "Mobil putih"}],
                         "forms": [{"profile": _kotak(-2250, -900, 2250, 900), "from": 250, "to": 1050,
                                    "material": "Warna"},
                                   {"profile": _kotak(-1300, -800, 1100, 800), "from": 1050, "to": 1550,
                                    "material": "Kaca pita"}],
                         "types": {w.split()[-1].title(): {"Warna": w} for w in WARNA if w.startswith("Mobil")}})
        z0 = round(HALAMAN * 1000)
        pohon = [(x, 14.0) for x in range(6, 86, 8)] + [(x, 86.0) for x in range(6, 84, 9)] + \
                [(4.0, y) for y in range(24, 84, 8)] + [(x, 23.0) for x in range(94, 136, 8)] + \
                [(88.2, y) for y in range(44, 88, 8)]
        for x, y in pohon:
            b.cmd("component", {"family": "RSTB Pohon", "at": mm(x, y), "level": "LT1", "offset": z0})
            hitung["pohon"] += 1
        warna = [w.split()[-1].title() for w in WARNA if w.startswith("Mobil")]
        n = 0
        for baris, (y, sudut) in enumerate(((9.5, 90), (18.5, 90), (28.5, 90), (37.0, 90))):
            for i, x in enumerate(range(93, 135, 3)):
                if (i * 7 + baris * 3) % 5 == 0:     # sebagian kosong [pola tetap]
                    continue
                b.cmd("component", {"family": "RSTB Mobil", "type": warna[n % len(warna)], "at": mm(x, y),
                                    "level": "LT1", "offset": z0, "angle": sudut})
                n += 1
        hitung["mobil"] = n
        b.cmd("project_info", {"status": "Fasad V4 purwarupa render Tahap 7 (acuan foto Defsa): panel putih-abu, kaca biru, "
                                         "papan nama, tapak; struktur LOD 300 tetap"})
        b.simpan(BIMC)
        if render:
            b.cmd("graphics", {"view": "{3D}", "hide": ["levels", "grids"]})
            for nama, az, el in (("Depan", -55, 10), ("Udara", -40, 32)):
                b.alat("render", {"view": "{3D}", "path": str(GAMBAR / f"4.10 Fasad V4 {nama}.png"), "width": 1800,
                                  "height": 1100, "azimuth": az, "elevation": el})
    return hitung


if __name__ == "__main__":
    print(bangun())
