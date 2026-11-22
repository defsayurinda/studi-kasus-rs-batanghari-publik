"""Tahap 2 langkah 2.4: parameter tanah per unit (indeks, kuat geser, pemampatan, konsolidasi, sudut geser).

Sumber rumus (dicatat juga di Excel 2.4):
- su = (qt - σv0) / Nkt                       FHWA GEC 5 (NHI-16-072) Pers. 7.13 hal. 7-36
- σ'p = 0,33 (qt - σv0)  (lempung utuh, m' = 1) GEC 5 Gambar 6-23 hal. 6-29
- ch = T* a² √Ir / t,  T*50 (u2) = 0,245      GEC 5 Pers. 6.19 hal. 6-36, Tabel 6-7 hal. 6-37; Un Pers. 6.20
- Cα/Cc ≈ 0,04 ± 0,01 (anorganik), 0,06 ± 0,01 (gambut)  GEC 5 hal. 6-46
- φ' = √(15,4 (N1)60) + 20                     GEC 5 Pers. 7.23 hal. 7-55 (Hatanaka dan Uchida)
- (N1)60 = CN N60, CN = 0,77 log10(20/po), po dalam tsf, CN ≤ 2   FHWA NHI-06-088 Pers. 3-3 hal. 3-56
"""
import math
from pathlib import Path

import numpy as np
import openpyxl

import tahap2_koreksi_data as kd
import tahap2_mutu_contoh as mc
import tahap2_stratigrafi as st

AKAR = Path(__file__).resolve().parents[1]
LAMA = AKAR / "01 Penyelidikan Tanah"
BARU = LAMA / "Penyelidikan Tambahan"
GW = 9.81
MAT = 0.7  # m di bawah muka tanah; median SP-1 Sep 2026 - Mar 2027 (langkah 2.3, kondisi normal)
JARI_KONUS = math.sqrt(10 / math.pi) / 100  # m (konus 10 cm²)
T50_U2 = 0.245
IR = 75  # [Asumsi: lempung lunak plastisitas tinggi, OCR ±1,5; GEC 5 Gambar 6-33 dibaca kasar; rentang 50-150]
TIDAK_DIPAKAI = {("BH-2", "UD-2"): "perolehan 64 %, tabung retak (Tahap 1 no. 9); mutu buruk (2.1)",
                 ("BH-7", "UD-3"): "mutu buruk, Δe/e0 0,093 (2.1)"}
ER = {"BH-4": 86, "BH-5": 85, "BH-6": 81, "BH-7": 53, "BH-8": 53, "BH-1": 53, "BH-2": 53, "BH-3": 53}


def _lapisan():
    return {t["nama"]: t for t in st.semua_titik()}


def unit_di(titik, z):
    for lp in titik["lapisan"]:
        if lp["atas"] <= z < lp["bawah"]:
            return lp["unit"]
    return titik["lapisan"][-1]["unit"]


def _baris(path, sheet):
    ws = openpyxl.load_workbook(path, data_only=True)[sheet]
    kepala, hasil = None, []
    for r in ws.iter_rows(values_only=True):
        isi = list(r)
        while isi and isi[0] is None:
            isi.pop(0)
        if not isi:
            continue
        if kepala is None and isi[0] == "Titik":
            kepala = isi
            continue
        if kepala and isinstance(isi[0], str) and isi[0][:2] in ("BH", "BT"):
            hasil.append(dict(zip(kepala, isi)))
    return hasil


def contoh_lab():
    """Gabungan indeks + UU + konsolidasi per contoh UD di bor gedung (BH-1 s.d. BH-8)."""
    T = _lapisan()
    data = {}
    for path in (LAMA / "Laboratorium.xlsx", BARU / "Laboratorium Tambahan.xlsx"):
        for b in _baris(path, "Indeks"):
            if not str(b["Contoh"]).startswith("UD") or b["Titik"] not in T:
                continue
            z = (b["Dari (m)"] + b["Sampai (m)"]) / 2
            data[(b["Titik"], b["Contoh"])] = dict(titik=b["Titik"], contoh=b["Contoh"], z=z,
                                                   unit=unit_di(T[b["Titik"]], z), w=b.get("Kadar air w (%)"),
                                                   gamma=b.get("Berat isi (kN/m³)"), LL=b.get("LL (%)"),
                                                   PI=b.get("PI (%)"), org=b.get("Kadar organik (%)"))
        for b in _baris(path, "Triaksial UU"):
            k = (b["Titik"], b["Contoh"])
            if k in data:
                data[k]["su_uu"] = b["cu (kPa)"]
                data[k]["regangan"] = b.get("Regangan runtuh (%)")
    # perbaikan berat isi BH-3 (Tahap 1 no. 11: angka adalah berat isi kering)
    for k, d in data.items():
        if d["titik"] == "BH-3" and isinstance(d["gamma"], (int, float)) and d["gamma"] < 9.81:
            d["gamma_catatan"] = f"tertulis {d['gamma']} (< γw, mustahil; diduga γ kering) - tidak dipakai"
            d["gamma"] = None
    for k, d in data.items():
        d["dipakai"] = k not in TIDAK_DIPAKAI
        d["alasan"] = TIDAK_DIPAKAI.get(k, "")
    return data


