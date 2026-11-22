"""Tahap 5 langkah 5.4: desain sloof (tie beam) 400 x 800 antar pile cap, sisi atas = sisi atas pelat LT1 (+12,85).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (21 Nov 2026); draf, menunggu persetujuan Defsa.
Kunci jawaban tidak dibuka. Beban pelat dari `tahap5_pelat_lt1` (5.3), dinding dari `tahap4_beban` (4.2), gaya kolom dasar dari
`tahap4_kolom` (4.7) dengan ukuran dan Pu kolom tangki opsi B dari `tahap5_tangki` (5.1), balok menerus PyNite dari `tahap4_balok`.

Acuan (halaman = nomor halaman PDF di acuan/privat, diverifikasi dengan pypdf):
- SNI 1726:2019 Pasal 7.13.7.2 (hal 104-105): pengikat fondasi KDS D-F, Ftie = 10 % SDS x Pu terbesar; Pasal 7.13.8.3.5 (hal 109):
  tambahan akibat serakan lateral; Tabel 22 (hal 107): batas beda penurunan, kategori risiko IV 0,002 L.
- SNI 2847:2019 Pasal 5.3.6 (hal 108): faktor T >= 1,0; Tabel 6.6.3.1.1(a) (hal 125): balok 0,35 Ig; Pasal 18.13.3.1-18.13.3.3 (hal 449):
  sloof menerus, dimensi >= ln/20, sengkang <= min(setengah dimensi, 300), memenuhi 18.6; Pasal 18.6.3.1 (hal 400) dan 18.6.3.2 (hal 401):
  tulangan memanjang rho <= 0,025, M+ >= 0,5 M-; 18.6.4.4 dan 18.6.4.6 (hal 402): sengkang; 18.6.5.1-18.6.5.2 (hal 403): Ve dari Mpr;
  18.8.5.1 (hal 418): ldh = fy db / (5,4 sqrt fc'); Tabel 25.4.2.2 (hal 588), Tabel 25.4.2.4 (hal 590): ld; Pasal 25.2.1 (hal 581):
  spasi bersih.
Pasal yang tidak ada di acuan ditulis persis "belum ada di acuan".
"""
from __future__ import annotations

import functools
import math
import os
import pickle
import sys
from pathlib import Path

import numpy as np
import openpyxl
from openpyxl.styles import PatternFill

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_balok as tbk  # noqa: E402
import tahap4_beban as tb  # noqa: E402
import tahap4_kolom as kl  # noqa: E402
import tahap5_mri as mri  # noqa: E402
import tahap5_pelat_lt1 as pl  # noqa: E402
import tahap5_telaah as ts  # noqa: E402
import tahap5_tangki as tn  # noqa: E402
from tahap5_mri import R, idn  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "05 Struktur Tengah"
BERKAS = KELUAR / "5.4 Desain Sloof.xlsx"
LABEL = mri.LABEL
STATUS = "disetujui Defsa 21 Nov 2026"
LABEL_AI = f"DIISI AI ATAS PERMINTAAN DEFSA (21 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."
KEPUTUSAN = ("21 Nov 2026: semua usulan AI disetujui. (1) **SL-1 (sloof dalam) 400 × 900**, 10 D29 atas / 8 D25 bawah (2 lapis, ρ 2,06 %); "
             "SL-2 (tepi) dan SL-3 (as 10, MRI) tetap 400 × 800 (6 D29 / 4 D29 dan 11 D22 / 5 D29). (2) **δ desain 16 mm** (0,002 L, SNI 1726:2019 Tabel 22) "
             "sampai penurunan tiang Tahap 6 ada. (3) **T tidak dimasukkan ke kombinasi gempa** (hanya 1,2D + 1,6L + 1,0T). (4) **Kepala tiang dianggap sendi** "
             "(momen dasar kolom gempa masuk ke sloof) sampai Tahap 6. Sloof baja karbon biasa (muka terdekat 1,8 m dari isocenter MRI). "
             "Ujung di inti diangkur ke pile cap inti (Tahap 6). Langkah berikutnya: 5.5 pit lift.")

FC, FY, FYT = pl.FC, pl.FY, 420.0
EC = 4700 * math.sqrt(FC)                  # MPa (Pasal 19.2.2.1)
PHI_M, PHI_V = 0.90, 0.75                  # Tabel 21.2.1
SDS = tb.SDS
EV = 0.2 * SDS
L = 8.0
SEL_BAWAH, SEL_ATAS, SEL_SAMPING = 0.050, 0.040, 0.050   # m, ke sengkang [Asumsi 5.4: bawah/samping 50 (tanah + asam), atas 40]
DB_POKOK = (25, 22, 29)
DS_PILIH = (13, 16)
S_MIN = 0.075                              # m, spasi sengkang praktis terkecil [Asumsi]
RHO_MAKS = 0.025                           # 18.6.3.1
UKURAN = [(0.40, 0.80), (0.40, 0.90), (0.50, 0.80), (0.50, 0.90)]
H_PELAT = pl.H
HK = 0.75                                  # m, lebar kolom podium (opsi B: semua kolom tangki 0,75)
SEL_KOL = 0.053                            # m, selimut kolom 40 + sengkang D13 [Asumsi, 4.7]
D_PL = tb.GAMMA_C * pl.H + pl.SIDL_LT1     # kPa, 8,00 (5.3)
LO_PL = pl.LO_PL1                          # 4,79
D_MRI = D_PL + pl.Q_RF                     # 8,655 (5.3)
LO_MRI = pl.LO_PL2                         # 2,87
QU_PL = 1.2 * D_PL + 1.6 * LO_PL           # 17,264
Q_DL = ((1 - tb.BUKAAN) * tb.DINDING_LUAR["bata"][0] + tb.BUKAAN * tb.DINDING_LUAR["kaca"][0] + tb.DINDING_LUAR["fasad"][0])
H_DINDING = 4.2                            # m, tinggi dinding luar setara 4.6 `beban_balok` [Asumsi]
W_FASAD = Q_DL * H_DINDING                 # kN/m'
W_R09 = 0.45 * 4.5                         # kN/m', 0,45 kN/m2 x 4,5 m [Alat Medis R-09; tinggi = tinggi tingkat]
M_ISO = (80.5, 57.0)
P_MAGNET = 48.1                            # kN, dibagi 4 tepi panel [Asumsi]
DELTA_16, DELTA_8 = 0.002 * L, 0.001 * L   # m
IE_FAKTOR = 0.35                           # Tabel 6.6.3.1.1(a)
K_ROT = tn.k_pegas(HK)                     # kNm/rad, pegas putar ujung garis = kolom 750 di atas sloof (4 Ec 0,70 Ig / 4,5 m, seperti 5.1)
TOL = {"a": 0.5, "b": 5.0, "c": 1.0, "d": 2.0}   # % (T-93), ditetapkan sebelum membandingkan
TIPE = ("SL-1", "SL-2", "SL-3")
NAMA_TIPE = {"SL-1": "sloof dalam (pelat dua sisi)", "SL-2": "sloof tepi (pelat satu sisi + dinding fasad)",
             "SL-3": "sloof as 10 di panel MRI (pelat satu sisi + fasad + pelindung)"}


def luas(db):
    return math.pi * db ** 2 / 4


def floor25(s):
    return math.floor(s / 0.025 + 1e-9) * 0.025


# ------------------------------------------------------------------ data kolom (4.7, opsi B 5.1)
@functools.lru_cache(maxsize=1)
def data_kolom():
    """Per kolom dasar LT1 (kunci ('LT2', x, y)): F (n, 5) = [P, Mx, My, Vx, Vy] ujung bawah semua kombinasi (K1 U K2), penanda
    gempa, ukuran b, kelompok, reaksi dasar R_D dan R_L. Kolom tangki memakai Pu dan ukuran opsi B (5.1)."""
    cache = os.environ.get("SLOOF_CACHE")   # shortcut: hanya untuk pengembangan, hasil analisis OpenSees 100 detik
    if cache and Path(cache).exists():
        return pickle.load(open(cache, "rb"))
    d = tn.hasil_46_47()
    hs = [kl.analisis("K2", d["um"]), kl.analisis("K1", d["um"])]
    gk = kl.gaya_kolom(hs)
    out = {}
    for k, v in gk.items():
        if k[0] != "LT2":
            continue
        rd = max(float(kl.ujung(h["gaya"]["D"][k])[0][0]) for h in hs)
        rl = max(float(kl.ujung(h["gaya"]["L"][k])[0][0]) for h in hs)
        out[k] = {"F": v["F"][:, 0, :], "gempa": v["gempa"], "b": float(v["b"]), "kel": v["kelompok"], "R_D": rd, "R_L": rl}
    kb = tn.hitung()["kolom_b"]
    for (x, y), v in kb.items():
        e = out[("LT2", x, y)]
        e["b_A"], e["Pu_A"], e["b"], e["Pu_B"] = e["b"], v["Pu_A"], v["b_B"], v["Pu_B"]
        e["kel"] = "K-T B LT2"
    if cache:
        pickle.dump(out, open(cache, "wb"))
    return out


def pu_gravitasi(e):
    """Pu = maks (1,4 D; 1,2 D + 1,6 L) di dasar kolom (kombinasi non-gempa); kolom tangki: Pu opsi B (5.1)."""
    if "Pu_B" in e:
        return float(e["Pu_B"])
    return float(e["F"][~e["gempa"], 0].max())


def gaya_ikat(dk=None):
    """Ftie = 0,10 SDS Pu (SNI 1726:2019 7.13.7.2) per kelompok kolom; Pu = yang lebih besar dari kolom di kedua ujung sloof."""
    dk = dk or data_kolom()
    kel = {}
    for k, e in dk.items():
        kel.setdefault(e["kel"].replace(" LT2", ""), []).append(k)
    baris = []
    for nama, ks in kel.items():
        pu = max(pu_gravitasi(dk[k]) for k in ks)
        kunci = max(ks, key=lambda k: pu_gravitasi(dk[k]))
        baris.append({"kel": nama, "n": len(ks), "b": dk[kunci]["b"], "pu": pu, "kunci": (kunci[1], kunci[2]), "ftie": 0.10 * SDS * pu})
    # segmen sloof: Pu = yang lebih besar dari dua kolom di ujung
    seg = []
    for (lv, x, y), e in dk.items():
        for (x2, y2) in ((x + L, y), (x, y + L)):
            e2 = dk.get(("LT2", x2, y2))
            if e2:
                seg.append(0.10 * SDS * max(pu_gravitasi(e), pu_gravitasi(e2)))
    return {"kelompok": sorted(baris, key=lambda b: -b["ftie"]), "ftie_maks": max(seg), "n_segmen": len(seg),
            "pu_maks": max(b["pu"] for b in baris)}


# ------------------------------------------------------------------ momen kolom (kepala tiang sendi)
def bagi(m, posisi, tepi):
    return m if posisi in tepi else m / 2


def momen_kolom(dk=None):
    """Momen dasar kolom gempa maksimum per kelompok (Mx: sloof arah Y, My: sloof arah X) dan bagian yang diterima sloof:
    kolom dalam di arah itu M/2 per sloof, kolom tepi M. Per tipe sloof: maksimum bagian di kolom pada garisnya."""
    dk = dk or data_kolom()
    per_kolom = {}
    for k, e in dk.items():
        f = e["F"][e["gempa"]]
        per_kolom[(k[1], k[2])] = {"Mx": float(np.abs(f[:, 1]).max()), "My": float(np.abs(f[:, 2]).max()), "kel": e["kel"].replace(" LT2", "")}
    kel = {}
    for xy, v in per_kolom.items():
        kel.setdefault(v["kel"], []).append((xy, v))
    baris = []
    for nama, lst in kel.items():
        mx = max(v["Mx"] for _, v in lst)
        my = max(v["My"] for _, v in lst)
        baris.append({"kel": nama, "n": len(lst), "Mx": mx, "My": my, "M_dalam": max(mx, my) / 2, "M_tepi": max(mx, my)})

    def bagian(xy, arah):
        x, y = xy
        v = per_kolom[xy]
        if arah == "X":     # sloof sepanjang X (garis y tetap): momen My, kolom tepi bila x = 12 atau 84
            return bagi(v["My"], x, (12.0, 84.0))
        return bagi(v["Mx"], y, (27.0, 75.0))
    xs, ys = sorted({k[0] for k in per_kolom}), sorted({k[1] for k in per_kolom})
    tipe = {"SL-1": [], "SL-2": [], "SL-3": []}
    for y in ys:
        for x in xs:
            if 27.0 < y < 75.0:
                tipe["SL-1"].append((bagian((x, y), "X"), (x, y), "X"))
            if y in (27.0, 75.0):
                tipe["SL-2"].append((bagian((x, y), "X"), (x, y), "X"))
    for x in xs:
        for y in ys:
            if 12.0 < x < 84.0:
                tipe["SL-1"].append((bagian((x, y), "Y"), (x, y), "Y"))
            if x == 12.0:
                tipe["SL-2"].append((bagian((x, y), "Y"), (x, y), "Y"))
            if x == 84.0:
                tipe["SL-3"].append((bagian((x, y), "Y"), (x, y), "Y"))
    me = {t: max(v) for t, v in tipe.items()}
    return {"kelompok": sorted(baris, key=lambda b: -b["M_tepi"]), "per_kolom": per_kolom, "me": {t: v[0] for t, v in me.items()},
            "me_ket": {t: v[1:] for t, v in me.items()}, "M_maks": max(max(v["Mx"], v["My"]) for v in per_kolom.values())}


# ------------------------------------------------------------------ penampang
def as_min(b, d):
    """Pasal 9.6.1.2: max(0,25 sqrt fc' / fy; 1,4 / fy) b d (mm2)."""
    return max(0.25 * math.sqrt(FC) / FY, 1.4 / FY) * b * d * 1e6


