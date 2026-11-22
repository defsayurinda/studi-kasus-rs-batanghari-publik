"""Langkah 7.6: DED MEP dasar (koordinasi saja, keputusan rencana 8): GM-01..GM-06 di CADCraft (KOP_A3).
Shaft dan lubang pelat (tahap4_bim.SHAFT + IFC STR 7.3), ruang alat atap podium (letak 7.3), zona MRI, bukaan
dinding inti (IFC), beban alat per lantai (tahap4_beban.alat_per_lantai). Posisi alat: tahap7_federasi.ALAT. DATA SIMULASI.
Jalankan (satu lembar per proses, timeout di pemanggil):
  .venv\\Scripts\\python.exe skrip\\tahap7_gambar_mep.py GM-02 | ... | --pdf | --cek | --data
"""
from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_gambar_ded as t4g  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "07 DED dan RKS"
DWG = KELUAR / "Gambar" / "DWG"
PLOT = KELUAR / "Gambar" / "_plot_mep"
PNG = KELUAR / "Gambar"
PDF = KELUAR / "7.6 Gambar MEP Dasar DED.pdf"
IFC_STR = AKAR / "model" / "RSTB-STR-T7-LOD300.ifc"
STATUS = "DISETUJUI 22 NOV 2026"
TANGGAL = "NOVEMBER 2026"
H = 1.6
LANTAI = ["LT1", "LT2", "LT3", "LT4", "LT5", "LT6", "ATAP"]
NAMA = {"GM-01": "GM-01 Daftar Gambar dan Catatan MEP", "GM-02": "GM-02 Denah Shaft dan Lubang Pelat",
        "GM-03": "GM-03 Ruang Alat Atap Podium", "GM-04": "GM-04 Zona MRI LT1",
        "GM-05": "GM-05 Bukaan Dinding Inti", "GM-06": "GM-06 Beban Alat per Lantai"}
JUDUL = {"GM-01": "Daftar gambar, lingkup, dan catatan umum MEP dasar",
         "GM-02": "Denah kunci shaft dan lubang pelat per lantai",
         "GM-03": "Ruang alat atap podium: chiller M-01, pompa M-04, landasan",
         "GM-04": "Zona MRI LT1: magnet R-03, kompresor R-06, jarak bebas",
         "GM-05": "Bukaan pintu dinding inti lift dan tangga",
         "GM-06": "Beban alat MEP per lantai dan daftar alat"}


def idn(v, d=2):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def simpan(g, no):
    PLOT.mkdir(parents=True, exist_ok=True)
    dwg = DWG / f"{NAMA[no]}.dwg"
    g.simpan(dwg, PLOT / f"{dwg.stem}.pdf", PNG / f"{dwg.stem}.png")
    return dwg


# ------------------------------------------------------------------ data (tanpa CADCraft)
@lru_cache(None)
def bukaan_ifc():
    """Lubang pelat dan bukaan dinding dari IFC STR 7.3: [{jenis, lantai, x0, y0, x1, y1, z0, z1}] (m).
    Hasil disimpan ke cache/mep_bukaan.json (kunci = ukuran + waktu ubah IFC)."""
    kunci = f"{IFC_STR.stat().st_size}-{int(IFC_STR.stat().st_mtime)}"
    c = AKAR / "cache" / "mep_bukaan.json"
    if c.exists():
        d = json.loads(c.read_text(encoding="utf-8"))
        if d.get("kunci") == kunci:
            return d["bukaan"]
    import ifcopenshell
    import ifcopenshell.geom as geom
    import ifcopenshell.util.element as ue
    import numpy as np
    m = ifcopenshell.open(str(IFC_STR))
    s = geom.settings()
    s.set(s.USE_WORLD_COORDS, True)
    out = []
    for o in m.by_type("IfcOpeningElement"):
        if not o.VoidsElements:
            continue
        h = o.VoidsElements[0].RelatingBuildingElement
        v = np.array(geom.create_shape(s, o).geometry.verts).reshape(-1, 3)
        lo, hi = v.min(0), v.max(0)
        out.append({"jenis": h.is_a()[3:], "lantai": ue.get_container(h).Name,
                    "x0": round(float(lo[0]), 2), "y0": round(float(lo[1]), 2), "x1": round(float(hi[0]), 2),
                    "y1": round(float(hi[1]), 2), "z0": round(float(lo[2]), 2), "z1": round(float(hi[2]), 2)})
    c.parent.mkdir(exist_ok=True)
    c.write_text(json.dumps({"kunci": kunci, "bukaan": out}, ensure_ascii=False), encoding="utf-8")
    return out


