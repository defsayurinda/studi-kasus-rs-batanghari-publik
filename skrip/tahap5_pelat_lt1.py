"""Tahap 5 langkah 5.3: desain pelat LT1 (+12,85), panel MRI 9-10/D-E, beban transit magnet, tulangan tahan karat, getaran.

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (21 Nov 2026); disetujui Defsa 21 Nov 2026 (semua usulan AI); sebelumnya draf menunggu persetujuan
Defsa. Kunci jawaban tidak dibuka. Data dari `04 Struktur Atas/Data Owner/Data Beban MEP Rinci.xlsx` (via `tahap5_mri`,
`tahap5_telaah`), beban dari `tahap4_beban`, metode desain langsung dari `tahap4_pelat` (argumen selimut, fc', balok baru).

Metode:
- PL-1 (pelat umum LT1 dengan sloof 400 x 800): metode desain langsung SNI 2847:2019 Pasal 8.10; hmin Tabel 8.3.1.2.
- Panel MRI (PL-2): DDM beban merata + tambahan beban titik (roda transit, kaki magnet) dari pelat tumpuan sederhana
  (deret Navier beban persegi, PyNite sebagai pembanding) untuk momen positif; momen negatif tambahan dari pelat
  tiga tepi jepit satu tepi sendi (PyNite). Penjumlahan puncak = konservatif.
- Pons dan tumpu: SNI 2847:2019 Pasal 22.6.5.2 dan 22.8.3.2. Tulangan tahan karat: Pasal 25.4.2 dan 25.5.2, massa SNI 2052:2017.
- Getaran: teori pelat dan SDOF seperti 5.2 [Asumsi: buku dinamika belum ada di acuan].
Pasal yang tidak ada di acuan ditulis persis "belum ada di acuan".
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
import tahap3_zonasi as tz  # noqa: E402
import tahap4_beban as tb  # noqa: E402
import tahap4_pelat as tp  # noqa: E402
import tahap5_mri as mri  # noqa: E402
import tahap5_telaah as ts  # noqa: E402
from tahap5_mri import R, idn  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "05 Struktur Tengah"
BERKAS = KELUAR / "5.3 Desain Pelat LT1.xlsx"
LABEL = mri.LABEL
STATUS = "disetujui Defsa 21 Nov 2026 (fc' 35, selimut bawah 50, opsi A monolit 250, arsip dibatasi zona)"
LABEL_AI = f"DIISI AI ATAS PERMINTAAN DEFSA (21 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."
KEPUTUSAN = ("21 Nov 2026: semua usulan AI disetujui. (1) Pelat LT1 dan sloof **fc' 35 MPa** (paparan S2, SNI 2847:2019 "
             "Tabel 19.3.2.1: w/cm maks 0,45, fc' min 31 MPa). (2) Selimut bawah **50 mm** dengan void former/lantai kerja "
             "(Tabel 20.6.1.3.1), atas 20 mm. (3) Panel MRI 9-10/D-E **opsi A monolit 250** tanpa sambungan isolasi "
             "(fn 11,67 Hz; B 300 beresonansi dengan M-01 14,5 Hz; C menurunkan F izin M-04 ke 15,4 N); R-06 tetap di atas "
             "pegas. (4) Beban arsip rekam medis padat 7,18 kPa **dibatasi pada zonanya** (tidak untuk seluruh LT1); zona "
             "arsip ditetapkan di Tahap 7 dan panelnya dicek lokal. Tulangan D13-200 atas dan bawah; pelat penyebar transit "
             "tidak perlu; baja tahan karat A955M 144,6 kg. Langkah berikutnya: 5.4 sloof dan tie beam.")

G = mri.G
H = 0.250                    # m, tebal pelat LT1 [Data keputusan 5.3 dari Defsa/rencana]
FC, FY = 35.0, 420.0         # MPa; fc' 35 = kelas paparan S2 (keputusan 2.7; Tabel 19.3.2.1: w/cm <= 0,45, fc' >= 31)
SEL_B, SEL_A = 0.050, 0.020  # m, selimut bawah (tanah + 10 mm asam) dan atas
DB = 0.013                   # m, D13
BW, HB = 0.400, 0.800        # m, sloof
KOL = 0.750                  # m, kolom tipikal podium
L = 8.0
NU, ZETA = mri.NU, mri.ZETA
EC = 4700 * math.sqrt(FC)    # MPa (Pasal 19.2.2.1)
LO_PL1, LO_PL2 = 4.79, 2.87
SIDL_LT1 = tb.SIDL["keramik"][0] + tb.SIDL["partisi"][0]    # tanpa plafon dan gantung (tidak ada ruang di bawah LT1)
Q_RF = 27.5 / 42.0
P_RODA = 48.1 / 4            # kN per roda [Asumsi: 4 roda/skate]
C_RODA = 0.150               # m, tapak roda [Asumsi]
XC0, XC1, YT = 83.4, 80.5, 57.0   # pusat kelompok roda: awal (roda belakang di tepi gedung), isocenter; lintasan y
OFF_RODA = 0.600             # m, roda di xc +- 0,6 dan y +- 0,6 [Asumsi: segi empat 1,2 x 1,2 m]
KAKI_DX, KAKI_DY = 0.80, 0.60   # m [Asumsi: jarak kaki dari isocenter arah x dan y]
PANEL_X0, PANEL_Y0 = 76.0, 51.0  # sudut barat-selatan panel 9-10/D-E
CELAH = 0.025                # m [Asumsi: celah sambungan isolasi]
SH_LT1 = ("SH-1", "SH-2", "SH-3", "SH-5", "SH-6")
LEBAR_ZONA = 2.0
ZONA_TK = (79.5, 81.5, 56.0, 58.0)


# ------------------------------------------------------------------ pelat: pembantu
def as_perlu(mu, d, fc=FC):
    """As (mm2/m) dari Mu (kNm/m), blok persegi, phi 0,9 (Pasal 22.2.2.4, Tabel 21.2.1)."""
    mn = mu / 0.9
    a = 0.85 * fc * 1000
    akar = d * d - 2 * mn / a
    return 1e6 * a / (FY * 1000) * (d - math.sqrt(max(akar, 0.0)))


def phimn(as_mm2, d, fc=FC):
    return 0.9 * as_mm2 * 1e-6 * FY * 1000 * (d - as_mm2 * 1e-6 * FY / (1.7 * fc))


def d_eff(sel, lapis2=True):
    return H - sel - DB / 2 - (DB if lapis2 else 0.0)


def pilih_s(mu, sel, db=13, h=H, fc=FC):
    """Spasi D13 (kelipatan 25 mm, s <= 2h dan 450; Pasal 8.7.2.2) yang cukup untuk Mu; bila s < 75 -> D16."""
    d = d_eff(sel)
    as_min = max(0.0018 * 420 / FY, 0.0014) * h * 1e6
    perlu = max(as_perlu(mu, d, fc), as_min)
    smaks = min(2 * h * 1000, 450.0)
    for dia in (db, 16):
        ab = math.pi * dia ** 2 / 4
        for s in (smaks, 200, 175, 150, 125, 100, 75):
            s = min(s, smaks)
            if 1000 * ab / s >= perlu and phimn(1000 * ab / s, d, fc) >= mu:
                return {"db": dia, "s": s, "as_ada": 1000 * ab / s, "as_perlu": perlu, "phimn": phimn(1000 * ab / s, d, fc), "d": d}
    return {"db": 16, "s": 75, "as_ada": 1000 * math.pi * 16 ** 2 / 4 / 75, "as_perlu": perlu, "phimn": 0.0, "d": d}


# ------------------------------------------------------------------ pelat: beban titik (Navier dan PyNite)
def navier_koef(beban, a=L, nu=NU, n=200):
    """Koefisien deret Navier (Cx, Cy) untuk kumpulan beban persegi [(P, u, v, xi, eta)] di pelat a x a tumpuan sederhana;
    Mx(x, y) = sum Cx[m, k] sin(m pi x / a) sin(k pi y / a)."""
    m = np.arange(1, n + 1)[:, None]
    k = np.arange(1, n + 1)[None, :]
    den = np.pi ** 4 * ((m ** 2 + k ** 2) / a ** 2) ** 2
    q = 0.0
    for (P, u, v, xi, eta) in beban:
        q = q + 16 * (P / (u * v)) / (np.pi ** 2 * m * k) * np.sin(m * np.pi * xi / a) * np.sin(k * np.pi * eta / a)             * np.sin(m * np.pi * u / (2 * a)) * np.sin(k * np.pi * v / (2 * a))
    return q * ((m * np.pi / a) ** 2 + nu * (k * np.pi / a) ** 2) / den, q * ((k * np.pi / a) ** 2 + nu * (m * np.pi / a) ** 2) / den


def _sin(x, a, n):
    return np.sin(np.arange(1, n + 1)[:, None] * np.pi * np.atleast_1d(x)[None, :] / a)


def navier_mom(P, a, u, v, xi, eta, x, y, nu=NU, n=200):
    """Momen (Mx, My) kNm/m di (x, y) akibat satu beban persegi u x v total P (kN) berpusat di (xi, eta)."""
    cx, cy = navier_koef([(P, u, v, xi, eta)], a, nu, n)
    sx, sy = _sin(x, a, n), _sin(y, a, n)
    return float((sx.T @ cx @ sy)[0, 0]), float((sx.T @ cy @ sy)[0, 0])


def navier_maks(beban, a=L, n=200, langkah=0.05):
    """Momen positif maksimum (kNm/m) dan lokasinya pada kisi di sekitar kumpulan beban [(P, u, v, xi, eta)]."""
    cx, cy = navier_koef(beban, a, NU, n)
    xs = np.arange(max(0.05, min(b[3] for b in beban) - 0.6), min(a - 0.05, max(b[3] for b in beban) + 0.6) + 1e-9, langkah)
    ys = np.arange(max(0.05, min(b[4] for b in beban) - 0.6), min(a - 0.05, max(b[4] for b in beban) + 0.6) + 1e-9, langkah)
    sx, sy = _sin(xs, a, n), _sin(ys, a, n)
    mm = np.maximum(sx.T @ cx @ sy, sx.T @ cy @ sy)
    i, j = np.unravel_index(np.argmax(mm), mm.shape)
    return float(mm[i, j]), (float(xs[i]), float(ys[j]))


def pynite_model(h, ec_mpa, mesh, pressures, jepit=False, a=L):
    """Pelat a x a, elemen PyNite; tepi tumpuan sederhana, atau jepit di x=0, y=0, y=a dan sendi di x=a (jepit=True).
    pressures: [(i, j, kPa)] tekanan merata di elemen (i, j), positif ke bawah."""
    from Pynite import FEModel3D
    e = ec_mpa * 1000.0
    m = FEModel3D()
    m.add_material("c", e, e / (2 * (1 + NU)), NU, 23.6)
    n = int(round(a / mesh))
    for i in range(n + 1):
        for j in range(n + 1):
            m.add_node(f"N{i}_{j}", i * mesh, j * mesh, 0.0)
    for i in range(n):
        for j in range(n):
            m.add_quad(f"Q{i}_{j}", f"N{i}_{j}", f"N{i + 1}_{j}", f"N{i + 1}_{j + 1}", f"N{i}_{j + 1}", h, "c")
    for i in range(n + 1):
        for j in range(n + 1):
            tepi = i in (0, n) or j in (0, n)
            rot = jepit and (i == 0 or j in (0, n))
            m.def_support(f"N{i}_{j}", True, True, tepi, rot, rot, True)
    for (i, j, p) in pressures:
        m.add_quad_surface_pressure(f"Q{i}_{j}", -p, case="D")
    m.add_load_combo("U", {"D": 1.0})
    m.analyze_linear(check_statics=False, sparse=True)
    return m, n


def _mq(m, i, j):
    q = m.quads[f"Q{i}_{j}"].moment(0.0, 0.0, combo_name="U")
    return float(q[0][0]), float(q[1][0])


def pynite_roda(xc, yc, jepit, mesh=0.25, ec=EC):
    """Empat roda (P_RODA, faktor 1,6) di xc +- OFF_RODA, yc +- OFF_RODA (koordinat lokal panel), tekanan pada elemen terdekat."""
    tek = []
    for dx in (-OFF_RODA, OFF_RODA):
        for dy in (-OFF_RODA, OFF_RODA):
            nn = int(round(L / mesh))
            i, j = min(int((xc + dx) // mesh), nn - 1), min(int((yc + dy) // mesh), nn - 1)
            tek.append((i, j, 1.6 * P_RODA / mesh ** 2))
    m, n = pynite_model(H, ec, mesh, tek, jepit=jepit)
    ms = [_mq(m, i, j) for i in range(n) for j in range(n)]
    if not jepit:
        return max(max(abs(a), abs(b)) for a, b in ms)
    w = max(abs(_mq(m, 0, j)[0]) for j in range(n))
    sb = max(abs(_mq(m, i, 0)[1]) for i in range(n))
    nb = max(abs(_mq(m, i, n - 1)[1]) for i in range(n))
    return max(w, sb, nb)


# ------------------------------------------------------------------ getaran pelat (seperti 5.2)
def getar_pelat(h, fc, a, b, mi, m_tambah=0.0, jepit=False):
    ec = 4700 * math.sqrt(fc)
    D = ec * 1e6 * h ** 3 / (12 * (1 - NU ** 2))
    m = mri.RHO_BETON * h + m_tambah
    fn = math.pi / 2 * (1 / a ** 2 + 1 / b ** 2) * math.sqrt(D / m)
    if jepit:
        fn *= 1.823      # pelat persegi jepit semua tepi / tumpuan sederhana (35,99 / 19,74) [Asumsi: teori pelat]
    mm = m * a * b / 4
    ab = mi["a_batas_mg"] * 1e-3 * G
    out = {"h": h, "ec": ec, "D": D, "m": m, "fn": fn, "mm": mm}
    for kode, f in (("M-04", mi["f_m04"]), ("R-06", mi["f_r06"]), ("M-01", mi["f_m01_kipas"])):
        hh = mri.respons_h(f, fn, ZETA)
        out[kode] = {"f": f, "r": f / fn, "H": hh, "F": ab * mm / hh}
    return out


# ------------------------------------------------------------------ hitung semua
@functools.lru_cache(maxsize=1)
def hitung():
    mi = mri.baca_masukan()
    r = {"mi": mi}
    # ---- beban dan PL-1
    d_mati = tb.GAMMA_C * H + SIDL_LT1
    qu1 = max(1.4 * d_mati, 1.2 * d_mati + 1.6 * LO_PL1)
    p1 = tp.desain_panel("PL-1", "LT1 umum Lo 4,79", H, SIDL_LT1, LO_PL1, KOL, selimut=SEL_B, selimut_atas=SEL_A,
                         fc=FC, bw=BW, hb=HB)
    ln = L - KOL
    mo = qu1 * L * ln ** 2 / 8
    r["pl1"] = {"D": d_mati, "qu": qu1, "ln": ln, "Mo": mo, "p": p1, "af": p1["af"], "hmin": p1["hmin"],
                "hmin_tepi": p1["hmin_tepi"], "Vu": p1["Vu"], "phiVc": p1["phiVc"], "w_diri": tb.GAMMA_C * H}
    baris1 = []
    for b in p1["baris"]:
        sel = SEL_B if b["posisi"] == "pos" else SEL_A
        pl = pilih_s(b["Mu"], sel)
        baris1.append({**b, "sel": sel, "d13": pl["d"], "s13": pl["s"], "db13": pl["db"], "as13": pl["as_ada"], "phimn13": pl["phimn"],
                       "as_min13": max(0.0018 * 420 / FY, 0.0014) * H * 1e6})
    r["pl1"]["baris"] = baris1
    # ---- alternatif selimut bawah 75 (cor langsung di tanah) dan fc' 35 pada panel tipikal
    alt = {}
    for sel in (0.050, 0.075):
        pa = [b for b in baris1 if b["posisi"] == "pos" and b["lajur"] == "tengah" and b["bentang"] == "ujung"][0]
        d = d_eff(sel)
        as_ = max(as_perlu(pa["Mu"], d), pa["as_min13"])
        pl = pilih_s(pa["Mu"], sel)
        alt[sel] = {"d": d, "as": as_, "s": pl["s"], "as_ada": pl["as_ada"], "Mu": pa["Mu"]}
    r["alt_sel"] = alt
    # ---- panel MRI PL-2 (beban merata)
    d2 = tb.GAMMA_C * H + SIDL_LT1 + Q_RF
    qu2 = max(1.4 * d2, 1.2 * d2 + 1.6 * LO_PL2)
    p2 = tp.desain_panel("PL-2", "Panel MRI 9-10/D-E", H, SIDL_LT1 + Q_RF, LO_PL2, KOL, selimut=SEL_B, selimut_atas=SEL_A,
                         fc=FC, bw=BW, hb=HB)
    uj = [b for b in p2["baris"] if b["bentang"] == "ujung"]
    pos_ddm = max(b["Mu"] for b in uj if b["posisi"] == "pos")
    neg_ddm = max(b["Mu"] for b in uj if b["posisi"] != "pos")
    r["pl2"] = {"D": d2, "qu": qu2, "p": p2, "pos_ddm": pos_ddm, "neg_ddm": neg_ddm, "skala_tr": 1.2 * d2 / qu2}
    # ---- transit magnet: Navier (persegi 0,15) tiap 0,05 m dan PyNite di beberapa posisi
    ptn = []
    xs_nav = np.arange(XC0, XC1 - 1e-9, -0.05)
    yl = YT - PANEL_Y0
    nav = []
    for xc in xs_nav:
        xl = xc - PANEL_X0
        bb = [(P_RODA * 1.6, C_RODA, C_RODA, xl + dx, yl + dy) for dx in (-OFF_RODA, OFF_RODA) for dy in (-OFF_RODA, OFF_RODA)]
        nav.append((float(xc), navier_maks(bb, langkah=0.05)))
    xc_w, (m_nav, pos_nav) = max(nav, key=lambda t: t[1][0])
    r["transit"] = {"nav": nav, "xc_w": xc_w, "m_nav": m_nav, "pos_nav": (pos_nav[0] + PANEL_X0, pos_nav[1] + PANEL_Y0)}
    pyn = []
    for xc in (83.4, 82.7, 82.0, 81.3, 80.6):
        a_ = pynite_roda(xc - PANEL_X0, yl, False)
        b_ = pynite_roda(xc - PANEL_X0, yl, True)
        pyn.append((xc, a_, b_))
    r["transit"]["pyn"] = pyn
    r["transit"]["m_pyn"] = max(t[1] for t in pyn)
    r["transit"]["neg_pyn"] = max(t[2] for t in pyn)
    r["transit"]["m_pos"] = max(m_nav, r["transit"]["m_pyn"])
    # ---- kaki magnet (operasi): 4 kaki 12 kN faktor 1,2, persegi 0,25
    xl0, yl0 = mi["iso"][0] - PANEL_X0, mi["iso"][1] - PANEL_Y0
    kaki = [(1.2 * mi["p_kaki"], mi["kaki_a"], mi["kaki_b"], xl0 + dx, yl0 + dy) for dx in (-KAKI_DX, KAKI_DX) for dy in (-KAKI_DY, KAKI_DY)]
    m_kaki, pos_kaki = navier_maks(kaki)
    r["kaki"] = {"M": m_kaki, "pos": (pos_kaki[0] + PANEL_X0, pos_kaki[1] + PANEL_Y0)}
    # ---- kebutuhan momen total panel MRI: dua kombinasi
    op_pos = pos_ddm + m_kaki
    tr_pos = pos_ddm * r["pl2"]["skala_tr"] + r["transit"]["m_pos"]
    op_neg = neg_ddm
    tr_neg = neg_ddm * r["pl2"]["skala_tr"] + r["transit"]["neg_pyn"]
    r["pl2"].update({"op_pos": op_pos, "tr_pos": tr_pos, "op_neg": op_neg, "tr_neg": tr_neg,
                     "mu_pos": max(op_pos, tr_pos), "mu_neg": max(op_neg, tr_neg)})
    r["pl2"]["pos_gov"] = "transit" if tr_pos >= op_pos else "operasi"
    r["pl2"]["neg_gov"] = "transit" if tr_neg >= op_neg else "operasi"
    # tulangan terpilih: bawah (positif), atas (negatif); pembanding D13-200 bawaan
    pb, pa = pilih_s(r["pl2"]["mu_pos"], SEL_B), pilih_s(r["pl2"]["mu_neg"], SEL_A)
    r["pl2"]["bawah"], r["pl2"]["atas"] = pb, pa
    r["pl2"]["s200_phimn"] = phimn(1000 * math.pi * 13 ** 2 / 4 / 200, d_eff(SEL_B))
    for sel in (0.050, 0.075):
        d_ = d_eff(sel)
        alt[sel]["pl2_as"] = as_perlu(r["pl2"]["mu_pos"], d_)
        alt[sel]["pl2_phimn"] = phimn(1000 * math.pi * 13 ** 2 / 4 / 200, d_)
        alt[sel]["pl2_rasio"] = r["pl2"]["mu_pos"] / alt[sel]["pl2_phimn"]
        alt[sel]["pl2_s"] = pilih_s(r["pl2"]["mu_pos"], sel)["s"]
    # pelat penyebar: ukuran persegi per roda (m) agar D13-200 bawah cukup
    peny = []
    for c in (0.15, 0.30, 0.50, 0.80, 1.00, 1.20):
        xl = r["transit"]["xc_w"] - PANEL_X0
        bb = [(P_RODA * 1.6, c, c, xl + dx, yl + dy) for dx in (-OFF_RODA, OFF_RODA) for dy in (-OFF_RODA, OFF_RODA)]
        mm_, _ = navier_maks(bb)
        tot = pos_ddm * r["pl2"]["skala_tr"] + mm_
        peny.append({"c": c, "M": mm_, "total": tot, "ok200": tot <= r["pl2"]["s200_phimn"]})
    r["penyebar"] = peny
    # ---- pons dan tumpu: kaki magnet (ulang 5.2) dan satu roda
    d_p = H * 1000 - SEL_B * 1000 - DB * 1000
    def pons(c_mm, vu):
        b0 = 4 * (c_mm + d_p)
        k = mri.vc_koef(b0, d_p)
        pv = 0.75 * k * math.sqrt(FC) * b0 * d_p / 1000
        return {"c": c_mm, "b0": b0, "k": k, "phivc": pv, "vu": vu, "rasio": vu / pv}
    r["pons_kaki"] = pons(mi["kaki_a"] * 1000, 1.2 * mi["p_kaki"])
    r["pons_roda"] = pons(C_RODA * 1000, 1.6 * P_RODA)
    r["tumpu"] = {"q": mi["p_kaki"] / (mi["kaki_a"] * mi["kaki_b"]), "phi": 0.65 * 0.85 * FC * 1000}
    r["tumpu"]["rasio"] = 1.2 * r["tumpu"]["q"] / r["tumpu"]["phi"]
    r["tumpu"]["q_roda"] = P_RODA / C_RODA ** 2
    r["tumpu"]["rasio_roda"] = 1.6 * r["tumpu"]["q_roda"] / r["tumpu"]["phi"]
    r["pons_roda"]["d"] = d_p
    # ---- SH-6 dan lubang LT1 lain
    wb = openpyxl.load_workbook(ts.MEP, data_only=True)
    sh = {x["Kode"]: x for x in ts.baca_baris(wb, "Shaft dan Lubang")}
    lub = []
    for kode in SH_LT1:
        x = sh[kode]
        x0, x1 = ts.parse_rentang(x["x (m)"])
        y0, y1 = ts.parse_rentang(x["y (m)"])
        pak = r["pl2"] if kode == "SH-6" else None
        s_b = pak["bawah"]["s"] if pak else [b for b in baris1 if b["bentang"] == "interior" and b["posisi"] == "pos" and b["lajur"] == "tengah"][0]["s13"]
        s_a = pak["atas"]["s"] if pak else [b for b in baris1 if b["bentang"] == "interior" and b["posisi"] == "neg_int" and b["lajur"] == "tengah"][0]["s13"]
        ab = math.pi * 13 ** 2 / 4
        a_, b_ = x1 - x0, y1 - y0
        n_b = max(2, math.ceil(a_ * 1000 / s_b * ab / 2 / ab)), max(2, math.ceil(b_ * 1000 / s_b * ab / 2 / ab))
        lub.append({"kode": kode, "x": (x0, x1), "y": (y0, y1), "a": a_, "b": b_, "s_b": s_b, "s_a": s_a,
                    "n_x": n_b[0], "n_y": n_b[1], "uraian": str(x["Fungsi"]), "tembus": str(x["Lantai tembus"])})
    r["lubang"] = lub
    sh6 = [x for x in lub if x["kode"] == "SH-6"][0]
    iso = mi["iso"]
    sh6["jarak_iso"] = ts.jarak_titik_ke_kotak(iso[0], iso[1], sh6["x"][0], sh6["x"][1], sh6["y"][0], sh6["y"][1])
    sh6["di_zona"] = mri.tumpang(ZONA_TK, (sh6["x"][0], sh6["x"][1], sh6["y"][0], sh6["y"][1]))
    sh6["jarak_roda_y"] = (YT - OFF_RODA - C_RODA / 2) - sh6["y"][1]
    r["sh6_di_bukaan"] = [k for k, *_ in tp.BUKAAN].count("SH-6")
    # ---- baja tahan karat (zona 2,0 x 2,0)
    ld = FY / (2.1 * math.sqrt(FC)) * 13
    lap = 1.3 * ld
    pakai = math.ceil(lap / 10) * 10
    pj = LEBAR_ZONA + 2 * pakai / 1000
    sb, sa = pb["s"], pa["s"]
    nb_b, nb_a = math.ceil(LEBAR_ZONA * 1000 / sb) + 1, math.ceil(LEBAR_ZONA * 1000 / sa) + 1
    jml = 2 * nb_b + 2 * nb_a
    massa = jml * pj * mri.MASSA_BAJA["D13"]
    r["tk"] = {"ld": ld, "lap": lap, "pakai": pakai, "pj": pj, "s_b": sb, "s_a": sa, "nb_b": nb_b, "nb_a": nb_a, "jml": jml,
               "massa": massa, "massa_52": 148.26}
    # ---- getaran: opsi A, B, C
    m_rf = mi["berat_rf"] * 1000 / (mi["rf"][0] * mi["rf"][1]) / G
    opsi = {}
    opsi["A"] = getar_pelat(H, FC, 8.0, 8.0, mi, m_rf)
    opsi["A"]["fn_jepit"] = opsi["A"]["fn"] * 1.823
    opsi["A"]["H_jepit"] = {k: mri.respons_h(opsi["A"][k]["f"], opsi["A"]["fn_jepit"], ZETA) for k in ("M-04", "R-06", "M-01")}
    opsi["B30"] = getar_pelat(0.30, FC, 8.0, 8.0, mi, m_rf)
    opsi["B35"] = getar_pelat(0.35, FC, 8.0, 8.0, mi, m_rf)
    opsi["C"] = getar_pelat(H, FC, 7.0, 6.0, mi, m_rf)
    r["getar"] = opsi
    r["m_rf"] = m_rf
    # opsi C: balok tambahan
    pj_c = 6.0 + 7.0 + 7.0
    r["isolasi"] = {"panjang": pj_c, "luas_bawah": BW * (HB - H), "vol": pj_c * BW * (HB - H), "vol_penuh": pj_c * BW * HB,
                    "celah": CELAH}
    # ---- alat berat LT1
    q_izin = (qu1 - 1.2 * d_mati) / 1.2
    p_ddm_tg = [b for b in baris1 if b["bentang"] == "interior" and b["posisi"] == "pos" and b["lajur"] == "tengah"][0]
    skala = 1.2 * d_mati / qu1
    cap = p_ddm_tg["phimn13"]
    alat = []
    for it in ts.baca_item():
        lt = it["lantai"]
        if not lt.startswith("LT1") or it["lembar"] == "Lift" or it["lembar"] == "Shaft dan Lubang":
            continue
        raw = it["raw"]
        kode = it["kode"]
        if kode in ("R-04", "R-09"):
            continue
        w = float(raw.get("Berat per unit (kN)") or raw.get("Berat operasi per unit (kN)"))
        n = int(raw["Jumlah"])
        x0, x1 = it["x"]
        y0, y1 = it["y"]
        tap = str(raw.get("Tapak (m)") or raw.get("Tapak p × l (m)"))
        a_, b_ = [float(s.replace(",", ".")) for s in tap.replace("rel ", "").split("×")[:2]] if "×" in tap else (0, 0)
        if kode == "R-03":
            continue
        if kode == "R-05":
            a_, b_ = mi["rf"]
        if kode == "R-07":
            alat.append({"kode": kode, "uraian": it["uraian"], "n": n, "w": w, "a": 0, "b": 0, "q": 0.0, "izin": q_izin,
                         "ket": "digantung ke pelat LT2: tidak membebani LT1", "M": 0.0, "rasio": 0.0})
            continue
        q = w / (a_ * b_)
        flag = q > q_izin
        mu, rasio = 0.0, 0.0
        if flag:
            mx, _ = navier_mom(1.2 * w, L, min(a_, 3.0), min(b_, 3.0), 4.0, 4.0, 4.0, 4.0)
            mu = p_ddm_tg["Mu"] * skala + mx
            rasio = mu / cap
        alat.append({"kode": kode, "uraian": it["uraian"], "n": n, "w": w, "a": a_, "b": b_, "q": q, "izin": q_izin,
                     "ket": "perlu cek lokal" if flag else "tercakup beban rencana", "M": mu, "rasio": rasio})
    r["alat"] = alat
    r["alat_izin"] = q_izin
    r["alat_cap"] = cap
    # ---- dinding pelindung utara di panel 9-10/E-F dan timur ke sloof as 10
    w_n = 1.2 * mi["berat_pelindung"] / sum(mi["dinding"])
    a_, b_ = 1.0, L - 1.0
    m_neg = w_n * a_ * b_ ** 2 / L ** 2
    p_atas = [b for b in baris1 if b["bentang"] == "interior" and b["posisi"] == "neg_int" and b["lajur"] == "tengah"][0]
    mu_tot = p_atas["Mu"] + m_neg
    pl = pilih_s(mu_tot, SEL_A)
    r["pelindung"] = {"w": mi["berat_pelindung"] / sum(mi["dinding"]), "wu": w_n, "M": m_neg, "Mu_ddm": p_atas["Mu"], "Mu_tot": mu_tot,
                      "phimn": p_atas["phimn13"], "s_baru": pl["s"], "as_baru": pl["as_ada"], "timur": mi["berat_pelindung"] / sum(mi["dinding"]) * mi["dinding"][1],
                      "ada_cukup": p_atas["phimn13"] >= mu_tot}
    # ---- cek silang T-92
    nb_ = r["pl1"]
    r["t92"] = {}
    # (a) qu dan Mo PL-1 tangan: D = 23,6 x 0,25 + 1,10 + 1,00
    qu_t = 1.2 * (23.6 * 0.25 + 1.10 + 1.00) + 1.6 * 4.79
    mo_t = qu_t * 8.0 * (8.0 - 0.75) ** 2 / 8
    r["t92"]["a"] = {"qu_tangan": qu_t, "qu_skrip": qu1, "mo_tangan": mo_t, "mo_skrip": mo}
    # (b) beban persegi 0,8 x 0,8 di tengah, P 48,1 kN: PyNite mesh 0,2 vs Navier (rata-rata 4 elemen tengah)
    mesh = 0.2
    c4 = [(19, 19), (19, 20), (20, 19), (20, 20)]
    m_, n_ = pynite_model(H, EC, mesh, [(i, j, 48.1 / 0.64) for i in range(18, 22) for j in range(18, 22)])
    py_b = float(np.mean([abs(_mq(m_, i, j)[0]) for i, j in c4]))
    nv_b = float(np.mean([navier_mom(48.1, 8.0, 0.8, 0.8, 4.0, 4.0, 4.0 + dx, 4.0 + dy)[0] for dx in (-0.1, 0.1) for dy in (-0.1, 0.1)]))
    r["t92"]["b"] = {"pynite": py_b, "navier": nv_b}
    # (c) pons satu roda tangan: d = 250 - 50 - 13 = 187; b0 = 4 (150 + 187); phi Vc = 0,75 x 0,33 sqrt(35) b0 d / 1000
    d_t = 187.0
    b0_t = 4 * (150.0 + d_t)
    r["t92"]["c"] = {"tangan": 0.75 * 0.33 * math.sqrt(35.0) * b0_t * d_t / 1000, "skrip": r["pons_roda"]["phivc"]}
    # (d) massa baja tahan karat tangan (jumlah batang dan lewatan 580 mm dihitung sendiri)
    r["t92"]["d"] = {"tangan": 44 * 3.16 * 1.04, "skrip": massa, "m52": 148.26}
    return r


# ------------------------------------------------------------------ lembar Excel: baris
def baris_beban(r):
    p = r["pl1"]
    a = [
        R("gc", "Berat jenis beton bertulang", tb.GAMMA_C, "kN/m³", "", "SNI 1727:2020 Tabel C3.1-2 (4.2)", "0.0"),
        R("h", "Tebal pelat LT1", H * 1000, "mm", "struktural, ditumpu sloof", "[Keputusan 5.3: pelat 250 mm]", "0"),
        R("wd", "Berat sendiri pelat", "={gc}*{h}/1000", "kPa", "", "", "0.00", p["w_diri"]),
        R("kera", "Keramik 19 mm + spesi 25 mm", tb.SIDL["keramik"][0], "kPa", "", "SNI 1727:2020 Tabel C3.1-1 (4.2)", "0.00"),
        R("part", "Partisi", tb.SIDL["partisi"][0], "kPa", "tanpa plafon dan gantung: tidak ada ruang di bawah LT1", "[Asumsi 4.2]", "0.00"),
        R("D", "Beban mati D", "={wd}+{kera}+{part}", "kPa", "", "", "0.00", p["D"]),
        R("Lo", "Beban hidup PL-1 (lobi dan koridor lantai pertama)", LO_PL1, "kPa", "100 psf = 4,79 kPa",
          "SNI 1727:2020 Tabel 4.3-1 (hal PDF 52); [Asumsi: lobi dan koridor lantai pertama perkantoran dipakai untuk RS]", "0.00"),
        R("qu1", "qu = maks(1,4 D; 1,2 D + 1,6 L)", "=MAX(1.4*{D},1.2*{D}+1.6*{Lo})", "kPa", "", "SNI 2847:2019 Tabel 5.3.1 (hal PDF 106)", "0.000", p["qu"]),
        R("Lo2", "Beban hidup PL-2 (panel MRI; ruang operasi/laboratorium)", LO_PL2, "kPa", "60 psf = 2,87 kPa", "SNI 1727:2020 Tabel 4.3-1 (hal PDF 52)", "0.00"),
        R("qrf", "Sangkar RF merata (27,5 kN / 42 m²)", "=27.5/42", "kPa", "", "[Alat Medis R-05]; SNI 1727:2020 Pasal 3.1.3", "0.000", Q_RF),
        R("D2", "Beban mati panel MRI D = D + sangkar RF", "={D}+{qrf}", "kPa", "", "", "0.000", r["pl2"]["D"]),
        R("qu2", "qu panel MRI", "=MAX(1.4*{D2},1.2*{D2}+1.6*{Lo2})", "kPa", "", "", "0.000", r["pl2"]["qu"]),
    ]
    return [("A", "Beban pelat LT1 dan panel MRI", a)]


def baris_panel(r):
    p = r["pl1"]
    a = [
        R("L", "Bentang as-ke-as", L, "m", "grid 8 x 8", "[3.6, tahap4_beban.GRID]", "0.0"),
        R("kol", "Lebar kolom podium", KOL * 1000, "mm", "", "[3.6]", "0"),
        R("ln", "Bentang bersih ln", "=({L}*1000-{kol})/1000", "m", "", "", "0.00", p["ln"]),
        R("Mo", "Mo = qu l2 ln² / 8", "={qu1}*{L}*{ln}^2/8", "kNm", "", "SNI 2847:2019 Pasal 8.10.3.2 (hal PDF 187)", "0.0", p["Mo"]),
        R("afv", "αf sloof 400 x 800, sayap pelat 250 (interior)", p["af"], "-", "dari tahap4_pelat.alpha_f; > 2,0", "SNI 2847:2019 Pers. 8.10.2.7b, Pasal 8.4.1.8", "0.000"),
        R("hmin", "hmin (αfm > 2,0): ln (0,8 + fy/1400) / (36 + 9β)", "=MAX({ln}*1000*(0.8+420/1400)/(36+9*1),90)", "mm", "β = 1 (panel bujur sangkar), batas 90 mm",
          "SNI 2847:2019 Tabel 8.3.1.2 (hal PDF 156)", "0.0", p["hmin"] * 1000),
        R("hok", "Cek tebal 250 mm terhadap hmin", '=IF({h}>={hmin},"memenuhi, lendutan tidak dihitung","tidak memenuhi")', "", "SNI 2847:2019 Pasal 8.3.1.2: bila h >= hmin lendutan tidak dihitung", ""),
        R("Asmin", "As min = 0,0018 Ag per m", "=0.0018*{h}*1000", "mm²/m", "", "SNI 2847:2019 Tabel 8.6.1.1 (hal PDF 167)", "0", p["baris"][0]["as_min13"]),
        R("smaks", "Spasi maksimum min(2h; 450)", "=MIN(2*{h},450)", "mm", "", "SNI 2847:2019 Pasal 8.7.2.2 (hal PDF 171)", "0", 450.0),
        R("d_pos", "d bawah (selimut 50, D13, lapis kedua)", f"={{h}}-{SEL_B * 1000:.0f}-13/2-13", "mm", "", "SNI 2847:2019 Tabel 20.6.1.3.1 (hal PDF 482)", "0.0", d_eff(SEL_B) * 1000),
        R("d_neg", "d atas (selimut 20, D13, lapis kedua)", f"={{h}}-{SEL_A * 1000:.0f}-13/2-13", "mm", "", "SNI 2847:2019 Tabel 20.6.1.3.1 (hal PDF 482)", "0.0", d_eff(SEL_A) * 1000),
        R("d_v", "d geser satu arah (selimut 50, tanpa lapis kedua)", f"={{h}}-{SEL_B * 1000:.0f}-13/2", "mm", "", "SNI 2847:2019 Tabel 20.6.1.3.1", "0.0", (H - SEL_B - DB / 2) * 1000),
        R("Vu", "Geser satu arah Vu = qu (L/2 - bw/2 - d) per m", "={qu1}*({L}/2-0.4/2-{d_v}/1000)", "kN/m", "", "SNI 2847:2019 Pasal 22.5 (Pers. 22.5.5.1)", "0.0", p["Vu"]),
        R("phiVc", "φVc = 0,75 x 0,17 √fc' b d", "=0.75*0.17*SQRT(35)*1000*{d_v}/1000", "kN/m", "fc' 35", "SNI 2847:2019 Pers. 22.5.5.1 (hal PDF 508), Tabel 21.2.1", "0.0", p["phiVc"]),
    ]
    return [("A", "Panel tipikal PL-1: Mo, tebal minimum, d, dan geser satu arah", a)]


def baris_mri(r):
    q = r["pl2"]
    a = [
        R("ddm_pos", "Mu positif DDM terbesar (panel ujung, per m)", q["pos_ddm"], "kNm/m", "baris ujung (sisi timur tepi gedung): lajur kolom atau tengah terbesar", "tahap4_pelat.desain_panel (PL-2)", "0.00"),
        R("ddm_neg", "Mu negatif DDM terbesar (per m)", q["neg_ddm"], "kNm/m", "", "tahap4_pelat.desain_panel (PL-2)", "0.00"),
        R("skala", "Faktor beban transit terhadap qu operasi = 1,2 D / qu", "={D2}*1.2/{qu2}", "-", "transit: 1,2D + 1,6T, Lo ruangan 0 [Asumsi]", "", "0.0000", q["skala_tr"]),
        R("m_kaki", "Momen titik kaki magnet (4 x 1,2 x 12 kN, Navier)", r["kaki"]["M"], "kNm/m", "kaki di isocenter ± 0,80 / ± 0,60 m [Asumsi]; persegi 0,25 x 0,25", "deret Navier, pelat 8 x 8 tumpuan sederhana", "0.00"),
        R("m_roda", "Momen titik roda transit terbesar (1,6 x 4 roda 12,03 kN)", r["transit"]["m_pos"], "kNm/m", "maks Navier dan PyNite sepanjang lintasan", "lembar Transit Magnet", "0.00"),
        R("mu_op", "Mu positif kombinasi operasi = DDM + kaki", "={ddm_pos}+{m_kaki}", "kNm/m", "", "", "0.00", q["op_pos"]),
        R("mu_tr", "Mu positif kombinasi transit = DDM x skala + roda", "={ddm_pos}*{skala}+{m_roda}", "kNm/m", "", "", "0.00", q["tr_pos"]),
        R("mu_pos", "Mu positif penentu", "=MAX({mu_op},{mu_tr})", "kNm/m", f"menentukan: {q['pos_gov']}", "", "0.00", q["mu_pos"]),
        R("neg_roda", "Momen negatif tambahan roda (model tiga tepi jepit, PyNite)", r["transit"]["neg_pyn"], "kNm/m", "tepi timur sendi (tepi gedung)", "lembar Transit Magnet", "0.00"),
        R("mu_neg", "Mu negatif penentu = maks(DDM; DDM x skala + roda)", "=MAX({ddm_neg},{ddm_neg}*{skala}+{neg_roda})", "kNm/m", f"menentukan: {q['neg_gov']}", "", "0.00", q["mu_neg"]),
        R("phi200", "φMn bawah D13-200 (d 187)", "=0.9*(1000*PI()*13^2/4/200)/1e6*420*1000*((250-50-13/2-13)/1000-(1000*PI()*13^2/4/200)/1e6*420/(1.7*35))", "kNm/m", "pembanding bawaan 5.2", "", "0.00", q["s200_phimn"]),
        R("s_b", "Spasi D13 bawah terpilih (dua arah)", q["bawah"]["s"], "mm", f"D{q['bawah']['db']}; kelipatan 25 mm dari pilih_s", "SNI 2847:2019 Pasal 8.7.2.2", "0"),
        R("s_a", "Spasi D13 atas terpilih (dua arah)", q["atas"]["s"], "mm", f"D{q['atas']['db']}", "", "0"),
        R("pb", "φMn bawah terpasang", f"=0.9*(1000*PI()*{q['bawah']['db']}^2/4/{{s_b}})/1e6*420*1000*({{d_pos}}/1000-(1000*PI()*{q['bawah']['db']}^2/4/{{s_b}})/1e6*420/(1.7*35))",
          "kNm/m", "", "SNI 2847:2019 Pasal 22.2, Tabel 21.2.1", "0.00", q["bawah"]["phimn"]),
        R("pa", "φMn atas terpasang", f"=0.9*(1000*PI()*{q['atas']['db']}^2/4/{{s_a}})/1e6*420*1000*({{d_neg}}/1000-(1000*PI()*{q['atas']['db']}^2/4/{{s_a}})/1e6*420/(1.7*35))",
          "kNm/m", "", "", "0.00", q["atas"]["phimn"]),
        R("r_b", "Rasio Mu / φMn bawah", "={mu_pos}/{pb}", "-", "", "", "0.000", q["mu_pos"] / q["bawah"]["phimn"]),
        R("r_a", "Rasio Mu / φMn atas", "={mu_neg}/{pa}", "-", "", "", "0.000", q["mu_neg"] / q["atas"]["phimn"]),
    ]
    return [("A", "Panel MRI 9-10/D-E (PL-2): momen penentu dan tulangan", a)]


def baris_pons(r):
    pk, pr, t = r["pons_kaki"], r["pons_roda"], r["tumpu"]
    mi = r["mi"]
    a = [
        R("dp", "d pons = 250 - 50 - 13", f"=250-{SEL_B * 1000:.0f}-13", "mm", "db penuh (konservatif)", "SNI 2847:2019 Tabel 20.6.1.3.1", "0", pk["b0"] / 4 - pk["c"]),
        R("fcp", "fc'", FC, "MPa", "kelas S2", "[Keputusan 2.7, Tabel 19.3.2.1]", "0"),
        R("ck", "Sisi tapak kaki magnet", pk["c"], "mm", "0,25 x 0,25 m", "[Alat Medis R-03]", "0"),
        R("b0k", "b0 kaki = 4 (c + d)", "=4*({ck}+{dp})", "mm", "", "SNI 2847:2019 Pasal 22.6.4.1 (hal PDF 518)", "0", pk["b0"]),
        R("vck", "vc/(λ√fc') kaki: terkecil dari tiga", "=MIN(0.33,0.17*(1+2/1),0.083*(2+40*{dp}/{b0k}))", "-", "β = 1, αs = 40", "SNI 2847:2019 Tabel 22.6.5.2 (hal PDF 521)", "0.000", pk["k"]),
        R("pvk", "φVc kaki", "=0.75*{vck}*SQRT({fcp})*{b0k}*{dp}/1000", "kN", "φ = 0,75", "SNI 2847:2019 Tabel 21.2.1 (hal PDF 491)", "0.0", pk["phivc"]),
        R("vuk", "Vu kaki = 1,2 x 12 kN", f"=1.2*{mi['p_kaki']}", "kN", "", "SNI 2847:2019 Tabel 5.3.1", "0.0", pk["vu"]),
        R("rk", "Rasio pons kaki", "={vuk}/{pvk}", "-", "5.2 (d 187, fc' 30): 0,0325", "", "0.0000", pk["rasio"]),
        R("qk", "Tekanan satu kaki = 12 / (0,25 x 0,25)", f"={mi['p_kaki']}/({mi['kaki_a']}*{mi['kaki_b']})", "kPa", "", "", "0.0", t["q"]),
        R("pht", "φ 0,85 fc' tumpu (A2/A1 = 1)", "=0.65*0.85*{fcp}*1000", "kPa", "φ = 0,65", "SNI 2847:2019 Pasal 22.8.3.2 (hal PDF 540), Tabel 21.2.1", "#,##0", t["phi"]),
        R("rtk", "Rasio tumpu kaki = 1,2 q / φ 0,85 fc'", "=1.2*{qk}/{pht}", "-", "", "", "0.0000", t["rasio"]),
        R("cr", "Sisi tapak roda transit", pr["c"], "mm", "150 x 150", "[Asumsi: tapak roda 150 x 150]", "0"),
        R("b0r", "b0 roda = 4 (c + d)", "=4*({cr}+{dp})", "mm", "", "SNI 2847:2019 Pasal 22.6.4.1", "0", pr["b0"]),
        R("vcr", "vc/(λ√fc') roda", "=MIN(0.33,0.17*(1+2/1),0.083*(2+40*{dp}/{b0r}))", "-", "", "SNI 2847:2019 Tabel 22.6.5.2", "0.000", pr["k"]),
        R("pvr", "φVc roda", "=0.75*{vcr}*SQRT({fcp})*{b0r}*{dp}/1000", "kN", "", "", "0.0", pr["phivc"]),
        R("vur", "Vu roda = 1,6 x 12,03 kN", f"=1.6*{P_RODA}", "kN", "1,6T (transit); berat sendiri di dalam b0 diabaikan", "SNI 2847:2019 Tabel 5.3.1", "0.0", pr["vu"]),
        R("rr", "Rasio pons roda", "={vur}/{pvr}", "-", "", "", "0.0000", pr["rasio"]),
        R("qr", "Tekanan satu roda = 12,03 / 0,15²", f"={P_RODA}/({C_RODA}^2)", "kPa", "", "", "#,##0", t["q_roda"]),
        R("rtr", "Rasio tumpu roda = 1,6 q / φ 0,85 fc'", "=1.6*{qr}/{pht}", "-", "", "SNI 2847:2019 Pasal 22.8.3.2", "0.0000", t["rasio_roda"]),
    ]
    return [("A", "Pons dan tumpu: kaki magnet (ulang 5.2 dengan d dan fc' baru) dan satu roda transit", a)]


def baris_tk(r):
    k = r["tk"]
    a = [
        R("sisi", "Sisi zona tanpa baja karbon", LEBAR_ZONA, "m", "x 79,5-81,5 / y 56-58", "[Syarat MRI 7, 5.2]", "0.00"),
        R("sb", "Spasi bawah (D13)", k["s_b"], "mm", "dari panel MRI", "lembar Panel MRI", "0"),
        R("sa", "Spasi atas (D13)", k["s_a"], "mm", "", "lembar Panel MRI", "0"),
        R("nbb", "Batang per lapis bawah per arah", "=ROUNDUP({sisi}*1000/{sb},0)+1", "buah", "", "", "0", k["nb_b"]),
        R("nba", "Batang per lapis atas per arah", "=ROUNDUP({sisi}*1000/{sa},0)+1", "buah", "", "", "0", k["nb_a"]),
        R("fyt", "fy (A955M mutu 420 [Asumsi])", FY, "MPa", "", "SNI 2847:2019 Tabel 20.2.2.4(a) (hal PDF 472)", "0"),
        R("fct", "fc'", FC, "MPa", "", "", "0"),
        R("ldt", "ld D13 = fy ψt ψe / (2,1 λ √fc') db", "={fyt}/(2.1*SQRT({fct}))*13", "mm", "ψt = ψe = λ = 1", "SNI 2847:2019 Tabel 25.4.2.2 (hal PDF 588)", "0.0", k["ld"]),
        R("lpt", "Lewatan kelas B = 1,3 ld", "=1.3*{ldt}", "mm", "", "SNI 2847:2019 Tabel 25.5.2.1 (hal PDF 608)", "0.0", k["lap"]),
        R("lpk", "Lewatan dipakai (dibulatkan ke atas 10 mm)", "=CEILING({lpt},10)", "mm", "", "", "0", k["pakai"]),
        R("pjt", "Panjang satu batang = 2,0 + 2 lewatan", "={sisi}+2*{lpk}/1000", "m", "lewatan di luar zona", "", "0.00", k["pj"]),
        R("jml", "Jumlah batang tahan karat (4 lapis)", "=2*{nbb}+2*{nba}", "buah", "bawah x dan y, atas x dan y", "", "0", k["jml"]),
        R("msd", "Massa D13", mri.MASSA_BAJA["D13"], "kg/m", "", "SNI 2052:2017 (hal PDF 8; 1,U2 = 1,04)", "0.000"),
        R("mass", "Massa tulangan tahan karat zona", "={jml}*{pjt}*{msd}", "kg", "5.2: 148,26 kg (D13-200, fc' 30)", "", "0.0", k["massa"]),
    ]
    return [("A", "Tulangan baja tahan karat ASTM A955M di zona 2,0 x 2,0 m", a)]


def baris_getar(r):
    mi, A = r["mi"], r["getar"]["A"]
    ab = mi["a_batas_mg"] * 1e-3 * G
    a = [
        R("fcg", "fc'", FC, "MPa", "", "[S2]", "0"),
        R("ecg", "Ec = 4700 √fc'", "=4700*SQRT({fcg})", "MPa", "", "SNI 2847:2019 Pasal 19.2.2.1 (hal PDF 456)", "#,##0.0", A["ec"]),
        R("nug", "ν", NU, "-", "", "[Asumsi]", "0.00"),
        R("rho", "Massa jenis beton", mri.RHO_BETON, "kg/m³", "", "[Asumsi]", "0"),
        R("mrf", "Massa sangkar RF terbagi rata", f"={mi['berat_rf']}*1000/({mi['rf'][0]}*{mi['rf'][1]})/{G}", "kg/m²", "", "[Alat Medis R-05]", "0.0", r["m_rf"]),
        R("zg", "Redaman ζ", ZETA, "-", "", "[Asumsi]", "0.00"),
        R("abg", "Batas percepatan 0,5 x 10⁻³ g", f"={mi['a_batas_mg']}*1e-3*{G}", "m/s²", "0-50 Hz", "[Syarat MRI 5]", "0.00000", ab),
    ]
    def opsi(kode, ket, h, a_, b_, kunci):
        o = r["getar"][kunci]
        rows = [
            R(f"h_{kode}", f"{ket}: tebal", h, "m", "", "", "0.000"),
            R(f"a_{kode}", f"{ket}: sisi a", a_, "m", "", "", "0.0"),
            R(f"b_{kode}", f"{ket}: sisi b", b_, "m", "", "", "0.0"),
            R(f"D_{kode}", f"{ket}: D = Ec h³ / (12 (1 - ν²))", f"={{ecg}}*1000000*{{h_{kode}}}^3/(12*(1-{{nug}}^2))", "N·m", "", "teori pelat; belum ada di acuan", "#,##0", o["D"]),
            R(f"m_{kode}", f"{ket}: massa per luas", f"={{rho}}*{{h_{kode}}}+{{mrf}}", "kg/m²", "berat sendiri + sangkar RF", "", "0.0", o["m"]),
            R(f"fn_{kode}", f"{ket}: fn = (π/2)(1/a² + 1/b²) √(D/m)", f"=PI()/2*(1/{{a_{kode}}}^2+1/{{b_{kode}}}^2)*SQRT({{D_{kode}}}/{{m_{kode}}})", "Hz",
              "tumpuan sederhana (konservatif)", "[Asumsi: buku dinamika belum ada di acuan]", "0.00", o["fn"]),
            R(f"M_{kode}", f"{ket}: massa modal m a b / 4", f"={{m_{kode}}}*{{a_{kode}}}*{{b_{kode}}}/4", "kg", "", "", "#,##0", o["mm"]),
        ]
        for sm, kunci_f in (("M-04", "m04"), ("R-06", "r06"), ("M-01", "m01")):
            f = {"M-04": mi["f_m04"], "R-06": mi["f_r06"], "M-01": mi["f_m01_kipas"]}[sm]
            rows += [
                R(f"H_{kunci_f}_{kode}", f"{ket}: H di {idn(f)} Hz ({sm})",
                  f"=({f}/{{fn_{kode}}})^2/SQRT((1-({f}/{{fn_{kode}}})^2)^2+(2*{{zg}}*({f}/{{fn_{kode}}}))^2)", "-", "H = r² / √((1 - r²)² + (2 ζ r)²)", "", "0.000", o[sm]["H"]),
                R(f"F_{kunci_f}_{kode}", f"{ket}: gaya izin {sm}", f"={{abg}}*{{M_{kode}}}/{{H_{kunci_f}_{kode}}}", "N", "F = a_batas M_modal / H", "", "#,##0.0", o[sm]["F"]),
            ]
        return rows
    blocks = [
        ("B", "Opsi A: monolit 250 mm (panel 8 x 8, tanpa sambungan isolasi)", opsi("A", "A 250", H, 8.0, 8.0, "A")),
        ("C", "Opsi B1: panel MRI ditebalkan 300 mm", opsi("B30", "B 300", 0.30, 8.0, 8.0, "B30")),
        ("D", "Opsi B2: panel MRI ditebalkan 350 mm", opsi("B35", "B 350", 0.35, 8.0, 8.0, "B35")),
        ("E", "Opsi C: sambungan isolasi keliling ruang MRI (pelat 7,0 x 6,0 di atas sloof/balok tambahan)", opsi("C", "C 250 (7 x 6)", H, 7.0, 6.0, "C")),
    ]
    return [("A", "Masukan umum", a)] + [(h, t, rows) for h, t, rows in blocks]


def semua_baris(r):
    out = {}
    for nama, fn in (("Beban", baris_beban), ("Panel Tipikal", baris_panel), ("Panel MRI", baris_mri), ("Pons dan Tumpu", baris_pons),
                     ("Baja Tahan Karat", baris_tk), ("Getaran dan Isolasi", baris_getar)):
        out[nama] = [rw for _, _, rows in fn(r) for rw in rows]
    return out




# ------------------------------------------------------------------ teks tabel
def teks_alat(r):
    out = []
    for a in r["alat"]:
        tap = f"{idn(a['a'], 1)} × {idn(a['b'], 1)} m" if a["a"] else "-"
        cek = a["ket"]
        if a["rasio"]:
            cek += f"; Mu total {idn(a['M'], 1)} kNm/m / φMn {idn(r['alat_cap'], 1)} = {idn(a['rasio'], 3)} (beban titik di tengah panel, tumpuan sederhana)"
        out.append([f"{a['kode']} {a['uraian']}", f"{a['n']} × {idn(a['w'], 1)} kN" + (f", tapak {tap}" if a["a"] else ""), idn(a["q"], 2), cek,
                    "[Alat Medis / Daftar Alat]"])
    out.append(["R-03 magnet MRI, R-04 pelindung, R-05 sangkar RF", "lihat lembar Panel MRI dan Pons dan Tumpu", "-",
                "panel MRI didesain terpisah (PL-2)", "[Alat Medis R-03..R-05]"])
    out.append(["R-09 dinding timbal 2 mm Pb (0,45 kN/m² dinding)", "x 66-74 / y 44-63", "-",
                "beban dinding: dengan tinggi [Asumsi: tinggi lantai 4,50 m] = 2,03 kN/m'; dicek di 5.4 (sloof) bila di as, "
                "selain itu garis di atas pelat PL-1", "[Alat Medis R-09]"])
    out.append(["Lift L-1..7: pit dan beban kait", "pit di bawah +12,85", "-", "tepi pit dirujuk ke 5.5", "[Lift]"])
    out.append(["Gedung utilitas (E-01..G-02)", "x 100-134 / y 44-76", "-", "gedung terpisah; informasi data owner, bukan pelat podium LT1", "[Gedung Utilitas]"])
    return out


def teks_zonasi():
    lo = {"GAWAT DARURAT": ("2,87 / 4,79", "ruang tindakan seperti ruang operasi; koridor lantai pertama 4,79"),
          "RADIOLOGI": ("2,87 / 4,79", "alat berat dicek per alat (tabel di bawah)"),
          "FARMASI, REKAM MEDIS": ("4,79", "[Asumsi: gudang obat dan arsip 4,79; arsip padat (rak) bisa 7,18, keputusan Defsa]"),
          "LOBI DAN PENDAFTARAN": ("4,79", "Tabel 4.3-1: lobi dan koridor lantai pertama"),
          "POLIKLINIK": ("2,87 / 4,79", "ruang periksa 2,87 (ruang pasien 1,92); koridor 4,79"),
          "PENUNJANG, LOKER, JENAZAH": ("4,79", "[Asumsi: dipakai 4,79]")}
    out = []
    for n, x0, x1, y0, y1, _ in tz.ZONA["LT1"]:
        a, b = lo[n]
        out.append([n, f"x {idn(x0, 0)}-{idn(x1, 0)} / y {idn(y0, 0)}-{idn(y1, 0)}", a, b, "[3.4 zonasi; SNI 1727:2020 Tabel 4.3-1 hal PDF 52]"])
    out.append(["Pakai PL-1", "seluruh LT1", "4,79", "menentukan; PL-2 hanya panel MRI 9-10/D-E (2,87)", "[Keputusan 5.3]"])
    return out


def teks_tulangan_pl1(r):
    nm = {"neg_int": "negatif (tumpuan dalam)", "pos": "positif (lapangan)", "neg_eks": "negatif (tumpuan luar)"}
    out = []
    for b in r["pl1"]["baris"]:
        ket = "memenuhi" if b["phimn13"] >= b["Mu"] and b["as13"] >= b["as_min13"] and b["s13"] <= 450 else "periksa"
        out.append([f"{'interior' if b['bentang'] == 'interior' else 'tepi dan sudut (ujung)'}; {nm[b['posisi']]}; lajur {b['lajur']}",
                    f"{idn(b['Mu'], 2)} kNm/m; d {idn(b['d13'] * 1000, 1)}; As perlu {idn(max(b['As'], b['as_min13']), 0)} mm²/m",
                    f"D{b['db13']}-{b['s13']:.0f} ({idn(b['as13'], 0)} mm²/m), φMn {idn(b['phimn13'], 1)} kNm/m", ket])
    return out


def teks_selimut(r):
    a = r["alt_sel"]
    out = []
    for sel, nm in ((0.050, "50 mm (lantai kerja / void former; +10 mm asam)"), (0.075, "75 mm (dicor langsung di atas tanah)")):
        x = a[sel]
        out.append([f"Selimut bawah {nm}", f"d {idn(x['d'] * 1000, 1)} mm",
                    f"PL-1 ujung positif tengah: As perlu {idn(x['as'], 0)} mm²/m (D13-{x['s']:.0f}); "
                    f"PL-2 positif: As perlu {idn(x['pl2_as'], 0)}, D13-200 φMn {idn(x['pl2_phimn'], 1)} kNm/m, rasio {idn(x['pl2_rasio'], 3)}, spasi {x['pl2_s']:.0f}",
                    "bahan keputusan Defsa"])
    return out


def teks_transit(r):
    t = r["transit"]
    nav = dict(t["nav"])
    out = []
    for xc, mp, mn in t["pyn"]:
        k = min(nav, key=lambda z: abs(z - xc))
        out.append([f"x pusat {idn(xc, 1)} (roda di x {idn(xc - OFF_RODA, 1)} dan {idn(xc + OFF_RODA, 1)}), y 57,0", idn(nav[k][0], 2), idn(mp, 2), idn(mn, 2)])
    return out


def teks_penyebar(r):
    return [[f"{idn(p['c'] * 1000, 0)} × {idn(p['c'] * 1000, 0)} mm", idn(p["M"], 2), idn(p["total"], 2),
             "cukup" if p["ok200"] else "tidak cukup"] for p in r["penyebar"]]


def teks_lubang(r):
    ld = math.ceil(r["tk"]["ld"] / 10) * 10 / 1000
    out = []
    for x in r["lubang"]:
        sh = x["kode"] == "SH-6"
        out.append([x["kode"], f"{idn(x['a'], 1)} × {idn(x['b'], 1)}", f"x {idn(x['x'][0])}-{idn(x['x'][1])} / y {idn(x['y'][0])}-{idn(x['y'][1])}",
                    f"{x['tembus']}: menembus pelat LT1",
                    f"{x['n_x']} D13 tiap sisi sejajar y dan {x['n_y']} D13 tiap sisi sejajar x (bawah dan atas); panjang batang = ukuran + 2 ld "
                    f"({idn(x['a'] + 2 * ld, 2)} dan {idn(x['b'] + 2 * ld, 2)} m); ld D13 = {idn(ld * 1000, 0)} mm",
                    "panel MRI D13-200 (PL-2)" if sh else "PL-1 D13-200 [tulangan terpotong digantikan, praktik Pasal 8.5.4.2; belum dikutip]"])
    return out


def teks_getar_banding(r):
    A, B3, B35, C = (r["getar"][k] for k in ("A", "B30", "B35", "C"))

    def hf(o, s):
        return f"H {idn(o[s]['H'], 2)}; F izin {idn(o[s]['F'], 1)} N"
    isol = r["isolasi"]
    return [
        ["A: monolit 250 (tanpa sambungan isolasi, diafragma LT1 utuh)", idn(A["fn"], 2),
         f"M-04 24,2 Hz: {hf(A, 'M-04')}. R-06 50 Hz: {hf(A, 'R-06')}. M-01 14,5 Hz: {hf(A, 'M-01')}. Bila panel menerus (tepi jepit): fn {idn(A['fn_jepit'], 1)} Hz, "
         f"H M-04 {idn(A['H_jepit']['M-04'], 2)}, R-06 {idn(A['H_jepit']['R-06'], 2)}, M-01 {idn(A['H_jepit']['M-01'], 2)}",
         "tidak ada tambahan; diafragma LT1 utuh; getaran M-04/R-06 menjalar lewat pelat, sloof, dan kolom ke panel", "fn model tumpuan sederhana = batas bawah (konservatif)"],
        ["B1: panel MRI 300", idn(B3["fn"], 2),
         f"M-04: {hf(B3, 'M-04')}. R-06: {hf(B3, 'R-06')}. M-01 14,5 Hz: {hf(B3, 'M-01')} (r = {idn(B3['M-01']['r'], 2)}: resonansi)",
         "tambah beton 64 m² × 0,05 m = 3,2 m³ dan beban 1,2 kPa ke sloof; fn mendekati 14,5 Hz kipas M-01", "tidak dianjurkan"],
        ["B2: panel MRI 350", idn(B35["fn"], 2),
         f"M-04: {hf(B35, 'M-04')}. R-06: {hf(B35, 'R-06')}. M-01 14,5 Hz: {hf(B35, 'M-01')}",
         f"tambah beton 64 × 0,10 = 6,4 m³ dan beban 2,4 kPa; fn di atas 14,5 Hz (r {idn(B35['M-01']['r'], 2)})", "H M-01 masih > 3"],
        ["C: sambungan isolasi keliling ruang MRI (celah 25 mm [Asumsi]) di atas balok x 77, y 54, y 60", idn(C["fn"], 2),
         f"pelat 7,0 × 6,0: M-04: {hf(C, 'M-04')}. R-06: {hf(C, 'R-06')}. M-01: {hf(C, 'M-01')}",
         f"sloof/balok tambahan 400 × 800 sepanjang {idn(isol['panjang'], 1)} m (6,0 + 7,0 + 7,0): beton di bawah pelat {idn(isol['vol'], 1)} m³ "
         f"(penuh {idn(isol['vol_penuh'], 1)} m³); tumpuan balok tambahan belum dirancang; diafragma LT1 terputus; getaran M-04/kolom tetap lewat sloof/pile cap",
         "pedoman getaran lantai (AISC DG11, CCIP-016, SCI P354): belum ada di acuan"],
    ]


# ------------------------------------------------------------------ workbook
NAMA = ["Petunjuk", "Ringkasan", "Beban", "Panel Tipikal", "Panel MRI", "Transit Magnet", "Pons dan Tumpu", "Lubang SH-6",
        "Baja Tahan Karat", "Getaran dan Isolasi", "Cek Silang T-92", "Acuan"]


def _tt(lb, kepala, isi, rata, beku=False, ai=True, **kw):
    if kw:
        return lb.tabel(kepala, [[i + 1, *row] for i, row in enumerate(isi)], rata=rata, beku=beku, **kw)
    return mri._teks_tabel(lb, kepala, isi, rata, beku=beku, ai=ai)


def buat_excel(keluar=BERKAS):
    from format_dokumen import AI, Lembar, set_font_bawaan
    r = hitung()
    p, q, t, k = r["pl1"], r["pl2"], r["transit"], r["tk"]
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    for s in NAMA:
        wb.create_sheet(s)
    mri.REF.clear()
    mri.LABEL_PAKAI.clear()
    ket = LABEL + " " + LABEL_AI
    tt = _tt

    def tambah_beban(lb):
        lb.kosong()
        lb.bagian("B", "Zonasi LT1 dan beban hidup")
        tt(lb, ["No", "Zona", "x / y", "Lo (kPa)", "Catatan", "Sumber"], teks_zonasi(), list("cllcll"))
        lb.kosong()
        lb.bagian("C", "Alat berat di LT1: tekanan tapak terhadap kapasitas panel PL-1")
        tt(lb, ["No", "Alat", "Jumlah, berat, tapak", "q (kPa)", "Cek", "Sumber"], teks_alat(r), list("cllcll"))
        lb.kosong()
        lb.catatan(f"q izin = (qu - 1,2 D) / 1,2 = {idn(r['alat_izin'], 2)} kPa (alat menggantikan beban hidup 4,79 di tapaknya). Alat di atas batas dicek lokal "
                   "sebagai beban titik di tengah panel (tumpuan sederhana) ditambah momen DDM 1,2 D, dibandingkan dengan φMn D13-200 bawah.")
    mri._lembar_hitung(wb, "Beban", 3, "Beban pelat LT1, zonasi, dan alat berat", ket + " Pelat LT1 +12,85, 250 mm, ditumpu sloof 400 × 800 di semua as; "
                       "tanpa plafon dan gantung (tidak ada ruang di bawah LT1).", baris_beban(r), tambah_beban)

    def tambah_panel(lb):
        lb.kosong()
        lb.bagian("B", "Tulangan PL-1 per lajur (D13, s dicoba 200; 175; ...)")
        tt(lb, ["No", "Lokasi (bentang; momen; lajur)", "Mu, d, As perlu", "", "Tulangan terpilih", "Cek"],
           [[x[0], x[1], "", x[2], x[3]] for x in teks_tulangan_pl1(r)], list("clcclc"))
        lb.kosong()
        lb.catatan("Panel interior memakai baris interior; panel tepi dan sudut memakai baris ujung (arah tegak lurus tepi; baris interior untuk arah sejajar tepi). "
                   "Lajur kolom memakai lebar 4,0 - 0,40 m (0,85 momen lajur kolom dipikul sloof). Semua baris D13-200 (s maksimum praktis, dipakai juga di 5.2). "
                   f"hmin tepi {idn(p['hmin_tepi'] * 1000, 0)} mm. Lendutan tidak dihitung (SNI 2847:2019 Pasal 8.3.1.2: h >= hmin). Tepi pit lift dirujuk ke 5.5.")
        lb.kosong()
        lb.bagian("C", "Bahan keputusan: selimut bawah 50 atau 75 mm")
        tt(lb, ["No", "Opsi", "d", "", "Akibat pada tulangan", "Status"], [[x[0], x[1], "", x[2], x[3]] for x in teks_selimut(r)], list("clcclc"))
    mri._lembar_hitung(wb, "Panel Tipikal", 4, "Panel tipikal PL-1: DDM, hmin, tulangan, dan geser", ket + " fc' 35 MPa (kelas paparan S2, keputusan 2.7: "
                       "SNI 2847:2019 Tabel 19.3.2.1 hal PDF 464, w/cm <= 0,45, fc' >= 31 MPa; R19.3.2.1 hal PDF 460), fy 420, D13. Selimut bawah 50 mm "
                       "(Tabel 20.6.1.3.1 hal PDF 482: kontak tanah D16 dan lebih kecil 40 mm + 10 mm perlindungan asam [Asumsi 2.7]); atas 20 mm. "
                       "Sloof yang dicor bersama ikut S2.", baris_panel(r), tambah_panel)

    def tambah_mri(lb):
        lb.kosong()
        lb.bagian("B", "Dinding pelindung R-04 dan sloof as 10 (rujukan 5.4)")
        pl = r["pelindung"]
        tt(lb, ["No", "Butir", "Hasil", "", "Keterangan", "Sumber"], [
            ["Dinding utara y 60 (x 77-84)", f"{idn(pl['w'], 2)} kN/m'", "", f"di panel 9-10/E-F, 1,0 m dari as E: beban garis 1,2 × {idn(pl['w'], 2)} = {idn(pl['wu'], 2)} kN/m'; strip satu arah jepit-jepit L = 8 m: "
             f"M- di E = {idn(pl['M'], 2)} kNm/m; Mu atas PL-1 lajur tengah {idn(pl['Mu_ddm'], 2)} + {idn(pl['M'], 2)} = {idn(pl['Mu_tot'], 2)} kNm/m vs φMn D13-200 {idn(pl['phimn'], 2)}: "
             f"{'cukup' if pl['ada_cukup'] else 'perlu tulangan atas rapat D13-' + str(int(pl['s_baru']))}", "[Alat Medis R-04]; geometri: utara 7,0 m, timur 6,0 m [Asumsi]"],
            ["Dinding timur x 84 (y 54-60)", f"{idn(pl['timur'], 1)} kN total", "", f"{idn(pl['w'], 2)} kN/m' langsung ke sloof as 10: catat untuk 5.4 (beban garis tambahan pada sloof tepi)", "[Alat Medis R-04]"],
        ], list("clccll"))
    mri._lembar_hitung(wb, "Panel MRI", 5, "Panel MRI 9-10/D-E (PL-2): momen DDM + beban titik", ket + " Panel x 76-84 / y 51-59; tepi timur (x 84) tepi gedung, tiga sisi lain menerus. "
                       "Momen positif = DDM beban merata + beban titik pelat tumpuan sederhana (konservatif); momen negatif tambahan dari model tiga tepi jepit, tepi timur sendi (PyNite). "
                       "Kaki: isocenter ± 0,80 m (x) dan ± 0,60 m (y) [Asumsi: jarak antar kaki tidak ada di data owner].", baris_mri(r), tambah_mri)

    # ---- Transit Magnet
    lb = Lembar(wb["Transit Magnet"], 6, "Beban transit magnet 48,1 kN", [5, 50, 18, 18, 18, 40])
    lb.catatan(ket + " Magnet 48,1 kN bergeser dari bukaan dinding timur (x 84, y 55,7-58,3) ke isocenter sepanjang y 57,0 di atas 4 roda/skate 12,03 kN, segi empat 1,2 × 1,2 m, "
               "tapak 150 × 150 mm [Asumsi]. Kombinasi 1,2D + 1,6T; beban hidup ruangan 0 saat instalasi [Asumsi]. Pelat 8 × 8 tumpuan sederhana (panel 9-10/D-E).")
    lb.kosong()
    lb.bagian("A", "Momen positif dan negatif tambahan sepanjang lintasan (faktor 1,6 sudah termasuk)")
    tt(lb, ["No", "Posisi kelompok roda", "M+ Navier (kNm/m, persegi 0,15)", "M+ PyNite (kNm/m, mesh 0,25)", "M- PyNite tiga tepi jepit (kNm/m)", "Keterangan"],
       [x + ["Navier tiap 0,05 m; PyNite di 5 posisi"] for x in teks_transit(r)], list("clcccl"), beku=True)
    lb.kosong()
    lb.bagian("B", "Momen maksimum dan perbandingan dengan kapasitas")
    px, py_ = t["pos_nav"]
    tt(lb, ["No", "Besaran", "Nilai", "Satuan", "Rasio", "Keterangan"], [
        ["M+ roda maksimum (Navier, persegi 0,15)", round(t["m_nav"], 3), "kNm/m", None,
         f"di x pusat kelompok {idn(t['xc_w'], 2)} m, lokasi momen x {idn(px, 2)} / y {idn(py_, 2)}"],
        ["M+ roda maksimum PyNite (5 posisi)", round(t["m_pyn"], 3), "kNm/m", None, "mesh 0,25, tekanan di elemen terdekat (tapak 0,25 > 0,15): lebih kecil dari Navier"],
        ["M+ penentu tambahan roda", round(t["m_pos"], 3), "kNm/m", None, "maks keduanya"],
        ["M- tambahan roda (PyNite jepit)", round(t["neg_pyn"], 3), "kNm/m", None, "elemen tepi barat/selatan/utara"],
        ["Mu+ kombinasi transit total", round(q["tr_pos"], 3), "kNm/m", round(q["tr_pos"] / q["bawah"]["phimn"], 4),
         f"DDM × {idn(q['skala_tr'], 3)} + roda; φMn bawah {idn(q['bawah']['phimn'], 2)} (D13-{q['bawah']['s']:.0f})"],
        ["Mu+ kombinasi operasi (kaki magnet) total", round(q["op_pos"], 3), "kNm/m", round(q["op_pos"] / q["bawah"]["phimn"], 4),
         "menentukan" if q["pos_gov"] == "operasi" else "tidak menentukan"],
        ["Mu- kombinasi transit total", round(q["tr_neg"], 3), "kNm/m", round(q["tr_neg"] / q["atas"]["phimn"], 4), f"φMn atas {idn(q['atas']['phimn'], 2)}"],
        ["Pons satu roda (Vu / φVc)", f"{idn(r['pons_roda']['vu'], 2)} / {idn(r['pons_roda']['phivc'], 1)}", "kN", round(r["pons_roda"]["rasio"], 4),
         "Pasal 22.6.5.2, b0 = 4 (c + d)"],
    ], list("clccc") + ["l"], fmt=[None, None, "0.000", None, "0.000", None], fill_kolom={2: AI})
    lb.kosong()
    lb.bagian("C", "Pelat baja penyebar beban per roda (bahan keputusan)")
    tt(lb, ["No", "Ukuran penyebar per roda", "M+ roda (kNm/m)", "Mu+ transit total (kNm/m)", "Terhadap φMn D13-200 bawah", "Keterangan"],
       [x + [f"φMn {idn(q['s200_phimn'], 2)} kNm/m"] for x in teks_penyebar(r)], list("clcccl"))
    lb.kosong()
    lb.catatan("D13-200 bawah sudah cukup untuk transit tanpa penyebar; kombinasi operasi (kaki magnet) yang menentukan. Pelat penyebar hanya mengurangi M+ roda sekitar "
               f"{idn((1 - r['penyebar'][-1]['M'] / r['penyebar'][0]['M']) * 100, 0)} %; dipasang bila data pabrikan skate berbeda (tapak lebih kecil atau beban dinamis).")

    # ---- Pons dan Tumpu
    mri._lembar_hitung(wb, "Pons dan Tumpu", 7, "Pons dan tumpu: kaki magnet dan roda transit",
                       ket + " Ulang 5.2 dengan tebal 250, selimut bawah 50, fc' 35.", baris_pons(r))

    # ---- Lubang SH-6
    lb = Lembar(wb["Lubang SH-6"], 8, "Lubang pelat LT1: SH-6 dan shaft lain", [5, 10, 16, 36, 30, 60, 40])
    lb.catatan(ket + " SH-6 (pipa ventilasi helium MRI Ø 300, 0,6 × 0,6 m) menembus pelat LT1 sampai atap podium utara; sudah termuat di tahap4_pelat.BUKAAN (4.5, jumlah entri "
               f"SH-6 = {r['sh6_di_bukaan']}). SNI 2847:2019 Pasal 8.5.4.1 (hal PDF 166): bukaan diizinkan bila kekuatan dan layan dipenuhi.")
    lb.kosong()
    lb.bagian("A", "Lubang yang menembus pelat LT1")
    tt(lb, ["No", "Kode", "Ukuran (m)", "Letak", "Tembus", "Tulangan tepi lubang (tambahan, bawah dan atas)", "Dasar tulangan"],
       teks_lubang(r), list("clcllll"), beku=True)
    lb.kosong()
    lb.bagian("B", "SH-6: jarak ke isocenter, zona tahan karat, dan lintasan roda")
    s6 = [x for x in r["lubang"] if x["kode"] == "SH-6"][0]
    tt(lb, ["No", "Cek", "Hasil", "Satuan", "Status", "Keterangan", ""], [
        ["Jarak terdekat tepi lubang ke isocenter (80,5; 57,0)", round(s6["jarak_iso"], 3), "m", "memenuhi" if s6["jarak_iso"] > 1.0 else "tidak",
         "radius tanpa baja karbon 1,0 m; tulangan tambahan karbon di luar radius", ""],
        ["Tumpang tindih lubang dengan zona tahan karat x 79,5-81,5 / y 56-58", round(s6["di_zona"], 3), "m²",
         "tidak memotong zona" if s6["di_zona"] == 0 else "memotong", "zona dan lubang terpisah", ""],
        ["Jarak y tepi utara lubang ke tepi selatan tapak roda transit", round(s6["jarak_roda_y"], 3), "m",
         "tidak bentrok" if s6["jarak_roda_y"] > 0 else "bentrok", "lintasan y 56,4-57,6", ""],
    ], list("clcccll"), fmt=[None, None, "0.000", None, None, None, None], fill_kolom={2: AI})

    # ---- Baja Tahan Karat
    def tambah_tk(lb):
        lb.kosong()
        lb.bagian("B", "Perbandingan dengan 5.2 dan catatan")
        tt(lb, ["No", "Butir", "Nilai", "", "Penjelasan", "Sumber"], [
            ["Massa 5.2 (D13-200 atas/bawah, fc' 30, lewatan 620)", "148,26 kg", "",
             f"5.3: fc' 35 (ld {idn(k['ld'], 0)} < 475 mm), lewatan {k['pakai']} mm, batang {idn(k['pj'], 2)} m; spasi sama → massa {idn(k['massa'], 2)} kg "
             f"({idn((k['massa'] / 148.26 - 1) * 100, 1)} %)", "[5.2]"],
            ["Kawat ikat dan kursi/penahan jarak", "tahan karat atau plastik", "", "non-magnetik di dalam zona [Asumsi: syarat pabrikan]", "[Asumsi]"],
            ["Kontak galvanik baja tahan karat - baja karbon", "belum ada di acuan", "", "titik lewatan di luar zona; pemisah/pelapis dibahas dengan pemasok", "belum ada di acuan"],
        ], list("clccll"))
    mri._lembar_hitung(wb, "Baja Tahan Karat", 9, "Tulangan baja tahan karat ASTM A955M di zona MRI",
                       ket + " Keputusan 5.2 (SNI 2847:2019 Pasal 20.2.1.3): kotak x 79,5-81,5 / y 56-58, kedua lapis kedua arah. Lewatan kelas B seluruhnya di luar zona "
                       "(panjang batang = 2,0 + 2 × lewatan).", baris_tk(r), tambah_tk)

    # ---- Getaran dan isolasi
    def tambah_getar(lb):
        lb.kosong()
        lb.bagian("F", "Banding opsi A, B, C (tanpa keputusan)")
        tt(lb, ["No", "Opsi", "fn (Hz)", "", "H dan gaya izin di pelat (M-04 24,2 Hz; R-06 50 Hz; M-01 kipas 14,5 Hz)", "Akibat struktur dan biaya"],
           [[x[0], x[1], "", x[2], x[3]] for x in teks_getar_banding(r)], list("clccll"))
        lb.kosong()
        A, B3, C = r["getar"]["A"], r["getar"]["B30"], r["getar"]["C"]
        lb.catatan("USULAN AI (berdasarkan angka): opsi A dipertahankan sebagai dasar. fn pelat 250 = " + idn(A["fn"], 1) + " Hz (batas bawah, tumpuan sederhana; menerus lebih tinggi), "
                   "gaya izin M-04 dan R-06 setara atau lebih besar dari opsi lain, tanpa biaya dan diafragma LT1 utuh. Hindari tebal 300 (fn " + idn(B3["fn"], 1) + " Hz ≈ 14,5 Hz kipas M-01: "
                   "H " + idn(B3["M-01"]["H"], 1) + "). Opsi C menurunkan gaya izin M-04 menjadi " + idn(C["M-04"]["F"], 1) + " N dan memutus diafragma. Semua opsi bergantung pada gaya dinamis "
                   "sumber dari pabrikan (belum ada) dan pengukuran setelah konstruksi (Syarat MRI 5). Pedoman getaran lantai (AISC DG11, CCIP-016, SCI P354): belum ada di acuan. "
                   "Keputusan di tangan Defsa.")
    mri._lembar_hitung(wb, "Getaran dan Isolasi", 10, "Getaran lantai di bawah magnet dan sambungan isolasi",
                       ket + " Metode 5.2: pelat persegi tumpuan sederhana satu ragam dan faktor respons percepatan [Asumsi: buku dinamika belum ada di acuan]. "
                       "Batas 0,5 × 10⁻³ g, 0-50 Hz [Syarat MRI 5].", baris_getar(r), tambah_getar)

    # ---- Cek silang T-92
    lb = Lembar(wb["Cek Silang T-92"], 11, "Cek silang T-92", [5, 54, 14, 14, 12, 12, 10, 52])
    lb.catatan(ket + " Toleransi ditetapkan sebelum membandingkan. Cara 1 = tangan atau metode lain; cara 2 = skrip atau Excel.")
    lb.kosong()
    lb.bagian("A", "Lima cek silang")
    ws = lb.ws
    x2 = r["t92"]
    kep = ["No", "Cek", "Cara 1", "Cara 2", "Selisih (%)", "Toleransi (%)", "Status", "Cara 1 / cara 2"]
    isi = [
        [1, "(a) qu PL-1 (kPa)", None, None, None, 0.5, None, "1: tangan 1,2 (23,6 × 0,25 + 1,10 + 1,00) + 1,6 × 4,79. 2: lembar Beban"],
        [2, "(a) Mo PL-1 interior (kNm)", None, None, None, 0.5, None, "1: tangan qu × 8 × 7,25² / 8. 2: lembar Panel Tipikal"],
        [3, "(b) Mx di tengah pelat 8 × 8 akibat 48,1 kN pada 0,8 × 0,8 m (kNm/m)", None, None, None, 5.0, None,
         "1: PyNite mesh 0,2 (rata-rata 4 elemen tengah). 2: deret Navier beban persegi (rata-rata 4 titik elemen)"],
        [4, "(c) φVc pons satu roda (kN)", None, None, None, 0.5, None, "1: tangan 0,75 × 0,33 √35 × 4 (150 + 187) × 187. 2: lembar Pons dan Tumpu"],
        [5, "(d) Massa tulangan tahan karat (kg)", None, None, None, 0.5, None, "1: tangan 44 × 3,16 × 1,04. 2: lembar Baja Tahan Karat"],
    ]
    r0, a0, a1 = lb.tabel(kep, isi, rata=list("clcccccl"), fmt=[None, None, "0.000", "0.000", "0.00", "0.0", None, None])

    def ref(key):
        return "=" + mri._sub("{" + key + "}", ws.title)
    c2, c3 = lb.kol(2), lb.kol(3)
    ws[f"{c2}{a0}"] = "=1.2*(23.6*0.25+1.10+1.00)+1.6*4.79"
    ws[f"{c3}{a0}"] = ref("qu1")
    ws[f"{c2}{a0 + 1}"] = "=(1.2*(23.6*0.25+1.10+1.00)+1.6*4.79)*8*(8-0.75)^2/8"
    ws[f"{c3}{a0 + 1}"] = ref("Mo")
    ws[f"{c2}{a0 + 2}"] = x2["b"]["pynite"]
    ws[f"{c3}{a0 + 2}"] = x2["b"]["navier"]
    ws[f"{c2}{a0 + 3}"] = "=0.75*0.33*SQRT(35)*4*(150+187)*187/1000"
    ws[f"{c3}{a0 + 3}"] = ref("pvr")
    ws[f"{c2}{a0 + 4}"] = "=44*3.16*1.04"
    ws[f"{c3}{a0 + 4}"] = ref("mass")
    for i in range(5):
        rr = a0 + i
        ws[f"{lb.kol(4)}{rr}"] = f"=ABS({c3}{rr}-{c2}{rr})/{c2}{rr}*100"
        ws[f"{lb.kol(6)}{rr}"] = f'=IF({lb.kol(4)}{rr}<={lb.kol(5)}{rr},"Lolos","Tidak lolos")'
        ws[f"{lb.kol(5)}{rr}"].fill = PatternFill("solid", fgColor=AI)
    ws[f"{c2}{a0 + 2}"].fill = PatternFill("solid", fgColor=AI)
    ws[f"{c3}{a0 + 2}"].fill = PatternFill("solid", fgColor=AI)
    lb.kosong()
    lb.catatan(f"Pembanding 5.2: massa tahan karat 148,26 kg (D13-200, fc' 30, lewatan 620 mm, batang 3,24 m); 5.3 {idn(k['massa'], 2)} kg karena fc' 35 memendekkan ld "
               f"({idn(k['ld'], 0)} mm, lewatan {k['pakai']} mm, batang {idn(k['pj'], 2)} m); jumlah batang sama (D13-200).")

    # ---- Ringkasan
    lb = Lembar(wb["Ringkasan"], 2, "Ringkasan temuan dan keputusan yang diminta dari Defsa", [5, 38, 62, 46, 40])
    lb.catatan(f"STATUS: {STATUS}. " + ket)
    lb.kosong()
    lb.bagian("A", "Temuan")
    ps = q["bawah"]
    A = r["getar"]["A"]
    tt(lb, ["No", "Temuan", "Hasil kunci", "Keputusan Defsa", "Usulan AI"], [
        ["Beban dan tebal PL-1",
         f"D {idn(p['D'], 2)} kPa, qu {idn(p['qu'], 3)} kPa, Mo {idn(p['Mo'], 1)} kNm; αf {idn(p['af'], 2)}; hmin {idn(p['hmin'] * 1000, 0)} mm < 250 (lendutan tidak dihitung). "
         f"Semua lajur D13-200 (φMn terkecil {idn(min(b['phimn13'] for b in p['baris']), 1)} kNm/m); geser Vu {idn(p['Vu'], 1)} < φVc {idn(p['phiVc'], 1)} kN/m.",
         "Menyetujui fc' 35 MPa (S2) untuk pelat LT1 dan sloof.", "Setuju."],
        ["Selimut bawah",
         f"50 mm: panel MRI rasio {idn(r['alt_sel'][0.05]['pl2_rasio'], 3)}; 75 mm: rasio {idn(r['alt_sel'][0.075]['pl2_rasio'], 3)} (D13-200 tetap cukup).", "Pilih 50 / 75 mm.",
         "50 mm bila ada lantai kerja dan void former."],
        ["Panel MRI 9-10/D-E",
         f"Mu+ penentu {idn(q['mu_pos'], 1)} kNm/m ({q['pos_gov']}) vs φMn {idn(ps['phimn'], 1)}; Mu- {idn(q['mu_neg'], 1)} ({q['neg_gov']}) vs {idn(q['atas']['phimn'], 1)}. D13-200 atas dan bawah cukup.",
         "Menyetujui tulangan.", "Setuju."],
        ["Transit magnet 48,1 kN",
         f"M+ roda maks {idn(t['m_pos'], 2)} kNm/m di x pusat {idn(t['xc_w'], 1)}; Mu+ transit {idn(q['tr_pos'], 1)} < operasi {idn(q['op_pos'], 1)} kNm/m. "
         f"Pons roda rasio {idn(r['pons_roda']['rasio'], 3)}; kaki {idn(r['pons_kaki']['rasio'], 3)}.",
         "Pelat penyebar perlu / tidak.", "Tidak perlu; minta ukuran skate dari pabrikan."],
        ["SH-6",
         f"Menembus LT1; jarak ke isocenter {idn(s6['jarak_iso'], 2)} m, di luar zona tahan karat; tambahan {s6['n_x']} D13 / {s6['n_y']} D13 tiap sisi.", "Menyetujui.", "Setuju."],
        ["Baja tahan karat A955M",
         f"{k['jml']} batang D13 panjang {idn(k['pj'], 2)} m, ld {idn(k['ld'], 0)} mm, lewatan {k['pakai']} mm di luar zona: {idn(k['massa'], 1)} kg (5.2: 148,26 kg).", "Menyetujui.", "Setuju."],
        ["Getaran dan sambungan isolasi",
         f"A (monolit): fn {idn(A['fn'], 1)} Hz, F izin M-04 {idn(A['M-04']['F'], 1)} N, R-06 {idn(A['R-06']['F'], 1)} N, H M-01 {idn(A['M-01']['H'], 2)}. "
         f"B300: fn {idn(r['getar']['B30']['fn'], 1)} Hz ≈ 14,5 Hz (H {idn(r['getar']['B30']['M-01']['H'], 1)}). C: fn {idn(r['getar']['C']['fn'], 1)} Hz, "
         f"F izin M-04 {idn(r['getar']['C']['M-04']['F'], 1)} N, beton tambahan {idn(r['isolasi']['vol'], 1)} m³.",
         "Pilih A / B / C.", "A (lihat lembar Getaran dan Isolasi)."],
        ["Alat berat LT1 dan tangki",
         f"R-01 dan R-06 melebihi q izin {idn(r['alat_izin'], 2)} kPa: cek lokal rasio terbesar {idn(max(a['rasio'] for a in r['alat']), 3)}. Tangki opsi B (5.1) di atap podium utara +21,85, "
         "bukan LT1: beban lewat kolom 750 ke 5.6.", "Menyetujui.", "Setuju."],
    ], list("clllll")[:5], beku=True)

    # ---- Acuan
    lb = Lembar(wb["Acuan"], 12, "Acuan yang dipakai dan statusnya", [5, 26, 22, 56, 14, 36])
    lb.catatan(ket + " Halaman = nomor halaman PDF di acuan/privat (diverifikasi dengan pypdf, 21 Nov 2026).")
    lb.kosong()
    lb.bagian("A", "Pasal yang diverifikasi di PDF")
    tt(lb, ["No", "Acuan", "Pasal", "Isi yang dipakai", "Hal. PDF", "Status"], [
        ["SNI 1727:2020", "Tabel 4.3-1", "Rumah sakit: ruang operasi dan lab 2,87; ruang pasien 1,92; koridor di atas lantai pertama 3,83; lobi dan koridor lantai pertama (perkantoran) 4,79.", "52", "Terverifikasi"],
        ["SNI 1727:2020", "Tabel C3.1-1, C3.1-2", "Keramik, partisi, berat jenis beton.", "277-278", "dari 4.2"],
        ["SNI 2847:2019", "Tabel 19.3.2.1, R19.3.2.1", "Kelas paparan S2: w/cm maks 0,45, fc' min 31 MPa.", "464; 460", "Terverifikasi"],
        ["SNI 2847:2019", "Tabel 20.6.1.3.1", "Selimut: kontak tanah, D16 dan lebih kecil 40 mm; dicor langsung di tanah 75 mm; pelat tidak terpapar 20 mm.", "482", "Terverifikasi"],
        ["SNI 2847:2019", "Tabel 5.3.1", "1,4D; 1,2D + 1,6L.", "106", "Terverifikasi"],
        ["SNI 2847:2019", "Tabel 8.3.1.2", "Tebal minimum pelat dua arah dengan balok.", "156", "Terverifikasi"],
        ["SNI 2847:2019", "Tabel 8.6.1.1, 8.7.2.2", "As min 0,0018 Ag; spasi maksimum min(2h; 450).", "167; 171", "Terverifikasi"],
        ["SNI 2847:2019", "8.10.3.2, Tabel 8.10.4.2", "Mo = qu l2 ln²/8; distribusi momen bentang ujung.", "187; 188", "Terverifikasi"],
        ["SNI 2847:2019", "8.5.4.1", "Bukaan pada sistem pelat.", "166", "Terverifikasi"],
        ["SNI 2847:2019", "19.2.2.1", "Ec = 4700 √fc'.", "456", "Terverifikasi"],
        ["SNI 2847:2019", "Tabel 21.2.1", "φ lentur 0,90; geser 0,75; tumpu 0,65.", "491", "Terverifikasi"],
        ["SNI 2847:2019", "22.5.5.1, 22.6.4.1, Tabel 22.6.5.2", "Vc satu arah; b0 dan vc dua arah.", "508; 518; 521", "Terverifikasi"],
        ["SNI 2847:2019", "22.8.3.2", "Tumpu 0,85 fc' A1.", "540", "Terverifikasi"],
        ["SNI 2847:2019", "20.2.1.3, Tabel 20.2.2.4(a)", "Tulangan A955M (tahan karat).", "467; 472", "Terverifikasi (dari 5.2)"],
        ["SNI 2847:2019", "Tabel 25.4.2.2, Tabel 25.5.2.1", "ld dan lewatan kelas B 1,3 ld.", "588; 608", "Terverifikasi"],
        ["SNI 2052:2017", "Tabel massa nominal", "D13 1,04 kg/m (OCR 1,U2).", "8", "Terverifikasi (OCR kasar)"],
    ], list("clllcl"), beku=True)
    lb.kosong()
    lb.bagian("B", "Tidak ada di acuan")
    tt(lb, ["No", "Acuan", "Pasal", "Keterangan", "Hal. PDF", "Status"], [
        ["AISC DG11, CCIP-016, SCI P354", "-", "Pedoman getaran lantai.", "-", "belum ada di acuan"],
        ["Buku dinamika struktur", "-", "Pelat tumpuan sederhana dan SDOF.", "-", "belum ada di acuan"],
        ["SNI 2847:2019 Pasal 8.5.4.2", "-", "Tulangan tambahan tepi lubang (praktik, belum dikutip).", "-", "belum ada di acuan"],
        ["Kontak galvanik baja tahan karat - baja karbon", "-", "Pemisah di titik lewatan.", "-", "belum ada di acuan"],
        ["ASTM A955, permeabilitas magnetik, GFRP", "-", "Lihat 5.2.", "-", "belum ada di acuan"],
        ["Jarak kaki magnet dan tapak skate", "-", "Data pabrikan magnet.", "-", "belum ada di acuan"],
    ], list("clllcl"))

    # ---- Petunjuk
    lb = Lembar(wb["Petunjuk"], 1, "Petunjuk desain pelat LT1 (langkah 5.3)", [6, 120])
    lb.catatan(f"STATUS: {STATUS}. " + ket)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        "Pelat LT1 +12,85, h 250 mm, fc' 35 MPa (kelas paparan S2, keputusan 2.7), fy 420, D13; selimut bawah 50 mm dan atas 20 mm; ditumpu sloof 400 × 800 di semua as.",
        "PL-1 (umum, Lo 4,79) dihitung dengan metode desain langsung tahap4_pelat (argumen baru selimut, fc', balok); PL-2 (panel MRI 9-10/D-E, Lo 2,87) dengan DDM ditambah beban titik.",
        "Beban titik: deret Navier (beban persegi, pelat tumpuan sederhana) dan PyNite sebagai pembanding; momen negatif tambahan dari model tiga tepi jepit satu tepi sendi (PyNite).",
        "Zona baja tahan karat A955M x 79,5-81,5 / y 56-58 (keputusan 5.2); lewatan di luar zona. SH-6 menembus LT1 dan berada di luar zona.",
        "Getaran: opsi A (monolit), B (tebal 300 dan 350), C (sambungan isolasi) disusun sebagai perbandingan tanpa keputusan.",
        "Sel hijau diisi AI atas permintaan Defsa. Sel putih berisi rumus Excel (dihitung ulang dan dicocokkan dengan Python di cocokkan()).",
        "Lembar: Ringkasan; Beban; Panel Tipikal; Panel MRI; Transit Magnet; Pons dan Tumpu; Lubang SH-6; Baja Tahan Karat; Getaran dan Isolasi; Cek Silang T-92; Acuan.",
    ])], rata=list("cl"))

    for ws in wb:   # sheet berisi beberapa tabel berbeda: ulang kepala saat cetak menyesatkan
        if ws.title not in ("Petunjuk", "Pons dan Tumpu"):
            ws.print_title_rows = None
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
    ws = wb["Cek Silang T-92"]
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and len(c.value) > 3 and c.value[0] == "(" and c.value[1] in "abcd" and c.value[2] == ")":
                st = ws.cell(c.row, c.column + 5).value
                n_cek += 1
                if st != "Lolos":
                    pesan.append(f"T-92 {c.value}: status {st}")
    return not pesan, "; ".join(pesan) or f"semua {n_cek} rumus/cek Excel cocok dengan Python"


# ------------------------------------------------------------------ ringkasan .md
def _md_baris(rows, n=4):
    return "\n".join("| " + " | ".join(str(c) for c in a[:n]) + " |" for a in rows)


def buat_md(keluar=KELUAR / "5.3 Desain Pelat LT1.md"):
    r = hitung()
    p, q, t, k, pl = r["pl1"], r["pl2"], r["transit"], r["tk"], r["pelindung"]
    A, B3, C = (r["getar"][x] for x in ("A", "B30", "C"))
    s6 = [x for x in r["lubang"] if x["kode"] == "SH-6"][0]
    pk, pr = r["pons_kaki"], r["pons_roda"]
    x2 = r["t92"]
    alt = r["alt_sel"]
    judul = f"5.3 Desain Pelat LT1 ({'disetujui Defsa ' + KEPUTUSAN.split(':')[0] if KEPUTUSAN else STATUS})"
    teks = f"""# {judul}

