"""Tahap 4 langkah 4.8: dinding struktural khusus (inti lif dan inti tangga), balok kopel (ambang pintu inti), tangga,
dan atap sementara tahap 1 (SNI 2847:2019 Pasal 18.10; SNI 1727:2020 untuk beban tangga dan angin atap).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (20 Nov 2026); disetujui
Defsa 20 Nov 2026 (pintu inti asumsi diterima, tanpa elemen batas khusus). Kunci jawaban tidak dibuka.

Gaya dalam: model 3D tahap4_model (inti = kolom kotak ElasticTimoshenkoBeam, retak 0,35 Ig, faktor bukaan 0,85) dengan
ukuran balok 4.6 dan kolom 4.7, K1 dan K2 diselubungi. Gempa pola ELF V = V ELF, torsi tak terduga 0,05 Ax, 100 % +
30 %, ρ 1,3, Ev 0,2 SDS D (sama dengan 4.7). Dinding inti tidak memikul gravitasi di model (diafragma hanya mengikat
horizontal), sehingga gaya aksial gravitasi inti dihitung tributari sendiri: berat dinding, lajur pelat 1,0 m di
sekeliling inti [Asumsi], dan tangga di dalam inti tangga. Inti lif dianggap tanpa beban lif (rel, kereta, mesin
dipikul balok mesin/pit, Tahap 5) [Asumsi; aksial lebih kecil konservatif untuk lentur dan tarik].

Acuan SNI 2847:2019 (halaman cetak = halaman PDF - 22): 18.10.2.1-18.10.2.3 hal. 402-403 (ρ >= 0,0025, s <= 450, dua
lapis bila Vu > 0,17 Acv √fc' atau hw/lw >= 2, 1,25 fy); 18.10.3 hal. 403 (Vu dari analisis; SNI 2847:2019 belum
memuat Ωv dan ωv ACI 318-19, dicantumkan sebagai informasi); 18.10.4.1-18.10.4.5 hal. 403-404 (Vn = Acv (αc √fc' +
ρt fy), αc 0,25-0,17, ρl >= ρt bila hw/lw <= 2, batas 0,66 dan 0,83 √fc'); 18.10.5.1-18.10.5.2 hal. 405 (lentur-aksial
22.4, sayap efektif min(setengah jarak badan; 0,25 hw)); 18.10.6.2 hal. 406-407 (c >= lw/(600 (1,5 δu/hw)), δu/hw >=
0,005, tinggi >= maks(lw; Mu/4Vu)); 18.10.6.3 hal. 407 (σ > 0,2 fc', berhenti < 0,15 fc'); 18.10.6.4 hal. 407-409 dan
Tabel 18.10.6.4(f) hal. 408; 18.10.6.5 hal. 411-412 (ρ > 2,8/fy: s <= min(200; 8 db), di zona sendi min(150; 6 db));
18.10.7.1-18.10.7.4 hal. 412-414 (balok kopel); 21.2.4.1 hal. 474 (φ geser 0,60 bila Vn < geser saat Mn tercapai);
21.2.4.3 hal. 474 (φ 0,85 balok kopel diagonal); Tabel 7.3.1.1 hal. 120 (tebal pelat satu arah); 17.3.3 hal. 319,
17.4.1.2 hal. 321, 17.4.2.2 hal. 323 (angkur). SNI 1727:2020: Tabel 4.3-1 tangga 4,79 kPa; Gambar 27.3-1 (hal. 129
dari 300) Cp atap -0,9 sampai -1,3; Tabel 26.13-1 GCpi ±0,18.
"""
from __future__ import annotations

import functools
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import cache_analisis  # noqa: E402
import tahap4_beban as tb  # noqa: E402
import tahap4_kolom as kl  # noqa: E402
import tahap4_model as tm  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "04 Struktur Atas"
BERKAS = KELUAR / "4.8 Desain Dinding Geser, Tangga, Atap.xlsx"
LABEL = tb.LABEL
STATUS = "disetujui Defsa 20 Nov 2026"
FC, FY, ES = 35.0, 420.0, 200000.0
BETA1 = 0.85 - 0.05 * (FC - 28) / 7      # 0,80
EPS_TY = 0.002
T = tb.DINDING_T                          # 0,35 m
SEL = 20.0                                # mm, dinding tidak terpapar (Tabel 20.6.1.3.1)
H_PINTU = 2.4                             # m [Asumsi]
DIM = {"L": (8.0, 8.0), "T": (4.0, 6.0)}  # jarak as dinding (m), tahap4_model.UKURAN_INTI
PINTU = {"L": [(-2.0, 1.4), (2.0, 1.4)], "T": [(0.0, 1.2)]}   # (x pusat, lebar) di dinding selatan [Asumsi]
KELOMPOK = {"W-L": "L", "W-TM": "T", "W-TP": "T"}
URUT_LV = kl.URUT_LV
LAJUR_PELAT = 1.0                         # m [Asumsi]
DB_BATAS = (16, 19, 22, 25, 29)
N_BATAS = (4, 6, 8, 10, 12, 16)
LEG_MIN = 0.60                            # m, panjang minimum zona batas untuk menampung batang [Asumsi praktis]
RHO_BATAS = 0.04                          # ρ zona batas maks (kemacetan tulangan) [Asumsi praktis, seperti kolom 4.7]


def luas(db):
    return math.pi * db ** 2 / 4


def floor25(s):
    return math.floor(s / 25 + 1e-9) * 25


def kelompok_inti(nama):
    return "W-L" if nama.startswith("Inti") else ("W-TM" if nama.endswith("y39") else "W-TP")


def hw_inti(nama):
    return tb.LEVEL[[x for x in tb.INTI if x[0] == nama][0][2]] - tm.DASAR


def hw_kelompok(g):
    return min(hw_inti(n) for n, _, _ in tb.INTI if kelompok_inti(n) == g)


# ------------------------------------------------------------------ geometri penampang
def potongan(tipe):
    """Potongan dinding persegi (x0, x1, y0, y1, nama) di koordinat lokal inti (m), dinding selatan dipotong pintu."""
    dx, dy = DIM[tipe]
    ex, ey = (dx + T) / 2, (dy + T) / 2
    out = []
    xs = [-ex]
    for xc, w in sorted(PINTU[tipe]):
        xs += [xc - w / 2, xc + w / 2]
    xs.append(ex)
    for a, b in zip(xs[::2], xs[1::2]):
        out.append((a, b, -dy / 2 - T / 2, -dy / 2 + T / 2, "S"))
    out.append((-ex, ex, dy / 2 - T / 2, dy / 2 + T / 2, "N"))
    out.append((-dx / 2 - T / 2, -dx / 2 + T / 2, -dy / 2 + T / 2, dy / 2 - T / 2, "W"))
    out.append((dx / 2 - T / 2, dx / 2 + T / 2, -dy / 2 + T / 2, dy / 2 - T / 2, "E"))
    return out


def panjang_efektif(a, b, d, be):
    """Panjang [a, b] yang berjarak <= be dari muka dalam badan (±(d/2 - T/2)); bagian sudut selalu efektif."""
    f = d / 2 - T / 2
    kiri = max(0.0, min(b, -f + be) - a)
    kanan = max(0.0, b - max(a, f - be))
    return min(b - a, kiri + kanan)


def persegi_u(tipe, arah, hw):
    """Persegi (u0, u1, lebar) pada arah lentur (u = x untuk arah X, y untuk Y), sayap efektif 18.10.5.2."""
    dx, dy = DIM[tipe]
    be = 0.25 * hw
    out = []
    for x0, x1, y0, y1, nm in potongan(tipe):
        if arah == "X":
            w = (y1 - y0) if nm in "SN" else panjang_efektif(y0, y1, dy, be)
            out.append((x0, x1, w))
        else:
            w = (x1 - x0) if nm in "WE" else panjang_efektif(x0, x1, dx, be)
            out.append((y0, y1, w))
    return np.array([r for r in out if r[2] > 1e-9])


def titik_batas(tipe):
    dx, dy = DIM[tipe]
    p = [(sx * dx / 2, sy * dy / 2) for sx in (-1, 1) for sy in (-1, 1)]
    for xc, w in PINTU[tipe]:
        p += [(xc - w / 2 - 0.15, -dy / 2), (xc + w / 2 + 0.15, -dy / 2)]
    return p


@functools.lru_cache(maxsize=None)
def batang(tipe, db_v, s_v, nb, db_b):
    """Batang (x, y, As mm², jenis) : badan dua lapis di as dinding @ s_v, batas nb D db_b di sudut dan sisi pintu."""
    dx, dy = DIM[tipe]
    tb_ = titik_batas(tipe)
    out = [(x, y, nb * luas(db_b), "batas") for x, y in tb_]
    for x0, x1, y0, y1, nm in potongan(tipe):
        if nm in "SN":
            yc = (y0 + y1) / 2
            pts = [(x, yc) for x in np.arange(x0 + s_v / 2000, x1, s_v / 1000)]
        else:
            xc = (x0 + x1) / 2
            pts = [(xc, y) for y in np.arange(y0 + s_v / 2000, y1, s_v / 1000)]
        for x, y in pts:
            if min(math.hypot(x - a, y - b) for a, b in tb_) >= 0.45:
                out.append((float(x), float(y), 2 * luas(db_v), "badan"))
    return tuple(out)


def batang_u(tipe, arah, hw, bt):
    """(u, As) batang yang berada di bagian penampang efektif arah ini."""
    dx, dy = DIM[tipe]
    be = 0.25 * hw
    out = []
    for x, y, a, _ in bt:
        if arah == "X":
            sayap = abs(x) >= dx / 2 - T / 2 - 1e-9 and abs(y) < dy / 2 - T / 2
            ok = (not sayap) or (dy / 2 - T / 2 - abs(y) <= be)
            u = x
        else:
            sayap = abs(y) >= dy / 2 - T / 2 - 1e-9 and abs(x) < dx / 2 - T / 2
            ok = (not sayap) or (dx / 2 - T / 2 - abs(x) <= be)
            u = y
        if ok:
            out.append((u, a))
    return np.array(out)


def sifat(rects):
    """A (m²), I terhadap u = 0 (m⁴), umaks (m) dari persegi efektif."""
    u0, u1, w = rects[:, 0], rects[:, 1], rects[:, 2]
    a = float((w * (u1 - u0)).sum())
    i = float((w * (u1 ** 3 - u0 ** 3) / 3).sum())
    return a, i, float(max(u1.max(), -u0.min()))


# ------------------------------------------------------------------ interaksi P-M (blok persegi pada persegi)
def titik_pm(c, rects, bars, tanda=1):
    """Pn (kN), Mn (kNm) terhadap pusat inti, εt, φ untuk kedalaman sumbu netral c (m, array); tanda +1: serat tekan
    di u terbesar, -1: di u terkecil."""
    c = np.atleast_1d(np.asarray(c, float))
    u0, u1, w = (rects[:, 0], rects[:, 1], rects[:, 2]) if tanda > 0 else (-rects[:, 1], -rects[:, 0], rects[:, 2])
    ub, ab = bars[:, 0] * tanda, bars[:, 1]
    umax, umin = u1.max(), u0.min()
    a = np.minimum(BETA1 * c, umax - umin)
    lo = np.maximum(u0[None, :], (umax - a)[:, None])
    ov = np.maximum(u1[None, :] - lo, 0.0)
    fcon = 0.85 * FC * 1000 * w[None, :] * ov                     # kN
    pc, mc = fcon.sum(1), (fcon * (u1[None, :] + lo) / 2).sum(1)
    eps = 0.003 * (c[:, None] - (umax - ub[None, :])) / c[:, None]
    fs = np.clip(ES * eps, -FY, FY) - 0.85 * FC * (ub[None, :] >= (umax - a)[:, None])
    fb = fs * ab[None, :] / 1000
    pn = pc + fb.sum(1)
    mn = mc + (fb * ub[None, :]).sum(1)
    et = 0.003 * (umax - ub.min() - c) / c
    phi = np.clip(0.65 + 0.25 * (et - EPS_TY) / (0.005 - EPS_TY), 0.65, 0.90)
    return pn, mn, et, phi