def shaft_ifc():
    """Matriks shaft x lantai pelat yang dilubangi (IFC) beside rentang tahap4_bim.SHAFT.
    [(nama, x0, x1, y0, y1, lantai_ifc[list], lantai_rencana[list])]; lubang inti lift diberi nama 'VOID LIF'."""
    import tahap4_bim as b
    pel = [d for d in bukaan_ifc() if d["jenis"] == "Slab"]
    out = []
    daftar = list(b.SHAFT)
    lif = [d for d in pel if d["x1"] - d["x0"] > 5]
    if lif:
        d = lif[0]
        daftar.append(("VOID LIF", d["x0"], d["x1"], d["y0"], d["y1"], None, None))
    for nama, x0, x1, y0, y1, a, z in daftar:
        ifc = sorted({d["lantai"] for d in pel if abs(d["x0"] - x0) < 0.05 and abs(d["y0"] - y0) < 0.05}, key=LANTAI.index)
        renc = LANTAI[LANTAI.index(a) + 1: LANTAI.index(z) + 1] if a else None
        out.append((nama, x0, x1, y0, y1, ifc, renc))
    return out


def bukaan_inti():
    """Bukaan dinding inti (IFC) dikelompokkan per inti: {inti: [(x0, x1, lebar, tinggi, [lantai])]}."""
    import tahap4_bim as b
    import tahap4_dinding as td
    out = {}
    for d in (d for d in bukaan_ifc() if d["jenis"] == "Wall"):
        cx = (d["x0"] + d["x1"]) / 2
        cy = (d["y0"] + d["y1"]) / 2
        inti = min(b.PUSAT, key=lambda k: abs(b.PUSAT[k][0] - cx) + abs(b.PUSAT[k][1] - cy - (4 if k.startswith("Inti") else 3)))
        lb = round(d["x1"] - d["x0"], 2)
        kel = out.setdefault(inti, {})
        k = (d["x0"], d["x1"], lb, round(d["z1"] - d["z0"], 2))
        kel.setdefault(k, []).append(d["lantai"])
    return {i: [(*k, sorted(v, key=LANTAI.index)) for k, v in sorted(kel.items())] for i, kel in out.items()}


def beban_lantai():
    """[(lantai, alat, kN)] dan total per lantai dari tahap4_beban.alat_per_lantai (Data Beban MEP Rinci)."""
    import tahap4_beban as tb
    r = tb.alat_per_lantai()
    baris = [(lv, a, q) for lv in LANTAI if lv in r for a, q in r[lv]]
    total = {lv: sum(q for _, q in r[lv]) for lv in r}
    return baris, total


def alat():
    import tahap7_federasi as f
    return {a[0]: a for a in f.ALAT}


def rentang(ls):
    """['LT2','LT3','LT4'] -> 'LT2-LT4'."""
    if not ls:
        return "-"
    i = [LANTAI.index(x) for x in ls]
    if i == list(range(i[0], i[-1] + 1)):
        return ls[0] if len(ls) == 1 else f"{ls[0]}-{ls[-1]}"
    return ", ".join(ls)


# ------------------------------------------------------------------ bantu gambar
def rect(g, x0, y0, x1, y1, ly):
    g.pline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], ly, tutup=True)


def latar(g, xs=None, ys=None, as_luar=True, ujung=4.0):
    """Garis as gedung (1-10, A-G) dan tepi podium/menara."""
    import tahap4_beban as tb
    xs = xs or tb.GRID_X
    ys = ys or tb.GRID_Y
    g.layer("A-TEPI", 7, 0.35)
    y0, y1 = min(ys) - ujung, max(ys) + ujung
    x0, x1 = min(xs) - ujung, max(xs) + ujung
    for x in xs:
        g.as_grid(str(tb.GRID_X.index(x) + 1), (x, y0), (x, y1), dua_ujung=as_luar)
    for y in ys:
        g.as_grid("ABCDEFG"[tb.GRID_Y.index(y)], (x0, y), (x1, y), dua_ujung=as_luar)


