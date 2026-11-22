"""Tahap 6 langkah 6.4: stabilitas tebing P-2 (Bishop, Spencer), perkuatan, kuat residu U5, serakan lateral.

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (21 Nov 2026); disetujui
Defsa 21 Nov 2026 (Zhang 2004 untuk beban kinematik 6.5). Kunci jawaban tidak dibuka. Geometri, bahan, bidang licin, beban, berm + pelandaian, dan rutin
irisan Bishop diimpor dari `la_tebing` (LA.3, disetujui); Spencer ditambahkan di sini (irisan `la_tebing._iris`).

Acuan (halaman = nomor halaman PDF di acuan/):
- SNI 8460:2017 Ps. 7.5.5 Tabel 25 hal. 134 (FK statis 1,5), Ps. 7.5.1.1 hal. 133 (FK gempa 1,1), Ps. 12.2.7 hal. 279
  (kh = 0,5 amax), Ps. 12.2.5 b.3 hal. 278 (kh 50 % bila perpindahan 25-50 mm diizinkan), Ps. 12.2.7 b hal. 279
  (berbasis perpindahan: Newmark atau numerik), hal. 277 (FK > 1,1 pasca-likuifaksi fondasi) [Asumsi dipakai untuk lereng].
- SNI 2847:2019 Ps. 22.5.5.1 (Vc = 0,17 lambda akar(f'c) bw d), Ps. 22.5.2.2 (lingkaran: bw = D, d = 0,8 D).
- Belum ada di acuan/: Idriss & Boulanger (2008) kuat residu; Youd, Hansen & Bartlett (2002); Zhang, Robertson &
  Brachman (2004); Spencer (1967); Kayu (Fv dolken).
"""
from __future__ import annotations

import math
import os
import pickle
import re
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import la_tebing as lt  # noqa: E402
import tahap2_likuifaksi as lk  # noqa: E402
import tahap2_parameter as tp  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "06 Struktur Bawah dan Basement"
UJI = KELUAR / "Data Uji"
GAMBAR = KELUAR / "Gambar"
BERKAS = KELUAR / "6.4 Stabilitas Tebing.xlsx"
MD = KELUAR / "6.4 Stabilitas Tebing.md"
VERIFIKASI = AKAR / "VERIFIKASI.md"
PNG_PROFIL = GAMBAR / "6.4 Profil Serakan Lateral.png"
PNG_BIDANG = GAMBAR / "6.4 Bidang Kritis P-2.png"
CACHE = Path(tempfile.gettempdir()) / "tahap6_tebing_hasil.pkl"

LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
STATUS = "disetujui Defsa 21 Nov 2026"
LABEL_AI = f"DIISI AI ATAS PERMINTAAN DEFSA (21 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."

K_SU = (1.64, 1.40)       # analisis balik LA.3: lempung x 1,64, bidang licin x 1,40 (`la_tebing.k_desain()`)
BORS = ("BH-2", "BH-5", "BH-6")   # bor terdekat ke potongan P-2 (BH-6 x 90, y 35; BH-2 x 85, y 40; BH-5 x 60, y 35)
X_TIANG = -26.3           # m, garis tiang gedung utama paling selatan (6.3), y 26,3 dari batas lahan
Y_TIANG_LAHAN = 26.3
R_KM = (20.0, 50.0, 100.0, 200.0)   # [Asumsi] jarak sumber gempa untuk Youd (kepekaan)
R_DASAR = 50.0   # [Asumsi: Mw 7 dan PGA batuan 0,164 g (2.6) cocok dengan atenuasi tipikal R sekitar 40-50 km]
ELEV_TIANG_ATAS = lt.pl.peil_usulan()["halaman"]   # +12,05 muka urugan halaman
TAN_PHI_U5 = math.tan(math.radians(lt.BAHAN["U5"].phi))
FC_BETON = 30.0           # MPa [Asumsi: sama dengan 6.2]
D_BOR = 0.6               # m tiang bor batas lahan
S_BOR = 1.2               # m [Asumsi] jarak as ke as
PHI_GESER = 0.75          # SNI 2847:2019 Tabel 21.2.1 geser
EMBED = 3.0               # m [Asumsi] 5 D di bawah titik terdalam bidang kritis
D_DOLKEN = 0.15           # m [Asumsi]
FV_KAYU = 1.0             # MPa [Asumsi] kuat geser sejajar serat kayu kelas II, belum ada di acuan/
TOL = {"bishop_spencer": 5.0, "pyslope": 2.0, "excel": 0.1, "youd_zhang": 2.0}   # %, %, %, faktor; ditetapkan dulu


def sg(v, d=2):
    return ("+" if v >= 0 else "-") + idn(abs(v), d)