@functools.lru_cache(maxsize=None)
def diagram(tipe, arah, hw, tanda, tul):
    """Diagram rapat (Pn naik): Pn, Mn, φPn, φMn, c; φPn dibatasi 0,65 × 0,80 Po (Tabel 22.4.2.1)."""
    rects = persegi_u(tipe, arah, hw)
    bars = batang_u(tipe, arah, hw, batang(tipe, *tul))
    dalam = rects[:, 1].max() - rects[:, 0].min()
    c = np.concatenate([np.geomspace(0.005, 0.1 * dalam, 80), np.linspace(0.1 * dalam, 3 * dalam, 400)[1:]])
    pn, mn, _, phi = titik_pm(c, rects, bars, tanda)
    ag, _, _ = sifat(rects)
    ast = bars[:, 1].sum()
    po = (0.85 * FC * (ag * 1e6 - ast) + FY * ast) / 1000
    naik = np.concatenate([[True], pn[1:] > np.maximum.accumulate(pn)[:-1] + 1e-6])
    pn, mn, phi, c = pn[naik], mn[naik], phi[naik], c[naik]
    assert np.all(np.diff(pn) > 0)
    return {"Pn": pn, "Mn": mn, "phiPn": phi * pn, "phiMn": phi * mn, "c": c, "Po": po,
            "phiPmax": 0.65 * 0.80 * po, "Ast": ast}


def mn_pada(dg, p, desain=False):
    """Mn (atau φMn) pada aksial p; nan di luar diagram. φPn penampang bersayap tidak selalu naik terhadap c (φ turun
    lebih cepat dari Pn naik), jadi φMn diambil yang terkecil dari semua perpotongan φPn = p [konservatif]."""
    p = np.asarray(p, float)
    if not desain:
        return np.interp(p, dg["Pn"], dg["Mn"], left=np.nan, right=np.nan)
    a, m = dg["phiPn"], dg["phiMn"]
    pf = p.reshape(-1)
    lo, hi = np.minimum(a[:-1], a[1:]), np.maximum(a[:-1], a[1:])
    t = (pf[:, None] - a[None, :-1]) / np.where(a[1:] == a[:-1], 1e-12, a[1:] - a[:-1])[None, :]
    mm = m[None, :-1] + t * (m[1:] - m[:-1])[None, :]
    ok = (pf[:, None] >= lo[None, :]) & (pf[:, None] <= hi[None, :])
    out = np.where(ok, mm, np.inf).min(1)
    out = np.where(np.isinf(out) | (pf > dg["phiPmax"]), np.nan, out)
    return out.reshape(p.shape)


def mn_arah(tipe, arah, hw, tul, p, desain=True):
    """φMn (atau Mn) terkecil dari dua arah tekan pada aksial p [konservatif: tanda momen model tidak dipetakan]."""
    return np.fmin(mn_pada(diagram(tipe, arah, hw, 1, tul), p, desain),
                   mn_pada(diagram(tipe, arah, hw, -1, tul), p, desain))


def c_pada(tipe, arah, hw, tul, p):
    """c (m) terbesar dari dua arah tekan pada Pn = p (gaya aksial terfaktor, 18.10.6.2)."""
    return max(float(np.interp(p, diagram(tipe, arah, hw, s, tul)["Pn"], diagram(tipe, arah, hw, s, tul)["c"]))
               for s in (1, -1))


# ------------------------------------------------------------------ analisis 3D: gaya inti
@cache_analisis.disk
def analisis(konfig="K2"):
    """Gaya ujung tiap elemen inti [P, Mx, My, Vx, Vy, T] untuk E arah X±/Y± (eksentrisitas ±) dan perpindahan
    puncak inti (m) arah gaya."""
    import openseespy.opensees as ops
    r = kl.balok_rancang()
    tm.UKURAN_BALOK = dict(r["ukuran_model"])
    tm.UKURAN_KOLOM = dict(kl.UKURAN_KOLOM)
    hasil, puncak, info = {}, {}, {}
    try:
        e = tb.elf(konfig)
        for arah in ("X", "Y"):
            ax = min(3.0, max(1.0, (max(tm.faktor_ax(konfig, arah)) / 1.2) ** 2))
            for tanda in (1, -1):
                m = tm.bangun(konfig)
                ops.timeSeries("Linear", 1)
                ops.pattern("Plain", 1, 1)
                for i, (t, fx) in enumerate(zip(m["tk"], e["Fx"]), start=1):
                    x0, y0, x1, y1 = t["bounds"]
                    ecc = tanda * 0.05 * ax
                    if arah == "X":
                        ops.load(m["master"][i], fx, 0, 0, 0, 0, ecc * (y1 - y0) * fx)
                    else:
                        ops.load(m["master"][i], 0, fx, 0, 0, 0, ecc * (x1 - x0) * fx)
                tm._analisis_statik()
                kasus = f"{arah}{'+' if tanda > 0 else '-'}"
                hasil[kasus] = {}
                for el in m["inti"]:
                    lf = np.array(ops.eleResponse(el["ele"], "localForce"))
                    u = kl.ujung(lf)
                    hasil[kasus][(el["nama"], el["lv"])] = np.column_stack([u, [lf[3], lf[3]]])
                    info[(el["nama"], el["lv"])] = el
                for nama in {el["nama"] for el in m["inti"]}:
                    top = max((el for el in m["inti"] if el["nama"] == nama), key=lambda el: el["i"])
                    d = abs(ops.nodeDisp(top["node"], 1 if arah == "X" else 2))
                    puncak[(nama, arah)] = max(puncak.get((nama, arah), 0.0), d)
    finally:
        tm.UKURAN_BALOK = {}
        tm.UKURAN_KOLOM = {}
    return {"gaya": hasil, "puncak": puncak, "info": info, "konfig": konfig}


# ------------------------------------------------------------------ gravitasi inti (tributari)
def beban_tangga(h_tk):
    """Beban mati tangga rata-rata per luas denah (kPa) dari desain tangga."""
    s = tangga(h_tk)
    return s["qd_rata"]


def gravitasi(konfig="K2"):
    """{(nama, lv): (PD, PL)} gaya aksial di ujung bawah elemen inti (kN)."""
    lv_ada = {t["lv"] for t in tb.tingkat(konfig)}
    out = {}
    for nama, kel, puncak in tb.INTI:
        cx, cy = tm.PUSAT_INTI[nama]
        dx, dy = DIM["L" if nama.startswith("Inti") else "T"]
        top = tb.LEVEL[puncak] if konfig == "K2" else min(tb.LEVEL[puncak], tb.LEVEL["LT5"])
        lvs = [lv for lv in URUT_LV if lv in lv_ada and tb.LEVEL[lv] <= top + 1e-6]
        pd = pl = 0.0
        for lv in reversed(lvs):
            h = tm.TINGGI[lv]
            pd += tb.GAMMA_C * T * kel * h * tb.FAKTOR_BUKAAN_DINDING
            lajur = (dx + T + 2 * LAJUR_PELAT) * (dy + T + 2 * LAJUR_PELAT) - (dx + T) * (dy + T)
            if konfig == "K1" and lv == "LT5":
                qd, ql = tb.SIDL["rangka_atap_sementara"][0], 0.96
            else:
                qd, ql = kl.tbk.beban_panel(lv, cx, cy - dy / 2 - T / 2 - LAJUR_PELAT / 2)
            pd += qd * lajur
            pl += ql * lajur
            if not nama.startswith("Inti"):
                a_in = (dx - T) * (dy - T)
                pd += beban_tangga(h) * a_in
                pl += L_TANGGA * a_in
            out[(nama, lv)] = (pd, pl)
    return out


def kombinasi(h, g, k):
    """Gaya terfaktor (n, 2, 6) dan penanda gempa untuk elemen inti k = (nama, lv)."""
    pd, pl = g[k]
    d = np.zeros((2, 6))
    d[:, 0] = pd
    l_ = np.zeros((2, 6))
    l_[:, 0] = pl
    ev = 0.2 * tb.SDS
    out, gempa = [1.4 * d, 1.2 * d + 1.6 * l_], [False, False]
    gy = h["gaya"]
    for a, o in (("X", "Y"), ("Y", "X")):
        for s1 in "+-":
            ea = gy[f"{a}{s1}"][k]
            for s2 in "+-":
                eo = gy[f"{o}{s2}"][k]
                for sg in (1, -1):
                    for so in (1, -1):
                        eq = tb.RHO * (sg * ea + 0.3 * so * eo)
                        out += [(1.2 + ev) * d + l_ + eq, (0.9 - ev) * d + eq]
                        gempa += [True, True]
    return np.array(out), np.array(gempa)


def gaya_inti(hs):
    """{(nama, lv): {'F', 'gempa', 'kelompok', 'tipe'}} K1 ∪ K2."""
    out = {}
    for h in hs:
        g = gravitasi(h["konfig"])
        for k in h["info"]:
            f, ge = kombinasi(h, g, k)
            if k in out:
                out[k]["F"] = np.concatenate([out[k]["F"], f])
                out[k]["gempa"] = np.concatenate([out[k]["gempa"], ge])
            else:
                kel = kelompok_inti(k[0])
                out[k] = {"F": f, "gempa": ge, "kelompok": kel, "tipe": KELOMPOK[kel]}
    return out


# ------------------------------------------------------------------ geser dinding
def geser_dinding(tipe, F):
    """Gaya geser per dinding badan (kN) untuk semua kombinasi dan ujung: arah X (dinding S/N) dan Y (W/E).
    Vu dinding = |V|/2 + |T| d/(2 A0) [aliran geser torsi kotak tertutup, A0 = dx dy]."""
    dx, dy = DIM[tipe]
    a0 = dx * dy
    vx = np.abs(F[..., 3]) / 2 + np.abs(F[..., 5]) * dx / (2 * a0)
    vy = np.abs(F[..., 4]) / 2 + np.abs(F[..., 5]) * dy / (2 * a0)
    return vx, vy


def panjang_bersih(tipe):
    """Panjang bersih dinding badan arah X (dinding selatan berpintu) dan Y (m)."""
    dx, dy = DIM[tipe]
    return dx + T - sum(w for _, w in PINTU[tipe]), dy + T


def alpha_c(rasio):
    return float(np.interp(rasio, [1.5, 2.0], [0.25, 0.17]))


PILIH_HORIZ = sorted([(2 * luas(db) / (T * 1000 * s), db, s) for db in (13, 16, 19) for s in
                      (300, 250, 200, 175, 150, 125, 100) if 2 * luas(db) / (T * 1000 * s) >= 0.0025])