Disusun AI 21 Nov 2026. Data simulasi. Rincian angka di `5.3 Desain Pelat LT1.xlsx` (`skrip/tahap5_pelat_lt1.py`, uji `tests/test_tahap5_pelat_lt1.py`).
Data dari `04 Struktur Atas/Data Owner/Data Beban MEP Rinci.xlsx`; beban dari 4.2; metode desain langsung dari 4.5 (`tahap4_pelat`).

## Sistem, mutu, selimut

Pelat LT1 +12,85, tebal 250 mm, struktural, ditumpu sloof 400 × 800 di semua as (grid 8 × 8 m); sisi atas sloof = sisi atas pelat. Mutu **fc' 35 MPa**, fy 420 MPa,
tulangan D13. Kelas paparan S2 (keputusan 2.7): SNI 2847:2019 Tabel 19.3.2.1 (hal PDF 464) w/cm maks 0,45 dan fc' min 31 MPa (R19.3.2.1 hal PDF 460); sloof yang dicor
bersama ikut S2. Selimut bawah **50 mm** (Tabel 20.6.1.3.1 hal PDF 482: kontak tanah D16 dan lebih kecil 40 mm + 10 mm perlindungan asam [Asumsi 2.7]); atas 20 mm
(tidak terpapar). Pembanding cor langsung di atas tanah: 75 mm. Kombinasi 1,4D dan 1,2D + 1,6L (Tabel 5.3.1, hal PDF 106).

