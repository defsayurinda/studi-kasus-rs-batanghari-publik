"""Tahap 4 langkah 4.3: model analisis 3D sistem ganda di openseespy (ragam, gaya lateral ekivalen, ragam spektrum).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (20 Nov 2026); draf, menunggu persetujuan
Defsa. Kunci jawaban tidak dibuka.

Model: kolom dan balok `elasticBeamColumn`, dinding inti sebagai kolom kotak `ElasticTimoshenkoBeam` di pusat inti
(geser ikut dihitung), diafragma kaku per lantai (`rigidDiaphragm`) dengan massa dan inersia putar di pusat massa,
jepit di LT1 +12,85 (Pasal 7.7.1; interaksi tanah-struktur di Tahap 6). Kekakuan retak SNI 2847:2019 Tabel 6.6.3.1.1:
kolom 0,70 Ig, balok 0,35 Ig, dinding retak 0,35 Ig (luas 1,0 Ag). Ec = 4.700 √fc' (Pasal 19.2.2.1): fc' 35 kolom dan
dinding, 30 balok (3.6). Berat seismik dan geometri dari langkah 4.2 (tahap4_beban). Spektrum desain 4.1 opsi (a).
SNI 1726:2019: Pasal 7.7.3 (model 3D, retak), 7.8 (ELF), 7.8.4.2 (torsi tak terduga 5 %), 7.8.6 (simpangan), 7.8.7
(P-delta), 7.9.1 (ragam spektrum, CQC, skala 100 %), Tabel 13-14 (ketidakberaturan), Tabel 16, Tabel 20 (0,010 hsx),
7.2.5.1 (sistem ganda 25 %).
"""
from __future__ import annotations

import csv
import functools
import math
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_beban as tb  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "04 Struktur Atas"
LABEL = tb.LABEL
STATUS = "disetujui Defsa 20 Nov 2026 (tipe 1b diterima)"
G = 9.81
EC_35 = 4700 * math.sqrt(35) * 1000    # kPa
EC_30 = 4700 * math.sqrt(30) * 1000
NU = 0.2
RETAK = {"kolom": 0.70, "balok": 0.35, "dinding": 0.35}
# Penampang balok khusus (4.6): {(lv, x1, y1, x2, y2): (b, h)}; kosong = semua balok BALOK_B × BALOK_H (4.3).
UKURAN_BALOK = {}
# Kolom khusus (4.7): {(lv ujung atas, x, y): b}; kosong = ukuran per tingkat 3.6.
UKURAN_KOLOM = {}
ZETA = 0.05
DASAR = tb.LEVEL["LT1"]
PUSAT_INTI = {"Tangga x22 y39": (22, 39), "Tangga x46 y39": (46, 39), "Tangga x70 y39": (70, 39),
              "Tangga x22 y63": (22, 63), "Tangga x46 y63": (46, 63), "Tangga x70 y63": (70, 63),
              "Inti lif x50-58 y35-43": (54, 39)}
UKURAN_INTI = {"Tangga": (4.0, 6.0), "Inti": (8.0, 8.0)}
POSISI_ALAT_ATAP = (67.0, 68.0)
PANJANG_UJUNG = 8.0   # m, dinding geser ujung menara arah Y (alternatif, as 2 dan 10, y 35-43)
DINDING_UJUNG = [("Ujung x20", "ATAP", 20.0, 39.0), ("Ujung x84", "ATAP", 84.0, 39.0)]   # pusat berat alat atap podium utara (chiller, tangki, pompa) dari Daftar Alat


# ------------------------------------------------------------------ penampang
def kotak(dx, dy, t):
    """A, Ix (terhadap sumbu sejajar X), Iy (sejajar Y), J, Av arah X, Av arah Y untuk kotak dinding tebal t (as)."""
    bo, ho, bi, hi = dx + t, dy + t, dx - t, dy - t
    a = bo * ho - bi * hi
    ix = (bo * ho ** 3 - bi * hi ** 3) / 12   # lentur akibat gaya arah Y
    iy = (ho * bo ** 3 - hi * bi ** 3) / 12   # lentur akibat gaya arah X
    am = dx * dy
    j = 4 * am ** 2 * t / (2 * (dx + dy))
    return a, ix, iy, j, 2 * dx * t, 2 * dy * t


def persegi(b, h):
    return b * h, b * h ** 3 / 12, h * b ** 3 / 12, b * h * (b ** 2 + h ** 2) / 12 * 0.6


# ------------------------------------------------------------------ data per tingkat
def data_tingkat(konfig="K2"):
    """Tingkat dengan wilayah, berat, pusat massa, dan inersia putar."""
    from shapely.ops import unary_union
    tk = tb.tingkat(konfig)
    berat = {t["lv"]: t for t in tb.berat_tingkat(konfig)}
    out = []
    for t in tk:
        lv = t["lv"]
        g = [x for x in (t.get("lantai"), t.get("atap"), t.get("atap_ringan")) if x is not None]
        wil = unary_union(g)
        w = berat[lv]["w"]
        mep_atap = 0.0
        if lv == "LT3":
            mep_atap = [v for n, v in tb.alat_per_lantai()["LT3"] if n.startswith("Atap podium")][0]
        wu = w - mep_atap
        c = wil.centroid
        xc = (wu * c.x + mep_atap * POSISI_ALAT_ATAP[0]) / w
        yc = (wu * c.y + mep_atap * POSISI_ALAT_ATAP[1]) / w
        # inersia putar: bidang merata (integrasi numerik grid 1 m) + massa titik alat
        xs, ys = np.meshgrid(np.arange(0.5, 140, 1.0), np.arange(0.5, 100, 1.0))
        pts = [(x, y) for x, y in zip(xs.ravel(), ys.ravel()) if wil.contains(Point(x, y))]
        p = np.array(pts)
        ip = np.mean((p[:, 0] - xc) ** 2 + (p[:, 1] - yc) ** 2) * wu
        ip += mep_atap * ((POSISI_ALAT_ATAP[0] - xc) ** 2 + (POSISI_ALAT_ATAP[1] - yc) ** 2)
        minx, miny, maxx, maxy = wil.bounds
        out.append({"lv": lv, "z": tb.LEVEL[lv] - DASAR, "wil": wil, "w": w, "m": w / G, "J": ip / G,
                    "xc": xc, "yc": yc, "bounds": (minx, miny, maxx, maxy), "kolom_bawah": t["kolom_bawah"]})
    return out


# ------------------------------------------------------------------ pembangun model
def nid(i, ix, iy):
    return i * 1000 + ix * 10 + iy


