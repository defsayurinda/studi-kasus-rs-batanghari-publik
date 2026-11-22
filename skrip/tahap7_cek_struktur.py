"""Tahap 7 langkah 7.3: cek struktur tambahan (K-01 balok inti lift, chiller M-01 vs 14,5 Hz, pit K-04b, fasad T-112, LB-1).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI (22 Nov 2026), status draf, disetujui atas delegasi Defsa
22 Nov 2026. Kunci jawaban tidak dibuka.

- K-01: balok BL-350x600 as 6 (x 52, y 35-43) di dalam inti lift LT2-ATAP dihapus. Model OpenSees 4.3
  (`tahap4_model`) dijalankan dengan dan tanpa balok itu (skrip tahap 4 tidak diubah, jadi cache analisis tidak basi).
- Chiller M-01: frekuensi alami lantai atap podium dengan massa chiller, cara 1 Rayleigh tangan (f = 0,18 √(g/Δ),
  rel + balok induk, Dunkerley) dan cara 2 grillage openseespy (T-113, ≤ 10 %). Keputusan rencana 5.
- K-04b: pit L-5..6 dan L-7 sebagian di luar Cap E; cek dengan rumus cap kaku 6.3 (`tahap6_tata_letak.periksa`).
- T-112: beban fasad V4 dari model 7.1 (luas IFC × berat satuan 4.10) vs 4.10 V3 (6.028 kN).
- LB-1: balok tepi pelat turun CSSD LT2 (`tahap4_balok._desain_anak`, pasal sama dengan 4.6).
- Model STR 7.3: `model/RSTB-STR-T7-LOD300.bimc/.ifc` dari STR 6.9 (perintah `--bangun`).
"""
from __future__ import annotations

import math
import shutil
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import box

sys.path.insert(0, str(Path(__file__).parent))

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "07 DED dan RKS"
XLSX = KELUAR / "7.3 Cek Struktur Tambahan.xlsx"
MD = KELUAR / "7.3 Cek Struktur Tambahan.md"
STR6 = AKAR / "model" / "RSTB-STR-T6-LOD300.bimc"
BIMC = AKAR / "model" / "RSTB-STR-T7-LOD300.bimc"
IFC = AKAR / "model" / "RSTB-STR-T7-LOD300.ifc"
STATUS = "draf, disetujui atas delegasi Defsa 22 Nov 2026"
LABEL = "DATA SIMULASI untuk studi kasus portofolio, tidak untuk konstruksi."
G = 9.81
TOL = {"K-01": 1.0, "T-112": 5.0, "T-113": 10.0}     # %, ditetapkan sebelum menghitung (00 Rencana Tahap 7)
F_KIPAS = 14.5                                        # Hz, kipas chiller M-01 (Data Beban MEP Rinci, catatan 5.2)
RASIO_F = 1.4                                         # keputusan rencana 5 [Asumsi]
PEGAS = 0.025                                         # m, lendutan statik pegas peredam
BALOK_K01 = (52.0, 35.0, 43.0)                        # x, y0, y1 (as 6, bentang B-C, di dalam inti lift)


def idn(v, d=1):
    if v is None:
        return "-"
    return f"{v:,.{d}f}".replace(",", "_").replace(".", ",").replace("_", ".")


# ------------------------------------------------------------------ K-01: OpenSees dengan/tanpa balok inti lift
def _ukur_ops():
    import tahap4_model as tm
    r = tm.ragam("K2")
    out = {"T": [float(x) for x in r["T"][:3]], "hapus": r["model"].get("dihapus", 0)}
    for arah in "XY":
        e = tm.elf_statik("K2", arah)
        d = 0 if arah == "X" else 1
        u = [float(x[d]) for x in e["u"]]
        z = [t["z"] for t in e["tk"]]
        dr = max((u[i] - (u[i - 1] if i else 0.0)) / (z[i] - (z[i - 1] if i else 0.0)) for i in range(len(u)))
        out[arah] = {"u": u[-1], "drift": dr, "inti": e["v_inti"] / (e["v_inti"] + e["v_kolom"])}
    return out


def k01_opensees():
    """Model 4.3 K2: dasar vs tanpa balok as 6 di inti lift (dihapus dengan ops.remove setelah bangun)."""
    import openseespy.opensees as ops
    import tahap4_model as tm
    asli = tm.bangun

    def tanpa(*a, **k):
        m = asli(*a, **k)
        x, y0, y1 = BALOK_K01
        hapus = [b for b in m["balok"] if b["x1"] == b["x2"] == x and {b["y1"], b["y2"]} == {y0, y1}]
        for b in hapus:
            ops.remove("ele", b["ele"])
        m["balok"] = [b for b in m["balok"] if b not in hapus]
        m["dihapus"] = len(hapus)
        return m

    a = _ukur_ops()
    tm.bangun = tanpa
    try:
        b = _ukur_ops()
    finally:
        tm.bangun = asli
    baris = [("T1 (s)", a["T"][0], b["T"][0]), ("T2 (s)", a["T"][1], b["T"][1]), ("T3 (s)", a["T"][2], b["T"][2])]
    for arah in "XY":
        baris += [(f"Perpindahan atap ELF {arah} (mm)", a[arah]["u"] * 1e3, b[arah]["u"] * 1e3),
                  (f"Simpangan antar lantai maks ELF {arah} (‰)", a[arah]["drift"] * 1e3, b[arah]["drift"] * 1e3),
                  (f"Porsi geser dasar inti {arah} (%)", a[arah]["inti"] * 100, b[arah]["inti"] * 100)]
    baris = [(n, x, y, (y - x) / x * 100) for n, x, y in baris]
    return {"baris": baris, "hapus": b["hapus"], "maks": max(abs(r[3]) for r in baris),
            "lolos": max(abs(r[3]) for r in baris) <= TOL["K-01"]}


# ------------------------------------------------------------------ chiller: tata letak dan frekuensi
def _sifat(b, h):
    import tahap4_model as tm
    e = tm.EC_30 if hasattr(tm, "EC_30") else 4700 * math.sqrt(30) * 1e3
    r = b / h
    j = (1 / 3 - 0.21 * r * (1 - r ** 4 / 12)) * b ** 3 * h
    return {"A": b * h, "Iv": b * h ** 3 / 12, "Ih": h * b ** 3 / 12, "J": j, "E": e, "G": e / 2.4}


def tata_chiller(letak="lama"):
    """Garis grillage atap podium + titik chiller. 'lama' = Tahap 4 (rel arah x di x 60-76, y 52,9-65,7);
    'baru' = y ≥ 63, unit diputar (11 m arah y, y 63,5-74,5), rel arah y bentang 59-67-75."""
    import tahap4_balok as tbk
    import tahap4_beban as tb
    import tahap4_bim as bim
    uk = bim.ukuran_balok()

    def ukb(x1, y1, x2, y2):
        return uk.get(("LT3", x1, y1, x2, y2), (tb.BALOK_B, tb.BALOK_H))

    pd = 115.8 / 6                                          # 4.9: 115,8 kN/unit, 6 titik tumpu
    if letak == "lama":
        rel = [("x", y, 60.0, 76.0, 0.30, 0.50, "rel") for y in bim.REL_Y]
        induk = [("y", x, 51.0, 67.0, *ukb(x, 51.0, x, 59.0), "induk") for x in (60.0, 68.0, 76.0)]
        tepi = [("x", y, 60.0, 76.0, *ukb(60.0, y, 68.0, y), "induk") for y in (51.0, 59.0, 67.0)]
        titik = [(x, y, pd) for y in bim.REL_Y for x in tbk.CHILLER_X]
        tump = [(x, y) for x in (60.0, 68.0, 76.0) for y in (51.0, 59.0, 67.0)]
        unit = [box(62.5, y0, 73.5, y0 + 2.3) for y0 in bim.CHILLER_Y0]
        satu_arah = "y"
    else:
        x0 = [68.4 + 3.5 * i for i in range(4)]
        xs = [round(x + d, 2) for x in x0 for d in (0.6, 1.7)]
        rel = [("y", x, 59.0, 75.0, 0.30, 0.50, "rel" if abs(x - 76.0) > 0.01 else "induk") for x in xs]
        induk = [("x", y, 68.0, 84.0, *ukb(68.0, y, 76.0, y), "induk") for y in (59.0, 67.0, 75.0)]
        tepi = [("y", x, 59.0, 75.0, *ukb(x, 67.0, x, 75.0), "induk") for x in (68.0, 84.0)]
        tepi = [t for t in tepi] + ([] if any(abs(r[1] - 76.0) < 0.01 for r in rel) else
                                    [("y", 76.0, 59.0, 75.0, *ukb(76.0, 67.0, 76.0, 75.0), "induk")])
        titik = [(x, y, pd) for x in xs for y in (63.5, 69.0, 74.5)]
        tump = [(x, y) for x in (68.0, 76.0, 84.0) for y in (59.0, 67.0, 75.0)]
        unit = [box(x, 63.5, x + 2.3, 74.5) for x in x0]
        satu_arah = "x"
    return {"letak": letak, "garis": rel + induk + tepi, "titik": titik, "tump": tump, "unit": unit, "arah_pelat": satu_arah,
            "x0": x0 if letak == "baru" else None}


