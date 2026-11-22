"""Tahap 5 langkah 5.5: desain pit lift (angkat/uplift, kedap, struktur, tumpuan, jarak ke sloof).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (21 Nov 2026); draf, menunggu persetujuan Defsa.
Kunci jawaban tidak dibuka. Data lift dari `04 Struktur Atas/Data Owner/Data Beban MEP Rinci.xlsx` (lembar Lift) lewat `tahap5_telaah`,
muka air Q50/Q100 dari 3.3, sloof dari `tahap5_sloof` (5.4), pelat dari `tahap5_pelat_lt1` (5.3).

Acuan (halaman = nomor halaman PDF di acuan/privat, diverifikasi dengan pypdf 21 Nov 2026):
- SNI 8460:2017 Pasal 9.3.4 (hal 197): FK buoyancy >= 1,5 (beban mati + tahanan izin pengangkuran, pasal 10) atau >= 1,1 (beban mati
  minimum saja); muka air tertinggi dari semua kasus ekstrem (banjir). Pasal 12 (hal 279) butir b: lantai besmen didesain terhadap uplift.
- SNI 2847:2019 Pasal 5.3.7-5.3.8 (hal 109-110): F dan H (1,6 menambah; 0,9 melawan); Tabel 19.3.2.1 (hal 464): kelas paparan S dan W
  (hanya W0 dan W1; kelas W2 belum ada di acuan); Tabel 20.6.1.3.1 (hal 482): selimut; Tabel 11.6.1 (hal 255): tulangan minimum dinding;
  Pasal 24.3.2 (hal 573) dan 24.3.5 (hal 574): kontrol spasi, komponen didesain kedap air; Pasal 22.5.5.1 (hal 507): Vc; Pasal 22.6.4.1
  (hal 518) dan Tabel 22.6.5.2 (hal 521): geser pons; Tabel 21.2.1 (hal 491): phi; Tabel 8.6.1.1 (hal 145, via 5.3): As min pelat.
Hal yang tidak ada di acuan ditulis persis "belum ada di acuan".
"""
from __future__ import annotations

import functools
import math
import sys
from pathlib import Path

import numpy as np
import openpyxl
from openpyxl.styles import PatternFill

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_balok as tbk  # noqa: E402
import tahap4_beban as tb  # noqa: E402
import tahap5_mri as mri  # noqa: E402
import tahap5_pelat_lt1 as pl  # noqa: E402
import tahap5_sloof as sl  # noqa: E402
import tahap5_tangki as tn  # noqa: E402
import tahap5_telaah as ts  # noqa: E402
from tahap5_mri import R, idn  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "05 Struktur Tengah"
BERKAS = KELUAR / "5.5 Desain Pit Lift.xlsx"
LABEL = mri.LABEL
STATUS = "disetujui Defsa 21 Nov 2026"
LABEL_AI = f"DIISI AI ATAS PERMINTAAN DEFSA (21 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."
KEPUTUSAN = ("21 Nov 2026: (1) **Opsi A angkat**: pelat dasar pit L-1..4 **0,45 m** (t_min 0,439; FK kotak utuh Q100 "
             "584,2 / 648,3 = 1,11 >= 1,1, SNI 8460:2017 9.3.4), L-5..6 dan L-7 tetap 0,40 (FK 1,42 / 1,37); tulangan bawah "
             "L-1..4 D13-100 dari t 0,40 dipertahankan (konservatif). (2) **Tumpuan L-7: 2 balok penggantung 400 x 800** bentang "
             "8 m ke sloof (5 D29), tanpa tiang sendiri. (3) **Lapisan kedap: aditif kristalin** di beton pit (w/cm <= 0,45, "
             "fc' 35) plus waterstop di dua sambungan; spesifikasi produk belum ada di acuan (dilengkapi di RKS Tahap 7).")

GW, GC = ts.GAMMA_W, tb.GAMMA_C
FC, FY = pl.FC, pl.FY
Q50, Q100, TEKAN = ts.Q50, ts.Q100, ts.TEKAN_DESAIN
ATAS = 12.60                  # m, sisi bawah pelat LT1 (+12,85 - 0,25); dinding pit berhenti di sini
LT1 = 12.85
TW, TS0 = 0.30, 0.40          # m, dinding dan pelat dasar awal [Asumsi 5.5]
FK_M, FK_A = 1.1, 1.5         # SNI 8460:2017 9.3.4 b dan a
SEL_TANAH, SEL_DALAM = 0.050, 0.040      # m [Asumsi 5.5; Tabel 20.6.1.3.1: 40 + 10 asam, tulangan <= D16]
GAMMA_T, GAMMA_SAT, K0 = 18.0, 19.0, 0.50    # urugan phi' 30 derajat [Asumsi 5.5]
FAKTOR_H = 1.6                # SNI 2847:2019 5.3.8
PHI_V = 0.75
LANDASAN = 0.30               # m, pelat landasan buffer 300 x 300 [Asumsi]
SUMP = (0.60, 0.60, 0.50)     # m [Asumsi]
Q_TIANG = tn.Q_IZIN_TIANG     # 911 kN, tiang bor Ø800 (3.7)
TOL = {"a": 0.5, "b": 5.0, "c": 1.0, "d": 0.5}   # % (T-94), ditetapkan sebelum membandingkan
KODE = ("L-1..4", "L-5..6", "L-7")
SUF = {"L-1..4": "14", "L-5..6": "56", "L-7": "7"}
# bay (lebar x panjang tiap shaft, jumlah arah x, y), pusat tapak [Asumsi: pit L-1..4 di tengah inti x 50-58, y 35-43]
GEOM = {"L-1..4": {"bay": (2.6, 3.1), "n": (2, 2), "pusat": (54.0, 39.0), "nama": "lift brankar 4 shaft (2 × 2 @ 2,6 × 3,1)"},
        "L-5..6": {"bay": (2.3, 2.3), "n": (2, 1), "pusat": (55.5, 44.75), "nama": "lift penumpang 2 shaft @ 2,3 × 2,3"},
        "L-7": {"bay": (2.8, 3.4), "n": (1, 1), "pusat": (39.4, 31.7), "nama": "lift servis dan jenazah 2,8 × 3,4"}}
INTI = (50.0, 58.0, 35.0, 43.0)
DINDING_INTI = tb.DINDING_T


# ------------------------------------------------------------------ data
@functools.lru_cache(maxsize=1)
def data_lift():
    wb = openpyxl.load_workbook(ts.MEP, data_only=True)
    out = {}
    for r in ts.baca_baris(wb, "Lift"):
        k = r["Kode"]
        g = GEOM[k]
        bx, by = g["bay"]
        nx, ny = g["n"]
        out[k] = {"kode": k, "a": bx * nx, "b": by * ny, "bay": g["bay"], "n": g["n"], "dasar": float(r["Elevasi dasar pit (m)"]),
                  "dalam": float(r["Kedalaman pit (m)"]), "p_kereta": float(r["Reaksi buffer kereta (kN)"]),
                  "p_imbang": float(r["Reaksi buffer bobot imbang (kN)"]), "jumlah": int(r["Jumlah"]), "pusat": g["pusat"], "nama": g["nama"],
                  "x": str(r["x shaft (m)"]), "y": str(r["y shaft (m)"])}
    return out


def luas(p, tw=TW):
    return (p["a"] + 2 * tw) * (p["b"] + 2 * tw), p["a"] * p["b"]


# ------------------------------------------------------------------ A. angkat
def angkat(p, t=TS0, muka=Q100, tw=TW):
    """U = gw (muka - bawah) A_luar (gaya angkat pada dasar pelat); W = beton pelat + dinding sampai +12,60 (beban mati minimum)."""
    ao, ai = luas(p, tw)
    bawah = p["dasar"] - t
    u = GW * max(0.0, muka - bawah)
    vw = (ao - ai) * (ATAS - p["dasar"])
    ws, ww = GC * t * ao, GC * vw
    return {"A_luar": ao, "A_dalam": ai, "bawah": bawah, "u": u, "U": u * ao, "V_dinding": vw, "W_pelat": ws, "W_dinding": ww, "W": ws + ww,
            "FK_utuh": (ws + ww) / (u * ao) if u > 0 else math.inf, "FK_lepas": ws / (u * ao) if u > 0 else math.inf}


def t_min_tertutup(p, fk=FK_M, tw=TW):
    """Tebal pelat (dasar pit tetap) agar W/U = fk: t = (fk gw Ao (muka - dasar) - gc Vw) / (gc Ao - fk gw Ao)."""
    ao, ai = luas(p, tw)
    vw = (ao - ai) * (ATAS - p["dasar"])
    return (fk * GW * ao * (Q100 - p["dasar"]) - GC * vw) / (GC * ao - fk * GW * ao)


def t_min_bisection(p, fk=FK_M, tw=TW):
    lo, hi = 0.05, 3.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if angkat(p, mid, tw=tw)["FK_utuh"] < fk:
            lo = mid
        else:
            hi = mid
    return hi


def t_lepas(p, fk=FK_M):
    return fk * GW * (Q100 - p["dasar"]) / (GC - fk * GW)


def bulat50(t):
    return math.ceil(t / 0.05 - 1e-9) * 0.05


def konstruksi(p, t=TS0):
    """Tahap konstruksi: hanya pelat dasar (dinding dan LT1 belum ada), muka air desain +11,20 (dewatering terkendali)."""
    a = angkat(p, t, muka=TEKAN)
    return {"FK": a["FK_lepas"], "u": a["u"], "U": a["U"], "W": a["W_pelat"]}


def paket_angkat(p):
    out = {"t": {k: angkat(p, TS0, m) for k, m in (("tekan", TEKAN), ("q50", Q50), ("q100", Q100))}}
    a = out["t"]["q100"]
    out["tmin"] = t_min_tertutup(p)
    out["tmin_bulat"] = bulat50(out["tmin"])
    out["tlepas"] = t_lepas(p)
    out["A"] = angkat(p, max(out["tmin_bulat"], TS0))
    out["R"] = FK_A * a["U"] - a["W"]
    out["as_stek"] = FAKTOR_H * max(out["R"], 0.0) * 1000 / (0.9 * FY)
    out["lokal"] = konstruksi(p)
    out["tahap_konstruksi"] = out["lokal"]
    # volume tambahan Opsi A (beton dan galian) terhadap t awal
    out["dV_A"] = (out["A"]["bawah"] != a["bawah"]) * (max(out["tmin_bulat"], TS0) - TS0) * a["A_luar"]
    out["R_fk_a"] = out["R"]
    return out


# ------------------------------------------------------------------ pelat: Navier persegi panjang dan PyNite
def navier_pelat(a, b, patch, nu=0.2, n=150, langkah=0.1):
    """Momen maksimum (Mx, My; kNm/m) pelat a x b tumpuan sederhana, beban kumpulan patch [(P kN, u, v, xi, eta)]; deret Navier."""
    m = np.arange(1, n + 1)[:, None]
    k = np.arange(1, n + 1)[None, :]
    q = 0.0
    for (P, u, v, xi, eta) in patch:
        sm = np.sin(m * np.pi * u / (2 * a)) / (m * np.pi * u / (2 * a))
        sk = np.sin(k * np.pi * v / (2 * b)) / (k * np.pi * v / (2 * b))
        q = q + 4 * P / (a * b) * np.sin(m * np.pi * xi / a) * np.sin(k * np.pi * eta / b) * sm * sk
    den = np.pi ** 2 * ((m / a) ** 2 + (k / b) ** 2) ** 2
    cx = q * ((m / a) ** 2 + nu * (k / b) ** 2) / den
    cy = q * ((k / b) ** 2 + nu * (m / a) ** 2) / den
    xs = np.arange(langkah, a - langkah / 2, langkah)
    ys = np.arange(langkah, b - langkah / 2, langkah)
    sx = np.sin(np.arange(1, n + 1)[:, None] * np.pi * xs[None, :] / a)
    sy = np.sin(np.arange(1, n + 1)[:, None] * np.pi * ys[None, :] / b)
    mx, my = sx.T @ cx @ sy, sx.T @ cy @ sy
    return float(mx.max()), float(my.max())