def bangun(konfig="K2", tanpa_inti=False, faktor_dinding=None, dinding_ujung=False):
    import openseespy.opensees as ops
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)
    tk = data_tingkat(konfig)
    gx, gy = tb.GRID_X, tb.GRID_Y
    ops.geomTransf("Linear", 1, 1.0, 0.0, 0.0)   # kolom/inti: z lokal = X global
    ops.geomTransf("Linear", 2, 0.0, 0.0, 1.0)   # balok: z lokal = Z global
    gc = EC_35 / (2 * (1 + NU))
    gb = EC_30 / (2 * (1 + NU))
    fd = faktor_dinding if faktor_dinding is not None else RETAK["dinding"]
    ada = set()
    # dasar
    for ix, x in enumerate(gx):
        for iy, y in enumerate(gy):
            if tb.PODIUM.buffer(0.01).contains(Point(x, y)):
                ops.node(nid(0, ix, iy), x, y, 0.0)
                ops.fix(nid(0, ix, iy), 1, 1, 1, 1, 1, 1)
                ada.add(nid(0, ix, iy))
    inti = {}
    if not tanpa_inti:
        for k, (nama, kel, puncak) in enumerate(tb.INTI):
            cx, cy = PUSAT_INTI[nama]
            ops.node(50000 + k, cx, cy, 0.0)
            ops.fix(50000 + k, 1, 1, 1, 1, 1, 1)
            inti[k] = (nama, puncak, cx, cy)
        if dinding_ujung:
            for k, (nama, puncak, cx, cy) in enumerate(DINDING_UJUNG, start=len(tb.INTI)):
                ops.node(50000 + k, cx, cy, 0.0)
                ops.fix(50000 + k, 1, 1, 1, 1, 1, 1)
                inti[k] = (nama, puncak, cx, cy)
    ele = 1
    kolom_lt1, inti_lt1 = [], []
    daftar_balok, daftar_kolom, daftar_inti = [], [], []
    master = {}
    for i, t in enumerate(tk, start=1):
        z = t["z"]
        wil_b, uk0 = t["kolom_bawah"]
        budak = []
        for ix, x in enumerate(gx):
            for iy, y in enumerate(gy):
                p = Point(x, y)
                bawah = nid(i - 1, ix, iy)
                if wil_b.buffer(0.01).contains(p) and bawah in ada:
                    uk = UKURAN_KOLOM.get((t["lv"], x, y), uk0)
                    a, iz_, iy_, j = persegi(uk, uk)
                    n = nid(i, ix, iy)
                    ops.node(n, x, y, z)
                    ada.add(n)
                    ops.element("elasticBeamColumn", ele, bawah, n, a, EC_35, gc, j, RETAK["kolom"] * iy_,
                                RETAK["kolom"] * iz_, 1)
                    if i == 1:
                        kolom_lt1.append(ele)
                    daftar_kolom.append({"ele": ele, "lv": t["lv"], "i": i, "x": x, "y": y, "b": uk})
                    ele += 1
                    if t["wil"].buffer(0.01).contains(p):
                        budak.append(n)
        # balok
        if t["lv"] != "LT5" or konfig == "K2":
            for ix, x in enumerate(gx):
                for iy, y in enumerate(gy):
                    for dx, dy in ((1, 0), (0, 1)):
                        n1, n2 = nid(i, ix, iy), nid(i, ix + dx, iy + dy)
                        if n1 in ada and n2 in ada and ix + dx < len(gx) and iy + dy < len(gy):
                            xm, ym = x + 4.0 * dx, y + 4.0 * dy
                            if t["wil"].buffer(0.01).contains(Point(xm, ym)):
                                bb, hb = UKURAN_BALOK.get((t["lv"], x, y, x + 8.0 * dx, y + 8.0 * dy),
                                                          (tb.BALOK_B, tb.BALOK_H))
                                ab, izb, iyb, jb = persegi(bb, hb)  # izb: terhadap sumbu horizontal (lentur vertikal)
                                ops.element("elasticBeamColumn", ele, n1, n2, ab, EC_30, gb, jb,
                                            RETAK["balok"] * izb, RETAK["balok"] * iyb, 2)
                                daftar_balok.append({"ele": ele, "lv": t["lv"], "i": i, "x1": x, "y1": y,
                                                     "x2": x + 8.0 * dx, "y2": y + 8.0 * dy,
                                                     "arah": "X" if dx else "Y", "wil": t["wil"],
                                                     "b": bb, "h": hb})
                                ele += 1
        # inti
        for k, (nama, puncak, cx, cy) in inti.items():
            top = tb.LEVEL[puncak] if konfig == "K2" else min(tb.LEVEL[puncak], tb.LEVEL["LT5"])
            if tb.LEVEL[t["lv"]] <= top + 1e-6:
                bawah = 50000 + 100 * (i - 1) + k
                n = 50000 + 100 * i + k
                ops.node(n, cx, cy, z)
                if nama.startswith("Ujung"):
                    lw, tw = PANJANG_UJUNG, tb.DINDING_T
                    a_, ix_, iy_, j_ = tw * lw, tw * lw ** 3 / 12, lw * tw ** 3 / 12, lw * tw ** 3 / 3
                    avx, avy = 5 / 6 * a_ * 0.1, 5 / 6 * a_
                    f = 1.0
                else:
                    dxi, dyi = UKURAN_INTI[nama.split()[0]]
                    a_, ix_, iy_, j_, avx, avy = kotak(dxi, dyi, tb.DINDING_T)
                    f = tb.FAKTOR_BUKAAN_DINDING
                # transf 1: z lokal = X, y lokal = -Y: Iz lokal = I terhadap X (ix_), Iy lokal = iy_
                ops.element("ElasticTimoshenkoBeam", ele, bawah, n, EC_35, gc, a_, fd * j_, fd * f * iy_,
                            fd * f * ix_, f * avy, f * avx, 1)
                if i == 1:
                    inti_lt1.append(ele)
                daftar_inti.append({"ele": ele, "lv": t["lv"], "i": i, "nama": nama, "k": k, "node": n})
                ele += 1
                budak.append(n)
        # diafragma kaku dan massa
        mn = 99000 + i
        ops.node(mn, t["xc"], t["yc"], z)
        ops.fix(mn, 0, 0, 1, 1, 1, 0)
        ops.mass(mn, t["m"], t["m"], 0.0, 0.0, 0.0, t["J"])
        ops.rigidDiaphragm(3, mn, *budak)
        master[i] = mn
    return {"tk": tk, "master": master, "kolom_lt1": kolom_lt1, "inti_lt1": inti_lt1, "n_ele": ele - 1,
            "balok": daftar_balok, "kolom": daftar_kolom, "inti": daftar_inti}


def _analisis_statik():
    import openseespy.opensees as ops
    ops.constraints("Transformation")
    ops.numberer("RCM")
    ops.system("UmfPack")
    ops.test("NormDispIncr", 1e-8, 10)
    ops.algorithm("Linear")
    ops.integrator("LoadControl", 1.0)
    ops.analysis("Static")
    return ops.analyze(1)


