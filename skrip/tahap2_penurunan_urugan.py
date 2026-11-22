"""Tahap 2 penyelesaian: penurunan akibat urugan halaman ke +11,50 (TOR butir 4) di setiap titik penyelidikan.

Rumus dan sumber:
- Penurunan primer 1D: S = Σ H [Cr/(1+e0) log(σ'p/σ'0) + Cc/(1+e0) log(σ'f/σ'p)]  FHWA NHI-06-088 Bab 7.5,
  Pers. 7-2 hal. 7-24 (Cc/(1+e0) = Ccε, hal. 7-25); bagian terkonsolidasi lebih memakai Cr.
- Waktu: t = Tv Hdr² / cv, Tv(90 %) = 0,848                                 Pers. 7-8 hal. 7-31, Tabel 7-4 hal. 7-32
- Sekunder: S = Σ H Cα/(1+e0) log(t2/t1)                                    Bab 7.5.4 hal. 7-38
- Amblas/desakan lateral: bahaya bila γ H urugan > 3 su                      Pers. 7-11 hal. 7-41
- PVD: t = dc²/(8 ch) [F(n) + Fs] ln(1/(1-U)), F(n) = ln(dc/dw) - 0,75     FHWA GEC 13 Vol. I Pers. 2-1, 2-2
  hal. 2-32; dc = 1,05 s (segitiga) hal. 2-33; dw = 2(a+b)/π Pers. 2-3 dan Fs ≈ 2 hal. 2-35
Parameter dari 2.4 (disetujui Defsa). Urugan dianggap luas (Δσ tetap terhadap kedalaman).
"""
import math

import numpy as np

import tahap2_stratigrafi as st

ELEV_RENCANA = 11.50  # TOR butir 4
GAMMA_URUG = 19.0  # kN/m³ [Asumsi: urugan tanah dipadatkan]
GW = 9.81
MAT = 0.7  # m di bawah muka tanah asli (2.3)
ATAS_U5_HA = -0.3  # elevasi atas U5 untuk bor tangan yang tidak mencapainya [Asumsi: median bor]
T_DESAIN = 50.0  # tahun, umur rencana untuk pemampatan sekunder [Asumsi]
CV = 1.8  # m²/th (2.4)
CH = 4.5  # m²/th (2.4)
DW = 2 * (0.100 + 0.004) / math.pi  # m, PVD 100 × 4 mm (Pers. 2-3)
FS_GANGGUAN = 2.0

PAR = {  # γ, e0, Cc, Cr, Cα (2.4)
    "U1": (17.0, None, 0.0, 0.0, 0.0),
    "U2": (17.8, 1.09, 0.38, 0.035, 0.0),
    "U3": (10.7, 6.0, 3.5, 0.36, 0.21),
    "U4": (15.2, 2.05, 0.75, 0.075, 0.03),
    "U5": (19.0, None, 0.0, 0.0, 0.0),
    "U6": (19.1, 0.77, 0.37, 0.05, 0.0),
    "U7": (20.0, None, 0.0, 0.0, 0.0),
    "U8": (20.0, None, 0.0, 0.0, 0.0),
}


def sigma_p(unit, z, sv0):
    if unit == "U2":
        return max(96.0, sv0)
    if unit == "U3":
        return sv0 + 7.0  # lab BH-7 UD-2 dan BH-3 UD-2: σ'p 25-27 pada σ'v0 ±18-20
    if unit == "U4":
        return sv0 + min(18.0, max(0.0, 18.0 * (8.5 - z) / 5.5))  # POP 2.4
    if unit == "U6":
        return max(400.0, sv0)
    return sv0


def lapisan_lengkap(t):
    lap = [dict(lp) for lp in t["lapisan"]]
    if t["jenis"] == "Bor tangan":
        dasar4 = t["elev"] - ATAS_U5_HA
        if lap[-1]["unit"] == "U4":
            lap[-1]["bawah"] = dasar4
        else:  # HA-9 berhenti di gambut: anggap gambut sampai akhir bor, lalu U4
            lap.append(dict(atas=lap[-1]["bawah"], bawah=dasar4, unit="U4"))
        lap.append(dict(atas=dasar4, bawah=dasar4 + 9.0, unit="U5"))
    return lap


