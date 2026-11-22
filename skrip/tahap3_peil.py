"""Langkah 3.3: hidrologi banjir rencana, peil lantai dan utilitas, urugan halaman, drainase dan kolam retensi.

Data: '03 Desain Konsep/Data Owner/Data Hidrologi Banjir.xlsx' (CV Hidro Tepian, Feb 2027), surat sempadan (Q50 Balai),
TOR Lampiran C (topografi), langkah 2.8 (penurunan urugan), langkah 3.2 (tapak, sempadan, zona labil).
Rumus Gumbel dan metode rasional belum ada dokumennya di acuan/ (label [Literatur, belum ada di acuan]).
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 19 Nov 2026.
Rev B (LA.2): Log-Pearson III, uji kecocokan, cek peil (lembar 8); disetujui Defsa 20 Nov 2026 (LA.2).
Bangun ulang Excel saja:  .venv\\Scripts\\python.exe skrip\\tahap3_peil.py --excel
Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap3_peil.py
"""
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import openpyxl

import tahap3_tapak as tp

AKAR = Path(__file__).resolve().parents[1]
DATA = AKAR / "03 Desain Konsep" / "Data Owner"
KELUAR = AKAR / "03 Desain Konsep"
BERKAS = KELUAR / "3.3 Peil dan Urugan.xlsx"
PDF = KELUAR / "3.3 Gambar Peil dan Urugan.pdf"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = "DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026."
LABEL_LA2 = "Disetujui Defsa 20 Nov 2026 (LA.2)."

DPL_KE_LOKAL = -1.840  # Data Hidrologi lembar 1: lokal = dpl - 1,840 (pengikatan BM-1 Jan 2027)
NOL_ARSIP, NOL_UKUR_ULANG = 3.150, 3.500  # papan duga 1990-2007 (lembar 1 baris 1 dan 3)
Q50_BALAI_DPL = 13.69  # surat sempadan butir 6
T_PERIODE = [2, 5, 10, 25, 50, 100, 200]
EULER = 0.5772156649


# ------------------------------------------------------------------ hidrologi
@lru_cache(maxsize=1)
def maksimum_tahunan():
    """[(tahun, alat, bacaan, nol_dipakai, elev_dpl_penyedia, bulan_data)] dari lembar Maksimum Tahunan."""
    ws = openpyxl.load_workbook(DATA / "Data Hidrologi Banjir.xlsx", data_only=True)["Maksimum Tahunan"]
    hasil = []
    for r in ws.iter_rows(values_only=True):
        v = [x for x in r if x is not None]
        if v and isinstance(v[0], int) and 1980 < v[0] < 2100:
            tahun, _, alat, bacaan, nol, dpl, _, bulan = v[:8]
            hasil.append((tahun, alat, float(bacaan), float(nol), float(dpl), int(bulan)))
    return tuple(hasil)


def deret(koreksi_nol=True, buang_tidak_lengkap=True):
    """Elevasi maksimum tahunan (m lokal). Koreksi: papan duga 1990-2007 memakai nol +3,500 (ukur ulang 2008),
    bukan +3,150 arsip. Tahun < 12 bulan data (1999, papan rusak Jan-Jun = musim banjir) dibuang."""
    hasil = []
    for tahun, alat, bacaan, nol, dpl, bulan in maksimum_tahunan():
        if buang_tidak_lengkap and bulan < 12:
            continue
        if koreksi_nol and alat.startswith("papan"):
            dpl = bacaan + NOL_UKUR_ULANG
        hasil.append((tahun, dpl + DPL_KE_LOKAL))
    return hasil


def yn_sn(n):
    """Rata-rata dan simpangan baku variat tereduksi Gumbel untuk n data (posisi plot Weibull m/(n+1));
    dasar tabel Yn, Sn di buku hidrologi [Literatur: Gumbel 1958; belum ada di acuan]."""
    y = [-math.log(-math.log(m / (n + 1))) for m in range(1, n + 1)]
    return float(np.mean(y)), float(np.std(y))


def gumbel_yn_sn(x, T):
    """Cara 1, faktor frekuensi dengan Yn, Sn (cara penyedia): X_T = x̄ + s (Y_T - Yn) / Sn."""
    n = len(x)
    yn, sn = yn_sn(n)
    yt = -math.log(-math.log(1 - 1 / T))
    return float(np.mean(x) + np.std(x, ddof=1) * (yt - yn) / sn)


def gumbel_momen(x, T):
    """Cara 2, metode momen: K_T = -(√6/π)(0,5772 + ln ln(T/(T-1))) [Literatur: Chow, Maidment, Mays 1988,
    Applied Hydrology Pers. 12.3.x; belum ada di acuan]."""
    k = -math.sqrt(6) / math.pi * (EULER + math.log(math.log(T / (T - 1))))
    return float(np.mean(x) + k * np.std(x, ddof=1))


def tabel_frekuensi():
    """Muka air (m lokal) per periode ulang: penyedia (tanpa koreksi) vs terkoreksi, dua cara."""
    x_pen = [e for _, e in deret(koreksi_nol=False, buang_tidak_lengkap=False)]
    x_kor = [e for _, e in deret()]
    return [{"T": T, "penyedia": gumbel_yn_sn(x_pen, T), "koreksi_yn": gumbel_yn_sn(x_kor, T),
             "koreksi_momen": gumbel_momen(x_kor, T)} for T in T_PERIODE]


# ------------------------------------------------------------------ LA.2: Log-Pearson III dan uji kecocokan
# Disetujui Defsa 20 Nov 2026 (LA.2). Rumus belum ada dokumennya di acuan/ (label [Literatur]).
T_LP3 = [25, 50, 100, 500]
ALFA = 0.05  # taraf nyata uji kecocokan


def statistik_log(x):
    """Rata-rata, simpangan baku sampel, dan koefisien skewness terkoreksi bias dari log10 x:
    Cs = n Σ(y - ȳ)³ / ((n - 1)(n - 2) s³) [Literatur: Chow, Maidment, Mays 1988, Pers. 11.2.x dan 12.3; belum di acuan]."""
    y = np.log10(np.asarray(x, float))
    n = len(y)
    m, s = float(y.mean()), float(y.std(ddof=1))
    cs = float(n * ((y - m) ** 3).sum() / ((n - 1) * (n - 2) * s ** 3))
    return {"n": n, "rata": m, "sd": s, "cs": cs}


def k_lp3(cs, T):
    """Faktor frekuensi Pearson III, pendekatan Kite (1977) yang dikutip Chow, Maidment, Mays (1988) Pers. 12.3.8:
    K = z + (z² - 1)k + (z³ - 6z)k²/3 - (z² - 1)k³ + z k⁴ + k⁵/3, k = Cs/6, z = Φ⁻¹(1 - 1/T)
    [Literatur: belum ada di acuan]."""
    from scipy.stats import norm

    z = float(norm.ppf(1 - 1 / T))
    k = cs / 6
    return z + (z * z - 1) * k + (z ** 3 - 6 * z) * k ** 2 / 3 - (z * z - 1) * k ** 3 + z * k ** 4 + k ** 5 / 3


def lp3_k(x, T):
    """Cara (a): log X_T = ȳ + K s."""
    st = statistik_log(x)
    return float(10 ** (st["rata"] + k_lp3(st["cs"], T) * st["sd"]))


def lp3_scipy(x, T):
    """Cara (b): kuantil eksak scipy.stats.pearson3 pada log10 x (parameter momen)."""
    from scipy.stats import pearson3

    st = statistik_log(x)
    return float(10 ** pearson3.ppf(1 - 1 / T, st["cs"], loc=st["rata"], scale=st["sd"]))


def _cdf(dist, x_data):
    """Fungsi peluang tak-terlampaui F(x) untuk distribusi yang diparameterkan dari x_data."""
    from scipy.stats import pearson3

    x_data = np.asarray(x_data, float)
    xb, s = x_data.mean(), x_data.std(ddof=1)
    if dist == "gumbel_yn":
        yn, sn = yn_sn(len(x_data))
        return lambda v: np.exp(-np.exp(-(yn + (np.asarray(v, float) - xb) * sn / s)))
    if dist == "gumbel_momen":
        a = math.sqrt(6) * s / math.pi
        u = xb - EULER * a
        return lambda v: np.exp(-np.exp(-(np.asarray(v, float) - u) / a))
    if dist == "lp3":
        st = statistik_log(x_data)
        return lambda v: pearson3.cdf(np.log10(np.asarray(v, float)), st["cs"], loc=st["rata"], scale=st["sd"])
    raise ValueError(dist)