# ------------------------------------------------------------------ spektrum
@functools.lru_cache(maxsize=None)
def tabel_spektrum(jenis="situs"):
    if jenis == "SE":
        import tahap4_respons_situs as rs
        t = np.logspace(-2, 1, 300)
        return t, rs.sa_se(t)
    t, sa = [], []
    with open(KELUAR / "4.1 Spektrum Desain Spesifik Situs.csv", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        next(r)
        for row in r:
            t.append(float(row[0]))
            sa.append(float(row[6]))
    o = np.argsort(t)
    return np.array(t)[o], np.array(sa)[o]


def sa(tn, jenis="situs"):
    t, s = tabel_spektrum(jenis)
    return float(np.interp(tn, t, s))


# ------------------------------------------------------------------ ragam
def ragam(konfig="K2", n=None, **kw):
    import openseespy.opensees as ops
    m = bangun(konfig, **kw)
    tk = m["tk"]
    n = n or 3 * len(tk)
    lam = ops.eigen("-fullGenLapack", n)
    per = [2 * math.pi / math.sqrt(l) for l in lam]
    phi = []
    for j in range(1, n + 1):
        v = np.array([[ops.nodeEigenvector(m["master"][i], j, d) for d in (1, 2, 6)] for i in m["master"]])
        mm = np.array([[t["m"], t["m"], t["J"]] for t in tk])
        nrm = math.sqrt(np.sum(mm * v ** 2))
        phi.append(v / nrm)
    mm = np.array([[t["m"], t["m"], t["J"]] for t in tk])
    gam_x = [float(np.sum(mm[:, 0] * p[:, 0])) for p in phi]
    gam_y = [float(np.sum(mm[:, 1] * p[:, 1])) for p in phi]
    mtot = sum(t["m"] for t in tk)
    jtot = sum(t["J"] for t in tk)
    mrz = [float(np.sum(mm[:, 2] * p[:, 2])) ** 2 / jtot for p in phi]
    hasil = {"T": per, "phi": phi, "gx": gam_x, "gy": gam_y, "mx": [g ** 2 / mtot for g in gam_x],
             "my": [g ** 2 / mtot for g in gam_y], "mrz": mrz, "tk": tk, "model": m}
    try:
        mp = ops.modalProperties("-return")
        hasil["mx_ops"] = list(mp["partiMassRatiosMX"])
        hasil["my_ops"] = list(mp["partiMassRatiosMY"])
    except Exception:
        pass
    return hasil


def cqc(r, w):
    """Kombinasi CQC respons ragam r (n_ragam × ...) dengan frekuensi sudut w, redaman ZETA."""
    r = np.asarray(r, dtype=float)
    n = len(w)
    out = np.zeros(r.shape[1:])
    for i in range(n):
        for k in range(n):
            b = w[k] / w[i]
            rho = 8 * ZETA ** 2 * (1 + b) * b ** 1.5 / ((1 - b ** 2) ** 2 + 4 * ZETA ** 2 * b * (1 + b) ** 2)
            out = out + rho * r[i] * r[k]
    return np.sqrt(np.abs(out))


def titik_tepi(t):
    """Empat titik sudut kotak batas wilayah lantai (untuk simpangan tepi)."""
    x0, y0, x1, y1 = t["bounds"]
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def perpindahan_titik(u, t, x, y):
    """(ux, uy) titik (x, y) dari perpindahan master (ux, uy, rz) diafragma kaku."""
    return u[0] - u[2] * (y - t["yc"]), u[1] + u[2] * (x - t["xc"])


def rsa(konfig="K2", jenis="situs", **kw):
    """Ragam spektrum CQC per arah: geser tingkat, perpindahan pusat massa dan tepi (elastis, spektrum/(R/Ie))."""
    rg = ragam(konfig, **kw)
    tk = rg["tk"]
    w = [2 * math.pi / t for t in rg["T"]]
    hasil = {}
    for arah, gam in (("X", rg["gx"]), ("Y", rg["gy"])):
        fs, us = [], []
        for j, (tn, p, g) in enumerate(zip(rg["T"], rg["phi"], gam)):
            a_ = sa(tn, jenis) * G / (tb.R / tb.IE)
            d_ = a_ / w[j] ** 2
            f = np.array([[t["m"] * p[i, 0], t["m"] * p[i, 1], t["J"] * p[i, 2]] for i, t in enumerate(tk)]) * g * a_
            fs.append(f)
            us.append(p * g * d_)
        geser = [np.cumsum(f[::-1, :2], axis=0)[::-1] for f in fs]   # geser tingkat per ragam
        # perpindahan pusat massa tingkat atas diproyeksikan ke tingkat bawah (Pasal 7.8.6)
        sim_cm, sim_tepi = [], []
        for u in us:
            row_cm, row_tp = [], []
            for i, t in enumerate(tk):
                ua = perpindahan_titik(u[i], t, t["xc"], t["yc"])
                ub = perpindahan_titik(u[i - 1], tk[i - 1], t["xc"], t["yc"]) if i > 0 else (0.0, 0.0)
                row_cm.append([ua[0] - ub[0], ua[1] - ub[1]])
                tp = []
                for (x, y) in titik_tepi(t):
                    pa = perpindahan_titik(u[i], t, x, y)
                    pb = perpindahan_titik(u[i - 1], tk[i - 1], x, y) if i > 0 else (0.0, 0.0)
                    tp.append([pa[0] - pb[0], pa[1] - pb[1]])
                row_tp.append(tp)
            sim_cm.append(row_cm)
            sim_tepi.append(row_tp)
        hasil[arah] = {"geser": cqc(geser, w), "sim_cm": cqc(sim_cm, w), "sim_tepi": cqc(sim_tepi, w),
                       "u": cqc(us, w)}
    hasil["ragam"] = rg
    return hasil


# ------------------------------------------------------------------ gaya lateral ekivalen
def elf_statik(konfig="K2", arah="X", eksentrisitas=0.0, faktor=1.0, **kw):
    """ELF dengan gaya di pusat massa ± torsi tak terduga (eksentrisitas × dimensi tegak lurus)."""
    import openseespy.opensees as ops
    e = tb.elf(konfig)
    m = bangun(konfig, **kw)
    tk = m["tk"]
    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    for i, (t, fx) in enumerate(zip(tk, e["Fx"]), start=1):
        x0, y0, x1, y1 = t["bounds"]
        f = fx * faktor
        if arah == "X":
            ops.load(m["master"][i], f, 0, 0, 0, 0, eksentrisitas * (y1 - y0) * f)
        else:
            ops.load(m["master"][i], 0, f, 0, 0, 0, eksentrisitas * (x1 - x0) * f)
    _analisis_statik()
    ops.reactions()
    d = 0 if arah == "X" else 1
    u = [np.array([ops.nodeDisp(m["master"][i], k) for k in (1, 2, 6)]) for i in range(1, len(tk) + 1)]
    v_kolom = -sum(ops.nodeReaction(n, d + 1) for n in _dasar_kolom(m))
    v_inti = -sum(ops.nodeReaction(50000 + k, d + 1) for k in range(len(tb.INTI)) if _ada_node(50000 + k))
    return {"u": u, "tk": tk, "V": sum(e["Fx"]) * faktor, "v_kolom": v_kolom, "v_inti": v_inti}


def _ada_node(n):
    import openseespy.opensees as ops
    return n in ops.getNodeTags()


def _dasar_kolom(m):
    import openseespy.opensees as ops
    return [n for n in ops.getNodeTags() if n < 1000]


def rasio_torsi(konfig="K2"):
    """δmax/δavg simpangan antar tingkat di tepi, ELF dengan torsi tak terduga 5 % (Ax = 1), Tabel 13 tipe 1a/1b."""
    out = {}
    for arah in ("X", "Y"):
        hasil = []
        for e in (0.05, -0.05):
            r = elf_statik(konfig, arah, e)
            d = 0 if arah == "X" else 1
            rows = []
            for i, t in enumerate(r["tk"]):
                tp = []
                for (x, y) in titik_tepi(t):
                    pa = perpindahan_titik(r["u"][i], t, x, y)
                    pb = perpindahan_titik(r["u"][i - 1], r["tk"][i - 1], x, y) if i > 0 else (0.0, 0.0)
                    tp.append(abs(pa[d] - pb[d]))
                # dua ujung tegak lurus arah gaya
                if arah == "X":
                    ujung = (max(tp[0], tp[1]), max(tp[2], tp[3]))
                else:
                    ujung = (max(tp[0], tp[3]), max(tp[1], tp[2]))
                rows.append(max(ujung) / (sum(ujung) / 2))
            hasil.append(rows)
        out[arah] = list(np.max(np.array(hasil), axis=0))
    return out


def faktor_ax(konfig="K2", arah="X"):
    """δmax/δavg perpindahan total di tepi (bukan simpangan antar tingkat) untuk Ax (Pers. 43)."""
    hasil = []
    d = 0 if arah == "X" else 1
    for e in (0.05, -0.05):
        r = elf_statik(konfig, arah, e)
        rows = []
        for i, t in enumerate(r["tk"]):
            tp = [abs(perpindahan_titik(r["u"][i], t, x, y)[d]) for (x, y) in titik_tepi(t)]
            uj = (max(tp[0], tp[1]), max(tp[2], tp[3])) if arah == "X" else (max(tp[0], tp[3]), max(tp[1], tp[2]))
            rows.append(max(uj) / (sum(uj) / 2))
        hasil.append(rows)
    return list(np.max(np.array(hasil), axis=0))


# ------------------------------------------------------------------ cek silang 4.4
def periode_rayleigh(konfig="K2", arah="X"):
    """T = 2π √(Σ w δ² / (g Σ F δ)) dari ELF statik tanpa torsi tak terduga (cara 2 untuk T-70)."""
    e = tb.elf(konfig)
    r = elf_statik(konfig, arah, 0.0)
    d = 0 if arah == "X" else 1
    dl = [u[d] for u in r["u"]]
    num = sum(t["w"] * x ** 2 for t, x in zip(r["tk"], dl))
    den = G * sum(f * x for f, x in zip(e["Fx"], dl))
    return 2 * math.pi * math.sqrt(num / den)


def kantilever_inti(geser=True, p=1000.0):
    """Lendutan puncak inti lif 8 × 8 m setinggi K2 (25,8 m) akibat P di puncak arah X: openseespy vs rumus."""
    import openseespy.opensees as ops
    h = tb.LEVEL["ATAP"] - DASAR
    a_, ix_, iy_, j_, avx, avy = kotak(8.0, 8.0, tb.DINDING_T)
    f = tb.FAKTOR_BUKAAN_DINDING
    gc = EC_35 / (2 * (1 + NU))
    e_i = EC_35 * RETAK["dinding"] * f * iy_
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)
    ops.node(1, 0, 0, 0)
    ops.node(2, 0, 0, h)
    ops.fix(1, 1, 1, 1, 1, 1, 1)
    ops.geomTransf("Linear", 1, 1.0, 0.0, 0.0)
    av = f * avx if geser else 1e6
    ops.element("ElasticTimoshenkoBeam", 1, 1, 2, EC_35, gc, a_, j_, RETAK["dinding"] * f * iy_,
                RETAK["dinding"] * f * ix_, f * avy if geser else 1e6, av, 1)
    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    ops.load(2, p, 0, 0, 0, 0, 0)
    _analisis_statik()
    d_ops = ops.nodeDisp(2, 1)
    d_rumus = p * h ** 3 / (3 * e_i) + (p * h / (gc * f * avx) if geser else 0.0)
    return {"ops": d_ops, "rumus": d_rumus, "EI": e_i, "h": h}