def idn(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------------------------------------------ Spencer
def spencer(s, bid, kh):
    """FK Spencer (1967): gaya antar-irisan sejajar, sudut theta konstan; FK momen = FK gaya.
    s = irisan `la_tebing._iris`; N dan S dari keseimbangan tiap irisan (alpha = -theta dasar irisan)."""
    from scipy.optimize import brentq
    if s is None:
        return float("nan")
    al = -s["th"]
    sa, ca = np.sin(al), np.cos(al)
    W, Wm, u, c, tphi, beta = s["W"] + s["Q"], s["Wm"], s["u"], s["c"], s["tphi"], s["beta"]
    rx, ry = s["xm"] - bid.xo, s["ym"] - bid.yo
    tx, ty, nx, ny = np.cos(s["th"]), np.sin(s["th"]), -np.sin(s["th"]), np.cos(s["th"])
    cr_t, cr_n = rx * ty - ry * tx, rx * ny - ry * nx
    m_drive = float(np.sum(W * (bid.xo - s["xm"])) + np.sum(kh * Wm * (bid.yo - s["ycg"])))

    def dq(F, t):
        num = F * (W * sa + kh * Wm * ca) - c * beta - (W * ca - kh * Wm * sa - u * beta) * tphi
        den = F * np.cos(al + t) + tphi * np.sin(al + t)
        if np.any(den < 0.05):   # penyebut mendekati nol / negatif: tidak stabil secara numerik (seperti m-alpha Bishop)
            raise ValueError("penyebut Spencer")
        return num / den

    def f_gaya(F, t):
        return float(np.sum(dq(F, t)))

    def f_momen(F, t):
        d = dq(F, t)
        N = W * ca - kh * Wm * sa + d * np.sin(al + t)
        S = W * sa + kh * Wm * ca - d * np.cos(al + t)
        return float(np.sum(S * cr_t) - (m_drive + np.sum(N * cr_n)))

    def akar(f, t):
        Fs = np.linspace(0.15, 6.0, 60)
        v = []
        for F in Fs:
            try:
                v.append(f(F, t))
            except Exception:
                v.append(np.nan)
        v = np.array(v)
        for i in range(len(Fs) - 1):
            if np.isfinite(v[i]) and np.isfinite(v[i + 1]) and v[i] * v[i + 1] < 0:
                return brentq(lambda F: f(F, t), Fs[i], Fs[i + 1], xtol=1e-7)
        return float("nan")

    def beda(t):
        return akar(f_gaya, t) - akar(f_momen, t)

    ts = np.radians(np.arange(-70.0, 81.0, 2.5))
    bs = [beda(t) for t in ts]
    for i in range(len(ts) - 1):
        if np.isfinite(bs[i]) and np.isfinite(bs[i + 1]) and bs[i] * bs[i + 1] < 0:
            t0 = brentq(beda, ts[i], ts[i + 1], xtol=1e-6)
            return akar(f_gaya, t0)
    ok = [(abs(b_), t_) for b_, t_ in zip(bs, ts) if np.isfinite(b_)]   # akar di tepi daerah penyebut valid: terima bila FK gaya = FK momen (< 2 %)
    if ok:
        b_, t_ = min(ok)
        ff = akar(f_gaya, t_)
        if np.isfinite(ff) and b_ / ff < 0.02:
            return ff
    return float("nan")


# ------------------------------------------------------------------ kasus dan konfigurasi
def kasus():
    n, sp = lt.kondisi(), lt.SELISIH_PASIR
    return [
        dict(kode="a", nama="(a) Muka air rendah +4,00", izin=1.5, dasar="statis",
             kon=lt.Kondisi("a", "(a) Muka air rendah +4,00", lt.MA_RENDAH, lt.MA_RENDAH + sp), residu=False),
        dict(kode="a0", nama="(a0) Statis muka normal +6,37 (LA.3)", izin=1.5, dasar="statis", kon=n[0], residu=False),
        dict(kode="b", nama="(b) Surut cepat Q50 +11,85 ke +4,00", izin=1.25, dasar="surut", kon=n[1], residu=False),
        dict(kode="c", nama="(c) Gempa kh 0,171, muka normal", izin=1.1, dasar="gempa", kon=n[2], residu=False),
        dict(kode="c2", nama="(c') Gempa kh 0,085 (50 %), muka normal", izin=1.1, dasar="gempa",
             kon=lt.Kondisi("c2", "gempa kh 50 %", lt.MA_NORMAL, lt.MA_NORMAL + sp, 0.5 * lt.KH), residu=False),
        dict(kode="d", nama="(d) Pasca-likuifaksi, U5 kuat residu Sr, muka +4,00", izin=1.1, dasar="gempa",
             kon=lt.Kondisi("d", "pasca-likuifaksi", lt.MA_RENDAH, lt.MA_RENDAH + sp), residu=True),
    ]


def pot_konf(konf, sr=None):
    """konf 'tanpa' = tebing LA.3 tanpa perkuatan; 'perkuatan' = berm bronjong + pelandaian 1V:2H (LA.3)."""
    pot = lt.potongan("P-2", k_su=K_SU, berm=(konf == "perkuatan"), landai=(konf == "perkuatan"))
    if sr is not None:
        # su dikali k lempung 1,64 di `la_tebing._iris` untuk kode yang tidak dikenal: dibagi dulu agar efektif Sr
        lt.BAHAN["U5R"] = lt.Bahan("U5R", 19.0, su=sr / K_SU[0], sumber="U5 pasca-likuifaksi, phi = 0, su = Sr")
        pot = replace(pot, lapis=[("U5R" if k == "U5" else k, e) for k, e in pot.lapis])
    return pot


def fk_satu(ks, konf, sr):
    pot = pot_konf(konf, sr if ks["residu"] else None)
    kh = ks["kon"].kh
    out = {}
    for nm, xm in (("semua", None), ("persil", 0.0)):
        f, b, s = lt.cari(pot, ks["kon"], x_min=xm)
        sp = spencer(s, b, kh) if s is not None else float("nan")
        r = dict(bishop=f, spencer=sp, bidang=(b.xo, b.yo, b.r, b.potong) if b else None,
                 x1=s["x1"] if s else None, x2=s["x2"] if s else None,
                 y_min=float(np.min(s["ym"])) if s else None)
        if nm == "persil" and s is not None:
            _, M = lt._fk_den(s, b, kh, "bishop")
            r["M"] = float(M)
            r["P"] = max(0.0, (ks["izin"] - f) * M / b.r)
        out[nm] = r
    return out


# ------------------------------------------------------------------ kuat residu U5
DELTA_SR = [(0, 0.0), (10, 1.0), (25, 2.0), (50, 4.0), (75, 5.0)]   # [Asumsi: bacaan Idriss-Boulanger 2008; FC 10 % = 1]


def delta_sr(fc):
    return float(np.interp(fc, [a for a, _ in DELTA_SR], [b for _, b in DELTA_SR]))


def sr_rasio(n160, fc):
    """Sr/sigma'vo (Idriss & Boulanger 2008), batas atas tan phi' (redistribusi rongga signifikan, konservatif)."""
    x = n160 + delta_sr(fc)
    return min(math.exp(x / 16 + ((x - 16) / 21.2) ** 3 - 3.0), TAN_PHI_U5)


def spt_pool():
    """Uji SPT di U5 untuk bor terdekat: bor, dari, elevasi, (N1)60, (N1)60cs, FC, sigma'v, FS."""
    hasil = []
    for r in lk.analisis_spt():
        if r["bor"] in BORS:
            hasil.append(dict(bor=r["bor"], dari=round(r["z"] - 0.225, 2), z=r["z"], elev=r["elev"], n160=r["n160"],
                              n160cs=r["n160cs"], fc=r["fc"], sve=r["sve"], fs=r["fs"], sumber_fc=r["sumber_fc"]))
    for h in hasil:
        h["delta"] = delta_sr(h["fc"])
        h["rasio"] = sr_rasio(h["n160"], h["fc"])
        h["sr"] = h["rasio"] * h["sve"]
    return hasil


def d50_saringan():
    """{(bor, dari): D50 (mm)} dari analisis saringan (interpolasi log ukuran terhadap persen lolos)."""
    import openpyxl
    hasil = {}
    for path in (tp.LAMA / "Laboratorium.xlsx", tp.BARU / "Laboratorium Tambahan.xlsx"):
        ws = openpyxl.load_workbook(path, data_only=True)["Analisis Saringan"]
        ukuran = None
        for r in ws.iter_rows(values_only=True):
            if "Titik" in r:
                ukuran = [float(re.search(r"([\d.,]+)\s*mm", c).group(1).replace(",", "."))
                          for c in r if isinstance(c, str) and c.startswith("Lolos")]
            elif ukuran and isinstance(r[0], str) and r[0].startswith("BH") or (ukuran and any(
                    isinstance(c, str) and c.startswith("BH") for c in r)):
                bor = next(c for c in r if isinstance(c, str) and c.startswith("BH"))
                num = [c for c in r if isinstance(c, (int, float))]
                dari, lolos = float(num[0]), num[-len(ukuran):]
                u, p = np.array(ukuran[::-1]), np.array(lolos[::-1], float)   # ukuran naik, lolos naik
                hasil[(bor, dari)] = float(10 ** np.interp(50.0, p, np.log10(u)))
    return hasil


# ------------------------------------------------------------------ serakan lateral
def youd(M, R, W, T15, F15, D50):
    """Youd, Hansen & Bartlett (2002), muka bebas: log(DH + 0,01) = ...; DH dalam m. Batas: 1 <= W <= 20 %, 1 <= T15 <= 15 m."""
    Rs = R + 10 ** (0.89 * M - 5.64)
    lg = (-16.713 + 1.532 * M - 1.406 * math.log10(Rs) - 0.012 * R + 0.592 * math.log10(W) + 0.540 * math.log10(T15)
          + 3.413 * math.log10(100 - F15) - 0.795 * math.log10(D50 + 0.1))
    return max(10 ** lg - 0.01, 0.0)


def zhang_gmax(fs, n160cs):
    """Regangan geser maksimum (pecahan) Zhang dkk. (2004) dari FS dan (N1)60cs lewat Dr = akar((N1)60cs/46)."""
    dr = math.sqrt(min(max(n160cs, 0.0), 46.0) / 46.0)
    fa = 0.032 + 4.7 * dr - 6.0 * dr ** 2
    glim = max(0.0, 1.859 * (1.1 - dr) ** 3)
    if fs >= 2.0:
        return 0.0
    if fs <= fa:
        return glim
    return min(glim, 0.035 * (1 - fa) * (2 - fs) / (fs - fa))


def zhang_dh(ldi, L, H):
    return 6.0 * (L / H) ** -0.8 * ldi


def geometri_bebas():
    pot = lt.potongan("P-2", k_su=K_SU)
    xs, zs = pot.xs, pot.zs
    x_puncak = lt.X_PUNCAK_P2
    z_puncak = float(np.interp(x_puncak, xs, zs))
    z_dasar = float(zs.min())
    x_kaki = float(next(x for x, z in zip(xs, zs) if x > x_puncak and z <= z_dasar + 0.15))
    H = z_puncak - z_dasar
    L = x_kaki - X_TIANG
    return dict(z_puncak=z_puncak, z_dasar=z_dasar, x_kaki=x_kaki, H=H, L=L, W=100 * H / L, LH=L / H)


def u5_batas():
    d = dict(lt.LAPIS["P-2"])
    return d["U4"], d["U5"]   # atas U5 = bawah U4 (+1,01), bawah U5 (-9,18)


def tepi_irisan():
    atas, bawah = u5_batas()
    return np.r_[atas, np.arange(0.5, bawah, -0.5), bawah]


def profil_rata(pool, bors=None):
    """FS, (N1)60cs, (N1)60 rata-rata antar bor pada tengah tiap irisan 0,5 m U5 (interpolasi tiap bor)."""
    bors = bors or BORS
    e = tepi_irisan()
    mid = (e[:-1] + e[1:]) / 2
    fs, n, n1 = [], [], []
    for b in bors:
        t = sorted([h for h in pool if h["bor"] == b], key=lambda h: h["elev"])
        el = [h["elev"] for h in t]
        fs.append(np.interp(mid, el, [h["fs"] for h in t]))
        n.append(np.interp(mid, el, [h["n160cs"] for h in t]))
        n1.append(np.interp(mid, el, [h["n160"] for h in t]))
    return mid, np.mean(fs, axis=0), np.mean(n, axis=0), np.mean(n1, axis=0)


def serakan(pool, d50, bors=None, R=R_DASAR, geo=None):
    geo = geo or geometri_bebas()
    e = tepi_irisan()
    mid, fs, n160cs, n160 = profil_rata(pool, bors)
    dz = e[:-1] - e[1:]
    gm = np.array([zhang_gmax(a, b) for a, b in zip(fs, n160cs)])
    contrib = gm * dz
    ldi = float(contrib.sum())
    dh_z = zhang_dh(ldi, geo["L"], geo["H"])
    t15 = float(dz[n160 <= 15].sum())
    uji = [h for h in pool if (bors is None or h["bor"] in bors) and h["n160"] <= 15]
    f15 = float(np.mean([h["fc"] for h in uji]))
    dd = [d50[(h["bor"], h["dari"])] for h in uji if (h["bor"], h["dari"]) in d50]
    d5015 = float(np.mean(dd))
    dh_y = youd(lk.MW, R, geo["W"], t15, f15, d5015)
    # kumulatif dari dasar U5 ke atas: u di tepi atas tiap irisan
    cum = np.cumsum(contrib[::-1])[::-1]
    u_atas = dh_z * cum / ldi if ldi > 0 else np.zeros_like(cum)
    return dict(e=e, mid=mid, fs=fs, n160cs=n160cs, n160=n160, dz=dz, gm=gm, contrib=contrib, ldi=ldi, dh_zhang=dh_z,
                t15=t15, f15=f15, d50=d5015, n_d50=len(dd), dh_youd=dh_y, u_atas=u_atas, geo=geo, R=R,
                kepekaan={r: youd(lk.MW, r, geo["W"], t15, f15, d5015) for r in R_KM})


def profil_node(sk):
    """Node profil perpindahan di garis tiang: (elevasi, lapisan, u m) dari muka urugan sampai -12."""
    atas, bawah = u5_batas()
    dh = sk["dh_zhang"]
    node = [(ELEV_TIANG_ATAS, "Urugan U1/U2", dh), (10.22, "U2 (muka asli)", dh), (8.48, "U4", dh), (4.0, "U4", dh),
            (atas, "Atas U5", dh)]
    for e, u in zip(sk["e"][1:-1], sk["u_atas"][1:]):
        node.append((float(e), "U5", float(u)))
    node += [(bawah, "Dasar U5 / atas U6", 0.0), (-12.0, "U6", 0.0)]
    return node


# ------------------------------------------------------------------ perkuatan
def kapasitas_bor():
    """Geser tiang bor Ø600 tanpa sengkang (beton polos, konservatif): SNI 2847:2019 Ps. 22.5.5.1 dan 22.5.2.2."""
    bw, d = D_BOR, 0.8 * D_BOR
    vc = 0.17 * 1.0 * math.sqrt(FC_BETON) * bw * d * 1000.0   # kN
    return dict(vc=vc, fvc=PHI_GESER * vc, per_m=PHI_GESER * vc / S_BOR)


def kapasitas_dolken():
    a = math.pi * D_DOLKEN ** 2 / 4
    v = 0.75 * FV_KAYU * a * 1000.0      # kN, geser maksimum lingkaran = 4V/3A
    return dict(a=a, v=v, baris_per_m=1 / (2.5 * D_DOLKEN))


def perkuatan_tabel(h):
    kb, kd = kapasitas_bor(), kapasitas_dolken()
    z0 = float(np.interp(0.0, *(lambda p: (p.xs, p.zs))(lt.potongan("P-2", k_su=K_SU))))
    out = []
    for ks in kasus():
        for konf in ("tanpa", "perkuatan"):
            r = h["fk"][(ks["kode"], konf)]["persil"]
            P = r["P"]
            y_min = r["y_min"]
            tip = (-9.18 - EMBED) if ks["residu"] else (y_min - EMBED)
            out.append(dict(kode=ks["kode"], nama=ks["nama"], konf=konf, izin=ks["izin"], fk=r["bishop"], P=P,
                            n_bor=P / kb["fvc"], s_bor=(kb["fvc"] / P) if P > 0 else None, L_bor=z0 - tip,
                            n_dolken=P / kd["v"], baris_dolken=math.ceil(P / kd["v"] / kd["baris_per_m"]) if P > 0 else 0,
                            tip=tip))
    return out


# ------------------------------------------------------------------ inklinometer
def baca_inklinometer():
    import openpyxl
    ws = openpyxl.load_workbook(UJI / "Pemantauan Urugan dan PVD.xlsx", data_only=True)["Inklinometer"]
    d = {}
    for r in ws.iter_rows(min_row=9, values_only=True):
        if r[2] in ("INC-1", "INC-2", "INC-3"):
            d.setdefault((r[2], str(r[3])), []).append((float(r[4]), float(r[5]), float(r[6])))
    return d


def ringkas_inklinometer(d, bidang=None):
    hasil = {}
    for inc in ("INC-1", "INC-2"):
        tgl = sorted({t for (i, t) in d if i == inc})
        akhir, awal = d[(inc, tgl[-1])], d[(inc, "2027-05-15")]
        ptop = lambda rows: max(rows, key=lambda x: x[1])[2]
        dt = (np.datetime64(tgl[-1]) - np.datetime64("2027-05-15")).astype(int)
        laju = (ptop(akhir) - ptop(awal)) / dt
        a = sorted(akhir, key=lambda x: x[1])   # elevasi naik
        g = [(abs(a[i + 1][2] - a[i][2]) / (a[i + 1][1] - a[i][1]), (a[i][1] + a[i + 1][1]) / 2) for i in range(len(a) - 1)]
        gmax = max(g)
        hasil[inc] = dict(tgl=tgl[-1], atas=ptop(akhir), atas_mei=ptop(awal), laju=laju, gradien=gmax[0], elev_geser=gmax[1],
                          profil=sorted(akhir, key=lambda x: -x[1]))
    return hasil


def y_bidang(b, x):
    xo, yo, r, potong = b
    if abs(x - xo) > r:
        return None   # bidang tidak mencapai x
    y = yo - math.sqrt(r * r - (x - xo) ** 2)
    if potong:
        pot = lt.potongan("P-2", k_su=K_SU)
        a, c = pot.licin_rentang()
        if a <= x <= c:
            y = max(y, float(pot.y_licin(x)))
    return y


# ------------------------------------------------------------------ cek silang pyslope
def cek_pyslope():
    """Bishop pyslope vs skrip pada lingkaran yang sama: lereng 6 m, 30 derajat, dua lapis c-phi, muka air di kaki."""
    import contextlib
    import io

    import pyslope as ps
    xs, zs = [0.0, 20.784609690826528, 31.176914536239792, 51.96152422706632], [6.0, 6.0, 0.0, 0.0]   # y pyslope - 34 (raster la_tebing -25..15)
    lt.BAHAN["UJIA"] = lt.Bahan("UJIA", 18.0, su=5.0, phi=25.0)
    lt.BAHAN["UJIB"] = lt.Bahan("UJIB", 19.0, su=8.0, phi=30.0)
    pot = lt.Potongan("UJI", np.array(xs), np.array(zs), [("UJIA", 3.0), ("UJIB", -99.0)])
    kon = lt.Kondisi("uji", "uji", 0.0, 0.0, mat=1000.0)

    def pyslope_fk(lingkaran=None):
        s = ps.Slope(height=6, angle=30)
        s.set_materials(ps.Material(18, 25, 5, 3, "A"), ps.Material(19, 30, 8, 40, "B"))
        s.set_water_table(6.0)
        s.update_analysis_options(slices=60)
        if lingkaran:
            s.add_single_circular_plane(*lingkaran)
        with contextlib.redirect_stderr(io.StringIO()):
            s.analyse_slope()
        return s.get_min_FOS(), s.get_min_FOS_circle()

    f0, c0 = pyslope_fk()
    daftar = [c0, (26.0, 52.0, 20.0), (30.0, 55.0, 24.0), (28.0, 50.0, 17.0)]
    baris = []
    for c in daftar:
        fp, cc = pyslope_fk(c) if c is not c0 else (f0, c0)
        fs, _ = lt.fk(pot, kon, lt.Bidang(cc[0], cc[1] - 34.0, cc[2]), "bishop")
        if np.isfinite(fs):   # lingkaran yang menyinggung kaki ditolak `_iris` (tidak wajar)
            baris.append(dict(lingkaran=cc, pyslope=fp, skrip=float(fs), selisih=abs(fs - fp) / fp * 100))
    return baris


# ------------------------------------------------------------------ hitung semua
def semua(pakai_cache=True):
    if pakai_cache and CACHE.exists() and os.environ.get("TAHAP6_TEBING_CACHE") == "1":
        return pickle.loads(CACHE.read_bytes())
    pool = spt_pool()
    d50 = d50_saringan()
    sr_all = [h["sr"] for h in pool]
    sr = float(np.mean(sr_all))
    h = dict(pool=pool, d50=d50, sr=sr, sr_min=float(min(sr_all)), sr_maks=float(max(sr_all)),
             ratio=float(np.mean([x["rasio"] for x in pool])))
    h["fk"] = {}
    for ks in kasus():
        for konf in ("tanpa", "perkuatan"):
            h["fk"][(ks["kode"], konf)] = fk_satu(ks, konf, sr)
    # sensitivitas Sr terendah, kasus (d) perkuatan
    ksd = next(k for k in kasus() if k["kode"] == "d")
    h["fk_d_srmin"] = fk_satu(ksd, "perkuatan", h["sr_min"])
    # Spencer pencarian kasar: statis (a), perkuatan, bidang yang masuk persil
    ksa = kasus()[0]
    pot = pot_konf("perkuatan")
    b0 = h["fk"][("a", "perkuatan")]["persil"]["bidang"]
    best = (np.inf, None)
    for dx in (-3, 0, 3):
        for dy in (-3, 0, 3):
            for dr in (-1.5, 0, 1.5):
                b = lt.Bidang(b0[0] + dx, b0[1] + dy, b0[2] + dr, b0[3])
                if b.r <= 1.0:
                    continue
                s = lt._iris(pot, ksa["kon"], b)
                if s is None or s["x1"] > 0.0:
                    continue
                f = spencer(s, b, 0.0)
                if np.isfinite(f) and f < best[0]:
                    best = (f, (b.xo, b.yo, b.r, b.potong))
    h["spencer_cari"] = dict(fk=best[0], bidang=best[1])
    h["sk"] = serakan(pool, d50)
    h["sk_bor"] = {b: serakan(pool, d50, bors=(b,)) for b in ("BH-5", "BH-6")}
    h["pyslope"] = cek_pyslope()
    h["inc"] = ringkas_inklinometer(baca_inklinometer())
    if pakai_cache:
        CACHE.write_bytes(pickle.dumps(h))
    return h


# ------------------------------------------------------------------ gambar
def gambar(h):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    GAMBAR.mkdir(exist_ok=True)
    sk = h["sk"]
    node = profil_node(sk)
    fig, ax = plt.subplots(1, 2, figsize=(11, 6.5), gridspec_kw=dict(width_ratios=[1.3, 1]))
    a = ax[0]
    el = [n[0] for n in node]
    u = [n[2] for n in node]
    a.plot(u, el, "-", color="#1f4e79", lw=2, label="u(z) = DH x ∫γ / LDI (Zhang)")
    atas, bawah = u5_batas()
    a.axhspan(bawah, atas, color="#f4d9a6", alpha=0.5, label="U5 pasir (likuifaksi)")
    a.axhline(ELEV_TIANG_ATAS, color="gray", lw=0.8, ls=":")
    a.axvline(sk["dh_youd"], color="#c00000", ls="--", label=f"DH Youd {idn(sk['dh_youd'], 2)} m (R {int(sk['R'])} km)")
    a.axvline(sk["dh_zhang"], color="#1f4e79", ls="--", lw=0.8, label=f"DH Zhang {idn(sk['dh_zhang'], 2)} m")
    a.set_xlabel("Perpindahan lateral u (m), garis tiang x = -26,3 m")
    a.set_ylabel("Elevasi (m)")
    a.set_title("Profil serakan lateral di garis tiang (beban kinematik 6.5)")
    a.grid(alpha=0.3)
    a.legend(fontsize=8, loc="lower right")
    b = ax[1]
    b.barh(sk["mid"], sk["gm"] * 100, height=0.45, color="#7f7f7f")
    b.set_xlabel("γmax Zhang (%)")
    b.set_title(f"γmax per lapis, LDI = {idn(sk['ldi'], 2)} m")
    b.grid(alpha=0.3)
    b2 = b.twiny()
    b2.plot(sk["fs"], sk["mid"], "o-", color="#c00000", ms=3)
    b2.set_xlabel("FS likuifaksi (rata-rata BH-2, BH-5, BH-6)", color="#c00000")
    fig.text(0.5, 0.005, LABEL, ha="center", fontsize=7)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(PNG_PROFIL, dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    pot = pot_konf("perkuatan")
    pot0 = pot_konf("tanpa")
    ax.plot(pot0.xs, pot0.zs, "k-", lw=1.5, label="muka tanah P-2 (tanpa perkuatan)")
    ax.plot(pot.xs, pot.zs, "-", color="#2e7d32", lw=1.2, label="dengan pelandaian + berm")
    for kode, warna in (("a", "#1f4e79"), ("c", "#c00000"), ("d", "#7030a0")):
        for konf, ls in (("tanpa", "--"), ("perkuatan", "-")):
            r = h["fk"][(kode, konf)]["persil"]
            if not r["bidang"]:
                continue
            xo, yo, rr, _ = r["bidang"]
            th = np.linspace(math.radians(180 + 10), math.radians(360 - 10), 200)
            xx, yy = xo + rr * np.cos(th), yo + rr * np.sin(th)
            top = np.interp(xx, pot0.xs, pot0.zs)
            m = yy < np.maximum(top, 4.0)
            ax.plot(xx[m], yy[m], ls, color=warna, lw=1.0, label=f"({kode}) {konf}: FK {idn(r['bishop'], 2)}")
    ax.axvline(0, color="k", lw=0.6, ls=":")
    ax.text(0.3, 12.5, "batas lahan", fontsize=8)
    ax.set_xlim(-30, 45)
    ax.set_ylim(-12, 14)
    ax.set_aspect("equal")
    ax.set_xlabel("Jarak dari batas lahan (m)")
    ax.set_ylabel("Elevasi (m)")
    ax.set_title("P-2: bidang kritis Bishop yang masuk persil")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(alpha=0.3)
    fig.text(0.5, 0.005, LABEL, ha="center", fontsize=7)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(PNG_BIDANG, dpi=150)
    plt.close(fig)


# ------------------------------------------------------------------ Excel
def buat_excel(keluar=BERKAS, h=None):
    import openpyxl
    from format_dokumen import AI, Lembar, set_font_bawaan
    h = h or semua()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    ket = LABEL + " " + LABEL_AI
    adr = {}
    ks_list = kasus()
    sk, geo = h["sk"], h["sk"]["geo"]

    # ---- 1 Petunjuk
    lp = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk dan daftar lembar", [26, 100])
    lp.catatan(f"STATUS: {STATUS}. " + ket)
    lp.kosong()
    lp.bagian("A", "Isi lembar")
    lp.tabel(["Lembar", "Isi"], [
        ["Data", "Parameter, kasus, FK izin SNI 8460, geometri bebas serakan"],
        ["Inklinometer", "INC-1 dan INC-2: profil terakhir, laju, zona geser, dibandingkan bidang kritis"],
        ["FK Tebing", "FK Bishop dan Spencer P-2 per kasus, tanpa dan dengan perkuatan LA.3 (berm + pelandaian)"],
        ["Perkuatan", "Gaya geser perlu di batas lahan dan perbandingan tiang bor Ø600, cerucuk dolken, geser garis tiang"],
        ["Kuat Residu", "Sr U5 (Idriss dan Boulanger 2008), rumus Excel hidup"],
        ["Serakan Lateral", "Youd dkk. 2002 dan Zhang dkk. 2004, profil perpindahan per kedalaman (rumus Excel hidup)"],
        ["Cek Silang", "Bishop-Spencer, pyslope, Youd-Zhang, Excel-Python (T-102); GeoFEM3D"],
        ["Kesimpulan", "Hasil, perkuatan yang disarankan, keputusan Defsa"]], rata=["l", "l"], beku=False)
    lp.kosong()
    lp.catatan("Sel hijau diisi AI dari skrip `tahap6_tebing.py`. Rumus Excel hidup: lembar Kuat Residu dan Serakan Lateral. "
               "FK tebing dari pencarian bidang `la_tebing.cari` (Bishop) dan Spencer pada bidang yang sama; tidak dihitung di Excel.")

    # ---- 2 Data
    ld = Lembar(wb.create_sheet("Data"), 2, "Data masukan", [44, 16, 70])
    ld.catatan(ket)
    ld.kosong()
    ld.bagian("A", "Parameter dan batas FK")
    ld.tabel(["Besaran", "Nilai", "Sumber"], [
        ["Faktor su lempung (analisis balik LA.3)", K_SU[0], "`la_tebing.k_desain()`, disetujui Defsa 20 Nov 2026"],
        ["Faktor su bidang licin (LA.3)", K_SU[1], "idem"],
        ["Puncak tebing P-2 dari batas lahan (m)", lt.X_PUNCAK_P2, "LA.3 GESER_P2 (surat sempadan Feb 2027)"],
        ["Muka air rendah (m)", lt.MA_RENDAH, "TOR 4.3 Lampiran A (Sep)"],
        ["Muka air normal LA.3 (m)", round(lt.MA_NORMAL, 3), "TOR Lampiran A, rata-rata 12 bulan"],
        ["Muka Q50 (m)", lt.MA_Q50, "langkah 3.3"],
        ["kh = 0,5 amax", round(lt.KH, 4), "SNI 8460:2017 Ps. 12.2.7 hal. 279; amax 0,342 g (2.6)"],
        ["kh 50 % (c')", round(0.5 * lt.KH, 4), "SNI 8460 Ps. 12.2.5 b.3 hal. 278 (perpindahan 25-50 mm diizinkan)"],
        ["FK izin statis", 1.5, "SNI 8460 Ps. 7.5.5 Tabel 25 hal. 134"],
        ["FK izin surut cepat", 1.25, "Tabel 25 [Asumsi: kondisi sementara]"],
        ["FK izin gempa", 1.1, "SNI 8460 Ps. 7.5.1.1 hal. 133"],
        ["FK izin pasca-likuifaksi", 1.1, "[Asumsi: kondisi gempa; SNI 8460 hal. 277 FK > 1,1 pasca-likuifaksi fondasi]"],
        ["Mw", lk.MW, "PuSGeN 2017 deagregasi (2.6)"],
        ["R jarak sumber dasar (km)", R_DASAR, "[Asumsi: belum ada jarak sumber di proyek; kepekaan 50 / 100 / 200 km]"],
        ["Garis tiang gedung dari batas lahan (m)", Y_TIANG_LAHAN, "6.3 `tahap6_tata_letak.rancang('a')`"],
        ["H muka bebas (m)", round(geo["H"], 2), f"puncak +{idn(geo['z_puncak'], 2)} ke dasar sungai {idn(geo['z_dasar'], 2)} (potongan P-2)"],
        ["L dari kaki muka bebas ke garis tiang (m)", round(geo["L"], 1), f"kaki x {idn(geo['x_kaki'], 1)} m, garis tiang x {idn(X_TIANG, 1)} m"],
        ["W = 100 H/L (%)", round(geo["W"], 2), "Youd: berlaku 1-20 %"],
        ["L/H", round(geo["LH"], 2), "Zhang: berlaku 4-40"],
    ], rata=["l", "c", "l"], fmt=[None, "0.000", None], fill_kolom={1: AI}, beku=False)

    # ---- 3 Inklinometer
    li = Lembar(wb.create_sheet("Inklinometer"), 3, "Inklinometer INC-1 dan INC-2", [14, 14, 14, 14, 14, 14, 40])
    li.catatan(ket + " Data: `Data Uji/Pemantauan Urugan dan PVD.xlsx` lembar Inklinometer.")
    li.kosong()
    li.bagian("A", "Ringkasan dan laju")
    rb = h["fk"][("a", "tanpa")]["persil"]["bidang"]
    rb_x1 = h["fk"][("a", "tanpa")]["persil"]["x1"]
    inc1 = h["inc"]["INC-1"]
    y_bid = y_bidang(rb, -2.0)
    rows = []
    for inc, x in (("INC-1", -2.0), ("INC-2", None)):
        v = h["inc"][inc]
        rows.append([inc, v["tgl"], round(v["atas_mei"], 1), round(v["atas"], 1), round(v["laju"], 3),
                     round(v["gradien"], 3), round(v["elev_geser"], 2)])
    li.tabel(["Titik", "Tanggal akhir", "Puncak 15 Mei (mm)", "Puncak akhir (mm)", "Laju Mei-Jul (mm/hari)",
              "Gradien maks (mm/m)", "Elevasi zona geser (m)"], rows, rata=["l"] + ["c"] * 6,
             fmt=[None, None, "0.0", "0.0", "0.000", "0.000", "0.00"], fill=AI, beku=False)
    li.kosong()
    li.catatan(f"Bidang licin LA.3 di +5,43 (menerus di x = -2 m). Bidang kritis kasus (a) tanpa perkuatan yang masuk persil: "
               f"{'elevasi ' + sg(y_bid) + ' m di x = -2 m' if y_bid is not None else 'ujung darat x = ' + idn(rb_x1, 1) + ' m, tidak mencapai x = -2 m'}. Zona geser INC-1 terukur {idn(inc1['elev_geser'], 2)} m: "
               f"{'cocok' if abs(inc1['elev_geser'] - 5.43) <= 1.0 else 'tidak cocok'} dengan bidang licin (selisih "
               f"{idn(abs(inc1['elev_geser'] - 5.43), 2)} m). Laju INC-1 {idn(inc1['laju'], 3)} mm/hari: lereng masih bergerak.")
    li.kosong()
    li.bagian("B", "Profil INC-1 dan INC-2, pembacaan terakhir (20 Jul 2027)")
    pr1, pr2 = h["inc"]["INC-1"]["profil"], h["inc"]["INC-2"]["profil"]
    n = min(len(pr1), len(pr2))
    li.tabel(["Kedalaman (m)", "Elevasi INC-1 (m)", "INC-1 (mm)", "Elevasi INC-2 (m)", "INC-2 (mm)"],
             [[round(pr1[i][0], 2), round(pr1[i][1], 2), round(pr1[i][2], 2), round(pr2[i][1], 2), round(pr2[i][2], 2)]
              for i in range(n)], rata=["c"] * 5, fmt=["0.00", "0.00", "0.0", "0.00", "0.0"], fill=AI, beku=False)

    # ---- 4 FK Tebing
    lf = Lembar(wb.create_sheet("FK Tebing"), 4, "FK Bishop dan Spencer, P-2", [34, 11, 11, 11, 11, 11, 11, 11, 11, 12, 12, 12])
    lf.catatan(ket + " k su lempung 1,64 dan bidang licin 1,40 (analisis balik LA.3). 'Semua' = bidang kritis seluruh tebing; "
               "'persil' = bidang yang ujung daratnya masuk persil (x <= 0). Spencer dihitung pada bidang kritis Bishop yang sama.")
    lf.kosong()
    for konf, jud in (("tanpa", "Tanpa perkuatan"), ("perkuatan", "Dengan perkuatan LA.3: berm bronjong +6,50 lebar 8 m + pelandaian 1V:2H")):
        lf.bagian("A" if konf == "tanpa" else "B", jud)
        rows = []
        for ks in ks_list:
            a, p = h["fk"][(ks["kode"], konf)]["semua"], h["fk"][(ks["kode"], konf)]["persil"]
            rows.append([ks["nama"], ks["izin"], round(a["bishop"], 3), round(a["spencer"], 3), round(p["bishop"], 3),
                         round(p["spencer"], 3), "Ya" if p["bishop"] >= ks["izin"] else "Tidak",
                         round(a["x1"], 1) if a["x1"] is not None else None, round(a["x2"], 1) if a["x2"] is not None else None,
                         round(p["x1"], 1) if p["x1"] is not None else None, round(p["x2"], 1) if p["x2"] is not None else None])
        lf.tabel(["Kasus", "FK izin", "Bishop semua", "Spencer semua", "Bishop persil", "Spencer persil", "Persil memenuhi?",
                  "x1 semua (m)", "x2 semua (m)", "x1 persil (m)", "x2 persil (m)"], rows,
                 rata=["l"] + ["c"] * 10, fmt=[None, "0.00", "0.000", "0.000", "0.000", "0.000", None, "0.0", "0.0", "0.0", "0.0"],
                 fill=AI, beku=False)
        lf.kosong()
    sc = h["spencer_cari"]
    lf.catatan(f"Pencarian Spencer kasar (kasus a, perkuatan, 27 kandidat sekitar bidang Bishop kritis, hanya bidang yang masuk persil, kh 0): "
               f"FK Spencer minimum {idn(sc['fk'], 3)} (Bishop persil {idn(h['fk'][('a', 'perkuatan')]['persil']['bishop'], 3)}).")
    lf.catatan(f"Kasus (d): U5 pasca-likuifaksi phi = 0, su = Sr rata-rata {idn(h['sr'], 1)} kPa (lembar Kuat Residu). Dengan Sr terendah "
               f"{idn(h['sr_min'], 1)} kPa: FK Bishop persil (perkuatan) {idn(h['fk_d_srmin']['persil']['bishop'], 3)}.")
    lf.catatan("Kasus (a0) memakai muka normal +6,37 seperti LA.3 (statis), pembanding; kasus (a) muka rendah +4,00 baru. "
               "Bidang kritis diberi gambar di `Gambar/6.4 Bidang Kritis P-2.png`.")

    # ---- 5 Perkuatan
    pk = perkuatan_tabel(h)
    kb, kd = kapasitas_bor(), kapasitas_dolken()
    lq = Lembar(wb.create_sheet("Perkuatan"), 5, "Gaya geser perlu dan pilihan perkuatan", [34, 13, 11, 11, 13, 13, 13, 13, 13, 13])
    lq.catatan(ket)
    lq.kosong()
    lq.bagian("A", "Kapasitas satuan (rumus Excel hidup)")
    r0 = lq.baris
    lq.tabel(["Besaran", "Nilai", "Satuan", "Sumber"], [
        ["Diameter tiang bor D", D_BOR, "m", "[Asumsi]"],
        ["f'c", FC_BETON, "MPa", "[Asumsi: sama 6.2]"],
        ["Jarak as ke as", S_BOR, "m", "[Asumsi]"],
        ["Vc = 0,17 akar(f'c) bw d, bw = D, d = 0,8 D", f"=0.17*SQRT({lq.kol(1)}{r0 + 2})*{lq.kol(1)}{r0 + 1}*0.8*{lq.kol(1)}{r0 + 1}*1000", "kN",
         "SNI 2847:2019 Ps. 22.5.5.1 dan 22.5.2.2 (tanpa sengkang, konservatif)"],
        ["phi geser", PHI_GESER, "-", "SNI 2847:2019 Tabel 21.2.1"],
        ["phi Vc per tiang", f"={lq.kol(1)}{r0 + 4}*{lq.kol(1)}{r0 + 5}", "kN", ""],
        ["phi Vc per m lari", f"={lq.kol(1)}{r0 + 6}/{lq.kol(1)}{r0 + 3}", "kN/m", ""],
        ["Dolken: D (m)", D_DOLKEN, "m", "[Asumsi]"],
        ["Dolken: Fv sejajar serat", FV_KAYU, "MPa", "[Asumsi: kayu kelas II; belum ada di acuan/]"],
        ["Dolken: V = 0,75 Fv A (geser maks lingkaran 4V/3A)", f"=0.75*{lq.kol(1)}{r0 + 9}*PI()*{lq.kol(1)}{r0 + 8}^2/4*1000", "kN", "[Asumsi]"],
    ], rata=["l", "c", "c", "l"], fmt=[None, "0.000", None, None], fill_kolom={1: AI}, beku=False)
    adr["vc"] = f"'Perkuatan'!{lq.kol(1)}{r0 + 4}"
    adr["fvc_m"] = f"'Perkuatan'!{lq.kol(1)}{r0 + 7}"
    adr["v_dolken"] = f"'Perkuatan'!{lq.kol(1)}{r0 + 10}"
    kolom_fvc, kolom_vd = f"{lq.kol(1)}{r0 + 6}", f"{lq.kol(1)}{r0 + 10}"
    lq.kosong()
    lq.bagian("B", "Gaya geser perlu di batas lahan (bidang yang masuk persil) agar FK = FK izin")
    rows = []
    r1 = lq.baris + 1
    for i, p in enumerate(pk):
        rr = r1 + i
        rows.append([p["nama"], "Tanpa perkuatan" if p["konf"] == "tanpa" else "Berm + landai", p["izin"], round(p["fk"], 3),
                     round(p["P"], 1), f"={lq.kol(4)}{rr}/(${kolom_fvc[0]}${kolom_fvc[1:]}/${lq.kol(1)}${r0 + 3})",
                     f"=IF({lq.kol(4)}{rr}>0,${kolom_fvc[0]}${kolom_fvc[1:]}/{lq.kol(4)}{rr},\"-\")",
                     round(p["L_bor"], 1), f"={lq.kol(4)}{rr}/${kolom_vd[0]}${kolom_vd[1:]}", p["baris_dolken"]])
    lq.tabel(["Kasus", "Konfigurasi", "FK izin", "FK Bishop persil", "P perlu (kN/m)", "Tiang bor Ø600 per m (rumus)",
              "Jarak as bor perlu (m) (rumus)", "Panjang bor (m)", "Dolken Ø15 per m (rumus)", "Baris dolken (jarak 2,5 D)"], rows,
             rata=["l", "l"] + ["c"] * 8, fmt=[None, None, "0.00", "0.000", "#,##0.0", "0.00", "0.00", "0.0", "0.0", "0"],
             fill_kolom={i: AI for i in (3, 4, 7, 9)}, beku=False)
    lq.kosong()
    lq.catatan("P = (FK izin - FK) x M dorong / R pada bidang kritis yang masuk persil (rumus gaya_stabil LA.3, `la_tebing.gaya_stabil`). "
               "Panjang bor: dari +10,36 sampai (titik terdalam bidang kritis - 3 m); kasus (d) sampai U6 (-9,18) - 3 m. "
               "Hanya geser beton polos yang dicek; lentur dan lawan tanah di 6.5/6.7. Tiang bor pada P tinggi perlu jarak < 1,2 m (dua baris).")
    lq.kosong()
    lq.bagian("C", "Perbandingan pilihan perkuatan (kasus penentu: gempa dan pasca-likuifaksi)")
    pc = {(p["kode"], p["konf"]): p for p in pk}
    kritis = max(("c", "d"), key=lambda k: pc[(k, "perkuatan")]["P"])
    rows = [
        ["(i) Bronjong + pelandaian saja", f"gempa {idn(pc[('c', 'perkuatan')]['fk'], 2)}; pasca-lik {idn(pc[('d', 'perkuatan')]['fk'], 2)}",
         f"statis (a) {idn(pc[('a', 'perkuatan')]['fk'], 2)} / izin 1,5", "Tidak cukup untuk gempa dan pasca-likuifaksi (FK < 1,1)"],
        ["(ii) Baris tiang bor Ø600 di batas lahan",
         f"gempa (c): P {idn(pc[('c', 'perkuatan')]['P'], 0)} kN/m, jarak as {idn(pc[('c', 'perkuatan')]['s_bor'], 2)} m; "
         f"pasca-likuifaksi (d): P {idn(pc[('d', 'perkuatan')]['P'], 0)} kN/m, {idn(pc[('d', 'perkuatan')]['n_bor'], 1)} tiang per m",
         f"panjang ±{idn(pc[('c', 'perkuatan')]['L_bor'], 1)} m (c); ±{idn(pc[('d', 'perkuatan')]['L_bor'], 1)} m (d, sampai U6)",
         "Layak untuk (a), (b), (c') dan (c) bila jarak as ±1 m / dua baris; TIDAK layak untuk (d): perbaikan tanah U5 atau terima perpindahan (Newmark)"],
        ["(iii) Cerucuk dolken Ø15", f"{idn(pc[(kritis, 'perkuatan')]['n_dolken'], 0)} batang per m",
         f"{pc[(kritis, 'perkuatan')]['baris_dolken']} baris", "Tidak cukup: kapasitas geser tiap batang kecil, panjang terbatas [Asumsi Fv 1 MPa]"],
        ["(iv) Geser garis tiang gedung", "tidak mengubah FK tebing", "baris y 26,3 m sudah di luar jalur penyangga (y <= 25,5)",
         "Tidak menyelesaikan stabilitas tebing; hanya mengurangi gaya kinematik di 6.5"],
    ]
    lq.tabel(["Pilihan", "Hasil", "Catatan", "Kesimpulan"], rows, rata=["l"] * 4, fill=AI, beku=False)

    # ---- 6 Kuat Residu
    lr = Lembar(wb.create_sheet("Kuat Residu"), 6, "Kuat residu U5 (Idriss dan Boulanger 2008)", [10, 10, 11, 12, 10, 10, 14, 13, 13, 13])
    lr.catatan(ket)
    lr.kosong()
    lr.catatan("Sr / sigma'vo = exp(x/16 + ((x - 16)/21,2)^3 - 3,0) dengan x = (N1)60cs-Sr = (N1)60 + Delta; batas atas tan phi' U5 (33 derajat). "
               "[Literatur: Idriss dan Boulanger 2008, belum ada di acuan/]. Delta dari FC [Asumsi: bacaan grafik; FC 10 % = 1]. "
               "Bor terdekat P-2: BH-2, BH-5, BH-6.")
    lr.kosong()
    lr.bagian("A", "Uji SPT di U5 (bor terdekat P-2)")
    pool = h["pool"]
    r0 = lr.baris
    rows = []
    for i, p in enumerate(pool):
        rr = r0 + 1 + i
        k = lr.kol
        rows.append([p["bor"], round(p["z"], 2), round(p["elev"], 2), round(p["n160"], 3), round(p["fc"], 1), round(p["delta"], 2),
                     f"={k(3)}{rr}+{k(5)}{rr}",
                     f"=MIN(EXP({k(6)}{rr}/16+(({k(6)}{rr}-16)/21.2)^3-3),TAN(RADIANS(33)))", round(p["sve"], 2),
                     f"={k(7)}{rr}*{k(8)}{rr}"])
    lr.tabel(["Bor", "z (m)", "Elevasi (m)", "(N1)60", "FC (%)", "Delta", "(N1)60cs-Sr", "Sr/σ'vo", "σ'vo (kPa)", "Sr (kPa)"], rows,
             rata=["l"] + ["c"] * 9, fmt=[None, "0.00", "0.00", "0.0", "0.0", "0.00", "0.0", "0.000", "0.0", "0.0"],
             fill_kolom={i: AI for i in (1, 2, 3, 4, 5, 8)}, beku=False)
    ra, rz = r0 + 1, r0 + len(pool)
    lr.kosong()
    rr0 = lr.baris
    lr.tabel(["Besaran", "Nilai"], [["Sr rata-rata (kPa)", f"=AVERAGE({lr.kol(9)}{ra}:{lr.kol(9)}{rz})"],
                                    ["Sr terendah (kPa)", f"=MIN({lr.kol(9)}{ra}:{lr.kol(9)}{rz})"],
                                    ["Sr/σ'vo rata-rata", f"=AVERAGE({lr.kol(7)}{ra}:{lr.kol(7)}{rz})"]],
             rata=["l", "c"], fmt=[None, "0.000"], fill_kolom={1: AI}, beku=False)
    adr["sr"] = f"'Kuat Residu'!{lr.kol(1)}{rr0 + 1}"
    adr["sr_min"] = f"'Kuat Residu'!{lr.kol(1)}{rr0 + 2}"

    # ---- 7 Serakan Lateral
    ls = Lembar(wb.create_sheet("Serakan Lateral"), 7, "Serakan lateral dan profil perpindahan", [16, 14, 12, 12, 12, 12, 12, 12, 13, 14, 14, 14])
    ls.catatan(ket)
    ls.kosong()
    ls.bagian("A", "Youd, Hansen dan Bartlett (2002), muka bebas [Literatur, belum ada di acuan/]")
    ra0 = ls.baris
    k1 = ls.kol(1)
    yrows = [["Mw", lk.MW, "2.6"], ["R (km) dasar", R_DASAR, "[Asumsi: kepekaan 20/50/100/200 km]"], ["H (m)", round(geo["H"], 3), "potongan P-2"],
             ["L (m)", round(geo["L"], 2), "potongan P-2"], ["T15 (m)", round(sk["t15"], 3), "tebal U5 (N1)60 <= 15, rata-rata BH-2/5/6"],
             ["F15 (%)", round(sk["f15"], 3), "FC rata-rata uji (N1)60 <= 15"],
             ["D50,15 (mm)", round(sk["d50"], 4), f"saringan ({sk['n_d50']} contoh)"],
             ["W = 100 H/L (%)", f"=100*{k1}{ra0 + 3}/{k1}{ra0 + 4}", ""],
             ["R* = R + 10^(0,89 M - 5,64)", f"={k1}{ra0 + 2}+10^(0.89*{k1}{ra0 + 1}-5.64)", ""],
             ["log (DH + 0,01)", f"=-16.713+1.532*{k1}{ra0 + 1}-1.406*LOG10({k1}{ra0 + 9})-0.012*{k1}{ra0 + 2}+0.592*LOG10({k1}{ra0 + 8})"
                        f"+0.54*LOG10({k1}{ra0 + 5})+3.413*LOG10(100-{k1}{ra0 + 6})-0.795*LOG10({k1}{ra0 + 7}+0.1)", ""],
             ["DH Youd (m) = 10^(log) - 0,01", f"=10^{k1}{ra0 + 10}-0.01", "Youd dkk. 2002"]]
    ls.tabel(["Besaran", "Nilai", "Sumber"], yrows, rata=["l", "c", "l"], fmt=[None, "0.0000", None],
             fill_kolom={1: AI}, beku=False)
    adr["dh_youd"] = f"'Serakan Lateral'!{k1}{ra0 + 11}"
    ls.kosong()
    ls.catatan("Kepekaan R (km): " + "; ".join(f"R {int(r)} km: DH {idn(v, 2)} m" for r, v in sk["kepekaan"].items()) +
               f". Batas berlaku: W 1-20 % (W = {idn(geo['W'], 1)} %), T15 1-15 m (T15 = {idn(sk['t15'], 1)} m). Empiris: sebaran faktor ±2.")
    ls.kosong()
    ls.bagian("B", "Zhang, Robertson dan Brachman (2004), LDI per irisan 0,5 m [Literatur, belum ada di acuan/]")
    rb0 = ls.baris
    n = len(sk["dz"])
    first, last = rb0 + 1, rb0 + n
    c = ls.kol
    rows = []
    for i in range(n):
        rr = first + i
        rows.append([round(float(sk["e"][i]), 2), round(float(sk["e"][i + 1]), 2), f"={c(0)}{rr}-{c(1)}{rr}",
                     round(float(sk["fs"][i]), 4), round(float(sk["n160cs"][i]), 3), f"=SQRT(MIN({c(4)}{rr},46)/46)",
                     f"=0.032+4.7*{c(5)}{rr}-6*{c(5)}{rr}^2", f"=MAX(0,1.859*(1.1-{c(5)}{rr})^3)",
                     f"=IF({c(3)}{rr}>=2,0,IF({c(3)}{rr}<={c(6)}{rr},{c(7)}{rr},MIN({c(7)}{rr},0.035*(1-{c(6)}{rr})*(2-{c(3)}{rr})/({c(3)}{rr}-{c(6)}{rr}))))",
                     f"={c(8)}{rr}*{c(2)}{rr}", f"=SUM({c(9)}{rr}:{c(9)}${last})", None])
    ls.tabel(["Elevasi atas (m)", "Elevasi bawah (m)", "dz (m)", "FS", "(N1)60cs", "Dr", "Fα", "γlim", "γmax", "γmax dz (m)",
              "∫ dari dasar U5 (m)", "u di tepi atas (m)"], rows, rata=["c"] * 12,
             fmt=["0.00", "0.00", "0.00", "0.000", "0.00", "0.000", "0.000", "0.000", "0.0000", "0.0000", "0.0000", "0.000"],
             fill_kolom={0: AI, 1: AI, 3: AI, 4: AI}, beku=False)
    rc = ls.baris
    ls.tabel(["Besaran", "Nilai"], [["LDI (m)", f"=SUM({c(9)}{first}:{c(9)}{last})"], ["L/H", f"={k1}{ra0 + 4}/{k1}{ra0 + 3}"],
                                    ["DH Zhang (m) = 6 (L/H)^-0,8 LDI", f"=6*{c(1)}{rc + 2}^-0.8*{c(1)}{rc + 1}"]],
             rata=["l", "c"], fmt=[None, "0.0000"], fill_kolom={1: AI}, beku=False)
    adr["ldi"] = f"'Serakan Lateral'!{c(1)}{rc + 1}"
    adr["dh_zhang"] = f"'Serakan Lateral'!{c(1)}{rc + 3}"
    dhz = f"{c(1)}{rc + 3}"
    ldi = f"{c(1)}{rc + 1}"
    for i in range(n):          # kolom u di tepi atas irisan (rumus mengacu DH dan LDI di atas)
        rr = first + i
        ls.ws[f"{c(11)}{rr}"] = f"={dhz}*{c(10)}{rr}/{ldi}"
        ls.ws[f"{c(11)}{rr}"].number_format = "0.000"
    ls.kosong()
    ls.bagian("C", "Profil perpindahan lateral di garis tiang x = -26,3 m (beban kinematik untuk 6.5)")
    ls.catatan("u(z) = DH Zhang x (∫ γmax dz dari dasar U5 sampai z) / LDI. Di atas U5 (U4, U2, urugan) bergerak kaku = DH; U6 nol.")
    node = profil_node(sk)
    rp0 = ls.baris
    rows = []
    for i, (e, lap, u) in enumerate(node):
        if lap == "U5":
            j = int(np.argmin(np.abs(sk["e"][1:-1] - e))) + 1     # baris irisan dengan tepi atas = e
            f = f"={c(11)}{first + j}"
        elif lap.startswith("Dasar") or lap == "U6":
            f = 0
        else:
            f = f"={dhz}"
        rows.append([round(e, 2), lap, f])
    ls.tabel(["Elevasi (m)", "Lapisan", "u (m)"], rows, rata=["c", "l", "c"], fmt=["0.00", None, "0.000"], fill_kolom={2: AI}, beku=False)
    ls.kosong()
    ls.bagian("D", "Kepekaan bor")
    rows = [["Rata-rata BH-2/5/6 (dasar)", round(sk["ldi"], 3), round(sk["dh_zhang"], 3), round(sk["dh_youd"], 3), round(sk["t15"], 2)]]
    for b, v in h["sk_bor"].items():
        rows.append([b, round(v["ldi"], 3), round(v["dh_zhang"], 3), round(v["dh_youd"], 3), round(v["t15"], 2)])
    ls.tabel(["Bor", "LDI (m)", "DH Zhang (m)", "DH Youd (m)", "T15 (m)"], rows, rata=["l"] + ["c"] * 4,
             fmt=[None, "0.000", "0.000", "0.000", "0.00"], fill=AI, beku=False)

    # ---- 8 Cek Silang
    lc = Lembar(wb.create_sheet("Cek Silang"), 8, "Cek silang (T-102)", [38, 16, 16, 14, 14, 34])
    lc.catatan(ket)
    lc.kosong()
    lc.bagian("A", "Bishop vs Spencer pada bidang kritis yang sama (toleransi ≤ 5 %)")
    rows = []
    for konf in ("tanpa", "perkuatan"):
        for ks in ks_list:
            for nm in ("semua", "persil"):
                a = h["fk"][(ks["kode"], konf)][nm]
                if nm == "persil" and a["bidang"] == h["fk"][(ks["kode"], konf)]["semua"]["bidang"]:
                    continue
                if np.isfinite(a["spencer"]):
                    rows.append([f"{ks['nama']} ({konf}, {nm})", round(a["bishop"], 3), round(a["spencer"], 3),
                                 round((a["spencer"] - a["bishop"]) / a["bishop"] * 100, 2), None, None])
    lc.tabel(["Kasus", "Bishop", "Spencer", "Selisih (%)", "", ""], rows, rata=["l", "c", "c", "c", "c", "c"],
             fmt=[None, "0.000", "0.000", "0.00", None, None], fill=AI, beku=False)
    lc.kosong()
    lc.bagian("B", "pyslope (Bishop) vs skrip pada lingkaran yang sama (toleransi ≤ 2 %)")
    rows = [[f"x {idn(p['lingkaran'][0], 2)}; y {idn(p['lingkaran'][1], 2)}; R {idn(p['lingkaran'][2], 2)}", round(p["pyslope"], 4),
             round(p["skrip"], 4), round(p["selisih"], 3), None, None] for p in h["pyslope"]]
    lc.tabel(["Lingkaran (lereng 6 m, 30 derajat, 2 lapis c-phi)", "pyslope", "Skrip", "Selisih (%)", "", ""], rows,
             rata=["l", "c", "c", "c", "c", "c"], fmt=[None, "0.0000", "0.0000", "0.000", None, None], fill=AI, beku=False)
    lc.kosong()
    lc.bagian("C", "Youd vs Zhang (sebaran empiris; dilaporkan, faktor ≤ 2)")
    rows = [[f"DH Youd R {int(R_DASAR)} km (m)", round(sk["dh_youd"], 3)], ["DH Zhang (m)", round(sk["dh_zhang"], 3)],
            ["Rasio Zhang/Youd", round(sk["dh_zhang"] / sk["dh_youd"], 2)]]
    lc.tabel(["Besaran", "Nilai"], rows, rata=["l", "c"], fmt=[None, "0.00"], fill=AI, beku=False)
    lc.kosong()
    lc.catatan("GeoFEM3D tidak dipakai: aplikasi hanya fondasi pada tanah datar berlapis horizontal dan belum memodelkan lereng. "
               "Cek silang kedua memakai Spencer dan pyslope (Bishop) pada kasus sederhana.")

    # ---- 9 Kesimpulan
    lk_ = Lembar(wb.create_sheet("Kesimpulan"), 9, "Kesimpulan dan keputusan", [28, 110])
    lk_.catatan(ket)
    lk_.kosong()
    lk_.bagian("A", "Hasil")
    lk_.tabel(["Butir", "Isi"], [[a, b] for a, b in kesimpulan_teks(h, pk)], rata=["l", "l"], beku=False)
    lk_.kosong()
    lk_.bagian("B", "Hal yang perlu diputuskan Defsa")
    lk_.tabel(["No", "Keputusan"], [[i, t] for i, t in enumerate(KEPUTUSAN, 1)], rata=["c", "l"], beku=False)
    for ws in wb:
        ws.freeze_panes = "A5"   # judul lembar tetap terlihat
    wb.save(keluar)
    return keluar, adr


KEPUTUSAN = [
    "KEPUTUSAN DEFSA 21 Nov 2026: draf 6.4 disetujui; profil serakan lateral Zhang dkk. (2004) dipakai sebagai beban "
    "kinematik 6.5, Youd dkk. (2002) sebagai batas bawah.",
    "Acuan serakan lateral dan kuat residu (Youd 2002, Zhang 2004, Idriss-Boulanger 2008) belum ada di acuan/: tambahkan PDF atau terima label [Literatur].",
    "Jarak sumber R (kepekaan 50/100/200 km) adalah asumsi; tentukan R dari deagregasi PuSGeN bila ingin satu nilai.",
    "Pilih perkuatan batas lahan: tiang bor Ø600 (dua baris) atau turap; dolken tidak cukup. Biaya kasar tidak dihitung.",
    "FK izin pasca-likuifaksi 1,1 adalah asumsi (SNI 8460 hal. 277 untuk fondasi).",
    "kh 50 % (c') hanya sah bila perpindahan 25-50 mm diizinkan (Ps. 12.2.5 b.3); perlu analisis Newmark bila dipakai.",
]


def kesimpulan_teks(h, pk):
    fk = h["fk"]
    sk = h["sk"]
    f = lambda k, c, j="persil": fk[(k, c)][j]["bishop"]
    pc = {(p["kode"], p["konf"]): p for p in pk}
    return [
        ["FK Bishop persil, perkuatan LA.3",
         f"(a) {idn(f('a', 'perkuatan'), 2)} / 1,5; (b) {idn(f('b', 'perkuatan'), 2)} / 1,25; (c) {idn(f('c', 'perkuatan'), 2)} / 1,1; "
         f"(c') {idn(f('c2', 'perkuatan'), 2)} / 1,1; (d) {idn(f('d', 'perkuatan'), 2)} / 1,1."],
        ["Gaya geser perlu (berm + landai)",
         f"(a) {idn(pc[('a', 'perkuatan')]['P'], 0)}; (b) {idn(pc[('b', 'perkuatan')]['P'], 0)}; (c) {idn(pc[('c', 'perkuatan')]['P'], 0)}; "
         f"(c') {idn(pc[('c2', 'perkuatan')]['P'], 0)}; (d) {idn(pc[('d', 'perkuatan')]['P'], 0)} kN/m."],
        ["Perkuatan disarankan",
         f"Berm + pelandaian (LA.3) ditambah baris tiang bor Ø600 di batas lahan untuk (a), (b), (c'), (c) (jarak as ±{idn(pc[('c', 'perkuatan')]['s_bor'], 1)} m untuk (c)); "
         f"(d) pasca-likuifaksi FK {idn(f('d', 'perkuatan'), 2)} perlu perbaikan tanah U5 (tiang tidak cukup); dolken tidak cukup; geser garis tiang gedung tidak membantu."],
        ["Sr U5", f"{idn(h['sr'], 1)} kPa rata-rata (Sr/σ'vo {idn(h['ratio'], 3)}); terendah {idn(h['sr_min'], 1)} kPa."],
        ["Serakan lateral di garis tiang",
         f"DH Youd {idn(sk['dh_youd'], 2)} m (R {int(R_DASAR)} km); DH Zhang {idn(sk['dh_zhang'], 2)} m (LDI {idn(sk['ldi'], 2)} m)."],
    ]


# ------------------------------------------------------------------ verifikasi T-102
def t102(berkas=BERKAS, adr=None, h=None):
    h = h or semua()
    sel = [(abs(a["spencer"] - a["bishop"]) / a["bishop"] * 100, f"{k[0]} {k[1]} {nm}") for k, v in h["fk"].items()
           for nm, a in (("semua", v["semua"]), ("persil", v["persil"])) if np.isfinite(a["spencer"])]
    dbs, kasus_dbs = max(sel)
    dpy = max(p["selisih"] for p in h["pyslope"])
    sk = h["sk"]
    faktor = max(sk["dh_zhang"], sk["dh_youd"]) / min(sk["dh_zhang"], sk["dh_youd"])
    r = dict(dbs=dbs, kasus_dbs=kasus_dbs, dpy=dpy, faktor=faktor, dxl=None)
    if adr:
        import openpyxl
        wb = openpyxl.load_workbook(berkas, data_only=True)

        def baca(a):
            sh, cel = a.split("!")
            return wb[sh.strip("'")][cel].value
        py = {"sr": h["sr"], "sr_min": h["sr_min"], "dh_youd": sk["dh_youd"], "ldi": sk["ldi"], "dh_zhang": sk["dh_zhang"],
              "fvc_m": kapasitas_bor()["per_m"], "vc": kapasitas_bor()["vc"], "v_dolken": kapasitas_dolken()["v"]}
        try:
            ds = [abs(float(baca(adr[k])) - py[k]) / py[k] * 100 for k in py]
            r["dxl"] = max(ds)
        except (TypeError, ValueError):
            r["dxl"] = None
    r["lolos"] = dbs <= TOL["bishop_spencer"] and dpy <= TOL["pyslope"] and (r["dxl"] is not None and r["dxl"] <= TOL["excel"])
    return r


def catat_t102(r=None, h=None, berkas=VERIFIKASI):
    h = h or semua()
    r = r or t102(h=h)
    sk = h["sk"]
    dxl = idn(r["dxl"], 4) if r["dxl"] is not None else "tidak dihitung"
    baris = ("| T-102 | Cek silang 6.4 stabilitas tebing P-2 (Bishop, Spencer, perkuatan), kuat residu U5 (Idriss-Boulanger 2008), serakan lateral "
             "(Youd 2002, Zhang 2004) | (a) Bishop vs Spencer pada bidang kritis yang sama, 6 kasus x 2 konfigurasi x (semua, persil), selisih terbesar "
             f"{idn(r['dbs'], 2)} % (kasus {r['kasus_dbs']}); (b) pyslope (Bishop) vs skrip pada 3 lingkaran sama (lereng 6 m, 30 derajat, 2 lapis c-phi), selisih terbesar "
             f"{idn(r['dpy'], 2)} % | (c) rumus Excel hidup (Kuat Residu, Serakan Lateral, Perkuatan) vs Python, selisih terbesar {dxl} %; "
             f"(d) DH Youd {idn(sk['dh_youd'], 2)} m vs Zhang {idn(sk['dh_zhang'], 2)} m (R {int(R_DASAR)} km [Asumsi]): faktor {idn(r['faktor'], 2)} (dilaporkan, empiris; "
             f"<= 2 {'terpenuhi' if r['faktor'] <= TOL['youd_zhang'] else 'tidak terpenuhi'}) "
             "| (a) <= 5 %; (b) <= 2 %; (c) <= 0,1 %; (d) faktor <= 2 (dilaporkan) | "
             f"{'Lolos' if r['lolos'] else 'GAGAL'}, {STATUS} | `skrip/tahap6_tebing.py`, `tests/test_tahap6_tebing.py` | Ditetapkan sebelum membandingkan. "
             "Data simulasi. GeoFEM3D tidak dipakai (belum bisa lereng). Acuan Youd/Zhang/Idriss-Boulanger/Spencer belum ada di acuan/. "
             + ("" if r["dbs"] <= TOL["bishop_spencer"] else f"(a) melewati 5 % hanya di {r['kasus_dbs']}: Spencer lebih tinggi dari Bishop (Bishop konservatif); bidang tak-lingkaran (licin) dengan kh. ")
             + "|")
    teks = Path(berkas).read_text(encoding="utf-8").split("\n")
    teks = [ln for ln in teks if not ln.startswith("| T-102 |")]
    i = next(k for k, ln in enumerate(teks) if ln.startswith("| T-101 |"))
    teks.insert(i + 1, baris)
    Path(berkas).write_text("\n".join(teks), encoding="utf-8")
    return baris


# ------------------------------------------------------------------ Markdown
def tulis_md(keluar=MD, h=None, r=None):
    h = h or semua()
    r = r or t102(h=h)
    pk = perkuatan_tabel(h)
    sk, geo = h["sk"], h["sk"]["geo"]
    ks_list = kasus()
    kb, kd = kapasitas_bor(), kapasitas_dolken()
    pc = {(p["kode"], p["konf"]): p for p in pk}
    L = [f"# 6.4 Stabilitas tebing P-2 dan serakan lateral ({STATUS}, 21 Nov 2026)\n",
         "DATA SIMULASI. Disusun AI atas permintaan Defsa; kunci jawaban tidak dibuka. Rincian di `6.4 Stabilitas Tebing.xlsx` "
         "(`skrip/tahap6_tebing.py`, uji `tests/test_tahap6_tebing.py`), gambar di `Gambar/6.4 Profil Serakan Lateral.png` dan `6.4 Bidang Kritis P-2.png`.\n",
         "## Metode\n",
         f"- Geometri, bahan, bidang licin, beban, berm bronjong + pelandaian 1V:2H dari `la_tebing.py` (LA.3, disetujui); k su lempung {idn(K_SU[0], 2)}, bidang licin "
         f"{idn(K_SU[1], 2)} (analisis balik LA.3). Puncak P-2 {idn(lt.X_PUNCAK_P2, 1)} m dari batas lahan.",
         "- FK Bishop dari pencarian `la_tebing.cari`; Spencer (1967, gaya antar-irisan sejajar, FK momen = FK gaya) di bidang kritis Bishop yang sama "
         "[Literatur: Spencer 1967, belum ada di acuan/]. 'Persil' = bidang yang ujung daratnya masuk persil (x <= 0).",
         "- FK izin SNI 8460:2017: statis 1,5 (Ps. 7.5.5 Tabel 25 hal. 134); surut 1,25 (Tabel 25 [Asumsi]); gempa 1,1 (Ps. 7.5.1.1 hal. 133); "
         "kh = 0,5 amax = 0,171 (Ps. 12.2.7 hal. 279); kh 50 % bila perpindahan 25-50 mm diizinkan (Ps. 12.2.5 b.3 hal. 278); "
         "pasca-likuifaksi 1,1 [Asumsi: hal. 277].\n",
         "## FK tebing P-2 (Bishop / Spencer)\n",
         "| Kasus | FK izin | Tanpa: semua | Tanpa: persil | Perkuatan: semua | Perkuatan: persil | Persil memenuhi? |", "|---|---|---|---|---|---|---|"]
    for ks in ks_list:
        t, p = h["fk"][(ks["kode"], "tanpa")], h["fk"][(ks["kode"], "perkuatan")]
        fm = lambda d: f"{idn(d['bishop'], 2)} / {idn(d['spencer'], 2)}"
        L.append(f"| {ks['nama']} | {idn(ks['izin'], 2)} | {fm(t['semua'])} | {fm(t['persil'])} | {fm(p['semua'])} | {fm(p['persil'])} | "
                 f"{'Ya' if p['persil']['bishop'] >= ks['izin'] else 'Tidak'} |")
    L.append("\nKasus (a0) = statis muka normal +6,37 seperti LA.3 (pembanding); (a) muka rendah +4,00 kasus baru. "
             f"Spencer kasar (a, perkuatan, 27 kandidat): FK {idn(h['spencer_cari']['fk'], 2)}.\n")
    L.append("## Gaya geser perlu di batas lahan dan perkuatan\n")
    L.append("P = (FK izin - FK) x M dorong / R pada bidang yang masuk persil (cara `gaya_stabil` LA.3).\n")
    L.append("| Kasus | P tanpa perkuatan (kN/m) | P dengan berm + landai (kN/m) | Tiang bor Ø600 per m | Jarak as bor (m) | Panjang bor (m) | Dolken Ø15 per m |")
    L.append("|---|---|---|---|---|---|---|")
    for ks in ks_list:
        a, b = pc[(ks["kode"], "tanpa")], pc[(ks["kode"], "perkuatan")]
        L.append(f"| {ks['nama']} | {idn(a['P'], 0)} | {idn(b['P'], 0)} | {idn(b['n_bor'], 2)} | "
                 f"{idn(b['s_bor'], 2) if b['s_bor'] else '-'} | {idn(b['L_bor'], 1)} | {idn(b['n_dolken'], 1)} |")
    L.append(f"\nKapasitas: tiang bor Ø600 f'c 30 (beton polos) Vc = 0,17 akar(f'c) bw d = {idn(kb['vc'], 0)} kN (SNI 2847:2019 Ps. 22.5.5.1; bw = D, d = 0,8 D Ps. 22.5.2.2), "
             f"phi Vc = {idn(kb['fvc'], 0)} kN per tiang, {idn(kb['per_m'], 0)} kN/m pada jarak 1,2 m [Asumsi]. Dolken Ø15 geser {idn(kd['v'], 1)} kN per batang "
             "[Asumsi Fv 1 MPa, belum ada di acuan/]. Lentur dan lawan tanah dicek di 6.5/6.7.\n")
    L.append("| Pilihan | Hasil |\n|---|---|")
    L.append(f"| (i) Bronjong + pelandaian saja | gempa FK {idn(pc[('c', 'perkuatan')]['fk'], 2)}, pasca-likuifaksi {idn(pc[('d', 'perkuatan')]['fk'], 2)}: tidak cukup |")
    L.append(f"| (ii) Baris tiang bor Ø600 di batas lahan | gempa (c): jarak as {idn(pc[('c', 'perkuatan')]['s_bor'], 2)} m (P {idn(pc[('c', 'perkuatan')]['P'], 0)} kN/m), "
             f"layak (dua baris / rapat); pasca-likuifaksi (d): P {idn(pc[('d', 'perkuatan')]['P'], 0)} kN/m = {idn(pc[('d', 'perkuatan')]['n_bor'], 1)} tiang per m, tidak layak "
             "(perlu perbaikan tanah U5 atau terima perpindahan lewat analisis Newmark) |")
    L.append("| (iii) Cerucuk dolken Ø15 | tidak cukup: puluhan batang per meter, panjang terbatas |")
    L.append("| (iv) Geser garis tiang gedung | tidak menyelesaikan stabilitas tebing: baris y 26,3 m sudah di luar jalur penyangga (y <= 25,5 m) |")
    L.append("\nBiaya kasar tidak dihitung (opsional, tanpa harga satuan di acuan).\n")
    L.append("## Inklinometer\n")
    for inc in ("INC-1", "INC-2"):
        v = h["inc"][inc]
        L.append(f"- {inc}: puncak {idn(v['atas_mei'], 1)} mm (15 Mei) ke {idn(v['atas'], 1)} mm ({v['tgl']}), laju {idn(v['laju'], 3)} mm/hari; "
                 f"gradien terbesar {idn(v['gradien'], 2)} mm/m di elevasi {idn(v['elev_geser'], 2)} m.")
    y_bid = y_bidang(h["fk"][("a", "tanpa")]["persil"]["bidang"], -2.0)
    L.append(f"- Bidang licin LA.3 +5,43 (menerus di x = -2 m); bidang kritis (a, tanpa perkuatan, persil) "
             f"{'di x = -2 m pada ' + sg(y_bid) + ' m' if y_bid is not None else 'berujung di x = ' + idn(h['fk'][('a', 'tanpa')]['persil']['x1'], 1) + ' m, tidak mencapai x = -2 m'}. Zona geser INC-1 "
             f"{'cocok' if abs(h['inc']['INC-1']['elev_geser'] - 5.43) <= 1.0 else 'tidak cocok'} dengan bidang licin.\n")
    L.append("## Kuat residu U5\n")
    L.append(f"Idriss dan Boulanger (2008) [Literatur, belum ada di acuan/]: Sr/σ'vo = exp(x/16 + ((x - 16)/21,2)^3 - 3,0) dengan x = (N1)60 + Delta, "
             f"batas tan phi' = {idn(TAN_PHI_U5, 3)}. Bor BH-2, BH-5, BH-6 ({len(h['pool'])} uji): Sr/σ'vo rata-rata {idn(h['ratio'], 3)}, "
             f"Sr rata-rata {idn(h['sr'], 1)} kPa (terendah {idn(h['sr_min'], 1)}, tertinggi {idn(h['sr_maks'], 1)}). Dipakai su = Sr, phi = 0 (kasus d).\n")
    L.append("## Serakan lateral di garis tiang (x = -26,3 m)\n")
    L.append(f"- H = {idn(geo['H'], 1)} m, L = {idn(geo['L'], 1)} m, W = {idn(geo['W'], 1)} %, L/H = {idn(geo['LH'], 2)}; Mw {idn(lk.MW, 1)}; "
             f"T15 = {idn(sk['t15'], 1)} m, F15 = {idn(sk['f15'], 1)} %, D50,15 = {idn(sk['d50'], 3)} mm ({sk['n_d50']} contoh saringan).")
    L.append(f"- Youd dkk. (2002) [Literatur, belum ada di acuan/]: DH = {idn(sk['dh_youd'], 2)} m (R {int(R_DASAR)} km [Asumsi]); kepekaan " +
             "; ".join(f"R {int(r_)} km: {idn(v, 2)} m" for r_, v in sk["kepekaan"].items()) + ". Empiris, sebaran faktor ±2.")
    L.append(f"- Zhang dkk. (2004) [Literatur, belum ada di acuan/]: LDI = {idn(sk['ldi'], 2)} m, DH = 6 (L/H)^-0,8 LDI = {idn(sk['dh_zhang'], 2)} m. "
             f"Kepekaan bor: BH-5 {idn(h['sk_bor']['BH-5']['dh_zhang'], 2)} m, BH-6 {idn(h['sk_bor']['BH-6']['dh_zhang'], 2)} m.")
    L.append("- Profil u(z) (beban kinematik untuk 6.5): " + "; ".join(f"{sg(e)} m: {idn(u, 2)} m" for e, _, u in profil_node(sk)
                                                                         if e in (ELEV_TIANG_ATAS, 1.01, -2.0, -4.5, -9.18, -12.0) or abs(e - round(e)) < 1e-9 and e in (-2.0, -4.0, -6.0, -8.0)) + ".\n")
    L.append("## Verifikasi T-102\n")
    L.append(f"Toleransi ditetapkan dulu: Bishop vs Spencer <= 5 %; pyslope vs skrip <= 2 %; Excel = Python <= 0,1 %; Youd vs Zhang faktor <= 2 (dilaporkan). Hasil: "
             f"(a) {idn(r['dbs'], 2)} % (kasus {r['kasus_dbs']}); (b) {idn(r['dpy'], 2)} %; (c) {idn(r['dxl'], 4) if r['dxl'] is not None else '-'} %; (d) faktor {idn(r['faktor'], 2)}. "
             f"Lolos: {'ya' if r['lolos'] else 'TIDAK'}" + ("" if r["dbs"] <= TOL["bishop_spencer"] else
             f" ((a) melewati 5 % hanya di {r['kasus_dbs']}: Spencer lebih tinggi dari Bishop, jadi Bishop konservatif; bidang tak-lingkaran dengan kh)") + f". GeoFEM3D tidak dipakai (hanya fondasi pada tanah datar, belum bisa lereng).\n")
    L.append("## Hal yang perlu diputuskan Defsa\n")
    for i, k in enumerate(KEPUTUSAN, 1):
        L.append(f"{i}. {k}")
    L.append(f"\nStatus: {STATUS}.\n")
    Path(keluar).write_text("\n".join(L), encoding="utf-8")
    return keluar


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from format_dokumen import hitung_ulang_excel
    h = semua()
    for k, v in h["fk"].items():
        print(k, round(v["semua"]["bishop"], 3), round(v["semua"]["spencer"], 3), round(v["persil"]["bishop"], 3),
              round(v["persil"]["spencer"], 3), round(v["persil"].get("P", 0), 1))
    gambar(h)
    berkas, adr = buat_excel(h=h)
    print(berkas, hitung_ulang_excel(berkas))
    r = t102(berkas, adr, h)
    print(r)
    print(catat_t102(r, h))
    print(tulis_md(h=h, r=r))


if __name__ == "__main__":
    main()