def statistik(nilai):
    v = np.array([x for x in nilai if isinstance(x, (int, float))], float)
    if len(v) == 0:
        return None
    sd = float(v.std(ddof=1)) if len(v) > 1 else 0.0
    return dict(n=len(v), rata=float(v.mean()), sd=sd, min=float(v.min()), maks=float(v.max()),
                kv=sd / float(v.mean()) * 100 if v.mean() else 0)


# ------------------------------------------------------------------ konsolidasi
def sigma_p_bilinear(kurva):
    """σ'p sebagai perpotongan dua garis lurus e-log σ' (bagian atas dan bagian NC), titik patah optimum."""
    s = np.log10([k[0] for k in kurva])
    e = np.array([k[1] for k in kurva])
    terbaik = None
    for i in range(2, len(s) - 1):
        a1 = np.polyfit(s[:i], e[:i], 1)
        a2 = np.polyfit(s[i - 1:], e[i - 1:], 1) if len(s) - i + 1 >= 2 else None
        if a2 is None or a1[0] == a2[0]:
            continue
        res = np.sum((np.polyval(a1, s[:i]) - e[:i]) ** 2) + np.sum((np.polyval(a2, s[i - 1:]) - e[i - 1:]) ** 2)
        x = (a2[1] - a1[1]) / (a1[0] - a2[0])
        if terbaik is None or res < terbaik[0]:
            terbaik = (res, 10 ** x)
    return terbaik[1]


def konsolidasi():
    T = _lapisan()
    hasil = []
    ringkas = {}
    for path in (LAMA / "Laboratorium.xlsx", BARU / "Laboratorium Tambahan.xlsx"):
        for b in _baris(path, "Ringkasan Konsolidasi"):
            ringkas[(b["Titik"], b["Contoh"])] = b
    cv = {}
    for path in (LAMA / "Laboratorium.xlsx", BARU / "Laboratorium Tambahan.xlsx"):
        for b in _baris(path, "Konsolidasi"):
            if b["Tahap"] == "Beban" and b.get("cv (m²/tahun)"):
                cv.setdefault((b["Titik"], b["Contoh"]), []).append((b["Tegangan (kPa)"], b["cv (m²/tahun)"]))
    mutu = {(h["titik"], h["contoh"]): h for h in mc.hitung(0.0)}
    for c in mc.baca_konsolidasi():
        k = (c["titik"], c["contoh"])
        r = ringkas[k]
        z = (c["dari"] + c["sampai"]) / 2
        sp_bil = sigma_p_bilinear(c["kurva"])
        cvs = [v for s_, v in cv.get(k, []) if s_ >= 1.5 * c["sp"]]  # rentang NC
        hasil.append(dict(titik=c["titik"], contoh=c["contoh"], z=z, unit=unit_di(T[c["titik"]], z), e0=c["e0"],
                          Cc=r.get("Cc (lab)"), Cr=r.get("Cr (lab)"), sp_lab=c["sp"], sp_bil=sp_bil,
                          cv_nc=float(np.median(cvs)) if cvs else None, lunne=mutu[k]["lunne"],
                          dipakai=k not in TIDAK_DIPAKAI, alasan=TIDAK_DIPAKAI.get(k, "")))
    return hasil


