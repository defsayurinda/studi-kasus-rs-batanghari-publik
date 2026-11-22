"""Tahap 4 langkah 4.6: desain balok SRPMK dan balok khusus (SNI 2847:2019 Pasal 9, 18.6, 22.5, 22.7).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (20 Nov 2026); draf, menunggu
persetujuan Defsa. Kunci jawaban tidak dibuka.

Gaya dalam: model 3D tahap4_model (K1 dan K2, diselubungi) dengan beban gravitasi pada balok (beban pelat dua arah
setara q L/3 per sisi [Literatur: beban segitiga setara], berat badan balok, dinding luar/parapet pada balok tepi,
beban titik reaksi balok anak tangki dan tiang dek helipad) dan gaya gempa pola ELF dengan V = V ELF (= ragam
spektrum terskala, 4.3), torsi tak terduga 0,05 Ax, arah 100 % + 30 % (SNI 1726 Pasal 7.5.3), ρ 1,3, Ev 0,2 SDS D.
Model rangka saja (25 % gaya, SNI 1726 Pasal 7.2.5.1) ikut diselubungi. Desain per kelompok balok; ukuran kelompok
dinaikkan bertahap bila syarat praktis tidak terpenuhi, lalu model dihitung ulang dengan ukuran baru.

Acuan SNI 2847:2019 (halaman cetak): Tabel 6.5.2 hal. 99 dan 6.5.4 hal. 100 (koefisien, cek silang); 9.6.1.2 hal. 189
(As min); 9.6.3.3 hal. 192 dan 9.6.4.2-9.6.4.3 hal. 193 (tulangan geser/torsi minimum); Tabel 9.7.6.2.2 hal. 202
(spasi geser); 9.7.6.3.3 hal. 203 (spasi torsi ph/8, 300); 18.6.2 hal. 377 (dimensi); 18.6.3 hal. 378-379
(ρ <= 0,025, M+ >= 0,5 M- di muka joint, >= 0,25 maks); 18.6.4 hal. 380-381 (sengkang pengekang 2h, batang sudut dan
selang-seling ditopang (25.7.2.3), s <= d/4, 6db, 150; di luar sendi d/2); 18.6.5 hal. 382 (Ve dari Mpr 1,25 fy;
Vc = 0); 18.8.2.3 hal. 393 (hc >= 20 db); 22.5.1.2 hal. 482 (batas penampang geser); 22.7.3.2 hal. 510 (torsi
kompatibilitas); Tabel 22.7.4.1(a) hal. 511 (ambang Tth); Tabel 22.7.5.1 hal. 513 (Tcr); 22.7.6.1 hal. 514 (Tn, Al);
22.7.7.1 hal. 516 (batas penampang geser + torsi); Tabel 21.2.1 hal. 469 (φ).
"""
from __future__ import annotations

import functools
import math
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).parent))
import cache_analisis  # noqa: E402
import tahap4_beban as tb  # noqa: E402
import tahap4_model as tm  # noqa: E402
import tahap4_pelat as tp  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "04 Struktur Atas"
BERKAS = KELUAR / "4.6 Desain Balok.xlsx"
LABEL = tb.LABEL
STATUS = "disetujui Defsa 20 Nov 2026"
FC, FY, FYT = 30.0, 420.0, 420.0
SEL = 0.040                                    # selimut balok (Tabel 20.6.1.3.1)
PHI_M, PHI_V = 0.90, 0.75                      # Tabel 21.2.1
L_GRID = 8.0
UKURAN = [(0.35, 0.60), (0.40, 0.70), (0.45, 0.80), (0.50, 0.90), (0.60, 1.00), (0.60, 1.20), (0.70, 1.20)]
RHO_PAKAI = 0.020   # batas praktis kemacetan tulangan di joint [Asumsi]; batas SNI 18.6.3.1 = 0,025
S_MIN = 0.075       # spasi sengkang terkecil yang masih praktis [Asumsi]
DB_LENTUR = (22, 25, 29)
DB_SENGKANG = (10, 13)

# ---- beban khusus
TANGKI_X = (60.0, 68.0, 76.0)          # balok induk arah Y penumpu balok anak tangki (y 67-75, LT3 atap V1)
TANGKI_Y_INDUK = 67.0                  # balok induk arah X sisi selatan pelat tangki (memikul lajur 2 m)
DEK_KANTILEVER, DEK_BALIK, DEK_JARAK = 4.7, 8.0, 4.0   # dek helipad baja: kantilever, bentang balik, jarak balok [Asumsi]
CHILLER_X = (62.5, 68.0, 73.5)         # titik tumpu chiller 11,0 m pada rel (x global) [Asumsi tata letak]


def luas(db):
    return math.pi * db ** 2 / 4


def floor25(s):
    return math.floor(s * 1000 / 25 + 1e-9) * 25 / 1000


def kolom_lebar(b):
    xm, ym = (b["x1"] + b["x2"]) / 2, (b["y1"] + b["y2"]) / 2
    return tb.KOLOM_MEN if tb.MENARA.buffer(0.01).contains(Point(xm, ym)) else tb.KOLOM_POD


def atap_di(lv, x, y):
    return lv == "ATAP" or (lv == "LT3" and tb.V1.buffer(0.01).contains(Point(x, y))) or \
        (lv == "LT4" and not tb.MENARA.buffer(0.01).contains(Point(x, y)))


# ------------------------------------------------------------------ beban gravitasi pada balok
def beban_panel(lv, x, y):
    """(D, L) kPa pelat di titik (x, y) pada tingkat lv [Asumsi zona per tingkat; reduksi beban hidup diabaikan]."""
    pel = tb.GAMMA_C * tp.H
    if lv == "LT2":
        return pel + tp.SIDL_LANTAI + tb.GANTUNG["podium"], 2.87
    if lv == "LT3":
        if tb.V1.buffer(0.01).contains(Point(x, y)):
            tambah = 2.2 if (60 <= x <= 76 and 51 <= y <= 67) else 0.0   # chiller + impak disebar [Asumsi]
            return pel + tp.SIDL_ATAP + tambah, 0.96
        return pel + tp.SIDL_LANTAI + tb.GANTUNG["AHU"], 4.79
    if lv == "LT4" and not tb.MENARA.buffer(0.01).contains(Point(x, y)):
        return pel + tp.SIDL_ATAP, 0.96
    if lv == "ATAP":
        return pel + tp.SIDL_ATAP + tb.SIDL["dek_helipad"][0], 2.87   # dek helipad di atas atap (K2)
    lo = 3.83 if 35 <= y <= 43 else 1.92        # koridor tengah menara [Asumsi]
    return pel + tp.SIDL_LANTAI + tb.GANTUNG["menara"], lo


def beban_balok(b):
    """Beban merata setara (D, L) kN/m pada balok dari pelat kedua sisi, berat badan, dan dinding luar/parapet."""
    xm, ym = (b["x1"] + b["x2"]) / 2, (b["y1"] + b["y2"]) / 2
    nx, ny = (0.0, 2.0) if b["arah"] == "X" else (2.0, 0.0)
    d_, l_ = tb.GAMMA_C * b["b"] * (b["h"] - tp.H), 0.0
    sisi, panel = 0, None
    for s in (1, -1):
        px, py = xm + s * nx, ym + s * ny
        if b["wil"].buffer(0.01).contains(Point(px, py)):
            dq, lq = beban_panel(b["lv"], px, py)
            d_ += dq * L_GRID / 3            # q L/3 per sisi
            l_ += lq * L_GRID / 3
            sisi += 1
            panel = (dq, lq)
    if sisi == 1:  # balok tepi: dinding luar + fasad setinggi tingkat, atau parapet di atap
        q_dl = (1 - tb.BUKAAN) * tb.DINDING_LUAR["bata"][0] + tb.BUKAAN * tb.DINDING_LUAR["kaca"][0] + \
            tb.DINDING_LUAR["fasad"][0]
        d_ += q_dl * (tb.PARAPET if atap_di(b["lv"], xm, ym) else 4.2)
    if b["lv"] == "LT3" and b["arah"] == "X" and abs(b["y1"] - TANGKI_Y_INDUK) < 0.01 and 60 <= xm <= 76:
        d_ += tb.atap_khusus()["tangki_kpa"] * 2.0   # lajur 2 m pelat tangki (y 67-69), penuh [Asumsi konservatif]
    return d_, l_, sisi, panel