| Selimut bawah | d | Akibat |
|---|---|---|
| 50 mm | {idn(alt[0.05]['d'] * 1000, 1)} mm | PL-1 ujung positif tengah As {idn(alt[0.05]['as'], 0)} mm²/m; panel MRI rasio D13-200 {idn(alt[0.05]['pl2_rasio'], 3)} |
| 75 mm | {idn(alt[0.075]['d'] * 1000, 1)} mm | PL-1 As {idn(alt[0.075]['as'], 0)} mm²/m (+{idn((alt[0.075]['as'] / alt[0.05]['as'] - 1) * 100, 0)} %); panel MRI rasio D13-200 {idn(alt[0.075]['pl2_rasio'], 3)} (spasi {alt[0.075]['pl2_s']:.0f}) |

## Beban dan PL-1

D = 23,6 × 0,25 + keramik 1,10 + partisi 1,00 = {idn(p['D'], 2)} kPa (tanpa plafon dan gantung: tidak ada ruang di bawah LT1). Lo = 4,79 kPa (Tabel 4.3-1, hal PDF 52: lobi dan koridor lantai pertama) untuk
seluruh LT1 (**PL-1**); ruang tindakan dan periksa 2,87 atau kurang, tercakup. qu = {idn(p['qu'], 3)} kPa; ln = {idn(p['ln'], 2)} m; Mo = {idn(p['Mo'], 1)} kNm.
αf sloof = {idn(p['af'], 2)} (> 2,0); **hmin = {idn(p['hmin'] * 1000, 1)} mm** (Tabel 8.3.1.2, hal PDF 156) < 250 mm: lendutan tidak dihitung. As min 450 mm²/m, s maks 450 mm;
Vu {idn(p['Vu'], 1)} kN/m < φVc {idn(p['phiVc'], 1)} kN/m.

