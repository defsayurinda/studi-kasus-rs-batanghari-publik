"""Tahap 6 langkah 6.3: jumlah dan tata letak tiang bor Ø800 per cap (cap kolom biasa dan enam cap inti gabungan; Cap C digabung ke Cap E, revisi 22 Nov 2026).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (21 Nov 2026); disetujui Defsa 21 Nov 2026 (100 % + 30 %, varian a,
jarak 2,4/3,6/4,8 m). Kunci jawaban tidak dibuka. Reaksi dari `tahap6_telaah` (5.6 -> 6.0), izin per tiang dari
`tahap6_nsf` (6.2, disetujui), tahanan terfaktor dari `tahap6_tiang_tunggal` (6.1), pola cap Tahap 3 dari `tahap3_bim`.

Acuan (halaman = nomor halaman PDF di acuan/pustaka; nomor cetak dalam kurung):
- FHWA-NHI-06-089 Vol II 9.6.1.1 hal. 188 (9-78): tanah tanpa kohesi, jarak >= 3D, tahanan kelompok = jumlah tiang;
  9.6.1.3 hal. 191-192 (9-81, 9-82), Pers. 9-18 dan 9-19: kegagalan blok Qug = 2D(B+Z)cu1 + BZ cu2 Nc;
  9.8 hal. 199 (9-89): seret kelompok dihitung dari luas keliling blok, bukan jumlah seret tiap tiang.
- SNI 8460:2017 Pasal 9.7.2.1 hal. 204 (seret sebagai beban), 9.2.3.1 hal. 194 (FK 2,5); FHWA GEC10 Tabel 8-4 hal. 222 (tahanan terfaktor).
- Converse-Labarre [Literatur, belum ada di acuan/]: pembanding saja.
"""
from __future__ import annotations

import itertools
import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).parent))
import tahap3_bim as b3  # noqa: E402
import tahap3_pondasi as p3  # noqa: E402
import tahap6_nsf as ns  # noqa: E402
import tahap6_telaah as tl  # noqa: E402
import tahap6_tiang_tunggal as t6  # noqa: E402

t3 = t6.t3
AKAR = t6.AKAR
KELUAR = t6.KELUAR
BERKAS = KELUAR / "6.3 Tata Letak Tiang.xlsx"
MD = KELUAR / "6.3 Tata Letak Tiang.md"
VERIFIKASI = AKAR / "VERIFIKASI.md"

LABEL = t6.LABEL
STATUS = "disetujui Defsa 21 Nov 2026; revisi 22 Nov 2026: Cap C digabung ke Cap E (keputusan Defsa)"
LABEL_AI = f"DIHITUNG AI ATAS PERMINTAAN DEFSA (21 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."
idn = t6.idn

D = t6.D
KEL = math.pi * D
AG = math.pi * D ** 2 / 4
S = b3.JARAK_TIANG                      # 2,4 m (3D, keputusan 6.0)
TEPI = b3.TEPI_CAP                      # 0,80 m dari as tiang ke tepi cap (Tahap 3)
MARGIN = 0.40                           # m, titik beban (kolom/inti) minimal sekian di dalam tepi cap [Asumsi: ±setengah kolom 0,75 m]
PANJANG = 38.45                         # m dari bawah cap (Tahap 3)
TAMBAH = 1.55                           # m, varian (b): zona selatan 40,00 m
N_UTILITAS = 68                         # tiang gedung utilitas + parkir, tidak berubah (3.7 [Asumsi])
N_T3 = 305                              # tiang gedung utama Tahap 3
ZP = {"SELATAN": "SELATAN", "TENGAH": "UTARA", "UTARA": "UTARA"}   # TENGAH memakai sifat UTARA [Asumsi: konservatif; 6.2 tidak menghitung tengah]
TOL = {"rigid": 0.5, "sigma": 0.1, "jarak": 0.0}   # %, %, pasangan < 2,4 m ; ditetapkan sebelum membandingkan
INTI = {                                # cap inti gabungan: (titik inti, kolom 1, kolom 2) = (G, G) pasangan zona_gabung
    "A": ("INTI-T22/39", "2/B", "2/C"), "B": ("INTI-T22/63", "2/E", "2/F"), "C": ("INTI-T46/39", "5/B", "5/C"),
    "D": ("INTI-T46/63", "5/E", "5/F"), "E": ("INTI-LIF", "6/B", "6/C"), "F": ("INTI-T70/39", "8/B", "8/C"),
    "G": ("INTI-T70/63", "8/E", "8/F")}
SPASI = (2.4, 3.6, 4.8)           # m, pilihan jarak tiang di cap inti (>= 3D) [Asumsi: spasi lebih lebar menambah lengan momen]
_G = [round(0.3 * i, 2) for i in range(-10, 11)] + [round(0.6 * i, 2) for i in list(range(6, 11)) + list(range(-10, -5))]
GESER = sorted(((i, j) for i in _G for j in _G), key=lambda a: (abs(a[0]) + abs(a[1]), a))   # geseran grid terhadap titik berat beban (m)
KOMB_ORTO = 0.3                         # SNI 1726:2019 Pasal 7.5.3 a (hal. 79 PDF): 100 % arah utama + 30 % arah tegak lurus
TANDA = [(sx, sy * KOMB_ORTO) for sx in (1, -1) for sy in (1, -1)] + [(sx * KOMB_ORTO, sy) for sx in (1, -1) for sy in (1, -1)]
TANDA_PENUH = [(sx, sy) for sx in (1, -1) for sy in (1, -1)]   # 100 % + 100 % serentak (kepekaan, arahan tugas awal)


# ------------------------------------------------------------------ berat cap (temuan 6.9; usulan AI, disetujui atas delegasi Defsa 22 Nov 2026)
GAMMA_BETON = 24.0                      # kN/m3
MUKA_AIR_DESAIN = 11.20                 # m, muka air desain 6.0 [Asumsi]
MUKA_CAP = 12.05                        # m
H_KOLOM = {2: 1.000, 3: 0.800, 4: 0.950}        # m, tebal cap kolom per jumlah tiang (keputusan 6.7)
H_INTI = 1.200                          # m, cap inti lain (6.7)
H_E = 2.000                             # m, Cap E (pelat, 6.7): 1,8 dan 1,9 gagal pons inti; keputusan usulan AI disetujui atas delegasi Defsa 22 Nov 2026: 2.000 tanpa tulangan pons
H_KOLOM_LAIN = 1.200                    # m, cap kolom 5-6 tiang (tidak ada di 6.7) [Asumsi]
SEBELUM_BERAT = dict(kolom=152, n_cap_kolom=56, per_tipe="28/16/12/0", inti=78, n_cap_inti=6)   # hasil 6.3 sebelum berat cap (22 Nov 2026 pagi)
F_W = dict(layan=1.0, maks=1.2, min=0.9)   # faktor berat cap: layan; ultimit gempa Pu maks; Pu min


def tebal_cap(n=None, kode=None):
    """Tebal cap (m) menurut keputusan 6.7: Cap E 1,8; cap inti lain 1,2; cap kolom 2/3/4 tiang 1,0/0,8/0,95."""
    if kode is not None:
        return H_E if kode == "E" else H_INTI
    return H_KOLOM.get(n, H_KOLOM_LAIN)


def berat_cap(A, h):
    """Berat cap bersih (kN): A h 24 dikurangi apung 9,81 A (muka air 11,20 - dasar cap) bila dasar di bawah +11,20."""
    return A * h * GAMMA_BETON - 9.81 * A * max(0.0, MUKA_AIR_DESAIN - (MUKA_CAP - h))


# ------------------------------------------------------------------ sifat tiang tunggal per zona
@lru_cache(maxsize=None)
def sifat(zona, tambah=0.0):
    zp = ZP[zona]
    uj = t3.PROFIL[zp]["ujung"] + tambah
    a = ns.izin_sni(zp, uj)
    r = t6.hitung("A", zp, uj)
    l = t6.lrfd_A(r)
    return dict(zp=zp, panjang=PANJANG + tambah, izin=a["izin"], izin_st=a["izin_st"], izin_lik=a["izin_lik"], Qult=a["Qult_st"],
                Qult_tu=a["Qult_tanpaU5"], Qn1=a["Qn1"], Qn2=a["Qn2"], sf=r["Qs_st"] / KEL, qb=r["Qb"] / AG, Qb=r["Qb"], **l)


def tambah_zona(zona, varian):
    return TAMBAH if (varian == "b" and ZP[zona] == "SELATAN") else 0.0


# ------------------------------------------------------------------ beban tiang kelompok kaku
def _geom(pos):
    p = np.array(pos, float)
    xc, yc = p[:, 0].mean(), p[:, 1].mean()
    return p, xc, yc, ((p[:, 0] - xc) ** 2).sum(), ((p[:, 1] - yc) ** 2).sum()


def momen_ecc(pos, beban):
    """Momen eksentrisitas beban terhadap titik berat grup: (Mx, My) = (sum P (y - yc), sum P (x - xc)).
    Konvensi: Mx (dan Mux) ditahan oleh sebaran y tiang; My (dan Muy) oleh sebaran x. beban = [(x, y, P)]."""
    _, xc, yc, _, _ = _geom(pos)
    return sum(P * (y - yc) for x, y, P in beban), sum(P * (x - xc) for x, y, P in beban)


def beban_tiang(pos, beban, mux=0.0, muy=0.0):
    """Rumus cap kaku: Pi = sum P / n + (Mx + Mux) (yi - yc) / sum (y - yc)^2 + (My + Muy) (xi - xc) / sum (x - xc)^2."""
    p, xc, yc, sx, sy = _geom(pos)
    mx, my = momen_ecc(pos, beban)
    out = np.full(len(p), sum(b[2] for b in beban) / len(p))
    if sy > 1e-9:
        out += (mx + mux) * (p[:, 1] - yc) / sy
    if sx > 1e-9:
        out += (my + muy) * (p[:, 0] - xc) / sx
    return out


def beban_matriks(pos, beban, mux=0.0, muy=0.0):
    """Cara kedua: kesetimbangan sum Pi = P, sum Pi (yi - yc) = Mx + Mux, sum Pi (xi - xc) = My + Muy (norma minimum, lstsq)."""
    p, xc, yc, _, _ = _geom(pos)
    mx, my = momen_ecc(pos, beban)
    A = np.vstack([np.ones(len(p)), p[:, 1] - yc, p[:, 0] - xc])
    b = np.array([sum(q[2] for q in beban), mx + mux, my + muy])
    return np.linalg.lstsq(A, b, rcond=None)[0]


# ------------------------------------------------------------------ efisiensi dan seret kelompok
def blok(pos):
    """Blok kelompok (persegi panjang pembungkus tiang + D): B (x), Z (y), keliling, luas."""
    p = np.array(pos, float)
    B, Z = np.ptp(p[:, 0]) + D, np.ptp(p[:, 1]) + D
    return B, Z, 2 * (B + Z), B * Z