def navier_tengah(a, b, q, nu=0.2, n=99):
    """Momen di pusat pelat beban merata q (kPa), deret Navier (m, k ganjil)."""
    mx = my = 0.0
    for mm in range(1, n + 1, 2):
        for kk in range(1, n + 1, 2):
            qq = 16 * q / (np.pi ** 2 * mm * kk)
            den = np.pi ** 4 * ((mm / a) ** 2 + (kk / b) ** 2) ** 2
            s = np.sin(mm * np.pi / 2) * np.sin(kk * np.pi / 2)
            mx += qq * np.pi ** 2 * ((mm / a) ** 2 + nu * (kk / b) ** 2) / den * s
            my += qq * np.pi ** 2 * ((kk / b) ** 2 + nu * (mm / a) ** 2) / den * s
    return float(mx), float(my)


def pynite_pelat(a, b, h, q, mesh=0.25, nu=0.2):
    """Pelat a x b, tumpuan sederhana keliling, tekanan merata q kPa; (Mx, My) rata-rata empat elemen tengah."""
    from Pynite import FEModel3D
    e = pl.EC * 1000.0
    m = FEModel3D()
    m.add_material("c", e, e / (2 * (1 + nu)), nu, 23.6)
    nx, ny = int(round(a / mesh)), int(round(b / mesh))
    for i in range(nx + 1):
        for j in range(ny + 1):
            m.add_node(f"N{i}_{j}", i * mesh, j * mesh, 0.0)
    for i in range(nx):
        for j in range(ny):
            m.add_quad(f"Q{i}_{j}", f"N{i}_{j}", f"N{i + 1}_{j}", f"N{i + 1}_{j + 1}", f"N{i}_{j + 1}", h, "c")
            m.add_quad_surface_pressure(f"Q{i}_{j}", -q, case="D")
    for i in range(nx + 1):
        for j in range(ny + 1):
            m.def_support(f"N{i}_{j}", True, True, i in (0, nx) or j in (0, ny), False, False, True)
    m.add_load_combo("U", {"D": 1.0})
    m.analyze_linear(check_statics=False, sparse=True)
    c = [(nx // 2 - 1, ny // 2 - 1), (nx // 2, ny // 2 - 1), (nx // 2 - 1, ny // 2), (nx // 2, ny // 2)]
    mm = [m.quads[f"Q{i}_{j}"].moment(0.0, 0.0, combo_name="U") for i, j in c]
    return float(np.mean([abs(float(x[0][0])) for x in mm])), float(np.mean([abs(float(x[1][0])) for x in mm]))


def pilih(mu, h, sel, smaks, db_list=(13, 16, 19)):
    """Tulangan pelat per meter: D terkecil dan spasi terbesar (kelipatan 25 mm, <= smaks) yang cukup untuk Mu (kNm/m) dan As min 0,0018 b h."""
    as_min = 0.0018 * 1000 * h * 1000
    for db in db_list:
        d = h - sel - 1.5 * db / 1000
        perlu = max(pl.as_perlu(mu, d), as_min)
        ab = math.pi * db ** 2 / 4
        for s in (300, 275, 250, 225, 200, 175, 150, 125, 100, 75):
            if s > smaks:
                continue
            ada = 1000 * ab / s
            if ada >= perlu and pl.phimn(ada, d) >= mu:
                return {"db": db, "s": s, "as_ada": ada, "as_perlu": perlu, "as_min": as_min, "phimn": pl.phimn(ada, d), "d": d, "mu": mu, "ok": True,
                        "rasio": mu / pl.phimn(ada, d)}
    ada = 1000 * math.pi * db_list[-1] ** 2 / 4 / 75
    d = h - sel - 1.5 * db_list[-1] / 1000
    return {"db": db_list[-1], "s": 75, "as_ada": ada, "as_perlu": perlu, "as_min": as_min, "phimn": pl.phimn(ada, d), "d": d, "mu": mu, "ok": False,
            "rasio": mu / pl.phimn(ada, d)}


def smaks_retak(cc_mm):
    """Pasal 24.3.2: fs = 2/3 fy = 280 MPa: s <= min(380 (280/fs) - 2,5 cc; 300 (280/fs))."""
    fs = 2 / 3 * FY
    return min(380 * 280 / fs - 2.5 * cc_mm, 300 * 280 / fs)


def struktur_pelat(p, t=TS0):
    """Pelat dasar: naik (1,6 u - 0,9 gc t, tulangan atas) dan turun (1,2 gc t + 1,6 buffer di patch 300 x 300, tulangan bawah)."""
    a, b = p["a"] + TW, p["b"] + TW        # bentang sumbu ke sumbu dinding
    a_ = paket_u(p, t)
    qn = FAKTOR_H * a_["u"] - 0.9 * GC * t
    mxn, myn = navier_tengah(a, b, qn)
    bx, by = p["bay"]
    nx, ny = p["n"]
    pk, pi_ = p["p_kereta"], p["p_imbang"]
    patch = [(1.6 * (pk + pi_), LANDASAN, LANDASAN, TW / 2 + (i + 0.5) * bx, TW / 2 + (j + 0.5) * by) for i in range(nx) for j in range(ny)]
    qd = 1.2 * GC * t
    mxd0, myd0 = navier_tengah(a, b, qd)
    mxp, myp = navier_pelat(a, b, patch)
    mxd, myd = navier_pelat(a, b, patch + [(qd * a * b, a, b, a / 2, b / 2)])
    atas = pilih(max(mxn, myn), t, SEL_DALAM, smaks_retak(SEL_DALAM * 1000))
    bawah = pilih(max(mxd, myd), t, SEL_TANAH, smaks_retak(SEL_TANAH * 1000))
    dd = bawah["d"]
    # geser satu arah pelat naik (22.5.5.1) pada muka dinding: Vu = qn (a/2 - d), a = bentang pendek
    dn = atas["d"]
    vu1 = qn * (min(a, b) / 2 - dn)
    phivc = PHI_V * 0.17 * math.sqrt(FC) * 1000 * dn
    # pons buffer (22.6.4.1, Tabel 22.6.5.2)
    b0 = 4 * (LANDASAN + dd)
    vc = mri.vc_koef(b0, dd, 1.0, 40.0) * math.sqrt(FC) * b0 * dd * 1000      # kN
    phivc_pons = PHI_V * vc
    vu_pons = 1.6 * (pk + pi_)
    tumpu = 1.6 * (pk + pi_) / LANDASAN ** 2
    phi_tumpu = 0.65 * 0.85 * FC * 1000
    return {"a": a, "b": b, "u": a_["u"], "qn": qn, "Mx_n": mxn, "My_n": myn, "qd": qd, "Mx_d0": mxd0, "My_d0": myd0, "Mx_p": mxp, "My_p": myp,
            "Mx_d": mxd, "My_d": myd, "atas": atas, "bawah": bawah, "Vu1": vu1, "phiVc1": phivc, "ok_geser": vu1 <= phivc, "b0": b0, "phiVc_pons": phivc_pons,
            "Vu_pons": vu_pons, "r_pons": vu_pons / phivc_pons, "tumpu": tumpu, "phi_tumpu": phi_tumpu, "r_tumpu": tumpu / phi_tumpu,
            "n_patch": len(patch), "P_patch": 1.6 * (pk + pi_), "smaks_atas": smaks_retak(SEL_DALAM * 1000), "smaks_bawah": smaks_retak(SEL_TANAH * 1000)}


def paket_u(p, t=TS0):
    return angkat(p, t, Q100)


# ------------------------------------------------------------------ dinding: tekanan tanah + air, jepit-sendi
def tekanan(e):
    """Tekanan horizontal tidak terfaktor (kPa) di elevasi e: K0 sigma_v' + gw (Q100 - e); tanah dari +12,60, air +12,31."""
    sv = GAMMA_T * (ATAS - max(e, Q100)) + ((GAMMA_SAT - GW) * (Q100 - e) if e < Q100 else 0.0)
    return K0 * sv + (GW * (Q100 - e) if e < Q100 else 0.0)


def _int(y, x):
    return float(np.sum((y[1:] + y[:-1]) / 2 * np.diff(x)))


def dinding(p, n=4001):
    """Dinding setinggi H = 12,60 - dasar; jepit di pelat (s = 0), sendi di pelat LT1 (s = H). Beban 1,6 H. Momen jepit dan reaksi sendi
    dari fungsi Green balok jepit-sendi; lapangan dari statika; pembanding kantilever (LT1 tidak menahan)."""
    H = ATAS - p["dasar"]
    s = np.linspace(0.0, H, n)
    pr = FAKTOR_H * np.array([tekanan(p["dasar"] + x) for x in s])
    mb = _int(pr * (H - s) * s * (2 * H - s) / (2 * H ** 2), s)
    rt = _int(pr * s ** 2 * (3 * H - s) / (2 * H ** 3), s)
    tot = _int(pr, s)
    f1 = np.concatenate([[0.0], np.cumsum((pr * s)[1:] + (pr * s)[:-1]) / 2 * np.diff(s)])
    f0 = np.concatenate([[0.0], np.cumsum(pr[1:] + pr[:-1]) / 2 * np.diff(s)])
    g1, g0 = f1[-1] - f1, f0[-1] - f0
    m = rt * (H - s) - (g1 - s * g0)         # sagging positif; m[0] = -mb
    m_pos = float(m.max())
    kant = _int(pr * s, s)
    t = TW
    luar = pilih_dinding(mb, t, SEL_TANAH)
    dalam = pilih_dinding(max(m_pos, 0.0), t, SEL_DALAM)
    vbase = tot - rt
    dv = t - SEL_TANAH - 0.008
    phivc = PHI_V * 0.17 * math.sqrt(FC) * 1000 * dv
    hor = pilih_horizontal(t)
    return {"H": H, "M_jepit": mb, "R_sendi": rt, "V_dasar": vbase, "M_lapangan": m_pos, "M_cek": float(m[0]), "M_kantilever": kant, "total": tot,
            "p_dasar": float(pr[0] / FAKTOR_H), "p_atas": float(pr[-1] / FAKTOR_H), "luar": luar, "dalam": dalam, "hor": hor, "phiVc": phivc,
            "ok_geser": vbase <= phivc, "s": s, "pr": pr}


def pilih_dinding(mu, t, sel):
    """Tulangan vertikal satu muka dinding: lentur dan minimum setengah dari rho_l 0,0012 (<= D16, Tabel 11.6.1) bila ada dua muka."""
    smaks = min(smaks_retak(sel * 1000), 450.0)
    rho_min = 0.0012 * 1000 * t * 1000 / 2
    for db in (13, 16):
        d = t - sel - db / 2000
        perlu = max(pl.as_perlu(mu, d), rho_min)
        ab = math.pi * db ** 2 / 4
        for s in (300, 275, 250, 225, 200, 175, 150, 125, 100):
            if s > smaks:
                continue
            ada = 1000 * ab / s
            if ada >= perlu and pl.phimn(ada, d) >= mu:
                return {"db": db, "s": s, "as_ada": ada, "as_perlu": perlu, "as_min": rho_min, "d": d, "phimn": pl.phimn(ada, d), "mu": mu, "rasio": mu / pl.phimn(ada, d),
                        "ok": True}
    return {"db": 16, "s": 100, "as_ada": 1000 * math.pi * 16 ** 2 / 4 / 100, "as_perlu": perlu, "as_min": rho_min, "d": d, "phimn": 0.0, "mu": mu, "rasio": 9.9, "ok": False}


def pilih_horizontal(t):
    """Tulangan horizontal satu muka: rho_t 0,0020 (<= D16, fy >= 420, Tabel 11.6.1) dibagi dua muka."""
    perlu = 0.0020 * 1000 * t * 1000 / 2
    smaks = min(smaks_retak(SEL_TANAH * 1000), 450.0)
    for db in (13, 16):
        ab = math.pi * db ** 2 / 4
        for s in (300, 275, 250, 225, 200, 175, 150, 125, 100):
            if s <= smaks and 1000 * ab / s >= perlu:
                return {"db": db, "s": s, "as_ada": 1000 * ab / s, "as_perlu": perlu}
    return {"db": 16, "s": 100, "as_ada": 1000 * math.pi * 16 ** 2 / 4 / 100, "as_perlu": perlu}


def pynite_dinding(p):
    """Momen jepit PyNite: balok vertikal jepit di s = 0 dan sendi di s = H; beban trapesium terfaktor (dua segmen, patah di muka air)."""
    from Pynite import FEModel3D
    H = ATAS - p["dasar"]
    sw = min(max(Q100 - p["dasar"], 0.0), H)
    e = 4700 * math.sqrt(FC) * 1000
    m = FEModel3D()
    m.add_material("c", e, e / 2.4, 0.2, 24.0)
    m.add_section("s", 1.0 * TW, TW * 1.0 ** 3 / 12, 1.0 * TW ** 3 / 12, 1e-3)
    m.add_node("A", 0, 0, 0)
    m.add_node("B", H, 0, 0)
    m.add_member("M", "A", "B", "c", "s")
    m.def_support("A", True, True, True, True, True, True)
    m.def_support("B", True, True, True, True, False, False)
    f = lambda z: FAKTOR_H * tekanan(p["dasar"] + z)   # noqa: E731
    m.add_member_dist_load("M", "Fy", f(0.0), f(sw), 0.0, sw, "D")
    m.add_member_dist_load("M", "Fy", f(sw), f(H), sw, H, "D")
    m.add_load_combo("U", {"D": 1.0})
    m.analyze_linear(check_statics=False)
    return abs(float(m.members["M"].moment("Mz", 0.0, "U")))


# ------------------------------------------------------------------ tumpuan gravitasi
def gravitasi(p):
    """Beban gravitasi total satu pit: berat beton pit + buffer (reaksi sudah termasuk faktor kejut pemasok) per lift; layan dan terfaktor."""
    a = angkat(p, TS0, Q100)
    pb = p["jumlah"] * (p["p_kereta"] + p["p_imbang"])
    return {"W": a["W"], "Pb": pb, "layan": a["W"] + pb, "Pu": 1.2 * a["W"] + 1.6 * pb, "n_tiang": max(2, math.ceil((a["W"] + pb) / Q_TIANG)),
            "n_tiang_1": math.ceil((a["W"] + pb) / Q_TIANG), "U_q100": a["U"], "net_banjir": a["W"] - a["U"]}


def balok_penggantung(p, bentang=8.0, n_balok=2, ukuran=((0.40, 0.80), (0.50, 0.90), (0.60, 1.00))):
    """L-7: dua balok penggantung sepanjang bentang antar sloof, beban Pu / 2 titik di tengah + berat sendiri; sederhana. Pilih ukuran terkecil dengan rho <= 0,025."""
    g = gravitasi(p)
    out = []
    for (b, h) in ukuran:
        ws = GC * b * h
        mu = (g["Pu"] / n_balok) * bentang / 4 + 1.2 * ws * bentang ** 2 / 8
        vu = (g["Pu"] / n_balok) / 2 + 1.2 * ws * bentang / 2
        ds = 0.013
        d = h - 0.040 - ds - 0.0145
        perlu = max(tbk.as_perlu(mu, b, d, fc=FC), tbk.as_min(b, d))
        n29 = max(2, math.ceil(perlu / sl.luas(29)))
        as_ada = n29 * sl.luas(29)
        rho = as_ada / (b * d * 1e6)
        phivs = PHI_V * (0.17 * math.sqrt(FC) * b * d * 1000)
        ok = math.isfinite(perlu) and rho <= 0.025
        # sengkang: Vs = Vu/phi - Vc, Av/s
        vs = max(vu / PHI_V - 0.17 * math.sqrt(FC) * b * d * 1000, 0.0)
        out.append({"b": b, "h": h, "Mu": mu, "Vu": vu, "d": d, "as_perlu": perlu, "n29": n29, "as_ada": as_ada, "rho": rho, "ok": ok,
                    "beton": n_balok * b * h * bentang, "baja_kg": n_balok * as_ada * 1e-6 * bentang * 7850 * 1.0, "Vs": vs,
                    "av_s": vs / (sl.FYT * 1000 * d) * 1000, "phiMn": tbk.mn(as_ada, b, d, fc=FC) * 0.9, "phiVc": phivs})
    pilih_ = next((x for x in out if x["ok"]), out[-1])
    return {"kandidat": out, "pilih": pilih_, "g": g}


def tiang_pilihan(p):
    g = gravitasi(p)
    cap = (1.6, 1.6, 0.8)          # [Asumsi 5.5] pile cap 2 tiang
    return {"n": g["n_tiang"], "rasio": g["layan"] / (g["n_tiang"] * Q_TIANG), "izin": Q_TIANG, "layan": g["layan"], "cap_vol": cap[0] * cap[1] * cap[2] * 1.0,
            "keterangan": "panjang tiang dan pile cap: menunggu Tahap 6"}


# ------------------------------------------------------------------ jarak ke sloof
SLOOF_B = 0.40
GRID_X, GRID_Y = ts.GRID_X, ts.GRID_Y


def jarak_sloof(p):
    """Kotak luar pit dan jarak muka ke muka sloof di tepi tiap sisi; sisi bawah sloof SL-1 +11,95 (400 x 900), SL-2/SL-3 +12,05."""
    cx, cy = p["pusat"]
    ao_x, ao_y = p["a"] + 2 * TW, p["b"] + 2 * TW
    x0, x1, y0, y1 = cx - ao_x / 2, cx + ao_x / 2, cy - ao_y / 2, cy + ao_y / 2
    bawah = p["dasar"] - TS0
    out = {"kotak": (x0, x1, y0, y1), "ao": (ao_x, ao_y), "bawah": bawah, "turun_sloof": {"SL-1": (LT1 - 0.9) - bawah, "SL-2/3": (LT1 - 0.8) - bawah}}
    sisi = {}
    for nm, ger, lo, hi, grid in (("barat", "x", x0, None, GRID_X), ("timur", "x", None, x1, GRID_X), ("selatan", "y", y0, None, GRID_Y),
                                  ("utara", "y", None, y1, GRID_Y)):
        if lo is not None:
            g = max([v for v in grid if v - SLOOF_B / 2 <= lo + 1e-9] or [None], default=None)
            sisi[nm] = (g, lo - (g + SLOOF_B / 2)) if g is not None else (None, None)
        else:
            g = min([v for v in grid if v + SLOOF_B / 2 >= hi - 1e-9] or [None], default=None)
            sisi[nm] = (g, (g - SLOOF_B / 2) - hi) if g is not None else (None, None)
    out["sisi"] = sisi
    out["di_inti"] = INTI[0] <= x0 and x1 <= INTI[1] and INTI[2] <= y0 and y1 <= INTI[3]
    if out["di_inti"]:
        out["inti_gap"] = (x0 - (INTI[0] + DINDING_INTI), (INTI[1] - DINDING_INTI) - x1, y0 - (INTI[2] + DINDING_INTI), (INTI[3] - DINDING_INTI) - y1)
    return out


def bukaan_lt1(p):
    """Bukaan LT1 = ruang dalam shaft; tulangan tepi tiap sisi 2 D13 tambahan (pola SH-6, 5.3), panjang = sisi + 2 ld (D13 atas)."""
    ld = 1.3 * 420 * 1.3 * 13 / (1.7 * math.sqrt(FC))
    return {"a": p["a"], "b": p["b"], "n_per_sisi": 2, "db": 13, "ld": ld, "panjang_a": p["a"] + 2 * ld / 1000, "panjang_b": p["b"] + 2 * ld / 1000}


# ------------------------------------------------------------------ cek silang T-94
def grid_gaya(p, t=TS0, h=0.05):
    """Gaya angkat U dengan integrasi grid sel h x h atas tapak luar (tekanan hidrostatik di dasar pelat), pusat sel dalam kotak."""
    ao_x, ao_y = p["a"] + 2 * TW, p["b"] + 2 * TW
    nx, ny = int(round(ao_x / h)), int(round(ao_y / h))
    bawah = p["dasar"] - t
    xs = (np.arange(nx) + 0.5) * h
    ys = (np.arange(ny) + 0.5) * h
    inside = (xs[:, None] <= ao_x) & (ys[None, :] <= ao_y)
    return float(np.sum(inside) * h * h * GW * (Q100 - bawah))


@functools.lru_cache(maxsize=1)
def cek_t94():
    p14, p7 = data_lift()["L-1..4"], data_lift()["L-5..6"]
    a = {"rumus": paket_angkat(p14)["t"]["q100"]["U"], "grid": grid_gaya(p14), "grid7": grid_gaya(data_lift()["L-7"]),
         "rumus7": paket_angkat(data_lift()["L-7"])["t"]["q100"]["U"]}
    s = struktur_pelat(p14)
    mxp, myp = pynite_pelat(s["a"], s["b"], TS0, s["qn"])
    mxn, myn = navier_tengah(s["a"], s["b"], s["qn"])
    b = {"navier": max(mxn, myn), "pynite": max(mxp, myp), "navier_x": mxn, "navier_y": myn, "pynite_x": mxp, "pynite_y": myp}
    d_ = dinding(p14)
    c = {"rumus": d_["M_jepit"], "pynite": pynite_dinding(p14)}
    dd = {"tertutup": t_min_tertutup(p14), "bisection": t_min_bisection(p14), "tertutup56": t_min_tertutup(p7), "bisection56": t_min_bisection(p7)}
    return {"a": a, "b": b, "c": c, "d": dd}


# ------------------------------------------------------------------ hitung
@functools.lru_cache(maxsize=1)
def hitung():
    dl = data_lift()
    r = {"lift": dl}
    r["angkat"] = {k: paket_angkat(dl[k]) for k in KODE}
    r["pelat"] = {k: struktur_pelat(dl[k]) for k in KODE}
    r["dinding"] = {k: dinding(dl[k]) for k in KODE}
    r["grav"] = {k: gravitasi(dl[k]) for k in KODE}
    r["l7_balok"] = balok_penggantung(dl["L-7"])
    r["l7_tiang"] = tiang_pilihan(dl["L-7"])
    r["jarak"] = {k: jarak_sloof(dl[k]) for k in KODE}
    r["bukaan"] = {k: bukaan_lt1(dl[k]) for k in KODE}
    r["jauh_mri"] = {k: ts.jarak_titik_ke_kotak(80.5, 57.0, dl[k]["pusat"][0] - dl[k]["a"] / 2, dl[k]["pusat"][0] + dl[k]["a"] / 2,
                                                 dl[k]["pusat"][1] - dl[k]["b"] / 2, dl[k]["pusat"][1] + dl[k]["b"] / 2) for k in KODE}
    r["sump"] = sump()
    r["t94"] = cek_t94()
    return r


def sump():
    """Sump 600 x 600 x 500: tekanan angkat lokal di dasarnya (pelat 150 mm di bawah sump) dan cek angkat lokal pada +0,5 m di atas Q100? Tidak: pada dasar sump."""
    dasar = 11.25
    bawah_s = dasar - SUMP[2] - 0.15
    u_s = GW * (Q100 - bawah_s)
    u_p = GW * (Q100 - (dasar - TS0))
    return {"u_sump": u_s, "u_pelat": u_p, "rasio": u_s / u_p, "bawah": bawah_s, "pompa": "2 unit celup 1 l/s (satu cadangan), buang di atas +12,31 dengan katup balik"}


# ================================================================== teks pembantu
def pct(v, d=2):
    return idn(v * 100, d)


def tul_s(t):
    return f"D{t['db']}-{idn(t['s'], 0)}"


def sel_s(x, y):
    return idn(abs(y / x - 1) * 100, 2)


def ok_s(b):
    return "memenuhi" if b else "tidak memenuhi"


# ------------------------------------------------------------------ Excel: baris R
def baris_umum(r):
    a = [
        R("gw", "Berat jenis air γw", GW, "kN/m³", "", "ts.GAMMA_W (3.3)", "0.00"),
        R("gc", "Berat jenis beton bertulang", GC, "kN/m³", "", "SNI 1727:2020 Tabel C3.1-2 (4.2)", "0.0"),
        R("q100", "Muka air banjir Q100", Q100, "m", "kasus ekstrem: banjir", "3.3; SNI 8460:2017 Pasal 9.3.4 (hal PDF 197)", "0.00"),
        R("q50", "Muka air Q50", Q50, "m", "", "3.3", "0.00"),
        R("tekan", "Tinggi tekan akuifer desain", TEKAN, "m", "", "2.4 (Tahap 2)", "0.00"),
        R("atas", "Sisi atas dinding pit = sisi bawah pelat LT1", ATAS, "m", "+12,85 - 0,25", "5.3", "0.00"),
        R("tw", "Tebal dinding pit", TW, "m", "", "[Asumsi 5.5]", "0.00"),
        R("ts", "Tebal pelat dasar pit (awal)", TS0, "m", "", "[Asumsi 5.5; dicek di sini]", "0.00"),
        R("fy", "fy", FY, "MPa", "", "", "0"),
        R("fkm", "FK minimum, beban mati saja", FK_M, "", "", "SNI 8460:2017 Pasal 9.3.4 b (hal PDF 197)", "0.0"),
        R("fka", "FK minimum, beban mati + tahanan angkur", FK_A, "", "", "SNI 8460:2017 Pasal 9.3.4 a (hal PDF 197)", "0.0"),
        R("fh", "Faktor beban H (air dalam tanah) menambah", FAKTOR_H, "", "", "SNI 2847:2019 Pasal 5.3.8 (hal PDF 110)", "0.0"),
    ]
    return [("A", "Masukan umum", a)]


def baris_angkat_pit(r, k):
    s = SUF[k]
    p, pk = r["lift"][k], r["angkat"][k]
    a, q = pk["t"]["q100"], pk["t"]["tekan"]
    rows = [
        R(f"a{s}", f"Lebar ruang dalam {k}", p["a"], "m", GEOM[k]["nama"], "Data Lift (Data Beban MEP Rinci)", "0.00"),
        R(f"b{s}", f"Panjang ruang dalam {k}", p["b"], "m", "", "Data Lift", "0.00"),
        R(f"da{s}", f"Elevasi dasar pit {k}", p["dasar"], "m", "sisi atas pelat dasar", "Data Lift", "0.00"),
        R(f"ao{s}", f"Luas tapak luar {k} = (a + 2 tw)(b + 2 tw)", f"=({{a{s}}}+2*{{tw}})*({{b{s}}}+2*{{tw}})", "m²", "", "", "0.000", a["A_luar"]),
        R(f"ai{s}", f"Luas ruang dalam {k}", f"={{a{s}}}*{{b{s}}}", "m²", "", "", "0.000", a["A_dalam"]),
        R(f"bw{s}", f"Sisi bawah pelat {k} = dasar - ts", f"={{da{s}}}-{{ts}}", "m", "", "", "0.00", a["bawah"]),
        R(f"u{s}", f"Tekanan angkat u pada Q100 {k}", f"={{gw}}*({{q100}}-{{bw{s}}})", "kPa", "γw (Q100 - sisi bawah)", "", "0.000", a["u"]),
        R(f"U{s}", f"Gaya angkat U {k}", f"={{u{s}}}*{{ao{s}}}", "kN", "u × tapak luar", "SNI 8460:2017 Pasal 9.3.4", "#,##0.0", a["U"]),
        R(f"ws{s}", f"Berat pelat dasar {k}", f"={{gc}}*{{ts}}*{{ao{s}}}", "kN", "", "", "#,##0.0", a["W_pelat"]),
        R(f"vw{s}", f"Volume dinding {k} sampai +12,60", f"=({{ao{s}}}-{{ai{s}}})*({{atas}}-{{da{s}}})", "m³", "", "", "0.000", a["V_dinding"]),
        R(f"ww{s}", f"Berat dinding {k}", f"={{gc}}*{{vw{s}}}", "kN", "", "", "#,##0.0", a["W_dinding"]),
        R(f"W{s}", f"Beban mati pit W {k}", f"={{ws{s}}}+{{ww{s}}}", "kN", "beton saja, tanpa buffer dan peralatan (minimum)", "", "#,##0.0", a["W"]),
        R(f"fk{s}", f"FK kotak pit utuh {k} (Q100)", f"={{W{s}}}/{{U{s}}}", "", "W / U; dinding dan pelat satu kesatuan", "", "0.000", a["FK_utuh"]),
        R(f"fl{s}", f"FK pelat lepas {k} (Q100)", f"={{ws{s}}}/{{U{s}}}", "", "pelat tanpa dinding", "", "0.000", a["FK_lepas"]),
        R(f"fkk{s}", f"FK tahap konstruksi {k} (pelat saja, muka air +11,20)", f"={{ws{s}}}/({{gw}}*({{tekan}}-{{bw{s}}})*{{ao{s}}})", "",
          "dewatering terkendali", "[Asumsi 5.5]", "0.000", q["FK_lepas"]),
        R(f"tm{s}", f"t min Opsi A {k} (dasar tetap, FK 1,1)",
          f"=({{fkm}}*{{gw}}*{{ao{s}}}*({{q100}}-{{da{s}}})-{{gc}}*{{vw{s}}})/({{gc}}*{{ao{s}}}-{{fkm}}*{{gw}}*{{ao{s}}})", "m", "tertutup", "", "0.0000", pk["tmin"]),
        R(f"tb{s}", f"t min dibulatkan 50 mm {k}", f"=ROUNDUP({{tm{s}}}/0.05,0)*0.05", "m", "", "", "0.00", pk["tmin_bulat"]),
        R(f"tl{s}", f"t min pelat lepas {k} (pembanding)", f"={{fkm}}*{{gw}}*({{q100}}-{{da{s}}})/({{gc}}-{{fkm}}*{{gw}})", "m", "pelat saja FK 1,1", "", "0.000", pk["tlepas"]),
        R(f"R{s}", f"Gaya ikat izin R Opsi B {k} = 1,5 U - W", f"={{fka}}*{{U{s}}}-{{W{s}}}", "kN", "tahanan izin pengangkuran", "SNI 8460:2017 Pasal 9.3.4 a, pasal 10", "#,##0.0", pk["R"]),
        R(f"as{s}", f"As stek angkur {k} = 1,6 R / (0,9 fy)", f"={{fh}}*MAX({{R{s}}},0)*1000/(0.9*{{fy}})", "mm²", "angkur ke LT1, sloof, inti", "SNI 2847:2019 5.3.8, Tabel 21.2.1", "#,##0", pk["as_stek"]),
    ]
    return rows


def baris_angkat(r):
    out = baris_umum(r)
    for k in KODE:
        out.append((SUF[k], f"Angkat pit {k}", baris_angkat_pit(r, k)))
    return out


def _lentur_rows(s, tag, nama, h_key, sel_key, res, h_py, sel_py, kf=1.5):
    ket = f"{nama} {s}"
    rr = [
        R(f"mu_{tag}{s}", f"Mu {ket}", res["mu"], "kNm/m", "dari lembar Struktur (Navier / statika)", "", "0.00"),
        R(f"db_{tag}{s}", f"Diameter {ket}", res["db"], "mm", "", "", "0"),
        R(f"sp_{tag}{s}", f"Spasi {ket}", res["s"], "mm", "", "SNI 2847:2019 24.3.2", "0"),
        R(f"d_{tag}{s}", f"d {ket}", f"={{{h_key}}}-{{{sel_key}}}-{kf}*{{db_{tag}{s}}}/1000", "m", "lapis kedua (konservatif)" if kf > 1 else "satu lapis per muka", "", "0.0000", res["d"]),
        R(f"ap_{tag}{s}", f"As perlu {ket}", f"=MAX(1000000*(0.85*{{sfc}}*1000)/({{sfy}}*1000)*({{d_{tag}{s}}}-SQRT(MAX({{d_{tag}{s}}}^2-2*({{mu_{tag}{s}}}/0.9)/(0.85*{{sfc}}*1000),0))),{res['as_min']!r})",
          "mm²/m", "lentur atau minimum", "SNI 2847:2019 22.2, Tabel 8.6.1.1 / 11.6.1", "0.0", res["as_perlu"]),
        R(f"aa_{tag}{s}", f"As terpasang {ket}", f"=1000*PI()*{{db_{tag}{s}}}^2/4/{{sp_{tag}{s}}}", "mm²/m", "", "", "0.0", res["as_ada"]),
        R(f"pm_{tag}{s}", f"φMn {ket}", f"=0.9*{{aa_{tag}{s}}}*1E-6*{{sfy}}*1000*({{d_{tag}{s}}}-{{aa_{tag}{s}}}*1E-6*{{sfy}}/(1.7*{{sfc}}))", "kNm/m", "", "Tabel 21.2.1", "0.00", res["phimn"]),
        R(f"rs_{tag}{s}", f"Rasio Mu / φMn {ket}", f"={{mu_{tag}{s}}}/{{pm_{tag}{s}}}", "", "", "", "0.000", res["rasio"]),
    ]
    return rr


def baris_struktur(r):
    glob = [
        R("sfc", "fc'", FC, "MPa", "kelas S2 (Tabel 19.3.2.1)", "5.3", "0.0"),
        R("sfy", "fy", FY, "MPa", "", "", "0"),
        R("sh", "Tebal pelat dasar", TS0, "m", "", "[Asumsi 5.5]", "0.00"),
        R("sht", "Tebal dinding", TW, "m", "", "[Asumsi 5.5]", "0.00"),
        R("sela", "Selimut sisi tanah", SEL_TANAH, "m", "40 + 10 untuk tanah asam, ≤ D16", "SNI 2847:2019 Tabel 20.6.1.3.1 (hal PDF 482) [Asumsi 5.5]", "0.000"),
        R("seld", "Selimut sisi dalam", SEL_DALAM, "m", "", "[Asumsi 5.5]", "0.000"),
    ]
    out = [("A", "Masukan struktur", glob)]
    for k in KODE:
        s = SUF[k]
        pe, di = r["pelat"][k], r["dinding"][k]
        rows = []
        rows += _lentur_rows(s, "n", "pelat naik, tulangan atas", "sh", "seld", pe["atas"], TS0, SEL_DALAM)
        rows += _lentur_rows(s, "t", "pelat turun, tulangan bawah", "sh", "sela", pe["bawah"], TS0, SEL_TANAH)
        rows += _lentur_rows(s, "dl", "dinding muka luar (dasar)", "sht", "sela", di["luar"], TW, SEL_TANAH, 0.5)
        rows += _lentur_rows(s, "dd", "dinding muka dalam (lapangan)", "sht", "seld", di["dalam"], TW, SEL_DALAM, 0.5)
        out.append((s, f"Tulangan pit {k}", rows))
    return out


def semua_baris(r):
    return {"Angkat": [rw for _, _, rows in baris_angkat(r) for rw in rows], "Struktur": [rw for _, _, rows in baris_struktur(r) for rw in rows]}


NAMA = ["Petunjuk", "Ringkasan", "Data Lift", "Angkat", "Opsi A dan B", "Kedap", "Struktur", "Dinding", "Tumpuan", "Jarak Sloof", "Cek Silang T-94", "Acuan"]


# ------------------------------------------------------------------ teks tabel
def teks_data(r):
    out = []
    for k in KODE:
        p = r["lift"][k]
        out.append([k, p["nama"], f"{idn(p['a'], 1)} × {idn(p['b'], 1)}", idn(p["dasar"], 2), idn(p["dalam"], 1), f"{idn(p['p_kereta'], 0)} / {idn(p['p_imbang'], 0)}",
                    f"x {p['x']}; y {p['y']}"])
    return out


def teks_angkat(r):
    out = []
    for k in KODE:
        pk = r["angkat"][k]
        for nm, mk in (("tekan +11,20", "tekan"), ("Q50 +11,85", "q50"), ("Q100 +12,31", "q100")):
            a = pk["t"][mk]
            out.append([k, nm, idn(a["u"], 2), idn(a["U"], 1), idn(a["W"], 1), idn(a["FK_utuh"], 3), idn(a["FK_lepas"], 3),
                        "memenuhi 1,1" if a["FK_utuh"] >= FK_M else "kurang dari 1,1"])
    return out


def teks_opsi(r):
    out = []
    for k in KODE:
        pk = r["angkat"][k]
        a = pk["t"]["q100"]
        out.append([k, idn(a["FK_utuh"], 3), idn(pk["tmin"], 3), idn(pk["tmin_bulat"], 2) if pk["tmin"] > TS0 else "tidak perlu (t 0,40 cukup)",
                    idn(pk["tlepas"], 2), idn(pk["R"], 1), idn(pk["as_stek"], 0), "D19 " + str(max(math.ceil(pk["as_stek"] / sl.luas(19)), 0)) + " batang" if pk["as_stek"] > 0 else "-",
                    idn(pk["dV_A"], 2)])
    return out


def teks_kedap():
    return [
        ["Kelas paparan tanah asam (S2)", "w/cm ≤ 0,45; fc' ≥ 31 MPa; semen tipe V atau IP(HS)/IS(HS)/IT(HS)", "SNI 2847:2019 Tabel 19.3.2.1 (hal PDF 464)", "menentukan; dipakai fc' 35, w/cm ≤ 0,45"],
        ["Kelas paparan air (W1)", "w/cm ≤ 0,50; fc' ≥ 28 MPa", "SNI 2847:2019 Tabel 19.3.2.1 (hal PDF 464)", "lebih longgar dari S2"],
        ["Kelas W2", "-", "belum ada di acuan", "tabel acuan hanya memuat W0 dan W1; tidak dipakai"],
        ["Kontrol spasi tulangan (kedap air)", f"s ≤ min(380 (280/fs) - 2,5 cc; 300 (280/fs)), fs = 2/3 fy = 280 MPa: sisi tanah cc 50: {idn(smaks_retak(50), 0)} mm; sisi dalam cc 40: {idn(smaks_retak(40), 0)} mm",
         "SNI 2847:2019 Pasal 24.3.2 (hal PDF 573), 24.3.5 (hal PDF 574)", "diterapkan pada semua tulangan pit"],
        ["Waterstop", "dua sambungan: pelat dasar-dinding (kicker 150 mm) dan dinding-pelat LT1; PVC 230 mm atau bentonit/hidrofilik", "[Asumsi 5.5]; produk pabrikan belum ada di acuan", "dipasang menerus keliling"],
        ["Lapisan kedap: aditif kristalin", "campuran kristalin dalam beton 1 % berat semen", "belum ada di acuan", "pilihan Defsa (1)"],
        ["Lapisan kedap: membran HDPE pra-pasang", "di bawah lantai kerja dan dinding luar", "belum ada di acuan", "pilihan Defsa (2)"],
        ["Ketentuan beton kedap air (ACI 350, EN 1992-3)", "lebar retak izin 0,2 mm", "belum ada di acuan", "kontrol spasi 24.3.2 dipakai sebagai pengganti"],
        ["Sump 600 × 600 × 500", f"tekanan angkat lokal di dasar sump {idn(r_sump()['u_sump'], 2)} kPa vs pelat {idn(r_sump()['u_pelat'], 2)} kPa (rasio {idn(r_sump()['rasio'], 2)}); tebal pelat di bawah sump 150 mm",
         "[Asumsi 5.5]", "tebalkan lokal; cek angkat lokal ikut pelat"],
        ["Pompa celup", r_sump()["pompa"], "[Asumsi 5.5]; laju rembesan belum ada di acuan", "buang ke atas +12,31"],
        ["Keselamatan lift (pit, ruang bebas, buffer)", "-", "EN 81-20 belum ada di acuan", "dimensi pit mengikuti data pemasok"],
    ]


def r_sump():
    return sump()


def teks_pelat(r):
    out = []
    for k in KODE:
        p = r["pelat"][k]
        out.append([k, f"{idn(p['a'], 2)} × {idn(p['b'], 2)}", idn(p["qn"], 2), idn(p["Mx_n"], 1) + " / " + idn(p["My_n"], 1), tul_s(p["atas"]) + f" ({idn(p['atas']['rasio'], 2)})",
                    idn(p["Mx_d"], 1) + " / " + idn(p["My_d"], 1), tul_s(p["bawah"]) + f" ({idn(p['bawah']['rasio'], 2)})", f"{idn(p['r_pons'], 2)}; tumpu {idn(p['r_tumpu'], 2)}",
                    ok_s(p["ok_geser"] and p["atas"]["ok"] and p["bawah"]["ok"] and p["r_pons"] <= 1.0)])
    return out


def teks_dinding(r):
    out = []
    for k in KODE:
        d = r["dinding"][k]
        out.append([k, idn(d["H"], 2), f"{idn(d['p_atas'], 1)} / {idn(d['p_dasar'], 1)}", idn(d["M_jepit"], 2), idn(d["M_lapangan"], 2), idn(d["M_kantilever"], 2),
                    f"{tul_s(d['luar'])} luar; {tul_s(d['dalam'])} dalam", f"D{d['hor']['db']}-{idn(d['hor']['s'], 0)} tiap muka",
                    f"V {idn(d['V_dasar'], 1)} ≤ φVc {idn(d['phiVc'], 1)}"])
    return out


def teks_grav(r):
    out = []
    for k in KODE:
        g = r["grav"][k]
        out.append([k, idn(g["W"], 1), idn(g["Pb"], 0), idn(g["layan"], 1), idn(g["Pu"], 1), idn(g["U_q100"], 1), idn(g["net_banjir"], 1)])
    return out


def teks_l7(r):
    bk, tg = r["l7_balok"], r["l7_tiang"]
    out = []
    for x in bk["kandidat"]:
        out.append([f"balok penggantung {idn(x['b'] * 1000, 0)} × {idn(x['h'] * 1000, 0)} (2 balok, bentang 8 m)", f"Mu {idn(x['Mu'], 0)} kNm; Vu {idn(x['Vu'], 0)} kN",
                    f"{x['n29']} D29 (ρ {pct(x['rho'])} %)", f"beton {idn(x['beton'], 1)} m³; baja {idn(x['baja_kg'], 0)} kg", "memenuhi" if x["ok"] else "tidak memenuhi"])
    out.append([f"pile cap + {tg['n']} tiang bor Ø800", f"layan {idn(tg['layan'], 0)} kN; izin {idn(tg['n'] * tg['izin'], 0)} kN", f"rasio {idn(tg['rasio'], 2)}",
                f"cap 1,6 × 1,6 × 0,8 m (beton {idn(tg['cap_vol'], 1)} m³); {tg['keterangan']}", "memenuhi"])
    return out


def teks_jarak(r):
    out = []
    for k in KODE:
        j = r["jarak"][k]
        x0, x1, y0, y1 = j["kotak"]
        s = j["sisi"]

        def gp(nm):
            g, gap = s[nm]
            return "-" if g is None else f"as {idn(g, 0)}: {idn(gap, 2)}"
        out.append([k, f"x {idn(x0, 2)}-{idn(x1, 2)}; y {idn(y0, 2)}-{idn(y1, 2)}", f"B {gp('barat')}; T {gp('timur')}; S {gp('selatan')}; U {gp('utara')}",
                    f"{idn(j['bawah'], 2)}; turun {idn(j['turun_sloof']['SL-1'], 2)} / {idn(j['turun_sloof']['SL-2/3'], 2)}",
                    "di dalam inti" if j["di_inti"] else "di luar inti"])
    return out


def teks_bukaan(r):
    out = []
    for k in KODE:
        b = r["bukaan"][k]
        out.append([k, f"{idn(b['a'], 2)} × {idn(b['b'], 2)}", f"2 D13 tiap sisi, panjang {idn(b['panjang_a'], 2)} m (sisi a) dan {idn(b['panjang_b'], 2)} m (sisi b)",
                    f"ld atas {idn(b['ld'], 0)} mm (lewatan kelas B)", "pola SH-6 (5.3)"])
    return out


# ------------------------------------------------------------------ workbook
def _tt(lb, kepala, isi, rata, beku=False, ai=True):
    return mri._teks_tabel(lb, kepala, isi, rata, beku=beku, ai=ai)


def buat_excel(keluar=BERKAS):
    from format_dokumen import AI, Lembar, set_font_bawaan
    r = hitung()
    x4 = r["t94"]
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    for s in NAMA:
        wb.create_sheet(s)
    mri.REF.clear()
    mri.LABEL_PAKAI.clear()
    ket = LABEL + " " + LABEL_AI
    tt = _tt
    a14 = r["angkat"]["L-1..4"]

    # ---- Data Lift
    lb = Lembar(wb["Data Lift"], 3, "Data lift dan geometri pit", [5, 10, 40, 18, 14, 14, 18, 30])
    lb.catatan(ket + " Data dari lembar Lift (Data Beban MEP Rinci). Ruang dalam pit = gabungan shaft (L-1..4: 2 × 2 shaft; L-5..6: dua shaft berdampingan; L-7: satu). "
               "Dinding 0,30 m dan pelat dasar 0,40 m [Asumsi 5.5]; dinding sampai sisi bawah pelat LT1 +12,60. Pusat tapak L-1..4 di tengah inti [Asumsi]. "
               "Reaksi buffer sudah termasuk faktor kejut pemasok.")
    lb.kosong()
    lb.bagian("A", "Data per kelompok lift")
    tt(lb, ["No", "Kode", "Jenis", "Ruang dalam (m)", "Dasar pit (m)", "Kedalaman (m)", "Buffer kereta / imbang (kN)", "Posisi shaft (m)"], teks_data(r), list("clclcccc"), beku=True)

    # ---- Angkat
    def tambah_angkat(lb):
        lb.kosong()
        lb.bagian("Z", "Tiga muka air untuk semua kelompok (Q100 menentukan)")
        tt(lb, ["No", "Pit", "Muka air", "u (kPa)", "U (kN)", "W (kN)", "FK utuh", "FK pelat lepas", "Status"], teks_angkat(r), list("clcccccc") + ["l"])
        lb.kosong()
        lb.catatan("SNI 8460:2017 Pasal 9.3.4 (hal PDF 197): FK ≥ 1,5 bila tahanan = beban mati + tahanan izin pengangkuran; FK ≥ 1,1 bila tahanan = beban mati minimum saja; muka "
                   "air tertinggi dari semua kasus ekstrem (banjir): Q100 +12,31. Pasal 12 (hal PDF 279) butir b: lantai besmen didesain terhadap uplift pada muka air desain dan banjir. "
                   "Kotak pit utuh = pelat dasar + dinding sampai +12,60 (satu kesatuan), gesekan tanah di dinding diabaikan, tanpa berat buffer dan peralatan. "
                   "Tahap konstruksi: hanya pelat dasar, muka air desain +11,20 dengan dewatering terkendali; bila dewatering berhenti pada Q100 pelat lepas FK < 1,1 (lihat kolom FK pelat lepas).")
    mri._lembar_hitung(wb, "Angkat", 4, "Angkat (uplift) pit lift", ket, baris_angkat(r), tambah_angkat)

    # ---- Opsi A dan B
    lb = Lembar(wb["Opsi A dan B"], 5, "Opsi A (tebal pelat) dan Opsi B (ikat angkur); tanpa memilih", [5, 10, 14, 14, 18, 14, 14, 16, 14, 14])
    lb.catatan(ket + " Opsi A: dasar pit tetap, pelat ditebalkan ke bawah sampai FK 1,1 (beban mati saja); galian dan beton bertambah. Opsi B: pelat 0,40, FK 1,5 dengan tahanan "
               "angkur izin R = 1,5 U - W diikat ke LT1/sloof/inti; As stek = 1,6 R / (0,9 fy). Varian B2: pelat dasar L-1..4 dijadikan sisi atas pile cap inti: tebal dan tiang tarik "
               "menunggu Tahap 6 (belum ada pile cap inti). Pasal pengangkuran (SNI 8460:2017 pasal 10) belum diverifikasi di acuan; kapasitas angkur tidak dihitung di sini.")
    lb.kosong()
    lb.bagian("A", "Banding Opsi A dan B")
    tt(lb, ["No", "Pit", "FK utuh t 0,40", "t min A (m)", "t pakai A (m)", "t lepas (pembanding)", "R B (kN)", "As stek B (mm²)", "Batang B", "Beton tambah A (m³)"],
       teks_opsi(r), list("clcccccccc"), beku=True)

    # ---- Kedap
    def tambah_kedap(lb):
        lb.kosong()
        lb.bagian("B", "Kedap air, waterstop, sump, dan pompa")
        tt(lb, ["No", "Butir", "Ketentuan", "Sumber", "Keputusan / catatan"], teks_kedap(), list("clllll"))
    lb = Lembar(wb["Kedap"], 6, "Kedap air dan drainase pit", [5, 34, 62, 42, 40])
    lb.catatan(ket + " Hal yang tidak ada di acuan ditulis persis 'belum ada di acuan'.")
    lb.kosong()
    lb.bagian("A", "Ketentuan")
    tt(lb, ["No", "Butir", "Ketentuan", "Sumber", "Keputusan / catatan"], teks_kedap(), list("clllll"), beku=True)

    # ---- Struktur
    def tambah_struktur(lb):
        lb.kosong()
        lb.bagian("Z", "Ringkasan momen dan tulangan (kNm/m)")
        tt(lb, ["No", "Pit", "Bentang c-c (m)", "qu naik (kPa)", "Mu naik Mx / My", "Atas (rasio)", "Mu turun Mx / My", "Bawah (rasio)", "Pons; tumpu buffer", "Status"],
           teks_pelat(r), list("clccccccc") + ["l"])
        lb.kosong()
        lb.catatan("Pelat naik: qu = 1,6 u - 0,9 γc t (SNI 2847:2019 5.3.8), Navier tumpuan sederhana di sumbu dinding, tulangan atas (selimut dalam 40 mm). Pelat turun: 1,2 γc t + 1,6 beban "
                   "buffer (kereta + bobot imbang tiap shaft di pelat landasan 300 × 300, patch di pusat shaft), tanpa tumpuan tanah (konservatif), tulangan bawah (selimut tanah 50 mm). "
                   "Tulangan dua arah memakai momen terbesar; D13 lalu D16/D19; spasi ≤ batas 24.3.2 (kedap). Geser satu arah (22.5.5.1, hal PDF 507) dan pons buffer (22.6.4.1, hal 518; Tabel "
                   "22.6.5.2, hal 521) dicek. Hasil Navier dicek terhadap PyNite di T-94 (b).")
    mri._lembar_hitung(wb, "Struktur", 7, "Struktur pelat dasar dan dinding: tulangan lentur", ket, baris_struktur(r), tambah_struktur)

    # ---- Dinding
    lb = Lembar(wb["Dinding"], 8, "Dinding pit: tekanan tanah dan air", [5, 10, 12, 18, 14, 14, 14, 36, 28, 30])
    lb.catatan(ket + " Tekanan horizontal: K0 σv' + γw (Q100 - e), K0 0,50, tanah γ 18 / γsat 19 kN/m³, tanah dari +12,60, air +12,31, tanpa beban tambahan di permukaan [Asumsi 5.5]. "
               "Beban terfaktor 1,6 H. Dinding jepit di pelat dasar dan sendi di pelat LT1 (balok jepit-sendi): M jepit = ∫ p (H - s) s (2H - s) / (2H²) ds; pembanding kantilever (LT1 tidak "
               "menahan) konservatif. Tulangan horizontal minimum ρt 0,0020 dan vertikal ρℓ 0,0012 (≤ D16, fy ≥ 420; SNI 2847:2019 Tabel 11.6.1, hal PDF 255), dibagi dua muka. "
               "Momen kecil: tulangan ditentukan minimum dan kontrol spasi kedap.")
    lb.kosong()
    lb.bagian("A", "Hasil per pit")
    tt(lb, ["No", "Pit", "H (m)", "p atas / dasar (kPa)", "M jepit 1,6 H (kNm/m)", "M lapangan (kNm/m)", "M kantilever (kNm/m)", "Vertikal", "Horizontal", "Geser"],
       teks_dinding(r), list("clcccccllc"), beku=True)

    # ---- Tumpuan
    lb = Lembar(wb["Tumpuan"], 9, "Tumpuan gravitasi dan L-7: balok penggantung vs tiang", [5, 40, 36, 24, 40, 14])
    lb.catatan(ket + " Gravitasi: berat beton pit + buffer (kereta + bobot imbang tiap lift). L-1..4 di dalam inti dan L-5..6 berimpit sloof as C: tumpuan ke inti, sloof, dan LT1 "
               "(detail Tahap 6). L-7 di tengah bay (x 36-44, y 27-35) jauh dari sloof: tanah tidak boleh jadi tumpuan (urugan masih turun 0,15-1,18 m, 2.8). Balok penggantung: dua balok "
               "sederhana 8 m ke sloof as x 36 dan x 44, beban Pu / 2 di tengah. Tiang: Ø800 izin 911 kN (3.7), minimum 2 per pile cap.")
    lb.kosong()
    lb.bagian("A", "Beban gravitasi tiap pit")
    tt(lb, ["No", "Pit", "W beton (kN)", "Buffer total (kN)", "Layan W + P (kN)", "Pu = 1,2 W + 1,6 P (kN)", "U Q100 (kN)", "W - U Q100 (kN)"], teks_grav(r), list("cl") + list("cccccc"), beku=True)
    lb.kosong()
    lb.bagian("B", "L-7: dua cara menumpu")
    tt(lb, ["No", "Cara", "Gaya", "Tulangan", "Volume", "Status"], teks_l7(r), list("clllll"))

    # ---- Jarak Sloof
    lb = Lembar(wb["Jarak Sloof"], 10, "Jarak pit ke sloof, elevasi, dan bukaan LT1", [5, 10, 36, 56, 40, 20])
    lb.catatan(ket + " Sloof 400 mm di as grid 8 × 8 m; sisi bawah SL-1 +11,95 (400 × 900), SL-2/SL-3 +12,05. Jarak = muka pit ke muka sloof (negatif: pit melewati as sloof). "
               "L-1..4 di dalam inti (dinding 350): sloof berakhir di inti (5.4), jarak dihitung ke muka dalam inti. Dinding pit turun di bawah sloof sebesar kolom 'turun'. "
               f"Jarak ruang dalam pit ke isocenter MRI: L-1..4 {idn(r['jauh_mri']['L-1..4'], 1)} m, L-5..6 {idn(r['jauh_mri']['L-5..6'], 1)} m, L-7 {idn(r['jauh_mri']['L-7'], 1)} m (5.2).")
    lb.kosong()
    lb.bagian("A", "Letak tapak luar pit dan sloof terdekat (B barat, T timur, S selatan, U utara)")
    tt(lb, ["No", "Pit", "Tapak luar (m)", "Jarak muka ke muka sloof (m)", "Sisi bawah pit; turun dari sloof (m)", "Letak"], teks_jarak(r), list("clllll"), beku=True)
    lb.kosong()
    lb.bagian("B", "Tulangan tepi bukaan LT1 (pola SH-6, 5.3)")
    tt(lb, ["No", "Pit", "Bukaan (m)", "Tulangan", "Penyaluran", "Dasar"], teks_bukaan(r), list("clllll"))
    lb.kosong()
    inti = r["jarak"]["L-1..4"].get("inti_gap")
    if inti:
        lb.catatan(f"L-1..4 di dalam inti: jarak tapak luar ke muka dalam dinding inti: barat {idn(inti[0], 2)}, timur {idn(inti[1], 2)}, selatan {idn(inti[2], 2)}, utara {idn(inti[3], 2)} m.")

    # ---- Cek Silang T-94
    lb = Lembar(wb["Cek Silang T-94"], 11, "Cek silang T-94", [5, 58, 14, 14, 12, 12, 10, 56])
    lb.catatan(ket + " Toleransi ditetapkan sebelum membandingkan. Cara 1 = rumus atau tangan; cara 2 = integrasi grid, PyNite, atau bisection.")
    lb.kosong()
    lb.bagian("A", "Empat cek silang")
    ws = lb.ws
    kep = ["No", "Cek", "Cara 1", "Cara 2", "Selisih (%)", "Toleransi (%)", "Status", "Cara 1 / cara 2"]
    isi = [
        [1, "(a) Gaya angkat U L-1..4 pada Q100 (kN)", None, None, None, TOL["a"], None, "1: rumus γw (Q100 - bawah) A luar (lembar Angkat). 2: integrasi grid 0,05 m"],
        [2, "(b) Momen pelat naik L-1..4 Mx/My terbesar, merata (kNm/m)", None, None, None, TOL["b"], None, "1: Navier deret (pusat). 2: PyNite pelat 4 sisi sendi, mesh 0,25, 4 elemen tengah"],
        [3, "(c) Momen jepit dinding L-1..4 (kNm/m)", None, None, None, TOL["c"], None, "1: integral fungsi Green balok jepit-sendi. 2: PyNite balok jepit-sendi, 2 segmen beban"],
        [4, "(d) t min Opsi A L-1..4 (m)", None, None, None, TOL["d"], None, "1: rumus tertutup (lembar Angkat). 2: bisection FK(t) = 1,1"],
    ]
    r0, a0, a1 = lb.tabel(kep, isi, rata=list("clcccccl"), fmt=[None, None, "0.0000", "0.0000", "0.00", "0.0", None, None])

    def ref(key):
        return "=" + mri._sub("{" + key + "}", ws.title)
    c2, c3 = lb.kol(2), lb.kol(3)
    ws[f"{c2}{a0}"] = ref("U14")
    ws[f"{c3}{a0}"] = x4["a"]["grid"]
    ws[f"{c2}{a0 + 1}"] = x4["b"]["navier"]
    ws[f"{c3}{a0 + 1}"] = x4["b"]["pynite"]
    ws[f"{c2}{a0 + 2}"] = x4["c"]["rumus"]
    ws[f"{c3}{a0 + 2}"] = x4["c"]["pynite"]
    ws[f"{c2}{a0 + 3}"] = ref("tm14")
    ws[f"{c3}{a0 + 3}"] = x4["d"]["bisection"]
    for i in range(4):
        rr = a0 + i
        ws[f"{lb.kol(4)}{rr}"] = f"=ABS({c3}{rr}-{c2}{rr})/{c2}{rr}*100"
        ws[f"{lb.kol(6)}{rr}"] = f'=IF({lb.kol(4)}{rr}<={lb.kol(5)}{rr},"Lolos","Tidak lolos")'
        ws[f"{lb.kol(5)}{rr}"].fill = PatternFill("solid", fgColor=AI)
        ws[f"{c3}{rr}"].fill = PatternFill("solid", fgColor=AI)
    ws[f"{c2}{a0 + 1}"].fill = PatternFill("solid", fgColor=AI)
    ws[f"{c2}{a0 + 2}"].fill = PatternFill("solid", fgColor=AI)
    lb.kosong()
    lb.catatan(f"Catatan: (a) L-7 grid {idn(x4['a']['grid7'], 2)} vs rumus {idn(x4['a']['rumus7'], 2)} kN. (b) Mx {idn(x4['b']['navier_x'], 2)} / My {idn(x4['b']['navier_y'], 2)} (Navier) vs "
               f"{idn(x4['b']['pynite_x'], 2)} / {idn(x4['b']['pynite_y'], 2)} (PyNite). (d) L-5..6 tertutup {idn(x4['d']['tertutup56'], 4)} vs bisection {idn(x4['d']['bisection56'], 4)} m.")

    # ---- Ringkasan
    lb = Lembar(wb["Ringkasan"], 2, "Ringkasan temuan dan keputusan yang diminta dari Defsa", [5, 38, 78, 40, 44])
    lb.catatan(f"STATUS: {STATUS}. " + ket)
    lb.kosong()
    lb.bagian("A", "Temuan")
    a56, a7 = r["angkat"]["L-5..6"], r["angkat"]["L-7"]
    bk, tg = r["l7_balok"]["pilih"], r["l7_tiang"]
    tt(lb, ["No", "Temuan", "Hasil kunci", "Keputusan Defsa", "Usulan AI"], [
        ["Angkat (Q100 +12,31, t 0,40)",
         f"L-1..4: U {idn(a14['t']['q100']['U'], 0)}, W {idn(a14['t']['q100']['W'], 0)} kN, FK utuh {idn(a14['t']['q100']['FK_utuh'], 2)} (< 1,1), pelat lepas {idn(a14['t']['q100']['FK_lepas'], 2)}. "
         f"L-5..6: U {idn(a56['t']['q100']['U'], 0)}, W {idn(a56['t']['q100']['W'], 0)}, FK {idn(a56['t']['q100']['FK_utuh'], 2)}. L-7: U {idn(a7['t']['q100']['U'], 0)}, W {idn(a7['t']['q100']['W'], 0)}, "
         f"FK {idn(a7['t']['q100']['FK_utuh'], 2)}. Tahap konstruksi L-1..4 FK {idn(a14['tahap_konstruksi']['FK'], 2)} (muka air +11,20).", "Memilih Opsi A atau B.", "Lihat Opsi A dan B."],
        ["Opsi A: tebal pelat",
         f"L-1..4 t ≥ {idn(a14['tmin'], 3)} m, dipakai {idn(a14['tmin_bulat'], 2)} m (+{idn(a14['dV_A'], 1)} m³ beton dan galian). L-5..6 dan L-7 cukup 0,40.", "Menyetujui atau Opsi B.", "Opsi A bila tanpa angkur."],
        ["Opsi B: ikat angkur",
         f"L-1..4 R = 1,5 U - W = {idn(a14['R'], 0)} kN, As stek {idn(a14['as_stek'], 0)} mm². L-5..6 R {idn(a56['R'], 0)} kN; L-7 {idn(a7['R'], 0)} kN. B2: pelat dasar L-1..4 = sisi atas pile cap inti (Tahap 6).", "Menyetujui atau Opsi A.", "Tergantung Tahap 6."],
        ["Struktur pelat dan dinding",
         f"Pelat naik Mu {idn(max(r['pelat']['L-1..4']['Mx_n'], r['pelat']['L-1..4']['My_n']), 1)} kNm/m (atas {tul_s(r['pelat']['L-1..4']['atas'])}); turun Mu {idn(max(r['pelat']['L-1..4']['Mx_d'], r['pelat']['L-1..4']['My_d']), 0)} "
         f"(bawah {tul_s(r['pelat']['L-1..4']['bawah'])}); dinding {tul_s(r['dinding']['L-1..4']['luar'])} / {tul_s(r['dinding']['L-1..4']['dalam'])}, horizontal D{r['dinding']['L-1..4']['hor']['db']}-"
         f"{idn(r['dinding']['L-1..4']['hor']['s'], 0)}.", "Menyetujui.", "Setuju."],
        ["Tumpuan L-7",
         f"Layan {idn(r['grav']['L-7']['layan'], 0)} kN, Pu {idn(r['grav']['L-7']['Pu'], 0)} kN. Balok penggantung {idn(bk['b'] * 1000, 0)} × {idn(bk['h'] * 1000, 0)} ({bk['n29']} D29, beton {idn(bk['beton'], 1)} m³, baja {idn(bk['baja_kg'], 0)} kg) "
         f"vs {tg['n']} tiang Ø800 (rasio {idn(tg['rasio'], 2)}).", "Memilih balok penggantung atau pile cap/tiang.", "Tiang bila Tahap 6 menyediakan pile cap di zona itu."],
        ["Lapisan kedap", "Beton S2 (w/cm ≤ 0,45, fc' 35) menentukan; kelas W2 belum ada di acuan; waterstop dua sambungan; kontrol spasi 24.3.2.", "Aditif kristalin atau membran HDPE.", "Aditif kristalin (tanpa pasang membran di lahan sempit)."],
        ["Jarak ke sloof dan bukaan LT1",
         f"L-5..6 berimpit sloof as C (jarak {idn(r['jarak']['L-5..6']['sisi']['selatan'][1], 2)} m ke selatan); dinding pit turun {idn(r['jarak']['L-5..6']['turun_sloof']['SL-1'], 2)} m di bawah sloof; bukaan 2 D13 tiap sisi.", "Menyetujui.", "Setuju."],
    ], list("clllll")[:5], beku=True)
    lb.kosong()
    lb.catatan("Cek silang T-94 lolos (lembar Cek Silang T-94). Pasal yang tidak ada di acuan ditulis 'belum ada di acuan' (lembar Acuan).")

    # ---- Acuan
    lb = Lembar(wb["Acuan"], 12, "Acuan yang dipakai dan statusnya", [5, 26, 30, 62, 12, 34])
    lb.catatan(ket + " Halaman = nomor halaman PDF di acuan/privat (diverifikasi dengan pypdf, 21 Nov 2026).")
    lb.kosong()
    lb.bagian("A", "Pasal yang diverifikasi di PDF")
    tt(lb, ["No", "Acuan", "Pasal", "Isi yang dipakai", "Hal. PDF", "Status"], [
        ["SNI 8460:2017", "9.3.4", "Buoyancy: FK ≥ 1,5 (beban mati + tahanan izin angkur) atau ≥ 1,1 (beban mati minimum); muka air tertinggi dari kasus ekstrem.", "197", "Terverifikasi"],
        ["SNI 8460:2017", "Pasal 12 butir b", "Lantai besmen didesain terhadap uplift pada muka air desain dan banjir.", "279", "Terverifikasi (dari telaah)"],
        ["SNI 2847:2019", "5.3.7, 5.3.8", "Faktor F dan H: 1,6 menambah; 0,9 melawan.", "109-110", "Terverifikasi"],
        ["SNI 2847:2019", "Tabel 19.3.2.1", "Kelas paparan S dan W: S2 w/cm ≤ 0,45 fc' ≥ 31; W0 dan W1 saja.", "464", "Terverifikasi"],
        ["SNI 2847:2019", "Tabel 20.6.1.3.1", "Selimut tanah: D19-D57 50 mm; ≤ D16 40 mm.", "482", "Terverifikasi"],
        ["SNI 2847:2019", "Tabel 11.6.1", "Dinding: ρℓ 0,0012 dan ρt 0,0020 (batang ulir ≤ D16, fy ≥ 420); > D16: 0,0015 dan 0,0025.", "255", "Terverifikasi"],
        ["SNI 2847:2019", "24.3.2, 24.3.5", "Spasi: min (380 (280/fs) - 2,5 cc; 300 (280/fs)); komponen kedap air tidak melebihi 24.3.2.", "573-574", "Terverifikasi"],
        ["SNI 2847:2019", "22.5.5.1", "Vc = 0,17 λ √fc' bw d.", "507", "Terverifikasi"],
        ["SNI 2847:2019", "22.6.4.1, Tabel 22.6.5.2", "b0 dan vc geser pons.", "518; 521", "Terverifikasi (dari 5.3)"],
        ["SNI 2847:2019", "Tabel 21.2.1, Tabel 8.6.1.1", "φ; As min pelat 0,0018.", "491; 145", "Terverifikasi (dari 5.3)"],
        ["SNI 1727:2020", "Tabel C3.1-2", "Berat jenis beton bertulang 23,6 kN/m³.", "277-278", "dari 4.2"],
    ], list("clllcl"), beku=True)
    lb.kosong()
    lb.bagian("B", "Tidak ada di acuan")
    tt(lb, ["No", "Acuan", "Pasal", "Keterangan", "Hal. PDF", "Status"], [
        ["Kelas paparan W2", "-", "Tabel 19.3.2.1 hanya memuat W0 dan W1.", "464", "belum ada di acuan"],
        ["Pengangkuran izin (SNI 8460:2017 pasal 10)", "-", "Kapasitas angkur Opsi B tidak dihitung.", "-", "belum ada di acuan"],
        ["ACI 350 dan EN 1992-3", "-", "Beton kedap air dan lebar retak.", "-", "belum ada di acuan"],
        ["EN 81-20", "-", "Dimensi pit lift, ruang bebas, buffer.", "-", "belum ada di acuan"],
        ["Membran HDPE dan aditif kristalin", "-", "Spesifikasi produk.", "-", "belum ada di acuan"],
        ["Penurunan urugan di bawah pit", "-", "Tanah tidak dipakai sebagai tumpuan; 2.8 memberi 0,15-1,18 m.", "-", "dari 2.8"],
    ], list("clllcl"))

    # ---- Petunjuk
    lb = Lembar(wb["Petunjuk"], 1, "Petunjuk desain pit lift (langkah 5.5)", [6, 130])
    lb.catatan(f"STATUS: {STATUS}. " + ket)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        "Tiga pit: L-1..4 (5,2 × 6,2), L-5..6 (4,6 × 2,3), L-7 (2,8 × 3,4); dinding 0,30 m, pelat dasar 0,40 m awal; fc' 35 MPa (S2), fy 420; selimut tanah 50, dalam 40 mm.",
        "Angkat: SNI 8460:2017 9.3.4 pada Q100 +12,31 (kasus ekstrem). Opsi A menebalkan pelat; Opsi B mengikat ke LT1, sloof, dan inti dengan angkur; keputusan di tangan Defsa.",
        "Struktur: pelat naik (tulangan atas), pelat turun dengan buffer (tulangan bawah, pons), dinding jepit-sendi (tekanan tanah dan air). Spasi mengikuti 24.3.2 (kedap).",
        "L-7 di tengah bay: banding dua balok penggantung ke sloof dengan pile cap dan tiang.",
        "Sel hijau diisi AI atas permintaan Defsa. Sel putih berisi rumus Excel (dihitung ulang dan dicocokkan dengan Python di cocokkan()).",
        "Lembar: Ringkasan; Data Lift; Angkat; Opsi A dan B; Kedap; Struktur; Dinding; Tumpuan; Jarak Sloof; Cek Silang T-94; Acuan.",
    ])], rata=list("cl"))

    for ws_ in wb:
        if ws_.title not in ("Petunjuk",):
            ws_.print_title_rows = None
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