# ------------------------------------------------------------------ desain kelompok
def desain_kelompok(g, lv, anggota, gi, hs_puncak):
    tipe = KELOMPOK[g]
    dx, dy = DIM[tipe]
    hw = hw_kelompok(g)
    hw_maks = max(hw_inti(n) for n, _ in anggota)
    lw = {"X": dx + T, "Y": dy + T}
    rasio_hw = {a: hw_maks / lw[a] for a in "XY"}
    Fs = [gi[k]["F"] for k in anggota]
    # ---- geser
    lnet = dict(zip("XY", panjang_bersih(tipe)))
    vu = {"X": max(float(geser_dinding(tipe, F)[0].max()) for F in Fs),
          "Y": max(float(geser_dinding(tipe, F)[1].max()) for F in Fs)}
    vu_total = {"X": max(float(np.abs(F[..., 3]).max()) for F in Fs),
                "Y": max(float(np.abs(F[..., 4]).max()) for F in Fs)}
    ac = {a: alpha_c(rasio_hw[a]) for a in "XY"}
    # ---- lentur-aksial: pilih tulangan vertikal badan dan batas
    # kandidat (badan vertikal × batas) urut luas baja total; ρ zona batas sisi pintu <= RHO_BATAS
    kand = sorted((sum(b[2] for b in batang(tipe, v[1], v[2], nb, dbb)), (v[1], v[2], nb, dbb))
                  for v in PILIH_HORIZ if v[2] >= 150 for nb in N_BATAS for dbb in DB_BATAS
                  if nb * luas(dbb) / (LEG_MIN * T * 1e6) <= RHO_BATAS)
    hasil = None
    for _, tul in kand:
        rasio = 0.0
        for F in Fs:
            p = F[..., 0]
            r = (np.abs(F[..., 2]) / mn_arah(tipe, "X", hw, tul, p) + np.abs(F[..., 1]) / mn_arah(tipe, "Y", hw, tul, p))
            rasio = max(rasio, float(np.nanmax(np.where(np.isnan(r), np.inf, r))))
        if rasio <= 1.0:
            hasil = (tul, rasio)
            break
    if hasil is None:
        hasil = (tul, rasio)
    tul, rasio_pm = hasil
    # kombinasi penentu P-M
    pen = None
    for k, F in zip(anggota, Fs):
        p = F[..., 0]
        r = (np.abs(F[..., 2]) / mn_arah(tipe, "X", hw, tul, p) + np.abs(F[..., 1]) / mn_arah(tipe, "Y", hw, tul, p))
        r = np.where(np.isnan(r), np.inf, r)
        i, e = np.unravel_index(np.argmax(r), r.shape)
        if pen is None or r[i, e] > pen["rasio"]:
            f = F[i, e]
            pen = {"kunci": k, "rasio": float(r[i, e]), "Pu": float(f[0]), "Mux": abs(float(f[1])),
                   "Muy": abs(float(f[2])), "phiMnX": float(mn_arah(tipe, "X", hw, tul, f[0])),
                   "phiMnY": float(mn_arah(tipe, "Y", hw, tul, f[0]))}
    # ---- tulangan horizontal dan φ geser (21.2.4.1)
    gs = {}
    for a in "XY":
        acw = T * lnet[a]
        # geser saat Mn tercapai: Vu × Mn/Mu pada kombinasi gempa dengan Mu terbesar arah ini
        im = 2 if a == "X" else 1
        vmn = 0.0
        for F, gem in zip(Fs, [gi[k]["gempa"] for k in anggota]):
            m = np.abs(F[gem][..., im])
            j = np.unravel_index(np.argmax(m), m.shape)
            mu = float(m[j])
            mn = float(mn_arah(tipe, a, hw, tul, F[gem][j][0], desain=False))
            vdin = geser_dinding(tipe, F[gem][j])[0 if a == "X" else 1]
            if mu > 1e-6:
                vmn = max(vmn, float(vdin) * mn / mu)
        for rho, db, s in PILIH_HORIZ:
            vn = acw * (ac[a] * math.sqrt(FC) + rho * FY) * 1000
            phi = 0.75 if vn >= vmn else 0.60
            if phi * vn >= vu[a] and vn <= 0.83 * math.sqrt(FC) * acw * 1000:
                break
        gs[a] = {"Acw": acw, "Vu": vu[a], "Vu_total": vu_total[a], "alpha_c": ac[a], "rho_t": rho, "db": db, "s": s,
                 "Vn": vn, "V_Mn": vmn, "phi": phi, "phiVn": phi * vn, "rasio": vu[a] / (phi * vn),
                 "batas_083": 0.83 * math.sqrt(FC) * acw * 1000,
                 "batas_066": 0.66 * math.sqrt(FC) * 2 * acw * 1000,
                 "dua_lapis": vu_total[a] > 0.17 * 2 * acw * math.sqrt(FC) * 1000 or rasio_hw[a] >= 2.0,
                 "hw_lw": rasio_hw[a]}
    horiz = max((gs["X"]["rho_t"], gs["X"]["db"], gs["X"]["s"]), (gs["Y"]["rho_t"], gs["Y"]["db"], gs["Y"]["s"]))
    # ρl >= ρt bila hw/lw <= 2 (18.10.4.3)
    rho_l = 2 * luas(tul[0]) / (T * 1000 * tul[1])
    hw_lw_min = min(hw / x for x in lw.values())          # 18.10.4.3 memakai inti terpendek kelompok
    perlu_l = horiz[0] if hw_lw_min <= 2.0 else 0.0025
    if rho_l < perlu_l - 1e-12:
        v = [p for p in PILIH_HORIZ if p[0] >= perlu_l][0]
        tul = (v[1], v[2], tul[2], tul[3])
        rho_l = v[0]
    return {"kelompok": g, "lv": lv, "tipe": tipe, "anggota": anggota, "hw": hw, "hw_maks": hw_maks, "lw": lw,
            "tul": tul, "rho_l": rho_l, "horiz": horiz, "pm": pen, "rasio_pm": rasio_pm, "geser": gs}


# ------------------------------------------------------------------ elemen batas
def elemen_batas(x, gi, puncak):
    """18.10.6.2 (perpindahan, hanya penampang kritis LT1 bila hw/lw >= 2) dan 18.10.6.3 (tegangan) per kelompok-lv."""
    tipe, hw, tul = x["tipe"], x["hw"], x["tul"]
    out = {}
    for a in "XY":
        rects = persegi_u(tipe, a, hw)
        ag, ii, umax = sifat(rects)
        out[a] = {"Ag": ag, "I": ii, "umax": umax, "S": ii / umax}
    # tegangan: σ = P/A + |Mx|/Sy-arah + |My|/Sx-arah (sudut), A terkecil
    ag = min(out["X"]["Ag"], out["Y"]["Ag"])
    sig, pen = 0.0, None
    for k in x["anggota"]:
        F = gi[k]["F"][gi[k]["gempa"]]
        s = (F[..., 0] / ag + np.abs(F[..., 2]) / out["X"]["S"] + np.abs(F[..., 1]) / out["Y"]["S"]) / 1000   # MPa
        j = np.unravel_index(np.argmax(s), s.shape)
        if float(s[j]) > sig:
            sig = float(s[j])
            f = F[j]
            pen = {"kunci": k, "Pu": float(f[0]), "Mux": abs(float(f[1])), "Muy": abs(float(f[2]))}
    hasil = {"penampang": out, "Ag": ag, "sigma": sig, "sigma_pen": pen, "perlu_tegangan": sig > 0.2 * FC,
             "henti_tegangan": sig < 0.15 * FC}
    # perpindahan: hanya elemen LT2 (penampang kritis di dasar)
    perp = []
    if x["lv"] == "LT2":
        for k in x["anggota"]:
            nama = k[0]
            hwi = hw_inti(nama)
            F = gi[k]["F"][gi[k]["gempa"]]
            for a in "XY":
                lw = x["lw"][a]
                de = max(puncak.get((nama, a, kf), 0.0) for kf in ("K1", "K2"))
                du = tb.CD * de / tb.IE
                rasio = max(du / hwi, 0.005)
                pmax = float(F[..., 0].max())
                c = c_pada(tipe, a, hw, tul, pmax)
                clim = lw / (600 * 1.5 * rasio)
                im = 2 if a == "X" else 1
                iv = 3 if a == "X" else 4
                m = np.abs(F[..., im])
                j = np.unravel_index(np.argmax(m), m.shape)
                mu, vu_ = float(m[j]), float(abs(F[j][iv]))
                perp.append({"inti": nama, "arah": a, "hw": hwi, "lw": lw, "berlaku": hwi / lw >= 2.0, "de": de,
                             "du": du, "du_hw": du / hwi, "rasio": rasio, "Pu": pmax, "c": c, "c_lim": clim,
                             "perlu": c >= clim and hwi / lw >= 2.0, "tinggi": max(lw, mu / (4 * vu_) if vu_ else 0),
                             "c_lw": c / lw})
    hasil["perpindahan"] = perp
    # zona batas: panjang dan ρ (18.10.6.4(a), 18.10.6.5)
    cmax = max([p["c"] for p in perp], default=0.0)
    lw_min = min(x["lw"].values())
    leg = max(cmax - 0.1 * lw_min, cmax / 2, LEG_MIN)
    nb, dbb = tul[2], tul[3]
    a_sudut = leg * T + (leg - T) * T
    a_kusen = leg * T
    hasil.update({"leg": leg, "rho_sudut": nb * luas(dbb) / (a_sudut * 1e6), "rho_kusen": nb * luas(dbb) / (a_kusen * 1e6),
                  "batas_rho": 2.8 / FY})
    hasil["perlu"] = any(p["perlu"] for p in perp) or (hasil["perlu_tegangan"] and not any(p["berlaku"] for p in perp)
                                                       if perp else hasil["perlu_tegangan"])
    # tulangan transversal batas
    db_h = 13 if dbb >= 22 else 10
    if hasil["perlu"]:
        bc = T * 1000 - 2 * SEL
        ag_be, ach = leg * 1000 * T * 1000, (leg * 1000 - SEL) * bc
        ra, rb = 0.3 * (ag_be / ach - 1) * FC / FY, 0.09 * FC / FY
        s = floor25(min(T * 1000 / 3, 6 * dbb, 150.0))
        hasil["trans"] = {"jenis": "SBE 18.10.6.4", "s": s, "s_luar": floor25(min(200.0, 8 * dbb)), "ra": ra,
                          "rb": rb, "Ash_perlu": max(ra, rb) * s * bc, "db": 13}
    else:
        s_sendi = floor25(min(150.0, 6 * dbb))
        s_luar = floor25(min(200.0, 8 * dbb))
        perlu_ikat = max(hasil["rho_sudut"], hasil["rho_kusen"]) > 2.8 / FY
        hasil["trans"] = {"jenis": "18.10.6.5(a)" if perlu_ikat else "tidak perlu sengkang pengekang",
                          "s": s_sendi if perlu_ikat else None, "s_luar": s_luar if perlu_ikat else None,
                          "db": db_h, "perlu_ikat": perlu_ikat}
    return hasil


# ------------------------------------------------------------------ balok kopel (ambang pintu)
def koef_aliran(tipe):
    """Aliran geser per satuan gaya (1/m) di pintu dinding selatan: qx (Vx; dinding selatan = badan), qy (Vy; sayap),
    qt (T): q = V Q/I dan T/(2 A0), kotak as tebal T, posisi paling kritis di rentang pintu."""
    dx, dy = DIM[tipe]
    _, ix, iy, _, _, _ = tm.kotak(dx, dy, T)
    out = []
    for xc, w in PINTU[tipe]:
        xa = max(abs(xc) - w / 2, 0.0)         # Q terbesar (badan) di x terkecil
        xb = abs(xc) + w / 2                   # sayap: terbesar di x terbesar
        qx = (T * (dy / 2) * (dx / 2) + T * ((dx / 2) ** 2 - xa ** 2) / 2) / iy
        qy = T * (dy / 2) * xb / ix
        out.append({"xc": xc, "w": w, "qx": qx, "qy": qy, "qt": 1 / (2 * dx * dy)})
    return out


def balok_kopel(g, gi):
    tipe = KELOMPOK[g]
    ks = [k for k in gi if gi[k]["kelompok"] == g]
    best = None
    for p in koef_aliran(tipe):
        for k in ks:
            F = gi[k]["F"]
            h_tk = tm.TINGGI[k[1]]
            q = p["qx"] * np.abs(F[..., 3]) + p["qy"] * np.abs(F[..., 4]) + p["qt"] * np.abs(F[..., 5])
            vu = float(q.max()) * h_tk
            if best is None or vu > best["Vu"]:
                best = {"Vu": vu, "kunci": k, "h_tk": h_tk, **p}
    ln, h = best["w"], best["h_tk"] - H_PINTU
    bw = T
    acw = bw * h
    batas033 = 0.33 * math.sqrt(FC) * acw * 1000
    batas083 = 0.83 * math.sqrt(FC) * acw * 1000
    rasio = ln / h
    diagonal = rasio < 2 and best["Vu"] > batas033
    d = h - 0.075
    mu = best["Vu"] * ln / 2
    as_ = max(mu / (0.9 * FY * 0.9 * d * 1000) * 1e6, 1.4 / FY * bw * d * 1e6, 0.25 * math.sqrt(FC) / FY * bw * d * 1e6)
    out = {**best, "ln": ln, "h": h, "ln_h": rasio, "Acw": acw, "batas033": batas033, "batas083": batas083,
           "diagonal": diagonal, "Mu": mu, "d": d, "As": as_}
    if diagonal:
        alpha = math.atan((h - 0.3) / ln)
        avd = best["Vu"] / (0.85 * 2 * FY * math.sin(alpha)) * 1000
        out.update({"alpha": math.degrees(alpha), "Avd": avd})
    else:
        av_s = best["Vu"] / 0.75 / (FY * d * 1000) * 1e3            # mm²/mm, Vc = 0 [konservatif, 18.6.5.2]
        s = floor25(min(d * 1000 / 4, 150.0, 2 * luas(13) / max(av_s, 1e-9)))
        out.update({"Av_s": av_s, "s": s, "kaki": 2, "db_s": 13})
    nb = max(math.ceil(as_ / luas(19)), 3)
    out["batang"] = (nb, 19)
    if diagonal:
        out["diag"] = (max(math.ceil(out["Avd"] / luas(25)), 4), 25)       # >= 4 batang per kelompok (18.10.7.4(b))
    return out


# ------------------------------------------------------------------ tangga
TEBAL_TANGGA_MIN = 0.15
FINISH_TANGGA = 1.5    # kPa keramik + spesi + railing [Asumsi; Tabel C3.1-1 keramik 1,10]
L_TANGGA = 4.79        # kPa Tabel 4.3-1 tangga dan jalan keluar
GOING = 0.28


