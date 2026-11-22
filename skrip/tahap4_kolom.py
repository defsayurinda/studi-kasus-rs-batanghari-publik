"""Tahap 4 langkah 4.7: desain kolom SRPMK dan hubungan balok-kolom (HBK) sistem ganda (SNI 2847:2019 Pasal 18.7, 18.8).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (20 Nov 2026); disetujui Defsa
20 Nov 2026 (kolom transfer tangki 950/800). Kunci jawaban tidak dibuka.

Gaya dalam: model 3D tahap4_model (K1 dan K2, diselubungi) dengan ukuran balok hasil 4.6 (`tahap4_balok.rancang()`).
Beban gravitasi: pelat dua arah sebagai beban segitiga sungguhan pada balok (16 beban titik per sisi, total q L²/4;
bukan q L/3 setara momen agar gaya aksial kolom tidak berlebih 33 %), berat badan balok, dinding/parapet, beban titik
balok anak tangki dan tiang dek helipad (4.6), berat sendiri kolom di ujung atas. Dinding inti tidak memikul gravitasi
di model (diafragma hanya mengikat horizontal) sehingga gaya aksial kolom konservatif. Gempa pola ELF V = V ELF,
torsi tak terduga 0,05 Ax, 100 % + 30 %, ρ 1,3, Ev 0,2 SDS D; model rangka saja 25 % (SNI 1726 Pasal 7.2.5.1).

Acuan SNI 2847:2019 (halaman cetak = halaman PDF - 22): Tabel 6.3.2.1 hal. 97 (lebar sayap efektif); Tabel 21.2.1
hal. 469 dan 21.2.4.3 hal. 474 (φ geser 0,75, joint 0,85); Tabel 21.2.2 hal. 471 (φ 0,65-0,90, εty 0,002); Tabel
22.4.2.1 hal. 480 (Pn,max 0,80 Po); 22.5.6.1 hal. 486 (Vc dengan aksial tekan); 25.2.3 hal. 560 (spasi bersih kolom
>= 40 mm, 1,5 db); 18.7.2.1 hal. 385 (dimensi); 18.7.3.2 hal. 385 (ΣMnc >= 1,2 ΣMnb, tulangan pelat dalam lebar efektif
ikut Mnb); 18.7.4.1 hal. 386 (0,01-0,06 Ag); 18.7.5.1 hal. 386 (lo); 18.7.5.2 hal. 387-390 (hx <= 350, semua batang
ditopang bila Pu > 0,3 Ag fc'); 18.7.5.3 hal. 389 (s <= b/4, 6db, so); Tabel 18.7.5.4 hal. 389-390 (Ash, kf, kn);
18.7.5.5 hal. 390 (di luar lo 6db, 150); 18.7.6 hal. 391-392 (Ve dari Mpr, Vc = 0); 18.8.2-18.8.5 hal. 392-396
(1,25 fy, 20 db, h joint >= 0,5 h balok, Tabel 18.8.4.1 γ 1,7/1,2/1,0, muka terkekang bila lebar balok >= 3/4 lebar
joint, Aj, ldh = fy db/(5,4 √fc')).
"""
from __future__ import annotations

import functools
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import cache_analisis  # noqa: E402
import tahap4_balok as tbk  # noqa: E402
import tahap4_beban as tb  # noqa: E402
import tahap4_model as tm  # noqa: E402
import tahap4_pelat as tp  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "04 Struktur Atas"
BERKAS = KELUAR / "4.7 Desain Kolom dan HBK.xlsx"
LABEL = tb.LABEL
STATUS = "disetujui Defsa 20 Nov 2026"
FC, FY, FYT, ES = 35.0, 420.0, 420.0, 200000.0   # kolom fc' 35 (3.6, tahap4_model), BjTS 420B
FC_B = tbk.FC                                    # balok dan pelat fc' 30
BETA1 = 0.85 - 0.05 * (FC - 28) / 7              # Tabel 22.2.2.4.3: 0,80
SEL = 40.0                                       # mm selimut ke sengkang (Tabel 20.6.1.3.1)
DS = 13                                          # sengkang dan ikat silang D13
EPS_TY = 0.002                                   # 21.2.2.1, BjTS 420
PHI_V, PHI_J = 0.75, 0.85
RHO_PAKAI = 0.04    # batas praktis sambungan lewatan [Asumsi]; SNI 18.7.4.1 = 0,06
DB_KOLOM = (22, 25, 29, 32)
L_GRID = tbk.L_GRID
URUT_LV = ["LT2", "LT3", "LT4", "LT5", "LT6", "ATAP"]   # tingkat di ujung atas segmen kolom
TANGKI_KOLOM = {(x, y) for x in tbk.TANGKI_X for y in (67.0, 75.0)}
# Keputusan Defsa 20 Nov 2026: kolom penumpu balok transfer tangki diperbesar (usulan 4.7), menerus LT1-LT3.
UKURAN_KOLOM = {(lv, x, y): (0.95 if abs(x - 68.0) < 0.01 else 0.80)
                for lv in ("LT2", "LT3") for (x, y) in TANGKI_KOLOM}


def luas(db):
    return math.pi * db ** 2 / 4


def floor25(s):
    return math.floor(s / 25 + 1e-9) * 25


# ------------------------------------------------------------------ penampang kolom dan diagram interaksi
def baris_batang(b, m, db):
    """Baris tulangan (jarak dari serat tekan, mm) dan luasnya untuk kolom bujur sangkar b (m), m batang per sisi."""
    h = b * 1000
    d0 = SEL + DS + db / 2
    ys = np.linspace(d0, h - d0, m)
    n = np.array([m] + [2] * (m - 2) + [m])
    return ys, n * luas(db)


def titik_pm(c, b, ys, as_, fy=FY):
    """Pn (kN), Mn (kNm), εt, φ untuk kedalaman sumbu netral c (mm, array); tekan positif, lentur satu sumbu."""
    h = b * 1000
    c = np.atleast_1d(np.asarray(c, float))
    a = np.minimum(BETA1 * c, h)
    eps = 0.003 * (c[:, None] - ys[None, :]) / c[:, None]
    fs = np.clip(ES * eps, -fy, fy) - 0.85 * FC * (ys[None, :] < a[:, None])
    cc = 0.85 * FC * a * h
    pn = (cc + (fs * as_).sum(1)) / 1e3
    mn = (cc * (h / 2 - a / 2) + (fs * as_ * (h / 2 - ys)).sum(1)) / 1e6
    et = 0.003 * (ys.max() - c) / c
    phi = np.clip(0.65 + 0.25 * (et - EPS_TY) / (0.005 - EPS_TY), 0.65, 0.90)   # Tabel 21.2.2 (sengkang)
    return pn, mn, et, phi


@functools.lru_cache(maxsize=None)
def diagram(b, m, db, fy=FY):
    """Diagram rapat: (Pn, Mn) nominal dan (φPn, φMn) desain berurutan menurut P; φPn dibatasi 0,65 × 0,80 Po."""
    ys, as_ = baris_batang(b, m, db)
    h = b * 1000
    c = np.concatenate([np.geomspace(1.0, 0.1 * h, 60), np.linspace(0.1 * h, 3.0 * h, 400)[1:]])
    pn, mn, _, phi = titik_pm(c, b, ys, as_, fy)
    ast = as_.sum()
    po = (0.85 * FC * (h * h - ast) + fy * ast) / 1e3                  # Pers. 22.4.2.2
    pt = -fy * ast / 1e3
    pn = np.concatenate([[pt], pn])
    mn = np.concatenate([[0.0], mn])
    phi = np.concatenate([[0.90], phi])
    naik = np.concatenate([[True], pn[1:] > np.maximum.accumulate(pn)[:-1] + 1e-6])   # buang ujung jenuh (a = h)
    pn, mn, phi = pn[naik], mn[naik], phi[naik]
    assert np.all(np.diff(pn) > 0), "Pn harus naik terhadap c"
    php = phi * pn
    assert np.all(np.diff(php) > 0), "φPn harus naik terhadap c"
    return {"Pn": pn, "Mn": mn, "phiPn": php, "phiMn": phi * mn, "Po": po, "Pt": pt, "Ast": ast,
            "phiPmax": 0.65 * 0.80 * po}


def mn_pada(dg, p, desain=False):
    """Mn (atau φMn) pada gaya aksial p (kN); nan bila di luar diagram (φPn,max atau tarik murni)."""
    p = np.asarray(p, float)
    kp, km = ("phiPn", "phiMn") if desain else ("Pn", "Mn")
    out = np.interp(p, dg[kp], dg[km], left=np.nan, right=np.nan)
    if desain:
        out = np.where(p > dg["phiPmax"], np.nan, out)
    return out


def pilihan_tulangan(b):
    """Susunan (Ast, m, db) yang sah: ρ 0,01-RHO_PAKAI, spasi bersih >= max(40, 1,5 db) (25.2.3), urut Ast."""
    out = []
    for db in DB_KOLOM:
        for m in range(4, 13):   # >= 12 batang: pengekangan merata [Asumsi praktis]
            ast = 4 * (m - 1) * luas(db)
            rho = ast / (b * 1000) ** 2
            bersih = (b * 1000 - 2 * SEL - 2 * DS - db) / (m - 1) - db
            if 0.01 <= rho <= RHO_PAKAI and bersih >= max(40.0, 1.5 * db):
                out.append((ast, m, db))
    return sorted(out)


