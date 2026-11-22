"""Tahap 5 langkah 5.6: penerusan kolom dan inti ke pile cap, tabel reaksi ke pondasi untuk Tahap 6.

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (21 Nov 2026); disetujui Defsa 21 Nov 2026.
Kunci jawaban tidak dibuka. Gaya dasar kolom dari `tahap4_kolom` (4.7; kasus E = model dengan inti, kasus R rangka saja TIDAK dipakai), gaya dasar
inti dari `tahap4_dinding` (4.8), ukuran dan beban kolom tangki opsi B dari `tahap5_tangki` (5.1), pelat LT1 dari `tahap5_pelat_lt1` (5.3),
sloof dari `tahap5_sloof` (5.4), pit lift dari `tahap5_pit_lift` (5.5).

Acuan (halaman = nomor halaman PDF di acuan/privat, diverifikasi dengan pypdf 21 Nov 2026):
- SNI 1726:2019 Pasal 4.2.2.3 (hal 38-39) kombinasi seismik kuat; Pasal 4.2.3.1 (hal 39) dan 4.2.3.3 (hal 40) kombinasi tegangan izin; Pasal 7.4.2
  (hal 76-77) Ev = 0,2 SDS D dan Eh = rho QE; Pasal 7.5.3 (hal 79) kombinasi ortogonal 100 % + 30 %; Pasal 7.13.4 (hal 102) reduksi guling 25 %
  (TIDAK dipakai); Pasal 7.13.7.2 (hal 104-105) pengikat fondasi.
- SNI 2847:2019 Pasal 16.3.1.1-16.3.1.2 (hal 310), 16.3.3.4 dan 16.3.3.5 (hal 311), 16.3.4.1-16.3.4.2 dan 16.3.5.1 (hal 312), 16.3.5.2 (hal 313):
  sambungan ke fondasi; Pasal 18.13.2.1-18.13.2.4 (hal 448): kolom dan dinding di pile cap; Pasal 18.13.3 (hal 449); Pasal 22.8.3.2 (hal 540): tumpu;
  Pasal 25.4.2 (hal 587-590), 25.4.3 (hal 591), 25.4.9 (hal 604): panjang penyaluran; Pasal 18.8.5.1 (hal 418).
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
from shapely.geometry import LineString, box

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_beban as tb  # noqa: E402
import tahap4_dinding as td  # noqa: E402
import tahap4_kolom as kl  # noqa: E402
import tahap4_model as tm  # noqa: E402
import tahap5_mri as mri  # noqa: E402
import tahap5_pelat_lt1 as pl  # noqa: E402
import tahap5_pit_lift as pit  # noqa: E402
import tahap5_sloof as sl  # noqa: E402
import tahap5_tangki as tn  # noqa: E402
import tahap5_telaah as ts  # noqa: E402
from tahap5_mri import R, idn  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "05 Struktur Tengah"
BERKAS = KELUAR / "5.6 Reaksi ke Pondasi.xlsx"
LABEL = mri.LABEL
STATUS = "disetujui Defsa 21 Nov 2026"
LABEL_AI = f"DIISI AI ATAS PERMINTAAN DEFSA (21 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."
KEPUTUSAN = ("21 Nov 2026: semua usulan AI disetujui. (1) Reaksi Tahap 6 memakai Pmax/Pmin dengan ΔP sloof. (2) Pile cap inti tebal 1.200 mm, denah di Tahap 6. "
             "(3) Amplop K1 dan K2. (4) Kasus R tidak dipakai untuk reaksi. (5) Tumpang tributari inti 4.8 dipertahankan (konservatif). "
             "(6) Sloof SL-1 as 6 di dalam inti lift dihapus; kolom (52,35) dan (52,43) masuk pile cap inti di Tahap 6. "
             "(7)-(8) Kolom tangki opsi B didesain ulang (P-M, kolom kuat balok lemah, stek) sebagai tambahan 5.6a sebelum Tahap 6. "
             "(9) Reaksi memakai kasus E; desain sloof tetap 5.4. "
             "(10) 21 Nov 2026 (5.6a): kolom tangki 800 seragam; reaksi diperbarui. Langkah berikutnya: 5.7 model BIMCraft.")

FC, FY, FYT = kl.FC, kl.FY, 420.0
GC = tb.GAMMA_C
SDS = tb.SDS
RHO = tb.RHO
EV = 0.2 * SDS                                  # SNI 1726:2019 Pasal 7.4.2.2 (hal 77)
HALAMAN = 12.05                                  # m, kepala pile cap = halaman (tahap3_bim.HALAMAN 12050 mm)
T_CAP = 1.200                                    # m [Asumsi 3.7: tahap3_bim.TEBAL_CAP]
BAWAH_PELAT = pl.LT1 - pl.H if hasattr(pl, "LT1") else 12.85 - pl.H   # 12,60 m, sisi bawah pelat LT1
LT1 = 12.85
SEL_CAP, DB_CAP = 0.075, 0.032                   # m, selimut beton pada tanah (Tabel 20.6.1.3.1) dan tulangan bawah cap D32 [Asumsi 5.6]
L = 8.0
TOL = {"a": 5.0, "b": 1.0, "c": 0.5, "d": 0.5}   # % (T-95), ditetapkan sebelum membandingkan
KASUS = ("D", "L", "EX+", "EX-", "EY+", "EY-")
UKURAN_SLOOF = {"SL-1": (0.40, 0.90), "SL-2": (0.40, 0.80), "SL-3": (0.40, 0.80)}   # keputusan Defsa 5.4
MRI_PANEL = (76.0, 51.0, 84.0, 59.0)             # x0, y0, x1, y1 panel MRI 9-10/D-E (5.3)
T_PIT = {"L-1..4": 0.45, "L-5..6": pit.TS0, "L-7": pit.TS0}   # keputusan Defsa 5.5 (21 Nov 2026)
BALOK_PG = (0.40, 0.80)                          # balok penggantung L-7 (5.5)
NAMA_X, NAMA_Y = ts.NAMA_X, ts.NAMA_Y
GX, GY = tb.GRID_X, tb.GRID_Y


# ================================================================== data mentah (analisis OpenSees, K1 dan K2)
def _kolom_mentah(h):
    g = h["gaya"]
    out = {}
    for k in h["kolom"]:
        if k[0] == "LT2":
            out[(k[1], k[2])] = {c: np.array(kl.ujung(g[c][k])[0], dtype=float) for c in KASUS}
    return out


def _inti_mentah(hd, konfig):
    gr = td.gravitasi(konfig)
    out = {}
    for (nama, lv), pdpl in gr.items():
        if lv != "LT2":
            continue
        e = {c: np.array(hd["gaya"][c[1:]][(nama, lv)][0], dtype=float) for c in KASUS[2:]}
        d = np.zeros(6)
        d[0] = pdpl[0]
        lv_ = np.zeros(6)
        lv_[0] = pdpl[1]
        out[nama] = {"D": d, "L": lv_, **e}
    return out


@functools.lru_cache(maxsize=1)
def data_mentah():
    """Satu kali jalan (lama, ~10 menit): gaya dasar kolom (kasus E) dan inti, K1 dan K2; desain tulangan dasar 4.7 dan 4.8; kolom tangki opsi B (5.1).
    Hasil dapat disimpan ke berkas pickle lewat variabel lingkungan PENERUSAN_CACHE (shortcut hanya untuk pengembangan)."""
    cache = os.environ.get("PENERUSAN_CACHE")
    if cache and Path(cache).exists():
        return pickle.load(open(cache, "rb"))
    d = tn.hasil_46_47()
    hk = {"K2": kl.analisis("K2", d["um"]), "K1": kl.analisis("K1", d["um"])}
    rk = kl.rancang()   # = rancang_dari(hk, balok_rancang()); versi tanpa argumen ter-cache di disk
    hd = {"K2": td.analisis("K2"), "K1": td.analisis("K1")}
    rd = td.rancang()   # = rancang([K2, K1]); ter-cache di disk
    th = tn.hitung()
    tul_k = {}
    for x in rk["kelompok"]:
        if x["kelompok"].endswith("LT2"):
            gs = x["geser"]
            tul_k[x["kelompok"].replace(" LT2", "")] = {
                "b": float(x["b"]), "m": int(x["m"]), "db": int(x["db"]), "n_batang": int(x["n_batang"]), "Ast": float(x["Ast"]),
                "rho": float(x["rho"]), "s_lo": float(gs["s_lo"]), "lo": float(gs["lo"]), "kaki": int(gs["kaki"]), "Ash": float(gs["Ash"]),
                "s_luar": float(gs["s_luar"]), "Ve": float(gs["Ve"]), "n": int(x["n"])}
    tul_i = {}
    for x in rd["kelompok"]:
        if x["lv"] != "LT2":
            continue
        tul_i[x["kelompok"]] = {"tipe": x["tipe"], "anggota": [k[0] for k in x["anggota"]], "tul": tuple(x["tul"]), "rho_l": float(x["rho_l"]),
                                "horiz": tuple(x["horiz"]), "leg": float(x["batas"]["leg"]), "trans": dict(x["batas"]["trans"]),
                                "perlu_batas": bool(x["batas"]["perlu"])}
    kb = th["kolom_b"]
    out = {"kolom": {k: _kolom_mentah(h) for k, h in hk.items()}, "inti": {k: _inti_mentah(h, k) for k, h in hd.items()},
           "kolom_meta": {k: {"b": float(v["b"]), "kel": v["kelompok"].replace(" LT2", "")} for k, v in
                          {(c[1], c[2]): {"b": hk["K2"]["kolom"][c]["b"], "kelompok": kl.kelompok_kolom(*c, hk["K2"]["kolom"][c]["b"])}
                           for c in hk["K2"]["kolom"] if c[0] == "LT2"}.items()},
           "tangki": {k: {"b_B": float(v["b_B"]), "b_A": float(v["b_A"]), "dD": float(th["w_b"][k] - th["w_a"][k])} for k, v in kb.items()},
           "statika": {k: {c: tuple(map(float, h["statika"][c])) for c in ("D", "L")} for k, h in hk.items()},
           "tul_kolom": tul_k, "tul_inti": tul_i}
    if cache:
        pickle.dump(out, open(cache, "wb"))
    return out


# ================================================================== kombinasi (SNI 1726:2019 4.2.2.3, 4.2.3.3, 7.4.2, 7.5.3)
def kombinasi_daftar(jenis):
    """Daftar kombinasi berurutan sama untuk semua titik: (nama, cD, cL, cE, kunci E), E = RHO (sg Ea + 0,3 so Eo).
    jenis 'ult': kekuatan (4.2.2.1 no. 1-2 dan 4.2.2.3 no. 6-7); 'lay': tegangan izin (4.2.3.1 no. 1-2 dan 4.2.3.3 no. 8-10)."""
    if jenis == "ult":
        out = [("1,4 D", 1.4, 0.0, 0.0, None), ("1,2 D + 1,6 L", 1.2, 1.6, 0.0, None)]
    else:
        out = [("D", 1.0, 0.0, 0.0, None), ("D + L", 1.0, 1.0, 0.0, None)]
    for a, o in (("X", "Y"), ("Y", "X")):
        for s1 in "+-":
            for s2 in "+-":
                for sg in (1, -1):
                    for so in (1, -1):
                        ke = (f"E{a}{s1}", f"E{o}{s2}", sg, so)
                        if jenis == "ult":
                            out += [("(1,2 + 0,2 SDS) D + L + E", 1.2 + EV, 1.0, RHO, ke), ("(0,9 - 0,2 SDS) D + E", 0.9 - EV, 0.0, RHO, ke)]
                        else:
                            out += [("(1,0 + 0,14 SDS) D + 0,7 E", 1.0 + 0.7 * EV, 0.0, 0.7 * RHO, ke),
                                    ("(1,0 + 0,105 SDS) D + 0,75 L + 0,525 E", 1.0 + 0.525 * EV, 0.75, 0.525 * RHO, ke),
                                    ("(0,6 - 0,14 SDS) D + 0,7 E", 0.6 - 0.7 * EV, 0.0, 0.7 * RHO, ke)]
    return out


@functools.lru_cache(maxsize=2)
def _matriks(jenis):
    kd = kombinasi_daftar(jenis)
    return kd, np.array([k[1] for k in kd]), np.array([k[2] for k in kd]), np.array([k[3] for k in kd])


def hitung_komb(raw, jenis, d_tambah=0.0, l_tambah=0.0):
    """raw {kasus: vektor}; kembalikan (F (n_komb, n), E_unit (n_komb, n)). Tambahan d_tambah dan l_tambah (kN) hanya ke P (indeks 0)."""
    kd, cd, cl, ce = _matriks(jenis)
    n = len(raw["D"])
    d, l_ = raw["D"].astype(float).copy(), raw["L"].astype(float).copy()
    d[0] += d_tambah
    l_[0] += l_tambah
    eu = np.zeros((len(kd), n))
    for i, k in enumerate(kd):
        if k[4] is not None:
            ea, eo, sg, so = k[4]
            eu[i] = sg * raw[ea] + 0.3 * so * raw[eo]
    return cd[:, None] * d + cl[:, None] * l_ + ce[:, None] * eu, eu


# ================================================================== titik reaksi
def label_as(x, y):
    return f"{NAMA_X[GX.index(x)]}/{NAMA_Y[GY.index(y)]}"


def kotak_inti():
    """{nama: (x0, y0, x1, y1, luas as)} kotak sumbu dinding inti; bukaan lif L-1..4 dicatat terpisah."""
    out = {}
    for nama, (cx, cy) in tm.PUSAT_INTI.items():
        dx, dy = td.DIM["L" if nama.startswith("Inti") else "T"]
        out[nama] = (cx - dx / 2, cy - dy / 2, cx + dx / 2, cy + dy / 2, dx * dy)
    return out


def id_inti(nama):
    return "INTI-LIF" if nama.startswith("Inti") else "INTI-T" + nama.split()[1][1:] + "/" + nama.split()[2][1:]


def bukaan_lif():
    p = pit.data_lift()["L-1..4"]
    return p["a"] * p["b"]


def luas_trib(x, y):
    """(luas pelat umum PL-1, luas di panel MRI) milik kolom (x, y): persegi 8 x 8 di sekitar titik dipotong podium, dikurangi kotak inti, dan
    dipisah menurut panel MRI [Asumsi 5.6: tributari]."""
    g = box(x - L / 2, y - L / 2, x + L / 2, y + L / 2).intersection(tb.PODIUM)
    for v in kotak_inti().values():
        g = g.difference(box(*v[:4]))
    mri_ = g.intersection(box(*MRI_PANEL)).area
    return g.area - mri_, mri_


def _bagi_dua(x, a, b):
    """Aturan tuas: beban di koordinat x antara a dan b: (bagian ke a, bagian ke b)."""
    return (b - x) / (b - a), (x - a) / (b - a)


def _tambah(dic, kunci, d=0.0, l_=0.0, kat=None):
    e = dic.setdefault(kunci, {"D": 0.0, "L": 0.0, "kat": {}})
    e["D"] += d
    e["L"] += l_
    if kat:
        e["kat"][kat] = e["kat"].get(kat, 0.0) + d + l_
    return e


def tambahan(kolom_xy, b_kolom):
    """Beban tambahan struktur tengah per titik (kN) {kunci: {'D', 'L', 'kat': {kategori: kN}}}. Kunci kolom (x, y), inti nama.
    Kategori: pelat, sloof, stek, pit, mri."""
    out = {}
    ada = set(kolom_xy)
    dpl, lpl, dm, lm = sl.D_PL, sl.LO_PL, sl.D_MRI, sl.LO_MRI
    # ---- pelat LT1 (tributari); pelat di dalam inti ke inti
    for xy in kolom_xy:
        a_u, a_m = luas_trib(*xy)
        _tambah(out, xy, d=dpl * a_u + dm * a_m, l_=lpl * a_u + lm * a_m, kat="pelat")
    for nama, v in kotak_inti().items():
        a = v[4] - (bukaan_lif() if nama.startswith("Inti") else 0.0)
        _tambah(out, nama, d=dpl * a, l_=lpl * a, kat="pelat")
        # stek dinding inti dari sisi bawah pelat ke kepala cap
        kel = [k[1] for k in tb.INTI if k[0] == nama][0]
        _tambah(out, nama, d=GC * tb.DINDING_T * kel * (BAWAH_PELAT - HALAMAN), kat="stek")
    # ---- stek kolom
    for xy in kolom_xy:
        _tambah(out, xy, d=GC * b_kolom[xy] ** 2 * (BAWAH_PELAT - HALAMAN), kat="stek")
    # ---- sloof: berat sendiri di bawah pelat, dinding fasad (tepi), R-09 (dalam)
    for (x, y), (x2, y2), tipe in segmen_sloof(ada):
        b, h = UKURAN_SLOOF[tipe]
        w = GC * b * (h - sl.H_PELAT) + (sl.W_R09 if tipe == "SL-1" else sl.W_FASAD)
        for k in ((x, y), (x2, y2)):
            _tambah(out, k, d=w * L / 2, kat="sloof")
    # ---- dinding pelindung MRI dan magnet (5.3, 5.4)
    mi = mri.baca_masukan()
    wp = sl.pl_w()
    utara, timur = mi["dinding"]
    for (xk, yk), f in zip(((76.0, 51.0), (84.0, 51.0), (76.0, 59.0), (84.0, 59.0)), (0.25,) * 4):
        _tambah(out, (xk, yk), d=sl.P_MAGNET * f, kat="mri")
    for (y0, y1) in ((54.0, 59.0), (59.0, 60.0)):         # dinding timur di sloof as 10 (x 84), y 54-60
        a, b = (51.0, 59.0) if y1 <= 59.0 else (59.0, 67.0)
        pa, pb = _bagi_dua((y0 + y1) / 2, a, b)
        w = wp * (y1 - y0)
        _tambah(out, (84.0, a), d=w * pa, kat="mri")
        _tambah(out, (84.0, b), d=w * pb, kat="mri")
    w_u = wp * utara                                        # dinding utara di y 60, resultan x 80,5 [Asumsi 5.6]
    xa, xb = _bagi_dua(80.5, 76.0, 84.0)
    ya, yb = _bagi_dua(60.0, 59.0, 67.0)
    for (xk, fx) in ((76.0, xa), (84.0, xb)):
        for (yk, fy) in ((59.0, ya), (67.0, yb)):
            _tambah(out, (xk, yk), d=w_u * fx * fy, kat="mri")
    # ---- pit lift (5.5)
    dl = pit.data_lift()
    for kode in ("L-1..4", "L-5..6", "L-7"):
        p = dl[kode]
        w = pit.angkat(p, T_PIT[kode], pit.Q100)["W"]
        pb = p["jumlah"] * (p["p_kereta"] + p["p_imbang"])
        if kode == "L-1..4":
            _tambah(out, [n for n in kotak_inti() if n.startswith("Inti")][0], d=w, l_=pb, kat="pit")
        elif kode == "L-5..6":
            cx, cy = p["pusat"]
            a, b = max(g for g in GX if g <= cx), min(g for g in GX if g >= cx)
            pa, pb_ = _bagi_dua(cx, a, b)
            yg = min(GY, key=lambda g: abs(g - cy))             # sloof as C (y 43) berimpit dengan pit
            for xg, f in ((a, pa), (b, pb_)):
                _tambah(out, (xg, yg), d=w * f, l_=pb * f, kat="pit")
        else:
            cx, cy = p["pusat"]
            wb = GC * BALOK_PG[0] * BALOK_PG[1] * L
            for yb_ in (cy - p["b"] / 2, cy + p["b"] / 2):      # dua balok penggantung sejajar X di tepi shaft [Asumsi 5.6]
                d_b, l_b = (w / 2 + wb), pb / 2                  # beban pit dan berat balok, titik di tengah bentang
                a, b = max(g for g in GY if g <= yb_), min(g for g in GY if g >= yb_)
                pa, pb_ = _bagi_dua(yb_, a, b)
                for xg in (36.0, 44.0):
                    for yg, f in ((a, pa), (b, pb_)):
                        _tambah(out, (xg, yg), d=d_b / 2 * f, l_=l_b / 2 * f, kat="pit")
    return out


def segmen_sloof(ada):
    """[((x, y), (x2, y2), tipe)] sloof antar titik kolom: SL-2 tepi (y = 27, 75 dan x = 12), SL-3 as 10 (x = 84), SL-1 lainnya (5.4)."""
    out = []
    for (x, y) in sorted(ada):
        if (x + L, y) in ada:
            out.append(((x, y), (x + L, y), "SL-2" if y in (27.0, 75.0) else "SL-1"))
        if (x, y + L) in ada:
            out.append(((x, y), (x, y + L), "SL-2" if x == 12.0 else ("SL-3" if x == 84.0 else "SL-1")))
    return out


# ================================================================== delta P sloof (kepala tiang sendi)
def delta_p(mom, ada):
    """Tambahan P (kN, tekan positif) tiap kolom dari geser sloof V = (mA + mB) / L, per kombinasi. mom {xy: (n_komb, 2)} = [Mx, My] bagian E
    (momen kolom pada node). Sloof arah X menerima My (bagian: kolom dalam 1/2, tepi 1; 5.4), arah Y menerima -Mx. Ujung kecil: -V; ujung besar: +V (arah X);
    sebaliknya untuk arah Y (keseimbangan momen sloof terhadap ujung B)."""
    n = next(iter(mom.values())).shape[0]
    dp = {xy: np.zeros(n) for xy in ada}
    for (a, b, tipe) in segmen_sloof(ada):
        if a[1] == b[1]:   # sloof sepanjang X
            ma = sl.bagi(1.0, a[0], (12.0, 84.0)) * mom[a][:, 1]
            mb = sl.bagi(1.0, b[0], (12.0, 84.0)) * mom[b][:, 1]
            v = (ma + mb) / L
            dp[a] += -v
            dp[b] += v
        else:
            ma = sl.bagi(1.0, a[1], (27.0, 75.0)) * (-mom[a][:, 0])
            mb = sl.bagi(1.0, b[1], (27.0, 75.0)) * (-mom[b][:, 0])
            v = (ma + mb) / L
            dp[a] += v
            dp[b] += -v
    return dp


# ================================================================== hitung reaksi
def _gabung(per_konfig, fungsi):
    """Amplop atas dua konfigurasi (K1, K2): fungsi(a, b) elemen-wise."""
    it = iter(per_konfig.values())
    h = next(it)
    for x in it:
        h = fungsi(h, x)
    return h


@functools.lru_cache(maxsize=1)
def hitung():
    m = data_mentah()
    kol_k = m["kolom"]
    xy = sorted(kol_k["K2"])
    b_kol = {k: m["kolom_meta"][k]["b"] for k in xy}
    kel_kol = {k: m["kolom_meta"][k]["kel"] for k in xy}
    tangki = {k: v for k, v in m["tangki"].items()}
    for k, v in tangki.items():
        b_kol[k] = v["b_B"]
        kel_kol[k] = "K-T B"
    tam = tambahan(xy, b_kol)
    titik = []
    kd_u, kd_l = _matriks("ult")[0], _matriks("lay")[0]
    mom = {kf: {} for kf in kol_k}
    res = {}
    for k in xy:
        d_tam = tam[k]["D"] + (tangki[k]["dD"] if k in tangki else 0.0)
        l_tam = tam[k]["L"]
        r = {"id": label_as(*k), "x": k[0], "y": k[1], "tipe": "kolom", "kel": kel_kol[k], "b": b_kol[k], "kat": dict(tam[k]["kat"]),
             "dD_tangki": tangki[k]["dD"] if k in tangki else 0.0}
        r["D_model"], r["L_model"] = max(kol_k[kf][k]["D"][0] for kf in kol_k), max(kol_k[kf][k]["L"][0] for kf in kol_k)
        r["D_tam"], r["L_tam"] = d_tam, l_tam
        r["raw"] = {kf: kol_k[kf][k] for kf in kol_k}
        r["Fu"], r["Fl"] = {}, {}
        for kf in kol_k:
            fu, eu_u = hitung_komb(kol_k[kf][k], "ult", d_tam, l_tam)
            fl, eu_l = hitung_komb(kol_k[kf][k], "lay", d_tam, l_tam)
            r["Fu"][kf], r["Fl"][kf] = fu, fl
        titik.append(r)
        res[k] = r
    # momen E pada node per kombinasi (untuk delta P sloof): bagian E = cE * E_unit, komponen [Mx, My]
    for kf in kol_k:
        for k in xy:
            fu = None
            for jenis in ("ult", "lay"):
                _, eu = hitung_komb(kol_k[kf][k], jenis)
                _, cd, cl, ce = _matriks(jenis)
                mom[kf].setdefault(jenis, {})[k] = ce[:, None] * eu[:, 1:3]
    dp = {}
    for kf in kol_k:
        dp[kf] = {j: delta_p(mom[kf][j], set(xy)) for j in ("ult", "lay")}
    for r in titik:
        k = (r["x"], r["y"])
        r["dP"] = {kf: {j: dp[kf][j][k] for j in ("ult", "lay")} for kf in kol_k}
    # ---- inti
    inti = []
    for nama in tm.PUSAT_INTI:
        ik = {kf: m["inti"][kf][nama] for kf in m["inti"]}
        v = kotak_inti()[nama]
        d_tam, l_tam = tam[nama]["D"], tam[nama]["L"]
        r = {"id": id_inti(nama), "nama": nama, "x": (v[0] + v[2]) / 2, "y": (v[1] + v[3]) / 2, "tipe": "inti", "kel": td.kelompok_inti(nama),
             "b": 0.0, "kat": dict(tam[nama]["kat"]), "dD_tangki": 0.0, "D_model": max(ik[kf]["D"][0] for kf in ik),
             "L_model": max(ik[kf]["L"][0] for kf in ik), "D_tam": d_tam, "L_tam": l_tam, "raw": ik, "Fu": {}, "Fl": {}}
        for kf in ik:
            r["Fu"][kf] = hitung_komb(ik[kf], "ult", d_tam, l_tam)[0]
            r["Fl"][kf] = hitung_komb(ik[kf], "lay", d_tam, l_tam)[0]
        r["dP"] = {kf: {j: np.zeros(len(kd_u if j == "ult" else kd_l)) for j in ("ult", "lay")} for kf in ik}
        inti.append(r)
    semua = titik + inti
    for r in semua:
        r["amp"] = amplop(r)
    return {"titik": titik, "inti": inti, "semua": semua, "tam": tam, "mentah": m, "kd": {"ult": kd_u, "lay": kd_l},
            "mom": mom, "t95": cek_t95(titik, inti, tam, m)}


def kombinasi_ce(jenis):
    return _matriks(jenis)[3]


def amplop(r):
    """Amplop K1 dan K2 per titik. Kolom: kepala tiang sendi (M ke pile cap = 0), P dengan dan tanpa delta P sloof. Inti: P, M, V, T penuh."""
    kd_u, kd_l = _matriks("ult")[0], _matriks("lay")[0]
    out = {}
    for jenis, kd in (("ult", kd_u), ("lay", kd_l)):
        F = {kf: (r["Fu"] if jenis == "ult" else r["Fl"])[kf] for kf in r["Fu"]}
        p0 = np.concatenate([F[kf][:, 0] for kf in F])
        dp = np.concatenate([r["dP"][kf][jenis] for kf in F])
        nm = np.concatenate([[k[0] for k in kd] for _ in F])
        kf_ = np.concatenate([[kf] * len(kd) for kf in F])
        vres = np.concatenate([np.hypot(F[kf][:, 3], F[kf][:, 4]) for kf in F])
        pd_ = p0 + dp
        i_max, i_min, i_maxd, i_mind = int(np.argmax(p0)), int(np.argmin(p0)), int(np.argmax(pd_)), int(np.argmin(pd_))
        d = {"Pmax": float(p0[i_max]), "Pmin": float(p0[i_min]), "Pmax_dP": float(pd_[i_maxd]), "Pmin_dP": float(pd_[i_mind]),
             "dP_maks": float(np.abs(dp).max()), "Vmax": float(vres.max()),
             "n_Pmax": nm[i_max], "n_Pmin": nm[i_min], "k_Pmax": kf_[i_max], "k_Pmin": kf_[i_min],
             "n_Pmax_dP": nm[i_maxd], "n_Pmin_dP": nm[i_mind], "k_Pmax_dP": kf_[i_maxd], "k_Pmin_dP": kf_[i_mind]}
        if r["tipe"] == "inti":
            mx = np.concatenate([np.abs(F[kf][:, 1]) for kf in F])
            my = np.concatenate([np.abs(F[kf][:, 2]) for kf in F])
            tt = np.concatenate([np.abs(F[kf][:, 5]) for kf in F])
            d.update({"Mx": float(mx.max()), "My": float(my.max()), "T": float(tt.max())})
        else:
            d.update({"Mx": 0.0, "My": 0.0, "T": 0.0})
        out[jenis] = d
    return out


# ================================================================== panjang penyaluran dan penerusan ke pile cap
def ldh_2543(db, fc=FC):
    """Pasal 25.4.3.1 (hal 591): maks (0,24 fy db / (lambda sqrt fc'); 8 db; 150 mm), psi_e = psi_c = psi_r = 1,0 (diizinkan, 25.4.3.2)."""
    return max(0.24 * FY * db / math.sqrt(fc), 8 * db, 150.0)


def ld_tarik(db, koef=1.7, fc=FC, psi_t=1.0):
    """Pasal 25.4.2.1 (hal 587): maks (Tabel 25.4.2.2 (hal 588); 300 mm). Koef 1,7 bila spasi bersih >= 2 db dan selimut >= db; kalau tidak 1,1."""
    return max(FY * psi_t * db / (koef * math.sqrt(fc)), 300.0)


def ldc(db, fc=FC):
    """Pasal 25.4.9.2 (hal 604): maks (0,24 fy db / sqrt fc'; 0,043 fy db); minimum 200 mm (25.4.9.1)."""
    return max(0.24 * FY * db / math.sqrt(fc), 0.043 * FY * db, 200.0)


def tersedia():
    """(vertikal untuk kait ke dasar cap, lurus) mm: tebal cap - selimut 75 (Tabel 20.6.1.3.1, hal 482) - tulangan bawah cap D32 [Asumsi 5.6]."""
    return (T_CAP - SEL_CAP - DB_CAP) * 1000, (T_CAP - SEL_CAP) * 1000


def tumpu(a1, fc=FC):
    """phi Bn (kN) dasar kolom/dinding pada beton cap, A2 = A1 (konservatif): phi 0,65 x 0,85 fc' A1 (22.8.3.2, hal 540; Tabel 21.2.1 phi tumpu 0,65)."""
    return 0.65 * 0.85 * fc * a1 * 1000


def kelompok_titik(hasil):
    k = {}
    for r in hasil["titik"]:
        k.setdefault(r["kel"], []).append(r)
    return k


def stek_kolom(hasil):
    """Per kelompok kolom: penyaluran stek ke cap, tulangan pengekang, tumpu, dowel minimum, tarik, geser friksi."""
    m = hasil["mentah"]["tul_kolom"]
    out = []
    ver, lur = tersedia()
    for kel, rs in kelompok_titik(hasil).items():
        t = m[kel.replace(" B", "")] if kel.replace(" B", "") in m else m["K-T"]
        db, b = t["db"], max(r["b"] for r in rs)
        bersih = (t["b"] * 1000 - 2 * kl.SEL - 2 * kl.DS - db) / (t["m"] - 1) - db
        koef = 1.7 if (bersih >= 2 * db and (kl.SEL + kl.DS) >= db) else 1.1
        pu_max = max(r["amp"]["ult"]["Pmax_dP"] for r in rs)
        pu_min = min(r["amp"]["ult"]["Pmin_dP"] for r in rs)
        vu = max(r["amp"]["ult"]["Vmax"] for r in rs)
        ag = (b * 1000) ** 2
        a1 = b ** 2
        mu_fr = 0.6      # [Asumsi 5.6: beton dicor pada beton keras tidak dikasarkan; nilai Tabel 22.9.4.2 (hal 544) tidak terbaca di PDF]
        out.append({"kel": kel, "n": len(rs), "b": b, "tul_dari": t["b"], "m": t["m"], "db": db, "n_batang": t["n_batang"], "Ast": t["Ast"],
                    "bersih": bersih, "koef": koef, "ldh": ldh_2543(db), "ld": ld_tarik(db, koef), "ldc": ldc(db), "ver": ver, "lur": lur,
                    "s_lo": t["s_lo"], "lo": t["lo"], "kaki": t["kaki"], "n_sengkang": math.ceil(ver / t["s_lo"]), "pu_max": pu_max, "pu_min": pu_min,
                    "vu": vu, "phiBn": tumpu(a1), "as_min": 0.005 * ag, "phiTn": 0.9 * t["Ast"] * FY / 1000,
                    "phiVn": 0.75 * mu_fr * t["Ast"] * FY / 1000, "mu": mu_fr, "tarik": pu_min < 0,
                    "ok_ldh": ldh_2543(db) <= ver, "ok_ld": ld_tarik(db, koef) <= lur})
    return out


def inti_penerusan(hasil):
    """Per kelompok inti (W-L, W-TM, W-TP): penyaluran tulangan vertikal badan dan elemen batas ke cap inti, transversal, tumpu, tarik."""
    mt = hasil["mentah"]["tul_inti"]
    ver, lur = tersedia()
    out = []
    for kel, t in mt.items():
        rs = [r for r in hasil["inti"] if r["kel"] == kel]
        dbv, s, nb, dbb = t["tul"]
        dx, dy = td.DIM[t["tipe"]]
        ag = tm.kotak(dx, dy, tb.DINDING_T)[0]
        pu_max = max(r["amp"]["ult"]["Pmax"] for r in rs)
        pu_min = min(r["amp"]["ult"]["Pmin"] for r in rs)
        db = max(dbv, dbb)
        out.append({"kel": kel, "tipe": t["tipe"], "anggota": [r["id"] for r in rs], "db_v": dbv, "s_v": s, "n_batas": nb, "db_batas": dbb, "db": db,
                    "ldh": ldh_2543(db), "ld": ld_tarik(db, 1.7), "ldc": ldc(db), "ver": ver, "lur": lur, "ag": ag, "rho_l": t["rho_l"],
                    "as_web": t["rho_l"] * ag * 1e6, "as_batas": nb * sl.luas(dbb), "leg": t["leg"], "trans": t["trans"], "perlu_batas": t["perlu_batas"],
                    "pu_max": pu_max, "pu_min": pu_min, "phiBn": tumpu(ag), "phiTn_web": 0.9 * t["rho_l"] * ag * 1e6 * FY / 1000,
                    "ok_ldh": ldh_2543(db) <= ver, "ok_ld": ld_tarik(db, 1.7) <= lur})
    return out


def sloof_di_inti(xy):
    """Sloof (antar titik kolom) yang menyentuh kotak sumbu dinding inti dan yang melintas di dalamnya (geometri 5.4)."""
    kot = {n: box(*v[:4]) for n, v in kotak_inti().items()}
    out = []
    for a, b, tipe in segmen_sloof(xy):
        ls = LineString([a, b])
        for n, g in kot.items():
            if ls.intersects(g):
                dalam = ls.intersection(g.buffer(-0.01)).length > 0
                out.append({"inti": n, "a": a, "b": b, "tipe": tipe, "di_dalam": dalam, "panjang_kontak": ls.intersection(g).length})
    return out


@functools.lru_cache(maxsize=1)
def desain_sloof():
    """Desain 5.4 (ukuran keputusan Defsa) dengan gaya kolom 5.4 (`sl.data_kolom`)."""
    dk = sl.data_kolom()
    return {t: sl.desain(t, *UKURAN_SLOOF[t], dk=dk) for t in sl.TIPE}


def angkur_sloof(hasil):
    """Angkur ujung sloof ke pile cap inti: ldh (18.8.5.1 seperti 5.4), tersedia di dinding inti 297 mm, gaya Mpr As 1,25 fy, kait ke bawah dan tinggi cap minimum."""
    des = desain_sloof()
    ftie = sl.gaya_ikat(sl.data_kolom())["ftie_maks"]
    out = []
    for t, d in des.items():
        for lap, ts_ in (("atas", d["atas"]), ("bawah", d["bawah"])):
            db = ts_["db"]
            ldh_ = sl.ldh(db)
            tersedia_inti = (tb.DINDING_T - sl.SEL_KOL) * 1000
            ld_ = ld_tarik(db, 1.7)
            out.append({"tipe": t, "lapis": lap, "n": ts_["n"], "db": db, "As": ts_["As"], "T_mpr": ts_["As"] * 1.25 * FY / 1000, "ldh": ldh_,
                        "tersedia": tersedia_inti, "kurang": ldh_ - tersedia_inti, "ok": ldh_ <= tersedia_inti,
                        "h_cap_kait": ldh_ + (SEL_CAP + DB_CAP) * 1000, "h_cap_lurus": ld_ + SEL_CAP * 1000, "ld": ld_,
                        "T_per_batang": 1.25 * FY * sl.luas(db) / 1000})
    return {"baris": out, "ftie": ftie, "di_inti": sloof_di_inti({(r["x"], r["y"]) for r in hasil["titik"]})}


# ================================================================== cek silang T-95
def cek_t95(titik, inti, tam, m):
    """(a) Sigma D model vs berat seismik 4.2 (ELF W); (b) Sigma geser dasar E vs V ELF; (c) tambahan 5.x: dua cara; (d) Excel di cocokkan()."""
    a, b = {}, {}
    tinggi = tb.LEVEL["LT2"] - tb.LEVEL["LT1"]
    b_k = {k: v["b"] for k, v in m["kolom_meta"].items()}
    b_k.update({k: v["b_A"] for k, v in m["tangki"].items()})           # model OpenSees memakai ukuran opsi A (4.7)
    for kf in m["kolom"]:
        sk = sum(v["D"][0] for v in m["kolom"][kf].values())
        si = sum(v["D"][0] for v in m["inti"][kf].values())
        e = tb.elf(kf)
        tk = e["tingkat"]
        w_din = sum(t["komp"]["dinding inti"] for t in tk)
        lv_ada = {t["lv"] for t in tb.tingkat(kf)}
        din48, din_setengah = 0.0, 0.0
        for nama, kel, puncak in tb.INTI:
            top = tb.LEVEL[puncak] if kf == "K2" else min(tb.LEVEL[puncak], tb.LEVEL["LT5"])
            for lv in kl.URUT_LV:
                if lv in lv_ada and tb.LEVEL[lv] <= top + 1e-6:
                    din48 += GC * tb.DINDING_T * kel * tm.TINGGI[lv] * tb.FAKTOR_BUKAAN_DINDING
            din_setengah += GC * tb.DINDING_T * kel * tb.FAKTOR_BUKAAN_DINDING * tinggi / 2
        kol_setengah = sum(GC * x ** 2 * tinggi / 2 for x in b_k.values())
        a[kf] = {"kolom": sk, "inti": si, "model": sk + si, "W": e["W"], "statika_total": m["statika"][kf]["D"][0],
                 "statika_dasar": m["statika"][kf]["D"][1], "W_dinding": w_din, "W_rangka": e["W"] - w_din, "kol_setengah": kol_setengah,
                 "din_setengah": din_setengah, "rangka2": e["W"] - w_din + kol_setengah, "dinding48": din48, "dinding42": w_din + din_setengah,
                 "tributari_inti": si - din48}
        for c, idx in (("EX+", 3), ("EX-", 3), ("EY+", 4), ("EY-", 4)):
            vs = sum(v[c][idx] for v in m["kolom"][kf].values()) + sum(v[c][idx] for v in m["inti"][kf].values())
            b[(kf, c)] = {"jumlah": abs(vs), "V": e["V"]}
    # (c) tambahan: cara 1 = jumlah per titik; cara 2 = rumus total
    kat1 = {}
    for e in tam.values():
        for k, v in e["kat"].items():
            kat1[k] = kat1.get(k, 0.0) + v
    a_pod = tb.PODIUM.area
    a_mri = (MRI_PANEL[2] - MRI_PANEL[0]) * (MRI_PANEL[3] - MRI_PANEL[1])
    bukaan = bukaan_lif()
    pelat2 = (sl.D_PL + sl.LO_PL) * (a_pod - bukaan - a_mri) + (sl.D_MRI + sl.LO_MRI) * a_mri
    n_x = (len(GX) - 1) * len(GY)
    n_y = (len(GY) - 1) * len(GX)
    jml = {"SL-2": 2 * (len(GX) - 1) + (len(GY) - 1), "SL-3": len(GY) - 1}
    jml["SL-1"] = n_x + n_y - jml["SL-2"] - jml["SL-3"]
    w = {t: GC * UKURAN_SLOOF[t][0] * (UKURAN_SLOOF[t][1] - sl.H_PELAT) + (sl.W_R09 if t == "SL-1" else sl.W_FASAD) for t in jml}
    sloof2 = sum(jml[t] * L * w[t] for t in jml)
    xs = [r for r in titik]
    stek2 = GC * (BAWAH_PELAT - HALAMAN) * (sum(r["b"] ** 2 for r in xs) + sum(k[1] * tb.DINDING_T for k in tb.INTI))
    dl = pit.data_lift()
    pit2 = sum(pit.angkat(dl[k], T_PIT[k], pit.Q100)["W"] + dl[k]["jumlah"] * (dl[k]["p_kereta"] + dl[k]["p_imbang"]) for k in T_PIT) \
        + 2 * GC * BALOK_PG[0] * BALOK_PG[1] * L
    mi = mri.baca_masukan()
    mri2 = sl.pl_w() * sum(mi["dinding"]) + sl.P_MAGNET
    c = {"kat1": kat1, "kat2": {"pelat": pelat2, "sloof": sloof2, "stek": stek2, "pit": pit2, "mri": mri2}, "n_sloof": jml, "w_sloof": w}
    c["total1"], c["total2"] = sum(kat1.values()), sum(c["kat2"].values())
    return {"a": a, "b": b, "c": c}


# ================================================================== teks pembantu
def f(v):
    return float(v)


def e_maks(r, awal, idx):
    """Nilai mutlak maksimum komponen idx dari kasus E arah awal ('EX' atau 'EY') di semua tanda dan konfigurasi."""
    return max(float(abs(r["raw"][kf][f"{awal}{s}"][idx])) for kf in r["raw"] for s in "+-")


def ukuran_s(r):
    return "inti" if r["tipe"] == "inti" else idn(r["b"] * 1000, 0)


def pen_s(nama, kf):
    return f"{nama} ({kf})"


# ------------------------------------------------------------------ baris R
def baris_kombinasi(h):
    a = [
        R("sds", "SDS (spektrum 4.1 opsi a)", SDS, "", "", "tahap4_beban.SDS (4.1)", "0.000"),
        R("rho", "Faktor redundansi ρ", RHO, "", "KDS D, sementara (4.3)", "SNI 1726:2019 Pasal 7.3.4.2 (4.3)", "0.00"),
        R("ev", "Ev = 0,2 SDS (dikali D)", "=0.2*{sds}", "", "", "SNI 1726:2019 Pasal 7.4.2.2 (hal PDF 77)", "0.0000", EV),
        R("o30", "Faktor arah ortogonal", 0.3, "", "100 % arah utama + 30 % arah tegak lurus", "SNI 1726:2019 Pasal 7.5.3 (hal PDF 79)", "0.00"),
    ]
    b = [
        R("u1", "Faktor D: 1,2 + 0,2 SDS", "=1.2+{ev}", "", "(1,2 + 0,2 SDS) D + L + ρ QE", "SNI 1726:2019 Pasal 4.2.2.3 no. 6 (hal PDF 38)", "0.0000", 1.2 + EV),
        R("u2", "Faktor D: 0,9 - 0,2 SDS", "=0.9-{ev}", "", "(0,9 - 0,2 SDS) D + ρ QE", "SNI 1726:2019 Pasal 4.2.2.3 no. 7 (hal PDF 38)", "0.0000", 0.9 - EV),
        R("eu", "Faktor E ultimit", "={rho}", "", "E = ρ (QE arah utama + 0,3 QE ortogonal)", "SNI 1726:2019 Pasal 7.4.2.1 (hal PDF 77)", "0.00", RHO),
    ]
    c = [
        R("l1", "Faktor D layan: 1,0 + 0,14 SDS", "=1+0.7*{ev}", "", "(1,0 + 0,14 SDS) D + 0,7 ρ QE", "SNI 1726:2019 Pasal 4.2.3.3 no. 8 (hal PDF 40)", "0.0000", 1 + 0.7 * EV),
        R("l2", "Faktor D layan: 1,0 + 0,105 SDS", "=1+0.525*{ev}", "", "(1,0 + 0,105 SDS) D + 0,75 L + 0,525 ρ QE", "SNI 1726:2019 Pasal 4.2.3.3 no. 9 (hal PDF 40)", "0.0000",
          1 + 0.525 * EV),
        R("l3", "Faktor D layan: 0,6 - 0,14 SDS", "=0.6-0.7*{ev}", "", "(0,6 - 0,14 SDS) D + 0,7 ρ QE", "SNI 1726:2019 Pasal 4.2.3.3 no. 10 (hal PDF 40)", "0.0000",
          0.6 - 0.7 * EV),
        R("e1", "Faktor E layan no. 8 dan 10: 0,7 ρ", "=0.7*{rho}", "", "", "SNI 1726:2019 Pasal 4.2.3.3 (hal PDF 40)", "0.000", 0.7 * RHO),
        R("e2", "Faktor E layan no. 9: 0,525 ρ", "=0.525*{rho}", "", "", "SNI 1726:2019 Pasal 4.2.3.3 (hal PDF 40)", "0.0000", 0.525 * RHO),
    ]
    return [("A", "Masukan", a), ("B", "Faktor kombinasi ultimit", b), ("C", "Faktor kombinasi layan (tegangan izin)", c)]


def baris_beban(h):
    c = h["t95"]["c"]
    dl = pit.data_lift()
    mi = mri.baca_masukan()
    wl = c["w_sloof"]
    pm = lambda k: dl[k]["jumlah"] * (dl[k]["p_kereta"] + dl[k]["p_imbang"])   # noqa: E731
    wp = {k: pit.angkat(dl[k], T_PIT[k], pit.Q100)["W"] for k in T_PIT}
    sum_b2 = sum(r["b"] ** 2 for r in h["titik"])
    sum_kel = sum(k[1] for k in tb.INTI)
    pelat_d = sl.D_PL * (tb.PODIUM.area - bukaan_lif() - 64.0) + sl.D_MRI * 64.0
    pelat_l = sl.LO_PL * (tb.PODIUM.area - bukaan_lif() - 64.0) + sl.LO_MRI * 64.0
    a = [
        R("gc", "Berat jenis beton bertulang", GC, "kN/m³", "", "SNI 1727:2020 Tabel C3.1-2 (4.2)", "0.0"),
        R("dpl", "D pelat PL-1", sl.D_PL, "kPa", "250 mm + keramik + partisi", "5.3, 5.4 (tahap5_sloof.D_PL)", "0.000"),
        R("lpl", "Beban hidup PL-1", sl.LO_PL, "kPa", "", "SNI 1727:2020 Tabel 4.3-1 (hal PDF 52), 5.3", "0.00"),
        R("dmri", "D panel MRI", sl.D_MRI, "kPa", "D PL-1 + sangkar RF 0,655", "5.3, 5.4", "0.000"),
        R("lmri", "Beban hidup panel MRI", sl.LO_MRI, "kPa", "", "5.3, 5.4", "0.00"),
        R("apod", "Luas podium LT1 (12-84 × 27-75)", "=(84-12)*(75-27)", "m²", "", "tahap4_beban.PODIUM", "#,##0.0", tb.PODIUM.area),
        R("amri", "Luas panel MRI 9-10/D-E (76-84 × 51-59)", "=(84-76)*(59-51)", "m²", "", "5.3", "0.0", 64.0),
        R("bkn", "Bukaan LT1 lif L-1..4 (5,2 × 6,2)", "=5.2*6.2", "m²", "pelat tidak ada di dalam shaft; bukaan L-5..6 dan L-7 tidak dikurangkan (konservatif)",
          "5.5 (tahap5_pit_lift)", "0.00", bukaan_lif()),
        R("pld", "Σ D pelat LT1 ke semua titik", "={dpl}*({apod}-{bkn}-{amri})+{dmri}*{amri}", "kN", "tributari 8 × 8; pelat di dalam inti ke inti", "[Asumsi 5.6: tributari; sloof menerus diabaikan]",
          "#,##0.0", pelat_d),
        R("pll", "Σ L pelat LT1 ke semua titik", "={lpl}*({apod}-{bkn}-{amri})+{lmri}*{amri}", "kN", "", "", "#,##0.0", pelat_l),
    ]
    b = []
    for t, (bs, hs) in UKURAN_SLOOF.items():
        k = t.replace("-", "").lower()
        b += [R(f"b{k}", f"Lebar {t}", bs, "m", "", "keputusan Defsa 5.4", "0.00"), R(f"h{k}", f"Tinggi {t}", hs, "m", "", "keputusan Defsa 5.4", "0.00")]
    b += [R("hpl", "Tebal pelat LT1", sl.H_PELAT, "m", "", "5.3", "0.00"),
          R("wfs", "Dinding fasad pada sloof tepi", sl.W_FASAD, "kN/m'", "SL-2, SL-3", "5.4 (tahap5_sloof.W_FASAD)", "0.000"),
          R("wr9", "Dinding timbal R-09 pada sloof dalam", sl.W_R09, "kN/m'", "SL-1 (konservatif)", "[Alat Medis R-09], 5.4", "0.000")]
    for t in UKURAN_SLOOF:
        k = t.replace("-", "").lower()
        extra = "{wr9}" if t == "SL-1" else "{wfs}"
        b.append(R(f"w{k}", f"Beban garis {t} (berat sendiri di bawah pelat + dinding)", f"={{gc}}*{{b{k}}}*({{h{k}}}-{{hpl}})+{extra}", "kN/m'", "", "5.4", "0.000", wl[t]))
    b += [R("nsl2", "Jumlah segmen SL-2", "=2*(10-1)+(7-1)", "buah", "y = 27 dan 75 (9 bentang) + x = 12 (6 bentang)", "grid 8 × 8 m (5.4)", "0", c["n_sloof"]["SL-2"]),
          R("nsl3", "Jumlah segmen SL-3", "=7-1", "buah", "x = 84 (6 bentang)", "", "0", c["n_sloof"]["SL-3"]),
          R("nsl1", "Jumlah segmen SL-1", "=((10-1)*7+(7-1)*10)-{nsl2}-{nsl3}", "buah", "", "", "0", c["n_sloof"]["SL-1"]),
          R("sls", "Σ berat sloof + dinding ke semua titik (setengah bentang tiap ujung)", "=8*({nsl1}*{wsl1}+{nsl2}*{wsl2}+{nsl3}*{wsl3})", "kN", "bentang 8 m",
            "[Asumsi 5.6: setengah bentang ke tiap ujung]", "#,##0.0", c["kat2"]["sloof"])]
    d = [
        R("lt1", "Peil atas pelat LT1", LT1, "m", "", "3.3", "0.00"),
        R("bpl", "Sisi bawah pelat LT1", "={lt1}-{hpl}", "m", "", "5.5 (ATAS)", "0.00", BAWAH_PELAT),
        R("hal", "Kepala pile cap = halaman", HALAMAN, "m", "", "3.7 (tahap3_bim.HALAMAN)", "0.00"),
        R("hst", "Tinggi stek (sisi bawah pelat ke kepala cap)", "={bpl}-{hal}", "m", "", "", "0.00", BAWAH_PELAT - HALAMAN),
        R("sb2", "Σ b² semua kolom LT1 (opsi B untuk kolom tangki)", sum_b2, "m²", "", "4.7, 5.1", "0.000"),
        R("skl", "Σ keliling dinding inti", sum_kel, "m", "6 tangga × 20 + lif 32", "tahap4_beban.INTI", "0.0"),
        R("stk", "Σ berat stek kolom dan dinding inti", "={gc}*({sb2}+{skl}*0.35)*{hst}", "kN", "dinding inti T 0,35 m", "[Asumsi 5.6: tanpa faktor bukaan]", "#,##0.0", c["kat2"]["stek"]),
    ]
    e = []
    for k in T_PIT:
        s = k.replace("L-", "").replace("..", "").replace(".", "")
        e += [R(f"pw{s}", f"Berat pit {k} (beton pelat t {idn(T_PIT[k], 2)} + dinding)", wp[k], "kN", "", "5.5 (angkat, t keputusan Defsa)", "#,##0.0"),
              R(f"pb{s}", f"Beban buffer {k} (dianggap beban hidup)", pm(k), "kN", "reaksi buffer sudah termasuk faktor kejut pemasok", "5.5 (gravitasi: 1,6 Pb)", "#,##0.0")]
    e += [R("wbg", "Berat dua balok penggantung L-7 (400 × 800 × 8 m)", "=2*{gc}*0.4*0.8*8", "kN", "", "5.5, [Asumsi 5.6]", "0.0", 2 * GC * 0.32 * 8),
          R("pit_t", "Σ berat pit, buffer, dan balok penggantung", "={pw14}+{pb14}+{pw56}+{pb56}+{pw7}+{pb7}+{wbg}", "kN", "", "", "#,##0.0", c["kat2"]["pit"])]
    g = [
        R("wp", "Beban garis dinding pelindung MRI", sl.pl_w(), "kN/m'", "93,2 kN / 13,0 m", "[Alat Medis R-04], 5.3", "0.000"),
        R("pu", "Panjang dinding pelindung utara", mi["dinding"][0], "m", "di y 60, resultan x 80,5 [Asumsi 5.6]", "[Alat Medis R-04]", "0.0"),
        R("pt", "Panjang dinding pelindung timur", mi["dinding"][1], "m", "di sloof as 10, y 54-60", "[Alat Medis R-04]", "0.0"),
        R("mag", "Berat magnet MRI", sl.P_MAGNET, "kN", "dibagi sama ke empat kolom sudut panel", "[Alat Medis R-03], [Asumsi 5.4]", "0.0"),
        R("mri_t", "Σ pelindung dan magnet", "={wp}*({pu}+{pt})+{mag}", "kN", "", "", "#,##0.0", c["kat2"]["mri"]),
        R("tot2", "Σ tambahan struktur tengah (cara 2: rumus total)", "={pld}+{pll}+{sls}+{stk}+{pit_t}+{mri_t}", "kN", "pelat + sloof + stek + pit + MRI", "", "#,##0.0", c["total2"]),
    ]
    return [("A", "Pelat LT1 (5.3)", a), ("B", "Sloof (5.4)", b), ("C", "Stek kolom dan dinding inti", d), ("D", "Pit lift (5.5)", e), ("E", "Dinding pelindung dan magnet MRI", g)]


def baris_stek(h):
    st = stek_kolom(h)
    a = [R("sfy", "fy", FY, "MPa", "", "", "0.0"), R("sfc", "fc' kolom dan pile cap", FC, "MPa", "pile cap sama dengan kolom", "[Asumsi 5.6]", "0.0"),
         R("tcap", "Tebal pile cap", T_CAP * 1000, "mm", "", "[Asumsi 3.7] tahap3_bim.TEBAL_CAP", "0"),
         R("scap", "Selimut beton pile cap pada tanah", SEL_CAP * 1000, "mm", "", "SNI 2847:2019 Tabel 20.6.1.3.1 (hal PDF 482)", "0"),
         R("dcap", "Tulangan bawah pile cap", DB_CAP * 1000, "mm", "satu lapis D32", "[Asumsi 5.6]", "0"),
         R("ver", "Tersedia vertikal untuk kait ke atas tulangan bawah cap", "={tcap}-{scap}-{dcap}", "mm", "", "", "0", tersedia()[0]),
         R("lur", "Tersedia untuk batang lurus", "={tcap}-{scap}", "mm", "", "", "0", tersedia()[1])]
    out = [("A", "Masukan umum", a)]
    for i, x in enumerate(st):
        n = x["kel"]
        rows = [
            R(f"kb{i}", f"{n}: lebar kolom", x["b"], "m", f"{x['n']} kolom", "4.7, 5.1", "0.00"),
            R(f"kd{i}", f"{n}: diameter stek", x["db"], "mm", f"{x['n_batang']} batang, tulangan dari kelompok 4.7 ({idn(x['tul_dari'], 2)} m)", "4.7 (tahap4_kolom.rancang)", "0"),
            R(f"ka{i}", f"{n}: Ast stek", x["Ast"], "mm²", "", "4.7", "#,##0.0"),
            R(f"kk{i}", f"{n}: koefisien Tabel 25.4.2.2", x["koef"], "", f"spasi bersih {idn(x['bersih'], 0)} mm; 1,7 bila ≥ 2 db dan selimut ≥ db",
              "SNI 2847:2019 Tabel 25.4.2.2 (hal PDF 588)", "0.0"),
            R(f"kh{i}", f"{n}: ldh kait 90° = 0,24 fy db / √fc'", f"=MAX(0.24*{{sfy}}*{{kd{i}}}/SQRT({{sfc}}),8*{{kd{i}}},150)", "mm", "maks (…; 8 db; 150)",
              "SNI 2847:2019 Pasal 25.4.3.1 (hal PDF 591)", "0.0", x["ldh"]),
            R(f"kl{i}", f"{n}: ld tarik lurus", f"=MAX({{sfy}}*{{kd{i}}}/({{kk{i}}}*SQRT({{sfc}})),300)", "mm", "ψt = ψe = 1,0 (batang vertikal tanpa lapis)",
              "SNI 2847:2019 Pasal 25.4.2.1 dan Tabel 25.4.2.2 (hal PDF 587-588)", "0.0", x["ld"]),
            R(f"kc{i}", f"{n}: ldc tekan", f"=MAX(0.24*{{sfy}}*{{kd{i}}}/SQRT({{sfc}}),0.043*{{sfy}}*{{kd{i}}},200)", "mm", "", "SNI 2847:2019 Pasal 25.4.9 (hal PDF 604)", "0.0", x["ldc"]),
            R(f"ko{i}", f"{n}: rasio ldh / tersedia vertikal", f"={{kh{i}}}/{{ver}}", "", "kait ke dasar cap dekat permukaan bawah", "SNI 2847:2019 Pasal 18.13.2.2 (hal PDF 448)", "0.000",
              x["ldh"] / x["ver"]),
            R(f"kr{i}", f"{n}: rasio ld lurus / tersedia", f"={{kl{i}}}/{{lur}}", "", "> 1 berarti batang lurus tidak cukup: kait", "", "0.000", x["ld"] / x["lur"]),
            R(f"kg{i}", f"{n}: As min dasar kolom = 0,005 Ag", f"=0.005*{{kb{i}}}^2*1000000", "mm²", "", "SNI 2847:2019 Pasal 16.3.4.1 (hal PDF 312)", "#,##0.0", x["as_min"]),
            R(f"kt{i}", f"{n}: φBn tumpu = 0,65 × 0,85 fc' A1", f"=0.65*0.85*{{sfc}}*{{kb{i}}}^2*1000", "kN", "A2 = A1 (konservatif)", "SNI 2847:2019 Pasal 16.3.3.4 dan 22.8.3.2 (hal PDF 311, 540)",
              "#,##0.0", x["phiBn"]),
            R(f"kp{i}", f"{n}: φTn stek = 0,9 Ast fy", f"=0.9*{{ka{i}}}*{{sfy}}/1000", "kN", "", "SNI 2847:2019 Pasal 16.3.1.2 (hal PDF 310)", "#,##0.0", x["phiTn"]),
        ]
        out.append((chr(66 + i), f"Kelompok {n}", rows))
    return out


def baris_inti(h):
    it = inti_penerusan(h)
    out = []
    for i, x in enumerate(it):
        n = x["kel"]
        rows = [
            R(f"id{i}", f"{n}: diameter terbesar (badan {x['db_v']}, batas {x['db_batas']})", x["db"], "mm", f"badan D{x['db_v']}-{x['s_v']}; elemen batas {x['n_batas']} D{x['db_batas']}",
              "4.8 (tahap4_dinding.rancang)", "0"),
            R(f"ih{i}", f"{n}: ldh kait 90°", f"=MAX(0.24*{{sfy}}*{{id{i}}}/SQRT({{sfc}}),8*{{id{i}}},150)", "mm", "", "SNI 2847:2019 Pasal 25.4.3.1 (hal PDF 591)", "0.0", x["ldh"]),
            R(f"il{i}", f"{n}: ld tarik lurus (koef 1,7)", f"=MAX({{sfy}}*{{id{i}}}/(1.7*SQRT({{sfc}})),300)", "mm", "", "SNI 2847:2019 Pasal 25.4.2.1, Tabel 25.4.2.2", "0.0", x["ld"]),
            R(f"ic{i}", f"{n}: ldc tekan", f"=MAX(0.24*{{sfy}}*{{id{i}}}/SQRT({{sfc}}),0.043*{{sfy}}*{{id{i}}},200)", "mm", "", "SNI 2847:2019 Pasal 25.4.9", "0.0", x["ldc"]),
            R(f"io{i}", f"{n}: rasio ldh / tersedia vertikal", f"={{ih{i}}}/{{ver}}", "", "", "", "0.000", x["ldh"] / x["ver"]),
            R(f"ir{i}", f"{n}: rasio ld lurus / tersedia", f"={{il{i}}}/{{lur}}", "", "> 1: kait diperlukan", "", "0.000", x["ld"] / x["lur"]),
            R(f"ia{i}", f"{n}: luas dinding Ag", x["ag"], "m²", f"kotak {'8 × 8' if x['tipe'] == 'L' else '4 × 6'} sumbu, T 0,35", "tahap4_model.kotak", "0.00"),
            R(f"it{i}", f"{n}: φBn tumpu", f"=0.65*0.85*{{sfc}}*{{ia{i}}}*1000", "kN", "A2 = A1", "SNI 2847:2019 Pasal 22.8.3.2 (hal PDF 540)", "#,##0", x["phiBn"]),
            R(f"iw{i}", f"{n}: φTn tulangan badan = 0,9 ρl Ag fy", f"=0.9*{x['rho_l']!r}*{{ia{i}}}*1000000*{{sfy}}/1000", "kN", f"ρl {idn(x['rho_l'] * 100, 3)} % (4.8); tulangan batas tidak dihitung",
              "SNI 2847:2019 Pasal 16.3.4.2, 11.6.1, 18.10.2.1", "#,##0", x["phiTn_web"]),
        ]
        out.append((chr(65 + i), f"Kelompok inti {n}", rows))
    return out


def baris_angkur(h):
    an = angkur_sloof(h)
    out = []
    a = [R("afy", "fy", FY, "MPa", "", "", "0.0"), R("afc", "fc'", sl.FC, "MPa", "sloof 5.4", "5.4", "0.0"),
         R("atd", "Tebal dinding inti", tb.DINDING_T * 1000, "mm", "", "4.2", "0"), R("ask", "Selimut kolom + sengkang", sl.SEL_KOL * 1000, "mm", "", "5.4", "0"),
         R("att", "Tersedia horizontal di dinding inti", "={atd}-{ask}", "mm", "", "[Asumsi 5.4]", "0.0", (tb.DINDING_T - sl.SEL_KOL) * 1000),
         R("aft", "Ftie pengikat fondasi", an["ftie"], "kN", "10 % SDS Pu", "5.4, SNI 1726:2019 Pasal 7.13.7.2 (hal PDF 104-105)", "0.0"),
         R("ahc", "Tersedia vertikal kait (cap 1.200 - 75 - 32)", tersedia()[0], "mm", "", "lembar Stek Kolom", "0"),
         R("asc", "Selimut + tulangan bawah cap", (SEL_CAP + DB_CAP) * 1000, "mm", "", "", "0.0")]
    out.append(("A", "Masukan", a))
    for i, x in enumerate(an["baris"]):
        n = f"{x['tipe']} {x['lapis']}"
        rows = [
            R(f"sn{i}", f"{n}: jumlah batang", x["n"], "buah", "", "5.4 (tahap5_sloof.desain)", "0"),
            R(f"sd{i}", f"{n}: diameter", x["db"], "mm", "", "5.4", "0"),
            R(f"sa{i}", f"{n}: As", f"={{sn{i}}}*PI()*{{sd{i}}}^2/4", "mm²", "", "", "#,##0.0", x["As"]),
            R(f"st{i}", f"{n}: T = As × 1,25 fy (Mpr)", f"={{sa{i}}}*1.25*{{afy}}/1000", "kN", "gaya tarik bila sloof mencapai Mpr", "SNI 2847:2019 Pasal 18.6.5.1 (hal PDF 403)", "#,##0.0", x["T_mpr"]),
            R(f"sh{i}", f"{n}: ldh kait 90°", f"=MAX({{afy}}*{{sd{i}}}/(5.4*SQRT({{afc}})),8*{{sd{i}}},150)", "mm", "seperti 5.4", "SNI 2847:2019 Pasal 18.8.5.1 (hal PDF 418)", "0.0", x["ldh"]),
            R(f"sk{i}", f"{n}: kurang terhadap dinding inti", f"={{sh{i}}}-{{att}}", "mm", "> 0: tidak cukup di dinding", "", "0.0", x["kurang"]),
            R(f"sc{i}", f"{n}: tinggi cap min bila kait ke bawah", f"={{sh{i}}}+{{asc}}", "mm", "ldh + selimut + tulangan bawah cap", "[Asumsi 5.6]", "0.0", x["h_cap_kait"]),
            R(f"sl{i}", f"{n}: tinggi cap min bila batang lurus ke bawah", f"=MAX({{afy}}*{{sd{i}}}/(1.7*SQRT({{afc}})),300)+{{scap}}", "mm", "ld lurus + selimut", "SNI 2847:2019 Tabel 25.4.2.2", "0.0",
              x["h_cap_lurus"]),
        ]
        out.append((chr(66 + i), f"{n}", rows))
    return out


def semua_baris(h):
    out = {}
    for nama, fn in (("Kombinasi", baris_kombinasi), ("Beban Tambahan", baris_beban), ("Stek Kolom", baris_stek), ("Penerusan Inti", baris_inti),
                     ("Angkur Sloof Inti", baris_angkur)):
        out[nama] = [rw for _, _, rows in fn(h) for rw in rows]
    return out


NAMA = ["Petunjuk", "Ringkasan", "Ringkasan Tahap 6", "Kombinasi", "Beban Tambahan", "Tambahan per Titik", "Reaksi Titik", "Amplop Reaksi", "Delta P Sloof",
        "Stek Kolom", "Penerusan Inti", "Angkur Sloof Inti", "Penerusan Ringkas", "Cek Silang T-95", "Acuan"]


# ================================================================== teks tabel
def rank_pmax(h, n=5, jenis="lay"):
    return sorted(h["titik"], key=lambda r: -r["amp"][jenis]["Pmax_dP"])[:n]


def teks_kombinasi():
    out = []
    for jenis, nm in (("ult", "ultimit"), ("lay", "layan")):
        kd = kombinasi_daftar(jenis)
        urut, cnt = [], {}
        for k in kd:
            cnt[k[0]] = cnt.get(k[0], 0) + 1
            if k[0] not in urut:
                urut.append(k[0])
        for nama in urut:
            k = next(x for x in kd if x[0] == nama)
            pasal = {"1,4 D": "4.2.2.1 no. 1", "1,2 D + 1,6 L": "4.2.2.1 no. 2", "(1,2 + 0,2 SDS) D + L + E": "4.2.2.3 no. 6, 7.4.2",
                     "(0,9 - 0,2 SDS) D + E": "4.2.2.3 no. 7, 7.4.2", "D": "4.2.3.1 no. 1", "D + L": "4.2.3.1 no. 2",
                     "(1,0 + 0,14 SDS) D + 0,7 E": "4.2.3.3 no. 8", "(1,0 + 0,105 SDS) D + 0,75 L + 0,525 E": "4.2.3.3 no. 9",
                     "(0,6 - 0,14 SDS) D + 0,7 E": "4.2.3.3 no. 10"}[nama]
            out.append([nm, nama, k[1], k[2], k[3], cnt[nama], pasal])
    return out


def teks_tambahan(h):
    out = []
    for r in h["semua"]:
        k = r["kat"]
        out.append([r["id"], r["kel"], k.get("pelat", 0.0), k.get("sloof", 0.0), k.get("stek", 0.0), k.get("pit", 0.0), k.get("mri", 0.0), None, r["D_tam"], r["L_tam"]])
    return out


def teks_reaksi(h):
    out = []
    for r in h["semua"]:
        out.append([r["id"], r["x"], r["y"], r["kel"], ukuran_s(r), f(r["D_model"]), f(r["D_tam"]), None, f(r["L_model"]), f(r["L_tam"]), None,
                    e_maks(r, "EX", 0), e_maks(r, "EX", 3), e_maks(r, "EX", 4), e_maks(r, "EY", 0), e_maks(r, "EY", 3), e_maks(r, "EY", 4)])
    return out


def teks_amplop(h):
    out = []
    for r in h["semua"]:
        a, u = r["amp"]["lay"], r["amp"]["ult"]
        out.append([r["id"], r["kel"], a["Pmax"], a["Pmax_dP"], a["Pmin"], a["Pmin_dP"], a["Vmax"], pen_s(a["n_Pmax_dP"], a["k_Pmax_dP"]),
                    u["Pmax_dP"], u["Pmin_dP"], u["Vmax"], u["Mx"], u["My"], u["T"], pen_s(u["n_Pmin_dP"], u["k_Pmin_dP"])])
    return out


def teks_dp(h):
    out = []
    for r in h["titik"]:
        a, u = r["amp"]["lay"], r["amp"]["ult"]
        out.append([r["id"], r["kel"], u["dP_maks"], a["dP_maks"], a["Pmax"], a["Pmax_dP"], a["Pmin"], a["Pmin_dP"], u["Pmax"], u["Pmax_dP"], u["Pmin"], u["Pmin_dP"]])
    return out


def teks_tahap6(h):
    out = []
    for r in h["semua"]:
        a, u = r["amp"]["lay"], r["amp"]["ult"]
        cat = "M ke cap 0 (sendi, 5.4)" if r["tipe"] == "kolom" else "M dan T penuh ke cap inti"
        out.append([r["id"], r["x"], r["y"], r["kel"], ukuran_s(r), a["Pmax_dP"], a["Pmin_dP"], a["Vmax"], u["Pmax_dP"], u["Pmin_dP"], u["Vmax"], u["Mx"], u["My"], u["T"], cat])
    return out


def teks_stek(h):
    out = []
    for x in stek_kolom(h):
        ok_t = x["pu_max"] <= x["phiBn"]
        out.append([f"{x['kel']} ({x['n']})", f"{x['n_batang']} D{x['db']}", x["ldh"], x["ld"], x["ldc"], x["ver"], x["lur"],
                    f"D{kl.DS}-{idn(x['s_lo'], 0)} ({x['kaki']} kaki), {x['n_sengkang']} baris di cap", x["pu_max"], x["phiBn"], x["pu_min"], x["phiTn"], x["vu"], x["phiVn"],
                    "memenuhi" if (x["ok_ldh"] and ok_t and x["vu"] <= x["phiVn"]) else "periksa"])
    return out


def teks_inti(h):
    out = []
    for x in inti_penerusan(h):
        tr = x["trans"]
        trs = f"{tr['jenis']}: D{tr['db']}-{idn(tr['s'], 0)}" if tr.get("s") else tr["jenis"]
        out.append([f"{x['kel']} ({len(x['anggota'])} inti)", f"D{x['db_v']}-{x['s_v']}; {x['n_batas']} D{x['db_batas']} per ujung (panjang {idn(x['leg'], 2)} m)", x["ldh"], x["ld"], x["ldc"],
                    x["pu_max"], x["phiBn"], trs, x["pu_min"], x["phiTn_web"], "cukup" if x["ok_ld"] else "perlu kait"])
    return out


def teks_angkur(h):
    an = angkur_sloof(h)
    out = []
    for x in an["baris"]:
        out.append([f"{x['tipe']} {x['lapis']}", f"{x['n']} D{x['db']}", x["T_mpr"], x["T_per_batang"], x["ldh"], x["tersedia"], x["kurang"],
                    "cukup" if x["ok"] else "tidak cukup: kait ke bawah masuk pile cap inti", x["h_cap_kait"], x["h_cap_lurus"]])
    return out


def teks_sloof_inti(h):
    out = []
    for s in angkur_sloof(h)["di_inti"]:
        ket_ = "melintas DI DALAM kotak inti" if s["di_dalam"] else ("berimpit garis dinding inti" if s["panjang_kontak"] > 0.5 else "hanya menyentuh ujung")
        out.append([s["inti"], f"({idn(s['a'][0], 0)}, {idn(s['a'][1], 0)}) - ({idn(s['b'][0], 0)}, {idn(s['b'][1], 0)}): {ket_}", s["tipe"], s["panjang_kontak"]])
    return out


NAMA_PASAL = [
    ["SNI 1726:2019", "4.2.2.1 no. 1-2; 4.2.2.3 no. 6-7", "Kombinasi kekuatan; E = Eh ± Ev.", "38-39", "pengaruh beban seismik yang paling menentukan harus ditinjau", "Terverifikasi"],
    ["SNI 1726:2019", "4.2.3.1 no. 1-2; 4.2.3.3 no. 8-10", "Kombinasi tegangan izin; koefisien 0,14 dan 0,105 SDS = 0,7 dan 0,525 × 0,2 SDS.", "39-40",
     "tegangan izin diperbolehkan untuk ditingkatkan sebesar 1,2 kali", "Terverifikasi; suku SDS tidak terbaca di teks PDF (disimpulkan dari 7.4.2.2); peningkatan 1,2 tidak dipakai"],
    ["SNI 1726:2019", "7.4.2.1, 7.4.2.2", "Eh = ρ QE; Ev = 0,2 SDS D.", "77", "Ev = 0,2 SDS D (Pers. 25)", "Terverifikasi"],
    ["SNI 1726:2019", "7.5.3 (juga 7.5.4)", "Kombinasi ortogonal 100 % + 30 %.", "79", "100 % gaya untuk satu arah ditambah 30 % gaya untuk arah tegak lurus", "Terverifikasi"],
    ["SNI 1726:2019", "7.13.4", "Reduksi gaya guling di muka kontak tanah-fondasi 25 % (ELF).", "102", "diizinkan untuk direduksi sebesar 25 %", "Terverifikasi; TIDAK dipakai (hanya dicatat)"],
    ["SNI 1726:2019", "7.13.7.2", "Pile cap dihubungkan dengan pengikat; Ftie = 10 % SDS Pu.", "104-105", "harus dihubungkan satu sama lain dengan pengikat", "Terverifikasi (dari 5.4)"],
    ["SNI 2847:2019", "16.3.1.1, 16.3.1.2", "Gaya dan momen dasar kolom/dinding disalurkan ke fondasi dengan tumpuan dan tulangan.", "310",
     "harus disalurkan ke fondasi pendukung dengan tumpuan pada beton dan dengan tulangan", "Terverifikasi"],
    ["SNI 2847:2019", "16.3.3.1, 16.3.3.4, 16.3.3.5", "Kekuatan desain sambungan; tumpu 22.8; geser-friksi 22.9.", "311", "kekuatan tumpu nominal Bn harus dihitung sesuai 22.8", "Terverifikasi"],
    ["SNI 2847:2019", "16.3.4.1, 16.3.4.2", "Tulangan dasar kolom ≥ 0,005 Ag; dinding sesuai 11.6.1.", "312", "As bidang kontak harus sedikitnya 0,005Ag", "Terverifikasi"],
    ["SNI 2847:2019", "16.3.5.1, 16.3.5.2", "Tulangan diteruskan ke fondasi atau dowel; momen disalurkan sesuai 10.7.5.", "312-313",
     "dengan meneruskan tulangan longitudinal sampai ke dalam fondasi pendukung", "Terverifikasi"],
    ["SNI 2847:2019", "18.13.2.1-18.13.2.4", "Tulangan kolom/dinding SRPMK menerus ke pile cap dan disalurkan tarik; kait 90° dekat sisi bawah; transversal 18.7.5.2-18.7.5.4 di bawah sisi atas cap; tulangan atas bila uplift.",
     "448", "harus menerus ke dalam fondasi telapak, fondasi rakit, atau poer", "Terverifikasi"],
    ["SNI 2847:2019", "18.7.5.1-18.7.5.4; 18.10.6.4-18.10.6.5", "Pengekangan kolom dan elemen batas dinding.", "408-412; 429-433", "-", "Terverifikasi (dari 4.7 dan 4.8)"],
    ["SNI 2847:2019", "18.8.5.1", "ldh sloof di joint = fy db / (5,4 λ √fc').", "418", "-", "Terverifikasi (dari 5.4)"],
    ["SNI 2847:2019", "22.8.3.2; Tabel 21.2.1", "Tumpu: φ 0,65, Bn = 0,85 fc' A1 (A2 = A1).", "540; 491", "-", "Terverifikasi"],
    ["SNI 2847:2019", "25.4.2.1, Tabel 25.4.2.2, 25.4.2.4", "ld tarik: maks (Tabel; 300 mm); koef 1,7 atau 1,1.", "587-590", "-", "Terverifikasi"],
    ["SNI 2847:2019", "25.4.3.1", "ldh = maks (0,24 ψe ψc ψr fy db / (λ √fc'); 8 db; 150).", "591", "Panjang penyaluran ldh diukur dari penampang kritis sampai ujung luar kait", "Terverifikasi (penjelasan R25.4.3.1)"],
    ["SNI 2847:2019", "25.4.9.1, 25.4.9.2", "ldc = maks (0,24 fy db / √fc'; 0,043 fy db; 200).", "604", "-", "Terverifikasi"],
    ["SNI 2847:2019", "Tabel 20.6.1.3.1", "Selimut beton pada tanah 75 mm.", "482", "Dicor dan secara permanen kontak dengan tanah: 75", "Terverifikasi"],
]
TIDAK_ADA = [
    ["SNI 2847:2019 Tabel 22.9.4.2", "Koefisien friksi μ untuk geser-friksi sambungan kolom-cap.", "544", "nilai μ tidak terbaca di teks PDF; dipakai 0,6 [Asumsi 5.6]; cek manual", "belum ada di acuan"],
    ["Kekakuan tiang, penurunan, dan ukuran pile cap", "Dimensi denah cap, tulangan bawah cap, jarak tepi; cek 18.13.2.3.", "-", "Tahap 6", "belum ada di acuan"],
    ["SNI 2847:2019 Pasal 11.6.1 (dinding)", "Teks tidak dibuka; rasio ρl dari 4.8 (≥ 0,0025) dipakai.", "-", "", "belum ada di acuan"],
    ["Pembagian beban pelat ke titik (tributari) dan balok penggantung L-7", "Asumsi mekanika.", "-", "", "belum ada di acuan"],
]


# ================================================================== workbook
def _tt(lb, kepala, isi, rata, fmt=None, beku=False, ai=True):
    from format_dokumen import AI
    return lb.tabel(kepala, [[i + 1, *row] for i, row in enumerate(isi)], rata=rata, fmt=fmt, beku=beku, fill=AI if ai else None)


def buat_excel(keluar=BERKAS):
    from format_dokumen import AI, Lembar, set_font_bawaan
    h = hitung()
    c95 = h["t95"]
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    for s in NAMA:
        wb.create_sheet(s)
    mri.REF.clear()
    mri.LABEL_PAKAI.clear()
    ket = LABEL + " " + LABEL_AI
    N = "#,##0.0"
    tabs = {}

    # ---- Kombinasi
    def tambah_komb(lb):
        lb.kosong()
        lb.bagian("D", "Kombinasi per titik (urutan sama untuk semua titik)")
        isi = [[r[1], r[0], f"D {idn(r[2], 4)}; L {idn(r[3], 2)}; E {idn(r[4], 3)}", r[5], r[6]] for r in teks_kombinasi()]
        _tt(lb, ["No", "Kombinasi", "Jenis", "Jumlah", "Faktor", "Pasal"], [[x[0], x[1], x[3], x[2], x[4]] for x in isi], list("clccll"))
        lb.kosong()
        lb.catatan("E per kombinasi = ρ (QE arah utama + 0,3 QE arah ortogonal) dengan tanda ± pada kedua arah dan eksentrisitas ± (kasus EX+, EX-, EY+, EY-); faktor E di tabel sudah memuat ρ. "
                   "Kasus 'R' (rangka saja 25 %) TIDAK dipakai untuk reaksi: hanya untuk desain kolom sistem ganda (4.7); reaksi ke pondasi memakai model dengan inti (kasus E). "
                   "Reduksi guling 25 % (SNI 1726:2019 Pasal 7.13.4, hal PDF 102) tidak dipakai. Peningkatan tegangan izin 1,2 (Pasal 4.2.3.3) tidak dipakai: Tahap 6 "
                   "memutuskan sendiri. Reaksi kolom dan inti dihitung per konfigurasi 4.3 (K1 = tahap 1 sampai LT5 sementara, K2 = penuh); amplop K1 dan K2.")
    mri._lembar_hitung(wb, "Kombinasi", 4, "Kombinasi beban untuk reaksi ke pondasi", ket + " SNI 1726:2019 Pasal 4.2.2.3, 4.2.3.3, 7.4.2, 7.5.3.", baris_kombinasi(h), tambah_komb)

    # ---- Beban Tambahan (rumus)
    def tambah_beban(lb):
        lb.kosong()
        lb.catatan("Pelat: tributari 8 × 8 m per kolom (dalam 64 m², tepi 32, sudut 16) dipotong podium dan dikurangi kotak inti; pelat di dalam kotak inti ke inti; zona MRI memakai D dan L panel MRI. "
                   "Sloof: berat sendiri di bawah pelat setengah bentang ke tiap ujung; fasad di sloof tepi; R-09 di sloof dalam (5.4). Pit L-1..4 (t 0,45 m, keputusan 5.5) seluruhnya ke inti lif; "
                   "L-5..6 berimpit sloof as C (y 43) dibagi aturan tuas ke kolom x 52 dan x 60; L-7 lewat dua balok penggantung 400 × 800 (di tepi shaft y 30,0 dan 33,4) ke sloof x 36 dan x 44 lalu aturan tuas ke empat kolom. "
                   "Buffer pit dianggap beban hidup (5.5: 1,6 Pb). Gaya angkat air pit (Q100) tidak dikurangkan dari tekan; dicatat terpisah di 5.5 sebagai beban banjir. "
                   "Pelindung timur di sloof as 10 (x 84, y 54-60), utara di y 60 (resultan x 80,5, y 59-67 [Asumsi 5.6]): aturan tuas ke kolom; magnet dibagi empat kolom sudut panel MRI. "
                   "Per titik: lembar Tambahan per Titik.")
    mri._lembar_hitung(wb, "Beban Tambahan", 5, "Beban tambahan struktur tengah: masukan dan jumlah", ket, baris_beban(h), tambah_beban)

    # ---- Tambahan per Titik
    lb = Lembar(wb["Tambahan per Titik"], 6, "Beban tambahan struktur tengah per titik (D + L menurut kategori)", [5, 14, 12, 13, 13, 13, 13, 13, 13, 13, 13])
    lb.catatan(ket + " Jumlah kolom Σ = pelat + sloof + stek + pit + pelindung/magnet (rumus). Dibagi D dan L pada dua kolom terakhir (buffer pit dan beban hidup pelat = L).")
    lb.kosong()
    lb.bagian("A", "Beban tambahan per titik")
    r0, a0, a1 = _tt(lb, ["No", "Titik", "Kelompok", "Pelat LT1 (kN)", "Sloof + dinding (kN)", "Stek (kN)", "Pit lift (kN)", "Pelindung + magnet (kN)", "Σ (kN)", "D tambahan (kN)", "L tambahan (kN)"],
                     teks_tambahan(h), list("clcccccccccc"), fmt=[None, None, None, N, N, N, N, N, N, N, N], beku=True)
    ws = lb.ws
    for r in range(a0, a1 + 1):
        ws[f"{lb.kol(8)}{r}"] = f"=SUM({lb.kol(3)}{r}:{lb.kol(7)}{r})"
    tabs["tam"] = (ws.title, a0, a1, [lb.kol(i) for i in range(11)])

    # ---- Reaksi Titik
    lb = Lembar(wb["Reaksi Titik"], 7, "Reaksi per titik: D, L, dan gempa (tak terfaktor)", [5, 14, 8, 8, 12, 9, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12])
    lb.catatan(ket + " Reaksi dasar elemen LT1 (ujung bawah), tak terfaktor, tekan positif. D model dan L model = maksimum K1 dan K2 (OpenSees 4.3, 4.7, 4.8); kolom tangki opsi B memakai ukuran dan "
               "D 5.1 (selisih D opsi B dan A ditambahkan ke D tambahan). Gempa EX dan EY (kasus E, belum dikali ρ, eksentrisitas ±): nilai mutlak maksimum di K1, K2, dan tanda ±. "
               "Momen dasar kolom tidak dilanjutkan ke pile cap (kepala tiang sendi, keputusan 5.4); momen inti ada di lembar Amplop Reaksi.")
    lb.kosong()
    lb.bagian("A", "Titik reaksi: 70 kolom LT1 dan 7 inti")
    r0, a0, a1 = _tt(lb, ["No", "Titik", "x (m)", "y (m)", "Kelompok", "Ukuran b (mm)", "D model (kN)", "D tambahan (kN)", "D total (kN)", "L model (kN)", "L tambahan (kN)", "L total (kN)",
                          "EX: P maks (kN)", "EX: Vx maks (kN)", "EX: Vy maks (kN)", "EY: P maks (kN)", "EY: Vx maks (kN)", "EY: Vy maks (kN)"], teks_reaksi(h),
                     list("clccccccccccccccc") + ["c"], fmt=[None, None, "0.0", "0.0", None, None] + [N] * 12, beku=True)
    ws = lb.ws
    for r in range(a0, a1 + 1):
        ws[f"{lb.kol(8)}{r}"] = f"={lb.kol(6)}{r}+{lb.kol(7)}{r}"
        ws[f"{lb.kol(11)}{r}"] = f"={lb.kol(9)}{r}+{lb.kol(10)}{r}"
    lb.kosong()
    lb.catatan("Σ D total, Σ L total, dan Σ geser dasar EX/EY ada di lembar Cek Silang T-95.")

    # ---- Amplop Reaksi
    lb = Lembar(wb["Amplop Reaksi"], 8, "Amplop reaksi layan dan ultimit per titik", [5, 14, 12, 12, 12, 12, 12, 12, 30, 12, 12, 12, 12, 12, 12, 30])
    lb.catatan(ket + " Amplop semua kombinasi (lembar Kombinasi) dan dua konfigurasi. Layan = tegangan izin (SNI 1726:2019 4.2.3), ultimit = kekuatan (4.2.2). "
               "Kolom P 'dengan ΔP' = P + tambahan akibat geser sloof (kepala tiang sendi, momen kolom gempa ke sloof, V = (mA + mB) / L; bagian 5.4: kolom dalam M/2 per sloof, "
               "tepi M; inti tidak dibagi). Pmin negatif = tarik. Mu inti = |M| maksimum tiap sumbu (tidak bersamaan), Tu = torsi maksimum. Kolom: Mu = 0 (sendi).")
    lb.kosong()
    lb.bagian("A", "Amplop per titik")
    _tt(lb, ["No", "Titik", "Kelompok", "Pmax layan (kN)", "Pmax layan + ΔP (kN)", "Pmin layan (kN)", "Pmin layan + ΔP (kN)", "Vmax layan (kN)", "Penentu Pmax layan",
             "Pu maks + ΔP (kN)", "Pu min + ΔP (kN)", "Vu maks (kN)", "Mux inti (kNm)", "Muy inti (kNm)", "Tu inti (kNm)", "Penentu Pu min"], teks_amplop(h),
        list("clc") + ["c"] * 6 + ["l"] + ["c"] * 6 + ["l"], fmt=[None, None, None] + [N] * 5 + [None] + [N] * 6 + [None], beku=True)

    # ---- Delta P Sloof
    lb = Lembar(wb["Delta P Sloof"], 9, "Tambahan P kolom akibat geser sloof (kepala tiang sendi)", [5, 14, 12, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14])
    dsum = max(float(np.abs(sum(np.array(r["dP"][kf][j]) for r in h["titik"])).max()) for kf in ("K1", "K2") for j in ("ult", "lay"))
    lb.catatan(ket + " Asumsi 5.4: kepala tiang sendi, momen dasar kolom gempa diterima sloof. V sloof = (mA + mB) / L, L = 8 m; ΔP = ∓V pada kedua ujung: jumlah ΔP semua kolom = 0 per kombinasi "
               f"(maksimum |Σ ΔP| per kombinasi {dsum:.1e} kN). Momen D dan L kolom tidak dilanjutkan (gravitasi sudah di lembar 5.4).")
    lb.kosong()
    lb.bagian("A", "Pengaruh ΔP pada Pmax dan Pmin per kolom")
    _tt(lb, ["No", "Titik", "Kelompok", "ΔP maks ultimit (kN)", "ΔP maks layan (kN)", "Pmax layan (kN)", "Pmax layan + ΔP (kN)", "Pmin layan (kN)", "Pmin layan + ΔP (kN)", "Pu maks (kN)",
             "Pu maks + ΔP (kN)", "Pu min (kN)", "Pu min + ΔP (kN)"], teks_dp(h), list("clc") + ["c"] * 10, fmt=[None, None, None] + [N] * 10, beku=True)

    # ---- Ringkasan Tahap 6
    lb = Lembar(wb["Ringkasan Tahap 6"], 3, "Ringkasan reaksi untuk Tahap 6 (pile cap dan tiang)", [5, 14, 8, 8, 12, 10, 13, 13, 12, 13, 13, 12, 13, 13, 12, 36])
    lb.catatan(ket + " Masukan Tahap 6: satu baris per titik (70 kolom, 7 inti). P tekan positif, negatif = tarik; sudah termasuk beban tambahan struktur tengah (pelat LT1, sloof, stek, pit lift, MRI) "
               "dan ΔP sloof. Tidak ada reduksi guling. Layan = tegangan izin tanpa peningkatan 1,2; ultimit untuk desain pile cap dan stek. Mu dan Tu hanya untuk inti.")
    lb.kosong()
    lb.bagian("A", "Reaksi desain per titik")
    _tt(lb, ["No", "Titik", "x (m)", "y (m)", "Kelompok", "Ukuran b (mm)", "Pmax layan (kN)", "Pmin layan (kN)", "Vmax layan (kN)", "Pu maks (kN)", "Pu min (kN)", "Vu maks (kN)",
             "Mux (kNm)", "Muy (kNm)", "Tu (kNm)", "Catatan"], teks_tahap6(h), list("clccccccccccccc") + ["l"],
        fmt=[None, None, "0.0", "0.0", None, None] + [N] * 9 + [None], beku=True)

    # ---- Stek Kolom
    def tambah_stek(lb):
        lb.kosong()
        lb.catatan("Kait 90° menghadap sumbu kolom di dekat sisi bawah cap bila stek memikul lentur (18.13.2.2, hal PDF 448). Sengkang pengekang kolom (18.7.5.2-18.7.5.4) diteruskan "
                   "di dalam pile cap dan disalurkan untuk fy tarik (18.13.2.3, hal 448): wajib bila tepi kolom ≤ setengah tebal cap (600 mm) dari tepi cap (ukuran cap menunggu Tahap 6); "
                   "usulan AI: teruskan sengkang s 4.7 sampai di atas tulangan bawah cap. Tulangan atas cap bila ada uplift (18.13.2.4): tidak ada tarik pada titik mana pun. "
                   "Ringkasan penerusan di lembar Penerusan Ringkas. Kolom tangki opsi B (b 800 seragam, 5.6a) memakai tulangan LT2 yang sama dengan kelompok K-T 4.7 (20 D22, D13-125), sesuai hasil 5.6a.")
    mri._lembar_hitung(wb, "Stek Kolom", 10, "Penerusan kolom ke pile cap: penyaluran", ket + " SNI 2847:2019 Pasal 16.3 dan 18.13.2.", baris_stek(h), tambah_stek)

    # ---- Penerusan Inti
    def tambah_inti(lb):
        lb.kosong()
        lb.catatan("Tulangan vertikal badan dan elemen batas dasar inti dari 4.8 diteruskan ke pile cap inti dan disalurkan sesuai 18.13.2.1 (tarik pada bidang kontak). Elemen batas khusus "
                   "tidak diwajibkan oleh 4.8 (perlu_batas = tidak), jadi pengekangan 18.10.6.5(a) pada zona batas diteruskan ke cap (18.13.2.3). Mu dan Tu inti per titik di lembar Amplop Reaksi. "
                   "Pu min inti positif: tidak ada tarik. Ukuran dan tinggi cap inti diputuskan di Tahap 6. Ringkasan di lembar Penerusan Ringkas.")
    mri._lembar_hitung(wb, "Penerusan Inti", 11, "Penerusan inti (dinding geser) ke pile cap inti: penyaluran", ket + " SNI 2847:2019 Pasal 16.3.4.2 dan 18.13.2.", baris_inti(h), tambah_inti)

    # ---- Angkur Sloof Inti
    def tambah_angkur(lb):
        lb.kosong()
        lb.catatan("Kebutuhan: kait 90° dari sloof diteruskan ke bawah masuk pile cap inti (ldh dari 5.4: D29 381 mm > 297 mm tersedia di dinding 350). Batang bengkok ke bawah memerlukan tinggi cap ≥ ldh + "
                   "selimut 75 + tulangan bawah D32; batang lurus ke bawah memerlukan ≥ ld lurus + 75 dan melebihi cap 1.200 mm untuk D29. Jadi pakai kait; tinggi cap 1.200 cukup. "
                   "Gaya T Mpr sangat besar: ukuran denah cap inti dan jalur gaya ke tiang dirancang di Tahap 6. Ringkasan di lembar Penerusan Ringkas.")
    mri._lembar_hitung(wb, "Angkur Sloof Inti", 12, "Angkur sloof ke pile cap inti: penyaluran", ket + " Gaya T = As × 1,25 fy; ldh sama dengan 5.4 (18.8.5.1).", baris_angkur(h), tambah_angkur)

    # ---- Penerusan Ringkas
    lb = Lembar(wb["Penerusan Ringkas"], 13, "Ringkasan penerusan kolom, inti, dan sloof ke pile cap", [5, 16, 34, 14, 14, 14, 14, 14, 30, 14, 14, 14, 14, 14, 14, 12])
    lb.catatan(ket)
    lb.kosong()
    lb.bagian("A", "Kolom: stek ke pile cap (SNI 2847:2019 16.3 dan 18.13.2)")
    _tt(lb, ["No", "Kelompok", "Stek", "ldh (mm)", "ld lurus (mm)", "ldc (mm)", "Tersedia kait (mm)", "Tersedia lurus (mm)", "Sengkang pengekang di cap", "Pu maks (kN)", "φBn (kN)",
             "Pu min (kN)", "φTn stek (kN)", "Vu maks (kN)", "φVn friksi (kN)", "Status"], teks_stek(h), list("clc") + ["c"] * 5 + ["l"] + ["c"] * 6 + ["c"],
        fmt=[None, None, None, N, N, N, N, N, None, N, N, N, N, N, N, None], beku=True)
    lb.kosong()
    lb.catatan("φVn geser-friksi memakai μ 0,6 dan seluruh Ast stek [Asumsi 5.6; nilai Tabel 22.9.4.2 belum ada di acuan].")
    lb.kosong()
    lb.bagian("B", "Inti: penerusan tulangan vertikal ke pile cap inti")
    _tt(lb, ["No", "Kelompok", "Tulangan vertikal", "ldh (mm)", "ld lurus (mm)", "ldc (mm)", "Pu maks (kN)", "φBn (kN)", "Transversal di cap", "Pu min (kN)", "φTn badan (kN)", "Batang lurus"],
        teks_inti(h), list("clc") + ["c"] * 5 + ["l"] + ["c"] * 3, fmt=[None, None, None, N, N, N, N, "#,##0", None, N, "#,##0", None])
    lb.kosong()
    lb.bagian("C", "Angkur ujung sloof ke pile cap inti")
    _tt(lb, ["No", "Tipe dan lapis", "Tulangan", "T Mpr (kN)", "T per batang (kN)", "ldh (mm)", "Tersedia di inti (mm)", "Kurang (mm)", "Hasil", "Tinggi cap min, kait (mm)",
             "Tinggi cap min, lurus (mm)"], teks_angkur(h), list("clc") + ["c"] * 5 + ["l", "c", "c"], fmt=[None, None, None, N, N, N, N, N, None, N, N])
    lb.kosong()
    lb.bagian("D", "Sloof yang menyentuh inti (geometri as 5.4)")
    _tt(lb, ["No", "Inti", "Segmen (x, y) dan keterangan", "Tipe sloof", "Panjang kontak (m)"], teks_sloof_inti(h), list("clccc"), fmt=[None, None, None, None, "0.0"])

    # ---- Cek Silang T-95
    lb = Lembar(wb["Cek Silang T-95"], 14, "Cek silang T-95", [5, 66, 16, 16, 12, 12, 10, 60])
    lb.catatan(ket + " Toleransi ditetapkan sebelum membandingkan (konstanta TOL). Cara 1 = hasil model atau jumlah per titik; cara 2 = berat struktur 4.2, V ELF, atau rumus total.")
    lb.kosong()
    lb.bagian("A", "Cek silang")
    ws = lb.ws
    a2, b2 = c95["a"], c95["b"]
    kep = ["No", "Cek", "Cara 1", "Cara 2", "Selisih (%)", "Toleransi (%)", "Status", "Cara 1 / cara 2"]
    isi, rumus = [], {}

    def baris(teks, c1, c2v, tol, ket_):
        isi.append([len(isi) + 1, teks, None, None, None, tol, None, ket_])
        rumus[len(isi) - 1] = (c1, c2v)
    for kf in ("K2", "K1"):
        a = a2[kf]
        baris(f"(a) Σ D kolom (rangka) {kf} vs berat 4.2 tanpa dinding inti + setengah kolom bawah (kN)", f(a["kolom"]), f"={a['W']!r}-{a['W_dinding']!r}+{a['kol_setengah']!r}", TOL["a"],
              f"1: OpenSees 4.7 (= statika 4.7 {idn(a['statika_total'], 1)}). 2: ELF W {idn(a['W'], 1)} - dinding inti {idn(a['W_dinding'], 1)} + setengah kolom LT1-LT2 {idn(a['kol_setengah'], 1)}")
    for kf in ("K2", "K1"):
        a = a2[kf]
        baris(f"(a) Dinding inti {kf}: rumus 4.8 vs berat 4.2 + setengah tingkat bawah (kN)", f(a["dinding48"]), f(a["dinding42"]), TOL["a"],
              "1: kel × T × h × 0,85 × γc semua tingkat. 2: komponen 'dinding inti' ELF + setengah tingkat LT1-LT2")
    for kf in ("K2", "K1"):
        for cs in ("EX+", "EY+"):
            v = b2[(kf, cs)]
            baris(f"(b) Σ geser dasar {cs} {kf} (kolom + inti) vs V ELF (kN)", f(v["jumlah"]), f(v["V"]), TOL["b"], "1: Σ gaya dasar OpenSees. 2: tahap4_beban.elf V")
    kt = {"pelat": "Pelat LT1", "sloof": "Sloof", "stek": "Stek", "pit": "Pit lift", "mri": "Pelindung + magnet"}
    kol_kat = {"pelat": 3, "sloof": 4, "stek": 5, "pit": 6, "mri": 7}
    nama_tam, a0t, a1t, kls = tabs["tam"]
    idx_kat = {}
    for k in kt:
        idx_kat[len(isi)] = k
        baris(f"(c) Σ tambahan {kt[k]} ke semua titik (kN)", f"=SUM('{nama_tam}'!{kls[kol_kat[k]]}{a0t}:{kls[kol_kat[k]]}{a1t})", None, TOL["c"],
              "1: jumlah per titik (lembar Tambahan per Titik). 2: rumus total (lembar Beban Tambahan)")
    baris("(c) Σ tambahan total (kN)", f"=SUM('{nama_tam}'!{kls[8]}{a0t}:{kls[8]}{a1t})", "=" + mri._sub("{tot2}", ws.title), TOL["c"], "1: jumlah per titik. 2: Σ pelat + sloof + stek + pit + MRI")
    r0, a0, a1 = lb.tabel(kep, isi, rata=list("clcccccl"), fmt=[None, None, N, N, "0.000", "0.0", None, None])
    c2, c3 = lb.kol(2), lb.kol(3)
    cara2_ref = {"pelat": ("pld", "pll"), "sloof": ("sls",), "stek": ("stk",), "pit": ("pit_t",), "mri": ("mri_t",)}
    for i, (c1, c2v) in rumus.items():
        rr = a0 + i
        ws[f"{c2}{rr}"] = c1
        if c2v is None:
            ws[f"{c3}{rr}"] = "=" + "+".join(mri._sub("{" + k + "}", ws.title) for k in cara2_ref[idx_kat[i]])
        else:
            ws[f"{c3}{rr}"] = c2v
        ws[f"{lb.kol(4)}{rr}"] = f"=ABS({c3}{rr}-{c2}{rr})/{c2}{rr}*100"
        ws[f"{lb.kol(6)}{rr}"] = f'=IF({lb.kol(4)}{rr}<={lb.kol(5)}{rr},"Lolos","Tidak lolos")'
        ws[f"{lb.kol(5)}{rr}"].fill = PatternFill("solid", fgColor=AI)
        ws[f"{c3}{rr}"].fill = PatternFill("solid", fgColor=AI)
    lb.kosong()
    x = a2["K2"]
    lb.catatan(f"Cek d, Excel dihitung ulang = Python: semua sel rumus di lembar R dan kolom total dicocokkan oleh `cocokkan()` (toleransi {idn(TOL['d'], 1)} %). "
               f"Temuan: Σ D model K2 (kolom + inti) {idn(x['model'], 0)} kN, lebih besar dari berat 4.2 + setengah bawah ({idn(x['W'] + x['kol_setengah'] + x['din_setengah'], 0)} kN) sebesar "
               f"{idn(x['tributari_inti'], 0)} kN ({idn(x['tributari_inti'] / x['model'] * 100, 1)} % dari Σ D): tributari inti 4.8 (lajur pelat 1 m dan beban tangga) tumpang dengan beban pelat "
               "pada rangka. Ini konservatif dan tidak dikurangkan; keputusan di Ringkasan.")

    # ---- Ringkasan
    lb = Lembar(wb["Ringkasan"], 2, "Ringkasan temuan dan keputusan yang diminta dari Defsa", [5, 38, 78, 40, 44])
    lb.catatan(f"STATUS: {STATUS}. " + ket)
    lb.kosong()
    lb.bagian("A", "Temuan")
    _tt(lb, ["No", "Temuan", "Hasil kunci", "Keputusan Defsa", "Usulan AI"], [list(t_) for t_ in temuan(h)], list("clllll")[:5], beku=True)

    # ---- Acuan
    lb = Lembar(wb["Acuan"], 15, "Acuan yang dipakai dan statusnya", [5, 18, 30, 60, 12, 44, 34])
    lb.catatan(ket + " Halaman = nomor halaman PDF di acuan/privat (diverifikasi dengan pypdf, 21 Nov 2026).")
    lb.kosong()
    lb.bagian("A", "Pasal yang diverifikasi di PDF")
    _tt(lb, ["No", "Acuan", "Pasal", "Isi yang dipakai", "Hal. PDF", "Kutipan (≤ 15 kata)", "Status"], NAMA_PASAL, list("clllcll"), beku=True)
    lb.kosong()
    lb.bagian("B", "Tidak ada di acuan")
    _tt(lb, ["No", "Acuan", "Keterangan", "Hal. PDF", "Catatan", "Status"], TIDAK_ADA, list("clllcl"))

    # ---- Petunjuk
    lb = Lembar(wb["Petunjuk"], 1, "Petunjuk reaksi ke pondasi (langkah 5.6)", [6, 130])
    lb.catatan(f"STATUS: {STATUS}. " + ket)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        "Masukan Tahap 6: lembar Ringkasan Tahap 6 (reaksi layan dan ultimit per titik). Reaksi dasar kolom LT1 dan inti dari model OpenSees 4.3 (kasus E, dengan inti) K1 dan K2; ditambah beban struktur tengah 5.3-5.5.",
        "Kasus R (rangka saja 25 %) TIDAK dipakai: hanya untuk desain kolom pada sistem ganda (4.7). Reduksi guling SNI 1726:2019 7.13.4 tidak dipakai.",
        "Kepala tiang sendi (keputusan 5.4): momen dasar kolom ke sloof, M ke pile cap kolom = 0; geser sloof menambah ±ΔP pada ujung sloof. Inti: momen dan torsi penuh ke pile cap inti.",
        "Sel hijau diisi AI atas permintaan Defsa. Sel putih berisi rumus Excel (dihitung ulang dan dicocokkan dengan Python di cocokkan()).",
        "Lembar: Ringkasan; Ringkasan Tahap 6; Kombinasi; Beban Tambahan; Tambahan per Titik; Reaksi Titik; Amplop Reaksi; Delta P Sloof; Stek Kolom; Penerusan Inti; Angkur Sloof Inti; "
        "Penerusan Ringkas; Cek Silang T-95; Acuan.",
    ])], rata=list("cl"))
    for ws_ in wb:   # sheet berisi beberapa tabel berbeda: ulang kepala saat cetak menyesatkan
        if ws_.title not in ("Petunjuk", "Reaksi Titik", "Amplop Reaksi", "Delta P Sloof", "Ringkasan Tahap 6", "Tambahan per Titik"):
            ws_.print_title_rows = None
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