| Lokasi | Mu, d, As perlu | Tulangan | Cek |
|---|---|---|---|
{_md_baris(teks_tulangan_pl1(r))}

Panel interior memakai baris interior; tepi dan sudut memakai baris ujung (arah tegak lurus tepi). Seluruh LT1 **D13-200 atas dan bawah dua arah**.

### Alat berat LT1 (q izin = {idn(r['alat_izin'], 2)} kPa)

| Alat | Beban dan tapak | q (kPa) | Cek |
|---|---|---|---|
{_md_baris(teks_alat(r))}

## Panel MRI 9-10/D-E (PL-2)

Panel x 76-84 / y 51-59, tepi timur = tepi gedung. D = {idn(q['D'], 3)} kPa (dengan sangkar RF 0,655), Lo 2,87, qu {idn(q['qu'], 3)} kPa. Momen positif = DDM + beban titik (tumpuan sederhana, konservatif):
DDM {idn(q['pos_ddm'], 2)} + kaki magnet {idn(r['kaki']['M'], 2)} = **{idn(q['op_pos'], 2)} kNm/m** (operasi) atau {idn(q['pos_ddm'] * q['skala_tr'], 2)} + roda {idn(t['m_pos'], 2)} = {idn(q['tr_pos'], 2)} (transit);
negatif {idn(q['mu_neg'], 2)} kNm/m (tiga tepi jepit, tepi timur sendi). **Tulangan: D13-{q['bawah']['s']:.0f} bawah (φMn {idn(q['bawah']['phimn'], 1)}, rasio {idn(q['mu_pos'] / q['bawah']['phimn'], 3)}) dan
D13-{q['atas']['s']:.0f} atas (φMn {idn(q['atas']['phimn'], 1)}, rasio {idn(q['mu_neg'] / q['atas']['phimn'], 3)}) dua arah**. Kaki magnet di isocenter ± 0,80 / ± 0,60 m [Asumsi: jarak kaki tidak ada di data owner].