def _invers(dist, x_data, p):
    from scipy.optimize import brentq

    f = _cdf(dist, x_data)
    return brentq(lambda v: float(f(v)) - p, 1.0, 40.0)


PARAMETER = {"gumbel_yn": 2, "gumbel_momen": 2, "lp3": 3}
NAMA_DIST = {"gumbel_yn": "Gumbel Yn-Sn", "gumbel_momen": "Gumbel momen", "lp3": "Log-Pearson III"}


def uji_chi_kuadrat(dist, x):
    """Chi-kuadrat dengan kelas berpeluang sama: G = 1 + 3,322 log n (dibulatkan), Ei = n/G, batas kelas dari
    kuantil distribusi; DK = G - R - 1 dengan R = jumlah parameter yang ditaksir (2 Gumbel, 3 LP3)
    [Literatur: Soewarno 1995; Haan 2002; belum di acuan]."""
    from scipy.stats import chi2

    x = np.asarray(x, float)
    n = len(x)
    g = int(round(1 + 3.322 * math.log10(n)))
    batas = [_invers(dist, x, i / g) for i in range(1, g)]
    o = np.histogram(x, bins=[-np.inf, *batas, np.inf])[0]
    e = n / g
    x2 = float(((o - e) ** 2 / e).sum())
    dk = g - PARAMETER[dist] - 1
    krit = float(chi2.ppf(1 - ALFA, dk))
    return {"G": g, "batas": batas, "O": o.tolist(), "E": e, "chi2": x2, "dk": dk, "kritis": krit,
            "lolos": x2 < krit}


def uji_ks(dist, x):
    """Smirnov-Kolmogorov: Dmaks = maks |P_empiris - P_teoritis|, P_empiris = m/(n + 1) (Weibull, data menaik).
    D kritis eksak scipy.stats.kstwo; pembanding asimtotik 1,36/√n [Literatur: Soewarno 1995; belum di acuan]."""
    from scipy.stats import kstwo

    xs = np.sort(np.asarray(x, float))
    n = len(xs)
    pe = np.arange(1, n + 1) / (n + 1)
    pt = _cdf(dist, xs)(xs)
    d = np.abs(pe - pt)
    i = int(d.argmax())
    krit = float(kstwo.ppf(1 - ALFA, n))
    return {"D": float(d[i]), "x_Dmaks": float(xs[i]), "kritis": krit, "kritis_asimtotik": 1.36 / math.sqrt(n),
            "lolos": float(d[i]) < krit, "P_emp": pe.tolist(), "P_teo": pt.tolist(), "x": xs.tolist()}


def uji_kecocokan():
    x = [e for _, e in deret()]
    return {d: {"chi2": uji_chi_kuadrat(d, x), "ks": uji_ks(d, x)} for d in PARAMETER}


def statistik_data():
    """Cs dan Ck data (bukan log) untuk syarat sebaran: Gumbel Cs ≈ 1,14, Ck ≈ 5,40
    [Literatur: Triatmodjo 2008, Hidrologi Terapan; belum di acuan]."""
    x = np.array([e for _, e in deret()])
    n = len(x)
    s = x.std(ddof=1)
    d = x - x.mean()
    cs = n * (d ** 3).sum() / ((n - 1) * (n - 2) * s ** 3)
    ck = n * n * (d ** 4).sum() / ((n - 1) * (n - 2) * (n - 3) * s ** 4)
    return {"cs": float(cs), "ck": float(ck)}


def banding_metode():
    """Muka air (m lokal) per T: Gumbel Yn-Sn, Gumbel momen, LP3 dua cara, penyedia (Gumbel tanpa koreksi)."""
    x_pen = [e for _, e in deret(koreksi_nol=False, buang_tidak_lengkap=False)]
    x = [e for _, e in deret()]
    return [{"T": T, "gumbel_yn": gumbel_yn_sn(x, T), "gumbel_momen": gumbel_momen(x, T), "lp3_k": lp3_k(x, T),
             "lp3_scipy": lp3_scipy(x, T), "penyedia": gumbel_yn_sn(x_pen, T)} for T in T_LP3]


PEIL_SETUJU = {"lantai": 12.85, "halaman": 12.05}  # disetujui Defsa 19 Nov 2026 (langkah 3.3)


def distribusi_terpilih():
    """Distribusi yang lolos dua uji; dari yang lolos dipilih Dmaks K-S terkecil. Untuk peil dipakai nilai
    terbesar di antara distribusi yang lolos (sikap konservatif; peil sudah disetujui berdasar Gumbel Yn-Sn)."""
    u = uji_kecocokan()
    lolos = [d for d in PARAMETER if u[d]["chi2"]["lolos"] and u[d]["ks"]["lolos"]]
    terbaik = min(lolos, key=lambda d: u[d]["ks"]["D"]) if lolos else None
    return {"lolos": lolos, "terbaik": terbaik}


def cek_peil():
    """Cek peil yang sudah disetujui terhadap tiap metode (lantai ≥ Q100 + 0,50; halaman ≥ Q50 dan ≥ Q50 + 0,15)."""
    tab = {r["T"]: r for r in banding_metode()}
    hasil = []
    for m in ("gumbel_yn", "gumbel_momen", "lp3_k", "penyedia"):
        q50, q100 = tab[50][m], tab[100][m]
        hasil.append({"metode": m, "q50": q50, "q100": q100,
                      "lantai_ok": PEIL_SETUJU["lantai"] >= q100 + JAGAAN["lantai"] - 1e-9,
                      "sisa_lantai": PEIL_SETUJU["lantai"] - q100 - JAGAAN["lantai"],
                      "halaman_ok": PEIL_SETUJU["halaman"] >= q50 - 1e-9,
                      "halaman_jagaan_ok": PEIL_SETUJU["halaman"] >= q50 + JAGAAN["halaman"] - 1e-9,
                      "sisa_halaman": PEIL_SETUJU["halaman"] - q50})
    return hasil



# ------------------------------------------------------------------ peil
JAGAAN = {"lantai": 0.50, "halaman": 0.15}  # [Asumsi: jagaan; tidak ada standar jagaan bangunan di acuan/]


def muka_air(T, cara="koreksi_yn"):
    return next(r[cara] for r in tabel_frekuensi() if r["T"] == T)


def opsi_peil():
    """Pilihan elevasi lantai dasar (dan utilitas vital) terhadap banjir rencana (m lokal)."""
    q50, q100 = muka_air(50), muka_air(100)
    maks = max(e for _, e in deret())
    return [
        {"opsi": "A", "dasar": "Arahan owner (surat 034, butir 2)", "banjir": None, "jagaan": None, "peil": 11.50},
        {"opsi": "B", "dasar": "TOR: lantai dasar +11,80", "banjir": None, "jagaan": None, "peil": 11.80},
        {"opsi": "C", "dasar": "Rekomendasi penyedia: Q50 + 0,30 (Q50 terkoreksi)", "banjir": q50, "jagaan": 0.30,
         "peil": q50 + 0.30},
        {"opsi": "D", "dasar": "Usulan: Q100 + 0,50 untuk fasilitas kategori IV [Asumsi]", "banjir": q100,
         "jagaan": JAGAAN["lantai"], "peil": math.ceil((q100 + JAGAAN["lantai"]) * 20) / 20},
        {"opsi": "-", "dasar": "Pembanding: maksimum tercatat 1990-2026 (terkoreksi)", "banjir": maks, "jagaan": None,
         "peil": None},
    ]


def peil_usulan():
    q50 = muka_air(50)
    lantai = next(o for o in opsi_peil() if o["opsi"] == "D")["peil"]
    halaman = math.ceil((q50 + JAGAAN["halaman"]) * 20) / 20
    return {"lantai": lantai, "utilitas": lantai, "halaman": halaman, "q50": q50, "q100": muka_air(100)}


# ------------------------------------------------------------------ topografi dan urugan
@lru_cache(maxsize=1)
def topografi():
    """TOR Lampiran C: grid 20 m × 15 m (m lokal). Kembalikan (xs, ys, z[y, x])."""
    teks = (AKAR / "00 Kerangka Acuan" / "TOR Owner.md").read_text(encoding="utf-8")
    bagian = teks[teks.index("## Lampiran C"):]
    baris = {}
    for b in bagian.splitlines():
        s = [c.strip() for c in b.strip().strip("|").split("|")]
        if len(s) == 9 and s[0][:2].strip().isdigit():
            baris[float(s[0].split()[0])] = [float(c.replace(",", ".")) for c in s[1:]]
    ys = sorted(baris)
    return np.arange(0, 141, 20.0), np.array(ys), np.array([baris[y] for y in ys])