def converse_labarre(pos):
    """Efisiensi Converse-Labarre untuk grid persegi panjang m x n; None bila bukan grid [Literatur, pembanding]."""
    p = np.round(np.array(pos, float), 3)
    m, n = len(set(p[:, 0])), len(set(p[:, 1]))
    if m * n != len(p):
        return None
    dm = cKDTree(p).query(p, k=2)[0][:, 1].min()
    th = math.degrees(math.atan(D / dm))
    return 1 - th * (n * (m - 1) + m * (n - 1)) / (90 * m * n)


def efisiensi(pos, s):
    """Efisiensi kelompok = min(1, kapasitas blok / (n Qult)); blok = keliling x sum f dz (U5-U7) + luas x qb (NHI-06-089 Pers. 9-18);
    tanah tanpa kohesi dan jarak >= 3D: jumlah tiang (hal. 9-78). Tanpa-dasar = hanya selimut blok (informasi, konservatif)."""
    n = len(pos)
    B, Z, per, luas = blok(pos)
    Qblok = per * s["sf"] + luas * s["qb"]
    Qblok0 = per * s["sf"]
    return dict(B=B, Z=Z, keliling=per, luas=luas, Qblok=Qblok, Qblok_tanpa_dasar=Qblok0, n_Qult=n * s["Qult"],
                eta=min(1.0, Qblok / (n * s["Qult"])), eta_tanpa_dasar=min(1.0, Qblok0 / (n * s["Qult"])), eta_cl=converse_labarre(pos))


# ------------------------------------------------------------------ pemeriksaan satu cap
def periksa(pos, titik, zona, tambah=0.0, tanda=None, h=None):
    """Semua cek satu cap. titik = [{x, y, Pmax, Pu, Pumin, Mux, Muy}]; zona = kunci SELATAN/TENGAH/UTARA (sifat terlemah di cap)."""
    s = sifat(zona, tambah)
    n = len(pos)
    lay = [(t["x"], t["y"], t["Pmax"]) for t in titik]
    uls = [(t["x"], t["y"], t["Pu"]) for t in titik]
    umin = [(t["x"], t["y"], t["Pumin"]) for t in titik]
    W = Wu = Wm = A = xc = yc = 0.0
    if h is not None:           # berat cap di pusat telapak: layan W, Pu maks 1,2 W, Pu min 0,9 W
        pa = np.array(pos, float)
        xc, yc = float((pa[:, 0].min() + pa[:, 0].max()) / 2), float((pa[:, 1].min() + pa[:, 1].max()) / 2)
        A = float((np.ptp(pa[:, 0]) + 2 * TEPI) * (np.ptp(pa[:, 1]) + 2 * TEPI))
        W = berat_cap(A, h)
        Wu, Wm = F_W["maks"] * W, F_W["min"] * W
        lay.append((xc, yc, W))
        uls.append((xc, yc, Wu))
        umin.append((xc, yc, Wm))
    P_lay = beban_tiang(pos, lay)
    mux, muy = sum(abs(t["Mux"]) for t in titik), sum(abs(t["Muy"]) for t in titik)
    mak, mik = [], []
    for sx, sy in (tanda or TANDA):
        mak.append(beban_tiang(pos, uls, sx * mux, sy * muy))
        mik.append(beban_tiang(pos, umin, sx * mux, sy * muy))
    Pu_maks, Pu_min = float(np.max(mak)), float(np.min(mik))
    sumP, sumPu = sum(b[2] for b in lay), sum(b[2] for b in uls)
    ef = efisiensi(pos, s)
    f_kel = min(n, ef["keliling"] / KEL)           # seret kelompok: keliling blok vs jumlah tiang (NHI-06-089 hal. 9-89)
    Qn1k, Qn2k = s["Qn1"] * f_kel, s["Qn2"] * f_kel
    izin_kel = min(ef["eta"] * n * s["Qult"] / t6.FK - Qn1k, ef["eta"] * n * s["Qult_tu"] / t6.FK_GM - Qn2k)
    dmin = float(cKDTree(np.array(pos)).query(np.array(pos), k=2)[0][:, 1].min())
    r = dict(n=n, sumP=sumP, sumPu=sumPu, P_layan=float(P_lay.max()), P_layan_min=float(P_lay.min()), Pu_maks=Pu_maks, Pu_min=Pu_min,
             Pu_rata=sumPu / n, izin=s["izin"], tekan_st=s["tekan_st"], tekan_gm=s["tekan_gm"], tarik_gm=s["tarik_gm"],
             Qn_kel=Qn1k, Qn_per_tiang=Qn1k / n, f_kel=f_kel, izin_kel=izin_kel, dmin=dmin, ef=ef, mux=mux, muy=muy,
             P_lay_semua=P_lay, W=W, Wu=Wu, Wm=Wm, A=A, h=h, xc=xc, yc=yc)
    r["cek"] = dict(layan=r["P_layan"] <= s["izin"] + 1e-9, kelompok=izin_kel >= sumP - 1e-9, tekan_gm=Pu_maks <= s["tekan_gm"],
                    tekan_st=r["Pu_rata"] <= s["tekan_st"], tarik=Pu_min >= -s["tarik_gm"], jarak=dmin >= S - 1e-9)
    r["lolos"] = all(r["cek"].values())
    return r


# ------------------------------------------------------------------ data titik beban
@lru_cache(maxsize=1)
def titik_beban():
    """77 titik reaksi dengan zona, kelompok Tahap 3 dan n Tahap 3 (dari 6.0)."""
    kel = tl.kelompok()
    baris, _ = tl.cocok_reaksi()
    out = {}
    for r in baris:
        out[r["Titik"]] = dict(nama=r["Titik"], x=float(r["x (m)"]), y=float(r["y (m)"]), Pmax=float(r["Pmax layan (kN)"]),
                               Pmin=float(r["Pmin layan (kN)"]), Pu=float(r["Pu maks (kN)"]), Pumin=float(r["Pu min (kN)"]),
                               Mux=float(r["Mux (kNm)"]), Muy=float(r["Muy (kNm)"]), Tu=float(r["Tu (kNm)"]), gi=r["gi"],
                               n_t3=kel[r["gi"]][2], zona=p3.zona(r["x (m)"], r["y (m)"]))
    return out


def zona_cap(titik):
    """Zona sifat terlemah: semua titik SELATAN -> SELATAN; selain itu UTARA (TENGAH diperlakukan UTARA)."""
    return "SELATAN" if all(ZP[t["zona"]] == "SELATAN" for t in titik) else "UTARA"


def grid(nx, ny, titik, dx=0.0, dy=0.0, sx=S, sy=S):
    """Posisi grid nx x ny (jarak sx, sy >= 2,4 m): pusat di titik berat beban (Pmax) + geseran (dx, dy), digeser seperlunya
    agar semua titik beban di dalam cap dengan margin 0,4 m; None bila mustahil."""
    P = sum(t["Pmax"] for t in titik)
    c = [sum(t[k] * t["Pmax"] for t in titik) / P + d for k, d in (("x", dx), ("y", dy))]
    for i, (k, nn, s) in enumerate((("x", nx, sx), ("y", ny, sy))):
        h = (nn - 1) * s / 2 + TEPI
        lo = max(t[k] for t in titik) + MARGIN - h
        hi = min(t[k] for t in titik) - MARGIN + h
        if lo > hi + 1e-9:
            return None
        c[i] = min(max(c[i], lo), hi)
    return [(c[0] + (i - (nx - 1) / 2) * sx, c[1] + (j - (ny - 1) / 2) * sy) for j in range(ny) for i in range(nx)]


def cap_kolom(varian="a"):
    """56 cap kolom biasa: n = max(2, ceil(Pmax/izin zona)), naik bila ada cek yang gagal (pola Tahap 3 `tahap3_bim.pola`)."""
    gabung = {g for pr in tl.zona_gabung() for g in pr}
    out = []
    for nm, t in titik_beban().items():
        if nm.startswith("INTI") or t["gi"] in gabung:
            continue
        z = zona_cap([t])
        tm = tambah_zona(z, varian)
        n = max(2, math.ceil(t["Pmax"] / sifat(z, tm)["izin"]))
        while True:
            if n > 6:
                raise RuntimeError(f"pola Tahap 3 hanya sampai 6 tiang: {nm}")
            p, (w, d) = b3.pola(n)
            pos = [(t["x"] + a, t["y"] + b) for a, b in p]
            r = periksa(pos, [t], z, tm, h=tebal_cap(n))
            if r["lolos"]:
                break
            n += 1
        out.append(dict(id=nm, jenis="kolom", titik=[t], zona=z, tambah=tm, pos=pos, ukuran=(w, d), n_t3=t["n_t3"], n0=n, r=r))
    return out


def _layout(titik, z, tm, pohon, n0, tanda=None, hc=None):
    """Generator tata letak cap inti yang lolos semua cek dan tidak bentrok dengan `pohon` (tiang lain), urut n lalu luas cap,
    lalu geseran terkecil. Konflik jarak dihitung vektor untuk semua geseran sekaligus."""
    P = sum(t["Pmax"] for t in titik)
    c0 = np.array([sum(t[k] * t["Pmax"] for t in titik) / P for k in ("x", "y")])
    G = np.array(GESER)
    cand = sorted(((nx * ny, ((nx - 1) * sx + 2 * TEPI) * ((ny - 1) * sy + 2 * TEPI), nx, ny, sx, sy)
                   for nx in range(1, 10) for ny in range(1, 10) for sx in SPASI for sy in SPASI
                   if nx * ny >= n0 and (nx > 1 or sx == S) and (ny > 1 or sy == S)))
    for n, _, nx, ny, sx, sy in cand:
        cs = np.empty_like(G)
        ok = np.ones(len(G), bool)
        for a, (k, nn, s) in enumerate((("x", nx, sx), ("y", ny, sy))):
            h = (nn - 1) * s / 2 + TEPI
            lo = max(t[k] for t in titik) + MARGIN - h
            hi = min(t[k] for t in titik) - MARGIN + h
            if lo > hi + 1e-9:
                ok[:] = False
                break
            cs[:, a] = np.clip(c0[a] + G[:, a], lo, hi)
        if not ok.any():
            continue
        off = np.array([((i - (nx - 1) / 2) * sx, (j - (ny - 1) / 2) * sy) for j in range(ny) for i in range(nx)])
        _, idx = np.unique(np.round(cs, 6), axis=0, return_index=True)
        cen = cs[np.sort(idx)]                               # pusat unik, urutan geseran terkecil dipertahankan
        d = pohon.query((cen[:, None, :] + off[None, :, :]).reshape(-1, 2))[0].reshape(len(cen), -1).min(1)
        for ic in np.nonzero(d >= S - 1e-9)[0]:
            pos = [tuple(map(float, q)) for q in cen[ic] + off]
            r = periksa(pos, titik, z, tm, tanda, hc)
            if r["lolos"]:
                yield (pos, r, nx, ny, sx, sy, float(cen[ic][0] - c0[0]), float(cen[ic][1] - c0[1]))