@functools.lru_cache(maxsize=None)
def tangga(h_tk):
    """Tangga pelat satu arah di dalam inti tangga 4 × 6 m, dua lengan per tingkat, bentang antara dinding as y
    (ℓ = 6,0 m, muka ke muka 5,65 m), terjepit sebagian di dinding (Tabel 7.3.1.1 satu ujung menerus ℓ/24)."""
    dx, dy = DIM["T"]
    ell = dy
    ln = dy - T
    naik = h_tk / 2
    n_r = math.ceil(naik / 0.175 - 1e-9)
    r = naik / n_r
    lf = (n_r - 1) * GOING
    bordes = (ln - lf) / 2
    th = math.atan(r / GOING)
    hmin = ell / 24
    t = max(TEBAL_TANGGA_MIN, math.ceil(hmin * 100 - 1e-9) / 100)
    lebar = (dx - T - 0.10) / 2      # lebar lengan, celah 100 mm
    qd_lengan = tb.GAMMA_C * (t / math.cos(th) + r / 2) + FINISH_TANGGA
    qd_bordes = tb.GAMMA_C * t + FINISH_TANGGA
    wu_l = 1.2 * qd_lengan + 1.6 * L_TANGGA
    wu_b = 1.2 * qd_bordes + 1.6 * L_TANGGA
    # balok sederhana bentang ln + t (tumpuan di muka dinding + t/2) dengan beban per proyeksi horizontal
    L = ln + t
    a1, a2 = bordes + t / 2, bordes + t / 2 + lf
    xs = np.linspace(0, L, 2001)
    w = np.where((xs >= a1) & (xs <= a2), wu_l, wu_b)
    tot = np.trapezoid(w, xs) if hasattr(np, "trapezoid") else np.trapz(w, xs)
    mom = np.trapezoid(w * xs, xs) if hasattr(np, "trapezoid") else np.trapz(w * xs, xs)
    rb = mom / L
    ra = tot - rb
    from scipy.integrate import cumulative_trapezoid
    v = ra - cumulative_trapezoid(w, xs, initial=0)
    m = cumulative_trapezoid(v, xs, initial=0)
    mpos = float(m.max())
    mneg = max(wu_l, wu_b) * ln ** 2 / 24                  # Tabel 6.5.2 tumpuan menyatu dengan dinding/balok tepi
    db = 13
    d = t * 1000 - SEL - db / 2
    def as_perlu(mu):
        rn = mu * 1e6 / (0.9 * 1000 * d ** 2)
        rho = 0.85 * FC_TANGGA / FY * (1 - math.sqrt(1 - 2 * rn / (0.85 * FC_TANGGA)))
        return rho * 1000 * d
    asmin = 0.0018 * 1000 * t * 1000                        # 7.6.1.1 (fy 420)
    asp, asn = max(as_perlu(mpos), asmin), max(as_perlu(mneg), asmin)
    sp = floor25(min(luas(db) * 1000 / asp, 3 * t * 1000, 450))
    sn = floor25(min(luas(db) * 1000 / asn, 3 * t * 1000, 450))
    vu = max(ra, rb)
    phivc = 0.75 * 0.17 * math.sqrt(FC_TANGGA) * 1000 * d / 1000
    qd_rata = ((qd_lengan * lf + qd_bordes * (ln - lf)) / ln) * (2 * lebar) / (dx - T)
    return {"h_tk": h_tk, "ell": ell, "ln": ln, "L": L, "n_r": n_r, "r": r, "going": GOING, "lf": lf, "bordes": bordes,
            "theta": math.degrees(th), "hmin": hmin, "t": t, "lebar": lebar, "qd_lengan": qd_lengan,
            "qd_bordes": qd_bordes, "wu_l": wu_l, "wu_b": wu_b, "a1": a1, "a2": a2, "Ra": ra, "Rb": rb, "Mpos": mpos,
            "Mneg": mneg, "d": d, "As_pos": asp, "As_neg": asn, "As_min": asmin, "s_pos": sp, "s_neg": sn,
            "Vu": vu, "phiVc": phivc, "qd_rata": qd_rata, "db": db}


FC_TANGGA = 30.0   # pelat tangga sama dengan pelat lantai (4.5)


def tangga_pynite(s):
    """Cek silang T-81: balok patah (bordes datar - lengan miring - bordes datar) sendi-rol di PyNite, beban vertikal
    per proyeksi horizontal; momen maksimum (kNm/m)."""
    from Pynite import FEModel3D
    m = FEModel3D()
    e = 4700 * math.sqrt(FC_TANGGA) * 1000
    m.add_material("c", e, e / 2.4, 0.2, 24.0)
    t = s["t"]
    m.add_section("s", t, t ** 3 / 12, 1.0 * t ** 3 / 12, 1e-3)
    tinggi = s["r"] * s["n_r"]
    pts = [(0.0, 0.0), (s["a1"], 0.0), (s["a2"], tinggi), (s["L"], tinggi)]
    for i, (x, y) in enumerate(pts):
        m.add_node(f"N{i}", x, y, 0.0)
    m.def_support("N0", True, True, True, True, True, False)
    m.def_support("N3", False, True, True, False, False, False)
    for i in range(3):
        m.add_member(f"M{i}", f"N{i}", f"N{i + 1}", "c", "s")
    cos = (s["a2"] - s["a1"]) / math.hypot(s["a2"] - s["a1"], tinggi)   # beban per proyeksi → per panjang batang
    m.add_member_dist_load("M0", "FY", -s["wu_b"], -s["wu_b"], case="U")
    m.add_member_dist_load("M1", "FY", -s["wu_l"] * cos, -s["wu_l"] * cos, case="U")
    m.add_member_dist_load("M2", "FY", -s["wu_b"], -s["wu_b"], case="U")
    m.add_load_combo("U", {"U": 1.0})
    m.analyze_linear(check_statics=False)
    mm = max(abs(m.members[f"M{i}"].max_moment("Mz", "U")) for i in range(3))
    mn_ = max(abs(m.members[f"M{i}"].min_moment("Mz", "U")) for i in range(3))
    return max(mm, mn_)


# ------------------------------------------------------------------ atap sementara tahap 1 dan angkur
ANGKUR = {"n": 4, "d": 16, "Ase": 157.0, "futa": 400.0, "hef": 150.0, "s": 150.0, "b_kolom": tb.KOLOM_MEN * 1000}


def atap_sementara():
    """Atap baja ringan sementara di atas kolom menara +30,25 (K1): reaksi per kolom dalam (tributari 8 × 8 m) dan
    angkur cor di tempat. Rangka baja ringan sendiri oleh pemasok (SNI baja ringan belum ada di acuan/)."""
    h = tb.LEVEL["LT5"] - 12.05
    qh = 0.613 * tb.kz(h) * tb.KZT * tb.KD * tb.KE * tb.V_ANGIN ** 2 / 1000
    hl = h / 24.0
    cp = float(np.interp(hl, [0.5, 1.0], [-0.9, -1.3]))
    g, gcpi = 0.85, 0.18
    p = qh * (g * cp - gcpi)                                  # kPa (negatif = hisap ke atas)
    atrib = kl.L_GRID ** 2
    d, lr = tb.SIDL["rangka_atap_sementara"][0], 0.96
    nu = (0.9 * d + p) * atrib                                # 0,9D + 1,0W (negatif = tarik angkur)
    pu_tekan = max(1.2 * d + 1.6 * lr, 1.4 * d) * atrib
    an = ANGKUR
    nsa = an["Ase"] * an["futa"] / 1000
    phi_nsa = 0.75 * an["n"] * nsa
    nb = 10 * math.sqrt(FC) * an["hef"] ** 1.5 / 1000
    ca = (an["b_kolom"] - an["s"]) / 2
    sisi = an["s"] + 2 * min(1.5 * an["hef"], ca)
    anc, anco = sisi ** 2, 9 * an["hef"] ** 2
    ncbg = anc / anco * nb
    phi_ncbg = 0.70 * ncbg
    return {"h": h, "qh": qh, "h_L": hl, "Cp": cp, "G": g, "GCpi": gcpi, "p": p, "Atrib": atrib, "D": d, "Lr": lr,
            "Nu": nu, "Pu_tekan": pu_tekan, "Nsa": nsa, "phiNsa": phi_nsa, "Nb": nb, "ca": ca, "ANc": anc,
            "ANco": anco, "Ncbg": ncbg, "phiNcbg": phi_ncbg, "tarik": max(-nu, 0.0),
            "ok": max(-nu, 0.0) <= min(phi_nsa, phi_ncbg), "ed_ok": ca >= 1.5 * an["hef"]}


# ------------------------------------------------------------------ rancang
@functools.lru_cache(maxsize=1)
def analisis_semua():
    return [analisis("K2"), analisis("K1")]


@cache_analisis.disk
def rancang(hs=None):
    hs = hs or analisis_semua()
    gi = gaya_inti(hs)
    puncak = {(n, a, h["konfig"]): v for h in hs for (n, a), v in h["puncak"].items()}
    grup = {}
    for k, v in gi.items():
        grup.setdefault((v["kelompok"], k[1]), []).append(k)
    hasil = []
    for (g, lv) in sorted(grup, key=lambda t: (list(KELOMPOK).index(t[0]), URUT_LV.index(t[1]))):
        x = desain_kelompok(g, lv, grup[(g, lv)], gi, puncak)
        x["batas"] = elemen_batas(x, gi, puncak)
        x["ok"] = (x["rasio_pm"] <= 1.0 and all(s["rasio"] <= 1.0 and s["Vu"] <= 0.75 * s["batas_083"]
                                                for s in x["geser"].values()))
        hasil.append(x)
    kopel = {g: balok_kopel(g, gi) for g in KELOMPOK}
    tg = {h: tangga(h) for h in sorted(set(tm.TINGGI.values()))}
    gov = max((x for x in hasil if x["kelompok"] == "W-L"), key=lambda x: x["rasio_pm"])
    return {"kelompok": hasil, "kopel": kopel, "tangga": tg, "atap": atap_sementara(), "gaya": gi,
            "puncak": puncak, "cp": cek_concreteproperties(hasil[0]),
            "pynite": {h: tangga_pynite(s) for h, s in tg.items()}, "gov": gov["kelompok"] + " " + gov["lv"]}


# ------------------------------------------------------------------ cek silang T-80: concreteproperties
def cek_concreteproperties(x, arah="X"):
    """Inti x (penampang LT2) lentur arah X (simetris terhadap x = 0): Mn pada Pn = Pu penentu, rumus sendiri vs
    concreteproperties (batang satu per satu, blok persegi 0,85 fc', β1 0,80)."""
    from concreteproperties.concrete_section import ConcreteSection
    from concreteproperties.material import Concrete, SteelBar
    from concreteproperties.stress_strain_profile import (ConcreteLinearNoTension, RectangularStressBlock,
                                                          SteelElasticPlastic)
    from sectionproperties.pre.library.concrete_sections import add_bar
    from sectionproperties.pre.library.primitive_sections import rectangular_section

    tipe, hw, tul = x["tipe"], x["hw"], x["tul"]
    ec = 4700 * math.sqrt(FC)
    beton = Concrete("fc35", 2.4e-6, ConcreteLinearNoTension(elastic_modulus=ec, ultimate_strain=0.003,
                                                              compressive_strength=FC), "lightgrey",
                     RectangularStressBlock(compressive_strength=FC, alpha=0.85, gamma=BETA1, ultimate_strain=0.003),
                     flexural_tensile_strength=0.62 * math.sqrt(FC))
    baja = SteelBar("BjTS420", 7.85e-6, SteelElasticPlastic(yield_strength=FY, elastic_modulus=ES,
                                                            fracture_strain=0.05), "grey")
    geom = None
    for x0, x1, y0, y1, _ in potongan(tipe):
        r = rectangular_section(d=(y1 - y0) * 1000, b=(x1 - x0) * 1000, material=beton).align_center(
            ((x0 + x1) / 2 * 1000, (y0 + y1) / 2 * 1000))
        geom = r if geom is None else geom + r
    for bx, by, a, _ in batang(tipe, *tul):
        geom = add_bar(geom, a, baja, bx * 1000, by * 1000, 8)
    sec = ConcreteSection(geom)
    pu = x["pm"]["Pu"]
    dg = diagram(tipe, arah, hw, 1, tul)
    pn = float(np.interp(pu, dg["phiPn"], dg["Pn"]))
    mn_sendiri = float(mn_pada(dg, pn))
    mi = sec.moment_interaction_diagram(theta=math.pi / 2, n_points=40, progress_bar=False)
    n_cp = np.array([r.n for r in mi.results]) / 1e3
    m_cp = np.array([abs(r.m_y) for r in mi.results]) / 1e6
    o = np.argsort(n_cp)
    mn_cp = float(np.interp(pn, n_cp[o], m_cp[o]))
    return {"Pn": pn, "Mn_sendiri": mn_sendiri, "Mn_cp": mn_cp, "kelompok": f"{x['kelompok']} {x['lv']}"}


# ------------------------------------------------------------------ Excel
C_RASIO = (0.02, 0.05, 0.08, 0.12, 0.18, 0.25, 0.35, 0.50, 0.75, 1.00)   # c/kedalaman titik diagram di Excel


def teks_tul(x):
    dbv, sv, nb, dbb = x["tul"]
    return dbv, sv, nb, dbb


