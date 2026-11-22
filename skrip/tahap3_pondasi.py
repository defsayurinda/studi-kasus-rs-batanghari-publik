"""Langkah 3.7: alternatif pondasi tiang (daya dukung kasar, gesekan negatif, jumlah tiang, pertimbangan tapak).

Acuan (halaman PDF): FHWA NHI-06-089 Soils and Foundations Vol II (acuan/pustaka) hal. 239 Pers. 9-37a dan 9-38
(fs = α su, α 0,55), hal. 242-243 Pers. 9-42, 9-43 (fs = β σ'v, β = 1,5 - 0,135 √z[ft], 0,25-1,2; fs ≤ 191 kPa),
Pers. 9-45 (qt = 1,2 N60 ksf = 57,5 N60 kPa, maks 90 ksf = 4.309 kPa). SNI 8460:2017 hal. 194 Pasal 9.2.3.1 (FK
fondasi dalam ≥ 2,5), hal. 204 (gesekan negatif sebagai beban, tidak dibagi FK), hal. 295 (downdrag likuifaksi:
FK > 1,1). Parameter tanah langkah 2.4; likuifaksi U5 langkah 2.6 (gesekan U5 diabaikan); peil 3.3; beban 3.6.
Rumus tiang bor dipakai juga untuk tiang pancang [Asumsi konservatif; metode Nordlund berbasis grafik]. β gesekan
negatif dan indeks harga per meter berlabel [Asumsi].
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 19 Nov 2026 (opsi A tiang bor Ø800).
"""
import functools
import math
from pathlib import Path

import tahap3_peil as pl
import tahap3_program as pr
import tahap3_struktur as st

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "03 Desain Konsep"
BERKAS = KELUAR / "3.7 Alternatif Pondasi.xlsx"
PDF = KELUAR / "3.7 Gambar Rencana Pondasi.pdf"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = "DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026 (opsi A)."
GW = 9.81

# Profil desain (BH-5 untuk U1-U5, BH-1 untuk batas U5/U6 dan U6/U7), kedalaman dari muka tanah asli +9,95
LAPISAN = [  # (unit, bawah m, γ kN/m³, jenis, su kPa, N60)
    ("U1", 0.31, 17.0, "lempung", 20.0, None),
    ("U2", 1.62, 17.8, "lempung", 35.0, None),
    ("U4", 9.46, 15.2, "lempung", None, None),  # su = 5,2 + 1,09 z
    ("U5", 19.30, 19.0, "pasir", None, 12),
    ("U6", 33.55, 19.1, "lempung", 85.0, None),
    ("U7", 55.0, 20.0, "pasir", None, 30),
]
ELEV_TANAH = 9.95
MAT = 0.7  # m di bawah muka tanah asli (2.3)
FK = 2.5
FK_LIK = 1.1
BETA_NSF = {"lempung": 0.25, "pasir": 0.35, "gambut": 0.25}  # [Asumsi: rentang β gesekan negatif Fellenius]

# Profil desain per zona tanah (laporan antara LA.1, tindak lanjut evaluasi kunci Tahap 3 no. 1): batas lapisan dari log
# bor 2.2 (tahap2_stratigrafi), parameter 2.4. U3 gambut γ 10,7 (2.4). Ujung tiang ±4 m masuk U7 di tiap profil.
LAPISAN_TENGAH = [  # BH-7 (50, 70), muka tanah +9,38, gambut 2,15 m
    ("U1", 0.41, 17.0, "lempung", 20.0, None),
    ("U2", 1.27, 17.8, "lempung", 35.0, None),
    ("U3", 3.42, 10.7, "gambut", None, None),
    ("U4", 9.63, 15.2, "lempung", None, None),
    ("U5", 18.10, 19.0, "pasir", None, 12),
    ("U6", 32.74, 19.1, "lempung", 85.0, None),
    ("U7", 55.0, 20.0, "pasir", None, 30),
]
LAPISAN_UTARA = [  # BH-3 (55, 78), muka tanah +9,23, gambut 2,84 m
    ("U1", 0.41, 17.0, "lempung", 20.0, None),
    ("U2", 1.13, 17.8, "lempung", 35.0, None),
    ("U3", 3.97, 10.7, "gambut", None, None),
    ("U4", 9.73, 15.2, "lempung", None, None),
    ("U5", 18.08, 19.0, "pasir", None, 12),
    ("U6", 32.62, 19.1, "lempung", 85.0, None),
    ("U7", 55.0, 20.0, "pasir", None, 30),
]


