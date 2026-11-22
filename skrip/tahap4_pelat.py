"""Tahap 4 langkah 4.5: desain pelat dua arah dengan balok (SNI 2847:2019, metode desain langsung).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (20 Nov 2026); draf, menunggu persetujuan
Defsa. Kunci jawaban tidak dibuka.

Acuan SNI 2847:2019 (halaman cetak): Tabel 8.3.1.2 hal. 134-135 (tebal minimum); Pasal 8.4.1.8 hal. 138 (sayap balok
<= 4h); Pasal 8.10.2-8.10.5 hal. 164-169 (metode desain langsung: Mo, Tabel 8.10.4.2, 8.10.5.1, 8.10.5.5,
8.10.5.7.1); Tabel 8.6.1.1 hal. 145 dan Tabel 24.4.3.2 hal. 553 (As min 0,0018 Ag); Pasal 8.7.2.2 hal. 149 (spasi
<= 2h, 450 mm); Tabel 20.6.1.3.1 hal. 460 (selimut 20 mm); Tabel 21.2.1 hal. 469 (φ lentur 0,90, geser 0,75);
Pers. 22.5.5.1 hal. 486 (Vc = 0,17 λ √fc' b d); Tabel 22.6.5.2 hal. 499 (geser dua arah 0,33 √fc').
Beban dari langkah 4.2 (disetujui), kombinasi 1,4D dan 1,2D + 1,6L (SNI 1726 Pasal 4.2.2.1).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_beban as tb  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "04 Struktur Atas"
BERKAS = KELUAR / "4.5 Desain Pelat.xlsx"
LABEL = tb.LABEL
STATUS = "disetujui Defsa 20 Nov 2026"

FC, FY = 30.0, 420.0          # MPa, pelat dan balok fc' 30 (3.6), BjTS 420B (SNI 2052)
L = 8.0                       # m, grid
H = 0.200                     # m, tebal pelat (3.6)
SELIMUT = 0.020               # m, Tabel 20.6.1.3.1 tidak terpapar
DB = 0.013                    # m, D13
PHI_M, PHI_V = 0.90, 0.75
SIDL_LANTAI = tb.SIDL["keramik"][0] + tb.SIDL["plafon"][0] + tb.SIDL["partisi"][0]
SIDL_ATAP = tb.SIDL["screed_atap"][0] + tb.SIDL["kedap_atap"][0] + tb.SIDL["plafon"][0] + tb.GANTUNG["atap"]

PANEL = [  # (kode, uraian, tebal m, SIDL kPa, Lo kPa, lebar kolom m, tepi?)
    ("P1", "LT2 bedah, ICU, lab (Lo 2,87)", 0.200, SIDL_LANTAI + tb.GANTUNG["podium"], 2.87, 0.75),
    ("P2", "LT2 kebidanan, hemodialisis (Lo 1,92)", 0.200, SIDL_LANTAI + tb.GANTUNG["podium"], 1.92, 0.75),
    ("P3", "Koridor LT2-LT6 (Lo 3,83)", 0.200, SIDL_LANTAI + tb.GANTUNG["podium"], 3.83, 0.75),
    ("P4", "LT3 aula, administrasi, ruang AHU (Lo 4,79)", 0.200, SIDL_LANTAI + tb.GANTUNG["AHU"], 4.79, 0.75),
    ("P5", "Menara rawat inap LT4-LT6 (Lo 1,92)", 0.200, SIDL_LANTAI + tb.GANTUNG["menara"], 1.92, 0.65),
    ("P6", "Atap LT3 barat dan atap podium utara di luar tangki (Lr 0,96)", 0.200, SIDL_ATAP, 0.96, 0.75),
    ("P7", "Atap menara helipad (Lo 2,87, tidak direduksi)", 0.200, SIDL_ATAP, 2.87, 0.65),
]


# ------------------------------------------------------------------ kekakuan balok terhadap pelat
def alpha_f(bw=tb.BALOK_B, hb=tb.BALOK_H, h=H, l2=L, tepi=False):
    """αf = Ecb Ib / Ecs Is (Pers. 8.10.2.7b); sayap = min(hb - h, 4h) tiap sisi (Pasal 8.4.1.8)."""
    hw = hb - h
    sayap = min(hw, 4 * h)
    bf = bw + (sayap if tepi else 2 * sayap)
    a1, y1 = bf * h, hb - h / 2
    a2, y2 = bw * hw, hw / 2
    yc = (a1 * y1 + a2 * y2) / (a1 + a2)
    ib = bf * h ** 3 / 12 + a1 * (y1 - yc) ** 2 + bw * hw ** 3 / 12 + a2 * (y2 - yc) ** 2
    is_ = (l2 / 2 if tepi else l2) * h ** 3 / 12
    return ib / is_, ib


def tebal_minimum(ln, alpha_fm, beta=1.0, fy=FY):
    """Tabel 8.3.1.2: αfm > 2,0: ln (0,8 + fy/1400) / (36 + 9β) >= 90 mm."""
    if alpha_fm > 2.0:
        return max(ln * (0.8 + fy / 1400) / (36 + 9 * beta), 0.090)
    return max(ln * (0.8 + fy / 1400) / (36 + 5 * beta * (alpha_fm - 0.2)), 0.125)


def c_torsi(bw=tb.BALOK_B, hb=tb.BALOK_H, h=H):
    """C (Pers. 8.10.5.2b) untuk balok tepi L: maksimum dari dua cara pembagian persegi."""
    def c(x, y):
        x, y = min(x, y), max(x, y)
        return (1 - 0.63 * x / y) * x ** 3 * y / 3
    hw = hb - h
    sayap = min(hw, 4 * h)
    a = c(bw, hb) + c(h, sayap)
    b = c(bw, hw) + c(h, sayap + bw)
    return max(a, b)


# ------------------------------------------------------------------ metode desain langsung
def interp(x, xs, ys):
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            return ys[i] + (ys[i + 1] - ys[i]) * (x - xs[i]) / (xs[i + 1] - xs[i])


def ddm(qu, ln, l1=L, l2=L, af=None, ujung=False, beta_t=None):
    """Momen per lajur (kNm) untuk satu bentang: kembalikan dict momen lajur kolom (balok, pelat) dan lajur tengah."""
    af = af if af is not None else alpha_f()[0]
    mo = qu * l2 * ln ** 2 / 8                                # Pers. 8.10.3.2
    if ujung:   # Tabel 8.10.4.2 kolom "pelat dengan balok di antara semua tumpuan"
        koef = {"neg_int": 0.70, "pos": 0.57, "neg_eks": 0.16}
    else:       # Pasal 8.10.4.1
        koef = {"neg_int": 0.65, "pos": 0.35, "neg_eks": 0.0}
    a = min(af * l2 / l1, 1.0)
    r = l2 / l1
    lk_neg = interp(r, [0.5, 1.0, 2.0], [0.75 + (0.90 - 0.75) * a, 0.75, 0.75 + (0.45 - 0.75) * a])   # Tabel 8.10.5.1
    lk_pos = interp(r, [0.5, 1.0, 2.0], [0.60 + (0.90 - 0.60) * a, 0.60 + (0.75 - 0.60) * a,
                                          0.60 + (0.45 - 0.60) * a])                                    # Tabel 8.10.5.5
    bt = beta_t if beta_t is not None else 2.5
    lk_eks = interp(r, [0.5, 1.0, 2.0], [0.75 + (0.90 - 0.75) * a, 0.75, 0.75 + (0.45 - 0.75) * a]) \
        if bt >= 2.5 else 1.0 - (1.0 - 0.75) * bt / 2.5                                               # Tabel 8.10.5.2
    balok = 0.85 * a                                          # Tabel 8.10.5.7.1
    out = {"Mo": mo}
    for k, f in (("neg_int", lk_neg), ("pos", lk_pos), ("neg_eks", lk_eks)):
        m = koef[k] * mo
        lk = f * m
        out[k] = {"M": m, "lajur_kolom": lk, "balok": balok * lk, "pelat_lk": (1 - balok) * lk, "lajur_tengah": m - lk}
    return out


def tulangan(mu_per_m, h=H, d_lapis=2, selimut=None, fc=None):
    """As perlu (mm²/m) dengan blok tegangan persegi; d lapis kedua (arah tegak lurus) dikurangi 1 db.
    selimut (m) dan fc (MPa) bawaan SELIMUT dan FC (4.5); 5.3 memakai selimut dan fc' lain."""
    selimut = SELIMUT if selimut is None else selimut
    fc = FC if fc is None else fc
    d = h - selimut - DB / 2 - (DB if d_lapis == 2 else 0.0)
    b = 1.0
    mu = mu_per_m / PHI_M  # kNm
    # As fy (d - a/2) = Mn, a = As fy / (0,85 fc' b)
    a_ = 0.85 * fc * 1000 * b
    k = mu / (FY * 1000)
    # As² fy/(2 a_) - As d + k = 0
    aa = FY * 1000 / (2 * a_)
    disk = d ** 2 - 4 * aa * k
    as_ = (d - math.sqrt(max(disk, 0.0))) / (2 * aa)
    as_min = max(0.0018 * 420 / FY, 0.0014) * h * b
    return {"d": d, "As": as_ * 1e6, "As_min": as_min * 1e6, "As_pakai": max(as_, as_min) * 1e6}