def inti_denah(g, pusat_dict, ly="S-INTI"):
    """Dinding inti (outline) dengan celah pintu dari IFC."""
    import tahap4_dinding as td
    bk = bukaan_inti()
    t = td.T
    for nama, (cx, cy) in pusat_dict.items():
        dx, dy = td.DIM["L" if nama.startswith("Inti") else "T"]
        xa, xb, ya, yb = cx - dx / 2, cx + dx / 2, cy - dy / 2, cy + dy / 2
        # tiga sisi utuh
        rect(g, xa - t / 2, yb - t / 2, xb + t / 2, yb + t / 2, ly)
        rect(g, xa - t / 2, ya + t / 2, xa + t / 2, yb - t / 2, ly)
        rect(g, xb - t / 2, ya + t / 2, xb + t / 2, yb - t / 2, ly)
        # sisi selatan dipotong pintu
        celah = sorted((x0, x1) for x0, x1, *_ in bk.get(nama, []))
        xs = [xa - t / 2]
        for x0, x1 in celah:
            xs += [x0, x1]
        xs.append(xb + t / 2)
        for p, q in zip(xs[::2], xs[1::2]):
            if q - p > 0.01:
                rect(g, p, ya - t / 2, q, ya + t / 2, ly)


def shaft_simbol(g, x0, y0, x1, y1, ly="M-SHAFT"):
    rect(g, x0, y0, x1, y1, ly)
    g.pline([(x0, y0), (x1, y1)], ly)
    g.pline([(x0, y1), (x1, y0)], ly)


def lapis(g, daftar):
    for ly, w, gy in daftar:
        g.layer(ly, 7, w, gy)


# ------------------------------------------------------------------ GM-01
def gm01():
    from cad_lembar import Gambar
    SK = 100
    with Gambar(SK) as g:
        g.layer("S-TEKS", 7, 0.18)
        g.teks((1.0, 23.8), "TABEL 1: DAFTAR GAMBAR MEP DASAR", "S-TEKS", 2.0, j="L", tebal=True)
        skala = {"GM-01": "-", "GM-02": "1:300", "GM-03": "1:150", "GM-04": "1:250", "GM-05": "1:100", "GM-06": "-"}
        rows = [[k, JUDUL[k], skala[k]] for k in NAMA]
        yb = t4g.tabel(g, 1.0, 23.3, [16, 112, 16], ["NO", "JUDUL", "SKALA"], rows)
        g.teks((1.0, yb - 0.8), "TABEL 2: LINGKUP (KEPUTUSAN RENCANA 8)", "S-TEKS", 2.0, j="L", tebal=True)
        lk = [["Masuk", "letak shaft dan lubang pelat, ruang dan landasan alat, zona MRI,\nbukaan dinding inti, beban alat per lantai"],
              ["Tidak masuk", "desain sistem (pipa, saluran udara, kabel, kapasitas, diagram);\ndikerjakan konsultan MEP"],
              ["Sumber letak", "model STR 7.3 (RSTB-STR-T7-LOD300.ifc), federasi 7.2 (ALAT), tahap4_bim.SHAFT"],
              ["Sumber beban", "Data Beban MEP Rinci (tahap4_beban.alat_per_lantai, 4.2)"]]
        yb2 = t4g.tabel(g, 1.0, yb - 1.3, [26, 118], ["BUTIR", "KETERANGAN"], lk)
        g.teks((1.0, yb2 - 0.8), "CATATAN UMUM", "S-TEKS", 2.0, j="L", tebal=True)
        cat = ["1. Gambar ini gambar koordinasi: menetapkan ruang yang dicadangkan, bukan rancangan sistem MEP.",
               "2. Lubang pelat dan bukaan dinding mengikuti model STR 7.3; lubang baru wajib disetujui perencana struktur.",
               "3. Chiller M-01 di atas pegas δ 25 mm dan rel GS-34; pompa M-04 di atas bantalan inersia + pegas (RKS 7.7).",
               "4. Kompresor MRI R-06 di atas pegas δ ≥ 25 mm, dudukan sendiri, di luar pelat panel MRI 9-10/D-E (5.2).",
               "5. Jalur kendaraan ≥ 12,0 m dari isocenter MRI (7.2); lift ≥ 8,0 m (terpenuhi 26,26 m, A-02).",
               "6. Koordinat dalam m terhadap titik nol gedung; elevasi lantai dari datum BM-1 = +10,000.",
               "7. Data studi kasus SIMULASI."]
        for i, s in enumerate(cat):
            g.teks((1.0, yb2 - 1.5 - i * 0.4), s, "S-TEKS", H, j="L")
        g.lembar("GM-01", JUDUL["GM-01"], "TANPA SKALA", pusat=None, status=STATUS, tanggal=TANGGAL,
                 subjudul="Langkah 7.6: koordinasi MEP", catatan=["MEP hanya koordinasi (keputusan rencana 8).", "Data studi kasus simulasi."],
                 judul_kop="DAFTAR GAMBAR MEP DASAR")
        g.viewport_tambahan((26, 40), (331, 283), (14.5, 12.0), SK, None, None)
        return simpan(g, "GM-01")


