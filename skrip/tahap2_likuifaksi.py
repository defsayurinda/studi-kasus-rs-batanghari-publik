"""Tahap 2 langkah 2.6: pemicu likuifaksi pasir U5 (Boulanger dan Idriss 2014, UCD/CGM-14/01).

Persamaan (nomor dan halaman laporan):
  CSR = 0,65 (σv/σ'v) (amax/g) rd                         Pers. 2.2  hal. 5
  rd = exp[α(z) + β(z) M]                                  Pers. 2.14 hal. 8
  CN = (Pa/σ'v)^m ≤ 1,7; m SPT/CPT                         Pers. 2.15 hal. 10
  Kσ = 1 - Cσ ln(σ'v/Pa) ≤ 1,1                             Pers. 2.16 hal. 11
  MSF = 1 + (MSFmax - 1)(8,64 exp(-M/4) - 1,325)           Pers. 2.19-2.21 hal. 14
  Δqc1N, Δ(N1)60 (butir halus)                             Pers. 2.22-2.23 hal. 15
  CRR M7,5 σ'1 atm (CPT, SPT)                              Pers. 2.24-2.25 hal. 17
  Ic, Q, F; FC = 80 (Ic + CFC) - 137                       Pers. 2.26-2.30 hal. 19-21
Beban gempa: PGAM = FPGA · PGA (SNI 1726:2019 Pasal 6.7.3 Pers. 15, Tabel 10 hal. 39).
"""
import math

import numpy as np
import openpyxl

import tahap2_koreksi_data as kd
import tahap2_parameter as tp
import tahap2_stratigrafi as st

PA = 101.325  # kPa
GW = 9.81
PGA = 0.1644  # g, batuan dasar MCEG, Desain Spektra Indonesia PUPR (2021) di -1,582; 103,616 (Kota Jambi)
SS, S1 = 0.3337, 0.2642


def fpga_se(pga):
    """SNI 1726:2019 Tabel 10, kelas SE: 2,4 (≤ 0,1); 1,9 (0,2); 1,6 (0,3); 1,4 (0,4); 1,2 (0,5); 1,1 (≥ 0,6)."""
    x = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    y = [2.4, 1.9, 1.6, 1.4, 1.2, 1.1]
    return float(np.interp(pga, x, y))


AMAX = PGA * fpga_se(PGA)
MW = 7.0  # PuSGeN 2017 deagregasi, Gambar 4.28 hal. 166: Kota Jambi ±6,6-7,2 [dibaca dari peta]
H_AKUIFER = 9.5  # m; muka air maksimum tahunan rata-rata sungai (TOR Lampiran A) [Asumsi tinggi tekan U5 saat gempa]
GAMMA = {"U1": 17.0, "U2": 17.8, "U3": 10.7, "U4": 15.2, "U5": 19.0, "U6": 19.1, "U7": 20.0, "U8": 20.0}


def rd(z, m=MW):
    a = -1.012 - 1.126 * math.sin(z / 11.73 + 5.133)
    b = 0.106 + 0.118 * math.sin(z / 11.28 + 5.142)
    return math.exp(a + b * m)


def msf(m, msfmax):
    return 1 + (msfmax - 1) * (8.64 * math.exp(-m / 4) - 1.325)


def tegangan(lapisan, elev, z, h=H_AKUIFER):
    """σv dan σ'v di kedalaman z. u = γw (h - elevasi titik) di pasir dan di bawahnya; di lapisan atas
    u hidrostatik dari MAT 0,7 m [Asumsi], tidak melebihi nilai akuifer."""
    sv = 0.0
    for lp in lapisan:
        if z <= lp["atas"]:
            break
        sv += GAMMA[lp["unit"]] * (min(z, lp["bawah"]) - lp["atas"])
    u = max(0.0, GW * (h - (elev - z)))
    return sv, sv - u


# ------------------------------------------------------------------ SPT
def crr_spt(n160cs):
    x = n160cs
    return math.exp(x / 14.1 + (x / 126) ** 2 - (x / 23.6) ** 3 + (x / 25.4) ** 4 - 2.8)