def temuan(h):
    """Tabel temuan (Temuan, Hasil kunci, Keputusan Defsa, Usulan AI) untuk Ringkasan dan MD."""
    c95 = h["t95"]
    top = rank_pmax(h, 5)
    pu_top = sorted(h["semua"], key=lambda r: -r["amp"]["ult"]["Pmax_dP"])[:3]
    pm = min(h["semua"], key=lambda r: r["amp"]["ult"]["Pmin_dP"])
    lif = [r for r in h["inti"] if r["id"] == "INTI-LIF"][0]
    dp_l = max(r["amp"]["lay"]["dP_maks"] for r in h["titik"])
    dp_u = max(r["amp"]["ult"]["dP_maks"] for r in h["titik"])
    st = stek_kolom(h)
    it = inti_penerusan(h)
    an = angkur_sloof(h)["baris"]
    sd = sum(r["D_model"] + r["D_tam"] for r in h["semua"])
    sl_ = sum(r["L_model"] + r["L_tam"] for r in h["semua"])
    return [
        ("Kombinasi", f"Ultimit 66 dan layan 98 kombinasi per konfigurasi (K1, K2): SNI 1726:2019 4.2.2.3, 4.2.3.3, 7.4.2 (Ev {idn(EV, 4)} D), 7.5.3 (100 % + 30 %). Kasus R tidak dipakai.",
         "Menyetujui.", "Setuju."),
        ("Reaksi total", f"Σ D total {idn(sd, 0)} kN, Σ L total {idn(sl_, 0)} kN (model + tambahan). Σ tambahan struktur tengah {idn(c95['c']['total1'], 0)} kN (pelat {idn(c95['c']['kat1']['pelat'], 0)}, "
         f"sloof {idn(c95['c']['kat1']['sloof'], 0)}, stek {idn(c95['c']['kat1']['stek'], 0)}, pit {idn(c95['c']['kat1']['pit'], 0)}, MRI {idn(c95['c']['kat1']['mri'], 0)} kN).", "Menyetujui.", "Setuju."),
        ("Reaksi kolom", "Pmax layan terbesar: " + "; ".join(f"{r['id']} {idn(r['amp']['lay']['Pmax_dP'], 0)} kN" for r in top) + f". Pu maks {pu_top[0]['id']} "
         f"{idn(pu_top[0]['amp']['ult']['Pmax_dP'], 0)} kN.", "Menyetujui tabel.", "Setuju; tabel di lembar Ringkasan Tahap 6."),
        ("Tarik (uplift)", f"Pu min terkecil {pm['id']} {idn(pm['amp']['ult']['Pmin_dP'], 0)} kN ({'tarik' if pm['amp']['ult']['Pmin_dP'] < 0 else 'tekan: tidak ada tarik'}); Pmin layan terkecil "
         f"{idn(min(r['amp']['lay']['Pmin_dP'] for r in h['semua']), 0)} kN.", "-", "Tidak ada tiang tarik; Tahap 6 memeriksa tekan dan geser."),
        ("Reaksi inti", f"INTI-LIF: Pmax layan {idn(lif['amp']['lay']['Pmax'], 0)}, Pu {idn(lif['amp']['ult']['Pmax'], 0)} kN, Mux/Muy {idn(lif['amp']['ult']['Mx'], 0)}/{idn(lif['amp']['ult']['My'], 0)} kNm, "
         f"Vu {idn(lif['amp']['ult']['Vmax'], 0)} kN, Tu {idn(lif['amp']['ult']['T'], 0)} kNm. Inti tangga: lembar Ringkasan Tahap 6.", "Menyetujui.", "Setuju."),
        ("ΔP sloof (kepala tiang sendi)", f"ΔP maks {idn(dp_u, 1)} kN ultimit, {idn(dp_l, 1)} kN layan; Σ ΔP = 0 per kombinasi.", "Pakai ΔP di reaksi atau tidak.", "Pakai (kecil, konservatif untuk Pmax)."),
        ("Stek kolom", "; ".join(f"{x['kel']}: ldh {idn(x['ldh'], 0)}, ld {idn(x['ld'], 0)}, ldc {idn(x['ldc'], 0)} mm vs tersedia {idn(x['ver'], 0)} (kait) / {idn(x['lur'], 0)} (lurus)" for x in st) + ".",
         "Menyetujui.", "Setuju; cap 1.200 mm cukup."),
        ("Penerusan inti", "; ".join(f"{x['kel']}: ldh {idn(x['ldh'], 0)} / ld {idn(x['ld'], 0)} mm ({'lurus cukup' if x['ok_ld'] else 'perlu kait'})" for x in it) + ".", "Menyetujui.", "Setuju."),
        ("Angkur sloof di inti", f"D29: ldh {idn(an[0]['ldh'], 0)} > 297 mm; kait ke bawah, tinggi cap min {idn(an[0]['h_cap_kait'], 0)} mm (lurus {idn(an[0]['h_cap_lurus'], 0)} > 1.200). T Mpr SL-1 atas "
         f"{idn(an[0]['T_mpr'], 0)} kN; Ftie {idn(angkur_sloof(h)['ftie'], 0)} kN.", "Ukuran cap inti di Tahap 6.", "Kait ke bawah; cap 1.200 cukup untuk angkur."),
        ("Cek silang T-95", "Lolos: lembar Cek Silang T-95 (a, b, c); (d) di cocokkan().", "-", "-"),
    ]