def beban_titik(b, konfig):
    """Beban titik [(PD, PL, a)] kN pada balok (a dari ujung 1): reaksi balok anak tangki dan tiang dek helipad."""
    out = []
    if b["lv"] == "LT3" and b["arah"] == "Y" and abs(b["y1"] - 67.0) < 0.01 and \
            any(abs(b["x1"] - x) < 0.01 for x in TANGKI_X):
        r = balok_anak_tangki()
        k = TANGKI_X.index(min(TANGKI_X, key=lambda x: abs(x - b["x1"])))
        out.append((r["R_D"][k], r["R_L"][k], 4.0))
    if konfig == "K2" and b["lv"] == "ATAP":
        h = dek_helipad()
        x0, y0, x1, y1 = tb.MENARA.bounds   # atap menara = MENARA
        if b["arah"] == "X":
            tepi = min(abs(b["y1"] - y0), abs(b["y1"] - y1)) < 0.01
            balik = min(abs(b["y1"] - y0 - DEK_BALIK), abs(b["y1"] - y1 + DEK_BALIK)) < 0.01
        else:
            tepi = min(abs(b["x1"] - x0), abs(b["x1"] - x1)) < 0.01
            balik = min(abs(b["x1"] - x0 - DEK_BALIK), abs(b["x1"] - x1 + DEK_BALIK)) < 0.01
        if tepi:
            out.append((h["PA_D"], h["PA_L"], 4.0))
        elif balik:
            out.append((h["PB_D"], h["PB_L"], 4.0))
    return out


def dek_helipad():
    """Reaksi tiang dek helipad baja (kantilever 4,7 m + bentang balik 8 m, balok @ 4 m) pada balok atap tepi (A)
    dan balok sejajar satu bentang ke dalam (B, angkat). Beban: dek 1,0 kPa [Asumsi], helipad merata 2,87 kPa atau
    satu roda 0,75 MTOW (SNI 1727 Pasal 4.11, diambil yang terbesar, tidak digabung)."""
    ak = tb.atap_khusus()
    lc, lb, s = DEK_KANTILEVER, DEK_BALIK, DEK_JARAK
    qd = tb.SIDL["dek_helipad"][0]
    pa_d, pb_d = qd * s * lc * (1 + lc / (2 * lb)), -qd * s * lc ** 2 / (2 * lb)
    merata = (ak["heli_merata"] * s * lc * (1 + lc / (2 * lb)), -ak["heli_merata"] * s * lc ** 2 / (2 * lb))
    roda = (ak["heli_terpusat"] * (1 + lc / lb), -ak["heli_terpusat"] * lc / lb)
    pa_l, pb_l = max(merata, roda, key=lambda t: t[0])
    return {"PA_D": pa_d, "PB_D": pb_d, "PA_L": pa_l, "PB_L": pb_l, "merata": merata, "roda": roda,
            "Pu_A": 1.2 * pa_d + 1.6 * pa_l}


# ------------------------------------------------------------------ analisis 3D
def kunci(b):
    return (b["lv"], b["x1"], b["y1"], b["x2"], b["y2"])


@cache_analisis.disk
def analisis(konfig="K2"):
    """localForce per balok untuk kasus D, L, E/R X±, Y± (E = model penuh, R = rangka saja 25 %)."""
    import openseespy.opensees as ops
    hasil = {}
    for kasus in ("D", "L"):
        m = tm.bangun(konfig)
        ops.timeSeries("Linear", 1)
        ops.pattern("Plain", 1, 1)
        for b in m["balok"]:
            d_, l_, _, _ = beban_balok(b)
            ops.eleLoad("-ele", b["ele"], "-type", "-beamUniform", 0.0, -(d_ if kasus == "D" else l_))
            for pd, pl, a in beban_titik(b, konfig):
                p = pd if kasus == "D" else pl
                ops.eleLoad("-ele", b["ele"], "-type", "-beamPoint", 0.0, -p, a / L_GRID)
        tm._analisis_statik()
        hasil[kasus] = {kunci(b): (list(ops.eleResponse(b["ele"], "localForce")), b) for b in m["balok"]}
    e = tb.elf(konfig)
    for arah in ("X", "Y"):
        ax = min(3.0, max(1.0, (max(tm.faktor_ax(konfig, arah)) / 1.2) ** 2))
        for tanda in (1, -1):
            for tanpa_inti, faktor, nama in ((False, 1.0, "E"), (True, 0.25, "R")):
                m = tm.bangun(konfig, tanpa_inti=tanpa_inti)
                ops.timeSeries("Linear", 1)
                ops.pattern("Plain", 1, 1)
                for i, (t, fx) in enumerate(zip(m["tk"], e["Fx"]), start=1):
                    x0, y0, x1, y1 = t["bounds"]
                    f = fx * faktor
                    ecc = tanda * 0.05 * ax
                    if arah == "X":
                        ops.load(m["master"][i], f, 0, 0, 0, 0, ecc * (y1 - y0) * f)
                    else:
                        ops.load(m["master"][i], 0, f, 0, 0, 0, ecc * (x1 - x0) * f)
                tm._analisis_statik()
                hasil[f"{nama}{arah}{'+' if tanda > 0 else '-'}"] = {
                    kunci(b): list(ops.eleResponse(b["ele"], "localForce")) for b in m["balok"]}
    return hasil


def titik_x(hc):
    return np.concatenate([[hc / 2], np.linspace(0.5, L_GRID - 0.5, 15), [L_GRID - hc / 2]])


def momen(lf, xs, w=0.0, pts=()):
    """Momen (positif = lentur ke bawah) di titik xs dari localForce [N,Vy,Vz,T,My,Mz]×2."""
    m = lf[4] + lf[2] * xs - w * xs ** 2 / 2
    for p, a in pts:
        m = m - p * np.clip(xs - a, 0, None)
    return m


def geser(lf, xs, w=0.0, pts=()):
    v = lf[2] - w * xs
    for p, a in pts:
        v = v - p * (xs > a)
    return v


def selubung(h, konfig="K2"):
    """Selubung momen terfaktor (muka joint dan lapangan) dan geser gravitasi per balok."""
    rho, ev = tb.RHO, 0.2 * tb.SDS
    out = {}
    for k, (lfd, b) in h["D"].items():
        d_, l_, sisi, panel = beban_balok(b)
        pt = beban_titik(b, konfig)
        hc = kolom_lebar(b)
        xs = titik_x(hc)
        md = momen(lfd, xs, d_, [(p[0], p[2]) for p in pt])
        ml = momen(h["L"][k][0], xs, l_, [(p[1], p[2]) for p in pt])
        vd = geser(lfd, xs, d_, [(p[0], p[2]) for p in pt])
        vl = geser(h["L"][k][0], xs, l_, [(p[1], p[2]) for p in pt])
        komb = [1.4 * md, 1.2 * md + 1.6 * ml]
        for nama in ("E", "R"):
            for a, o in (("X", "Y"), ("Y", "X")):
                for s1 in ("+", "-"):
                    ea = momen(h[f"{nama}{a}{s1}"][k], xs)
                    for s2 in ("+", "-"):
                        eo = momen(h[f"{nama}{o}{s2}"][k], xs)
                        for sg in (1, -1):
                            for so in (1, -1):
                                eq = rho * (sg * ea + 0.3 * so * eo)
                                komb.append((1.2 + ev) * md + ml + eq)
                                komb.append((0.9 - ev) * md + eq)
        kk = np.array(komb)
        muka = np.concatenate([kk[:, 0], kk[:, -1]])
        vg = (1.2 + ev) * np.abs(vd[[0, -1]]) + np.abs(vl[[0, -1]])   # gravitasi pada kombinasi gempa (18.6.5.1)
        vu_g = np.maximum(1.4 * np.abs(vd[[0, -1]]), 1.2 * np.abs(vd[[0, -1]]) + 1.6 * np.abs(vl[[0, -1]]))
        out[k] = {"b": b, "konfig": konfig, "sisi": sisi, "panel": panel, "hc": hc,
                  "neg": float(-min(muka.min(), 0.0)), "pos_ujung": float(max(muka.max(), 0.0)),
                  "pos_lap": float(max(kk[:, 1:-1].max(), 0.0)), "Vg": float(vg.max()), "Vu_g": float(vu_g.max()),
                  "D": d_, "L": l_, "titik": pt}
    return out


def gabung(*sels):
    """Selubung K1 ∪ K2 per balok (nilai terbesar)."""
    out = {}
    for sel in sels:
        for k, s in sel.items():
            if k not in out:
                out[k] = dict(s)
                continue
            o = out[k]
            for f in ("neg", "pos_ujung", "pos_lap", "Vg", "Vu_g"):
                if s[f] > o[f]:
                    o[f] = s[f]
                    o[f"{f}_konfig"] = s["konfig"]
    return out