# ------------------------------------------------------------------ GM-02
LABEL_SH = {"SH-1": (0, 1.2), "SH-2": (0, 1.2), "SH-3": (0, -1.0), "SH-4": (0, 1.6), "SH-5": (0, 1.2),
            "SH-6": (-2.4, 0), "SH-7": (0, -1.0), "LB-2": (0, 1.2), "VOID LIF": (0, 0)}


def gm02():
    from cad_lembar import Gambar
    import tahap4_bim as b
    SK = 300
    with Gambar(SK) as g:
        lapis(g, [("A-TEPI", 0.35, "Continuous"), ("A-MENARA", 0.25, "DASHED"), ("S-INTI", 0.35, "Continuous"),
                  ("M-SHAFT", 0.35, "Continuous"), ("M-TEKS", 0.18, "Continuous")])
        latar(g, as_luar=False, ujung=3.0)
        rect(g, 12, 27, 84, 75, "A-TEPI")
        rect(g, 20, 27, 84, 51, "A-MENARA")
        inti_denah(g, b.PUSAT)
        sh = shaft_ifc()
        for nama, x0, x1, y0, y1, ifc, _ in sh:
            shaft_simbol(g, x0, y0, x1, y1)
            dx, dy = LABEL_SH.get(nama, (0, 1.2))
            if nama == "VOID LIF":
                g.teks(((x0 + x1) / 2, (y0 + y1) / 2 + 1.0), "VOID LIF", "M-TEKS", H, j="MC", tebal=True)
                continue
            g.teks(((x0 + x1) / 2 + dx, (y0 + y1) / 2 + dy), nama, "M-TEKS", H, j="MC", tebal=True)
        g.teks((48.0, 76.4), "PODIUM LT1-LT3 (x 12-84, y 27-75); MENARA LT4-ATAP (x 20-84, y 27-51, PUTUS)", "M-TEKS", H, j="MC")
        # tabel matriks di bawah denah
        rows = []
        for nama, x0, x1, y0, y1, ifc, renc in sh:
            sel = ["●" if lv in ifc else "-" for lv in LANTAI[1:]]
            cocok = "IFC = rencana" if renc is None or renc == ifc else "BEDA"
            rows.append([nama, f"{idn(x0, 1)}-{idn(x1, 1)}", f"{idn(y0, 1)}-{idn(y1, 1)}",
                         f"{idn(x1 - x0, 1)} × {idn(y1 - y0, 1)}", idn((x1 - x0) * (y1 - y0), 2), *sel, cocok])
        g.teks((14.0, 20.6), "TABEL: LUBANG PELAT PER LANTAI (● = PELAT DILUBANGI, MODEL STR 7.3)", "M-TEKS", 2.0, j="L", tebal=True)
        t4g.tabel(g, 14.0, 19.9, [20, 22, 22, 22, 16, 11, 11, 11, 11, 11, 11, 24],
                  ["LUBANG", "x (m)", "y (m)", "UKURAN (m)", "LUAS m²", "LT2", "LT3", "LT4", "LT5", "LT6", "ATAP", "CEK"], rows)
        g.legenda_tambah("garis", "Shaft / lubang pelat (silang)", tebal=0.35)
        g.legenda_tambah("garis", "Dinding inti dengan bukaan pintu", tebal=0.35)
        g.legenda_tambah("garis", "Tepi menara LT4-ATAP (putus)", garis="DASHED", tebal=0.25)
        catatan = ["Letak shaft dari tahap4_bim.SHAFT; lantai dilubangi dibaca dari IfcOpeningElement di pelat model STR 7.3.",
                   "Pelat LT1 (pelat dasar) tidak dilubangi; shaft mulai dari pelat LT2. VOID LIF = ruang luncur inti lift x 50-58, y 35-43.",
                   "SH-7 berada di pelat turun LB-1 (CSSD LT2, GS-33): tepi lubang dicek perencana struktur saat detail MEP.",
                   "Lubang tambahan > 0,3 × 0,3 m wajib disetujui perencana struktur."]
        g.lembar("GM-02", JUDUL["GM-02"], f"1:{SK}", pusat=None, status=STATUS, tanggal=TANGGAL,
                 subjudul="Langkah 7.6: dari tahap4_bim.SHAFT dan IFC STR 7.3", catatan=catatan, judul_kop="SHAFT DAN LUBANG PELAT")
        g.viewport_tambahan((26, 40), (331, 283), (48.0, 41.4), SK, None, None)
        g.skala_grafis(205, 22, 20, bagi=4)
        return simpan(g, "GM-02")


