"""Laporan antara LA.3: stabilitas tebing sungai awal (P-1, P-2, P-3) dan rencana saluran pembuang ke sungai.

Metode irisan, dua cara: Bishop disederhanakan dan Fellenius (irisan biasa), keseimbangan momen umum terhadap
pusat lingkaran sehingga juga berlaku untuk lingkaran terpotong bidang licin lama (P-2). Pencarian lingkaran
grid pusat × elevasi singgung, lalu diperhalus di sekitar minimum.

Sumber kriteria (acuan/privat/SNI-8460-2017):
- FK lereng tanah statis: SNI 8460:2017 Pasal 7.5.5 Tabel 25 hal. 134 (1,25 / 1,5 / 2,0).
- Beban permukaan 10 kPa di atas lereng: Pasal 7.5.1 hal. 132.
- Kondisi perancangan (akhir konstruksi, rembesan tunak, surut cepat, gempa): Pasal 7.6 hal. 135.
- Pseudo-statik: FK > 1,1 (Pasal 7.5.1.1 hal. 133); kh = 0,5 PGA permukaan dengan faktor amplifikasi situs
  (Pasal 12.2.7 hal. 278-279, yang menulis FK > 1,0; dipakai yang lebih ketat 1,1).
Data: skrip/tahap2_kimia_tebing_gudang.py (penampang, bor tebing), parameter desain langkah 2.4, amax langkah 2.6,
sempadan dan zona labil langkah 3.2, peil dan retensi langkah 3.3, kolam retensi 3.4.
Keluaran: '03 Desain Konsep/LA.3 Stabilitas Tebing.xlsx' dan gambar GK-11 (CADCraft, kop KOP_A3).
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 20 Nov 2026 (LA.3).
Jalankan:  .venv\\Scripts\\python.exe skrip\\la_tebing.py
"""
import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np

import tahap2_air_tanah as at
import tahap2_kimia_tebing_gudang as kt
import tahap2_likuifaksi as lq
import tahap2_penurunan_urugan as pu
import tahap3_peil as pl
import tahap3_tapak as tp

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "03 Desain Konsep"
BERKAS = KELUAR / "LA.3 Stabilitas Tebing.xlsx"
PDF = KELUAR / "LA.3 Gambar Stabilitas Tebing.pdf"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
STATUS = "disetujui Defsa 20 Nov 2026 (LA.3)"
LABEL_AI = f"DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."
GW = 9.81

# ------------------------------------------------------------------ kriteria (SNI 8460:2017)
FK_IZIN = {
    "statis": (1.5, "SNI 8460:2017 Pasal 7.5.5 Tabel 25 hal. 134: biaya perbaikan > biaya desain konservatif, "
                    "ketidakpastian rendah (bor di tiap potongan, bidang licin teridentifikasi)"),
    "surut": (1.25, "SNI 8460:2017 Tabel 25 hal. 134 baris 1, ketidakpastian rendah [Asumsi: surut cepat kondisi "
                    "sementara; FK khusus surut cepat acuan belum ada di acuan/]"),
    "gempa": (1.1, "SNI 8460:2017 Pasal 7.5.1.1 hal. 133 (FK > 1,1); Pasal 12.2.7 hal. 279 menulis FK > 1,0, "
                   "dipakai yang lebih ketat"),
}
FK_KETIDAKPASTIAN_TINGGI = 2.0  # Tabel 25 kolom tinggi (bila bidang licin ternyata menerus ke dalam persil)
Q_PERMUKAAN = 10.0  # kPa, SNI 8460 Pasal 7.5.1 hal. 132
KH = 0.5 * lq.AMAX  # SNI 8460 Pasal 12.2.7 hal. 279; amax = PGAM = FPGA PGA (langkah 2.6, SNI 1726 Pers. 15)

# ------------------------------------------------------------------ muka air (datum lokal BM-1 +10,000)
MA_NORMAL = float(np.mean([r[1] for r in at.SUNGAI_BULANAN]))  # rata-rata 12 bulan TOR Lampiran A = +6,37
MA_RENDAH = 4.0  # TOR 4.3 dan Lampiran A (Sep), muka rendah musiman
MA_Q50 = pl.peil_usulan()["q50"]  # +11,85 (langkah 3.3)
SELISIH_PASIR = at.SELISIH_SURUT  # 0,9 m: tinggi tekan pasir di atas sungai (langkah 2.3)
POMPA_MULAI = 9.70  # muka sungai di atas ini outlet gravitasi terhalang (Data Hidrologi, lembar Lama Genangan)

# ------------------------------------------------------------------ parameter tanah desain (langkah 2.4)
SU4_A, SU4_B = 5.23, 1.09  # U4: su = a_k + b z (a_k = rata - 0,5 sd = 6,33 - 1,10), z di bawah muka tanah setempat
SU_LICIN = 4.4  # BT-2 UD-2 dari bidang licin [Uji sendiri, langkah 2.7]


@dataclass(frozen=True)
class Bahan:
    kode: str
    gamma: float
    su: float = 0.0  # kPa (tegangan total, φ = 0)
    phi: float = 0.0  # derajat (tegangan efektif, c' = 0)
    su_z: bool = False  # su = SU4_A + SU4_B z
    sumber: str = ""


BAHAN = {
    "U1": Bahan("U1", 17.0, phi=28.0, sumber="γ langkah 2.4 [Asumsi]; φ' 28° [Asumsi: lanau kepasiran urug, tidak diuji]"),
    "U2": Bahan("U2", 17.8, su=35.0, sumber="langkah 2.4 [Uji sendiri] UU n = 2"),
    "U4": Bahan("U4", 15.2, su_z=True, sumber="langkah 2.4: su = 5,23 + 1,09 z [Uji sendiri] UU n = 23"),
    "LICIN": Bahan("LICIN", 15.2, su=SU_LICIN, sumber="BT-2 UD-2 su 4,4 kPa [Uji sendiri] langkah 2.7"),
    "LONGSOR": Bahan("LONGSOR", 15.2, su=SU_LICIN,
                     sumber="BT-2K massa longsoran N 1-2 [Asumsi: su sama dengan bidang licin]"),
    "U5": Bahan("U5", 19.0, phi=33.0, sumber="langkah 2.4 φ' 33° [Korelasi GEC 5 Pers. 7.23]"),
    "U6": Bahan("U6", 19.1, su=85.0, sumber="langkah 2.4 [Uji sendiri] UU n = 5"),
    "BERM": Bahan("BERM", 20.0, phi=40.0, sumber="[Asumsi: bronjong/batu kosong terisi, γ 20, φ' 40°]"),
    "AIR": Bahan("AIR", GW, sumber="air sungai di atas muka tanah (bahan tanpa kuat geser)"),
}

# batas lapisan dari bor kepala tebing (elevasi bawah tiap lapis), langkah 2.7
LAPIS = {
    "P-1": [("U2", 8.61), ("U4", 1.32), ("U5", -9.16), ("U6", -99.0)],  # BT-1 (U1 0,32 m digabung ke U2)
    "P-2": [("U2", 8.48), ("U4", 1.01), ("U5", -9.18), ("U6", -99.0)],  # BT-2 (U1 0,29 m digabung ke U2)
    "P-3": [("U1", 9.18), ("U2", 7.61), ("U4", 0.48), ("U5", -8.51), ("U6", -99.0)],  # BT-3
}
X_LOKAL = {"P-1": 40.0, "P-2": 90.0, "P-3": 125.0}
BOR = {"P-1": ("BT-1", "BT-1K"), "P-2": ("BT-2", "BT-2K"), "P-3": ("BT-3", None)}

# bidang licin lama P-2 (jarak dari batas lahan, positif ke sungai): BT-2 jarak 4,5 di +5,18-5,68 (tengah +5,43);
# BT-2K jarak 15 dasar massa longsoran +3,76; muncul di kaki sekitar jarak 21,5 (permukaan +4,0)
LICIN_TEBAL = 0.5
LICIN_UJUNG_DARAT = -10.0  # [Asumsi: tidak ada bor di persil; diperpanjang datar 14,5 m ke darat dari BT-2]
LICIN_TITIK = [(LICIN_UJUNG_DARAT, 5.43), (4.5, 5.43), (15.0, 3.76), (21.5, 4.0)]
LONGSOR_DARI = 8.9  # massa longsoran di atas bidang licin mulai kaki lereng curam (P-2)
GESER_P2 = -2.0  # puncak P-2 Feb 2027 4,5 m (surat sempadan STA 0+050) vs survei Des 2026 6,5 m


# ------------------------------------------------------------------ geometri potongan
@dataclass
class Potongan:
    nama: str
    xs: np.ndarray  # jarak dari batas lahan (m), positif ke sungai
    zs: np.ndarray  # elevasi muka tanah / dasar sungai
    lapis: list
    licin: bool = False
    geser: float = 0.0
    licin_darat: float = LICIN_UJUNG_DARAT
    beban: list = field(default_factory=list)  # [(x0, x1, q kPa, uraian)], x0 < x1
    k_su: float = 1.0  # faktor kuat geser lempung (analisis balik)
    berm: tuple = ()  # titik (x, z) puncak berm/bronjong kaki di atas muka tanah asli

    def tanah0(self, x):
        return np.interp(x, self.xs, self.zs)

    def tanah(self, x):
        z = np.interp(x, self.xs, self.zs)
        if self.berm:
            bx, bz = zip(*self.berm)
            zb = np.interp(x, bx, bz, left=-99.0, right=-99.0)
            z = np.maximum(z, zb)
        return z

    def y_licin(self, x):
        px = [p[0] + (self.geser if p[0] > LICIN_UJUNG_DARAT else 0.0) for p in LICIN_TITIK]
        px[0] = self.licin_darat
        return np.interp(x, px, [p[1] for p in LICIN_TITIK])

    def licin_rentang(self):
        return self.licin_darat, LICIN_TITIK[-1][0] + self.geser

    def bahan(self, x, y):
        """Kode bahan di titik (x, y) di bawah muka tanah."""
        if self.berm and y > float(self.tanah0(x)):
            return "BERM"
        if self.licin:
            a, b = self.licin_rentang()
            if a <= x <= b:
                yl = float(self.y_licin(x))
                if abs(y - yl) <= LICIN_TEBAL / 2:
                    return "LICIN"
                if y > yl and x >= LONGSOR_DARI + self.geser:
                    return "LONGSOR"
        for kode, bawah in self.lapis:
            if y >= bawah:
                return kode
        return self.lapis[-1][0]

    def q(self, x):
        return sum(qq for x0, x1, qq, _ in self.beban if x0 <= x < x1)