def kantilever_pynite(p=1000.0):
    """Inti lif tanpa deformasi geser di PyNite (Euler-Bernoulli), untuk dibandingkan dengan openseespy."""
    from Pynite import FEModel3D
    h = tb.LEVEL["ATAP"] - DASAR
    a_, ix_, iy_, j_, avx, avy = kotak(8.0, 8.0, tb.DINDING_T)
    f = tb.FAKTOR_BUKAAN_DINDING
    m = FEModel3D()
    m.add_material("beton", EC_35, EC_35 / (2 * (1 + NU)), NU, 23.6)
    m.add_section("inti", a_, RETAK["dinding"] * f * iy_, RETAK["dinding"] * f * ix_, j_)
    m.add_node("A", 0, 0, 0)
    m.add_node("B", 0, h, 0)
    m.def_support("A", True, True, True, True, True, True)
    m.add_member("I", "A", "B", "beton", "inti")
    m.add_node_load("B", "FX", p)
    m.analyze_linear()
    return m.nodes["B"].DX["Combo 1"]


# ------------------------------------------------------------------ ringkasan pemeriksaan
TINGGI = {"LT2": 4.5, "LT3": 4.5, "LT4": 4.2, "LT5": 4.2, "LT6": 4.2, "ATAP": 4.2}
LO_RATA = 2.4   # kPa rata-rata beban hidup untuk Px (Pasal 7.8.7) [Asumsi: campuran zona 4.2]