def susun(n, db, b, ds, sel_tepi):
    """(batang per lapis, lapis, jarak titik berat dari serat tepi m); spasi bersih >= max(25, db) (25.2.1, hal 581)."""
    sb = max(25.0, db)
    lebar = b * 1000 - 2 * SEL_SAMPING * 1000 - 2 * ds
    n1 = max(2, int((lebar + sb) // (db + sb)))
    lapis = math.ceil(n / n1)
    y1 = sel_tepi * 1000 + ds + db / 2
    ys, sisa = [], n
    for k in range(lapis):
        m = min(n1, sisa)
        ys += [y1 + k * (db + sb)] * m
        sisa -= m
    return n1, lapis, sum(ys) / n / 1000


def tul(mu, b, h, ds, sel_tepi, as_lain=0.0, tambah=0.0):
    """Pilih D dan jumlah batang: lapis paling sedikit lalu As terkecil; As >= maks(As(Mu), As min, as_lain) + tambah (gaya tarik ikat)."""
    pilihan = []
    for db in DB_POKOK:
        n = 2
        perlu = 0.0
        while n <= 40:
            n1, lapis, yc = susun(n, db, b, ds, sel_tepi)
            d = h - yc
            perlu = max(tbk.as_perlu(mu, b, d, fc=FC), as_min(b, d), as_lain) + tambah
            if n * luas(db) >= perlu:
                break
            n += 1
        pilihan.append({"db": db, "n": n, "n1": min(n1, n), "lapis": lapis, "d": d, "As": n * luas(db), "As_perlu": perlu,
                        "rho": n * luas(db) / (b * d * 1e6), "yc": yc, "ok": math.isfinite(perlu) and n <= 40})
    ok = [p for p in pilihan if p["ok"]] or pilihan
    return min(ok, key=lambda p: (p["lapis"], p["As"]))


def phimn(t, b, fc=FC):
    return PHI_M * tbk.mn(t["As"], b, t["d"], fc=fc)


def mpr(t, b):
    return tbk.mn(t["As"], b, t["d"], fc=FC, fy=1.25 * FY)


# ------------------------------------------------------------------ gravitasi: PyNite
def beban_garis(tipe, b, h):
    """(bentang, beban_q, beban_p) untuk balok_menerus: kasus D (tetap), L1 (bentang ke-1,3,5), L2 (bentang ke-2,4,6).
    Beban segitiga pelat dari 16 titik per bentang (kl.BOBOT_SEGITIGA, kN per kPa)."""
    n = 6 if tipe == "SL-3" else 5
    ws = tb.GAMMA_C * b * (h - H_PELAT)
    sisi = 2 if tipe == "SL-1" else 1
    q, p = [], []
    for i in range(n):
        x0 = L * i
        q.append(("D", ws + (W_R09 if tipe == "SL-1" else W_FASAD), x0, x0 + L))
        dpl, lpl = (D_MRI, LO_MRI) if (tipe == "SL-3" and i == 3) else (D_PL, LO_PL)
        kasus_l = "L1" if i % 2 == 0 else "L2"
        for xj, bw in zip(kl.TITIK_SEGITIGA, kl.BOBOT_SEGITIGA):
            p.append(("D", sisi * dpl * float(bw), x0 + float(xj)))
            p.append((kasus_l, sisi * lpl * float(bw), x0 + float(xj)))
    if tipe == "SL-3":      # pelindung MRI y 54-59 (bentang D-E) dan y 59-60 (E-F); magnet 48,1 kN dibagi 4 tepi di tengah D-E
        q.append(("D", pl_w(), 27.0, 33.0))
        p.append(("D", P_MAGNET / 4, 28.0))
    return [L] * n, q, p


def pl_w():
    """Pelindung MRI R-04, kN/m' (7,17), data owner via 5.2/5.3."""
    mi = mri.baca_masukan()
    return mi["berat_pelindung"] / sum(mi["dinding"])


@functools.lru_cache(maxsize=None)
def gaya_garis(tipe, b, h):
    """Selubung gravitasi satu garis as (PyNite): kombinasi 1,4D; 1,2D + 1,6L (pola 3 kasus); (1,2 + 0,2 SDS) D + L; (0,9 - 0,2 SDS) D."""
    bt, q, p = beban_garis(tipe, b, h)
    res = tbk.balok_menerus(bt, q, p, b, h, k_rot=K_ROT)
    M, V = res["M"], res["V"]

    def c(fd, f1, f2, a=M):
        return fd * a["D"] + f1 * a["L1"] + f2 * a["L2"]
    g12 = [c(1.2, 1.6 * a, 1.6 * z) for a, z in ((1, 0), (0, 1), (1, 1))]
    v12 = [c(1.2, 1.6 * a, 1.6 * z, V) for a, z in ((1, 0), (0, 1), (1, 1))]
    g14 = c(1.4, 0, 0)
    sg, sv = c(1.2 + EV, 1, 1), c(1.2 + EV, 1, 1, V)
    su = c(0.9 - EV, 0, 0)
    d12 = c(1.2, 0, 0)

    def neg(a):
        return float(-np.min(a))

    def pos(a):
        return float(np.max(a))
    return {"neg_g12": max(neg(a) for a in g12), "neg_g": max(neg(a) for a in g12 + [g14]), "pos_g": max(pos(a) for a in g12 + [g14]),
            "v_g": max(float(np.abs(a).max()) for a in v12 + [c(1.4, 0, 0, V)]), "neg_s": neg(sg), "pos_s": pos(sg),
            "v_s": float(np.abs(sv).max()), "neg_d09": neg(su), "neg_d12": neg(d12), "reaksi": res["R"], "x": res["x"], "M": M, "V": V,
            "w_diri": tb.GAMMA_C * b * (h - H_PELAT)}


# ------------------------------------------------------------------ penurunan beda
def momen_penurunan(b, h, delta, ie=IE_FAKTOR, bentang=L):
    """M = 6 Ec Ie delta / L2 (kNm), ujung jepit-jepit, tumpuan turun delta; V = 2M/L."""
    return 6 * EC * 1000 * ie * (b * h ** 3 / 12) * delta / bentang ** 2


# ------------------------------------------------------------------ desain satu tipe dan ukuran
def desain(tipe, b, h, delta=DELTA_16, t_gempa=False, ie=IE_FAKTOR, dk=None, me_faktor=1.0):
    """Desain lentur, geser (18.6.5), dan detail sloof. t_gempa: T ikut di kombinasi gempa (varian). me_faktor 0: kepala tiang dianggap
    jepit (momen kolom tidak masuk ke sloof, varian pembanding)."""
    dk = dk or data_kolom()
    g = gaya_garis(tipe, b, h)
    me = momen_kolom(dk)["me"][tipe] * me_faktor
    ftie = gaya_ikat(dk)["ftie_maks"]
    t = momen_penurunan(b, h, delta, ie)
    ln = L - HK
    kasus = {
        "G": {"neg": g["neg_g"], "pos": g["pos_g"], "vu": g["v_g"], "seis": False, "tie": 0.0},
        "G+T": {"neg": g["neg_g12"] + t, "pos": max(g["pos_g"], t - g["neg_d12"]), "vu": g["v_g"] + 2 * t / L, "seis": False, "tie": 0.0},
        "E": {"neg": g["neg_s"] + me, "pos": max(g["pos_s"], me - g["neg_d09"]), "vu": g["v_s"], "seis": True, "tie": ftie},
    }
    if t_gempa:
        kasus["E+T"] = {"neg": g["neg_s"] + me + t, "pos": max(g["pos_s"], me + t - g["neg_d09"]), "vu": g["v_s"] + 2 * t / L, "seis": True,
                        "tie": ftie}
    for ds in DS_PILIH:
        atas = bawah = None
        for k, c in kasus.items():
            a_ = tul(c["neg"], b, h, ds, SEL_ATAS, tambah=c["tie"] / (PHI_M * FY / 1000))
            atas = a_ if atas is None or a_["As"] > atas["As"] else atas
        for k, c in kasus.items():
            b_ = tul(c["pos"], b, h, ds, SEL_BAWAH, as_lain=0.5 * atas["As"], tambah=c["tie"] / (PHI_M * FY / 1000))
            bawah = b_ if bawah is None or b_["As"] > bawah["As"] else bawah
        d = min(atas["d"], bawah["d"])
        mpr_n, mpr_p = mpr(atas, b), mpr(bawah, b)
        ve_e = (mpr_n + mpr_p) / ln
        vg = g["v_s"]
        ve = ve_e + vg
        ag = b * h * 1e6
        vc_n = 0.17 * math.sqrt(FC) * b * d * 1000
        vc = 0.0 if (ve_e >= 0.5 * ve and ftie < ag * FC / 20 / 1000) else vc_n         # 18.6.5.2 (hal 403)
        vu = max(ve, kasus["G"]["vu"], kasus["G+T"]["vu"])
        avs = max(vu / PHI_V - vc, 0.0) / (FYT * 1000 * d)
        avs_min = max(0.062 * math.sqrt(FC), 0.35) * b / FYT
        kaki = tbk.kaki_sengkang(max(atas["n1"], bawah["n1"]))
        a1 = luas(ds) * 1e-6
        db_min = min(atas["db"], bawah["db"]) / 1000
        s_perlu = kaki * a1 / max(avs, avs_min)
        s_ujung = floor25(min(s_perlu, d / 4, 6 * db_min, 0.150, b / 2, 0.300))      # 18.6.4.4 dan 18.13.3.2
        s_tengah = floor25(min(kaki * a1 / max(max(vu / PHI_V - vc_n, 0.0) / (FYT * 1000 * d), avs_min), d / 2, b / 2, 0.300))   # 18.6.4.6
        if s_ujung >= S_MIN - 1e-9:
            break
    ok_v = vu <= PHI_V * (vc_n + 0.66 * math.sqrt(FC) * b * d * 1000)                  # 22.5.1.2
    hasil = {}
    for k, c in kasus.items():
        hasil[k] = {**c, "r_neg": c["neg"] / phimn(atas, b), "r_pos": c["pos"] / phimn(bawah, b)}
    cek = {"rho": max(atas["rho"], bawah["rho"]) <= RHO_MAKS, "lapis": max(atas["lapis"], bawah["lapis"]) <= 2,
           "lentur": all(max(v["r_neg"], v["r_pos"]) <= 1.0 + 1e-9 for v in hasil.values()),
           "m_pos": bawah["As"] >= 0.5 * atas["As"] - 1e-9, "geser": ok_v, "sengkang": s_ujung >= S_MIN - 1e-9,
           "ln4d": ln >= 4 * d, "lebar": b >= max(0.3 * h, 0.25), "ln20": b >= min(ln / 20, 0.450)}
    return {"tipe": tipe, "b": b, "h": h, "d": d, "ln": ln, "atas": atas, "bawah": bawah, "ds": ds, "kaki": kaki, "T": t, "ME": me,
            "ftie": ftie, "g": g, "kasus": hasil, "phiMn_neg": phimn(atas, b), "phiMn_pos": phimn(bawah, b), "Mpr_neg": mpr_n,
            "Mpr_pos": mpr_p, "Ve_e": ve_e, "Vg": vg, "Ve": ve, "Vc": vc, "Vu": vu, "s_ujung": s_ujung, "s_tengah": s_tengah,
            "l_ujung": 2 * h, "cek": cek, "ok": all(cek.values()), "delta": delta, "t_gempa": t_gempa,
            "phiPn_tekan": 0.65 * 0.80 * (0.85 * FC * (b * h * 1e6 - (atas["As"] + bawah["As"])) + FY * (atas["As"] + bawah["As"])) / 1000}


# ------------------------------------------------------------------ ujung sloof
def ldh(db, fc=FC):
    """Pers. 18.8.5.1 (hal 418): fy db / (5,4 sqrt fc'), tidak kurang dari maks(8 db; 150 mm)."""
    return max(FY * db / (5.4 * math.sqrt(fc)), 8 * db, 150.0)


def ld_lurus(db, atas, koef=1.7, fc=FC):
    """Tabel 25.4.2.2 (hal 588): fy psi_t psi_e db / (koef lambda sqrt fc'); psi_t 1,3 batang atas (Tabel 25.4.2.4, hal 590)."""
    psi_t = 1.3 if atas else 1.0
    return FY * psi_t * db / (koef * math.sqrt(fc))


def ujung_tabel(db):
    """(jenis ujung, panjang perlu mm, tersedia mm, catatan)."""
    out = []
    for b in (0.75, 0.80, 0.95):
        out.append({"jenis": f"kolom tepi {int(b * 1000)}, kait 90° ke dalam kolom", "perlu": ldh(db), "ada": (b - SEL_KOL) * 1000, "pasal": "18.8.5.1"})
    out.append({"jenis": "kolom dalam: menerus melewati kolom", "perlu": 0.0, "ada": 0.0, "pasal": "18.13.3.1"})
    out.append({"jenis": "sambungan lewatan di tengah bentang (kelas B 1,3 ld, batang atas)", "perlu": 1.3 * ld_lurus(db, True), "ada": L * 1000 - 2 * 2 * 800, "pasal": "25.5.2.1"})
    out.append({"jenis": "inti: kait 90° ke dinding inti 350", "perlu": ldh(db), "ada": (tb.DINDING_T - SEL_KOL) * 1000, "pasal": "18.8.5.1"})
    out.append({"jenis": "inti: lurus bawah (koef 1,7)", "perlu": ld_lurus(db, False), "ada": (tb.DINDING_T - SEL_KOL) * 1000, "pasal": "25.4.2.2"})
    out.append({"jenis": "inti: lurus atas (koef 1,7; psi_t 1,3)", "perlu": ld_lurus(db, True), "ada": (tb.DINDING_T - SEL_KOL) * 1000, "pasal": "25.4.2.2"})
    return out


# ------------------------------------------------------------------ jarak ke isocenter MRI
def jarak_mri():
    """Jarak horizontal muka sloof terdekat ke isocenter (80,5; 57,0); sloof 400 mm. Sloof di bawah pelat: jarak 3D lebih besar."""
    b2 = 0.4 / 2
    kotak = {"as 9 (x 76)": (76 - b2, 76 + b2, 51.0, 59.0), "as 10 (x 84)": (84 - b2, 84 + b2, 51.0, 59.0),
             "as E (y 59)": (76.0, 84.0, 59 - b2, 59 + b2), "as D (y 51)": (76.0, 84.0, 51 - b2, 51 + b2)}
    return [{"nama": k, "kotak": v, "jarak": ts.jarak_titik_ke_kotak(M_ISO[0], M_ISO[1], *v)} for k, v in kotak.items()]


# ------------------------------------------------------------------ cek silang T-93
def cp_phimn(des):
    """phi Mn dengan concreteproperties (b x h, selimut atas 40 / bawah 50 mm). 'neg' dan 'pos': hanya tulangan tarik (sepadan dengan
    rumus sendiri tanpa tulangan tekan); 'neg_penuh' dan 'pos_penuh': kedua lapis ikut (tulangan tekan); 'neg_tarik': penuh dengan
    tarik ikat Ftie bersamaan."""
    from concreteproperties.concrete_section import ConcreteSection
    from concreteproperties.material import Concrete, SteelBar
    from concreteproperties.stress_strain_profile import ConcreteLinearNoTension, RectangularStressBlock, SteelElasticPlastic
    from sectionproperties.pre.library.concrete_sections import add_bar
    from sectionproperties.pre.library.primitive_sections import rectangular_section

    beta1 = 0.85 - 0.05 * (FC - 28) / 7
    beton = Concrete("fc35", 2.4e-6, ConcreteLinearNoTension(elastic_modulus=EC, ultimate_strain=0.003, compressive_strength=FC), "lightgrey",
                     RectangularStressBlock(compressive_strength=FC, alpha=0.85, gamma=beta1, ultimate_strain=0.003),
                     flexural_tensile_strength=0.62 * math.sqrt(FC))
    baja = SteelBar("BjTS420", 7.85e-6, SteelElasticPlastic(yield_strength=FY, elastic_modulus=200e3, fracture_strain=0.05), "grey")
    b, h, ds = des["b"] * 1000, des["h"] * 1000, des["ds"]

    def bangun(pakai_atas, pakai_bawah):
        geom = rectangular_section(d=h, b=b, material=beton)
        for t, atas, pakai in ((des["atas"], True, pakai_atas), (des["bawah"], False, pakai_bawah)):
            if not pakai:
                continue
            db, n, n1 = t["db"], t["n"], t["n1"]
            sb = max(25.0, db)
            sisa, k = n, 0
            sel = SEL_ATAS if atas else SEL_BAWAH
            while sisa > 0:
                m = min(n1, sisa)
                y = sel * 1000 + ds + db / 2 + k * (db + sb)
                y = h - y if atas else y
                x0 = SEL_SAMPING * 1000 + ds + db / 2
                x1 = b - x0
                for j in range(m):
                    geom = add_bar(geom, luas(db), baja, x0 + (x1 - x0) * (j / (m - 1) if m > 1 else 0.5), y, 16)
                sisa -= m
                k += 1
        return ConcreteSection(geom)

    def kap(sec, theta, n=0.0):
        return PHI_M * abs(sec.ultimate_bending_capacity(theta=theta, n=n).m_xy) / 1e6
    s_atas, s_bawah, s_penuh = bangun(True, False), bangun(False, True), bangun(True, True)
    return {"neg": kap(s_atas, math.pi), "pos": kap(s_bawah, 0.0), "neg_penuh": kap(s_penuh, math.pi), "pos_penuh": kap(s_penuh, 0.0),
            "neg_tarik": kap(s_penuh, math.pi, -des["ftie"] * 1e3)}


def pynite_penurunan(b, h, delta, ie=IE_FAKTOR):
    """Momen ujung PyNite: balok satu bentang jepit-jepit, tumpuan kanan turun delta, I = ie Ig (arah lentur kuat)."""
    from Pynite import FEModel3D
    e = EC * 1000
    m = FEModel3D()
    m.add_material("c", e, e / 2.4, 0.2, 24.0)
    m.add_section("s", b * h, h * b ** 3 / 12, ie * b * h ** 3 / 12, 1e-3)
    m.add_node("A", 0, 0, 0)
    m.add_node("B", L, 0, 0)
    m.add_member("M", "A", "B", "c", "s")
    for n in ("A", "B"):
        m.def_support(n, True, True, True, True, True, True)
    m.def_node_disp("B", "DY", -delta)
    m.analyze_linear(check_statics=False)
    return abs(float(m.members["M"].moment("Mz", 0, "Combo 1")))


def cek_t93(dk=None):
    dk = dk or data_kolom()
    gi = gaya_ikat(dk)
    top = gi["kelompok"][0]
    kunci = ("LT2",) + top["kunci"]
    e = dk[kunci]
    pu_tangan = max(1.4 * e["R_D"], 1.2 * e["R_D"] + 1.6 * e["R_L"]) if "Pu_B" not in e else e["Pu_B"]
    a = {"tangan": 0.10 * SDS * pu_tangan, "skrip": top["ftie"], "kolom": top["kunci"], "pu": pu_tangan, "tangki_b": "Pu_B" in e}
    # (b) satu bentang jepit-jepit, SL-1 400 x 800: PyNite (pegas putar sangat kaku) vs 5 w L2/96 + w L2/12 (kasus D)
    b_, h_ = 0.40, 0.80
    ws = tb.GAMMA_C * b_ * (h_ - H_PELAT) + W_R09
    wp = 2 * D_PL * L / 2        # puncak segitiga dua sisi, kN/m
    m_tangan = ws * L ** 2 / 12 + 5 * wp * L ** 2 / 96
    q = [("D", ws, 0.0, L)]
    p = [("D", 2 * D_PL * float(bw), float(xj)) for xj, bw in zip(kl.TITIK_SEGITIGA, kl.BOBOT_SEGITIGA)]
    r1 = tbk.balok_menerus([L], q, p, b_, h_, k_rot=1e10)
    j = int(np.argmin(np.abs(r1["x"] - L)))
    m_py = abs(float(r1["M"]["D"][j]))
    bb = {"tangan": m_tangan, "pynite": m_py}
    # (c) momen penurunan
    cc = {"tangan": momen_penurunan(0.40, 0.80, DELTA_16), "pynite": pynite_penurunan(0.40, 0.80, DELTA_16)}
    # (d) phi Mn penampang terpilih
    des = desain("SL-2", 0.40, 0.80, dk=dk)
    cp = cp_phimn(des)
    dd = {"sendiri_neg": des["phiMn_neg"], "cp_neg": float(cp["neg"]), "sendiri_pos": des["phiMn_pos"], "cp_pos": float(cp["pos"]),
          "cp_neg_penuh": float(cp["neg_penuh"]), "cp_pos_penuh": float(cp["pos_penuh"]), "cp_tarik": float(cp["neg_tarik"]), "des": des}
    return {"a": a, "b": bb, "c": cc, "d": dd}


# ------------------------------------------------------------------ hitung
@functools.lru_cache(maxsize=1)
def hitung():
    dk = data_kolom()
    r = {"gi": gaya_ikat(dk), "mk": momen_kolom(dk), "mri": jarak_mri()}
    r["desain"] = {(t, b, h): desain(t, b, h, dk=dk) for t in TIPE for (b, h) in UKURAN}
    r["sensitivitas"] = {}
    for (b, h) in UKURAN:
        for dl in (DELTA_16, DELTA_8):
            for tg in (False, True):
                r["sensitivitas"][(b, h, dl, tg)] = {t: desain(t, b, h, delta=dl, t_gempa=tg, dk=dk) for t in TIPE}
    r["jepit"] = {(t, b, h): desain(t, b, h, dk=dk, me_faktor=0.0) for t in TIPE for (b, h) in UKURAN}
    r["t93"] = cek_t93(dk)
    r["pu_maks"] = r["gi"]["pu_maks"]
    return r




# ------------------------------------------------------------------ teks pembantu
NAMA_CEK = {"rho": "ρ > 0,025 (18.6.3.1)", "lapis": "lebih dari 2 lapis", "lentur": "φMn kurang", "m_pos": "M+ < 0,5 M- (18.6.3.2)",
            "geser": "geser melebihi batas (22.5.1.2)", "sengkang": "spasi sengkang < 75 mm", "ln4d": "ln < 4d (18.6.2.1)",
            "lebar": "b < 0,3h (18.6.2.1)", "ln20": "b < ln/20 (18.13.3.2)"}
KOMBINASI = {"G": "1,4 D; 1,2 D + 1,6 L (pola)", "G+T": "1,2 D + 1,6 L + 1,0 T", "E": "(1,2 + 0,2 SDS) D + L + E kolom",
             "E+T": "(1,2 + 0,2 SDS) D + L + E kolom + 1,0 T"}


def pct(v, d=2):
    return idn(v * 100, d)


def tul_s(t):
    return f"{t['n']} D{t['db']}"


def status_s(d):
    if d["ok"]:
        return "memenuhi"
    return "tidak memenuhi: " + "; ".join(NAMA_CEK[k] for k, v in d["cek"].items() if not v)


def sengkang_s(d):
    return (f"D{d['ds']}-{idn(d['s_ujung'] * 1000, 0)} sepanjang 2h = {idn(d['l_ujung'] * 1000, 0)} mm dari muka kolom; "
            f"D{d['ds']}-{idn(d['s_tengah'] * 1000, 0)} di tengah; {d['kaki']} kaki")


def maks_kasus(d, kunci):
    return max(v[kunci] for v in d["kasus"].values())


def rasio_s(d):
    return idn(max(max(v["r_neg"], v["r_pos"]) for v in d["kasus"].values()), 3)


def d_(r, tipe, b=0.40, h=0.80):
    return r["desain"][(tipe, b, h)]


# ------------------------------------------------------------------ lembar Excel: baris R
def baris_ikat(r):
    gi = r["gi"]
    top = gi["kelompok"][0]
    x, y = top["kunci"]
    a = [
        R("sds", "SDS (spektrum 4.1 opsi a)", SDS, "", "", "tahap4_beban.SDS (4.1)", "0.000"),
        R("kf", "Koefisien gaya ikat", 0.10, "", "10 % SDS dikali Pu", "SNI 1726:2019 Pasal 7.13.7.2 (hal PDF 104-105); KDS D, kelas situs SF", "0.00"),
        R("pu", f"Pu terbesar di dasar kolom (kolom x {idn(x, 0)}, y {idn(y, 0)})", top["pu"], "kN",
          "maks (1,4 D; 1,2 D + 1,6 L), selubung K1 dan K2", "4.7 (tahap4_kolom, OpenSees)", "#,##0.0"),
        R("ftie", "Ftie = 0,10 SDS Pu", "={kf}*{sds}*{pu}", "kN", "kuat tarik dan tekan desain pengikat; Pu = yang lebih besar dari kolom di kedua ujung",
          "SNI 1726:2019 Pasal 7.13.7.2", "0.00", gi["ftie_maks"]),
    ]
    return [("A", "Gaya ikat antar pile cap", a)]


def baris_beban(r):
    a = [
        R("gc", "Berat jenis beton bertulang", tb.GAMMA_C, "kN/m³", "", "SNI 1727:2020 Tabel C3.1-2 (4.2)", "0.0"),
        R("bsl", "Lebar sloof konsep", 0.40, "m", "", "konsep 3.9, 5.3", "0.00"),
        R("hsl", "Tinggi sloof konsep", 0.80, "m", "sisi atas = sisi atas pelat LT1 +12,85", "konsep 3.9, 5.3", "0.00"),
        R("hpl", "Tebal pelat LT1", H_PELAT * 1000, "mm", "", "5.3", "0"),
        R("ws", "Berat sendiri sloof di bawah pelat", "={gc}*{bsl}*({hsl}-{hpl}/1000)", "kN/m'", "b (h - tebal pelat) gc", "", "0.000",
          tb.GAMMA_C * 0.40 * (0.80 - H_PELAT)),
        R("kera", "Keramik + spesi", tb.SIDL["keramik"][0], "kPa", "", "SNI 1727:2020 Tabel C3.1-1 (5.3)", "0.00"),
        R("part", "Partisi", tb.SIDL["partisi"][0], "kPa", "tanpa plafon dan gantung", "[Asumsi 4.2], 5.3", "0.00"),
        R("dpl", "D pelat PL-1 (berat sendiri + keramik + partisi)", "={gc}*{hpl}/1000+{kera}+{part}", "kPa", "", "5.3", "0.000", D_PL),
        R("lo", "Beban hidup PL-1", LO_PL, "kPa", "lobi dan koridor lantai pertama", "SNI 1727:2020 Tabel 4.3-1 (hal PDF 52), 5.3", "0.00"),
        R("qu", "qu pelat PL-1 = 1,2 D + 1,6 L", "=1.2*{dpl}+1.6*{lo}", "kPa", "puncak segitiga ke sloof = qu L/2 per sisi", "5.3", "0.000", QU_PL),
        R("qrf", "Sangkar RF merata (27,5 kN / 42 m²)", "=27.5/42", "kPa", "", "[Alat Medis R-05], 5.3", "0.000", pl.Q_RF),
        R("dmri", "D panel MRI 9-10/D-E", "={dpl}+{qrf}", "kPa", "", "5.3", "0.000", D_MRI),
        R("lo2", "Beban hidup panel MRI", LO_MRI, "kPa", "", "SNI 1727:2020 Tabel 4.3-1 (hal PDF 52), 5.3", "0.00"),
        R("bata", "Dinding bata 150 mm + plester", tb.DINDING_LUAR["bata"][0], "kPa", "", "4.2 (tahap4_beban.DINDING_LUAR)", "0.00"),
        R("kaca", "Jendela kaca dan kusen", tb.DINDING_LUAR["kaca"][0], "kPa", "", "4.2", "0.00"),
        R("fas", "Lapis fasad", tb.DINDING_LUAR["fasad"][0], "kPa", "", "4.2 [Asumsi; dirinci di 4.9]", "0.00"),
        R("bk", "Porsi bukaan fasad", tb.BUKAAN, "", "", "4.2 (V4, 3.11)", "0.00"),
        R("qdl", "Beban dinding luar per m² bidang", "=(1-{bk})*{bata}+{bk}*{kaca}+{fas}", "kPa", "", "4.2", "0.000", Q_DL),
        R("hd", "Tinggi dinding luar di atas sloof", H_DINDING, "m", "sama dengan 4.6 (`beban_balok`)", "[Asumsi 5.4]", "0.0"),
        R("wf", "Beban dinding fasad pada sloof tepi", "={qdl}*{hd}", "kN/m'", "", "4.6 (tahap4_balok.beban_balok)", "0.000", W_FASAD),
        R("qr09", "Dinding timbal R-09 (2 mm Pb + plester barit)", 0.45, "kN/m²", "", "[Alat Medis R-09]", "0.00"),
        R("hr09", "Tinggi dinding R-09", 4.5, "m", "tinggi tingkat LT1", "[Asumsi 5.4]", "0.0"),
        R("wr09", "Beban garis R-09 (dipasang pada sloof dalam, konservatif)", "={qr09}*{hr09}", "kN/m'", "letak sebenarnya menunggu tata letak LT1 (Tahap 7)",
          "[Asumsi 5.4]", "0.000", W_R09),
        R("bpl", "Berat pelindung magnet R-04", 93.2, "kN", "dinding utara 7,0 m + timur 6,0 m", "[Alat Medis R-04]", "0.0"),
        R("jpl", "Panjang dinding pelindung", 13.0, "m", "", "[Alat Medis R-04]", "0.0"),
        R("wpl", "Beban garis pelindung pada sloof as 10", "={bpl}/{jpl}", "kN/m'", "dinding timur y 54-60 langsung ke sloof as 10", "5.3", "0.000", pl_w()),
        R("mag", "Berat magnet MRI", P_MAGNET, "kN", "", "[Alat Medis R-03]", "0.0"),
        R("pmg", "Bagian magnet ke satu tepi panel", "={mag}/4", "kN", "dibagi sama ke empat tepi (as 9, 10, D, E)", "[Asumsi 5.4]", "0.000", P_MAGNET / 4),
    ]
    return [("A", "Masukan beban sloof", a)]


def baris_turun(r):
    ig = 0.40 * 0.80 ** 3 / 12
    a = [
        R("fc", "Mutu beton fc'", FC, "MPa", "kelas paparan S2", "5.3 (keputusan 2.7)", "0.0"),
        R("ec", "Ec = 4700 √fc'", "=4700*SQRT({fc})", "MPa", "", "SNI 2847:2019 Pasal 19.2.2.1", "#,##0.0", EC),
        R("b", "Lebar sloof", 0.40, "m", "", "konsep", "0.00"),
        R("h", "Tinggi sloof", 0.80, "m", "", "konsep", "0.00"),
        R("ig", "Ig = b h³ / 12", "={b}*{h}^3/12", "m⁴", "", "", "0.000000", ig),
        R("ief", "Faktor Ie / Ig balok", IE_FAKTOR, "", "0,35 Ig", "SNI 2847:2019 Tabel 6.6.3.1.1(a) (hal PDF 125)", "0.00"),
        R("ie", "Ie = 0,35 Ig", "={ief}*{ig}", "m⁴", "", "", "0.000000", IE_FAKTOR * ig),
        R("lb", "Bentang sloof", L, "m", "sumbu ke sumbu kolom", "grid 8 × 8 m", "0.0"),
        R("d16", "δ = 0,002 L", "=0.002*{lb}*1000", "mm", "kategori risiko IV, gedung > 1 tingkat, 0,002 L",
          "SNI 1726:2019 Tabel 22 (hal PDF 107) [Asumsi: dipakai sebagai beda penurunan desain]", "0.0", 16.0),
        R("mt16", "M penurunan = 6 Ec Ie δ / L² (δ 16 mm)", "=6*{ec}*1000*{ie}*{d16}/1000/{lb}^2", "kNm", "ujung jepit-jepit, tumpuan turun δ",
          "mekanika (cek PyNite T-93)", "0.00", momen_penurunan(0.40, 0.80, DELTA_16)),
        R("vt16", "V penurunan = 2 M / L (δ 16 mm)", "=2*{mt16}/{lb}", "kN", "", "", "0.00", 2 * momen_penurunan(0.40, 0.80, DELTA_16) / L),
        R("mg16", "M penurunan dengan Ig (pembanding, δ 16 mm)", "=6*{ec}*1000*{ig}*{d16}/1000/{lb}^2", "kNm", "tanpa reduksi kekakuan retak", "pembanding",
          "0.00", momen_penurunan(0.40, 0.80, DELTA_16, ie=1.0)),
        R("d8", "δ = 0,001 L (pembanding sensitivitas)", "=0.001*{lb}*1000", "mm", "", "[Asumsi 5.4]", "0.0", 8.0),
        R("mt8", "M penurunan (δ 8 mm)", "=6*{ec}*1000*{ie}*{d8}/1000/{lb}^2", "kNm", "", "", "0.00", momen_penurunan(0.40, 0.80, DELTA_8)),
    ]
    return [("A", "Momen akibat beda penurunan antar pile cap (sloof 400 × 800)", a)]


def baris_kap(r):
    d = d_(r, "SL-2")
    a_s, b_s = d["atas"], d["bawah"]
    ast = a_s["As"] + b_s["As"]
    a = [
        R("kb", "Lebar penampang SL-2", d["b"], "m", "", "", "0.00"),
        R("kh", "Tinggi penampang SL-2", d["h"], "m", "", "", "0.00"),
        R("kfc", "fc'", FC, "MPa", "", "", "0.0"),
        R("kfy", "fy", FY, "MPa", "", "", "0.0"),
        R("kas_a", f"As atas ({tul_s(a_s)}, {a_s['lapis']} lapis)", a_s["As"], "mm²", "", "tulangan terpilih desain", "#,##0.0"),
        R("kd_a", "d atas (selimut 40 mm ke sengkang)", a_s["d"], "m", "", "", "0.0000"),
        R("kas_b", f"As bawah ({tul_s(b_s)}, {b_s['lapis']} lapis)", b_s["As"], "mm²", "", "", "#,##0.0"),
        R("kd_b", "d bawah (selimut 50 mm ke sengkang)", b_s["d"], "m", "", "", "0.0000"),
        R("pm_a", "φMn atas = 0,9 As fy (d - a/2)", "=0.9*{kas_a}*{kfy}*({kd_a}-{kas_a}*{kfy}/(0.85*{kfc}*{kb}*1000000)/2)/1000", "kNm",
          "blok tegangan persegi, tulangan tarik saja", "SNI 2847:2019 Tabel 21.2.1 (φ 0,90), Pasal 22.2", "0.00", d["phiMn_neg"]),
        R("pm_b", "φMn bawah", "=0.9*{kas_b}*{kfy}*({kd_b}-{kas_b}*{kfy}/(0.85*{kfc}*{kb}*1000000)/2)/1000", "kNm", "", "", "0.00", d["phiMn_pos"]),
        R("phitn", "φTn = 0,9 (As atas + As bawah) fy (tarik ikat)", "=0.9*({kas_a}+{kas_b})*{kfy}/1000", "kN", "seluruh tulangan memanjang menerus",
          "SNI 2847:2019 Tabel 21.2.1", "#,##0.0", 0.9 * ast * FY / 1000),
        R("r_tie", "Ftie / φTn", "={ftie}/{phitn}", "", "Ftie dari lembar Gaya Ikat", "", "0.000", r["gi"]["ftie_maks"] / (0.9 * ast * FY / 1000)),
        R("phipn", "φPn tekan sloof = 0,65 × 0,80 (0,85 fc' (Ag - Ast) + fy Ast)",
          "=0.65*0.8*(0.85*{kfc}*({kb}*{kh}*1000000-({kas_a}+{kas_b}))+{kfy}*({kas_a}+{kas_b}))/1000", "kN",
          "diikat pelat LT1 dan tanah di sisi: tekuk tidak menentukan [Asumsi]", "SNI 2847:2019 Pasal 22.4.2.1", "#,##0.0", d["phiPn_tekan"]),
        R("r_tek", "Ftie / φPn", "={ftie}/{phipn}", "", "", "", "0.0000", r["gi"]["ftie_maks"] / d["phiPn_tekan"]),
    ]
    return [("A", "Kapasitas penampang SL-2 400 × 800 terhadap lentur dan gaya ikat", a)]


def baris_ujung(r):
    a = [
        R("ufy", "fy", FY, "MPa", "", "", "0.0"),
        R("ufc", "fc'", FC, "MPa", "", "", "0.0"),
        R("bk75", "Lebar kolom podium", 0.75, "m", "opsi B: semua kolom tangki juga 0,75", "5.1", "0.00"),
        R("selk", "Selimut kolom + sengkang (40 + 13)", SEL_KOL * 1000, "mm", "", "4.7", "0"),
        R("ldh25", "ldh D25 = fy db / (5,4 √fc'), min maks (8 db; 150)", "=MAX({ufy}*25/(5.4*SQRT({ufc})),8*25,150)", "mm",
          "kait standar 90° dalam inti kolom", "SNI 2847:2019 Pers. 18.8.5.1 (hal PDF 418)", "0.0", ldh(25)),
        R("ldh29", "ldh D29", "=MAX({ufy}*29/(5.4*SQRT({ufc})),8*29,150)", "mm", "", "SNI 2847:2019 Pers. 18.8.5.1", "0.0", ldh(29)),
        R("ldt750", "Tersedia di kolom 750", "=({bk75}*1000-{selk})", "mm", "dari muka kolom ke selimut luar kolom", "[Asumsi 5.4]", "0.0",
          (0.75 - SEL_KOL) * 1000),
        R("ld29b", "ld lurus D29 bawah (koef 1,7; ψt 1,0)", "={ufy}*29/(1.7*SQRT({ufc}))", "mm", "spasi bersih ≥ 2 db dan selimut ≥ db",
          "SNI 2847:2019 Tabel 25.4.2.2 (hal PDF 588)", "0.0", ld_lurus(29, False)),
        R("ld29a", "ld lurus D29 atas (koef 1,7; ψt 1,3)", "=1.3*{ufy}*29/(1.7*SQRT({ufc}))", "mm", "lebih dari 300 mm beton di bawah batang",
          "SNI 2847:2019 Tabel 25.4.2.4 (hal PDF 590)", "0.0", ld_lurus(29, True)),
        R("lap29", "Lewatan kelas B D29 atas = 1,3 ld", "=1.3*{ld29a}", "mm", "di tengah bentang, di luar 2h dari muka kolom",
          "SNI 2847:2019 Tabel 25.5.2.1 (hal PDF 608)", "0.0", 1.3 * ld_lurus(29, True)),
        R("dtebal", "Tebal dinding inti", tb.DINDING_T * 1000, "mm", "", "4.2", "0"),
        R("ldt_inti", "Tersedia di dinding inti", "={dtebal}-{selk}", "mm", "", "[Asumsi 5.4]", "0.0", (tb.DINDING_T - SEL_KOL) * 1000),
    ]
    return [("A", "Penyaluran tulangan sloof di ujung", a)]


def baris_mri(r):
    a = [
        R("ix", "Isocenter x", M_ISO[0], "m", "", "[Syarat MRI 1]", "0.0"),
        R("iy", "Isocenter y", M_ISO[1], "m", "", "[Syarat MRI 1]", "0.0"),
        R("rnm", "Radius bebas baja karbon dari isocenter", 1.0, "m", "", "[Syarat MRI 7]", "0.0"),
    ]
    b = []
    for i, m in enumerate(r["mri"]):
        x0, x1, y0, y1 = m["kotak"]
        b.append(R(f"jm{i}", f"Jarak muka sloof {m['nama']} ke isocenter", mri.fj("{ix}", "{iy}", x0, x1, y0, y1), "m",
                   f"kotak sloof x {idn(x0, 1)}-{idn(x1, 1)} / y {idn(y0, 1)}-{idn(y1, 1)} (lebar 0,40 m)", "geometri 5.3", "0.00", m["jarak"]))
    return [("A", "Masukan", a), ("B", "Jarak horizontal muka sloof terdekat ke isocenter (harus > 1,0 m)", b)]


def semua_baris(r):
    out = {}
    for nama, fn in (("Gaya Ikat", baris_ikat), ("Beban", baris_beban), ("Penurunan Beda", baris_turun), ("Kapasitas", baris_kap),
                     ("Ujung Sloof", baris_ujung), ("Jarak MRI", baris_mri)):
        out[nama] = [rw for _, _, rows in fn(r) for rw in rows]
    return out


NAMA = ["Petunjuk", "Ringkasan", "Gaya Ikat", "Beban", "Lentur Gravitasi", "Penurunan Beda", "Momen Kolom", "Desain Sloof", "Sensitivitas", "Kapasitas",
        "Ujung Sloof", "Jarak MRI", "Cek Silang T-93", "Acuan"]


# ------------------------------------------------------------------ teks tabel
def teks_ikat(r):
    out = []
    for b in r["gi"]["kelompok"]:
        x, y = b["kunci"]
        out.append([f"{b['kel']} (b {idn(b['b'] * 1000, 0)} mm)", b["n"], idn(b["pu"], 0), f"kolom penentu x {idn(x, 0)}, y {idn(y, 0)}; Ftie = {idn(b['ftie'], 1)} kN",
                    "4.7; kolom tangki opsi B dari 5.1"])
    return out


def teks_gravitasi(r):
    out = []
    for t in TIPE:
        for (b, h) in UKURAN:
            g = r["desain"][(t, b, h)]["g"]
            out.append([t, f"{idn(b * 1000, 0)} × {idn(h * 1000, 0)}", idn(g["neg_g"], 1), idn(g["pos_g"], 1), idn(g["v_g"], 1), idn(g["neg_s"], 1),
                        idn(g["pos_s"], 1), idn(g["v_s"], 1), idn(g["neg_d09"], 1)])
    return out


def teks_momen_kolom(r):
    mk = r["mk"]
    return [[b["kel"], b["n"], idn(b["Mx"], 1), idn(b["My"], 1), idn(b["M_dalam"], 1), idn(b["M_tepi"], 1)] for b in mk["kelompok"]]


def teks_me(r):
    mk = r["mk"]
    out = []
    for t in TIPE:
        (x, y), arah = mk["me_ket"][t]
        out.append([t, NAMA_TIPE[t], idn(mk["me"][t], 1), f"kolom x {idn(x, 0)}, y {idn(y, 0)}", f"sloof arah {arah}", "kolom dalam M/2, kolom tepi M"])
    return out


def teks_desain(r):
    out = []
    for t in TIPE:
        d = d_(r, t)
        out.append([t, f"{tul_s(d['atas'])} ({d['atas']['lapis']} lapis) / {tul_s(d['bawah'])} ({d['bawah']['lapis']} lapis)", idn(maks_kasus(d, "neg"), 1),
                    idn(maks_kasus(d, "pos"), 1), f"Ve {idn(d['Ve'], 1)}; Vu {idn(d['Vu'], 1)}", f"{idn(d['phiMn_neg'], 1)} / {idn(d['phiMn_pos'], 1)}",
                    rasio_s(d), sengkang_s(d), status_s(d)])
    return out


def teks_kombinasi(r):
    out = []
    for t in TIPE:
        d = d_(r, t)
        for k, v in d["kasus"].items():
            out.append([t, KOMBINASI[k] + (f"; Ftie {idn(v['tie'], 0)} kN" if v["tie"] else ""), idn(v["neg"], 1), idn(v["pos"], 1), idn(v["vu"], 1),
                        f"{idn(d['phiMn_neg'], 1)} / {idn(d['phiMn_pos'], 1)}", idn(max(v["r_neg"], v["r_pos"]), 3),
                        "T ikut" if "T" in k else "tanpa T"])
    return out


def teks_kandidat(r):
    out = []
    for t in TIPE:
        for (b, h) in UKURAN:
            d = r["desain"][(t, b, h)]
            out.append([t, f"{idn(b * 1000, 0)} × {idn(h * 1000, 0)}", f"{tul_s(d['atas'])} / {tul_s(d['bawah'])}", pct(d["atas"]["rho"]), d["atas"]["lapis"],
                        idn(d["Ve"], 1), rasio_s(d), sengkang_s(d), status_s(d)])
    return out


def teks_sens(r):
    out = []
    for (b, h) in UKURAN[:2]:
        for t in TIPE:
            for dl in (DELTA_16, DELTA_8):
                for tg in (False, True):
                    d = r["sensitivitas"][(b, h, dl, tg)][t]
                    out.append([t, f"{idn(b * 1000, 0)} × {idn(h * 1000, 0)}", f"δ {idn(dl * 1000, 0)} mm; T {'masuk' if tg else 'tidak masuk'} di gempa",
                                f"{tul_s(d['atas'])} / {tul_s(d['bawah'])}", pct(d["atas"]["rho"]), idn(max(v["neg"] for v in d["kasus"].values()), 1),
                                idn(d["T"], 1), status_s(d)])
    return out


def teks_jepit(r):
    out = []
    for t in TIPE:
        for (b, h) in UKURAN[:2]:
            d = r["jepit"][(t, b, h)]
            o = r["desain"][(t, b, h)]
            out.append([t, f"{idn(b * 1000, 0)} × {idn(h * 1000, 0)}", f"{tul_s(o['atas'])} / {tul_s(o['bawah'])} ({pct(o['atas']['rho'])} %)",
                        f"{tul_s(d['atas'])} / {tul_s(d['bawah'])} ({pct(d['atas']['rho'])} %)", status_s(d)])
    return out


def teks_ujung(r):
    out = []
    for u in ujung_tabel(29):
        if u["perlu"] == 0.0:
            out.append([u["jenis"], "-", "-", "menerus: tulangan atas dan bawah melewati kolom (tidak diputus)", u["pasal"]])
        else:
            ok = u["perlu"] <= u["ada"]
            out.append([u["jenis"], idn(u["perlu"], 0), idn(u["ada"], 0),
                        "cukup" if ok else "tidak cukup: perlu kait ke pile cap inti atau tulangan diteruskan (menunggu Tahap 6)", u["pasal"]])
    return out


# ------------------------------------------------------------------ workbook
def _tt(lb, kepala, isi, rata, beku=False, ai=True):
    return mri._teks_tabel(lb, kepala, isi, rata, beku=beku, ai=ai)


def _ketentuan(r):
    """(kunci, teks) untuk Ringkasan dan MD: angka kunci yang dipakai di beberapa tempat."""
    d1, d2, d3 = d_(r, "SL-1"), d_(r, "SL-2"), d_(r, "SL-3")
    k9 = r["desain"][("SL-1", 0.40, 0.90)]
    j1 = r["jepit"][("SL-1", 0.40, 0.80)]
    return d1, d2, d3, k9, j1


def buat_excel(keluar=BERKAS):
    from format_dokumen import AI, Lembar, set_font_bawaan
    r = hitung()
    gi, mk = r["gi"], r["mk"]
    d1, d2, d3, k9, j1 = _ketentuan(r)
    x3 = r["t93"]
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    for s in NAMA:
        wb.create_sheet(s)
    mri.REF.clear()
    mri.LABEL_PAKAI.clear()
    ket = LABEL + " " + LABEL_AI
    tt = _tt

    # ---- Gaya Ikat
    def tambah_ikat(lb):
        lb.kosong()
        lb.bagian("B", "Gaya ikat per kelompok kolom (Pu terbesar di dasar kolom)")
        tt(lb, ["No", "Kelompok kolom", "n kolom", "Pu (kN)", "Penentu dan Ftie", "Sumber"], teks_ikat(r), list("clccll"))
        lb.kosong()
        lb.catatan("SNI 1726:2019 Pasal 7.13.7.2 (hal PDF 104-105) berlaku untuk KDS D-F: pile cap harus dihubungkan dengan pengikat berkuat tarik dan tekan desain "
                   "≥ 10 % SDS × (beban mati + hidup terfaktor) pada pile cap atau kolom yang lebih besar, kecuali ada kekangan ekuivalen. Sloof dianggap pengikat. "
                   "Pasal 7.13.8.3.5 (hal PDF 109): bila laporan geoteknik menyatakan serakan lateral permanen, gaya pengikat ditambah tekanan akibat pergerakan tanah; "
                   "data serakan lateral belum ada (SI 5.4: data belum ada, menunggu Tahap 6 dan analisis likuifaksi). Tabel 22 (hal PDF 107) memuat batas beda penurunan, "
                   "bukan batas serakan. Cek kapasitas terhadap tarik dan tekan ada di lembar Kapasitas.")
    mri._lembar_hitung(wb, "Gaya Ikat", 3, "Gaya ikat antar pile cap (pengikat fondasi)", ket + " KDS D, kelas situs SF.", baris_ikat(r), tambah_ikat)

    # ---- Beban
    def tambah_beban(lb):
        lb.kosong()
        lb.catatan("Tipe sloof: SL-1 sloof dalam (pelat PL-1 dua sisi, beban garis R-09 dipasang konservatif); SL-2 sloof tepi (pelat satu sisi + dinding fasad); "
                   "SL-3 sloof as 10 (x 84), 6 bentang, bentang D-E dengan panel MRI (D 8,655; Lo 2,87), pelindung 7,17 kN/m' di y 54-59 (D-E) dan y 59-60 (E-F), "
                   "dan 12,0 kN di tengah D-E. Catatan: as 10 adalah tepi gedung (5.3: tepi timur x 84), jadi pelat hanya di satu sisi; rancangan awal menyebut dua sisi. "
                   "Panel MRI qu = 14,98 kPa < PL-1 17,26 kPa, sehingga sloof di as 9, D, E (PL-1 di kedua sisi) dicakup SL-1. Beban segitiga: 16 titik per bentang "
                   "(q × L/2 puncak, tributary 0,5 m). Beban hidup dengan pola 3 kasus (bentang ganjil, genap, semua).")
    mri._lembar_hitung(wb, "Beban", 4, "Beban pada sloof", ket + " Pelat LT1 +12,85, 250 mm, ditumpu sloof di semua as; sisi atas sloof = sisi atas pelat.",
                       baris_beban(r), tambah_beban)

    # ---- Lentur Gravitasi
    lb = Lembar(wb["Lentur Gravitasi"], 5, "Lentur gravitasi: balok menerus PyNite sepanjang satu garis as", [5, 10, 16, 14, 14, 14, 14, 14, 14, 16])
    lb.catatan(ket + f" Model: 5 bentang 8 m (SL-3: 6 bentang as 10), tumpuan sendi di kolom, pegas putar di kedua ujung garis = kolom 750 di atas sloof "
               f"({idn(K_ROT, 0)} kNm/rad, 4 Ec 0,70 Ig / 4,5 m seperti 5.1). Momen di sumbu tumpuan (konservatif); selubung semua bentang dan pola beban hidup. "
               "Mu+ = momen lapangan maksimum; Mu- = momen tumpuan maksimum (nilai mutlak).")
    lb.kosong()
    lb.bagian("A", "Hasil per tipe dan ukuran (D 400 × 800 menentukan 5.4; ukuran lain untuk kandidat)")
    _tt(lb, ["No", "Tipe", "Ukuran (mm)", "Mu- 1,4D; 1,2D+1,6L (kNm)", "Mu+ gravitasi (kNm)", "Vu gravitasi (kN)", "Mu- (1,2+0,2SDS)D+L (kNm)",
             "Mu+ (1,2+0,2SDS)D+L (kNm)", "V (1,2+0,2SDS)D+L (kN)", "Mu- (0,9-0,2SDS)D (kNm)"], teks_gravitasi(r), list("clcccccccc"), beku=True)

    # ---- Penurunan Beda
    def tambah_turun(lb):
        lb.kosong()
        lb.bagian("B", "Momen akibat penurunan beda per ukuran sloof (δ 16 mm; δ 8 mm; Ig)")
        isi = []
        for (b, h) in UKURAN:
            ig = b * h ** 3 / 12
            isi.append([f"{idn(b * 1000, 0)} × {idn(h * 1000, 0)}", idn(IE_FAKTOR * ig, 6), idn(momen_penurunan(b, h, DELTA_16), 1),
                        f"δ 8 mm: M = {idn(momen_penurunan(b, h, DELTA_8), 1)} kNm; δ 16 mm dengan Ig: M = {idn(momen_penurunan(b, h, DELTA_16, ie=1.0), 1)} kNm; "
                        f"V = 2M/L = {idn(2 * momen_penurunan(b, h, DELTA_16) / L, 1)} kN", "6 Ec Ie δ / L²"])
        tt(lb, ["No", "Ukuran sloof (mm)", "Ie (m⁴)", "M δ 16 (kNm)", "Pembanding", "Rumus"], isi, list("clccll"))
        lb.kosong()
        lb.catatan("Beda penurunan: kategori risiko IV, gedung lebih dari satu tingkat: 0,002 L = 16 mm (SNI 1726:2019 Tabel 22, hal PDF 107) [Asumsi: batas dipakai sebagai beda "
                   "penurunan desain; 2.8 hanya memberi penurunan urugan halaman 0,15-1,18 m, bukan penurunan pile cap; penurunan tiang dari Tahap 6 akan memperbarui]. "
                   "SNI 2847:2019 Pasal 5.3.6 (hal PDF 108): faktor beban T tidak kurang dari 1,0. Kombinasi 1,2D + 1,6L + 1,0T. Ie = 0,35 Ig (Tabel 6.6.3.1.1(a)). "
                   "Ujung jepit-jepit dengan penurunan satu tumpuan: momen berlawanan tanda di kedua ujung (satu ujung negatif, ujung lain positif), V konstan = 2M/L. "
                   "Gaya tambahan pada kolom dan pile cap tidak dihitung di 5.4.")
    mri._lembar_hitung(wb, "Penurunan Beda", 6, "Momen akibat beda penurunan antar pile cap", ket, baris_turun(r), tambah_turun)

    # ---- Momen Kolom
    lb = Lembar(wb["Momen Kolom"], 7, "Momen kolom bila kepala tiang dianggap sendi", [5, 34, 10, 16, 16, 18, 18, 40])
    lb.catatan(ket + " Momen dasar kolom LT1 (ujung bawah segmen LT1-LT2) dari 4.7: kombinasi gempa, termasuk ρ 1,3 dan Ev 0,2 SDS, dasar jepit. Bila kepala tiang sendi, "
               "momen itu dialihkan ke sloof: kolom dalam pada arah itu M/2 ke tiap sloof, kolom tepi M ke satu sloof. Mx (terhadap sumbu X) dipikul sloof arah Y; "
               "My dipikul sloof arah X. Momen sloof ujung = bagian kolom, V = 2M/L (pola antisimetris). Inti memikul momen gulingnya sendiri ke pile cap inti, tidak "
               "dibagi ke sloof [Asumsi]. Kolom tangki opsi B (5.1): momen tetap dari analisis 4.7 (kolom 800/950), konservatif untuk kolom 750.")
    lb.kosong()
    lb.bagian("A", "Momen dasar kolom gempa maksimum per kelompok")
    _tt(lb, ["No", "Kelompok kolom", "n", "Mx maks (kNm)", "My maks (kNm)", "M ke sloof kolom dalam (kNm)", "M ke sloof kolom tepi (kNm)"], teks_momen_kolom(r),
        list("clccccc"), beku=True)
    lb.kosong()
    lb.bagian("B", "Momen ujung sloof dari kolom (ME) yang menentukan per tipe")
    _tt(lb, ["No", "Tipe sloof", "Arah", "ME (kNm)", "Kolom penentu", "Pembagian", "Keterangan"],
        [[f"{x[0]}: {x[1]}", x[4].replace("sloof arah ", ""), x[2], x[3], x[5], "maksimum bagian kolom di semua kolom pada garis sloof tipe itu"] for x in teks_me(r)],
        list("clccccl"))

    # ---- Desain Sloof
    lb = Lembar(wb["Desain Sloof"], 8, "Desain sloof: lentur, geser, detail", [5, 10, 36, 14, 14, 18, 18, 12, 44, 40])
    lb.catatan(ket + " SNI 2847:2019 Pasal 18.13.3.3 (hal PDF 449): sloof yang memikul momen kolom sistem pemikul gaya seismik harus memenuhi 18.6: ρ ≤ 0,025 dan minimal "
               "2 batang menerus (18.6.3.1, hal 400); M+ ≥ 0,5 M- di muka joint (18.6.3.2, hal 401); sengkang pengekang ≤ min(d/4; 6 db; 150) di 2h (18.6.4.4, hal 402), "
               "≤ d/2 di tengah (18.6.4.6); Ve dari Mpr = 1,25 fy dan gravitasi, Vc = 0 bila Ve gempa ≥ 0,5 Ve dan gaya tekan < Ag fc'/20 (18.6.5.1-18.6.5.2, hal 403); "
               "18.13.3.2: dimensi terkecil ≥ ln/20 (tidak perlu > 450) dan sengkang ≤ min(setengah dimensi terkecil; 300). Selimut 50 mm bawah dan samping, 40 mm atas "
               "[Asumsi 5.4]; D25 diutamakan, D22/D29 bila perlu; gaya tarik ikat ditambahkan ke As (φ 0,9, konservatif). Tulangan tekan, sayap pelat (T) tidak diperhitungkan.")
    lb.kosong()
    lb.bagian("A", "Hasil 400 × 800 (δ 16 mm; T tidak di kombinasi gempa)")
    _tt(lb, ["No", "Tipe", "Tulangan atas / bawah", "Mu- maks (kNm)", "Mu+ maks (kNm)", "Ve; Vu (kN)", "φMn- / φMn+ (kNm)", "Rasio maks", "Sengkang", "Status"],
        teks_desain(r), list("clcccccclc"), beku=True)
    lb.kosong()
    lb.bagian("B", "Kombinasi per tipe (400 × 800)")
    _tt(lb, ["No", "Tipe", "Kombinasi", "Mu- (kNm)", "Mu+ (kNm)", "Vu (kN)", "φMn- / φMn+ (kNm)", "Rasio", "Keterangan"], teks_kombinasi(r), list("clcccccc") + ["l"])
    lb.kosong()
    lb.bagian("C", "Kandidat ukuran (keputusan di tangan Defsa)")
    _tt(lb, ["No", "Tipe", "Ukuran (mm)", "Tulangan atas / bawah", "ρ atas (%)", "Lapis atas", "Ve (kN)", "Rasio maks", "Sengkang", "Status"],
        teks_kandidat(r), list("clccccccll"))

    # ---- Sensitivitas
    lb = Lembar(wb["Sensitivitas"], 9, "Sensitivitas: δ, T di kombinasi gempa, dan kepala tiang jepit", [5, 10, 44, 36, 40, 40])
    lb.catatan(ket + " Varian pembanding; keputusan di tangan Defsa. 'Kepala tiang jepit' = momen kolom tidak masuk ke sloof (ME = 0), hanya gravitasi dan penurunan.")
    lb.kosong()
    lb.bagian("A", "Pengaruh δ (16 / 8 mm) dan T di kombinasi gempa (400 × 800 dan 400 × 900)")
    isi = []
    for x in teks_sens(r):
        isi.append([x[0], f"{x[1]}; {x[2]}", f"{x[3]} (ρ atas {x[4]} %)", f"Mu- maks {x[5]} kNm; M penurunan {x[6]} kNm", x[7]])
    _tt(lb, ["No", "Tipe", "Ukuran dan kondisi", "Tulangan atas / bawah", "Momen", "Status"], isi, list("clllll"), beku=True)
    lb.kosong()
    lb.bagian("B", "Kepala tiang sendi (momen kolom ke sloof) dibanding jepit (tanpa momen kolom)")
    _tt(lb, ["No", "Tipe", "Ukuran (mm)", "Sendi (ρ atas)", "Jepit (ρ atas)", "Status jepit"], teks_jepit(r), list("clllll"))

    # ---- Kapasitas
    mri._lembar_hitung(wb, "Kapasitas", 10, "Kapasitas penampang dan gaya ikat", ket + " Gaya ikat tarik juga ditambahkan ke As pada kombinasi gempa (pendekatan konservatif). "
                       f"Pembanding concreteproperties (T-93): φMn atas dengan tulangan tarik saja {idn(x3['d']['cp_neg'], 1)} kNm; dengan kedua lapis (tulangan tekan) "
                       f"{idn(x3['d']['cp_neg_penuh'], 1)}; dengan tarik Ftie bersamaan {idn(x3['d']['cp_tarik'], 1)} kNm (turun {idn((1 - x3['d']['cp_tarik'] / x3['d']['cp_neg_penuh']) * 100, 1)} % "
                       f"dari {idn(x3['d']['cp_neg_penuh'], 1)}), kurang dari tambahan As tarik yang dipakai.", baris_kap(r))

    # ---- Ujung Sloof
    def tambah_ujung(lb):
        lb.kosong()
        lb.bagian("B", "Panjang penyaluran perlu dan tersedia (D29, terbesar yang dipakai)")
        tt(lb, ["No", "Jenis ujung", "Perlu (mm)", "Tersedia (mm)", "Keputusan", "Pasal"], teks_ujung(r), list("clccll"))
        lb.kosong()
        lb.catatan("Kolom tepi: kait 90° ke dalam inti kolom (18.8.5.1, hal PDF 418); tersedia = lebar kolom - selimut 53 mm. Opsi B menyeragamkan kolom tangki jadi 750; "
                   "bila opsi A, kolom 800 dan 950 tersedia 747 dan 897 mm. Kolom dalam: tulangan menerus melewati kolom (18.13.3.1, hal PDF 449). Inti: dinding 350 mm "
                   "tidak cukup untuk ldh D29; tulangan sloof diangkur ke pile cap inti (kait ke bawah) atau diteruskan menembus inti: kedalaman dan ukuran pile cap inti "
                   "belum ada (Tahap 6). Tabel 25.4.2.2 koef 1,7 untuk spasi bersih ≥ 2 db dan selimut ≥ db; di luar itu koef 1,1 (hal PDF 588).")
    mri._lembar_hitung(wb, "Ujung Sloof", 11, "Ujung sloof: penyaluran di kolom tepi, kolom dalam, dan inti", ket, baris_ujung(r), tambah_ujung)

    # ---- Jarak MRI
    def tambah_mri(lb):
        lb.kosong()
        lb.bagian("C", "Status")
        isi = [[m["nama"], round(m["jarak"], 3), "m", "memenuhi" if m["jarak"] > 1.0 else "tidak", "sloof baja karbon biasa" if m["jarak"] > 1.0 else "perlu tahan karat"]
               for m in r["mri"]]
        lb.tabel(["No", "Sloof", "Jarak (m)", "Satuan", "Status", "Keputusan"], [[i + 1, *x] for i, x in enumerate(isi)], rata=list("clccll"), fmt=[None, None, "0.00", None, None, None])
        lb.kosong()
        lb.catatan("Jarak horizontal; sloof di bawah pelat sehingga jarak 3D lebih besar. Zona baja tahan karat x 79,5-81,5 / y 56-58 (5.2) tidak tersentuh sloof. "
                   "Semua jarak > 1,0 m: sloof memakai baja karbon biasa.")
    mri._lembar_hitung(wb, "Jarak MRI", 12, "Jarak sloof ke isocenter MRI", ket, baris_mri(r), tambah_mri)

    # ---- Cek Silang T-93
    lb = Lembar(wb["Cek Silang T-93"], 13, "Cek silang T-93", [5, 58, 14, 14, 12, 12, 10, 56])
    lb.catatan(ket + " Toleransi ditetapkan sebelum membandingkan. Cara 1 = tangan atau metode lain; cara 2 = skrip, PyNite, atau concreteproperties.")
    lb.kosong()
    lb.bagian("A", "Empat cek silang")
    ws = lb.ws
    a, b, c, d = x3["a"], x3["b"], x3["c"], x3["d"]
    kep = ["No", "Cek", "Cara 1", "Cara 2", "Selisih (%)", "Toleransi (%)", "Status", "Cara 1 / cara 2"]
    isi = [
        [1, "(a) Ftie maksimum (kN)", None, None, None, TOL["a"], None, f"1: tangan 0,10 × 0,386 × Pu {idn(a['pu'], 1)} kN. 2: lembar Gaya Ikat"],
        [2, "(b) Momen ujung sloof SL-1 jepit-jepit satu bentang, beban D (kNm)", None, None, None, TOL["b"], None,
         "1: tangan w L²/12 + 5 wp L²/96 (segitiga dua sisi). 2: PyNite balok menerus, pegas putar 1e10, beban 16 titik"],
        [3, "(c) Momen penurunan δ 16 mm, 400 × 800, Ie = 0,35 Ig (kNm)", None, None, None, TOL["c"], None, "1: lembar Penurunan Beda. 2: PyNite satu bentang jepit-jepit, DY turun 16 mm"],
        [4, "(d) φMn atas SL-2 400 × 800 (kNm)", None, None, None, TOL["d"], None, "1: lembar Kapasitas (rumus sendiri). 2: concreteproperties, tulangan tarik saja"],
        [5, "(d) φMn bawah SL-2 400 × 800 (kNm)", None, None, None, TOL["d"], None, "1: lembar Kapasitas. 2: concreteproperties, tulangan tarik saja"],
    ]
    r0, a0, a1 = lb.tabel(kep, isi, rata=list("clcccccl"), fmt=[None, None, "0.000", "0.000", "0.00", "0.0", None, None])

    def ref(key):
        return "=" + mri._sub("{" + key + "}", ws.title)
    c2, c3 = lb.kol(2), lb.kol(3)
    ws[f"{c2}{a0}"] = f"=0.10*0.386*{a['pu']!r}"
    ws[f"{c3}{a0}"] = ref("ftie")
    wsw = tb.GAMMA_C * 0.40 * (0.80 - H_PELAT) + W_R09
    ws[f"{c2}{a0 + 1}"] = f"={wsw!r}*8^2/12+5*{2 * D_PL * L / 2!r}*8^2/96"
    ws[f"{c3}{a0 + 1}"] = b["pynite"]
    ws[f"{c2}{a0 + 2}"] = ref("mt16")
    ws[f"{c3}{a0 + 2}"] = c["pynite"]
    ws[f"{c2}{a0 + 3}"] = ref("pm_a")
    ws[f"{c3}{a0 + 3}"] = d["cp_neg"]
    ws[f"{c2}{a0 + 4}"] = ref("pm_b")
    ws[f"{c3}{a0 + 4}"] = d["cp_pos"]
    for i in range(5):
        rr = a0 + i
        ws[f"{lb.kol(4)}{rr}"] = f"=ABS({c3}{rr}-{c2}{rr})/{c2}{rr}*100"
        ws[f"{lb.kol(6)}{rr}"] = f'=IF({lb.kol(4)}{rr}<={lb.kol(5)}{rr},"Lolos","Tidak lolos")'
        ws[f"{lb.kol(5)}{rr}"].fill = PatternFill("solid", fgColor=AI)
    for i in (1, 2, 3, 4):
        ws[f"{c3}{a0 + i}"].fill = PatternFill("solid", fgColor=AI)
    lb.kosong()
    lb.catatan(f"Catatan cek: pada (b) kontinuitas: pada garis menerus 5 bentang, momen tumpuan dalam SL-1 (Mu- gravitasi {idn(d1['g']['neg_g'], 1)} kNm) berbeda dari jepit-jepit karena momen "
               "terbagi ke bentang tetangga; perbandingan jepit-jepit satu bentang dipakai agar setara dengan rumus. untuk (c) PyNite tidak memuat deformasi geser (cocok dengan balok Euler). "
               f"Untuk (d) dengan tulangan tekan ikut, φMn atas {idn(d['cp_neg_penuh'], 1)} kNm dan bawah {idn(d['cp_pos_penuh'], 1)} kNm; rumus sendiri mengabaikan tulangan tekan (konservatif).")

    # ---- Ringkasan
    lb = Lembar(wb["Ringkasan"], 2, "Ringkasan temuan dan keputusan yang diminta dari Defsa", [5, 38, 70, 46, 44])
    lb.catatan(f"STATUS: {STATUS}. " + ket)
    lb.kosong()
    lb.bagian("A", "Temuan")
    me = mk["me"]
    tt(lb, ["No", "Temuan", "Hasil kunci", "Keputusan Defsa", "Usulan AI"], [
        ["Gaya ikat (SNI 1726 7.13.7.2)",
         f"Ftie = 0,10 × 0,386 × Pu {idn(gi['pu_maks'], 0)} kN = {idn(gi['ftie_maks'], 1)} kN (maks); kelompok tangki opsi B {idn(gi['kelompok'][1]['ftie'], 1)} kN. "
         f"φTn SL-2 {idn(0.9 * (d2['atas']['As'] + d2['bawah']['As']) * FY / 1000, 0)} kN: rasio {idn(gi['ftie_maks'] / (0.9 * (d2['atas']['As'] + d2['bawah']['As']) * FY / 1000), 3)}. "
         "Serakan lateral (7.13.8.3.5): data belum ada.", "Menyetujui.", "Setuju; Ftie bukan penentu."],
        ["Lentur gravitasi",
         f"Mu- / Mu+ / Vu 400 × 800: SL-1 {idn(d1['g']['neg_g'], 0)} / {idn(d1['g']['pos_g'], 0)} / {idn(d1['g']['v_g'], 0)}; SL-2 {idn(d2['g']['neg_g'], 0)} / {idn(d2['g']['pos_g'], 0)} / "
         f"{idn(d2['g']['v_g'], 0)}; SL-3 {idn(d3['g']['neg_g'], 0)} / {idn(d3['g']['pos_g'], 0)} / {idn(d3['g']['v_g'], 0)} (kNm, kNm, kN). Rasio ≤ {rasio_s(d1)}.", "Menyetujui.", "Setuju."],
        ["Penurunan beda δ 0,002 L",
         f"δ 16 mm: M = {idn(d1['T'], 1)} kNm (Ie 0,35 Ig; dengan Ig {idn(momen_penurunan(0.4, 0.8, DELTA_16, ie=1.0), 1)}); δ 8 mm: {idn(momen_penurunan(0.4, 0.8, DELTA_8), 1)} kNm. "
         f"Kombinasi G+T tidak menentukan (rasio {idn(d1['kasus']['G+T']['r_neg'], 2)}); gempa menentukan.", "Memilih δ desain (16 atau 8 mm).", "16 mm sampai penurunan tiang Tahap 6 ada."],
        ["Momen kolom (kepala tiang sendi)",
         f"M dasar kolom maks {idn(mk['M_maks'], 0)} kNm; ME ke sloof SL-1 {idn(me['SL-1'], 0)}, SL-2 {idn(me['SL-2'], 0)}, SL-3 {idn(me['SL-3'], 0)} kNm. "
         f"Tanpa momen kolom (jepit) SL-1 400 × 800 cukup: {tul_s(j1['atas'])} / {tul_s(j1['bawah'])}.", "Sendi atau jepit.", "Desain dengan asumsi sendi (aman) sampai Tahap 6."],
        ["Sloof 400 × 800",
         f"SL-1: {status_s(d1)} ({tul_s(d1['atas'])} atas, ρ {pct(d1['atas']['rho'])} %). SL-2: {tul_s(d2['atas'])} atas / {tul_s(d2['bawah'])} bawah, rasio {rasio_s(d2)}, "
         f"{status_s(d2)}. SL-3: {tul_s(d3['atas'])} / {tul_s(d3['bawah'])}, {status_s(d3)}.", "Memilih ukuran SL-1.",
         f"SL-1 400 × 900: {tul_s(k9['atas'])} atas ({k9['atas']['lapis']} lapis, ρ {pct(k9['atas']['rho'])} %), {status_s(k9)}; SL-2 dan SL-3 tetap 400 × 800."],
        ["Geser dan sengkang",
         f"Ve = Mpr/ln + Vg: SL-1 {idn(d1['Ve'], 0)}, SL-2 {idn(d2['Ve'], 0)}, SL-3 {idn(d3['Ve'], 0)} kN; Vc = 0. Sengkang D{d2['ds']}-{idn(d2['s_ujung'] * 1000, 0)} di 2h dan D{d2['ds']}-"
         f"{idn(d2['s_tengah'] * 1000, 0)} di tengah (SL-2).", "Menyetujui.", "Setuju."],
        ["Ujung sloof",
         f"ldh D29 {idn(ldh(29), 0)} mm vs tersedia kolom 750: {idn((0.75 - SEL_KOL) * 1000, 0)} mm (cukup); dinding inti 350: {idn((tb.DINDING_T - SEL_KOL) * 1000, 0)} mm (kurang): "
         "diangkur ke pile cap inti (Tahap 6).", "Menyetujui.", "Setuju."],
        ["Jarak ke isocenter MRI",
         "; ".join(f"{m['nama']} {idn(m['jarak'], 1)} m" for m in r["mri"]) + ": semua > 1,0 m, sloof baja karbon biasa.", "Menyetujui.", "Setuju."],
    ], list("clllll")[:5], beku=True)
    lb.kosong()
    lb.catatan(f"Cek silang T-93 lolos (lembar Cek Silang T-93). Pasal yang tidak ada di acuan ditulis 'belum ada di acuan' (lembar Acuan).")

    # ---- Acuan
    lb = Lembar(wb["Acuan"], 14, "Acuan yang dipakai dan statusnya", [5, 26, 30, 62, 12, 34])
    lb.catatan(ket + " Halaman = nomor halaman PDF di acuan/privat (diverifikasi dengan pypdf, 21 Nov 2026).")
    lb.kosong()
    lb.bagian("A", "Pasal yang diverifikasi di PDF")
    tt(lb, ["No", "Acuan", "Pasal", "Isi yang dipakai", "Hal. PDF", "Status"], [
        ["SNI 1726:2019", "7.13.7.2", "Pengikat fondasi KDS D-F: kuat tarik dan tekan ≥ 10 % SDS × (1,2D + 1,6L) pile cap atau kolom yang lebih besar.", "104-105", "Terverifikasi"],
        ["SNI 1726:2019", "7.13.8.3.5", "Pengikat; tambahan gaya akibat serakan lateral dari laporan geoteknik.", "109", "Terverifikasi; data belum ada"],
        ["SNI 1726:2019", "Tabel 22", "Batas beda penurunan: kategori risiko IV 0,002 L.", "107", "Terverifikasi"],
        ["SNI 2847:2019", "5.3.6", "Pengaruh T: faktor beban tidak kurang dari 1,0.", "108", "Terverifikasi"],
        ["SNI 2847:2019", "Tabel 6.6.3.1.1(a)", "Balok 0,35 Ig.", "125", "Terverifikasi"],
        ["SNI 2847:2019", "18.13.3.1-18.13.3.3", "Sloof: tulangan menerus, dimensi ≥ ln/20, sengkang ≤ min(setengah dimensi; 300), memenuhi 18.6.", "449", "Terverifikasi"],
        ["SNI 2847:2019", "18.6.3.1, 18.6.3.2", "ρ ≤ 0,025, 2 batang menerus; M+ ≥ 0,5 M- di muka joint.", "400; 401", "Terverifikasi"],
        ["SNI 2847:2019", "18.6.4.4, 18.6.4.6", "Sengkang pengekang di 2h: ≤ min(d/4; 6 db; 150), pertama ≤ 50 mm; di tengah ≤ d/2.", "402", "Terverifikasi"],
        ["SNI 2847:2019", "18.6.5.1, 18.6.5.2", "Ve dari Mpr (1,25 fy) dan gravitasi; Vc = 0 bila syarat dipenuhi.", "403", "Terverifikasi"],
        ["SNI 2847:2019", "18.8.5.1", "ldh = fy db / (5,4 λ √fc'), min maks (8 db; 150).", "418", "Terverifikasi"],
        ["SNI 2847:2019", "25.2.1", "Spasi bersih batang sejajar dalam lapis ≥ maks (25 mm; db).", "581", "Terverifikasi (dari 4.6)"],
        ["SNI 2847:2019", "Tabel 25.4.2.2, 25.4.2.4", "ld batang ulir tarik; ψt 1,3 batang atas.", "588; 590", "Terverifikasi"],
        ["SNI 2847:2019", "Tabel 25.5.2.1", "Lewatan kelas B 1,3 ld.", "608", "Terverifikasi (dari 5.3)"],
        ["SNI 2847:2019", "9.6.1.2, 22.5.1.2, Tabel 21.2.1, 22.4.2.1", "As min; batas Vn geser; φ; tekan aksial.", "211; 504; 491", "Terverifikasi (dari 4.6)"],
        ["SNI 1727:2020", "Tabel 4.3-1, C3.1-1, C3.1-2", "Beban hidup dan mati tambahan.", "52; 277-278", "dari 4.2 dan 5.3"],
    ], list("clllcl"), beku=True)
    lb.kosong()
    lb.bagian("B", "Tidak ada di acuan")
    tt(lb, ["No", "Acuan", "Pasal", "Keterangan", "Hal. PDF", "Status"], [
        ["Laporan geoteknik: serakan lateral (7.13.8.3.5)", "-", "Perpindahan tanah permanen akibat serakan lateral dan tekanan tambahan pada pengikat.", "-", "belum ada di acuan"],
        ["Penurunan pile cap (tiang)", "-", "Beda penurunan pile cap Tahap 6; 2.8 hanya penurunan urugan halaman.", "-", "belum ada di acuan"],
        ["Pembagian momen kolom ke sloof pada kepala tiang sendi", "-", "Cara membagi M/2 dan M; asumsi mekanika.", "-", "belum ada di acuan"],
        ["Tata letak dinding LT1 (fasad dan timbal R-09)", "-", "Beban garis dinding pada sloof; tinggi 4,2 m dari 4.6.", "-", "belum ada di acuan"],
    ], list("clllcl"))

    # ---- Petunjuk
    lb = Lembar(wb["Petunjuk"], 1, "Petunjuk desain sloof (langkah 5.4)", [6, 130])
    lb.catatan(f"STATUS: {STATUS}. " + ket)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        "Sloof konsep 400 × 800, sisi atas = sisi atas pelat LT1 +12,85 (250 mm); fc' 35 MPa (S2), fy 420; selimut 50 mm bawah dan samping, 40 mm atas; D25 (D22/D29 bila perlu), sengkang D13.",
        "Tiga tipe: SL-1 sloof dalam, SL-2 sloof tepi (dinding fasad), SL-3 sloof as 10 di panel MRI. Gravitasi dengan PyNite balok menerus; penurunan beda 6 Ec Ie δ / L²; momen kolom bila kepala tiang sendi.",
        "Karena sloof memikul momen kolom (18.13.3.3), detail memenuhi SRPMK balok (18.6). Bila 400 × 800 tidak memenuhi, kandidat 400 × 900, 500 × 800, 500 × 900 ditabelkan tanpa memilih.",
        "Sel hijau diisi AI atas permintaan Defsa. Sel putih berisi rumus Excel (dihitung ulang dan dicocokkan dengan Python di cocokkan()).",
        "Lembar: Ringkasan; Gaya Ikat; Beban; Lentur Gravitasi; Penurunan Beda; Momen Kolom; Desain Sloof; Sensitivitas; Kapasitas; Ujung Sloof; Jarak MRI; Cek Silang T-93; Acuan.",
    ])], rata=list("cl"))

    for ws_ in wb:   # sheet berisi beberapa tabel berbeda: ulang kepala saat cetak menyesatkan
        if ws_.title not in ("Petunjuk",):
            ws_.print_title_rows = None
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


