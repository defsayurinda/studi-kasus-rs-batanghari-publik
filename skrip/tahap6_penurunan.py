"""Langkah 6.6: penurunan kelompok tiang dan penurunan beda (63 cap gedung utama).

Metode (acuan di `acuan/pustaka/`, halaman dicek di lembar isian 6.6): rakit ekuivalen (NHI-06-089 Gb. 9-35 hal. 9-85, Gb. 9-36 hal. 9-86;
GEC10 Gb. 11-7), pemendekan elastis tiang (GEC10 11.4.2.1 hal. 11-9; NHI-06-089 Pers. 9-20), penurunan kepala cap = s tanah di bidang netral 6.2
+ s kelompok di bawah rakit + pemendekan elastis. Interaksi antar cap: superposisi Boussinesq (beban persegi panjang merata, metode sudut)
dari 63 cap; pembanding penyebaran 2V:1H per cap berdiri sendiri.

DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi.
Dihitung AI atas permintaan Defsa (22 Nov 2026). Kunci jawaban tidak dibuka.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import pickle
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tahap3_pondasi as p3  # noqa: E402
import tahap6_nsf as ns  # noqa: E402
import tahap6_tata_letak as tl  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "06 Struktur Bawah dan Basement"
GAMBAR = KELUAR / "Gambar"
BERKAS = KELUAR / "6.6 Penurunan Pondasi.xlsx"
MD = KELUAR / "6.6 Penurunan Pondasi.md"
LEMBAR = KELUAR / "6.6 Lembar Isian Penurunan.md"
PNG = GAMBAR / "6.6 Peta Penurunan.png"
VERIFIKASI = AKAR / "VERIFIKASI.md"
TMP = Path(tempfile.gettempdir())
CACHE = TMP / "tahap6_penurunan_hasil.pkl"
CACHE_FEM = TMP / "tahap6_penurunan_geofem.pkl"
GEOFEM = Path(r"C:\Users\Defsa\Downloads\Semster 7\Portofolio\GeoFEM3D\app")
JALAN_FEM = Path(__file__).with_name("tahap6_geofem_jalan.py")

LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
STATUS = "disetujui Defsa 22 Nov 2026 (varian d)"
LABEL_AI = (f"DIHITUNG AI ATAS PERMINTAAN DEFSA (22 Nov 2026), sel hijau; STATUS: {STATUS}. Kunci jawaban tidak dibuka.")
idn = ns.idn

# ---- tiang
D = 0.8
AG = math.pi * D ** 2 / 4                   # 0,5027 m2
EC = 4700.0 * math.sqrt(30.0)               # MPa, 25.743 (SNI 2847:2019 Ps. 19.2.2.1, f'c 30 [Asumsi 6.2])
EA = EC * 1e3 * AG                          # kN
KEPALA = 10.85
# ---- tanah (lembar isian 6.6 A.2; usulan AI)
CR, CC, SP, E0 = 0.05, 0.37, 400.0, 0.77    # U6 [Uji sendiri 2.4]; e0 = rata-rata 0,704 / 0,829
ES7, NU = 48000.0, 0.30                     # kPa; U7 pasir padat batas bawah 500 tsf [Literatur NHI-06-088 Tabel 5-16 hal. 5-85]
Z_DASAR = 55.0                              # m dari muka tanah asli, dasar U7 (di bawahnya kaku [Asumsi])
H_SUB = 1.0                                 # m, sublapis maksimum
BATAS_DS = 0.10                             # hitungan berhenti di Δσ < 10 % σ'v0
M_U7 = ES7 * (1 - NU) / ((1 + NU) * (1 - 2 * NU))    # kPa, modulus terbatas (pembanding 1D elastis, GeoFEM3D)
RAKIT_A = {"SELATAN": -21.50, "UTARA": -21.35, "TENGAH": -21.35}   # varian (a), lembar isian B (TENGAH memakai UTARA [Asumsi])
JARAK_TETANGGA = 8.5                        # m, jarak pusat ke pusat pasangan cap bertetangga
DELTA_IZIN = 16.0                           # mm (0,002 L, L 8 m)
ROT_IZIN = 1 / 500
TOL = {"excel": 1.0, "fem": 25.0, "de": 10.0}   # %, ditetapkan sebelum menghitung (lembar isian E)
OCR = 2.2                                   # σ'p = OCR x σ'v0 tanah asli (kepekaan; OCR 2,41 BH-4 dan 2,14 BH-5 dari σ'p bilinear 408,2/169,5 dan 424,4/198,3)
FJ = 2.0                                    # faktor jangka panjang penurunan tiang tunggal [Asumsi: konsolidasi U6 OC]
TOL["uji"] = 10.0                           # %, butir d: s tunggal model vs uji beban TP pada 1.400 kN
KUNCI = ("Cap E", "Cap A", "9/C", "3/B", "3/C")


# ------------------------------------------------------------------ Boussinesq persegi panjang (metode sudut)
def _f(m, n):
    """Faktor pengaruh sudut persegi panjang (Fadum), ganjil dalam m dan n."""
    m, n = np.asarray(m, float), np.asarray(n, float)
    sg = np.sign(m) * np.sign(n)
    m, n = np.abs(m), np.abs(n)
    a, b = m * m, n * n
    r = np.sqrt(a + b + 1)
    t1 = 2 * m * n * r / (a + b + a * b + 1) * (a + b + 2) / (a + b + 1)
    return sg * (t1 + np.arctan2(2 * m * n * r, a + b + 1 - a * b)) / (4 * math.pi)


def bous(q, cx, cy, B, L, px, py, h):
    """Δσz (kPa) di titik (px, py) pada kedalaman h di bawah beban persegi panjang merata q, pusat (cx, cy), B (x) x L (y)."""
    h = np.maximum(np.asarray(h, float), 0.05)
    x1, x2 = cx - B / 2 - px, cx + B / 2 - px
    y1, y2 = cy - L / 2 - py, cy + L / 2 - py
    return q * (_f(x2 / h, y2 / h) - _f(x1 / h, y2 / h) - _f(x2 / h, y1 / h) + _f(x1 / h, y1 / h))


# ------------------------------------------------------------------ penurunan satu sublapis
def s_u6(s0, ds, h, sp=SP):
    """Konsolidasi 1D U6 (m): Cr sampai σ'p, Cc di atasnya (lembar isian B). sp skalar atau array per sublapis."""
    s1 = s0 + ds
    return h / (1 + E0) * (CR * np.log10(np.minimum(s1, sp) / np.minimum(s0, sp)) + CC * np.log10(np.maximum(s1, sp) / np.maximum(s0, sp)))


def s_u7(ds, h, mod=ES7):
    return ds * h / mod


@lru_cache(maxsize=None)
def sublapis(tz, e_rakit):
    """Sublapis U6 (sisa di bawah rakit) dan U7 sampai z 55 m: dict array z, elevasi, h, u6, σ'v0."""
    zg = p3.PROFIL[tz]["elev"]
    bot = {u: b for u, b, *_ in p3.PROFIL[tz]["lapisan"]}
    zr = zg - e_rakit
    z, h, u6 = [], [], []
    for unit, a, b in (("U6", max(zr, bot["U5"]), bot["U6"]), ("U7", bot["U6"], Z_DASAR)):
        n = math.ceil((b - a) / H_SUB - 1e-9)
        t = (b - a) / n
        for i in range(n):
            z.append(a + (i + 0.5) * t)
            h.append(t)
            u6.append(unit == "U6")
    z, h = np.array(z), np.array(h)
    s0 = np.array([p3.sigma_v(v, tz) for v in z])
    return dict(z=z, e=zg - z, h=h, u6=np.array(u6), s0=s0, zr=zr, sp_ocr=OCR * (s0 - p3.urugan(tz)[1]))


def hitung_s(sl, ds, potong=True, ocr=False):
    """Penurunan (mm) kolom sublapis dengan Δσ ds. potong: berhenti di sublapis pertama dengan Δσ < 10 % σ'v0."""
    aktif = np.ones(len(ds), bool)
    if potong:
        bawah = np.nonzero(ds < BATAS_DS * sl["s0"])[0]
        if len(bawah):
            aktif[bawah[0]:] = False
    s = np.where(sl["u6"], s_u6(sl["s0"], ds, sl["h"], sl["sp_ocr"] if ocr else SP), s_u7(ds, sl["h"]))
    return float(np.sum(np.where(aktif, s, 0.0)) * 1000), aktif


# ------------------------------------------------------------------ pemendekan elastis tiang
def delta_e(tz, Q0):
    """Pemendekan elastis (mm) dengan Q(z): Q0 di kepala, naik (seret) ke Q0 + Qn di bidang netral, turun ke Qtoe (profil 6.2 dengan Q = Q0).
    Pembanding tangan: Q rata-rata per ruas (kepala-bidang netral, bidang netral-ujung), Pers. 9-20."""
    r = ns.np_zona(tz, Q=Q0)[1]
    zn, zb, Aa, Bb = r["z"], np.array(r["zb"]), np.array(r["A"]), np.array(r["B"])
    q = np.where(zb <= zn, Bb, Aa)
    zz = np.append(zb, zn)
    qq = np.append(q, Q0 + r["Qn"])
    o = np.argsort(zz, kind="stable")
    zz, qq = zz[o], qq[o]
    l_atas = KEPALA - p3.PROFIL[tz]["elev"]
    ujung = zb[-1]
    integral = float(np.sum((qq[1:] + qq[:-1]) / 2 * np.diff(zz))) + Q0 * l_atas
    q_toe = float(Aa[-1])
    tangan = ((Q0 + Q0 + r["Qn"]) / 2 * (l_atas + zn) + (Q0 + r["Qn"] + q_toe) / 2 * (ujung - zn)) / EA * 1000
    return dict(de=integral / EA * 1000, tangan=tangan, zn=zn, Qn=r["Qn"], Qmaks=Q0 + r["Qn"], Qtoe=q_toe, l_atas=l_atas, ujung=ujung)


# ------------------------------------------------------------------ data cap
def daftar_cap():
    ck, ci = tl.rancang("a")
    out = []
    for c in ck + ci:
        p = np.array(c["pos"], float)
        cx, cy = (p[:, 0].min() + p[:, 0].max()) / 2, (p[:, 1].min() + p[:, 1].max()) / 2
        B, L, _, _ = tl.blok(c["pos"])
        W = float(c["r"]["sumP"])
        out.append(dict(id=c["id"], jenis=c["jenis"], zona=c["zona"], tz=p3.zona(cx, cy), n=c["r"]["n"], W=W, Q0=W / c["r"]["n"],
                        P_tiang_maks=float(c["r"]["P_layan"]), cx=cx, cy=cy, B=B, L=L, nt=len(c["titik"])))
    return out


def cap_nomor(caps, id_):
    return next(i for i, c in enumerate(caps) if c["id"] == id_)


# ------------------------------------------------------------------ uji beban statik (6.2) dan varian (d)
def uji_beban():
    """k = rata-rata P100/s100 TP-1..4 (kN/mm, kekakuan kepala, sudah memuat pemendekan elastis) dan s terukur rata-rata pada P (interpolasi)."""
    kv = ns.baca_kurva()
    s100 = [dict((a, c) for a, b, c in v["pts"])[100] for v in kv.values()]
    k = float(np.mean([911.0 / s for s in s100]))

    def ukur(P):
        out = []
        for v in kv.values():
            pp = [b for a, b, c in v["pts"]]
            ss = [c for a, b, c in v["pts"]]
            out.append(float(np.interp(P, pp, ss)))
        return out
    return dict(k=k, k_tp=[911.0 / s for s in s100], ukur=ukur)