def muka_tanah(x, y):
    from scipy.interpolate import RegularGridInterpolator

    xs, ys, z = topografi()
    f = RegularGridInterpolator((ys, xs), z)
    return f(np.column_stack([np.clip(np.ravel(y), 0, 90), np.clip(np.ravel(x), 0, 140)])).reshape(np.shape(x))


@lru_cache(maxsize=4)
def penurunan_titik(h_halaman, iterasi=3):
    """Penurunan total (primer + sekunder 50 th) per titik penyelidikan untuk urugan sampai h_halaman, dengan
    urugan tambahan sebesar penurunannya (iterasi; beban tambahan ikut dihitung). Model langkah 2.8.
    Kembalikan [(x, y, elev, penurunan, 3su)]."""
    import tahap2_penurunan_urugan as pu
    import tahap2_stratigrafi as st

    hasil = []
    asal = pu.ELEV_RENCANA
    try:
        for t in st.semua_titik():
            s = 0.0
            for _ in range(iterasi):
                pu.ELEV_RENCANA = h_halaman + s
                r = pu.hitung_titik(t)
                s = r["total"] if r["urug"] > 0 else 0.0
            hasil.append((t["x"], t["y"], t["elev"], s, pu.amblas(t)[1]))
    finally:
        pu.ELEV_RENCANA = asal
    return tuple(hasil)


def grid_urugan(h_halaman, langkah=1.0):
    """Tebal urugan padat per sel 1 m di daerah yang boleh diurug (persil - sempadan - rencana rumija);
    zona labil dibatasi 1,0 m di atas muka tanah (surat sempadan butir 4)."""
    from scipy.interpolate import griddata
    from shapely import contains_xy

    xs = np.arange(langkah / 2, 140, langkah)
    ys = np.arange(langkah / 2, 90, langkah)
    gx, gy = np.meshgrid(xs, ys)
    z = muka_tanah(gx, gy)
    boleh = tp.persil().difference(tp.ruang_sempadan()).difference(tp.rumija())
    m_boleh = contains_xy(boleh, gx, gy)
    m_labil = contains_xy(tp.zona_labil(), gx, gy)
    pt = penurunan_titik(h_halaman)
    p = np.array([[a[0], a[1]] for a in pt])
    nil = np.array([a[3] for a in pt])
    s = griddata(p, nil, (gx, gy), method="linear")
    s = np.where(np.isnan(s), griddata(p, nil, (gx, gy), method="nearest"), s)
    target = np.where(m_labil, np.minimum(h_halaman, z + 1.0), h_halaman)
    tebal = np.where(m_boleh, np.maximum(0.0, target - z), 0.0)
    kompensasi = np.where(tebal > 0, s, 0.0)
    return {"gx": gx, "gy": gy, "z": z, "tebal": tebal, "kompensasi": kompensasi, "luas_sel": langkah ** 2,
            "boleh": m_boleh, "labil": m_labil}


FAKTOR = {"padat_ke_asli": 1.15, "asli_ke_lepas": 1.25}  # [Asumsi: tanah merah laterit; literatur belum di acuan]


def volume_urugan(h_halaman):
    g = grid_urugan(h_halaman)
    a = g["luas_sel"]
    v_geo = float(g["tebal"].sum() * a)
    v_komp = float(g["kompensasi"].sum() * a)
    v_padat = v_geo + v_komp
    v_asli = v_padat * FAKTOR["padat_ke_asli"]
    isi = g["tebal"] > 0
    return {"halaman": h_halaman, "luas": float(isi.sum() * a), "v_geometri": v_geo, "v_kompensasi": v_komp,
            "v_padat": v_padat, "v_asli": v_asli, "v_lepas": v_asli * FAKTOR["asli_ke_lepas"],
            "tebal_maks": float((g["tebal"] + g["kompensasi"]).max()),
            "tebal_rata": float((g["tebal"] + g["kompensasi"])[isi].mean())}


def volume_prisma(h_halaman):
    """Cara kedua (cek silang volume geometri): grid 20 × 15 TOR, tebal di empat sudut sel dirata-rata; daerah
    sempadan dan rumija dikurangi dengan proporsi luas; tanpa batas zona labil dan tanpa kompensasi."""
    xs, ys, z = topografi()
    tebal = np.maximum(0.0, h_halaman - z)
    v = 0.0
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            v += (xs[i + 1] - xs[i]) * (ys[j + 1] - ys[j]) * tebal[j:j + 2, i:i + 2].mean()
    luas_boleh = tp.persil().difference(tp.ruang_sempadan()).difference(tp.rumija()).area
    return v * luas_boleh / (140 * 90)


def tahap_urugan():
    """Tinggi urugan tahap pertama yang aman: γH ≤ 3 su (FHWA NHI-06-088 Pers. 7-11, langkah 2.8)."""
    import tahap2_penurunan_urugan as pu

    pt = penurunan_titik(peil_usulan()["halaman"])
    h1 = [a[4] / pu.GAMMA_URUG for a in pt]
    return {"h1_min": min(h1), "h1_median": float(np.median(h1)), "t_pvd_bulan": pu.t_pvd(1.2) * 12,
            "t90_tanpa_pvd_tahun": pu.t90_tanpa_pvd(8.0)}


# ------------------------------------------------------------------ drainase
C_LIMPASAN = {"sebelum": 0.30, "sesudah": 0.70}  # [Asumsi: semak/kebun vs atap+perkerasan+taman]


@lru_cache(maxsize=1)
def hujan_harian():
    ws = openpyxl.load_workbook(DATA / "Data Hidrologi Banjir.xlsx", data_only=True)["Hujan Harian Maksimum"]
    hasil = []
    for r in ws.iter_rows(values_only=True):
        v = [x for x in r if x is not None]
        if len(v) >= 2 and isinstance(v[0], int) and 1980 < v[0] < 2100:
            hasil.append(float(v[1]))
    return tuple(hasil)


def retensi(T=10):
    """Volume tampungan agar limpasan tidak bertambah (PKKPR persyaratan 4):
    V = (C_sesudah - C_sebelum) × R24_T × A [Asumsi: pendekatan volume harian; rinci di DED]."""
    r = gumbel_yn_sn(list(hujan_harian()), T)
    a = tp.lahan_perencanaan().area
    return {"T": T, "R24": r, "luas": a, "volume": (C_LIMPASAN["sesudah"] - C_LIMPASAN["sebelum"]) * r / 1000 * a}


def hari_terhalang():
    """Hari per tahun muka air sungai di atas +9,70 (saluran rendah mulai tergenang): outlet gravitasi terhalang."""
    ws = openpyxl.load_workbook(DATA / "Data Hidrologi Banjir.xlsx", data_only=True)["Lama Genangan"]
    hasil = []
    for r in ws.iter_rows(values_only=True):
        v = [x for x in r if x is not None]
        if len(v) >= 3 and isinstance(v[0], int) and 1980 < v[0] < 2100:
            hasil.append((int(v[0]), float(v[1]), int(v[2])))
    return hasil


def _cetak_ringkas():
    for o in opsi_peil():
        print(o)
    print(peil_usulan())
    for h in (11.50, peil_usulan()["halaman"]):
        print({k: round(v, 2) for k, v in volume_urugan(h).items()}, "prisma", round(volume_prisma(h), 0))
    print(tahap_urugan())
    print(retensi(10), retensi(25))
    print([r for r in hari_terhalang() if r[2] > 0])