# ------------------------------------------------------------------ GM-03
def gm03():
    from cad_lembar import Gambar
    import tahap7_gambar_str as gs
    a = alat()
    SK = 150
    with Gambar(SK) as g:
        lapis(g, [("S-REL", 0.25, "DASHED"), ("M-ALAT", 0.35, "Continuous"), ("M-PEGAS", 0.25, "Continuous"),
                  ("M-BEBAS", 0.18, "DASHDOT"), ("M-TEKS", 0.18, "Continuous"), ("A-TEPI", 0.35, "Continuous")])
        latar(g, [60.0, 68.0, 76.0, 84.0], [59.0, 67.0, 75.0])
        g.pline([(56.0, 51.0), (84.0, 51.0), (84.0, 75.0), (56.0, 75.0)], "A-TEPI")
        g.teks((70.0, 51.6), "TEPI MENARA y 51 (DINDING LT4)", "M-TEKS", H, j="MC")
        for x in gs.REL_X:
            rect(g, x - 0.15, 59.0, x + 0.15, 75.0, "S-REL")
        for k in ("M-01-1", "M-01-2", "M-01-3", "M-01-4"):
            _, _, _, _, x0, y0, x1, y1, *_ = a[k]
            rect(g, x0, y0, x1, y1, "M-ALAT")
            for px in (x0 + 0.3, x1 - 0.3):
                for py in (y0 + 0.5, (y0 + y1) / 2, y1 - 0.5):
                    g.aktif("M-PEGAS")
                    g.cmd("circle", {"center": g.mm((px, py)), "radius": 150})
            g.teks(((x0 + x1) / 2, y1 + 0.7), k.replace("M-01-", "M-01."), "M-TEKS", H, j="MC", tebal=True)
        _, _, _, _, x0, y0, x1, y1, *_ = a["M-04"]
        rect(g, x0, y0, x1, y1, "M-ALAT")
        g.teks(((x0 + x1) / 2, (y0 + y1) / 2 + 0.4), "POMPA M-04 (4 UNIT)", "M-TEKS", H, j="MC", tebal=True)
        g.teks(((x0 + x1) / 2, (y0 + y1) / 2 - 0.4), "BANTALAN INERSIA + PEGAS [ASUMSI]", "M-TEKS", H, j="MC")
        # zona bebas servis 1,0 m keliling kelompok chiller dan pompa [Asumsi]
        rect(g, 67.4, 62.5, 82.2, 75.5 - 0.0, "M-BEBAS")
        g.teks((86.5, 63.0), "ZONA BEBAS SERVIS 1,0 m [ASUMSI]", "M-TEKS", H, j="L")
        g.pline([(82.2, 63.0), (86.3, 63.0)], "M-TEKS")
        xs = [68.4, 70.7, 71.9, 74.2, 75.4, 77.7, 78.9, 81.2]
        for p, q in zip(xs, xs[1:]):
            g.ukur((p, 63.5), (q, 63.5), ((p + q) / 2, 61.6))
        g.ukur((68.4, 63.5), (81.2, 63.5), (74.8, 60.4))
        g.ukur((81.2, 63.5), (81.2, 74.5), (83.0, 69.0), rot=90)
        g.ukur((60.0, 62.0), (68.0, 62.0), (64.0, 60.8))
        g.ukur((60.0, 62.0), (60.0, 66.0), (58.6, 64.0), rot=90)
        g.tunjuk((69.0, 72.0), (63.0, 72.5), "REL 300 × 500 ARAH y (7 BUAH, GS-34)", "M-TEKS")
        g.tunjuk((68.7, 64.0), (63.0, 69.5), "PEGAS δ 25 mm (6 PER UNIT, TIPIKAL)", "M-TEKS")
        g.teks((72.0, 78.6), "DENAH ATAP PODIUM UTARA: RUANG ALAT (LETAK 7.3)", "M-TEKS", 2.2, j="MC", tebal=True)
        g.legenda_tambah("garis", "Alat M-01 / M-04 (tapak)", tebal=0.35)
        g.legenda_tambah("garis", "Rel landasan chiller (putus, GS-34)", garis="DASHED", tebal=0.25)
        g.legenda_tambah("garis", "Zona bebas servis (titik-garis)", garis="DASHDOT", tebal=0.18)
        catatan = ["Chiller M-01: 4 unit 2,3 × 11,0 m diputar, x 68,4-81,2, y 63,5-74,5 (7.3, K7.3-2); 115,8 kN operasi per unit; kipas 14,5 Hz.",
                   "Landasan: 7 rel arah y 300 × 500 (GS-34) + pegas δ 25 mm; alas alat 0,3 m di atas pelat (lapis atap 150 + rel/pegas).",
                   "Pompa M-04: kotak kelompok x 60-68, y 62-66 [Asumsi], bantalan inersia + pegas di atas lapis atap 150.",
                   "Jumlah dan letak pegas tiap unit dari pemasok (gambar skematik). Zona bebas servis 1,0 m [Asumsi], bukan syarat pabrikan."]
        g.lembar("GM-03", JUDUL["GM-03"], f"1:{SK}", pusat=None, status=STATUS, tanggal=TANGGAL,
                 subjudul="Langkah 7.6: letak 7.3, federasi 7.2", catatan=catatan, judul_kop="RUANG ALAT ATAP PODIUM")
        g.viewport_tambahan((26, 40), (331, 283), (72.0, 66.0), SK, None, None)
        g.skala_grafis(205, 22, 10, bagi=5)
        return simpan(g, "GM-03")