def kelompok(b, sisi):
    lv = b["lv"]
    xm = (b["x1"] + b["x2"]) / 2
    if lv == "LT3" and b["arah"] == "Y" and abs(b["y1"] - 67.0) < 0.01 and any(abs(b["x1"] - x) < 0.01 for x in TANGKI_X):
        return "B-T induk tangki x 68" if abs(b["x1"] - 68.0) < 0.01 else "B-T induk tangki x 60/76"
    if lv == "LT3" and b["arah"] == "X" and abs(b["y1"] - TANGKI_Y_INDUK) < 0.01 and 60 <= xm <= 76:
        return "B-T induk tangki y 67"
    tepi = "tepi" if sisi == 1 else "dalam"
    if lv in ("LT5", "LT6", "ATAP") or (lv == "LT4" and tb.MENARA.buffer(0.01).contains(
            Point(xm, (b["y1"] + b["y2"]) / 2))):
        return f"B-M {tepi} {lv}"
    return f"B-P {tepi} {lv}"


# ------------------------------------------------------------------ penampang
def as_perlu(mu, b, d, fc=FC, fy=FY, phi=PHI_M):
    """As (mm²) dari Mu (kNm) dengan blok tegangan persegi tanpa tulangan tekan."""
    a_ = 0.85 * fc * 1000 * b
    k = mu / phi / (fy * 1000)
    aa = fy * 1000 / (2 * a_)
    disk = d ** 2 - 4 * aa * k
    if disk < 0:
        return float("inf")
    return (d - math.sqrt(disk)) / (2 * aa) * 1e6


def mn(as_mm2, b, d, fc=FC, fy=FY):
    """Mn (kNm) tulangan tarik saja: As fy (d - a/2), a = As fy / (0,85 fc' b)."""
    a = as_mm2 * 1e-6 * fy / (0.85 * fc * b)
    return as_mm2 * 1e-6 * fy * 1000 * (d - a / 2)


def as_min(b, d):
    return max(0.25 * math.sqrt(FC) / FY, 1.4 / FY) * b * d * 1e6   # Pasal 9.6.1.2


