"""Tahap 6 langkah 6.5: tiang bor Ø800 menerima beban lateral (inersia gempa dan serakan lateral) dan kepala tiang.

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (22 Nov 2026); disetujui Defsa 22 Nov 2026
Defsa. Kunci jawaban tidak dibuka.

Metode: balok elemen hingga Euler-Bernoulli (800 simpul, 0,05 m) di atas pegas p-y nonlinier (Winkler), iterasi secant
(Picard), pegas dengan perpindahan tanah bebas: p = p_y(y_tiang - y_tanah). Kurva p-y mengikuti GEC9 / API:
- lempung lunak dan kaku: Matlock (1970) statik, pu = min(3 su + sigma'v + J su X/D ; 9 su) D, y50 = 2,5 eps50 D, J = 0,5;
- pasir: API RP 2GEO, p = A pu tanh(k X y / (A pu)), A = max(3 - 0,8 X/D ; 0,9);
- U5 terlikuifaksi: pengali p 0,1 / 0,3 pada kurva API, atau Matlock su = Sr.
Acuan di acuan/ (nomor halaman PDF): FHWA-HIF-18-031 (GEC9) bab 7 (p-y); SNI 2847:2019 Ps. 21.2.2 Tabel 21.2.2 (phi),
Ps. 22.2 (blok tegangan). Belum ada di acuan/: Matlock 1970, API RP 2GEO, Reese dan Matlock 1956/1960, Broms 1964,
Brandenberg dkk. 2007, Ashford dkk. 2011, Zhang dkk. 2004, Youd dkk. 2002.
"""
from __future__ import annotations

import json
import math
import os
import pickle
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

sys.path.insert(0, str(Path(__file__).parent))
import tahap3_pondasi as t3  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "06 Struktur Bawah dan Basement"
GAMBAR = KELUAR / "Gambar"
BERKAS = KELUAR / "6.5 Tiang Lateral.xlsx"
MD = KELUAR / "6.5 Tiang Lateral.md"
LEMBAR = KELUAR / "6.5 Lembar Isian Lateral.md"
VERIFIKASI = AKAR / "VERIFIKASI.md"
PNG_INERSIA = GAMBAR / "6.5 Profil Inersia.png"
PNG_KINEMATIK = GAMBAR / "6.5 Profil Kinematik.png"
CACHE = Path(tempfile.gettempdir()) / "tahap6_lateral_hasil.pkl"
PYD1 = Path(tempfile.gettempdir()) / "pydantic1"     # pydantic < 2 untuk openpile 0.3.3 (pydantic 2 tidak cocok)

LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
STATUS = "disetujui Defsa 22 Nov 2026"
LABEL_AI = f"DIISI AI ATAS PERMINTAAN DEFSA (22 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."

# ---- tiang
D = 0.8
KEPALA = 10.85
UJUNG = -27.60
PANJANG = KEPALA - UJUNG                    # 38,45 m
FC = 30.0                                   # MPa [Asumsi 6.2]
EC = 4700.0 * math.sqrt(FC)                 # MPa, SNI 2847:2019 Ps. 19.2.2.1 = 25.743
I_TIANG = math.pi * D ** 4 / 64             # m4
EI_BRUTO = EC * 1e3 * I_TIANG / 1e3         # MNm2 (EC MPa = 1e3 kPa; kPa m4 = kNm2 -> /1e3 = MNm2)
FAKTOR_EI = 0.5                             # [Asumsi: GEC9 bab 7; dicek M-phi di 6.7]
N_TIANG = 251                                  # 6.3 revisi 22 Nov 2026 (Cap C digabung ke Cap E, berat cap masuk): cap kolom 143 + cap inti 108; sebelumnya 244 lalu 230
V_ELF = {"X": 13164.5, "Y": 8967.1}         # kN, 5.6 T-95
H_TIANG = {k: v / N_TIANG for k, v in V_ELF.items()}   # kN per tiang [Asumsi: dibagi rata]
P_MAKS = 1560.0                             # kN, Cap E (6.3)
FRAKSI_INERSIA = 0.5                        # gabungan: kinematik penuh + 50 % inersia [Literatur: Caltrans / Ashford 2011]
# ---- tanah
GW = 9.81
J_MATLOCK = 0.5
EPS50 = {"U1": 0.02, "U2": 0.02, "U3": 0.02, "U4": 0.02, "U6": 0.005}   # [Asumsi: lempung lunak 0,02; kaku 0,005]
SU_GAMBUT = 10.0                            # kPa [Asumsi]
PHI = {"U5": 33.0, "U7": 38.0}
SU_U4 = (5.23, 1.09)                        # su = 5,23 + 1,09 z (z dari muka tanah asli)
SR_U5 = 14.8                                # kPa, kuat residu 6.4
KERAK = ("U1", "U2", "U3", "U4")
# ---- serakan lateral (6.4, Zhang 2004 di baris selatan): (elevasi m, perpindahan m); di atas +1,01 tetap 4,58
PROFIL_ZHANG = [(1.01, 4.58), (-2.00, 3.02), (-6.00, 1.20), (-9.18, 0.0)]
DH_ZHANG, DH_YOUD = 4.58, 0.19
# ---- tulangan usulan [Asumsi]
FY, ES_BAJA = 420.0, 200000.0
N_BAR, D_BAR, SELIMUT, D_SPIRAL = 16, 25.0, 75.0, 10.0
TOL = {"openpile": 5.0, "sebaran": 30.0, "excel": 0.5}   # persen; ditetapkan sebelum membandingkan

VARIAN_U5 = {"penuh": "U5 tidak terlikuifaksi (kuat penuh)", "m0.1": "U5 terlikuifaksi, pengali p 0,1 (dasar)",
             "m0.3": "U5 terlikuifaksi, pengali p 0,3", "sr": "U5 terlikuifaksi, Matlock su = Sr 14,8 kPa"}


def idn(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# ================================================================== tanah per simpul
def _su_lap(unit, su, X):
    if unit == "U4":
        return SU_U4[0] + SU_U4[1] * X
    if unit == "U3":
        return SU_GAMBUT
    return su


def tegangan(X, zona):
    """(sigma_v total, sigma'v efektif) kPa pada kedalaman X dari muka tanah asli (MAT t3.MAT)."""
    lap = t3.PROFIL[zona]["lapisan"]
    tot, atas = 0.0, 0.0
    for lp in lap:
        bawah = min(lp[1], X)
        if bawah > atas:
            tot += lp[2] * (bawah - atas)
        atas = lp[1]
        if atas >= X:
            break
    return tot, tot - GW * max(0.0, X - t3.MAT)


def mesh(n_el=800):
    """Simpul dari kepala (z = 0) ke ujung; elevasi menurun."""
    z = np.linspace(0.0, PANJANG, n_el + 1)
    return z, KEPALA - z


def parameter_tanah(zona, e, varian="m0.1", rankine=True):
    """Parameter kurva p-y tiap simpul (array). Tipe: 0 tanpa tanah, 1 lempung Matlock, 2 pasir API."""
    G = t3.PROFIL[zona]["elev"]
    n = len(e)
    tipe = np.zeros(n, int)
    P = {k: np.zeros(n) for k in ("su", "y50", "pu", "phi", "A", "k", "pmax", "mult", "X")}
    P["mult"][:] = 1.0
    for i, el in enumerate(e):
        X = G - el
        if X <= 0:
            continue
        unit, _, _, jenis, su, n60 = t3.lapisan_di(X, zona)
        tot, ef = tegangan(X, zona)
        P["X"][i] = X
        if unit in ("U1", "U2", "U3", "U4", "U6") or (unit == "U5" and varian == "sr"):
            s = SR_U5 if unit == "U5" else _su_lap(unit, su, X)
            eps = 0.02 if unit == "U5" else EPS50[unit]
            tipe[i] = 1
            pu = min(3 * s + ef + J_MATLOCK * s * X / D, 9 * s) * D
            if rankine and unit in KERAK:
                pu = min(pu, (tot + 2 * s) * D)     # pasif Rankine lempung (tegangan total) [Asumsi]
            P["su"][i], P["y50"][i], P["pu"][i] = s, 2.5 * eps * D, pu
        else:
            phi = PHI[unit]
            tipe[i] = 2
            r = math.pi / 180
            b, beta = 0.4, 45 + phi / 2
            c1 = (b * math.tan(phi * r) * math.sin(beta * r) / (math.tan((beta - phi) * r) * math.cos(phi / 2 * r))
                  + math.tan(beta * r) ** 2 * math.tan(phi / 2 * r) / math.tan((beta - phi) * r)
                  + b * math.tan(beta * r) * (math.tan(phi * r) * math.sin(beta * r) - math.tan(phi / 2 * r)))
            c2 = math.tan(beta * r) / math.tan((beta - phi) * r) - math.tan((45 - phi / 2) * r) ** 2
            c3 = (b * math.tan(phi * r) * math.tan(beta * r) ** 4
                  + math.tan((45 - phi / 2) * r) ** 2 * (math.tan(beta * r) ** 8 - 1))
            P["phi"][i] = phi
            P["A"][i] = max(0.9, 3 - 0.8 * X / D)
            P["k"][i] = max((0.1978 * phi ** 2 - 10.232 * phi + 136.82) * 1000, 5400)   # kN/m3 di bawah muka air
            P["pmax"][i] = min(c3 * ef * D, c1 * ef * X + c2 * ef * D)
            if unit == "U5" and varian in ("m0.1", "m0.3"):
                P["mult"][i] = 0.1 if varian == "m0.1" else 0.3
    return tipe, P


def p_of_y(tipe, P, y):
    """Reaksi tanah p (kN/m) untuk perpindahan relatif y (m) tiap simpul (vektor)."""
    a = np.abs(y)
    p = np.zeros_like(y)
    m1 = tipe == 1
    if m1.any():
        r = a[m1] / P["y50"][m1]
        p[m1] = np.where(r > 8, P["pu"][m1], 0.5 * P["pu"][m1] * np.cbrt(r))
    m2 = tipe == 2
    if m2.any():
        A, pm = P["A"][m2], np.maximum(P["pmax"][m2], 1e-9)
        p[m2] = A * pm * np.tanh(P["k"][m2] * P["X"][m2] * a[m2] / (A * pm))
    return np.sign(y) * p * P["mult"]


# ================================================================== penyelesai balok-di-atas-pegas
def u_tanah(e, skala=1.0, profil=PROFIL_ZHANG):
    """Perpindahan tanah bebas (m) pada elevasi e: linier antar titik, tetap di atas titik pertama, nol di bawah titik akhir."""
    el = [p[0] for p in profil][::-1]
    u = [p[1] for p in profil][::-1]
    return skala * np.interp(e, el, u, left=0.0, right=profil[0][1])


def solusi(zona="SELATAN", kepala="sendi", H=0.0, skala_tanah=0.0, varian="m0.1", rankine=True, faktor_ei=FAKTOR_EI,
           n_el=800, maks_iter=600, tol=1e-8, linier_nh=None):
    """Selesaikan tiang. H (kN) di kepala searah +y. kepala: 'sendi' (M = 0) atau 'jepit' (rotasi 0, translasi bebas).
    skala_tanah: pengali profil Zhang (1 = 4,58 m; DH_YOUD/DH_ZHANG = Youd). linier_nh: pegas linier k = nh X (kN/m3)."""
    z, e = mesh(n_el)
    n = n_el + 1
    L = PANJANG / n_el
    EI = faktor_ei * EC * 1e3 * I_TIANG            # kNm2
    tipe, P = parameter_tanah(zona, e, varian, rankine)
    ys = u_tanah(e, skala_tanah) * (tipe > 0)
    # matriks kekakuan balok (2 DOF per simpul: y, theta)
    c = EI / L ** 3
    ke = c * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L ** 2, -6 * L, 2 * L ** 2],
                       [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L ** 2, -6 * L, 4 * L ** 2]])
    I_, J_, V_ = [], [], []
    for k in range(n_el):
        d = [2 * k, 2 * k + 1, 2 * k + 2, 2 * k + 3]
        for a in range(4):
            for b in range(4):
                I_.append(d[a]); J_.append(d[b]); V_.append(ke[a, b])
    Kb = sp.csc_matrix((V_, (I_, J_)), shape=(2 * n, 2 * n))
    trib = np.full(n, L)
    trib[0] = trib[-1] = L / 2
    F = np.zeros(2 * n)
    F[0] = H
    bebas = np.ones(2 * n, bool)
    if kepala == "jepit":
        bebas[1] = False
    idx = np.where(bebas)[0]
    ks = np.zeros(n)
    y = np.zeros(n)
    if linier_nh is not None:
        ks = np.where(tipe > 0, linier_nh * P["X"], 0.0)       # kN/m2 (per panjang)
        it = 1
    else:
        ks = _kaku(tipe, P, np.full(n, 1e-3))
        it = 0
    for it in range(1, maks_iter + 1):
        diag = np.zeros(2 * n)
        diag[0::2] = ks * trib
        rhs = F.copy()
        rhs[0::2] += ks * trib * ys
        K = (Kb + sp.diags(diag)).tocsc()
        u = np.zeros(2 * n)
        u[idx] = spl.spsolve(K[idx][:, idx], rhs[idx])
        ynew = u[0::2]
        ks_pakai = ks.copy()
        if linier_nh is not None:
            y = ynew
            break
        sel = np.max(np.abs(ynew - y))
        y = ynew
        kn = _kaku(tipe, P, y - ys)
        ks = 0.5 * ks + 0.5 * kn
        if sel < max(tol, 1e-7 * float(np.max(np.abs(y)))):
            break
    th = u[1::2]
    # momen dan geser dari kelengkungan elemen: M = EI y'', V = -EI y''' (V kepala = H)
    yy, tt = y[:-1], th[:-1]
    y2, t2 = y[1:], th[1:]
    kur0 = (-6 / L ** 2) * yy + (-4 / L) * tt + (6 / L ** 2) * y2 + (-2 / L) * t2
    kur1 = (6 / L ** 2) * yy + (2 / L) * tt + (-6 / L ** 2) * y2 + (4 / L) * t2
    M = np.zeros(n)
    M[:-1] += EI * kur0
    M[1:] += EI * kur1
    M[1:-1] /= 2
    # tanda: M = EI y'' (kurvatur) searah z ke bawah
    Ve = EI * (12 / L ** 3 * (yy - y2) + 6 / L ** 2 * (tt + t2))
    V = np.zeros(n)
    V[:-1] += Ve
    V[1:] += Ve
    V[1:-1] /= 2
    V[0], V[-1] = Ve[0], Ve[-1]
    ks = ks_pakai                       # kekakuan yang dipakai pada penyelesaian terakhir (p = ks (y - ys) memenuhi keseimbangan)
    p = ks * (y - ys)
    return dict(z=z, e=e, y=y, th=th, M=M, V=V, p=p, ks=ks, iter=it, tipe=tipe, ys=ys, X=P["X"], EI=EI,
                pu=P["pu"], sel=float(np.max(np.abs(y - ys))))