# ------------------------------------------------------------------ Excel
def fmt(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


def buat_excel(keluar=BERKAS):
    from openpyxl.styles import PatternFill

    from format_dokumen import AI, Lembar, set_font_bawaan

    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    pu_ = peil_usulan()
    v115, vh = volume_urugan(11.50), volume_urugan(pu_["halaman"])
    tu = tahap_urugan()
    hijau = PatternFill("solid", fgColor=AI)

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk peil, urugan, dan drainase (langkah 3.3)", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        "Sumber: Data Hidrologi Banjir (CV Hidro Tepian, Feb 2027), surat sempadan butir 6 (Q50 Balai +13,69 m dpl), "
        "TOR Lampiran C (topografi), langkah 2.8 (penurunan), langkah 3.2 (sempadan, zona labil, rumija).",
        "Datum: elevasi lokal = elevasi dpl - 1,840 (lembar Pos dan Datum). Papan duga 1990-2007 dikoreksi ke nol "
        "+3,500 (pengikatan ulang Mar 2008), bukan +3,150 arsip; tahun 1999 (data 6 bulan, musim banjir hilang) dibuang.",
        "Gumbel dua cara: faktor frekuensi Yn-Sn (cara penyedia, Yn dan Sn dihitung dari variat tereduksi) dan metode "
        "momen. Rumus belum ada dokumennya di acuan/ (Chow dkk. 1988; Gumbel 1958) [Literatur].",
        "Urugan: grid 1 m, muka tanah interpolasi bilinear TOR Lampiran C, tanpa urugan di ruang sempadan dan rencana "
        "rumija, zona labil maks 1,0 m; urugan tambahan = penurunan model 2.8 (iterasi beban). Cek silang cara prisma.",
        "Jagaan, koefisien limpasan, dan faktor kembang-susut berlabel [Asumsi] karena standarnya belum ada di acuan/.",
        "Gambar: '3.3 Gambar Peil dan Urugan.pdf' (GK-02).",
        "Rev B (LA.2, 19 Nov 2026): lembar 8 'LP3 dan Uji' menambah Log-Pearson III dua cara, uji Chi-kuadrat dan "
        "Smirnov-Kolmogorov, perbandingan metode, dan cek peil. " + LABEL_LA2,
    ])], rata=list("cl"))

    # 2 Hidrologi (rumus Excel)
    lb = Lembar(wb.create_sheet("Hidrologi"), 2, "Muka air maksimum tahunan dan koreksi datum",
                [8, 12, 10, 12, 12, 12, 12, 10, 10])
    lb.catatan(LABEL + " Kolom hijau rumus Excel: dpl = bacaan + nol koreksi; lokal = dpl - 1,840. Dipakai = 0 untuk "
               "tahun dengan data kurang dari 12 bulan.")
    data = []
    for tahun, alat, bacaan, nol, dpl, bulan in maksimum_tahunan():
        nol_k = NOL_UKUR_ULANG if alat.startswith("papan") else nol
        data.append([tahun, alat, bacaan, nol, nol_k, None, None, bulan, 1 if bulan >= 12 else 0])
    r0, r1, r2 = lb.tabel(["Tahun", "Alat", "Bacaan (m)", "Nol penyedia (m dpl)", "Nol koreksi (m dpl)",
                           "Elevasi koreksi (m dpl)", "Elevasi koreksi (m lokal)", "Bulan data", "Dipakai"], data,
                          rata=list("ccccccccc"), fmt=[None, None, "0.00", "0.000", "0.000", "0.00", "0.00", "0", "0"],
                          fill_kolom={5: AI, 6: AI})
    ws = lb.ws
    for r in range(r1, r2 + 1):
        ws[f"H{r}"] = f"=E{r}+G{r}"
        ws[f"I{r}"] = f"=H{r}{DPL_KE_LOKAL:+.3f}"
    rng_l, rng_d = f"Hidrologi!I{r1}:I{r2}", f"Hidrologi!K{r1}:K{r2}"

    # 3 Frekuensi
    x_kor = [e for _, e in deret()]
    yn, sn = yn_sn(len(x_kor))
    yn0, sn0 = yn_sn(len(deret(False, False)))
    lb = Lembar(wb.create_sheet("Frekuensi"), 3, "Analisis frekuensi Gumbel (dua cara)", [10, 12, 14, 14, 14, 14, 16])
    lb.catatan(LABEL + f" Statistik dihitung Excel dari lembar Hidrologi (Dipakai = 1). Yn = {yn:.4f}, Sn = {sn:.4f} "
               f"untuk n = {len(x_kor)} (penyedia n = 37: Yn {yn0:.4f}, Sn {sn0:.4f}).")
    a0, a1, a2 = lb.tabel(["Besaran", "Nilai", "Keterangan"], [
        ["n", None, "jumlah tahun dipakai"], ["Rata-rata (m)", None, "AVERAGEIF"],
        ["Simpangan baku (m)", None, "sampel"], ["Yn", round(yn, 4), "variat tereduksi rata-rata"],
        ["Sn", round(sn, 4), "simpangan baku variat tereduksi"],
    ], rata=list("lcl"), fmt=[None, "0.000", None], fill_kolom={1: AI})
    w3 = lb.ws
    w3[f"D{a1}"] = f"=SUM({rng_d})"
    w3[f"D{a1 + 1}"] = f"=SUMPRODUCT({rng_l},{rng_d})/D{a1}"
    w3[f"D{a1 + 2}"] = (f"=SQRT(SUMPRODUCT(({rng_l}-D{a1 + 1})^2,{rng_d})/(D{a1}-1))")
    lb.kosong()
    tab = tabel_frekuensi()
    b0, b1, b2 = lb.tabel(["T (tahun)", "Y_T", "Cara 1 Yn-Sn (m lokal)", "Cara 2 momen (m lokal)",
                           "Penyedia tanpa koreksi (m lokal)", "Python cara 1", "Selisih cara 1 - 2 (m)"],
                          [[r["T"], None, None, None, round(r["penyedia"], 3), round(r["koreksi_yn"], 3), None]
                           for r in tab], rata=list("ccccccc"),
                          fmt=["0", "0.0000", "0.000", "0.000", "0.000", "0.000", "0.000"],
                          fill_kolom={1: AI, 2: AI, 3: AI, 6: AI}, beku=False)
    for r in range(b1, b2 + 1):
        w3[f"D{r}"] = f"=-LN(-LN(1-1/C{r}))"
        w3[f"E{r}"] = f"=$D${a1 + 1}+$D${a1 + 2}*(D{r}-$D${a1 + 3})/$D${a1 + 4}"
        w3[f"F{r}"] = f"=$D${a1 + 1}-SQRT(6)/PI()*(0.5772+LN(LN(C{r}/(C{r}-1))))*$D${a1 + 2}"
        w3[f"I{r}"] = f"=E{r}-F{r}"
    lb.catatan(f"Q50 Balai = +13,69 m dpl = +{fmt(Q50_BALAI_DPL + DPL_KE_LOKAL)} lokal; cara 1 terkoreksi "
               f"+{fmt(muka_air(50))}. Maksimum tercatat terkoreksi +{fmt(max(x_kor))} (2003), di atas '+11,20' TOR.")

    # 4 Peil
    lb = Lembar(wb.create_sheet("Peil"), 4, "Pilihan peil lantai dasar dan utilitas vital", [6, 50, 16, 12, 14, 40])
    lb.catatan(LABEL + " Usulan D untuk keputusan Defsa. Jagaan 0,50 m [Asumsi]; standar banjir rencana fasilitas "
               "kesehatan belum ada di acuan/.")
    q50 = muka_air(50)
    lb.tabel(["Opsi", "Dasar", "Banjir acuan (m lokal)", "Jagaan (m)", "Peil (m lokal)", "Penilaian"], [
        [o["opsi"], o["dasar"], round(o["banjir"], 2) if o["banjir"] else None, o["jagaan"],
         round(o["peil"], 2) if o["peil"] else None,
         {"A": f"Di bawah Q50 (+{fmt(q50)}) dan banjir 2003: tergenang",
          "B": "Di bawah Q50 terkoreksi: tergenang pada Q50",
          "C": "Lolos Q50, tanpa cadangan untuk Q100 dan ketidakpastian datum",
          "D": "Usulan: lantai dasar, IGD, dan utilitas vital tetap kering pada Q100",
          "-": "Banjir 2003 setelah koreksi nol papan"}[o["opsi"]]]
        for o in opsi_peil()], rata=list("clcccl"), fmt=[None, None, "0.00", "0.00", "0.00", None], fill=AI)
    lb.kosong()
    lb.bagian("B", "Akibat usulan")
    ramp = (pu_["lantai"] - pu_["halaman"]) * 12
    lb.tabel(["No", "Butir", "Nilai", "Satuan", "Keterangan"], [
        [1, "Peil lantai dasar (lobi, IGD) dan lantai utilitas vital", pu_["lantai"], "m", "ganti LT1 template BIM (+11,80)"],
        [2, "Peil halaman dan jalan akses ambulans", pu_["halaman"], "m", "Q50 + 0,15 [Asumsi]"],
        [3, "Beda lantai dasar - halaman", pu_["lantai"] - pu_["halaman"], "m", "ramp landai"],
        [4, "Panjang ramp 1:12 (kursi roda)", ramp, "m", "atau drop-off ditinggikan di depan IGD"],
        [5, "Muka air sungai Q100 untuk uplift basement", pu_["q100"], "m", "tinggi tekan desain +11,20 (2.3) perlu "
         "ditinjau di Tahap 6"],
    ], rata=list("clccl"), fmt=[None, None, "0.00", None, None], fill_kolom={2: AI}, beku=False)

    # 5 Urugan
    lb = Lembar(wb.create_sheet("Urugan"), 5, "Volume, tahapan, dan waktu urugan halaman", [6, 52, 16, 16, 12])
    lb.catatan(LABEL + f" Faktor: padat ke asli {FAKTOR['padat_ke_asli']}, asli ke lepas {FAKTOR['asli_ke_lepas']} "
               "[Asumsi]. Cek silang volume geometri dengan cara prisma grid 20 × 15 (T-38).")
    lb.tabel(["No", "Butir", "Halaman +11,50 (owner)", f"Halaman +{fmt(pu_['halaman'])} (usulan)", "Satuan"], [
        [1, "Luas yang diurug (persil - sempadan - rumija)", v115["luas"], vh["luas"], "m²"],
        [2, "Volume geometri (sampai elevasi halaman)", v115["v_geometri"], vh["v_geometri"], "m³ padat"],
        [3, "Urugan tambahan kompensasi penurunan (model 2.8)", v115["v_kompensasi"], vh["v_kompensasi"], "m³ padat"],
        [4, "Volume padat total", v115["v_padat"], vh["v_padat"], "m³"],
        [5, "Volume asli di sumber", v115["v_asli"], vh["v_asli"], "m³"],
        [6, "Volume lepas (angkutan)", v115["v_lepas"], vh["v_lepas"], "m³"],
        [7, "Tebal urugan rata-rata termasuk kompensasi", v115["tebal_rata"], vh["tebal_rata"], "m"],
        [8, "Tebal urugan maksimum (utara, gambut)", v115["tebal_maks"], vh["tebal_maks"], "m"],
        [9, "Cek silang: volume geometri cara prisma", volume_prisma(11.50), volume_prisma(pu_["halaman"]), "m³"],
        [10, "Tanah merah tawaran owner", 22000, 22000, "m³"],
    ], rata=list("clccc"), fmt=[None, None, "#,##0.00", "#,##0.00", None], fill_kolom={2: AI, 3: AI})
    lb.kosong()
    lb.bagian("B", "Tahapan dan waktu")
    lb.tabel(["No", "Butir", "Nilai", "Satuan", "Dasar"], [
        [1, "Tinggi urugan tahap pertama aman (γH ≤ 3 su), minimum", tu["h1_min"], "m", "FHWA NHI-06-088 Pers. 7-11"],
        [2, "Tinggi urugan tahap pertama, median titik", tu["h1_median"], "m", "su desain 2.4"],
        [3, "Jumlah tahap untuk tebal maksimum", math.ceil(vh["tebal_maks"] / tu["h1_min"]), "tahap", "pembulatan ke atas"],
        [4, "t90 per tahap dengan PVD segitiga 1,2 m", tu["t_pvd_bulan"], "bulan", "langkah 2.8"],
        [5, "t90 tanpa PVD (U4 tebal 8 m)", tu["t90_tanpa_pvd_tahun"], "tahun", "langkah 2.8"],
        [6, "Waktu urugan yang diminta owner", 1.5, "bulan", "6 minggu: tidak mungkin tanpa amblas"],
    ], rata=list("clccl"), fmt=[None, None, "0.00", None, None], fill_kolom={2: AI}, beku=False)

    # 6 Drainase
    lb = Lembar(wb.create_sheet("Drainase"), 6, "Kolam retensi dan saluran pembuang (kasar)", [6, 52, 16, 12, 40])
    r10, r25 = retensi(10), retensi(25)
    terhalang = [r for r in hari_terhalang() if r[2] > 0]
    lb.catatan(LABEL + f" R24 Gumbel cara 1 dari {len(hujan_harian())} tahun (1997-2026). C sebelum "
               f"{C_LIMPASAN['sebelum']}, sesudah {C_LIMPASAN['sesudah']} [Asumsi]. Rinci di DED (Tahap 7).")
    lb.tabel(["No", "Butir", "Nilai", "Satuan", "Keterangan"], [
        [1, "R24 kala ulang 10 tahun", r10["R24"], "mm", "Gumbel cara 1"],
        [2, "R24 kala ulang 25 tahun", r25["R24"], "mm", "Gumbel cara 1"],
        [3, "Luas lahan perencanaan", r10["luas"], "m²", "langkah 3.2"],
        [4, "Volume retensi Q10 = (C2 - C1) R24 A", r10["volume"], "m³", "PKKPR persyaratan 4"],
        [5, "Volume retensi Q25", r25["volume"], "m³", "pembanding"],
        [6, "Hari terbanyak muka sungai > +9,70 (outlet terhalang)", max(r[2] for r in terhalang), "hari",
         f"{len(terhalang)} dari 19 tahun 2008-2026"],
        [7, "Muka air sungai Q50 di outlet", q50, "m lokal", "pintu klep + pompa banjir di outlet"],
    ], rata=list("clccl"), fmt=[None, None, "#,##0.00", None, None], fill_kolom={2: AI})

    # 7 Tanggapan owner
    lb = Lembar(wb.create_sheet("Tanggapan Owner"), 7, "Tanggapan atas arahan owner (peil dan urugan)",
                [6, 26, 22, 86])
    lb.catatan(LABEL)
    lb.tabel(["No", "Arahan", "Tanggapan", "Dasar dan angka"], [
        [1, "Butir 2: lantai dasar +11,50", "Tidak dapat dipenuhi",
         f"Q50 terkoreksi +{fmt(q50)} (sama dengan Q50 Balai), banjir 2003 +{fmt(max(x_kor))}. Usulan lantai dasar "
         f"+{fmt(pu_['lantai'])} (Q100 + 0,50), halaman +{fmt(pu_['halaman'])}; akses rata dicapai dengan ramp "
         f"1:12 ±{fmt(ramp, 1)} m atau drop-off ditinggikan."],
        [2, "Data MEP: gedung utilitas +11,30", "Tidak dapat dipenuhi",
         f"Mengacu banjir +11,20 (TOR). Utilitas vital (genset, trafo, panel, pompa kebakaran) minimal "
         f"+{fmt(pu_['utilitas'])} sesuai keputusan rapat no. 2."],
        [3, "Butir 3: urug 22.000 m³ tanah merah dalam 6 minggu", "Tidak dapat dipenuhi seperti diminta",
         f"Kebutuhan padat {fmt(v115['v_padat'], 0)} m³ (+11,50) s.d. {fmt(vh['v_padat'], 0)} m³ (usulan), "
         f"setara {fmt(v115['v_lepas'], 0)}-{fmt(vh['v_lepas'], 0)} m³ lepas. Urugan bertahap ±{fmt(tu['h1_min'], 1)} m "
         f"per tahap dengan PVD (±{fmt(tu['t_pvd_bulan'], 0)} bulan per tahap). Ruang sempadan tidak diurug; zona "
         "labil maks 1,0 m. Mutu tanah merah diuji dulu (Tahap 7 RKS)."],
    ], rata=list("clll"), fill=AI)

    lembar_lp3(wb, rng_l, rng_d)
    wb.save(keluar)
    return keluar