def cap_inti(varian="a", lain=()):
    """Tujuh cap inti gabungan: grid persegi panjang (jarak >= 2,4 m, pilihan SPASI) dengan n terkecil (lalu luas cap terkecil)
    yang lolos semua cek dan tidak bentrok (< 2,4 m) dengan tiang lain. Pencarian menelusur balik (DFS): bila cap berikutnya
    tak punya tata letak, cap sebelumnya memakai alternatif berikutnya. Cap dengan beban terbesar dicoba lebih dulu."""
    tb = titik_beban()
    urut = sorted(INTI, key=lambda k: -sum(tb[t]["Pmax"] for t in INTI[k]))
    info = {}
    for kode in urut:
        titik = [tb[k] for k in INTI[kode]]
        z = zona_cap(titik)
        info[kode] = (titik, z, tambah_zona(z, varian), max(2, math.ceil(sum(t["Pmax"] for t in titik) / sifat(z, tambah_zona(z, varian))["izin"])))

    pohon0 = cKDTree(np.array(lain))
    daftar = {k: list(itertools.islice(_layout(*info[k][:3], pohon0, info[k][3], None, tebal_cap(kode=k)), 3000)) for k in urut}   # 3000 tata letak teratas per cap
    pohon_u = cKDTree(np.array(utilitas()))
    for k in urut:
        if not daftar[k]:       # cap kolom bertambah tiang (berat cap) sehingga cap inti tak muat di antara tiang lain: cari tanpa memperhitungkan cap kolom;
            # telapak yang menumpang cap kolom digabung dan dicek ulang (jarak, izin, berat) di gabung_cap
            daftar[k] = list(itertools.islice(_layout(*info[k][:3], pohon_u, info[k][3], None, tebal_cap(kode=k)), 3000))
        if not daftar[k]:       # tanpa tata letak berberat cap: sementara tanpa berat (cap itu digabung dan dicek ulang berberat di gabung_cap; sisa dicek di rancang)
            daftar[k] = list(itertools.islice(_layout(*info[k][:3], pohon_u, info[k][3]), 3000))

    def dfs(i, pilih):
        if i == len(urut):
            return []
        kode = urut[i]
        titik, z, tm, n0 = info[kode]
        for pos, r, nx, ny, sx, sy, dx, dy in daftar[kode]:
            if any(cKDTree(np.array(q)).query(np.array(pos))[0].min() < S - 1e-9 for q in pilih):
                continue
            rest = dfs(i + 1, pilih + [pos])
            if rest is not None:
                w, d = (nx - 1) * sx + 2 * TEPI, (ny - 1) * sy + 2 * TEPI
                n3 = sum(t["n_t3"] for t in titik if not t["nama"].startswith("INTI")) + 6
                return [dict(id=f"Cap {kode}", kode=kode, jenis="inti", titik=titik, zona=z, tambah=tm, pos=pos, ukuran=(w, d), nx=nx, ny=ny,
                             sx=sx, sy=sy, n0=n0, n_t3=n3, geser=(dx, dy), r=r)] + rest
        return None

    hasil = dfs(0, [])
    if hasil is None:       # cap kolom bertambah tiang (berat cap): cari tata letak cap inti tanpa memperhitungkan cap kolom (bentrok antar cap inti tetap dilarang);
        # telapak yang menumpang cap kolom digabung dan dicek ulang di gabung_cap
        for k in urut:
            daftar[k] = list(itertools.islice(_layout(*info[k][:3], pohon_u, info[k][3], None, tebal_cap(kode=k)), 3000)) or daftar[k]
        hasil = dfs(0, [])
    if hasil is None:
        raise RuntimeError("tidak ada tata letak cap inti yang bebas bentrok")
    return sorted(hasil, key=lambda c: c["kode"])


def utilitas():
    kel, pos, own = tl._data()
    return [tuple(map(float, p)) for p, g in zip(pos, own) if kel[g][0] >= tl.X_UTILITAS]


@lru_cache(maxsize=None)
def kepekaan_penuh():
    """Kepekaan: Mux, Muy 100 % + 100 % serentak. Tata letak terkecil tiap cap inti terhadap cap kolom dan utilitas (tanpa interaksi antar cap inti),
    lalu cek apakah semuanya dapat hidup berdampingan (jarak >= 2,4 m)."""
    ck = cap_kolom("a")
    pohon0 = cKDTree(np.array([q for c in ck for q in c["pos"]] + utilitas()))
    tb = titik_beban()
    hasil = {}
    for kode, nama in INTI.items():
        titik = [tb[k] for k in nama]
        z = zona_cap(titik)
        n0 = max(2, math.ceil(sum(t["Pmax"] for t in titik) / sifat(z)["izin"]))
        pos, r, nx, ny, sx, sy, dx, dy = next(_layout(titik, z, 0.0, pohon0, n0, TANDA_PENUH, tebal_cap(kode=kode)))
        hasil[kode] = dict(n=r["n"], nx=nx, ny=ny, sx=sx, sy=sy, pos=pos, Pu_maks=r["Pu_maks"], Pu_min=r["Pu_min"])
    bentrok = [(a, b) for a, b in itertools.combinations(hasil, 2)
               if cKDTree(np.array(hasil[a]["pos"])).query(np.array(hasil[b]["pos"]))[0].min() < S - 1e-9]
    return dict(per_cap=hasil, n=sum(v["n"] for v in hasil.values()), bentrok=bentrok)


def telapak(c):
    """Telapak cap (x0, y0, x1, y1): sumbu tiang terluar + TEPI."""
    p = np.array(c["pos"], float)
    return p[:, 0].min() - TEPI, p[:, 1].min() - TEPI, p[:, 0].max() + TEPI, p[:, 1].max() + TEPI


def bertumpang(a, b):
    """Luas tumpang dua telapak persegi (m2)."""
    ax0, ay0, ax1, ay1 = telapak(a)
    bx0, by0, bx1, by1 = telapak(b)
    return max(0.0, min(ax1, bx1) - max(ax0, bx0)) * max(0.0, min(ay1, by1) - max(ay0, by0))


def gabung_cap(ck, ci, varian="a"):
    """Gabungkan cap yang telapaknya bertumpang (keputusan Defsa 22 Nov 2026: Cap C digabung ke Cap E): satu cap = selubung telapak,
    tiang = gabungan, beban = jumlah titik beban; cek ulang dengan rumus cap kaku. Nama = cap dengan tiang terbanyak."""
    semua = list(ck) + list(ci)
    grup = [[c] for c in semua]
    berubah = True
    while berubah:
        berubah = False
        for i in range(len(grup)):
            for j in range(i + 1, len(grup)):
                if any(bertumpang(a, b) > 1e-6 for a in grup[i] for b in grup[j]):
                    grup[i] += grup.pop(j)
                    berubah = True
                    break
            if berubah:
                break
    hasil = []
    for g in grup:
        if len(g) == 1:
            hasil.append(g[0])
            continue
        utama = max(g, key=lambda c: c["r"]["n"])
        pos = [q for c in g for q in c["pos"]]
        titik = [t for c in g for t in c["titik"]]
        z = zona_cap(titik)
        tm = tambah_zona(z, varian)
        x0, y0, x1, y1 = [f(v) for f, v in zip((min, min, max, max), zip(*[telapak(c) for c in g]))]
        sp = float(cKDTree(np.array(pos)).query(np.array(pos), k=2)[0][:, 1].min())
        hg = tebal_cap(kode=utama.get("kode"))
        r = periksa(pos, titik, z, tm, h=hg)
        d = dict(id=utama["id"], kode=utama.get("kode"), jenis="inti", titik=titik, zona=z, tambah=tm, pos=pos, ukuran=(x1 - x0, y1 - y0),
                 nx=len({round(q[0], 3) for q in pos}), ny=len({round(q[1], 3) for q in pos}), sx=sp, sy=sp, n0=sum(c["n0"] for c in g),
                 n_t3=sum(c["n_t3"] for c in g), geser=(0.0, 0.0), r=r, gabungan=[c["id"] for c in g], union=None,
                 sebelum={c["id"]: {k: c["r"][k] for k in ("n", "P_layan", "Pu_maks", "Pu_min", "sumP")} for c in g})
        if not r["lolos"]:
            # gabungan polos (union tiang) gagal cek (mis. Pu maks > tekan gempa): cari tata letak baru untuk beban gabungan dengan n terkecil,
            # jarak >= 2,4 m terhadap tiang lain dan telapak tidak menumpang cap lain (mekanisme cap_inti)
            d["union"] = dict(n=r["n"], Pu_maks=r["Pu_maks"], P_layan=r["P_layan"], Pu_min=r["Pu_min"], cek={k: bool(v) for k, v in r["cek"].items()})
            lain_c = [c for c in semua if not any(c is x for x in g)]
            pohon = cKDTree(np.array([q for c in lain_c for q in c["pos"]] + utilitas()))
            n0 = max(2, math.ceil(sum(t["Pmax"] for t in titik) / sifat(z, tm)["izin"]))
            for pos2, r2, nx, ny, sx, sy, dx, dy in itertools.islice(_layout(titik, z, tm, pohon, n0, None, hg), 400):
                cand = dict(pos=pos2)
                if all(bertumpang(cand, c) < 1e-6 for c in lain_c):
                    w, dd = (nx - 1) * sx + 2 * TEPI, (ny - 1) * sy + 2 * TEPI
                    d.update(pos=pos2, r=r2, ukuran=(w, dd), nx=nx, ny=ny, sx=sx, sy=sy, n0=n0, geser=(dx, dy))
                    break
            else:
                d["tak_lolos"] = True        # varian (b): gabungan polos dipertahankan; rancang("a") tetap menolak hasil seperti ini
        hasil.append(d)
    return [c for c in hasil if c["jenis"] != "inti"], sorted([c for c in hasil if c["jenis"] == "inti"], key=lambda c: c["kode"])


@lru_cache(maxsize=None)
def rancang(varian="a"):
    """Hasil 6.3 (cap kolom, cap inti). Cache disk `cache/tahap6_rancang_<varian>_<sidik skrip>.pkl` (4-5 menit tanpa cache); TANPA_CACHE=1 memaksa hitung ulang."""
    import hashlib
    import os
    import pickle
    import inspect
    fn = (periksa, _layout, cap_inti, cap_kolom, gabung_cap, _rancang, berat_cap, tebal_cap, sifat, grid, beban_tiang)      # sidik hanya logika rancangan (teks md/Excel tidak ikut)
    kons = repr((GAMMA_BETON, MUKA_AIR_DESAIN, MUKA_CAP, H_KOLOM, H_INTI, H_E, H_KOLOM_LAIN, F_W, S, TEPI, MARGIN, SPASI, INTI, TANDA, N_UTILITAS))
    sidik = hashlib.sha256((kons + "".join(inspect.getsource(getattr(f, "__wrapped__", f)) for f in fn)).encode()).hexdigest()[:12]
    berkas = AKAR / "cache" / f"tahap6_rancang_{varian}_{sidik}.pkl"
    if berkas.exists() and not os.environ.get("TANPA_CACHE"):
        return pickle.loads(berkas.read_bytes())
    hasil = _rancang(varian)
    berkas.parent.mkdir(exist_ok=True)
    berkas.write_bytes(pickle.dumps(hasil))
    return hasil