def hitung_titik(t, langkah=0.1):
    lap = lapisan_lengkap(t)
    tebal_urug = max(0.0, ELEV_RENCANA - t["elev"])
    dsig = GAMMA_URUG * tebal_urug
    per_unit = {}
    sek = 0.0
    sv = 0.0
    tebal4 = 0.0
    zmaks = min(lap[-1]["bawah"], 40.0)
    for lp in lap:
        a, b = lp["atas"], min(lp["bawah"], zmaks)
        u = lp["unit"]
        g, e0, cc, cr, ca = PAR[u]
        n = max(1, int(round((b - a) / langkah)))
        h = (b - a) / n
        for i in range(n):
            z = a + (i + 0.5) * h
            sv_z = sv + g * (i + 0.5) * h
            u0 = GW * max(0.0, z - MAT)
            s0 = max(sv_z - u0, 1.0)
            if e0 is None:
                continue
            sp = sigma_p(u, z, s0)
            sf = s0 + dsig
            if sf <= sp:
                d = h * cr / (1 + e0) * math.log10(sf / s0)
            else:
                d = h * (cr / (1 + e0) * math.log10(sp / s0) + cc / (1 + e0) * math.log10(sf / sp))
            per_unit[u] = per_unit.get(u, 0.0) + d
            if ca:
                t1 = 1.0 if u == "U3" else None  # tahun; akhir primer gambut [Asumsi]
                if u == "U4":
                    t1 = t90_tanpa_pvd(None)
                sek += h * ca / (1 + e0) * math.log10(T_DESAIN / t1)
        sv += g * (b - a)
        if u == "U4":
            tebal4 += b - a
    primer = sum(per_unit.values())
    return dict(nama=t["nama"], jenis=t["jenis"], x=t["x"], y=t["y"], elev=t["elev"], urug=tebal_urug, dsig=dsig,
                per_unit=per_unit, primer=primer, sekunder=sek, total=primer + sek, tebal_u4=tebal4,
                t90=0.848 * (tebal4 / 2) ** 2 / CV if tebal4 else None)


def t90_tanpa_pvd(tebal_u4=8.0):
    tebal_u4 = 8.0 if tebal_u4 is None else tebal_u4
    return 0.848 * (tebal_u4 / 2) ** 2 / CV


def t_pvd(s, u=0.9, fs=FS_GANGGUAN, ch=CH):
    dc = 1.05 * s
    fn = math.log(dc / DW) - 0.75
    return dc ** 2 / (8 * ch) * (fn + fs) * math.log(1 / (1 - u))


def amblas(t):
    """Pers. 7-11: γH urugan dibanding 3 su lapisan lunak teratas (su desain 2.4)."""
    lap = lapisan_lengkap(t)
    su_min = 35.0
    for lp in lap:
        if lp["unit"] == "U3":
            su_min = min(su_min, 8.0)
        if lp["unit"] == "U4":
            su_min = min(su_min, 5.2 + 1.09 * lp["atas"])
    q = GAMMA_URUG * max(0.0, ELEV_RENCANA - t["elev"])
    return q, 3 * su_min, q > 3 * su_min


def semua():
    return [hitung_titik(t) for t in st.semua_titik()]


if __name__ == "__main__":
    for r in semua():
        print(f"{r['nama']:7s} elev {r['elev']:5.2f} urug {r['urug']:.2f} Δσ {r['dsig']:5.1f} primer {r['primer']:.3f}"
              f" sek {r['sekunder']:.3f} total {r['total']:.3f}", {k: round(v, 3) for k, v in r["per_unit"].items()})
    print("t90 tanpa PVD (U4 8 m)", round(t90_tanpa_pvd(8.0), 1), "th")
    for s in (1.0, 1.2, 1.5, 2.0):
        print("PVD s", s, "t90", round(t_pvd(s) * 12, 1), "bulan")