SEL_LP3 = {}  # alamat sel hasil Excel lembar 8, untuk dicocokkan dengan Python setelah dihitung ulang


def lembar_lp3(wb, rng_l, rng_d):
    """Lembar 8 (rev B, LA.2): Log-Pearson III, uji kecocokan, perbandingan metode, cek peil."""
    from format_dokumen import AI, Lembar

    x = [e for _, e in deret()]
    st = statistik_log(x)
    sd_ = statistik_data()
    u = uji_kecocokan()
    pil = distribusi_terpilih()
    bm = banding_metode()
    lb = Lembar(wb.create_sheet("LP3 dan Uji"), 8, "Log-Pearson III, uji kecocokan, dan cek peil (rev B)",
                [24, 13, 13, 14, 14, 14, 14, 34])
    lb.catatan(LABEL + " " + LABEL_LA2 + " Deret: maksimum tahunan terkoreksi (nol papan ≤ 2007 +3,500, 1999 dibuang, "
               f"n = {st['n']}, m lokal) dari lembar Hidrologi. Rumus LP3 dan uji kecocokan belum ada dokumennya di "
               "acuan/ [Literatur: Chow, Maidment, Mays 1988; Kite 1977; Soewarno 1995].")
    lb.bagian("A", "Statistik logaritma (rumus Excel dari lembar Hidrologi)")
    a0, a1, a2 = lb.tabel(["Besaran", "Excel", "Python", "Selisih"], [
        ["n", None, st["n"], None], ["Rata-rata log10 X", None, round(st["rata"], 6), None],
        ["Simpangan baku log10 X", None, round(st["sd"], 6), None],
        ["Skewness Cs (log10 X)", None, round(st["cs"], 6), None],
    ], rata=list("lccc"), fmt=[None, "0.000000", "0.000000", "0.000000"], fill_kolom={1: AI, 2: AI, 3: AI})
    ws = lb.ws
    n_, m_, s_, c_ = (f"$D${a1 + i}" for i in range(4))
    ws[f"D{a1}"] = f"=SUM({rng_d})"
    ws[f"D{a1 + 1}"] = f"=SUMPRODUCT(LOG10({rng_l}),{rng_d})/{n_}"
    ws[f"D{a1 + 2}"] = f"=SQRT(SUMPRODUCT((LOG10({rng_l})-{m_})^2,{rng_d})/({n_}-1))"
    ws[f"D{a1 + 3}"] = f"={n_}*SUMPRODUCT((LOG10({rng_l})-{m_})^3,{rng_d})/(({n_}-1)*({n_}-2)*{s_}^3)"
    for r in range(a1, a2 + 1):
        ws[f"F{r}"] = f"=D{r}-E{r}"
    for c in "DEF":
        ws[f"{c}{a1}"].number_format = "0"
    ws._print_rows = None  # lembar bertumpuk beberapa tabel: kepala tabel A tidak diulang di halaman lain
    SEL_LP3["statistik"] = [(f"D{a1 + i}", v) for i, v in enumerate((st["n"], st["rata"], st["sd"], st["cs"]))]
    lb.catatan("Cs = n Σ(y - ȳ)³ / ((n - 1)(n - 2) s³), y = log10 X. Data asli (bukan log): Cs = "
               f"{fmt(sd_['cs'], 3)}, Ck = {fmt(sd_['ck'], 3)}; syarat Gumbel Cs ≈ 1,14 dan Ck ≈ 5,40 tidak terpenuhi, "
               "LP3 tanpa syarat [Literatur: Triatmodjo 2008; belum di acuan].")
    lb.kosong()

    lb.bagian("B", "Log-Pearson III dua cara")
    b0, b1, b2 = lb.tabel(["T (tahun)", "z = Φ⁻¹(1 - 1/T)", "K (Kite)", "Cara a: faktor K (m lokal)",
                           "Cara b Excel GAMMA.INV (m lokal)", "Cara b Python pearson3 (m lokal)",
                           "Selisih a - b Python (%)", "Keterangan"],
                          [[T, None, None, None, None, round(lp3_scipy(x, T), 4), None,
                            "Pembanding" if T != 100 else "Banjir rencana lantai"] for T in T_LP3],
                          rata=list("cccccccl"), fmt=["0", "0.0000", "0.0000", "0.000", "0.000", "0.000", "0.000",
                                                         None],
                          fill_kolom={1: AI, 2: AI, 3: AI, 4: AI, 5: AI, 6: AI}, beku=False)
    for r in range(b1, b2 + 1):
        ws[f"D{r}"] = f"=_xlfn.NORM.S.INV(1-1/C{r})"
        k = f"({c_}/6)"
        ws[f"E{r}"] = (f"=D{r}+(D{r}^2-1)*{k}+(D{r}^3-6*D{r})*{k}^2/3-(D{r}^2-1)*{k}^3+D{r}*{k}^4+{k}^5/3")
        ws[f"F{r}"] = f"=10^({m_}+E{r}*{s_})"
        ws[f"G{r}"] = f"=10^({m_}-2*{s_}/{c_}+_xlfn.GAMMA.INV(1-1/C{r},4/{c_}^2,{s_}*{c_}/2))"
        ws[f"I{r}"] = f"=(F{r}/H{r}-1)*100"
    SEL_LP3["lp3"] = [(f"F{b1 + i}", lp3_k(x, T)) for i, T in enumerate(T_LP3)] + \
                     [(f"G{b1 + i}", lp3_scipy(x, T)) for i, T in enumerate(T_LP3)]
    lb.catatan("Cara a: log X_T = ȳ + K s, K pendekatan Kite (1977) dalam Chow dkk. (1988) Pers. 12.3.8, k = Cs/6. "
               "Cara b: kuantil eksak Pearson III (Cs > 0: ξ = ȳ - 2s/Cs, α = 4/Cs², β = s Cs/2, log X_T = ξ + "
               "Γ⁻¹(1 - 1/T; α, β)). Toleransi a - b 1 % (T-52).")
    lb.kosong()

    lb.bagian("C", "Uji kecocokan (α = 5 %, dihitung Python)")
    baris_c = []
    for d in PARAMETER:
        c2, ks = u[d]["chi2"], u[d]["ks"]
        baris_c.append([NAMA_DIST[d], c2["G"], c2["dk"], round(c2["chi2"], 3), round(c2["kritis"], 3),
                        round(ks["D"], 4), round(ks["kritis"], 4),
                        ("Diterima" if c2["lolos"] and ks["lolos"] else "Ditolak") +
                        f"; O = {'-'.join(map(str, c2['O']))}"])
    lb.tabel(["Distribusi", "Kelas G", "DK", "χ² hitung", "χ² kritis", "Dmaks K-S", "D kritis", "Hasil"], baris_c,
             rata=list("lcccccc" + "l"), fmt=[None, "0", "0", "0.000", "0.000", "0.0000", "0.0000", None],
             fill_kolom={i: AI for i in range(1, 8)}, beku=False)
    lb.catatan(f"Chi-kuadrat: G = 1 + 3,322 log n = {u['lp3']['chi2']['G']} kelas berpeluang sama (Ei = "
               f"{fmt(u['lp3']['chi2']['E'], 1)}), DK = G - R - 1 dengan R = 2 (Gumbel) atau 3 (LP3). K-S: P empiris "
               f"m/(n + 1), D kritis eksak (asimtotik 1,36/√n = {fmt(u['lp3']['ks']['kritis_asimtotik'], 4)}). "
               f"Semua distribusi diterima; Dmaks terkecil {NAMA_DIST[pil['terbaik']]}. Dengan n = {st['n']} daya "
               "uji rendah, jadi uji tidak dapat membedakan distribusi dengan tegas.")
    lb.kosong()

    from openpyxl.worksheet.pagebreak import Break

    ws.row_breaks.append(Break(id=lb.baris - 1))  # bagian D-F di halaman 2
    lb.bagian("D", "Perbandingan metode (m lokal)")
    lb.tabel(["T (tahun)", "Gumbel Yn-Sn (terkoreksi)", "Gumbel momen", "LP3 cara a", "LP3 cara b",
              "Penyedia (Gumbel tanpa koreksi)", "LP3 a - Gumbel Yn-Sn (m)", "Keterangan"],
             [[r["T"], r["gumbel_yn"], r["gumbel_momen"], r["lp3_k"], r["lp3_scipy"], r["penyedia"],
               r["lp3_k"] - r["gumbel_yn"],
               {25: "", 50: "Q50 Balai +11,85 (surat sempadan)", 100: "Dasar peil lantai",
                500: "Ekstrapolasi jauh (n = 36)"}[r["T"]]] for r in bm],
             rata=list("ccccccc" + "l"), fmt=["0"] + ["0.000"] * 6 + [None], fill_kolom={i: AI for i in range(1, 7)},
             beku=False)
    lb.kosong()

    lb.bagian("E", "Cek peil yang disetujui (lantai +12,85; halaman +12,05)")
    e0, e1, e2 = lb.tabel(["Metode", "Q50 (m lokal)", "Q100 (m lokal)", "Q100 + 0,50", "Peil lantai",
                           "Q50 + 0,15", "Peil halaman", "Status"],
                          [[{"gumbel_yn": "Gumbel Yn-Sn (dipakai)", "gumbel_momen": "Gumbel momen",
                             "lp3_k": "Log-Pearson III (cara a)", "penyedia": "Penyedia (tanpa koreksi)"}[c["metode"]],
                            c["q50"], c["q100"], None, PEIL_SETUJU["lantai"], None, PEIL_SETUJU["halaman"], None]
                           for c in cek_peil()],
                          rata=list("lccccccl"), fmt=[None] + ["0.000"] * 6 + [None],
                          fill_kolom={i: AI for i in range(1, 8)}, beku=False)
    for r in range(e1, e2 + 1):
        ws[f"F{r}"] = f"=E{r}+{JAGAAN['lantai']}"
        ws[f"H{r}"] = f"=D{r}+{JAGAAN['halaman']}"
        ws[f"J{r}"] = f'=IF(AND(G{r}>=F{r}-0.0005,I{r}>=H{r}-0.0005),"Memenuhi","Tidak memenuhi")'
    SEL_LP3["status"] = [f"J{r}" for r in range(e1, e2 + 1)]
    lb.kosong()
    lb.bagian("F", "Kesimpulan (draf LA.2)")
    for i, s in enumerate(kesimpulan_lp3()):
        lb.catatan(f"{i + 1}. {s}")
    return ws