def _rancang(varian="a"):
    ck = cap_kolom(varian)
    lain = [q for c in ck for q in c["pos"]] + utilitas()
    hasil = gabung_cap(ck, cap_inti(varian, lain), varian)
    for c in hasil[0] + hasil[1]:
        if varian == "a" and c.get("tak_lolos"):
            raise RuntimeError(f"{c['id']}: tidak ada tata letak gabungan yang lolos dan bebas tumpang")
        if c["r"]["W"] == 0.0 and c["jenis"] != "utilitas":
            raise RuntimeError(f"{c['id']}: tidak ada tata letak berberat cap dan tidak digabung")
    return hasil


# ------------------------------------------------------------------ ringkasan, temuan, T-101
def ringkas(varian="a"):
    ck, ci = rancang(varian)
    n_ck, n_ci = sum(c["r"]["n"] for c in ck), sum(c["r"]["n"] for c in ci)
    t3_ck, t3_ci = sum(c["n_t3"] for c in ck), sum(c["n_t3"] for c in ci)
    L = sum(c["r"]["n"] * (PANJANG + c["tambah"]) for c in ck + ci)
    return dict(n_kolom=n_ck, n_inti=n_ci, n=n_ck + n_ci, n_t3_kolom=t3_ck, n_t3_inti=t3_ci, n_t3=t3_ck + t3_ci,
                panjang=L, panjang_t3=(t3_ck + t3_ci) * PANJANG, total=n_ck + n_ci + N_UTILITAS)


def temuan_lif():
    """Temuan 6.2: Pmax layan per tiang selatan 1.710 kN (INTI-LIF 10.258 / 6) > izin 1.583 kN."""
    t = titik_beban()["INTI-LIF"]
    s = sifat("SELATAN")
    out = dict(P=t["Pmax"], n_t3=6, per_tiang=t["Pmax"] / 6, izin=s["izin"], n_sendiri=math.ceil(t["Pmax"] / s["izin"]), izin_b=sifat("SELATAN", TAMBAH)["izin"])
    for v in "ab":
        c = next(c for c in rancang(v)[1] if c["kode"] == "E")
        out[v] = dict(n=c["r"]["n"], n0=c["n0"], P_layan=c["r"]["P_layan"], sumP=c["r"]["sumP"], grid=_fmt_grid(c), panjang=PANJANG + c["tambah"])
    return out


def penentu(r):
    """Rasio pemakaian tiap cek di tata letak akhir: (nama, rasio) terbesar."""
    rs = {"layan (Pmax/tiang vs izin)": r["P_layan"] / r["izin"], "tekan gempa (Pu maks vs tekan_gm)": r["Pu_maks"] / r["tekan_gm"],
          "tarik gempa (-Pu min vs tarik_gm)": max(0.0, -r["Pu_min"]) / r["tarik_gm"], "kelompok (sum P vs izin kelompok)": r["sumP"] / r["izin_kel"]}
    return max(rs.items(), key=lambda a: a[1]), rs


def semua_tiang(varian="a"):
    ck, ci = rancang(varian)
    return [q for c in ck + ci for q in c["pos"]] + utilitas()


def t101(varian=("a", "b"), ex=None):
    """Cek silang T-101. ex = hasil baca Excel hidup {kode: (maks layan, maks Pu)} (opsional)."""
    selisih, dsig, dsum, pasang, ef_min, cl_min = 0.0, 0.0, 0.0, 0, 1.0, 1.0
    wtot = 0.0
    tak_b = []
    tb = titik_beban()
    for v in varian:
        ck, ci = rancang(v)
        tot = 0.0
        wtot = 0.0
        for c in ck + ci:
            pos, tt = c["pos"], c["titik"]
            rr = c["r"]
            lay = [(t["x"], t["y"], t["Pmax"]) for t in tt] + [(rr["xc"], rr["yc"], rr["W"])]
            uls = [(t["x"], t["y"], t["Pu"]) for t in tt] + [(rr["xc"], rr["yc"], rr["Wu"])]
            wtot += rr["W"]
            mux, muy = c["r"]["mux"], c["r"]["muy"]
            pairs = [(lay, 0.0, 0.0)] + [(uls, sx * mux, sy * muy) for sx, sy in TANDA]
            for bb, a, b in pairs:
                if c.get("tak_lolos"):      # varian (b): gabungan polos tak berberat-cap-lolos, bukan rancangan terpilih (hanya dilaporkan)
                    break
                p1, p2 = beban_tiang(pos, bb, a, b), beban_matriks(pos, bb, a, b)
                selisih = max(selisih, float(np.abs(p1 - p2).max() / np.abs(p1).max() * 100))
            tot += float(beban_tiang(pos, lay).sum())
            dsum = max(dsum, abs(float(beban_tiang(pos, lay).sum()) - sum(b[2] for b in lay)) / sum(b[2] for b in lay) * 100)
            ef_min = min(ef_min, c["r"]["ef"]["eta"])
            if c["r"]["ef"]["eta_cl"] is not None:
                cl_min = min(cl_min, c["r"]["ef"]["eta_cl"])
        ref = sum(t["Pmax"] for t in tb.values()) + wtot            # Σ reaksi 77 titik + berat semua cap
        dsig = max(dsig, abs(tot - ref) / ref * 100)
        pos = np.array(semua_tiang(v))
        if any(c.get("tak_lolos") for c in ck + ci):
            tak_b.append(v)
        else:
            pasang += len(cKDTree(pos).query_pairs(S - 1e-9))
    dex = max((max(abs(a - b) / abs(b) * 100 for a, b in zip(ex[k][0], ex[k][1])) for k in ex), default=None) if ex else None
    lolos = (selisih <= TOL["rigid"] and dsig <= TOL["sigma"] and dsum <= TOL["sigma"] and pasang <= TOL["jarak"]
             and (dex is None or dex <= TOL["rigid"]))
    return dict(selisih=selisih, dsig=dsig, dsum=dsum, pasang=pasang, eta_min=ef_min, cl_min=cl_min, dex=dex, lolos=lolos, tak_b=tak_b)


def catat_t101(r=None, berkas=VERIFIKASI):
    r = r or t101()
    ra, rb = ringkas("a"), ringkas("b")
    baris = ("| T-101 | Cek silang 6.3 jumlah dan tata letak tiang bor Ø800 (cap kolom + cap inti gabungan (Cap C digabung ke Cap E), berat cap dimasukkan (temuan 6.9, usulan AI, disetujui atas delegasi Defsa 22 Nov 2026), varian (a) tambah tiang dan (b) selatan 40,00 m) "
             f"| (a) beban tiang rumus cap kaku (skrip) vs penyelesaian matriks kesetimbangan (lstsq; Σ Pi = Σ P, Σ Pi·xi = M), selisih terbesar {idn(r['selisih'], 4)} %"
             + (f"; rumus Excel hidup (lembar Cap Inti) vs skrip {idn(r['dex'], 4)} %" if r["dex"] is not None else "")
             + f"; (b) Σ Pmax layan semua cap vs Σ reaksi 77 titik 5.6: selisih {idn(r['dsig'], 4)} % "
             f"| (c) jarak terdekat semua tiang (gedung utama + utilitas, dua varian): {r['pasang']} pasangan < 2,4 m; (d) efisiensi blok (NHI-06-089 Pers. 9-18) terkecil "
             f"{idn(r['eta_min'], 2)} vs Converse-Labarre terkecil {idn(r['cl_min'], 2)} (dilaporkan; CL hanya pembanding) "
             f"| (a) ≤ 0,5 %; (b) ≤ 0,1 %; (c) 0 pasangan < 2,4 m; (d) dilaporkan | {'Lolos' if r['lolos'] else 'GAGAL'}, {STATUS} "
             "| `skrip/tahap6_tata_letak.py`, `tests/test_tahap6_tata_letak.py` | Ditetapkan sebelum membandingkan. Data simulasi. "
             f"Gedung utama (a): {ra['n']} tiang vs {N_T3} Tahap 3; (b): {rb['n']} tiang. "
             + ("Varian (b): gabungan Cap E tidak menemukan tata letak berberat-cap yang lolos (polos dipertahankan, hanya dilaporkan; dikecualikan dari (a) dan (c)). " if r.get("tak_b") else "")
             + "Cek (b) memasukkan berat semua cap. |")
    teks = Path(berkas).read_text(encoding="utf-8").split("\n")
    teks = [ln for ln in teks if not ln.startswith("| T-101 |")]
    i = next(k for k, ln in enumerate(teks) if ln.startswith("| T-100 |"))
    teks.insert(i + 1, baris)
    Path(berkas).write_text("\n".join(teks), encoding="utf-8")
    return baris


# ------------------------------------------------------------------ Excel
ACUAN = [
    ("FHWA-NHI-06-089 Vol II 9.6.1.1 (tanah tanpa kohesi, jarak >= 3D: jumlah tiang), 9.6.1.3 Pers. 9-18/9-19 (kegagalan blok)", "ada",
     "acuan/pustaka/FHWA-NHI-06-089-Soils-and-Foundations-Vol-II.pdf; hal. 188, 191-192 (PDF); cetak 9-78, 9-81, 9-82"),
    ("FHWA-NHI-06-089 Vol II 9.8 (seret kelompok dari luas keliling blok)", "ada", "hal. 199 (PDF); cetak 9-89"),
    ("SNI 8460:2017 Pasal 9.7.2.1 hal. 204 (seret sebagai beban), 9.2.3.1 hal. 194 (FK 2,5)", "ada", "acuan/privat"),
    ("FHWA GEC10 Tabel 8-4 (tahanan terfaktor, tekan gempa phi 1,0, tarik 0,80) dan 10.6 (seret)", "ada", "acuan/pustaka/FHWA-NHI-18-024-GEC10-Drilled-Shafts.pdf; hal. 222 (PDF)"),
    ("SNI 1726:2019 Pasal 7.5.3 a (kombinasi ortogonal 100 % + 30 %)", "ada", "acuan/privat; hal. 79 PDF (cetak 67)"),
    ("Converse-Labarre (efisiensi kelompok grid persegi panjang)", "belum ada", "[Literatur, belum ada di acuan/]: pembanding saja."),
    ("SNI 8460 / SNI 2847 jarak tiang minimum dan tepi cap", "belum ada", "Jarak 3D (2,4 m) dan tepi 0,8 m mengikuti Tahap 3/keputusan 6.0; pasal jarak minimum tidak dikutip."),
]

