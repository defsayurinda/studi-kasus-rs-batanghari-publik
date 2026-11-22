"""Tahap 2 langkah 2.5: kelas situs gempa menurut SNI 1726:2019 Pasal 5 (Tabel 5, Pasal 5.3, 5.4).

v̄s = Σdi / Σ(di/vsi)          Pers. (1) hal. 31
N̄  = Σdi / Σ(di/Ni)           Pers. (2) hal. 32; N̄ch Pers. (3) hanya lapisan nonkohesif
s̄u = dc / Σ(di/sui)           Pers. (4)-(6) hal. 32, hanya lapisan kohesif, sui ≤ 250 kPa
"""
import math
from pathlib import Path

import numpy as np
import openpyxl

import tahap2_koreksi_data as kd
import tahap2_stratigrafi as st

AKAR = Path(__file__).resolve().parents[1]
BARU = AKAR / "01 Penyelidikan Tanah" / "Penyelidikan Tambahan"
OFFSET_DH = 3.0  # m, sumber downhole dari mulut lubang
ER = {"BH-4": 86, "BH-5": 85, "BH-6": 81, "BH-7": 53, "BH-8": 53, "BH-1": 53, "BH-2": 53, "BH-3": 53}
KOHESIF = {"U2", "U3", "U4", "U6", "U8"}
# su desain langkah 2.4 [usulan]: U4 = 5,2 + 1,09 z
SU = {"U1": None, "U2": 35.0, "U3": 8.0, "U6": 85.0, "U8": 150.0}


def _ws(nama):
    return openpyxl.load_workbook(BARU / "Geofisika Vs.xlsx", data_only=True)[nama]


def lokasi():
    hasil = {}
    for r in _ws("Lokasi").iter_rows(values_only=True):
        isi = [c for c in r if c is not None]
        if len(isi) >= 5 and isinstance(isi[2], (int, float)):
            hasil[isi[0]] = dict(metode=isi[1], x=isi[2], y=isi[3], elev=isi[4])
    return hasil


def masw():
    """{stasiun: [(dari, sampai, vs)]}; setengah ruang diperpanjang sampai 30 m."""
    hasil = {}
    for lembar in ("MASW L-1", "MASW L-2"):
        for r in _ws(lembar).iter_rows(values_only=True):
            isi = [c for c in r if c is not None]
            if len(isi) == 5 and str(isi[0]).startswith("L-") and isinstance(isi[1], int):
                sampai = 30.0 if isinstance(isi[3], str) else float(isi[3])
                hasil.setdefault(isi[0], []).append((float(isi[2]), sampai, float(isi[4])))
    return hasil


def vs30(lapisan, batas=30.0):
    """v̄s30 Pers. (1): lapisan dipotong di 30 m."""
    d_tot, t_tot = 0.0, 0.0
    for a, b, v in lapisan:
        b = min(b, batas)
        if b <= a:
            continue
        d_tot += b - a
        t_tot += (b - a) / v
    return d_tot / t_tot


def downhole():
    """Waktu tempuh S dikoreksi kemiringan: tc = t · z / √(z² + offset²); kecepatan interval antar-titik."""
    data = []
    for r in _ws("Downhole BH-5").iter_rows(values_only=True):
        isi = [c for c in r if c is not None]
        if len(isi) == 3 and all(isinstance(x, (int, float)) for x in isi):
            data.append(tuple(float(x) for x in isi))
    hasil = []
    for z, tp, ts in data:
        f = z / math.hypot(z, OFFSET_DH)
        hasil.append(dict(z=z, tp=tp, ts=ts, tsc=ts * f, tpc=tp * f))
    for i, h in enumerate(hasil):
        if i == 0:
            h["vs_int"] = h["z"] / (h["tsc"] / 1000)
            continue
        dt = (h["tsc"] - hasil[i - 1]["tsc"]) / 1000
        h["vs_int"] = (h["z"] - hasil[i - 1]["z"]) / dt if dt > 0 else None
        h["anomali"] = dt <= 0 or (i + 1 < len(hasil) and hasil[i + 1]["tsc"] - h["tsc"] > 2.5 * (h["tsc"] -
                                                                                                hasil[i - 1]["tsc"]))
    return hasil


def downhole_vs30():
    """v̄s30 langsung = 30 / tc(30 m) (sama dengan Pers. (1) karena Σdi/vsi = waktu tempuh)."""
    dh = {h["z"]: h for h in downhole()}
    return 30.0 / (dh[30.0]["tsc"] / 1000)