def _kaku(tipe, P, yrel):
    a = np.maximum(np.abs(yrel), 1e-6)
    return np.abs(p_of_y(tipe, P, a)) / a


def ringkas(s):
    """Besaran kunci: y kepala, M maks dan elevasinya, V maks, M kepala."""
    i = int(np.argmax(np.abs(s["M"])))
    j = int(np.argmax(np.abs(s["V"])))
    return dict(y0=float(s["y"][0]), th0=float(s["th"][0]), mmaks=float(abs(s["M"][i])), e_mmaks=float(s["e"][i]),
                vmaks=float(abs(s["V"][j])), e_vmaks=float(s["e"][j]), mkepala=float(s["M"][0]),
                ymaks=float(np.max(np.abs(s["y"]))), iter=s["iter"])


# ================================================================== kapasitas lentur kasar
def kapasitas_lentur(P_u=P_MAKS, fc=FC, fy=FY):
    """phi Mn (kNm) lingkaran Ø800, n D25 melingkar, tegangan blok Whitney, kompatibilitas regangan.
    phi dari SNI 2847:2019 Tabel 21.2.2 (spiral: tekan 0,75; tarik 0,90; transisi linier). Desain penuh di 6.7."""
    r = D / 2
    rs = r - (SELIMUT + D_SPIRAL + D_BAR / 2) / 1000
    ang = [2 * math.pi * k / N_BAR for k in range(N_BAR)]
    ys = np.array([rs * math.cos(a) for a in ang])         # + ke sisi tekan
    As = math.pi * (D_BAR / 1000) ** 2 / 4
    beta1 = max(0.65, min(0.85, 0.85 - 0.05 * (fc - 28) / 7))
    eps_y = fy / ES_BAJA

    def pm(c):
        a = min(beta1 * c, D)
        tengah = r - a                                     # jarak pusat ke garis atas blok
        th = math.acos(max(-1.0, min(1.0, tengah / r)))
        luas = r ** 2 * (th - math.sin(th) * math.cos(th))
        yc = (2 / 3) * r * math.sin(th) ** 3 / (th - math.sin(th) * math.cos(th)) if th > 1e-9 else 0.0
        Cc = 0.85 * fc * 1e3 * luas
        mc = Cc * yc
        eps = 0.003 * (c - (r - ys)) / c                   # + tekan
        fs = np.clip(eps * ES_BAJA, -fy, fy) * 1e3
        Pn = Cc + float(np.sum(fs * As)) - 0.85 * fc * 1e3 * As * float(np.sum(((r - ys) < a)))
        Mn = mc + float(np.sum(fs * As * ys)) - 0.85 * fc * 1e3 * As * float(np.sum(ys[(r - ys) < a]))
        et = -float(np.min(eps))                           # regangan tarik terbesar
        phi = 0.75 + 0.15 * min(1.0, max(0.0, (et - eps_y) / 0.003))
        return Pn, Mn, et, phi

    lo, hi = 1e-3, 5.0
    for _ in range(100):
        mid = (lo + hi) / 2
        Pn, Mn, et, phi = pm(mid)
        if phi * Pn < P_u:
            lo = mid
        else:
            hi = mid
    Pn, Mn, et, phi = pm((lo + hi) / 2)
    return dict(phiMn=phi * Mn, Mn=Mn, phi=phi, c=(lo + hi) / 2, eps_t=et, Pn=Pn, As=N_BAR * As * 1e6,
                rho=N_BAR * As / (math.pi * r ** 2))


# ================================================================== pembanding
def pembanding_elastis(zona, H=H_TIANG["X"], faktor_ei=FAKTOR_EI):
    """Pembanding orde (b): defleksi di muka tanah pada pegas linier nh (Reese-Matlock 1956/1960) dan Broms (1964) Hu.
    nh dicocokkan dari kekakuan secant solusi p-y pada 0..4 T (regresi k = nh X melalui nol)."""
    s = solusi(zona, "sendi", H, varian="m0.1", faktor_ei=faktor_ei)
    EI = s["EI"]
    G = t3.PROFIL[zona]["elev"]
    e_beban = KEPALA - G                                   # panjang bebas di atas muka tanah
    nh = 5000.0
    for _ in range(30):
        T = (EI / nh) ** 0.2
        m = (s["X"] > 0) & (s["X"] <= 4 * T)
        sec = np.abs(s["p"][m]) / np.maximum(np.abs(s["y"][m]), 1e-9)
        w = s["y"][m] ** 2                                  # bobot y^2: kekakuan di tempat tiang bergerak
        nh_baru = float(np.sum(w * sec * s["X"][m]) / np.sum(w * s["X"][m] ** 2))
        if abs(nh_baru - nh) / nh < 1e-4:
            nh = nh_baru
            break
        nh = nh_baru
    T = (EI / nh) ** 0.2
    yg_rm = 2.435 * H * T ** 3 / EI + 1.623 * H * e_beban * T ** 2 / EI
    ig = int(np.argmin(np.abs(s["X"] - 0.0) + (s["X"] <= 0) * 1e3))   # simpul pertama di dalam tanah
    yg_py = float(np.interp(G, s["e"][::-1], s["y"][::-1]))
    # pembanding tambahan: modulus konstan (Hetenyi), tiang semi-tak-hingga, beban H dan M = H e di muka tanah
    kc = 20000.0
    for _ in range(50):
        be = (kc / (4 * EI)) ** 0.25
        m = (s["X"] > 0) & (s["X"] <= math.pi / be)
        sec = np.abs(s["p"][m]) / np.maximum(np.abs(s["y"][m]), 1e-9)
        w = s["y"][m] ** 2
        kb = float(np.sum(w * sec) / np.sum(w))
        if abs(kb - kc) / kc < 1e-5:
            kc = kb
            break
        kc = kb
    be = (kc / (4 * EI)) ** 0.25
    yg_het = 2 * H * be * (1 + be * e_beban) / kc
    # linier nh pada FE yang sama (cek bahwa selisih berasal dari kurva p-y, bukan dari FE)
    sl = solusi(zona, "sendi", H, linier_nh=nh, faktor_ei=faktor_ei)
    yg_fe_lin = float(np.interp(G, sl["e"][::-1], sl["y"][::-1]))
    # Broms lempung, kepala bebas tiang panjang: Hu dari My = phiMn, su rata-rata 0..8D tertimbang kerak
    su_rata = float(np.mean([_su_lap(t3.lapisan_di(x, zona)[0], t3.lapisan_di(x, zona)[4], x) for x in np.linspace(0.05, 8 * D, 40)]))
    My = kapasitas_lentur()["phiMn"]
    # My = Hu (e + 1,5 D + 0,5 f); f = Hu / (9 su D)  ->  0,5 Hu^2/(9 su D) + Hu (e + 1,5 D) - My = 0
    a_ = 0.5 / (9 * su_rata * D)
    b_ = e_beban + 1.5 * D
    hu = (-b_ + math.sqrt(b_ ** 2 + 4 * a_ * My)) / (2 * a_)
    return dict(kc=kc, yg_het=yg_het, sebaran_het=abs(yg_het - yg_py) / yg_py * 100, nh=nh, T=T, yg_rm=yg_rm, yg_py=yg_py, yg_fe_lin=yg_fe_lin, sebaran=abs(yg_rm - yg_py) / yg_py * 100,
                dfe=abs(yg_fe_lin - yg_rm) / yg_rm * 100, su_rata=su_rata, hu=hu, rasio_hu=H / hu, e_bebas=e_beban, H=H)


# ================================================================== openpile (subproses dengan pydantic 1)
def _pasang_pydantic1():
    """pydantic < 2, pandas < 2.3, numpy < 2.1, numba < 0.61 dan salinan openpile ditambal (numpy 2.5 menolak int(array 1 elemen)) di folder temp pydantic1."""
    if not (PYD1 / "pydantic").exists():
        subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--target", str(PYD1), "pydantic<2", "pandas<2.3", "numpy<2.1", "numba<0.61", "llvmlite<0.44"], check=True)
    if not (PYD1 / "openpile" / "construct.py").exists():
        import importlib.util
        asal = Path(importlib.util.find_spec("openpile").origin).parent
        shutil.copytree(asal, PYD1 / "openpile")
        f = PYD1 / "openpile" / "construct.py"
        f.write_text(f.read_text(encoding="utf-8").replace("int(np.where(check == True)[0])",
                                                           "int(np.where(check == True)[0][0])"), encoding="utf-8")
        # kurva Matlock openpile: 7 titik + titik acak (interpolasi linier meremehkan kekakuan): 60 titik geometrik rapat
        g = PYD1 / "openpile" / "utils" / "py_curves.py"
        lama = "ylist_in = [0.0, 0.1 * y50, 0.21 * y50, 1 * y50, 3 * y50, 8 * y50, 15 * y50, ymax]"
        pts = ", ".join(f"{x:.6g} * y50" for x in np.geomspace(0.002, 15.0, 58))
        baru = f"ylist_in = [0.0, {pts}, ymax]"
        isi = g.read_text(encoding="utf-8").replace(lama, baru)
        f.write_text(f.read_text(encoding="utf-8").replace("spring_dim = 15", "spring_dim = 60"), encoding="utf-8")
        # openpile 0.3.3: Pmax_deep = 9 Su X; GEC9 Pers. A-2 (PDF hal. 222): pu = 9 Su D
        g.write_text(isi.replace("Pmax_deep = 9 * Su * X", "Pmax_deep = 9 * Su * D"), encoding="utf-8")