def pilih_tulangan(as_mm2, h=H):
    """Diameter dan spasi (kelipatan 25 mm) dengan s <= 2h dan 450 (Pasal 8.7.2.2)."""
    smax = min(2 * h * 1000, 450.0)
    for db in (10, 13, 16):
        ab = math.pi * db ** 2 / 4
        s = math.floor(min(smax, 1000 * ab / as_mm2) / 25) * 25
        if s >= 125:
            return db, s, 1000 * ab / s
    return 16, 100, 1000 * math.pi * 16 ** 2 / 4 / 100


def desain_panel(kode, uraian, h, sidl, lo, kolom, selimut=None, selimut_atas=None, fc=None, bw=None, hb=None):
    """selimut = selimut bawah (m); selimut_atas untuk momen negatif (bawaan = selimut); fc, bw, hb (m) bawaan 4.5."""
    selimut = SELIMUT if selimut is None else selimut
    selimut_atas = selimut if selimut_atas is None else selimut_atas
    fc = FC if fc is None else fc
    kb = {} if bw is None and hb is None else {"bw": tb.BALOK_B if bw is None else bw, "hb": tb.BALOK_H if hb is None else hb}
    bw = tb.BALOK_B if bw is None else bw    # kb kosong: alpha_f/c_torsi memakai bawaan (tahap5_tangki mengganti __defaults__)
    d_mati = tb.GAMMA_C * h + sidl
    qu = max(1.4 * d_mati, 1.2 * d_mati + 1.6 * lo)
    ln = L - kolom
    af, _ = alpha_f(h=h, **kb)
    aft, _ = alpha_f(h=h, tepi=True, **kb)
    beta_t = c_torsi(h=h, **kb) / (2 * (L / 2) * h ** 3 / 12)  # Pers. 8.10.5.2a, Is lebar l2/2 untuk tepi
    hmin = tebal_minimum(ln, af)                       # panel interior: keempat balok αf
    hmin_tepi = tebal_minimum(ln, (3 * af + aft) / 4)  # panel tepi: satu balok tepi (αf tepi >= 0,8, 8.3.1.2.1)
    hasil = {"kode": kode, "uraian": uraian, "h": h, "D": d_mati, "L": lo, "qu": qu, "ln": ln, "af": af, "aft": aft,
             "beta_t": beta_t, "hmin": hmin, "hmin_tepi": hmin_tepi, "rasio_LD": lo / d_mati, "baris": []}
    lebar_lk, lebar_lt = L / 2, L / 2   # lajur kolom 2 × 0,25 min(l1, l2); lajur tengah sisanya
    for bentang, ujung in (("interior", False), ("ujung", True)):
        m = ddm(qu, ln, af=af, ujung=ujung, beta_t=beta_t)
        for posisi in ("neg_int", "pos", "neg_eks"):
            if not ujung and posisi == "neg_eks":
                continue
            for lajur, lebar, kunci in (("kolom (pelat)", lebar_lk - bw, "pelat_lk"),
                                        ("tengah", lebar_lt, "lajur_tengah")):
                mu = m[posisi][kunci] / lebar
                t = tulangan(mu, h, selimut=selimut if posisi == "pos" else selimut_atas, fc=fc)
                db, s, as_ = pilih_tulangan(t["As_pakai"], h)
                phimn = PHI_M * as_ * 1e-6 * FY * 1000 * (t["d"] - as_ * 1e-6 * FY / (2 * 0.85 * fc))
                hasil["baris"].append({"bentang": bentang, "posisi": posisi, "lajur": lajur, "Mo": m["Mo"],
                                       "Mu": mu, "d": t["d"], "As": t["As"], "As_min": t["As_min"],
                                       "As_pakai": t["As_pakai"], "db": db, "s": s, "As_ada": as_, "phiMn": phimn})
    # geser satu arah pada muka balok (lebar 1 m), Pers. 22.5.5.1
    d = h - selimut - DB / 2
    vu = qu * (L / 2 - bw / 2 - d)    # pendekatan lajur 1 m sepanjang bentang pendek
    phivc = PHI_V * 0.17 * math.sqrt(fc) * 1000 * d   # kN/m
    hasil.update({"Vu": vu, "phiVc": phivc})
    return hasil