KEPUTUSAN = [
    ("Kombinasi arah gempa cap inti", "Dipakai 100 % + 30 % (SNI 1726:2019 Pasal 7.5.3 a, hal. 79 PDF): Mux, Muy dari 5.6 diterapkan 100 % satu arah + 30 % arah tegak lurus, "
     "tanda bolak-balik, bersama Pu maks (5.6 tidak memberi Pu per kombinasi gempa, jadi konservatif). Arahan tugas awal 100 % + 100 % serentak menghasilkan jumlah tiang "
     "jauh lebih banyak dan cap C dan E tidak muat berdampingan (jarak < 2,4 m); hasilnya di bagian Kepekaan. Bila 5.6 sudah memuat selubung dua arah, pilih 100 % + 100 % "
     "dan gabungkan cap C dan E (keputusan tambahan)."),
    ("Jarak tiang cap inti", "Jarak 2,4 m (3D) dan pilihan 3,6 / 4,8 m bila lengan momen perlu (>= 3D, NHI-06-089 hal. 9-78); spasi lebar mengurangi jumlah tiang "
     "tetapi memperbesar cap. Cap dibuat sebesar tata letak, tebal 1,20 m dan tulangan cap dicek di 6.4."),
    ("Pilihan (a) tambah tiang atau (b) perpanjang selatan ke 40,00 m", "Lihat lembar Varian 40 m: selisih tiang, panjang total, dan izin 1.750 kN. (b) hanya untuk cap yang "
     "seluruh titiknya di zona selatan; cap campuran memakai sifat utara/tengah."),
    ("Zona tengah", "Memakai izin dan tahanan zona utara (1.443 kN) [Asumsi: konservatif; 6.2 tidak menghitung tengah]."),
    ("Momen layan", "5.6 tidak memberi momen layan; cek layan hanya memuat eksentrisitas beban aksial terhadap titik berat grup tiang."),
    ("Beban inti titik", "Inti dimodelkan sebagai beban titik (ukuran dinding inti tidak dipakai); dinding inti sebenarnya menyebarkan beban sehingga tiang pinggir lebih ringan."),
    ("Efisiensi dan seret kelompok", "Tanah tanpa kohesi pada tahanan U5-U7 dan jarak >= 3D: efisiensi 1,0 selama blok (selimut + dasar) >= jumlah tiang (NHI-06-089 hal. 9-78, 9-81). "
     "Seret kelompok = min(n x Qn tunggal, keliling blok x seret satuan) (hal. 9-89); berat tanah dalam blok tidak ditambahkan (acuan tidak menyebut)."),
    ("Tu (torsi)", "Torsi diabaikan pada beban aksial tiang [Asumsi]; dicek di 6.4 sebagai geser cap."),
    ("Penggabungan Cap C ke Cap E (revisi 22 Nov 2026)", "Telapak Cap C (14 tiang) berada di dalam telapak Cap E (32 tiang), tiang selang-seling; keputusan Defsa 22 Nov 2026: digabung menjadi satu cap bernama Cap E "
     "(gabungan Cap C + Cap E): tiang = gabungan (jumlah tetap), beban = jumlah titik beban kedua cap, cek ulang dengan rumus cap kaku. Penggabungan dilakukan umum (uji tumpang telapak antar semua cap)."),
    ("Berat cap (revisi 22 Nov 2026)", "Berat cap dimasukkan (temuan 6.9, usulan AI, disetujui atas delegasi Defsa 22 Nov 2026): W = A h 24 kN/m³ dikurangi apung 9,81 A (11,20 - dasar cap) "
     "bila dasar di bawah +11,20 [Asumsi: muka air desain 6.0]; A = telapak (sumbu tiang terluar + 0,8 m), h dari 6.7: cap kolom 2/3/4 tiang 1,0/0,8/0,95 m, cap inti 1,2 m, Cap E 2,0 m "
     "(5-6 tiang: 1,2 m [Asumsi]). Layan + W; gempa Pu maks + 1,2 W; Pu min + 0,9 W; W bekerja di pusat telapak. Jumlah tiang bertambah bila izin terlampaui (algoritma lama, cek tidak dihapus)."),
    ("Gedung utilitas", f"{N_UTILITAS} tiang tidak berubah (beban 3.7 [Asumsi]); berat cap utilitas tidak dicek ulang di 6.3 (tidak dihitung ulang di tahap ini)."),
]


def _fmt_grid(c):
    if c.get("gabungan"):
        return f"gabungan {' + '.join(c['gabungan'])}, {c['r']['n']} tiang"
    if c["jenis"] == "inti":
        return f"{c['nx']} x {c['ny']}" + ("" if abs(c["sx"] - S) < 1e-9 and abs(c["sy"] - S) < 1e-9 else f" (jarak {idn(c['sx'], 1)} x {idn(c['sy'], 1)} m)")
    return f"pola {c['r']['n']} tiang"


def _blok_inti(lt, c, no):
    """Satu cap inti dengan rumus Excel hidup (beban layan dan ultimit per tiang). Kembalikan (alamat maks layan, alamat maks Pu)."""
    r = c["r"]
    lt.bagian(chr(64 + no), f"{c['id']}: {', '.join(t['nama'] for t in c['titik'])}, zona {c['zona'].lower()}, {r['n']} tiang")
    rows = [[t["nama"], t["x"], t["y"], round(t["Pmax"], 1), round(t["Pu"], 1), round(t["Pumin"], 1), round(t["Mux"], 1), round(t["Muy"], 1)] for t in c["titik"]]
    if r["W"]:      # berat cap (6.3 revisi 22 Nov 2026): layan W, Pu maks 1,2 W, Pu min 0,9 W di pusat telapak; ikut dalam rumus hidup
        rows.append(["Berat cap", round(r["xc"], 4), round(r["yc"], 4), round(r["W"], 1), round(r["Wu"], 1), round(r["Wm"], 1), 0.0, 0.0])
    h0, f1, l1 = lt.tabel(["Titik", "x (m)", "y (m)", "Pmax layan (kN)", "Pu maks (kN)", "Pu min (kN)", "Mux (kNm)", "Muy (kNm)"], rows,
                          rata=["l"] + ["c"] * 7, fmt=[None, "0.00", "0.00"] + ["#,##0.0"] * 5, fill=None, beku=False)
    col = lt.kol
    rng = lambda i, a, b: f"{col(i)}{a}:{col(i)}{b}"          # noqa: E731
    K = 13
    p_h = l1 + 3                                                  # kepala tabel parameter
    q_h = p_h + K + 3                                             # kepala tabel tiang
    q1, q2 = q_h + 1, q_h + r["n"]
    B = lambda k: f"${col(1)}${p_h + 1 + k}"                      # noqa: E731
    par = [("n tiang", f"=COUNT({rng(1, q1, q2)})"), ("xc (m)", f"=AVERAGE({rng(1, q1, q2)})"), ("yc (m)", f"=AVERAGE({rng(2, q1, q2)})"),
           ("Σ (x - xc)²", f"=SUMPRODUCT(({rng(1, q1, q2)}-{B(1)})^2)"), ("Σ (y - yc)²", f"=SUMPRODUCT(({rng(2, q1, q2)}-{B(2)})^2)"),
           ("Σ Pmax (kN)", f"=SUM({rng(3, f1, l1)})"), ("Mx layan = Σ P (y - yc)", f"=SUMPRODUCT({rng(3, f1, l1)},{rng(2, f1, l1)})-{B(5)}*{B(2)}"),
           ("My layan = Σ P (x - xc)", f"=SUMPRODUCT({rng(3, f1, l1)},{rng(1, f1, l1)})-{B(5)}*{B(1)}"), ("Σ Pu maks (kN)", f"=SUM({rng(4, f1, l1)})"),
           ("Mx ult = Σ Pu (y - yc)", f"=SUMPRODUCT({rng(4, f1, l1)},{rng(2, f1, l1)})-{B(8)}*{B(2)}"),
           ("My ult = Σ Pu (x - xc)", f"=SUMPRODUCT({rng(4, f1, l1)},{rng(1, f1, l1)})-{B(8)}*{B(1)}"),
           ("|Mux| (kNm)", f"=SUMPRODUCT(ABS({rng(6, f1, l1)}))"), ("|Muy| (kNm)", f"=SUMPRODUCT(ABS({rng(7, f1, l1)}))")]
    lt.kosong()
    lt.bagian("-", "Parameter grup tiang (rumus hidup)")
    h, a, b = lt.tabel(["Parameter", "Nilai"], [[k, v] for k, v in par], rata=["l", "c"], fmt=[None, "#,##0.00"], beku=False)
    assert h == p_h, (h, p_h)
    lt.kosong()
    lt.bagian("-", "Beban tiang kaku (layan; ultimit gempa, delapan kombinasi 100 % + 30 %)")
    n_ = B(0)
    rows = []
    for k, (x, y) in enumerate(c["pos"]):
        rr = q1 + k
        dx, dy = f"{col(3)}{rr}", f"{col(4)}{rr}"
        lay = f"={B(5)}/{n_}+IFERROR({B(6)}*{dy}/{B(4)},0)+IFERROR({B(7)}*{dx}/{B(3)},0)"
        ul = [f"={B(8)}/{n_}+IFERROR(({B(9)}+({fx})*{B(11)})*{dy}/{B(4)},0)+IFERROR(({B(10)}+({fy})*{B(12)})*{dx}/{B(3)},0)" for fx, fy in TANDA]
        rows.append([k + 1, round(x, 3), round(y, 3), f"={col(1)}{rr}-{B(1)}", f"={col(2)}{rr}-{B(2)}", lay] + ul)
    h, a, b = lt.tabel(["No", "x (m)", "y (m)", "x - xc", "y - yc", "P layan (kN)", ] + [f"Pu ({'+' if fx > 0 else '-'}{idn(abs(fx), 1)} Mux, {'+' if fy > 0 else '-'}{idn(abs(fy), 1)} Muy)" for fx, fy in TANDA],
                       rows, rata=["c"] * 14, fmt=["0", "0.000", "0.000", "0.000", "0.000"] + ["#,##0.0"] * 9, fill=AI_, beku=False)
    assert h == q_h, (h, q_h)
    rm = lt.baris
    lt.tabel(["Hasil", "Maks (kN)", "Batas (kN)"], [["P layan maks / izin tiang", f"=MAX({rng(5, q1, q2)})", round(r["izin"], 1)],
                                                  ["Pu maks / tekan gempa", f"=MAX({col(6)}{q1}:{col(13)}{q2})", round(r["tekan_gm"], 1)]],
             rata=["l", "c", "c"], fmt=[None, "#,##0.0", "#,##0.0"], fill=AI_, beku=False)
    lt.kosong()
    return (f"{col(1)}{rm + 1}", f"{col(1)}{rm + 2}")