def _q_pelat():
    import tahap4_beban as tb
    import tahap4_pelat as tp
    return tb.GAMMA_C * tp.H + tp.SIDL_ATAP                  # kPa (pelat 200 + SIDL atap; hidup atap tidak ikut massa)


def _lebar_tributari(t):
    """Pelat satu arah ke garis sejajar (rel dan balok sejajar rel); garis tepi menerima juga setengah bay luar 4 m."""
    arah = "x" if t["arah_pelat"] == "y" else "y"            # garis yang menerima pelat sejajar sumbu ini
    gs = sorted({g[1] for g in t["garis"] if g[0] == arah})
    lebar = {}
    for i, c in enumerate(gs):
        kiri = (c - gs[i - 1]) / 2 if i else 4.0
        kanan = (gs[i + 1] - c) / 2 if i < len(gs) - 1 else 4.0
        lebar[c] = kiri + kanan
    return arah, lebar


def frekuensi_ops(t, n_ragam=12):
    """Grillage openseespy: balok elasticBeamColumn di bidang z = 0, uz/rx/ry bebas, kolom = tumpuan uz sendi.
    Massa: berat sendiri balok + pelat dan SIDL (tributari satu arah ke garis sejajar rel) + chiller di titik tumpu."""
    import openseespy.opensees as ops
    arah_p, lebar = _lebar_tributari(t)
    q = _q_pelat()
    titik_x = {round(x, 3) for x, _, _ in t["titik"]}
    titik_y = {round(y, 3) for _, y, _ in t["titik"]}
    gx = {round(g[1], 3) for g in t["garis"] if g[0] == "y"}
    gy = {round(g[1], 3) for g in t["garis"] if g[0] == "x"}
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)
    ops.geomTransf("Linear", 1, 0.0, 0.0, 1.0)
    node, massa = {}, {}

    def n_(x, y):
        k = (round(x, 3), round(y, 3))
        if k not in node:
            node[k] = len(node) + 1
            ops.node(node[k], k[0], k[1], 0.0)
            massa[k] = 0.0
        return node[k]

    ele = 0
    for arah, c, a0, a1, b, h, _ in t["garis"]:
        lain = gx if arah == "x" else gy
        tt = titik_x if arah == "x" else titik_y
        sta = sorted({round(a0 + 0.5 * i, 3) for i in range(int((a1 - a0) / 0.5) + 1)} | {v for v in lain | tt if a0 <= v <= a1})
        s = _sifat(b, h)
        m_l = (24.0 * b * h + (q * lebar.get(round(c, 3), 0.0) if arah == arah_p else 0.0)) / G
        for p0, p1 in zip(sta[:-1], sta[1:]):
            a_, b_ = ((p0, c), (p1, c)) if arah == "x" else ((c, p0), (c, p1))
            i, j = n_(*a_), n_(*b_)
            ele += 1
            ops.element("elasticBeamColumn", ele, i, j, s["A"], s["E"], s["G"], s["J"], s["Iv"], s["Ih"], 1)
            for k in (a_, b_):
                massa[(round(k[0], 3), round(k[1], 3))] += m_l * (p1 - p0) / 2
    for x, y, p in t["titik"]:
        massa[(round(x, 3), round(y, 3))] += p / G
    tump = {(round(x, 3), round(y, 3)) for x, y in t["tump"]}
    for k, n in node.items():
        ops.fix(n, 1, 1, *((1, 1, 1) if k in tump else (0, 0, 0)), 1)   # kolom: jepit (aksi portal)
        ops.mass(n, 0.0, 0.0, massa[k], 1e-6, 1e-6, 0.0)
    lam = sorted(l for l in ops.eigen("-fullGenLapack", len(node) * 3) if l > 1e-6)[:n_ragam]
    f = [math.sqrt(l) / (2 * math.pi) for l in lam]
    # massa efektif vertikal tiap ragam (indikasi ragam mana yang menggerakkan massa chiller)
    mtot = sum(massa.values())
    part = []
    for j in range(1, n_ragam + 1):
        phi = {k: ops.nodeEigenvector(n, j, 3) for k, n in node.items()}
        num = sum(massa[k] * phi[k] for k in node) ** 2
        den = sum(massa[k] * phi[k] ** 2 for k in node)
        part.append(num / den / mtot if den else 0.0)
    ops.wipe()
    return {"f": f, "part": part, "mtot_kN": mtot * G, "n_node": len(node)}


def frekuensi_tangan(t):
    """Rayleigh f = 0,18 √(g/Δ) [Asumsi: rumus Rayleigh balok sederhana bermassa merata; acuan dinamika struktur belum
    ada di acuan/], Δ = Δ rel (sendi 8 m: ragam antisimetri rel menerus) + Δ balok induk (jepit di kolom, aksi portal), beban = massa × g."""
    arah_p, lebar = _lebar_tributari(t)
    q = _q_pelat()
    rel = [g for g in t["garis"] if g[6] == "rel"]
    L = 8.0
    hasil = []
    for g in rel:
        s = _sifat(g[4], g[5])
        w = 24.0 * g[4] * g[5] + q * lebar[round(g[1], 3)]
        # titik chiller pada bentang pertama rel: jarak dari tumpuan
        pts = [(y if g[0] == "y" else x) - g[2] for x, y, p in t["titik"]
               if abs((x if g[0] == "y" else y) - g[1]) < 0.01 and 0.01 < (y if g[0] == "y" else x) - g[2] < L - 0.01]
        p = t["titik"][0][2]
        d_r = 5 * w * L ** 4 / (384 * s["E"] * s["Iv"]) + sum(p * min(a, L - a) * (3 * L ** 2 - 4 * min(a, L - a) ** 2)
                                                             for a in pts) / (48 * s["E"] * s["Iv"])
        hasil.append({"c": g[1], "w": w, "pts": pts, "d_r": d_r, "EI": s["E"] * s["Iv"]})
    r = max(hasil, key=lambda z: z["d_r"])
    # balok induk tengah: reaksi tumpuan dalam rel menerus dua bentang 1,25 w L + titik di tumpuan + bagian titik bentang
    induk = [g for g in t["garis"] if g[6] == "induk" and g[0] != rel[0][0] and g[2] < r["c"] < g[3]]
    ind = sorted(induk, key=lambda g: abs(g[1] - (68.0 if t["letak"] == "lama" else 67.0)))[0]
    s = _sifat(ind[4], ind[5])
    a0 = ind[2] + L * math.floor((r["c"] - ind[2]) / L)
    p_rel = []
    for z in hasil:
        if not (a0 < z["c"] < a0 + L):
            continue
        p_tump = sum(p for x, y, p in t["titik"] if abs((x if rel[0][0] == "y" else y) - z["c"]) < 0.01 and
                     abs((y if rel[0][0] == "y" else x) - ind[1]) < 0.01)
        p_bent = sum(t["titik"][0][2] * 2 * a / L for a in z["pts"])   # dua bentang, bagian ke tumpuan dalam
        p_rel.append((z["c"] - a0, 1.25 * z["w"] * L + p_tump + p_bent))
    w_i = 24.0 * ind[4] * ind[5]
    d_i = w_i * L ** 4 / (384 * s["E"] * s["Iv"]) + sum(                  # jepit-jepit di kolom (aksi portal)
        p * min(a, L - a) ** 2 * (3 * L - 4 * min(a, L - a)) for a, p in p_rel) / (48 * s["E"] * s["Iv"])
    f_r = 0.18 * math.sqrt(G / r["d_r"])
    f_i = 0.18 * math.sqrt(G / d_i)
    f = 0.18 * math.sqrt(G / (r["d_r"] + d_i))
    return {"rel": r, "induk": ind, "p_rel": p_rel, "d_r": r["d_r"], "d_i": d_i, "f_r": f_r, "f_i": f_i, "f": f}