def periksa(konfig="K2"):
    e = tb.elf(konfig)
    r = rsa(konfig)
    rg = r["ragam"]
    tk = rg["tk"]
    hasil = {"konfig": konfig, "elf": e, "ragam": rg}
    # periode fundamental per arah (ragam dengan partisipasi terbesar)
    t1x = rg["T"][int(np.argmax(rg["mx"]))]
    t1y = rg["T"][int(np.argmax(rg["my"]))]
    hasil["T1"] = {"X": t1x, "Y": t1y}
    # geser dasar ELF per arah dengan T = min(T model, Cu Ta) (Pasal 7.9.1.4.1)
    skala = {}
    for arah, t1 in (("X", t1x), ("Y", t1y)):
        tt = min(t1, e["CuTa"])
        cs = max(min(tb.SDS / (tb.R / tb.IE), tb.SD1 / (tt * tb.R / tb.IE)), e["Cs_min"])
        v = cs * e["W"]
        vt = float(r[arah]["geser"][0, 0 if arah == "X" else 1])
        skala[arah] = {"T": tt, "Cs": cs, "V": v, "Vt": vt, "faktor": max(1.0, v / vt)}
    hasil["skala"] = skala
    # simpangan antar tingkat desain di pusat massa: Cd/Ie × elastis (tidak diskalakan, Pasal 7.9.1.4.1 kedua)
    sim = {}
    for arah, d in (("X", 0), ("Y", 1)):
        rows = []
        for i, t in enumerate(tk):
            hsx = TINGGI[t["lv"]]
            de = float(r[arah]["sim_cm"][i, d])
            dt = float(np.max(r[arah]["sim_tepi"][i, :, d]))
            delta = tb.CD * de / tb.IE
            delta_tepi = tb.CD * dt / tb.IE
            izin = 0.010 * hsx
            vx = float(r[arah]["geser"][i, d]) * skala[arah]["faktor"]
            px = sum(tt_["w"] + LO_RATA * tt_["wil"].area for tt_ in tk[i:])
            theta = px * delta * tb.IE / (vx * hsx * tb.CD)
            rows.append({"lv": t["lv"], "hsx": hsx, "delta": delta, "delta_tepi": delta_tepi, "izin": izin,
                         "rasio": delta / izin, "rasio_tepi": delta_tepi / izin, "Vx": vx, "Px": px,
                         "theta": theta, "k": vx / max(de, 1e-12)})
        sim[arah] = rows
    hasil["simpangan"] = sim
    hasil["theta_maks"] = min(0.5 / (1.0 * tb.CD), 0.25)
    # ketidakberaturan
    hasil["torsi"] = rasio_torsi(konfig)
    lunak = {}
    for arah in ("X", "Y"):
        ks = [row["k"] for row in sim[arah]]
        rr = []
        for i, k in enumerate(ks):
            atas = ks[i + 1:i + 2]
            tiga = ks[i + 1:i + 4]
            r1 = k / atas[0] if atas else None
            r3 = k / np.mean(tiga) if len(tiga) == 3 else None
            rr.append((r1, r3))
        lunak[arah] = rr
    hasil["lunak"] = lunak
    ws = [t["w"] for t in tk]
    hasil["massa"] = [ws[i] / min([ws[j] for j in (i - 1, i + 1) if 0 <= j < len(ws)]) for i in range(len(ws))]
    # pengecualian Pasal 7.3.2.2 butir 1: tipe 1a, 1b, 2 tidak berlaku bila tidak ada rasio simpangan > 130 % tingkat
    # di atasnya (dua tingkat teratas tidak dievaluasi)
    peng = {}
    for arah in ("X", "Y"):
        rr = [row["delta"] / row["hsx"] for row in sim[arah]]
        peng[arah] = max(rr[i] / rr[i + 1] for i in range(len(rr) - 2)) if len(rr) > 2 else 0.0
    hasil["pengecualian_7322"] = peng
    hasil["Ax"] = {a: [min(3.0, max(1.0, (v / 1.2) ** 2)) for v in faktor_ax(konfig, a)] for a in ("X", "Y")}
    # porsi rangka (sistem ganda): ELF statik tanpa torsi tak terduga
    porsi = {}
    for arah in ("X", "Y"):
        s = elf_statik(konfig, arah, 0.0)
        porsi[arah] = s["v_kolom"] / (s["v_kolom"] + s["v_inti"])
    hasil["porsi_rangka"] = porsi
    # simpangan dengan spektrum SE (saran AI pada 4.1)
    rse = rsa(konfig, "SE")
    hasil["simpangan_SE"] = {a: [tb.CD * float(rse[a]["sim_cm"][i, d]) / tb.IE / (0.010 * TINGGI[t["lv"]])
                                 for i, t in enumerate(tk)] for a, d in (("X", 0), ("Y", 1))}
    return hasil


def ringkas_teks(h):
    rg = h["ragam"]
    s = [f"== {h['konfig']}: W {h['elf']['W']:.0f} kN; Ta {h['elf']['Ta']:.3f}; CuTa {h['elf']['CuTa']:.3f}"]
    for j in range(min(6, len(rg["T"]))):
        s.append(f"  ragam {j + 1}: T {rg['T'][j]:.3f} s; Mx {rg['mx'][j]:.3f} My {rg['my'][j]:.3f} Rz {rg['mrz'][j]:.3f}")
    s.append(f"  kumulatif Mx {sum(rg['mx']):.3f} My {sum(rg['my']):.3f}")
    for a, v in h["skala"].items():
        s.append(f"  {a}: T {v['T']:.3f} Cs {v['Cs']:.4f} V {v['V']:.0f} Vt {v['Vt']:.0f} faktor {v['faktor']:.3f}")
    for a in ("X", "Y"):
        for row, tr, (r1, r3), se in zip(h["simpangan"][a], h["torsi"][a], h["lunak"][a], h["simpangan_SE"][a]):
            s.append(f"  {a} {row['lv']}: Δ {row['delta'] * 1000:.1f} mm ({row['rasio']:.2f} izin; tepi "
                     f"{row['rasio_tepi']:.2f}; SE {se:.2f}) θ {row['theta']:.3f} torsi {tr:.2f} lunak "
                     f"{'' if r1 is None else f'{r1:.2f}'}/{'' if r3 is None else f'{r3:.2f}'}")
    s.append(f"  massa rasio {[round(x, 2) for x in h['massa']]}; porsi rangka {h['porsi_rangka']}")
    s.append(f"  pengecualian 7.3.2.2 rasio maks {h['pengecualian_7322']}; Ax {h['Ax']}")
    return "\n".join(s)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for k in ("K2", "K1"):
        print(ringkas_teks(periksa(k)))