LANDAI_MIRING = 2.0  # 1V : 2H


def _xz(nama, g, x_darat):
    p = kt.penampang(nama)
    xs = np.array([t["jarak"] for t in p], float)
    zs = np.array([t["elev_kor"] for t in p], float)
    if g:
        xs = np.where(xs > -10, xs + g, xs)
        keep = np.r_[True, np.diff(xs) > 0]
        xs, zs = xs[keep], zs[keep]
    return np.r_[x_darat, xs], np.r_[zs[0], zs]


@lru_cache(maxsize=None)
def potongan(nama, beban=True, geser=None, licin_darat=LICIN_UJUNG_DARAT, x_darat=-45.0, k_su=1.0, berm=False,
             urug_labil=1.0, landai=False):
    p = kt.penampang(nama)
    xs = np.array([t["jarak"] for t in p], float)
    zs = np.array([t["elev_kor"] for t in p], float)
    g = (GESER_P2 if nama == "P-2" else 0.0) if geser is None else geser
    if g:
        zs_d = zs.copy()
        xs = np.where(xs > -10, xs + g, xs)  # tebing (bukan dataran) digeser ke darat
        keep = np.r_[True, np.diff(xs) > 0]
        xs, zs = xs[keep], zs_d[keep]
    xs = np.r_[x_darat, xs]
    zs = np.r_[zs[0], zs]
    if landai:  # lereng atas dipotong 1V : LANDAI_MIRING H dari kaki lereng curam (pengurangan beban)
        xk = float(next(x for x, z in zip(xs, zs) if x > -5 and z <= BERM_PUNCAK + 1.2))
        zk = float(np.interp(xk, xs, zs))
        xs = np.unique(np.r_[xs, np.arange(xk - 12, xk, 0.5)])
        zs = np.interp(xs, *_xz(nama, g, x_darat))
        zs = np.where(xs < xk, np.minimum(zs, zk + (xk - xs) / LANDAI_MIRING), zs)
    pot = Potongan(nama, np.asarray(xs, float), np.asarray(zs, float), LAPIS[nama], licin=(nama == "P-2"), geser=g, licin_darat=licin_darat, k_su=k_su)
    if berm:
        pot.berm = berm_kaki(pot)
    if beban:
        pot.beban = beban_permukaan(nama, pot, urug_labil=urug_labil)
    return pot


def beban_permukaan(nama, pot, urug_labil=1.0, halaman=None):
    """Beban di persil (x < 0): ruang sempadan tanpa beban (surat sempadan butir 3); jalur penyangga/zona labil
    urugan ≤ 1,0 m (butir 4) + 10 kPa; di utaranya urugan halaman ke +12,05 + 10 kPa (SNI 8460 Pasal 7.5.1)."""
    xl = X_LOKAL[nama]
    g = tp.kedalaman_sempadan(xl)
    h = pl.peil_usulan()["halaman"] if halaman is None else halaman
    z0 = float(pot.tanah(-g - 5))
    labil = tp.LX - tp.LABIL_STA[1] <= xl <= tp.LX - tp.LABIL_STA[0]
    gu = pu.GAMMA_URUG
    if labil:
        return [(-(g + tp.LABIL_LEBAR), -g, gu * urug_labil + Q_PERMUKAAN,
                 f"jalur penyangga: urugan {urug_labil:.1f} m × {gu:.0f} + {Q_PERMUKAAN:.0f}"),
                (pot.xs[0], -(g + tp.LABIL_LEBAR), gu * max(0.0, h - z0) + Q_PERMUKAAN,
                 f"halaman +{h:.2f}: urugan {h - z0:.2f} m × {gu:.0f} + {Q_PERMUKAAN:.0f}")]
    return [(pot.xs[0], -g, gu * max(0.0, h - z0) + Q_PERMUKAAN,
             f"halaman +{h:.2f}: urugan {h - z0:.2f} m × {gu:.0f} + {Q_PERMUKAAN:.0f}")]


BERM_PUNCAK = 6.5  # [Asumsi] puncak berm kaki ≈ muka air normal +6,37, bisa dikerjakan saat kemarau
BERM_LEBAR = 8.0  # m, lebar puncak dari kaki lereng curam
BERM_MIRING = 2.0  # 1V : 2H


def berm_kaki(pot):
    """Berm penahan kaki (bronjong/batu) mulai kaki lereng curam (muka tanah = puncak berm) ke arah sungai."""
    x0 = float(next(x for x, z in zip(pot.xs, pot.zs) if x > -5 and z <= BERM_PUNCAK + 1.0))
    x1 = x0 + BERM_LEBAR
    xx = np.arange(x1, x1 + 40, 0.1)
    turun = BERM_PUNCAK - (xx - x1) / BERM_MIRING
    xk = float(xx[np.argmax(turun <= pot.tanah0(xx))])
    return ((x0 - 1.0, BERM_PUNCAK), (x1, BERM_PUNCAK), (xk, BERM_PUNCAK - (xk - x1) / BERM_MIRING))


def luas_berm(pot):
    xx = np.arange(pot.berm[0][0], pot.berm[-1][0], 0.05)
    return float(np.sum(np.clip(pot.tanah(xx) - pot.tanah0(xx), 0, None)) * 0.05)


# ------------------------------------------------------------------ kondisi
@dataclass(frozen=True)
class Kondisi:
    kode: str
    nama: str
    ma_sungai: float
    h_pasir: float
    kh: float = 0.0
    mat: float = 0.7  # muka air tanah dangkal di bawah muka tanah (langkah 2.4); None = kering


def kondisi():
    return [
        Kondisi("statis", f"(a) Statis, muka air normal +{MA_NORMAL:.2f}", MA_NORMAL, MA_NORMAL + SELISIH_PASIR),
        Kondisi("surut", f"(b) Surut cepat Q50 +{MA_Q50:.2f} → +{MA_RENDAH:.2f}", MA_RENDAH,
                MA_NORMAL + SELISIH_PASIR),
        Kondisi("gempa", f"(c) Gempa pseudo-statik kh {KH:.3f}, muka air normal", MA_NORMAL,
                MA_NORMAL + SELISIH_PASIR, KH),
    ]


def x_pasir(pot):
    """Jarak tempat pasir U5 tersingkap di dasar sungai (muka tanah turun di bawah atas U5)."""
    atas = dict(pot.lapis)["U4"]
    return float(next(x for x, z in zip(pot.xs, pot.zs) if x > 0 and z <= atas))


def h_pasir(pot, kon, x):
    """Tinggi tekan pasir U5: kon.h_pasir di bawah persil (x ≤ 0), turun linear ke muka sungai di tempat pasir
    tersingkap di dasar sungai (pasir terhubung langsung ke sungai, langkah 2.3)."""
    xp = x_pasir(pot)
    f = float(np.clip((xp - x) / xp, 0.0, 1.0))
    return kon.ma_sungai + (kon.h_pasir - kon.ma_sungai) * f


# ------------------------------------------------------------------ irisan dan FK
@dataclass
class Bidang:
    xo: float
    yo: float
    r: float
    potong: bool = False  # True: lingkaran dipotong bidang licin (mengikuti bidang licin di bawahnya)


DX_R, DY_R, Y_R0, Y_R1 = 0.1, 0.02, -25.0, 15.0
_RASTER = {}


def _raster(pot):
    """Raster γ per kolom (x tiap 0,1 m, y tiap 0,02 m) dengan jumlah kumulatif γ dy dan γ y dy dari bawah."""
    kunci = (pot.nama, pot.geser, pot.licin, pot.licin_darat, pot.berm, tuple(pot.xs), tuple(pot.zs),
             tuple(pot.lapis))
    if kunci in _RASTER:
        pot._r = _RASTER[kunci]
    if getattr(pot, "_r", None) is None:
        gx = np.arange(pot.xs[0], pot.xs[-1] + DX_R, DX_R)
        gy = np.arange(Y_R0, Y_R1 + DY_R / 2, DY_R)
        yc = gy[:-1] + DY_R / 2
        G = np.zeros((len(gx), len(yc)))
        for i, x in enumerate(gx):
            G[i] = [BAHAN[pot.bahan(x, y)].gamma for y in yc]
        C0 = np.concatenate([np.zeros((len(gx), 1)), np.cumsum(G * DY_R, axis=1)], axis=1)
        C1 = np.concatenate([np.zeros((len(gx), 1)), np.cumsum(G * yc * DY_R, axis=1)], axis=1)
        pot._r = (gx, gy, C0, C1)
        if not pot.nama.startswith("UJI"):
            _RASTER[kunci] = pot._r
    return pot._r


def _berat(pot, xm, ym, tg, tw):
    """Berat per lebar satuan (tanah + air di atas muka tanah), berat tanah saja, dan titik berat y tanah."""
    gx, gy, C0, C1 = _raster(pot)
    i = np.clip(np.rint((xm - gx[0]) / DX_R).astype(int), 0, len(gx) - 1)

    def kum(C, y):
        return np.array([np.interp(yy, gy, C[ii]) for ii, yy in zip(i, y)])

    lo, hi = ym, np.maximum(ym, tg)
    ws = kum(C0, hi) - kum(C0, lo)
    my = kum(C1, hi) - kum(C1, lo)
    air = GW * (tw - np.maximum(tg, ym))
    ycg = np.where(ws > 0, my / np.where(ws > 0, ws, 1.0), tw)
    return ws + air, ws, ycg