def buat_excel(r, keluar=BERKAS, hitung_ulang=True):
    import openpyxl
    from format_dokumen import AI, Lembar, hitung_ulang_excel, set_font_bawaan

    kel = r["kelompok"]
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    lab = f"DIISI AI ATAS PERMINTAAN DEFSA (20 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk desain dinding geser, balok kopel, tangga, atap (4.8)",
                [6, 120])
    lb.catatan(LABEL + " " + lab)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, t] for i, t in enumerate([
        "Dinding struktural khusus (SNI 2847:2019 Pasal 18.10) tebal 350 mm, fc' 35 MPa, BjTS 420B, selimut 20 mm "
        "(dinding tidak terpapar). Inti lif 8 × 8 m (W-L, x 50-58 y 35-43, sampai atap), inti tangga 4 × 6 m menara "
        "(W-TM, y 39, sampai atap) dan podium (W-TP, y 63: x 22 sampai LT4, x 46/70 sampai LT3); ukuran as dinding. "
        "Nama kelompok = tingkat di ujung atas segmen (LT2 = segmen LT1-LT2, penampang kritis di LT1 +12,85).",
        "Pintu [Asumsi, ditinjau di Tahap 5 arsitektur]: inti lif dua pintu 1,4 m dan inti tangga satu pintu 1,2 m, "
        f"semuanya di dinding selatan, tinggi {H_PINTU:.1f} m. Penampang lentur dan geser memakai dinding selatan yang "
        "terpotong pintu (18.10.5.1 pengaruh bukaan). Ambang pintu = balok kopel (18.10.7).",
        "Gaya dalam dari model 3D 4.3 (inti = kolom kotak Timoshenko, retak 0,35 Ig, faktor bukaan 0,85) dengan "
        "ukuran balok 4.6 dan kolom 4.7. Gempa ELF V = 13.164 kN (K2), 0,05 Ax, 100 % + 30 %, ρ 1,3, Ev 0,077D; K1 "
        "dan K2 diselubungi. Aksial gravitasi inti tributari sendiri: berat dinding × 0,85, lajur pelat 1,0 m di "
        "sekeliling inti [Asumsi], tangga di dalam inti tangga; inti lif tanpa beban lif [Asumsi, konservatif "
        "untuk lentur].",
        "Lentur-aksial 18.10.5.1 hal. 405 (22.4): kompatibilitas regangan, blok persegi 0,85 fc', β1 0,80, φ Tabel "
        "21.2.2, φPn,max = 0,65 × 0,80 Po. Sayap efektif 18.10.5.2 hal. 405: min(setengah jarak badan; 0,25 hw) dari "
        "muka badan. Dua arah: (|Muy|/φMn,X + |Mux|/φMn,Y) <= 1 (Bresler α = 1), φMn arah = yang terkecil dari dua arah "
        "tekan [konservatif]. Batang batas di 4 sudut dan di kedua sisi tiap pintu.",
        "Tulangan badan 18.10.2.1-18.10.2.2 hal. 402-403: ρl, ρt >= 0,0025, s <= 450, dua lapis (Vu > 0,17 Acv √fc' "
        "atau hw/lw >= 2). Geser 18.10.4 hal. 403-404: Vn = Acw (αc √fc' + ρt fy), αc 0,25 (hw/lw <= 1,5) s.d. 0,17 "
        "(>= 2,0); Vu dinding badan = |V|/2 + |T| d/(2 A0) (torsi kotak tertutup); batas 0,83 √fc' Acw per segmen "
        "dan 0,66 √fc' Acv bersama. φ = 0,60 bila Vn < geser saat Mn tercapai (21.2.4.1 hal. 474), selain itu 0,75. "
        "ρl >= ρt bila hw/lw <= 2 (18.10.4.3). SNI 2847:2019 18.10.3 memakai Vu analisis; pembesaran Ωv ωv ACI "
        "318-19 hanya informasi.",
        "Elemen batas 18.10.6 hal. 406-412: (1) perpindahan 18.10.6.2 di penampang kritis LT1 bila hw/lw >= 2: perlu "
        "bila c >= lw/(600 × 1,5 δu/hw), δu = Cd δe/Ie (SNI 1726 Pasal 7.8.6) dari perpindahan puncak inti, δu/hw >= "
        "0,005; (2) tegangan 18.10.6.3: perlu bila σ = Pu/Ag + Mu/S > 0,2 fc', berhenti bila < 0,15 fc'. Bila tidak "
        "perlu: 18.10.6.5(a) bila ρ zona batas > 2,8/fy: sengkang/ikat silang 18.7.5.2(a)-(e), s <= min(200; 8 db), "
        "di zona sendi maks(lw; Mu/4Vu) s <= min(150; 6 db); 18.10.6.5(b) kait standar tulangan horizontal di tepi.",
        "Balok kopel 18.10.7 hal. 412-414: Vu ambang = aliran geser di pintu × tinggi tingkat; q = V Q/I (kotak as) + "
        "T/(2 A0), dijumlah mutlak [konservatif]. ℓn/h < 2 dan Vu > 0,33 √fc' Acw: tulangan diagonal (18.10.7.4, φ 0,85 "
        "21.2.4.3); selain itu 18.10.7.3: sebagai balok 18.6.3-18.6.5 (Vc = 0 konservatif). Vn <= 0,83 √fc' Acw.",
        "Tangga: pelat satu arah tebal >= ℓ/24 (Tabel 7.3.1.1 hal. 120, satu ujung menerus; ℓ = 6,0 m as dinding), "
        "fc' 30, dua lengan per tingkat, injakan 280 mm, tanjakan <= 175 mm; beban mati badan miring + anak tangga + "
        "finishing 1,5 kPa [Asumsi], hidup 4,79 kPa (SNI 1727 Tabel 4.3-1). Mu+ sendi-rol (balok patah), Mu- = wu ℓn²/24 "
        "(Tabel 6.5.2). Cek silang PyNite balok patah (T-81).",
        "Atap sementara tahap 1 (K1, keputusan M-4): rangka baja ringan + penutup metal 0,40 kPa di atas kolom menara "
        "+30,25; Lr 0,96; angin hisap SNI 1727 Gambar 27.3-1 Cp(h/L) dan GCpi +0,18 (Tabel 26.13-1), V 30 m/s [Asumsi "
        "4.2]. Angkur cor di tempat 4 M16 kelas 4.6 [Asumsi], hef 150: φNsa 17.4.1.2 (φ 0,75) dan jebol beton "
        "17.4.2.2 kelompok (kc 10, retak, φ 0,70 kondisi B, 17.3.3). Rangka baja ringan oleh pemasok (SNI baja "
        "ringan belum ada di acuan/).",
        "Sambungan kolom lantai menyusul (LT4 → LT5, tahap 2): tulangan kolom menara disambung dengan sambungan "
        "mekanis Tipe 2 (18.2.7.1(b) hal. 367; boleh di mana saja) atau sambungan lewatan kelas B di setengah tinggi "
        "tengah kolom LT5 (18.7.4.3) dengan stek kolom LT5 dicor di tahap 1. Rinci di gambar 4.10.",
        "Cek silang: T-80 concreteproperties vs rumus sendiri (Mn kotak inti lif); T-81 tangga rumus sendiri vs "
        "PyNite; T-82 rumus Excel = Python (dihitung ulang di Excel).",
        "Sel hijau berisi rumus atau hasil AI. Status: " + STATUS + ".",
    ])], rata=list("cl"))

    k = lb.kol
    # ---- gaya
    lb = Lembar(wb.create_sheet("Gaya Dinding"), 2, "Gaya terfaktor dinding inti per kelompok (K1 ∪ K2)",
                [10, 9, 30, 11, 11, 12, 12, 11, 11, 11])
    lb.catatan(LABEL + " Ujung bawah dan atas segmen, semua kombinasi. Pu tekan positif; Pu min pada kombinasi gempa. "
               "Mux terhadap sumbu X (goyangan Y), Muy terhadap Y (goyangan X). Tu torsi inti. Penentu = rasio P-M "
               "terbesar (lembar Cek P-M).")
    rows = []
    for x in kel:
        fs = [r["gaya"][kk] for kk in x["anggota"]]
        rows.append([x["kelompok"], x["lv"], ", ".join(kk[0].replace("Inti lif ", "Lif ") for kk in x["anggota"]),
                     round(max(float(f["F"][..., 0].max()) for f in fs), 1),
                     round(min(float(f["F"][f["gempa"]][..., 0].min()) for f in fs), 1),
                     round(max(float(np.abs(f["F"][..., 1]).max()) for f in fs), 1),
                     round(max(float(np.abs(f["F"][..., 2]).max()) for f in fs), 1),
                     round(max(float(np.abs(f["F"][..., 3]).max()) for f in fs), 1),
                     round(max(float(np.abs(f["F"][..., 4]).max()) for f in fs), 1),
                     round(max(float(np.abs(f["F"][..., 5]).max()) for f in fs), 1)])
    lb.tabel(["Kelompok", "Tingkat", "Inti", "Pu maks (kN)", "Pu min (kN)", "|Mux| maks (kNm)", "|Muy| maks (kNm)",
              "|Vux| maks (kN)", "|Vuy| maks (kN)", "|Tu| maks (kNm)"], rows, rata=list("cclccccccc"),
             fmt=[None, None, None] + ["0.0"] * 7, fill_kolom={i: AI for i in range(3, 10)})

    # ---- penampang dan data diagram
    lb = Lembar(wb.create_sheet("Penampang"), 3, "Sifat penampang efektif inti (bruto, 18.10.5.2)",
                [10, 7, 9, 9, 8, 10, 10, 11, 12, 12, 9, 11])
    lb.catatan(LABEL + " Penampang dinding as dx × dy tebal 350, dinding selatan terpotong pintu. Sayap efektif dari "
               "muka badan min(setengah jarak badan; 0,25 hw), hw terkecil kelompok. A, I terhadap pusat inti; S = I/u "
               "maks. Tulangan: badan vertikal dua lapis, batas nb D di 4 sudut + 2 per pintu.")
    rows = []
    for x in kel:
        if x["lv"] != "LT2":
            continue
        p = x["batas"]["penampang"]
        rows.append([x["kelompok"], x["tipe"], DIM[x["tipe"]][0], DIM[x["tipe"]][1], round(x["hw"], 2),
                     round(p["X"]["Ag"], 4), round(p["Y"]["Ag"], 4), round(p["X"]["I"], 3), round(p["Y"]["I"], 3),
                     round(p["X"]["S"], 3), round(p["Y"]["S"], 3), len(PINTU[x["tipe"]])])
    lb.tabel(["Kelompok", "Tipe", "dx (m)", "dy (m)", "hw min (m)", "A arah X (m²)", "A arah Y (m²)",
              "I arah X (m⁴)", "I arah Y (m⁴)", "S arah X (m³)", "S arah Y (m³)", "Pintu"], rows,
             rata=list("cccccccccccc"), fmt=[None, None, "0.0", "0.0", "0.00", "0.0000", "0.0000", "0.000", "0.000",
                                              "0.000", "0.000", "0"], fill_kolom={i: AI for i in range(5, 11)})

    # data penampang untuk rumus diagram: semua kelompok LT2, arah X dan Y, tanda +
    lb = Lembar(wb.create_sheet("Data Penampang"), 4, "Persegi beton dan batang (penampang kritis LT2)",
                [12, 7, 9, 10, 10, 10, 11])
    lb.catatan(LABEL + " u = koordinat searah lentur dari pusat inti (m), serat tekan di u terbesar. Persegi: u0, u1, "
               "lebar w (m). Batang: u dan As (mm², dua lapis badan atau nb batang batas).")
    baris, rentang = [], {}
    dasar = [x for x in kel if x["lv"] == "LT2"]
    for x in dasar:
        for a in "XY":
            rects = persegi_u(x["tipe"], a, x["hw"])
            bars = batang_u(x["tipe"], a, x["hw"], batang(x["tipe"], *x["tul"]))
            for rr in rects:
                baris.append([x["kelompok"], a, "beton", round(float(rr[0]), 4), round(float(rr[1]), 4),
                              round(float(rr[2]), 4), None])
            for bb in bars:
                baris.append([x["kelompok"], a, "batang", round(float(bb[0]), 4), None, None, round(float(bb[1]), 2)])
    _, d0, _ = lb.tabel(["Kelompok", "Arah", "Jenis", "u0 / u (m)", "u1 (m)", "w (m)", "As (mm²)"], baris,
                        rata=list("ccccccc"), fmt=[None, None, None, "0.0000", "0.0000", "0.0000", "0.00"])
    rr = d0
    for x in dasar:
        for a in "XY":
            nr = len(persegi_u(x["tipe"], a, x["hw"]))
            nbar = len(batang_u(x["tipe"], a, x["hw"], batang(x["tipe"], *x["tul"])))
            rentang[(x["kelompok"], a)] = ((rr, rr + nr - 1), (rr + nr, rr + nr + nbar - 1))
            rr += nr + nbar

    lb = Lembar(wb.create_sheet("Diagram P-M"), 5, "Titik diagram interaksi nominal penampang kritis (tanda +)",
                [10, 6, 9, 9, 9, 12, 12, 9, 8, 12, 12])
    lb.catatan(LABEL + " U = u maks (serat tekan); a = min(β1 c; kedalaman); beton tiap persegi 0,85 fc' w × "
               "maks(0; u1 - maks(u0; U - a)), lengan di tengah bagian tertekan; fs = Es 0,003 (c - (U - u))/c dibatasi "
               "±fy, dikurangi 0,85 fc' bila u >= U - a. Pn = ΣF, Mn = ΣF u terhadap pusat inti; εt dari batang terjauh; "
               "φ 0,65-0,90. Rumus SUMPRODUCT membaca lembar Data Penampang (min/maks ditulis (a+b∓|a-b|)/2).")
    baris = []
    for x in dasar:
        for a in "XY":
            rects = persegi_u(x["tipe"], a, x["hw"])
            dalam = float(rects[:, 1].max() - rects[:, 0].min())
            for cr in C_RASIO:
                baris.append([x["kelompok"], a, round(float(rects[:, 1].max()), 4), round(dalam, 4),
                              round(cr * dalam, 4)] + [None] * 6)
    _, g0, _ = lb.tabel(["Kelompok", "Arah", "U (m)", "Kedalaman (m)", "c (m)", "Pn (kN)", "Mn (kNm)", "εt", "φ",
                         "φPn (kN)", "φMn (kNm)"], baris, rata=list("ccccccccccc"),
                        fmt=[None, None, "0.0000", "0.0000", "0.0000", "0.0", "0.0", "0.00000", "0.000", "0.0", "0.0"],
                        fill_kolom={i: AI for i in range(5, 11)})
    dp = "'Data Penampang'!"
    rr = g0
    for x in dasar:
        for a in "XY":
            (r0, r1), (b0, b1) = rentang[(x["kelompok"], a)]
            u0, u1, w = (f"{dp}${k(3)}${r0}:${k(3)}${r1}", f"{dp}${k(4)}${r0}:${k(4)}${r1}",
                         f"{dp}${k(5)}${r0}:${k(5)}${r1}")
            ub, ab = f"{dp}${k(3)}${b0}:${k(3)}${b1}", f"{dp}${k(6)}${b0}:${k(6)}${b1}"
            for _ in C_RASIO:
                U, D, C = f"{k(2)}{rr}", f"{k(3)}{rr}", f"{k(4)}{rr}"
                A = f"(({BETA1}*{C}+{D}-ABS({BETA1}*{C}-{D}))/2)"          # min(β1 c, kedalaman)
                L_ = f"({U}-{A})"
                lo = f"(({u0}+{L_}+ABS({u0}-{L_}))/2)"                       # maks(u0, U - a)
                ov = f"(({u1}-{lo})+ABS({u1}-{lo}))/2"                       # maks(0, u1 - lo)
                eps = f"{ES}*0.003*({C}-({U}-{ub}))/{C}"
                fs = f"((ABS({eps}+{FY})-ABS({eps}-{FY}))/2-0.85*{FC}*({ub}>={L_}))"
                lb.ws[f"{k(5)}{rr}"] = (f"=0.85*{FC}*1000*SUMPRODUCT({w},{ov})+SUMPRODUCT({ab},{fs})/1000")
                lb.ws[f"{k(6)}{rr}"] = (f"=0.85*{FC}*1000*SUMPRODUCT({w},{ov},({u1}+{lo})/2)"
                                        f"+SUMPRODUCT({ab},{fs},{ub})/1000")
                lb.ws[f"{k(7)}{rr}"] = f"=0.003*({U}-MIN({ub})-{C})/{C}"
                lb.ws[f"{k(8)}{rr}"] = f"=MIN(0.9,MAX(0.65,0.65+0.25*({k(7)}{rr}-{EPS_TY})/(0.005-{EPS_TY})))"
                lb.ws[f"{k(9)}{rr}"] = f"={k(8)}{rr}*{k(5)}{rr}"
                lb.ws[f"{k(10)}{rr}"] = f"={k(8)}{rr}*{k(6)}{rr}"
                rr += 1

    # ---- cek P-M
    lb = Lembar(wb.create_sheet("Cek P-M"), 6, "Cek lentur-aksial dua arah (kombinasi penentu)",
                [10, 9, 22, 9, 8, 7, 8, 11, 11, 11, 11, 11, 9, 11])
    lb.catatan(LABEL + " Tulangan: badan vertikal dua lapis D @ s; batas nb D di tiap sudut dan sisi pintu. φMn,X dan "
               "φMn,Y pada Pu dari diagram rapat Python (yang terkecil dari dua arah tekan; titik Excel di lembar "
               "Diagram P-M). Rasio = Muy/φMn,X + Mux/φMn,Y <= 1.")
    _, c0, c1 = lb.tabel(["Kelompok", "Tingkat", "Penentu (inti)", "Badan D", "s (mm)", "nb", "D batas", "Pu (kN)",
                          "Mux (kNm)", "Muy (kNm)", "φMn,X (kNm)", "φMn,Y (kNm)", "Rasio", "Status"],
                         [[x["kelompok"], x["lv"], x["pm"]["kunci"][0].replace("Inti lif ", "Lif "), x["tul"][0],
                           x["tul"][1], x["tul"][2], x["tul"][3], round(x["pm"]["Pu"], 1), round(x["pm"]["Mux"], 1),
                           round(x["pm"]["Muy"], 1), round(x["pm"]["phiMnX"], 1), round(x["pm"]["phiMnY"], 1), None,
                           None] for x in kel], rata=list("cclccccccccccc"),
                         fmt=[None, None, None, "0", "0", "0", "0", "0.0", "0.0", "0.0", "0.0", "0.0", "0.000", None],
                         fill_kolom={i: AI for i in range(3, 14)})
    for rr in range(c0, c1 + 1):
        lb.ws[f"{k(12)}{rr}"] = f"={k(9)}{rr}/{k(10)}{rr}+{k(8)}{rr}/{k(11)}{rr}"
        lb.ws[f"{k(13)}{rr}"] = f'=IF({k(12)}{rr}<=1,"Memenuhi","Kurang")'

    # ---- geser
    lb = Lembar(wb.create_sheet("Geser Dinding"), 7, "Geser dinding badan per arah (18.10.4)",
                [10, 9, 6, 10, 8, 8, 9, 8, 7, 10, 10, 11, 7, 11, 8, 11, 12])
    lb.catatan(LABEL + " Acw = 0,35 × panjang bersih badan (dinding selatan dikurangi pintu). Vu dinding = |V|/2 + |T| "
               "d/(2 A0). ρt = 2 Ab/(t s). Vn = Acw (αc √fc' + ρt fy). V(Mn) = geser dinding saat Mn tercapai; φ = "
               "0,60 bila Vn < V(Mn) (21.2.4.1). Ve ACI 318-19 = 1,5 (0,9 + n/10) Vu (informasi, n tingkat 6).")
    rows = []
    for x in kel:
        for a in "XY":
            s = x["geser"][a]
            rows.append([x["kelompok"], x["lv"], a, round(s["Vu"], 1), round(s["hw_lw"], 2), None,
                         round(s["Acw"], 4), s["db"], s["s"], None, None, round(s["V_Mn"], 1), None, None, None, None,
                         None])
    _, s0, s1 = lb.tabel(["Kelompok", "Tingkat", "Arah", "Vu dinding (kN)", "hw/lw", "αc", "Acw (m²)", "D horiz",
                          "s (mm)", "ρt", "Vn (kN)", "V(Mn) (kN)", "φ", "φVn (kN)", "Rasio", "0,83√fc' Acw (kN)",
                          "Ve ACI 318-19 / φVn"], rows, rata=list("ccccccccccccccccc"),
                         fmt=[None, None, None, "0.0", "0.00", "0.000", "0.0000", "0", "0", "0.00000", "0.0", "0.0",
                              "0.00", "0.0", "0.000", "0.0", "0.00"], fill_kolom={i: AI for i in range(3, 17)})
    for rr in range(s0, s1 + 1):
        lb.ws[f"{k(5)}{rr}"] = f"=MIN(0.25,MAX(0.17,0.25-(0.25-0.17)*({k(4)}{rr}-1.5)/0.5))"
        lb.ws[f"{k(9)}{rr}"] = f"=2*PI()*{k(7)}{rr}^2/4/({T * 1000}*{k(8)}{rr})"
        lb.ws[f"{k(10)}{rr}"] = f"={k(6)}{rr}*({k(5)}{rr}*SQRT({FC})+{k(9)}{rr}*{FY})*1000"
        lb.ws[f"{k(12)}{rr}"] = f"=IF({k(10)}{rr}>={k(11)}{rr},0.75,0.6)"
        lb.ws[f"{k(13)}{rr}"] = f"={k(12)}{rr}*{k(10)}{rr}"
        lb.ws[f"{k(14)}{rr}"] = f"={k(3)}{rr}/{k(13)}{rr}"
        lb.ws[f"{k(15)}{rr}"] = f"=0.83*SQRT({FC})*{k(6)}{rr}*1000"
        lb.ws[f"{k(16)}{rr}"] = f"=MIN(1.5*(0.9+6/10),3)*{k(3)}{rr}/(0.75*{k(10)}{rr})"

    # ---- elemen batas
    lb = Lembar(wb.create_sheet("Elemen Batas"), 8, "Elemen batas: cara perpindahan (18.10.6.2) dan tegangan "
                "(18.10.6.3)", [22, 9, 10, 11, 11, 10, 11, 11, 10, 16, 10, 9, 26])
    lb.catatan(LABEL + f" δe = perpindahan puncak inti terbesar K1/K2 (ELF, eksentrisitas); δu = Cd δe/Ie = {tb.CD} δe/"
               f"{tb.IE}; δu/hw >= 0,005; c pada Pu maks gempa (nominal, dua arah tekan); c batas = lw/(600 × 1,5 "
               "δu/hw). Berlaku hanya bila hw/lw >= 2 (selain itu cara tegangan).")
    rows = []
    for x in kel:
        if x["lv"] != "LT2":
            continue
        for p in x["batas"]["perpindahan"]:
            rows.append([p["inti"].replace("Inti lif ", "Lif "), p["arah"], round(p["hw"], 2), round(p["lw"], 2),
                         round(p["de"], 5), None, None, None, round(p["Pu"], 1), round(p["c"], 4), None, None, None])
    _, p0, p1 = lb.tabel(["Inti", "Arah", "hw (m)", "lw (m)", "δe (m)", "δu (m)", "δu/hw dipakai", "hw/lw",
                          "Pu (kN)", "c (m)", "c batas (m)", "c/lw", "Status"], rows, rata=list("lcccccccccccc"),
                         fmt=[None, None, "0.00", "0.00", "0.00000", "0.0000", "0.0000", "0.00", "0.0", "0.0000",
                              "0.000", "0.000", None], fill_kolom={i: AI for i in range(4, 13)})
    for rr in range(p0, p1 + 1):
        lb.ws[f"{k(5)}{rr}"] = f"={tb.CD}*{k(4)}{rr}/{tb.IE}"
        lb.ws[f"{k(6)}{rr}"] = f"=MAX({k(5)}{rr}/{k(2)}{rr},0.005)"
        lb.ws[f"{k(7)}{rr}"] = f"={k(2)}{rr}/{k(3)}{rr}"
        lb.ws[f"{k(10)}{rr}"] = f"={k(3)}{rr}/(600*1.5*{k(6)}{rr})"
        lb.ws[f"{k(11)}{rr}"] = f"={k(9)}{rr}/{k(3)}{rr}"
        lb.ws[f"{k(12)}{rr}"] = (f'=IF({k(7)}{rr}<2,"Tidak berlaku (cara tegangan)",IF({k(9)}{rr}>={k(10)}{rr},'
                                 f'"Perlu elemen batas khusus","Tidak perlu"))')
    lb.kosong()
    lb.catatan("Cara tegangan 18.10.6.3: σ = Pu/A + |Muy|/S arah X + |Mux|/S arah Y (sudut, penampang bruto efektif, "
               f"A terkecil dua arah). Perlu bila σ > 0,2 fc' = {0.2 * FC:.1f} MPa; berhenti bila < 0,15 fc' = "
               f"{0.15 * FC:.2f} MPa.".replace(".", ",", 2))
    rows = []
    for x in kel:
        b = x["batas"]
        p = b["sigma_pen"]
        rows.append([x["kelompok"], x["lv"], round(p["Pu"], 1), round(p["Mux"], 1), round(p["Muy"], 1),
                     round(b["Ag"], 4), round(b["penampang"]["X"]["S"], 4), round(b["penampang"]["Y"]["S"], 4), None,
                     None])
    _, q0, q1 = lb.tabel(["Kelompok", "Tingkat", "Pu (kN)", "Mux (kNm)", "Muy (kNm)", "A (m²)", "S arah X (m³)",
                          "S arah Y (m³)", "σ (MPa)", "Status"], rows, rata=list("cccccccccc"),
                         fmt=[None, None, "0.0", "0.0", "0.0", "0.0000", "0.0000", "0.0000", "0.00", None],
                         fill_kolom={i: AI for i in range(2, 10)}, beku=False)
    for rr in range(q0, q1 + 1):
        lb.ws[f"{k(8)}{rr}"] = f"=({k(2)}{rr}/{k(5)}{rr}+{k(4)}{rr}/{k(6)}{rr}+{k(3)}{rr}/{k(7)}{rr})/1000"
        lb.ws[f"{k(9)}{rr}"] = (f'=IF({k(8)}{rr}>{0.2 * FC},"Perlu SBE",IF({k(8)}{rr}<{0.15 * FC},'
                                f'"Tidak perlu","Di antara 0,15-0,2 fc"))')
    lb.kosong()
    lb.catatan("Zona batas tanpa elemen batas khusus (18.10.6.5): panjang zona = maks(c - 0,1 lw; c/2; 450 mm "
               "[Asumsi praktis]); ρ = nb As/A zona (sudut L: leg t + (leg - t) t; sisi pintu: leg t). Bila ρ > 2,8/fy: "
               "sengkang 18.7.5.2(a)-(e), s <= min(200; 8 db), zona sendi s <= min(150; 6 db).")
    rows = []
    for x in kel:
        b = x["batas"]
        rows.append([x["kelompok"], x["lv"], x["tul"][2], x["tul"][3], round(b["leg"], 3), None, None, None, None,
                     None, None])
    _, z0, z1 = lb.tabel(["Kelompok", "Tingkat", "nb", "D", "Leg (m)", "A sudut (m²)", "ρ sudut", "ρ sisi pintu",
                          "2,8/fy", "s sendi (mm)", "s luar (mm)"], rows, rata=list("ccccccccccc"),
                         fmt=[None, None, "0", "0", "0.000", "0.0000", "0.0000", "0.0000", "0.0000", "0", "0"],
                         fill_kolom={i: AI for i in range(4, 11)}, beku=False)
    for rr in range(z0, z1 + 1):
        lb.ws[f"{k(5)}{rr}"] = f"={k(4)}{rr}*{T}+({k(4)}{rr}-{T})*{T}"
        lb.ws[f"{k(6)}{rr}"] = f"={k(2)}{rr}*PI()*{k(3)}{rr}^2/4/({k(5)}{rr}*1000000)"
        lb.ws[f"{k(7)}{rr}"] = f"={k(2)}{rr}*PI()*{k(3)}{rr}^2/4/({k(4)}{rr}*{T}*1000000)"
        lb.ws[f"{k(8)}{rr}"] = f"=2.8/{FY}"
        lb.ws[f"{k(9)}{rr}"] = f'=IF(MAX({k(6)}{rr},{k(7)}{rr})>{k(8)}{rr},FLOOR(MIN(150,6*{k(3)}{rr}),25),"-")'
        lb.ws[f"{k(10)}{rr}"] = f'=IF(MAX({k(6)}{rr},{k(7)}{rr})>{k(8)}{rr},FLOOR(MIN(200,8*{k(3)}{rr}),25),"-")'

    # ---- balok kopel
    lb = Lembar(wb.create_sheet("Balok Kopel"), 9, "Balok kopel (ambang pintu inti, 18.10.7)",
                [10, 9, 9, 9, 10, 12, 7, 7, 7, 9, 11, 11, 18, 11, 11])
    lb.catatan(LABEL + " Vu = maks(qx |Vx| + qy |Vy| + qt |T|) × tinggi tingkat; qx = Q/Iy (dinding selatan badan), "
               "qy = Q/Ix (sayap), qt = 1/(2 A0). h ambang = tinggi tingkat - tinggi pintu. Acw = bw h. Diagonal bila "
               "ℓn/h < 2 dan Vu > 0,33 √fc' Acw; selain itu 18.10.7.3 sebagai balok (Vc = 0). As lentur = Mu/(0,9 fy "
               "0,9 d), Mu = Vu ℓn/2, >= 1,4/fy bw d.")
    rows = []
    for g, c in r["kopel"].items():
        rows.append([g, round(c["qx"], 5), round(c["qy"], 5), round(c["qt"], 5), round(c["Vu"], 1), teks_lv(c),
                     round(c["ln"], 2), round(c["h"], 2), None, None, None, None, None, None, None])
    _, b0, b1 = lb.tabel(["Kelompok", "qx (1/m)", "qy (1/m)", "qt (1/m²)", "Vu (kN)", "Penentu", "ℓn (m)", "h (m)",
                          "ℓn/h", "Acw (m²)", "0,33√fc' Acw (kN)", "0,83√fc' Acw (kN)", "Penulangan", "Mu (kNm)",
                          "As (mm²)"], rows, rata=list("ccccccccccccccc"),
                         fmt=[None, "0.00000", "0.00000", "0.00000", "0.0", None, "0.00", "0.00", "0.000", "0.0000",
                              "0.0", "0.0", None, "0.0", "0.0"], fill_kolom={i: AI for i in range(1, 15)})
    for rr in range(b0, b1 + 1):
        lb.ws[f"{k(8)}{rr}"] = f"={k(6)}{rr}/{k(7)}{rr}"
        lb.ws[f"{k(9)}{rr}"] = f"={T}*{k(7)}{rr}"
        lb.ws[f"{k(10)}{rr}"] = f"=0.33*SQRT({FC})*{k(9)}{rr}*1000"
        lb.ws[f"{k(11)}{rr}"] = f"=0.83*SQRT({FC})*{k(9)}{rr}*1000"
        lb.ws[f"{k(12)}{rr}"] = (f'=IF(AND({k(8)}{rr}<2,{k(4)}{rr}>{k(10)}{rr}),"Diagonal 18.10.7.4",'
                                 f'"Balok 18.10.7.3 (18.6)")')
        lb.ws[f"{k(13)}{rr}"] = f"={k(4)}{rr}*{k(6)}{rr}/2"
        lb.ws[f"{k(14)}{rr}"] = (f"=MAX({k(13)}{rr}/(0.9*{FY}*0.9*({k(7)}{rr}-0.075)*1000)*1000000,"
                                 f"1.4/{FY}*{T}*({k(7)}{rr}-0.075)*1000000)")

    # ---- tangga
    lb = Lembar(wb.create_sheet("Tangga"), 10, "Tangga pelat di inti tangga 4 × 6 m (per 1 m lebar)",
                [44, 14, 14, 44])
    lb.catatan(LABEL + " Bentang ℓ = 6,0 m (as dinding); ℓn = 5,65 m; L hitung = ℓn + t. Beban per proyeksi horizontal. "
               "Mu+ balok patah sendi-rol (integrasi; cek PyNite T-81). Mu- = wu ℓn²/24. fc' 30, D13, selimut 20 mm.")
    hs = list(r["tangga"])
    rows = []
    t1 = r["tangga"]
    item = [("Tinggi tingkat (m)", "h_tk", "0.00", "SNI 1727 / 3.6"), ("Jumlah tanjakan per lengan", "n_r", "0", ""),
            ("Tanjakan r (m)", "r", "0.000", "<= 0,175 [Asumsi]"), ("Injakan (m)", "going", "0.00", "[Asumsi]"),
            ("Panjang lengan (m)", "lf", "0.00", "(n - 1) × injakan"), ("Bordes per sisi (m)", "bordes", "0.00",
                                                                         "(ℓn - lengan)/2"),
            ("Sudut θ (°)", "theta", "0.0", ""), ("h min ℓ/24 (m)", "hmin", "0.000", "Tabel 7.3.1.1 hal. 120"),
            ("Tebal t (m)", "t", "0.00", "dibulatkan 10 mm"),
            ("qD lengan (kPa)", "qd_lengan", "0.00", "γ (t/cos θ + r/2) + 1,5"),
            ("qD bordes (kPa)", "qd_bordes", "0.00", "γ t + 1,5"), ("wu lengan (kN/m)", "wu_l", "0.00", "1,2D + 1,6L"),
            ("wu bordes (kN/m)", "wu_b", "0.00", "1,2D + 1,6L"), ("Ra (kN)", "Ra", "0.00", ""), ("Rb (kN)", "Rb", "0.00", ""),
            ("Mu+ (kNm/m)", "Mpos", "0.00", "balok patah sendi-rol"), ("Mu- (kNm/m)", "Mneg", "0.00", "wu ℓn²/24"),
            ("d (mm)", "d", "0.0", "t - 20 - 6,5"), ("As+ perlu (mm²/m)", "As_pos", "0.0", "dan >= 0,0018 b t"),
            ("As- perlu (mm²/m)", "As_neg", "0.0", ""), ("s tulangan bawah D13 (mm)", "s_pos", "0", "<= 3t, 450"),
            ("s tulangan atas D13 (mm)", "s_neg", "0", "<= 3t, 450"), ("Vu (kN/m)", "Vu", "0.00", ""),
            ("φVc (kN/m)", "phiVc", "0.00", "0,75 × 0,17 √fc' b d")]
    assert len(hs) == 2, "lembar Tangga disiapkan untuk dua tinggi tingkat"
    for nm, key, f, ket in item:
        rows.append([nm] + [round(float(t1[h][key]), 4) for h in hs] + [ket])
    head = ["Besaran"] + [f"h = {h:.1f} m".replace(".", ",") for h in hs] + ["Keterangan"]
    _, t0, _ = lb.tabel(head, rows, rata=list("lccl"), fill_kolom={1: AI, 2: AI})
    # rumus Excel untuk Mu- dan As+ (kolom tiap tinggi)
    idx = {key: t0 + i for i, (_, key, _, _) in enumerate(item)}
    for j in range(len(hs)):
        c_ = k(1 + j)
        ln_ = DIM["T"][1] - T
        lb.ws[f"{c_}{idx['hmin']}"] = f"={DIM['T'][1]}/24"
        lb.ws[f"{c_}{idx['wu_l']}"] = f"=1.2*{c_}{idx['qd_lengan']}+1.6*{L_TANGGA}"
        lb.ws[f"{c_}{idx['wu_b']}"] = f"=1.2*{c_}{idx['qd_bordes']}+1.6*{L_TANGGA}"
        lb.ws[f"{c_}{idx['Mneg']}"] = f"=MAX({c_}{idx['wu_l']},{c_}{idx['wu_b']})*{ln_}^2/24"
        lb.ws[f"{c_}{idx['d']}"] = f"={c_}{idx['t']}*1000-{SEL}-13/2"
        rn = f"{c_}{idx['Mpos']}*1000000/(0.9*1000*{c_}{idx['d']}^2)"
        lb.ws[f"{c_}{idx['As_pos']}"] = (f"=MAX(0.85*{FC_TANGGA}/{FY}*(1-SQRT(1-2*{rn}/(0.85*{FC_TANGGA})))*1000*"
                                         f"{c_}{idx['d']},0.0018*1000*{c_}{idx['t']}*1000)")
        lb.ws[f"{c_}{idx['phiVc']}"] = f"=0.75*0.17*SQRT({FC_TANGGA})*1000*{c_}{idx['d']}/1000"
        for i in range(len(item)):
            lb.ws[f"{c_}{t0 + i}"].number_format = item[i][2]

    # ---- atap sementara
    at = r["atap"]
    lb = Lembar(wb.create_sheet("Atap Sementara"), 11, "Atap sementara tahap 1 dan angkur ke kolom menara",
                [54, 14, 46])
    lb.catatan(LABEL + " Kolom dalam, tributari 8 × 8 m. Uplift 0,9D + 1,0W (SNI 1727 kombinasi 5). Angkur 4 M16 "
               "kelas 4.6, futa 400 MPa [Asumsi], hef 150 mm, jarak 150 mm di kolom 650.")
    item = [("Tinggi atap dari halaman h (m)", at["h"], "0.00", "+30,25 - 12,05"),
            ("qh (kPa)", at["qh"], "0.0000", "0,613 Kz Kzt Kd Ke V² (V 30 m/s [Asumsi 4.2])"),
            ("h/L (L = 24 m)", at["h_L"], "0.000", "angin sejajar sisi pendek menara"),
            ("Cp atap 0 s.d. h/2", at["Cp"], "0.000", "Gambar 27.3-1 interpolasi -0,9 (0,5) s.d. -1,3 (1,0)"),
            ("G", at["G"], "0.00", "Pasal 26.11 kaku"), ("GCpi (+)", at["GCpi"], "0.00", "Tabel 26.13-1 tertutup"),
            ("p = qh (G Cp - GCpi) (kPa)", at["p"], "0.000", "hisap"),
            ("D rangka + penutup (kPa)", at["D"], "0.00", "4.2 [Asumsi]"), ("Lr (kPa)", at["Lr"], "0.00", "4.2"),
            ("A tributari (m²)", at["Atrib"], "0.0", ""), ("Nu = (0,9D + p) A (kN)", at["Nu"], "0.00", "negatif = tarik"),
            ("Pu tekan maks (kN)", at["Pu_tekan"], "0.00", "1,2D + 1,6Lr"),
            ("Nsa per angkur (kN)", at["Nsa"], "0.00", "Ase futa (17.4.1.2), Ase 157 mm²"),
            ("φNsa kelompok (kN)", at["phiNsa"], "0.00", "0,75 × 4 × Nsa (17.3.3)"),
            ("Nb (kN)", at["Nb"], "0.00", "10 √fc' hef^1,5 (17.4.2.2)"), ("ca (mm)", at["ca"], "0.0", ">= 1,5 hef: ψed 1"),
            ("ANc (mm²)", at["ANc"], "0", "(s + 2 × 1,5 hef)²"), ("ANco (mm²)", at["ANco"], "0", "9 hef²"),
            ("Ncbg (kN)", at["Ncbg"], "0.00", "ANc/ANco Nb (ψ = 1)"), ("φNcbg (kN)", at["phiNcbg"], "0.00", "φ 0,70")]
    _, a0, _ = lb.tabel(["Besaran", "Nilai", "Keterangan"], [[n, round(float(v), 4), ket] for n, v, _, ket in item],
                        rata=list("lcl"), fill_kolom={1: AI})
    ai = {n: a0 + i for i, (n, _, _, _) in enumerate(item)}
    for i, (_, _, f, _) in enumerate(item):
        lb.ws[f"{k(1)}{a0 + i}"].number_format = f
    v = lambda n: f"{k(1)}{ai[n]}"   # noqa: E731
    lb.ws[v("p = qh (G Cp - GCpi) (kPa)")] = f"={v('qh (kPa)')}*({v('G')}*{v('Cp atap 0 s.d. h/2')}-{v('GCpi (+)')})"
    lb.ws[v("Nu = (0,9D + p) A (kN)")] = (f"=(0.9*{v('D rangka + penutup (kPa)')}+{v('p = qh (G Cp - GCpi) (kPa)')})*"
                                         f"{v('A tributari (m²)')}")
    lb.ws[v("φNsa kelompok (kN)")] = f"=0.75*4*{v('Nsa per angkur (kN)')}"
    lb.ws[v("Nb (kN)")] = f"=10*SQRT({FC})*150^1.5/1000"
    lb.ws[v("Ncbg (kN)")] = f"={v('ANc (mm²)')}/{v('ANco (mm²)')}*{v('Nb (kN)')}"
    lb.ws[v("φNcbg (kN)")] = f"=0.7*{v('Ncbg (kN)')}"

    # ---- ringkasan
    lb = Lembar(wb.create_sheet("Ringkasan Tulangan"), 12, "Ringkasan tulangan dinding inti",
                [10, 9, 18, 18, 12, 34, 10, 30, 10])
    lb.catatan(LABEL + " Badan dua lapis (vertikal dan horizontal). Batas: nb batang di tiap sudut dan tiap sisi pintu. "
               "Tulangan horizontal masuk 150 mm ke tepi dan dikait (18.10.6.5(b)); tulangan vertikal disalurkan untuk "
               "1,25 fy di zona leleh (18.10.2.3). Perkiraan baja kg/m³ = (ρl + ρt) 7.850 + batas.")
    rows = []
    for x in kel:
        b = x["batas"]
        tr = b["trans"]
        if b["perlu"]:
            tt = f"SBE: D13-{tr['s']} (Ash {tr['Ash_perlu']:.0f} mm²)"
        elif tr.get("perlu_ikat"):
            tt = f"18.10.6.5: D{tr['db']}-{tr['s']} zona sendi, -{tr['s_luar']} luar"
        else:
            tt = "tanpa sengkang pengekang (ρ <= 2,8/fy)"
        ag = b["penampang"]["X"]["Ag"]
        kg = (x["rho_l"] + x["horiz"][0]) * 7850 + (x["tul"][2] * luas(x["tul"][3]) * len(titik_batas(x["tipe"]))
                                                   / 1e6 * 7850) / ag
        rows.append([x["kelompok"], x["lv"], f"D{x['tul'][0]}-{x['tul'][1]} (2 lapis)",
                     f"D{x['horiz'][1]}-{x['horiz'][2]} (2 lapis)", f"{x['tul'][2]}D{x['tul'][3]}", tt,
                     round(kg, 0), catatan(x), "Memenuhi" if x["ok"] else "Periksa"])
    lb.tabel(["Kelompok", "Tingkat", "Vertikal badan", "Horizontal badan", "Batas", "Pengekang batas", "kg/m³",
              "Catatan", "Status"], rows, rata=list("ccccclclc"), fill_kolom={i: AI for i in range(2, 9)})
    lb.kosong()
    rows = []
    for g, c in r["kopel"].items():
        if c["diagonal"]:
            t_ = (f"diagonal {c['diag'][0]}D{c['diag'][1]} per kelompok (Avd perlu {c['Avd']:.0f} mm²), "
                  f"α {c['alpha']:.0f}°, kekang penuh 18.10.7.4(d)")
        else:
            t_ = (f"atas/bawah {c['batang'][0]}D{c['batang'][1]}, sengkang 2 kaki D13-{c['s']}; tulangan badan "
                  "dinding diteruskan")
        rows.append([g, f"{c['ln'] * 1000:.0f} × {c['h'] * 1000:.0f}", t_])
    lb.tabel(["Kelompok", "Ambang ℓn × h (mm)", "Penulangan balok kopel"], rows, rata=list("ccl"),
             fill_kolom={1: AI, 2: AI}, beku=False)

    # ---- cek silang
    cs = r["cp"]
    lb = Lembar(wb.create_sheet("Cek Silang"), 13, "Cek silang T-80 dan T-81", [8, 70, 14, 14, 11, 10, 12])
    lb.catatan(LABEL + f" T-80: {cs['kelompok']} lentur arah X (simetris) pada Pn = {cs['Pn']:.0f} kN; "
               "concreteproperties dengan persegi dinding dan batang satu per satu. T-81: Mu+ tangga balok patah, "
               "integrasi sendiri vs PyNite (sendi-rol, beban vertikal). T-82 (Excel = Python) dicatat di VERIFIKASI.")
    rows = [["T-80", "Mn kotak inti (kNm): rumus sendiri | concreteproperties", round(cs["Mn_sendiri"], 1),
             round(cs["Mn_cp"], 1), None, 0.05, None]]
    for h_, s in r["tangga"].items():
        rows.append(["T-81", f"Mu+ tangga h {h_:.1f} m (kNm/m): integrasi | PyNite".replace(".", ","),
                     round(s["Mpos"], 3), round(r["pynite"][h_], 3), None, 0.01, None])
    _, x0, x1 = lb.tabel(["No", "Besaran", "Cara 1", "Cara 2", "Selisih", "Batas", "Status"], rows,
                         rata=list("clccccc"), fmt=[None, None, "0.0", "0.0", "0.0%", "0.0%", None],
                         fill_kolom={4: AI, 6: AI}, beku=False)
    for rr in range(x0, x1 + 1):
        lb.ws[f"{k(4)}{rr}"] = f"={k(2)}{rr}/{k(3)}{rr}-1"
        lb.ws[f"{k(6)}{rr}"] = f'=IF(ABS({k(4)}{rr})<={k(5)}{rr},"Lolos","Tidak lolos")'

    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    if hitung_ulang:
        hitung_ulang_excel(keluar)
    return keluar