# ------------------------------------------------------------------ GM-04
ISO = (80.5, 57.0)
R_BEBAS = 12.0


def gm04():
    from cad_lembar import Gambar
    a = alat()
    SK = 250
    with Gambar(SK) as g:
        lapis(g, [("A-TEPI", 0.35, "Continuous"), ("S-PANEL", 0.25, "Continuous"), ("M-ALAT", 0.35, "Continuous"),
                  ("M-ATAS", 0.25, "DASHED"), ("M-BEBAS", 0.25, "DASHDOT"), ("M-TEKS", 0.18, "Continuous")])
        latar(g, [68.0, 76.0, 84.0], [51.0, 59.0, 67.0])
        g.pline([(64.0, 47.0), (84.0, 47.0), (84.0, 71.0)], "A-TEPI")
        g.arsir([(76, 51), (84, 51), (84, 59), (76, 59)], "S-PANEL", "ANSI37", 1.5)
        g.teks((80.0, 50.2), "PELAT PANEL MRI 9-10/D-E", "M-TEKS", H, j="MC")
        g.teks((80.0, 49.5), "(TULANGAN A955M, 5.2)", "M-TEKS", H, j="MC")
        for k in ("R-03", "R-06"):
            _, _, _, _, x0, y0, x1, y1, *_ = a[k]
            rect(g, x0, y0, x1, y1, "M-ALAT")
        g.pline([(ISO[0] - 0.6, ISO[1]), (ISO[0] + 0.6, ISO[1])], "M-ALAT")
        g.pline([(ISO[0], ISO[1] - 0.6), (ISO[0], ISO[1] + 0.6)], "M-ALAT")
        g.aktif("M-BEBAS")
        g.cmd("circle", {"center": g.mm(ISO), "radius": R_BEBAS * 1000})
        for k in ("M-01-1", "M-01-2", "M-01-3", "M-01-4"):
            _, _, _, _, x0, y0, x1, y1, *_ = a[k]
            rect(g, x0, y0, x1, y1, "M-ATAS")
        g.teks((74.8, 75.4), "CHILLER M-01 DI ATAP PODIUM (DI ATAS)", "M-TEKS", H, j="MC")
        g.pline([(92.5, 44.0), (92.5, 70.0)], "M-ATAS")
        g.teks((93.0, 47.0), "LAJUR AMBULANS x 92,5-98,5 (7.2)", "M-TEKS", H, j="L", rot=90)
        g.tunjuk((81.6, 57.6), (72.5, 58.0), "R-03 MAGNET MRI 1,5 T (48,1 kN)", "M-TEKS")
        g.tunjuk(ISO, (72.5, 54.0), "ISOCENTER (80,5; 57,0)", "M-TEKS")
        g.tunjuk((75.0, 61.3), (69.0, 63.5), "R-06 KOMPRESOR, PEGAS δ ≥ 25 mm", "M-TEKS")
        g.ukur((ISO[0], ISO[1]), (ISO[0] + R_BEBAS, ISO[1]), (86.25, 54.2))
        g.teks((80.5, 44.3), "BATAS JALUR KENDARAAN R 12,0 m DARI ISOCENTER", "M-TEKS", H, j="MC")
        g.legenda_tambah("garis", "Alat MRI R-03 / R-06 (tapak)", tebal=0.35)
        g.legenda_tambah("garis", "Lingkar 12,0 m dari isocenter", garis="DASHDOT", tebal=0.25)
        g.legenda_tambah("garis", "Alat di lantai atas / lajur (putus)", garis="DASHED", tebal=0.25)
        g.legenda_tambah("arsir", "Pelat panel MRI 9-10/D-E", pola="ANSI37")
        catatan = ["R-03 magnet x 79,4-81,6, y 55,8-58,2 (48,1 kN); R-06 kompresor x 74,5-75,5, y 60,7-61,3 (3,9 kN, getaran 50 Hz).",
                   "R-06 di atas pegas δ ≥ 25 mm, dudukan sendiri, di luar pelat panel MRI; jarak ke isocenter 6,2 m (A-03, 7.2).",
                   "Jalur kendaraan ≥ 12,0 m dari isocenter (koreksi 7.2); lift dan bobot imbang 26,26 m ≥ 8,0 m (A-02).",
                   "Chiller M-01 di atap podium y ≥ 63,5 (7.3); gaya dinamis pabrikan MRI belum ada (5.2 butir 4)."]
        g.lembar("GM-04", JUDUL["GM-04"], f"1:{SK}", pusat=None, status=STATUS, tanggal=TANGGAL,
                 subjudul="Langkah 7.6: dari 5.2, 7.2, 7.3", catatan=catatan, judul_kop="ZONA MRI LT1")
        g.viewport_tambahan((26, 40), (331, 283), (80.0, 57.0), SK, None, None)
        g.skala_grafis(205, 22, 10, bagi=5)
        return simpan(g, "GM-04")