# ------------------------------------------------------------------ analisis 3D: gaya kolom
def kunci_kolom(k):
    return (k["lv"], k["x"], k["y"])


def _sisi_pelat(b):
    """(D, L) kPa pelat di tiap sisi balok yang ada pelatnya."""
    from shapely.geometry import Point
    xm, ym = (b["x1"] + b["x2"]) / 2, (b["y1"] + b["y2"]) / 2
    nx, ny = (0.0, 2.0) if b["arah"] == "X" else (2.0, 0.0)
    out = []
    for s in (1, -1):
        px, py = xm + s * nx, ym + s * ny
        if b["wil"].buffer(0.01).contains(Point(px, py)):
            out.append(tbk.beban_panel(b["lv"], px, py))
    return out


TITIK_SEGITIGA = np.arange(0.25, L_GRID, 0.5)   # 16 titik @ 0,5 m
BOBOT_SEGITIGA = (1 - np.abs(TITIK_SEGITIGA - L_GRID / 2) / (L_GRID / 2)) * (L_GRID / 2) * 0.5   # × q → kN


def beban_gravitasi(ops, m, konfig, kasus):
    """Pasang beban D atau L; kembalikan jumlah beban vertikal (kN) untuk cek statika T-78."""
    total = 0.0
    for b in m["balok"]:
        d_, l_, _, _ = tbk.beban_balok(b)
        sisi = _sisi_pelat(b)
        qd, ql = sum(s[0] for s in sisi), sum(s[1] for s in sisi)
        w = (d_ - qd * L_GRID / 3) if kasus == "D" else (l_ - ql * L_GRID / 3)   # sisa: badan, dinding, tangki
        ops.eleLoad("-ele", b["ele"], "-type", "-beamUniform", 0.0, -w)
        total += w * L_GRID
        q = qd if kasus == "D" else ql
        for x, wb in zip(TITIK_SEGITIGA, BOBOT_SEGITIGA):
            ops.eleLoad("-ele", b["ele"], "-type", "-beamPoint", 0.0, -q * wb, x / L_GRID)
            total += q * wb
        for pd, pl, a in tbk.beban_titik(b, konfig):
            p = pd if kasus == "D" else pl
            ops.eleLoad("-ele", b["ele"], "-type", "-beamPoint", 0.0, -p, a / L_GRID)
            total += p
    if kasus == "D":
        for k in m["kolom"]:
            h = tm.TINGGI[k["lv"]]
            w = tb.GAMMA_C * k["b"] ** 2 * h
            ops.load(ops.eleNodes(k["ele"])[1], 0, 0, -w, 0, 0, 0)
            total += w
    return total


@cache_analisis.disk
def analisis(konfig="K2", ukuran_balok=None):
    """localForce per kolom untuk D, L, E/R X±, Y±; plus jumlah beban dan reaksi aksial dasar (T-78)."""
    import openseespy.opensees as ops
    tm.UKURAN_BALOK = dict(ukuran_balok or {})
    tm.UKURAN_KOLOM = dict(UKURAN_KOLOM)
    hasil, statika, info = {}, {}, {}
    try:
        for kasus in ("D", "L"):
            m = tm.bangun(konfig)
            ops.timeSeries("Linear", 1)
            ops.pattern("Plain", 1, 1)
            total = beban_gravitasi(ops, m, konfig, kasus)
            tm._analisis_statik()
            hasil[kasus] = {kunci_kolom(k): np.array(ops.eleResponse(k["ele"], "localForce")) for k in m["kolom"]}
            dasar = sum(hasil[kasus][kunci_kolom(k)][0] for k in m["kolom"] if k["i"] == 1)
            statika[kasus] = (total, dasar)
            info = {kunci_kolom(k): k for k in m["kolom"]}
            balok = m["balok"]
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
                        kunci_kolom(k): np.array(ops.eleResponse(k["ele"], "localForce")) for k in m["kolom"]}
    finally:
        tm.UKURAN_BALOK = {}
        tm.UKURAN_KOLOM = {}
    return {"gaya": hasil, "statika": statika, "kolom": info, "balok": balok, "konfig": konfig}


def ujung(lf):
    """[[P, Mx, My, Vx, Vy] ujung bawah, ... ujung atas]; P tekan positif. Transf 1: z lokal = X global, y lokal =
    -Y global, sehingga Mz lokal = momen terhadap sumbu X (goyangan Y), My lokal = terhadap Y (goyangan X)."""
    return np.array([[lf[0], lf[5], lf[4], lf[2], lf[1]], [-lf[6], lf[11], lf[10], lf[2], lf[1]]])


def kombinasi(h, k):
    """Gaya terfaktor kolom k: array (n_komb, 2 ujung, 5) dan penanda kombinasi gempa."""
    g = h["gaya"]
    d, l_ = ujung(g["D"][k]), ujung(g["L"][k])
    ev = 0.2 * tb.SDS
    out, gempa = [1.4 * d, 1.2 * d + 1.6 * l_], [False, False]
    for nama in ("E", "R"):
        for a, o in (("X", "Y"), ("Y", "X")):
            for s1 in "+-":
                ea = ujung(g[f"{nama}{a}{s1}"][k])
                for s2 in "+-":
                    eo = ujung(g[f"{nama}{o}{s2}"][k])
                    for sg in (1, -1):
                        for so in (1, -1):
                            eq = tb.RHO * (sg * ea + 0.3 * so * eo)
                            out += [(1.2 + ev) * d + l_ + eq, (0.9 - ev) * d + eq]
                            gempa += [True, True]
    return np.array(out), np.array(gempa)


def kelompok_kolom(lv, x, y, b):
    if lv in ("LT2", "LT3") and (x, y) in TANGKI_KOLOM:
        return f"{'K-T68' if abs(x - 68.0) < 0.01 else 'K-T'} {lv}"
    return f"{'K-M' if b < 0.7 else 'K-P'} {lv}"


def urut_kelompok(nama):
    z, lv = nama.split()
    return URUT_LV.index(lv), {"K-P": 0, "K-T": 1, "K-T68": 2, "K-M": 3}[z]


def gaya_kolom(hs):
    """Gaya terfaktor per kolom, K1 ∪ K2: {kunci: {'F': (n, 2, 5), 'gempa': (n,), 'b', 'kelompok'}}."""
    out = {}
    for h in hs:
        for k, info in h["kolom"].items():
            f, g = kombinasi(h, k)
            if k in out:
                out[k]["F"] = np.concatenate([out[k]["F"], f])
                out[k]["gempa"] = np.concatenate([out[k]["gempa"], g])
            else:
                out[k] = {"F": f, "gempa": g, "b": info["b"], "kelompok": kelompok_kolom(*k, info["b"])}
    return out


# ------------------------------------------------------------------ balok di joint: Mn dengan pelat, Mpr
@functools.lru_cache(maxsize=1)
def tulangan_pelat():
    """As pelat (mm²/m) terbesar di lajur kolom 4.5: atas (negatif dalam) dan bawah (positif) [Asumsi konservatif:
    menambah ΣMnb]."""
    atas = bawah = 0.0
    for p in tp.PANEL:
        r = tp.desain_panel(*p)
        for x in r["baris"]:
            if x["lajur"].startswith("kolom"):
                if x["posisi"] == "neg_int":
                    atas = max(atas, x["As_ada"])
                elif x["posisi"] == "pos":
                    bawah = max(bawah, x["As_ada"])
    return atas, bawah


def sayap(bw, hc, tepi):
    """Lebar sayap efektif di luar badan, satu sisi (m), Tabel 6.3.2.1."""
    sw, ln = L_GRID - bw, L_GRID - hc
    return min(6 * tp.H, sw / 2, ln / 12) if tepi else min(8 * tp.H, sw / 2, ln / 8)


def momen_balok(g, hc, tepi, fy=FY):
    """Mn- (dengan tulangan pelat dalam lebar efektif) dan Mn+ (sayap tekan) balok kelompok g (kNm)."""
    bw, h = g["b"], g["h"]
    s_atas, s_bawah = tulangan_pelat()
    lebar = sayap(bw, hc, tepi) * (1 if tepi else 2)
    lap = [(g["atas"]["As"], g["atas"]["d"]),
           (s_atas * lebar, h - (tp.SELIMUT + tp.DB / 2)),
           (s_bawah * lebar, h - (tp.H - tp.SELIMUT - tp.DB / 2))]
    t = sum(a for a, _ in lap) * fy
    a = t / (0.85 * FC_B * bw * 1000)
    mneg = sum(a_ * fy * (d * 1000 - a / 2) for a_, d in lap) / 1e6
    be = bw + lebar
    ab = g["bawah"]["As"] * fy / (0.85 * FC_B * be * 1000)
    mpos = g["bawah"]["As"] * fy * (g["bawah"]["d"] * 1000 - ab / 2) / 1e6
    return mneg, mpos


@functools.lru_cache(maxsize=1)
def balok_rancang():
    return tbk.rancang()


def peta_balok():
    """{kunci balok: (arah, (x1, y1), (x2, y2), lv, kelompok dict)} untuk K1 ∪ K2."""
    r = balok_rancang()
    kel = {x["kelompok"]: x for x in r["kelompok"]}
    out = {}
    for k, nama in tbk._kunci_kelompok().items():
        lv, x1, y1, x2, y2 = k
        out[k] = {"lv": lv, "p1": (x1, y1), "p2": (x2, y2), "arah": "X" if y1 == y2 else "Y", "kel": kel[nama],
                  "tepi": "tepi" in nama}
    return out