def cocokkan(berkas=BERKAS):
    """Hitung ulang di Excel, lalu bandingkan rumus dengan Python. Kembalikan (ok, pesan)."""
    from format_dokumen import hitung_ulang_excel
    ok, err = hitung_ulang_excel(berkas)
    if not ok:
        return False, f"Excel tidak bisa menghitung ulang: {err[:120]}"
    r = hitung()
    wb = openpyxl.load_workbook(berkas, data_only=True)
    pesan, n_cek = [], 0
    for nama, rows in semua_baris(r).items():
        ws = wb[nama]
        for rw in rows:
            if rw["py"] is None:
                continue
            x = None
            for row in ws.iter_rows():
                for c in row:
                    if c.value == rw["label"]:
                        x = ws.cell(c.row, c.column + 1).value
            n_cek += 1
            if x is None or abs(x - rw["py"]) > max(1e-9, abs(rw["py"]) * 1e-6):
                pesan.append(f"{nama}/{rw['label']}: Excel {x} vs Python {rw['py']}")
    ws = wb["Cek Silang T-94"]
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and len(c.value) > 3 and c.value[0] == "(" and c.value[1] in "abcd" and c.value[2] == ")":
                st = ws.cell(c.row, c.column + 5).value
                n_cek += 1
                if st != "Lolos":
                    pesan.append(f"T-94 {c.value}: status {st}")
    return not pesan, "; ".join(pesan) or f"semua {n_cek} rumus/cek Excel cocok dengan Python"


