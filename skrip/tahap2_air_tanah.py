"""Tahap 2 langkah 2.3: pembaca data air tanah dan analisis (uji pompa, piezometer, MAT desain, blow-in).

Sumber data: 'Uji Pompa dan Piezometer.xlsx' (penyelidikan tambahan) dan lembar 'Muka Air' di 'Bor dan SPT.xlsx'.
"""
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import openpyxl

AKAR = Path(__file__).resolve().parents[1]
LAMA = AKAR / "01 Penyelidikan Tanah"
BERKAS = LAMA / "Penyelidikan Tambahan" / "Uji Pompa dan Piezometer.xlsx"
GAMMA_W = 9.81


def _baris(sheet, path=BERKAS):
    ws = openpyxl.load_workbook(path, data_only=True)[sheet]
    hasil, kepala = [], None
    for r in ws.iter_rows(values_only=True):
        isi = list(r)
        while isi and isi[0] is None:
            isi.pop(0)
        if not isi:
            continue
        if kepala is None and isinstance(isi[0], str) and isi[0] in ("Nama", "Tahap", "Tanggal dan jam", "Tanggal"):
            kepala = [k for k in isi if k is not None]
            continue
        if kepala and isi[0] is not None and not str(isi[0]).startswith(("LEMBAR", "DATA")):
            hasil.append(dict(zip(kepala, isi)))
    return hasil


def instrumen():
    return {b["Nama"]: b for b in _baris("Sumur dan Instrumen")}


def uji_bertahap():
    return _baris("Uji Bertahap")


def uji_debit_tetap():
    return _baris("Uji Debit Tetap")


def pemulihan():
    return _baris("Pemulihan")


def sungai_selama_uji():
    return [(datetime.strptime(b["Tanggal dan jam"], "%Y-%m-%d %H:%M"), b["Muka air sungai (m)"])
            for b in _baris("Sungai Selama Uji")]


def harian():
    data = []
    for b in _baris("Pemantauan Harian"):
        d = dict(b)
        d["Tanggal"] = datetime.strptime(str(b["Tanggal"])[:10], "%Y-%m-%d")
        data.append(d)
    return data


def mingguan():
    lama = _baris("Muka Air", LAMA / "Bor dan SPT.xlsx")
    baru = _baris("Pemantauan Mingguan")
    hasil = []
    for b in lama + baru:
        d = dict(b)
        t = b["Tanggal"]
        d["Tanggal"] = t if isinstance(t, datetime) else datetime.strptime(str(t)[:10], "%Y-%m-%d")
        hasil.append(d)
    return sorted(hasil, key=lambda d: d["Tanggal"])


# ------------------------------------------------------------------ uji pompa
def thiem_tertekan(q, r1, r2, s1, s2, b):
    """k (m/s) akuifer tertekan, kondisi tunak. r1 jauh, r2 dekat; s = penurunan muka air (m).
    FHWA GEC 5 (NHI-16-072) Pers. 10.24 hal. 10-47 ditulis dengan tinggi tekan h; h1 - h2 = s2 - s1."""
    return q * math.log(r1 / r2) / (2 * math.pi * b * (s2 - s1))


def cooper_jacob(t_menit, s, r, q, t_awal=None, t_akhir=None):
    """Kemiringan s terhadap log10 t: T = 2,30 Q / (4 π Δs), S = 2,25 T t0 / r².
    [Literatur: Cooper dan Jacob 1946; belum ada di acuan/]"""
    t = np.asarray(t_menit, float)
    s = np.asarray(s, float)
    m = np.ones_like(t, bool)
    if t_awal is not None:
        m &= t >= t_awal
    if t_akhir is not None:
        m &= t <= t_akhir
    a, b0 = np.polyfit(np.log10(t[m] * 60), s[m], 1)  # s = a log10(t) + b0, t dalam detik
    tr = 2.30 * q / (4 * math.pi * a)
    t0 = 10 ** (-b0 / a)
    return dict(T=tr, S=2.25 * tr * t0 / r ** 2, ds=a, t0=t0, n=int(m.sum()))


# ------------------------------------------------------------------ analisis
STATIS = {"PW-1": 2.721, "OW-1": 2.606, "OW-2": 2.448}  # m dari bibir pipa, 8 Des 2026 07.55
JARAK = {"OW-1": 10.0, "OW-2": 30.0}
TEBAL_AKUIFER = 9.3  # m di PW-1: U5 BH-5 9,46-18,97 dan BH-2 9,51-18,68 (langkah 2.2)
TEBING = [(40, -12), (60, -10), (80, -7), (90, -6.5), (100, -6)]  # puncak tebing (langkah 2.2, GT-01)
JENDELA_TUNAK = [(960, 1800), (2160, 4320)]  # menit; sebelum dan sesudah pompa mati 18 menit


def jarak_ke_tebing(x, y):
    xs, ys = zip(*TEBING)
    return y - float(np.interp(x, xs, ys))