def spt_satu(n60, fc, sv, sve, z, m=MW, amax=AMAX):
    dn = math.exp(1.63 + 9.7 / (fc + 0.01) - (15.7 / (fc + 0.01)) ** 2)
    n160cs = n60  # iterasi CN (m bergantung (N1)60cs)
    for _ in range(50):
        mm = 0.784 - 0.0768 * math.sqrt(min(n160cs, 46))
        cn = min(1.7, (PA / sve) ** mm)
        n160 = cn * n60
        baru = n160 + dn
        if abs(baru - n160cs) < 1e-6:
            break
        n160cs = baru
    csr = 0.65 * sv / sve * amax * rd(z, m)
    msfmax = min(2.2, 1.09 + (n160cs / 31.5) ** 2)
    cs = min(0.3, 1 / (18.9 - 2.55 * math.sqrt(min(n160cs, 37))))
    ks = min(1.1, 1 - cs * math.log(sve / PA))
    crr = crr_spt(n160cs) * msf(m, msfmax) * ks
    return dict(cn=cn, n160=n160, dn=dn, n160cs=n160cs, csr=csr, rd=rd(z, m), msf=msf(m, msfmax), ks=ks,
                crr75=crr_spt(n160cs), crr=crr, fs=crr / csr)


def fc_saringan():
    """{(bor, dari): lolos 0,075 mm (%)} dari analisis saringan lama dan tambahan."""
    hasil = {}
    for path in (tp.LAMA / "Laboratorium.xlsx", tp.BARU / "Laboratorium Tambahan.xlsx"):
        ws = openpyxl.load_workbook(path, data_only=True)["Analisis Saringan"]
        for r in ws.iter_rows(values_only=True):
            isi = [c for c in r if c is not None]
            if isi and str(isi[0]).startswith("BH") and isinstance(isi[-1], (int, float)):
                hasil[(isi[0], float(isi[2]))] = float(isi[-1])
    return hasil


def analisis_spt(m=MW, amax=AMAX, h=H_AKUIFER):
    T = {t["nama"]: t for t in st.semua_titik()}
    fcs = fc_saringan()
    fc_med = float(np.median(list(fcs.values())))
    hasil = []
    for u in kd.baca_spt():
        if kd.status_spt(u)[0] != "Ya" or u["jenis"] == "Penolakan":
            continue
        t = T[u["bor"]]
        z = u["dari"] + 0.225
        unit = tp.unit_di(t, z)
        if unit != "U5":
            continue
        fc = fcs.get((u["bor"], float(u["dari"])))
        sumber_fc = "saringan" if fc is not None else "median"
        fc = fc if fc is not None else fc_med
        sv, sve = tegangan(t["lapisan"], t["elev"], z, h)
        n60 = u["n"] * kd_er(u["bor"]) / 60
        r = spt_satu(n60, fc, sv, sve, z, m, amax)
        hasil.append(dict(bor=u["bor"], z=z, elev=t["elev"] - z, n=u["n"], n60=n60, fc=fc, sumber_fc=sumber_fc,
                          sv=sv, sve=sve, **r))
    return hasil


def kd_er(bor):
    return tp.ER[bor]


# ------------------------------------------------------------------ CPT
def crr_cpt(q):
    return math.exp(q / 113 + (q / 1000) ** 2 - (q / 140) ** 3 + (q / 137) ** 4 - 2.80)


def ic_robertson(qt, fs, sv, sve):
    """Ic Pers. 2.26-2.28; eksponen n: 1,0 lalu 0,5 bila Ic < 2,6 (Robertson dan Wride 1998, dirujuk IB2014 hal. 19)."""
    qn = max(qt - sv, 1e-3)
    f = fs / qn * 100
    for n in (1.0, 0.5):
        q = qn / PA * (PA / sve) ** n
        ic = math.sqrt((3.47 - math.log10(max(q, 1e-3))) ** 2 + (1.22 + math.log10(max(f, 1e-3))) ** 2)
        if n == 1.0 and ic >= 2.6:
            return ic
    return ic