def _openpile_jalankan(masuk):
    """Dipanggil di subproses: hitung dengan openpile, tulis JSON ke stdout."""
    import warnings
    warnings.filterwarnings("ignore")
    import pandas as pd
    _gi = pd.Series.__getitem__

    def _gi_posisi(self, k):   # openpile 0.3.3 memakai s[0] posisional; pandas baru menolaknya
        if isinstance(k, int) and k not in self.index:
            return self.iloc[k]
        return _gi(self, k)
    pd.Series.__getitem__ = _gi_posisi
    from openpile.analyses import simple_winkler_analysis
    from openpile.construct import Layer, Model, Pile, SoilProfile
    from openpile.soilmodels import API_clay, API_sand
    G = masuk["G"]
    lap = []
    atas = G
    for (unit, bawah, gam, su, n60, eps, tipe, mult) in masuk["lapisan"]:
        eb = G - bawah if G - bawah > UJUNG else UJUNG - 1.0
        if tipe == "clay":
            lm = API_clay(Su=su, eps50=eps, kind="static", J=J_MATLOCK, p_multiplier=mult)
        else:
            lm = API_sand(phi=su, kind="static", p_multiplier=mult)
        lap.append(Layer(name=unit, top=atas, bottom=eb, weight=gam, lateral_model=lm))
        atas = eb
        if eb < UJUNG:
            break
    sp_ = SoilProfile(name="p", top_elevation=G, water_line=G - masuk["mat"], layers=lap)
    pile = Pile(name="t", kind="Circular", material="Steel", top_elevation=KEPALA,
                pile_sections={"length": [PANJANG], "diameter": [D], "wall thickness": [D / 2]})
    pile.E = masuk["EI"] / I_TIANG                         # solid, EI setara
    mod = Model(name="m", pile=pile, soil=sp_, element_type="EulerBernoulli", coarseness=0.05,
                distributed_lateral=True, distributed_moment=False, base_shear=False, base_moment=False)
    mod.set_pointload(elevation=KEPALA, Py=masuk["H"])
    if masuk["kepala"] == "jepit":
        mod.set_support(elevation=KEPALA, Rz=True)
    r = simple_winkler_analysis(mod, max_iter=200)
    d, f = r.displacements, r.forces
    out = dict(e=list(map(float, d["Elevation [m]"])), y=list(map(float, d["Deflection [m]"])),
               ef=list(map(float, f["Elevation [m]"])), M=list(map(float, f["M [kNm]"])), V=list(map(float, f["V [kN]"])))
    print("@@" + json.dumps(out))


def openpile_inersia(zona, kepala, H, faktor_ei=FAKTOR_EI, varian="penuh"):
    """openpile: kurva yang sama (API clay/sand statik), tanpa Rankine; varian U5 'penuh' atau pengali. Mengembalikan dict atau None."""
    try:
        _pasang_pydantic1()
    except Exception:
        return None
    lapisan = []
    for unit, bawah, gam, jenis, su, n60 in t3.PROFIL[zona]["lapisan"]:
        if unit == "U5" and varian == "sr":
            lapisan.append((unit, bawah, gam, [SR_U5, SR_U5], None, 0.02, "clay", 1.0))
        elif unit in ("U5", "U7"):
            mult = {"m0.1": 0.1, "m0.3": 0.3}.get(varian, 1.0) if unit == "U5" else 1.0
            lapisan.append((unit, bawah, gam, PHI[unit], None, None, "sand", mult))
        else:
            atas_x = 0.0 if not lapisan else lapisan[-1][1]
            if unit == "U4":
                s = [SU_U4[0] + SU_U4[1] * atas_x, SU_U4[0] + SU_U4[1] * bawah]
            elif unit == "U3":
                s = [SU_GAMBUT, SU_GAMBUT]
            else:
                s = [su, su]
            lapisan.append((unit, bawah, gam, s, None, EPS50[unit], "clay", 1.0))
    masuk = dict(G=t3.PROFIL[zona]["elev"], lapisan=lapisan, mat=t3.MAT, EI=faktor_ei * EC * 1e3 * I_TIANG, H=H, kepala=kepala)
    env = dict(os.environ, PYTHONPATH=str(PYD1), PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--openpile", json.dumps(masuk)],
                       capture_output=True, text=True, env=env)
    for ln in r.stdout.splitlines():
        if ln.startswith("@@"):
            o = json.loads(ln[2:])
            return {k: np.array(v) for k, v in o.items()}
    return None


def cocok_openpile(zona="SELATAN", kepala="sendi", H=H_TIANG["X"], varian="penuh", rankine=False):
    """T-103(a): selisih y kepala dan M maks, solver sendiri vs openpile, kurva dan EI yang sama."""
    o = openpile_inersia(zona, kepala, H, varian=varian)
    if o is None:
        return None
    s = solusi(zona, kepala, H, varian=varian, rankine=rankine)
    ry, rm = ringkas(s), dict(y0=float(o["y"][np.argmax(o["e"])]), mmaks=float(np.max(np.abs(o["M"]))))
    # momen dan geser pada elevasi yang sama (interpolasi)
    oi = np.argsort(o["ef"])
    mo = np.interp(s["e"][::-1], o["ef"][oi], o["M"][oi])[::-1]
    return dict(y0_s=ry["y0"], y0_o=rm["y0"], m_s=ry["mmaks"], m_o=rm["mmaks"],
                dy=abs(ry["y0"] - rm["y0"]) / abs(rm["y0"]) * 100, dm=abs(ry["mmaks"] - rm["mmaks"]) / rm["mmaks"] * 100,
                dprofil=float(np.max(np.abs(np.abs(s["M"]) - np.abs(mo))) / rm["mmaks"] * 100), zona=zona, kepala=kepala,
                varian=varian)


# ================================================================== semua kasus
def kasus_daftar():
    """Daftar kasus: kode -> argumen solusi. Kasus utama (untuk lembar Profil) bertanda utama."""
    c = {}
    for kep in ("sendi", "jepit"):
        for arah in ("X", "Y"):
            for v in VARIAN_U5:
                c[f"I-S-{arah}-{v}-{kep}"] = dict(zona="SELATAN", kepala=kep, H=H_TIANG[arah], varian=v)
            c[f"I-S-{arah}-m0.1-{kep}-EIbruto"] = dict(zona="SELATAN", kepala=kep, H=H_TIANG[arah], varian="m0.1", faktor_ei=1.0)
            for v in ("penuh", "m0.1"):
                c[f"I-U-{arah}-{v}-{kep}"] = dict(zona="UTARA", kepala=kep, H=H_TIANG[arah], varian=v)
        for nama, sk in (("Youd", DH_YOUD / DH_ZHANG), ("Zhang", 1.0)):
            c[f"K-{nama}-m0.1-{kep}"] = dict(zona="SELATAN", kepala=kep, skala_tanah=sk, varian="m0.1")
            c[f"G-{nama}-m0.1-{kep}"] = dict(zona="SELATAN", kepala=kep, skala_tanah=sk, varian="m0.1", H=FRAKSI_INERSIA * H_TIANG["Y"])
        c[f"K-Zhang-m0.3-{kep}"] = dict(zona="SELATAN", kepala=kep, skala_tanah=1.0, varian="m0.3")
        c[f"K-Zhang-sr-{kep}"] = dict(zona="SELATAN", kepala=kep, skala_tanah=1.0, varian="sr")
        c[f"K-Zhang-m0.1-tanpaRankine-{kep}"] = dict(zona="SELATAN", kepala=kep, skala_tanah=1.0, varian="m0.1", rankine=False)
        c[f"K-Zhang-m0.1-EIbruto-{kep}"] = dict(zona="SELATAN", kepala=kep, skala_tanah=1.0, varian="m0.1", faktor_ei=1.0)
        c[f"G-Zhang-m0.1-X-{kep}"] = dict(zona="SELATAN", kepala=kep, skala_tanah=1.0, varian="m0.1", H=FRAKSI_INERSIA * H_TIANG["X"])
    return c


def skala_batas(kepala, phiMn, varian="m0.1", tertinggi=1.0):
    """Skala profil Zhang (kinematik saja) yang membuat Mmaks = phiMn (bisection). None bila Zhang penuh masih di bawah."""
    def mm(s):
        return ringkas(solusi("SELATAN", kepala, 0.0, skala_tanah=s, varian=varian))["mmaks"]
    if mm(tertinggi) <= phiMn:
        return None
    lo, hi = 0.0, tertinggi
    for _ in range(22):
        mid = (lo + hi) / 2
        if mm(mid) < phiMn:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def semua(pakai_cache=True):
    if pakai_cache and CACHE.exists() and os.environ.get("TAHAP6_LATERAL_CACHE") == "1":
        return pickle.loads(CACHE.read_bytes())
    h = dict(kap=kapasitas_lentur(), kasus={}, ringkas={})
    for k, a in kasus_daftar().items():
        s = solusi(**a)
        h["kasus"][k] = s
        h["ringkas"][k] = ringkas(s)
    kap = h["kap"]["phiMn"]
    h["batas"] = {kep: skala_batas(kep, kap) for kep in ("sendi", "jepit")}
    h["batas_dh"] = {kep: (None if v is None else v * DH_ZHANG) for kep, v in h["batas"].items()}
    h["pemb"] = pembanding_elastis("SELATAN")
    h["op"] = {kep: cocok_openpile("SELATAN", kep) for kep in ("sendi", "jepit")}
    h["op"]["utara"] = cocok_openpile("UTARA", "sendi")
    h["op"]["m0.1"] = cocok_openpile("SELATAN", "sendi", varian="m0.1")
    h["kasus"] = {k: {kk: vv for kk, vv in v.items() if kk in ("z", "e", "y", "M", "V", "p", "ys", "iter", "EI")}
                  for k, v in h["kasus"].items()}
    CACHE.write_bytes(pickle.dumps(h))
    return h

# ================================================================== gambar
def _batas_u5(zona="SELATAN"):
    G = t3.PROFIL[zona]["elev"]
    u = [lp for lp in t3.PROFIL[zona]["lapisan"] if lp[0] == "U5"]
    idx = t3.PROFIL[zona]["lapisan"].index(u[0])
    atas = t3.PROFIL[zona]["lapisan"][idx - 1][1]
    return G - atas, G - u[0][1]