# ------------------------------------------------------------------ joint
def joint_daftar(gk):
    """Semua joint (ujung atas kolom) dengan kolom bawah, kolom atas, dan balok tiap arah."""
    pb = peta_balok()
    kol = set(gk)
    joint = []
    for (lv, x, y) in kol:
        i = URUT_LV.index(lv)
        atas = (URUT_LV[i + 1], x, y) if i + 1 < len(URUT_LV) and (URUT_LV[i + 1], x, y) in kol else None
        arah = {"X": {"kiri": None, "kanan": None}, "Y": {"kiri": None, "kanan": None}}
        for kb, b in pb.items():
            if b["lv"] != lv:
                continue
            if b["p2"] == (x, y):
                arah[b["arah"]]["kiri"] = b
            elif b["p1"] == (x, y):
                arah[b["arah"]]["kanan"] = b
        joint.append({"lv": lv, "x": x, "y": y, "bawah": (lv, x, y), "atas": atas, "balok": arah})
    return joint


def cek_joint(j, gk, tul):
    """Kolom kuat balok lemah tiap arah: ΣMnc (Mn terendah pada Pu kombinasi gempa) vs 1,2 ΣMnb."""
    hc = gk[j["bawah"]]["b"]
    mnc = 0.0
    p_ujung = []
    for kk, e in ((j["bawah"], 1), (j["atas"], 0)):
        if kk is None:
            continue
        f = gk[kk]
        p = f["F"][f["gempa"], e, 0]
        dg = diagram(f["b"], *tul[f["kelompok"]][1:])
        mn = float(np.nanmin(mn_pada(dg, p)))
        mnc += mn
        p_ujung.append(mn)
    out = []
    for arah, sisi in j["balok"].items():
        ki, ka = sisi["kiri"], sisi["kanan"]
        if ki is None and ka is None:
            continue
        mki = momen_balok(ki["kel"], hc, ki["tepi"]) if ki else (0.0, 0.0)
        mka = momen_balok(ka["kel"], hc, ka["tepi"]) if ka else (0.0, 0.0)
        s1, s2 = mki[0] + mka[1], mki[1] + mka[0]
        mnb = max(s1, s2)
        ki_, ka_ = (mki[0], mka[1]) if s1 >= s2 else (mki[1], mka[0])
        out.append({"arah": arah, "Mnc_bawah": p_ujung[0], "Mnc_atas": p_ujung[1] if len(p_ujung) > 1 else 0.0,
                    "Mnc": mnc, "Mnb_kiri": ki_, "Mnb_kanan": ka_, "Mnb": mnb, "rasio": mnc / mnb})
    return out


def geser_joint(j, gk):
    """Geser joint tiap arah (18.8.2.1, Tabel 18.8.4.1): Vj = 1,25 fy (As1 + As2) - Vkol; φVn = 0,85 γ √fc' Aj."""
    hc = gk[j["bawah"]]["b"]
    ada = [b for s in j["balok"].values() for b in s.values() if b]
    terkekang = [b for b in ada if b["kel"]["b"] >= 0.75 * hc - 1e-9]   # 18.8.4.2, lebar joint efektif = hc
    muka = {(a, s) for a, ss in j["balok"].items() for s, b in ss.items() if b and b["kel"]["b"] >= 0.75 * hc - 1e-9}
    n = len(terkekang)
    lawan = any({(a, "kiri"), (a, "kanan")} <= muka for a in "XY")
    gamma = 1.7 if n == 4 else (1.2 if n == 3 or (n == 2 and lawan) else 1.0)
    i = URUT_LV.index(j["lv"])
    tinggi = [tm.TINGGI[j["lv"]]] + ([tm.TINGGI[URUT_LV[i + 1]]] if j["atas"] else [])
    aj = hc * hc
    phivn = PHI_J * gamma * math.sqrt(FC) * aj * 1000
    out = []
    for arah, s in j["balok"].items():
        ki, ka = s["kiri"], s["kanan"]
        if ki is None and ka is None:
            continue
        def t(b, pos):
            return 1.25 * FY * b["kel"][pos]["As"] / 1000 if b else 0.0
        def mpr(b, pos):
            return b["kel"]["Mpr_neg" if pos == "atas" else "Mpr_pos"] if b else 0.0
        kasus = [(t(ki, "atas") + t(ka, "bawah"), mpr(ki, "atas") + mpr(ka, "bawah")),
                 (t(ki, "bawah") + t(ka, "atas"), mpr(ki, "bawah") + mpr(ka, "atas"))]
        tt, smpr = max(kasus)
        vkol = smpr / np.mean(tinggi)
        dbs = [b["kel"][p]["db"] for b in (ki, ka) if b for p in ("atas", "bawah")]
        hb = max(b["kel"]["h"] for b in (ki, ka) if b)
        ldh = max(FY * max(dbs) / (5.4 * math.sqrt(FC)), 8 * max(dbs), 150.0)
        menerus = ki is not None and ka is not None
        out.append({"arah": arah, "T": tt, "SMpr": smpr, "Vkol": vkol, "Vj": tt - vkol, "gamma": gamma, "Aj": aj,
                    "phiVn": phivn, "rasio": (tt - vkol) / phivn, "n_terkekang": n, "db": max(dbs),
                    "hc_20db": (hc * 1000 >= 20 * max(dbs)) if menerus else True, "menerus": menerus,
                    "ldh": ldh, "ldh_ada": hc * 1000 - SEL - DS, "ldh_ok": menerus or ldh <= hc * 1000 - SEL - DS,
                    "h_joint": hc >= 0.5 * hb, "hb": hb, "SMpr_b": smpr})
    return out


# ------------------------------------------------------------------ desain kelompok
def rasio_pm(f, dg):
    """Rasio interaksi dua arah Bresler kontur beban α = 1: (|Mux| + |Muy|)/φMn(Pu) untuk semua kombinasi/ujung."""
    p = f["F"][:, :, 0]
    phimn = mn_pada(dg, p, desain=True)
    r = (np.abs(f["F"][:, :, 1]) + np.abs(f["F"][:, :, 2])) / phimn
    return np.where(np.isnan(r), np.inf, r)


def desain(gk, joint):
    """Pilih tulangan tiap kelompok: P-M dua arah lalu kolom kuat balok lemah (naikkan berulang)."""
    kel = {}
    for k, f in gk.items():
        kel.setdefault(f["kelompok"], []).append(k)
    pil = {g: pilihan_tulangan(gk[ks[0]]["b"]) for g, ks in kel.items()}
    idx = {}
    for g, ks in kel.items():
        b = gk[ks[0]]["b"]
        for i, (_, m, db) in enumerate(pil[g]):
            dg = diagram(b, m, db)
            if max(rasio_pm(gk[k], dg).max() for k in ks) <= 1.0:
                idx[g] = i
                break
        else:
            idx[g] = len(pil[g]) - 1
    idx_pm = dict(idx)
    for _ in range(60):
        tul = {g: pil[g][i] for g, i in idx.items()}
        naik = set()
        for j in joint:
            for c in cek_joint(j, gk, tul):
                if c["rasio"] < 1.2:
                    gb = gk[j["bawah"]]["kelompok"]
                    ga = gk[j["atas"]]["kelompok"] if j["atas"] else None
                    if idx[gb] < len(pil[gb]) - 1:
                        naik.add(gb)
                    elif ga and idx[ga] < len(pil[ga]) - 1:
                        naik.add(ga)
        if not naik:
            break
        for g in naik:
            idx[g] += 1
    tul = {g: pil[g][i] for g, i in idx.items()}
    return kel, tul, idx_pm