# ------------------------------------------------------------------ tambahan pemeriksaan
def simpangan_tepi_torsi(konfig="K2", arah="X"):
    """Rasio simpangan tepi terhadap izin dari ELF dengan torsi tak terduga 0,05 Ax (Pasal 7.8.4.2-7.8.4.3, 7.8.6)."""
    ax = min(3.0, max(1.0, (max(faktor_ax(konfig, arah)) / 1.2) ** 2))
    d = 0 if arah == "X" else 1
    terburuk = [0.0] * len(data_tingkat(konfig))
    for e in (0.05 * ax, -0.05 * ax):
        r = elf_statik(konfig, arah, e)
        for i, t in enumerate(r["tk"]):
            for (x, y) in titik_tepi(t):
                pa = perpindahan_titik(r["u"][i], t, x, y)
                pb = perpindahan_titik(r["u"][i - 1], r["tk"][i - 1], x, y) if i > 0 else (0.0, 0.0)
                terburuk[i] = max(terburuk[i], tb.CD * abs(pa[d] - pb[d]) / tb.IE / (0.010 * TINGGI[t["lv"]]))
    return ax, terburuk


def rangka_saja(konfig="K2", arah="X"):
    """Rangka tanpa dinding inti dibebani 25 % gaya ELF (Pasal 7.2.5.1): rasio simpangan terhadap izin (informasi)."""
    r = elf_statik(konfig, arah, 0.0, faktor=0.25, tanpa_inti=True)
    d = 0 if arah == "X" else 1
    out = []
    for i, t in enumerate(r["tk"]):
        b = r["u"][i - 1][d] if i > 0 else 0.0
        out.append(tb.CD * abs(r["u"][i][d] - b) / tb.IE / (0.010 * TINGGI[t["lv"]]))
    return out


IRREG = [  # (tipe, uraian, cara)
    ("H-1a/1b", "Torsi: δmax/δavg simpangan tepi > 1,2 / 1,4 (Ax = 1)", "torsi"),
    ("H-2", "Sudut dalam: kedua proyeksi > 15 % dimensi denah", "sudut"),
    ("H-3", "Diskontinuitas diafragma: bukaan > 50 % atau perubahan kekakuan > 50 %", "diafragma"),
    ("H-4", "Pergeseran tegak lurus bidang elemen vertikal", "tidak"),
    ("H-5", "Sistem nonparalel", "tidak"),
    ("V-1a/1b", "Tingkat lunak: k < 70 % atas atau 80 % rata-rata tiga di atas", "lunak"),
    ("V-2", "Berat: massa > 150 % tingkat di dekatnya", "massa"),
    ("V-3", "Geometri vertikal: dimensi sistem pemikul > 130 % tingkat di dekatnya", "geometri"),
    ("V-4", "Diskontinuitas bidang elemen vertikal", "tidak"),
    ("V-5a/5b", "Tingkat lemah (kekuatan < 80 % / 65 % atas)", "kekuatan"),
]


def ketidakberaturan(h):
    tor = max(max(h["torsi"]["X"]), max(h["torsi"]["Y"]))
    peng = max(h["pengecualian_7322"].values())
    lun = min(min(r for r, _ in h["lunak"][a] if r is not None) for a in ("X", "Y"))
    massa = max(h["massa"][:-1]) if len(h["massa"]) > 1 else 0.0
    baris = []
    for tipe, ur, cara in IRREG:
        if cara == "torsi":
            nilai = f"{tor:.2f}".replace(".", ",")
            ada = "Ya: 1b (> 1,4)" if tor > 1.4 else ("Ya: 1a" if tor > 1.2 else "Tidak")
            ak = ("ρ = 1,3 (7.3.4.2); Ax (7.8.4.3); torsi tak terduga masuk E dan simpangan; simpangan di tepi "
                  "(7.8.6); +25 % kolektor dan sambungan diafragma (7.3.3.4); ragam spektrum wajib (Tabel 16)")
        elif cara == "sudut":
            nilai = "LT3/LT4: 48/72 = 67 %; 24/48 = 50 %"
            ada = "Ya"
            ak = "+25 % kolektor dan sambungan diafragma (7.3.3.4); desain diafragma di sudut dalam"
        elif cara == "diafragma":
            nilai = "void LT2 624/3.456 = 18 %; luas lantai berubah ≤ 33 %"
            ada = "Tidak"
            ak = "-"
        elif cara == "lunak":
            nilai = f"k/k atas terkecil {lun:.2f}; pengecualian 7.3.2.2: rasio simpangan maks {peng:.2f} < 1,3".replace(".", ",")
            ada = "Tidak (dikecualikan)"
            ak = "-"
        elif cara == "massa":
            nilai = f"maks {massa:.2f} (LT3/LT4); pengecualian 7.3.2.2 berlaku".replace(".", ",")
            ada = "Tidak (dikecualikan)"
            ak = "-"
        elif cara == "geometri":
            nilai = "podium 48 m / menara 24 m arah Y = 200 %"
            ada = "Ya"
            ak = "ragam spektrum wajib (Tabel 16 hal. 68); ELF tidak diizinkan sebagai analisis akhir"
        elif cara == "kekuatan":
            nilai = "dicek pada desain kolom/dinding (4.7-4.8)"
            ada = "Belum"
            ak = "5b terlarang di KDS D (7.3.3.1)"
        else:
            nilai, ada, ak = "tidak ada pada denah", "Tidak", "-"
        baris.append([tipe, ur, nilai, ada, ak])
    return baris