def rangkak():
    """Cα = -Δe / Δlog t pada dekade terakhir (2.880-10.080 menit)."""
    hasil = []
    data = {}
    for b in _baris(BARU / "Laboratorium Tambahan.xlsx", "Rangkak"):
        data.setdefault((b["Titik"], b["Contoh"], b["Tegangan tahap (kPa)"]), []).append(
            (b["Waktu (menit)"], b["Angka pori e"]))
    kons = {(k["titik"], k["contoh"]): k for k in konsolidasi()}
    for (t, c, s), v in data.items():
        v = sorted(v)
        akhir = [x for x in v if x[0] >= 2880]
        a = np.polyfit(np.log10([x[0] for x in akhir]), [x[1] for x in akhir], 1)[0]
        cc = kons[(t, c)]["Cc"] if (t, c) in kons else None
        hasil.append(dict(titik=t, contoh=c, tegangan=s, Ca=-a, Cc=cc, rasio=(-a / cc) if cc else None))
    return hasil


# ------------------------------------------------------------------ CPTu
def profil_cptu():
    """σv0, u0, qnet tiap CPTu (σv0 dari γ unit 2.2; MAT normal 0,7 m)."""
    G = {"U1": 17.0, "U2": 17.8, "U3": 10.7, "U4": 15.2, "U5": 19.0, "U6": 19.1, "U7": 20.0}
    hasil = {}
    for t in st.semua_titik():
        if t["jenis"] != "CPTu":
            continue
        z = t["z"]
        gam = np.array([G[unit_di(t, zi)] for zi in z])
        dz = np.diff(np.concatenate([[0], z]))
        sv = np.cumsum(gam * dz)
        u0 = GW * np.clip(z - MAT, 0, None)
        hasil[t["nama"]] = dict(z=z, qt=t["qt"], sv=sv, u0=u0, qnet=t["qt"] * 1000 - sv,
                                unit=np.array([unit_di(t, zi) for zi in z]), titik=t)
    return hasil


def kalibrasi_nkt():
    """Nkt = qnet median CPTu (pada kedalaman contoh, ±0,25 m) / su UU contoh yang dipakai, U4 saja."""
    P = profil_cptu()
    lab = contoh_lab()
    hasil = []
    for (b, c), d in lab.items():
        if d["unit"] != "U4" or not d["dipakai"] or not d.get("su_uu"):
            continue
        qn = []
        for nama, p in P.items():
            if nama == "CPTu-4" and d["z"] <= 4.5:
                continue
            m = (abs(p["z"] - d["z"]) <= 0.25) & (p["unit"] == "U4")
            if m.any():
                qn.append(float(np.median(p["qnet"][m])))
        if qn:  # median antar-CPTu: lonjakan tipis (kayu CPTu-1 8,3 m, lensa lanau) tidak ikut
            hasil.append(dict(titik=b, contoh=c, z=d["z"], su=d["su_uu"], qnet=float(np.median(qn)),
                              Nkt=float(np.median(qn)) / d["su_uu"]))
    return hasil


def disipasi_ch():
    """Hitung ulang t50 dari data disipasi dengan u0 hidrostatik (MAT 0,7 m) dan Un (GEC 5 Pers. 6.20)."""
    ws = openpyxl.load_workbook(BARU / "CPTu.xlsx", data_only=True)["Disipasi Data"]
    data = {}
    for r in ws.iter_rows(values_only=True):
        isi = [x for x in r if x is not None]
        if len(isi) == 4 and str(isi[0]).startswith("CPTu"):
            data.setdefault((isi[0], isi[1]), []).append((isi[2], isi[3]))
    ws = openpyxl.load_workbook(BARU / "CPTu.xlsx", data_only=True)["Disipasi Ringkas"]
    t50_penyedia = {}
    for r in ws.iter_rows(values_only=True):
        isi = [x for x in r if x is not None]
        if len(isi) >= 7 and str(isi[0]).startswith("CPTu"):
            t50_penyedia[(isi[0], isi[1])] = isi[6]
    hasil = []
    for (n, z), v in data.items():
        v = sorted(v)
        u0 = GW * (z - MAT)
        ui = v[0][1]
        un = [(t, (u - u0) / (ui - u0)) for t, u in v]
        t50 = None
        for (t1, a), (t2, b) in zip(un, un[1:]):
            if a >= 0.5 >= b and t1 > 0:
                t50 = 10 ** (math.log10(t1) + (math.log10(t2) - math.log10(t1)) * (a - 0.5) / (a - b))
                break
        un_akhir = un[-1][1]
        ch = T50_U2 * JARI_KONUS ** 2 * math.sqrt(IR) / (t50 * 60) * 3.156e7 if t50 else None  # m²/tahun
        hasil.append(dict(cptu=n, z=z, u0=u0, ui=ui, u_akhir=v[-1][1], durasi=v[-1][0], un_akhir=un_akhir, t50=t50,
                          t50_penyedia=t50_penyedia.get((n, z)), ch=ch))
    return hasil