def kesimpulan_lp3():
    x = [e for _, e in deret()]
    pil = distribusi_terpilih()
    cp = {c["metode"]: c for c in cek_peil()}
    g, l3 = cp["gumbel_yn"], cp["lp3_k"]
    sd_ = statistik_data()
    return [
        f"LP3 dua cara cocok: selisih faktor K (Kite) dan pearson3 eksak ≤ "
        f"{fmt(max(abs(lp3_k(x, T) / lp3_scipy(x, T) - 1) for T in T_LP3) * 100, 3)} % (toleransi 1 %, T-52).",
        f"Chi-kuadrat dan Smirnov-Kolmogorov menerima ketiga distribusi ({', '.join(NAMA_DIST[d] for d in pil['lolos'])}); "
        f"Dmaks terkecil {NAMA_DIST[pil['terbaik']]}. Syarat Cs-Ck Gumbel tidak terpenuhi (Cs {fmt(sd_['cs'], 2)}, "
        f"Ck {fmt(sd_['ck'], 2)}), sehingga menurut kriteria parameter statistik LP3 lebih sesuai.",
        f"Distribusi yang dipakai untuk peil tetap Gumbel Yn-Sn: lolos dua uji, Dmaks terkecil, Q50 sama dengan "
        f"Q50 Balai, dan memberi muka air tertinggi. LP3 lebih rendah: Q100 +{fmt(l3['q100'])} vs +{fmt(g['q100'])} "
        f"({fmt(l3['q100'] - g['q100'])} m), Q50 +{fmt(l3['q50'])} vs +{fmt(g['q50'])}.",
        f"Peil lantai +{fmt(PEIL_SETUJU['lantai'])} ≥ Q100 + 0,50 untuk semua metode (sisa terkecil "
        f"{fmt(g['sisa_lantai'])} m pada Gumbel Yn-Sn). Halaman +{fmt(PEIL_SETUJU['halaman'])} ≥ Q50 + 0,15 untuk "
        f"semua metode (sisa ≥ {fmt(min(c['sisa_halaman'] for c in cp.values()))} m di atas Q50). Peil tidak diubah.",
        f"Bila Defsa memilih LP3, peil minimum turun ke Q100 + 0,50 = +{fmt(l3['q100'] + 0.5)}; tidak diusulkan "
        "karena n = 36 dan perbedaan metode pada Q100 ±0,5 m; cadangan ini menutup ketidakpastian datum dan metode.",
    ]