def cocokkan(berkas=BERKAS):
    """Hitung ulang di Excel, lalu bandingkan rumus dengan Python. Kembalikan (ok, pesan)."""
    from format_dokumen import hitung_ulang_excel
    ok, err = hitung_ulang_excel(berkas)
    if not ok:
        return False, f"Excel tidak bisa menghitung ulang: {err[:120]}"
    h = hitung()
    wb = openpyxl.load_workbook(berkas, data_only=True)
    pesan, n_cek = [], 0
    for nama, rows in semua_baris(h).items():
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
            if x is None or abs(x - rw["py"]) > max(1e-9, abs(rw["py"]) * TOL["d"] / 100):
                pesan.append(f"{nama}/{rw['label']}: Excel {x} vs Python {rw['py']}")
    from format_dokumen import KOLOM_AWAL
    ws = wb["Reaksi Titik"]
    for r in h["semua"]:
        for row in ws.iter_rows():
            for c in row:
                if c.value == r["id"] and c.column == KOLOM_AWAL + 1:     # kolom Titik
                    d_tot, l_tot = ws.cell(c.row, c.column + 7).value, ws.cell(c.row, c.column + 10).value
                    n_cek += 2
                    if abs(d_tot - (r["D_model"] + r["D_tam"])) > 1e-6 * max(1.0, abs(d_tot)):
                        pesan.append(f"Reaksi Titik/{r['id']}: D total Excel {d_tot} vs Python {r['D_model'] + r['D_tam']}")
                    if abs(l_tot - (r["L_model"] + r["L_tam"])) > 1e-6 * max(1.0, abs(l_tot)):
                        pesan.append(f"Reaksi Titik/{r['id']}: L total Excel {l_tot} vs Python {r['L_model'] + r['L_tam']}")
    ws = wb["Cek Silang T-95"]
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and len(c.value) > 3 and c.value[0] == "(" and c.value[1] in "abcd" and c.value[2] == ")":
                st = ws.cell(c.row, c.column + 5).value
                n_cek += 1
                if st != "Lolos":
                    pesan.append(f"T-95 {c.value}: status {st}")
    return not pesan, "; ".join(pesan) or f"semua {n_cek} rumus/cek Excel cocok dengan Python"