def _profil(profil):
    return PROFIL[profil or "SELATAN"]


def urugan(profil=None):
    """Tebal urugan di atas muka tanah asli sampai halaman (3.3) dan tegangan tambahannya."""
    h = pl.peil_usulan()["halaman"] - _profil(profil)["elev"]
    return h, 19.0 * h


def sigma_v(z, profil=None):
    """Tegangan efektif vertikal (kPa) pada kedalaman z (m) dari muka tanah asli, setelah urugan terkonsolidasi."""
    _, du = urugan(profil)
    s, atas = du, 0.0
    for _, bawah, g, *_ in _profil(profil)["lapisan"]:
        if z <= atas:
            break
        seg = min(z, bawah) - atas
        kering = max(0.0, min(seg, MAT - atas)) if atas < MAT else 0.0
        s += g * kering + (g - GW) * (seg - kering)
        atas = bawah
    return s


def lapisan_di(z, profil=None):
    lap = _profil(profil)["lapisan"]
    for lp in lap:
        if z <= lp[1]:
            return lp
    return lap[-1]


TIANG = {
    "BOR-800": {"nama": "Tiang bor Ø800, casing permanen di U1-U4", "D": 0.8, "pancang": False,
                "harga_m": 4.6, "getaran": "rendah"},
    "BOR-1000": {"nama": "Tiang bor Ø1000, casing permanen di U1-U4", "D": 1.0, "pancang": False,
                 "harga_m": 6.8, "getaran": "rendah"},
    "SPUN-600": {"nama": "Tiang pancang beton pratekan (spun) Ø600 kelas C", "D": 0.6, "pancang": True,
                 "harga_m": 1.9, "getaran": "tinggi"},
    "PIPA-610": {"nama": "Tiang pipa baja Ø610 × 12 + tebal korosi + lapisan", "D": 0.61, "pancang": True,
                 "harga_m": 5.2, "getaran": "tinggi"},
}  # harga per meter terpasang, juta Rp [Asumsi indeks; harga survei di 3.8]
UJUNG = 33.55 + 4.0  # m di bawah muka tanah asli: masuk U7 ±4 m
PROFIL = {
    "SELATAN": {"titik": "BH-5", "elev": ELEV_TANAH, "lapisan": LAPISAN, "ujung": UJUNG},
    "TENGAH": {"titik": "BH-7", "elev": 9.38, "lapisan": LAPISAN_TENGAH, "ujung": 32.74 + 4.0},
    "UTARA": {"titik": "BH-3", "elev": 9.23, "lapisan": LAPISAN_UTARA, "ujung": 32.62 + 4.0},
}
BATAS_ZONA = (0.5, 2.0)  # m tebal gambut U3: < 0,5 selatan, 0,5-2,0 tengah, ≥ 2,0 utara [Asumsi pembagian]


@functools.lru_cache(maxsize=None)
def kapasitas(kode, ujung=None, langkah=0.25, profil=None):
    """Qult (kN) tanpa gesekan U1-U5 (lunak dan mudah likuifaksi), dan gesekan negatif statis / likuifaksi."""
    ujung = ujung or _profil(profil)["ujung"]
    t = TIANG[kode]
    keliling = math.pi * t["D"]
    qs, nsf_statis, nsf_lik = 0.0, 0.0, 0.0
    z = langkah / 2
    while z < ujung:
        unit, bawah, g, jenis, su, n60 = lapisan_di(z, profil)
        sv = sigma_v(z, profil)
        if unit in ("U6", "U7"):
            if jenis == "lempung":
                fs = 0.55 * su
            else:
                beta = min(1.2, max(0.25, 1.5 - 0.135 * math.sqrt(z / 0.3048)))
                fs = min(beta * sv, 191.0)
            qs += fs * keliling * langkah
        else:
            f_nsf = BETA_NSF[jenis] * sv
            if unit in ("U1", "U2", "U3", "U4"):
                nsf_statis += f_nsf * keliling * langkah
            nsf_lik += f_nsf * keliling * langkah
        z += langkah
    n60 = lapisan_di(ujung, profil)[5] or 30
    qt = min(57.5 * n60, 4309.0)
    qb = qt * math.pi * t["D"] ** 2 / 4
    return {"Qs": qs, "Qb": qb, "Qult": qs + qb, "NSF_statis": nsf_statis, "NSF_lik": nsf_lik,
            "panjang": ujung + urugan(profil)[0] - 1.2}  # dari bawah pile cap (halaman - 1,2 m)