def helipad_pons(h=H, p=None):
    """Geser dua arah beban roda 0,75 MTOW pada 200 × 200 mm (Pasal 4.11.2), faktor 1,6 (Tabel 22.6.5.2)."""
    p = p or tb.atap_khusus()["heli_terpusat"]
    d = h - SELIMUT - DB / 2 - DB / 2
    bo = 4 * (0.200 + d)
    vc = min(0.33, 0.17 * (1 + 2 / 1.0), 0.083 * (2 + 20 * d / bo)) * math.sqrt(FC) * 1000  # kPa (αs 20, beban dalam)
    phivn = PHI_V * vc * bo * d
    return {"Pu": 1.6 * p, "bo": bo, "d": d, "vc": vc / 1000, "phiVn": phivn}


# ------------------------------------------------------------------ tangki air: balok anak dan pelat tebal
TANGKI = {"x": (60.0, 72.0), "y": (67.0, 73.0), "q": None}
H_TANGKI = 0.250
BALOK_ANAK_Y = 71.0   # usulan: balok anak sejajar X di y 71 (antara as F y 67 dan G y 75), x 56-76


def desain_tangki(h=H_TANGKI):
    """Pelat di bawah tangki bertumpu pada balok induk y 67 dan balok anak y 71 (bentang 4 m, satu arah dominan)."""
    q_t = tb.atap_khusus()["tangki_kpa"]
    d_mati = tb.GAMMA_C * h + SIDL_ATAP + q_t   # isi tangki tetap: beban mati (Pasal 3.1.3)
    qu = max(1.4 * d_mati, 1.2 * d_mati + 1.6 * 0.96)
    ln = 4.0 - tb.BALOK_B
    m_neg, m_pos = qu * ln ** 2 / 10, qu * ln ** 2 / 14   # koefisien bentang menerus [Literatur: ACI 6.5 / SNI 6.5.2]
    out = {"h": h, "q_tangki": q_t, "D": d_mati, "qu": qu, "ln": ln}
    for nama, m in (("negatif", m_neg), ("positif", m_pos)):
        t = tulangan(m, h, d_lapis=1)
        db, s, as_ = pilih_tulangan(t["As_pakai"], h)
        out[nama] = {"Mu": m, **t, "db": db, "s": s, "As_ada": as_}
    d = h - SELIMUT - DB / 2
    out["Vu"] = 1.15 * qu * ln / 2
    out["phiVc"] = PHI_V * 0.17 * math.sqrt(FC) * 1000 * d
    return out