def downhole_lapisan(batas=30.0, buang=(23.0,)):
    """Lapisan 1 m dari waktu tempuh terkoreksi; titik bacaan anomali dibuang dan diinterpolasi."""
    dh = [h for h in downhole() if h["z"] not in buang]
    z = np.array([0.0] + [h["z"] for h in dh])
    t = np.array([0.0] + [h["tsc"] for h in dh]) / 1000
    lap = []
    for a in range(int(batas)):
        ta, tb = np.interp([a, a + 1], z, t)
        lap.append((float(a), float(a + 1), 1.0 / (tb - ta)))
    return lap


def _lapisan_bor(nama):
    return next(t for t in st.semua_titik() if t["nama"] == nama)["lapisan"]


def unit_di(lap, z):
    for lp in lap:
        if lp["atas"] <= z < lp["bawah"]:
            return lp["unit"]
    return lap[-1]["unit"]


def n_rata(bor, pakai_n60=False, batas=30.0, nonkohesif_saja=False):
    """N̄ Pers. (2)/(3): tiap uji SPT mewakili interval tengah-tengah antar-uji; WOH dianggap N = 1 [Asumsi]."""
    uji = sorted([u for u in kd.baca_spt() if u["bor"] == bor and kd.status_spt(u)[0] == "Ya"],
                 key=lambda u: u["dari"])
    lap = _lapisan_bor(bor)
    z = [u["dari"] + 0.225 for u in uji]
    batas_i = [0.0] + [(a + b) / 2 for a, b in zip(z, z[1:])] + [batas]
    d_tot, s = 0.0, 0.0
    for i, u in enumerate(uji):
        a, b = batas_i[i], min(batas_i[i + 1], batas)
        if b <= a:
            continue
        if nonkohesif_saja and unit_di(lap, z[i]) in KOHESIF:
            continue
        n = u["n"] * (ER[bor] / 60 if pakai_n60 else 1)
        n = min(max(n, 1.0), 100.0)  # ≤ 300 pukulan/m (= 100 per 0,3 m)
        d_tot += b - a
        s += (b - a) / n
    return d_tot / s if s else None


def su_rata(bor, batas=30.0):
    """s̄u Pers. (4)-(6) dari lapisan kohesif bor dan su desain langkah 2.4 (U4 = 5,2 + 1,09 z)."""
    lap = _lapisan_bor(bor)
    d_c, s = 0.0, 0.0
    for lp in lap:
        if lp["unit"] not in KOHESIF:
            continue
        a, b = lp["atas"], min(lp["bawah"], batas)
        if b <= a:
            continue
        if lp["unit"] == "U4":
            zz = np.linspace(a, b, 50)
            su = 5.2 + 1.09 * zz
            s += float(np.trapezoid(1 / su, zz))
        else:
            s += (b - a) / min(SU[lp["unit"]], 250)
        d_c += b - a
    return d_c / s


def kelas(vs=None, n=None, su=None):
    if vs is not None:
        return "SC" if vs > 350 else "SD" if vs >= 175 else "SE"
    if n is not None:
        return "SC" if n > 50 else "SD" if n >= 15 else "SE"
    return "SC" if su >= 100 else "SD" if su >= 50 else "SE"


def tebal_gambut_ha():
    """Tebal gambut saja (log bor tangan) dan gambut + lempung organik (lembar Titik)."""
    wb = openpyxl.load_workbook(BARU / "Pemetaan Gambut Bor Tangan.xlsx", data_only=True)
    gambut = {}
    for r in wb["Log Bor Tangan"].iter_rows(values_only=True):
        isi = [c for c in r if c is not None]
        if isi and str(isi[0]).startswith("HA-") and "Gambut" in str(isi[-1]):
            gambut[isi[0]] = isi[2] - isi[1]
    return gambut


if __name__ == "__main__":
    for s_, l in masw().items():
        print(s_, round(vs30(l), 1), kelas(vs=vs30(l)))
    print("downhole vs30", round(downhole_vs30(), 1), "lapisan", round(vs30(downhole_lapisan()), 1))
    for h in downhole():
        if h.get("anomali") or h["vs_int"] is None:
            print("anomali", h)
    for b in ER:
        print(b, "N", round(n_rata(b), 1), "N60", round(n_rata(b, True), 1), "Nch", round(n_rata(b, False, nonkohesif_saja=True), 1),
              "su", round(su_rata(b), 1))
    print(tebal_gambut_ha())