def _iris(pot, kon, bid, n=60):
    """Kembalikan array irisan atau None bila lingkaran tidak memotong permukaan dengan wajar."""
    xx = np.linspace(pot.xs[0], pot.xs[-1], 1601)
    top = np.maximum(pot.tanah(xx), kon.ma_sungai)
    dy = bid.r ** 2 - (xx - bid.xo) ** 2
    yc = np.where(dy > 0, bid.yo - np.sqrt(np.clip(dy, 0, None)), np.inf)
    dalam = yc < top
    if not dalam.any():
        return None
    idx = np.flatnonzero(dalam)
    if idx[0] == 0 or idx[-1] == len(xx) - 1 or np.any(np.diff(idx) != 1):
        return None
    x1, x2 = xx[idx[0]], xx[idx[-1]]
    if x2 - x1 < 3.0:
        return None
    b = (x2 - x1) / n
    xm = x1 + b * (np.arange(n) + 0.5)
    xa, xb = xm - b / 2, xm + b / 2

    def dasar(x):
        y = bid.yo - np.sqrt(np.clip(bid.r ** 2 - (x - bid.xo) ** 2, 0, None))
        if bid.potong and pot.licin:
            a, c = pot.licin_rentang()
            yl = pot.y_licin(x)
            y = np.where((x >= a) & (x <= c), np.maximum(y, yl), y)
        return y

    ya, yb_, ym = dasar(xa), dasar(xb), dasar(xm)
    tg = pot.tanah(xm)
    tw = np.maximum(tg, kon.ma_sungai)
    if np.max(tg - ym) < 1.0:  # bidang terlalu dangkal (< 1 m di bawah muka tanah)
        return None
    if np.max(ym) > bid.yo - 1.0:  # dasar irisan harus di bawah pusat
        return None
    if np.max(np.abs(np.diff(ym))) > max(1.0, 2.0 * b):  # bidang terpotong harus menerus (tanpa loncatan)
        return None
    if np.any(tw <= ym):
        return None
    W, Wm, ycg = _berat(pot, xm, ym, tg, tw)
    W, Wm = W * b, Wm * b
    kode = ["AIR" if ym[i] > tg[i] else pot.bahan(xm[i], ym[i] + 1e-6) for i in range(n)]
    Q = np.array([pot.q(x) * b if tg_ >= kon.ma_sungai else 0.0 for x, tg_ in zip(xm, tg)])
    th = np.arctan2(yb_ - ya, b)  # arah dasar ke sungai (+x)
    beta = b / np.cos(th)
    kl, kw = pot.k_su if isinstance(pot.k_su, tuple) else (pot.k_su, pot.k_su)
    u = np.zeros(n)
    c = np.zeros(n)
    tphi = np.zeros(n)
    for i, k in enumerate(kode):
        m = BAHAN[k]
        if m.phi > 0:
            if kon.mat is None:
                hp = -1e9
            elif k == "U5":
                hp = h_pasir(pot, kon, xm[i])
            else:
                hp = max(kon.ma_sungai, float(pot.tanah(xm[i])) - kon.mat)
            u[i] = GW * max(0.0, hp - ym[i])
            tphi[i] = math.tan(math.radians(m.phi))
            c[i] = m.su  # c' (0 untuk semua bahan proyek; dipakai bahan uji)
        elif m.su_z:
            c[i] = (SU4_A + SU4_B * max(0.0, tg[i] - ym[i])) * kl
        else:
            c[i] = m.su * {"U6": 1.0, "LICIN": kw, "LONGSOR": kw}.get(k, kl)
    return dict(xm=xm, ym=ym, b=b, W=W, Wm=Wm, ycg=ycg, Q=Q, th=th, beta=beta, u=u, c=c, tphi=tphi, kode=kode,
                x1=x1, x2=x2, tg=tg)


def _fk(s, bid, kh, metode, tol=1e-4):
    return _fk_den(s, bid, kh, metode, tol)[0]


def _fk_den(s, bid, kh, metode, tol=1e-4):
    """(FK, momen dorong) terhadap pusat lingkaran. Momen dorong = W, Q, kh W, dan komponen gaya normal yang tidak
    lewat pusat (bidang terpotong); FK = Σ S_tersedia × lengan / momen dorong."""
    xm, ym, th, beta = s["xm"], s["ym"], s["th"], s["beta"]
    W, Q, Wm, u, c, tphi = s["W"], s["Q"], s["Wm"], s["u"], s["c"], s["tphi"]
    rx, ry = xm - bid.xo, ym - bid.yo
    tx, ty = np.cos(th), np.sin(th)
    nx, ny = -np.sin(th), np.cos(th)
    cr_t = rx * ty - ry * tx
    cr_n = rx * ny - ry * nx
    m_drive = np.sum((W + Q) * (bid.xo - xm)) + np.sum(kh * Wm * (bid.yo - s["ycg"]))
    if metode == "fellenius":
        N = (W + Q) * np.cos(th) + kh * Wm * np.sin(th)
        Sa = c * beta + np.clip(N - u * beta, 0, None) * tphi
        den = m_drive + np.sum(N * cr_n)
        return (float(np.sum(Sa * cr_t) / den), float(den)) if den > 0 else (np.inf, float(den))
    F = 1.0
    for _ in range(100):
        F = max(F, 0.05)
        ma = np.cos(th) - tphi * np.sin(th) / F
        if np.any(ma < 0.2):
            return np.nan, np.nan  # Bishop tidak stabil secara numerik (mα < 0,2)
        N = (W + Q + (c * beta - u * beta * tphi) * np.sin(th) / F) / ma
        Sa = c * beta + np.clip(N - u * beta, 0, None) * tphi
        den = m_drive + np.sum(N * cr_n)
        if den <= 0:
            return np.inf, float(den)
        Fb = float(np.sum(Sa * cr_t) / den)
        if abs(Fb - F) < tol:
            return Fb, float(den)
        F = Fb
    return F, float(den)


def fk(pot, kon, bid, metode="bishop"):
    s = _iris(pot, kon, bid)
    if s is None:
        return np.inf, None
    return _fk(s, bid, kon.kh, metode), s


def _kandidat(pot, kon, xo_r, yo_r, yt_r):
    for xo in xo_r:
        for yo in yo_r:
            for yt in yt_r:
                r = yo - yt
                if r <= 1.0:
                    continue
                yield Bidang(float(xo), float(yo), float(r), False)
                if pot.licin and yt < 5.4:
                    yield Bidang(float(xo), float(yo), float(r), True)


def cari(pot, kon, metode="bishop", x_min=None, kasar=True):
    """FK minimum: grid kasar pusat (x, y) × elevasi singgung, lalu dua kali diperhalus.
    x_min: hanya bidang yang ujung darat-nya ≤ x_min (bidang menjangkau ke dalam persil)."""
    best = (np.inf, None, None)

    def uji(c):
        nonlocal best
        f, s = fk(pot, kon, c, metode)
        if s is None or not np.isfinite(f):
            return
        if x_min is not None and s["x1"] > x_min:
            return
        if f < best[0]:
            best = (f, c, s)

    for c in _kandidat(pot, kon, np.arange(-20, 46, 3.0), np.arange(9, 46, 3.0), np.arange(-9, 8.5, 1.5)):
        uji(c)
    for d in (1.5, 0.5):
        if best[1] is None:
            break
        b0 = best[1]
        for c in _kandidat(pot, kon, b0.xo + np.arange(-2, 3) * d, b0.yo + np.arange(-2, 3) * d,
                           (b0.yo - b0.r) + np.arange(-2, 3) * d / 2):
            uji(c)
    return best


@lru_cache(maxsize=None)
def hasil(nama, kode, metode="bishop", x_min=None, beban=True, licin_darat=LICIN_UJUNG_DARAT, k_su=1.0, berm=False,
          urug_labil=1.0, landai=False):
    pot = potongan(nama, beban=beban, licin_darat=licin_darat, k_su=k_su, berm=berm, urug_labil=urug_labil,
                   landai=landai)
    kon = {k.kode: k for k in kondisi()}[kode]
    f, b, s = cari(pot, kon, metode, x_min)
    return dict(potongan=nama, kondisi=kode, metode=metode, fk=f, bidang=b, x1=s["x1"] if s else None,
                x2=s["x2"] if s else None, izin=FK_IZIN[kode][0], pot=pot, kon=kon)


def silang(nama, kode, k_su=1.0):
    """Cek silang: FK Fellenius pada bidang kritis Bishop (bidang sama, beda metode)."""
    h = hasil(nama, kode, k_su=k_su)
    f_fel, _ = fk(h["pot"], h["kon"], h["bidang"], "fellenius")
    return h["fk"], f_fel


def tabel_fk(k_su=1.0):
    baris = []
    for n in ("P-1", "P-2", "P-3"):
        for k in kondisi():
            hb, hf = hasil(n, k.kode, k_su=k_su), hasil(n, k.kode, "fellenius", k_su=k_su)
            f_sil, _ = fk(hb["pot"], hb["kon"], hb["bidang"], "fellenius")
            baris.append(dict(potongan=n, kondisi=k.kode, nama=k.nama, bishop=hb["fk"], fellenius=hf["fk"],
                              fel_sama=f_sil, izin=hb["izin"], x1=hb["x1"], x2=hb["x2"], bidang=hb["bidang"],
                              lolos=hb["fk"] >= hb["izin"]))
    return baris


def _kon_eksisting():
    return Kondisi("surut", f"eksisting, kemarau +{MA_RENDAH:.2f}", MA_RENDAH, MA_RENDAH + SELISIH_PASIR)


@lru_cache(maxsize=None)
def eksisting(nama="P-2", k_su=1.0, x_min=None):
    """Tebing sekarang (P-2: puncak Feb 2027) tanpa urugan, muka air rendah musiman +4,0."""
    pot = potongan(nama, beban=False, k_su=k_su)
    return cari(pot, _kon_eksisting(), x_min=x_min)


X_PUNCAK_P2 = 6.5 + GESER_P2  # puncak P-2 Feb 2027 (4,5 m dari batas lahan)


def _bagi_dua(f, lo, hi, target=1.0, tol=0.01):
    """k terkecil (dibulatkan ke atas 0,01) dengan f(k) ≥ target; f naik terhadap k."""
    if f(lo) >= target:
        return lo
    while hi - lo > tol:
        mid = round((lo + hi) / 2, 4)
        if f(mid) < target:
            lo = mid
        else:
            hi = mid
    return math.ceil(hi * 100) / 100


@lru_cache(maxsize=1)
def analisis_balik(target=1.0):
    """Analisis balik dua langkah, kondisi eksisting kemarau (tanpa urugan, muka air +4,0):
    1. faktor su lempung U2/U4 (kl) terkecil agar tebing P-1 dan P-3 yang tidak longsor FK ≥ 1,0 (batas bawah);
    2. dengan kl itu, faktor su bidang licin + massa longsoran (kw) agar bidang yang mencapai puncak P-2 FK = 1,0.
    Dasar langkah 2: puncak P-2 mundur 2 m Des 2026 - Feb 2027 (survei vs surat sempadan) dan 1-2 m sejak Agu 2026
    (langkah 3.2), hanya di x 80-100: P-2 di ambang runtuh, P-1 dan P-3 tidak."""
    kl = _bagi_dua(lambda k: min(eksisting("P-1", k)[0], eksisting("P-3", k)[0]), 1.0, 3.0, target)
    xm = X_PUNCAK_P2 - 0.5
    kw = _bagi_dua(lambda k: eksisting("P-2", (kl, k), xm)[0], 0.2, 3.0, target)
    return (kl, kw), eksisting("P-2", (kl, kw), xm)[0]


def k_desain():
    return analisis_balik()[0]


# ------------------------------------------------------------------ jarak aman, urugan, perkuatan
JARAK_UJI = (0.0, 5.0, 10.0, 15.5, 20.0, 25.5, 30.0, 35.0)