def buat_excel(keluar=KELUAR / "4.3 Analisis Struktur.xlsx"):
    import openpyxl
    from format_dokumen import AI, Lembar, set_font_bawaan

    hasil = {k: periksa(k) for k in ("K2", "K1")}
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    lab = f"DIISI AI ATAS PERMINTAAN DEFSA (20 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk analisis struktur 3D (4.3-4.4)", [6, 120])
    lb.catatan(LABEL + " " + lab)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, x] for i, x in enumerate([
        "Model openseespy 3D (skrip/tahap4_model.py): kolom dan balok elasticBeamColumn, inti dinding sebagai kolom "
        "kotak ElasticTimoshenkoBeam di pusat inti, diafragma kaku per lantai, jepit di LT1 +12,85 (SNI 1726 Pasal "
        "7.7.1; interaksi tanah-struktur di Tahap 6).",
        "Kekakuan retak SNI 2847:2019 Tabel 6.6.3.1.1: kolom 0,70 Ig, balok 0,35 Ig, dinding retak 0,35 Ig; bukaan "
        "pintu inti 0,85 [Asumsi]. Ec = 4.700 √fc' (Pasal 19.2.2.1): fc' 35 kolom dan dinding, 30 balok.",
        "Massa dan pusat massa per tingkat dari berat seismik 4.2 (alat atap podium di x 67, y 68); inersia putar "
        "dari sebaran luas lantai.",
        "Analisis: ragam (eigen), ragam spektrum CQC dengan spektrum 4.1 opsi (a) dibagi R/Ie (Pasal 7.9.1), skala "
        "gaya ke 100 % V ELF (Pasal 7.9.1.4.1), simpangan Cd/Ie tanpa skala; ELF statik untuk torsi tak terduga, Ax, "
        "dan porsi rangka.",
        "K2: akhir 6 lantai + helipad; K1: tahap 1 (atap baja ringan di atas LT4, keputusan M-4).",
        "Lembar Geser Dasar dan Simpangan memakai rumus Excel (Cs, V, faktor skala, Δ izin, rasio, θ) yang dicocokkan "
        "dengan Python.",
        "Status: " + STATUS + ".",
    ])], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Model"), 2, "Data model: tingkat, massa, pusat massa", [10, 12, 12, 14, 14, 12, 12, 16])
    lb.catatan(LABEL + " Inti: tangga 4 × 6 m (6 buah; 3 utara berhenti di LT3/LT4), lif 8 × 8 m; tebal 350 mm.")
    for kf, h in hasil.items():
        tk = h["ragam"]["tk"]
        lb.tabel([f"{kf} tingkat", "z (m)", "Luas (m²)", "W (kN)", "Massa (kN·s²/m)", "x pm (m)", "y pm (m)",
                  "J (kN·s²·m)"], [[t["lv"], round(t["z"], 2), round(t["wil"].area), round(t["w"]), round(t["m"], 1),
                                    round(t["xc"], 2), round(t["yc"], 2), round(t["J"])] for t in tk],
                 rata=list("cccccccc"), fmt=[None, "0.00", "#,##0", "#,##0", "#,##0.0", "0.00", "0.00", "#,##0"],
                 fill=AI, beku=False)
        lb.kosong()
    lb.ws.freeze_panes = "A5"

    lb = Lembar(wb.create_sheet("Ragam"), 3, "Periode dan partisipasi massa ragam", [10, 10, 12, 12, 12, 14, 14])
    lb.catatan(LABEL + " Partisipasi kumulatif 100 % (Pasal 7.9.1.1). Mx, My, Rz: rasio massa efektif ragam.")
    for kf, h in hasil.items():
        rg = h["ragam"]
        cx = np.cumsum(rg["mx"])
        cy = np.cumsum(rg["my"])
        lb.tabel([f"{kf} ragam", "T (s)", "Mx", "My", "Rz", "Σ Mx", "Σ My"],
                 [[j + 1, round(rg["T"][j], 4), round(rg["mx"][j], 4), round(rg["my"][j], 4), round(rg["mrz"][j], 4),
                   round(float(cx[j]), 4), round(float(cy[j]), 4)] for j in range(len(rg["T"]))],
                 rata=list("ccccccc"), fmt=[None, "0.000", "0.000", "0.000", "0.000", "0.000", "0.000"], fill=AI,
                 beku=False)
        lb.kosong()
    lb.ws.freeze_panes = "A5"

    lb = Lembar(wb.create_sheet("Geser Dasar"), 4, "Geser dasar ELF per arah dan skala ragam spektrum",
                [10, 8, 12, 12, 12, 12, 14, 14, 14, 12])
    lb.catatan(LABEL + f" T = min(T ragam, Cu Ta); Cs = max(min(SDS/(R/Ie), SD1/(T R/Ie)), 0,044 SDS Ie); V = Cs W; "
               f"faktor = MAX(1; V/Vt) (Pasal 7.9.1.4.1). SDS {tb.SDS}, SD1 {tb.SD1}, R {tb.R}, Ie {tb.IE}.")
    baris = []
    for kf, h in hasil.items():
        for a in ("X", "Y"):
            baris.append([kf, a, round(h["T1"][a], 4), round(h["elf"]["CuTa"], 4), None, round(h["elf"]["W"], 1), None,
                          None, round(h["skala"][a]["Vt"], 1), None])
    _, a0, b0 = lb.tabel(["Konfigurasi", "Arah", "T ragam (s)", "Cu Ta (s)", "T dipakai (s)", "W (kN)", "Cs", "V ELF (kN)",
                          "Vt ragam (kN)", "Faktor skala"], baris, rata=list("cccccccccc"),
                         fmt=[None, None, "0.000", "0.000", "0.000", "#,##0", "0.0000", "#,##0", "#,##0", "0.000"],
                         fill_kolom={4: AI, 6: AI, 7: AI, 9: AI})
    k = lb.kol
    for r in range(a0, b0 + 1):
        lb.ws[f"{k(4)}{r}"] = f"=MIN({k(2)}{r},{k(3)}{r})"
        lb.ws[f"{k(6)}{r}"] = (f"=MAX(MIN({tb.SDS}/({tb.R}/{tb.IE}),{tb.SD1}/({k(4)}{r}*{tb.R}/{tb.IE})),"
                               f"MAX(0.044*{tb.SDS}*{tb.IE},0.01))")
        lb.ws[f"{k(7)}{r}"] = f"={k(6)}{r}*{k(5)}{r}"
        lb.ws[f"{k(9)}{r}"] = f"=MAX(1,{k(7)}{r}/{k(8)}{r})"

    for kf, h in hasil.items():
        lb = Lembar(wb.create_sheet(f"Simpangan {kf}"), 5 if kf == "K2" else 6,
                    f"Simpangan antar tingkat, stabilitas, torsi {kf}",
                    [8, 9, 8, 12, 11, 10, 11, 10, 11, 12, 12, 10, 11, 11])
        ax_x, tepi_x = simpangan_tepi_torsi(kf, "X")
        ax_y, tepi_y = simpangan_tepi_torsi(kf, "Y")
        rx, ry = rangka_saja(kf, "X"), rangka_saja(kf, "Y")
        lb.catatan(LABEL + " Δ = Cd δe / Ie di pusat massa dari ragam spektrum (Pasal 7.8.6, 7.9.1.2); Δa = 0,010 hsx "
                   "(Tabel 20 hal. 88, kategori IV); θ = Px Δ Ie / (Vx hsx Cd) (Pers. 45), θmax = 0,5/(β Cd) = 0,091. "
                   f"Tepi + torsi: ELF dengan torsi tak terduga 0,05 Ax (Ax X {ax_x:.2f}, Y {ax_y:.2f}). Rangka saja: "
                   "25 % gaya ELF tanpa inti (Pasal 7.2.5.1, informasi).")
        baris = []
        for a, tepi, rs_ in (("X", tepi_x, rx), ("Y", tepi_y, ry)):
            for row, tp, rr, se, tr in zip(h["simpangan"][a], tepi, rs_, h["simpangan_SE"][a], h["torsi"][a]):
                baris.append([a, row["lv"], row["hsx"], round(row["delta"] * 1000, 2), None, None,
                              round(tp, 3), round(se, 3), round(tr, 3), round(row["Px"]), round(row["Vx"]), None,
                              round(rr, 3), None])
        _, a1, b1 = lb.tabel(["Arah", "Tingkat", "hsx (m)", "Δ pm (mm)", "Δa (mm)", "Δ/Δa", "Tepi + torsi Δ/Δa",
                              "SE Δ/Δa", "δmax/δavg", "Px (kN)", "Vx (kN)", "θ", "Rangka saja 25 % Δ/Δa", "Status"],
                             baris, rata=list("cccccccccccccc"),
                             fmt=[None, None, "0.0", "0.00", "0.0", "0.000", "0.000", "0.000", "0.00", "#,##0", "#,##0",
                                  "0.0000", "0.000", None], fill_kolom={4: AI, 5: AI, 11: AI, 13: AI})
        for r in range(a1, b1 + 1):
            lb.ws[f"{k(4)}{r}"] = f"=0.010*{k(2)}{r}*1000"
            lb.ws[f"{k(5)}{r}"] = f"={k(3)}{r}/{k(4)}{r}"
            lb.ws[f"{k(11)}{r}"] = f"={k(9)}{r}*{k(3)}{r}/1000*{tb.IE}/({k(10)}{r}*{k(2)}{r}*{tb.CD})"
            lb.ws[f"{k(13)}{r}"] = (f"=IF(AND({k(5)}{r}<=1,{k(6)}{r}<=1,{k(11)}{r}<=0.1),\"Memenuhi\","
                                    f"\"Periksa\")")

    lb = Lembar(wb.create_sheet("Ketidakberaturan"), 7, "Ketidakberaturan struktur (Tabel 13 dan 14) K2",
                [10, 50, 46, 18, 70])
    lb.catatan(LABEL + " K1 sama kecuali torsi arah Y 1,51 (1b) dan tanpa menara di atas LT4.")
    lb.tabel(["Tipe", "Uraian", "Nilai", "Ada?", "Akibat (SNI 1726)"], ketidakberaturan(hasil["K2"]),
             rata=list("lllll"), fill_kolom={2: AI, 3: AI, 4: AI})

    lb = Lembar(wb.create_sheet("Cek Silang"), 8, "Cek silang analisis (4.4)", [8, 44, 18, 18, 12, 10, 12])
    lb.catatan(LABEL + " Batas toleransi ditetapkan sebelum menghitung: struktur 5 % (periode 10 %).")
    ki, kb, kp = kantilever_inti(True), kantilever_inti(False), kantilever_pynite()
    baris = []
    for kf, h in hasil.items():
        for a in ("X", "Y"):
            ry = periode_rayleigh(kf, a)
            baris.append(["T-70", f"T ragam {kf} arah {a} (s): eigen vs Rayleigh dari ELF", round(h["T1"][a], 4),
                          round(ry, 4), None, 0.10, None])
    rg = hasil["K2"]["ragam"]
    baris.append(["T-71", "Partisipasi massa ragam 1 K2 arah X: hitungan sendiri vs modalProperties OpenSees",
                  round(rg["mx"][0], 5), round(rg.get("mx_ops", [0])[0] / 100, 5), None, 0.01, None])
    baris.append(["T-72", "Lendutan puncak inti lif (m), P 1.000 kN: openseespy Timoshenko vs rumus PL³/3EI + PL/GAv",
                  round(ki["ops"], 7), round(ki["rumus"], 7), None, 0.01, None])
    baris.append(["T-72", "Lendutan puncak inti lif tanpa geser (m): openseespy vs PyNite", round(kb["ops"], 7),
                  round(kp, 7), None, 0.01, None])
    _, a2, b2 = lb.tabel(["No", "Besaran", "Cara 1", "Cara 2", "Selisih", "Batas", "Status"], baris,
                         rata=list("clccccc"), fmt=[None, None, "0.0000000", "0.0000000", "0.0%", "0%", None],
                         fill_kolom={4: AI, 6: AI})
    for r in range(a2, b2 + 1):
        lb.ws[f"{k(4)}{r}"] = f"={k(3)}{r}/{k(2)}{r}-1"
        lb.ws[f"{k(6)}{r}"] = f"=IF(ABS({k(4)}{r})<={k(5)}{r},\"Lolos\",\"Tidak lolos\")"

    h2 = hasil["K2"]
    lb = Lembar(wb.create_sheet("Catatan"), 9, "Kesimpulan dan keputusan yang diminta", [8, 120])
    lb.catatan(LABEL + " " + lab)
    lb.tabel(["No", "Catatan"], [[i + 1, x] for i, x in enumerate([
        f"Periode K2: T1 {h2['T1']['X']:.3f} s (X), {h2['T1']['Y']:.3f} s (Y), di bawah Cu Ta {h2['elf']['CuTa']:.3f} s; "
        "partisipasi massa 100 %.",
        f"Geser dasar ragam spektrum 56 % ELF, sehingga gaya ragam dikalikan {h2['skala']['X']['faktor']:.2f} (X) dan "
        f"{h2['skala']['Y']['faktor']:.2f} (Y) agar sama dengan V ELF {h2['skala']['X']['V']:,.0f} kN.".replace(",", "."),
        "Simpangan antar tingkat paling besar 26 % (pusat massa), 29 % (tepi), dan 46 % (tepi, ELF + torsi tak terduga "
        "× Ax) dari 0,010 hsx; dengan spektrum SE sementara 32 %. θ <= 0,005, pengaruh P-delta diabaikan (Pasal 7.8.7).",
        "Ketidakberaturan K2: torsi berlebihan 1b arah Y (1,48 di LT4), sudut dalam (V1), geometri vertikal "
        "(podium-menara). Vertikal 1a/1b/2 dikecualikan Pasal 7.3.2.2. KDS D mengizinkan 1b (7.3.3.1 hanya melarang di "
        "E/F) dengan akibat pada lembar 7.",
        "Alternatif dinding geser ujung menara (2 × 8 m di as 2 dan 10) diuji: rasio torsi hanya turun 1,48 → 1,40, "
        "jadi tidak diusulkan. Keputusan Defsa 20 Nov 2026: tipe 1b diterima dengan akibatnya.",
        f"Porsi geser rangka hanya {h2['porsi_rangka']['X'] * 100:.0f} % (X) dan {h2['porsi_rangka']['Y'] * 100:.0f} % "
        "(Y). Pasal 7.2.5.1 mensyaratkan rangka mampu memikul 25 % gaya seismik desain: kolom dan balok didesain juga "
        "terhadap model rangka saja dengan 25 % gaya (4.6-4.7). Pada model itu simpangan 0,99-1,06 × izin (informasi).",
        "ρ = 1,3 tetap (tipe 1b, Pasal 7.3.4.2). Kombinasi 6/7 di 4.2 berlaku; torsi tak terduga × Ax masuk gaya desain.",
        "Gedung utilitas + parkir (struktur terpisah, x 100-134) dianalisis tersendiri bersama desain unsur (4.5-4.8).",
    ])], rata=list("cl"), fill_kolom={1: AI})

    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar, hasil