def varian_d(h, uji):
    """(d): s = s NP + FJ x (Q0 / k) x n^0,5 + s global (satu rakit seluas gedung, OCR). k kepala, jadi Δe tidak ditambah."""
    caps, tz_t = h["caps"], h["tz"]
    x0 = min(c["cx"] - c["B"] / 2 for c in caps)
    x1 = max(c["cx"] + c["B"] / 2 for c in caps)
    y0 = min(c["cy"] - c["L"] / 2 for c in caps)
    y1 = max(c["cy"] + c["L"] / 2 for c in caps)
    Wt = sum(c["W"] for c in caps)
    A = (x1 - x0) * (y1 - y0)
    q = Wt / A
    s_tung, rs, s_gl, ds0 = [], [], [], []
    for c in caps:
        sl = kolom_cap(c, tz_t, "a")
        hh = tz_t[c["tz"]]["e_a"] - sl["e"]
        ds = bous(q, (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0, c["cx"], c["cy"], hh)
        s_gl.append(hitung_s(sl, ds, ocr=True)[0])
        ds0.append(float(ds[0]))
        s_tung.append(c["Q0"] / uji["k"])
        rs.append(math.sqrt(c["n"]))
    s_tung, rs, s_gl = np.array(s_tung), np.array(rs), np.array(s_gl)
    return dict(q=q, A=A, W=Wt, B=x1 - x0, L=y1 - y0, s_tung=s_tung, rs=rs, s_glob=s_gl, ds0=ds0, total=h["s_np"] + FJ * s_tung * rs + s_gl)


# ------------------------------------------------------------------ hitungan utama
def tanah_zona(ps):
    """Per zona tanah: elevasi rakit (a), (b), s tanah di bidang netral (6.2, Q 911 kN)."""
    out = {}
    for tz in ("SELATAN", "TENGAH", "UTARA"):
        n = ns.np_zona(tz)[1]
        out[tz] = dict(e_a=RAKIT_A[tz], e_b=ns.elev(tz, n["z"]), zn=n["z"], Qn=n["Qn"], Qmaks=n["Qmaks"], s_np=float(ns.profil_sisa(tz, ps)(n["z"])),
                       sisa=ps["zona"][tz]["sisa"])
    return out


def kolom_cap(c, tz_t, v):
    return sublapis(c["tz"], tz_t[c["tz"]]["e_" + v])


def stres(caps, tz_t, v, cara):
    """Δσ (kPa) per cap di titik pusatnya pada sublapis rakitnya sendiri. cara: 'bous' (63 cap) atau '2v1' (cap sendiri)."""
    out = []
    for i, c in enumerate(caps):
        sl = kolom_cap(c, tz_t, v)
        if cara == "2v1":
            hh = tz_t[c["tz"]]["e_" + v] - sl["e"]
            out.append(c["W"] / ((c["B"] + hh) * (c["L"] + hh)))
            continue
        ds = np.zeros(len(sl["z"]))
        for j, cj in enumerate(caps):
            hh = tz_t[cj["tz"]]["e_" + v] - sl["e"]
            ds += bous(cj["W"] / (cj["B"] * cj["L"]), cj["cx"], cj["cy"], cj["B"], cj["L"], c["cx"], c["cy"], hh)
        out.append(ds)
    return out


def hitung(ps=None):
    ps = ps or ns.penurunan_sisa()
    caps = daftar_cap()
    tz_t = tanah_zona(ps)
    de = {}
    for c in caps:
        k = (c["tz"], round(c["Q0"], 3))
        de[k] = de.get(k) or delta_e(c["tz"], c["Q0"])
    h = dict(caps=caps, tz=tz_t, ps_sisa={z: ps["zona"][z]["sisa"] for z in ps["zona"]})
    for c in caps:
        c["de"] = de[(c["tz"], round(c["Q0"], 3))]
        c["s_np"] = tz_t[c["tz"]]["s_np"]
    res = {}
    for v in "ab":
        for cara in ("bous", "2v1"):
            ds_l = stres(caps, tz_t, v, cara)
            s_kel, s_z55, ds0 = [], [], []
            for c, ds in zip(caps, ds_l):
                sl = kolom_cap(c, tz_t, v)
                s_kel.append(hitung_s(sl, ds)[0])
                s_z55.append(hitung_s(sl, ds, potong=False)[0])
                ds0.append(float(ds[0]))
            res[(v, cara)] = dict(ds=ds_l, s_kel=np.array(s_kel), s_z55=np.array(s_z55), ds_atas=np.array(ds0))
    h["res"] = res
    s_np = np.array([c["s_np"] for c in caps])
    s_de = np.array([c["de"]["de"] for c in caps])
    tot = {k: s_np + r["s_kel"] + s_de for k, r in res.items()}
    for cara in ("bous", "2v1"):
        tot[("c", cara)] = np.maximum(tot[("a", cara)], tot[("b", cara)])
    h["total"], h["s_np"], h["s_de"] = tot, s_np, s_de
    uji = uji_beban()
    h["uji"] = dict(k=uji["k"], k_tp=uji["k_tp"], ukur_1400=uji["ukur"](1400.0), s_model_1400=1400.0 / uji["k"])
    h["d"] = varian_d(h, uji)
    tot[("d", "bous")] = h["d"]["total"]
    # kepekaan σ'p = OCR x σ'v0 tanah asli, varian (a) Boussinesq
    h["ocr_a"] = np.array([hitung_s(kolom_cap(c, tz_t, "a"), ds, ocr=True)[0] for c, ds in zip(caps, res[("a", "bous")]["ds"])])
    h["pasangan"] = pasangan(caps, tot[("c", "bous")])
    h["pasangan_v"] = {k: pasangan(caps, tot[k]) for k in tot}
    for p in h["pasangan"]:
        sd = h["d"]["total"]
        p["s_a_d"], p["s_b_d"] = float(sd[p["i"]]), float(sd[p["j"]])
        p["delta_d"] = abs(p["s_a_d"] - p["s_b_d"])
        p["rot_d"] = p["delta_d"] / 1000 / p["L"]
    h["sloof"] = sloof(h["pasangan"])
    h["sloof_d"] = sloof(h["pasangan_v"][("d", "bous")])
    return h


# ------------------------------------------------------------------ penurunan beda dan sloof
def pasangan(caps, s):
    out = []
    for i in range(len(caps)):
        for j in range(i + 1, len(caps)):
            L = math.hypot(caps[i]["cx"] - caps[j]["cx"], caps[i]["cy"] - caps[j]["cy"])
            if L <= JARAK_TETANGGA:
                d = abs(float(s[i] - s[j]))
                out.append(dict(i=i, j=j, a=caps[i]["id"], b=caps[j]["id"], L=L, delta=d, rot=d / 1000 / L, s_a=float(s[i]), s_b=float(s[j]),
                                lintas=caps[i]["tz"] != caps[j]["tz"]))
    return sorted(out, key=lambda p: -p["delta"])


M16 = {"400x800": 249.1, "SL-1 400x900": 354.7}   # kNm per 16 mm, L 8 m (5.4, sebanding δ dan 1/L2)


def momen_sloof(delta_mm, L=8.0):
    return {k: m * delta_mm / 16.0 * (8.0 / L) ** 2 for k, m in M16.items()}


def rasio_sl1(delta_mm, L=8.0):
    """Rasio M/φMn SL-1 400 x 900 pada 1,2D + 1,6L + 1,0T: tulangan desain 5.4 (δ 16 mm) tetap, bagian T diskala (δ, 1/L2). Tidak mengubah 5.4."""
    import tahap5_sloof as s5
    d = s5.desain("SL-1", 0.40, 0.90, delta=s5.DELTA_16)
    g, t16 = d["g"], d["T"]
    t = t16 * delta_mm / 16.0 * (8.0 / L) ** 2
    neg = (g["neg_g12"] + t) / d["phiMn_neg"]
    pos = max(g["pos_g"], t - g["neg_d12"]) / d["phiMn_pos"]
    return max(neg, pos), dict(t16=t16, neg_g12=g["neg_g12"], pos_g=g["pos_g"], neg_d12=g["neg_d12"], phi_neg=d["phiMn_neg"], phi_pos=d["phiMn_pos"])


def delta_rasio1():
    """δ (mm, L 8 m) saat rasio SL-1 = 1 (bagi dua)."""
    lo, hi = 16.0, 400.0
    for _ in range(60):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if rasio_sl1(m)[0] < 1 else (lo, m)
    return lo


def sloof(psg):
    mx = psg[0]
    r, _ = rasio_sl1(mx["delta"], mx["L"])
    r16, par = rasio_sl1(16.0)
    return dict(pasangan=mx, M=momen_sloof(mx["delta"], mx["L"]), rasio=r, rasio16=r16, par=par, delta_batas=delta_rasio1(),
                M16=momen_sloof(16.0))


# ------------------------------------------------------------------ GeoFEM3D (cek silang butir b)
def fem_masukan(h, kode, v="a"):
    """Masukan model: cap terisolasi, puncak model di elevasi rakit, lapisan U6 (E dari M) dan U7, dasar kaku z 55 m."""
    caps = h["caps"]
    i = cap_nomor(caps, kode)
    c = caps[i]
    tz_t = h["tz"]
    sl = kolom_cap(c, tz_t, v)
    q = c["W"] / (c["B"] * c["L"])
    ds = np.array([float(bous(q, 0, 0, c["B"], c["L"], 0, 0, tz_t[c["tz"]]["e_" + v] - e)) for e in sl["e"]])
    f = (1 + NU) * (1 - 2 * NU) / (1 - NU)
    lap = []
    # U6: satu lapis; σ' rata-rata = σ'v0 + Δσ/2 pada tebal berbobot
    u6 = sl["u6"]
    sig = float(np.sum((sl["s0"] + ds / 2)[u6] * sl["h"][u6]) / np.sum(sl["h"][u6]))
    M6 = (1 + E0) * sig / (0.434 * CR)
    lap.append(dict(tebal=float(np.sum(sl["h"][u6])), E=M6 * f, nu=NU, M=M6, sigma=sig))
    lap.append(dict(tebal=float(np.sum(sl["h"][~u6])), E=ES7, nu=NU, M=M_U7))
    # 1D elastis setara (modulus terbatas), cap terisolasi, sampai dasar kaku z 55 m
    Ms = np.where(u6, M6, M_U7)
    s1d = float(np.sum(ds * sl["h"] / Ms) * 1000)
    s1d_cc, _ = hitung_s(sl, ds, potong=False)
    return dict(kode=kode, B=c["B"], L=c["L"], q=q, W=c["W"], lap=lap, s1d_elastis=s1d, s1d_cr=s1d_cc, e_rakit=tz_t[c["tz"]]["e_" + v])


def fem_jalankan(masukan, halus=1.0, kasar=8.0, lebar=120.0):
    """Jalankan GeoFEM3D di subproses (venv-nya sendiri); hasil di-cache di %TEMP%."""
    kunci = hashlib.sha1(json.dumps([masukan["kode"], masukan["B"], masukan["L"], masukan["q"], masukan["lap"], halus, kasar, lebar],
                                    sort_keys=True).encode()).hexdigest()[:16]
    cache = pickle.loads(CACHE_FEM.read_bytes()) if CACHE_FEM.exists() else {}
    if kunci in cache:
        return cache[kunci]
    py = GEOFEM / ".venv" / "Scripts" / "python.exe"
    arg = json.dumps(dict(B=masukan["B"], L=masukan["L"], q=masukan["q"], lap=[(x["tebal"], x["E"], x["nu"]) for x in masukan["lap"]],
                          halus=halus, kasar=kasar, lebar=lebar, app=str(GEOFEM)))
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([str(py), str(JALAN_FEM), arg], capture_output=True, text=True, env=env, timeout=int(os.environ.get("FEM_TIMEOUT", "1500")))
    if p.returncode != 0:
        raise RuntimeError(f"GeoFEM3D gagal: {p.stderr[-600:]}")
    hasil = json.loads(p.stdout.strip().splitlines()[-1])
    cache[kunci] = hasil
    CACHE_FEM.write_bytes(pickle.dumps(cache))
    return hasil


MESH_FEM = {"Cap E": (3.0, 10.0, 160.0), "3/C": (0.8, 6.0, 120.0)}   # halus, kasar, lebar domain (m); hasil sudah konvergen (selisih jaring < 0,2 %)


def fem_semua(h):
    out = {}
    for kode, (halus, kasar, lebar) in MESH_FEM.items():
        m = fem_masukan(h, kode)
        try:
            r = fem_jalankan(m, halus, kasar, lebar)
        except Exception as e:      # noqa: BLE001  (batas waktu / GeoFEM tidak ada: GeoFEM belum diulang, dicatat di md)
            print("GeoFEM belum diulang untuk", kode, str(e)[:120])
            continue
        out[kode] = dict(masuk=m, fem=r["settlement"], waktu=r.get("waktu"), dof=r.get("dof"),
                         selisih=abs(r["settlement"] - m["s1d_elastis"]) / m["s1d_elastis"] * 100)
    return out


def semua(pakai_cache=True, fem=True):
    if pakai_cache and CACHE.exists() and os.environ.get("TAHAP6_PENURUNAN_CACHE") == "1":
        return pickle.loads(CACHE.read_bytes())
    h = hitung()
    if fem:
        h["fem"] = fem_semua(h)
    CACHE.write_bytes(pickle.dumps(h))
    return h




# ================================================================== gambar
def gambar(h, keluar=PNG, kunci=("c", "bous"), judul="terbesar dari varian (a) dan (b), rakit seluas kelompok (batas atas)"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    caps, s = h["caps"], h["total"][kunci]
    pas = h["pasangan_v"][kunci]
    fig, ax = plt.subplots(figsize=(11, 9.5), dpi=150)
    nm = plt.get_cmap("RdYlGn_r")
    lo, hi = float(s.min()), float(s.max())
    for c, v in zip(caps, s):
        ax.add_patch(Rectangle((c["cx"] - c["B"] / 2, c["cy"] - c["L"] / 2), c["B"], c["L"], fc=nm((v - lo) / (hi - lo)), ec="k", lw=0.6))
        ax.text(c["cx"], c["cy"], f"{c['id'].replace('Cap ', '')}\n{v:.0f}", ha="center", va="center", fontsize=5.5 if c["jenis"] == "kolom" else 7)
    for p in pas[:6]:
        a, b = caps[p["i"]], caps[p["j"]]
        ax.plot([a["cx"], b["cx"]], [a["cy"], b["cy"]], color="k", lw=1.2, ls="--")
    xs = [c["cx"] for c in caps]
    ys = [c["cy"] for c in caps]
    ax.set_xlim(min(xs) - 5, max(xs) + 5)
    ax.set_ylim(min(ys) - 5, max(ys) + 5)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("6.6 Penurunan total kepala cap (mm): " + judul + "\n"
                 "garis putus-putus: enam pasangan dengan penurunan beda terbesar. DATA SIMULASI, draf menunggu persetujuan Defsa", fontsize=8.5)
    sm = plt.cm.ScalarMappable(cmap=nm, norm=plt.Normalize(lo, hi))
    fig.colorbar(sm, ax=ax, shrink=0.7, label="s total (mm)")
    Path(keluar).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(keluar, bbox_inches="tight")
    plt.close(fig)
    return keluar


# ================================================================== Excel
ACUAN = [
    ("NHI-06-089 Vol II Gb. 9-35 hal. 9-85 (rakit ekuivalen D/3 di atas ujung, Duncan-Buchignani 1976), Gb. 9-36 hal. 9-86 (penyebaran 2V:1H), Pers. 9-20 (PDF hal. 193)",
     "ada", "acuan/pustaka/FHWA-NHI-06-089-Soils-and-Foundations-Vol-II.pdf"),
    ("GEC10 11.4.2.1 hal. 11-9 (Pers. 11-7), Gb. 11-7 hal. 11-12, Gb. 11-8 hal. 11-13; 10.6.2 hal. 10-47/48 (penurunan tiang = penurunan tanah di bidang netral)", "ada",
     "acuan/pustaka/ (GEC10)"),
    ("NHI-06-088 Tabel 5-16 hal. 5-85 (Es korelasi N60: pasir padat batas bawah 500 tsf = 48 MPa; pasir lepas 10 MPa)", "ada", "acuan/pustaka/ (NHI-06-088)"),
    ("SNI 1726:2019 Tabel 22 (simpangan izin, dipakai sebagai batas δ 0,002 L, kategori risiko IV)", "ada", "dipakai 5.4 [Asumsi]"),
    ("Fellenius (metode terpadu, bidang netral)", "tidak ada di acuan/", "[Literatur]; dasar yang ada: GEC10 10.6.2"),
    ("Boussinesq beban persegi panjang merata (metode sudut, faktor pengaruh Fadum/Newmark)", "tidak ada di acuan/",
     "[Literatur: teori elastisitas]; diuji terhadap integral titik beban (tests/test_tahap6_penurunan.py)"),
    ("Parameter U6 (Cc 0,37, Cr 0,05, σ'p 400, e0 0,77), σ'v0", "ada", "2.4 `Parameter Tanah.xlsx` [Uji sendiri]; `tahap3_pondasi.sigma_v`"),
    ("Sisa penurunan tanah dan bidang netral", "ada", "6.2 `tahap6_nsf.py` (disetujui Defsa 21 Nov 2026)"),
    ("Tata letak 63 cap dan Σ Pmax layan", "ada", "6.3 `tahap6_tata_letak.py rancang('a')` (disetujui)"),
    ("Momen sloof akibat δ", "ada", "5.4 (249,1 / 354,7 kNm per 16 mm, M = 6 Ec Ie δ / L²)"),
]
KEPUTUSAN = [
    "Letak rakit ekuivalen: (c) hitung (a) D/3 di atas ujung dan (b) bidang netral 6.2, ambil terbesar per cap [usulan AI, keputusan tanpa hitung ulang].",
    "Penurunan kepala cap = s tanah di bidang netral (6.2) + s kelompok di bawah rakit + pemendekan elastis; s tanah di NP ikut ditambahkan juga pada varian (a) [usulan AI].",
    "Interaksi: superposisi Boussinesq beban persegi panjang merata dari 63 cap di titik pusat tiap cap [usulan utama AI]; pembanding 2V:1H per cap berdiri sendiri.",
    "U6 konsolidasi 1D (Cr sampai σ'p 400 kPa, Cc di atasnya, e0 0,77); U7 elastis Es 48 MPa, ν 0,30; dasar kaku z 55 m atau Δσ < 10 % σ'v0 [usulan AI].",
    "Zona tengah memakai fungsi 6.2 untuk TENGAH (NP, s NP 14,8 mm), bukan utara [usulan AI].",
    "Pasangan bertetangga: jarak pusat ke pusat ≤ 8,5 m; δ vs 16 mm dan δ/L vs 1/500; untuk cap inti L = jarak pusat ke pusat sebenarnya.",
    "GeoFEM3D: cap terisolasi Cap E dan 3/C, varian (a), U6 E dari modulus terbatas pada σ' rata-rata, ν 0,30; dibandingkan dengan 1D elastis setara; toleransi 25 % [usulan AI].",
]


def kol_cap(h):
    caps, r = h["caps"], h["res"]
    out = []
    for i, c in enumerate(caps):
        out.append([i + 1, c["id"], c["jenis"], c["tz"], c["n"], c["W"], c["B"], c["L"], h["tz"][c["tz"]]["e_a"], h["tz"][c["tz"]]["e_b"], c["s_np"],
                    float(r[("a", "bous")]["s_kel"][i]), float(r[("b", "bous")]["s_kel"][i]), float(r[("a", "2v1")]["s_kel"][i]),
                    float(r[("b", "2v1")]["s_kel"][i]), c["de"]["de"]])
    return out


def stres_satu(h, c, v):
    """Δσ Boussinesq (63 cap) pada sublapis cap c, varian v."""
    caps, tz_t = h["caps"], h["tz"]
    sl = kolom_cap(c, tz_t, v)
    ds = np.zeros(len(sl["z"]))
    for cj in caps:
        hh = tz_t[cj["tz"]]["e_" + v] - sl["e"]
        ds += bous(cj["W"] / (cj["B"] * cj["L"]), cj["cx"], cj["cy"], cj["B"], cj["L"], c["cx"], c["cy"], hh)
    return ds


def keputusan_defsa(h):
    ps, sl = h["pasangan"], h["sloof"]
    n16 = sum(p["delta"] > DELTA_IZIN for p in ps)
    sd, pd_ = h["sloof_d"], h["pasangan_v"][("d", "bous")]
    out = [f"Pilih varian dasar penurunan beda: (d) kalibrasi uji beban (usulan AI; δ maks {idn(pd_[0]['delta'], 1)} mm, {sum(q['delta'] > DELTA_IZIN for q in pd_)} pasangan > 16 mm, "
           f"rasio SL-1 {idn(sd['rasio'], 2)}) atau (a)/(b) sebagai batas atas ({n16} pasangan > 16 mm, rasio SL-1 {idn(sl['rasio'], 2)}).",
           f"Penurunan beda (varian c): {n16} dari {len(ps)} pasangan melebihi 16 mm (maks {idn(ps[0]['delta'], 0)} mm, {ps[0]['a']} - {ps[0]['b']}). Pilih penanganan: "
           "(1) perbesar sloof, (2) perpanjang tiang atau ganti tata letak (turunkan tekanan rakit cap kolom kecil), (3) tunda cor sloof sampai sebagian penurunan selesai, "
           "(4) terima dengan sambungan fleksibel di utilitas dan pelat halaman (bukan struktur sloof).",
           f"Momen sloof pada δ maksimum: SL-1 {idn(sl['M']['SL-1 400x900'], 0)} kNm, rasio {idn(sl['rasio'], 2)} (cadangan sampai δ ±{idn(sl['delta_batas'], 0)} mm). "
           "Keputusan: perbesar sloof atau ganti pendekatan.",
           "Metode rakit seluas kelompok memberi tekanan besar pada cap kecil (4 tiang ± 550 kPa) dan penurunan beda besar terhadap cap inti yang tekanannya kecil: "
           "putuskan apakah varian 2V:1H (lebih halus) boleh menjadi acuan desain, atau metode lain (mis. beban pada 2/3 panjang, Fellenius).",
           "Sisa penurunan tanah 874 mm di utara terhadap lantai basement dan pelat halaman (bukan tiang): dicatat untuk sambungan utilitas dan pelat halaman (Tahap 7)."]
    return out


def buat_excel(keluar=BERKAS, h=None):
    import openpyxl
    from format_dokumen import AI, Lembar, set_font_bawaan
    h = h or semua()
    caps, res, tz_t = h["caps"], h["res"], h["tz"]
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    ket = LABEL + " " + LABEL_AI
    adr = {}

    def salin_fill(w, dst, src):
        w[dst].fill = w[src].fill.copy()

    # ---- Petunjuk
    lp = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk dan daftar lembar", [26, 100])
    lp.catatan(f"STATUS: {STATUS}. " + ket)
    lp.kosong()
    lp.bagian("A", "Isi lembar")
    lp.tabel(["Lembar", "Isi"], [
        ["Ringkasan", "Penurunan total maksimum per zona, cap kunci, penurunan beda maksimum, akibat ke sloof"],
        ["Data", "Parameter U6/U7, tiang dan Ec, EA (rumus hidup), zona tanah"],
        ["Per Cap", "63 cap: zona, n, ΣP, B, L, elevasi rakit (a)/(b), s NP, s kelompok (Boussinesq dan 2V:1H), Δe, s total (rumus hidup)"],
        ["Cap Inti", "Cap E dan 3/C varian (a): kolom sublapis dengan rumus hidup (Δσ 2V:1H, Cr/Cc/elastis, pemotongan Δσ < 10 % σ'v0)"],
        ["Penurunan Beda", "Semua pasangan bertetangga (≤ 8,5 m): δ, δ/L, cek, momen sloof (rumus hidup dari lembar Per Cap)"],
        ["Sloof", "Momen sloof 5.4 dan rasio SL-1 pada δ maksimum"],
        ["GeoFEM3D", "Cek silang butir b: 1D elastis setara vs GeoFEM3D (Cap E, 3/C)"],
        ["Verifikasi", "T-104: butir a, b, c"],
        ["Acuan", "Acuan dan status"],
        ["Keputusan", "Keputusan usulan AI dan hal yang perlu diputuskan Defsa"]], rata=["l", "l"], beku=False)

    # ---- Ringkasan
    lr = Lembar(wb.create_sheet("Ringkasan"), 2, "Ringkasan hasil", [34, 18, 18, 18, 18, 44])
    lr.catatan(ket)
    lr.kosong()
    lr.bagian("A", "Penurunan total maksimum per zona tanah (mm)")
    rows = []
    for tz in ("SELATAN", "TENGAH", "UTARA"):
        idx = [i for i, c in enumerate(caps) if c["tz"] == tz]
        row = [tz]
        for k in (("a", "bous"), ("b", "bous"), ("a", "2v1"), ("b", "2v1")):
            row.append(float(max(h["total"][k][i] for i in idx)))
        i_m = max(idx, key=lambda i: h["total"][("c", "bous")][i])
        row.append(f"{caps[i_m]['id']} ({h['total'][('c', 'bous')][i_m]:.1f} mm, varian terbesar)")
        rows.append(row)
    lr.tabel(["Zona", "(a) Boussinesq", "(b) Boussinesq", "(a) 2V:1H", "(b) 2V:1H", "Terbesar (c)"], rows, rata=["l", "r", "r", "r", "r", "l"],
             fmt=[None, "0.0", "0.0", "0.0", "0.0", None], fill_kolom={i: AI for i in range(1, 6)}, beku=False)
    lr.kosong()
    lr.bagian("B", "Cap kunci (mm)")
    rows = []
    for kd in KUNCI:
        i = cap_nomor(caps, kd)
        c = caps[i]
        rows.append([kd, c["tz"], c["s_np"], float(res[("a", "bous")]["s_kel"][i]), c["de"]["de"], float(h["total"][("c", "bous")][i])])
    lr.tabel(["Cap", "Zona", "s NP", "s kelompok (a)", "Δe", "s total (c)"], rows, rata=["l", "l", "r", "r", "r", "r"],
             fmt=[None, None, "0.0", "0.0", "0.0", "0.0"], fill_kolom={i: AI for i in range(2, 6)}, beku=False)
    lr.kosong()
    lr.bagian("C", "Penurunan beda dan sloof")
    ps = h["pasangan"]
    n16 = sum(p["delta"] > DELTA_IZIN for p in ps)
    sl = h["sloof"]
    lr.tabel(["Besaran", "Nilai", "", "", "", "Keterangan"], [
        ["Jumlah pasangan bertetangga", len(ps), "", "", "", "jarak pusat ≤ 8,5 m"],
        ["Pasangan δ > 16 mm", n16, "", "", "", f"dari {len(ps)} (varian c, Boussinesq)"],
        ["δ maksimum (mm)", ps[0]["delta"], "", "", "", f"{ps[0]['a']} - {ps[0]['b']}, L {ps[0]['L']:.2f} m"],
        ["δ/L maksimum", ps[0]["rot"], "", "", "", "batas 1/500 = 0,002"],
        ["M sloof SL-1 400 × 900 pada δ maks (kNm)", sl["M"]["SL-1 400x900"], "", "", "", "sebanding δ, 1/L²"],
        ["Rasio SL-1, 1,2D + 1,6L + 1,0T", sl["rasio"], "", "", "", f"tulangan 5.4 tetap; δ saat rasio = 1: {sl['delta_batas']:.0f} mm"],
        ["Varian (d): δ maksimum (mm)", h["sloof_d"]["pasangan"]["delta"], "", "", "", f"{h['sloof_d']['pasangan']['a']} - {h['sloof_d']['pasangan']['b']}; "
         f"{sum(q['delta'] > DELTA_IZIN for q in h['pasangan_v'][('d', 'bous')])} pasangan > 16 mm"],
        ["Varian (d): rasio SL-1", h["sloof_d"]["rasio"], "", "", "", "kalibrasi uji beban (usulan AI)"]],
        rata=["l", "r", "r", "r", "r", "l"], fmt=[None, "0.0000", None, None, None, None], fill_kolom={1: AI}, beku=False)

    # ---- Data
    ld = Lembar(wb.create_sheet("Data"), 3, "Data masukan", [46, 16, 78])
    ld.catatan(ket)
    ld.kosong()
    ld.bagian("A", "Tanah dan tiang")
    rows = [
        ["Cr U6", CR, "[Uji sendiri 2.4]"], ["Cc U6", CC, "[Uji sendiri 2.4]"], ["σ'p U6 (kPa)", SP, "[Uji sendiri 2.4]; tetap 400 kPa di seluruh U6 pada (a)-(c); OCR 2,41 (BH-4) dan 2,14 (BH-5); kepekaan OCR 2,2 di kolom (d)"],
        ["e0 U6", E0, "rata-rata 0,704 (BH-4 UD-4) / 0,829 (BH-5 UD-5) [Uji sendiri 2.4]"],
        ["Es U7 (kPa)", ES7, "NHI-06-088 Tabel 5-16 hal. 5-85, pasir padat batas bawah 500 tsf [Literatur]"],
        ["ν U7 dan U6 (GeoFEM3D)", NU, "[Asumsi]"], ["Batas hitungan Δσ / σ'v0", BATAS_DS, "lembar isian B; atau dasar U7 z 55 m"],
        ["f'c (MPa)", 30.0, "[Asumsi 6.2]"], ["Ec = 4700 akar(f'c) (MPa)", None, "SNI 2847:2019 Ps. 19.2.2.1 (rumus hidup)"],
        ["Diameter tiang D (m)", D, "6.1"], ["A tiang = π D² / 4 (m²)", None, "rumus hidup"], ["EA = Ec A (MN)", None, "rumus hidup"],
        ["Elevasi kepala tiang (m)", KEPALA, "6.0"],
        ["k kepala uji beban TP-1..4, 100 % = 911 kN (kN/mm)", h["uji"]["k"], "6.2 `Uji Beban Statis Tiang.xlsx`: rata-rata 911 / s100 (empat tiang)"],
        ["Faktor jangka panjang FJ", FJ, "[Asumsi: konsolidasi U6 OC]"]]
    r0, a, b = ld.tabel(["Besaran", "Nilai", "Sumber"], rows, rata=["l", "r", "l"], fill_kolom={1: AI}, beku=False)
    V = lambda i: f"{ld.kol(1)}{r0 + 1 + i}"
    ld.ws[V(8)] = f"=4700*SQRT({V(7)})"
    ld.ws[V(10)] = f"=PI()*{V(9)}^2/4"
    ld.ws[V(11)] = f"={V(8)}*{V(10)}"
    for i, f in ((8, "#,##0.0"), (10, "0.0000"), (11, "#,##0.00")):
        ld.ws[V(i)].number_format = f
    A = lambda k: f"Data!${ld.kol(1)}${r0 + 1 + k}"
    adr.update(cr=A(0), cc=A(1), sp=A(2), e0=A(3), es=A(4), bd=A(6), ea=A(11), k=A(13), fj=A(14))
    ld.kosong()
    ld.bagian("B", "Zona tanah (6.2, Q 911 kN)")
    ld.tabel(["Zona", "e rakit (a) (m)", "e rakit (b) NP (m)", "s tanah di NP (mm)", "Qn (kN)", "Sisa penurunan (mm)"],
             [[z, tz_t[z]["e_a"], tz_t[z]["e_b"], tz_t[z]["s_np"], tz_t[z]["Qn"], tz_t[z]["sisa"]] for z in tz_t], rata=["l"] * 6, beku=False,
             fmt=[None, "0.00", "0.00", "0.0", "#,##0", "#,##0"], fill_kolom={i: AI for i in range(1, 6)})

    # ---- Per Cap
    lc = Lembar(wb.create_sheet("Per Cap"), 4, "Penurunan per cap (63 cap)", [5, 10, 8, 10, 5, 10, 7, 7, 9, 9, 8, 9, 9, 9, 9, 8, 9, 9, 10, 10, 9, 6, 9, 10])
    lc.catatan(ket + " Kolom (d): s tot = s NP + FJ x s tunggal x Rs + s global (rumus hidup). s total (a)-(c) = s NP + s kelompok + Δe (rumus hidup). Boussinesq = superposisi 63 cap; 2:1 = 2V:1H cap berdiri sendiri. Satuan mm kecuali tertulis.")
    lc.kosong()
    kep = ["No", "Cap", "Jenis", "Zona", "n", "ΣP (kN)", "B (m)", "L (m)", "Elev (a)", "Elev (b)", "s NP", "s kel (a) B", "s kel (b) B", "s kel (a) 2:1",
           "s kel (b) 2:1", "Δe", "s tot (a)", "s tot (b)", "s tot (c)", "s tot (c) 2:1", "s tunggal", "Rs", "s global", "s tot (d)"]
    dd = h["d"]
    rows = [d + [None] * 4 + [float(dd["s_tung"][i]), None, float(dd["s_glob"][i]), None] for i, d in enumerate(kol_cap(h))]
    r0, ra, rz = lc.tabel(kep, rows, rata=["c", "l", "l", "l", "c"] + ["r"] * 19, beku=True, beku_kolom=3,
                          fmt=[None, None, None, None, "0", "#,##0", "0.00", "0.00", "0.00", "0.00"] + ["0.0"] * 10 + ["0.00", "0.00", "0.0", "0.0"],
                          fill_kolom={i: AI for i in list(range(5, 16)) + [20, 22]})
    K = lc.kol
    w = lc.ws
    for r in range(ra, rz + 1):
        w[f"{K(16)}{r}"] = f"={K(10)}{r}+{K(11)}{r}+{K(15)}{r}"
        w[f"{K(17)}{r}"] = f"={K(10)}{r}+{K(12)}{r}+{K(15)}{r}"
        w[f"{K(18)}{r}"] = f"=MAX({K(16)}{r},{K(17)}{r})"
        w[f"{K(19)}{r}"] = f"=MAX({K(10)}{r}+{K(13)}{r}+{K(15)}{r},{K(10)}{r}+{K(14)}{r}+{K(15)}{r})"
        w[f"{K(21)}{r}"] = f"=SQRT({K(4)}{r})"
        w[f"{K(23)}{r}"] = f"={K(10)}{r}+{adr['fj']}*{K(20)}{r}*{K(21)}{r}+{K(22)}{r}"
        for i in (21, 23):
            w[f"{K(i)}{r}"].number_format = "0.00" if i == 21 else "0.0"
            salin_fill(w, f"{K(i)}{r}", f"{K(10)}{r}")
        for i in (16, 17, 18, 19):
            w[f"{K(i)}{r}"].number_format = "0.0"
            salin_fill(w, f"{K(i)}{r}", f"{K(10)}{r}")
    adr.update(pc_id=f"'Per Cap'!${K(1)}${ra}:${K(1)}${rz}", pc_c=f"'Per Cap'!${K(18)}${ra}:${K(18)}${rz}", pc_rows=(ra, rz),
               pc_col={"a": K(16), "b": K(17), "c": K(18), "d": K(23)}, pc_d=f"'Per Cap'!${K(23)}${ra}:${K(23)}${rz}")

    # ---- Cap Inti (rumus hidup)
    li = Lembar(wb.create_sheet("Cap Inti"), 5, "Cap E dan 3/C varian (a): kolom sublapis (rumus hidup)", [10, 8, 10, 10, 8, 11, 12, 8, 11, 12, 8, 11])
    li.catatan(ket + " Δσ 2V:1H dan s adalah rumus hidup; Δσ Boussinesq (63 cap) dari skrip Python (nilai), s darinya rumus hidup.")
    li.kosong()
    adr["blok"] = {}
    w, Kk = li.ws, li.kol
    for kd in ("Cap E", "3/C"):
        i = cap_nomor(caps, kd)
        c = caps[i]
        sl_ = kolom_cap(c, tz_t, "a")
        li.bagian("A" if kd == "Cap E" else "B", f"{kd}: zona {c['tz']}, {c['n']} tiang, rakit (a)")
        prm = [["ΣP layan (kN)", c["W"], "6.3"], ["B (m)", c["B"], "jarak as terluar + D"], ["L (m)", c["L"], ""],
               ["Elevasi rakit (a) (m)", tz_t[c["tz"]]["e_a"], "lembar isian B"], ["s tanah di NP (mm)", c["s_np"], "6.2"],
               ["Δe (mm)", c["de"]["de"], "integrasi Q(z), Q0 = ΣP/n"]]
        p0, pa, pz = li.tabel(["Besaran", "Nilai", "Sumber"], prm, rata=["l", "r", "l"], fill_kolom={1: AI}, beku=False, fmt=[None, "#,##0.000", None])
        W_, B_, L_, ER, SNP, DE = (f"${Kk(1)}${pa + k}" for k in range(6))
        li.kosong()
        ds_b = stres_satu(h, c, "a")
        rows = [[k + 1, "U6" if sl_["u6"][k] else "U7", float(sl_["z"][k]), float(sl_["e"][k]), float(sl_["h"][k]), float(sl_["s0"][k]), None, None, None,
                 float(ds_b[k]), None, None] for k in range(len(sl_["z"]))]
        kp = ["No", "Lapis", "z (m)", "Elev (m)", "h (m)", "σ'v0 (kPa)", "Δσ 2:1 (kPa)", "aktif", "s 2:1 (mm)", "Δσ Bouss. (kPa)", "aktif", "s Bouss. (mm)"]
        t0, ta, tz_ = li.tabel(kp, rows, rata=["c", "c"] + ["r"] * 10, beku=False,
                               fmt=[None, None, "0.00", "0.00", "0.00", "0.0", "0.0", "0", "0.00", "0.0", "0", "0.00"], fill_kolom={i: AI for i in (2, 3, 4, 5, 9)})
        cr_, cc_, sp_, e0_, es_, bd_ = (adr[k] for k in ("cr", "cc", "sp", "e0", "es", "bd"))
        for r in range(ta, tz_ + 1):
            F, G, E_, H, Dl = f"{Kk(5)}{r}", f"{Kk(6)}{r}", f"{Kk(4)}{r}", f"{Kk(7)}{r}", f"{Kk(3)}{r}"
            hh = f"({ER}-{Dl})"
            w[G] = f"={W_}/(({B_}+{hh})*({L_}+{hh}))"
            w[H] = f"=IF({G}>={bd_}*{F},1,0)" if r == ta else f"=IF(AND({Kk(7)}{r - 1}=1,{G}>={bd_}*{F}),1,0)"

            def sfun(dsx, act):
                return (f"=IF({act}=1,IF({Kk(1)}{r}=\"U6\",{E_}/(1+{e0_})*({cr_}*LOG10(MIN({F}+{dsx},{sp_})/MIN({F},{sp_}))"
                        f"+{cc_}*LOG10(MAX({F}+{dsx},{sp_})/MAX({F},{sp_}))),{dsx}*{E_}/{es_})*1000,0)")
            w[f"{Kk(8)}{r}"] = sfun(G, H)
            w[f"{Kk(10)}{r}"] = (f"=IF({Kk(9)}{r}>={bd_}*{F},1,0)" if r == ta
                                 else f"=IF(AND({Kk(10)}{r - 1}=1,{Kk(9)}{r}>={bd_}*{F}),1,0)")
            w[f"{Kk(11)}{r}"] = sfun(f"{Kk(9)}{r}", f"{Kk(10)}{r}")
            for col, fm in ((6, "0.0"), (7, "0"), (8, "0.00"), (10, "0"), (11, "0.00")):
                w[f"{Kk(col)}{r}"].number_format = fm
                salin_fill(w, f"{Kk(col)}{r}", f"{Kk(5)}{r}")
        li.kosong()
        rs = li.baris
        sm2, smb = f"{Kk(8)}{rs}", f"{Kk(11)}{rs}"
        w[f"{Kk(0)}{rs}"] = "Σ s kelompok (mm)"
        w[sm2], w[smb] = f"=SUM({Kk(8)}{ta}:{Kk(8)}{tz_})", f"=SUM({Kk(11)}{ta}:{Kk(11)}{tz_})"
        w[f"{Kk(0)}{rs + 1}"] = "s total = s NP + Σ s + Δe (mm)"
        w[f"{Kk(8)}{rs + 1}"], w[f"{Kk(11)}{rs + 1}"] = f"={SNP}+{sm2}+{DE}", f"={SNP}+{smb}+{DE}"
        for r in (rs, rs + 1):
            w[f"{Kk(0)}{r}"].font = w[f"{Kk(0)}{ta}"].font.copy(bold=True)
            for col in (8, 11):
                w[f"{Kk(col)}{r}"].number_format = "0.00"
                salin_fill(w, f"{Kk(col)}{r}", f"{Kk(5)}{ta}")
        li.baris = rs + 3
        adr["blok"][kd] = dict(kel2=f"'Cap Inti'!{sm2}", kelb=f"'Cap Inti'!{smb}", tot2=f"'Cap Inti'!{Kk(8)}{rs + 1}", totb=f"'Cap Inti'!{Kk(11)}{rs + 1}")
    li.ws.freeze_panes = "A5"

    # ---- Penurunan Beda
    lb = Lembar(wb.create_sheet("Penurunan Beda"), 6, "Penurunan beda pasangan cap bertetangga", [5, 10, 10, 8, 9, 9, 9, 9, 10, 10, 11, 12, 12, 9, 9, 9, 10, 10])
    lb.catatan(ket + f" s dari lembar Per Cap (s tot c, Boussinesq). δ izin {DELTA_IZIN:.0f} mm, δ/L ≤ 1/500. Pasangan urut δ menurun.")
    lb.kosong()
    rows = [[k + 1, p["a"], p["b"], p["L"], "ya" if p["lintas"] else "tidak", p["s_a"], p["s_b"], None, None, None, None, None, None, p["s_a_d"], p["s_b_d"], None, None, None] for k, p in enumerate(ps)]
    kp = ["No", "Cap 1", "Cap 2", "L (m)", "Lintas zona", "s 1", "s 2", "δ (mm)", "δ/L", "δ ≤ 16", "δ/L ≤ 1/500", "M sloof 400×800", "M SL-1 400×900", "s 1 (d)", "s 2 (d)", "δ (d)", "δ/L (d)", "δ ≤ 16 (d)"]
    b0, ba, bz = lb.tabel(kp, rows, rata=["c", "l", "l", "r", "c", "r", "r", "r", "r", "c", "c", "r", "r", "r", "r", "r", "r", "c"], beku=True, beku_kolom=3,
                          fmt=[None, None, None, "0.00", None, "0.0", "0.0", "0.0", "0.00000", None, None, "#,##0", "#,##0", "0.0", "0.0", "0.0", "0.00000", None],
                          fill_kolom={3: AI, 5: AI, 6: AI, 13: AI, 14: AI})
    idc, cc_col = adr["pc_id"], adr["pc_c"]
    w, Kb = lb.ws, lb.kol
    for r in range(ba, bz + 1):
        w[f"{Kb(5)}{r}"] = f"=INDEX({cc_col},MATCH({Kb(1)}{r},{idc},0))"
        w[f"{Kb(6)}{r}"] = f"=INDEX({cc_col},MATCH({Kb(2)}{r},{idc},0))"
        w[f"{Kb(7)}{r}"] = f"=ABS({Kb(5)}{r}-{Kb(6)}{r})"
        w[f"{Kb(8)}{r}"] = f"={Kb(7)}{r}/1000/{Kb(3)}{r}"
        w[f"{Kb(9)}{r}"] = f"=IF({Kb(7)}{r}<={DELTA_IZIN},\"OK\",\"> 16 mm\")"
        w[f"{Kb(10)}{r}"] = f"=IF({Kb(8)}{r}<={ROT_IZIN},\"OK\",\"> 1/500\")"
        w[f"{Kb(11)}{r}"] = f"=249.1*{Kb(7)}{r}/16*(8/{Kb(3)}{r})^2"
        w[f"{Kb(12)}{r}"] = f"=354.7*{Kb(7)}{r}/16*(8/{Kb(3)}{r})^2"
        w[f"{Kb(15)}{r}"] = f"=ABS({Kb(13)}{r}-{Kb(14)}{r})"
        w[f"{Kb(16)}{r}"] = f"={Kb(15)}{r}/1000/{Kb(3)}{r}"
        w[f"{Kb(17)}{r}"] = f'=IF({Kb(15)}{r}<={DELTA_IZIN},"OK","> 16 mm")'
        for col, fm in ((5, "0.0"), (6, "0.0"), (7, "0.0"), (8, "0.00000"), (11, "#,##0"), (12, "#,##0"), (15, "0.0"), (16, "0.00000")):
            w[f"{Kb(col)}{r}"].number_format = fm
            salin_fill(w, f"{Kb(col)}{r}", f"{Kb(3)}{r}")
    lb.kosong()
    s0_, sa_, sz_ = lb.tabel(["Ringkasan", "", "Nilai"], [["δ maksimum (mm)", "", f"=MAX({Kb(7)}{ba}:{Kb(7)}{bz})"],
                                                          ["Pasangan δ > 16 mm", "", f"=COUNTIF({Kb(7)}{ba}:{Kb(7)}{bz},\">{DELTA_IZIN}\")"],
                                                          ["Pasangan δ/L > 1/500", "", f"=COUNTIF({Kb(8)}{ba}:{Kb(8)}{bz},\">{ROT_IZIN}\")"],
                                                          ["δ maksimum (d) (mm)", "", f"=MAX({Kb(15)}{ba}:{Kb(15)}{bz})"],
                                                          ["Pasangan δ (d) > 16 mm", "", f"=COUNTIF({Kb(15)}{ba}:{Kb(15)}{bz},\">{DELTA_IZIN}\")"]],
                             rata=["l", "l", "r"], beku=False, fill_kolom={2: AI})
    adr["beda"] = dict(max=f"'Penurunan Beda'!{Kb(2)}{sa_}", n=bz - ba + 1)

    # ---- Sloof
    ls = Lembar(wb.create_sheet("Sloof"), 7, "Akibat ke sloof (5.4)", [48, 16, 80])
    ls.catatan(ket + " Berkas 5.4 tidak diubah.")
    ls.kosong()
    p = sl["pasangan"]
    rows = [["Pasangan penentu", f"{p['a']} - {p['b']}", "δ terbesar, varian c Boussinesq"], ["δ (mm)", p["delta"], "lembar Penurunan Beda"],
            ["L (m)", p["L"], "jarak pusat ke pusat"],
            ["M sloof 400 × 800 per 16 mm, L 8 m (kNm)", 249.1, "5.4 (M = 6 Ec Ie δ / L²)"], ["M sloof SL-1 400 × 900 per 16 mm, L 8 m (kNm)", 354.7, "5.4"],
            ["M 400 × 800 pada δ maks (kNm)", None, "rumus hidup: M16 δ/16 (8/L)²"], ["M SL-1 400 × 900 pada δ maks (kNm)", None, "rumus hidup"],
            ["Rasio SL-1 (1,2D+1,6L+1,0T) pada δ 16 mm", sl["rasio16"], "skrip: tulangan desain 5.4 (kode kini), bagian T diskala; teks 5.4 menulis 0,48"],
            ["Rasio SL-1 pada δ maks", sl["rasio"], "(momen negatif 1,2D+1,6L + T diskala) / φMn"],
            ["δ saat rasio SL-1 = 1 (mm, L 8 m)", sl["delta_batas"], "cadangan sampai δ ini"],
            ["Varian (d): pasangan penentu", f"{h['sloof_d']['pasangan']['a']} - {h['sloof_d']['pasangan']['b']}", "δ terbesar varian (d)"],
            ["Varian (d): δ (mm)", h["sloof_d"]["pasangan"]["delta"], ""], ["Varian (d): L (m)", h["sloof_d"]["pasangan"]["L"], ""],
            ["Varian (d): M SL-1 400 × 900 (kNm)", None, "rumus hidup"],
            ["Varian (d): rasio SL-1", h["sloof_d"]["rasio"], "(1,2D+1,6L) + T diskala / φMn"]]
    s0, sa, sz = ls.tabel(["Besaran", "Nilai", "Keterangan"], rows, rata=["l", "r", "l"], fill_kolom={1: AI}, beku=False, fmt=[None, "#,##0.00", None])
    Kv = lambda k: f"{ls.kol(1)}{sa + k}"
    ls.ws[Kv(5)] = f"={Kv(3)}*{Kv(1)}/16*(8/{Kv(2)})^2"
    ls.ws[Kv(6)] = f"={Kv(4)}*{Kv(1)}/16*(8/{Kv(2)})^2"
    ls.ws[Kv(13)] = f"={Kv(4)}*{Kv(11)}/16*(8/{Kv(12)})^2"
    for k in (5, 6, 13):
        ls.ws[Kv(k)].number_format = "#,##0.0"

    # ---- GeoFEM3D
    lg = Lembar(wb.create_sheet("GeoFEM3D"), 8, "Cek silang GeoFEM3D (butir b)", [14, 9, 9, 11, 12, 12, 8, 14, 14, 12, 12, 10])
    lg.catatan(ket + " GeoFEM3D: beban merata di permukaan (puncak model = elevasi rakit (a)), elastis terdrainase, cap terisolasi, dasar kaku z 55 m; "
               "1D elastis setara = Σ Δσ h / M (Boussinesq cap terisolasi, M modulus terbatas).")
    lg.kosong()
    if h.get("fem"):
        rows = []
        for kd, f in h["fem"].items():
            m = f["masuk"]
            rows.append([kd, m["B"], m["L"], m["q"], m["lap"][0]["E"] / 1000, m["lap"][1]["E"] / 1000, NU, m["s1d_elastis"], f["fem"], None, TOL["fem"], None])
        g0, ga, gz = lg.tabel(["Cap", "B (m)", "L (m)", "q (kPa)", "E U6 (MPa)", "E U7 (MPa)", "ν", "s 1D elastis (mm)", "s GeoFEM3D (mm)", "Selisih (%)", "Batas (%)", "Status"],
                              rows, rata=["l"] + ["r"] * 10 + ["c"], beku=False, fmt=[None, "0.00", "0.00", "0.0", "0.0", "0.0", "0.00", "0.00", "0.00", "0.00", "0", None],
                              fill_kolom={i: AI for i in range(1, 9)})
        for r in range(ga, gz + 1):
            lg.ws[f"{lg.kol(9)}{r}"] = f"=ABS({lg.kol(8)}{r}-{lg.kol(7)}{r})/{lg.kol(7)}{r}*100"
            lg.ws[f"{lg.kol(11)}{r}"] = f"=IF({lg.kol(9)}{r}<={lg.kol(10)}{r},\"lolos\",\"GAGAL\")"
            lg.ws[f"{lg.kol(9)}{r}"].number_format = "0.00"
            salin_fill(lg.ws, f"{lg.kol(9)}{r}", f"{lg.kol(8)}{r}")
        lg.kosong()
        lg.tabel(["Cap", "s 1D Cr/Cc terisolasi (mm)", "Waktu (s)", "DOF"], [[kd, f["masuk"]["s1d_cr"], f["waktu"], f["dof"]] for kd, f in h["fem"].items()],
                 rata=["l", "r", "r", "r"], beku=False, fmt=[None, "0.0", "0", "0"], fill_kolom={1: AI, 2: AI, 3: AI})
    else:
        lg.catatan("GeoFEM3D belum dijalankan.")

    # ---- Verifikasi
    lv = Lembar(wb.create_sheet("Verifikasi"), 9, "Verifikasi T-104", [8, 90, 16, 12])
    lv.catatan(ket + " Butir a diisi setelah Excel dihitung ulang (lihat VERIFIKASI.md T-104).")
    lv.kosong()
    t = t104(None, None, h)
    lv.tabel(["Butir", "Pembanding", "Selisih (%)", "Batas (%)"], [
        ["a", "Python vs Excel rumus hidup (Cap E, 3/C: s kelompok 2V:1H dan Boussinesq, s total; lembar Per Cap; δ maksimum)", None, TOL["excel"]],
        ["b", "1D elastis setara vs GeoFEM3D (Cap E, 3/C), selisih terbesar", t["dfem"], TOL["fem"]],
        ["c", "Δe tangan (Pers. 9-20, Q rata-rata per ruas) vs integrasi Q(z), selisih terbesar 63 cap", t["dde"], TOL["de"]],
        ["d", "s tunggal model (Q0 / k) pada 1.400 kN vs rata-rata uji beban TP-1..4 pada 1.400 kN", t["dd"], TOL["uji"]]],
        rata=["c", "l", "r", "r"], beku=False, fmt=[None, None, "0.00", "0"], fill_kolom={2: AI})
    # ---- Acuan dan Keputusan
    la = Lembar(wb.create_sheet("Acuan"), 10, "Acuan", [90, 22, 70])
    la.catatan(ket)
    la.kosong()
    la.tabel(["Acuan", "Status", "Lokasi"], [list(a_) for a_ in ACUAN], rata=["l", "l", "l"], beku=False)
    lk = Lembar(wb.create_sheet("Keputusan"), 11, "Keputusan usulan AI dan hal untuk Defsa", [150])
    lk.catatan(ket)
    lk.kosong()
    lk.bagian("A", "Keputusan usulan AI (dipakai di hitungan)")
    lk.tabel(["Butir"], [[x] for x in KEPUTUSAN], rata=["l"], beku=False)
    lk.kosong()
    lk.bagian("B", "Hal yang perlu diputuskan Defsa")
    lk.tabel(["Butir"], [[x] for x in keputusan_defsa(h)], rata=["l"], beku=False)
    lk.kosong()
    lk.bagian("C", "Keputusan Defsa")
    lk.tabel(["Butir"], [["22 Nov 2026: varian (d) kalibrasi uji beban disetujui sebagai dasar desain; (a)/(b) batas atas; "
                          "δ desain sloof 22,2 mm; sloof SL-2/SL-3 400 × 800 (M 345 kNm) dicek di 6.7."]], rata=["l"], beku=False)
    Path(keluar).parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar, adr


# ================================================================== verifikasi T-104
def t104(berkas=None, adr=None, h=None):
    h = h or semua()
    caps = h["caps"]
    dde = max(abs(c["de"]["de"] - c["de"]["tangan"]) / c["de"]["de"] * 100 for c in caps)
    dfem = max(f["selisih"] for f in h["fem"].values()) if h.get("fem") else None
    u = h["uji"]
    dd = abs(u["s_model_1400"] - float(np.mean(u["ukur_1400"]))) / float(np.mean(u["ukur_1400"])) * 100
    dxl = None
    if berkas and adr:
        import openpyxl
        wb = openpyxl.load_workbook(berkas, data_only=True)

        def baca(a):
            sh, cel = a.split("!")
            return wb[sh.strip("'")][cel].value
        ds = []
        for kd in ("Cap E", "3/C"):
            i = cap_nomor(caps, kd)
            c = caps[i]
            py = {"kel2": h["res"][("a", "2v1")]["s_kel"][i], "kelb": h["res"][("a", "bous")]["s_kel"][i],
                  "tot2": c["s_np"] + h["res"][("a", "2v1")]["s_kel"][i] + c["de"]["de"],
                  "totb": c["s_np"] + h["res"][("a", "bous")]["s_kel"][i] + c["de"]["de"]}
            for k, v in py.items():
                ds.append(abs(float(baca(adr["blok"][kd][k])) - v) / abs(v) * 100)
            ra, _ = adr["pc_rows"]
            tot_a = wb["Per Cap"][f"{adr['pc_col']['a']}{ra + i}"].value
            ds.append(abs(float(tot_a) - py["totb"]) / py["totb"] * 100)
        ds.append(abs(float(baca(adr["beda"]["max"])) - h["pasangan"][0]["delta"]) / h["pasangan"][0]["delta"] * 100)
        dxl = max(ds)
    lolos = (dxl is not None and dxl <= TOL["excel"] and dfem is not None and dfem <= TOL["fem"] and dde <= TOL["de"] and dd <= TOL["uji"])
    return dict(dxl=dxl, dfem=dfem, dde=dde, dd=dd, lolos=lolos)


def catat_t104(r, h, berkas=VERIFIKASI):
    f = h.get("fem", {})
    fs = "; ".join(f"{k}: 1D elastis {idn(v['masuk']['s1d_elastis'], 1)} mm vs GeoFEM3D {idn(v['fem'], 1)} mm ({idn(v['selisih'], 1)} %)" for k, v in f.items())
    baris = ("| T-104 | Cek silang 6.6 penurunan kelompok tiang (63 cap, rakit ekuivalen, superposisi Boussinesq) dan penurunan beda | (a) Python vs Excel rumus hidup "
             f"(Cap E, 3/C: s kelompok 2V:1H, Boussinesq, s total; lembar Per Cap; δ maks): selisih terbesar {idn(r['dxl'], 4) if r['dxl'] is not None else 'tidak dihitung'} % "
             f"| (b) 1D elastis setara (modulus terbatas) vs GeoFEM3D (cap terisolasi, elastis): {fs}; (c) Δe tangan (Pers. 9-20, Q rata-rata per ruas) vs integrasi Q(z): "
             f"selisih terbesar 63 cap {idn(r['dde'], 2)} %; "
             f"(d) s tunggal model Q0/k = {idn(h['uji']['s_model_1400'], 2)} mm vs uji beban TP-1..4 pada 1.400 kN rata-rata {idn(float(np.mean(h['uji']['ukur_1400'])), 2)} mm "
             f"(selisih {idn(r['dd'], 1)} %) | (a) ≤ 1 %; (b) ≤ 25 %; (c) ≤ 10 %; (d) ≤ 10 % | {'Lolos' if r['lolos'] else 'GAGAL'}, {STATUS} "
             "| `skrip/tahap6_penurunan.py`, `tests/test_tahap6_penurunan.py` | Ditetapkan sebelum membandingkan. Data simulasi. GeoFEM3D hanya beban permukaan, elastis, terdrainase; "
             "bukan pembanding konsolidasi Cc. |")
    teks = Path(berkas).read_text(encoding="utf-8").split("\n")
    teks = [ln for ln in teks if not ln.startswith("| T-104 |")]
    i = next(k for k, ln in enumerate(teks) if ln.startswith("| T-103 |"))
    teks.insert(i + 1, baris)
    Path(berkas).write_text("\n".join(teks), encoding="utf-8")
    return baris


# ================================================================== Markdown
def tabel_md(kep, baris):
    return ["| " + " | ".join(kep) + " |", "|" + "---|" * len(kep)] + ["| " + " | ".join(str(x) for x in b) + " |" for b in baris]


def tulis_md(h=None, r=None, keluar=MD):
    h = h or semua()
    r = r or t104(h=h)
    caps, res, tz_t, ps, sl = h["caps"], h["res"], h["tz"], h["pasangan"], h["sloof"]
    tot = h["total"]
    n16 = sum(p["delta"] > DELTA_IZIN for p in ps)
    nrot = sum(p["rot"] > ROT_IZIN for p in ps)
    L = ["# 6.6 Penurunan kelompok tiang dan penurunan beda\n",
         LABEL,
         f"Dihitung AI atas permintaan Defsa (22 Nov 2026). STATUS: {STATUS}. DIHITUNG AI ATAS PERMINTAAN DEFSA (22 Nov 2026). Kunci jawaban tidak dibuka.\n",
         "Defsa meminta AI menghitung; hasilnya di berkas ini. Excel: `6.6 Penurunan Pondasi.xlsx`; skrip: `skrip/tahap6_penurunan.py`; peta: `Gambar/6.6 Peta Penurunan.png`.\n",
         "## 1. Tujuan\n",
         "Menghitung penurunan kepala 63 cap gedung utama (56 cap kolom + 7 cap inti, 244 tiang Ø800, 38,45 m) dari beban layan, lalu penurunan beda antar cap bertetangga "
         "terhadap batas 16 mm (0,002 L) dan 1/500, dan akibatnya ke sloof 5.4.\n",
         "## 2. Data dan acuan\n",
         f"- Tiang: A 0,5027 m², Ec 25.743 MPa (EA {idn(EA / 1000, 0)} MN), kepala sendi (6.5). Beban: Σ Pmax layan tiap cap (6.3, tanpa Qn).",
         f"- U6 (konsolidasi 1D): Cr {idn(CR, 2)}, Cc {idn(CC, 2)}, σ'p {SP:.0f} kPa, e0 {idn(E0, 2)} [Uji sendiri 2.4]. U7 elastis Es 48 MPa, ν 0,30 "
         "(NHI-06-088 Tabel 5-16 hal. 5-85) [Literatur]. Dasar kaku z 55 m [Asumsi]; hitungan berhenti di Δσ < 10 % σ'v0. Sublapis ≤ 1 m. σ'v0 dari `tahap3_pondasi.sigma_v` (termasuk urugan).",
         "- Rakit ekuivalen: luas kelompok (jarak as terluar + D). (a) D/3 di atas ujung (NHI-06-089 Gb. 9-35 hal. 9-85): selatan -21,50, utara dan tengah -21,35. "
         f"(b) bidang netral 6.2: selatan {idn(tz_t['SELATAN']['e_b'], 2)}, tengah {idn(tz_t['TENGAH']['e_b'], 2)}, utara {idn(tz_t['UTARA']['e_b'], 2)}. (c) ambil terbesar per cap.",
         "- s tanah di bidang netral (6.2): " + ", ".join(f"{z.lower()} {idn(tz_t[z]['s_np'], 1)} mm" for z in tz_t) + " (tengah dari fungsi 6.2 untuk TENGAH).",
         "- Interaksi: superposisi Boussinesq (beban persegi panjang merata, metode sudut) dari 63 cap di pusat tiap cap, tiap cap pada elevasi rakitnya; pembanding "
         "penyebaran 2V:1H (NHI-06-089 Gb. 9-36 hal. 9-86) cap berdiri sendiri. Acuan lengkap: lembar Acuan di Excel.\n",
         "## 3. Hasil\n",
         "Penurunan total maksimum per zona tanah (mm):\n"]
    rows = []
    for tz in ("SELATAN", "TENGAH", "UTARA"):
        idx = [i for i, c in enumerate(caps) if c["tz"] == tz]
        rw = [tz, len(idx)] + [idn(max(tot[k][i] for i in idx), 1) for k in (("a", "bous"), ("b", "bous"), ("a", "2v1"), ("b", "2v1"))]
        i_m = max(idx, key=lambda i: tot[("c", "bous")][i])
        rows.append(rw + [f"{caps[i_m]['id']} {idn(tot[('c', 'bous')][i_m], 1)}"])
    L += tabel_md(["Zona", "Cap", "(a) Boussinesq", "(b) Boussinesq", "(a) 2V:1H", "(b) 2V:1H", "Terbesar (c)"], rows)
    L += ["", "Cap kunci (mm; s total = s NP + s kelompok + Δe; kolom (a)/(b) = s kelompok Boussinesq):\n"]
    rows = []
    for kd in KUNCI:
        i = cap_nomor(caps, kd)
        c = caps[i]
        rows.append([kd, c["tz"], c["n"], idn(c["W"], 0), idn(c["s_np"], 1), idn(res[("a", "bous")]["s_kel"][i], 1), idn(res[("b", "bous")]["s_kel"][i], 1),
                     idn(c["de"]["de"], 1), idn(tot[("c", "bous")][i], 1), idn(tot[("c", "2v1")][i], 1)])
    L += tabel_md(["Cap", "Zona tanah", "n", "ΣP (kN)", "s NP", "s kel (a)", "s kel (b)", "Δe", "s total (c)", "s total (c) 2V:1H"], rows)
    zc = h["caps"][cap_nomor(caps, "Cap E")]["de"]
    L += ["",
          f"Δe: Q(z) naik dari Q0 = ΣP/n ke Q0 + Qn di bidang netral lalu turun ke tahanan ujung (profil 6.2 dengan Q = Q0). Contoh Cap E: Q0 {idn(caps[cap_nomor(caps, 'Cap E')]['Q0'], 0)} kN, "
          f"bidang netral {idn(zc['zn'], 1)} m dari muka tanah, Qmaks {idn(zc['Qmaks'], 0)} kN, Δe {idn(zc['de'], 1)} mm. Bidang netral per cap bergeser dari 6.2 (Q 911 kN) karena Q0 berbeda; "
          "letak rakit (b) dan s NP tetap memakai nilai 6.2.",
          f"Semua 63 cap: s total (c, Boussinesq) {idn(float(tot[('c', 'bous')].min()), 1)} sampai {idn(float(tot[('c', 'bous')].max()), 1)} mm; "
          "cap inti lebih kecil daripada cap kolom karena tekanan rakit lebih rendah (luas besar). Batas Δσ < 10 % σ'v0 tidak pernah tercapai sebelum dasar U7 (z 55 m) "
          f"karena 63 cap bersama membebani lapisan dalam: hitungan memakai seluruh U6 dan U7 sampai z 55 m (s kelompok Cap E (a) {idn(res[('a', 'bous')]['s_kel'][cap_nomor(caps, 'Cap E')], 1)} mm; "
          f"tanpa pemotongan {idn(res[('a', 'bous')]['s_z55'][cap_nomor(caps, 'Cap E')], 1)} mm).\n",
          "## 3a. Varian (d): kalibrasi uji beban statik (usulan AI, hasil utama penurunan beda)\n",
          "Rakit seluas kelompok (a)/(b) terlalu besar dibanding uji beban statik 6.2: kekakuan kepala 462-512 kN/mm pada 911 kN, TP-1..4 turun 4,5-5,1 mm pada 1.822 kN, "
          f"tiang tunggal 1.400 kN ±3 mm (model Q0/k = {idn(h['uji']['s_model_1400'], 2)} mm; uji {idn(float(np.mean(h['uji']['ukur_1400'])), 2)} mm). Cap 4 tiang 240 mm = ±80 kali tiang tunggal, "
          "karena rakit seluas kelompok memusatkan 500-550 kPa di U6 dan melewati σ'p. Varian (d):\n",
          f"s = s NP (6.2) + FJ × s tunggal × Rs + s global; s tunggal = Q0 / k, k = {idn(h['uji']['k'], 0)} kN/mm (rata-rata TP-1..4 pada 911 kN, kekakuan kepala sudah memuat pemendekan elastis, "
          f"jadi Δe tidak ditambah); FJ = {idn(FJ, 1)} jangka panjang [Asumsi: konsolidasi U6 OC]; Rs = n^0,5 [Literatur: Fleming dkk./Randolph, belum ada di acuan/]; "
          f"s global = konsolidasi U6 + U7 di bawah satu rakit gedung {idn(h['d']['B'], 1)} × {idn(h['d']['L'], 1)} m (ΣP {idn(h['d']['W'], 0)} kN, q {idn(h['d']['W'] / h['d']['A'], 0)} kPa) di elevasi rakit (a), "
          f"Boussinesq di pusat tiap cap, σ'p = {idn(OCR, 1)} × σ'v0 tanah asli (naik dengan kedalaman).\n",
          "Perbandingan varian (s total maksimum / minimum antar cap, mm; pasangan bertetangga):\n"] + tabel_md(
              ["Varian", "s total min", "s total maks", "δ maks (mm)", "Pasangan δ maks", "Jumlah > 16 mm", "δ/L maks"],
              [[nm, idn(float(tot[k].min()), 1), idn(float(tot[k].max()), 1), idn(h["pasangan_v"][k][0]["delta"], 1),
                f"{h['pasangan_v'][k][0]['a']} - {h['pasangan_v'][k][0]['b']}", sum(q["delta"] > DELTA_IZIN for q in h["pasangan_v"][k]),
                f"1/{idn(1 / h['pasangan_v'][k][0]['rot'], 0)}"]
               for k, nm in ((("a", "bous"), "(a) rakit D/3, Boussinesq"), (("b", "bous"), "(b) rakit di NP, Boussinesq"), (("c", "bous"), "(c) terbesar a/b"),
                             (("d", "bous"), "**(d) kalibrasi uji beban (usulan)**"))]) + [
          "", "Per zona tanah, varian (d), s total (mm):\n"] + tabel_md(
              ["Zona", "Cap", "Maks", "Min"], [[tz, sum(c["tz"] == tz for c in caps), idn(max(tot[("d", "bous")][i] for i, c in enumerate(caps) if c["tz"] == tz), 1),
                                                  idn(min(tot[("d", "bous")][i] for i, c in enumerate(caps) if c["tz"] == tz), 1)] for tz in ("SELATAN", "TENGAH", "UTARA")]) + [
          "", "Cap kunci varian (d) (mm): " + "; ".join(
              f"{kd}: s NP {idn(caps[cap_nomor(caps, kd)]['s_np'], 1)} + kel {idn(FJ * h['d']['s_tung'][cap_nomor(caps, kd)] * h['d']['rs'][cap_nomor(caps, kd)], 1)} + global "
              f"{idn(h['d']['s_glob'][cap_nomor(caps, kd)], 1)} = {idn(tot[('d', 'bous')][cap_nomor(caps, kd)], 1)}" for kd in KUNCI) + ".",
          "", f"Kepekaan σ'p: σ'p tetap 400 kPa di seluruh U6 dipakai pada (a)-(c). Dengan σ'p = {idn(OCR, 1)} × σ'v0 tanah asli (naik dengan kedalaman), s kelompok (a) Boussinesq: "
          + "; ".join(f"{kd} {idn(res[('a', 'bous')]['s_kel'][cap_nomor(caps, kd)], 1)} menjadi {idn(h['ocr_a'][cap_nomor(caps, kd)], 1)} mm" for kd in ("3/C", "Cap E")) + ".\n",
          "![Peta penurunan (c)](Gambar/6.6%20Peta%20Penurunan.png)\n",
          "![Peta penurunan (d)](Gambar/6.6%20Peta%20Penurunan%20(d).png)\n",
          "## 4. Penurunan beda\n",
          f"{len(ps)} pasangan bertetangga (jarak pusat ke pusat ≤ 8,5 m, termasuk cap inti ke cap kolom; L sebenarnya dicatat). Varian (c) Boussinesq: "
          f"**{n16} pasangan δ > 16 mm**, {nrot} pasangan δ/L > 1/500. Pembanding:\n",
          "| Varian | δ maks (mm) | Pasangan | Jumlah > 16 mm |", "|---|---|---|---|"]
    for k, nm in ((("a", "bous"), "(a) Boussinesq"), (("b", "bous"), "(b) Boussinesq"), (("c", "bous"), "(c) Boussinesq (dipakai)"), (("a", "2v1"), "(a) 2V:1H"),
                  (("b", "2v1"), "(b) 2V:1H"), (("c", "2v1"), "(c) 2V:1H")):
        pk = h["pasangan_v"][k]
        L.append(f"| {nm} | {idn(pk[0]['delta'], 1)} | {pk[0]['a']} - {pk[0]['b']} (L {idn(pk[0]['L'], 2)} m, δ/L 1/{idn(1 / pk[0]['rot'], 0)}) | {sum(p['delta'] > DELTA_IZIN for p in pk)} |")
    L += ["", "Sepuluh pasangan terbesar (varian c, Boussinesq):\n"]
    L += tabel_md(["Pasangan", "L (m)", "Lintas zona", "s 1", "s 2", "δ (mm)", "δ/L"],
                  [[f"{p['a']} - {p['b']}", idn(p["L"], 2), "ya" if p["lintas"] else "tidak", idn(p["s_a"], 1), idn(p["s_b"], 1), idn(p["delta"], 1), f"1/{idn(1 / p['rot'], 0)}"]
                   for p in ps[:10]])
    for a_, b_ in (("3/B", "3/C"),):
        p = next((q for q in ps if {q["a"], q["b"]} == {a_, b_}), None)
        if p:
            L += ["", f"Pasangan lintas zona {a_}-{b_}: δ {idn(p['delta'], 1)} mm, δ/L 1/{idn(1 / p['rot'], 0)} (s {idn(p['s_a'], 1)} dan {idn(p['s_b'], 1)} mm)."]
    L += ["", "## 5. Akibat ke sloof (5.4, berkas 5.4 tidak diubah)\n",
          f"Pasangan penentu {sl['pasangan']['a']} - {sl['pasangan']['b']}, δ {idn(sl['pasangan']['delta'], 1)} mm, L {idn(sl['pasangan']['L'], 2)} m. M sebanding δ dan 1/L²: "
          f"400 × 800 {idn(sl['M']['400x800'], 0)} kNm (249,1 per 16 mm), SL-1 400 × 900 {idn(sl['M']['SL-1 400x900'], 0)} kNm (354,7 per 16 mm).",
          f"Rasio SL-1 pada 1,2D + 1,6L + 1,0T dengan tulangan 5.4 tetap: {idn(sl['rasio16'], 2)} pada δ 16 mm (kode 5.4 kini; teks 5.4 menulis 0,48, selisih dicatat), "
          f"**{idn(sl['rasio'], 2)} pada δ maksimum**. Rasio = 1 tercapai pada δ ±{idn(sl['delta_batas'], 0)} mm (L 8 m): cadangan sloof sampai δ itu.\n",
          f"Varian (d): pasangan penentu {h['sloof_d']['pasangan']['a']} - {h['sloof_d']['pasangan']['b']}, δ {idn(h['sloof_d']['pasangan']['delta'], 1)} mm; "
          f"M SL-1 {idn(h['sloof_d']['M']['SL-1 400x900'], 0)} kNm, 400 × 800 {idn(h['sloof_d']['M']['400x800'], 0)} kNm; rasio SL-1 {idn(h['sloof_d']['rasio'], 2)}.\n",
          "## 6. GeoFEM3D (cek silang butir b)\n"]
    if h.get("fem"):
        L += ["GeoFEM3D hanya beban permukaan, elastis, terdrainase (README GeoFEM3D). Model: cap terisolasi, puncak model di elevasi rakit (a), q = ΣP/(B × L), "
              "U6 E dari modulus terbatas M = (1 + e0) σ' / (0,434 Cr) pada σ' rata-rata (E = M (1+ν)(1-2ν)/(1-ν), ν 0,30), U7 E 48 MPa, dasar kaku z 55 m. Pembanding: 1D elastis setara "
              "(Σ Δσ h / M, Boussinesq cap terisolasi), bukan versi Cc.\n"]
        L += tabel_md(["Cap", "B × L (m)", "q (kPa)", "E U6 (MPa)", "s 1D elastis (mm)", "s GeoFEM3D (mm)", "Selisih (%)", "1D Cr/Cc terisolasi (mm)"],
                      [[k, f"{idn(f['masuk']['B'], 2)} × {idn(f['masuk']['L'], 2)}", idn(f["masuk"]["q"], 0), idn(f["masuk"]["lap"][0]["E"] / 1000, 1), idn(f["masuk"]["s1d_elastis"], 1),
                        idn(f["fem"], 1), idn(f["selisih"], 1), idn(f["masuk"]["s1d_cr"], 1)] for k, f in h["fem"].items()])
    else:
        L += ["GeoFEM3D belum dijalankan."]
    L += ["", "## 7. Verifikasi T-104 (tercatat di `VERIFIKASI.md`)\n",
          f"- (a) Python vs Excel rumus hidup (Cap E, 3/C, lembar Per Cap, δ maks): selisih terbesar {idn(r['dxl'], 4) if r['dxl'] is not None else 'tidak dihitung'} % (batas 1 %).",
          f"- (b) 1D elastis setara vs GeoFEM3D: selisih terbesar {idn(r['dfem'], 1) if r['dfem'] is not None else 'tidak dihitung'} % (batas 25 %).",
          f"- (c) Δe tangan (Pers. 9-20, Q rata-rata per ruas) vs integrasi: selisih terbesar {idn(r['dde'], 2)} % (batas 10 %).",
          f"- (d) s tunggal model Q0/k pada 1.400 kN {idn(h['uji']['s_model_1400'], 2)} mm vs uji beban TP-1..4 rata-rata {idn(float(np.mean(h['uji']['ukur_1400'])), 2)} mm: selisih {idn(r['dd'], 1)} % (batas 10 %).",
          "- Status: " + ("Lolos." if r["lolos"] else "GAGAL, lihat VERIFIKASI.md."), "",
          "## 8. Temuan\n",
          f"1. Penurunan total cap {idn(float(tot[('c', 'bous')].min()), 0)}-{idn(float(tot[('c', 'bous')].max()), 0)} mm (Boussinesq) dan **{n16} dari {len(ps)} pasangan melebihi 16 mm**: batas 16 mm dilampaui jauh, bukan hanya di utara.",
          "2. Penyebab utama: metode rakit seluas kelompok memberi tekanan ±550 kPa di bawah cap 4 tiang (di atas σ'p 400 kPa, Cc ikut bekerja), sedangkan cap inti (luas besar) "
          "bertekanan jauh lebih rendah; selisih tekanan itu menjadi penurunan beda. Ini batas atas konservatif; varian 2V:1H lebih halus tetapi tetap melebihi 16 mm.",
          "3. Varian (b) (rakit di bidang netral) lebih besar daripada (a) hampir di semua cap karena U6 yang tertekan lebih tebal; keduanya memakai Qn = 0 pada beban rakit "
          "(sesuai lembar isian), sehingga (b) kemungkinan lebih besar lagi bila Qn ikut dibebankan ke tanah di bawah bidang netral.",
          "4. Cap A, 3/C ada di zona TENGAH menurut tebal gambut (lembar isian menyebutnya utara karena tengah diperlakukan utara pada sifat tiang); s NP tengah 14,8 mm.",
          "5. Titik rakit (b) di -13,7 sampai -14,0 berada di dalam U6 (U6 mulai ±-9,3), bukan di U5 seperti tertulis di lembar isian; U5 tidak masuk hitungan s kelompok.",
          "6. Tiang utara memakai ujung t3 -27,39 (profil 6.2) sedangkan lembar isian -27,60; selisih 0,2 m tidak mengubah hasil berarti.",
          "7. Sisa penurunan tanah utara 874 mm tidak diperhitungkan ke sloof (itu terhadap pelat halaman, Tahap 7).",
          "9. (a)/(b) tidak cocok dengan uji beban statik 6.2 (tiang tunggal 1.400 kN ±3 mm; cap 4 tiang 240 mm, ±80 kali): dipertahankan hanya sebagai batas atas; varian (d) dikalibrasi ke uji beban.",
          "10. Rasio SL-1 pada δ 16 mm: kode 5.4 kini 0,534, teks 5.4 menulis 0,48 (selisih belum dijelaskan; berkas 5.4 tidak diubah).",
          "11. Lembar isian A.2 menulis OCR 3,8-4,0: itu salah baca kolom (3,8/4,0 adalah cv m²/th). OCR = σ'p bilinear / σ'v0 = 408,2/169,5 = 2,41 dan 424,4/198,3 = 2,14; baris diperbaiki. "
          "Skrip memakai σ'p tetap 400 kPa di seluruh U6 pada (a)-(c); kepekaan OCR 2,2 di atas.",
          "8. Persegi pembungkus Cap C (5,6 × 15,2 m) berada di dalam persegi Cap E (15,2 × 17,6 m) karena grid tiang 6.3 saling menyisip; bebannya dijumlahkan "
          "(superposisi), sehingga Cap C (tekanan 218 kPa pada luasnya) menjadi cap dengan penurunan terbesar (280 mm).\n",
          "## 9. Hal yang perlu diputuskan Defsa\n"]
    L += [f"{k + 1}. {x}" for k, x in enumerate(keputusan_defsa(h))]
    L += ["", "## 10. Sumber\n",
          "- NHI-06-089 Gb. 9-35/9-36 (hal. 9-85/9-86), Pers. 9-20 (PDF hal. 193); GEC10 11.4.2.1 hal. 11-9, 10.6.2 hal. 10-47/48; NHI-06-088 Tabel 5-16 hal. 5-85. "
          "Belum ada di acuan/: Fellenius (bidang netral terpadu), Fadum/Newmark (Boussinesq persegi panjang)."]
    Path(keluar).write_text("\n".join(L) + "\n", encoding="utf-8")
    return keluar


def perbarui_lembar(h):
    t = LEMBAR.read_text(encoding="utf-8")
    ganti = [
        ("OCR 3,8-4,0 (bilinear)", "OCR 2,41 (BH-4: σ'p bilinear 408,2 / σ'v0 169,5) dan 2,14 (BH-5: 424,4 / 198,3) (3,8 dan 4,0 yang tertulis sebelumnya adalah cv m²/th, salah baca kolom)"),
        ("Usulan cap tipikal lain: ____ (usulan AI", "Usulan cap tipikal lain: 3/C (usulan AI"),
        ("Es ____ (korelasi N60 ke Es dari NHI-06-088, tabel dicek saat hitung)", "Es 48 MPa, ν 0,30 (NHI-06-088 Tabel 5-16 hal. 5-85, pasir padat batas bawah 500 tsf) [Literatur, usulan AI]"),
        ("dianggap kaku ____ [Asumsi]", "dianggap kaku (usulan AI) [Asumsi]"),
        ("Muka air: ____ (usulan:", "Muka air: muka air tanah 2.3 yang dipakai 6.2 (usulan AI;"),
        ("| ____ | - | - |", f"| {idn(h['tz']['TENGAH']['s_np'], 1)} (fungsi 6.2 untuk TENGAH, usulan AI) | - | - |"),
        ("sampai δ ±____ mm)", f"sampai δ ±{idn(h['sloof']['delta_batas'], 0)} mm, usulan AI dari 6.6)"),
        ("Pilihan letak rakit ekuivalen: ____", "Pilihan letak rakit ekuivalen: (c) keduanya, ambil terbesar (usulan AI)"),
        ("tiang sendiri: ____ (setuju / tidak)", "tiang sendiri: setuju (usulan AI)"),
        ("- Interaksi: ____ (usulan AI:", "- Interaksi: (usulan AI:"),
        ("Bila > cadangan: ____", "Bila > cadangan: lihat `6.6 Penurunan Pondasi.md` bagian 9 (usulan AI)"),
        ("(Tahap 7): ____", "(Tahap 7): dicatat (usulan AI)"),
        ("ν ____)", "ν 0,30, usulan AI)"),
        ("| ____ (usulan 25 %", "| 25 % (usulan AI; 25 %"),
    ]
    for a, b in ganti:
        t = t.replace(a, b)
    baris = "Defsa meminta AI menghitung; hasilnya di `6.6 Penurunan Pondasi.md`."
    if baris not in t:
        t = t.rstrip("\n") + "\n\n" + baris + "\n"
    LEMBAR.write_text(t, encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from format_dokumen import hitung_ulang_excel
    h = semua()
    caps = h["caps"]
    for k, t in h["total"].items():
        print(k, "maks", round(float(t.max()), 1), caps[int(t.argmax())]["id"])
    gambar(h)
    gambar(h, GAMBAR / "6.6 Peta Penurunan (d).png", ("d", "bous"), "varian (d) kalibrasi uji beban (s NP + FJ s tunggal Rs + s global)")
    berkas, adr = buat_excel(h=h)
    print(berkas, hitung_ulang_excel(berkas))
    r = t104(berkas, adr, h)
    print(r)
    catat_t104(r, h)
    print(tulis_md(h=h, r=r))
    perbarui_lembar(h)


if __name__ == "__main__":
    main()
