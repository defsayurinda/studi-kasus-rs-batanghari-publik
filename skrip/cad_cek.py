"""Pemeriksa kerapian DWG: teks dan angka ukur tidak boleh saling menumpuk (arahan Defsa 19 Nov 2026).

Membaca DWG hasil cad_lembar di CADCraft (find_text + query_entities Dimension), memperkirakan kotak tiap teks
(Times New Roman kapital: lebar ±0,62 × tinggi per huruf), lalu melaporkan pasangan yang bertumpuk, terpisah untuk
model space (layer C-*) dan paper space (KOP, KERTAS-TEKS).
Jalankan:  .venv\\Scripts\\python.exe skrip\\cad_cek.py "<berkas.dwg>"
"""
import math
import sys

from cadcraft import Sesi

LEBAR_HURUF = 0.90
KERTAS = {"KOP", "KERTAS-TEKS", "VIEWPORT"}


def _kotak(at, h, n, rot):
    w = LEBAR_HURUF * h * n
    x, y = at
    r = math.radians(rot or 0)
    pts = [(x, y), (x + w * math.cos(r), y + w * math.sin(r)),
           (x + w * math.cos(r) - h * math.sin(r), y + w * math.sin(r) + h * math.cos(r)),
           (x - h * math.sin(r), y + h * math.cos(r))]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _tumpang(a, b, susut=0.12):
    """Kotak a dan b bertumpuk (setelah disusutkan sedikit agar sentuhan tepi tidak dihitung)."""
    def s(k):
        dx, dy = (k[2] - k[0]) * susut / 2, (k[3] - k[1]) * susut / 2
        return k[0] + dx, k[1] + dy, k[2] - dx, k[3] - dy
    a, b = s(a), s(b)
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def baca(dwg):
    with Sesi() as c:
        c.buka(dwg)
        c.cmd("layout.set", {"name": "Model"})
        teks = [("model", t) for t in c.alat("find_text", {"limit": 5000}).get("texts", [])]
        dims = c.alat("query_entities", {"type": "Dimension", "limit": 5000}).get("entities", [])
        for lay in c.alat("inspect_drawing", {}).get("layouts", []):
            if lay == "Model":
                continue
            c.cmd("layout.set", {"name": lay})
            teks += [(f"kertas {lay}", t) for t in c.alat("find_text", {"limit": 5000}).get("texts", [])]
    hasil, dilihat = [], set()
    for ruang, t in teks:
        s = (t.get("text") or "").strip()
        kunci = (ruang, t.get("handle"))
        if not s or kunci in dilihat:
            continue
        dilihat.add(kunci)
        hasil.append((ruang, s, _kotak(t["at"], t["height"], len(s), t.get("rotation", 0))))
    for d in dims:
        g = d.get("geometry", {})
        m = g.get("textMid")
        if not m:
            continue
        nilai = f"{g.get('measurement', 0) / 1000:.2f}".replace(".", ",")
        rot = 90 if abs(g.get("p13", {}).get("x", 0) - g.get("p14", {}).get("x", 0)) < 1 else 0
        # DIMTXT × DIMSCALE; DIMSCALE dibaca dari jarak teks ke garis ukur (= 1,68 × DIMSCALE pada gaya PROYEK:
        # 504 di 1:300, 1260 di 1:750), bawaan 1:750 bila tidak terbaca
        d0 = g.get("defpt", {})
        off = abs(m["x"] - d0.get("x", m["x"])) if rot else abs(m["y"] - d0.get("y", m["y"]))
        h = 1.8 * (off / 1.68 if off > 0 else 750)
        w = LEBAR_HURUF * h * len(nilai)
        if rot:
            k = (m["x"] - h / 2, m["y"] - w / 2, m["x"] + h / 2, m["y"] + w / 2)
        else:
            k = (m["x"] - w / 2, m["y"] - h / 2, m["x"] + w / 2, m["y"] + h / 2)
        hasil.append(("model", f"[ukur {nilai}]", k))
    return hasil


def cek(dwg):
    item = baca(dwg)
    masalah = []
    for i in range(len(item)):
        for j in range(i + 1, len(item)):
            if item[i][0] == item[j][0] and _tumpang(item[i][2], item[j][2]):
                masalah.append((item[i][0], item[i][1], item[j][1]))
    return masalah


if __name__ == "__main__":
    m = cek(sys.argv[1])
    for r in m:
        print(r)
    print(f"{len(m)} pasangan bertumpuk")