def ke_pdf(berkas=BERKAS, pdf=None):
    return mri.ke_pdf(berkas, pdf)


# ------------------------------------------------------------------ ringkasan .md
def _md_baris(rows, n=None):
    return "\n".join("| " + " | ".join(str(c) for c in (a if n is None else a[:n])) + " |" for a in rows)


def ringkas_kelompok(h):
    out = []
    kel = {}
    for r in h["semua"]:
        kel.setdefault(r["kel"], []).append(r)
    for nama, rs in kel.items():
        a = [r["amp"]["lay"] for r in rs]
        u = [r["amp"]["ult"] for r in rs]
        out.append([nama, len(rs), idn(max(x["Pmax_dP"] for x in a), 0), idn(min(x["Pmin_dP"] for x in a), 0), idn(max(x["Vmax"] for x in a), 0), idn(max(x["Pmax_dP"] for x in u), 0),
                    idn(min(x["Pmin_dP"] for x in u), 0), idn(max(x["Vmax"] for x in u), 0)])
    return out


def buat_md(keluar=KELUAR / "5.6 Reaksi ke Pondasi.md"):
    h = hitung()
    c95 = h["t95"]
    judul = f"5.6 Reaksi ke Pondasi ({STATUS if not KEPUTUSAN else 'disetujui Defsa ' + KEPUTUSAN.split(':')[0]})"
    a2, b2, cc = c95["a"], c95["b"], c95["c"]
    x = a2["K2"]
    sel = lambda c1, c2: idn(abs(c2 / c1 - 1) * 100, 2)   # noqa: E731
    top = rank_pmax(h, 5)
    pu_top = sorted(h["semua"], key=lambda r: -r["amp"]["ult"]["Pmax_dP"])[:5]
    pm = min(h["semua"], key=lambda r: r["amp"]["ult"]["Pmin_dP"])
    dp_l = max(r["amp"]["lay"]["dP_maks"] for r in h["titik"])
    dp_u = max(r["amp"]["ult"]["dP_maks"] for r in h["titik"])
    an = angkur_sloof(h)
    anb = an["baris"]
    kf_pen = {"K1": 0, "K2": 0}
    for r in h["semua"]:
        kf_pen[r["amp"]["lay"]["k_Pmax_dP"]] += 1
    tab_pasal = "\n".join(f"| {p[0]} {p[1]} | hal {p[3]} | {p[4]} | {p[5]} |" for p in NAMA_PASAL)
    tab_tidak = "\n".join(f"| {p[0]} | {p[1]} | {p[3]} | {p[4]} |" for p in TIDAK_ADA)
    teks = f"""# {judul}

Disusun AI 21 Nov 2026. Data simulasi. Rincian angka di `5.6 Reaksi ke Pondasi.xlsx` (`skrip/tahap5_penerusan.py`, uji `tests/test_tahap5_penerusan.py`).
Gaya dasar kolom dari 4.7 dan inti dari 4.8 (OpenSees 4.3, kasus E dengan inti, K1 dan K2), kolom tangki opsi B dari 5.1, pelat dari 5.3, sloof dari 5.4, pit lift dari 5.5.
Dari lembar **Ringkasan Tahap 6** pile cap dan tiang Tahap 6 dapat dihitung langsung.

## Acuan (halaman = nomor halaman PDF)

| Acuan | Halaman | Kutipan pendek | Status |
|---|---|---|---|
{tab_pasal}

Tidak ada di acuan (ditulis "belum ada di acuan"):

| Acuan | Keterangan | Halaman | Catatan |
|---|---|---|---|
{tab_tidak}

## Sistem dan asumsi

- Reaksi = gaya dasar elemen kolom LT1 (ujung bawah segmen LT1-LT2, tekan positif) tak terfaktor D, L, EX±, EY± dan satu titik per inti (7 inti, pusat inti 4.3). **Kasus R (rangka saja 25 %) tidak
  dipakai** (hanya untuk desain kolom sistem ganda, 4.7); reaksi memakai model dengan inti (kasus E). K1 dan K2 dihitung terpisah, tabel memakai amplop keduanya (Pmax layan ditentukan K1 di {kf_pen['K1']} titik, K2 di {kf_pen['K2']} titik).
- Kombinasi ultimit (SNI 1726:2019 4.2.2.1 no. 1-2, 4.2.2.3, 7.4.2): 1,4 D; 1,2 D + 1,6 L; ({idn(1.2 + EV, 4)}) D + L ± ρ E; ({idn(0.9 - EV, 4)}) D ± ρ E, ρ {idn(RHO, 1)}, Ev = 0,2 SDS D (SDS {idn(SDS, 3)}).
  Layan (tegangan izin, 4.2.3): D; D + L; ({idn(1 + 0.7 * EV, 4)}) D + 0,7 ρ E; ({idn(1 + 0.525 * EV, 4)}) D + 0,75 L + 0,525 ρ E; ({idn(0.6 - 0.7 * EV, 4)}) D + 0,7 ρ E. E = ρ (arah utama ± + 0,3 ortogonal ±), 7.5.3.
  Koefisien 0,14 dan 0,105 SDS tidak terbaca di teks PDF (hanya suku 0,7 dan 0,525); diturunkan dari 0,7 dan 0,525 × 0,2 SDS (7.4.2.2), cocok dengan angka yang diminta. Peningkatan tegangan izin 1,2 dan reduksi guling 25 % (7.13.4) tidak dipakai.
- Kepala tiang sendi (keputusan 5.4): M dasar kolom ke pile cap = 0; momen kolom gempa diterima sloof; geser sloof V = (mA + mB) / 8 m menambah ∓ΔP pada ujung sloof (bagian 5.4: kolom dalam M/2 per sloof,
  tepi M; inti tidak dibagi). Inti: P, V, M, T penuh ke pile cap inti.
- **[Asumsi 5.6]** Beban tambahan struktur tengah: pelat LT1 tributari 8 × 8 (sloof menerus diabaikan; pelat di dalam kotak inti ke inti; bukaan lif L-5..6 dan L-7 tidak dikurangi); sloof setengah bentang ke tiap ujung;
  fasad di sloof tepi, R-09 di sloof dalam (5.4); stek dari sisi bawah pelat (+12,60) ke kepala cap (+12,05) tanpa bukaan; pit L-1..4 (t 0,45) seluruhnya ke inti lif, L-5..6 ke kolom x 52 dan 60 pada sloof as C,
  L-7 lewat dua balok penggantung 400 × 800 di tepi shaft (y 30,0 dan 33,4) ke sloof x 36 dan x 44; buffer pit = beban hidup; dinding pelindung utara di y 60 (x 80,5), timur di sloof as 10, magnet dibagi empat kolom sudut panel.
  Gaya angkat air pit (Q100) tidak dikurangkan dari tekan; dicatat di 5.5 sebagai beban banjir. Pile cap fc' 35 (= kolom), tebal 1.200 mm [Asumsi 3.7], selimut 75 mm (Tabel 20.6.1.3.1, hal 482), tulangan bawah cap D32 [Asumsi 5.6].

## Tabel reaksi ringkas (kN; tabel lengkap 77 titik di Excel, lembar Ringkasan Tahap 6)

Per kelompok, amplop semua titik, P dengan ΔP sloof (negatif = tarik):

| Kelompok | n | Pmax layan | Pmin layan | Vmax layan | Pu maks | Pu min | Vu maks |
|---|---|---|---|---|---|---|---|
{_md_baris(ringkas_kelompok(h))}

Lima titik Pmax layan terbesar: {'; '.join(f"{r['id']} ({r['kel']}) {idn(r['amp']['lay']['Pmax_dP'], 0)} kN" for r in top)}.
Lima Pu maks terbesar: {'; '.join(f"{r['id']} {idn(r['amp']['ult']['Pmax_dP'], 0)} kN" for r in pu_top)}.
Pu min terkecil: **{pm['id']} {idn(pm['amp']['ult']['Pmin_dP'], 0)} kN** ({'tarik' if pm['amp']['ult']['Pmin_dP'] < 0 else 'tekan, tidak ada tarik di titik mana pun'}); penentu: {pm['amp']['ult']['n_Pmin_dP']} ({pm['amp']['ult']['k_Pmin_dP']}).

Inti (pile cap inti; P layan maks, Pu, Mu, Vu, Tu):

| Inti | Pmax layan | Pu maks | Pu min | Mux (kNm) | Muy (kNm) | Vu (kN) | Tu (kNm) |
|---|---|---|---|---|---|---|---|
{_md_baris([[r['id'], idn(r['amp']['lay']['Pmax'], 0), idn(r['amp']['ult']['Pmax'], 0), idn(r['amp']['ult']['Pmin'], 0), idn(r['amp']['ult']['Mx'], 0), idn(r['amp']['ult']['My'], 0), idn(r['amp']['ult']['Vmax'], 0), idn(r['amp']['ult']['T'], 0)] for r in h['inti']])}

Total: Σ D (model + tambahan) {idn(sum(r['D_model'] + r['D_tam'] for r in h['semua']), 0)} kN; Σ L {idn(sum(r['L_model'] + r['L_tam'] for r in h['semua']), 0)} kN; Σ tambahan struktur tengah {idn(cc['total1'], 0)} kN
(pelat {idn(cc['kat1']['pelat'], 0)}, sloof {idn(cc['kat1']['sloof'], 0)}, stek {idn(cc['kat1']['stek'], 0)}, pit {idn(cc['kat1']['pit'], 0)}, pelindung dan magnet {idn(cc['kat1']['mri'], 0)} kN).

## Pengaruh geser sloof (ΔP, kepala tiang sendi)

ΔP maksimum {idn(dp_u, 1)} kN (ultimit) dan {idn(dp_l, 1)} kN (layan); jumlah ΔP semua kolom = 0 per kombinasi. Pmax layan tertinggi tanpa ΔP {idn(max(r['amp']['lay']['Pmax'] for r in h['titik']), 1)} kN,
dengan ΔP {idn(max(r['amp']['lay']['Pmax_dP'] for r in h['titik']), 1)} kN. Pengaruhnya kecil karena momen dasar kolom pada sistem ganda kecil.

## Penerusan kolom ke pile cap (SNI 2847:2019 16.3, 18.13.2, 25.4)

Tersedia: tebal cap 1.200 - selimut 75 - D32 = {idn(tersedia()[0], 0)} mm (kait), {idn(tersedia()[1], 0)} mm (lurus).

| Kelompok | Stek | ldh | ld lurus | ldc | Sengkang di cap | Pu maks / φBn | Pu min / φTn | Vu / φVn friksi |
|---|---|---|---|---|---|---|---|---|
{chr(10).join(f"| {y['kel']} ({y['n']}) | {y['n_batang']} D{y['db']} | {idn(y['ldh'], 0)} | {idn(y['ld'], 0)} | {idn(y['ldc'], 0)} | D{kl.DS}-{idn(y['s_lo'], 0)}, {y['n_sengkang']} baris | {idn(y['pu_max'], 0)} / {idn(y['phiBn'], 0)} | {idn(y['pu_min'], 0)} / {idn(y['phiTn'], 0)} | {idn(y['vu'], 0)} / {idn(y['phiVn'], 0)} |" for y in stek_kolom(h))}

Kait 90° dekat sisi bawah cap menghadap sumbu kolom (18.13.2.2); sengkang pengekang kolom diteruskan ke dalam cap dan disalurkan untuk fy (18.13.2.3, wajib bila tepi kolom ≤ 600 mm dari tepi cap);
As dasar ≥ 0,005 Ag (16.3.4.1) terpenuhi; tumpu φBn (22.8.3.2) jauh melebihi Pu maks; tidak ada tarik (18.13.2.4 tidak menambah tulangan atas). Kolom tangki opsi B (800 seragam, 5.6a) memakai tulangan LT2 5.6a, identik dengan kelompok K-T 4.7.

## Penerusan inti ke pile cap inti

| Kelompok | Tulangan vertikal | ldh | ld lurus | ldc | Batang lurus | Transversal di cap | Pu maks / φBn |
|---|---|---|---|---|---|---|---|
{chr(10).join(f"| {y['kel']} ({len(y['anggota'])} inti) | D{y['db_v']}-{y['s_v']}; {y['n_batas']} D{y['db_batas']} per ujung | {idn(y['ldh'], 0)} | {idn(y['ld'], 0)} | {idn(y['ldc'], 0)} | {'cukup' if y['ok_ld'] else 'perlu kait'} | {y['trans']['jenis']}{(': D' + str(y['trans']['db']) + '-' + idn(y['trans']['s'], 0)) if y['trans'].get('s') else ''} | {idn(y['pu_max'], 0)} / {idn(y['phiBn'], 0)} |" for y in inti_penerusan(h))}

Tulangan vertikal badan dan elemen batas diteruskan ke pile cap inti dan disalurkan tarik pada bidang kontak (18.13.2.1); pengekangan zona batas diteruskan ke cap (18.13.2.3). Pu min inti positif, tidak ada uplift.

## Angkur sloof ke pile cap inti

Kait 90° ke dinding inti 350 tidak cukup (ldh D29 {idn(anb[0]['ldh'], 0)} mm > 297 mm). Gaya T = As × 1,25 fy: SL-1 atas {idn(anb[0]['T_mpr'], 0)} kN (10 D29), bawah {idn(anb[1]['T_mpr'], 0)} kN; Ftie {idn(an['ftie'], 0)} kN (5.4).
Kebutuhan: batang sloof dikait 90° ke bawah masuk pile cap inti; tinggi cap minimum {idn(anb[0]['h_cap_kait'], 0)} mm (kait D29) atau {idn(anb[0]['h_cap_lurus'], 0)} mm bila batang lurus (melebihi cap 1.200 mm), jadi **kait**; ukuran denah cap inti
dan jalur gaya ke tiang diputuskan di Tahap 6. Geometri: hanya satu segmen sloof SL-1 (as 6, x 52, y 35-43) melintas di dalam kotak inti lif; sisanya berimpit dengan garis dinding inti.

## Cek silang T-95 (toleransi ditetapkan dulu)

| Cek | Cara 1 | Cara 2 | Selisih | Toleransi |
|---|---|---|---|---|
| (a) Σ D kolom K2 vs berat 4.2 tanpa dinding inti + setengah kolom | {idn(x['kolom'], 0)} kN | {idn(x['rangka2'], 0)} kN | {sel(x['kolom'], x['rangka2'])} % | {idn(TOL['a'], 1)} % |
| (a) Σ D kolom K1 | {idn(a2['K1']['kolom'], 0)} kN | {idn(a2['K1']['rangka2'], 0)} kN | {sel(a2['K1']['kolom'], a2['K1']['rangka2'])} % | {idn(TOL['a'], 1)} % |
| (a) dinding inti K2: rumus 4.8 vs 4.2 | {idn(x['dinding48'], 0)} kN | {idn(x['dinding42'], 0)} kN | {sel(x['dinding48'], x['dinding42'])} % | {idn(TOL['a'], 1)} % |
| (b) Σ geser dasar EX+ K2 vs V ELF | {idn(b2[('K2', 'EX+')]['jumlah'], 1)} kN | {idn(b2[('K2', 'EX+')]['V'], 1)} kN | {sel(b2[('K2', 'EX+')]['jumlah'], b2[('K2', 'EX+')]['V'])} % | {idn(TOL['b'], 1)} % |
| (b) Σ geser dasar EY+ K1 vs V ELF | {idn(b2[('K1', 'EY+')]['jumlah'], 1)} kN | {idn(b2[('K1', 'EY+')]['V'], 1)} kN | {sel(b2[('K1', 'EY+')]['jumlah'], b2[('K1', 'EY+')]['V'])} % | {idn(TOL['b'], 1)} % |
| (c) Σ tambahan: jumlah per titik vs rumus total | {idn(cc['total1'], 1)} kN | {idn(cc['total2'], 1)} kN | {sel(cc['total1'], cc['total2'])} % | {idn(TOL['c'], 1)} % |
| (d) Excel dihitung ulang vs Python | rumus Excel | Python | lihat `cocokkan()` | {idn(TOL['d'], 1)} % |

Temuan (a): Σ D model (kolom + inti) K2 {idn(x['model'], 0)} kN, berat 4.2 + setengah tingkat bawah {idn(x['W'] + x['kol_setengah'] + x['din_setengah'], 0)} kN; selisih {idn(x['tributari_inti'], 0)} kN
({idn(x['tributari_inti'] / x['model'] * 100, 1)} %) = tributari inti di 4.8 (lajur pelat 1 m di sekeliling inti dan beban tangga) yang tumpang dengan beban pelat pada rangka. Konservatif; tidak dikurangkan.

## Data yang masih kurang

1. Ukuran denah pile cap, jarak tepi, dan tulangan bawah cap (Tahap 6): dipakai tebal 1.200 mm dan D32 sebagai asumsi; cek 18.13.2.3 (tepi kolom ke tepi cap).
2. Kekakuan tiang dan penurunan (Tahap 6): kepala tiang sendi atau jepit menentukan momen kolom ke cap dan ΔP sloof.
3. Nilai μ geser-friksi (SNI 2847:2019 Tabel 22.9.4.2) tidak terbaca di PDF; dipakai 0,6 [Asumsi 5.6].
4. Kolom tangki opsi B: 800 seragam (keputusan Defsa 21 Nov 2026, 5.6a); stek memakai tulangan LT2 5.6a (20 D22, D13-125), sama dengan K-T 4.7.
5. Tata letak dinding pelindung utara MRI (dipakai y 60, x 77-84) dan lokasi balok penggantung L-7.

## Yang perlu diputuskan Defsa

1. **ΔP sloof di reaksi Tahap 6**: pakai Pmax dan Pmin dengan ΔP (maks {idn(dp_u, 1)} kN ultimit) atau tanpa? Usulan AI: pakai (kecil dan konservatif; kepala tiang sendi adalah keputusan 5.4).
2. **Ukuran dan tinggi cap inti minimum**: angkur sloof D29 butuh kait ke bawah dan tinggi ≥ {idn(anb[0]['h_cap_kait'], 0)} mm; usulan AI: cap inti 1.200 mm (sama kolom), denah ditentukan di Tahap 6 menurut jalur gaya T Mpr.
3. **Reaksi K1 atau K2**: tabel memakai amplop K1 dan K2 (K2 menentukan di {kf_pen['K2']} dari 77 titik untuk Pmax layan). Usulan AI: pakai amplop, karena K1 adalah tahap konstruksi/operasi awal.
4. **Kasus R tidak dipakai** untuk reaksi (hanya desain kolom sistem ganda). Usulan AI: setuju.
5. **Tumpang tributari inti 4.8** ({idn(x['tributari_inti'], 0)} kN, {idn(x['tributari_inti'] / x['model'] * 100, 1)} % Σ D): dipertahankan atau dikurangi? Usulan AI: pertahankan (konservatif), tinjau ulang bila tiang Tahap 6 menentukan.
6. **Sloof SL-1 as 6 (x 52, y 35-43) melintas di dalam inti lif** dan kolom (52,35), (52,43) berada pada garis dinding inti: usulan AI hapus sloof itu dan gabungkan kedua kolom ke pile cap inti di Tahap 6.
7. **Kolom tangki opsi B**: terjawab di 5.6a, 800 seragam (disetujui Defsa 21 Nov 2026); tulangan LT2 5.6a dipakai untuk stek.

8. **P-M kolom tangki (opsi B)**: dikerjakan di 5.6a (P-M, kolom kuat balok lemah, stek); reaksi 5.6 diperbarui untuk b 800.
9. **ΔP sloof memakai kasus E (dengan inti)**, sedangkan desain sloof 5.4 memakai momen kolom dari amplop 4.7 (termasuk kasus R rangka 25 %, momen sampai 1.047 kNm). Bila momen 5.4 dipakai, ΔP bisa naik sampai sekitar 2M/L ≈ 260 kN di kolom tangki. Usulan AI: reaksi Tahap 6 memakai E (keseimbangan dengan geser dasar), desain sloof tetap 5.4 (konservatif).

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