def jangkauan_persil(nama="P-2", kode="statis", k_su=None, berm=False, urug_labil=1.0):
    """[(d, FK)]: FK Bishop minimum untuk bidang yang ujung atasnya masuk persil sejauh ≥ d (x1 ≤ -d)."""
    k = k_desain() if k_su is None else k_su
    return [(d, hasil(nama, kode, x_min=-d, k_su=k, berm=berm, urug_labil=urug_labil)["fk"]) for d in JARAK_UJI]


def jarak_aman(nama="P-2", kode="statis", k_su=None, berm=False):
    """Jarak terkecil dari batas lahan (ke darat) yang tidak lagi dilewati bidang dengan FK < izin."""
    izin = FK_IZIN[kode][0]
    for d, f in jangkauan_persil(nama, kode, k_su, berm):
        if f >= izin:
            return d, f
    return None, None


def gaya_stabil(nama="P-2", kode="statis", target=None, x_min=0.0, k_su=None, berm=False, landai=False):
    """Gaya geser tambahan per meter lari (kN/m) yang harus dipikul tiang/turap yang memotong bidang kritis agar
    FK = target: P = (FK_target - FK) × M_dorong / R."""
    k = k_desain() if k_su is None else k_su
    h = hasil(nama, kode, x_min=x_min, k_su=k, berm=berm, landai=landai)
    t = FK_IZIN[kode][0] if target is None else target
    s = _iris(h["pot"], h["kon"], h["bidang"])
    f, den = _fk_den(s, h["bidang"], h["kon"].kh, "bishop")
    return dict(fk=f, target=t, P=max(0.0, (t - f) * den / h["bidang"].r), bidang=h["bidang"], x1=h["x1"],
                x2=h["x2"], y_dasar=float(np.min(s["ym"])), M=den)


def perkuatan(k_su=None):
    """FK Bishop P-2 per kondisi: tanpa perkuatan dan dengan berm kaki; semua bidang dan bidang yang masuk persil."""
    k = k_desain() if k_su is None else k_su
    baris = []
    for kon in kondisi():
        row = dict(kondisi=kon.kode, nama=kon.nama, izin=FK_IZIN[kon.kode][0])
        row["tanpa"] = hasil("P-2", kon.kode, k_su=k)["fk"]
        row["tanpa_persil"] = hasil("P-2", kon.kode, x_min=0.0, k_su=k)["fk"]
        row["berm"] = hasil("P-2", kon.kode, k_su=k, berm=True)["fk"]
        row["berm_persil"] = hasil("P-2", kon.kode, x_min=0.0, k_su=k, berm=True)["fk"]
        row["landai"] = hasil("P-2", kon.kode, k_su=k, berm=True, landai=True)["fk"]
        row["landai_persil"] = hasil("P-2", kon.kode, x_min=0.0, k_su=k, berm=True, landai=True)["fk"]
        baris.append(row)
    return baris


def pengaruh_urugan(k_su=None):
    """FK statis bidang yang masuk jalur penyangga (x1 ≤ -garis sempadan) untuk urugan zona labil 0 s.d. 1,5 m."""
    k = k_desain() if k_su is None else k_su
    g = tp.kedalaman_sempadan(X_LOKAL["P-2"])
    return [(t, hasil("P-2", "statis", x_min=-g, k_su=k, urug_labil=t)["fk"]) for t in (0.0, 0.5, 1.0, 1.5)]


# ------------------------------------------------------------------ saluran pembuang ke sungai
OUTLET_X = 128.0  # lokal; di luar zona labil (x 70-110) dan longsoran lama P-2 (x 80-100)
T_KOSONG_JAM = 6.0  # [Asumsi] kolam kosong dalam 6 jam setelah hujan Q10 (siap hujan berikutnya)
TC_MENIT = 15.0  # [Asumsi] waktu konsentrasi persil ±1 ha
N_MANNING = 0.012  # [Asumsi] HDPE/beton halus
S_PIPA = 0.01
D_PIPA = 0.40
ETA_POMPA = 0.65  # [Asumsi]
DASAR_KOLAM = pl.peil_usulan()["halaman"] - 1.8  # kolam dalam 1,8 m (tahap3_zonasi.RETENSI)
INVERT_OUTLET = POMPA_MULAI  # pintu klep di +9,70: sungai di atasnya → klep menutup, pompa jalan


def saluran():
    r = pl.retensi(10)
    i = r["R24"] / 24 * (24 / (TC_MENIT / 60)) ** (2 / 3)  # Mononobe (mm/jam) [acuan belum ada di acuan/]
    a_ha = r["luas"] / 1e4
    q_pra = pl.C_LIMPASAN["sebelum"] * i * a_ha / 360  # rasional (m³/s) [acuan belum ada di acuan/]
    q_pasca = pl.C_LIMPASAN["sesudah"] * i * a_ha / 360
    luas = math.pi * D_PIPA ** 2 / 4
    q_pipa = luas * (D_PIPA / 4) ** (2 / 3) * S_PIPA ** 0.5 / N_MANNING
    q_kosong = r["volume"] / (T_KOSONG_JAM * 3600)
    q_pompa = max(q_pra, q_kosong)
    h_statis = pl.peil_usulan()["q100"] + 0.5 - DASAR_KOLAM
    h_total = h_statis + 1.5  # [Asumsi] kehilangan pipa, klep, belokan
    terhalang = [x for x in pl.hari_terhalang() if x[2] > 0]
    return dict(volume=r["volume"], R24=r["R24"], i=i, luas_ha=a_ha, q_pra=q_pra, q_pasca=q_pasca, q_pipa=q_pipa,
                q_kosong=q_kosong, q_pompa=q_pompa, n_pompa=3, q_unit=q_pompa / 2, h_statis=h_statis,
                h_total=h_total, daya_kw=9.81 * q_pompa * h_total / ETA_POMPA,
                t_kosong_pompa=r["volume"] / q_pompa / 3600, hari_maks=max(x[2] for x in terhalang),
                tahun_terhalang=len(terhalang), n_tahun=len(pl.hari_terhalang()), dasar_kolam=DASAR_KOLAM,
                invert=INVERT_OUTLET, jarak_labil=OUTLET_X - (tp.LX - tp.LABIL_STA[0]),
                jarak_longsor=OUTLET_X - 100.0, garis_sempadan=tp.kedalaman_sempadan(OUTLET_X))