def muat_y63():
    """Apakah 4 unit 11,0 × 2,3 m (jarak 1,2 m) muat di atap podium y ≥ 63 tanpa menumpang tangki opsi B dan tepi atap."""
    import tahap4_beban as tb
    x0, y0, x1, y1 = tb.PODIUM.bounds
    perlu = 4 * 2.3 + 3 * 1.2
    tangki = box(60.0, 67.0, 68.0, 75.0)                     # tangki opsi B (5.1)
    t = tata_chiller("baru")
    tumpang = sum(u.intersection(tangki).area for u in t["unit"])
    di_atap = all(tb.PODIUM.contains(u) for u in t["unit"])
    return {"perlu": perlu, "ada_x": y1 - 63.0, "muat_x": y1 - 63.0 >= perlu, "tumpang_tangki": tumpang, "di_atap": di_atap,
            "muat_y": tumpang < 1e-6 and di_atap, "unit": [u.bounds for u in t["unit"]], "x0": t["x0"]}


def rel_baru():
    """Desain rel baru arah y dua bentang 8 m (59-67-75), pola `tahap4_balok.balok_chiller` (lajur pelat 2,0 m)."""
    import tahap4_balok as tbk
    import tahap4_beban as tb
    import tahap4_pelat as tp
    ak = tb.atap_khusus()
    pd = 115.8 / 6
    pl = ak["chiller_impak_kn"] / 6 - pd

    def beban(b, h):
        qd = (tb.GAMMA_C * tp.H + tp.SIDL_ATAP) * 2.0 + tb.GAMMA_C * b * (h - tp.H)
        pts = [a - 59.0 for a in (63.5, 69.0, 74.5)]
        return ([("D", qd, 0.0, 16.0), ("L", 0.96 * 2.0, 0.0, 16.0)],
                [("D", pd, a) for a in pts] + [("L", pl, a) for a in pts])

    des, r, gaya = tbk._desain_anak(beban, [8.0, 8.0], tb.BALOK_B, [(0.30, 0.50), (0.30, 0.60), (0.35, 0.60)])
    return {**des, **gaya, "PD": pd, "PL": pl, "lama": tbk.balok_chiller()}


def chiller():
    import tahap4_balok as tbk
    out = {}
    for letak in ("lama", "baru"):
        t = tata_chiller(letak)
        o, h = frekuensi_ops(t), frekuensi_tangan(t)
        dekat = [(f, p) for f, p in zip(o["f"], o["part"]) if abs(f - F_KIPAS) / F_KIPAS <= 0.10]
        out[letak] = {"tata": t, "ops": o, "tangan": h, "f1": o["f"][0], "selisih": (h["f"] - o["f"][0]) / o["f"][0] * 100,
                      "dekat_kipas": dekat, "syarat": RASIO_F * F_KIPAS, "lolos_syarat": o["f"][0] >= RASIO_F * F_KIPAS}
    f_peg = math.sqrt(G / PEGAS) / (2 * math.pi)
    r = F_KIPAS / f_peg
    out["pegas"] = {"f": f_peg, "r": r, "T": 1 / (r ** 2 - 1)}
    out["y63"] = muat_y63()
    out["rel_baru"] = rel_baru()
    out["rel_lama"] = tbk.balok_chiller()
    return out


# ------------------------------------------------------------------ K-04b: pit di luar Cap E
EXT_L7 = (37.1, 29.4, 41.7)                 # x0, y0, x1 perlebaran Cap E di bawah pit L-7 (sampai muka selatan Cap E)
TIANG_L7 = [(37.9, 30.2), (40.9, 30.2)]     # 2 tiang Ø800 baru di perlebaran (0,8 m dari tepi, Tahap 3)


def pit_k04b():
    import tahap5_bim as t5
    import tahap5_pit_lift as pit
    import tahap6_bim as t6
    import tahap6_tata_letak as tl
    ck, ci = tl.rancang("a")
    c = next(c for c in ci if c["id"] == "Cap E")
    r0 = c["r"]
    bb = next(x for x in t6.caps() if x["id"] == "Cap E")["bbox"]
    cap = box(*bb)
    dl = pit.data_lift()
    pits = {}
    for k in ("L-5..6", "L-7"):
        luar, _ = t5.pit_geom(k, dl[k])
        g = pit.gravitasi(dl[k])
        pits[k] = {"kotak": luar.bounds, "luas": luar.area, "luar": luar.difference(cap).area,
                   "jarak": (bb[1] - luar.bounds[1]) if k == "L-7" else (luar.bounds[3] - bb[3]), **g}
    # L-5..6: pelat dasar dan dinding pit menjorok 0,39 m dari muka utara Cap E: kantilever dari muka cap
    p56 = pits["L-5..6"]
    t_s, tw = pit.TS0, pit.TW
    tinggi = pit.ATAS - (dl["L-5..6"]["dasar"] - t_s)
    a = p56["jarak"]
    w_dind = 24.0 * tw * tinggi
    w_pel = 24.0 * t_s * a
    mu = 1.2 * (w_dind * (a - tw / 2) + w_pel * a / 2)
    d = (t_s - 0.050 - 0.008) * 1000                                   # mm, selimut tanah 50 (5.5), D16
    as_min = 0.0018 * 1000 * t_s * 1000                                 # mm²/m, Tabel 8.6.1.1 (5.5)
    phimn = 0.9 * as_min * 420 * (d - as_min * 420 / (0.85 * 30 * 1000) / 2) / 1e6   # kNm/m
    kant = {"a": a, "Mu": mu, "phiMn_min": phimn, "lolos": mu <= phimn}
    # cek cap kaku 6.3: (A) perlebaran tanpa tiang (berat cap tambahan) ; (B) perlebaran + 2 tiang (cap lokal)
    wt = dict(x=r0["xc"], y=r0["yc"], Pmax=r0["W"], Pu=r0["Wu"], Pumin=r0["Wm"], Mux=0, Muy=0)
    ext = box(EXT_L7[0], EXT_L7[1], EXT_L7[2], bb[1])
    w_ext = tl.berat_cap(ext.area, tl.H_E)
    p7 = pits["L-7"]
    pindah = dict(x=39.4, y=31.7, Pmax=0.41 * p7["layan"], Pu=0.41 * p7["Pu"], Pumin=0.0, Mux=0, Muy=0)  # bagian 5.6 ke as A

    def cek(pos, extra):
        r = tl.periksa(pos, c["titik"] + [wt] + extra, c["zona"], c["tambah"], h=None)
        return {k: float(r[k]) for k in ("P_layan", "Pu_maks", "Pu_min", "dmin")} | {"izin": r["izin"], "lolos": r["lolos"]}

    e_w = dict(x=ext.centroid.x, y=ext.centroid.y, Pmax=w_ext, Pu=1.2 * w_ext, Pumin=0.9 * w_ext, Mux=0, Muy=0)
    dasar = cek(c["pos"], [])
    opsi_a = cek(c["pos"], [e_w, pindah])
    lokal = (w_ext + p7["layan"]) / len(TIANG_L7)          # cap lokal: perlebaran + seluruh pit L-7 ke 2 tiang baru
    lokal_u = (1.2 * w_ext + p7["Pu"]) / len(TIANG_L7)
    semua = np.array(list(c["pos"]) + TIANG_L7)
    jarak = min(float(np.hypot(*(semua[i] - semua[j]))) for i in range(len(semua)) for j in range(i)
                if i >= len(c["pos"]))
    pit_ok = box(*p7["kotak"]).within(ext.union(cap))
    return {"pits": pits, "kant": kant, "ext": ext.bounds, "w_ext": w_ext, "dasar": dasar, "opsi_a": opsi_a,
            "lokal": lokal, "lokal_u": lokal_u, "izin": dasar["izin"], "rasio_lokal": lokal / dasar["izin"],
            "jarak_min": jarak, "pit_tertutup": pit_ok, "tiang_baru": TIANG_L7, "n_tiang_cap": len(c["pos"])}