# ------------------------------------------------------------------ CU
def triaksial_cu():
    hasil = {}
    for b in _baris(BARU / "Laboratorium Tambahan.xlsx", "Triaksial CU"):
        s3 = b["σ'3 konsolidasi (kPa)"] - b["Δu runtuh (kPa)"]
        s1 = s3 + b["(σ1-σ3) runtuh (kPa)"]
        hasil.setdefault((b["Titik"], b["Contoh"], (b["Dari (m)"] + b["Sampai (m)"]) / 2), []).append(
            ((s1 + s3) / 2, (s1 - s3) / 2))
    keluar = []
    T = _lapisan()
    for (t, c, z), pq in hasil.items():
        p = np.array([x[0] for x in pq])
        q = np.array([x[1] for x in pq])
        sin0 = float((p @ q) / (p @ p))  # garis lewat titik nol: q = p sin φ'
        a, b = np.polyfit(p, q, 1)  # q = a p + b  → sin φ' = a, c' = b / cos φ'
        phi1 = math.degrees(math.asin(min(sin0, 0.999)))
        phi2 = math.degrees(math.asin(min(a, 0.999)))
        c2 = b / math.cos(math.radians(phi2))
        keluar.append(dict(titik=t, contoh=c, z=z, unit=unit_di(T[t], z), phi_c0=phi1, phi=phi2, c=c2, pq=pq))
    return keluar


# ------------------------------------------------------------------ pasir
def spt_pasir():
    """(N1)60 dan φ' Hatanaka-Uchida untuk uji SPT di U5 dan U7 (uji yang dipakai)."""
    T = _lapisan()
    G = {"U1": 17.0, "U2": 17.8, "U3": 10.7, "U4": 15.2, "U5": 19.0, "U6": 19.1, "U7": 20.0, "U8": 20.0}
    hasil = []
    for u in kd.baca_spt():
        if kd.status_spt(u)[0] != "Ya":
            continue
        t = T[u["bor"]]
        z = u["dari"] + 0.225
        un = unit_di(t, z)
        if un not in ("U5", "U7"):
            continue
        sv = 0.0
        for lp in t["lapisan"]:
            if z <= lp["atas"]:
                break
            sv += G[lp["unit"]] * (min(z, lp["bawah"]) - lp["atas"])
        sv_eff = sv - GW * max(0.0, z - MAT)
        po_tsf = sv_eff / 95.76
        cn = min(2.0, 0.77 * math.log10(20 / po_tsf))
        n60 = u["n"] * ER[u["bor"]] / 60
        n160 = cn * n60
        phi = math.sqrt(15.4 * n160) + 20
        hasil.append(dict(bor=u["bor"], z=z, unit=un, n60=n60, sv_eff=sv_eff, cn=cn, n160=n160, phi=phi,
                          tolak=u["jenis"] == "Penolakan"))
    return hasil


def geser_langsung_lama():
    return [(b["Titik"], b["Dari (m)"], b["φ (°)"], b["c (kPa)"]) for b in _baris(LAMA / "Laboratorium.xlsx",
                                                                                   "Geser Langsung")]


if __name__ == "__main__":
    lab = contoh_lab()
    for u in ("U2", "U3", "U4", "U6"):
        d = [x for x in lab.values() if x["unit"] == u and x["dipakai"]]
        print(u, "γ", statistik([x["gamma"] for x in d]), "\n   su", statistik([x.get("su_uu") for x in d]))
    for k in konsolidasi():
        print(k)
    for r in rangkak():
        print(r)
    nk = kalibrasi_nkt()
    print("Nkt", [round(x["Nkt"], 1) for x in nk], statistik([x["Nkt"] for x in nk]))
    for d in disipasi_ch():
        print(d)
    for c in triaksial_cu():
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in c.items() if k != "pq"})
    sp = spt_pasir()
    for u in ("U5", "U7"):
        print(u, "N160", statistik([x["n160"] for x in sp if x["unit"] == u and not x["tolak"]]),
              "phi", statistik([x["phi"] for x in sp if x["unit"] == u and not x["tolak"]]))
    print(geser_langsung_lama())