# ------------------------------------------------------------------ ringkasan untuk Excel, gambar, laporan
def fmt(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


@lru_cache(maxsize=1)
def ringkasan():
    k, f_balik = analisis_balik()
    return dict(
        k=k, f_balik=f_balik, f_eks_lab=eksisting("P-2", 1.0, X_PUNCAK_P2 - 0.5)[0],
        eks={n: eksisting(n, k)[0] for n in ("P-1", "P-2", "P-3")},
        lab=tabel_fk(1.0), balik=tabel_fk(k), perkuatan=perkuatan(),
        jangkau={kd: jangkauan_persil("P-2", kd) for kd in ("statis", "surut", "gempa")},
        jangkau_berm=jangkauan_persil("P-2", "statis", berm=True),
        urugan=pengaruh_urugan(), gaya=gaya_stabil("P-2", "statis", x_min=0.0),
        gaya_kon={kd: gaya_stabil("P-2", kd, x_min=0.0) for kd in ("statis", "surut", "gempa")},
        gaya_berm=gaya_stabil("P-2", "statis", x_min=0.0, berm=True),
        gaya_akhir={kd: gaya_stabil("P-2", kd, x_min=0.0, berm=True, landai=True) for kd in ("statis", "surut", "gempa")},
        berm_luas=luas_berm(potongan("P-2", berm=True)), saluran=saluran())


def kesimpulan(r=None):
    r = r or ringkasan()
    sl = r["saluran"]
    p2 = {b["kondisi"]: b for b in r["balik"] if b["potongan"] == "P-2"}
    pk = {b["kondisi"]: b for b in r["perkuatan"]}
    jstat = dict(r["jangkau"]["statis"])
    jberm = dict(r["jangkau_berm"])
    d_aman = next((d for d, f in r["jangkau"]["statis"] if f >= FK_IZIN["statis"][0]), None)
    d_aman_b = next((d for d, f in r["jangkau_berm"] if f >= FK_IZIN["statis"][0]), None)
    urug = dict(r["urugan"])
    g = tp.kedalaman_sempadan(X_LOKAL["P-2"])
    return [
        f"Dengan parameter desain 2.4 (garis bawah UU) semua potongan memberi FK < 1 (P-2 eksisting "
        f"{fmt(r['f_eks_lab'])}), padahal tebing masih berdiri: garis su desain terlalu rendah untuk lereng. Analisis "
        f"balik: P-1 dan P-3 yang tidak longsor perlu su lempung ≥ {fmt(r['k'][0])} × garis desain (FK eksisting "
        f"{fmt(r['eks']['P-1'])} dan {fmt(r['eks']['P-3'])}); dengan itu puncak P-2 yang sedang mundur (FK = 1,0) "
        f"memberi su bidang licin/massa longsoran {fmt(r['k'][1])} × 4,4 = {fmt(r['k'][1] * SU_LICIN, 1)} kPa.",
        f"P-2 dengan parameter analisis balik (Bishop / Fellenius): statis {fmt(p2['statis']['bishop'])} / "
        f"{fmt(p2['statis']['fellenius'])}, surut cepat {fmt(p2['surut']['bishop'])} / "
        f"{fmt(p2['surut']['fellenius'])}, gempa {fmt(p2['gempa']['bishop'])} / {fmt(p2['gempa']['fellenius'])}; "
        f"izin 1,5 / 1,25 / 1,1 (SNI 8460 Tabel 25 hal. 134, Pasal 7.5.1.1 hal. 133). Tidak memenuhi: tebing P-2 "
        "PERLU DIPERKUAT sebelum PBG (surat sempadan butir 5).",
        f"Bidang yang masuk persil (x1 ≤ 0): FK statis {fmt(jstat[0.0])}; bidang yang melewati jalur penyangga "
        f"(x1 ≤ -{fmt(g, 1)}) {fmt(jstat[15.5])}; FK statis ≥ 1,5 baru tercapai untuk bidang yang masuk "
        + (f"≥ {fmt(d_aman, 1)} m dari batas lahan." if d_aman is not None else
           f"lebih dari {fmt(JARAK_UJI[-1], 0)} m dari batas lahan (tidak tercapai di rentang uji)."),
        f"Urugan jalur penyangga 0 / 0,5 / 1,0 / 1,5 m: FK statis bidang yang melewatinya "
        f"{fmt(urug[0.0])} / {fmt(urug[0.5])} / {fmt(urug[1.0])} / {fmt(urug[1.5])}. Batas 1,0 m (butir 4) "
        "dipertahankan; urugan halaman di jalur ini baru boleh setelah perkuatan selesai dan dipantau.",
        f"Berm kaki saja hampir tidak menaikkan FK (statis {fmt(pk['statis']['tanpa'])} → {fmt(pk['statis']['berm'])}): "
        "bidang kritis P-2 ada di lereng atas yang curam (48°) dan bidang licin, di atas berm. Berm tetap perlu sebagai "
        "pelindung gerusan kaki dan penahan massa longsoran.",
        f"Perkuatan konsep (gabungan): (1) pelandaian lereng atas 1V:{LANDAI_MIRING:.0f}H dari kaki lereng curam "
        f"(pengurangan beban, galian di ruang sempadan, izin Balai); (2) berm kaki bronjong/batu puncak "
        f"+{fmt(BERM_PUNCAK)}, lebar {fmt(BERM_LEBAR, 1)} m, lereng 1:{BERM_MIRING:.0f}, ±{fmt(r['berm_luas'], 1)} m³/m, "
        f"di atas geotekstil pemisah; FK P-2 menjadi statis {fmt(pk['statis']['landai'])}, surut "
        f"{fmt(pk['surut']['landai'])}, gempa {fmt(pk['gempa']['landai'])}; (3) baris tiang bor/turap di batas lahan "
        f"menembus bidang licin +5,18-5,68 sampai pasir U5, kapasitas geser ≥ "
        f"{fmt(max(v['P'] for v in r['gaya_akhir'].values()), 0)} kN/m (gempa menentukan; statis "
        f"{fmt(r['gaya_akhir']['statis']['P'], 0)}, surut {fmt(r['gaya_akhir']['surut']['P'], 0)} kN/m) agar bidang "
        "yang masuk persil memenuhi FK izin. Rancangan rinci Tahap 6.",
        "Gempa: U5 berpotensi likuifaksi (2.6, FS < 1). Analisis pseudo-statik dengan φ' 33° tidak menangkap "
        "penyebaran lateral; kajian pasca-likuifaksi (kuat residu pasir) wajib di Tahap 6 [acuan belum ada di acuan/].",
        f"Jarak bangunan: menara/podium y ≥ 27 di luar jalur penyangga (y ≤ {fmt(g + tp.LABIL_LEBAR, 1)}). Statis, "
        f"bidang yang menjangkau ≥ 25,5 m sudah FK {fmt(jstat[25.5])}-{fmt(jstat[30.0])} ≥ 1,5, jadi tepi podium "
        f"y 27 tidak perlu digeser; tetapi bidang 0-20 m (ruang sempadan, jalur penyangga) FK {fmt(jstat[0.0])}-"
        f"{fmt(jstat[20.0])} < 1,5 dan saat gempa semua bidang FK < 1,1, sehingga perkuatan selesai sebelum urugan "
        "halaman dan podium dibangun. Tiang bor gedung di sisi selatan dicek beban lateral tanah (Tahap 6).",
        f"Saluran pembuang: outlet di x {OUTLET_X:.0f} (P-3), {fmt(sl['jarak_labil'], 0)} m di timur zona labil dan "
        f"{fmt(sl['jarak_longsor'], 0)} m dari longsoran P-2; pipa Ø{D_PIPA * 1000:.0f} i = 1 % (kapasitas "
        f"{fmt(sl['q_pipa'] * 1000, 0)} L/s ≥ laju izin {fmt(sl['q_pra'] * 1000, 0)} L/s); pintu klep di "
        f"+{fmt(sl['invert'])}; pompa {sl['n_pompa']} × {fmt(sl['q_unit'] * 1000, 0)} L/s (2 kerja + 1 cadangan), "
        f"H ±{fmt(sl['h_total'], 1)} m, ±{fmt(sl['daya_kw'], 1)} kW, jalan saat sungai > +{fmt(POMPA_MULAI)} "
        f"(maks {sl['hari_maks']} hari/tahun, {sl['tahun_terhalang']} dari {sl['n_tahun']} tahun); kolam Q10 "
        f"{fmt(sl['volume'], 0)} m³ kosong dalam ±{fmt(sl['t_kosong_pompa'], 1)} jam.",
    ]


def buat_excel(keluar=BERKAS):
    import openpyxl

    from format_dokumen import AI, Lembar, set_font_bawaan

    r = ringkasan()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)

    # 1 Petunjuk
    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk stabilitas tebing dan saluran pembuang (LA.3)", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, t] for i, t in enumerate([
        "Tujuan: stabilitas tebing sungai awal (P-1, P-2, P-3) dan rencana saluran pembuang ke sungai, syarat surat "
        "sempadan butir 5 sebelum PBG (notulen rapat konsep 5 Apr 2027).",
        "Metode: irisan 60 buah, Bishop disederhanakan dan Fellenius, keseimbangan momen terhadap pusat lingkaran; "
        "lingkaran biasa dan lingkaran terpotong bidang licin lama P-2. Pencarian grid pusat × elevasi singgung, "
        "diperhalus dua kali. Lempung U2/U4 tegangan total (su, φ = 0); pasir U5 dan urugan U1 tegangan efektif.",
        "Koordinat potongan: jarak dari batas lahan selatan (positif ke sungai); elevasi lokal (BM-1 +10,000). P-2 "
        "digeser 2,0 m ke darat sesuai puncak Feb 2027 (surat sempadan STA 0+050: 4,5 m; survei Des 2026: 6,5 m).",
        "Kondisi (SNI 8460 Pasal 7.6 hal. 135): (a) statis muka air normal; (b) surut cepat Q50 → muka rendah "
        "musiman, kuat geser tak terdrainase tetap, tinggi tekan pasir tertinggal; (c) gempa pseudo-statik.",
        "Beban: ruang sempadan tanpa beban (butir 3); jalur penyangga zona labil urugan ≤ 1,0 m (butir 4); halaman "
        "+12,05 di utaranya; semuanya + 10 kPa (SNI 8460 Pasal 7.5.1 hal. 132). Urugan sebagai beban (tanpa kuat geser).",
        "Dua set parameter: (1) desain langkah 2.4 apa adanya; (2) analisis balik P-2 (FK eksisting = 1,0), faktor "
        "pada su lempung. Set (2) dipakai untuk kesimpulan dan perkuatan; set (1) ditampilkan sebagai batas bawah.",
        "Sel hijau diisi AI. Angka FK dari skrip/la_tebing.py (pencarian numerik, bukan rumus Excel); status, kh, dan "
        "saluran memakai rumus Excel yang dicocokkan dengan Python.",
        "Status: " + STATUS + ".",
    ])], rata=list("cl"))

    # 2 Data dan parameter
    lb = Lembar(wb.create_sheet("Parameter"), 2, "Data potongan, parameter tanah, muka air, beban",
                [6, 14, 16, 12, 12, 12, 70])
    lb.catatan(LABEL + " Parameter dari langkah 2.4 (Ringkasan), bor tebing langkah 2.7.")
    lb.bagian("A", "Parameter tanah")
    lb.tabel(["No", "Kode", "Bahan", "γ (kN/m³)", "su atau c' (kPa)", "φ' (°)", "Sumber"], [
        [i + 1, b.kode, {"U1": "Urugan lama", "U2": "Kerak lempung teguh", "U4": "Lempung lunak",
                         "LICIN": "Bidang licin lama", "LONGSOR": "Massa longsoran", "U5": "Pasir lepas-agak padat",
                         "U6": "Lempung kaku", "BERM": "Bronjong/batu (perkuatan)", "AIR": "Air sungai"}[b.kode],
         b.gamma, "5,23 + 1,09 z" if b.su_z else b.su, b.phi, b.sumber]
        for i, b in enumerate(BAHAN.values()) if not b.kode.startswith("UJI")],
        rata=list("cclcccl"), fmt=[None, None, None, "0.0", "0.0", "0", None], fill_kolom={6: AI})
    lb.kosong()
    lb.bagian("B", "Batas lapisan (elevasi bawah, m) dan bor")
    lb.tabel(["No", "Potongan", "x lokal (m)", "U2/U1 bawah", "U4 bawah", "U5 bawah", "Keterangan"], [
        [i + 1, n, X_LOKAL[n], LAPIS[n][-4][1], dict(LAPIS[n])["U4"], dict(LAPIS[n])["U5"],
         f"Bor {BOR[n][0]}" + (f" dan {BOR[n][1]}" if BOR[n][1] else "") +
         ("; bidang licin +5,18-5,68 (BT-2), massa longsoran BT-2K +3,76-6,11; diperpanjang ke darat sampai "
          f"jarak {LICIN_UJUNG_DARAT:.0f} m [Asumsi: tidak ada bor di persil]" if n == "P-2" else "")]
        for i, n in enumerate(("P-1", "P-2", "P-3"))], rata=list("ccccccl"), fmt=[None, None, "0", "0.00", "0.00", "0.00", None])
    lb.kosong()
    lb.bagian("C", "Muka air, gempa, dan beban permukaan")
    r0 = lb.baris + 1
    lb.tabel(["No", "Butir", "Nilai", "Satuan", "", "", "Sumber"], [
        [1, "Muka air normal", MA_NORMAL, "m", "", "", "Rata-rata 12 bulan TOR Lampiran A (tahap2_air_tanah)"],
        [2, "Muka air Q50", MA_Q50, "m", "", "", "Langkah 3.3 (sama dengan surat Balai)"],
        [3, "Muka air rendah musiman", MA_RENDAH, "m", "", "", "TOR 4.3 dan Lampiran A (Sep)"],
        [4, "Tinggi tekan pasir di atas sungai", SELISIH_PASIR, "m", "", "",
         "Langkah 2.3 (PZ-1 saat surut); turun linear ke muka sungai di tempat pasir tersingkap"],
        [5, "Tinggi tekan pasir saat surut cepat", MA_NORMAL + SELISIH_PASIR, "m", "", "",
         "[Asumsi: pasir belum turun dari kondisi normal saat sungai sudah di +4,00]"],
        [6, "amax = PGAM (langkah 2.6)", lq.AMAX, "g", "", "", "SNI 1726:2019 Pers. 15 hal. 39"],
        [7, "kh = 0,5 amax", f"=E{r0 + 5}*0.5", "-", "", "", "SNI 8460:2017 Pasal 12.2.7 hal. 279"],
        [8, "Beban permukaan", Q_PERMUKAAN, "kPa", "", "", "SNI 8460:2017 Pasal 7.5.1 hal. 132"],
        [9, "γ urugan", pu.GAMMA_URUG, "kN/m³", "", "", "Langkah 2.8"],
    ], rata=list("clccccl"), fmt=[None, None, "0.000", None, None, None, None], fill_kolom={2: AI})
    lb.kosong()
    lb.bagian("D", "Beban permukaan per potongan (x dari batas lahan, negatif ke darat)")
    bb = []
    for n in ("P-1", "P-2", "P-3"):
        for x0, x1, qq, ur in potongan(n).beban:
            bb.append([len(bb) + 1, n, max(x0, -45.0), x1, qq, "kPa", ur])
    lb.tabel(["No", "Potongan", "x dari (m)", "x sampai (m)", "q (kPa)", "Satuan", "Uraian"], bb,
             rata=list("ccccccl"), fmt=[None, None, "0.0", "0.0", "0.0", None, None])

    # 3 Kriteria
    lb = Lembar(wb.create_sheet("Kriteria"), 3, "Kriteria faktor keamanan (SNI 8460:2017)", [6, 30, 12, 90])
    lb.catatan(LABEL + " Pasal dan halaman dicocokkan dengan acuan/privat/SNI-8460-2017 (nomor halaman cetak).")
    lb.tabel(["No", "Kondisi", "FK izin", "Dasar"], [
        [1, "(a) Statis", FK_IZIN["statis"][0], FK_IZIN["statis"][1]],
        [2, "(b) Surut cepat", FK_IZIN["surut"][0], FK_IZIN["surut"][1]],
        [3, "(c) Gempa pseudo-statik", FK_IZIN["gempa"][0], FK_IZIN["gempa"][1]],
        [4, "Statis, ketidakpastian tinggi", FK_KETIDAKPASTIAN_TINGGI,
         "Tabel 25 kolom tinggi; berlaku bila bor persil menunjukkan bidang licin menerus jauh ke darat"],
    ], rata=list("clcl"), fmt=[None, None, "0.00", None], fill_kolom={2: AI, 3: AI})

    # 4 FK
    lb = Lembar(wb.create_sheet("FK Lereng"), 4, "Faktor keamanan per potongan dan kondisi",
                [6, 10, 40, 12, 12, 12, 10, 12, 12, 12, 12, 12])
    lb.catatan(LABEL + " Bishop dan Fellenius dicari terpisah (bidang kritis masing-masing); 'Fellenius bidang "
               "Bishop' = cek silang pada bidang yang sama. x1-x2 = ujung bidang (jarak dari batas lahan).")
    for huruf, judul, data in (("A", f"Parameter analisis balik (su lempung × {fmt(r['k'][0])}, bidang licin × {fmt(r['k'][1])}) - DIPAKAI", r["balik"]),
                               ("B", "Parameter desain 2.4 apa adanya (batas bawah)", r["lab"])):
        lb.bagian(huruf, judul)
        r0 = lb.baris + 1
        rows = []
        for i, b in enumerate(data):
            rr = r0 + i
            rows.append([i + 1, b["potongan"], b["nama"], b["bishop"], b["fellenius"], b["fel_sama"], b["izin"],
                         f'=IF(F{rr}>=I{rr},"Memenuhi","Tidak")', b["bidang"].xo, b["bidang"].yo, b["bidang"].r,
                         f"{b['x1']:.1f} s.d. {b['x2']:.1f}".replace(".", ",")])
        lb.tabel(["No", "Potongan", "Kondisi", "FK Bishop", "FK Fellenius", "Fellenius bidang Bishop", "FK izin",
                  "Status (Bishop)", "Pusat x (m)", "Pusat y (m)", "R (m)", "x1 s.d. x2 (m)"], rows,
                 rata=list("ccl") + ["c"] * 9, fmt=[None, None, None, "0.00", "0.00", "0.00", "0.00", None, "0.0",
                                                   "0.0", "0.00", None], fill_kolom={3: AI, 4: AI, 5: AI})
        lb.kosong()

    # 5 Analisis balik
    lb = Lembar(wb.create_sheet("Analisis Balik"), 5, "Analisis balik dua langkah (kondisi eksisting)",
                [6, 56, 14, 12, 60])
    lb.catatan(LABEL + f" Kondisi eksisting: tanpa urugan, muka air rendah +{fmt(MA_RENDAH)}, P-2 puncak Feb 2027. "
               "Langkah 1: faktor su lempung U2/U4 terkecil agar P-1 dan P-3 (tidak longsor) FK ≥ 1,0. Langkah 2: faktor "
               "su bidang licin dan massa longsoran agar bidang yang mencapai puncak P-2 (x1 ≤ 4,0 m) FK = 1,0.")
    r0 = lb.baris + 1
    lb.tabel(["No", "Butir", "Nilai", "Satuan", "Keterangan"], [
        [1, "FK P-2 eksisting, parameter 2.4 apa adanya", r["f_eks_lab"], "-", "< 1 padahal tebing berdiri"],
        [2, "Faktor su lempung U2/U4 (langkah 1)", r["k"][0], "-", "Bisection, toleransi 0,01, dibulatkan ke atas"],
        [3, "FK P-1 eksisting dengan faktor langkah 1", r["eks"]["P-1"], "-", "≥ 1,0"],
        [4, "FK P-3 eksisting dengan faktor langkah 1", r["eks"]["P-3"], "-", "≥ 1,0"],
        [5, "Faktor su bidang licin dan massa longsoran (langkah 2)", r["k"][1], "-", "Bisection, target FK P-2 = 1,0"],
        [6, "FK P-2 eksisting (bidang mencapai puncak)", r["f_balik"], "-", "Target 1,0"],
        [7, "su U4 di z = 5 m termobilisasi", f"=(5.23+1.09*5)*E{r0 + 1}", "kPa", "Garis desain 2.4: 10,68 kPa"],
        [8, "su bidang licin termobilisasi", f"=4.4*E{r0 + 4}", "kPa", "BT-2 UD-2: 4,4 kPa"],
    ], rata=list("clccl"), fmt=[None, None, "0.00", None, None], fill_kolom={2: AI})
    lb.catatan("Tafsiran: garis su UU 2.4 (contoh terganggu, batas bawah) terlalu rendah untuk lereng; P-2 lebih lemah "
               "karena bidang licin lama. Faktor ini batas bawah (P-1, P-3 bisa lebih kuat). Perlu uji lapangan (vane/CPTu) "
               "di tebing pada Tahap 6.")

    # 6 Jarak dan urugan
    lb = Lembar(wb.create_sheet("Jarak dan Urugan"), 6, "Jangkauan bidang gelincir ke persil dan pengaruh urugan",
                [6, 26, 14, 14, 14, 16, 50])
    lb.catatan(LABEL + " FK Bishop minimum untuk bidang yang ujung atasnya masuk persil ≥ d (parameter analisis "
               "balik, P-2). Garis sempadan di x 90 = 15,5 m; jalur penyangga 15,5-25,5 m; menara/podium y ≥ 27 m.")
    js, ju, jg, jb = (dict(r["jangkau"]["statis"]), dict(r["jangkau"]["surut"]), dict(r["jangkau"]["gempa"]),
                      dict(r["jangkau_berm"]))
    lb.tabel(["No", "Masuk persil d (m)", "FK statis", "FK surut", "FK gempa", "FK statis + berm", "Keterangan"], [
        [i + 1, d, js[d], ju[d], jg[d], jb[d], {0.0: "batas lahan", 15.5: "garis sempadan / awal jalur penyangga",
                                                25.5: "akhir jalur penyangga", 30.0: "± tepi podium/menara (y 27)"}.get(d, "")]
        for i, d in enumerate(JARAK_UJI)], rata=list("cccccc") + ["l"], fmt=[None, "0.0", "0.00", "0.00", "0.00", "0.00", None],
        fill_kolom={2: AI, 3: AI, 4: AI, 5: AI})
    lb.kosong()
    lb.bagian("B", "Pengaruh tebal urugan jalur penyangga (statis, bidang x1 ≤ -15,5)")
    lb.tabel(["No", "Tebal urugan (m)", "FK statis", "", "", "", "Keterangan"], [
        [i + 1, t, f, "", "", "", "batas surat sempadan butir 4" if t == 1.0 else ""] for i, (t, f) in
        enumerate(r["urugan"])], rata=list("ccccccl"), fmt=[None, "0.0", "0.00", None, None, None, None], fill_kolom={2: AI})

    # 7 Perkuatan
    lb = Lembar(wb.create_sheet("Perkuatan"), 7, "Kebutuhan dan konsep perkuatan tebing P-2",
                [6, 44, 14, 14, 14, 16, 16, 12])
    lb.catatan(LABEL + f" Berm kaki: puncak +{fmt(BERM_PUNCAK)}, lebar {fmt(BERM_LEBAR, 1)} m, lereng 1:{BERM_MIRING:.0f}, "
               "bahan bronjong/batu [Asumsi γ 20, φ' 40°]. FK Bishop, parameter analisis balik.")
    r0 = lb.baris + 1
    lb.tabel(["No", "Kondisi", "Tanpa (semua bidang)", "Tanpa (masuk persil)", "Berm (semua bidang)",
              "Berm + pelandaian (semua)", "Berm + pelandaian (masuk persil)", "FK izin"], [
        [i + 1, p["nama"], p["tanpa"], p["tanpa_persil"], p["berm"], p["landai"], p["landai_persil"], p["izin"]]
        for i, p in enumerate(r["perkuatan"])], rata=list("cl") + ["c"] * 6, fmt=[None, None] + ["0.00"] * 6,
        fill_kolom={2: AI, 3: AI, 4: AI, 5: AI, 6: AI})
    lb.kosong()
    lb.bagian("B", "Syarat perkuatan yang diangkakan")
    ga, gb = r["gaya"], r["gaya_berm"]
    lb.tabel(["No", "Butir", "Nilai", "Satuan", "", "", "", ""], [
        [1, "Volume berm kaki per meter lari", r["berm_luas"], "m³/m", "", "", "", ""],
        [2, "Panjang perkuatan (x 70-110 + 10 m tiap sisi)", 60.0, "m", "", "", "", ""],
        [3, "Volume berm total", f"=E{lb.baris + 1}*E{lb.baris + 2}", "m³", "", "", "", ""],
        [4, "Gaya geser tiang, FK statis 1,5, tanpa perkuatan lain", ga["P"], "kN/m", "", "", "", ""],
        [5, "Gaya geser tiang, statis 1,5, dengan berm + pelandaian", r["gaya_akhir"]["statis"]["P"], "kN/m", "", "", "", ""],
        [6, "Gaya geser tiang, surut 1,25, dengan berm + pelandaian", r["gaya_akhir"]["surut"]["P"], "kN/m", "", "", "", ""],
        [7, "Gaya geser tiang, gempa 1,1, dengan berm + pelandaian", r["gaya_akhir"]["gempa"]["P"], "kN/m", "", "", "", ""],
        [8, "Kemiringan pelandaian lereng atas (1V : nH)", LANDAI_MIRING, "-", "", "", "", ""],
        [9, "Batas urugan jalur penyangga sebelum perkuatan selesai", 1.0, "m", "", "", "", ""],
    ], rata=list("clcc") + ["c"] * 4, fmt=[None, None, "#,##0.00", None, None, None, None, None], fill_kolom={2: AI})

    # 8 Saluran
    sl = r["saluran"]
    lb = Lembar(wb.create_sheet("Saluran Pembuang"), 8, "Rencana saluran pembuang ke sungai", [6, 56, 14, 12, 60])
    lb.catatan(LABEL + " Rumus rasional dan Mononobe [acuan belum ada di acuan/; rinci di DED Tahap 7]. Kolam "
               "retensi x 112-134, y 22-40, dalam 1,8 m (langkah 3.4).")
    r0 = lb.baris + 1
    lb.tabel(["No", "Butir", "Nilai", "Satuan", "Keterangan"], [
        [1, "Volume retensi Q10", sl["volume"], "m³", "tahap3_peil.retensi(10), PKKPR persyaratan 4"],
        [2, "R24 kala ulang 10 tahun", sl["R24"], "mm", "Gumbel, langkah 3.3"],
        [3, "Waktu konsentrasi", TC_MENIT, "menit", "[Asumsi] persil ±1 ha"],
        [4, "Intensitas Mononobe I = R24/24 (24/tc)^(2/3)", f"=E{r0 + 1}/24*(24/(E{r0 + 2}/60))^(2/3)", "mm/jam", ""],
        [5, "Luas lahan perencanaan", sl["luas_ha"], "ha", "langkah 3.2"],
        [6, "Laju buang izin Q = C_sebelum I A / 360", f"={pl.C_LIMPASAN['sebelum']}*E{r0 + 3}*E{r0 + 4}/360", "m³/s",
         f"C sebelum {pl.C_LIMPASAN['sebelum']} [Asumsi 3.3]"],
        [7, "Kapasitas pipa Ø400, i 1 %, n 0,012 (penuh)", f"=PI()*{D_PIPA}^2/4*({D_PIPA}/4)^(2/3)*{S_PIPA}^0.5/{N_MANNING}",
         "m³/s", "Manning [Asumsi n]"],
        [8, "Kapasitas pompa = maks(laju izin; V / 6 jam)", f"=MAX(E{r0 + 5},E{r0}/({T_KOSONG_JAM}*3600))", "m³/s",
         "3 unit × 50 % (2 kerja + 1 cadangan)"],
        [9, "Tinggi angkat statis (Q100 + 0,5 - dasar kolam)", sl["h_statis"], "m", f"dasar kolam +{fmt(DASAR_KOLAM)}"],
        [10, "Tinggi angkat total", f"=E{r0 + 8}+1.5", "m", "[Asumsi] kehilangan 1,5 m"],
        [11, "Daya pompa total = 9,81 Q H / η", f"=9.81*E{r0 + 7}*E{r0 + 9}/{ETA_POMPA}", "kW", f"η {ETA_POMPA} [Asumsi]; catu genset RS"],
        [12, "Waktu kosong kolam dengan pompa", f"=E{r0}/E{r0 + 7}/3600", "jam", ""],
        [13, "Muka sungai pompa mulai (pintu klep menutup)", POMPA_MULAI, "m", "Data Hidrologi lembar Lama Genangan"],
        [14, "Hari terlama per tahun sungai > +9,70", sl["hari_maks"], "hari",
         f"{sl['tahun_terhalang']} dari {sl['n_tahun']} tahun 2008-2026"],
        [15, "Lokasi outlet x lokal", OUTLET_X, "m", f"{fmt(sl['jarak_labil'], 0)} m di timur zona labil; "
                                                    f"{fmt(sl['jarak_longsor'], 0)} m dari longsoran P-2"],
        [16, "Garis sempadan di outlet (dari batas selatan)", sl["garis_sempadan"], "m", "pipa melintas ruang sempadan "
         "tertanam, tanpa perkerasan; izin Balai"],
    ], rata=list("clccl"), fmt=[None, None, "#,##0.000", None, None], fill_kolom={2: AI})

    # 9 Kesimpulan
    lb = Lembar(wb.create_sheet("Kesimpulan"), 9, "Kesimpulan dan rekomendasi (draf)", [6, 130])
    lb.catatan(LABEL + " " + STATUS + ".")
    lb.tabel(["No", "Kesimpulan"], [[i + 1, t] for i, t in enumerate(kesimpulan(r))], rata=list("cl"), fill=AI)
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