def geser_kolom(g, ks, gk, tul, jm):
    """Geser kapasitas (18.7.6) dan tulangan pengekang (18.7.5) satu kelompok; nilai terburuk anggota."""
    b = gk[ks[0]]["b"]
    _, m, db = tul[g]
    lv = ks[0][0]
    h_tk = tm.TINGGI[lv]
    dg125 = diagram(b, m, db, fy=1.25 * FY)
    hasil = None
    for k in ks:
        f = gk[k]
        pg = f["F"][f["gempa"], :, 0]
        ps = np.linspace(pg.min(), pg.max(), 25)
        mpr_c = float(np.nanmax(np.interp(ps, dg125["Pn"], dg125["Mn"])))
        ja = jm.get(k)
        hb = max([jj["hb"] for jj in ja["geser"]], default=tb.BALOK_H) if ja else tb.BALOK_H
        lu = h_tk - hb
        i = URUT_LV.index(lv)
        # momen dari Mpr balok: bagian ke kolom bawah 0,5 bila ada kolom atas (kekakuan sama), 1,0 bila atap
        m_atas = max([jj["SMpr_b"] for jj in ja["geser"]], default=0.0) * (0.5 if ja and ja["atas"] else 1.0) \
            if ja else mpr_c
        kb = (URUT_LV[i - 1], k[1], k[2]) if i > 0 else None
        jb = jm.get(kb) if kb else None
        m_bawah = max([jj["SMpr_b"] for jj in jb["geser"]], default=0.0) * 0.5 if jb else mpr_c   # dasar: sendi kolom
        ve1 = 2 * mpr_c / lu
        ve2 = (min(m_atas, mpr_c) + min(m_bawah, mpr_c)) / lu
        vu = float(np.abs(f["F"][:, 0, 3:5]).max())
        ve = max(min(ve1, ve2), vu)
        pmin = float(pg.min())
        pmax = float(f["F"][:, :, 0].max())
        r = {"kunci": k, "lu": lu, "Mpr_c": mpr_c, "Ve1": ve1, "M_atas": min(m_atas, mpr_c),
             "M_bawah": min(m_bawah, mpr_c), "Ve2": ve2, "Vu": vu, "Ve": ve, "Pu_min": pmin, "Pu_maks": pmax, "hb": hb}
        if hasil is None or (r["Ve"], r["Pu_maks"]) > (hasil["Ve"], hasil["Pu_maks"]):
            hasil = {**r, "Pu_maks_kel": max(pmax, hasil["Pu_maks_kel"] if hasil else 0.0)}
        else:
            hasil["Pu_maks_kel"] = max(hasil["Pu_maks_kel"], pmax)
        hasil["Pu_min_kel"] = min(hasil.get("Pu_min_kel", pmin), pmin)
    bmm = b * 1000
    ag = bmm ** 2
    d = bmm - SEL - DS - db / 2
    pmin, pmaks = hasil["Pu_min_kel"], hasil["Pu_maks_kel"]
    vc0 = pmin * 1000 < ag * FC / 20                                       # 18.7.6.2.1 (b)
    vc_n = 0.17 * (1 + max(pmin, 0) * 1000 / (14 * ag)) * math.sqrt(FC) * bmm * d / 1000   # 22.5.6.1
    vc = 0.0 if vc0 else vc_n
    avs = max(hasil["Ve"] / PHI_V - vc, 0.0) * 1000 / (FYT * d)          # mm²/mm
    avs_luar = max(hasil["Ve"] / PHI_V - vc_n, 0.0) * 1000 / (FYT * d)
    bc = bmm - 2 * SEL
    ach = bc ** 2
    kf = max(FC / 175 + 0.6, 1.0)
    nl = 4 * (m - 1)
    kn = nl / (nl - 2)
    ra = 0.3 * (ag / ach - 1) * FC / FYT
    rb = 0.09 * FC / FYT
    rc = 0.2 * kf * kn * pmaks * 1000 / (FYT * ach) if pmaks * 1000 > 0.3 * ag * FC else 0.0
    rasio = max(ra, rb, rc)
    kaki = m                                                                # semua batang ditopang (ikat silang)
    ash = kaki * luas(DS)
    hx = (bmm - 2 * SEL - 2 * DS - db) / (m - 1)
    so = min(max(100 + (350 - hx) / 3, 100.0), 150.0)
    s_ash = ash / (bc * rasio)
    s_v = ash / avs if avs > 0 else 1e9
    s_maks = min(bmm / 4, 6 * db, so)
    s_lo = floor25(min(s_ash, s_v, s_maks))
    s_luar = floor25(min(6 * db, 150.0, ash / avs_luar if avs_luar > 0 else 1e9))
    lo = max(bmm, hasil["lu"] * 1000 / 6, 450.0)
    return {**hasil, "b": b, "d": d, "Vc": vc, "Vc_n": vc_n, "Vc0": vc0, "Av_s": avs, "bc": bc, "Ach": ach, "kf": kf,
            "kn": kn, "ra": ra, "rb": rb, "rc": rc, "rasio_ash": rasio, "kaki": kaki, "Ash": ash, "hx": hx, "so": so,
            "s_ash": s_ash, "s_v": s_v, "s_maks": s_maks, "s_lo": s_lo, "s_luar": s_luar, "lo": lo,
            "ok": s_lo >= 75 and hx <= 350 and hasil["Ve"] <= PHI_V * (vc_n + 0.66 * math.sqrt(FC) * bmm * d / 1000)}


@functools.lru_cache(maxsize=1)
@cache_analisis.disk
def rancang():
    r = balok_rancang()
    um = r["ukuran_model"]
    return rancang_dari([analisis("K2", um), analisis("K1", um)], r)


def rancang_dari(hs, r):
    """Desain dari hasil analisis hs (K2, K1) dan hasil balok r."""
    gk = gaya_kolom(hs)
    joint = joint_daftar(gk)
    kel, tul, idx_pm = desain(gk, joint)
    jm = {}
    for j in joint:
        j["scwb"] = cek_joint(j, gk, tul)
        j["geser"] = geser_joint(j, gk)
        jm[j["bawah"]] = j
    hasil = []
    for g in sorted(kel, key=urut_kelompok):
        ks = kel[g]
        b = gk[ks[0]]["b"]
        ast, m, db = tul[g]
        dg = diagram(b, m, db)
        # kombinasi P-M penentu
        terburuk = None
        for k in ks:
            rr = rasio_pm(gk[k], dg)
            i, e = np.unravel_index(np.argmax(rr), rr.shape)
            if terburuk is None or rr[i, e] > terburuk["rasio"]:
                fk = gk[k]["F"][i, e]
                terburuk = {"kunci": k, "rasio": float(rr[i, e]), "Pu": fk[0], "Mux": abs(fk[1]), "Muy": abs(fk[2]),
                            "phiMn": float(mn_pada(dg, fk[0], desain=True)), "ujung": "atas" if e else "bawah"}
        sc = [dict(c, joint=(j["lv"], j["x"], j["y"])) for j in joint if j["bawah"] in ks for c in j["scwb"]]
        gj = [dict(c, joint=(j["lv"], j["x"], j["y"])) for j in joint if j["bawah"] in ks for c in j["geser"]]
        gs = geser_kolom(g, ks, gk, tul, jm)
        pil0 = pilihan_tulangan(b)[idx_pm[g]]
        hasil.append({"kelompok": g, "n": len(ks), "b": b, "m": m, "db": db, "n_batang": 4 * (m - 1), "Ast": ast,
                      "rho": ast / (b * 1000) ** 2, "pm": terburuk, "dg": dg, "awal_pm": pil0,
                      "scwb_min": min(sc, key=lambda c: c["rasio"]) if sc else None,
                      "scwb_gagal": sum(c["rasio"] < 1.2 for c in sc), "n_joint": len(sc),
                      "hbk": max(gj, key=lambda c: c["rasio"]) if gj else None, "hbk_semua": gj, "scwb_semua": sc,
                      "geser": gs,
                      "Pu_maks": max(float(gk[k]["F"][:, :, 0].max()) for k in ks),
                      "Pu_min": min(float(gk[k]["F"][gk[k]["gempa"], :, 0].min()) for k in ks)})
    for x in hasil:
        cek = {"dimensi": x["b"] >= 0.3, "rho": 0.01 <= x["rho"] <= 0.06, "pm": x["pm"]["rasio"] <= 1.0,
               "scwb": x["scwb_gagal"] == 0, "geser": x["geser"]["ok"],
               "hbk": all(c["rasio"] <= 1.0 and c["hc_20db"] and c["ldh_ok"] and c["h_joint"] for c in x["hbk_semua"])}
        x["cek"] = cek
        x["ok"] = all(cek.values())
        x["usulan"] = None if x["ok"] else usulan_ukuran(x["kelompok"], kel[x["kelompok"]], gk, joint, tul)
    stat = {h["konfig"]: h["statika"] for h in hs}
    gov = max(hasil, key=lambda x: x["pm"]["rasio"])
    return {"kelompok": hasil, "joint": joint, "statika": stat, "balok": r,
            "cp": {**cek_concreteproperties(gov), "kelompok": gov["kelompok"]}}


def usulan_ukuran(g, ks, gk, joint, tul):
    """Ukuran kolom terkecil (kelipatan 50 mm) dan tulangannya yang memenuhi P-M, ΣMnc >= 1,2 ΣMnb, dan geser joint
    di semua joint kelompok g dengan gaya yang sama.
    shortcut: kekakuan model 3D tidak diubah (dua sampai enam kolom); analisis diulang bila Defsa memilih opsi ini."""
    js = [j for j in joint if j["bawah"] in ks]
    b0 = gk[ks[0]]["b"]
    for b in np.arange(b0 + 0.05, b0 + 0.551, 0.05):
        b = round(float(b), 2)
        gk2 = {k: (dict(v, b=b) if k in ks else v) for k, v in gk.items()}
        for ast, m, db in pilihan_tulangan(b):
            dg = diagram(b, m, db)
            if max(rasio_pm(gk2[k], dg).max() for k in ks) > 1.0:
                continue
            tul2 = dict(tul, **{g: (ast, m, db)})
            sc = [c["rasio"] for j in js for c in cek_joint(j, gk2, tul2)]
            gj = [c for j in js for c in geser_joint(j, gk2)]
            if min(sc, default=9) >= 1.2 and all(c["rasio"] <= 1.0 for c in gj):
                return {"b": b, "n_batang": 4 * (m - 1), "db": db, "rho": ast / (b * 1000) ** 2,
                        "scwb": min(sc), "hbk": max(c["rasio"] for c in gj)}
    return None