def buat_excel(keluar=BERKAS):
    import openpyxl
    from format_dokumen import AI, Lembar, set_font_bawaan
    global AI_
    AI_ = AI
    ra, rb = ringkas("a"), ringkas("b")
    ck, ci = rancang("a")
    ckb, cib = rancang("b")
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    ket = LABEL + " " + LABEL_AI
    lr = Lembar(wb.create_sheet("Ringkasan"), 1, "Jumlah dan tata letak tiang bor Ø800 (6.3)", [24, 24, 11, 12, 12, 10, 10, 18, 12, 12, 12, 8, 12, 12, 9, 9])
    lt = Lembar(wb.create_sheet("Cap Inti"), 2, "Cap inti gabungan (rumus hidup)", [16, 11, 11, 13, 14, 14, 13, 13, 13, 13, 13, 13, 13, 13])
    lk = Lembar(wb.create_sheet("Cap Kolom"), 3, "Cap kolom biasa (56 cap)", [14, 10, 12, 12, 12, 10, 10, 12, 12, 12, 12, 9])
    lv = Lembar(wb.create_sheet("Varian 40 m"), 4, "Temuan 1.710 kN: (a) tambah tiang atau (b) selatan 40,00 m", [26, 14, 14, 14, 14, 14, 14, 14])
    lf = Lembar(wb.create_sheet("Verifikasi"), 5, "Verifikasi T-101", [46, 16, 16, 40])
    la = Lembar(wb.create_sheet("Acuan"), 6, "Acuan", [60, 11, 70])
    ld = Lembar(wb.create_sheet("Keputusan"), 7, "Hal yang perlu diputuskan Defsa", [28, 110])

    # ---- Cap Inti (dibuat dulu untuk alamat rumus)
    lt.catatan(f"STATUS: {STATUS}. " + ket)
    lt.catatan("Varian (a): panjang 38,45 m semua zona. Beban dari 6.0 (reaksi 5.6). Pu dan Mu: Pu maks dipadukan dengan Mux, Muy gempa serentak (konservatif). "
               "Konvensi: Mux ditahan oleh sebaran y tiang, Muy oleh sebaran x.")
    lt.kosong()
    alamat = {}
    for no, c in enumerate(ci, 1):
        alamat[c["kode"]] = _blok_inti(lt, c, no)

    # ---- Ringkasan
    lr.catatan(f"STATUS: {STATUS}. " + ket)
    lr.catatan("Jumlah tiang, izin, dan tahanan dari 6.1/6.2 (disetujui). Sel hijau = hasil hitungan AI. Rincian cap inti di lembar Cap Inti (rumus Excel hidup), cap kolom di lembar Cap Kolom.")
    lr.kosong()
    lr.bagian("A", "Ringkasan jumlah tiang gedung utama")
    rows = [["Cap kolom biasa (56 cap)", ra["n_kolom"], ra["n_t3_kolom"], rb["n_kolom"], None],
            [f"{len(ci)} cap inti gabungan ({sum(len(c['titik']) for c in ci)} titik beban)", ra["n_inti"], ra["n_t3_inti"], rb["n_inti"], None],
            ["Gedung utama", "=SUM(D{a}:D{b})", "=SUM(E{a}:E{b})", "=SUM(F{a}:F{b})", None],
            ["Gedung utilitas + parkir (tidak berubah)", N_UTILITAS, N_UTILITAS, N_UTILITAS, None],
            ["Total", None, None, None, None]]
    r0 = lr.baris
    a1, b1 = r0 + 1, r0 + 2
    rows[2] = [rows[2][0]] + [f"=SUM({lr.kol(i)}{a1}:{lr.kol(i)}{b1})" for i in (1, 2, 3)] + [None]
    rows[4] = ["Total"] + [f"={lr.kol(i)}{r0 + 3}+{lr.kol(i)}{r0 + 4}" for i in (1, 2, 3)] + [None]
    lr.tabel(["Kelompok", "6.3 (a) tambah tiang", "Tahap 3", "6.3 (b) selatan 40 m"], [r[:4] for r in rows], rata=["l", "c", "c", "c"],
             fmt=[None, "#,##0", "#,##0", "#,##0"], fill_kolom={1: AI, 3: AI}, beku=False)
    lr.kosong()
    lr.tabel(["Panjang tiang total gedung utama (m)", "6.3 (a)", "Tahap 3", "6.3 (b)"],
             [["Σ n x panjang (38,45 m; selatan (b) 40,00 m)", round(ra["panjang"], 1), round(ra["panjang_t3"], 1), round(rb["panjang"], 1)],
              ["Selisih terhadap Tahap 3 (m), untuk Tahap 8", round(ra["panjang"] - ra["panjang_t3"], 1), None, round(rb["panjang"] - ra["panjang_t3"], 1)],
              ["Selisih jumlah tiang terhadap Tahap 3", ra["n"] - ra["n_t3"], None, rb["n"] - ra["n_t3"]]],
             rata=["l", "c", "c", "c"], fmt=[None, "#,##0.0", "#,##0.0", "#,##0.0"], fill_kolom={1: AI, 3: AI}, beku=False)
    lr.kosong()
    lr.bagian("B", "Hasil per cap inti (varian a)")
    rows = []
    for c in ci:
        r = c["r"]
        (nm, rs), _ = penentu(r)
        rows.append([c["id"], " + ".join(t["nama"] for t in c["titik"]), c["zona"].capitalize(), round(r["sumP"], 0), round(r["izin"], 0), c["n0"], r["n"],
                     _fmt_grid(c), round(r["P_layan"], 0), round(r["Pu_maks"], 0), round(r["Pu_min"], 0), round(r["ef"]["eta"], 2), round(r["Qn_kel"], 0),
                     round(r["izin_kel"], 0), c["n_t3"], next(x for x in cib if x["kode"] == c["kode"])["r"]["n"]])
    lr.tabel(["Cap", "Titik beban", "Zona", "Σ Pmax (kN)", "Izin / tiang (kN)", "n layan saja", "n akhir (a)", "Tata letak", "Pmax / tiang (kN)",
              "Pu maks / tiang (kN)", "Pu min / tiang (kN)", "η", "Qn kelompok (kN)", "Izin kelompok (kN)", "n T3", "n (b)"], rows,
             rata=["l", "l", "c"] + ["c"] * 13, fmt=[None, None, None, "#,##0", "#,##0", "0", "0", None, "#,##0", "#,##0", "#,##0", "0.00", "#,##0", "#,##0", "0", "0"],
             fill_kolom={i: AI for i in range(3, 16)}, beku=True)
    lr.catatan("n layan saja = ⌈Σ Pmax / izin⌉. n akhir dipicu cek terbesar di tata letak (lihat tabel penentu di bawah). Pu min negatif = tarik.")
    lr.kosong()
    lr.bagian("C", "Rasio pemakaian per cek, cap inti (tata letak akhir, varian a)")
    rows = []
    for c in ci:
        (nm, v), rs = penentu(c["r"])
        rows.append([c["id"]] + [round(x, 2) for x in rs.values()] + [nm])
    lr.tabel(["Cap", "Layan", "Tekan gempa", "Tarik gempa", "Kelompok", "Rasio terbesar"], rows, rata=["l", "c", "c", "c", "c", "l"],
             fmt=[None, "0.00", "0.00", "0.00", "0.00", None], fill=AI, beku=False)
    lr.kosong()
    lr.bagian("D", "Efisiensi dan seret kelompok cap inti (varian a)")
    rows = []
    for c in ci:
        r, e = c["r"], c["r"]["ef"]
        rows.append([c["id"], round(e["B"], 2), round(e["Z"], 2), round(e["keliling"], 1), round(e["Qblok"], 0), round(e["n_Qult"], 0), round(e["eta"], 2),
                     round(e["eta_tanpa_dasar"], 2), round(e["eta_cl"], 2) if e["eta_cl"] else None, round(r["f_kel"], 2), round(r["Qn_kel"], 0), round(r["Qn_per_tiang"], 0)])
    lr.tabel(["Cap", "B (m)", "Z (m)", "Keliling blok (m)", "Qblok (kN)", "n x Qult (kN)", "η blok", "η blok tanpa dasar", "η Converse-Labarre", "n ekivalen seret",
              "Qn kelompok (kN)", "Qn per tiang (kN)"], rows, rata=["l"] + ["c"] * 11,
             fmt=[None, "0.00", "0.00", "0.0", "#,##0", "#,##0", "0.00", "0.00", "0.00", "0.00", "#,##0", "#,##0"], fill=AI, beku=False)
    lr.kosong()
    lr.bagian("E", "Cek jarak tiang")
    pos = np.array(semua_tiang("a"))
    dn = cKDTree(pos).query(pos, k=2)[0][:, 1]
    lr.tabel(["Butir", "Hasil"], [["Jumlah tiang dicek (utama + utilitas), varian (a)", len(pos)], ["Jarak terdekat (m)", round(float(dn.min()), 3)],
                                  ["Pasangan < 2,4 m", len(cKDTree(pos).query_pairs(S - 1e-9))]], rata=["l", "c"], fmt=[None, "0.000"], fill=AI, beku=False)

    lr.kosong()
    lr.bagian("F", "Kepekaan: Mux dan Muy 100 % + 100 % serentak (tiap cap inti dicari sendiri sebelum penggabungan, tanpa interaksi antar cap inti)")
    kp = kepekaan_penuh()
    rows = [[c["id"], c["r"]["n"], kp["per_cap"][c["kode"]]["n"], f"{kp['per_cap'][c['kode']]['nx']} x {kp['per_cap'][c['kode']]['ny']} (jarak {idn(kp['per_cap'][c['kode']]['sx'], 1)} x {idn(kp['per_cap'][c['kode']]['sy'], 1)} m)",
             round(kp["per_cap"][c["kode"]]["Pu_maks"], 0), round(kp["per_cap"][c["kode"]]["Pu_min"], 0), c["n_t3"]] for c in ci]
    lr.tabel(["Cap", "n (100 % + 30 %)", "n (100 % + 100 %)", "Tata letak 100 % + 100 %", "Pu maks / tiang", "Pu min / tiang", "n T3"], rows, rata=["l"] + ["c"] * 6,
             fmt=[None, "0", "0", None, "#,##0", "#,##0", "0"], fill=AI, beku=False)
    lr.catatan(f"Jumlah inti 100 % + 100 %: {kp['n']} tiang. Pasangan cap yang bentrok (jarak < 2,4 m) bila semuanya berdiri sendiri: "
               + (", ".join(f"{a}-{b}" for a, b in kp["bentrok"]) or "tidak ada") + ".")

    # ---- Cap Kolom
    lk.catatan(f"STATUS: {STATUS}. " + ket)
    lk.kosong()
    rows = []
    for c, cb in zip(ck, ckb):
        r, t = c["r"], c["titik"][0]
        rows.append([t["nama"], c["zona"].capitalize(), round(t["Pmax"], 0), round(t["Pu"], 0), round(r["izin"], 0), r["n"], round(r["P_layan"], 0), round(r["Pu_maks"], 0),
                     round(r["ef"]["eta"], 2), round(r["izin_kel"], 0), c["n_t3"], cb["r"]["n"]])
    h0, a, b = lk.tabel(["Titik", "Zona", "Pmax layan (kN)", "Pu maks (kN)", "Izin / tiang (kN)", "n 6.3 (a)", "Pmax / tiang (kN)", "Pu / tiang (kN)", "η",
                         "Izin kelompok (kN)", "n Tahap 3", "n (b)"], rows, rata=["l", "c"] + ["c"] * 10,
                        fmt=[None, None, "#,##0", "#,##0", "#,##0", "0", "#,##0", "#,##0", "0.00", "#,##0", "0", "0"], fill_kolom={i: AI for i in (5, 6, 7, 8, 9, 11)}, beku=True)
    lk.tabel(["Jumlah", "", "", "", "", "n 6.3 (a)", "", "", "", "", "n Tahap 3", "n (b)"],
             [["Σ (56 cap)", None, None, None, None, f"=SUM({lk.kol(5)}{a}:{lk.kol(5)}{b})", None, None, None, None, f"=SUM({lk.kol(10)}{a}:{lk.kol(10)}{b})",
               f"=SUM({lk.kol(11)}{a}:{lk.kol(11)}{b})"]], rata=["l"] * 12, fmt=[None] * 5 + ["0"] + [None] * 4 + ["0", "0"], beku=False)

    # ---- Varian
    tl_ = temuan_lif()
    lv.catatan(f"STATUS: {STATUS}. " + ket)
    lv.kosong()
    lv.bagian("A", "Temuan 6.2: Pmax layan per tiang selatan > izin")
    lv.tabel(["Butir", "Nilai"], [["INTI-LIF, Σ Pmax layan (kN)", round(tl_["P"], 0)], ["Per tiang, 6 tiang Tahap 3 (kN)", round(tl_["per_tiang"], 0)],
                                  ["Izin selatan 38,45 m (kN)", round(tl_["izin"], 0)], ["Tiang minimum bila INTI-LIF berdiri sendiri", tl_["n_sendiri"]],
                                  ["Izin selatan 40,00 m (kN)", round(tl_["izin_b"], 0)]], rata=["l", "c"], fmt=[None, "#,##0"], fill=AI, beku=False)
    lv.kosong()
    lv.bagian("B", "Cap E (INTI-LIF + 6/B + 6/C) setelah penggabungan")
    lv.tabel(["Varian", "Σ Pmax (kN)", "n layan saja", "n akhir", "Tata letak", "Pmax / tiang (kN)", "Panjang (m)", "Total tiang gedung utama"],
             [["(a) tambah tiang, 38,45 m", round(tl_["a"]["sumP"], 0), tl_["a"]["n0"], tl_["a"]["n"], tl_["a"]["grid"], round(tl_["a"]["P_layan"], 0), tl_["a"]["panjang"], ra["n"]],
              ["(b) selatan 40,00 m", round(tl_["b"]["sumP"], 0), tl_["b"]["n0"], tl_["b"]["n"], tl_["b"]["grid"], round(tl_["b"]["P_layan"], 0), tl_["b"]["panjang"], rb["n"]]],
             rata=["l"] + ["c"] * 7, fmt=[None, "#,##0", "0", "0", None, "#,##0", "0.00", "#,##0"], fill=AI, beku=False)
    lv.kosong()
    lv.bagian("C", "Cap inti: (a) vs (b)")
    rows = []
    for c, cb in zip(ci, cib):
        rows.append([c["id"], c["zona"].capitalize(), c["r"]["n"], cb["r"]["n"], c["r"]["n"] - cb["r"]["n"], round(c["r"]["izin"], 0), round(cb["r"]["izin"], 0),
                     round(c["r"]["n"] * PANJANG - cb["r"]["n"] * (PANJANG + cb["tambah"]), 1)])
    lv.tabel(["Cap", "Zona", "n (a)", "n (b)", "Selisih n", "Izin (a) (kN)", "Izin (b) (kN)", "Panjang total (a) - (b) (m)"], rows, rata=["l"] + ["c"] * 7,
             fmt=[None, None, "0", "0", "0", "#,##0", "#,##0", "#,##0.0"], fill=AI, beku=False)
    lv.kosong()
    lv.bagian("D", "Gedung utama: (a) vs (b)")
    lv.tabel(["Butir", "(a)", "(b)", "Tahap 3"], [["Jumlah tiang", ra["n"], rb["n"], ra["n_t3"]], ["Panjang total (m)", round(ra["panjang"], 1), round(rb["panjang"], 1), round(ra["panjang_t3"], 1)]],
             rata=["l", "c", "c", "c"], fmt=[None, "#,##0.0", "#,##0.0", "#,##0.0"], fill=AI, beku=False)

    # ---- Verifikasi (diisi dari t101 setelah dihitung ulang; nilai awal)
    lf.catatan(f"STATUS: {STATUS}. " + ket)
    lf.kosong()
    r = t101()
    lf.tabel(["Cek", "Hasil", "Toleransi", "Keterangan"],
             [["(a) rumus cap kaku vs matriks kesetimbangan (%)", round(r["selisih"], 6), TOL["rigid"], "semua cap, dua varian, layan + delapan kombinasi 100 % + 30 %"],
              ["(b) Σ Pmax semua cap vs Σ reaksi 77 titik (%)", round(r["dsig"], 6), TOL["sigma"], f"Σ reaksi = {sum(t['Pmax'] for t in titik_beban().values()):,.1f} kN"],
              ["(c) pasangan tiang < 2,4 m", r["pasang"], TOL["jarak"], "gedung utama + utilitas, dua varian"],
              ["(d) η blok terkecil", round(r["eta_min"], 3), "dilaporkan", "NHI-06-089 Pers. 9-18"],
              ["(d) η Converse-Labarre terkecil", round(r["cl_min"], 3), "dilaporkan", "pembanding saja"]], rata=["l", "c", "c", "l"], fill=AI, beku=False)
    la.catatan(ket)
    la.kosong()
    la.tabel(["Acuan", "Status", "Letak"], [list(a) for a in ACUAN], rata=list("lcl"), beku=True)
    ld.catatan(ket)
    ld.kosong()
    ld.tabel(["Butir", "Keterangan"], [list(k) for k in KEPUTUSAN], rata=list("ll"), beku=True)
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar, alamat