def cpt_satu(qt_kpa, fs, sv, sve, z, m=MW, amax=AMAX, cfc=0.0):
    ic = ic_robertson(qt_kpa, fs, sv, sve)
    fc = min(100.0, max(0.0, 80 * (ic + cfc) - 137))
    qcn = qt_kpa / PA
    q1cs = qcn
    for _ in range(60):
        mm = 1.338 - 0.249 * min(max(q1cs, 21), 254) ** 0.264
        cn = min(1.7, (PA / sve) ** mm)
        q1 = cn * qcn
        dq = (11.9 + q1 / 14.6) * math.exp(1.63 - 9.7 / (fc + 2) - (15.7 / (fc + 2)) ** 2)
        baru = q1 + dq
        if abs(baru - q1cs) < 1e-6:
            break
        q1cs = baru
    csr = 0.65 * sv / sve * amax * rd(z, m)
    msfmax = min(2.2, 1.09 + (q1cs / 180) ** 3)
    cs = min(0.3, 1 / (37.3 - 8.27 * min(q1cs, 211) ** 0.264))
    ks = min(1.1, 1 - cs * math.log(sve / PA))
    crr = crr_cpt(q1cs) * msf(m, msfmax) * ks
    return dict(ic=ic, fc=fc, qc1n=q1, dq=dq, qc1ncs=q1cs, csr=csr, msf=msf(m, msfmax), ks=ks, crr=crr,
                fs_liq=crr / csr if ic < 2.6 else None)


def analisis_cpt(m=MW, amax=AMAX, h=H_AKUIFER, langkah=0.05):
    P = tp.profil_cptu()
    hasil = {}
    for n, p in P.items():
        t = p["titik"]
        baris = []
        for i, z in enumerate(p["z"]):
            if p["unit"][i] != "U5":
                continue
            sv, sve = tegangan(t["lapisan"], t["elev"], z, h)
            qt = p["qt"][i] * 1000
            fs = tp.profil_cptu  # placeholder agar linter tidak mengeluh
            fs = float(_fs(t, i))
            r = cpt_satu(qt, fs, sv, sve, z, m, amax)
            baris.append(dict(z=float(z), qt=qt, fs=fs, sv=sv, sve=sve, **r))
        hasil[n] = baris
    return hasil


_FS = {}


def _fs(t, i):
    if t["nama"] not in _FS:
        data = kd.baca_cptu()[t["nama"]]
        _FS[t["nama"]] = [d[2] for d in data]
    return _FS[t["nama"]][i]


def ringkas_cpt(hasil):
    """Tebal lapisan FS < 1 dan FS < 1,2 per CPTu (Ic < 2,6 saja), langkah data 0,05 m."""
    keluar = {}
    for n, b in hasil.items():
        fs = [x["fs_liq"] for x in b if x["fs_liq"] is not None]
        keluar[n] = dict(n=len(b), n_pasir=len(fs), tebal_fs1=0.05 * sum(1 for f in fs if f < 1.0),
                         tebal_fs12=0.05 * sum(1 for f in fs if f < 1.2), fs_min=min(fs) if fs else None,
                         fs_med=float(np.median(fs)) if fs else None)
    return keluar


if __name__ == "__main__":
    print(f"PGA {PGA}, FPGA {fpga_se(PGA):.3f}, amax {AMAX:.3f} g, Mw {MW}")
    sp = analisis_spt()
    fsv = [x["fs"] for x in sp]
    print("SPT n", len(sp), "FS min", round(min(fsv), 2), "median", round(float(np.median(fsv)), 2),
          "FS<1:", sum(f < 1 for f in fsv), "FS<1.2:", sum(f < 1.2 for f in fsv))
    for x in sorted(sp, key=lambda x: x["fs"])[:8]:
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in x.items() if k in (
            "bor", "z", "n", "n60", "fc", "sve", "n160cs", "csr", "crr", "fs")})
    for mm in (6.5, 7.5):
        f2 = [x["fs"] for x in analisis_spt(m=mm)]
        print("M", mm, "FS min", round(min(f2), 2), "FS<1:", sum(f < 1 for f in f2))
    c = analisis_cpt()
    for n, r in ringkas_cpt(c).items():
        print(n, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
