"""Tahap 4 langkah 4.2: pembebanan menurut SNI 1727:2020 dan SNI 1726:2019.

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (20 Nov 2026); draf, menunggu persetujuan
Defsa; disetujui Defsa 20 Nov 2026. Kunci jawaban tidak dibuka.

Acuan (halaman cetak):
SNI 1727:2020: Pasal 3.1.2-3.1.3 hal. 20 (beban mati, peralatan tetap); Tabel 4.3-1 hal. 25-28 (beban hidup); Pasal
4.3.2 hal. 28 (partisi >= 0,72 kPa); Pasal 4.6.3 hal. 30 (impak mesin 20 %); Pasal 4.7 hal. 31-32 (reduksi); Pasal
4.8.2 hal. 33 (atap); Pasal 4.11 hal. 35 (helipad); Pasal 8.3 hal. 95 (hujan R = 0,0098 (ds + dh)); Pasal 26.5.1
hal. 107 (V dari Buku Peta Angin Indonesia, belum ada di acuan/); Tabel 26.6-1 hal. 108 (Kd 0,85); Tabel 26.10-1
hal. 114 (Kz); Pasal 26.11.1 hal. 115 (G 0,85); Gambar 27.3-1 hal. 128-129 (Cp dinding); Tabel C3.1-1 hal. 277-278
(berat komponen); Tabel C3.1-2 hal. 279-281 (densitas; beton bertulang batu 23,6 kN/m³).
SNI 1726:2019: Pasal 4.2.2.1 dan 4.2.2.3 hal. 25-26 (kombinasi); Pasal 7.3.4.2 hal. 64 (ρ); Pasal 7.4.2.2 hal. 65
(Ev = 0,2 SDS D); Pasal 7.7.2 hal. 68 (berat seismik efektif); Pasal 7.8.1.1 hal. 69-70 (Cs); Tabel 17 dan Pasal
7.8.2.1 hal. 72 (Cu, Ta); Pasal 7.8.3 hal. 73 (distribusi vertikal). Spektrum: langkah 4.1 opsi (a) (SDS 0,386, SD1
0,459), dipilih Defsa 20 Nov 2026.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_telaah as tl  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "04 Struktur Atas"
BERKAS = KELUAR / "4.2 Pembebanan.xlsx"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
STATUS = "disetujui Defsa 20 Nov 2026"

# ------------------------------------------------------------------ parameter
GAMMA_C = 23.6           # kN/m³ beton bertulang agregat batu, Tabel C3.1-2
SDS, SD1 = 0.386, 0.459  # 4.1 opsi (a)
R, OMEGA0, CD, IE = 7.0, 2.5, 5.5, 1.5   # sistem ganda (3.6, Tabel 12); Ie kategori IV (Tabel 4)
CT, X_TA = 0.0488, 0.75  # Tabel 18 "semua sistem struktur lainnya"
CU = 1.4                 # Tabel 17, SD1 >= 0,4
RHO = 1.3                # Pasal 7.3.4.2: KDS D, sementara sampai syarat a/b diperiksa di 4.3
LEVEL = {"LT1": 12.85, "LT2": 17.35, "LT3": 21.85, "LT4": 26.05, "LT5": 30.25, "LT6": 34.45, "ATAP": 38.65}
GRID_X = [12.0 + 8.0 * i for i in range(10)]
GRID_Y = [27.0 + 8.0 * j for j in range(7)]
PELAT, BALOK_B, BALOK_H = 0.200, 0.350, 0.600          # m, pra-dimensi 3.6
KOLOM_POD, KOLOM_MEN, DINDING_T = 0.750, 0.650, 0.350  # m
FAKTOR_BUKAAN_DINDING = 0.85                           # [Asumsi] pintu pada dinding inti

# ------------------------------------------------------------------ wilayah lantai (m lokal)
PODIUM = box(12, 27, 84, 75)
MENARA = box(20, 27, 84, 51)
V1 = box(36, 51, 84, 75)                 # LT3 utara tidak dibangun (V1, 3.8); atap LT2 +21,85 (Data MEP)
VOID_LT2 = box(36, 51, 62, 75)           # void dan taman dalam LT2 (zonasi 3.4)
LT3 = PODIUM.difference(V1)
ATAP_LT3_BARAT = LT3.difference(MENARA)
HELIDEK = box(52 - 33.3 / 2, 39 - 33.3 / 2, 52 + 33.3 / 2, 39 + 33.3 / 2)  # 33,3 m (LA.4), pusat menara [Asumsi]

# ------------------------------------------------------------------ beban mati tambahan (kPa), Tabel C3.1-1
SIDL = {
    "keramik": (1.10, "Keramik 19 mm di atas spesi 25 mm (Tabel C3.1-1 hal. 278)"),
    "plafon": (0.17, "Rangka baja gantung 0,10 + papan gipsum 9 mm 9 × 0,008 (Tabel C3.1-1 hal. 277)"),
    "partisi": (1.00, "Partisi bata ringan/gipsum [Asumsi]; >= 0,72 kPa Pasal 4.3.2 hal. 28 dan >= 0,48 Pasal 7.7.2"),
    "screed_atap": (1.15, "Screed kemiringan beton 50 mm × 0,023/mm (Tabel C3.1-1 hal. 277)"),
    "kedap_atap": (0.07, "Membran bitumen permukaan halus (Tabel C3.1-1 hal. 277)"),
    "rangka_atap_sementara": (0.40, "Atap sementara LT4 tahap 1: baja ringan + penutup metal [Asumsi]"),
    "dek_helipad": (1.00, "Dek helipad baja + pelat aluminium [Asumsi; desain dek menyusul]"),
}
# beban gantung MEP per zona (Data Beban MEP Rinci lembar 8); minimal 0,19 duct (Tabel C3.1-1)
GANTUNG = {"podium": 0.50, "AHU": 0.80, "menara": 0.35, "atap": 0.30}
DINDING_LUAR = {  # kPa bidang dinding
    "bata": (2.78 + 2 * 0.24, "Bata merah 150 mm: interpolasi 102/203 mm 1,87/3,78 + plester 2 × 0,24 (Tabel C3.1-1 "
                              "hal. 278 dan catatan a)"),
    "kaca": (0.38, "Jendela kaca, kusen, dan sash (Tabel C3.1-1 hal. 278)"),
    "fasad": (0.50, "Lapis fasad louver aluminium/ACP dan rangka [Asumsi; dirinci di 4.9]"),
}
BUKAAN = 0.35   # porsi bukaan fasad (V4, 3.11)
PARAPET = 1.2   # m [Asumsi]

# ------------------------------------------------------------------ beban hidup (Tabel 4.3-1 hal. 25-28)
HIDUP = [  # (zona, lantai, Lo kPa, terpusat kN, reduksi?, sumber)
    ("Ruang operasi, ICU, laboratorium, CSSD", "LT2", 2.87, 4.45, "Ya (4.7.2)", "Rumah sakit: ruang operasi, laboratorium"),
    ("Kebidanan, hemodialisis, rawat", "LT2", 1.92, 4.45, "Ya (4.7.2)", "Rumah sakit: ruang pasien"),
    ("Koridor di atas lantai pertama", "LT2-LT6", 3.83, 4.45, "Ya (4.7.2)", "Rumah sakit: koridor di atas lantai pertama"),
    ("Administrasi (kantor)", "LT3", 2.40, 8.90, "Ya (4.7.2)", "Gedung perkantoran: kantor"),
    ("Aula dan diklat (kursi dapat dipindah)", "LT3", 4.79, 0.0, "Tidak (4.7.5)", "Ruang pertemuan: kursi dapat dipindahkan"),
    ("Ruang AHU dan mesin", "LT3", 4.79, 0.0, "Tidak [Asumsi]",
     "Tidak ada di Tabel 4.3-1 (Pasal 4.2): disamakan ruang pertemuan 4,79 [Asumsi]; berat alat sebagai beban mati"),
    ("Rawat inap (ruang pasien)", "LT4-LT6", 1.92, 4.45, "Ya (4.7.2)", "Rumah sakit: ruang pasien"),
    ("Tangga dan jalan keluar", "semua", 4.79, 1.33, "Ya (4.7.2)", "Tangga dan jalan keluar"),
    ("Atap datar (atap LT3 barat, atap sementara)", "LT4", 0.96, 1.33, "Ya (4.8.2)", "Atap datar"),
    ("Atap podium utara (area alat, pemeliharaan)", "LT3", 0.96, 1.33, "Ya (4.8.2)",
     "Atap datar; alat sebagai beban mati (Pasal 3.1.3); jalur pemeliharaan 1,92 bila ada"),
    ("Helipad (MTOW AW139 66,7 kN > 13,35 kN)", "ATAP", 2.87, 13.35, "Tidak (4.11.1)", "Helipad"),
    ("Parkir mobil penumpang (gedung utilitas)", "GU LT2-LT4", 1.92, 13.35, "Tidak (4.7.4)", "Garasi mobil penumpang"),
]
AW139_KG = 6800.0


# ------------------------------------------------------------------ alat MEP per lantai
def alat_per_lantai():
    """Berat operasi alat (kN) per bidang lantai (Data Beban MEP Rinci, berat operasi; Pasal 3.1.3)."""
    a = tl.ringkas()["atap"]["jumlah"]
    return {
        "LT2": [("M-14 AHU kebidanan/lab", 2 * 18.1), ("C-01/C-02 sterilisator, cuci", 2 * 18.1 + 2 * 8.8),
                ("R-07 X-ray gantung pelat LT2", 2 * 3.4)],
        "LT3": [("M-10..M-12 AHU OK/ICU/CSSD", 4 * 31.4 + 4 * 26.0 + 3 * 20.6),
                ("O-01..O-03 lampu dan pendant gantung pelat LT3", 4 * 1.8 + 8 * 2.2 + 12 * 1.5),
                ("Atap podium utara: chiller, tangki 210 m³, pompa", a)],
        "LT4": [("M-05 VRF atap LT3 barat", 6 * 3.2), ("M-15 AHU rawat inap", 2 * 19.6)],
        "LT5": [("M-15 AHU rawat inap", 2 * 19.6)],
        "LT6": [("M-15 AHU rawat inap", 2 * 19.6)],
        "ATAP": [("M-06 kipas buang", 6 * 1.5)],
    }


# ------------------------------------------------------------------ geometri dan berat unsur
def panjang_grid_di(wil):
    """Panjang garis grid (balok) di dalam wilayah (m)."""
    from shapely.geometry import LineString
    tot = 0.0
    for x in GRID_X:
        tot += LineString([(x, 0), (x, 200)]).intersection(wil.buffer(1e-6)).length
    for y in GRID_Y:
        tot += LineString([(0, y), (200, y)]).intersection(wil.buffer(1e-6)).length
    return tot


def titik_kolom(wil):
    """Titik grid di dalam atau di tepi wilayah."""
    from shapely.geometry import Point
    w = wil.buffer(0.01)
    return [(x, y) for x in GRID_X for y in GRID_Y if w.contains(Point(x, y))]


INTI = [  # (nama, keliling m, puncak)
    ("Tangga x22 y39", 20.0, "ATAP"), ("Tangga x46 y39", 20.0, "ATAP"), ("Tangga x70 y39", 20.0, "ATAP"),
    ("Tangga x22 y63", 20.0, "LT4"), ("Tangga x46 y63", 20.0, "LT3"), ("Tangga x70 y63", 20.0, "LT3"),
    ("Inti lif x50-58 y35-43", 32.0, "ATAP"),
]
URUT = ["LT1", "LT2", "LT3", "LT4", "LT5", "LT6", "ATAP"]


def tingkat(konfig="K2"):
    """Daftar tingkat di atas LT1 dengan wilayah lantai dan atap. K1: tahap 1 (menara s.d. atap sementara di atas LT4,
    elevasi +30,25 tanpa pelat); K2: akhir (6 lantai + helipad)."""
    t = [
        {"lv": "LT2", "lantai": PODIUM.difference(VOID_LT2), "atap": None, "kolom_bawah": (PODIUM, KOLOM_POD)},
        {"lv": "LT3", "lantai": LT3, "atap": V1, "kolom_bawah": (PODIUM, KOLOM_POD)},
        {"lv": "LT4", "lantai": MENARA, "atap": ATAP_LT3_BARAT, "kolom_bawah": (LT3, KOLOM_POD)},
    ]
    if konfig == "K1":
        t.append({"lv": "LT5", "lantai": None, "atap": None, "atap_ringan": MENARA, "kolom_bawah": (MENARA, KOLOM_MEN)})
    else:
        t += [{"lv": "LT5", "lantai": MENARA, "atap": None, "kolom_bawah": (MENARA, KOLOM_MEN)},
              {"lv": "LT6", "lantai": MENARA, "atap": None, "kolom_bawah": (MENARA, KOLOM_MEN)},
              {"lv": "ATAP", "lantai": None, "atap": MENARA, "helidek": True, "kolom_bawah": (MENARA, KOLOM_MEN)}]
    return t


def keliling(wil):
    return wil.exterior.length if wil.geom_type == "Polygon" else sum(g.exterior.length for g in wil.geoms)


def berat_tingkat(konfig="K2"):
    """Berat seismik efektif per tingkat (kN), dipecah per komponen (Pasal 7.7.2)."""
    tk = tingkat(konfig)
    alat = alat_per_lantai()
    hasil = []
    for i, t in enumerate(tk):
        lv = t["lv"]
        h_bawah = LEVEL[lv] - LEVEL[URUT[URUT.index(lv) - 1]]
        h_atas = (LEVEL[tk[i + 1]["lv"]] - LEVEL[lv]) if i + 1 < len(tk) else 0.0
        lantai = t.get("lantai")
        atap = t.get("atap")
        bidang = unary_union([g for g in (lantai, atap) if g is not None]) if (lantai or atap) else None
        a_lantai = lantai.area if lantai is not None else 0.0
        a_atap = atap.area if atap is not None else 0.0
        a = a_lantai + a_atap
        # pelat dan balok
        pelat = GAMMA_C * PELAT * a
        balok = GAMMA_C * BALOK_B * (BALOK_H - PELAT) * (panjang_grid_di(bidang) if bidang is not None else 0.0)
        # kolom: setengah tingkat bawah + setengah tingkat atas
        wil_b, ukuran_b = t["kolom_bawah"]
        kol_b = len(titik_kolom(wil_b)) * GAMMA_C * ukuran_b ** 2 * h_bawah / 2
        kol_a = 0.0
        if i + 1 < len(tk):
            wil_a, ukuran_a = tk[i + 1]["kolom_bawah"]
            kol_a = len(titik_kolom(wil_a)) * GAMMA_C * ukuran_a ** 2 * h_atas / 2
        # dinding inti
        din = 0.0
        for _, kel, puncak in INTI:
            top = LEVEL[puncak] if konfig == "K2" else min(LEVEL[puncak], LEVEL["LT5"])
            for h, ada in ((h_bawah, LEVEL[lv] <= top), (h_atas, LEVEL[lv] + h_atas <= top + 1e-6 and h_atas > 0)):
                if ada:
                    din += GAMMA_C * DINDING_T * kel * h / 2 * FAKTOR_BUKAAN_DINDING
        # beban mati tambahan
        sidl_l = a_lantai * (SIDL["keramik"][0] + SIDL["plafon"][0] + SIDL["partisi"][0])
        gantung = 0.0
        if lantai is not None:
            if lv in ("LT2", "LT3"):
                ahu = lantai.intersection(box(62, 27, 84, 51)).area if lv == "LT3" else 0.0
                gantung = (a_lantai - ahu) * GANTUNG["podium"] + ahu * GANTUNG["AHU"]
            else:
                gantung = a_lantai * GANTUNG["menara"]
        sidl_a = a_atap * (SIDL["screed_atap"][0] + SIDL["kedap_atap"][0] + SIDL["plafon"][0] + GANTUNG["atap"])
        ringan = t.get("atap_ringan")
        sidl_r = ringan.area * SIDL["rangka_atap_sementara"][0] if ringan is not None else 0.0
        heli = HELIDEK.area * SIDL["dek_helipad"][0] if t.get("helidek") else 0.0
        # dinding luar dan fasad: setengah tingkat bawah + atas, keliling bidang di elevasi itu
        q_dl = (1 - BUKAAN) * DINDING_LUAR["bata"][0] + BUKAAN * DINDING_LUAR["kaca"][0] + DINDING_LUAR["fasad"][0]
        kel_b = keliling(wil_b)
        kel_a = keliling(tk[i + 1]["kolom_bawah"][0]) if i + 1 < len(tk) else 0.0
        fasad = q_dl * (kel_b * h_bawah / 2 + kel_a * h_atas / 2)
        if a_atap or t.get("helidek"):
            fasad += q_dl * PARAPET * (keliling(atap) if atap is not None else 0.0)
        mep = sum(w for _, w in alat.get(lv, [])) if (konfig == "K2" or lv in ("LT2", "LT3", "LT4")) else 0.0
        komp = {"pelat": pelat, "balok": balok, "kolom": kol_b + kol_a, "dinding inti": din,
                "SIDL lantai": sidl_l + gantung, "SIDL atap": sidl_a + sidl_r, "dek helipad": heli,
                "dinding luar dan fasad": fasad, "alat MEP": mep}
        hasil.append({"lv": lv, "elev": LEVEL[lv], "h": LEVEL[lv] - LEVEL["LT1"], "luas": a, "luas_lantai": a_lantai,
                      "luas_atap": a_atap, "komp": komp, "w": sum(komp.values())})
    return hasil


# ------------------------------------------------------------------ gempa: gaya lateral ekivalen
def elf(konfig="K2", sds=SDS, sd1=SD1):
    tk = berat_tingkat(konfig)
    w = sum(t["w"] for t in tk)
    hn = tk[-1]["h"]
    ta = CT * hn ** X_TA
    cs_31 = sds / (R / IE)
    cs_32 = sd1 / (ta * R / IE)
    cs_min = max(0.044 * sds * IE, 0.01)
    cs = max(min(cs_31, cs_32), cs_min)
    v = cs * w
    k = 1.0 if ta <= 0.5 else (2.0 if ta >= 2.5 else 1 + (ta - 0.5) / 2.0)
    wh = [t["w"] * t["h"] ** k for t in tk]
    fx = [v * x / sum(wh) for x in wh]
    return {"W": w, "hn": hn, "Ta": ta, "CuTa": CU * ta, "Cs_31": cs_31, "Cs_32": cs_32, "Cs_min": cs_min, "Cs": cs,
            "V": v, "k": k, "Fx": fx, "tingkat": tk, "Ev": 0.2 * sds}


# ------------------------------------------------------------------ angin (Pasal 26-27)
V_ANGIN = 30.0     # m/s [Asumsi: Buku Peta Angin Indonesia belum ada di acuan/]
KZT, KD, KE, G = 1.0, 0.85, 1.0, 0.85
KZ_C = [(4.6, 0.85), (6.1, 0.90), (7.6, 0.94), (9.1, 0.98), (12.2, 1.04), (15.2, 1.09), (18.0, 1.13), (21.3, 1.17),
        (24.4, 1.21), (27.4, 1.24), (30.5, 1.26), (36.6, 1.31)]  # Tabel 26.10-1 eksposur C


def kz(z):
    zs, ks = zip(*KZ_C)
    return float(np.interp(max(z, 4.6), zs, ks))


def angin(v=V_ANGIN):
    """Geser dasar angin SPGAU (kN) arah utara-selatan (bidang 64-72 m) dan timur-barat (bidang 24-48 m).
    Tinggi dari halaman +12,05; menara sampai atap +38,65 dan parapet; podium sampai +26,05."""
    h_men = LEVEL["ATAP"] + PARAPET - 12.05
    h_pod = LEVEL["LT4"] + PARAPET - 12.05
    qh = 0.613 * kz(h_men) * KZT * KD * KE * v ** 2 / 1000  # kPa
    hasil = {}
    for arah, b_men, l_men, b_pod, l_pod in (("U-S", 64.0, 24.0, 72.0, 48.0), ("T-B", 24.0, 64.0, 48.0, 72.0)):
        cp_pergi = float(np.interp(l_men / b_men, [1.0, 2.0, 4.0], [-0.5, -0.3, -0.2]))
        # sisi datang memakai qz per pias 1 m, sisi pergi qh
        datang = sum(0.613 * kz(z + 0.5) * KZT * KD * KE * v ** 2 / 1000 * G * 0.8 *
                     (b_men if z >= h_pod else b_pod) for z in np.arange(0, h_men, 1.0))
        pergi = qh * G * abs(cp_pergi) * (b_men * h_men + (b_pod - b_men) * h_pod)
        hasil[arah] = {"datang": datang, "pergi": pergi, "V": datang + pergi, "cp_pergi": cp_pergi}
    return {"qh": qh, "v": v, "arah": hasil}


def v_angin_setara_gempa():
    """Kecepatan angin dasar yang membuat geser angin (faktor 1,0 W) sama dengan geser gempa (1,0 E, ρ = 1)."""
    v_e = elf("K2")["V"]
    va = max(a["V"] for a in angin(1.0)["arah"].values())
    return math.sqrt(v_e / va)


# ------------------------------------------------------------------ atap podium, helipad, hujan
def atap_khusus():
    hc = AW139_KG * 9.81 / 1000
    hujan_ds_dh = 75.0   # mm [Asumsi: tinggi luapan saluran sekunder/parapet 50 + kepala hidraulik 25]
    return {
        "tangki_kpa": tl.ringkas()["atap"]["q_tangki"],
        "chiller_kpa": 115.8 / (11.0 * 2.3),
        "chiller_impak_kn": 115.8 * 1.2,
        "heli_berat": hc, "heli_terpusat": 0.75 * hc, "heli_jarak": 2.44, "heli_tunggal": 13.35, "heli_merata": 2.87,
        "hujan_mm": hujan_ds_dh, "hujan_kpa": 0.0098 * hujan_ds_dh,
    }


KOMBINASI = [
    ("1", "1,4D", "4.2.2.1"),
    ("2", "1,2D + 1,6L + 0,5Lr (atau 0,5R)", "4.2.2.1"),
    ("3", "1,2D + 1,6Lr (atau 1,6R) + (L atau 0,5W); L × 0,5 bila Lo <= 4,78 kPa", "4.2.2.1"),
    ("4", "1,2D + 1,0W + L + 0,5Lr (atau 0,5R); L × 0,5 bila Lo <= 4,78 kPa", "4.2.2.1"),
    ("5", "0,9D + 1,0W", "4.2.2.1"),
    ("6", "(1,2 + 0,2 SDS)D + ρQE + L = 1,277D + 1,3QE + L", "4.2.2.3, Ev Pasal 7.4.2.2, ρ Pasal 7.3.4.2"),
    ("7", "(0,9 - 0,2 SDS)D + ρQE = 0,823D + 1,3QE", "4.2.2.3"),
    ("6m", "(1,2 + 0,2 SDS)D + Ω0QE + L = 1,277D + 2,5QE + L (unsur yang disyaratkan kuat lebih)", "4.2.2.3, 7.4.3"),
    ("7m", "(0,9 - 0,2 SDS)D + Ω0QE = 0,823D + 2,5QE", "4.2.2.3, 7.4.3"),
]


# ------------------------------------------------------------------ cek silang T-68: volume beton model LOD 200
def volume_ifc_lod200(berkas=AKAR / "model" / "RSTB-STR-T3-LOD200.ifc"):
    """Volume beton struktur atas gedung utama (x < 95 m) dari IFC LOD 200, tanpa LT1/pondasi (m³) per jenis."""
    import ifcopenshell
    import ifcopenshell.util.element as ue
    import ifcopenshell.util.placement as up
    f = ifcopenshell.open(str(berkas))
    vol = {"IfcSlab": 0.0, "IfcBeam": 0.0, "IfcColumn": 0.0, "IfcWall": 0.0}
    for e in f.by_type("IfcElement"):
        if e.is_a() not in vol:
            continue
        st = ue.get_container(e)
        n = st.Name if st else ""
        if e.is_a() in ("IfcSlab", "IfcBeam") and n == "LT1":
            continue
        try:
            x = up.get_local_placement(e.ObjectPlacement)[0][3] / 1000.0
        except Exception:
            x = 0.0
        if e.is_a() == "IfcSlab":
            x = 0.0  # pelat gedung utama dan utilitas terpisah; disaring dengan luas di bawah
        v = 0.0
        for d in ue.get_psets(e, qtos_only=True).values():
            for kk, vv in d.items():
                if "Volume" in kk and isinstance(vv, (int, float)):
                    v = vv
                    break
        if e.is_a() == "IfcSlab":
            if v > 0 and v / PELAT > 1500:     # pelat gedung utama (luas > 1.500 m²)
                vol["IfcSlab"] += v
        elif x < 95.0:
            vol[e.is_a()] += v
    return vol


def volume_beton_python():
    """Volume beton struktur atas gedung utama (m³) dengan dasar yang sama dengan IFC LOD 200: kolom dan dinding inti
    setinggi penuh mulai LT1, balok tinggi penuh 600 mm (tumpang dengan pelat seperti model), tanpa faktor bukaan."""
    tk = tingkat("K2")
    pelat = sum(sum(g.area for g in (t.get("lantai"), t.get("atap")) if g is not None) for t in tk) * PELAT
    balok = sum(panjang_grid_di(unary_union([g for g in (t.get("lantai"), t.get("atap")) if g is not None]))
                for t in tk if t.get("lantai") is not None or t.get("atap") is not None) * BALOK_B * BALOK_H
    kolom, dinding = 0.0, 0.0
    for t in tk:
        lv = t["lv"]
        h = LEVEL[lv] - LEVEL[URUT[URUT.index(lv) - 1]]
        wil, uk = t["kolom_bawah"]
        kolom += len(titik_kolom(wil)) * uk ** 2 * h
        for _, kel, puncak in INTI:
            if LEVEL[lv] <= LEVEL[puncak] + 1e-6:
                dinding += kel * DINDING_T * h
    return {"IfcSlab": pelat, "IfcBeam": balok, "IfcColumn": kolom, "IfcWall": dinding}


def berat_struktur_python(konfig="K2"):
    tk = berat_tingkat(konfig)
    return {k: sum(t["komp"][k] for t in tk) for k in ("pelat", "balok", "kolom", "dinding inti")}


def ringkasan():
    e2, e1 = elf("K2"), elf("K1")
    return {"K2": e2, "K1": e1, "angin": angin(), "v_setara": v_angin_setara_gempa(), "atap": atap_khusus()}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    r = ringkasan()
    for k in ("K1", "K2"):
        e = r[k]
        print(f"{k}: W {e['W']:.0f} kN; hn {e['hn']:.2f}; Ta {e['Ta']:.3f}; Cs {e['Cs']:.4f}; V {e['V']:.0f} kN; k {e['k']:.2f}")
        for t, f in zip(e["tingkat"], e["Fx"]):
            print(f"  {t['lv']} A {t['luas']:.0f} m² W {t['w']:.0f} kN Fx {f:.0f}",
                  {kk: round(vv) for kk, vv in t["komp"].items()})
    a = r["angin"]
    print(f"angin V {a['v']} m/s qh {a['qh']:.3f} kPa", {k: round(v["V"]) for k, v in a["arah"].items()},
          f"V setara gempa {r['v_setara']:.0f} m/s")
    print(r["atap"])
    print("IFC", {k: round(v, 1) for k, v in volume_ifc_lod200().items()})
    print("Python", {k: round(v, 1) for k, v in volume_beton_python().items()})


# ------------------------------------------------------------------ cek silang T-68 (dasar geometri sama)
def koreksi_ifc():
    """Volume IFC LOD 200 dikoreksi untuk perubahan geometri sesudah 3.9: void LT2 (x 36-62, y 51-75) dan V1
    (LT3 utara tidak dibangun; model LOD 200 memuat pelat LT3 penuh dan atap podium penuh di LT4)."""
    v = volume_ifc_lod200()
    void = VOID_LT2.area * PELAT
    v1 = V1.area * PELAT
    return {"ifc": v, "koreksi_pelat": -(void + v1), "ifc_total": sum(v.values()),
            "ifc_koreksi": sum(v.values()) - void - v1, "python": sum(volume_beton_python().values())}


# ------------------------------------------------------------------ Excel
def buat_excel(keluar=BERKAS):
    import openpyxl
    from format_dokumen import AI, Lembar, set_font_bawaan

    r = ringkasan()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    lab = f"DIISI AI ATAS PERMINTAAN DEFSA (20 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk pembebanan (4.2)", [6, 120])
    lb.catatan(LABEL + " " + lab)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, x] for i, x in enumerate([
        "Dasar: SNI 1727:2020 (beban mati, hidup, helipad, hujan, angin) dan SNI 1726:2019 (berat seismik, gaya lateral "
        "ekivalen awal, kombinasi). Pasal dan halaman cetak ditulis di tiap baris.",
        "Spektrum desain dari langkah 4.1 opsi (a), dipilih Defsa 20 Nov 2026: SDS 0,386, SD1 0,459, KDS D.",
        "Geometri: grid 8 m; podium x 12-84, y 27-75; menara x 20-84, y 27-51; V1 (LT3 utara x 36-84, y 51-75 tidak "
        "dibangun, atap LT2 +21,85 memikul alat); void LT2 x 36-62, y 51-75 (zonasi 3.4); pra-dimensi 3.6.",
        "Konfigurasi K1 (tahap 1: menara sampai LT4 dengan atap baja ringan sementara di +30,25) dan K2 (akhir: 6 lantai, "
        "atap helipad +38,65 dengan dek 33,3 × 33,3 m).",
        "Beban alat dari Data Beban MEP Rinci (berat operasi, Pasal 3.1.3) setelah telaah 4.0 (M-1: atap podium 2.676 kN).",
        "Lembar 6-8 memakai rumus Excel (jumlah komponen, Cs, V, Fx, angin) yang dicocokkan dengan Python (T-69).",
        "Status: " + STATUS + ".",
    ])], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Beban Mati Tambahan"), 2, "Beban mati tambahan (SNI 1727 Tabel C3.1-1)",
                [34, 12, 90])
    lb.catatan(LABEL + " Berat sendiri unsur beton dihitung dari ukuran dengan γ 23,6 kN/m³ (Tabel C3.1-2 hal. 279).")
    baris = [[k.replace("_", " "), v, s] for k, (v, s) in SIDL.items()]
    baris += [[f"Gantung MEP {k}", v, "Data Beban MEP Rinci lembar 8 (>= 0,19 duct, Tabel C3.1-1)"] for k, v in
              GANTUNG.items()]
    baris += [[f"Dinding luar: {k}", round(v, 2), s] for k, (v, s) in DINDING_LUAR.items()]
    baris += [["Porsi bukaan fasad", BUKAAN, "V4 (3.11)"], ["Tinggi parapet (m)", PARAPET, "[Asumsi]"]]
    lb.tabel(["Komponen", "Nilai (kPa)", "Sumber"], baris, rata=list("lcl"), fmt=[None, "0.00", None], fill_kolom={1: AI})
    lb.kosong()
    lantai = SIDL["keramik"][0] + SIDL["plafon"][0] + SIDL["partisi"][0]
    lb.tabel(["Jumlah per tipe bidang", "kPa", "Isi"], [
        ["Lantai podium (tanpa gantung)", round(lantai, 2), "keramik + plafon + partisi"],
        ["Lantai podium + gantung 0,50", round(lantai + GANTUNG["podium"], 2), ""],
        ["Ruang AHU LT3 + gantung 0,80", round(lantai + GANTUNG["AHU"], 2), ""],
        ["Lantai menara + gantung 0,35", round(lantai + GANTUNG["menara"], 2), ""],
        ["Atap beton", round(SIDL["screed_atap"][0] + SIDL["kedap_atap"][0] + SIDL["plafon"][0] + GANTUNG["atap"], 2),
         "screed + kedap + plafon + gantung"],
    ], rata=list("lcl"), fmt=[None, "0.00", None], fill_kolom={1: AI}, beku=False)

    lb = Lembar(wb.create_sheet("Beban Hidup"), 3, "Beban hidup (SNI 1727 Tabel 4.3-1 hal. 25-28)",
                [40, 12, 11, 12, 16, 70])
    lb.catatan(LABEL + " Reduksi Pasal 4.7.2 hal. 31: L = Lo (0,25 + 4,57/√(KLL AT)), >= 0,5Lo (satu lantai) atau "
               "0,4Lo (dua lantai atau lebih); helipad tidak direduksi (4.11.1).")
    lb.tabel(["Zona", "Lantai", "Lo (kPa)", "Terpusat (kN)", "Reduksi", "Sumber Tabel 4.3-1"],
             [list(x) for x in HIDUP], rata=list("lcccll"), fmt=[None, None, "0.00", "0.00", None, None],
             fill_kolom={2: AI, 3: AI})

    lb = Lembar(wb.create_sheet("Alat MEP"), 4, "Beban alat MEP per lantai (berat operasi, Pasal 3.1.3)",
                [10, 70, 16, 40])
    lb.catatan(LABEL + " Data Beban MEP Rinci (24 Mei 2027) setelah telaah 4.0. Impak mesin berputar +20 % "
               "(Pasal 4.6.3 hal. 30) hanya untuk desain unsur penumpu lokal (4.5-4.6), tidak untuk berat seismik.")
    baris = [[lv, n, round(w, 1), "berat seismik dan beban mati lokal"] for lv, isi in alat_per_lantai().items()
             for n, w in isi]
    lb.tabel(["Lantai", "Alat", "Berat operasi (kN)", "Dipakai untuk"], baris, rata=list("clcl"),
             fmt=[None, None, "#,##0.0", None], fill_kolom={2: AI})

    ak = r["atap"]
    lb = Lembar(wb.create_sheet("Atap dan Helipad"), 5, "Beban khusus atap podium, helipad, dan hujan",
                [52, 14, 12, 70])
    lb.catatan(LABEL + " Beban lokal untuk desain pelat/balok (4.5-4.6).")
    lb.tabel(["Butir", "Nilai", "Satuan", "Dasar"], [
        ["Tangki air 210 m³ pada tapak 12,0 × 6,0 m", round(ak["tangki_kpa"], 2), "kPa", "Telaah M-1/M-10; 7 balok dudukan @ 1,0 m"],
        ["Chiller per unit pada tapak 11,0 × 2,3 m", round(ak["chiller_kpa"], 2), "kPa", "Daftar Alat M-01, 6 titik tumpu"],
        ["Chiller per unit dengan impak 20 %", round(ak["chiller_impak_kn"], 1), "kN", "Pasal 4.6.3 hal. 30 (mesin berputar)"],
        ["Berat lepas landas maksimum AW139", round(ak["heli_berat"], 1), "kN", "6.800 kg (surat Kantor SAR, data owner)"],
        ["Dua beban terpusat 0,75 MTOW, jarak 2,44 m, bidang 200 × 200 mm", round(ak["heli_terpusat"], 1), "kN tiap",
         "Pasal 4.11.2 hal. 35; tidak bersamaan dengan beban merata"],
        ["Beban terpusat tunggal, bidang 114 × 114 mm", ak["heli_tunggal"], "kN", "Pasal 4.11.2 hal. 35"],
        ["Beban merata helipad (MTOW > 13,35 kN)", ak["heli_merata"], "kPa", "Tabel 4.3-1 hal. 26; tidak direduksi"],
        ["Dek helipad kantilever 4,7 m (berat sendiri)", SIDL["dek_helipad"][0], "kPa", SIDL["dek_helipad"][1]],
        ["Tinggi air ds + dh pada saluran sekunder", ak["hujan_mm"], "mm", "[Asumsi: luapan parapet 50 + kepala 25 mm]"],
        ["Beban hujan R = 0,0098 (ds + dh)", round(ak["hujan_kpa"], 3), "kPa", "Pasal 8.3 hal. 95; < Lr 0,96 kecuali "
         "genangan"],
    ], rata=list("lccl"), fmt=[None, "0.00", None, None], fill_kolom={1: AI})

    # 6 berat seismik (rumus jumlah)
    for no, kf in ((6, "K2"), (7, "K1")):
        e = r[kf]
        lb = Lembar(wb.create_sheet(f"Berat Seismik {kf}"), no,
                    f"Berat seismik efektif dan gaya lateral ekivalen {kf} (Pasal 7.7.2, 7.8)",
                    [8, 10, 10, 11, 11, 10, 10, 11, 11, 11, 10, 10, 11, 12, 12])
        lb.catatan(LABEL + (" K2: akhir 6 lantai + helipad." if kf == "K2" else
                            " K1: tahap 1, menara sampai LT4, atap baja ringan sementara di +30,25 (tanpa pelat).") +
                   " Kolom dan dinding: setengah tingkat bawah + setengah tingkat atas. Fx = Cvx V, Cvx = w h^k / Σ w h^k.")
        kom = list(e["tingkat"][0]["komp"])
        baris = [[t["lv"], t["elev"], round(t["h"], 2), round(t["luas"], 0)] + [round(t["komp"][c], 1) for c in kom] +
                 [None, None] for t in e["tingkat"]]
        _, a, b = lb.tabel(["Tingkat", "Elevasi (m)", "h (m)", "Luas (m²)"] + [c.capitalize() + " (kN)" for c in kom] +
                           ["W tingkat (kN)", "Fx (kN)"], baris, rata=["c"] * 15,
                           fmt=[None, "0.00", "0.00", "#,##0"] + ["#,##0"] * 11, fill_kolom={13: AI, 14: AI})
        k = lb.kol
        for rr in range(a, b + 1):
            lb.ws[f"{k(13)}{rr}"] = f"=SUM({k(4)}{rr}:{k(12)}{rr})"
        lb.kosong()
        _, a2, b2 = lb.tabel(["Besaran", "Nilai", "Dasar", "", "", "", "", "", "", "", "", "", "", "", ""], [
            ["W total (kN)", f"=SUM({k(13)}{a}:{k(13)}{b})", "Pasal 7.7.2"],
            ["hn (m)", f"=MAX({k(2)}{a}:{k(2)}{b})", "di atas LT1 +12,85 (taraf penjepitan)"],
            ["Ta = Ct hn^x (s)", None, f"Ct {CT}, x {X_TA} (Tabel 18 hal. 72)"],
            ["Cs (31) = SDS/(R/Ie)", None, f"SDS {SDS}, R {R}, Ie {IE} (Pasal 7.8.1.1 hal. 69)"],
            ["Cs (32) = SD1/(T R/Ie)", None, f"SD1 {SD1}, T = Ta"],
            ["Cs min = 0,044 SDS Ie >= 0,01", None, "Pers. (34) hal. 70"],
            ["Cs dipakai", None, ""],
            ["V = Cs W (kN)", None, "Pers. (30) hal. 69"],
            ["k", None, "Pasal 7.8.3 hal. 73"],
            ["Batas atas T = Cu Ta (s)", None, f"Cu {CU} (Tabel 17 hal. 72)"],
        ], rata=["l", "c", "l"] + ["l"] * 12, fmt=[None, "#,##0.0000"] + [None] * 13, fill_kolom={1: AI}, beku=False)
        ws = lb.ws
        c = k(1)
        ws[f"{c}{a2 + 2}"] = f"={CT}*{c}{a2 + 1}^{X_TA}"
        ws[f"{c}{a2 + 3}"] = f"={SDS}/({R}/{IE})"
        ws[f"{c}{a2 + 4}"] = f"={SD1}/({c}{a2 + 2}*{R}/{IE})"
        ws[f"{c}{a2 + 5}"] = f"=MAX(0.044*{SDS}*{IE},0.01)"
        ws[f"{c}{a2 + 6}"] = f"=MAX(MIN({c}{a2 + 3},{c}{a2 + 4}),{c}{a2 + 5})"
        ws[f"{c}{a2 + 7}"] = f"={c}{a2 + 6}*{c}{a2}"
        ws[f"{c}{a2 + 8}"] = f"=IF({c}{a2 + 2}<=0.5,1,IF({c}{a2 + 2}>=2.5,2,1+({c}{a2 + 2}-0.5)/2))"
        ws[f"{c}{a2 + 9}"] = f"={CU}*{c}{a2 + 2}"
        for rr in range(a, b + 1):
            ws[f"{k(14)}{rr}"] = (f"={c}${a2 + 7}*{k(13)}{rr}*{k(2)}{rr}^{c}${a2 + 8}/"
                                  f"SUMPRODUCT({k(13)}${a}:{k(13)}${b},{k(2)}${a}:{k(2)}${b}^{c}${a2 + 8})")

    an = r["angin"]
    lb = Lembar(wb.create_sheet("Angin"), 8, "Beban angin SPGAU (SNI 1727 Pasal 26-27) dan pembanding gempa",
                [44, 16, 16, 70])
    lb.catatan(LABEL + " V dari Buku Peta Angin Indonesia (Pasal 26.5.1 hal. 107) BELUM ADA di acuan/; V 30 m/s "
               "[Asumsi] hanya untuk membandingkan orde dengan gempa. Eksposur C [Asumsi: lebar sungai < 1.524 m].")
    _, a3, _ = lb.tabel(["Besaran", "U-S (bidang 64-72 m)", "T-B (bidang 24-48 m)", "Dasar"], [
        ["V (m/s)", an["v"], an["v"], "[Asumsi]"],
        ["Kz pada h menara", round(kz(LEVEL["ATAP"] + PARAPET - 12.05), 3), round(kz(LEVEL["ATAP"] + PARAPET - 12.05), 3),
         "Tabel 26.10-1 hal. 114, eksposur C, h dari halaman +12,05"],
        ["qh = 0,613 Kz Kzt Kd Ke V² (kPa)", None, None, "Pers. 26.10-1.si hal. 114; Kd 0,85 (Tabel 26.6-1), Kzt 1, Ke 1"],
        ["Cp sisi pergi", an["arah"]["U-S"]["cp_pergi"], an["arah"]["T-B"]["cp_pergi"], "Gambar 27.3-1 hal. 129 (L/B)"],
        ["Geser sisi datang (kN)", round(an["arah"]["U-S"]["datang"], 0), round(an["arah"]["T-B"]["datang"], 0),
         "qz G 0,8 per pias 1 m; G 0,85 (Pasal 26.11.1 hal. 115)"],
        ["Geser sisi pergi (kN)", round(an["arah"]["U-S"]["pergi"], 0), round(an["arah"]["T-B"]["pergi"], 0), "qh G |Cp|"],
        ["Geser dasar angin (kN)", None, None, "jumlah"],
        ["Geser dasar gempa K2, ρ = 1 (kN)", round(r["K2"]["V"], 0), round(r["K2"]["V"], 0), "lembar 6"],
        ["V angin yang menyamai gempa (m/s)", round(r["v_setara"], 0), "", "gempa menentukan untuk SPGAU"],
    ], rata=list("lccl"), fmt=[None, "#,##0.000", "#,##0.000", None], fill_kolom={1: AI, 2: AI}, beku=False)
    ws = lb.ws
    for cc in (lb.kol(1), lb.kol(2)):
        ws[f"{cc}{a3 + 2}"] = f"=0.613*{cc}{a3 + 1}*1*{KD}*1*{cc}{a3}^2/1000"
        ws[f"{cc}{a3 + 6}"] = f"={cc}{a3 + 4}+{cc}{a3 + 5}"

    lb = Lembar(wb.create_sheet("Kombinasi"), 9, "Kombinasi beban ultimit (SNI 1726 Pasal 4.2.2)", [8, 90, 40])
    lb.catatan(LABEL + f" Ev = 0,2 SDS D = {0.2 * SDS:.3f} D (Pasal 7.4.2.2); ρ = 1,3 sementara (Pasal 7.3.4.2, "
               "diperiksa di 4.3); Ω0 = 2,5 (Tabel 12, sistem ganda). Arah gempa: 100 % + 30 % arah tegak lurus bila "
               "disyaratkan Pasal 7.5 (4.3).")
    lb.tabel(["No", "Kombinasi", "Pasal"], [list(x) for x in KOMBINASI], rata=list("cll"), fill_kolom={1: AI})

    kr = koreksi_ifc()
    lb = Lembar(wb.create_sheet("Catatan"), 10, "Cek silang, keputusan, dan catatan", [8, 120])
    lb.catatan(LABEL + " " + lab)
    lb.tabel(["No", "Catatan"], [[i + 1, x] for i, x in enumerate([
        f"T-68: volume beton struktur atas gedung utama, Python {kr['python']:,.0f} m³ terhadap IFC LOD 200 "
        f"{kr['ifc_total']:,.0f} m³ (dikoreksi void LT2 dan V1: {kr['ifc_koreksi']:,.0f} m³), selisih "
        f"{(kr['python'] / kr['ifc_koreksi'] - 1) * 100:.1f} %.".replace(",", "."),
        f"Cek wajar: berat seismik K2 {r['K2']['W']:,.0f} kN pada luas {sum(t['luas'] for t in r['K2']['tingkat']):,.0f} m² "
        f"= {r['K2']['W'] / sum(t['luas'] for t in r['K2']['tingkat']):.1f} kPa rata-rata.".replace(",", "."),
        f"Geser dasar ELF K2 {r['K2']['V']:,.0f} kN (Cs {r['K2']['Cs']:.4f}); K1 {r['K1']['V']:,.0f} kN. Dengan spektrum "
        "SE sementara 3.6 (SDS 0,482) geser dasar 25 % lebih besar.".replace(",", "."),
        "Angin tidak menentukan SPGAU: geser angin baru menyamai gempa pada V ±100 m/s. Klading dan dek helipad tetap "
        "dicek angin di 4.9 setelah Buku Peta Angin Indonesia tersedia.",
        "KEPUTUSAN M-4 (Defsa 20 Nov 2026): evakuasi udara mulai tahap 2. K1 tetap memakai atap baja ringan "
        "sementara di atas LT4 tanpa beban helipad; helipad AW139 hanya di atap menara +38,65 (K2). Owner perlu "
        "diberi tahu bahwa permintaan Kantor SAR/Dinkes untuk evakuasi udara sejak tahap 1 tidak dipenuhi.",
        "KEPUTUSAN M-5: ruang AHU LT3 (x 62-84, y 27-51) dihitung sudah terpasang sejak tahap 1 karena melayani "
        "kamar operasi, ICU, dan CSSD di LT2.",
        "Catatan geometri untuk 4.9: zonasi 3.4 memuat void LT3 x 46-62, y 27-75 yang bertabrakan dengan inti lif "
        "x 50-58, y 35-43 (lif melayani LT1-LT6). Pelat LT3 dihitung penuh di luar V1.",
        "Pelat atap LT4 di bawah kolom menara dan atap podium utara memikul alat; beban lokal ada di lembar 5.",
    ])], rata=list("cl"), fill_kolom={1: AI})

    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


# ------------------------------------------------------------------ gambar GS-02 (CADCraft, KOP_A3)
PNG_GS02 = KELUAR / "Gambar" / "GS-02 Zona Beban.png"
PDF_GS02 = KELUAR / "4.2 Gambar Zona Beban.pdf"
ARSIR_L = {1.92: (".", "DOTS"), 2.87: ("/", "ANSI31"), 3.83: ("x", "ANSI37"), 4.79: ("-", "LINE"), 0.96: (None, None),
           30.1: ("+", "NET")}
ZONA_GAMBAR = {
    "LT2 +17,35": [("Bedah, CSSD", (62, 84, 27, 63), 2.87), ("ICU, HCU", (36, 62, 27, 51), 2.87),
                   ("Kebidanan", (12, 36, 27, 43), 1.92), ("Lab", (12, 36, 43, 55), 2.87),
                   ("Hemodialisis", (12, 36, 55, 75), 1.92), ("Rehab", (62, 84, 63, 75), 1.92)],
    "LT3 +21,85": [("Adm., aula", (12, 46, 27, 51), 4.79), ("Adm., aula", (12, 36, 51, 75), 4.79),
                   ("Penunjang", (46, 62, 27, 51), 3.83), ("AHU", (62, 84, 27, 51), 4.79),
                   ("Atap podium utara", (36, 84, 51, 75), 0.96), ("Tangki", (60, 72, 67, 73), 30.1)],
    "LT4 +26,05": [("Rawat inap", (20, 48, 27, 51), 1.92), ("Inti", (48, 58, 27, 51), 3.83),
                   ("Rawat inap", (58, 84, 27, 51), 1.92), ("Atap LT3", (12, 20, 27, 51), 0.96),
                   ("Atap LT3", (12, 36, 51, 75), 0.96)],
    "LT5 +30,25": [("Rawat inap", (20, 48, 27, 51), 1.92), ("Inti", (48, 58, 27, 51), 3.83),
                   ("Rawat inap", (58, 84, 27, 51), 1.92)],
    "LT6 +34,45": [("Rawat inap", (20, 48, 27, 51), 1.92), ("Inti", (48, 58, 27, 51), 3.83),
                   ("Rawat inap", (58, 84, 27, 51), 1.92)],
    "ATAP +38,65": [("Helipad", (20, 84, 27, 51), 2.87)],
}


def gambar():
    from matplotlib.patches import Circle, Rectangle
    from cad_lembar import STATUS_DRAF
    from gambar_teknik import BukuPDF as PdfPages
    from gambar_teknik import Kertas
    from tahap2_gambar_air_tanah import gaya_sumbu
    from tahap2_gambar_geoteknik import kotak_catatan

    k = Kertas()
    posisi = [(28, 168), (118, 168), (208, 168), (28, 70), (118, 70), (208, 70)]
    for (judul, zona), (x0, y0) in zip(ZONA_GAMBAR.items(), posisi):
        ax = k.sumbu(x0, y0, 80, 60)
        ax.add_patch(Rectangle((12, 27), 72, 48, fill=False, lw=0.4, ls="--", ec="k"))
        for nama, (a, b_, c, d), lo in zona:
            ax.add_patch(Rectangle((a, c), b_ - a, d - c, fc="w", ec="k", lw=0.5, hatch=ARSIR_L[lo][0]))
            if (b_ - a) * (d - c) >= 90:
                ax.text((a + b_) / 2, (c + d) / 2, f"{nama}\n{lo:.2f}".replace(".", ","), ha="center", va="center",
                        fontsize=4.6)
        if judul.startswith("ATAP"):
            ax.add_patch(Rectangle(tuple(HELIDEK.bounds[:2]), 33.3, 33.3, fill=False, ls="--", lw=0.6, ec="k"))
            ax.add_patch(Circle((52, 39), 12.5, fill=False, lw=0.6, ec="k"))
        for gx in GRID_X:
            ax.axvline(gx, color="0.6", lw=0.2, ls=":")
        for gy in GRID_Y:
            ax.axhline(gy, color="0.6", lw=0.2, ls=":")
        ax.set_xlim(8, 88)
        ax.set_ylim(20, 79)
        ax.set_aspect("equal")
        ax.set_xticks([12, 28, 44, 60, 76, 84])
        ax.set_yticks([27, 43, 59, 75])
        ax.tick_params(labelsize=5)
        gaya_sumbu(ax, judul)
    for lo, (_, pola) in ARSIR_L.items():
        if pola:
            k.legenda("arsir", f"Lo {lo:.2f} kPa".replace(".", ",") if lo < 30 else "Tangki air 30,1 kPa (lokal)",
                      pola=pola, skala_pola=0.45)
    k.teks(30, 275, "DENAH ZONA BEBAN HIDUP DAN BEBAN KHUSUS", fontsize=11, fontweight="bold")
    k.teks(30, 270, "SNI 1727:2020 Tabel 4.3-1; angka di zona = Lo (kPa); koordinat grid lokal (m)", fontsize=6.5)
    sid = SIDL["keramik"][0] + SIDL["plafon"][0] + SIDL["partisi"][0]
    kotak_catatan(k, 287, "CATATAN", [
        f"SIDL lantai {sid:.2f} kPa + gantung MEP 0,35-0,80 kPa; SIDL atap 1,69 kPa (Tabel C3.1-1).".replace(".", ",", 2),
        "Koridor di atas lantai pertama 3,83 kPa; tangga 4,79 kPa; atap 0,96 kPa tanpa arsir (Tabel 4.3-1).",
        "Atap podium utara: 4 chiller 115,8 kN, tangki 2.168 kN, pompa; impak 20 % (Pasal 4.6.3).",
        "Helipad AW139: 2,87 kPa atau 2 × 50,0 kN @ 2,44 m, tidak direduksi (Pasal 4.11); dek 33,3 × 33,3 m "
        "(garis putus), FATO Ø25 m (lingkaran).",
        "V1: LT3 utara x 36-84, y 51-75 tidak dibangun; void LT2 x 36-62, y 51-75.",
        "Tahap 1 (K1): menara sampai LT4, atap baja ringan sementara (keputusan M-4 menunggu).",
    ], 80)
    k.etiket("Zona beban", "GS-02", "Tanpa skala", "1 / 1", tanggal="JULI 2027", status="DISETUJUI 20 NOV 2026")
    PNG_GS02.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(PDF_GS02) as pdf:
        k.simpan(pdf, PNG_GS02)
    return PDF_GS02