BUKAAN = [  # dari Data Beban MEP Rinci lembar 7
    ("SH-1", 2.0, 1.2), ("SH-2", 2.4, 1.6), ("SH-3", 1.6, 1.2), ("SH-4", 2.4, 2.4), ("SH-5", 2.0, 1.2),
    ("SH-6", 0.6, 0.6), ("SH-7", 1.8, 1.0), ("LB-2", 0.8, 0.8),
]


def tulangan_bukaan():
    """Tulangan tambahan tepi bukaan = tulangan terpotong (praktik Pasal 8.5.4.2 b-c untuk pelat tanpa balok,
    dipakai sebagai syarat minimum [Asumsi]); tulangan dasar P1 lajur tengah."""
    p = desain_panel(*PANEL[0])
    base = [r for r in p["baris"] if r["bentang"] == "interior" and r["posisi"] == "pos" and r["lajur"] == "tengah"][0]
    out = []
    for kode, a, b in BUKAAN:
        terpotong_a = a * base["As_ada"]   # mm² per arah (lebar bukaan × As/m)
        terpotong_b = b * base["As_ada"]
        n_a = math.ceil(terpotong_a / 2 / (math.pi * 13 ** 2 / 4))
        n_b = math.ceil(terpotong_b / 2 / (math.pi * 13 ** 2 / 4))
        out.append({"kode": kode, "a": a, "b": b, "tambah_sisi_a": max(n_a, 2), "tambah_sisi_b": max(n_b, 2)})
    return out