def cocokkan(berkas=BERKAS):
    """Hitung ulang di Excel, lalu bandingkan rumus dengan Python. Kembalikan (ok, pesan)."""
    from format_dokumen import hitung_ulang_excel
    ok, err = hitung_ulang_excel(berkas)
    if not ok:
        return False, f"Excel tidak bisa menghitung ulang: {err[:120]}"
    r = hitung()
    wb = openpyxl.load_workbook(berkas, data_only=True)
    pesan, n_cek = [], 0
    for nama, rows in semua_baris(r).items():
        ws = wb[nama]
        for rw in rows:
            if rw["py"] is None:
                continue
            x = None
            for row in ws.iter_rows():
                for c in row:
                    if c.value == rw["label"]:
                        x = ws.cell(c.row, c.column + 1).value
            n_cek += 1
            if x is None or abs(x - rw["py"]) > max(1e-9, abs(rw["py"]) * 1e-6):
                pesan.append(f"{nama}/{rw['label']}: Excel {x} vs Python {rw['py']}")
    ws = wb["Cek Silang T-93"]
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and len(c.value) > 3 and c.value[0] == "(" and c.value[1] in "abcd" and c.value[2] == ")":
                st = ws.cell(c.row, c.column + 5).value
                n_cek += 1
                if st != "Lolos":
                    pesan.append(f"T-93 {c.value}: status {st}")
    return not pesan, "; ".join(pesan) or f"semua {n_cek} rumus/cek Excel cocok dengan Python"