# ------------------------------------------------------------------ T-112: fasad V4 dari model 7.1
BERAT_FASAD = {"FS-KacaBiru": (0.38, "SNI 1727 Tabel C3.1-1 hal. 278 (kaca, kusen, sash)"),
               "FS-KacaPita": (0.38, "SNI 1727 Tabel C3.1-1 hal. 278"),
               "FS-PanelPutih": (0.40, "[Asumsi: panel komposit 50 mm + rangka, = q_ov 4.10]"),
               "FS-PanelAbu": (0.40, "[Asumsi: = q_ov 4.10]"), "FS-PanelAbuTua": (0.40, "[Asumsi: = q_ov 4.10]"),
               "TP-Overstek": (0.40, "4.10 q_ov rangka hollow + ACP [Asumsi]")}


def fasad_t112():
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.element as ue
    import tahap4_fasad as fa
    n = fa.hitung()
    b = fa.berat_fasad(n)
    f = ifcopenshell.open(str(AKAR / "model" / "RSTB-ARS-T7-LOD300.ifc"))
    st = ifcopenshell.geom.settings()
    st.set("use-world-coords", True)
    luas = {k: 0.0 for k in BERAT_FASAD}
    for w in f.by_type("IfcWall") + f.by_type("IfcSlab"):
        t = ue.get_type(w)
        nm = (t.Name if t else "") or ""
        if nm not in luas:
            continue
        v = np.array(ifcopenshell.geom.create_shape(st, w).geometry.verts).reshape(-1, 3)
        d = v.max(0) - v.min(0)
        luas[nm] += d[0] * d[1] if nm == "TP-Overstek" else max(d[0], d[1]) * d[2]
    rinci = [(k, luas[k], q, s, luas[k] * q) for k, (q, s) in BERAT_FASAD.items()]
    w4 = sum(r[4] for r in rinci)
    panel = sum(luas[k] for k in luas if k.startswith("FS-Panel"))
    w_grc = w4 + panel * (1.0 - 0.40)                        # kepekaan: panel GRC 1,0 kPa [Asumsi]
    return {"rinci": rinci, "w4": w4, "w3": b["wv3"], "w42": b["w42"], "selisih": (w4 - b["wv3"]) / b["wv3"] * 100,
            "w_grc": w_grc, "lolos": w4 <= b["wv3"] * (1 + TOL["T-112"] / 100), "luas_v3": fa.luas_fasad_python()}


# ------------------------------------------------------------------ LB-1: balok tepi pelat turun CSSD LT2
URUG = (0.25, 20.0)          # m, kN/m³: isian screed di pelat turun [Asumsi: lantai jadi rata dengan sekitarnya]


def lb1():
    import tahap4_balok as tbk
    import tahap4_beban as tb
    import tahap4_bim as bim
    import tahap4_pelat as tp
    x0, x1, y0, y1, turun = bim.LB1
    sidl = tp.SIDL_LANTAI + tb.GANTUNG["podium"]
    lo = 2.87                                                # P1 LT2 (tahap4_pelat.PANEL)
    q_n = tb.GAMMA_C * tp.H + sidl
    q_t = q_n + URUG[0] * URUG[1]
    uk = [(0.30, 0.60), (0.35, 0.60), (0.35, 0.70), (0.40, 0.70)]
    out = {}
    lebar = {y0: (0.5, (y1 - y0) / 2), y1: ((59.0 - y1) / 2, (y1 - y0) / 2)}
    for y in (y0, y1):
        ln_, lt_ = lebar[y]

        def beban(b, h, ln_=ln_, lt_=lt_):
            qd = q_n * ln_ + q_t * lt_ + tb.GAMMA_C * b * (h - tp.H)
            return [("D", qd, 0.0, x1 - x0), ("L", lo * (ln_ + lt_), 0.0, x1 - x0)], []
        des, r, gaya = tbk._desain_anak(beban, [x1 - x0], tb.BALOK_B, uk)
        out[f"y {idn(y, 0)}"] = {**des, **gaya, "L": x1 - x0, "RD": float(r["R"]["D"][0]), "RL": float(r["R"]["L"][0]),
                                 "lebar": ln_ + lt_}
    pa = [("D", out[k]["RD"], (y - 51.0)) for k, y in ((f"y {idn(y0, 0)}", y0), (f"y {idn(y1, 0)}", y1))] + \
         [("L", out[k]["RL"], (y - 51.0)) for k, y in ((f"y {idn(y0, 0)}", y0), (f"y {idn(y1, 0)}", y1))]

    def beban_x(b, h):
        qd = q_n * 1.0 + tb.GAMMA_C * b * (h - tp.H)
        return [("D", qd, 0.0, 8.0), ("L", lo * 1.0, 0.0, 8.0), ("D", q_t * 1.0, y0 - 51.0, y1 - 51.0),
                ("L", lo * 1.0, y0 - 51.0, y1 - 51.0)], pa
    des, r, gaya = tbk._desain_anak(beban_x, [8.0], tb.BALOK_B, uk)
    out[f"x {idn(x0, 0)}"] = {**des, **gaya, "L": 8.0, "lebar": 1.0}
    return {"balok": out, "q_n": q_n, "q_t": q_t, "sidl": sidl, "lo": lo, "turun": turun, "LB1": bim.LB1,
            "lolos": all(v["ok"] for v in out.values())}