Dinding pelindung R-04: utara y 60 (x 77-84) {idn(pl['w'], 2)} kN/m' berada di panel 9-10/E-F, 1,0 m dari as E: M- di E {idn(pl['M'], 2)} kNm/m; Mu atas PL-1 {idn(pl['Mu_tot'], 2)} vs φMn {idn(pl['phimn'], 2)}:
{'cukup' if pl['ada_cukup'] else 'perlu tulangan atas lebih rapat'}. Dinding timur x 84 ({idn(pl['timur'], 1)} kN) langsung ke sloof as 10: **dicatat untuk 5.4**.

## Transit magnet 48,1 kN

Empat roda 12,03 kN, segi empat 1,2 × 1,2 m, tapak 150 × 150 mm [Asumsi], dari bukaan x 84 ke isocenter sepanjang y 57,0; 1,2D + 1,6T, Lo 0.

| Posisi | M+ Navier | M+ PyNite | M- PyNite jepit |
|---|---|---|---|
{_md_baris(teks_transit(r))}

M+ roda maksimum **{idn(t['m_pos'], 2)} kNm/m** (Navier {idn(t['m_nav'], 2)} di x pusat {idn(t['xc_w'], 2)}); Mu+ transit {idn(q['tr_pos'], 2)} < operasi {idn(q['op_pos'], 2)}; rasio transit
{idn(q['tr_pos'] / q['bawah']['phimn'], 3)} dari φMn. **Pelat penyebar tidak diperlukan**; pengaruh ukuran penyebar per roda:

| Penyebar | M+ roda | Mu+ transit | Terhadap φMn D13-200 |
|---|---|---|---|
{_md_baris(teks_penyebar(r))}

## Pons dan tumpu (d {idn(pr['d'], 0)} mm, fc' 35)

| Beban | Vu | φVc | Rasio | Tumpu |
|---|---|---|---|---|
| Kaki magnet 12 kN (0,25 × 0,25) | {idn(pk['vu'], 1)} kN | {idn(pk['phivc'], 1)} kN | {idn(pk['rasio'], 4)} | 1,2 × {idn(r['tumpu']['q'], 0)} kPa / φ0,85fc' {idn(r['tumpu']['phi'], 0)} = {idn(r['tumpu']['rasio'], 4)} |
| Satu roda 12,03 kN (0,15 × 0,15) | {idn(pr['vu'], 1)} kN | {idn(pr['phivc'], 1)} kN | {idn(pr['rasio'], 4)} | 1,6 × {idn(r['tumpu']['q_roda'], 0)} / {idn(r['tumpu']['phi'], 0)} = {idn(r['tumpu']['rasio_roda'], 4)} |

## Lubang SH-6

SH-6 (0,6 × 0,6 m, x 82,1-82,7 / y 54,7-55,3) **menembus pelat LT1** sampai atap podium utara dan sudah termuat di `tahap4_pelat.BUKAAN`. Jarak ke isocenter {idn(s6['jarak_iso'], 2)} m (> 1,0 m),
tidak memotong zona tahan karat, {idn(s6['jarak_roda_y'], 2)} m dari tapak roda transit. Tulangan tambahan tepi lubang: {s6['n_x']} D13 tiap sisi bawah dan atas (praktik 8.5.4.2, belum dikutip), panjang ukuran + 2 ld.
Shaft SH-1, SH-2, SH-3, SH-5 juga menembus LT1 (tabel di Excel). Tepi pit lift dirujuk ke 5.5.