def teks_lv(c):
    return f"{c['kunci'][0].replace('Inti lif ', 'Lif ')} {c['kunci'][1]}"


def catatan(x):
    c = []
    if x["batas"]["perlu"]:
        c.append("elemen batas khusus")
    if x["rasio_pm"] > 1:
        c.append(f"P-M {x['rasio_pm']:.2f} > 1".replace(".", ","))
    for a, s in x["geser"].items():
        if s["rasio"] > 1:
            c.append(f"geser {a} {s['rasio']:.2f}".replace(".", ","))
        if s["phi"] < 0.75:
            c.append(f"φ geser {a} 0,60")
    return "; ".join(c) or "-"


def cek_excel(r, berkas=BERKAS):
    """T-82: selisih terbesar Excel (dihitung ulang) vs Python: titik diagram (Pn, Mn relatif %; φ), rasio P-M (%),
    φVn (kN), c batas (mm)."""
    import openpyxl
    from format_dokumen import baca_tabel
    wb = openpyxl.load_workbook(berkas, data_only=True)
    sel = []
    _, dd = baca_tabel(wb["Diagram P-M"], "Kelompok")
    i = 0
    for x in [x for x in r["kelompok"] if x["lv"] == "LT2"]:
        for a in "XY":
            rects = persegi_u(x["tipe"], a, x["hw"])
            bars = batang_u(x["tipe"], a, x["hw"], batang(x["tipe"], *x["tul"]))
            dalam = rects[:, 1].max() - rects[:, 0].min()
            for cr in C_RASIO:
                c = round(cr * dalam, 4)
                pn, mn, _, phi = titik_pm(c, rects, bars)
                # relatif (%): koordinat di lembar Data Penampang dibulatkan 0,1 mm
                sel += [abs(float(dd[i][5]) - pn[0]) / max(abs(pn[0]), 1.0) * 100,
                        abs(float(dd[i][6]) - mn[0]) / max(abs(mn[0]), 1.0) * 100, abs(float(dd[i][8]) - phi[0])]
                i += 1
    _, dp = baca_tabel(wb["Cek P-M"], "Kelompok")
    _, dg = baca_tabel(wb["Geser Dinding"], "Kelompok")
    j = 0
    for n, x in enumerate(r["kelompok"]):
        sel.append(abs(float(dp[n][12]) - x["pm"]["rasio"]) * 100)
        for a in "XY":
            sel.append(abs(float(dg[j][13]) - x["geser"][a]["phiVn"]))
            j += 1
    _, de = baca_tabel(wb["Elemen Batas"], "Inti")
    pp = [p for x in r["kelompok"] if x["lv"] == "LT2" for p in x["batas"]["perpindahan"]]
    for n, p in enumerate(pp):
        sel.append(abs(float(de[n][10]) - p["c_lim"]) * 1000)              # mm
    return max(sel)