# ------------------------------------------------------------------ model STR 7.3 (BIMCraft)
def bangun_str(h):
    """STR 6.9 → STR 7.3: hapus balok K-01 dan rel chiller lama (+ tulangan), tambah rel baru, balok LB-1,
    perlebaran Cap E + 2 tiang di bawah pit L-7. Tulangan unsur baru di DED 7.5."""
    import tahap4_bim as bim
    import tahap6_bim as t6
    from bimcraft import Sesi, ke_v011
    shutil.copy(STR6, BIMC)
    mm = bim.mm
    log = {}
    with Sesi(BIMC) as b:
        b.cmd("project_info", {"status": "Struktur - model LOD 300 langkah 7.3 (basis 6.9): K-01, chiller, LB-1, pit L-7"})
        lev = {k: e["name"] for e in b.alat("query_elements", {"category": "level", "limit": 50})["elements"] for k in (e["id"], e["guid"])}
        bal = b.alat("query_elements", {"category": "beam", "limit": 5000})["elements"]
        hapus = []
        for e in bal:
            (x1, y1, *_), (x2, y2, *_) = e["axis"]
            x, y0_, y1_ = (v * 1000 for v in BALOK_K01)
            k01 = abs(x1 - x) < 1 and abs(x2 - x) < 1 and {round(y1), round(y2)} == {round(y0_), round(y1_)}
            rel = (lev.get(e["level"], e["level"]) == "LT3" and abs(y1 - y2) < 1 and
                   any(abs(y1 - yr * 1000) < 1 for yr in bim.REL_Y) and {round(x1), round(x2)} == {60000, 76000})
            if k01 or rel:
                hapus.append(e)
        guid = {e["guid"] for e in hapus}
        besi = [r["id"] for r in b.alat("query_elements", {"category": "rebar", "limit": 50000})["elements"] if r["host"] in guid]
        for i in range(0, len(besi), 2000):
            b.cmd("delete", {"ids": besi[i:i + 2000]})
        b.cmd("delete", {"ids": [e["id"] for e in hapus]})
        log["hapus_balok"] = len(hapus)
        log["hapus_besi"] = len(besi)
        log["hapus_k01"] = sum(1 for e in hapus if abs(e["axis"][0][0] - 52000) < 1)
        tipe = set()

        def tipe_balok(bb, hb):
            n = f"BL-{round(bb * 1000)}x{round(hb * 1000)}-fc30"
            if n not in tipe:
                b.cmd("type", {"category": "beam", "name": n, "width": round(bb * 1000), "depth": round(hb * 1000),
                               "material": "Beton fc 30 S2"})
                tipe.add(n)
            return n

        baru = []
        rb = h["chiller"]["rel_baru"]
        for g in h["chiller"]["baru"]["tata"]["garis"]:
            if g[6] == "rel":
                r = b.cmd("beam", {"points": [mm(g[1], g[2]), mm(g[1], g[3])], "type": tipe_balok(rb["b"], rb["h"]), "level": "LT3"})
                baru += r.get("ids") or [r.get("id")]
        n_rel = len(baru)
        x0, x1, y0, y1, _ = bim.LB1
        lb = h["lb1"]["balok"]
        for (p, q), k in ((((x0, 51.0), (x0, 59.0)), f"x {idn(x0, 0)}"), (((x0, y0), (x1, y0)), f"y {idn(y0, 0)}"),
                          (((x0, y1), (x1, y1)), f"y {idn(y1, 0)}")):
            r = b.cmd("beam", {"points": [mm(*p), mm(*q)], "type": tipe_balok(lb[k]["b"], lb[k]["h"]), "level": "LT2"})
            baru += r.get("ids") or [r.get("id")]
        ids_b = [i for i in baru if isinstance(i, int)]
        b.cmd("modify", {"ids": ids_b, "params": {"RSTB_Tahap": "7", "RSTB_LOD": "300", "RSTB_Status": STATUS,
                                                  "RSTB_Mutu": "fc' 30 MPa; BjTS 420B", "RSTB_Paket": "tahap 1",
                                                  "RSTB_KelasPaparan": "-",
                                                  "RSTB_Sumber": "[balok] 7.3: rel chiller y ≥ 63 dan balok tepi LB-1"}})
        # perlebaran Cap E + 2 tiang
        ex = h["pit"]["ext"]
        w, d = round((ex[2] - ex[0]) * 1000), round((ex[3] - ex[1]) * 1000)
        nt = f"PC-{w}x{d}-h2000-fc35"
        b.cmd("type", {"category": "footing", "name": nt, "width": w, "depth": d, "material": "Beton fc 35 S2"})
        r = b.cmd("footing", {"at": mm((ex[0] + ex[2]) / 2, (ex[1] + ex[3]) / 2), "type": nt, "thickness": 2000,
                              "offset": round((t6.MUKA_CAP - t6.LT1) * 1000), "level": "LT1"})
        ids_p = [i for i in (r.get("ids") or [r.get("id")]) if isinstance(i, int)]
        contoh = next(t for t in t6.tiang() if t["cap"] == "Cap E")
        for x, y in TIANG_L7:
            r = b.cmd("structural_column", {"at": mm(x, y), "type": "TB-800-fc35", "level": "LT1",
                                            "base_offset": round((contoh["z0"] - t6.LT1) * 1000), "height": round(contoh["L"] * 1000)})
            ids_p += [i for i in (r.get("ids") or [r.get("id")]) if isinstance(i, int)]
        b.cmd("modify", {"ids": ids_p, "params": {"RSTB_Tahap": "7", "RSTB_LOD": "300", "RSTB_Status": STATUS,
                                                  "RSTB_Mutu": "fc' 35 MPa; BjTS 420B", "RSTB_Paket": "tahap 1",
                                                  "RSTB_KelasPaparan": "S2",
                                                  "RSTB_Sumber": "[cap] 7.3 perlebaran Cap E di bawah pit L-7 (h 2.000, menyatu) "
                                                                 "+ 2 tiang bor Ø800 seperti Cap E"}})
        log.update(rel_baru=n_rel, lb1=3, cap_ext=1, tiang_baru=len(TIANG_L7))
        b.simpan(BIMC)
        b.simpan(IFC)
    t6.ifc_pasca(IFC)
    ke_v011(IFC)
    return log


def cek_model(path=IFC):
    """Hitung ulang dari IFC: balok di inti lift, rel LT3, tiang, cap (pembanding log bangun)."""
    import ifcopenshell
    import ifcopenshell.util.placement as up
    f = ifcopenshell.open(str(path))
    inti = box(50.175, 35.175, 57.825, 42.825)
    n_inti = 0
    for e in f.by_type("IfcBeam"):
        m = up.get_local_placement(e.ObjectPlacement)
        if inti.contains(box(m[0, 3] / 1000 - 0.01, m[1, 3] / 1000 - 0.01, m[0, 3] / 1000 + 0.01, m[1, 3] / 1000 + 0.01)) \
                and "BL-350x600" in (e.Name or e.ObjectType or ""):
            n_inti += 1
    return {"IfcPile": len(f.by_type("IfcPile")), "IfcFooting": len(f.by_type("IfcFooting")),
            "IfcBeam": len(f.by_type("IfcBeam")), "balok_titik_awal_di_inti": n_inti}


# ------------------------------------------------------------------ hitung semua
def hitung():
    return {"k01": k01_opensees(), "chiller": chiller(), "pit": pit_k04b(), "fasad": fasad_t112(), "lb1": lb1()}


KEPUTUSAN = [
    ("K7.3-1 K-01 balok inti lift", "Balok BL-350x600 as 6 (x 52, y 35-43) LT2-ATAP dihapus (6 balok); pelat inti lift "
     "tidak ada (ruang luncur), kolom 6/B dan 6/C tetap dijepit balok arah x dan dinding inti. Model 4.3 berubah ≤ 0,3 %, "
     "jadi hasil Tahap 4-6 tetap berlaku tanpa hitung ulang."),
    ("K7.3-2 Chiller M-01 (keputusan rencana 5)", "Frekuensi lantai atap jauh di bawah 1,4 × 14,5 Hz di kedua letak, "
     "jadi cabang pegas-saja tidak berlaku; chiller dipindah ke y ≥ 63 (unit diputar 11 m arah y, x 68,4-81,3, y 63,5-74,5, "
     "di atas rehab medik/isolasi/koridor, bukan kamar operasi) dan tetap di atas pegas δ 25 mm (RKS). Rel baru arah y; pompa "
     "M-04 pindah ke x 60-68, y 62-66 [Asumsi]."),
    ("K7.3-3 Pit K-04b", "L-5..6: pelat dasar dan dinding pit menjorok 0,39 m dari muka utara Cap E sebagai kantilever, "
     "tanpa perlebaran. L-7: Cap E diperlebar lokal x 37,1-41,7, y 29,4-32,2 (h 2.000, menyatu) dengan 2 tiang Ø800 baru; "
     "balok penggantung 5.6 tidak diperlukan. Perlebaran tanpa tiang ditolak: tiang Cap E sudah di rasio layan 1,00."),
    ("K7.3-4 Fasad T-112", "Beban fasad V4 lebih kecil dari V3 4.10, jadi angkur dan balok tepi 4.10 tetap (tidak dicek ulang)."),
    ("K7.3-5 LB-1 (keputusan rencana 6)", "Balok tepi di tiga sisi pelat turun (x 70; y 52; y 56); sisi x 76 = balok induk. "
     "Pelat tetap 200 mm; isian screed 250 mm [Asumsi]."),
]