## Baja tahan karat A955M (zona x 79,5-81,5 / y 56-58)

fy 420 [Asumsi mutu]; ld D13 = {idn(k['ld'], 1)} mm (Tabel 25.4.2.2, hal PDF 588, fc' 35); lewatan kelas B 1,3 ld = {idn(k['lap'], 1)} → {k['pakai']} mm (Tabel 25.5.2.1, hal PDF 608), seluruhnya di luar zona;
batang {idn(k['pj'], 2)} m (2,0 + 2 × lewatan); {k['nb_b']} batang per lapis (D13-{k['s_b']:.0f}) × 4 lapis = {k['jml']} batang; massa **{idn(k['massa'], 2)} kg** (D13 1,04 kg/m, SNI 2052:2017).
Dibanding 5.2 (148,26 kg): lebih kecil {idn((1 - k['massa'] / 148.26) * 100, 1)} % karena fc' 35 memendekkan ld dan lewatan (620 → {k['pakai']} mm); jumlah batang sama. Kawat ikat dan kursi/penahan jarak
tahan karat atau plastik [Asumsi, syarat pabrikan]. Kontak galvanik baja tahan karat - baja karbon: belum ada di acuan.

## Getaran dan sambungan isolasi panel MRI

Batas 0,5 × 10⁻³ g (0-50 Hz). Metode 5.2 (pelat 8 × 8 tumpuan sederhana = batas bawah fn; Ec 4700 √35 = {idn(A['ec'], 0)} MPa). Pedoman getaran lantai (AISC DG11, CCIP-016, SCI P354): belum ada di acuan.

| Opsi | fn (Hz) | H dan F izin | Akibat |
|---|---|---|---|
{_md_baris(teks_getar_banding(r))}

**Usulan AI** (berdasarkan angka): opsi A dipertahankan; hindari tebal 300 (fn {idn(B3['fn'], 1)} Hz ≈ 14,5 Hz kipas M-01, H {idn(B3['M-01']['H'], 1)}); opsi C menurunkan F izin M-04 menjadi {idn(C['M-04']['F'], 1)} N dan memutus
diafragma. Semua opsi bergantung pada gaya dinamis sumber dari pabrikan dan pengukuran setelah konstruksi. Keputusan di tangan Defsa.

## Pelat dasar tangki opsi B (5.1)

Tangki 8 × 8 × 3,5 m di bay 7-8/F-G dengan pelat dua arah 350 berada di atap podium utara +21,85, bukan LT1: tidak relevan untuk pelat LT1; beban lewat kolom 750 ke 5.6.

## Cek silang T-92

| Cek | Cara 1 | Cara 2 | Selisih | Toleransi |
|---|---|---|---|---|
| (a) qu PL-1 | tangan {idn(x2['a']['qu_tangan'], 3)} kPa | skrip {idn(x2['a']['qu_skrip'], 3)} kPa | {idn(abs(x2['a']['qu_skrip'] / x2['a']['qu_tangan'] - 1) * 100, 2)} % | 0,5 % |
| (a) Mo PL-1 | tangan {idn(x2['a']['mo_tangan'], 2)} kNm | skrip {idn(x2['a']['mo_skrip'], 2)} kNm | {idn(abs(x2['a']['mo_skrip'] / x2['a']['mo_tangan'] - 1) * 100, 2)} % | 0,5 % |
| (b) Mx tengah 8 × 8, 48,1 kN pada 0,8 × 0,8 | PyNite {idn(x2['b']['pynite'], 3)} kNm/m | Navier {idn(x2['b']['navier'], 3)} kNm/m | {idn(abs(x2['b']['pynite'] / x2['b']['navier'] - 1) * 100, 2)} % | 5 % |
| (c) φVc pons roda | tangan {idn(x2['c']['tangan'], 2)} kN | skrip {idn(x2['c']['skrip'], 2)} kN | {idn(abs(x2['c']['skrip'] / x2['c']['tangan'] - 1) * 100, 2)} % | 0,5 % |
| (d) massa tahan karat | tangan 44 × 3,16 × 1,04 = {idn(x2['d']['tangan'], 2)} kg | skrip {idn(x2['d']['skrip'], 2)} kg | {idn(abs(x2['d']['skrip'] / x2['d']['tangan'] - 1) * 100, 2)} % | 0,5 % |

## Data yang masih kurang

1. Jarak antar kaki magnet dan tapak skate/roda dari pabrikan (dipakai [Asumsi]).
2. Gaya dinamis M-04 dan R-06; pedoman getaran lantai.
3. Tata letak LT1 sebenarnya: rekam medis dan farmasi (arsip padat 7,18 kPa) dan R-09 dinding timbal sebagai beban garis.
4. Tumpuan balok tambahan opsi C; ukuran celah isolasi (25 mm [Asumsi]).

## Yang perlu diputuskan Defsa

1. **fc' 35 MPa (S2)** untuk pelat LT1 dan sloof yang dicor bersama (usulan AI: setuju; fc' min 31 MPa).
2. **Selimut bawah 50 mm** (lantai kerja/void former) **atau 75 mm** (cor langsung di tanah): D13-200 tetap cukup untuk keduanya (usulan AI: 50 mm dengan lantai kerja).
3. **Sambungan isolasi panel MRI A / B / C** (usulan AI: A; hindari tebal 300).
4. **Pelat penyebar beban transit**: tidak diperlukan; putuskan bila skate pabrikan bertapak lebih kecil.
5. Beban hidup rekam medis dan farmasi (4,79 dipakai; arsip padat 7,18 menaikkan qu sekitar 22 %).
6. Beban garis dinding timbal R-09 dan pelindung timur R-04 ke 5.4.
"""
    if KEPUTUSAN:
        teks += f"\n## Keputusan Defsa\n\n{KEPUTUSAN}\n"
    keluar.write_text(teks, encoding="utf-8")
    return keluar


def ke_pdf(berkas=BERKAS, pdf=None):
    return mri.ke_pdf(berkas, pdf)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    r = hitung()
    print(buat_excel())
    print(cocokkan())
    print(buat_md())