def beban_izin(kode, profil=None):
    """Beban kerja izin per tiang: statis Qult/FK - NSF statis; likuifaksi Qult/FK_lik - NSF likuifaksi. Ambil kecil."""
    k = kapasitas(kode, profil=profil)
    statis = k["Qult"] / FK - k["NSF_statis"]
    lik = k["Qult"] / FK_LIK - k["NSF_lik"]
    return {"statis": statis, "likuifaksi": lik, "izin": min(statis, lik), **k}


# ------------------------------------------------------------------ beban kolom (layan D + L, sistem ganda)
def beban_kolom():
    d = st.beban_mati("GANDA")
    l_ = st.LL["operasi/lab"]
    trib = st.BENTANG ** 2
    per_lantai = (d + l_) * trib
    p = st.PRA["GANDA"]
    kolom = st.GAMMA_C * (p["kolom_podium"] / 1000) ** 2 * 13.2 + st.GAMMA_C * (p["kolom_menara"] / 1000) ** 2 * 12.6
    men = pr.MASSA["MENARA"]
    hasil = []
    for x in st.GRID_X:
        for y in st.GRID_Y:
            dlm = men["x"][0] <= x <= men["x"][1] and men["y"][0] <= y <= men["y"][1]
            faktor = (0.5 if x in (st.GRID_X[0], st.GRID_X[-1]) else 1.0) * \
                     (0.5 if y in (st.GRID_Y[0], st.GRID_Y[-1]) else 1.0)
            lantai = 6 if dlm else 3
            hasil.append({"x": x, "y": y, "lantai": lantai, "P": per_lantai * lantai * faktor + kolom})
    return hasil


def jumlah_tiang(kode):
    pa = beban_izin(kode)["izin"]
    total, per_kolom = 0, []
    for c in beban_kolom():
        n = max(2, math.ceil(c["P"] / pa))
        per_kolom.append({**c, "n": n})
        total += n
    inti = 7 * 6  # 6 inti tangga + inti lif: ±6 tiang per inti [Asumsi]
    return {"per_kolom": per_kolom, "kolom": total, "inti": inti, "total": total + inti}


def biaya(kode):
    j = jumlah_tiang(kode)
    return j["total"] * kapasitas(kode)["panjang"] * TIANG[kode]["harga_m"]


def ringkasan():
    return {k: {"izin": beban_izin(k), "jumlah": jumlah_tiang(k)["total"], "biaya": biaya(k)} for k in TIANG}



# ------------------------------------------------------------------ gedung utilitas + parkir dan opsi
GU_GRID_X = [100.0, 108.5, 117.0, 125.5, 134.0]
GU_GRID_Y = [44.0, 52.0, 60.0, 68.0, 76.0]
GUDANG_X = 144.0  # tepi barat gudang tetangga (langkah 2.7)


def beban_kolom_gu():
    d, l_ = 9.0, 2.4  # kPa [Asumsi: pelat 200 + finishing ringan; parkir/utilitas rata-rata]
    hasil = []
    for x in GU_GRID_X:
        for y in GU_GRID_Y:
            fx = 0.5 if x in (GU_GRID_X[0], GU_GRID_X[-1]) else 1.0
            fy = 0.5 if y in (GU_GRID_Y[0], GU_GRID_Y[-1]) else 1.0
            hasil.append({"x": x, "y": y, "lantai": 4, "P": (d + l_) * 8.5 * 8.0 * fx * fy * 4 + 120.0})
    return hasil


_GAMBUT = None


def tebal_gambut(x, y):
    """Tebal gambut U3 (m) di (x, y): interpolasi linear titik penyelidikan 2.2, di luar jangkauan titik terdekat."""
    global _GAMBUT
    import numpy as np
    from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator

    import tahap2_stratigrafi as strat
    if _GAMBUT is None:
        t = strat.semua_titik()
        pts = np.array([[a["x"], a["y"]] for a in t])
        nil = np.array([strat.tebal_organik(a) for a in t])
        _GAMBUT = (LinearNDInterpolator(pts, nil), NearestNDInterpolator(pts, nil))
    v = float(_GAMBUT[0](x, y))
    return v if v == v else float(_GAMBUT[1](x, y))