# ------------------------------------------------------------------ Excel
def buat_excel(h):
    import openpyxl
    from format_dokumen import Lembar, set_font_bawaan
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    k, c, p, fs, lb = h["k01"], h["chiller"], h["pit"], h["fasad"], h["lb1"]
    s = Lembar(wb.create_sheet("Ringkasan"), 1, "Ringkasan cek struktur tambahan 7.3", [6, 54, 30, 50])
    s.catatan(f"STATUS: {STATUS}. {LABEL}")
    s.catatan("Petunjuk: tiap lembar satu butir (K-01, Chiller, Pit, Fasad dan LB-1); lembar Acuan dan Keputusan memuat pasal "
              "dan keputusan atas delegasi. Hitung ulang: .venv\\Scripts\\python.exe skrip\\tahap7_cek_struktur.py")
    s.kosong()
    s.bagian("A", "Hasil utama")
    s.tabel(["No", "Butir", "Hasil", "Keterangan"], [
        [1, "K-01: perubahan model 4.3 tanpa balok inti lift", f"maks {idn(k['maks'], 2)} %", f"batas {TOL['K-01']} %; {k['hapus']} elemen dihapus"],
        [2, "T-113 frekuensi atap chiller (letak lama): tangan / OpenSees", f"{idn(c['lama']['tangan']['f'], 2)} / {idn(c['lama']['f1'], 2)} Hz",
         f"selisih {idn(c['lama']['selisih'], 1)} % (batas {idn(TOL['T-113'], 0)} %); syarat {idn(c['lama']['syarat'], 1)} Hz"],
        [3, "Frekuensi letak baru y ≥ 63: tangan / OpenSees", f"{idn(c['baru']['tangan']['f'], 2)} / {idn(c['baru']['f1'], 2)} Hz",
         f"selisih {idn(c['baru']['selisih'], 1)} %"],
        [4, "K-04b L-7: 2 tiang baru, beban layan per tiang", f"{idn(p['lokal'], 0)} kN", f"izin {idn(p['izin'], 0)} kN; rasio {idn(p['rasio_lokal'], 2)}"],
        [5, "T-112 fasad V4 vs V3 4.10", f"{idn(fs['w4'], 0)} vs {idn(fs['w3'], 0)} kN", f"{idn(fs['selisih'], 1)} % (lebih ringan)"],
        [6, "LB-1 balok tepi", "lolos" if lb["lolos"] else "gagal", ", ".join(f"{n}: {idn(v['b'] * 1000, 0)} × {idn(v['h'] * 1000, 0)}" for n, v in lb["balok"].items())],
    ], rata=list("clcl"), beku=False)
    s = Lembar(wb.create_sheet("K-01"), 2, "K-01: balok as 6 di inti lift, model OpenSees 4.3 K2", [50, 16, 16, 14])
    s.catatan("Model tahap4_model.bangun (K2) dijalankan dua kali; kedua, 6 balok x 52 y 35-43 dihapus (ops.remove). ELF dan ragam 4.3.")
    s.tabel(["Besaran", "Dengan balok", "Tanpa balok", "Selisih (%)"],
            [[n, round(a, 4), round(b, 4), round(d, 3)] for n, a, b, d in k["baris"]], rata=list("lrrr"))
    s = Lembar(wb.create_sheet("Chiller"), 3, "Chiller M-01: frekuensi alami lantai atap podium (T-113)", [52, 18, 18, 40])
    s.catatan("Cara 1: f = 0,18 √(g/Δ), Δ = Δ rel (sendi 8 m) + Δ induk (jepit di kolom), beban massa (pelat 200 + SIDL atap, "
              "berat balok, chiller 115,8 kN/6 titik). [Asumsi: rumus Rayleigh; acuan dinamika belum ada di acuan/]. Cara 2: grillage "
              "openseespy, EI kotor, kolom = tumpuan jepit (aksi portal).")
    rows = []
    for letak in ("lama", "baru"):
        x = c[letak]
        t = x["tangan"]
        rows += [[f"[{letak}] Δ rel / Δ induk (mm)", round(t["d_r"] * 1e3, 2), round(t["d_i"] * 1e3, 2), "cara 1"],
                 [f"[{letak}] f rel / f induk / f gabungan cara 1 (Hz)", round(t["f_r"], 2), round(t["f"], 2), f"f induk {t['f_i']:.2f}"],
                 [f"[{letak}] f1..f3 OpenSees (Hz)", round(x["ops"]["f"][0], 2), round(x["ops"]["f"][2], 2),
                  ", ".join(f"{v:.2f}" for v in x["ops"]["f"][:6])],
                 [f"[{letak}] selisih cara 1 vs 2 (%)", round(x["selisih"], 1), TOL["T-113"], "T-113"],
                 [f"[{letak}] syarat 1,4 × 14,5 Hz", round(x["syarat"], 1), "lolos" if x["lolos_syarat"] else "tidak", "keputusan rencana 5"],
                 [f"[{letak}] ragam dalam 14,5 ± 10 % (f, massa efektif)", len(x["dekat_kipas"]), "-",
                  "; ".join(f"{f:.2f} Hz ({m * 100:.1f} %)" for f, m in x["dekat_kipas"]) or "-"]]
    pg = c["pegas"]
    rows += [["Pegas δ 25 mm: f pegas (Hz) / rasio 14,5/f", round(pg["f"], 2), round(pg["r"], 2), f"transmisibilitas {pg['T']:.3f} (lantai kaku)"],
             ["y ≥ 63 orientasi x: perlu / ada (m)", round(c["y63"]["perlu"], 1), round(c["y63"]["ada_x"], 1), "tidak muat" if not c["y63"]["muat_x"] else "muat"],
             ["y ≥ 63 orientasi y: di atap, tumpang tangki (m²)", "ya" if c["y63"]["di_atap"] else "tidak", round(c["y63"]["tumpang_tangki"], 2), "muat" if c["y63"]["muat_y"] else "tidak muat"]]
    rb, rl = c["rel_baru"], c["rel_lama"]
    rows += [["Rel lama 4.6 (arah x, x 60-76)", f"{rl['b'] * 1000:.0f} × {rl['h'] * 1000:.0f}", "-", "dihapus di STR 7.3"],
             ["Rel baru (arah y, y 59-67-75): b × h, Mu-/Mu+/Vu", f"{rb['b'] * 1000:.0f} × {rb['h'] * 1000:.0f}",
              f"{rb['Mneg']:.0f}/{rb['Mpos']:.0f}/{rb['Vu']:.0f}", "lolos" if rb["ok"] else "gagal"]]
    s.tabel(["Butir", "Nilai 1", "Nilai 2", "Keterangan"], rows, rata=list("lrrl"))
    s = Lembar(wb.create_sheet("Pit"), 4, "K-04b: pit lift di luar telapak Cap E", [52, 18, 18, 40])
    rows = [[f"{n}: luas / di luar Cap E (m²)", round(v["luas"], 2), round(v["luar"], 2), f"menjorok {v['jarak']:.2f} m; layan {v['layan']:.0f} kN"]
            for n, v in p["pits"].items()]
    kt = p["kant"]
    rows += [["L-5..6 kantilever pelat dasar: Mu / φMn tulangan min (kNm/m)", round(kt["Mu"], 1), round(kt["phiMn_min"], 1), "lolos" if kt["lolos"] else "gagal"],
             ["Cap E 6.3 dasar: P layan maks / izin (kN)", round(p["dasar"]["P_layan"], 1), round(p["izin"], 1), "rasio 1,00"],
             ["Opsi A perlebar tanpa tiang: P layan maks (kN)", round(p["opsi_a"]["P_layan"], 1), round(p["izin"], 1), "gagal layan" if p["opsi_a"]["P_layan"] > p["izin"] else "lolos"],
             ["Opsi B perlebar + 2 tiang: berat perlebaran (kN)", round(p["w_ext"], 0), "-", f"kotak {tuple(round(v, 2) for v in p['ext'])}"],
             ["Opsi B: layan / ultimit per tiang baru (kN)", round(p["lokal"], 0), round(p["lokal_u"], 0), f"izin layan {p['izin']:.0f}; rasio {p['rasio_lokal']:.2f}"],
             ["Opsi B: jarak tiang baru ke tiang terdekat (m)", round(p["jarak_min"], 2), 2.4, "≥ 3D"],
             ["Pit L-7 tertutup cap + perlebaran", "ya" if p["pit_tertutup"] else "tidak", "-", "-"]]
    s.tabel(["Butir", "Nilai 1", "Nilai 2", "Keterangan"], rows, rata=list("lrrl"))
    s = Lembar(wb.create_sheet("Fasad dan LB-1"), 5, "T-112 beban fasad V4 dan LB-1 balok tepi", [40, 16, 14, 50, 16])
    s.tabel(["Tipe fasad (model 7.1)", "Luas (m²)", "q (kPa)", "Sumber", "Berat (kN)"],
            [[n, round(a, 1), q, src, round(w, 1)] for n, a, q, src, w in fs["rinci"]] +
            [["Jumlah V4", "-", "-", "-", round(fs["w4"], 1)], ["V3 4.10 (berat_fasad wv3)", "-", "-", "4.10", round(fs["w3"], 1)],
             ["Kepekaan panel GRC 1,0 kPa [Asumsi]", "-", "-", "-", round(fs["w_grc"], 1)]], rata=list("lrrlr"))
    s.kosong()
    s.tabel(["Balok LB-1", "b × h (mm)", "L (m)", "Atas / bawah, Mu+ / Vu", "Status"],
            [[n, f"{v['b'] * 1000:.0f} × {v['h'] * 1000:.0f}", v["L"],
              f"{v['atas']['n']}D{v['atas']['db']} / {v['bawah']['n']}D{v['bawah']['db']}; {v['Mpos']:.0f} kNm / {v['Vu']:.0f} kN",
              "lolos" if v["ok"] else "gagal"] for n, v in lb["balok"].items()], rata=list("lcrll"))
    s = Lembar(wb.create_sheet("Acuan dan Keputusan"), 6, "Acuan dan keputusan 7.3", [36, 110])
    s.tabel(["Butir", "Isi"], KEPUTUSAN + [
        ("Acuan balok", "SNI 2847:2019 Pasal 9 dan Tabel 9.7.6.2.2 lewat tahap4_balok._desain_anak (pasal sama dengan 4.6)"),
        ("Acuan berat", "SNI 1727:2020 Tabel C3.1-1 hal. 278 (kaca); panel dan overstek [Asumsi] seperti 4.10"),
        ("Acuan tiang", "Rumus cap kaku dan izin 6.3 (tahap6_tata_letak.periksa)"),
        ("Belum ada di acuan", "Kriteria getaran alat (rasio 1,4; pegas 25 mm) dan rumus Rayleigh: [Asumsi]")], rata=list("ll"))
    wb.save(XLSX)
    return XLSX