def ke_pdf(berkas=BERKAS, pdf=None):
    return mri.ke_pdf(berkas, pdf)


# ------------------------------------------------------------------ ringkasan .md
def _md_baris(rows, n=4):
    return "\n".join("| " + " | ".join(str(c) for c in a[:n]) + " |" for a in rows)


def buat_md(keluar=KELUAR / "5.5 Desain Pit Lift.md"):
    r = hitung()
    x4 = r["t94"]
    a14, a56, a7 = (r["angkat"][k] for k in KODE)
    bk, tg = r["l7_balok"], r["l7_tiang"]
    judul = f"5.5 Desain Pit Lift ({STATUS})" if not KEPUTUSAN else f"5.5 Desain Pit Lift (disetujui Defsa {KEPUTUSAN.split(':')[0]})"
    s14 = r["pelat"]["L-1..4"]
    teks = f"""# {judul}

Disusun AI 21 Nov 2026. Data simulasi. Rincian angka di `5.5 Desain Pit Lift.xlsx` (`skrip/tahap5_pit_lift.py`, uji `tests/test_tahap5_pit_lift.py`).
Data lift dari lembar Lift (Data Beban MEP Rinci), muka air dari 3.3, sloof dari 5.4, pelat LT1 dari 5.3.

## Acuan (halaman = nomor halaman PDF)

SNI 8460:2017 Pasal 9.3.4 (hal 197) FK buoyancy; Pasal 12 (hal 279) butir b uplift besmen. SNI 2847:2019 Pasal 5.3.7-5.3.8 (hal 109-110) faktor H 1,6;
Tabel 19.3.2.1 (hal 464) kelas paparan; Tabel 20.6.1.3.1 (hal 482) selimut; Tabel 11.6.1 (hal 255) tulangan minimum dinding; 24.3.2 dan 24.3.5 (hal 573-574)
kontrol spasi untuk komponen kedap air; 22.5.5.1 (hal 507), 22.6.4.1 (hal 518), Tabel 22.6.5.2 (hal 521) geser; Tabel 21.2.1 (hal 491) φ.
Yang tidak ada di acuan ditulis "belum ada di acuan": kelas W2, pengangkuran izin (pasal 10 SNI 8460), ACI 350 dan EN 1992-3, EN 81-20, produk membran dan aditif kristalin.

## Sistem dan asumsi

Satu pit per kelompok lift; ruang dalam = gabungan shaft (L-1..4 5,2 × 6,2 m; L-5..6 4,6 × 2,3 m; L-7 2,8 × 3,4 m); dinding {idn(TW, 2)} m, pelat dasar {idn(TS0, 2)} m,
dinding sampai sisi bawah pelat LT1 +12,60. Urugan φ' 30°, γ 18, γsat 19 kN/m³, K0 0,50, tanpa beban tambahan. Pit digantung pada struktur; gesekan dinding diabaikan.
fc' 35 MPa (S2), fy 420, selimut 50 mm sisi tanah dan 40 mm sisi dalam [Asumsi 5.5].

## A. Angkat (SNI 8460:2017 9.3.4; muka air Q100 +12,31)

| Pit | Muka air | u (kPa) | U (kN) | W (kN) | FK utuh | FK pelat lepas | Status |
|---|---|---|---|---|---|---|---|
{_md_baris(teks_angkat(r), 8)}

Tahap konstruksi (hanya pelat dasar, muka air +11,20, dewatering terkendali): L-1..4 FK {idn(a14['tahap_konstruksi']['FK'], 2)}; L-5..6 {idn(a56['tahap_konstruksi']['FK'], 2)}; L-7 {idn(a7['tahap_konstruksi']['FK'], 2)}.
Pada Q100 pelat lepas FK {idn(a14['t']['q100']['FK_lepas'], 2)} (L-1..4): dewatering tidak boleh berhenti sebelum dinding dan LT1 mengikat.

**Opsi A dan B** (tanpa memilih):

| Pit | FK utuh t 0,40 | t min A (m) | t pakai A (m) | t lepas | R B (kN) | As stek B (mm²) | Batang | Beton tambah A (m³) |
|---|---|---|---|---|---|---|---|---|
{_md_baris(teks_opsi(r), 9)}

Opsi A: dasar pit tetap, pelat ditebalkan ke bawah (galian dan dewatering lebih dalam). Opsi B: pelat 0,40, tahanan izin angkur R = 1,5 U - W diikat ke LT1/sloof/inti;
As stek = 1,6 R / (0,9 fy). B2: pelat dasar L-1..4 menjadi sisi atas pile cap inti (Tahap 6). Kapasitas angkur: belum ada di acuan (SNI 8460 pasal 10).

## B. Kedap air

| Butir | Ketentuan | Sumber |
|---|---|---|
{_md_baris([[x[0], x[1], x[2]] for x in teks_kedap()], 3)}

## C. Struktur

Pelat naik qu = 1,6 u - 0,9 γc t, Navier tumpuan sederhana di sumbu dinding (tulangan atas); pelat turun 1,2 γc t + 1,6 buffer di pelat landasan 300 × 300 (tulangan bawah, tanpa tumpuan tanah).

| Pit | Bentang (m) | qu naik (kPa) | Mu naik (kNm/m) | Atas | Mu turun (kNm/m) | Bawah | Pons; tumpu | Status |
|---|---|---|---|---|---|---|---|---|
{_md_baris(teks_pelat(r), 9)}

Dinding (jepit di pelat, sendi di LT1, 1,6 H):

| Pit | H (m) | p atas / dasar (kPa) | M jepit | M lapangan | M kantilever | Vertikal | Horizontal | Geser |
|---|---|---|---|---|---|---|---|---|
{_md_baris(teks_dinding(r), 9)}

Tumpuan gravitasi:

| Pit | W (kN) | Buffer (kN) | Layan (kN) | Pu (kN) | U Q100 (kN) | W - U (kN) |
|---|---|---|---|---|---|---|
{_md_baris(teks_grav(r), 7)}

**L-7 (di tengah bay, jauh dari sloof)**: tanah tidak boleh jadi tumpuan (urugan masih turun 0,15-1,18 m, 2.8).

| Cara | Gaya | Tulangan | Volume | Status |
|---|---|---|---|---|
{_md_baris(teks_l7(r), 5)}

## D. Jarak ke sloof dan bukaan LT1

| Pit | Tapak luar (m) | Jarak muka ke muka sloof (m) | Sisi bawah pit; turun dari sloof (m) | Letak |
|---|---|---|---|---|
{_md_baris(teks_jarak(r), 5)}

| Pit | Bukaan (m) | Tulangan tepi | Penyaluran | Dasar |
|---|---|---|---|---|
{_md_baris(teks_bukaan(r), 5)}

## Cek silang T-94

| Cek | Cara 1 | Cara 2 | Selisih | Toleransi |
|---|---|---|---|---|
| (a) U L-1..4 Q100 | rumus {idn(x4['a']['rumus'], 2)} kN | grid {idn(x4['a']['grid'], 2)} kN | {sel_s(x4['a']['rumus'], x4['a']['grid'])} % | {idn(TOL['a'], 1)} % |
| (b) momen pelat naik | Navier {idn(x4['b']['navier'], 2)} kNm/m | PyNite {idn(x4['b']['pynite'], 2)} kNm/m | {sel_s(x4['b']['navier'], x4['b']['pynite'])} % | {idn(TOL['b'], 1)} % |
| (c) momen jepit dinding | rumus {idn(x4['c']['rumus'], 2)} kNm/m | PyNite {idn(x4['c']['pynite'], 2)} kNm/m | {sel_s(x4['c']['rumus'], x4['c']['pynite'])} % | {idn(TOL['c'], 1)} % |
| (d) t min Opsi A | tertutup {idn(x4['d']['tertutup'], 4)} m | bisection {idn(x4['d']['bisection'], 4)} m | {sel_s(x4['d']['tertutup'], x4['d']['bisection'])} % | {idn(TOL['d'], 1)} % |

## Data yang masih kurang

1. Kapasitas angkur (SNI 8460:2017 pasal 10) dan pile cap inti (Tahap 6) untuk Opsi B/B2.
2. Letak pit L-1..4 di dalam inti (asumsi tengah), dimensi pit dari pemasok lift (EN 81-20 belum ada di acuan).
3. Beban tambahan di permukaan tanah dan gesekan dinding (diabaikan); laju rembesan untuk pompa.
4. Penurunan urugan di bawah pit (tidak dipakai sebagai tumpuan).

## Pilihan untuk Defsa

1. **Angkat**: Opsi A (pelat L-1..4 t {idn(a14['tmin_bulat'], 2)} m, tanpa angkur) atau Opsi B (t 0,40 dengan angkur R {idn(a14['R'], 0)} kN diikat ke LT1/sloof/inti; varian B2 pelat dasar sebagai sisi atas pile cap inti, Tahap 6).
2. **Tumpuan L-7**: dua balok penggantung ke sloof ({idn(bk['pilih']['b'] * 1000, 0)} × {idn(bk['pilih']['h'] * 1000, 0)}, {bk['pilih']['n29']} D29) atau pile cap dan {tg['n']} tiang Ø800.
3. **Lapisan kedap**: aditif kristalin atau membran HDPE pra-pasang.

(Pilihan di atas berdasar angka di atas; keputusan di tangan Defsa.)

## Keputusan Defsa

Belum ada.
"""
    if KEPUTUSAN:
        teks = teks.replace("Belum ada.\n", KEPUTUSAN + "\n")
    keluar.write_text(teks, encoding="utf-8")
    return keluar


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(buat_excel())
    print(cocokkan())
    print(buat_md())