def baca_excel(berkas=BERKAS, alamat=None):
    import openpyxl
    wb = openpyxl.load_workbook(berkas, data_only=True)
    ws = wb["Cap Inti"]
    out = {}
    for k, (a, b) in (alamat or {}).items():
        py = next(c for c in rancang("a")[1] if c["kode"] == k)["r"]
        out[k] = ((ws[a].value, ws[b].value), (py["P_layan"], py["Pu_maks"]))
    return out


# ------------------------------------------------------------------ Markdown
def revisi_berat(ck, ci):
    """Paragraf revisi: berat cap dimasukkan (temuan 6.9). Jumlah tiang sebelum (tanpa berat cap) dari konstanta SEBELUM_BERAT."""
    import collections
    k = collections.Counter(c["r"]["n"] for c in ck)
    sb = SEBELUM_BERAT
    nk, ni = sum(c["r"]["n"] for c in ck), sum(c["r"]["n"] for c in ci)
    wr = [c["r"]["W"] / c["r"]["P_layan"] / c["r"]["n"] * 100 for c in ck]
    e = next(c for c in ci if c["kode"] == "E")
    return ("**Berat cap dimasukkan (temuan 6.9, usulan AI, disetujui atas delegasi Defsa 22 Nov 2026).** Kekurangan sistematis untuk semua cap: tanpa berat cap, mis. 4/C utara Pmax 1.407 kN + ±91 kN berat cap melampaui izin 1.443 kN. "
            "W = A h 24 kN/m³ dikurangi apung 9,81 A (11,20 - dasar cap) bila dasar di bawah +11,20 [Asumsi: muka air desain 6.0]; A = telapak (sumbu tiang terluar + 0,8 m); h dari 6.7: cap kolom 2/3/4 tiang 1,0/0,8/0,95 m, "
            "cap inti 1,2 m, Cap E 2,0 m, cap 5-6 tiang 1,2 m [Asumsi]. Kombinasi: layan + W; gempa Pu maks + 1,2 W; Pu min + 0,9 W; W di pusat telapak. "
            "Algoritma jumlah tiang tidak diubah (cek tidak dihapus); cap inti yang tidak lagi muat di antara cap kolom yang bertambah dicari tanpa memperhitungkan cap kolom, lalu telapak yang bertumpang digabung dan dicek ulang (gabung_cap). "
            f"Hasil (a), gedung utama: cap kolom {len(ck)} cap / {nk} tiang (sebelum {sb['n_cap_kolom']} cap / {sb['kolom']}; 2/3/4/6 tiang: {k.get(2, 0)}/{k.get(3, 0)}/{k.get(4, 0)}/{k.get(6, 0)}, sebelum {sb['per_tipe']}), "
            f"cap inti {len(ci)} cap / {ni} tiang (sebelum {sb['n_cap_inti']} cap / {sb['inti']}), total gedung utama {nk + ni} tiang (sebelum {sb['kolom'] + sb['inti']}, {idn((nk + ni) / (sb['kolom'] + sb['inti']) * 100 - 100, 1)} %); "
            f"dengan 68 tiang utilitas (tidak dicek ulang): {nk + ni + N_UTILITAS} tiang (sebelum {sb['kolom'] + sb['inti'] + 68}). Berat cap per tiang cap kolom rata-rata {idn(sum(wr) / len(wr), 1)} % dari P layan maksimum. "
            f"Cap E gabungan ({', '.join(e.get('gabungan', []))}): {e['r']['n']} tiang, {idn(e['ukuran'][0], 1)} × {idn(e['ukuran'][1], 1)} m, W {idn(e['r']['W'], 0)} kN, Pu maks {idn(e['r']['Pu_maks'], 0)} kN, Pu min {idn(e['r']['Pu_min'], 0)} kN. "
            "Varian (b) selatan 40 m: gabungan Cap E tidak menemukan tata letak berberat-cap yang lolos (hanya dilaporkan). Berat cap gedung utilitas (68 tiang, Tahap 3) tidak dicek ulang.\n")