# ------------------------------------------------------------------ gambar GK-11 (CAD asli)
DX_DENAH, DY_DENAH = 0.0, 140.0  # denah kunci diletakkan di atas potongan pada model space (m)
V_POT = 1.0  # potongan tanpa pembesaran vertikal


def _poligon_lapis(pot, x0, x1, atas, bawah):
    """Poligon lapisan antara elevasi atas/bawah, dipotong muka tanah."""
    xx = np.linspace(x0, x1, 241)
    zt = np.minimum(pot.tanah0(xx), atas)
    ok = zt > bawah
    if not ok.any():
        return None
    xx, zt = xx[ok], zt[ok]
    return [(float(x), float(z)) for x, z in zip(xx, zt)] + [(float(xx[-1]), bawah), (float(xx[0]), bawah)]


def gambar_cad(status=None):
    from cad_lembar import STATUS_SETUJU, Gambar
    import tahap3_program as pr
    import tahap3_zonasi as zn

    r = ringkasan()
    k = r["k"]
    pot = potongan("P-2", k_su=k, berm=True)
    x0, x1 = -38.0, 42.0
    dwg = KELUAR / "Gambar" / "DWG" / "GK-11 Stabilitas Tebing.dwg"
    png = KELUAR / "Gambar" / "GK-11 Stabilitas Tebing.png"
    with Gambar(300) as g:
        # ---------------- potongan P-2 (model space: x = jarak, y = elevasi)
        pola = {"U2": "GT-LEMPUNG-TEGUH", "U4": "GT-LEMPUNG-LUNAK", "U5": "GT-PASIR-LEPAS", "U6": "GT-LEMPUNG-KAKU"}
        nama = {"U2": "U2 kerak lempung teguh, su 35 kPa", "U4": "U4 lempung lunak, su = 5,23 + 1,09 z kPa",
                "U5": "U5 pasir lepas-agak padat, φ' 33°", "U6": "U6 lempung kaku, su 85 kPa"}
        atas = 12.0
        for kode, bawah in pot.lapis:
            bw = max(bawah, -8.0)
            pg = _poligon_lapis(pot, x0, x1, atas, bw)
            if pg:
                g.layer(f"G-{kode}", 7, 0.18)
                g.arsir(pg, f"G-{kode}", pola=pola[kode], skala_pola=0.5)
                g.legenda_tambah("arsir", nama[kode], pola=pola[kode], skala_pola=0.5)
            atas = bawah
        # bidang licin dan massa longsoran
        a, b_ = pot.licin_rentang()
        xx = np.linspace(a, b_, 60)
        yl = pot.y_licin(xx)
        g.layer("G-LICIN", 7, 0.5)
        pita = [(float(x), float(y + LICIN_TEBAL / 2)) for x, y in zip(xx, yl)] + \
               [(float(x), float(y - LICIN_TEBAL / 2)) for x, y in zip(xx[::-1], yl[::-1])]
        g.arsir(pita, "G-LICIN", pola="SOLID")
        xs_l = np.linspace(LONGSOR_DARI + pot.geser, b_, 40)
        zt = pot.tanah0(xs_l)
        yl2 = pot.y_licin(xs_l) + LICIN_TEBAL / 2
        ok = zt > yl2
        g.arsir([(float(x), float(z)) for x, z in zip(xs_l[ok], zt[ok])] +
                [(float(x), float(y)) for x, y in zip(xs_l[ok][::-1], yl2[ok][::-1])], "G-LICIN",
                pola="GT-LONGSOR", skala_pola=0.5)
        g.legenda_tambah("arsir", "Bidang licin dan massa longsoran lama",
                         pola="GT-LONGSOR", skala_pola=0.5)
        # muka tanah, berm
        g.layer("G-TANAH", 7, 0.5)
        xx = np.linspace(x0, x1, 321)
        g.pline([(float(x), float(z)) for x, z in zip(xx, pot.tanah0(xx))], "G-TANAH")
        bx = np.linspace(pot.berm[0][0], pot.berm[-1][0], 80)
        bz, bz0 = pot.tanah(bx), pot.tanah0(bx)
        okb = bz - bz0 > 0.01
        g.layer("G-BERM", 7, 0.35, "DASHED")
        g.arsir([(float(x), float(z)) for x, z in zip(bx[okb], bz[okb])] +
                [(float(x), float(z)) for x, z in zip(bx[okb][::-1], bz0[okb][::-1])], "G-BERM", pola="ANSI37",
                skala_pola=0.6)
        g.legenda_tambah("arsir", f"Usulan berm kaki bronjong/batu, puncak +{fmt(BERM_PUNCAK)}", pola="ANSI37",
                         skala_pola=0.6)
        potl = potongan("P-2", k_su=k, berm=True, landai=True)
        xl_ = np.linspace(-2.0, 8.0, 101)
        zl0, zl1 = pot.tanah0(xl_), potl.tanah0(xl_)
        okl = zl0 - zl1 > 0.02
        g.layer("G-LANDAI", 7, 0.35, "DASHED")
        g.pline([(float(x), float(z)) for x, z in zip(xl_[okl], zl1[okl])], "G-LANDAI")
        g.legenda_tambah("garis", f"Usulan pelandaian lereng atas 1V:{LANDAI_MIRING:.0f}H", garis="DASHED", tebal=0.35)
        # beban permukaan
        g.layer("G-BEBAN", 7, 0.25)
        for bx0, bx1, qq, ur in pot.beban:
            bx0 = max(bx0, x0)
            zt0 = float(pot.tanah0(bx0))
            tinggi_m = 0.6 if "penyangga" in ur else 1.2
            g.pline([(bx0, zt0 + 0.15), (bx0, zt0 + tinggi_m), (bx1, zt0 + tinggi_m), (bx1, zt0 + 0.15)], "G-BEBAN")
            for xa in np.arange(bx0 + 1.0, bx1, 2.5):
                g.pline([(float(xa), zt0 + tinggi_m), (float(xa), zt0 + 0.25)], "G-BEBAN")
            g.teks(((bx0 + bx1) / 2, zt0 + tinggi_m + 0.5), f"q = {fmt(qq, 1)} kPa", "G-BEBAN", 1.6, j="BC")
        # muka air
        g.layer("G-AIR", 7, 0.25, "HIDDEN")
        for nm, el in (("Q50", MA_Q50), ("NORMAL", MA_NORMAL), ("RENDAH", MA_RENDAH)):
            xa = float(np.interp(el, pot.tanah0(np.linspace(0, x1, 400))[::-1], np.linspace(0, x1, 400)[::-1]))
            g.pline([(xa, el), (x1, el)], "G-AIR")
            g.teks((x1 + 0.5, el), f"MA {nm} +{fmt(el)}", "G-AIR", 1.5, j="ML")
        g.legenda_tambah("garis", "Muka air sungai", garis="HIDDEN", tebal=0.25)
        # lingkaran kritis (parameter analisis balik, tanpa berm) dan dengan berm
        gaya = {"statis": ("Continuous", 0.5), "surut": ("DASHED", 0.5), "gempa": ("DASHDOT", 0.5)}
        for kd, (gr, tb) in gaya.items():
            h = hasil("P-2", kd, x_min=0.0, k_su=k)
            s = _iris(h["pot"], h["kon"], h["bidang"])
            g.layer(f"G-BIDANG-{kd.upper()}", 7, tb, gr)
            g.pline([(float(s["x1"]), float(h["pot"].tanah(s["x1"])))] +
                    [(float(x), float(y)) for x, y in zip(s["xm"], s["ym"])] +
                    [(float(s["x2"]), float(max(h["pot"].tanah(s["x2"]), h["kon"].ma_sungai)))], f"G-BIDANG-{kd.upper()}")
            g.legenda_tambah("garis", f"Bidang kritis {h['kon'].nama[:3]} FK {fmt(h['fk'])} (izin {fmt(h['izin'])})",
                             garis=gr, tebal=tb)
        hb = hasil("P-2", "statis", x_min=0.0, k_su=k, berm=True, landai=True)
        s = _iris(hb["pot"], hb["kon"], hb["bidang"])
        g.layer("G-BIDANG-BERM", 7, 0.35, "DOT")
        g.pline([(float(x), float(y)) for x, y in zip(s["xm"], s["ym"])], "G-BIDANG-BERM")
        g.legenda_tambah("garis", f"Statis + berm + pelandaian FK {fmt(hb['fk'])}", garis="DOT", tebal=0.35)
        # bor
        g.layer("G-BOR", 7, 0.35)
        for nm, xb, ea, eb in (("BT-2", 4.5 + pot.geser, 10.28, 0.0), ("BT-2K", 15.0 + pot.geser, 6.11, -3.0)):
            g.pline([(xb, ea), (xb, max(eb, -7.5))], "G-BOR")
            g.teks((xb, ea + 0.6), nm, "G-BOR", 1.6, j="BC", tebal=True)
        # batas dan ukuran
        gs = tp.kedalaman_sempadan(X_LOKAL["P-2"])
        g.layer("C-BATAS", 7, 0.35, "PHANTOM")
        for xb, nm in ((0.0, "BATAS"), (-gs, "SEMPADAN"), (-(gs + tp.LABIL_LEBAR), "PENYANGGA"),
                       (-27.0, "PODIUM")):
            g.pline([(xb, -7.5), (xb, 13.4)], "C-BATAS")
            g.teks((xb + 0.4, 13.6), nm, "C-BATAS", 1.4, rot=90)
        g.ukur((-gs, 12.6), (0.0, 12.6), (-gs / 2, 12.6))
        g.ukur((-(gs + tp.LABIL_LEBAR), 12.6), (-gs, 12.6), (-(gs + 5), 12.6))
        g.teks((-gs / 2, 13.9), "RUANG SEMPADAN", "C-BATAS", 1.5, j="BC")
        g.teks((-(gs + 5), 13.9), "JALUR PENYANGGA", "C-BATAS", 1.5, j="BC")
        g.ukur(pot.berm[0], pot.berm[1], (pot.berm[0][0] + 4, BERM_PUNCAK + 1.6))
        g.teks((pot.berm[0][0] + 4, BERM_PUNCAK + 2.9), "BERM", "C-BATAS", 1.5, j="BC")
        # skala elevasi
        g.layer("C-SKALA", 7, 0.18)
        g.pline([(x0 - 1, -6), (x0 - 1, 12)], "C-SKALA")
        for el in range(-6, 13, 2):
            g.pline([(x0 - 1.6, el), (x0 - 1, el)], "C-SKALA")
            g.teks((x0 - 2.0, el), f"{el:+d},00", "C-SKALA", 1.4, j="MR")
        g.teks((x0 + 1, -7.0), "UTARA (PERSIL)", "C-SKALA", 1.6)
        g.teks((x1 - 1, -7.0), "SELATAN (SUNGAI BATANGHARI)", "C-SKALA", 1.6, j="R")

        # ---------------- denah kunci (model space digeser DY_DENAH)
        def d(p):
            return (p[0] + DX_DENAH, p[1] + DY_DENAH)

        g.layer("C-PERSIL", 7, 0.5, "PHANTOM")
        g.pline([d(p) for p in [(0, 0), (140, 0), (140, 90), (0, 90)]], "C-PERSIL", tutup=True)
        g.layer("C-SEMPADAN", 7, 0.25)
        g.arsir([d(p) for p in list(tp.ruang_sempadan().exterior.coords)[:-1]], "C-SEMPADAN", pola="DOTS",
                skala_pola=1.6)
        g.layer("C-LABIL", 7, 0.25)
        g.arsir([d(p) for p in list(tp.zona_labil().exterior.coords)[:-1]], "C-LABIL", pola="ANSI31", skala_pola=2.0)
        mn = pr.MASSA["PODIUM"]
        g.layer("A-MASSA", 7, 0.35)
        g.pline([d(p) for p in [(mn["x"][0], mn["y"][0]), (mn["x"][1], mn["y"][0]), (mn["x"][1], mn["y"][1]),
                                (mn["x"][0], mn["y"][1])]], "A-MASSA", tutup=True)
        g.teks(d(((mn["x"][0] + mn["x"][1]) / 2, 50)), "PODIUM + MENARA", "A-MASSA", 6.0, j="MC")
        rx0, rx1, ry0, ry1 = zn.RETENSI
        g.layer("C-RETENSI", 7, 0.35)
        g.arsir([d(p) for p in [(rx0, ry0), (rx1, ry0), (rx1, ry1), (rx0, ry1)]], "C-RETENSI", pola="ANSI38",
                skala_pola=2.0)
        g.teks(d(((rx0 + rx1) / 2, ry1 + 2.5)), f"KOLAM RETENSI {fmt(r['saluran']['volume'], 0)} M³", "C-RETENSI", 5.0, j="MC")
        # pipa pembuang, rumah pompa, outlet
        sl = r["saluran"]
        g.layer("C-PIPA", 7, 0.5, "DASHED")
        yo_ = -tp.puncak_2026(OUTLET_X) + 1.0
        g.pline([d((OUTLET_X, ry0)), d((OUTLET_X, yo_))], "C-PIPA")
        g.layer("C-POMPA", 7, 0.35)
        g.arsir([d(p) for p in [(OUTLET_X - 3, ry0 - 6), (OUTLET_X + 3, ry0 - 6), (OUTLET_X + 3, ry0 - 1),
                                (OUTLET_X - 3, ry0 - 1)]], "C-POMPA", pola="SOLID")
        g.pline([d((OUTLET_X + 3, ry0 - 3.5)), d((OUTLET_X + 14, ry0 - 3.5))], "C-POMPA")
        g.teks(d((OUTLET_X + 15, ry0 - 3.5)), f"RUMAH POMPA {sl['n_pompa']} × {fmt(sl['q_unit'] * 1000, 0)} L/S",
               "C-POMPA", 4.5, j="ML")
        g.pline([d((OUTLET_X, yo_)), d((OUTLET_X + 14, yo_ - 6))], "C-PIPA")
        g.teks(d((OUTLET_X + 15, yo_ - 6)), f"OUTLET + PINTU KLEP +{fmt(sl['invert'])}", "C-PIPA", 4.5, j="ML")
        # garis potongan
        g.layer("C-POTONGAN", 7, 0.5, "DASHDOT")
        for n in ("P-1", "P-2", "P-3"):
            xl = X_LOKAL[n]
            g.pline([d((xl, -14)), d((xl, 30))], "C-POTONGAN")
            g.teks(d((xl + 1, -17)), n, "C-POTONGAN", 7.0, tebal=True)
        g.teks(d((70, -21)), "SUNGAI BATANGHARI", "C-TEKS", 7.0, j="MC", tebal=True)

        g.lembar("GK-11", "Stabilitas tebing P-2 dan saluran pembuang", "1:300 / 1:1000", pusat=None,
                 judul_kop="Stabilitas tebing P-2",
                 subjudul="LA.3: Bishop dan Fellenius, parameter analisis balik; data 2.7, 2.4, 3.2, 3.3",
                 status=status or STATUS_SETUJU, viewports=[], revisi="A",
                 catatan=[
                     "FK izin 1,5/1,25/1,1: SNI 8460:2017 Tabel 25 hal. 134, Pasal 7.5.1.1 hal. 133.",
                     f"su lempung × {fmt(k[0])}, bidang licin × {fmt(k[1])} (analisis balik).",
                     f"Pompa jalan bila sungai > +{fmt(POMPA_MULAI)}.",
                 ])
        g.viewport_tambahan((24, 190), (331, 280), pusat=(3.0, 5.0), skala=300, judul="Potongan tebing P-2 (x 90)",
                            teks_skala="SKALA 1:300 (H = V)")
        g.viewport_tambahan((24, 60), (331, 178), pusat=(75 + DX_DENAH, 35 + DY_DENAH), skala=1000,
                            judul="Denah kunci: potongan, zona labil, saluran pembuang", teks_skala="SKALA 1:1000")
        g.skala_grafis(215, 22, 20)
        g.panah_utara(322, 160, 8)
        g.simpan(dwg, PDF, png)
    return dwg


def buat():
    buat_excel()
    gambar_cad()
    return BERKAS, PDF


if __name__ == "__main__":
    import sys

    if "--ringkas" in sys.argv:
        for t in kesimpulan():
            print("-", t)
    else:
        print(buat())
        for t in kesimpulan():
            print("-", t)