# ------------------------------------------------------------------ gambar GK-02 (CAD asli)
POT_X = 70.0  # potongan A-A utara-selatan di x = 70 m
POT_Y0 = -95.0  # letak potongan di model space (m)
V_EKS = 5.0  # pembesaran vertikal potongan


def _y_pot(elev):
    return POT_Y0 + (elev - 4.0) * V_EKS


def gambar_cad(status=None):
    from contourpy import contour_generator

    from cad_lembar import STATUS_SETUJU, Gambar

    pu_ = peil_usulan()
    h = pu_["halaman"]
    g_ = grid_urugan(h)
    vh = volume_urugan(h)
    dwg = KELUAR / "Gambar" / "DWG" / "GK-02 Peil dan Urugan.dwg"
    png = KELUAR / "Gambar" / "GK-02 Peil dan Urugan.png"
    with Gambar(750) as g:
        # zona tanpa urugan dan zona labil
        g.layer("C-SEMPADAN", 3, 0.25)
        g.arsir(list(tp.ruang_sempadan().exterior.coords)[:-1], "C-SEMPADAN", pola="DOTS", skala_pola=0.6)
        g.legenda_tambah("arsir", "Ruang sempadan: tanpa urugan", pola="DOTS", skala_pola=0.6)
        g.layer("C-LABIL", 1, 0.25)
        g.arsir(list(tp.zona_labil().exterior.coords)[:-1], "C-LABIL", pola="ANSI31", skala_pola=1.2)
        g.legenda_tambah("arsir", "Zona labil: urugan maks 1,0 m di atas muka tanah", pola="ANSI31", skala_pola=1.2)
        rj = tp.rumija()
        g.layer("C-RUMIJA", 8, 0.25)
        for geom in getattr(rj, "geoms", [rj]):
            g.arsir(list(geom.exterior.coords)[:-1], "C-RUMIJA", pola="ANSI37", skala_pola=0.8)
        g.legenda_tambah("arsir", "Rencana rumija: tanpa urugan", pola="ANSI37", skala_pola=0.8)
        # kontur tebal urugan total (termasuk kompensasi penurunan)
        tebal = np.where(g_["tebal"] > 0, g_["tebal"] + g_["kompensasi"], np.nan)
        g.layer("C-KONTUR-URUG", 7, 0.35, "DASHED")
        gen = contour_generator(g_["gx"], g_["gy"], np.ma.masked_invalid(tebal))
        xs_, ys_, _ = topografi()
        kotak_teks = [(min(max(x_, 2.5), 132.5) - 0.8, y_ - 2.8, min(max(x_, 2.5), 132.5) + 6.0, y_ + 2.6)
                      for x_ in xs_ for y_ in ys_]

        def bebas(pt):
            return not any(k[0] <= pt[0] <= k[2] and k[1] <= pt[1] <= k[3] for k in kotak_teks)

        for lv in (2.0, 3.0, 4.0, 5.0):
            for seg in gen.lines(lv):
                if len(seg) < 4:
                    continue
                potong, cur = [], []
                for pt in seg[::2]:  # garis kontur diputus di sekitar teks titik tinggi
                    if bebas(pt):
                        cur.append(tuple(pt))
                    elif cur:
                        potong.append(cur)
                        cur = []
                if cur:
                    potong.append(cur)
                for c_ in potong:
                    if len(c_) > 1:
                        g.pline(c_, "C-KONTUR-URUG")
                kand = [pt for pt in seg if all(bebas((pt[0] + dx, pt[1] + dy)) for dx in (0, 1, 2.5, 4.5) for dy in (0.5, 2.0))
                        and abs(pt[0] - POT_X) > 8 and 8 < pt[0] < 130]
                if kand:
                    m = kand[len(kand) // 2]
                    g.teks((m[0] + 0.8, m[1] + 1.4), f"{lv:.0f},0 M", "C-KONTUR-URUG", 1.5)
        g.legenda_tambah("garis", "Kontur tebal urugan padat termasuk kompensasi penurunan", garis="DASHED", tebal=0.35)
        # titik tinggi eksisting / rencana di grid TOR
        g.layer("C-ELEVASI", 7, 0.18)
        xs, ys, z = topografi()
        for j, yy in enumerate(ys):
            for i, xx in enumerate(xs):
                ax, ay = min(max(xx, 2.5), 132.5), yy
                if yy >= 88 or yy <= 0 or ay - 3.0 < tp.kedalaman_sempadan(ax):
                    continue
                labil = tp.zona_labil().contains(tp.box(ax - .01, ay - .01, ax + .01, ay + .01))
                rencana = min(h, z[j, i] + 1.0) if labil else h
                g.cmd("insert", {"name": g.blok_silang(1.0 * 750 / 1000), "at": g.mm((ax, ay))})
                g.teks((ax + 1.0, ay + 0.9), f"+{z[j, i]:.2f}".replace(".", ","), "C-ELEVASI", 1.4)
                g.teks((ax + 1.0, ay - 2.1), f"+{rencana:.2f}".replace(".", ","), "C-ELEVASI", 1.4, tebal=True)
        # persil dan garis potongan
        g.layer("C-PERSIL", 7, 0.7, "PHANTOM")
        g.pline([(0, 0), (140, 0), (140, 90), (0, 90)], "C-PERSIL", tutup=True)
        g.layer("C-POTONGAN", 7, 0.5, "DASHDOT")
        g.pline([(POT_X, -4), (POT_X, 94)], "C-POTONGAN")
        g.teks((POT_X + 1.5, 91.5), "A", "C-POTONGAN", 3.0, tebal=True)
        g.teks((POT_X + 1, -8), "A", "C-POTONGAN", 3.0, tebal=True)
        g.titik_tinggi((0, 0), "BM-1 +10,000", teks_at=(-21, -10.5))
        g.pline([(-0.7, -0.7), (-5.2, -0.7), (-8, -9.3), (-11.5, -9.3)], "C-TEKS")
        g.teks((35, 94.5), "JALAN KOLEKTOR", "C-TEKS", 2.2, j="MC", tebal=True)
        g.teks((70, -14), "SUNGAI BATANGHARI", "C-TEKS", 2.6, j="MC", tebal=True)

        # potongan A-A (x = 70), vertikal dibesarkan 5 kali
        yy_ = np.linspace(0, 90, 91)
        zt = muka_tanah(np.full_like(yy_, POT_X), yy_)
        g.layer("C-POT-TANAH", 7, 0.5)
        g.pline([(y, _y_pot(e)) for y, e in zip(yy_, zt)], "C-POT-TANAH")
        kol = int(POT_X)
        tb = g_["tebal"][:, kol] + g_["kompensasi"][:, kol]
        yc = g_["gy"][:, kol]
        g.layer("C-POT-URUG", 7, 0.35)
        zc = muka_tanah(np.full_like(yc, POT_X), yc)
        atas = [(y, _y_pot(z_ + t0)) for y, z_, t0, t_ in zip(yc, zc, g_["tebal"][:, kol], tb) if t_ > 0]
        if atas:
            bawah = [(y, _y_pot(float(muka_tanah(np.array([POT_X]), np.array([y]))[0]) - k))
                     for y, k in zip(yc, g_["kompensasi"][:, kol]) if k > 0 or True][::-1]
            bawah = [(y, b) for (y, b) in bawah if atas[0][0] <= y <= atas[-1][0]]
            g.arsir(atas + bawah, "C-POT-URUG", pola="ANSI32", skala_pola=1.0)
        g.legenda_tambah("arsir", "Urugan (potongan), termasuk kompensasi penurunan", pola="ANSI32", skala_pola=1.0)
        g.layer("C-POT-AIR", 7, 0.25, "HIDDEN")
        for nama, el in (("Q100", pu_["q100"]), ("Q50", pu_["q50"])):
            g.pline([(-4.5, _y_pot(el)), (95, _y_pot(el))], "C-POT-AIR")
            g.teks((96, _y_pot(el) - 0.6), f"{nama} +{el:.2f}".replace(".", ","), "C-POT-AIR", 1.6)
        g.layer("C-POT-PEIL", 7, 0.5)
        g.pline([(30, _y_pot(pu_["lantai"])), (60, _y_pot(pu_["lantai"]))], "C-POT-PEIL")
        g.teks((30, _y_pot(pu_["lantai"]) + 1.0), f"PEIL LANTAI DASAR +{pu_['lantai']:.2f}".replace(".", ","),
               "C-POT-PEIL", 1.8, tebal=True)
        g.teks((-3, _y_pot(13.75)), f"HALAMAN +{h:.2f}".replace(".", ","), "C-POT-PEIL", 1.8, tebal=True)
        g.pline([(10.5, _y_pot(13.6)), (16, _y_pot(h))], "C-POT-PEIL", tebal=0.18)
        # skala elevasi
        g.layer("C-POT-SKALA", 7, 0.18)
        g.pline([(-6, _y_pot(6)), (-6, _y_pot(14))], "C-POT-SKALA")
        for el in range(6, 15):
            g.pline([(-6.8, _y_pot(el)), (-6, _y_pot(el))], "C-POT-SKALA")
            g.teks((-7.5, _y_pot(el)), f"+{el},00", "C-POT-SKALA", 1.4, j="MR")
        g.teks((0, _y_pot(5.2)), "SELATAN (TEBING)", "C-POT-SKALA", 1.6)
        g.teks((90, _y_pot(5.2)), "UTARA (JALAN)", "C-POT-SKALA", 1.6, j="R")

        g.lembar("GK-02", "Peil dan urugan", "1:750", pusat=(76, 40), vp=((24, 128), (331, 283)),
                 subjudul="TOR Lampiran C; Data Hidrologi Banjir (datum dikoreksi); penurunan langkah 2.8; batas langkah 3.2",
                 status=status or STATUS_SETUJU,
                 catatan=[
                     f"Peil lantai dasar dan utilitas vital +{fmt(pu_['lantai'])} (Q100 +{fmt(pu_['q100'])} + 0,50).",
                     f"Halaman +{fmt(h)} (Q50 +{fmt(pu_['q50'])} + 0,15); ramp 1:12 ke lantai dasar.",
                     f"Urugan padat {fmt(vh['v_padat'], 0)} m³ termasuk kompensasi penurunan {fmt(vh['v_kompensasi'], 0)} m³.",
                     "Urugan bertahap maks ±1,0 m per tahap dengan PVD; dipantau pelat penurunan.",
                     "Titik tinggi: atas eksisting (TOR Lamp. C), bawah rencana (tebal).",
                 ])
        g.viewport_tambahan((24, 52), (331, 118), pusat=(45, _y_pot(10.0)), judul="Potongan A-A",
                            teks_skala="SKALA H 1:750, V 1:150")
        g.skala_grafis(205, 22, 50)
        g.panah_utara(318, 262, 10)
        g.simpan(dwg, PDF, png)
    return dwg


def buat():
    buat_excel()
    gambar_cad()
    return BERKAS, PDF

def cek_excel(path=BERKAS):
    """Cocokkan nilai Excel lembar 8 (setelah dihitung ulang di Excel) dengan Python. Kembalikan selisih mutlak maks
    per kelompok; None bila nilai cache Excel belum ada."""
    ws = openpyxl.load_workbook(path, data_only=True)["LP3 dan Uji"]
    hasil = {}
    for kel in ("statistik", "lp3"):
        nilai = [(ws[a].value, v) for a, v in SEL_LP3[kel]]
        hasil[kel] = None if any(e is None for e, _ in nilai) else max(abs(e - v) for e, v in nilai)
    hasil["status"] = [ws[a].value for a in SEL_LP3["status"]]
    return hasil


if __name__ == "__main__":
    import sys

    if "--excel" in sys.argv:  # rev B (LA.2): bangun ulang Excel saja, hitung di Excel, cocokkan dengan Python
        from format_dokumen import hitung_ulang_excel

        buat_excel()
        print("hitung ulang Excel:", hitung_ulang_excel(BERKAS))
        print("cek Excel vs Python:", cek_excel())
        sys.exit()
    x0 = [e for _, e in deret(False, False)]
    x1 = [e for _, e in deret()]
    print("n penyedia", len(x0), "rata", round(np.mean(x0), 3), "sd", round(np.std(x0, ddof=1), 3), yn_sn(len(x0)))
    print("n koreksi", len(x1), "rata", round(np.mean(x1), 3), "sd", round(np.std(x1, ddof=1), 3), yn_sn(len(x1)))
    for r in tabel_frekuensi():
        print({k: round(v, 3) for k, v in r.items()})
    print("Q50 Balai lokal", round(Q50_BALAI_DPL + DPL_KE_LOKAL, 2), "maks 1990-2026 koreksi", round(max(x1), 2))
    for r in banding_metode():
        print({k: round(v, 3) for k, v in r.items()})
    print(uji_kecocokan()["lp3"]["ks"]["D"], distribusi_terpilih(), *kesimpulan_lp3(), sep="\n")
    _cetak_ringkas()