# ------------------------------------------------------------------ md dan VERIFIKASI
def tulis_md(h, log=None, model=None):
    k, c, p, fs, lb = h["k01"], h["chiller"], h["pit"], h["fasad"], h["lb1"]
    L = [f"# 7.3 Cek Struktur Tambahan ({STATUS})", "", f"{LABEL} Skrip `skrip/tahap7_cek_struktur.py`, Excel "
         "`7.3 Cek Struktur Tambahan.xlsx`, model `model/RSTB-STR-T7-LOD300.bimc/.ifc` (+ `-v0.11.bimc`). Kunci jawaban tidak dibuka.", "",
         "## K-01 balok as 6 di inti lift", "",
         f"Balok BL-350x600 x 52, y 35-43 di LT2-ATAP ({k['hapus']} elemen di model 4.3) melintas di ruang luncur lift L-1..4. "
         "Dihapus. Inti lift tidak punya pelat (ruang luncur), jadi balok hanya memikul berat sendiri; kolom 6/B dan 6/C tetap terikat "
         "balok arah x dan dinding inti.", "", "| Besaran | Dengan balok | Tanpa balok | Selisih (%) |", "|---|---|---|---|"]
    L += [f"| {n} | {idn(a, 4)} | {idn(b, 4)} | {idn(d, 3)} |" for n, a, b, d in k["baris"]]
    L += ["", f"Selisih maksimum {idn(k['maks'], 2)} % ≤ {idn(TOL['K-01'], 0)} % (batas ditetapkan sebelum menghitung): hasil Tahap 4-6 tetap. "
          "Skrip tahap 4 tidak diubah (balok dihapus lewat `ops.remove` di skrip ini), jadi cache OpenSees tidak basi.", ""]
    for letak, judul in (("lama", "letak Tahap 4 (x 62,5-73,5, y 52,9-65,7)"), ("baru", "y ≥ 63 (unit diputar)")):
        x, t = c[letak], c[letak]["tangan"]
        if letak == "lama":
            L += ["## Chiller M-01 dan 14,5 Hz (T-113, B-7)", "",
                  "Cara 1: f = 0,18 √(g/Δ) [Asumsi: rumus Rayleigh balok sendi bermassa merata; acuan dinamika belum ada di acuan/], "
                  "Δ = Δ rel (sendi 8 m) + Δ balok induk (jepit di kolom). Cara 2: grillage openseespy (balok EI kotor, kolom "
                  "tumpuan jepit, massa pelat 200 + SIDL atap satu arah ke garis sejajar rel, chiller 115,8 kN di 6 titik).", "",
                  "| Letak | Δ rel (mm) | Δ induk (mm) | f cara 1 (Hz) | f1 OpenSees (Hz) | Selisih (%) | Syarat 20,3 Hz |", "|---|---|---|---|---|---|---|"]
        L.append(f"| {judul} | {idn(t['d_r'] * 1e3, 2)} | {idn(t['d_i'] * 1e3, 2)} | {idn(t['f'], 2)} | {idn(x['f1'], 2)} | "
                 f"{idn(x['selisih'], 1)} | {'lolos' if x['lolos_syarat'] else 'tidak'} |")
    pg, y = c["pegas"], c["y63"]
    lol = all(abs(c[k]["selisih"]) <= TOL["T-113"] for k in ("lama", "baru"))
    L += ["", f"**T-113 {'lolos' if lol else 'gagal toleransi'}** (batas {idn(TOL['T-113'], 0)} %): selisih {idn(c['lama']['selisih'], 1)} % / "
          f"{idn(c['baru']['selisih'], 1)} %. Cara 1 menggabung rel dan balok induk sefase (Dunkerley, batas bawah), sedangkan "
          "ragam pertama grillage adalah getaran rel sendiri (rel tanpa pelat penghubung, balok induk hampir diam); rel sendiri cara 1 "
          f"{idn(c['lama']['tangan']['f_r'], 2)} Hz vs grillage {idn(c['lama']['f1'], 2)} Hz. Kesimpulan tidak peka terhadap selisih ini: "
          f"kedua cara ≤ {idn(max(c['lama']['f1'], c['baru']['f1']), 1)} Hz, jauh di bawah 20,3 Hz dan di bawah 14,5 Hz."]
    L += ["", f"Ragam OpenSees letak lama: {', '.join(idn(v, 2) for v in c['lama']['ops']['f'][:6])} Hz; ragam dalam 14,5 ± 10 %: "
          f"{'; '.join(f'{idn(f, 2)} Hz (massa efektif {idn(m * 100, 1)} %)' for f, m in c['lama']['dekat_kipas']) or 'tidak ada'}. "
          f"Letak baru: {', '.join(idn(v, 2) for v in c['baru']['ops']['f'][:6])} Hz; dalam 14,5 ± 10 %: "
          f"{'; '.join(f'{idn(f, 2)} Hz ({idn(m * 100, 1)} %)' for f, m in c['baru']['dekat_kipas']) or 'tidak ada'}.", "",
          f"Keputusan rencana 5: frekuensi lantai ≥ 1,4 × 14,5 = 20,3 Hz tidak tercapai di kedua letak (lantai beton bentang 8 m "
          f"secara wajar 5-10 Hz; mencapai 20,3 Hz butuh Δ ≤ {idn((0.18 / 20.3) ** 2 * G * 1e3, 2)} mm), jadi cabang pegas-saja "
          f"tidak berlaku dan chiller **dipindah ke y ≥ 63**. Orientasi asli (11 m arah x) tidak muat: perlu {idn(y['perlu'], 1)} m, "
          f"ada {idn(y['ada_x'], 1)} m (y 63-75). Unit diputar (11 m arah y): x0 = {', '.join(idn(v, 1) for v in y['x0'])}, y 63,5-74,5, "
          f"di atas atap {'ya' if y['di_atap'] else 'tidak'}, tumpang tangki opsi B {idn(y['tumpang_tangki'], 2)} m². Di bawahnya "
          "LT2 rehab medik, isolasi, dan koridor (letak lama di atas Kamar operasi 4). Pegas δ 25 mm tetap dipasang: f pegas "
          f"{idn(pg['f'], 2)} Hz, rasio 14,5/f {idn(pg['r'], 2)}, transmisibilitas lantai kaku {idn(pg['T'], 3)} (RKS 7.7).", "",
          f"Rel baru arah y (x {', '.join(idn(g[1], 1) for g in c['baru']['tata']['garis'] if g[6] == 'rel')}; y 59-67-75; satu rel "
          "berimpit balok induk x 76): "
          f"{idn(c['rel_baru']['b'] * 1000, 0)} × {idn(c['rel_baru']['h'] * 1000, 0)}, Mu- {idn(c['rel_baru']['Mneg'], 0)} kNm, "
          f"Mu+ {idn(c['rel_baru']['Mpos'], 0)} kNm, Vu {idn(c['rel_baru']['Vu'], 0)} kN, {'lolos' if c['rel_baru']['ok'] else 'gagal'} "
          "(pola 4.6 `balok_chiller`). Rel lama 8 × x 60-76 dihapus dari model STR. Pompa M-04 pindah ke x 60-68, y 62-66 [Asumsi].", "",
          "## K-04b pit lift di luar Cap E", "", "| Pit | Luas (m²) | Di luar cap (m²) | Menjorok (m) | Layan (kN) |", "|---|---|---|---|---|"]
    L += [f"| {n} | {idn(v['luas'], 2)} | {idn(v['luar'], 2)} | {idn(v['jarak'], 2)} | {idn(v['layan'], 0)} |" for n, v in p["pits"].items()]
    kt = p["kant"]
    L += ["", "Beban pit sudah ada di reaksi 6.3 lewat 5.6 (L-1..4 ke inti, L-5..6 ke 6/C dan 7/C, L-7 lewat balok penggantung).",
          "", f"- **L-5..6**: pelat dasar 400 dan dinding 300 menjorok {idn(kt['a'], 2)} m dari muka utara Cap E sebagai kantilever: "
          f"Mu {idn(kt['Mu'], 1)} kNm/m ≤ φMn tulangan minimum {idn(kt['phiMn_min'], 1)} kNm/m. Tidak diperlebar.",
          f"- **L-7** menjorok {idn(p['pits']['L-7']['jarak'], 2)} m. Perlebaran tanpa tiang (berat {idn(p['w_ext'], 0)} kN + "
          f"bagian pit yang semula ke as A): P layan maks Cap E {idn(p['opsi_a']['P_layan'], 0)} kN > izin {idn(p['izin'], 0)} kN "
          f"(sudah {idn(p['dasar']['P_layan'], 0)} kN, rasio 1,00): **ditolak**. Dipilih perlebaran x {idn(p['ext'][0], 1)}-{idn(p['ext'][2], 1)}, "
          f"y {idn(p['ext'][1], 1)}-{idn(p['ext'][3], 2)}, h 2.000, menyatu dengan Cap E, dengan **2 tiang Ø800 baru** di "
          f"{', '.join(f'({idn(a, 1)}; {idn(b, 1)})' for a, b in p['tiang_baru'])}: perlebaran + seluruh pit ke 2 tiang = "
          f"{idn(p['lokal'], 0)} kN/tiang (rasio {idn(p['rasio_lokal'], 2)}), jarak ke tiang terdekat {idn(p['jarak_min'], 2)} m ≥ 2,4 m. "
          "Balok penggantung 5.6 tidak diperlukan (beban cap as A turun, aman). Tiang gedung utama 251 → 253 (total 319 → 321).", "",
          "## T-112 beban fasad", "", "| Tipe | Luas (m²) | q (kPa) | Berat (kN) |", "|---|---|---|---|"]
    L += [f"| {n} | {idn(a, 1)} | {idn(q, 2)} | {idn(w, 0)} |" for n, a, q, _, w in fs["rinci"]]
    L += ["", f"V4 {idn(fs['w4'], 0)} kN vs V3 4.10 {idn(fs['w3'], 0)} kN ({idn(fs['selisih'], 1)} %); dengan panel GRC 1,0 kPa "
          f"[Asumsi] {idn(fs['w_grc'], 0)} kN, tetap di bawah V3. Luas panel termasuk bagian di belakang kaca pita (konservatif). "
          "T-112 lolos: angkur dan balok tepi 4.10 tetap.", "", "## LB-1 balok tepi pelat turun CSSD LT2", "",
          f"Pelat turun x {idn(lb['LB1'][0], 0)}-{idn(lb['LB1'][1], 0)}, y {idn(lb['LB1'][2], 0)}-{idn(lb['LB1'][3], 0)}, -300 mm. "
          f"Beban: pelat 200 + SIDL {idn(lb['sidl'], 2)} kPa = {idn(lb['q_n'], 2)} kPa; di pelat turun + isian screed 250 mm × 20 kN/m³ "
          f"[Asumsi] = {idn(lb['q_t'], 2)} kPa; Lo {idn(lb['lo'], 2)} kPa (P1). Desain `tahap4_balok._desain_anak` (SNI 2847 Pasal 9, "
          "seperti 4.6). Sisi x 76 = balok induk.", "", "| Balok | b × h (mm) | L (m) | Tulangan atas/bawah | Mu+ (kNm) | Vu (kN) | Status |",
          "|---|---|---|---|---|---|---|"]
    L += [f"| {n} | {idn(v['b'] * 1000, 0)} × {idn(v['h'] * 1000, 0)} | {idn(v['L'], 1)} | {v['atas']['n']}D{v['atas']['db']} / "
          f"{v['bawah']['n']}D{v['bawah']['db']} | {idn(v['Mpos'], 0)} | {idn(v['Vu'], 0)} | {'lolos' if v['ok'] else 'gagal'} |"
          for n, v in lb["balok"].items()]
    if log:
        L += ["", "## Model STR 7.3", "", f"Dari STR 6.9: {log['hapus_balok']} balok dihapus ({log['hapus_k01']} K-01, "
              f"{log['hapus_balok'] - log['hapus_k01']} rel lama; tulangan terhapus {log['hapus_besi']}: STR 6.9 hanya memuat tulangan tiang "
              f"dan Cap E); ditambah {log['rel_baru']} "
              f"rel baru, {log['lb1']} balok LB-1, 1 perlebaran Cap E, {log['tiang_baru']} tiang. Tulangan unsur baru digambar di DED 7.5."]
    if model:
        L.append(f"Cek IFC: {model['IfcPile']} IfcPile, {model['IfcFooting']} IfcFooting, {model['IfcBeam']} IfcBeam.")
    L += ["", "## Keputusan (disetujui atas delegasi Defsa 22 Nov 2026)", ""] + [f"- **{a}**: {b}" for a, b in KEPUTUSAN]
    L += ["", "## Langkah berikutnya", "", "Federasi 7.2 diulang dengan STR 7.3 (T-111). Lalu 7.4-7.6 DED: denah atap dengan letak "
          "chiller/pompa baru (GA), GS perlebaran Cap E + 2 tiang dan LB-1 (7.5), tulangan rel baru."]
    MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    return MD


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    h = hitung()
    import json
    jlog = AKAR / "cache" / "tahap7_cek_struktur_log.json"     # ringkasan bangun terakhir (md tetap lengkap tanpa --bangun)
    if "--bangun" in argv:
        log = bangun_str(h)
        jlog.parent.mkdir(exist_ok=True)
        jlog.write_text(json.dumps(log), encoding="utf-8")
    else:
        log = json.loads(jlog.read_text(encoding="utf-8")) if jlog.exists() else None
    model = cek_model() if IFC.exists() else None
    buat_excel(h)
    tulis_md(h, log, model)
    k, c = h["k01"], h["chiller"]
    print("K-01 maks %", round(k["maks"], 3), "| f lama", round(c["lama"]["tangan"]["f"], 2), round(c["lama"]["f1"], 2),
          "| f baru", round(c["baru"]["tangan"]["f"], 2), round(c["baru"]["f1"], 2), "| y63", c["y63"]["muat_y"],
          "| rel", c["rel_baru"]["b"], c["rel_baru"]["h"], c["rel_baru"]["ok"], "| pit", round(h["pit"]["opsi_a"]["P_layan"]),
          round(h["pit"]["lokal"]), "| fasad", round(h["fasad"]["w4"]), round(h["fasad"]["w3"]), "| LB-1", h["lb1"]["lolos"],
          "| log", log, "| model", model)
    return h


if __name__ == "__main__":
    main()