# ------------------------------------------------------------------ cek silang T-77: concreteproperties
def cek_concreteproperties(x):
    """Kelompok x pada kombinasi P-M penentu: (1) Mn satu sumbu pada Pu, rumus sendiri vs concreteproperties;
    (2) kapasitas dua arah searah (Mux, Muy) dari kontur biaksial concreteproperties vs garis Bresler α = 1."""
    from concreteproperties.concrete_section import ConcreteSection
    from concreteproperties.material import Concrete, SteelBar
    from concreteproperties.stress_strain_profile import (ConcreteLinearNoTension, RectangularStressBlock,
                                                          SteelElasticPlastic)
    from sectionproperties.pre.library.concrete_sections import add_bar
    from sectionproperties.pre.library.primitive_sections import rectangular_section

    ec = 4700 * math.sqrt(FC)
    beton = Concrete("fc35", 2.4e-6, ConcreteLinearNoTension(elastic_modulus=ec, ultimate_strain=0.003,
                                                              compressive_strength=FC), "lightgrey",
                     RectangularStressBlock(compressive_strength=FC, alpha=0.85, gamma=BETA1, ultimate_strain=0.003),
                     flexural_tensile_strength=0.62 * math.sqrt(FC))
    baja = SteelBar("BjTS420", 7.85e-6, SteelElasticPlastic(yield_strength=FY, elastic_modulus=ES,
                                                            fracture_strain=0.05), "grey")
    h = x["b"] * 1000
    geom = rectangular_section(d=h, b=h, material=beton)
    ys = np.linspace(SEL + DS + x["db"] / 2, h - SEL - DS - x["db"] / 2, x["m"])
    for yy in ys:
        for xx in ys:
            if yy in (ys[0], ys[-1]) or xx in (ys[0], ys[-1]):
                geom = add_bar(geom, luas(x["db"]), baja, xx, yy, 16)
    sec = ConcreteSection(geom)
    pu, mux, muy = x["pm"]["Pu"], x["pm"]["Mux"], x["pm"]["Muy"]
    # nominal pada Pn = Pu/φ (φ dari rumus sendiri pada titik itu) supaya keduanya pada gaya aksial yang sama
    dg = x["dg"]
    pn = float(np.interp(pu, dg["phiPn"], dg["Pn"]))
    mn_sendiri = float(mn_pada(dg, pn))
    mi = sec.moment_interaction_diagram(theta=0, n_points=40, progress_bar=False)
    n_cp = np.array([r.n for r in mi.results]) / 1e3
    m_cp = np.array([abs(r.m_x) for r in mi.results]) / 1e6
    o = np.argsort(n_cp)
    mn_cp = float(np.interp(pn, n_cp[o], m_cp[o]))
    bb = sec.biaxial_bending_diagram(n=pn * 1e3, n_points=48, progress_bar=False)
    mx, my = bb.get_results_lists()[0:2] if len(bb.get_results_lists()) == 2 else bb.get_results_lists()[1:3]
    mx, my = np.abs(np.array(mx)) / 1e6, np.abs(np.array(my)) / 1e6
    sudut = math.atan2(muy, mux)
    ang = np.arctan2(my, mx)
    rad = np.hypot(mx, my)
    o = np.argsort(ang)
    r_cp = float(np.interp(sudut, ang[o], rad[o]))
    r_bresler = mn_sendiri / (math.cos(sudut) + math.sin(sudut))
    return {"Pn": pn, "Mn_sendiri": mn_sendiri, "Mn_cp": mn_cp, "sudut": math.degrees(sudut),
            "R_cp": r_cp, "R_bresler": r_bresler}


# ------------------------------------------------------------------ Excel
C_RASIO = (0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.85, 1.00, 1.25)   # c/b titik diagram di Excel


def teks_joint(j):
    return f"{j[0]} x {j[1]:.0f} y {j[2]:.0f}"