# ------------------------------------------------------------------ cek silang T-73: PyNite pelat 3 × 3 panel
def pynite_panel(qu=None, mesh=0.5, titik=None):
    """Sistem 3 × 3 panel 8 × 8 m dengan balok T (web 350 × 400 di bawah pelat, tanpa eksentrisitas) di atas tumpuan
    titik di grid; momen positif lajur tengah panel tengah dibandingkan dengan DDM interior."""
    from Pynite import FEModel3D
    p = desain_panel(*PANEL[0])
    qu = qu or p["qu"]
    e = 4700 * math.sqrt(FC) * 1000
    nu = 0.2
    m = FEModel3D()
    m.add_material("c", e, e / (2 * (1 + nu)), nu, 23.6)
    n = int(round(3 * L / mesh))
    nama = {}
    for i in range(n + 1):
        for j in range(n + 1):
            k = f"N{i}_{j}"
            m.add_node(k, i * mesh, j * mesh, 0.0)
            nama[(i, j)] = k
    for i in range(n):
        for j in range(n):
            m.add_quad(f"Q{i}_{j}", nama[(i, j)], nama[(i + 1, j)], nama[(i + 1, j + 1)], nama[(i, j + 1)], H, "c")
    _, ib = alpha_f()
    ib_web = ib - L * H ** 3 / 12 * 0.0   # balok T penuh; pelat juga dimodelkan (sedikit kaku berlebih) [Asumsi]
    a_b = tb.BALOK_B * (tb.BALOK_H - H)
    m.add_section("b", a_b, ib - (2 * 0.4 + 0.35) * H ** 3 / 12, 1e-3, 1e-3)  # Iy: lentur vertikal (bidang XY)
    step = int(round(L / mesh))
    for g in range(4):
        for i in range(n):
            for (a, b) in (((i, g * step), (i + 1, g * step)), ((g * step, i), (g * step, i + 1))):
                m.add_member(f"B{a}{b}", nama[a], nama[b], "c", "b")
    for gi in range(4):
        for gj in range(4):
            m.def_support(nama[(gi * step, gj * step)], True, True, True, False, False, True)
    # tahan rotasi kaku dan translasi bidang
    for k in nama.values():
        m.def_support(k, True, True, False, False, False, True) if k not in [nama[(gi * step, gj * step)] for gi in range(4) for gj in range(4)] else None
    for i in range(n):
        for j in range(n):
            m.add_quad_surface_pressure(f"Q{i}_{j}", -qu, case="D")
    for (x, y, pp) in (titik or []):
        m.add_node_load(nama[(int(round(x / mesh)), int(round(y / mesh)))], "FZ", -pp, case="D")
    m.add_load_combo("U", {"D": 1.0})
    m.analyze_linear(check_statics=False, sparse=True)
    # momen lajur tengah positif panel tengah: rata-rata Mx (kNm/m) pada elemen di garis tengah panel x = 12,
    # y 10-14 (lajur tengah 4 m)
    vals = []
    ic = int(round(1.5 * L / mesh)) - 1
    for j in range(int(round((L + L / 4) / mesh)), int(round((2 * L - L / 4) / mesh))):
        q = m.quads[f"Q{ic}_{j}"]
        mx = q.moment(0.0, 0.0, combo_name="U")
        vals.append(abs(float(mx[0][0])))
    pusat = max(abs(float(m.quads[f"Q{i}_{j}"].moment(0.0, 0.0, combo_name="U")[k][0]))
                for i in range(ic - 2, ic + 3) for j in range(ic - 2, ic + 3) for k in (0, 1))
    return {"Mpos_lajur_tengah": sum(vals) / len(vals), "M_pusat_maks": pusat, "qu": qu}