def gambar(h):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    GAMBAR.mkdir(parents=True, exist_ok=True)
    G = t3.PROFIL["SELATAN"]["elev"]
    u5a, u5b = _batas_u5()
    kap = h["kap"]["phiMn"]

    def dasar(axs, judul_y):
        for a in axs:
            a.axhline(G, color="saddlebrown", lw=0.8, ls=":")
            a.axhspan(u5b, u5a, color="gold", alpha=0.18, lw=0)
            a.axhline(KEPALA, color="gray", lw=0.6, ls="--")
            a.axvline(0, color="k", lw=0.5)
            a.set_ylim(-28, 12)
            a.grid(alpha=0.3)
        axs[0].set_ylabel("Elevasi (m)")
        axs[0].set_xlabel(judul_y)
        axs[1].set_xlabel("Momen M (kNm)")
        axs[2].set_xlabel("Geser V (kN)")
        axs[0].text(0.02, G + 0.3, "muka tanah asli", transform=axs[0].get_yaxis_transform(), fontsize=7, color="saddlebrown")
        axs[0].text(0.02, u5b + 0.3, "U5 (pasir, likuifaksi)", transform=axs[0].get_yaxis_transform(), fontsize=7, color="goldenrod")

    # ---- gambar 1: inersia
    fig, ax = plt.subplots(1, 3, figsize=(11, 6.4), sharey=True)
    dasar(ax, "Perpindahan y (mm)")
    for kep, w in (("sendi", "tab:blue"), ("jepit", "tab:red")):
        s = h["kasus"][f"I-S-X-m0.1-{kep}"]
        ax[0].plot(s["y"] * 1000, s["e"], color=w, label=f"{kep}, U5 pengali 0,1")
        ax[1].plot(s["M"], s["e"], color=w)
        ax[2].plot(s["V"], s["e"], color=w)
        s2 = h["kasus"][f"I-S-X-penuh-{kep}"]
        ax[0].plot(s2["y"] * 1000, s2["e"], color=w, ls="--", lw=1, label=f"{kep}, U5 kuat penuh")
        ax[1].plot(s2["M"], s2["e"], color=w, ls="--", lw=1)
        ax[2].plot(s2["V"], s2["e"], color=w, ls="--", lw=1)
    ax[0].legend(fontsize=7, loc="lower right")
    fig.suptitle(f"6.5 Inersia gempa arah X, {idn(H_TIANG['X'], 2)} kN per tiang Ø800 (selatan, EI = 0,5 EI bruto)\nDATA SIMULASI, disetujui Defsa 22 Nov 2026",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(PNG_INERSIA, dpi=150)
    plt.close(fig)

    # ---- gambar 2: kinematik dan gabungan
    fig, ax = plt.subplots(1, 3, figsize=(11, 6.4), sharey=True)
    dasar(ax, "Perpindahan y (m)")
    sz = h["kasus"]["K-Zhang-m0.1-sendi"]
    ax[0].plot(sz["ys"], sz["e"], color="gray", lw=2.4, alpha=0.6, label="tanah bebas Zhang 4,58 m")
    for nama, kep, w, ls in (("K-Zhang", "sendi", "tab:blue", "-"), ("K-Zhang", "jepit", "tab:red", "-"),
                             ("K-Youd", "sendi", "tab:blue", "--"), ("K-Youd", "jepit", "tab:red", "--")):
        s = h["kasus"][f"{nama}-m0.1-{kep}"]
        lb = f"{'Zhang' if 'Zhang' in nama else 'Youd'} {kep}"
        ax[0].plot(s["y"], s["e"], color=w, ls=ls, label=lb)
        ax[1].plot(s["M"], s["e"], color=w, ls=ls)
        ax[2].plot(s["V"], s["e"], color=w, ls=ls)
    for a in (ax[1],):
        a.axvline(kap, color="green", lw=1.2, ls="-.")
        a.axvline(-kap, color="green", lw=1.2, ls="-.")
        a.text(kap, -26, " φMn", color="green", fontsize=8)
    ax[0].legend(fontsize=7, loc="lower right")
    fig.suptitle("6.5 Serakan lateral (kinematik saja): Zhang 4,58 m dan Youd 0,19 m, U5 pengali 0,1, tekanan kerak dibatasi Rankine\n"
                 "Teori balok kecil-lendutan: lendutan Zhang beberapa meter hanya indikasi tuntutan. DATA SIMULASI, disetujui Defsa 22 Nov 2026", fontsize=9)
    fig.tight_layout()
    fig.savefig(PNG_KINEMATIK, dpi=150)
    plt.close(fig)


# ================================================================== Excel
def _baris_inersia(h):
    r = h["ringkas"]
    out = []
    for z, kz in (("S", "Selatan"), ("U", "Utara")):
        for arah in ("X", "Y"):
            for v in (VARIAN_U5 if z == "S" else {"penuh": VARIAN_U5["penuh"], "m0.1": VARIAN_U5["m0.1"]}):
                a, b = r[f"I-{z}-{arah}-{v}-sendi"], r[f"I-{z}-{arah}-{v}-jepit"]
                out.append([kz, arah, idn(H_TIANG[arah], 2), VARIAN_U5[v], a["y0"] * 1000, a["mmaks"], a["e_mmaks"], a["vmaks"],
                            b["y0"] * 1000, b["mmaks"], abs(b["mkepala"]), b["vmaks"]])
        a, b = r[f"I-S-X-m0.1-sendi-EIbruto"], r[f"I-S-X-m0.1-jepit-EIbruto"]
        if z == "S":
            out.append([kz, "X", idn(H_TIANG["X"], 2), "U5 pengali 0,1, EI BRUTO (varian)", a["y0"] * 1000, a["mmaks"], a["e_mmaks"],
                        a["vmaks"], b["y0"] * 1000, b["mmaks"], abs(b["mkepala"]), b["vmaks"]])
    for ln in out:                       # H sebagai angka
        ln[2] = float(ln[2].replace(".", "").replace(",", "."))
    return out


def buat_excel(keluar=BERKAS, h=None):
    import openpyxl
    from format_dokumen import AI, Lembar, set_font_bawaan
    h = h or semua()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    ket = LABEL + " " + LABEL_AI
    adr = {}
    kap, pm, r = h["kap"], h["pemb"], h["ringkas"]
    kinematik = ("K-Youd-m0.1", "K-Zhang-m0.1", "K-Zhang-m0.3", "K-Zhang-sr", "K-Zhang-m0.1-tanpaRankine", "K-Zhang-m0.1-EIbruto")
    nama_kin = {"K-Youd-m0.1": "Youd 2002, 0,19 m (U5 pengali 0,1)", "K-Zhang-m0.1": "Zhang 2004, 4,58 m (U5 pengali 0,1, dasar)",
                "K-Zhang-m0.3": "Zhang 4,58 m, U5 pengali 0,3", "K-Zhang-sr": "Zhang 4,58 m, U5 Matlock su = Sr 14,8 kPa",
                "K-Zhang-m0.1-tanpaRankine": "Zhang 4,58 m, tanpa batas pasif Rankine kerak (kepekaan)",
                "K-Zhang-m0.1-EIbruto": "Zhang 4,58 m, EI bruto (kepekaan)"}

    # ---- 1 Petunjuk
    lp = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk dan daftar lembar", [26, 100])
    lp.catatan(f"STATUS: {STATUS}. " + ket)
    lp.kosong()
    lp.bagian("A", "Isi lembar")
    lp.tabel(["Lembar", "Isi"], [
        ["Data", "Tiang, EI, beban inersia per tiang, serakan Zhang, profil tanah dan kurva p-y (rumus Excel hidup: Ec, I, EI, H per tiang)"],
        ["Inersia", "Gaya inersia gempa X dan Y per tiang: y kepala, M maks, V maks, M kepala; kepala sendi dan jepit; varian U5"],
        ["Kinematik", "Serakan lateral Youd dan Zhang (tanpa inersia); kepala sendi dan jepit; kepekaan"],
        ["Gabungan", "Kinematik penuh + 50 % inersia; φMn tiang Ø800 (tulangan usulan) dan rasio M/φMn (rumus hidup); perpindahan tanah batas"],
        ["Profil", "z, elevasi, y, M, V per 0,25 m untuk delapan kasus utama (masukan 6.7)"],
        ["Pembanding", "T-103: openpile vs solver sendiri; Reese-Matlock, Hetenyi, Broms (rumus hidup)"],
        ["Kesimpulan", "Hasil, syarat lanjut, keputusan Defsa"]], rata=["l", "l"], beku=False)
    lp.kosong()
    lp.catatan("Sel hijau diisi AI dari skrip `tahap6_lateral.py` (balok elemen hingga 800 simpul di atas pegas p-y nonlinier). "
               "Rumus Excel hidup: Data, Gabungan (rasio), Pembanding. Hasil p-y tidak dihitung di Excel.")

    # ---- 2 Data
    ld = Lembar(wb.create_sheet("Data"), 2, "Data masukan", [46, 16, 78])
    ld.catatan(ket)
    ld.kosong()
    ld.bagian("A", "Tiang dan beban")
    rows = [
        ["Diameter tiang D (m)", D, "6.1, 6.3 (disetujui)"],
        ["f'c (MPa)", FC, "[Asumsi 6.2]"],
        ["Ec = 4700 akar(f'c) (MPa)", None, "SNI 2847:2019 Ps. 19.2.2.1 (rumus hidup)"],
        ["I = π D⁴ / 64 (m⁴)", None, "rumus hidup"],
        ["EI bruto = Ec I (MNm²)", None, "Ec MPa = MN/m²; rumus hidup"],
        ["Faktor EI retak", FAKTOR_EI, "[Asumsi: GEC9 bab 7 menyarankan EI retak; dicek M-φ di 6.7]"],
        ["EI dipakai (MNm²)", None, "rumus hidup"],
        ["V ELF arah X (kN)", V_ELF["X"], "5.6 T-95 (kasus E)"],
        ["V ELF arah Y (kN)", V_ELF["Y"], "5.6 T-95"],
        ["Jumlah tiang gedung utama", N_TIANG, "6.3 (revisi Cap C digabung ke Cap E dan berat cap masuk: cap kolom 143, cap inti 108; sebelumnya 244, lalu 230)"],
        ["H per tiang X (kN)", None, "V / N, dibagi rata [Asumsi, konservatif]; rumus hidup"],
        ["H per tiang Y (kN)", None, "rumus hidup"],
        ["Pmax tiang (kN)", P_MAKS, "Cap E (6.3); dipakai untuk φMn"],
        ["Fraksi inersia pada gabungan", FRAKSI_INERSIA, "kinematik penuh + 50 % inersia [Literatur: Ashford dkk. 2011 / Caltrans; belum ada di acuan/]"],
        ["Elevasi kepala tiang (m)", KEPALA, "6.0"],
        ["Elevasi ujung tiang (m)", UJUNG, "6.0"],
        ["Panjang tiang (m)", None, "rumus hidup"],
        ["Perpindahan tanah Zhang (m)", DH_ZHANG, "6.4 (keputusan Defsa 21 Nov 2026)"],
        ["Perpindahan tanah Youd (m)", DH_YOUD, "6.4; batas bawah"],
        ["Skala Youd = DH Youd / DH Zhang", None, "profil sama diskala; rumus hidup"],
        ["Muka tanah asli selatan / utara (m)", f"{t3.PROFIL['SELATAN']['elev']} / {t3.PROFIL['UTARA']['elev']}", "`tahap3_pondasi.PROFIL`"],
        ["Muka air tanah di bawah muka tanah asli (m)", t3.MAT, "`tahap3_pondasi.MAT` (2.3)"],
        ["Panjang bebas di atas muka tanah selatan (m)", round(KEPALA - t3.PROFIL["SELATAN"]["elev"], 2),
         "kepala +10,85 di atas muka tanah asli +9,95; urugan halaman sampai +12,05 tidak diberi tahanan [Asumsi, konservatif]"],
    ]
    r0, a, b = ld.tabel(["Besaran", "Nilai", "Sumber"], rows, rata=["l", "r", "l"], fill_kolom={1: AI}, beku=False)
    V = lambda i: f"{ld.kol(1)}{r0 + 1 + i}"
    ws = ld.ws
    ws[V(2)] = f"=4700*SQRT({V(1)})"
    ws[V(3)] = f"=PI()*{V(0)}^4/64"
    ws[V(4)] = f"={V(2)}*{V(3)}"
    ws[V(6)] = f"={V(5)}*{V(4)}"
    ws[V(10)] = f"={V(7)}/{V(9)}"
    ws[V(11)] = f"={V(8)}/{V(9)}"
    ws[V(16)] = f"={V(14)}-{V(15)}"
    ws[V(19)] = f"={V(18)}/{V(17)}"
    for i, f in ((2, "#,##0.0"), (3, "0.000000"), (4, "#,##0.00"), (6, "#,##0.00"), (10, "#,##0.00"), (11, "#,##0.00"),
                 (16, "0.00"), (19, "0.0000")):
        ws[V(i)].number_format = f
    adr.update(ec=f"'Data'!{V(2)}", i=f"'Data'!{V(3)}", ei=f"'Data'!{V(6)}", h_x=f"'Data'!{V(10)}", h_y=f"'Data'!{V(11)}",
               skala_youd=f"'Data'!{V(19)}", panjang=f"'Data'!{V(16)}")
    adr_ei, adr_hx, adr_hy = f"'Data'!{V(6)}", f"'Data'!{V(10)}", f"'Data'!{V(11)}"
    ld.kosong()
    ld.bagian("B", "Profil tanah dan kurva p-y (kedalaman dari muka tanah asli; elevasi atas, bawah lapisan)")
    baris = []
    for zona in ("SELATAN", "UTARA"):
        G = t3.PROFIL[zona]["elev"]
        atas = 0.0
        for unit, bawah, gam, jenis, su, n60 in t3.PROFIL[zona]["lapisan"]:
            if unit == "U4":
                par, kurva = "su = 5,23 + 1,09 z kPa", "Matlock lempung lunak, eps50 0,02; dibatasi Rankine"
            elif unit == "U3":
                par, kurva = f"su {SU_GAMBUT:.0f} kPa [Asumsi]", "Matlock, eps50 0,02; dibatasi Rankine"
            elif unit in ("U1", "U2"):
                par, kurva = f"su {su:.0f} kPa", "Matlock, eps50 0,02; dibatasi Rankine"
            elif unit == "U5":
                par, kurva = "φ' 33°, N60 12", "API pasir; terlikuifaksi: pengali p 0,1 / 0,3, atau Matlock su = Sr 14,8 kPa"
            elif unit == "U6":
                par, kurva = f"su {su:.0f} kPa", "Matlock, eps50 0,005"
            else:
                par, kurva = "φ' 38°, N60 30", "API pasir"
            baris.append([zona.title(), unit, round(G - atas, 2), round(G - min(bawah, t3.PROFIL[zona]["ujung"]), 2), gam, par, kurva])
            atas = bawah
            if bawah >= t3.PROFIL[zona]["ujung"]:
                break
    ld.tabel(["Lapisan", "γ (kN/m³)", "Elevasi atas-bawah (m); parameter; kurva p-y"],
             [[f"{x[0]} {x[1]}", x[4], f"{idn(x[2], 2)} s.d. {idn(x[3], 2)}; {x[5]}; {x[6]}"] for x in baris],
             rata=["l", "r", "l"], fmt=[None, "0.0", None], fill_kolom={1: AI, 2: AI}, beku=False)
    ld.kosong()
    ld.bagian("C", "Profil perpindahan tanah bebas (6.4, Zhang 2004, garis tiang selatan y 26,3 m)")
    ld.tabel(["Elevasi (m)", "u (m)", "Catatan"],
             [[p[0], p[1], "di atas elevasi ini tetap sama" if i == 0 else ("tanah bergerak nol di bawah" if i == len(PROFIL_ZHANG) - 1 else "interpolasi linier")]
              for i, p in enumerate(PROFIL_ZHANG)],
             rata=["r", "r", "l"], fmt=["0.00", "0.00", None], fill_kolom={0: AI, 1: AI}, beku=False)
    ld.kosong()
    ld.catatan("Tekanan kerak (U1-U4) dibatasi pasif Rankine lempung: (σv total + 2 su) D [Asumsi]; lihat kepekaan 'tanpa Rankine' di lembar Kinematik. "
               "Kurva statik (monotonik) dipakai untuk inersia dan serakan [Asumsi]. U5 terlikuifaksi: dasar pengali 0,1.")

    # ---- 3 Inersia
    li = Lembar(wb.create_sheet("Inersia"), 3, "Beban inersia gempa per tiang", [10, 7, 10, 38, 11, 11, 11, 10, 11, 11, 11, 10])
    li.catatan(ket)
    li.kosong()
    li.bagian("A", "Hasil per kasus (y kepala mm; M kNm; elevasi m; V kN). M kepala hanya pada kepala jepit")
    li.tabel(["Zona", "Arah", "H (kN)", "Model U5", "Sendi y0 (mm)", "Sendi M maks", "Elev. M maks", "Sendi V maks", "Jepit y0 (mm)",
              "Jepit M maks", "Jepit M kepala", "Jepit V maks"], _baris_inersia(h), rata=["l", "c"] + ["r"] * 10,
             fmt=[None, None, "0.00", None, "0.0", "0.0", "0.00", "0.0", "0.0", "0.0", "0.0", "0.0"], fill=AI, beku=False)
    li.kosong()
    li.catatan("Sendi: M kepala = 0, momen maksimum di dalam tanah. Jepit: rotasi kepala 0, translasi bebas, momen maksimum di kepala (cap kaku). "
               "Zona selatan dihitung penuh; utara untuk U5 kuat penuh dan U5 pengali 0,1.")

    # ---- 4 Kinematik
    lk = Lembar(wb.create_sheet("Kinematik"), 4, "Serakan lateral (kinematik saja)", [44, 10, 12, 11, 11, 10, 12, 11, 11, 11])
    lk.catatan(ket)
    lk.kosong()
    lk.bagian("A", "Hasil per kasus, zona selatan")
    baris = []
    for k in kinematik:
        a, b = r[f"{k}-sendi"], r[f"{k}-jepit"]
        baris.append([nama_kin[k], a["y0"], a["mmaks"], a["e_mmaks"], a["vmaks"], a["mmaks"] / kap["phiMn"], b["y0"], abs(b["mkepala"]),
                      b["mmaks"], b["vmaks"]])
    lk.tabel(["Kasus", "Sendi y0 (m)", "Sendi M maks (kNm)", "Elev. M maks", "Sendi V maks (kN)", "M/φMn sendi", "Jepit y0 (m)",
              "Jepit M kepala", "Jepit M maks", "Jepit V maks"], baris, rata=["l"] + ["r"] * 9,
             fmt=[None, "0.000", "#,##0", "0.00", "#,##0", "0.0", "0.000", "#,##0", "#,##0", "#,##0"], fill=AI, beku=False)
    lk.kosong()
    lk.catatan("Teori balok lendutan kecil dan pegas p-y: pada lendutan beberapa meter nilai hanya penanda tuntutan (tiang akan membentuk sendi plastis). "
               "Kasus Youd 0,19 m adalah batas bawah; Zhang 4,58 m batas atas (6.4).")

    # ---- 5 Gabungan
    lg = Lembar(wb.create_sheet("Gabungan"), 5, "Kinematik penuh + 50 % inersia dan kapasitas lentur", [44, 14, 14, 14, 14, 14])
    lg.catatan(ket)
    lg.kosong()
    lg.bagian("A", "Kapasitas lentur kasar tiang Ø800 (hanya untuk rasio; desain tulangan penuh di 6.7)")
    rk, _, _ = lg.tabel(["Besaran", "Nilai", "Sumber"], [
        ["Tulangan usulan", f"{N_BAR} D{int(D_BAR)}, spiral Ø{int(D_SPIRAL)}", "[Asumsi]"],
        ["As (mm²)", kap["As"], "16 × π 25² / 4"],
        ["ρ (%)", kap["rho"] * 100, "As / Ag"],
        ["fy (MPa)", FY, "[Asumsi]"],
        ["P (kN) pada φMn", P_MAKS, "Cap E (6.3)"],
        ["Regangan tarik terjauh εt", kap["eps_t"], "kompatibilitas regangan, blok tegangan Whitney"],
        ["φ", kap["phi"], "SNI 2847:2019 Ps. 21.2.2 Tabel 21.2.2, spiral (0,75 sampai 0,90)"],
        ["Mn (kNm)", kap["Mn"], "interaksi dihitung sendiri pada P / φ"],
        ["φMn (kNm)", kap["phiMn"], "rumus: φ × Mn (nilai dipakai untuk rasio)"]], rata=["l", "r", "l"], fill_kolom={1: AI}, beku=False)
    adr["phimn_cel"] = f"'Gabungan'!{lg.kol(1)}{rk + 9}"
    PHIMN = f"{lg.kol(1)}{rk + 9}"
    lg.ws[f"{lg.kol(1)}{rk + 9}"] = f"={lg.kol(1)}{rk + 8}*{lg.kol(1)}{rk + 7}"
    lg.ws[f"{lg.kol(1)}{rk + 9}"].number_format = "#,##0.0"
    for i, f in ((2, "#,##0"), (3, "0.00"), (6, "0.0000"), (7, "0.000"), (8, "#,##0.0")):
        lg.ws[f"{lg.kol(1)}{rk + i}"].number_format = f
    lg.kosong()
    lg.bagian("B", "Gabungan: kinematik penuh + 50 % inersia (arah Y, searah serakan ke sungai) dan kepekaan arah X")
    kg = [("G-Zhang-m0.1", "Zhang 4,58 m + 0,5 H Y"), ("G-Youd-m0.1", "Youd 0,19 m + 0,5 H Y"), ("G-Zhang-m0.1-X", "Zhang 4,58 m + 0,5 H X (kepekaan)")]
    baris = []
    for k, nm in kg:
        ks_s, ks_j = (k + "-sendi", k + "-jepit") if not k.endswith("-X") else (k[:-2] + "-X-sendi", k[:-2] + "-X-jepit")
        a, b = r[ks_s], r[ks_j]
        baris.append([nm, a["mmaks"], None, b["mmaks"], None, a["vmaks"]])
    rg, _, _ = lg.tabel(["Kasus", "Sendi M maks (kNm)", "Sendi M/φMn", "Jepit M maks (kNm)", "Jepit M/φMn", "Sendi V maks (kN)"], baris,
                        rata=["l"] + ["r"] * 5, fmt=[None, "#,##0", "0.00", "#,##0", "0.00", "#,##0"], fill_kolom={1: AI, 3: AI, 5: AI},
                        beku=False)
    for i in range(len(baris)):
        rr = rg + 1 + i
        lg.ws[f"{lg.kol(2)}{rr}"] = f"={lg.kol(1)}{rr}/${PHIMN[0]}${PHIMN[1:]}"
        lg.ws[f"{lg.kol(4)}{rr}"] = f"={lg.kol(3)}{rr}/${PHIMN[0]}${PHIMN[1:]}"
    adr["rasio_g_sendi"] = f"'Gabungan'!{lg.kol(2)}{rg + 1}"
    adr["rasio_g_jepit"] = f"'Gabungan'!{lg.kol(4)}{rg + 1}"
    lg.kosong()
    lg.bagian("C", "Perpindahan tanah bebas yang masih tertahan (kinematik saja, M maks = φMn)")
    bt = h["batas_dh"]
    lg.tabel(["Kepala", "Skala profil Zhang", "DH kerak batas (m)", "Terhadap Zhang 4,58 m", "Terhadap Youd 0,19 m"],
             [[kp, (h["batas"][kp] if h["batas"][kp] is not None else "> 1"), (bt[kp] if bt[kp] is not None else "> 4,58"),
               (f"{idn(bt[kp] / DH_ZHANG * 100, 1)} %" if bt[kp] is not None else "-"),
               (f"{idn(bt[kp] / DH_YOUD, 2)} kali" if bt[kp] is not None else "-")] for kp in ("sendi", "jepit")],
             rata=["l", "r", "r", "r", "r"], fmt=[None, "0.000", "0.000", None, None], fill=AI, beku=False)
    lg.kosong()
    lg.catatan("Rasio M/φMn > 1: tiang Ø800 tulangan usulan tidak menahan tuntutan; lihat Kesimpulan.")

    # ---- 6 Profil
    kolom_kasus = [("I-S-X-m0.1-sendi", "Inersia X sendi"), ("I-S-X-m0.1-jepit", "Inersia X jepit"), ("K-Youd-m0.1-sendi", "Youd sendi"),
                   ("K-Youd-m0.1-jepit", "Youd jepit"), ("K-Zhang-m0.1-sendi", "Zhang sendi"), ("K-Zhang-m0.1-jepit", "Zhang jepit"),
                   ("G-Zhang-m0.1-sendi", "Zhang+0,5 inersia sendi"), ("G-Zhang-m0.1-jepit", "Zhang+0,5 inersia jepit")]
    lf = Lembar(wb.create_sheet("Profil"), 6, "Profil per kedalaman (selatan)", [8, 9] + [10] * (3 * len(kolom_kasus)), zoom=80)
    lf.catatan(ket + " y dalam mm; M kNm; V kN; elevasi m. Untuk masukan 6.7.")
    lf.kosong()
    kepala = ["z (m)", "Elev. (m)"]
    for _, nm in kolom_kasus:
        kepala += [f"{nm}: y", f"{nm}: M", f"{nm}: V"]
    idx = np.round(np.arange(0.0, PANJANG + 1e-9, 0.25) / (PANJANG / 800)).astype(int)
    baris = []
    for i in idx:
        i = min(i, 800)
        row = [round(h["kasus"][kolom_kasus[0][0]]["z"][i], 2), round(h["kasus"][kolom_kasus[0][0]]["e"][i], 2)]
        for k, _ in kolom_kasus:
            s = h["kasus"][k]
            row += [s["y"][i] * 1000, s["M"][i], s["V"][i]]
        baris.append(row)
    lf.tabel(kepala, baris, rata=["r"] * len(kepala), fmt=["0.00", "0.00"] + ["#,##0.0", "#,##0.0", "#,##0.0"] * len(kolom_kasus),
             fill=AI, beku_kolom=2)

    # ---- 7 Pembanding
    lb = Lembar(wb.create_sheet("Pembanding"), 7, "Cek silang T-103", [50, 15, 15, 15, 60])
    lb.catatan(ket)
    lb.kosong()
    lb.bagian("A", "(a) openpile 0.3.3 vs solver sendiri, beban inersia X, kurva p-y dan EI yang sama (tanpa Rankine)")
    op = h["op"]
    baris = []
    for nm, o in (("Selatan, sendi, U5 kuat penuh", op["sendi"]), ("Selatan, jepit, U5 kuat penuh", op["jepit"]),
                  ("Utara, sendi, U5 kuat penuh", op["utara"]), ("Selatan, sendi, U5 pengali 0,1", op["m0.1"])):
        baris.append([nm, o["y0_o"] * 1000, o["y0_s"] * 1000, o["dy"], f"M maks openpile {idn(o['m_o'], 1)}, sendiri {idn(o['m_s'], 1)} kNm; "
                      f"selisih {idn(o['dm'], 2)} %; selisih profil M terbesar {idn(o['dprofil'], 2)} % M maks"])
    lb.tabel(["Kasus", "y kepala openpile (mm)", "y kepala sendiri (mm)", "Selisih y (%)", "Catatan"], baris, rata=["l", "r", "r", "r", "l"],
             fmt=[None, "0.00", "0.00", "0.00", None], fill=AI, beku=False)
    lb.kosong()
    lb.bagian("B", "(b) Pembanding orde: defleksi di muka tanah selatan, sendi, H X (rumus hidup di sel kuning)")
    rp, _, _ = lb.tabel(["Besaran", "Nilai", "Satuan", "", "Sumber"], [
        ["H (kN)", None, "kN", "", "Data"],
        ["EI dipakai (kNm²)", None, "kNm²", "", "Data"],
        ["Panjang bebas e (m)", pm["e_bebas"], "m", "", "kepala +10,85 - muka tanah +9,95"],
        ["nh ekuivalen (kN/m³)", pm["nh"], "kN/m³", "", "kekakuan secant p-y 0..4T, regresi berbobot y², k = nh X"],
        ["T = (EI / nh)^0,2 (m)", None, "m", "", "Reese dan Matlock 1956 (belum ada di acuan/)"],
        ["y muka tanah Reese-Matlock (mm)", None, "mm", "", "2,435 H T³/EI + 1,623 H e T²/EI"],
        ["k modulus konstan (kN/m²)", pm["kc"], "kN/m²", "", "kekakuan secant berbobot y² pada 0..π/β"],
        ["β = (k / 4EI)^0,25 (1/m)", None, "1/m", "", "Hetenyi"],
        ["y muka tanah Hetenyi (mm)", None, "mm", "", "2 H β (1 + β e) / k"],
        ["y muka tanah p-y solver sendiri (mm)", pm["yg_py"] * 1000, "mm", "", "balok-di-atas-pegas p-y"],
        ["su rata-rata 0..8D (kPa)", pm["su_rata"], "kPa", "", "kerak U1-U4"],
        ["My = φMn (kNm)", None, "kNm", "", "Gabungan"],
        ["Hu Broms kepala bebas tiang panjang (kN)", None, "kN", "", "My = Hu (e + 1,5 D + 0,5 f), f = Hu / 9 su D; Broms 1964 (GEC9 hal. PDF 83: tidak andal, hanya orde)"],
        ["H / Hu", None, "-", "", "rasio beban kerja terhadap batas"]], rata=["l", "r", "l", "l", "l"],
        fill_kolom={1: AI}, beku=False)
    Vb = lambda i: f"{lb.kol(1)}{rp + 1 + i}"
    w = lb.ws
    w[Vb(0)] = f"={adr_hx}"
    w[Vb(1)] = f"={adr_ei}*1000"
    w[Vb(4)] = f"=({Vb(1)}/{Vb(3)})^0.2"
    w[Vb(5)] = f"=(2.435*{Vb(0)}*{Vb(4)}^3/{Vb(1)}+1.623*{Vb(0)}*{Vb(2)}*{Vb(4)}^2/{Vb(1)})*1000"
    w[Vb(7)] = f"=({Vb(6)}/(4*{Vb(1)}))^0.25"
    w[Vb(8)] = f"=2*{Vb(0)}*{Vb(7)}*(1+{Vb(7)}*{Vb(2)})/{Vb(6)}*1000"
    w[Vb(11)] = f"='Gabungan'!{PHIMN}"
    w[Vb(12)] = (f"=(-({Vb(2)}+1.5*{D})+SQRT(({Vb(2)}+1.5*{D})^2+4*(0.5/(9*{Vb(10)}*{D}))*{Vb(11)}))/(2*(0.5/(9*{Vb(10)}*{D})))")
    w[Vb(13)] = f"={Vb(0)}/{Vb(12)}"
    for i, f in ((0, "0.00"), (1, "#,##0"), (2, "0.00"), (3, "#,##0"), (4, "0.000"), (5, "0.00"), (6, "#,##0"), (7, "0.0000"), (8, "0.00"),
                 (9, "0.00"), (10, "0.0"), (11, "#,##0.0"), (12, "#,##0.0"), (13, "0.000")):
        w[Vb(i)].number_format = f
    adr.update(yg_rm=f"'Pembanding'!{Vb(5)}", yg_het=f"'Pembanding'!{Vb(8)}", hu=f"'Pembanding'!{Vb(12)}", t_rm=f"'Pembanding'!{Vb(4)}")
    lb.kosong()
    lb.tabel(["Sebaran y muka tanah", "Nilai (%)", "", "", "Batas"], [
        ["Reese-Matlock vs p-y sendiri", pm["sebaran"], "", "", f"<= {TOL['sebaran']:.0f} % (dicatat)"],
        ["Hetenyi vs p-y sendiri", pm["sebaran_het"], "", "", f"<= {TOL['sebaran']:.0f} % (dicatat)"],
        ["FE sendiri (pegas linier nh) vs rumus Reese-Matlock", pm["dfe"], "", "", "<= 2 % (cek bahwa FE benar)"]],
        rata=["l", "r", "r", "r", "l"], fmt=[None, "0.00", None, None, None], fill_kolom={1: AI}, beku=False)
    lb.kosong()
    lb.catatan("(c) Excel = Python: sel rumus hidup (Data: Ec, I, EI, H per tiang, skala Youd, panjang; Gabungan: φMn dan rasio; Pembanding: T, y, Hu) "
               "dihitung ulang di Excel lalu dibandingkan dengan Python (selisih tertulis di VERIFIKASI.md T-103).")

    # ---- 8 Kesimpulan
    lc = Lembar(wb.create_sheet("Kesimpulan"), 8, "Kesimpulan", [150])
    lc.catatan(ket)
    lc.kosong()
    lc.bagian("A", "Hasil")
    lc.tabel(["Butir"], [[x] for x in kesimpulan_butir(h)], rata=["l"], beku=False)
    lc.kosong()
    lc.bagian("B", "Keputusan Defsa")
    lc.tabel(["Butir"], [[x] for x in keputusan_butir(h)], rata=["l"], beku=False)

    Path(keluar).parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar, adr


def kesimpulan_butir(h):
    r, kap = h["ringkas"], h["kap"]
    a, b = r["I-S-X-m0.1-sendi"], r["I-S-X-m0.1-jepit"]
    z, j = r["K-Zhang-m0.1-sendi"], r["K-Zhang-m0.1-jepit"]
    y_, yj = r["K-Youd-m0.1-sendi"], r["K-Youd-m0.1-jepit"]
    g, gj = r["G-Zhang-m0.1-sendi"], r["G-Zhang-m0.1-jepit"]
    gy, gyj = r["G-Youd-m0.1-sendi"], r["G-Youd-m0.1-jepit"]
    bt = h["batas_dh"]
    return [
        f"Inersia saja (X, {idn(H_TIANG['X'], 2)} kN per tiang, selatan, EI 0,5 EI bruto, U5 pengali 0,1): sendi y kepala {idn(a['y0'] * 1000, 1)} mm, "
        f"M maks {idn(a['mmaks'], 1)} kNm di elevasi {idn(a['e_mmaks'], 2)} m; jepit y kepala {idn(b['y0'] * 1000, 1)} mm, M kepala {idn(abs(b['mkepala']), 1)} kNm. "
        f"Keduanya jauh di bawah φMn {idn(kap['phiMn'], 0)} kNm (rasio {idn(max(a['mmaks'], abs(b['mkepala'])) / kap['phiMn'], 2)}): inersia saja tidak menentukan.",
        f"Kinematik Youd 0,19 m: sendi M maks {idn(y_['mmaks'], 0)} kNm (rasio {idn(y_['mmaks'] / kap['phiMn'], 2)}), V maks {idn(y_['vmaks'], 0)} kN; "
        f"jepit M maks {idn(yj['mmaks'], 0)} kNm (rasio {idn(yj['mmaks'] / kap['phiMn'], 2)}), V maks {idn(yj['vmaks'], 0)} kN.",
        f"Kinematik Zhang 4,58 m: sendi M maks {idn(z['mmaks'], 0)} kNm (rasio {idn(z['mmaks'] / kap['phiMn'], 1)}), V maks {idn(z['vmaks'], 0)} kN; "
        f"jepit M maks {idn(j['mmaks'], 0)} kNm (rasio {idn(j['mmaks'] / kap['phiMn'], 1)}), V maks {idn(j['vmaks'], 0)} kN.",
        f"Gabungan Zhang + 50 % inersia Y: sendi {idn(g['mmaks'], 0)} kNm (rasio {idn(g['mmaks'] / kap['phiMn'], 1)}), jepit {idn(gj['mmaks'], 0)} kNm "
        f"(rasio {idn(gj['mmaks'] / kap['phiMn'], 1)}); Youd + 50 % inersia: sendi {idn(gy['mmaks'], 0)} kNm (rasio {idn(gy['mmaks'] / kap['phiMn'], 2)}), "
        f"jepit {idn(gyj['mmaks'], 0)} kNm (rasio {idn(gyj['mmaks'] / kap['phiMn'], 2)}).",
        ("Perpindahan tanah batas yang masih tertahan (kinematik saja, M = φMn): sendi "
         + (f"{idn(bt['sendi'], 2)} m" if bt["sendi"] is not None else "> 4,58 m") + ", jepit "
         + (f"{idn(bt['jepit'], 2)} m" if bt["jepit"] is not None else "> 4,58 m")
         + f" (Youd 0,19 m: {'di bawah' if (bt['sendi'] or 9) > DH_YOUD and (bt['jepit'] or 9) > DH_YOUD else 'di atas'} batas)."),
        ("Tiang Ø800 dengan 16D25 tidak dapat menahan serakan Zhang 4,58 m (rasio jauh di atas 1, lendutan beberapa meter): perbaikan tanah U5 di jalur "
         "tebing atau tiang batas lahan Ø600 (6.4) menjadi syarat; di luar itu desain tiang gedung utama harus mengecualikan beban kinematik Zhang."
         if z["mmaks"] > kap["phiMn"] else "Tiang Ø800 menahan serakan Zhang pada tulangan usulan."),
    ]


def keputusan_butir(h):
    return [
        "1. Keputusan Defsa 22 Nov 2026: draf 6.5 disetujui; U5 terlikuifaksi memakai pengali p 0,1 (varian 0,3 dan Matlock Sr tetap tercatat sebagai kepekaan).",
        "2. Keputusan Defsa 22 Nov 2026: kepala tiang SENDI; sloof 5.4 (didesain dengan kepala sendi) tidak dicek ulang (B-4 tutup). Momen dan geser per kedalaman kasus sendi dipakai di 6.7.",
        "3. Masih terbuka (dibawa ke perkuatan tebing / 6.7): tuntutan Zhang tidak tertahan tiang Ø800 (batas 0,22 m); perbaikan tanah U5 di jalur tebing atau tiang batas lahan Ø600 (6.4) menjadi syarat; Youd 0,19 m (rasio 0,86) kasus kinematik desain setelah perkuatan.",
        "4. Pembagian inersia rata ke 251 tiang [Asumsi]; bila dinding basement dan pelat ikut menahan, H per tiang turun.",
        "5. Tekanan kerak dibatasi pasif Rankine [Asumsi]: tanpa batas, tuntutan naik (lembar Kinematik, kepekaan).",
    ]


# ================================================================== verifikasi T-103
def t103(berkas=BERKAS, adr=None, h=None):
    h = h or semua()
    op = [h["op"][k] for k in ("sendi", "jepit", "utara", "m0.1")]
    dop = max(max(o["dy"], o["dm"]) for o in op)
    dy_maks = max(o["dy"] for o in op)
    dm_maks = max(o["dm"] for o in op)
    pm = h["pemb"]
    seb = max(pm["sebaran"], pm["sebaran_het"])
    r = dict(dop=dop, dy=dy_maks, dm=dm_maks, seb=seb, seb_rm=pm["sebaran"], seb_het=pm["sebaran_het"], dfe=pm["dfe"], dxl=None,
             rasio_hu=pm["rasio_hu"])
    if adr:
        import openpyxl
        wb = openpyxl.load_workbook(berkas, data_only=True)

        def baca(a):
            sh, cel = a.split("!")
            return wb[sh.strip("'")][cel].value
        e_b = pm["e_bebas"]
        T = (FAKTOR_EI * EC * I_TIANG * 1e3 / pm["nh"]) ** 0.2
        EIk = FAKTOR_EI * EC * I_TIANG * 1e3
        Hx = H_TIANG["X"]
        be = (pm["kc"] / (4 * EIk)) ** 0.25
        py = {"ec": EC, "i": I_TIANG, "ei": FAKTOR_EI * EC * I_TIANG, "h_x": Hx, "h_y": H_TIANG["Y"], "skala_youd": DH_YOUD / DH_ZHANG,
              "panjang": PANJANG, "t_rm": T,
              "yg_rm": (2.435 * Hx * T ** 3 / EIk + 1.623 * Hx * e_b * T ** 2 / EIk) * 1000,
              "yg_het": 2 * Hx * be * (1 + be * e_b) / pm["kc"] * 1000,
              "phimn_cel": h["kap"]["phi"] * h["kap"]["Mn"],
              "rasio_g_sendi": h["ringkas"]["G-Zhang-m0.1-sendi"]["mmaks"] / (h["kap"]["phi"] * h["kap"]["Mn"]),
              "rasio_g_jepit": h["ringkas"]["G-Zhang-m0.1-jepit"]["mmaks"] / (h["kap"]["phi"] * h["kap"]["Mn"])}
        a_ = 0.5 / (9 * pm["su_rata"] * D)
        b_ = e_b + 1.5 * D
        py["hu"] = (-b_ + math.sqrt(b_ ** 2 + 4 * a_ * py["phimn_cel"])) / (2 * a_)
        try:
            ds = [abs(float(baca(adr[k])) - py[k]) / abs(py[k]) * 100 for k in py]
            r["dxl"] = max(ds)
        except (TypeError, ValueError, KeyError):
            r["dxl"] = None
    r["lolos"] = (dop <= TOL["openpile"] and seb <= TOL["sebaran"] and r["dxl"] is not None and r["dxl"] <= TOL["excel"])
    return r


def catat_t103(r=None, h=None, berkas=VERIFIKASI):
    h = h or semua()
    r = r or t103(h=h)
    pm = h["pemb"]
    dxl = idn(r["dxl"], 4) if r["dxl"] is not None else "tidak dihitung"
    baris = ("| T-103 | Cek silang 6.5 tiang lateral Ø800: y kepala dan M maks inersia (selatan sendi dan jepit, utara sendi, U5 pengali 0,1), "
             "pembanding orde y muka tanah, Excel = Python | (a) solver sendiri (balok elemen hingga 800 simpul + pegas p-y secant) vs openpile 0.3.3 "
             f"(kurva API clay/sand statik dan EI sama, 4 kasus inersia X): selisih y kepala terbesar {idn(r['dy'], 2)} %, M maks terbesar {idn(r['dm'], 2)} % | "
             f"(b) y muka tanah, p-y sendiri {idn(pm['yg_py'] * 1000, 2)} mm; Reese-Matlock {idn(pm['yg_rm'] * 1000, 2)} mm (sebaran {idn(r['seb_rm'], 1)} %), "
             f"Hetenyi {idn(pm['yg_het'] * 1000, 2)} mm (sebaran {idn(r['seb_het'], 1)} %); FE linier nh vs rumus {idn(r['dfe'], 2)} %; Broms H/Hu {idn(pm['rasio_hu'], 2)} "
             f"| (c) rumus Excel hidup (Data, Gabungan, Pembanding) vs Python, selisih terbesar {dxl} % "
             "| (a) <= 5 %; (b) sebaran <= 30 % (dicatat); (c) <= 0,5 % | "
             f"{'Lolos' if r['lolos'] else 'GAGAL'}, {STATUS} | `skrip/tahap6_lateral.py`, `tests/test_tahap6_lateral.py` | Ditetapkan sebelum membandingkan. "
             "Data simulasi. openpile 0.3.3 hanya jalan dengan pydantic < 2, pandas < 2.3, numpy < 2.1 (folder temp terpisah) dan tiga tambalan "
             "(int(array), kurva Matlock 15 titik rapat). openpile memakai pu dalam 9 su X (bukan 9 su D, GEC9 Pers. A-2); beda diabaikan karena beban inersia kecil. "
             "Kasus kinematik tidak dapat dibandingkan dengan openpile (tanpa perpindahan tanah bebas). |")
    teks = Path(berkas).read_text(encoding="utf-8").split("\n")
    teks = [ln for ln in teks if not ln.startswith("| T-103 |")]
    i = next(k for k, ln in enumerate(teks) if ln.startswith("| T-102 |"))
    teks.insert(i + 1, baris)
    Path(berkas).write_text("\n".join(teks), encoding="utf-8")
    return baris


# ================================================================== Markdown
def tulis_md(h=None, r=None, keluar=MD):
    h = h or semua()
    r = r or t103(h=h)
    rs, kap, pm = h["ringkas"], h["kap"], h["pemb"]
    bt = h["batas_dh"]

    def t(k):
        return rs[k]

    L = [f"# 6.5 Tiang lateral Ø800 dan kepala tiang\n",
         f"{LABEL} Disusun AI atas permintaan Defsa (22 Nov 2026). STATUS: {STATUS}. Kunci jawaban tidak dibuka. "
         "Hasil hitung AI; lembar isian Defsa di `6.5 Lembar Isian Lateral.md`. Berkas: `6.5 Tiang Lateral.xlsx`, skrip `skrip/tahap6_lateral.py`.\n",
         "## 1. Metode dan data\n",
         f"- Tiang Ø800, panjang {idn(PANJANG, 2)} m (kepala +10,85, ujung -27,60), f'c 30 MPa [Asumsi 6.2], Ec {idn(EC, 0)} MPa "
         f"(SNI 2847:2019 Ps. 19.2.2.1), I {idn(I_TIANG, 6)} m⁴, EI bruto {idn(EI_BRUTO, 1)} MNm², EI dipakai 0,5 EI bruto = {idn(FAKTOR_EI * EI_BRUTO, 1)} MNm² "
         "[Asumsi: GEC9 bab 7; dicek M-φ di 6.7] dengan varian EI bruto.",
         "- Solver: balok Euler-Bernoulli elemen hingga 800 elemen (0,05 m) di atas pegas p-y nonlinier, iterasi secant dengan relaksasi, "
         "pegas mengikuti perpindahan tanah bebas: p = p(y tiang - y tanah). Divalidasi dengan openpile 0.3.3 (T-103 a).",
         "- Kurva p-y (GEC9 Lampiran A, PDF hal. 222 Pers. A-1 dan A-2, Matlock; pasir API RP 2GEO [belum ada di acuan/]): U1-U4 dan U3 gambut (su 10 kPa [Asumsi]) "
         "Matlock lunak eps50 0,02, U4 su = 5,23 + 1,09 z; U5 API pasir φ' 33°; U6 Matlock su 85 kPa eps50 0,005; U7 API pasir φ' 38°. Kurva statik [Asumsi]. "
         "Tekanan kerak U1-U4 dibatasi pasif Rankine lempung (σv total + 2 su) D [Asumsi].",
         "- U5 terlikuifaksi: pengali p 0,1 (dasar) dan 0,3 [Literatur: Brandenberg dkk. 2007; Ashford dkk. 2011, belum ada di acuan/; GEC9 PDF hal. 124 membahas "
         "likuifaksi dan p-multiplier, belum dibaca rinci]; varian Matlock su = Sr 14,8 kPa (6.4).",
         f"- Beban inersia (5.6 kasus E): X {idn(V_ELF['X'], 1)} kN → {idn(H_TIANG['X'], 2)} kN per tiang; Y {idn(V_ELF['Y'], 1)} kN → {idn(H_TIANG['Y'], 2)} kN "
         "(dibagi rata 251 tiang [Asumsi, konservatif]). P-Δ dengan Pmax 1.560 kN tidak dimasukkan (hanya φMn pada P itu).",
         "- Kinematik (6.4, keputusan Defsa 21 Nov 2026): profil Zhang 4,58 m dari +1,01 ke atas, 3,02 m di -2,00, 1,20 m di -6,00, 0 dari -9,18 ke bawah; "
         "Youd 0,19 m = profil sama diskala 0,19/4,58. Gabungan: kinematik penuh + 50 % inersia (arah Y; kepekaan X) [Literatur: Ashford dkk. 2011 / Caltrans, belum ada di acuan/].",
         "- Elevasi muka tanah asli selatan +9,95, utara +9,23 (`tahap3_pondasi`), muka air 0,7 m di bawahnya. Kepala tiang +10,85 berada 0,90 m di atas muka tanah selatan; "
         "urugan sampai +12,05 tidak diberi tahanan [Asumsi, konservatif]. Zona dihitung: selatan (penentu, baris y 26,3 m) dan utara (inersia).\n",
         "## 2. Hasil inersia saja (selatan, X, EI 0,5 EI bruto)\n",
         "| Model U5 | Sendi y0 (mm) | Sendi M maks (kNm) di elev. | Jepit y0 (mm) | Jepit M kepala (kNm) | V (kN) |",
         "|---|---|---|---|---|---|"]
    for v in VARIAN_U5:
        a, b = t(f"I-S-X-{v}-sendi"), t(f"I-S-X-{v}-jepit")
        L.append(f"| {VARIAN_U5[v]} | {idn(a['y0'] * 1000, 1)} | {idn(a['mmaks'], 1)} (+{idn(a['e_mmaks'], 2)}) | {idn(b['y0'] * 1000, 1)} | "
                 f"{idn(abs(b['mkepala']), 1)} | {idn(a['vmaks'], 1)} |")
    a, b = t("I-S-X-m0.1-sendi-EIbruto"), t("I-S-X-m0.1-jepit-EIbruto")
    L.append(f"| EI bruto, U5 pengali 0,1 | {idn(a['y0'] * 1000, 1)} | {idn(a['mmaks'], 1)} (+{idn(a['e_mmaks'], 2)}) | {idn(b['y0'] * 1000, 1)} | "
             f"{idn(abs(b['mkepala']), 1)} | {idn(a['vmaks'], 1)} |")
    ay, by = t("I-S-Y-m0.1-sendi"), t("I-S-Y-m0.1-jepit")
    L += [f"\nArah Y ({idn(H_TIANG['Y'], 2)} kN, U5 pengali 0,1): sendi y0 {idn(ay['y0'] * 1000, 1)} mm, M maks {idn(ay['mmaks'], 1)} kNm; jepit y0 {idn(by['y0'] * 1000, 1)} mm, "
          f"M kepala {idn(abs(by['mkepala']), 1)} kNm. Utara (X, U5 pengali 0,1): sendi y0 {idn(t('I-U-X-m0.1-sendi')['y0'] * 1000, 1)} mm, M maks {idn(t('I-U-X-m0.1-sendi')['mmaks'], 1)} kNm.\n",
          f"Gambar: `Gambar/6.5 Profil Inersia.png`. φMn tiang (lihat 4): {idn(kap['phiMn'], 0)} kNm.\n",
          "## 3. Hasil kinematik (selatan, tanpa inersia)\n",
          "| Kasus | Sendi y0 (m) | Sendi M maks (kNm) | Sendi V maks (kN) | Jepit M kepala (kNm) | Jepit M maks (kNm) | Jepit V maks (kN) | M/φMn sendi | M/φMn jepit |",
          "|---|---|---|---|---|---|---|---|---|"]
    kk = (("K-Youd-m0.1", "Youd 0,19 m"), ("K-Zhang-m0.1", "Zhang 4,58 m"), ("K-Zhang-m0.3", "Zhang, U5 pengali 0,3"),
          ("K-Zhang-sr", "Zhang, U5 Matlock Sr"), ("K-Zhang-m0.1-tanpaRankine", "Zhang, tanpa batas Rankine"), ("K-Zhang-m0.1-EIbruto", "Zhang, EI bruto"))
    for k, nm in kk:
        a, b = t(k + "-sendi"), t(k + "-jepit")
        L.append(f"| {nm} | {idn(a['y0'], 3)} | {idn(a['mmaks'], 0)} | {idn(a['vmaks'], 0)} | {idn(abs(b['mkepala']), 0)} | {idn(b['mmaks'], 0)} | "
                 f"{idn(b['vmaks'], 0)} | {idn(a['mmaks'] / kap['phiMn'], 2)} | {idn(b['mmaks'] / kap['phiMn'], 2)} |")
    L += ["\nGambar: `Gambar/6.5 Profil Kinematik.png`. Peringatan: teori balok lendutan kecil; pada lendutan beberapa meter (Zhang) nilai hanya penanda tuntutan, "
          "tiang akan membentuk sendi plastis dan menahan lebih sedikit dari yang diperlihatkan.\n",
          "## 4. Kapasitas lentur kasar dan gabungan\n",
          f"- Tulangan usulan {N_BAR} D{int(D_BAR)} (As {idn(kap['As'], 0)} mm², ρ {idn(kap['rho'] * 100, 2)} %) [Asumsi], spiral Ø{int(D_SPIRAL)}, selimut {int(SELIMUT)} mm, fy {int(FY)} MPa. "
          f"Pada P = {idn(P_MAKS, 0)} kN: εt {idn(kap['eps_t'], 4)}, φ {idn(kap['phi'], 3)} (SNI 2847:2019 Tabel 21.2.2), φMn = **{idn(kap['phiMn'], 0)} kNm**. "
          "Hanya untuk rasio; desain penuh di 6.7.\n",
          "| Gabungan | Sendi M maks (kNm) | Rasio | Jepit M maks (kNm) | Rasio |", "|---|---|---|---|---|"]
    for k, nm in (("G-Youd-m0.1", "Youd 0,19 m + 0,5 H Y"), ("G-Zhang-m0.1", "Zhang 4,58 m + 0,5 H Y"), ("G-Zhang-m0.1-X", "Zhang + 0,5 H X")):
        ks = k if not k.endswith("-X") else "G-Zhang-m0.1-X"
        a, b = t(ks + "-sendi"), t(ks + "-jepit")
        L.append(f"| {nm} | {idn(a['mmaks'], 0)} | {idn(a['mmaks'] / kap['phiMn'], 2)} | {idn(b['mmaks'], 0)} | {idn(b['mmaks'] / kap['phiMn'], 2)} |")
    L += [f"\nPerpindahan tanah batas yang masih tertahan (kinematik saja, M = φMn): sendi "
          f"{idn(bt['sendi'], 2) + ' m' if bt['sendi'] is not None else '> 4,58 m'}, jepit {idn(bt['jepit'], 2) + ' m' if bt['jepit'] is not None else '> 4,58 m'} "
          f"(Youd 0,19 m). Kesimpulan:\n"]
    L += [f"- {x}" for x in kesimpulan_butir(h)]
    L += ["\n## 5. Kepala tiang dan sloof 5.4 (butir B-4)\n"]
    jj = t("I-S-X-m0.1-jepit")
    L += [f"- Sendi: momen kepala nol, momen maks {idn(t('I-S-X-m0.1-sendi')['mmaks'], 0)} kNm di dalam tanah (inersia). Jepit: M kepala {idn(abs(jj['mkepala']), 0)} kNm per tiang "
          f"(inersia) dan y kepala turun {idn(t('I-S-X-m0.1-sendi')['y0'] / jj['y0'], 1)} kali.",
          "- Sloof 5.4 didesain dengan kepala tiang sendi: seluruh momen dasar kolom (SL-1 Mu- 1.464 kNm termasuk 980 kNm dari kolom) masuk sloof (`05 Struktur Tengah/5.4 Desain Sloof.md`). "
          f"Bila kepala jepit, tiang ikut menahan momen: momen kepala inersia {idn(abs(jj['mkepala']), 0)} kNm per tiang (beberapa tiang per cap) mengurangi momen sloof; "
          "desain sloof dengan sendi tetap di sisi aman untuk lentur, jadi **sloof tidak perlu dicek ulang untuk inersia**. "
          "Yang perlu dicek bila jepit: momen kepala tiang masuk ke cap dan tulangan stek tiang (6.7) dan sloof sebagai pengikat cap terhadap serakan (V ikat).",
          "- Untuk serakan Zhang jepit, M kepala (lihat 3) melebihi semua kapasitas: kepala jepit tidak realistis pada kasus itu; keputusan kepala tiang mengikuti keputusan perbaikan tanah.\n",
          "## 6. Verifikasi T-103 (tercatat di `VERIFIKASI.md`)\n",
          f"- (a) openpile vs solver sendiri, inersia: selisih y kepala terbesar {idn(r['dy'], 2)} %, M maks {idn(r['dm'], 2)} % (batas 5 %).",
          f"- (b) pembanding orde y muka tanah: p-y sendiri {idn(pm['yg_py'] * 1000, 2)} mm, Reese-Matlock {idn(pm['yg_rm'] * 1000, 2)} mm "
          f"(sebaran {idn(r['seb_rm'], 1)} %), Hetenyi {idn(pm['yg_het'] * 1000, 2)} mm (sebaran {idn(r['seb_het'], 1)} %); batas 30 % (dicatat). "
          f"Broms (1964, GEC9 PDF hal. 83: tidak andal): Hu {idn(pm['hu'], 0)} kN, H/Hu {idn(pm['rasio_hu'], 2)}.",
          f"- (c) Excel = Python: selisih terbesar {idn(r['dxl'], 4) if r['dxl'] is not None else 'tidak dihitung'} % (batas 0,5 %).",
          "- Status: " + ("Lolos." if r["lolos"] else "GAGAL, lihat VERIFIKASI.md."),
          "\n## 7. Keputusan Defsa\n"]
    L += [f"- {x}" for x in keputusan_butir(h)]
    L += ["\n## 8. Sumber\n",
          "- GEC9 (FHWA-HIF-18-031, `acuan/pustaka/`): PDF hal. 70 (analisis push-over, EI), hal. 83 (Broms), hal. 124 (likuifaksi, p-multiplier), hal. 222 (Matlock Pers. A-1, A-2). "
          "Halaman lain belum dicek.",
          "- SNI 2847:2019 Ps. 19.2.2.1 (Ec), Ps. 21.2.2 Tabel 21.2.2 (φ). Belum ada di acuan/: Matlock 1970, API RP 2GEO, Reese-Matlock 1956, Broms 1964, "
          "Brandenberg dkk. 2007, Ashford dkk. 2011, Zhang dkk. 2004, Youd dkk. 2002.\n"]
    Path(keluar).write_text("\n".join(L), encoding="utf-8")
    return keluar


def perbarui_lembar():
    t = LEMBAR.read_text(encoding="utf-8")
    baris = "Status 22 Nov 2026: hasilnya di `6.5 Tiang Lateral.md` (disetujui Defsa 22 Nov 2026)."
    if baris not in t:
        LEMBAR.write_text(t.rstrip("\n") + "\n\n" + baris + "\n", encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from format_dokumen import hitung_ulang_excel
    h = semua()
    for k in ("I-S-X-m0.1-sendi", "I-S-X-m0.1-jepit", "K-Youd-m0.1-sendi", "K-Zhang-m0.1-sendi", "K-Zhang-m0.1-jepit", "G-Zhang-m0.1-sendi"):
        print(k, {a: round(b, 4) for a, b in h["ringkas"][k].items()})
    print("kap", h["kap"], "batas", h["batas_dh"])
    gambar(h)
    berkas, adr = buat_excel(h=h)
    print(berkas, hitung_ulang_excel(berkas))
    r = t103(berkas, adr, h)
    print(r)
    catat_t103(r, h)
    print(tulis_md(h=h, r=r))
    perbarui_lembar()


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--openpile":
        _openpile_jalankan(json.loads(sys.argv[2]))
    else:
        main()