def buat_excel(r, keluar=BERKAS, hitung_ulang=True):
    import openpyxl
    from format_dokumen import AI, Lembar, hitung_ulang_excel, set_font_bawaan

    kel = r["kelompok"]
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    lab = f"DIISI AI ATAS PERMINTAAN DEFSA (20 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk desain kolom dan HBK (4.7)", [6, 120])
    lb.catatan(LABEL + " " + lab)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, t] for i, t in enumerate([
        "Kolom SRPMK sistem ganda, fc' 35 MPa (3.6), BjTS 420B (fy = fyt = 420 MPa), selimut 40 mm ke sengkang D13. "
        "Ukuran pra-dimensi 3.6: podium 750 × 750 (LT1-LT4), menara 650 × 650 (LT4-atap). Keputusan Defsa 20 Nov "
        "2026: kolom penumpu balok transfer tangki diperbesar menerus LT1-LT3, x 68 (y 67/75) 950 × 950 (K-T68) dan "
        "x 60/76 (y 67/75) 800 × 800 (K-T); model 3D dihitung ulang dengan ukuran ini. Kelompok K-P podium, K-M "
        "menara; nama = tingkat di ujung atas kolom.",
        "Gaya dalam dari model 3D 4.3 (openseespy) dengan ukuran balok 4.6. Beban pelat = beban segitiga sungguhan "
        "(total q L²/4 per sisi; bukan q L/3 setara momen 4.6, agar aksial tidak berlebih), berat badan balok, "
        "dinding/parapet, beban titik tangki dan dek helipad, berat kolom. Gempa ELF V = 13.164 kN (K2), 0,05 Ax, "
        "100 % + 30 %, ρ 1,3, Ev 0,077D; model rangka saja 25 % (SNI 1726 Pasal 7.2.5.1); K1 dan K2 diselubungi.",
        "Interaksi P-M: kompatibilitas regangan (εcu 0,003, β1 0,80, blok 0,85 fc'), φ Tabel 21.2.2 hal. 471 "
        "(0,65-0,90, εty 0,002), Pn,max = 0,80 Po (Tabel 22.4.2.1 hal. 480). Dua arah: kontur beban Bresler α = 1 "
        "(Mux + Muy)/φMn(Pu) <= 1 [Literatur: Bresler 1960; konservatif untuk penampang simetris]; dicek silang dengan "
        "kontur biaksial concreteproperties (T-77). ρ 0,01-0,06 (18.7.4.1 hal. 386), dipakai <= 0,04 [Asumsi praktis "
        "sambungan lewatan]; spasi bersih >= 40 mm dan 1,5 db (25.2.3 hal. 560).",
        "Kolom kuat balok lemah 18.7.3.2 hal. 385: ΣMnc >= 1,2 ΣMnb di setiap joint, kedua arah. Mnc kolom bawah dan "
        "atas pada Pu kombinasi gempa yang memberi Mn terendah; Mnb = Mn- satu sisi (dengan tulangan pelat 4.5 dalam "
        "lebar sayap efektif Tabel 6.3.2.1 hal. 97) + Mn+ sisi lain (sayap tekan). Bila gagal, tulangan kolom "
        "dinaikkan; bila tetap gagal, ditandai untuk keputusan Defsa (perbesar kolom atau 18.7.3.3).",
        "Geser 18.7.6 hal. 391-392: Ve = maks(min(2 Mpr,c/lu; (Ma + Mb)/lu); Vu), Mpr,c pada rentang Pu gempa "
        "(1,25 fy, φ 1); Ma, Mb dari ΣMpr balok di joint (bagi 0,5 bila ada kolom di sisi lain joint), dibatasi Mpr,c; "
        "dasar LT1 sendi kolom. Vc = 0 di lo bila Pu < Ag fc'/20 (18.7.6.2.1), selain itu Pers. 22.5.6.1 hal. 486.",
        "Pengekang 18.7.5 hal. 386-390: lo = maks(b; lu/6; 450); Ash/(s bc) Tabel 18.7.5.4 (a) 0,3 (Ag/Ach - 1) "
        "fc'/fyt, (b) 0,09 fc'/fyt, (c) 0,2 kf kn Pu/(fyt Ach) bila Pu > 0,3 Ag fc'; semua batang memanjang ditopang "
        "kaki sengkang/ikat silang D13 (hx <= 350); s <= b/4, 6db, so = 100 + (350 - hx)/3 (100-150). Di luar lo "
        "s <= 6db dan 150 mm (18.7.5.5). Sambungan lewatan hanya di setengah tinggi tengah kolom (18.7.4.3).",
        "HBK 18.8 hal. 392-396: Vj = 1,25 fy (As1 + As2) - Vkol, Vkol = ΣMpr balok/H rata-rata; φVn = 0,85 γ √fc' Aj "
        "(φ 21.2.4.3 hal. 474), Aj = hc², γ 1,7/1,2/1,0 (Tabel 18.8.4.1); muka terkekang bila lebar balok >= 3/4 "
        "lebar joint (18.8.4.2): balok 350 tidak mengekang kolom 650/750, balok transfer 600 mengekang kolom 750. "
        "Tulangan transversal joint = lo (18.8.3.1). hc >= 20 db balok (18.8.2.3), hc >= h balok/2 (18.8.2.4), "
        "ldh = fy db/(5,4 √fc') >= 8db, 150 (18.8.5.1) masuk inti di joint tepi.",
        "Cek silang: T-77 concreteproperties (satu sumbu dan dua arah) vs rumus sendiri; T-78 statika beban "
        "gravitasi D = reaksi aksial dasar; T-79 rumus Excel = Python (setelah dihitung ulang di Excel).",
        "Sel hijau berisi rumus atau hasil AI. Status: " + STATUS + ".",
    ])], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Gaya Kolom"), 2, "Gaya terfaktor kolom per kelompok (K1 ∪ K2)",
                [12, 6, 9, 12, 12, 20, 12, 12, 12, 11])
    lb.catatan(LABEL + " Pu tekan positif. Pu min = terkecil pada kombinasi gempa (dapat tarik). Kombinasi penentu "
               "= rasio Bresler terbesar (lembar Cek P-M). Mux momen terhadap sumbu X (goyangan Y), Muy terhadap Y.")
    lb.tabel(["Kelompok", "n", "b (mm)", "Pu maks (kN)", "Pu min gempa (kN)", "Penentu (kolom, ujung)", "Pu (kN)",
              "Mux (kNm)", "Muy (kNm)", "Vu maks (kN)"],
             [[x["kelompok"], x["n"], x["b"] * 1000, round(x["Pu_maks"], 1), round(x["Pu_min"], 1),
               f"{teks_joint(x['pm']['kunci'])}, {x['pm']['ujung']}", round(x["pm"]["Pu"], 1),
               round(x["pm"]["Mux"], 1), round(x["pm"]["Muy"], 1), round(x["geser"]["Vu"], 1)] for x in kel],
             rata=list("lccccccccc"), fmt=[None, "0", "0", "0.0", "0.0", None, "0.0", "0.0", "0.0", "0.0"],
             fill_kolom={i: AI for i in range(3, 10)})

    # ---- penampang (baris tulangan) untuk rumus diagram
    lb = Lembar(wb.create_sheet("Penampang"), 3, "Baris tulangan memanjang (lentur satu sumbu)",
                [12, 9, 8, 14, 9, 8, 12])
    lb.catatan(LABEL + " Kolom bujur sangkar, m batang per sisi, n = 4(m - 1). d = jarak baris dari serat tekan "
               "= 40 + 13 + db/2 sampai b - (40 + 13 + db/2), dibagi rata. As baris = n baris × π db²/4.")
    baris, rentang = [], {}
    for x in kel:
        ys, as_ = baris_batang(x["b"], x["m"], x["db"])
        for i, (y, a) in enumerate(zip(ys, as_)):
            baris.append([x["kelompok"], x["b"] * 1000, i + 1, round(float(y), 2), int(round(a / luas(x["db"]))),
                          x["db"], None])
    _, a0, a1 = lb.tabel(["Kelompok", "b (mm)", "Baris", "d (mm)", "n batang", "D", "As (mm²)"], baris,
                         rata=list("lcccccc"), fmt=[None, "0", "0", "0.00", "0", "0", "0.0"], fill_kolom={6: AI})
    k = lb.kol
    r_ = a0
    for x in kel:
        rentang[x["kelompok"]] = (r_, r_ + x["m"] - 1)
        r_ += x["m"]
    for rr in range(a0, a1 + 1):
        lb.ws[f"{k(6)}{rr}"] = f"={k(4)}{rr}*PI()*{k(5)}{rr}^2/4"

    lb = Lembar(wb.create_sheet("Diagram P-M"), 4, "Titik diagram interaksi nominal dan desain",
                [12, 8, 9, 9, 11, 11, 9, 7, 11, 11])
    lb.catatan(LABEL + " a = min(β1 c; b), β1 = 0,80; fs = Es 0,003 (c - d)/c dibatasi ±fy, dikurangi 0,85 fc' bila "
               "d < a (beton terdesak); Pn = 0,85 fc' a b + Σ As fs; Mn = 0,85 fc' a b (b/2 - a/2) + Σ As fs (b/2 - d). "
               "εt = 0,003 (dt - c)/c; φ = 0,65 + 0,25 (εt - 0,002)/0,003 dibatasi 0,65-0,90. Rumus SUMPRODUCT "
               "membaca lembar Penampang.")
    baris = []
    for x in kel:
        for cr in C_RASIO:
            baris.append([x["kelompok"], x["b"] * 1000, round(cr * x["b"] * 1000, 1)] + [None] * 7)
    _, d0, d1 = lb.tabel(["Kelompok", "b (mm)", "c (mm)", "a (mm)", "Pn (kN)", "Mn (kNm)", "εt", "φ", "φPn (kN)",
                          "φMn (kNm)"], baris, rata=list("lccccccccc"),
                         fmt=[None, "0", "0.0", "0.0", "0.0", "0.0", "0.00000", "0.000", "0.0", "0.0"],
                         fill_kolom={i: AI for i in range(3, 10)})
    pen = "Penampang"
    rr = d0
    for x in kel:
        p0, p1 = rentang[x["kelompok"]]
        d_ = f"'{pen}'!${k(3)}${p0}:${k(3)}${p1}"
        as_ = f"'{pen}'!${k(6)}${p0}:${k(6)}${p1}"
        for _ in C_RASIO:
            b_, c_, a_ = f"{k(1)}{rr}", f"{k(2)}{rr}", f"{k(3)}{rr}"
            eps = f"{ES}*0.003*({c_}-{d_})/{c_}"
            fs = f"((ABS({eps}+{FY})-ABS({eps}-{FY}))/2-0.85*{FC}*({d_}<{a_}))"
            lb.ws[a_] = f"=MIN({BETA1}*{c_},{b_})"
            lb.ws[f"{k(4)}{rr}"] = f"=(0.85*{FC}*{a_}*{b_}+SUMPRODUCT({as_},{fs}))/1000"
            lb.ws[f"{k(5)}{rr}"] = (f"=(0.85*{FC}*{a_}*{b_}*({b_}/2-{a_}/2)+SUMPRODUCT({as_},{fs},{b_}/2-{d_}))"
                                    "/1000000")
            lb.ws[f"{k(6)}{rr}"] = f"=0.003*(MAX({d_})-{c_})/{c_}"
            lb.ws[f"{k(7)}{rr}"] = f"=MIN(0.9,MAX(0.65,0.65+0.25*({k(6)}{rr}-{EPS_TY})/(0.005-{EPS_TY})))"
            lb.ws[f"{k(8)}{rr}"] = f"={k(7)}{rr}*{k(4)}{rr}"
            lb.ws[f"{k(9)}{rr}"] = f"={k(7)}{rr}*{k(5)}{rr}"
            rr += 1

    lb = Lembar(wb.create_sheet("Cek P-M"), 5, "Cek interaksi P-M dua arah (kombinasi penentu)",
                [12, 8, 7, 6, 11, 9, 11, 11, 10, 10, 10, 11, 9, 11])
    lb.catatan(LABEL + " Ast = n π D²/4; ρ = Ast/b²; Po = 0,85 fc' (b² - Ast) + fy Ast; φPn,max = 0,65 × 0,80 Po. "
               "φMn(Pu) dari diagram rapat Python (interpolasi φPn-φMn; titik Excel di lembar Diagram P-M). "
               "Rasio = (Mux + Muy)/φMn(Pu) <= 1.")
    _, c0, c1 = lb.tabel(["Kelompok", "b (mm)", "n", "D", "Ast (mm²)", "ρ", "Po (kN)", "φPn,max (kN)", "Pu (kN)",
                          "Mux (kNm)", "Muy (kNm)", "φMn(Pu) (kNm)", "Rasio", "Status"],
                         [[x["kelompok"], x["b"] * 1000, x["n_batang"], x["db"], None, None, None, None,
                           round(x["pm"]["Pu"], 1), round(x["pm"]["Mux"], 1), round(x["pm"]["Muy"], 1),
                           round(x["pm"]["phiMn"], 1), None, None] for x in kel],
                         rata=list("lccccccccccccc"),
                         fmt=[None, "0", "0", "0", "0", "0.0000", "0", "0", "0.0", "0.0", "0.0", "0.0", "0.000", None],
                         fill_kolom={i: AI for i in (4, 5, 6, 7, 11, 12, 13)})
    for rr in range(c0, c1 + 1):
        lb.ws[f"{k(4)}{rr}"] = f"={k(2)}{rr}*PI()*{k(3)}{rr}^2/4"
        lb.ws[f"{k(5)}{rr}"] = f"={k(4)}{rr}/{k(1)}{rr}^2"
        lb.ws[f"{k(6)}{rr}"] = f"=(0.85*{FC}*({k(1)}{rr}^2-{k(4)}{rr})+{FY}*{k(4)}{rr})/1000"
        lb.ws[f"{k(7)}{rr}"] = f"=0.65*0.8*{k(6)}{rr}"
        lb.ws[f"{k(12)}{rr}"] = f"=({k(9)}{rr}+{k(10)}{rr})/{k(11)}{rr}"
        lb.ws[f"{k(13)}{rr}"] = (f'=IF(AND({k(12)}{rr}<=1,{k(8)}{rr}<={k(7)}{rr},{k(5)}{rr}>=0.01,{k(5)}{rr}<=0.06),'
                                 f'"Memenuhi","Kurang")')

    lb = Lembar(wb.create_sheet("Kolom Kuat Balok Lemah"), 6, "ΣMnc >= 1,2 ΣMnb (joint terlemah per kelompok)",
                [12, 18, 6, 10, 10, 10, 10, 10, 10, 8, 11, 11])
    lb.catatan(LABEL + " Joint di ujung atas kolom kelompok. Mnc pada Pu gempa yang memberi Mn terendah; Mnb kiri/kanan "
               "= pasangan Mn- (dengan pelat) dan Mn+ yang memberi ΣMnb terbesar. Kolom 'Joint gagal' = jumlah "
               "joint × arah dengan rasio < 1,2 dari seluruh joint kelompok.")
    baris = []
    for x in kel:
        s = x["scwb_min"]
        if s is None:
            continue
        baris.append([x["kelompok"], teks_joint(s["joint"]), s["arah"], round(s["Mnc_bawah"], 1),
                      round(s["Mnc_atas"], 1), round(s["Mnb_kiri"], 1), round(s["Mnb_kanan"], 1), None, None, None,
                      None, f"{x['scwb_gagal']} / {x['n_joint']}"])
    _, s0, s1 = lb.tabel(["Kelompok", "Joint", "Arah", "Mnc bawah (kNm)", "Mnc atas (kNm)", "Mnb kiri (kNm)",
                          "Mnb kanan (kNm)", "ΣMnc (kNm)", "ΣMnb (kNm)", "Rasio", "Status", "Joint gagal"], baris,
                         rata=list("lccccccccccc"),
                         fmt=[None, None, None, "0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "0.00", None, None],
                         fill_kolom={i: AI for i in range(7, 12)})
    for rr in range(s0, s1 + 1):
        lb.ws[f"{k(7)}{rr}"] = f"={k(3)}{rr}+{k(4)}{rr}"
        lb.ws[f"{k(8)}{rr}"] = f"={k(5)}{rr}+{k(6)}{rr}"
        lb.ws[f"{k(9)}{rr}"] = f"={k(7)}{rr}/{k(8)}{rr}"
        lb.ws[f"{k(10)}{rr}"] = f'=IF({k(9)}{rr}>=1.2,"Memenuhi","Kurang")'

    lb = Lembar(wb.create_sheet("Geser Kolom"), 7, "Geser kapasitas kolom (18.7.6)",
                [12, 7, 10, 10, 10, 9, 9, 9, 9, 10, 9, 8, 11])
    lb.catatan(LABEL + " Ve1 = 2 Mpr,c/lu; Ve2 = (Ma + Mb)/lu dari Mpr balok; Ve = maks(min(Ve1; Ve2); Vu). "
               "Vc = 0 bila Pu min < Ag fc'/20, selain itu 0,17 (1 + Pu/(14 Ag)) √fc' b d. Av/s perlu = (Ve/0,75 - Vc)/"
               "(fyt d) untuk semua kaki searah geser.")
    _, g0, g1 = lb.tabel(["Kelompok", "lu (m)", "Mpr,c (kNm)", "Ma (kNm)", "Mb (kNm)", "Ve1 (kN)", "Ve2 (kN)",
                          "Vu (kN)", "Ve (kN)", "Pu min (kN)", "Vc (kN)", "d (mm)", "Av/s perlu (mm²/mm)"],
                         [[x["kelompok"], round(x["geser"]["lu"], 2), round(x["geser"]["Mpr_c"], 1),
                           round(x["geser"]["M_atas"], 1), round(x["geser"]["M_bawah"], 1), None, None,
                           round(x["geser"]["Vu"], 1), None, round(x["geser"]["Pu_min_kel"], 1),
                           round(x["geser"]["Vc"], 1), round(x["geser"]["d"], 1), None] for x in kel],
                         rata=list("lcccccccccccc"),
                         fmt=[None, "0.00", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "0.0",
                              "0.000"], fill_kolom={i: AI for i in (2, 3, 4, 5, 6, 8, 10, 12)})
    for rr in range(g0, g1 + 1):
        lb.ws[f"{k(5)}{rr}"] = f"=2*{k(2)}{rr}/{k(1)}{rr}"
        lb.ws[f"{k(6)}{rr}"] = f"=({k(3)}{rr}+{k(4)}{rr})/{k(1)}{rr}"
        lb.ws[f"{k(8)}{rr}"] = f"=MAX(MIN({k(5)}{rr},{k(6)}{rr}),{k(7)}{rr})"
        lb.ws[f"{k(12)}{rr}"] = f"=MAX({k(8)}{rr}/{PHI_V}-{k(10)}{rr},0)*1000/({FYT}*{k(11)}{rr})"

    lb = Lembar(wb.create_sheet("Pengekang"), 8, "Tulangan pengekang lo dan di luar lo (18.7.5)",
                [12, 7, 7, 9, 9, 9, 6, 9, 9, 8, 8, 9, 9, 9, 9])
    lb.catatan(LABEL + " bc = b - 2 × 40; (a) 0,3 (b²/bc² - 1) fc'/fyt; (b) 0,09 fc'/fyt; (c) 0,2 kf kn Pu/(fyt bc²) "
               "bila Pu > 0,3 Ag fc' (kf = 1,0; kn = n/(n - 2)). Ash = kaki × π 13²/4; s Ash = Ash/(bc × maks). "
               "so = 100 + (350 - hx)/3 dibatasi 100-150. s lo = min(s Ash; s geser; b/4; 6 db; so) dibulatkan 25 mm.")
    _, e0, e1 = lb.tabel(["Kelompok", "b (mm)", "bc (mm)", "(a)", "(b)", "(c)", "Kaki", "Ash (mm²)", "s Ash (mm)",
                          "hx (mm)", "so (mm)", "s geser (mm)", "s lo (mm)", "lo (mm)", "s luar lo (mm)"],
                         [[x["kelompok"], x["b"] * 1000, None, None, None, round(x["geser"]["rc"], 5),
                           x["geser"]["kaki"], None, None, round(x["geser"]["hx"], 1), None,
                           round(min(x["geser"]["s_v"], 9999), 1), x["geser"]["s_lo"], None, x["geser"]["s_luar"]]
                          for x in kel], rata=list("lcccccccccccccc"),
                         fmt=[None, "0", "0", "0.00000", "0.00000", "0.00000", "0", "0.0", "0.0", "0.0", "0.0", "0.0",
                              "0", "0", "0"], fill_kolom={i: AI for i in range(2, 15)})
    for i, rr in enumerate(range(e0, e1 + 1)):
        x = kel[i]
        lb.ws[f"{k(2)}{rr}"] = f"={k(1)}{rr}-2*{SEL}"
        lb.ws[f"{k(3)}{rr}"] = f"=0.3*({k(1)}{rr}^2/{k(2)}{rr}^2-1)*{FC}/{FYT}"
        lb.ws[f"{k(4)}{rr}"] = f"=0.09*{FC}/{FYT}"
        lb.ws[f"{k(7)}{rr}"] = f"={k(6)}{rr}*PI()*{DS}^2/4"
        lb.ws[f"{k(8)}{rr}"] = f"={k(7)}{rr}/({k(2)}{rr}*MAX({k(3)}{rr},{k(4)}{rr},{k(5)}{rr}))"
        lb.ws[f"{k(10)}{rr}"] = f"=MIN(MAX(100+(350-{k(9)}{rr})/3,100),150)"
        lb.ws[f"{k(13)}{rr}"] = f"=MAX({k(1)}{rr},{x['geser']['lu']:.3f}*1000/6,450)"

    lb = Lembar(wb.create_sheet("HBK"), 9, "Geser hubungan balok-kolom (joint terkritis per kelompok)",
                [12, 18, 6, 7, 6, 8, 11, 10, 10, 8, 10, 10, 10, 8, 10])
    lb.catatan(LABEL + " T = 1,25 fy (As atas satu sisi + As bawah sisi lain) (18.8.2.1); Vkol = ΣMpr balok/H rata-rata "
               "tingkat di atas dan di bawah joint; Vj = T - Vkol; Aj = hc²; φVn = 0,85 γ √fc' Aj (Tabel 18.8.4.1). "
               "Muka terkekang = lebar balok >= 3/4 hc (18.8.4.2).")
    baris = []
    for x in kel:
        c = x["hbk"]
        if c is None:
            continue
        hmean = c["SMpr"] / c["Vkol"] if c["Vkol"] else 0.0
        baris.append([x["kelompok"], teks_joint(c["joint"]), c["arah"], c["n_terkekang"], c["gamma"], x["b"] * 1000,
                      None, round(c["T"], 1), round(c["SMpr"], 1), round(hmean, 2), None, None, None, None,
                      f"{x['b'] * 1000 / c['db']:.0f}"])
    _, h0, h1 = lb.tabel(["Kelompok", "Joint", "Arah", "Muka kekang", "γ", "hc (mm)", "Aj (mm²)", "T (kN)",
                          "ΣMpr (kNm)", "H (m)", "Vkol (kN)", "Vj (kN)", "φVn (kN)", "Rasio", "hc/db"], baris,
                         rata=list("lcccccccccccccc"),
                         fmt=[None, None, None, "0", "0.0", "0", "0", "0.0", "0.0", "0.00", "0.0", "0.0", "0.0",
                              "0.00", None], fill_kolom={i: AI for i in range(6, 15)})
    for rr in range(h0, h1 + 1):
        lb.ws[f"{k(6)}{rr}"] = f"={k(5)}{rr}^2"
        lb.ws[f"{k(10)}{rr}"] = f"={k(8)}{rr}/{k(9)}{rr}"
        lb.ws[f"{k(11)}{rr}"] = f"={k(7)}{rr}-{k(10)}{rr}"
        lb.ws[f"{k(12)}{rr}"] = f"={PHI_J}*{k(4)}{rr}*SQRT({FC})*{k(6)}{rr}/1000"
        lb.ws[f"{k(13)}{rr}"] = f"={k(11)}{rr}/{k(12)}{rr}"

    lb = Lembar(wb.create_sheet("Ringkasan Tulangan"), 10, "Ringkasan tulangan kolom dan joint",
                [12, 11, 14, 8, 22, 9, 18, 34, 11])
    lb.catatan(LABEL + " Semua batang memanjang ditopang kaki sengkang/ikat silang D13 berkait 135° (ikat silang "
                       "berselang 90°/135°, 18.7.5.2). Tulangan joint = tulangan lo diteruskan melalui joint (18.8.3.1). "
                       "Sambungan lewatan kelas B di setengah tinggi tengah kolom (18.7.4.3).")
    lb.tabel(["Kelompok", "b × h (mm)", "Memanjang", "ρ", "Sengkang lo (kaki per arah)", "lo (mm)", "Di luar lo",
              "Catatan", "Status"],
             [[x["kelompok"], f"{x['b'] * 1000:.0f} × {x['b'] * 1000:.0f}", f"{x['n_batang']}D{x['db']}",
               round(x["rho"], 4), f"{x['geser']['kaki']} kaki D{DS}-{x['geser']['s_lo']}",
               round(x["geser"]["lo"]), f"{x['geser']['kaki']} kaki D{DS}-{x['geser']['s_luar']}",
               catatan_kelompok(x), "Memenuhi" if x["ok"] else "Periksa"] for x in kel],
             rata=list("lcccccclc"), fmt=[None, None, None, "0.0000", None, "0", None, None, None],
             fill_kolom={i: AI for i in range(1, 9)})

    us = [x for x in kel if x.get("usulan")]
    if us:
        lb.kosong()
        lb.catatan("Usulan untuk kelompok yang belum memenuhi (keputusan Defsa): ukuran kolom terkecil kelipatan 50 mm "
                   "dan tulangannya yang memenuhi P-M, ΣMnc >= 1,2 ΣMnb, dan geser joint dengan gaya yang sama "
                   "(kekakuan model belum diubah; analisis 4.3 diulang bila diterima). Alternatif: tulangan bawah "
                   "balok transfer yang masuk joint dikurangi sampai syarat 18.6.3.2 (>= 0,5 As atas) [perlu dicek].")
        lb.tabel(["Kelompok", "Usulan b × h (mm)", "Memanjang", "ρ", "ΣMnc/ΣMnb min", "Rasio geser joint maks"],
                 [[x["kelompok"], f"{x['usulan']['b'] * 1000:.0f} × {x['usulan']['b'] * 1000:.0f}",
                   f"{x['usulan']['n_batang']}D{x['usulan']['db']}", round(x["usulan"]["rho"], 4),
                   round(x["usulan"]["scwb"], 2), round(float(x["usulan"]["hbk"]), 2)] for x in us],
                 rata=list("lccccc"), fmt=[None, None, None, "0.0000", "0.00", "0.00"],
                 fill_kolom={i: AI for i in range(1, 6)}, beku=False)

    cs = r["cp"]
    lb = Lembar(wb.create_sheet("Cek Silang"), 11, "Cek silang T-77 dan T-78", [8, 66, 14, 14, 11, 10, 12])
    st = r["statika"]["K2"]["D"]
    lb.catatan(LABEL + f" T-77: kelompok {cs['kelompok']} pada kombinasi penentu (Pn = {cs['Pn']:.0f} kN, arah momen "
               f"{cs['sudut']:.1f}° dari sumbu X). concreteproperties: blok persegi 0,85 fc', β1 0,80, εcu 0,003, baja "
               "elastis-plastis, batang satu per satu. Kontur biaksial concreteproperties harus di luar garis Bresler "
               "α = 1 (rasio >= 1: Bresler konservatif). T-78: jumlah beban mati gravitasi yang dipasang = jumlah gaya "
               "aksial kolom LT1 (K2). T-79 (Excel = Python) dicatat di VERIFIKASI.")
    _, t0, t1 = lb.tabel(["No", "Besaran", "Cara 1", "Cara 2", "Selisih", "Batas", "Status"], [
        ["T-77", "Mn satu sumbu pada Pn (kNm): rumus sendiri | concreteproperties", round(cs["Mn_sendiri"], 1),
         round(cs["Mn_cp"], 1), None, 0.05, None],
        ["T-77", "Kapasitas dua arah searah Mu (kNm): concreteproperties | Bresler α = 1", round(cs["R_cp"], 1),
         round(cs["R_bresler"], 1), None, 0.35, None],
        ["T-78", "Beban D gravitasi K2 (kN): jumlah beban dipasang | ΣN kolom LT1", round(st[0], 1), round(st[1], 1),
         None, 0.001, None],
    ], rata=list("clccccc"), fmt=[None, None, "0.0", "0.0", "0.0%", "0.0%", None], fill_kolom={4: AI, 6: AI},
        beku=False)
    for rr in range(t0, t1 + 1):
        lb.ws[f"{k(4)}{rr}"] = f"={k(2)}{rr}/{k(3)}{rr}-1"
        lb.ws[f"{k(6)}{rr}"] = f'=IF(ABS({k(4)}{rr})<={k(5)}{rr},"Lolos","Tidak lolos")'
    lb.ws[f"{k(6)}{t0 + 1}"] = f'=IF(AND({k(4)}{t0 + 1}>=0,{k(4)}{t0 + 1}<={k(5)}{t0 + 1}),"Lolos","Tidak lolos")'

    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    if hitung_ulang:
        hitung_ulang_excel(keluar)
    return keluar


def catatan_kelompok(x):
    c = []
    if not x["cek"]["scwb"]:
        c.append(f"ΣMnc/ΣMnb < 1,2 di {x['scwb_gagal']} joint (min {x['scwb_min']['rasio']:.2f})".replace(".", ","))
    if not x["cek"]["hbk"]:
        c.append(f"geser joint {x['hbk']['rasio']:.2f} > 1".replace(".", ","))
    u = x.get("usulan")
    if u:
        c.append(f"usulan {u['b'] * 1000:.0f} × {u['b'] * 1000:.0f} {u['n_batang']}D{u['db']}: keputusan Defsa")
    h = x["hbk"]
    if h and h["gamma"] > 1.0:
        c.append(f"joint γ {h['gamma']}")
    if x["geser"]["rc"] > 0:
        c.append("Pu > 0,3 Ag fc': Tabel 18.7.5.4 (c)")
    if not x["geser"]["Vc0"]:
        c.append("Vc dihitung (Pu >= Ag fc'/20)")
    return "; ".join(c) or "-"


def cek_excel(r, berkas=BERKAS):
    """T-79: selisih terbesar rumus Excel (dihitung ulang di Excel) terhadap Python: titik diagram (relatif), rasio
    P-M, ΣMnc/ΣMnb, Ve, s Ash, Vj, φVn."""
    import openpyxl
    from format_dokumen import baca_tabel
    wb = openpyxl.load_workbook(berkas, data_only=True)
    _, dd = baca_tabel(wb["Diagram P-M"], "Kelompok")
    sel = []
    i = 0
    for x in r["kelompok"]:
        ys, as_ = baris_batang(x["b"], x["m"], x["db"])
        for cr in C_RASIO:
            pn, mn, _, phi = titik_pm(cr * x["b"] * 1000, x["b"], ys, as_)
            sel += [abs(float(dd[i][4]) - pn[0]), abs(float(dd[i][5]) - mn[0]), abs(float(dd[i][7]) - phi[0])]
            i += 1
    _, dp = baca_tabel(wb["Cek P-M"], "Kelompok")
    _, dg = baca_tabel(wb["Geser Kolom"], "Kelompok")
    _, de = baca_tabel(wb["Pengekang"], "Kelompok")
    for j, x in enumerate(r["kelompok"]):
        sel.append(abs(float(dp[j][12]) - x["pm"]["rasio"]) * 100)          # rasio dalam persen
        sel.append(abs(float(dg[j][8]) - x["geser"]["Ve"]))
        sel.append(abs(float(de[j][8]) - x["geser"]["s_ash"]))
    _, ds = baca_tabel(wb["Kolom Kuat Balok Lemah"], "Kelompok")
    sc = [x["scwb_min"] for x in r["kelompok"] if x["scwb_min"]]
    for j, s in enumerate(sc):
        sel.append(abs(float(ds[j][9]) - s["rasio"]) * 100)
    _, dh = baca_tabel(wb["HBK"], "Kelompok")
    hb = [x["hbk"] for x in r["kelompok"] if x["hbk"]]
    for j, h in enumerate(hb):
        sel += [abs(float(dh[j][11]) - h["Vj"]), abs(float(dh[j][12]) - h["phiVn"])]
    return max(sel)


def cetak(r):
    print("statika", r["statika"])
    for x in r["kelompok"]:
        pm, sc, hj, gs = x["pm"], x["scwb_min"], x["hbk"], x["geser"]
        print(f"{x['kelompok']:9s} n {x['n']:3d} b {x['b']:.2f} {x['n_batang']}D{x['db']} ρ {x['rho']:.4f} "
              f"(awal P-M {x['awal_pm'][1]}/{x['awal_pm'][2]}) Pu {x['Pu_min']:.0f}..{x['Pu_maks']:.0f} "
              f"PM {pm['rasio']:.2f} | SCWB min {sc['rasio'] if sc else 0:.2f} gagal {x['scwb_gagal']}/{x['n_joint']} "
              f"{sc['joint'] if sc else ''} | HBK {hj['rasio'] if hj else 0:.2f} γ {hj['gamma'] if hj else 0} | "
              f"Ve {gs['Ve']:.0f} (Ve1 {gs['Ve1']:.0f} Ve2 {gs['Ve2']:.0f} Vu {gs['Vu']:.0f}) s lo {gs['s_lo']} "
              f"luar {gs['s_luar']} lo {gs['lo']:.0f} ok {x['ok']} {[k for k, v in x['cek'].items() if not v]}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    import time
    t0 = time.time()
    r = rancang()
    cetak(r)
    if "--excel" in sys.argv:
        print(buat_excel(r), "selisih Excel-Python maks", cek_excel(r))
    print(f"waktu {time.time() - t0:.0f} s")