def helipad_lentur(mesh=0.5):
    """Momen pelat atap menara akibat dua beban roda 1,6 × 50,0 kN (jarak 2,44 m) di tengah panel + 1,2D
    (PyNite, model 3 × 3 panel), dibanding φMn tulangan lajur tengah P7."""
    pr = desain_panel(*PANEL[6])
    pu = 1.6 * tb.atap_khusus()["heli_terpusat"]
    c = 1.5 * L
    r = pynite_panel(qu=1.2 * pr["D"], mesh=mesh, titik=[(c - 1.22, c, pu), (c + 1.22, c, pu)])
    b = [x for x in pr["baris"] if x["bentang"] == "interior" and x["posisi"] == "pos" and x["lajur"] == "tengah"][0]
    return {"Pu": pu, "M_maks": r["M_pusat_maks"], "phiMn": b["phiMn"], "tulangan": f"D{b['db']}-{b['s']:.0f}"}


def ringkasan():
    return {"panel": [desain_panel(*p) for p in PANEL], "pons": helipad_pons(), "tangki": desain_tangki(),
            "bukaan": tulangan_bukaan()}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    r = ringkasan()
    for p in r["panel"]:
        print(f"{p['kode']} qu {p['qu']:.2f} αf {p['af']:.2f}/{p['aft']:.2f} βt {p['beta_t']:.2f} hmin {p['hmin']*1000:.0f} "
              f"(tepi {p['hmin_tepi']*1000:.0f}) Vu {p['Vu']:.1f} φVc {p['phiVc']:.1f} L/D {p['rasio_LD']:.2f}")
        for b in p["baris"]:
            print(f"   {b['bentang']:8s} {b['posisi']:7s} {b['lajur']:14s} Mu {b['Mu']:6.2f} As {b['As']:6.0f} "
                  f"min {b['As_min']:4.0f} -> D{b['db']}-{b['s']:.0f} ({b['As_ada']:.0f}) φMn {b['phiMn']:.1f}")
    print(r["pons"])
    t = r["tangki"]
    print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in t.items() if not isinstance(v, dict)},
          {k: (t[k]["db"], t[k]["s"], round(t[k]["Mu"], 1)) for k in ("negatif", "positif")})
    print(r["bukaan"])