def zona(x, y):
    tg = tebal_gambut(x, y)
    return "SELATAN" if tg < BATAS_ZONA[0] else ("TENGAH" if tg < BATAS_ZONA[1] else "UTARA")


def n_tiang(kode, kolom, per_zona=False):
    if not per_zona:
        pa = beban_izin(kode)["izin"]
        return [{**c, "n": max(2, math.ceil(c["P"] / pa)), "kode": kode, "zona": "SELATAN"} for c in kolom]
    izin = {z: beban_izin(kode, z)["izin"] for z in PROFIL}
    hasil = []
    for c in kolom:
        z = zona(c["x"], c["y"])
        hasil.append({**c, "n": max(2, math.ceil(c["P"] / izin[z])), "kode": kode, "zona": z})
    return hasil


OPSI = {
    "A": {"nama": "Seluruhnya tiang bor Ø800", "utama": "BOR-800", "gu": "BOR-800"},
    "B": {"nama": "Seluruhnya tiang pancang spun Ø600", "utama": "SPUN-600", "gu": "SPUN-600"},
    "C": {"nama": "Hibrida: spun Ø600 di gedung utama, bor Ø800 di gedung utilitas + parkir (dekat gudang)",
          "utama": "SPUN-600", "gu": "BOR-800"},
    "D": {"nama": "Seluruhnya tiang pipa baja Ø610", "utama": "PIPA-610", "gu": "PIPA-610"},
}


def opsi(kunci, per_zona=False):
    """Jumlah dan biaya tiang per opsi. per_zona=True: profil tanah per zona gambut (LA.1); False: profil BH-5 (3.7)."""
    o = OPSI[kunci]
    utama = n_tiang(o["utama"], beban_kolom(), per_zona)
    gu = n_tiang(o["gu"], beban_kolom_gu(), per_zona)
    inti = []
    for cx, cy in list(st.INTI) + [(54.0, 39.0)]:
        z = zona(cx, cy) if per_zona else "SELATAN"
        n = 6 if z == "SELATAN" else math.ceil(6 * beban_izin(o["utama"])["izin"] / beban_izin(o["utama"], z)["izin"])
        inti.append({"x": cx, "y": cy, "n": n, "kode": o["utama"], "zona": z})
    n_utama = sum(c["n"] for c in utama + inti)
    n_gu = sum(c["n"] for c in gu)
    biaya_ = sum(c["n"] * kapasitas(c["kode"], profil=c["zona"])["panjang"] * TIANG[c["kode"]]["harga_m"]
                 for c in utama + inti + gu)
    jarak_pancang = min((GUDANG_X - c["x"] for c in utama + gu if TIANG[c["kode"]]["pancang"]), default=None)
    return {"nama": o["nama"], "n_utama": n_utama, "n_gu": n_gu, "biaya": biaya_, "jarak_pancang_gudang": jarak_pancang,
            "utama": utama, "gu": gu, "inti": inti}