# ------------------------------------------------------------------ GM-05
def gm05():
    from cad_lembar import Gambar
    import tahap4_bim as b
    bk = bukaan_inti()
    SK = 100
    lif, tg = "Inti lif x50-58 y35-43", "Tangga x22 y39"
    with Gambar(SK) as g:
        lapis(g, [("S-INTI", 0.35, "Continuous"), ("M-TEKS", 0.18, "Continuous")])
        inti_denah(g, {lif: b.PUSAT[lif], tg: b.PUSAT[tg]})
        for nama in (lif, tg):
            for x0, x1, lb, t, _ in bk[nama]:
                cy = b.PUSAT[nama][1] - (4 if nama.startswith("Inti") else 3)
                g.ukur((x0, cy - 0.175), (x1, cy - 0.175), ((x0 + x1) / 2, cy - 1.0))
        g.teks((54.0, 39.0), "INTI LIFT 8 × 8 m", "M-TEKS", H, j="MC", tebal=True)
        g.teks((22.0, 39.0), "INTI TANGGA 4 × 6 m", "M-TEKS", H, j="MC", tebal=True)
        g.teks((22.0, 38.4), "(TIPIKAL 6 INTI)", "M-TEKS", H, j="MC")
        rows = []
        for nama, d in bk.items():
            for x0, x1, lb, t, ls in d:
                rows.append([nama.replace("Inti lif x50-58 y35-43", "Inti lift").replace("Tangga ", "Tangga "),
                             f"{idn(x0, 2)}-{idn(x1, 2)}", f"{idn(lb, 2)} × {idn(t, 2)}", rentang(ls), str(len(ls))])
        rows.sort(key=lambda r: r[0])
        g.teks((14.0, 31.4), "TABEL: BUKAAN DINDING INTI (MODEL STR 7.3; SISI SELATAN, DINDING 350 mm)", "M-TEKS", 2.0, j="L", tebal=True)
        t4g.tabel(g, 14.0, 30.8, [34, 30, 30, 26, 14], ["INTI", "x (m)", "b × h (m)", "LANTAI", "JML"], rows)
        catatan = ["Bukaan dari IfcOpeningElement di dinding inti model STR 7.3; ambang bawah = muka pelat tiap lantai, tinggi 2,4 m.",
                   "Inti lift: 2 pintu 1,4 m (as x 52 dan x 56); inti tangga: 1 pintu 1,2 m di tengah sisi selatan.",
                   "Bukaan MEP baru di dinding inti (pipa, saluran) tidak ada di model: wajib dihitung ulang perencana struktur (4.10).",
                   "Dinding geser 350 mm f'c 35 MPa (GS-03..14)."]
        g.lembar("GM-05", JUDUL["GM-05"], f"1:{SK}", pusat=None, status=STATUS, tanggal=TANGGAL,
                 subjudul="Langkah 7.6: dari IFC STR 7.3", catatan=catatan, judul_kop="BUKAAN DINDING INTI")
        g.viewport_tambahan((26, 150), (178, 283), (54.0, 39.0), SK, "Denah inti lift", f"SKALA 1:{SK}")
        g.viewport_tambahan((182, 150), (331, 283), (22.0, 39.0), SK, "Denah inti tangga tipikal", f"SKALA 1:{SK}")
        g.viewport_tambahan((26, 40), (331, 146), (29.0, 27.0), SK, None, None)
        g.skala_grafis(205, 22, 5, bagi=5)
        return simpan(g, "GM-05")