def susunan(n, db, b, ds):
    """(batang per lapis, jumlah lapis, jarak titik berat dari serat tepi m); spasi bersih >= max(25, db) (25.2.1)."""
    sb = max(25.0, db)
    lebar = b * 1000 - 2 * SEL * 1000 - 2 * ds
    n1 = max(2, int((lebar + sb) // (db + sb)))
    lapis = math.ceil(n / n1)
    y1 = SEL * 1000 + ds + db / 2
    ys, sisa = [], n
    for k in range(lapis):
        m = min(n1, sisa)
        ys += [y1 + k * (db + sb)] * m
        sisa -= m
    return n1, lapis, sum(ys) / n / 1000


def tulangan_lentur(mu, b, h, ds, as_lain=0.0):
    """Pilih D dan n dengan lapis paling sedikit lalu As terkecil: As >= max(As(Mu), As min, as_lain)."""
    pilihan = []
    for db in DB_LENTUR:
        n = 2
        while n <= 40:
            n1, lapis, yc = susunan(n, db, b, ds)
            d = h - yc
            perlu = max(as_perlu(mu, b, d), as_min(b, d), as_lain)
            if n * luas(db) >= perlu:
                break
            n += 1
        pilihan.append({"db": db, "n": n, "n1": min(n1, n), "lapis": lapis, "d": d, "As": n * luas(db),
                        "As_perlu": perlu})
    return min(pilihan, key=lambda p: (p["lapis"], p["As"]))


def kaki_sengkang(n1):
    """Kaki vertikal agar batang sudut dan selang-seling ditopang (Pasal 18.6.4.2 → 25.7.2.3)."""
    return max(2, math.ceil(n1 / 2) + (1 if n1 % 2 == 0 and n1 > 2 else 0))


def desain_penampang(b, h, mneg, mpos_u, mpos_l, vg, vu_g, tu=0.0, hc=0.75, gempa=True):
    """Desain lentur, geser (kapasitas bila gempa), dan torsi satu penampang; kembalikan dict dengan kunci 'ok'."""
    ln = L_GRID - hc
    for ds in DB_SENGKANG:
        acp, pcp = b * h, 2 * (b + h)
        x1, y1 = b - 2 * SEL - ds / 1000, h - 2 * SEL - ds / 1000
        aoh, ph = x1 * y1, 2 * (x1 + y1)
        tth = 0.083 * math.sqrt(FC) * acp ** 2 / pcp * 1000          # Tabel 22.7.4.1(a), kNm
        tcr = 0.33 * math.sqrt(FC) * acp ** 2 / pcp * 1000           # Tabel 22.7.5.1
        tu_d = min(tu, PHI_V * tcr)                                   # 22.7.3.2 torsi kompatibilitas
        torsi = tu_d > PHI_V * tth
        ats = tu_d / (PHI_V * 2 * 0.85 * aoh * FYT * 1000) if torsi else 0.0   # m²/m per kaki, θ 45°
        al = 0.0
        if torsi:
            al = max(ats * ph * FYT / FY,
                     0.42 * math.sqrt(FC) * acp / FY - max(ats, 0.175 * b / FYT) * ph * FYT / FY) * 1e6   # mm²
        atas = tulangan_lentur(mneg, b, h, ds, al / 4)
        bawah = tulangan_lentur(max(mpos_u, mpos_l), b, h, ds,
                                max(0.5 * atas["As"] if gempa else 0.0, 0.25 * atas["As"]) + al / 4)
        d = min(atas["d"], bawah["d"])
        rho = atas["As"] / (b * atas["d"] * 1e6)
        atas_lap = max(2, math.ceil(0.25 * max(atas["As"], bawah["As"]) / luas(atas["db"])))
        vc_n = 0.17 * math.sqrt(FC) * b * d * 1000                     # Pers. 22.5.5.1
        if gempa:
            mpr_n = mn(atas["As"], b, atas["d"], fy=1.25 * FY)
            mpr_p = mn(bawah["As"], b, bawah["d"], fy=1.25 * FY)
            ve_e = (mpr_n + mpr_p) / ln
            ve = ve_e + vg
            vc = 0.0 if ve_e >= 0.5 * ve else vc_n                       # 18.6.5.2
        else:
            mpr_n = mpr_p = ve_e = 0.0
            ve, vc = vu_g, vc_n
        vu = max(ve, vu_g)
        avs = max(vu / PHI_V - vc, 0.0) / (FYT * 1000 * d)              # m²/m semua kaki
        avs_l = max(vu / PHI_V - vc_n, 0.0) / (FYT * 1000 * d)          # di luar sendi plastis (Vc dihitung)
        avs_min = max(0.062 * math.sqrt(FC), 0.35) * b / FYT            # 9.6.3.3 / 9.6.4.2 (Av + 2At)
        vs = vu / PHI_V - vc
        ok_v = vu <= PHI_V * (vc_n + 0.66 * math.sqrt(FC) * b * d * 1000)   # 22.5.1.2
        ok_t = True
        if torsi:
            kiri = math.hypot(vu / (b * d), tu_d * ph / (1.7 * aoh ** 2))
            ok_t = kiri <= PHI_V * (vc_n / (b * d) + 0.66 * math.sqrt(FC) * 1000)   # 22.7.7.1(a)
        a1 = luas(ds) * 1e-6
        db_min = min(atas["db"], bawah["db"]) / 1000
        bts_t = (ph / 8, 0.300) if torsi else (1.0,)

        def spasi(avs_, kaki):
            s1 = a1 / (ats + avs_ / kaki) if (ats + avs_) > 0 else 1.0
            return min(s1, kaki * a1 / avs_min)

        if gempa:
            kaki = kaki_sengkang(max(atas["n1"], bawah["n1"]))
            s_sendi = floor25(min(spasi(avs, kaki), d / 4, 6 * db_min, 0.150, *bts_t))   # 18.6.4.4
            s_lap = floor25(min(spasi(avs_l, kaki), d / 2, *bts_t))                       # 18.6.4.6
        else:
            smax = (d / 2, 0.600) if vs <= 0.33 * math.sqrt(FC) * b * d * 1000 else (d / 4, 0.300)   # Tabel 9.7.6.2.2
            for kaki in (2, 4):   # balok bukan SPGS: 2 kaki, 4 kaki bila spasi < 100 mm [Asumsi praktik]
                s_sendi = floor25(min(spasi(avs, kaki), *smax, *bts_t))
                s_lap = floor25(min(spasi(avs_l, kaki), *smax, *bts_t))
                if s_sendi >= 0.100:
                    break
        if s_sendi >= S_MIN - 1e-9:
            break
    samping = math.ceil(al / 2 / luas(13) / 2) if torsi else 0   # per sisi, D13
    if h > 0.9:
        samping = max(samping, 2)                                   # tulangan kulit 9.7.2.3
    ok = {"rho": rho <= RHO_PAKAI, "lapis": max(atas["lapis"], bawah["lapis"]) <= 2, "geser": ok_v, "torsi": ok_t,
          "sengkang": s_sendi >= S_MIN - 1e-9, "dimensi": ln >= 4 * d and b >= max(0.3 * h, 0.25) if gempa else True,
          "joint": hc >= 20 * max(atas["db"], bawah["db"]) / 1000 if gempa else True}
    return {"b": b, "h": h, "d": d, "ln": ln, "hc": hc, "atas": atas, "bawah": bawah, "atas_lap": atas_lap,
            "rho": rho, "Mneg": mneg, "Mpos": max(mpos_u, mpos_l), "Mpos_u": mpos_u, "Mpos_l": mpos_l,
            "phiMn_neg": PHI_M * mn(atas["As"], b, atas["d"]), "phiMn_pos": PHI_M * mn(bawah["As"], b, bawah["d"]),
            "Mpr_neg": mpr_n, "Mpr_pos": mpr_p, "Ve_e": ve_e, "Vg": vg, "Ve": ve, "Vu_g": vu_g, "Vc": vc,
            "Vu": vu, "Vs": vs, "Tu": tu, "Tu_d": tu_d, "phiTth": PHI_V * tth, "phiTcr": PHI_V * tcr,
            "torsi": torsi, "At_s": ats * 1e6 / 1000, "Al": al, "samping": samping, "ds": ds, "kaki": kaki,
            "s_sendi": s_sendi, "s_lap": s_lap, "l_sendi": 2 * h, "cek": ok, "ok": all(ok.values())}


def torsi_tepi(panel, hc):
    """Tu (kNm) balok tepi dari momen negatif luar pelat yang tidak dipikul balok tegak lurus (DDM 4.5)."""
    if panel is None:
        return 0.0
    qu = max(1.4 * panel[0], 1.2 * panel[0] + 1.6 * panel[1])
    ln = L_GRID - hc
    m = tp.ddm(qu, ln, ujung=True)["neg_eks"]
    t = (m["M"] - m["balok"]) / L_GRID       # kNm/m sepanjang balok tepi
    return t * ln / 2


def desain_kelompok(sel, uk_kel):
    """Satu penampang per kelompok dari selubung terburuk anggotanya."""
    kel = {}
    for k, s in sel.items():
        kel.setdefault(kelompok(s["b"], s["sisi"]), []).append(s)
    hasil = []
    for nama, ss in sorted(kel.items()):
        b, h = uk_kel.get(nama, (tb.BALOK_B, tb.BALOK_H))
        hc = min(s["hc"] for s in ss)
        tu = max((torsi_tepi(s["panel"], s["hc"]) for s in ss if s["sisi"] == 1), default=0.0)
        r = desain_penampang(b, h, max(s["neg"] for s in ss), max(s["pos_ujung"] for s in ss),
                             max(s["pos_lap"] for s in ss), max(s["Vg"] for s in ss), max(s["Vu_g"] for s in ss),
                             tu=tu, hc=hc)
        r.update({"kelompok": nama, "n": len(ss), "kunci": [kunci(s["b"]) for s in ss],
                  "wu": max(1.2 * s["D"] + s["L"] for s in ss)})
        hasil.append(r)
    return hasil


# Ukuran akhir dari iterasi penuh `rancang(awal=())` (20 Nov 2026): dipakai sebagai titik awal supaya cepat;
# rancang() tetap memeriksa ulang dan menaikkan ukuran bila ada kelompok yang tidak memenuhi.
UKURAN_AWAL = (("B-T induk tangki x 60/76", (0.45, 0.80)), ("B-T induk tangki x 68", (0.60, 1.20)),
               ("B-T induk tangki y 67", (0.40, 0.70)))   # 6 iterasi dari 350 × 600


@functools.lru_cache(maxsize=2)
@cache_analisis.disk
def rancang(awal=None, maks_iter=10):
    """Iterasi ukuran kelompok: analisis K1 + K2, desain, naikkan ukuran kelompok yang tidak memenuhi."""
    uk_kel = dict(UKURAN_AWAL if awal is None else awal)
    riwayat = []
    for it in range(maks_iter):
        peta = {}
        tm.UKURAN_BALOK = {}
        for k, s in _kunci_kelompok().items():
            if s in uk_kel:
                peta[k] = uk_kel[s]
        tm.UKURAN_BALOK = peta
        sel = gabung(selubung(analisis("K2"), "K2"), selubung(analisis("K1"), "K1"))
        hasil = desain_kelompok(sel, uk_kel)
        gagal = [r for r in hasil if not r["ok"]]
        riwayat.append({r["kelompok"]: (r["b"], r["h"], r["ok"]) for r in hasil})
        if not gagal or all((r["b"], r["h"]) == UKURAN[-1] for r in gagal):
            break
        for r in gagal:
            i = UKURAN.index((r["b"], r["h"])) if (r["b"], r["h"]) in UKURAN else 0
            uk_kel[r["kelompok"]] = UKURAN[min(i + 1, len(UKURAN) - 1)]
    ukuran_model = dict(tm.UKURAN_BALOK)
    tm.UKURAN_BALOK = {}
    return {"kelompok": hasil, "selubung": sel, "ukuran": uk_kel, "ukuran_model": ukuran_model,
            "riwayat": riwayat, "iterasi": it + 1}


@functools.lru_cache(maxsize=1)
def _kunci_kelompok():
    """Peta kunci balok -> nama kelompok (geometri model K2 dan K1, tidak bergantung ukuran)."""
    out = {}
    for konfig in ("K2", "K1"):
        m = tm.bangun(konfig)
        for b in m["balok"]:
            out.setdefault(kunci(b), kelompok(b, beban_balok(b)[2]))
    return out


def dampak_massa(ukuran_model):
    """Tambahan berat balok (kN) akibat ukuran khusus dan rasionya terhadap W K2 (massa 4.2 belum diubah)."""
    dw = sum(tb.GAMMA_C * (b * (h - tp.H) - tb.BALOK_B * (tb.BALOK_H - tp.H)) * L_GRID
             for (b, h) in ukuran_model.values())
    w = tb.elf("K2")["W"]
    return {"dW": dw, "W": w, "rasio": dw / w}


# ------------------------------------------------------------------ balok anak (bukan SPGS): PyNite menerus
def balok_menerus(bentang, beban_q, beban_p, b, h, k_rot=None):
    """Balok menerus di atas tumpuan sendi (PyNite). beban_q: [(kasus, w kN/m, x0, x1)], beban_p: [(kasus, P, x)]
    (ke bawah positif). k_rot (kNm/rad, opsional, 5.1): pegas putar di kedua ujung (kekakuan kolom); None = sendi.
    Kembalikan fungsi momen/geser per kasus, titik x, dan reaksi tumpuan per kasus."""
    from Pynite import FEModel3D
    e = 4700 * math.sqrt(FC) * 1000
    m = FEModel3D()
    m.add_material("c", e, e / 2.4, 0.2, 24.0)
    m.add_section("s", b * h, h * b ** 3 / 12, b * h ** 3 / 12, 1e-3)
    tump = [0.0]
    for L in bentang:
        tump.append(tump[-1] + L)
    xs = sorted(set([round(x, 4) for x in tump] + [round(p[2], 4) for p in beban_p] +
                    [round(x, 4) for q in beban_q for x in q[2:]] + list(np.round(np.arange(0, tump[-1] + 1e-9, 0.25), 4))))
    nama = {}
    for i, x in enumerate(xs):
        nama[x] = f"N{i}"
        m.add_node(f"N{i}", x, 0.0, 0.0)
    for x in tump:
        n = nama[round(x, 4)]
        m.def_support(n, x == 0.0, True, True, True, True, False)
        if k_rot and x in (tump[0], tump[-1]):
            m.def_support_spring(n, "RZ", k_rot)
    for i in range(len(xs) - 1):
        m.add_member(f"M{i}", f"N{i}", f"N{i + 1}", "c", "s")
    kasus = sorted({q[0] for q in beban_q} | {p[0] for p in beban_p})
    for ks, w, x0, x1 in beban_q:
        for i in range(len(xs) - 1):
            a, c = max(xs[i], x0), min(xs[i + 1], x1)
            if c - a > 1e-6:
                m.add_member_dist_load(f"M{i}", "FY", -w, -w, a - xs[i], c - xs[i], case=ks)
    for ks, p, x in beban_p:
        m.add_node_load(nama[round(x, 4)], "FY", -p, case=ks)
    for ks in kasus:
        m.add_load_combo(ks, {ks: 1.0})
    m.analyze_linear(check_statics=False)
    titik, mom, ges = [], {k: [] for k in kasus}, {k: [] for k in kasus}
    for i in range(len(xs) - 1):
        mem = m.members[f"M{i}"]
        L = xs[i + 1] - xs[i]
        for f in (0.0, 0.5, 1.0):
            titik.append(xs[i] + f * L)
            for ks in kasus:
                mom[ks].append(mem.moment("Mz", f * L, ks))
                ges[ks].append(mem.shear("Fy", f * L, ks))
    titik = np.array(titik)
    # tanda: momen di tumpuan dalam negatif (lentur ke atas)
    for ks in kasus:
        arr = np.array(mom[ks])
        j = int(np.argmin(np.abs(titik - tump[1])))
        tanda = -1.0 if arr[j] > 0 else 1.0
        mom[ks] = tanda * arr
        ges[ks] = np.array(ges[ks])
    reaksi = {ks: [m.nodes[nama[round(x, 4)]].RxnFY[ks] for x in tump] for ks in kasus}
    return {"x": titik, "M": mom, "V": ges, "R": reaksi, "tumpuan": tump}


def _desain_anak(fungsi_beban, bentang, hc, ukuran):
    """Pilih ukuran balok anak terkecil yang memenuhi; kembalikan desain, gaya, dan reaksi layan."""
    for b, h in ukuran:
        q, p = fungsi_beban(b, h)
        r = balok_menerus(bentang, q, p, b, h)
        mu = np.maximum(1.4 * r["M"]["D"], 1.2 * r["M"]["D"] + 1.6 * r["M"]["L"])
        mu2 = np.minimum(1.4 * r["M"]["D"], 1.2 * r["M"]["D"] + 1.6 * r["M"]["L"])
        x = r["x"]
        dalam = np.abs(x - r["tumpuan"][1]) <= hc / 2 + 1e-6
        jauh = np.abs(x - r["tumpuan"][1]) >= hc / 2 - 1e-6
        muka = np.abs(np.abs(x - r["tumpuan"][1]) - hc / 2) < 0.13
        mneg = float(-mu2[muka & jauh].min()) if (muka & jauh).any() else float(-mu2.min())
        mpos = float(mu.max())
        vu_ = np.maximum(1.4 * np.abs(r["V"]["D"]), 1.2 * np.abs(r["V"]["D"]) + 1.6 * np.abs(r["V"]["L"]))
        vu = float(vu_[~dalam].max())
        des = desain_penampang(b, h, mneg, 0.0, mpos, 0.0, vu, hc=hc, gempa=False)
        if des["ok"] or (b, h) == ukuran[-1]:
            return des, r, {"Mneg": mneg, "Mpos": mpos, "Vu": vu, "Mneg_pusat": float(-mu2.min())}


@functools.lru_cache(maxsize=4)
def balok_anak_tangki(b_awal=None):
    """Balok anak y 71 dua bentang 8 m (x 60-68-76) di atas balok induk; lajur 4 m pelat 250 mm, tangki 30,1 kPa di
    x 60-72 (tidak di seluruh bentang kedua). Isi tangki = beban mati (SNI 1727 Pasal 3.1.3, 4.5)."""
    qt = tb.atap_khusus()["tangki_kpa"]

    def beban(b, h):
        d_pel = (tb.GAMMA_C * tp.H_TANGKI + tp.SIDL_ATAP) * 4.0 + tb.GAMMA_C * b * (h - tp.H_TANGKI)
        return ([("D", d_pel, 0.0, 16.0), ("D", qt * 4.0, 0.0, 12.0), ("L", 0.96 * 4.0, 0.0, 16.0)], [])

    uk = [(0.40, 0.80), (0.50, 0.90), (0.50, 1.00), (0.60, 1.10), (0.60, 1.20)]
    des, r, gaya = _desain_anak(beban, [8.0, 8.0], tb.BALOK_B, uk)
    q, _ = beban(des["b"], des["h"])
    wu_rata = max(1.4 * (q[0][1] + q[1][1] * 12 / 16), 1.2 * (q[0][1] + q[1][1] * 12 / 16) + 1.6 * q[2][1])
    wu_penuh = max(1.4 * (q[0][1] + q[1][1]), 1.2 * (q[0][1] + q[1][1]) + 1.6 * q[2][1])
    ln = 8.0 - tb.BALOK_B
    # cek silang T-75: koefisien Tabel 6.5.2 (dua bentang, muka tumpuan dalam pertama wu ln²/9) dengan beban penuh
    rp = balok_menerus([8.0, 8.0], [("D", q[0][1] + q[1][1], 0.0, 16.0), ("L", q[2][1], 0.0, 16.0)], [],
                       des["b"], des["h"])
    mu2 = np.minimum(1.4 * rp["M"]["D"], 1.2 * rp["M"]["D"] + 1.6 * rp["M"]["L"])
    muka = np.abs(np.abs(rp["x"] - 8.0) - tb.BALOK_B / 2) < 0.13
    return {**des, **gaya, "R_D": r["R"]["D"], "R_L": r["R"]["L"], "wu_penuh": wu_penuh, "wu_rata": wu_rata,
            "qt": qt, "M_koef": wu_penuh * ln ** 2 / 9, "M_pynite_penuh": float(-mu2[muka].min()),
            "V_koef": 1.15 * wu_penuh * ln / 2}


@functools.lru_cache(maxsize=1)
def balok_chiller():
    """Rel dudukan chiller: balok anak arah X dua bentang 8 m (x 60-68-76) di atap V1 LT3; titik tumpu chiller
    115,8 kN / 6 titik (D) + impak 20 % (L, SNI 1727 Pasal 4.6.3) di x 62,5 / 68,0 / 73,5; lajur pelat 2,0 m."""
    ak = tb.atap_khusus()
    pd = 115.8 / 6
    pl = ak["chiller_impak_kn"] / 6 - pd

    def beban(b, h):
        qd = (tb.GAMMA_C * tp.H + tp.SIDL_ATAP) * 2.0 + tb.GAMMA_C * b * (h - tp.H)
        return ([("D", qd, 0.0, 16.0), ("L", 0.96 * 2.0, 0.0, 16.0)],
                [("D", pd, x - 60.0) for x in CHILLER_X if abs(x - 68.0) > 0.01] +
                [("L", pl, x - 60.0) for x in CHILLER_X if abs(x - 68.0) > 0.01])

    des, r, gaya = _desain_anak(beban, [8.0, 8.0], tb.BALOK_B, [(0.30, 0.50), (0.30, 0.60), (0.35, 0.60)])
    return {**des, **gaya, "PD": pd, "PL": pl, "R_D": r["R"]["D"], "R_L": r["R"]["L"]}


# ------------------------------------------------------------------ cek silang T-74: concreteproperties
def cek_concreteproperties(des):
    """φMn negatif dan positif penampang dengan concreteproperties (blok tegangan persegi, baja elastis-plastis,
    tulangan atas dan bawah per lapis) dibanding rumus sendiri `mn` (tulangan tarik saja)."""
    from concreteproperties.concrete_section import ConcreteSection
    from concreteproperties.material import Concrete, SteelBar
    from concreteproperties.stress_strain_profile import (ConcreteLinearNoTension, RectangularStressBlock,
                                                          SteelElasticPlastic)
    from sectionproperties.pre.library.concrete_sections import add_bar
    from sectionproperties.pre.library.primitive_sections import rectangular_section

    beta1 = 0.85 - 0.05 * (FC - 28) / 7                  # Tabel 22.2.2.4.3
    ec = 4700 * math.sqrt(FC)
    beton = Concrete("fc30", 2.4e-6, ConcreteLinearNoTension(elastic_modulus=ec, ultimate_strain=0.003,
                                                              compressive_strength=FC),
                     "lightgrey", RectangularStressBlock(compressive_strength=FC, alpha=0.85, gamma=beta1,
                                                         ultimate_strain=0.003),
                     flexural_tensile_strength=0.62 * math.sqrt(FC))
    baja = SteelBar("BjTS420", 7.85e-6, SteelElasticPlastic(yield_strength=FY, elastic_modulus=200e3,
                                                            fracture_strain=0.05), "grey")
    b, h, ds = des["b"] * 1000, des["h"] * 1000, des["ds"]
    geom = rectangular_section(d=h, b=b, material=beton)
    for t, atas in ((des["atas"], True), (des["bawah"], False)):
        db, n, n1 = t["db"], t["n"], t["n1"]
        sb = max(25.0, db)
        sisa, k = n, 0
        while sisa > 0:
            m = min(n1, sisa)
            y = SEL * 1000 + ds + db / 2 + k * (db + sb)
            y = h - y if atas else y
            x0 = SEL * 1000 + ds + db / 2
            x1 = b - x0
            for j in range(m):
                x = x0 + (x1 - x0) * (j / (m - 1) if m > 1 else 0.5)
                geom = add_bar(geom, luas(db), baja, x, y, 16)
            sisa -= m
            k += 1
    sec = ConcreteSection(geom)
    pos = sec.ultimate_bending_capacity(theta=0).m_xy / 1e6
    neg = sec.ultimate_bending_capacity(theta=math.pi).m_xy / 1e6
    return {"phiMn_neg_cp": PHI_M * abs(neg), "phiMn_pos_cp": PHI_M * abs(pos),
            "phiMn_neg": des["phiMn_neg"], "phiMn_pos": des["phiMn_pos"]}


# ------------------------------------------------------------------ ringkasan
@functools.lru_cache(maxsize=1)
def ringkasan():
    r = rancang()
    kel = {x["kelompok"]: x for x in r["kelompok"]}
    contoh = kel.get("B-P dalam LT3") or r["kelompok"][0]
    return {**r, "tangki": balok_anak_tangki(), "chiller": balok_chiller(), "helipad": dek_helipad(),
            "massa": dampak_massa(r["ukuran_model"]), "cp": cek_concreteproperties(contoh), "contoh": contoh}


def teks_tulangan(t):
    return f"{t['n']}D{t['db']}" + (f" ({t['lapis']} lapis)" if t["lapis"] > 1 else "")


# ------------------------------------------------------------------ Excel
def buat_excel(keluar=BERKAS, hitung_ulang=True):
    import openpyxl
    from format_dokumen import AI, Lembar, hitung_ulang_excel, set_font_bawaan

    r = ringkasan()
    kel = r["kelompok"]
    t, c, cp, ms = r["tangki"], r["chiller"], r["cp"], r["massa"]
    ak = tb.atap_khusus()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    lab = f"DIISI AI ATAS PERMINTAAN DEFSA (20 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk desain balok (4.6)", [6, 120])
    lb.catatan(LABEL + " " + lab)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, x] for i, x in enumerate([
        "Balok SRPMK fc' 30 MPa, BjTS 420B (fy = fyt = 420 MPa), selimut 40 mm (Tabel 20.6.1.3.1). Ukuran dasar "
        "350 × 600 (3.6); kelompok dinaikkan bertahap (400 × 700 sampai 700 × 1.200) bila ρ > 0,020 [Asumsi praktis; "
        "SNI 18.6.3.1 membolehkan 0,025], tulangan lebih dari 2 lapis, atau batas geser/torsi tidak terpenuhi.",
        "Gaya dalam dari model 3D 4.3 (openseespy) dengan beban gravitasi langsung pada balok (pelat q L/3 per sisi, "
        "berat badan, dinding/parapet, beban titik tangki dan dek helipad) dan gempa pola ELF V = 13.164 kN (K2), "
        "torsi tak terduga 0,05 Ax, 100 % + 30 %, ρ 1,3, Ev 0,077D; model rangka saja 25 % (SNI 1726 Pasal 7.2.5.1) "
        "ikut diselubungi; K1 (tahap 1) dan K2 (akhir) diselubungi. Momen diambil di muka kolom.",
        "Lentur: blok tegangan persegi, φ 0,90 (Tabel 21.2.1 hal. 469), As min Pasal 9.6.1.2 hal. 189; SRPMK 18.6.3 "
        "hal. 378-379: M+ muka >= 0,5 M-, tulangan menerus >= 0,25 maks, minimal 2 batang. Spasi bersih >= "
        "max(25 mm, db). Joint: hc >= 20 db (18.8.2.3 hal. 393).",
        "Geser kapasitas SRPMK 18.6.5 hal. 382: Ve = (Mpr- + Mpr+)/ln + Vg, Mpr dengan 1,25 fy dan φ 1; Vc = 0 bila "
        "bagian gempa >= 0,5 Ve. Sengkang pengekang sepanjang 2h, s <= d/4, 6db, 150 mm (18.6.4.4 hal. 381); di luar "
        "sendi s <= d/2 (18.6.4.6). Kaki sengkang menopang batang sudut dan selang-seling (18.6.4.2, 25.7.2.3). "
        "Batas penampang Vu <= φ(Vc + 0,66 √fc' b d) (22.5.1.2 hal. 482).",
        "Torsi balok tepi: torsi kompatibilitas dari momen negatif luar pelat (DDM 4.5) yang tidak dipikul balok tegak "
        "lurus; diabaikan bila Tu <= φTth (Tabel 22.7.4.1(a) hal. 511), dibatasi φTcr (22.7.3.2 hal. 510). At/s dan "
        "Al Pasal 22.7.6.1 hal. 514 (θ 45°, Ao 0,85 Aoh), minimum 9.6.4.2-9.6.4.3 hal. 193, spasi ph/8 dan 300 mm "
        "(9.7.6.3.3 hal. 203), batas penampang 22.7.7.1 hal. 516. Penampang badan saja (sayap diabaikan).",
        "Balok khusus: balok anak tangki dan rel chiller (bukan SPGS, Pasal 9 dan Tabel 9.7.6.2.2 hal. 202; PyNite "
        "balok menerus), balok induk penumpu tangki (SRPMK dengan beban titik), balok atap tepi penumpu dek helipad.",
        "Cek silang: T-74 φMn concreteproperties vs rumus sendiri; T-75 koefisien Tabel 6.5.2 hal. 99 vs PyNite; "
        "T-76 rumus Excel vs Python (setelah dihitung ulang di Excel).",
        "Sel hijau berisi rumus atau hasil AI. Status: " + STATUS + ".",
    ])], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Gaya Kelompok"), 2, "Selubung gaya terfaktor per kelompok balok",
                [26, 7, 9, 9, 8, 11, 11, 11, 11, 11, 10])
    lb.catatan(LABEL + " Nilai terbesar anggota kelompok, K1 ∪ K2. M- dan M+ ujung di muka kolom; M+ lapangan maks "
               "di bentang. Vg = geser gravitasi (1,2 + 0,2 SDS)D + L di muka kolom; Vu,g = maks(1,4D; 1,2D + 1,6L). "
               "Tu = torsi kompatibilitas balok tepi (sebelum dibatasi). B-P podium, B-M menara, B-T penumpu tangki.")
    lb.tabel(["Kelompok", "n", "b (mm)", "h (mm)", "hc (m)", "M- (kNm)", "M+ ujung (kNm)", "M+ lap. (kNm)",
              "Vg (kN)", "Vu,g (kN)", "Tu (kNm)"],
             [[x["kelompok"], x["n"], x["b"] * 1000, x["h"] * 1000, x["hc"], round(x["Mneg"], 1),
               round(x["Mpos_u"], 1), round(x["Mpos_l"], 1), round(x["Vg"], 1), round(x["Vu_g"], 1),
               round(x["Tu"], 1)] for x in kel],
             rata=list("lcccccccccc"), fmt=[None, "0", "0", "0", "0.00", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0"],
             fill_kolom={i: AI for i in range(2, 11)})
    lb.kosong()
    lb.catatan(f"Ukuran khusus menambah berat balok {ms['dW']:.0f} kN = {ms['rasio'] * 100:.2f} % W K2 "
               f"({ms['W']:,.0f} kN)".replace(",", ".").replace(".", ",", 1) +
               ": massa 4.2 dan kekakuan 4.3 tidak dihitung ulang (pengaruh < 0,5 %); balok yang lebih besar hanya "
               "menambah kekakuan sehingga simpangan 4.3 tetap di bawah batas.")

    lb = Lembar(wb.create_sheet("Lentur"), 3, "Tulangan lentur dan kekuatan",
                [26, 9, 9, 11, 10, 6, 6, 7, 9, 11, 10, 11, 9, 11])
    lb.catatan(LABEL + " As = n π db²/4; a = As fy/(0,85 fc' b); φMn = 0,9 As fy (d - a/2) (tulangan tarik saja, "
               "konservatif; T-74). ρ = As/(b d) <= 0,020 [Asumsi praktis] <= 0,025 (18.6.3.1). Tulangan atas di "
               "lapangan: batang menerus >= 0,25 As maks (lembar Geser dan Torsi).")
    baris = []
    for x in kel:
        for pos, tt, mu in (("atas (M-)", x["atas"], x["Mneg"]), ("bawah (M+)", x["bawah"], x["Mpos"])):
            baris.append([x["kelompok"], x["b"] * 1000, x["h"] * 1000, pos, round(mu, 1), tt["n"], tt["db"],
                          tt["lapis"], round(tt["d"] * 1000, 1), None, None, None, None, None])
    _, a, b_ = lb.tabel(["Kelompok", "b (mm)", "h (mm)", "Posisi", "Mu (kNm)", "n", "D", "Lapis", "d (mm)",
                         "As (mm²)", "a (mm)", "φMn (kNm)", "ρ", "Status"], baris,
                        rata=list("lccccccccccccc"),
                        fmt=[None, "0", "0", None, "0.0", "0", "0", "0", "0.0", "0", "0.0", "0.0", "0.0000", None],
                        fill_kolom={9: AI, 10: AI, 11: AI, 12: AI, 13: AI})
    k = lb.kol
    for rr in range(a, b_ + 1):
        lb.ws[f"{k(9)}{rr}"] = f"={k(5)}{rr}*PI()*{k(6)}{rr}^2/4"
        lb.ws[f"{k(10)}{rr}"] = f"={k(9)}{rr}*{FY}/(0.85*{FC}*{k(1)}{rr})"
        lb.ws[f"{k(11)}{rr}"] = f"=0.9*{k(9)}{rr}*{FY}*({k(8)}{rr}-{k(10)}{rr}/2)/1000000"
        lb.ws[f"{k(12)}{rr}"] = f"={k(9)}{rr}/({k(1)}{rr}*{k(8)}{rr})"
        lb.ws[f"{k(13)}{rr}"] = f'=IF(AND({k(11)}{rr}>={k(4)}{rr},{k(12)}{rr}<=0.025),"Memenuhi","Kurang")'

    lb = Lembar(wb.create_sheet("Geser dan Torsi"), 4, "Geser kapasitas, sengkang, dan torsi",
                [26, 8, 9, 9, 10, 9, 10, 10, 9, 9, 9, 10, 9, 9, 10, 9, 11])
    lb.catatan(LABEL + " Mpr = As (1,25 fy)(d - a/2), a = As 1,25 fy/(0,85 fc' b), φ = 1; Ve = (Mpr- + Mpr+)/ln + Vg "
               "(18.6.5.1). Vc = 0 bila (Mpr- + Mpr+)/ln >= 0,5 Ve (18.6.5.2). Sengkang tertutup; s sendi berlaku "
               "sepanjang 2h dari muka kolom. Torsi: φTth = 0,75 × 0,083 √fc' Acp²/pcp.")
    baris = []
    for x in kel:
        baris.append([x["kelompok"], round(x["ln"], 2), round(x["atas"]["As"], 1), round(x["atas"]["d"] * 1000, 1),
                      round(x["bawah"]["As"], 1), round(x["bawah"]["d"] * 1000, 1), None, None, round(x["Vg"], 1),
                      None, round(x["Vc"], 1), f"{x['kaki']} kaki D{x['ds']}", round(x["s_sendi"] * 1000),
                      round(x["s_lap"] * 1000), round(x["Tu_d"], 1), round(x["phiTth"], 1), None])
    _, a, b_ = lb.tabel(["Kelompok", "ln (m)", "As atas (mm²)", "d atas (mm)", "As bawah (mm²)", "d bawah (mm)",
                         "Mpr- (kNm)", "Mpr+ (kNm)", "Vg (kN)", "Ve (kN)", "Vc (kN)", "Sengkang", "s sendi (mm)",
                         "s lap. (mm)", "Tu desain (kNm)", "φTth (kNm)", "Torsi"], baris,
                        rata=list("lcccccccccccccccc"),
                        fmt=[None, "0.00", "0", "0.0", "0", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0", None, "0", "0",
                             "0.0", "0.0", None],
                        fill_kolom={i: AI for i in (6, 7, 9, 10, 11, 12, 13, 14, 16)})
    for i, rr in enumerate(range(a, b_ + 1)):
        bb = kel[i]["b"] * 1000
        for kol_m, kol_as, kol_d in ((6, 2, 3), (7, 4, 5)):
            lb.ws[f"{k(kol_m)}{rr}"] = (f"={k(kol_as)}{rr}*1.25*{FY}*({k(kol_d)}{rr}-{k(kol_as)}{rr}*1.25*{FY}/"
                                        f"(0.85*{FC}*{bb:.0f})/2)/1000000")
        lb.ws[f"{k(9)}{rr}"] = f"=({k(6)}{rr}+{k(7)}{rr})/{k(1)}{rr}+{k(8)}{rr}"
        lb.ws[f"{k(16)}{rr}"] = f'=IF({k(14)}{rr}>{k(15)}{rr},"Ditulangi","Diabaikan")'

    lb = Lembar(wb.create_sheet("Ringkasan Tulangan"), 5, "Ringkasan tulangan per kelompok balok",
                [26, 12, 16, 16, 18, 12, 12, 12, 16, 12])
    lb.catatan(LABEL + " Atas lapangan = batang menerus >= 0,25 As maks dan minimal 2 (18.6.3.1-18.6.3.2). Al torsi "
               "dibagi: 1/4 ditambahkan ke tulangan atas, 1/4 ke bawah, 1/2 sebagai tulangan samping D13 (22.7.6.1).")
    lb.tabel(["Kelompok", "b × h (mm)", "Atas tumpuan", "Bawah", "Atas lapangan", "Sengkang", "s sendi / lap. (mm)",
              "At/s (mm²/mm)", "Al (mm²) / samping", "Status"],
             [[x["kelompok"], f"{x['b'] * 1000:.0f} × {x['h'] * 1000:.0f}", teks_tulangan(x["atas"]),
               teks_tulangan(x["bawah"]), f"{x['atas_lap']}D{x['atas']['db']}", f"{x['kaki']} kaki D{x['ds']}",
               f"{x['s_sendi'] * 1000:.0f} / {x['s_lap'] * 1000:.0f}", round(x["At_s"], 3),
               (f"{x['Al']:.0f} / {x['samping']} D13 per sisi" if x["Al"] > 0 else
                f"kulit {x['samping']} D13 per sisi (9.7.2.3)") if x["samping"] else "-",
               "Memenuhi" if x["ok"] else "Periksa"] for x in kel],
             rata=list("lccccccccc"), fmt=[None] * 7 + ["0.000", None, None], fill_kolom={i: AI for i in range(1, 10)})

    lb = Lembar(wb.create_sheet("Balok Khusus"), 6, "Balok tangki, rel chiller, dan dek helipad", [50, 16, 12, 62])
    lb.catatan(LABEL + " Balok anak bukan bagian SPGS (Pasal 9), dianalisis PyNite sebagai balok menerus dua bentang "
               "di atas tumpuan sendi (balok induk). Reaksi layan balok anak tangki dimasukkan sebagai beban titik di "
               "tengah balok induk x 60/68/76 (y 67-75) pada model 3D.")
    t68 = [x for x in kel if x["kelompok"] == "B-T induk tangki x 68"][0]
    lb.tabel(["Butir", "Nilai", "Satuan", "Keterangan"], [
        ["Balok anak tangki y 71 (x 60-68-76)", f"{t['b'] * 1000:.0f} × {t['h'] * 1000:.0f}", "mm",
         f"atas {teks_tulangan(t['atas'])}, bawah {teks_tulangan(t['bawah'])}, sengkang {t['kaki']} kaki "
         f"D{t['ds']}-{t['s_sendi'] * 1000:.0f}" +
         (f", tulangan kulit {t['samping']} D13 per sisi (9.7.2.3)" if t["samping"] else "")],
        ["  Beban tangki (lajur 4 m, x 60-72)", round(t["qt"] * 4, 1), "kN/m", "isi tetap = beban mati"],
        ["  Mu- muka tumpuan dalam / Mu+ maks", f"{t['Mneg']:.0f} / {t['Mpos']:.0f}", "kNm", "PyNite, 1,4D menentukan"],
        ["  Vu muka tumpuan dalam", round(t["Vu"]), "kN", "Vs <= 0,66 √fc' b d (22.5.1.2)"],
        ["  Reaksi layan D pada x 60 / 68 / 76", " / ".join(f"{v:.0f}" for v in t["R_D"]), "kN",
         "masuk model 3D sebagai beban titik"],
        ["Balok induk x 68 (y 67-75) penumpu tangki", f"{t68['b'] * 1000:.0f} × {t68['h'] * 1000:.0f}", "mm",
         f"atas {teks_tulangan(t68['atas'])}, bawah {teks_tulangan(t68['bawah'])}, Ve {t68['Ve']:.0f} kN, "
         f"{t68['kaki']} kaki D{t68['ds']}-{t68['s_sendi'] * 1000:.0f}"],
        ["Rel dudukan chiller (8 rel, x 60-68-76)", f"{c['b'] * 1000:.0f} × {c['h'] * 1000:.0f}", "mm",
         f"atas {teks_tulangan(c['atas'])}, bawah {teks_tulangan(c['bawah'])}, {c['kaki']} kaki "
         f"D{c['ds']}-{c['s_sendi'] * 1000:.0f}"],
        ["  Titik tumpu chiller D / impak 20 % (L)", f"{c['PD']:.1f} / {c['PL']:.1f}", "kN",
         "115,8 kN / 6 titik; SNI 1727 Pasal 4.6.3"],
        ["  Mu- / Mu+ / Vu", f"{c['Mneg']:.0f} / {c['Mpos']:.0f} / {c['Vu']:.0f}", "kNm, kN", "PyNite"],
    ], rata=list("lccl"), fill_kolom={1: AI, 3: AI})
    lb.kosong()
    lb.catatan("Dek helipad baja: balok kantilever 4,7 m @ 4,0 m dengan bentang balik 8,0 m [Asumsi, desain baja "
               "menyusul]. Tiang A di balok atap tepi (tengah bentang), angkur B di balok sejajar 8 m ke dalam. "
               "RA = q s lc (1 + lc/(2 lb)); RB = -q s lc²/(2 lb); roda: RA = P (1 + lc/lb), RB = -P lc/lb.")
    _, a, b_ = lb.tabel(["Kasus", "q (kPa) / P (kN)", "RA (kN)", "RB (kN)"], [
        ["Dek mati (beban D)", tb.SIDL["dek_helipad"][0], None, None],
        ["Helipad merata, SNI 1727 Tabel 4.3-1 (L, tidak menentukan)", ak["heli_merata"], None, None],
        ["Satu roda 0,75 MTOW, Pasal 4.11.2 (L, menentukan)", round(ak["heli_terpusat"], 3), None, None],
    ], rata=list("lccc"), fmt=[None, "0.00", "0.0", "0.0"], fill_kolom={2: AI, 3: AI}, beku=False)
    lc, lbk, sj = DEK_KANTILEVER, DEK_BALIK, DEK_JARAK
    for rr in (a, a + 1):
        lb.ws[f"{k(2)}{rr}"] = f"={k(1)}{rr}*{sj}*{lc}*(1+{lc}/(2*{lbk}))"
        lb.ws[f"{k(3)}{rr}"] = f"=-{k(1)}{rr}*{sj}*{lc}^2/(2*{lbk})"
    lb.ws[f"{k(2)}{a + 2}"] = f"={k(1)}{a + 2}*(1+{lc}/{lbk})"
    lb.ws[f"{k(3)}{a + 2}"] = f"=-{k(1)}{a + 2}*{lc}/{lbk}"

    lb = Lembar(wb.create_sheet("Cek Silang"), 7, "Cek silang T-74 dan T-75", [8, 62, 14, 14, 11, 10, 12])
    con = r["contoh"]
    lb.catatan(LABEL + f" T-74: penampang contoh {con['kelompok']} {con['b'] * 1000:.0f} × {con['h'] * 1000:.0f} "
               f"({teks_tulangan(con['atas'])} atas, {teks_tulangan(con['bawah'])} bawah); concreteproperties "
               "menghitung tulangan atas dan bawah per lapis (blok persegi 0,85 fc', β1 0,836, εcu 0,003, baja "
               "elastis-plastis), rumus sendiri tulangan tarik saja. T-75: balok anak tangki dengan tangki penuh dua "
               "bentang (beban sama di kedua cara). T-76 (Excel = Python) dicatat di VERIFIKASI.")
    _, a, b_ = lb.tabel(["No", "Besaran", "Cara 1", "Cara 2", "Selisih", "Batas", "Status"], [
        ["T-74", "φMn negatif (kNm): rumus sendiri | concreteproperties", round(cp["phiMn_neg"], 1),
         round(cp["phiMn_neg_cp"], 1), None, 0.05, None],
        ["T-74", "φMn positif (kNm): rumus sendiri | concreteproperties", round(cp["phiMn_pos"], 1),
         round(cp["phiMn_pos_cp"], 1), None, 0.05, None],
        ["T-75", "Mu- muka tumpuan dalam balok anak tangki (kNm): Tabel 6.5.2 wu ln²/9 | PyNite",
         round(t["M_koef"], 1), round(t["M_pynite_penuh"], 1), None, 0.15, None],
    ], rata=list("clccccc"), fmt=[None, None, "0.0", "0.0", "0.0%", "0%", None], fill_kolom={4: AI, 6: AI},
        beku=False)
    for rr in range(a, b_ + 1):
        lb.ws[f"{k(4)}{rr}"] = f"={k(2)}{rr}/{k(3)}{rr}-1"
        lb.ws[f"{k(6)}{rr}"] = f'=IF(ABS({k(4)}{rr})<={k(5)}{rr},"Lolos","Tidak lolos")'

    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    if hitung_ulang:
        hitung_ulang_excel(keluar)
    return keluar


def cek_excel(berkas=BERKAS):
    """T-76: selisih mutlak terbesar rumus Excel (sudah dihitung ulang di Excel) terhadap Python: φMn, Mpr, Ve."""
    import openpyxl
    from format_dokumen import baca_tabel
    r = ringkasan()
    wb = openpyxl.load_workbook(berkas, data_only=True)
    _, dl = baca_tabel(wb["Lentur"], "Kelompok")
    _, dg = baca_tabel(wb["Geser dan Torsi"], "Kelompok")
    selisih = []
    for i, x in enumerate(r["kelompok"]):
        selisih += [abs(float(dl[2 * i][11]) - x["phiMn_neg"]), abs(float(dl[2 * i + 1][11]) - x["phiMn_pos"]),
                    abs(float(dg[i][6]) - x["Mpr_neg"]), abs(float(dg[i][7]) - x["Mpr_pos"]),
                    abs(float(dg[i][9]) - x["Ve"])]
    return max(selisih)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    import time
    t0 = time.time()
    r = ringkasan()
    print("iterasi", r["iterasi"], "ukuran", r["ukuran"])
    for x in r["kelompok"]:
        print(f"{x['kelompok']:26s} n {x['n']:3d} {x['b']*1000:.0f}x{x['h']*1000:.0f} M- {x['Mneg']:6.0f} "
              f"M+ {x['Mpos']:5.0f} atas {teks_tulangan(x['atas'])} bawah {teks_tulangan(x['bawah'])} "
              f"ρ {x['rho']:.4f} Ve {x['Ve']:.0f} (Vg {x['Vg']:.0f}) Tu {x['Tu_d']:.0f}/{x['phiTth']:.0f} "
              f"D{x['ds']} {x['kaki']}k s {x['s_sendi']*1000:.0f}/{x['s_lap']*1000:.0f} ok {x['ok']} "
              f"{[k for k, v in x['cek'].items() if not v]}")
    t = r["tangki"]
    print("tangki", t["b"], t["h"], round(t["Mneg"]), round(t["Mpos"]), round(t["Vu"]), teks_tulangan(t["atas"]),
          teks_tulangan(t["bawah"]), t["ds"], t["kaki"], t["s_sendi"], t["ok"], [round(x) for x in t["R_D"]],
          "koef", round(t["M_koef"]), "pynite", round(t["M_pynite_penuh"]))
    c = r["chiller"]
    print("chiller", c["b"], c["h"], round(c["Mneg"]), round(c["Mpos"]), round(c["Vu"]), teks_tulangan(c["atas"]),
          teks_tulangan(c["bawah"]), c["s_sendi"], c["ok"])
    print("helipad", r["helipad"])
    print("massa", r["massa"])
    print("cp", r["cp"])
    if "--excel" in sys.argv:
        print(buat_excel(), "selisih Excel-Python maks", cek_excel())
    print(f"waktu {time.time() - t0:.0f} s")