def ke_pdf(berkas=BERKAS, pdf=None):
    return mri.ke_pdf(berkas, pdf)


# ------------------------------------------------------------------ ringkasan .md
def _md_baris(rows, n=4):
    return "\n".join("| " + " | ".join(str(c) for c in a[:n]) + " |" for a in rows)


def buat_md(keluar=KELUAR / "5.4 Desain Sloof.md"):
    r = hitung()
    gi, mk, x3 = r["gi"], r["mk"], r["t93"]
    d1, d2, d3, k9, j1 = _ketentuan(r)
    judul = f"5.4 Desain Sloof ({'disetujui Defsa ' + KEPUTUSAN.split(':')[0] if KEPUTUSAN else STATUS})"
    ab = x3["a"], x3["b"], x3["c"], x3["d"]
    sel = lambda x, y: idn(abs(y / x - 1) * 100, 2)   # noqa: E731
    me = mk["me"]
    ft = d2["atas"]["As"] + d2["bawah"]["As"]
    teks = f"""# {judul}

Disusun AI 21 Nov 2026. Data simulasi. Rincian angka di `5.4 Desain Sloof.xlsx` (`skrip/tahap5_sloof.py`, uji `tests/test_tahap5_sloof.py`).
Beban pelat dari 5.3, dinding dari 4.2/4.6, gaya kolom dasar dari 4.7 (kolom tangki opsi B dari 5.1), balok menerus PyNite dari 4.6.

## Acuan (halaman = nomor halaman PDF)

SNI 1726:2019 Pasal 7.13.7.2 (hal 104-105) pengikat fondasi KDS D; 7.13.8.3.5 (hal 109) serakan lateral; Tabel 22 (hal 107) batas beda penurunan.
SNI 2847:2019 Pasal 5.3.6 (hal 108) faktor T ≥ 1,0; Tabel 6.6.3.1.1(a) (hal 125) balok 0,35 Ig; 18.13.3.1-18.13.3.3 (hal 449) sloof; 18.6.3 (hal 400-401),
18.6.4 (hal 402), 18.6.5 (hal 403) detail balok SRPMK; 18.8.5.1 (hal 418) ldh; Tabel 25.4.2.2 dan 25.4.2.4 (hal 588, 590) ld; 25.2.1 (hal 581) spasi.
Pasal yang tidak ada di acuan ditulis "belum ada di acuan".

## Sistem dan asumsi

Sloof 400 × 800 di semua as (grid 8 × 8 m), sisi atas = sisi atas pelat LT1 +12,85 (250 mm). fc' 35 MPa (S2), fy 420, Ec = {idn(EC, 0)} MPa. Selimut 50 mm ke sengkang
di bawah dan samping, 40 mm di atas [Asumsi 5.4]; D25 (D22/D29 bila perlu), sengkang D13. Tiga tipe: **SL-1** sloof dalam (pelat dua sisi, beban garis timbal R-09
{idn(W_R09, 2)} kN/m' dipasang konservatif), **SL-2** sloof tepi (pelat satu sisi + dinding fasad {idn(W_FASAD, 2)} kN/m' = {idn(Q_DL, 3)} kPa × {idn(H_DINDING, 1)} m, dari 4.6),
**SL-3** sloof as 10 (x 84) dengan panel MRI D {idn(D_MRI, 3)} kPa, pelindung {idn(pl_w(), 2)} kN/m' (y 54-60) dan 12,0 kN di tengah D-E. As 10 adalah tepi gedung (5.3),
jadi pelatnya satu sisi (rancangan awal menyebut dua sisi). Pelat: D {idn(D_PL, 2)} kPa, Lo {idn(LO_PL, 2)} kPa, qu {idn(QU_PL, 3)} kPa.

## Gaya ikat (SNI 1726:2019 7.13.7.2)

Ftie = 0,10 SDS Pu, SDS 0,386; Pu = 1,4D atau 1,2D + 1,6L terbesar di kedua ujung sloof.

| Kelompok kolom | n | Pu (kN) | Ftie (kN) |
|---|---|---|---|
{_md_baris([[b['kel'] + ' (b ' + idn(b['b'] * 1000, 0) + ' mm)', b['n'], idn(b['pu'], 0), idn(b['ftie'], 1)] for b in gi['kelompok']])}

Ftie maksimum {idn(gi['ftie_maks'], 1)} kN. φTn SL-2 400 × 800 = 0,9 × {idn(ft, 0)} × 420 = {idn(0.9 * ft * FY / 1000, 0)} kN: rasio {idn(gi['ftie_maks'] / (0.9 * ft * FY / 1000), 3)};
φPn tekan {idn(d2['phiPn_tekan'], 0)} kN. Ftie tidak menentukan. Gaya tambahan serakan lateral (7.13.8.3.5): **data belum ada** (menunggu geoteknik dan Tahap 6).

## Beban dan lentur gravitasi (400 × 800)

Balok menerus PyNite 5 bentang (SL-3 6 bentang), beban pelat segitiga q L/2, pola beban hidup, pegas putar ujung = kolom 750 ({idn(K_ROT, 0)} kNm/rad).

| Tipe | Mu- grav. (kNm) | Mu+ grav. (kNm) | Vu grav. (kN) |
|---|---|---|---|
{_md_baris([[t, idn(d_(r, t)['g']['neg_g'], 1), idn(d_(r, t)['g']['pos_g'], 1), idn(d_(r, t)['g']['v_g'], 1)] for t in TIPE])}

## Penurunan beda (SNI 1726:2019 Tabel 22; SNI 2847:2019 5.3.6)

δ = 0,002 L = 16 mm [Asumsi: batas Tabel 22 kategori risiko IV, gedung > 1 tingkat; 2.8 hanya memberi penurunan urugan halaman 0,15-1,18 m; tiang Tahap 6 memperbarui].
M = 6 Ec Ie δ / L², Ie = 0,35 Ig: 400 × 800 **{idn(d1['T'], 1)} kNm** (dengan Ig {idn(momen_penurunan(0.4, 0.8, DELTA_16, ie=1.0), 1)} kNm); δ 8 mm: {idn(momen_penurunan(0.4, 0.8, DELTA_8), 1)} kNm;
400 × 900: {idn(momen_penurunan(0.4, 0.9, DELTA_16), 1)} kNm. V = 2M/L = {idn(2 * d1['T'] / L, 1)} kN. Kombinasi 1,2D + 1,6L + 1,0T: rasio SL-1 {idn(d1['kasus']['G+T']['r_neg'], 2)}, tidak menentukan.

## Momen kolom bila kepala tiang dianggap sendi

Momen dasar kolom LT1 kombinasi gempa (ρ 1,3 dan Ev termasuk, 4.7): kolom dalam M/2 ke tiap sloof, kolom tepi M ke satu sloof; V = 2M/L. Inti tidak dibagi ke sloof [Asumsi].

| Kelompok | Mx maks (kNm) | My maks (kNm) | M kolom dalam (kNm) | M kolom tepi (kNm) |
|---|---|---|---|---|
{_md_baris([[b['kel'], idn(b['Mx'], 1), idn(b['My'], 1), idn(b['M_dalam'], 1), idn(b['M_tepi'], 1)] for b in mk['kelompok']], 5)}

Momen ujung sloof yang menentukan: SL-1 **{idn(me['SL-1'], 1)}**, SL-2 {idn(me['SL-2'], 1)}, SL-3 {idn(me['SL-3'], 1)} kNm. Kolom tangki opsi B memakai momen 4.7 kolom 800/950 (konservatif untuk 750).

## Desain sloof (400 × 800; δ 16 mm; T tidak di kombinasi gempa)

SNI 2847:2019 18.13.3.3: sloof yang memikul momen kolom memenuhi 18.6 (ρ ≤ 0,025, M+ ≥ 0,5 M-, sengkang pengekang di 2h, Ve dari Mpr 1,25 fy, Vc = 0). Gaya tarik ikat ditambahkan ke As.

| Tipe | Mu- / Mu+ maks (kNm) | Ve (kN) | Tulangan atas / bawah | ρ atas (%) | Rasio | Sengkang | Status |
|---|---|---|---|---|---|---|---|
{chr(10).join(f"| {t} | {idn(maks_kasus(d_(r, t), 'neg'), 0)} / {idn(maks_kasus(d_(r, t), 'pos'), 0)} | {idn(d_(r, t)['Ve'], 0)} | {tul_s(d_(r, t)['atas'])} ({d_(r, t)['atas']['lapis']} lapis) / {tul_s(d_(r, t)['bawah'])} | {pct(d_(r, t)['atas']['rho'])} | {rasio_s(d_(r, t))} | D{d_(r, t)['ds']}-{idn(d_(r, t)['s_ujung'] * 1000, 0)} / {idn(d_(r, t)['s_tengah'] * 1000, 0)} | {status_s(d_(r, t))} |" for t in TIPE)}

Kombinasi menentukan: gempa (SL-1 Mu- {idn(d1['kasus']['E']['neg'], 0)} kNm = gravitasi seismik {idn(d1['g']['neg_s'], 0)} + momen kolom {idn(d1['ME'], 0)}).

**Kandidat ukuran** (rasio, ρ atas, tulangan; tanpa memilih):

| Tipe | Ukuran | Tulangan atas / bawah | ρ atas (%) | Lapis | Rasio | Status |
|---|---|---|---|---|---|---|
{chr(10).join(f"| {t} | {idn(b * 1000, 0)} × {idn(h * 1000, 0)} | {tul_s(r['desain'][(t, b, h)]['atas'])} / {tul_s(r['desain'][(t, b, h)]['bawah'])} | {pct(r['desain'][(t, b, h)]['atas']['rho'])} | {r['desain'][(t, b, h)]['atas']['lapis']} | {rasio_s(r['desain'][(t, b, h)])} | {status_s(r['desain'][(t, b, h)])} |" for t in TIPE for (b, h) in UKURAN)}

**Pengaruh δ dan T** (400 × 800 / 400 × 900, tulangan atas):

| Tipe | Ukuran | δ 16, T tidak di gempa | δ 16, T di gempa | δ 8, T tidak di gempa | δ 8, T di gempa |
|---|---|---|---|---|---|
{chr(10).join(f"| {t} | {idn(b * 1000, 0)} × {idn(h * 1000, 0)} | " + " | ".join(f"{tul_s(r['sensitivitas'][(b, h, dl, tg)][t]['atas'])} ({pct(r['sensitivitas'][(b, h, dl, tg)][t]['atas']['rho'], 1)} %){'' if r['sensitivitas'][(b, h, dl, tg)][t]['ok'] else ' tidak memenuhi'}" for dl, tg in ((DELTA_16, False), (DELTA_16, True), (DELTA_8, False), (DELTA_8, True))) + " |" for t in TIPE for (b, h) in UKURAN[:2])}

**Kepala tiang jepit** (tanpa momen kolom ke sloof): SL-1 400 × 800 menjadi {tul_s(j1['atas'])} atas / {tul_s(j1['bawah'])} bawah (ρ {pct(j1['atas']['rho'])} %), {status_s(j1)}.

## Ujung sloof (D29, SNI 2847:2019 18.8.5.1; 25.4.2)

| Jenis ujung | ldh / ld perlu (mm) | Tersedia (mm) | Hasil |
|---|---|---|---|
{_md_baris(teks_ujung(r), 4)}

## Jarak ke isocenter MRI (80,5; 57,0)

| Sloof | Jarak muka sloof terdekat (m) | Syarat |
|---|---|---|
{chr(10).join(f"| {m['nama']} | {idn(m['jarak'], 2)} | > 1,0 m: {'memenuhi' if m['jarak'] > 1.0 else 'tidak'} |" for m in r['mri'])}

Semua > 1,0 m: sloof baja karbon biasa. Zona tahan karat x 79,5-81,5 / y 56-58 tidak tersentuh sloof.

## Cek silang T-93

| Cek | Cara 1 | Cara 2 | Selisih | Toleransi |
|---|---|---|---|---|
| (a) Ftie maks | tangan {idn(ab[0]['tangan'], 2)} kN | skrip {idn(ab[0]['skrip'], 2)} kN | {sel(ab[0]['tangan'], ab[0]['skrip'])} % | {idn(TOL['a'], 1)} % |
| (b) momen ujung jepit-jepit SL-1 beban D | tangan {idn(ab[1]['tangan'], 2)} kNm | PyNite {idn(ab[1]['pynite'], 2)} kNm | {sel(ab[1]['tangan'], ab[1]['pynite'])} % | {idn(TOL['b'], 1)} % |
| (c) momen penurunan δ 16 mm | tangan {idn(ab[2]['tangan'], 2)} kNm | PyNite {idn(ab[2]['pynite'], 2)} kNm | {sel(ab[2]['tangan'], ab[2]['pynite'])} % | {idn(TOL['c'], 1)} % |
| (d) φMn atas SL-2 | rumus sendiri {idn(ab[3]['sendiri_neg'], 2)} kNm | concreteproperties {idn(ab[3]['cp_neg'], 2)} kNm | {sel(ab[3]['sendiri_neg'], ab[3]['cp_neg'])} % | {idn(TOL['d'], 1)} % |
| (d) φMn bawah SL-2 | rumus sendiri {idn(ab[3]['sendiri_pos'], 2)} kNm | concreteproperties {idn(ab[3]['cp_pos'], 2)} kNm | {sel(ab[3]['sendiri_pos'], ab[3]['cp_pos'])} % | {idn(TOL['d'], 1)} % |

(b) Pada garis menerus, momen tumpuan dalam lebih kecil dari jepit-jepit karena momen terbagi ke bentang tetangga; perbandingan memakai satu bentang jepit-jepit agar setara dengan rumus.
Cek tarik bersamaan lentur: φMn atas dengan Ftie {idn(ab[3]['cp_tarik'], 1)} kNm (concreteproperties, kedua lapis; tanpa Ftie {idn(ab[3]['cp_neg_penuh'], 1)} kNm).

## Data yang masih kurang

1. Serakan lateral dan penurunan beda pile cap (geoteknik, Tahap 6): δ 16 mm hanya batas SNI 1726 Tabel 22, bukan hasil hitungan.
2. Tata letak dinding LT1 (fasad 4,2 m dari 4.6; timbal R-09 letak sebenarnya); beban garis dan lokasi di Tahap 7.
3. Kekakuan tiang/pile cap (kepala tiang sendi atau jepit) dan ukuran pile cap inti untuk angkur sloof di inti.
4. Panjang dinding pelindung di as 10 yang menumpu langsung pada sloof (7,17 kN/m' dari data 5.3).

## Yang perlu diputuskan Defsa

1. **Ukuran sloof** bila 400 × 800 tidak memenuhi pada SL-1: usulan AI SL-1 400 × 900 ({tul_s(k9['atas'])} atas, ρ {pct(k9['atas']['rho'])} %, {k9['atas']['lapis']} lapis); SL-2 dan SL-3 cukup 400 × 800.
2. **δ desain**: 16 mm (0,002 L) atau 8 mm (0,001 L): usulan AI 16 mm sampai penurunan tiang Tahap 6 ada; gempa menentukan, jadi tulangan tidak berubah antara 16 dan 8 mm bila T tidak di gempa.
3. **T di kombinasi gempa**: usulan AI tidak dimasukkan (T bekerja jangka panjang); bila dimasukkan, SL-1 400 × 900 tidak lagi memenuhi (lihat tabel pengaruh).
4. **Kepala tiang sendi atau jepit**: sendi membuat momen kolom masuk ke sloof dan menentukan SL-1; usulan AI desain dengan sendi (aman) sampai Tahap 6.
5. Tinggi dinding fasad 4,2 m dan beban R-09 pada sloof dalam (konservatif).

(Usulan AI berdasar angka di atas; keputusan di tangan Defsa.)
"""
    if KEPUTUSAN:
        teks += f"\n## Keputusan Defsa\n\n{KEPUTUSAN}\n"
    else:
        teks += "\n## Keputusan Defsa\n\n(belum diisi)\n"
    keluar.write_text(teks, encoding="utf-8")
    return keluar


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(buat_excel())
    print(cocokkan())
    print(buat_md())