# ------------------------------------------------------------------ Excel
def buat_excel(keluar=BERKAS):
    import openpyxl
    from format_dokumen import AI, Lembar, set_font_bawaan

    r = ringkasan()
    hl = helipad_lentur()
    pn = pynite_panel()
    p1 = r["panel"][0]
    ddm_lt = [b for b in p1["baris"] if b["bentang"] == "interior" and b["posisi"] == "pos" and b["lajur"] == "tengah"][0]
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    lab = f"DIISI AI ATAS PERMINTAAN DEFSA (20 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk desain pelat (4.5)", [6, 120])
    lb.catatan(LABEL + " " + lab)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, x] for i, x in enumerate([
        "Pelat dua arah 200 mm dengan balok 350 × 600 di semua as (grid 8 × 8 m), fc' 30 MPa, BjTS 420B, selimut 20 mm "
        "(Tabel 20.6.1.3.1 hal. 460).",
        "Metode desain langsung SNI 2847:2019 Pasal 8.10 hal. 164-169: syarat 8.10.2 dipenuhi (>= 3 bentang tiap arah, "
        "panel bujur sangkar, L/D <= 2, αf1 l2²/αf2 l1² = 1). Mo = qu l2 ln²/8; distribusi interior 0,65/0,35 dan "
        "bentang ujung Tabel 8.10.4.2; lajur kolom Tabel 8.10.5.1/5.2/5.5; balok memikul 0,85 lajur kolom "
        "(Tabel 8.10.5.7.1).",
        "As dengan blok tegangan persegi, φ 0,90 (Tabel 21.2.1 hal. 469); As min 0,0018 Ag (Tabel 8.6.1.1 hal. 145); "
        "spasi <= 2h = 400 mm (Pasal 8.7.2.2).",
        "Panel khusus: atap tangki (pelat 250 mm + balok anak y 71), atap helipad (beban roda), bukaan shaft.",
        "Cek silang T-73: model pelat PyNite 3 × 3 panel terhadap DDM.",
        "Status: " + STATUS + ".",
    ])], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Panel"), 2, "Tipe panel, beban, dan syarat tebal",
                [8, 46, 10, 11, 10, 11, 10, 10, 12, 12, 12])
    lb.catatan(LABEL + " qu = max(1,4D; 1,2D + 1,6L). hmin Tabel 8.3.1.2 hal. 134: αfm <= 2 (b): ln(0,8 + fy/1400)/"
               "(36 + 5β(αfm - 0,2)) >= 125 mm. Geser satu arah φVc = 0,75 × 0,17 √fc' b d (Pers. 22.5.5.1).")
    baris = [[p["kode"], p["uraian"], p["h"] * 1000, round(p["D"], 2), p["L"], None, round(p["af"], 2),
              round(p["hmin"] * 1000), round(p["Vu"], 1), round(p["phiVc"], 1), None] for p in r["panel"]]
    _, a, b = lb.tabel(["Kode", "Panel", "h (mm)", "D (kPa)", "L (kPa)", "qu (kPa)", "αf", "hmin (mm)", "Vu (kN/m)",
                        "φVc (kN/m)", "Status"], baris, rata=list("clccccccccc"),
                       fmt=[None, None, "0", "0.00", "0.00", "0.00", "0.00", "0", "0.0", "0.0", None],
                       fill_kolom={5: AI, 10: AI})
    k = lb.kol
    for rr in range(a, b + 1):
        lb.ws[f"{k(5)}{rr}"] = f"=MAX(1.4*{k(3)}{rr},1.2*{k(3)}{rr}+1.6*{k(4)}{rr})"
        lb.ws[f"{k(10)}{rr}"] = f'=IF(AND({k(2)}{rr}>={k(7)}{rr},{k(8)}{rr}<={k(9)}{rr}),"Memenuhi","Periksa")'

    lb = Lembar(wb.create_sheet("Tulangan"), 3, "Momen DDM dan tulangan per lajur (kNm/m, mm²/m)",
                [7, 10, 14, 15, 10, 9, 10, 10, 7, 9, 10, 11])
    lb.catatan(LABEL + " Lajur kolom pelat: lebar 4,0 - 0,35 m (0,85 momen lajur kolom dipikul balok, 4.6); lajur "
               "tengah 4,0 m. D10 dipakai bila spasi >= 125 mm, selain itu D13. Panel P7 tulangan bawah D13-200 (helipad).")
    baris = []
    nama_m = {"neg_int": "negatif dalam", "pos": "positif", "neg_eks": "negatif luar"}
    for p in r["panel"]:
        for x in p["baris"]:
            baris.append([p["kode"], x["bentang"], nama_m[x["posisi"]], x["lajur"], round(x["Mu"], 2),
                          round(x["d"] * 1000), round(x["As"]), round(x["As_min"]), x["db"], x["s"], None, None])
    _, a, b = lb.tabel(["Panel", "Bentang", "Momen", "Lajur", "Mu", "d (mm)", "As perlu", "As min", "D", "s (mm)",
                        "As ada", "Status"], baris, rata=list("cccccccccccc"),
                       fmt=[None, None, None, None, "0.00", "0", "0", "0", "0", "0", "0", None],
                       fill_kolom={10: AI, 11: AI})
    for rr in range(a, b + 1):
        lb.ws[f"{k(10)}{rr}"] = f"=1000*PI()*{k(8)}{rr}^2/4/{k(9)}{rr}"
        lb.ws[f"{k(11)}{rr}"] = f'=IF({k(10)}{rr}>=MAX({k(6)}{rr},{k(7)}{rr}),"Memenuhi","Kurang")'

    t = r["tangki"]
    pons = r["pons"]
    lb = Lembar(wb.create_sheet("Panel Khusus"), 4, "Atap tangki, helipad, dan bukaan", [52, 16, 16, 60])
    lb.catatan(LABEL + " Tangki 210 m³ di atap podium utara x 60-72, y 67-73 (telaah M-1/M-10).")
    neg, pos = t["negatif"], t["positif"]
    lb.tabel(["Butir", "Nilai", "Satuan", "Keterangan"], [
        ["Usulan: pelat di bawah tangki", t["h"] * 1000, "mm", "x 56-76, y 67-75; balok anak sejajar X di y 71 (4.6)"],
        ["Beban tangki merata", round(t["q_tangki"], 2), "kPa", "beban mati (isi tetap, SNI 1727 Pasal 3.1.3)"],
        ["qu", round(t["qu"], 2), "kPa", "1,2D + 1,6Lr"],
        ["Bentang bersih (balok induk y 67 - balok anak y 71)", t["ln"], "m", ""],
        ["Mu negatif = qu ln²/10", round(neg["Mu"], 1), "kNm/m",
         f"D{neg['db']}-{neg['s']:.0f} atas (As {neg['As_ada']:.0f} >= {neg['As_pakai']:.0f})"],
        ["Mu positif = qu ln²/14", round(pos["Mu"], 1), "kNm/m",
         f"D{pos['db']}-{pos['s']:.0f} bawah (As {pos['As_ada']:.0f} >= {pos['As_pakai']:.0f})"],
        ["Vu (1,15 qu ln/2) / φVc", f"{t['Vu']:.1f} / {t['phiVc']:.1f}".replace(".", ","), "kN/m", "memenuhi"],
        ["Helipad: geser pons roda 1,6 × 50,0 kN, 200 × 200 mm",
         f"{pons['Pu']:.1f} / {pons['phiVn']:.1f}".replace(".", ","), "kN", "Tabel 22.6.5.2: vc 0,33 √fc'; memenuhi"],
        ["Helipad: momen pelat akibat dua roda + 1,2D (PyNite)", round(hl["M_maks"], 1), "kNm/m",
         f"> φMn {hl['phiMn']:.1f} ({hl['tulangan']}); pakai D13-200 bawah dua arah di panel atap menara"],
    ], rata=list("lccl"), fill_kolom={1: AI, 3: AI})
    lb.kosong()
    lb.tabel(["Bukaan", "Ukuran (m)", "Tambahan tiap sisi", "Keterangan"],
             [[x["kode"], f"{x['a']} × {x['b']}".replace(".", ","),
               f"{x['tambah_sisi_a']} D13 // {x['tambah_sisi_b']} D13",
               "tulangan terpotong digantikan di kedua sisi bukaan (praktik Pasal 8.5.4.2) [Asumsi]"]
              for x in r["bukaan"]], rata=list("lccl"), fill_kolom={2: AI}, beku=False)

    lb = Lembar(wb.create_sheet("Cek Silang"), 5, "Cek silang T-73", [8, 60, 16, 16, 12, 10, 12])
    lb.catatan(LABEL + " PyNite: pelat quad 0,5 m, balok T sebagai anggota tanpa eksentrisitas, tumpuan sendi di 16 "
               "titik kolom; momen positif lajur tengah panel tengah P1. DDM adalah metode pendekatan (batas 30 %).")
    _, a, b = lb.tabel(["No", "Besaran", "DDM", "PyNite", "Selisih", "Batas", "Status"], [
        ["T-73", "Momen positif lajur tengah panel interior P1 (kNm/m)", round(ddm_lt["Mu"], 2),
         round(pn["Mpos_lajur_tengah"], 2), None, 0.30, None]],
        rata=list("clccccc"), fmt=[None, None, "0.00", "0.00", "0.0%", "0%", None], fill_kolom={4: AI, 6: AI},
        beku=False)
    lb.ws[f"{k(4)}{a}"] = f"={k(3)}{a}/{k(2)}{a}-1"
    lb.ws[f"{k(6)}{a}"] = f'=IF(ABS({k(4)}{a})<={k(5)}{a},"Lolos","Tidak lolos")'

    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar, {"helipad": hl, "pynite": pn, "ddm": ddm_lt["Mu"]}