def ringkas_uji_pompa():
    dt = uji_debit_tetap()
    t = np.array([b["Waktu sejak mulai (menit)"] for b in dt], float)
    q = np.array([b["Debit (L/s)"] for b in dt], float) / 1000
    s = {k: np.array([b[f"{k} kedalaman air (m)"] for b in dt], float) - STATIS[k] for k in STATIS}
    tunak = np.zeros_like(t, bool)
    for a, b in JENDELA_TUNAK:
        tunak |= (t >= a) & (t <= b)
    q_rata = float(q[(t >= 35) & (q > 0)].mean())
    s1, s2 = float(s["OW-1"][tunak].mean()), float(s["OW-2"][tunak].mean())
    k_thiem = thiem_tertekan(q_rata, JARAK["OW-2"], JARAK["OW-1"], s2, s1, TEBAL_AKUIFER)
    # sumur bayangan (batas isian sungai): s = Q/(2πT) ln(r_bayangan / r)
    a_pw = jarak_ke_tebing(65, 40)
    bay = (65.0, 40.0 - 2 * a_pw)
    t_bay = {}
    for ow, (x, y) in {"OW-1": (75, 40), "OW-2": (95, 40)}.items():
        rb = math.hypot(x - bay[0], y - bay[1])
        sw = s1 if ow == "OW-1" else s2
        t_bay[ow] = q_rata / (2 * math.pi * sw) * math.log(rb / JARAK[ow])
    q_awal = float(q[t <= 30].mean())
    cj = {ow: cooper_jacob(t, s[ow], JARAK[ow], q_awal, t_awal=1 if ow == "OW-1" else 3, t_akhir=20)
          for ow in ("OW-1", "OW-2")}
    # pemulihan (Theis-Jacob): s' terhadap log10(t/t')
    pm = pemulihan()
    tp = np.array([b["Waktu sejak pompa berhenti (menit)"] for b in pm], float)
    tt = np.array([b["Waktu sejak mulai (menit)"] for b in pm], float)
    sr = np.array([b["OW-1 kedalaman air (m)"] for b in pm], float) - STATIS["OW-1"]
    m = (tp >= 1) & (tp <= 20)
    kem = np.polyfit(np.log10(tt[m] / tp[m]), sr[m], 1)[0]
    t_pulih = 2.30 * q_rata / (4 * math.pi * kem)
    return dict(q_rata=q_rata, q_awal=q_awal, s1=s1, s2=s2, k_thiem=k_thiem, T_thiem=k_thiem * TEBAL_AKUIFER,
                a_pw=a_pw, T_bayangan=t_bay, cj=cj, T_pulih=t_pulih, t=t, s=s, q=q, tp=tp, tt=tt, sr=sr)


def uji_bertahap_jacob():
    """s_w = B Q + C Q² dari penurunan akhir tiap tahap (Jacob 1947) [Literatur; belum ada di acuan/]."""
    data = uji_bertahap()
    akhir = {}
    for b in data:
        if b["Waktu sejak mulai (menit)"] % 100 == 90 or b["Waktu sejak mulai (menit)"] in (90, 190, 290, 390):
            akhir[b["Tahap"]] = b
    q = np.array([np.mean([x["Debit (L/s)"] for x in data if x["Tahap"] == k]) for k in sorted(akhir)]) / 1000
    sw = np.array([akhir[k]["PW-1 kedalaman air (m)"] - STATIS["PW-1"] for k in sorted(akhir)])
    c, b = np.polyfit(q, sw / q, 1)  # s/Q = B + C Q
    return dict(q=q, sw=sw, B=b, C=c, efisiensi=[b * qi / (b * qi + c * qi ** 2) for qi in q])


SENSOR_B = ["PZ-2B (m)", "PZ-3B (m)", "PZ-4B (m)"]
SENSOR_A = ["PZ-2A (m)", "PZ-3A (m)", "PZ-4A (m)"]


def bersihkan_harian():
    """Data harian tanpa hari uji pompa (sensor B), tanpa lonjakan petir PZ-3A 14 Feb 2027."""
    H = harian()
    hasil = []
    for d in H:
        e = dict(d)
        if datetime(2026, 12, 7) <= d["Tanggal"] <= datetime(2026, 12, 13):
            for k in SENSOR_B:
                e[k] = None
        if d["Tanggal"] == datetime(2027, 2, 14):
            e["PZ-3A (m)"] = None
        hasil.append(e)
    return hasil


def regresi_jeda(sensor, jeda_maks=10):
    """h(t) = a + b · sungai(t - L); pilih L (hari) dengan r terbesar."""
    H = bersihkan_harian()
    riv = np.array([d["Sungai (m)"] for d in H], float)
    h = np.array([d[sensor] if isinstance(d[sensor], (int, float)) else np.nan for d in H], float)
    terbaik = None
    for L in range(jeda_maks + 1):
        x = riv[:len(riv) - L] if L else riv
        y = h[L:]
        m = ~np.isnan(y)
        b, a = np.polyfit(x[m], y[m], 1)
        r = float(np.corrcoef(x[m], y[m])[0, 1])
        if terbaik is None or r > terbaik["r"]:
            terbaik = dict(sensor=sensor, L=L, a=float(a), b=float(b), r=r, n=int(m.sum()))
    return terbaik