def cetak(r):
    for x in r["kelompok"]:
        b = x["batas"]
        gx, gy = x["geser"]["X"], x["geser"]["Y"]
        pp = " ".join(f"{p['inti'][:10]}{p['arah']} c {p['c']:.2f}/{p['c_lim']:.2f}{'*' if p['berlaku'] else ''}"
                      for p in b["perpindahan"])
        print(f"{x['kelompok']:5s} {x['lv']:4s} tul {x['tul']} PM {x['rasio_pm']:.2f} | VX {gx['Vu']:.0f}/{gx['phiVn']:.0f}"
              f" φ{gx['phi']} {gx['db']}-{gx['s']} | VY {gy['Vu']:.0f}/{gy['phiVn']:.0f} φ{gy['phi']} | σ {b['sigma']:.2f}"
              f" perlu {b['perlu']} ρbatas {max(b['rho_sudut'], b['rho_kusen']):.4f} {pp}")
    for g, c in r["kopel"].items():
        print(g, {kk: (round(v, 3) if isinstance(v, float) else v) for kk, v in c.items() if kk != "kunci"})
    for h, s in r["tangga"].items():
        print("tangga", h, "t", s["t"], "M+", round(s["Mpos"], 2), "PyNite", round(r["pynite"][h], 2), "M-",
              round(s["Mneg"], 2), "s", s["s_pos"], s["s_neg"], "qd rata", round(s["qd_rata"], 2))
    print("atap", {kk: round(v, 3) if isinstance(v, float) else v for kk, v in r["atap"].items()})
    print("T-80", r["cp"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    import time
    t0 = time.time()
    r = rancang()
    cetak(r)
    if "--excel" in sys.argv:
        print(buat_excel(r), "selisih Excel-Python maks", cek_excel(r))
    print(f"waktu {time.time() - t0:.0f} s")