def fmt(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


# ------------------------------------------------------------------ Excel
def buat_excel(keluar=BERKAS):
    import openpyxl

    from format_dokumen import AI, Lembar, set_font_bawaan

    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk alternatif pondasi (langkah 3.7)", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        "Rumus: FHWA NHI-06-089 Vol II hal. 239 (Pers. 9-37a, 9-38), hal. 242-243 (Pers. 9-42, 9-43, 9-45). Syarat: SNI "
        "8460:2017 hal. 194 (FK ≥ 2,5), hal. 204 (gesekan negatif sebagai beban), hal. 295 (likuifaksi FK > 1,1).",
        "Gesekan U1-U5 tidak dihitung (lunak, menurun, dan U5 mudah likuifaksi, langkah 2.6). Gesekan negatif statis di "
        "U1-U4 (urugan ke halaman +12,05 dan konsolidasi sisa); saat likuifaksi di U1-U5.",
        "Ujung tiang ±4 m masuk pasir padat U7 (puncak ±33,6 m di bawah muka tanah asli, BH-1). Panjang dari bawah pile "
        "cap (halaman - 1,2 m).",
        "Beban kolom layan D + L sistem ganda (langkah 3.6). Inti dinding ±6 tiang per inti [Asumsi]. Pelat lantai "
        "dasar dan tiangnya dibahas di Tahap 5.",
        "Indeks harga per meter dan β gesekan negatif [Asumsi]; harga survei di 3.8. Gambar: GK-07.",
    ])], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Profil"), 2, "Profil tanah desain dan tegangan efektif", [8, 12, 12, 12, 12, 12, 30])
    lb.catatan(LABEL + f" Urugan {fmt(urugan()[0])} m (γ 19) sampai halaman; MAT {MAT} m di bawah muka tanah asli.")
    atas = 0.0
    rows = []
    for unit, bawah, g, jenis, su, n60 in LAPISAN:
        rows.append([unit, atas, bawah, g, su if su else ("5,2 + 1,09 z" if unit == "U4" else "-"),
                     n60 if n60 else "-", round(sigma_v(bawah), 1)])
        atas = bawah
    lb.tabel(["Unit", "Atas (m)", "Bawah (m)", "γ (kN/m³)", "su (kPa)", "N60", "σ'v di dasar lapisan (kPa)"], rows,
             rata=list("ccccccc"), fmt=[None, "0.00", "0.00", "0.0", None, None, "0.0"], fill_kolom={6: AI})

    lb = Lembar(wb.create_sheet("Daya Dukung"), 3, "Daya dukung tiang tunggal", [26, 14, 14, 14, 14, 30])
    lb.catatan(LABEL + " Izin = min(Qult/2,5 - NSF statis; Qult/1,1 - NSF likuifaksi).")
    kode = list(TIANG)
    data = [beban_izin(k) for k in kode]
    lb.tabel(["Butir"] + kode + ["Keterangan"], [
        ["Diameter (m)"] + [TIANG[k]["D"] for k in kode] + [""],
        ["Panjang dari bawah pile cap (m)"] + [round(d["panjang"], 1) for d in data] + [""],
        ["Qs U6 + U7 (kN)"] + [round(d["Qs"]) for d in data] + ["α 0,55 su; β σ'v"],
        ["Qb ujung U7 (kN)"] + [round(d["Qb"]) for d in data] + ["57,5 N60, N60 30"],
        ["Qult (kN)"] + [round(d["Qult"]) for d in data] + [""],
        ["NSF statis U1-U4 (kN)"] + [round(d["NSF_statis"]) for d in data] + ["β 0,25 [Asumsi]"],
        ["NSF likuifaksi U1-U5 (kN)"] + [round(d["NSF_lik"]) for d in data] + ["β 0,25/0,35 [Asumsi]"],
        ["Beban izin statis (kN)"] + [round(d["statis"]) for d in data] + ["Qult/2,5 - NSF"],
        ["Beban izin likuifaksi (kN)"] + [round(d["likuifaksi"]) for d in data] + ["Qult/1,1 - NSF"],
        ["Beban izin (kN)"] + [round(d["izin"]) for d in data] + ["menentukan"],
    ], rata=["l"] + ["c"] * len(kode) + ["l"], fill_kolom={i + 1: AI for i in range(len(kode))})

    lb = Lembar(wb.create_sheet("Opsi"), 4, "Perbandingan opsi pondasi", [6, 52, 12, 12, 16, 16, 40])
    lb.catatan(LABEL + " Biaya = jumlah × panjang × indeks harga per meter (bukan RAB).")
    rows = []
    for k in OPSI:
        o = opsi(k)
        rows.append([k, o["nama"], o["n_utama"], o["n_gu"], round(o["biaya"]),
                     "-" if o["jarak_pancang_gudang"] is None else f"{fmt(o['jarak_pancang_gudang'], 0)} m",
                     {"A": "tanpa getaran; casing melindungi beton dari asam (S2); kualitas dikontrol",
                      "B": "termurah; getaran pemancangan 10 m dari gudang bercerucuk; sulit menembus U6/U7",
                      "C": "pancang ≥ 60 m dari gudang; perlu uji tiang (PDA) untuk kepastian; usulan rekayasa nilai",
                      "D": "termahal; korosi tanah asam (pH 3,7-4,0) perlu tebal korosi dan lapisan"}[k]])
    lb.tabel(["Opsi", "Uraian", "Tiang gedung utama", "Tiang GU + parkir", "Biaya (juta Rp, indeks)",
              "Pancang terdekat ke gudang", "Catatan"], rows, rata=list("clccccl"),
             fmt=[None, None, "0", "0", "#,##0", None, None], fill=AI)
    lb.kosong()
    lb.bagian("B", "Usulan")
    lb.tabel(["No", "Butir", "", "", "", "", "Uraian"], [
        [1, "Keputusan Defsa 19 Nov 2026", "", "", "", "", "Opsi A tiang bor Ø800 ke U7: tanpa getaran dekat gudang, kuat terhadap "
         "beban lateral likuifaksi dan penyebaran lateral ke sungai, casing permanen di zona asam."],
        [2, "Rekayasa nilai", "", "", "", "", "Opsi C hibrida dikaji setelah uji pemancangan dan PDA (paket 12) "
         "membuktikan tiang spun menembus U6 dan mencapai daya dukung; selisih biaya dibawa ke 3.8."],
        [3, "Syarat", "", "", "", "", "Uji beban statik tiang uji sebelum produksi; pemantauan getaran dan muka air di "
         "sisi gudang (batas +8,6, langkah 2.8); beton tiang kelas paparan S2."],
    ], rata=list("cl") + ["l"] * 5, fill_kolom={6: AI}, beku=False)
    wb.save(keluar)
    return keluar