# ------------------------------------------------------------------ GM-06
def gm06():
    from cad_lembar import Gambar
    SK = 100
    baris, total = beban_lantai()
    a = alat()
    with Gambar(SK) as g:
        g.layer("S-TEKS", 7, 0.18)
        g.teks((1.0, 23.8), "TABEL 1: BEBAN ALAT MEP PER LANTAI (DATA BEBAN MEP RINCI)", "S-TEKS", 2.0, j="L", tebal=True)
        rows = []
        for lv in LANTAI:
            isi = [r for r in baris if r[0] == lv]
            for i, (_, n, q) in enumerate(isi):
                rows.append([lv if i == 0 else "", n, idn(q, 1), idn(total[lv], 1) if i == 0 else ""])
        yb = t4g.tabel(g, 1.0, 23.3, [16, 96, 20, 24], ["LANTAI", "ALAT", "kN", "TOTAL kN"], rows)
        g.teks((1.0, yb - 0.8), f"JUMLAH SEMUA LANTAI: {idn(sum(total.values()), 1)} kN", "S-TEKS", H, j="L", tebal=True)
        g.teks((17.6, 23.8), "TABEL 2: ALAT DI MODEL FEDERASI 7.2 (LETAK 7.3)", "S-TEKS", 2.0, j="L", tebal=True)
        r2 = []
        for k, (_, ifc, ur, lv, x0, y0, x1, y1, *_rest) in a.items():
            r2.append([k, ifc.replace("Ifc", ""), "atap podium" if k.startswith("M-") else lv,
                       f"{idn(x0, 1)}-{idn(x1, 1)}", f"{idn(y0, 1)}-{idn(y1, 1)}"])
        t4g.tabel(g, 17.6, 23.3, [18, 30, 24, 26, 26], ["KODE", "JENIS IFC", "LETAK", "x (m)", "y (m)"], r2)
        catatan = ["Beban alat dari Data Beban MEP Rinci (4.2) lewat tahap4_beban.alat_per_lantai; sudah masuk desain pelat dan balok Tahap 4.",
                   "LT3 memuat beban atap podium utara (chiller, tangki 210 m³, pompa) karena atap podium = pelat di atas LT3.",
                   "Letak alat dari tahap7_federasi.ALAT (federasi 7.2 dengan perpindahan chiller dan pompa 7.3)."]
        g.lembar("GM-06", JUDUL["GM-06"], "TANPA SKALA", pusat=None, status=STATUS, tanggal=TANGGAL,
                 subjudul="Langkah 7.6: dari 4.2 dan 7.2", catatan=catatan, judul_kop="BEBAN ALAT MEP")
        g.viewport_tambahan((26, 40), (331, 283), (14.5, 12.0), SK, None, None)
        return simpan(g, "GM-06")


LEMBAR = {"GM-01": gm01, "GM-02": gm02, "GM-03": gm03, "GM-04": gm04, "GM-05": gm05, "GM-06": gm06}


# ------------------------------------------------------------------ set PDF
def gabung_pdf(keluar=PDF):
    from pypdf import PdfReader, PdfWriter
    w = PdfWriter()
    hilang = []
    for no in LEMBAR:
        f = PLOT / f"{NAMA[no]}.pdf"
        if not f.exists():
            hilang.append(no)
            continue
        w.add_page(PdfReader(str(f)).pages[0])
        w.add_outline_item(no, len(w.pages) - 1)
    w.write(str(keluar))
    return len(w.pages), hilang


def cek():
    import cad_cek
    return {no: len(cad_cek.cek(str(DWG / f"{NAMA[no]}.dwg"))) for no in LEMBAR if (DWG / f"{NAMA[no]}.dwg").exists()}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    if "--pdf" in a:
        print(gabung_pdf())
    elif "--cek" in a:
        print(cek())
    elif "--data" in a:
        for r in shaft_ifc():
            print(r)
        for k, v in bukaan_inti().items():
            print(k, v)
        print(beban_lantai()[1])
    else:
        for no in a:
            if no in LEMBAR:
                d = LEMBAR[no]()
                import cad_cek
                print(no, d.name, len(cad_cek.cek(str(d))), "pasangan", flush=True)