def tulis_md(keluar=MD, r=None):
    r = r or t101()
    ra, rb = ringkas("a"), ringkas("b")
    ck, ci = rancang("a")
    ckb, cib = rancang("b")
    tl_ = temuan_lif()
    s_ = {z: sifat(z) for z in ("SELATAN", "UTARA")}
    L = [f"# 6.3 Jumlah dan tata letak tiang bor Ø800 ({STATUS}, 21 Nov 2026)\n",
         "DATA SIMULASI. Disusun AI atas permintaan Defsa; kunci jawaban tidak dibuka. Rincian di `6.3 Tata Letak Tiang.xlsx` (`skrip/tahap6_tata_letak.py`, "
         "uji `tests/test_tahap6_tata_letak.py`).\n",
         "## Tujuan\n",
         "Menentukan jumlah dan posisi tiang bor Ø800 (panjang 38,45 m, kepala +10,85 m, jarak 2,4 m = 3D) di 56 cap kolom biasa dan enam cap inti hasil "
         "penggabungan 14 cap kolom dengan cap inti (keputusan 6.0), dengan izin per tiang 6.1/6.2, cek beban layan, ultimit gempa (kelompok kaku), tarik, efisiensi dan seret kelompok.\n",
         "## Revisi berat cap (22 Nov 2026)\n",
         revisi_berat(ck, ci),
         "## Data dan acuan\n",
         f"- Beban: 77 titik reaksi 5.6 (6.0): Pmax layan, Pu maks/min, Mux, Muy. Σ Pmax = {idn(sum(t['Pmax'] for t in titik_beban().values()), 0)} kN.",
         f"- Izin per tiang (6.2, disetujui): selatan {idn(s_['SELATAN']['izin'], 0)} kN, utara {idn(s_['UTARA']['izin'], 0)} kN; tengah memakai utara [Asumsi: konservatif; 6.2 tidak menghitung tengah].",
         "- Tahanan terfaktor GEC10 Tabel 8-4 (6.1): tekan statis / gempa dan tarik gempa selatan "
         f"{idn(s_['SELATAN']['tekan_st'], 0)} / {idn(s_['SELATAN']['tekan_gm'], 0)} / {idn(s_['SELATAN']['tarik_gm'], 0)} kN; utara {idn(s_['UTARA']['tekan_st'], 0)} / "
         f"{idn(s_['UTARA']['tekan_gm'], 0)} / {idn(s_['UTARA']['tarik_gm'], 0)} kN.",
         "- Cap kolom: n = max(2, ⌈Pmax / izin⌉) dengan pola Tahap 3 (`tahap3_bim.pola`), naik bila cek ultimit gagal. Cap inti: grid persegi panjang (jarak ≥ 2,4 m; "
         "pilihan 2,4 / 3,6 / 4,8 m), n terkecil yang lolos semua cek dan tidak bentrok (< 2,4 m) dengan tiang lain; semua titik beban 0,4 m di dalam tepi cap (tepi 0,8 m dari as tiang).",
         "- Beban tiang cap kaku: Pi = ΣP/n + (Mx + Mux)(yi - yc)/Σ(y - yc)² + (My + Muy)(xi - xc)/Σ(x - xc)², Mx dan My dari eksentrisitas beban terhadap titik berat grup; "
         "delapan kombinasi (100 % + 30 % dengan tanda bolak-balik, SNI 1726:2019 Pasal 7.5.3 a hal. 79 PDF); ultimit memakai Pu maks (konservatif, 5.6 tidak memberi Pu per kombinasi gempa); Tu diabaikan [Asumsi]; momen layan tidak tersedia (keterbatasan).",
         "- Efisiensi dan blok: NHI-06-089 9.6.1.1 hal. 188 (jarak ≥ 3D, tanah tanpa kohesi: jumlah tiang), Pers. 9-18/9-19 hal. 191-192 (blok = keliling x selimut U5-U7 + luas x qb), "
         "seret kelompok dari keliling blok 9.8 hal. 199. Converse-Labarre [Literatur, belum ada di acuan/] hanya pembanding.\n",
         "## Hasil per cap inti\n",
         "| Cap | Titik beban | Zona | Σ Pmax (kN) | Izin (kN) | n layan | n akhir | Tata letak | Pmax/tiang | Pu maks/tiang | Pu min/tiang | η | Qn kel. | Izin kel. | n T3 | n (b) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c, cb in zip(ci, cib):
        e = c["r"]
        L.append(f"| {c['id']} | {' + '.join(t['nama'] for t in c['titik'])} | {c['zona'].capitalize()} | {idn(e['sumP'], 0)} | {idn(e['izin'], 0)} | {c['n0']} | {e['n']} | "
                 f"{_fmt_grid(c)} | {idn(e['P_layan'], 0)} | {idn(e['Pu_maks'], 0)} | {idn(e['Pu_min'], 0)} | {idn(e['ef']['eta'], 2)} | {idn(e['Qn_kel'], 0)} | "
                 f"{idn(e['izin_kel'], 0)} | {c['n_t3']} | {cb['r']['n']} |")
    pen = {c["id"]: penentu(c["r"])[0][0] for c in ci}
    L.append("\nCek dengan rasio pemakaian terbesar: " + "; ".join(f"{k}: {v}" for k, v in pen.items()) + ". Pu min negatif = tarik. Qn kel. = seret kelompok = min(n x Qn tunggal, keliling blok x seret satuan).\n")
    ef = [c["r"]["ef"] for c in ci]
    L.append(f"Efisiensi blok = {idn(min(e['eta'] for e in ef), 2)} (tidak menentukan: selimut + dasar blok ≥ n x Qult); tanpa dasar blok η "
             f"{idn(min(e['eta_tanpa_dasar'] for e in ef), 2)}-{idn(max(e['eta_tanpa_dasar'] for e in ef), 2)}; Converse-Labarre (pembanding) "
             f"{idn(min(e['eta_cl'] for e in ef if e['eta_cl']), 2)}-{idn(max(e['eta_cl'] for e in ef if e['eta_cl']), 2)}. Cap kolom biasa: lihat lembar Cap Kolom.\n")
    kp = kepekaan_penuh()
    L.append("Kepekaan Mux, Muy 100 % + 100 % serentak (arahan tugas awal): tiap cap inti sendiri butuh " + ", ".join(
        f"{c['id'][-1]} {kp['per_cap'][c['kode']]['n']}" for c in ci) + f" = {kp['n']} tiang (vs {ra['n_inti']} pada 100 % + 30 %, {ra['n_t3_inti']} Tahap 3); "
        "pasangan cap yang bentrok bila berdiri sendiri: " + (", ".join(f"{a}-{b}" for a, b in kp["bentrok"]) or "tidak ada") + ".\n")
    L.append("## Ringkasan jumlah tiang\n")
    L.append("| Kelompok | 6.3 (a) | Tahap 3 | 6.3 (b) selatan 40 m |\n|---|---|---|---|")
    L.append(f"| Cap kolom biasa (56) | {ra['n_kolom']} | {ra['n_t3_kolom']} | {rb['n_kolom']} |")
    L.append(f"| {len(ci)} cap inti gabungan | {ra['n_inti']} | {ra['n_t3_inti']} | {rb['n_inti']} |")
    L.append(f"| Gedung utama | {ra['n']} | {ra['n_t3']} | {rb['n']} |")
    L.append(f"| Gedung utilitas + parkir (tidak berubah) | {N_UTILITAS} | {N_UTILITAS} | {N_UTILITAS} |")
    L.append(f"| Total | {ra['total']} | {ra['n_t3'] + N_UTILITAS} | {rb['total']} |")
    L.append(f"\nPanjang total gedung utama (untuk Tahap 8): (a) {idn(ra['panjang'], 1)} m, Tahap 3 {idn(ra['panjang_t3'], 1)} m (selisih {idn(ra['panjang'] - ra['panjang_t3'], 1)} m, "
             f"{ra['n'] - ra['n_t3']:+d} tiang); (b) {idn(rb['panjang'], 1)} m (selisih {idn(rb['panjang'] - ra['panjang_t3'], 1)} m, {rb['n'] - ra['n_t3']:+d} tiang).\n")
    L.append("## Temuan 1.710 kN dengan dua pilihan\n")
    a, b = tl_["a"], tl_["b"]
    L.append(f"6.2 menemukan Pmax layan per tiang selatan {idn(tl_['per_tiang'], 0)} kN (INTI-LIF {idn(tl_['P'], 0)} kN / 6 tiang) > izin {idn(tl_['izin'], 0)} kN. "
             f"INTI-LIF sendiri butuh ≥ {tl_['n_sendiri']} tiang. Setelah penggabungan ke Cap E (INTI-LIF + 6/B + 6/C, Σ Pmax {idn(a['sumP'], 0)} kN):\n")
    L.append("| Pilihan | n layan saja | n akhir | Tata letak | Pmax/tiang | Panjang | Total tiang gedung utama |\n|---|---|---|---|---|---|---|")
    L.append(f"| (a) tambah tiang, 38,45 m (izin {idn(tl_['izin'], 0)}) | {a['n0']} | {a['n']} | {a['grid']} | {idn(a['P_layan'], 0)} | {idn(a['panjang'], 2)} m | {ra['n']} |")
    L.append(f"| (b) selatan diperpanjang 40,00 m (izin {idn(tl_['izin_b'], 0)}) | {b['n0']} | {b['n']} | {b['grid']} | {idn(b['P_layan'], 0)} | {idn(b['panjang'], 2)} m | {rb['n']} |")
    L.append("\nKeduanya dihitung penuh (semua cap); (b) hanya untuk cap seluruhnya di zona selatan (+1,55 m). Pilihan tidak memicu hitungan baru. "
             f"(b) menurunkan n layan saja (Cap E {a['n0']} ke {b['n0']}) tetapi jumlah akhir sama ({ra['n']} vs {rb['n']}): momen gempa inti (tekan dan tarik) yang menentukan, bukan layan; "
             f"(b) menambah panjang {idn(rb['panjang'] - ra['panjang'], 1)} m. Perpanjangan hanya berguna bila 5.6 memberi beban gempa inti yang lebih ringan.\n")
    L.append("## Verifikasi T-101\n")
    L.append(f"Toleransi ditetapkan dulu: (a) rumus cap kaku vs matriks kesetimbangan ≤ 0,5 %; (b) Σ Pmax semua cap vs Σ reaksi ≤ 0,1 %; (c) 0 pasangan < 2,4 m; "
             f"(d) η blok vs Converse-Labarre dilaporkan. Hasil: (a) {idn(r['selisih'], 4)} %" + (f" (Excel hidup vs skrip {idn(r['dex'], 4)} %)" if r["dex"] is not None else "") +
             f"; (b) {idn(r['dsig'], 4)} %; (c) {r['pasang']} pasangan; (d) η blok terkecil {idn(r['eta_min'], 2)}, Converse-Labarre terkecil {idn(r['cl_min'], 2)}. "
             f"Lolos: {'ya' if r['lolos'] else 'TIDAK'}.\n")
    L.append("## Hal yang perlu diputuskan Defsa\n")
    for i, k in enumerate(KEPUTUSAN, 1):
        L.append(f"{i}. **{k[0]}**: {k[1]}")
    L.append(f"\nStatus: {STATUS}.\n")
    Path(keluar).write_text("\n".join(L), encoding="utf-8")
    return keluar


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from format_dokumen import hitung_ulang_excel
    berkas, alamat = buat_excel()
    print(berkas, hitung_ulang_excel(berkas))
    ex = baca_excel(berkas, alamat)
    r = t101(ex=ex)
    print(r)
    print(catat_t101(r))
    print(tulis_md(r=r))
    for v in "ab":
        print(v, ringkas(v))
    print(temuan_lif())


if __name__ == "__main__" and "--cek" not in sys.argv:
    main()