# ------------------------------------------------------------------ gambar GK-07
POT_X0 = 160.0  # letak kolom tanah potongan di model space (kanan denah)


def _pola_kelompok(n, s):
    """Posisi tiang relatif terhadap kolom untuk n tiang, jarak s."""
    if n <= 2:
        return [(-s / 2, 0), (s / 2, 0)]
    if n == 3:
        h = s * math.sqrt(3) / 2
        return [(-s / 2, -h / 3), (s / 2, -h / 3), (0, 2 * h / 3)]
    if n == 4:
        return [(-s / 2, -s / 2), (s / 2, -s / 2), (s / 2, s / 2), (-s / 2, s / 2)]
    if n == 5:
        return [(-s / 2, -s / 2), (s / 2, -s / 2), (s / 2, s / 2), (-s / 2, s / 2), (0, 0)]
    return [(-s, -s / 2), (0, -s / 2), (s, -s / 2), (-s, s / 2), (0, s / 2), (s, s / 2)][:max(6, n)]


def gambar_cad(status=None, kunci="A"):
    from cad_lembar import STATUS_SETUJU, Gambar

    o = opsi(kunci)
    dwg = KELUAR / "Gambar" / "DWG" / "GK-07 Rencana Pondasi.dwg"
    png = KELUAR / "Gambar" / "GK-07 Rencana Pondasi.png"

    def k(x0, x1, y0, y1):
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    with Gambar(500) as g:
        for i, x in enumerate(st.GRID_X):
            g.as_grid(str(i + 1), (x, st.GRID_Y[0] - 4), (x, st.GRID_Y[-1] + 4), r_kertas=3.2)
        for j, y in enumerate(st.GRID_Y):
            g.as_grid(st.NAMA_Y[j], (st.GRID_X[0] - 4, y), (st.GRID_X[-1] + 4, y), r_kertas=3.2)
        for c in o["utama"] + o["gu"]:
            d = TIANG[c["kode"]]["D"]
            s = 3 * d
            pos = _pola_kelompok(c["n"], s)
            xs = [c["x"] + p[0] for p in pos]
            ys = [c["y"] + p[1] for p in pos]
            m = d / 2 + 0.4
            g.layer("S-PILECAP", 7, 0.35)
            g.pline(k(min(xs) - m, max(xs) + m, min(ys) - m, max(ys) + m), "S-PILECAP", tutup=True)
            g.layer("S-TIANG", 7, 0.25)
            for px, py in zip(xs, ys):
                g.cmd("circle", {"center": g.mm((px, py)), "radius": d / 2 * 1000})
        g.legenda_tambah("garis", "Pile cap (kepala tiang)", tebal=0.35)
        g.legenda_tambah("garis", f"{TIANG[OPSI[kunci]['utama']]['nama'].split(',')[0]} (lingkaran)", tebal=0.25)
        g.layer("A-MASSA", 7, 0.5, "PHANTOM")
        for nm in ("PODIUM", "GEDUNG UTILITAS"):
            m_ = pr.MASSA[nm]
            g.pline(k(*m_["x"], *m_["y"]), "A-MASSA", tutup=True)
        g.legenda_tambah("garis", "Batas massa bangunan", garis="PHANTOM", tebal=0.5)
        # kolom tanah potongan
        y0 = -10.0  # elevasi model untuk muka tanah asli: y = y0 + elev
        g.layer("G-PROFIL", 7, 0.25)
        pola = {"U1": ("ANSI37", 0.3), "U2": ("ANSI33", 0.3), "U4": ("ANSI32", 0.5), "U5": ("DOTS", 0.3),
                "U6": ("ANSI31", 0.6), "U7": ("DOTS", 0.6)}
        atas = 0.0
        lebar = 10.0
        for unit, bawah, *_ in LAPISAN:
            if atas >= 45:
                break
            bw = min(bawah, 45.0)
            g.arsir(k(POT_X0, POT_X0 + lebar, y0 + ELEV_TANAH - bw, y0 + ELEV_TANAH - atas), "G-PROFIL",
                    pola=pola[unit][0], skala_pola=pola[unit][1])
            ket = {"U1": None, "U2": "U1-U2", "U4": "U4 NSF", "U5": "U5 LIKUIFAKSI", "U6": "U6 GESEKAN",
                   "U7": "U7 UJUNG"}[unit]
            if ket:
                yt = y0 + ELEV_TANAH - ((0.0 if unit == "U2" else atas) + bw) / 2
                g.teks((POT_X0 + lebar + 0.8, yt), ket, "G-PROFIL", 1.6)
            atas = bawah
        hu = urugan()[0]
        g.arsir(k(POT_X0, POT_X0 + lebar, y0 + ELEV_TANAH, y0 + ELEV_TANAH + hu), "G-PROFIL", pola="ANSI37",
                skala_pola=0.6)
        g.teks((POT_X0 + lebar + 0.8, y0 + ELEV_TANAH + hu / 2), "URUGAN", "G-PROFIL", 1.6)
        kp = kapasitas(OPSI[kunci]["utama"])
        dt = TIANG[OPSI[kunci]["utama"]]["D"]
        cx = POT_X0 + lebar / 2
        atas_t, bawah_t = y0 + ELEV_TANAH + hu - 1.2, y0 + ELEV_TANAH - UJUNG
        g.layer("S-TIANG-POT", 7, 0.5)
        g.arsir_lubang(k(cx - dt / 2, cx + dt / 2, bawah_t, atas_t), [], "S-TIANG-POT", pola="SOLID")
        g.layer("G-TEKS", 7, 0.25)
        for el in range(-30, 15, 5):
            g.pline([(POT_X0 - 0.6, y0 + el), (POT_X0, y0 + el)], "G-TEKS")
        g.teks((POT_X0 + lebar / 2, y0 + ELEV_TANAH + hu + 2.5),
               f"Ø{int(dt * 1000)} L ± {kp['panjang']:.0f} M".replace(".", ","), "G-TEKS", 1.6, j="MC", tebal=True)
        pa = beban_izin(OPSI[kunci]["utama"])
        g.lembar("GK-07", "Rencana pondasi tiang", "1:500", pusat=(71, 51), vp=((24, 110), (288, 283)),
                 subjudul=f"Opsi {kunci}: {OPSI[kunci]['nama'].lower()}; langkah 3.7",
                 status=status or STATUS_SETUJU,
                 catatan=[
                     f"Beban izin tiang {fmt(pa['izin'], 0)} kN (Qult {fmt(pa['Qult'], 0)} kN, FK 2,5, NSF statis "
                     f"{fmt(pa['NSF_statis'], 0)} kN).",
                     f"Jumlah tiang: gedung utama {o['n_utama']}, gedung utilitas + parkir {o['n_gu']}.",
                     "Gesekan U1-U5 diabaikan; ujung ±4 m di pasir padat U7.",
                     "Uji beban statik dan PDA sebelum tiang produksi.",
                 ])
        g.viewport_tambahan((290, 40), (331, 283), pusat=(POT_X0 + 9.5, y0 - 8.0), skala=500,
                            judul="Profil tiang", teks_skala="SKALA 1:500")
        g.skala_grafis(185, 22, 25, bagi=5)
        g.simpan(dwg, PDF, png)
    return dwg


def buat():
    buat_excel()
    gambar_cad()
    return BERKAS, PDF

if __name__ == "__main__":
    print("urugan", urugan(), "σ'v 9,46", round(sigma_v(9.46), 1), "σ'v 33,55", round(sigma_v(33.55), 1))
    for k, v in ringkasan().items():
        iz = v["izin"]
        print(k, {a: round(b) for a, b in iz.items()}, "n", v["jumlah"], "biaya", round(v["biaya"]))
    pk = max(beban_kolom(), key=lambda c: c["P"])
    print("kolom maks", pk)