def puncak_banjir():
    H = bersihkan_harian()
    i = int(np.argmax([d["Sungai (m)"] for d in H]))
    awal = H[0]
    hasil = {"Sungai (m)": (H[i]["Tanggal"], H[i]["Sungai (m)"])}
    for k in SENSOR_B + SENSOR_A:
        nil = [(d["Tanggal"], d[k]) for d in H if isinstance(d[k], (int, float))]
        tg, v = max(nil, key=lambda z: z[1])
        rasio = (v - awal[k]) / (H[i]["Sungai (m)"] - awal["Sungai (m)"])
        hasil[k] = (tg, v, rasio)
    return hasil


def regresi_pz1():
    W = [w for w in mingguan() if isinstance(w.get("PZ-1 elevasi (m)"), (int, float))]
    x = np.array([w["Muka air sungai (m)"] for w in W], float)
    y = np.array([w["PZ-1 elevasi (m)"] for w in W], float)
    b, a = np.polyfit(x, y, 1)
    return dict(a=float(a), b=float(b), r=float(np.corrcoef(x, y)[0, 1]), n=len(W), x=x, y=y,
                tgl=[w["Tanggal"] for w in W])


# Profil untuk blow-in (langkah 2.2): (nama, elevasi muka tanah, [(bawah lapisan dari muka tanah, γ)], atas pasir)
GAMMA = {"U1": 17.0, "U2": 17.8, "U3": 10.7, "U4": 15.2}
PROFIL = {
    "Tengah tapak (BH-5)": (9.95, [(0.31, "U1"), (1.62, "U2"), (9.46, "U4")]),
    "Utara, gambut (BH-3)": (9.23, [(0.41, "U1"), (1.13, "U2"), (3.97, "U3"), (9.73, "U4")]),
    "Sisi tebing (CPTu-6)": (10.55, [(0.4, "U1"), (1.35, "U2"), (9.0, "U4")]),
}
FK_BLOWIN = 1.25  # SNI 8460:2017 Pasal 10.3.6.7.2 hal. 211


def fk_blowin(profil, elev_dasar, h_akuifer):
    """FK = σv total lapisan kedap antara dasar galian dan atas pasir / u di atas pasir."""
    elev0, lap = PROFIL[profil]
    z_pasir = elev0 - lap[-1][0]
    if elev_dasar <= z_pasir:
        return 0.0
    sig, atas = 0.0, 0.0
    for bawah, u in lap:
        z_a, z_b = elev0 - atas, elev0 - bawah
        tebal = max(0.0, min(z_a, elev_dasar) - z_b)
        sig += GAMMA[u] * tebal
        atas = bawah
    u = GAMMA_W * max(0.0, h_akuifer - z_pasir)
    return float("inf") if u == 0 else sig / u


def elev_dasar_min(profil, h_akuifer, fk=FK_BLOWIN):
    """Elevasi dasar galian terendah yang masih memenuhi FK (dicari dengan bagi dua)."""
    elev0, lap = PROFIL[profil]
    lo, hi = elev0 - lap[-1][0], elev0
    if fk_blowin(profil, hi, h_akuifer) < fk:
        return None  # tanpa galian pun tidak memenuhi
    for _ in range(60):
        mid = (lo + hi) / 2
        if fk_blowin(profil, mid, h_akuifer) >= fk:
            hi = mid
        else:
            lo = mid
    return hi


SUNGAI_BULANAN = [  # TOR Lampiran A: (bulan, rata-rata, maksimum tercatat), datum lokal
    ("Jan", 8.60, 11.20), ("Feb", 8.40, 10.60), ("Mar", 8.10, 10.10), ("Apr", 7.60, 9.40), ("Mei", 6.40, 8.30),
    ("Jun", 5.30, 7.20), ("Jul", 4.60, 6.30), ("Agu", 4.10, 5.40), ("Sep", 4.00, 5.60), ("Okt", 4.80, 7.00),
    ("Nov", 6.50, 8.90), ("Des", 8.00, 10.40)]
SELISIH_SURUT = 0.9  # m; PZ-1 di atas sungai saat surut (Sep 2026) [Uji sendiri: Muka Air BH-1]


if __name__ == "__main__":
    ins = instrumen()
    print({k: (v["x lokal (m)"], v["y lokal (m)"]) for k, v in ins.items()})
    dt = uji_debit_tetap()
    print(len(dt), dt[0], dt[-1])
    for b in dt:
        if b.get("Keterangan"):
            print("KET", b)
    print(len(pemulihan()), len(uji_bertahap()), len(harian()), len(mingguan()))
