"""Tahap 5 langkah 5.2: kajian MRI (jarak ke jalur ambulans, beban, tulangan non-magnetik, getaran, bukaan).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (21 Nov 2026); draf, menunggu persetujuan
Defsa. Kunci jawaban tidak dibuka. Data dibaca langsung dari `04 Struktur Atas/Data Owner/Data Beban MEP Rinci.xlsx`
(lembar Syarat MRI, Alat Medis, Daftar Alat, Lift, Data Pabrikan) lewat fungsi baca `tahap5_telaah`.

Metode:
- Jarak dan opsi: geometri (jarak titik ke kotak, `tahap5_telaah.jarak_titik_ke_kotak`); kapasitas parkir dari `tahap3_basement`.
- Beban MRI: pembagian beban peralatan; cek pons dan tumpu satu kaki magnet (SNI 2847:2019 Pasal 22.6.5.2 dan 22.8.3.2).
- Non-magnetik: panjang penyaluran dan lewatan SNI 2847:2019 Pasal 25.4.2 dan 25.5.2; massa SNI 2052:2017.
- Getaran: teori getaran pelat persegi tumpuan sederhana (satu ragam) dan isolator pegas satu derajat kebebasan
  [Asumsi: buku dinamika belum ada di acuan]; pembanding PyNite (elemen pelat) dan deret Navier.
Pasal yang tidak ada di acuan ditulis persis "belum ada di acuan".
"""
from __future__ import annotations

import functools
import math
import re
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import PatternFill

sys.path.insert(0, str(Path(__file__).parent))
import tahap3_basement as t3  # noqa: E402
import tahap4_balok as tbk  # noqa: E402
import tahap4_beban as tb  # noqa: E402
import tahap4_pelat as tp  # noqa: E402
import tahap5_telaah as ts  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
MEP = ts.MEP
BIAYA = AKAR / "03 Desain Konsep" / "3.8 Perkiraan Biaya.xlsx"
KELUAR = AKAR / "05 Struktur Tengah"
BERKAS = KELUAR / "5.2 Kajian MRI.xlsx"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
STATUS = "disetujui Defsa 21 Nov 2026 (opsi 2, baja tahan karat)"
LABEL_AI = f"DIISI AI ATAS PERMINTAAN DEFSA (21 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."
KEPUTUSAN = ("21 Nov 2026: **opsi 2** (jalur ambulans dipindah ke x 92,5-98,5; MRI, sloof, dan kolom tetap) dan "
             "**tulangan baja tahan karat ASTM A955M** (SNI 2847:2019 pasal 20.2.1.3) di zona 2,0 × 2,0 m pelat panel "
             "9-10/D-E. Tindak lanjut: P4 hilang (76 motor, kurang 19 dari 300) dicarikan tempat di Tahap 7 tapak; "
             "R-06 di atas pegas δ ≥ 25 mm; sambungan isolasi panel MRI, beban transit magnet, dan pons kaki diputuskan "
             "di 5.3; permintaan data pabrikan (permeabilitas baja tahan karat, gaya dinamis M-04/R-06) tetap dikirim.")
# teks keputusan Defsa; bila diisi, judul .md menjadi "disetujui Defsa ..." dan ada bagian keputusan

G = 9.81                      # m/s2
FC = tp.FC                    # 30 MPa [4.5, tahap4_pelat]
FY = tp.FY                    # 420 MPa
RHO_BETON = 2400.0            # kg/m3 [Asumsi, massa jenis beton untuk massa getaran]
NU = 0.2                      # [Asumsi: angka Poisson beton]
ZETA = 0.02                   # [Asumsi: redaman pelat beton terisi alat]
ZETA_I = 0.05                 # [Asumsi: redaman isolator pegas]
H_PELAT = 0.25                # m, pelat LT1 [Asumsi, ditetapkan 5.3]
SELIMUT = 50.0                # mm [Asumsi, ditetapkan 5.3]
DB_PELAT, S_PELAT = 13.0, 200.0   # D13-200 atas dan bawah dua arah [Asumsi, ditetapkan 5.3]
LEBAR_PARKIR_MOTOR = 2.0      # m [Asumsi: deretan motor tegak lurus; pedoman parkir belum ada di acuan]
MASSA_BAJA = {"D10": 0.617, "D13": 1.04, "D22": 2.984}   # kg/m [SNI 2052:2017 hal PDF 7-8; D13 terbaca 1,04 (OCR 1,U2)]
SLOOF = {"b": 400.0, "h": 800.0, "selimut": 40.0, "n_atas": 4, "n_bawah": 4, "db": 22.0, "ds": 10.0, "s": 150.0,
         "kait": 75.0}   # [Asumsi: konsep 5.0, ditetapkan 5.4]
GRID_E = ts.GRID_Y[4]         # as E, y 59
GRID_9 = ts.GRID_X[8]         # as 9, x 76
HASIL_PYNITE_MESH = 0.5


def idn(v, d=1):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------------------------------------------ data masukan
def baca_masukan(berkas=MEP):
    """Semua angka MRI dari data owner (teks lembar diurai dengan regex)."""
    wb = openpyxl.load_workbook(berkas, data_only=True)
    sy = {r["Butir"]: r for r in ts.baca_baris(wb, "Syarat MRI", "Butir")}
    m = ts.syarat_mri(berkas)
    it = m["item"]
    f = lambda s: float(str(s).replace(",", "."))   # noqa: E731
    r03, r04, r05, r06 = (it[k]["raw"] for k in ("R-03", "R-04", "R-05", "R-06"))
    kaki = re.search(r"±(\d+(?:,\d+)?) kN pada (\d+(?:,\d+)?) × (\d+(?:,\d+)?) m", r03["Tumpuan / gantungan"])
    pel = re.search(r"dinding (\d+(?:,\d+)?) \+ (\d+(?:,\d+)?) m", r04["Tapak (m)"])
    sangkar = re.search(r"(\d+(?:,\d+)?) × (\d+(?:,\d+)?)", r05["Tapak (m)"])
    getar = sy["Getaran lantai di bawah magnet"]["Syarat"]
    a_batas = re.search(r"(\d+(?:,\d+)?) × 10⁻³ g", getar)
    f_maks = re.search(r"0-(\d+) Hz", getar)
    bukaan = re.search(r"(\d+(?:,\d+)?) × (\d+(?:,\d+)?) m", sy["Jalur masuk magnet"]["Syarat"])
    radius = re.search(r"radius (\d+(?:,\d+)?) m", sy["Pelat dasar ruang MRI"]["Syarat"])
    m04, m01 = it["M-04"]["raw"], it["M-01"]["raw"]
    peg = [r for r in ts.baca_baris(wb, "Data Pabrikan", "Alat") if str(r["Alat"]).startswith("Chiller")][0]
    delta = re.search(r"defleksi statik (\d+) mm", peg["Rekomendasi"])
    return {
        "iso": m["iso"], "d_logam": m["d_logam"], "d_lift": m["d_lift"], "item": it,
        "ruang": it["R-03"]["x"] + it["R-03"]["y"],
        "berat_magnet": float(r03["Berat per unit (kN)"]), "n_kaki": int(re.match(r"(\d+) kaki", r03["Tumpuan / gantungan"]).group(1)),
        "p_kaki": f(kaki.group(1)), "kaki_a": f(kaki.group(2)), "kaki_b": f(kaki.group(3)),
        "berat_pelindung": float(r04["Berat per unit (kN)"]), "dinding": (f(pel.group(1)), f(pel.group(2))),
        "garis_pabrik": 7.3,   # "±7,3 kN/m'" pada kolom Keterangan R-04 (teks); dibandingkan di Beban MRI
        "berat_rf": float(r05["Berat per unit (kN)"]), "rf": (f(sangkar.group(1)), f(sangkar.group(2))),
        "a_batas_mg": f(a_batas.group(1)), "f_maks": float(f_maks.group(1)),
        "bukaan": (f(bukaan.group(1)), f(bukaan.group(2))), "radius": f(radius.group(1)),
        "f_m04": f(re.search(r"\((\d+(?:,\d+)?) Hz\)", m04["Putaran / frekuensi"]).group(1)),
        "f_m01_kipas": f(re.search(r"kipas[^(]*\((\d+(?:,\d+)?) Hz\)", m01["Putaran / frekuensi"]).group(1)),
        "f_r06": f(re.search(r"Getaran (\d+) Hz", r06["Keterangan"]).group(1)),
        "delta_pegas_mm": float(delta.group(1)),
        "lift": {k: it[k]["x"] + it[k]["y"] for k in ("L-1..4", "L-5..6", "L-7")},
        "r09": it["R-09"]["x"] + it["R-09"]["y"], "r07": it["R-07"]["x"] + it["R-07"]["y"],
        "r06_kotak": it["R-06"]["x"] + it["R-06"]["y"],
    }


# ------------------------------------------------------------------ hitungan
def tumpang(a, b):
    """Luas irisan dua kotak (x0, x1, y0, y1); bersinggungan = 0."""
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[2], b[2]))


def jarak(px, py, k):
    return ts.jarak_titik_ke_kotak(px, py, *k)


def vc_koef(b0, d, beta=1.0, alfa_s=40.0):
    """Koefisien vc/(λ√fc') terkecil dari tiga persamaan SNI 2847:2019 Tabel 22.6.5.2."""
    return min(0.33, 0.17 * (1 + 2 / beta), 0.083 * (2 + alfa_s * d / b0))


def respons_h(f, fn, zeta):
    r = f / fn
    return r * r / math.sqrt((1 - r * r) ** 2 + (2 * zeta * r) ** 2)


def transmisibilitas(f, fi, zeta):
    r = f / fi
    return math.sqrt(1 + (2 * zeta * r) ** 2) / math.sqrt((1 - r * r) ** 2 + (2 * zeta * r) ** 2)


def navier_tengah(q, a, D, n=199):
    """Lendutan tengah pelat persegi tumpuan sederhana (deret Navier), q kPa -> m."""
    s = sum((-1) ** ((i + j) // 2 - 1) / (i * j * (i * i / a ** 2 + j * j / a ** 2) ** 2)
            for i in range(1, n, 2) for j in range(1, n, 2))
    return 16 * q * 1000 / (math.pi ** 6 * D) * s


def pynite_pelat(a, h, ec_mpa, nu, q_kpa, mesh=HASIL_PYNITE_MESH):
    """Lendutan tengah (m) pelat a x a tumpuan sederhana di semua tepi, beban merata q (kPa), elemen pelat PyNite."""
    from Pynite import FEModel3D
    e = ec_mpa * 1000.0
    m = FEModel3D()
    m.add_material("c", e, e / (2 * (1 + nu)), nu, 23.6)
    n = int(round(a / mesh))
    for i in range(n + 1):
        for j in range(n + 1):
            m.add_node(f"N{i}_{j}", i * mesh, j * mesh, 0.0)
    for i in range(n):
        for j in range(n):
            m.add_quad(f"Q{i}_{j}", f"N{i}_{j}", f"N{i + 1}_{j}", f"N{i + 1}_{j + 1}", f"N{i}_{j + 1}", h, "c")
            m.add_quad_surface_pressure(f"Q{i}_{j}", -q_kpa, case="D")
    for i in range(n + 1):
        for j in range(n + 1):
            tepi = i in (0, n) or j in (0, n)
            m.def_support(f"N{i}_{j}", True, True, tepi, False, False, True)
    m.add_load_combo("U", {"D": 1.0})
    m.analyze_linear(check_statics=False, sparse=True)
    return abs(float(m.nodes[f"N{n // 2}_{n // 2}"].DZ["U"]))


@functools.lru_cache(maxsize=1)
def hitung():
    mi = baca_masukan()
    px, py = mi["iso"]
    d12, d8 = mi["d_logam"], mi["d_lift"]
    ru = mi["ruang"]                                       # x0, x1, y0, y1 ruang MRI awal
    lajur = (ts.JALUR_X[0], ts.JALUR_X[1], ts.JALUR_Y[0], ts.JALUR_Y[1])
    p4 = ts.P4
    lebar_lajur = lajur[1] - lajur[0]
    r = {"mi": mi, "lajur": lajur, "p4": p4}

    # ---- jarak dan opsi
    j0 = jarak(px, py, (lajur[0], lajur[0], lajur[2], lajur[3]))
    o1x = lajur[0] - d12
    hw = (ru[1] - ru[0]) / 2
    ru1 = (o1x - hw, o1x + hw, ru[2], ru[3])
    jl = {k: jarak(o1x, py, v) for k, v in mi["lift"].items()}
    d_as9, d_asE = abs(o1x - GRID_9), abs(py - GRID_E)
    o1 = {"iso_x": o1x, "ruang": ru1, "j_lajur": jarak(o1x, py, (lajur[0], lajur[0], lajur[2], lajur[3])),
          "j_p4": jarak(o1x, py, (p4[0], p4[0], p4[2], p4[3])), "j_lift": jl, "d_as9": d_as9, "d_asE": d_asE,
          "d_kolom": math.hypot(d_as9, d_asE), "ov_r09": tumpang(ru1, mi["r09"]), "ov_r07": tumpang(ru1, mi["r07"]),
          "ov_r06": tumpang(ru1, mi["r06_kotak"]), "koridor_p": ru[1] - ru1[1], "koridor_l": mi["bukaan"][0]}
    tepi2 = px + d12
    laj2 = (tepi2, tepi2 + lebar_lajur)
    sisa = p4[1] - laj2[1]
    luas_p4 = (p4[1] - p4[0]) * (p4[3] - p4[2])
    tertutup = max(0.0, min(laj2[1], p4[1]) - max(laj2[0], p4[0])) * (p4[3] - p4[2])
    sempit = max(0.0, p4[1] - max(laj2[1], p4[0])) * (p4[3] - p4[2])
    hilang_luas = luas_p4 if sisa < LEBAR_PARKIR_MOTOR else tertutup
    per_motor = t3.LUAS_PER["motor"]
    motor_total = sum(z["jumlah"] for z in t3.kapasitas_permukaan() if z["jenis"] == "motor")
    motor_hilang = int(hilang_luas // per_motor)
    o2 = {"tepi": tepi2, "lajur": laj2, "j_lajur": jarak(px, py, (tepi2, tepi2, lajur[2], lajur[3])), "sisa_p4": sisa,
          "luas_p4": luas_p4, "tertutup": tertutup, "sempit": sempit, "hilang_luas": hilang_luas,
          "motor_per": per_motor, "motor_total": motor_total, "motor_hilang": motor_hilang,
          "motor_sisa": motor_total - motor_hilang, "motor_butuh": t3.KEBUTUHAN["motor"],
          "motor_kurang": t3.KEBUTUHAN["motor"] - (motor_total - motor_hilang), "amb_butuh": t3.KEBUTUHAN["ambulans"],
          "persil_x": 140.0}
    r.update({"j0": j0, "o1": o1, "o2": o2})

    # ---- beban MRI
    a_kaki = mi["kaki_a"] * mi["kaki_b"]
    q_kaki = mi["p_kaki"] / a_kaki
    pj = sum(mi["dinding"])
    q_pel = mi["berat_pelindung"] / pj
    luas_rf = mi["rf"][0] * mi["rf"][1]
    q_rf = mi["berat_rf"] / luas_rf
    d = H_PELAT * 1000 - SELIMUT - DB_PELAT
    c = mi["kaki_a"] * 1000
    b0 = 4 * (c + d)
    vcko = vc_koef(b0, d)
    phivc = 0.75 * vcko * 1.0 * math.sqrt(FC) * b0 * d / 1000
    vu = 1.2 * mi["p_kaki"]
    phi_tumpu = 0.65 * 0.85 * FC * 1000       # kPa, A2/A1 = 1 (konservatif)
    r["beban"] = {"a_kaki": a_kaki, "q_kaki": q_kaki, "pj": pj, "q_pel": q_pel, "luas_rf": luas_rf, "q_rf": q_rf,
                  "cek_kaki": mi["n_kaki"] * mi["p_kaki"] / mi["berat_magnet"] - 1,
                  "sel_pel": (q_pel / mi["garis_pabrik"] - 1), "lo": 2.87, "d": d, "b0": b0, "vcko": vcko,
                  "phivc": phivc, "vu": vu, "rasio_pons": vu / phivc, "phi_tumpu": phi_tumpu,
                  "tegangan": 1.2 * q_kaki, "rasio_tumpu": 1.2 * q_kaki / phi_tumpu}

    # ---- non-magnetik
    sisi = 2 * mi["radius"]
    nb = sisi * 1000 / S_PELAT + 1
    ld13 = FY / (2.1 * math.sqrt(FC)) * 13
    lap13 = 1.3 * ld13
    pakai13 = math.ceil(lap13 / 10) * 10
    pj13 = sisi + 2 * pakai13 / 1000
    berat_pelat = 4 * nb * pj13 * MASSA_BAJA["D13"]
    ld22 = FY / (1.7 * math.sqrt(FC)) * 22
    lap22 = 1.3 * ld22
    pakai22 = math.ceil(lap22 / 10) * 10
    pj22 = sisi + 2 * pakai22 / 1000
    n_bar = SLOOF["n_atas"] + SLOOF["n_bawah"]
    berat_bar = n_bar * pj22 * MASSA_BAJA["D22"]
    n_sk = math.ceil(sisi * 1000 / SLOOF["s"]) + 1
    kel = 2 * ((SLOOF["b"] - 2 * SLOOF["selimut"]) + (SLOOF["h"] - 2 * SLOOF["selimut"])) + 2 * SLOOF["kait"]
    berat_sk = n_sk * kel / 1000 * MASSA_BAJA["D10"]
    r["nm"] = {"sisi": sisi, "nb": nb, "ld13": ld13, "lap13": lap13, "pakai13": pakai13, "pj13": pj13,
               "berat_pelat": berat_pelat, "ld22": ld22, "lap22": lap22, "pakai22": pakai22, "pj22": pj22,
               "n_bar": n_bar, "berat_bar": berat_bar, "n_sk": n_sk, "kel": kel, "berat_sk": berat_sk,
               "berat_sloof": berat_bar + berat_sk, "berat_opsi1": berat_pelat + berat_bar + berat_sk}

    # ---- getaran
    ec = 4700 * math.sqrt(FC)
    Dk = ec * 1e6 * H_PELAT ** 3 / (12 * (1 - NU ** 2))
    a = 8.0
    m_sendiri = RHO_BETON * H_PELAT
    m_rf = mi["berat_rf"] * 1000 / luas_rf / G
    m = m_sendiri + m_rf
    fn = math.pi / 2 * (1 / a ** 2 + 1 / a ** 2) * math.sqrt(Dk / m)
    mm = m * a * a / 4
    ab = mi["a_batas_mg"] * 1e-3 * G
    fi = math.sqrt(G / (mi["delta_pegas_mm"] / 1000)) / (2 * math.pi)
    sumber = {}
    for kode, f in (("M-04", mi["f_m04"]), ("R-06", mi["f_r06"]), ("M-01", mi["f_m01_kipas"])):
        h = respons_h(f, fn, ZETA)
        sumber[kode] = {"f": f, "H": h, "F": ab * mm / h, "r": f / fn}
    t_m04 = transmisibilitas(mi["f_m04"], fi, ZETA_I)
    t_r06 = transmisibilitas(mi["f_r06"], fi, ZETA_I)
    q_pelat = m * G / 1000
    d_pyn = pynite_pelat(a, H_PELAT, ec, NU, q_pelat)
    d_nav = navier_tengah(q_pelat, a, Dk)
    r["getar"] = {"ec": ec, "D": Dk, "m_sendiri": m_sendiri, "m_rf": m_rf, "m": m, "fn": fn, "M_modal": mm,
                  "a_batas": ab, "fi": fi, "sumber": sumber, "T_m04": t_m04, "T_r06": t_r06,
                  "F_m04_sumber": sumber["M-04"]["F"] / t_m04, "F_r06_pegas": sumber["R-06"]["F"] / t_r06,
                  "q": q_pelat, "d_pynite": d_pyn, "d_navier": d_nav, "fn_rayleigh": 0.18 * math.sqrt(G / d_pyn),
                  "sel_rayleigh": 0.18 * math.sqrt(G / d_pyn) / fn - 1, "sel_pyn_nav": d_pyn / d_nav - 1}

    # ---- bukaan
    rc = tbk.rancang()
    kunci = [v for k, v in tbk._kunci_kelompok().items()
             if k[0] == "LT2" and abs(k[1] - 84.0) < 1e-6 and abs(k[3] - 84.0) < 1e-6]
    kel_b = kunci[0]
    bb, hb = rc["ukuran"].get(kel_b, (tb.BALOK_B, tb.BALOK_H))
    lt1, lt2 = tb.LEVEL["LT1"], tb.LEVEL["LT2"]
    atas = lt1 + mi["bukaan"][1]
    bawah = lt2 - hb
    ujung = [d_ for d_ in tbk.tm.DINDING_UJUNG if abs(d_[2] - 84.0) < 1e-6]
    r["bukaan"] = {"lt1": lt1, "lt2": lt2, "kel_balok": kel_b, "b_balok": bb, "h_balok": hb, "atas": atas,
                   "bawah_balok": bawah, "sisa": bawah - atas, "halaman": ts.HALAMAN, "beda": lt1 - ts.HALAMAN,
                   "y0": py - mi["bukaan"][0] / 2, "y1": py + mi["bukaan"][0] / 2,
                   "ke_as_E": GRID_E - (py + mi["bukaan"][0] / 2), "dinding_ujung": ujung,
                   "koridor": o1["koridor_p"]}

    # ---- cek silang T-91
    r["t91"] = {"a_tangan": lajur[0] - px, "a_skrip": j0, "b_fn": fn, "b_ray": r["getar"]["fn_rayleigh"],
                "c_tangan": 44 * 3.24 * 1.04, "c_skrip": berat_pelat}
    return r


# ------------------------------------------------------------------ lembar Excel: pembantu
KEP = ["No", "Besaran", "Nilai", "Satuan", "Rumus / dasar", "Sumber"]
LEBAR = [5, 46, 14, 10, 46, 46]
REF: dict = {}
LABEL_PAKAI: set = set()


def R(key, label, nilai, sat="", rumus="", sumber="", fmt="0.00", py=None):
    return {"key": key, "label": label, "nilai": nilai, "sat": sat, "rumus": rumus, "sumber": sumber, "fmt": fmt, "py": py}


def _sub(tpl, sheet):
    def f(mm):
        s, a = REF[mm.group(1)]
        return a if s == sheet else f"'{s}'!{a}"
    return re.sub(r"\{(\w+)\}", f, tpl)


def tabel_hitung(lb, rows, beku=False):
    """Tabel besaran: nilai angka = masukan (sel hijau AI); nilai berawalan '=' = rumus Excel (tanpa isi)."""
    ws = lb.ws
    r0 = lb.baris
    for i, rw in enumerate(rows):
        assert rw["key"] not in REF, f"kunci ganda {rw['key']}"
        assert (ws.title, rw["label"]) not in LABEL_PAKAI, f"label ganda {rw['label']}"
        LABEL_PAKAI.add((ws.title, rw["label"]))
        REF[rw["key"]] = (ws.title, f"{lb.kol(2)}{r0 + 1 + i}")
    data = [[i + 1, rw["label"], None, rw["sat"], rw["rumus"], rw["sumber"]] for i, rw in enumerate(rows)]
    _, a0, a1 = lb.tabel(KEP, data, rata=list("clccll"), beku=beku)
    for i, rw in enumerate(rows):
        c = ws[f"{lb.kol(2)}{a0 + i}"]
        v = rw["nilai"]
        if isinstance(v, str) and v.startswith("="):
            c.value = _sub(v, ws.title)
        else:
            c.value = v
            from format_dokumen import AI
            c.fill = PatternFill("solid", fgColor=AI)
        c.number_format = rw["fmt"]
    return a0, a1


def fj(px, py, x0, x1, y0, y1):
    """Rumus Excel jarak titik ke kotak (0 bila di dalam)."""
    return f"=SQRT(MAX({x0}-{px},0,{px}-{x1})^2+MAX({y0}-{py},0,{py}-{y1})^2)"


def fov(a, b):
    """Rumus Excel luas irisan dua kotak (x0, x1, y0, y1) berisi string sel atau angka."""
    return (f"=MAX(0,MIN({a[1]},{b[1]})-MAX({a[0]},{b[0]}))*MAX(0,MIN({a[3]},{b[3]})-MAX({a[2]},{b[2]}))")


# ------------------------------------------------------------------ baris per lembar
def baris_jarak(r):
    mi, o1, o2 = r["mi"], r["o1"], r["o2"]
    ru, la, p4 = mi["ruang"], r["lajur"], r["p4"]
    L1, L2, L3 = mi["lift"]["L-1..4"], mi["lift"]["L-5..6"], mi["lift"]["L-7"]
    a = [
        R("iso_x", "Isocenter x", mi["iso"][0], "m", "", "[Syarat MRI 1]"),
        R("iso_y", "Isocenter y", mi["iso"][1], "m", "", "[Syarat MRI 1]"),
        R("d_logam", "Syarat jarak benda logam bergerak besar", mi["d_logam"], "m", "", "[Syarat MRI 2]"),
        R("d_lift", "Syarat jarak lift", mi["d_lift"], "m", "", "[Syarat MRI 3]"),
        R("ru_x0", "Ruang MRI awal, x barat", ru[0], "m", "", "[Syarat MRI 1, R-03]"),
        R("ru_x1", "Ruang MRI awal, x timur (tepi gedung as 10)", ru[1], "m", "", "[Syarat MRI 1, R-03]"),
        R("ru_y0", "Ruang MRI, y selatan", ru[2], "m", "", "[Syarat MRI 1, R-03]"),
        R("ru_y1", "Ruang MRI, y utara", ru[3], "m", "", "[Syarat MRI 1, R-03]"),
        R("la_x0", "Lajur ambulans, tepi barat", la[0], "m", "", "[Asumsi, 5.0: lebar 6 m, sumbu x 91 (tahap3_basement)]"),
        R("la_x1", "Lajur ambulans, tepi timur", la[1], "m", "", "[Asumsi, 5.0]"),
        R("la_y0", "Lajur ambulans, y selatan", la[2], "m", "", "[Asumsi, 5.0: lajur menerus setinggi zona P4]"),
        R("la_y1", "Lajur ambulans, y utara", la[3], "m", "", "[Asumsi, 5.0]"),
        R("p4_x0", "Zona parkir P4, x barat", p4[0], "m", "", "[3.5, tahap3_basement P4 timur]"),
        R("p4_x1", "Zona parkir P4, x timur", p4[1], "m", "", "[3.5]"),
        R("p4_y0", "Zona parkir P4, y selatan", p4[2], "m", "", "[3.5]"),
        R("p4_y1", "Zona parkir P4, y utara", p4[3], "m", "", "[3.5]"),
        R("r_nm", "Radius tanpa tulangan baja di sekitar isocenter", mi["radius"], "m", "", "[Syarat MRI 7]"),
    ]
    b = [
        R("j0", "Opsi 0: jarak isocenter ke tepi barat lajur", fj("{iso_x}", "{iso_y}", "{la_x0}", "{la_x0}", "{la_y0}", "{la_y1}"),
          "m", "jarak titik ke kotak (lajur dianggap garis x 88)", "[Syarat MRI 2]", "0.00", r["j0"]),
        R("kurang0", "Opsi 0: kekurangan terhadap syarat", "={d_logam}-{j0}", "m", "syarat - jarak", "", "0.00", mi["d_logam"] - r["j0"]),
        R("ok0", "Opsi 0: status", '=IF({j0}>={d_logam},"memenuhi","tidak memenuhi")', "", "bandingkan dengan 12,0 m", ""),
    ]
    c = [
        R("o1x", "Opsi 1: isocenter x baru (tepi lajur - syarat)", "={la_x0}-{d_logam}", "m", "88 - 12", "geser MRI ke barat", "0.00", o1["iso_x"]),
        R("o1hw", "Opsi 1: setengah lebar ruang", "=({ru_x1}-{ru_x0})/2", "m", "isocenter tetap di tengah ruang", "", "0.00", (ru[1] - ru[0]) / 2),
        R("o1x0", "Opsi 1: ruang x barat", "={o1x}-{o1hw}", "m", "", "", "0.00", o1["ruang"][0]),
        R("o1x1", "Opsi 1: ruang x timur", "={o1x}+{o1hw}", "m", "", "", "0.00", o1["ruang"][1]),
        R("j1", "Opsi 1: jarak isocenter ke tepi barat lajur", fj("{o1x}", "{iso_y}", "{la_x0}", "{la_x0}", "{la_y0}", "{la_y1}"),
          "m", "", "", "0.00", o1["j_lajur"]),
        R("m1", "Opsi 1: margin terhadap syarat", "={j1}-{d_logam}", "m", "0 = tepat batas, tanpa cadangan", "", "0.00", o1["j_lajur"] - mi["d_logam"]),
        R("ket1", "Opsi 1: status", '=IF(ABS({m1})<0.000001,"tepat batas",IF({m1}>0,"memenuhi","tidak memenuhi"))', "", "", ""),
        R("jp4", "Opsi 1: jarak isocenter ke tepi barat P4", fj("{o1x}", "{iso_y}", "{p4_x0}", "{p4_x0}", "{p4_y0}", "{p4_y1}"),
          "m", "", "", "0.00", o1["j_p4"]),
        R("jl14", "Opsi 1: jarak ke lift L-1..4 (syarat 8,0 m)", fj("{o1x}", "{iso_y}", *L1), "m",
          f"kotak x {idn(L1[0])}-{idn(L1[1])} / y {idn(L1[2])}-{idn(L1[3])}", "[Lift]", "0.00", o1["j_lift"]["L-1..4"]),
        R("jl56", "Opsi 1: jarak ke lift L-5..6", fj("{o1x}", "{iso_y}", *L2), "m",
          f"kotak x {idn(L2[0])}-{idn(L2[1])} / y {idn(L2[2])}-{idn(L2[3])}", "[Lift]", "0.00", o1["j_lift"]["L-5..6"]),
        R("jl7", "Opsi 1: jarak ke lift L-7", fj("{o1x}", "{iso_y}", *L3), "m",
          f"kotak x {idn(L3[0])}-{idn(L3[1])} / y {idn(L3[2])}-{idn(L3[3])}", "[Lift]", "0.00", o1["j_lift"]["L-7"]),
        R("das9", "Opsi 1: jarak isocenter ke as 9 (sloof dan balok x 76)", f"=ABS({{o1x}}-{GRID_9})", "m",
          "sloof as 9 melewati isocenter", "[grid, tahap5_telaah]", "0.00", o1["d_as9"]),
        R("dasE", "Opsi 1: jarak isocenter ke as E (y 59)", f"=ABS({{iso_y}}-{GRID_E})", "m", "", "", "0.00", o1["d_asE"]),
        R("dkol", "Opsi 1: jarak isocenter ke kolom 9/E (76; 59)", "=SQRT({das9}^2+{dasE}^2)", "m",
          "kolom di dalam ruang MRI baru", "", "0.00", o1["d_kolom"]),
        R("ov09", "Opsi 1: tumpang tindih ruang dengan R-09 (dinding timbal)",
          fov(("{o1x0}", "{o1x1}", "{ru_y0}", "{ru_y1}"), mi["r09"]), "m²",
          f"R-09 x {idn(mi['r09'][0])}-{idn(mi['r09'][1])} / y {idn(mi['r09'][2])}-{idn(mi['r09'][3])}", "[Alat Medis R-09]", "0.00", o1["ov_r09"]),
        R("ov07", "Opsi 1: tumpang tindih dengan R-07/R-08 (ruang X-ray)",
          fov(("{o1x0}", "{o1x1}", "{ru_y0}", "{ru_y1}"), mi["r07"]), "m²",
          f"R-07 x {idn(mi['r07'][0])}-{idn(mi['r07'][1])} / y {idn(mi['r07'][2])}-{idn(mi['r07'][3])}", "[Alat Medis R-07]", "0.00", o1["ov_r07"]),
        R("ov06", "Opsi 1: tumpang tindih dengan R-06 (kompresor)",
          fov(("{o1x0}", "{o1x1}", "{ru_y0}", "{ru_y1}"), mi["r06_kotak"]), "m²",
          "0 = bersinggungan di y 60, harus dipindah", "[Alat Medis R-06]", "0.00", o1["ov_r06"]),
        R("kor_p", "Opsi 1: panjang koridor masuk magnet (dinding ruang ke tepi gedung)", "={ru_x1}-{o1x1}", "m", "84 - 79,5", "", "0.00", o1["koridor_p"]),
        R("kor_l", "Opsi 1: lebar koridor masuk magnet", mi["bukaan"][0], "m", "", "[Syarat MRI 8]"),
    ]
    d = [
        R("o2t", "Opsi 2: tepi barat lajur baru (isocenter + syarat)", "={iso_x}+{d_logam}", "m", "80,5 + 12", "", "0.00", o2["tepi"]),
        R("o2e", "Opsi 2: tepi timur lajur baru (lebar tetap)", "={o2t}+({la_x1}-{la_x0})", "m", "lebar 6 m", "", "0.00", o2["lajur"][1]),
        R("j2", "Opsi 2: jarak isocenter ke tepi barat lajur baru", fj("{iso_x}", "{iso_y}", "{o2t}", "{o2t}", "{la_y0}", "{la_y1}"),
          "m", "", "", "0.00", o2["j_lajur"]),
        R("sisa", "Opsi 2: lebar sisa P4 di timur lajur", "={p4_x1}-{o2e}", "m", "100 - 98,5", "", "0.00", o2["sisa_p4"]),
        R("lpm", "Lebar minimum deretan parkir motor", LEBAR_PARKIR_MOTOR, "m", "", "[Asumsi: pedoman parkir belum ada di acuan]"),
        R("lp4", "Luas P4", "=({p4_x1}-{p4_x0})*({p4_y1}-{p4_y0})", "m²", "", "", "0.00", o2["luas_p4"]),
        R("ltup", "Luas P4 tertutup lajur baru", "=MAX(0,MIN({o2e},{p4_x1})-MAX({o2t},{p4_x0}))*({p4_y1}-{p4_y0})", "m²", "", "", "0.00", o2["tertutup"]),
        R("lsem", "Luas sisa P4 sempit (tidak terpakai)", "=MAX(0,{p4_x1}-MAX({o2e},{p4_x0}))*({p4_y1}-{p4_y0})", "m²", "", "", "0.00", o2["sempit"]),
        R("lhil", "Luas P4 hilang", "=IF({sisa}<{lpm},{lp4},{ltup})", "m²", "sisa < lebar minimum: seluruh P4 hilang", "", "0.00", o2["hilang_luas"]),
        R("mper", "Luas per motor", o2["motor_per"], "m²", "", "[Asumsi, tahap3_basement.LUAS_PER]"),
        R("mhil", "Motor hilang dari P4", "=INT({lhil}/{mper})", "unit", "", "", "0", o2["motor_hilang"]),
        R("mtot", "Motor tersedia (P3 + P4 + P5)", o2["motor_total"], "unit", "tahap3_basement.kapasitas_permukaan", "[3.5, Tahap 3]", "0"),
        R("msisa", "Motor sisa setelah P4 hilang", "={mtot}-{mhil}", "unit", "", "", "0", o2["motor_sisa"]),
        R("mbut", "Kebutuhan motor", o2["motor_butuh"], "unit", "", "[surat owner 034 butir 4]", "0"),
        R("mkur", "Kekurangan motor", "={mbut}-{msisa}", "unit", "positif = kurang", "", "0", o2["motor_kurang"]),
        R("abut", "Kebutuhan ambulans (di drop-off IGD, bukan di P4)", o2["amb_butuh"], "unit", "kapasitas P4 hanya dihitung motor",
          "[tahap3_basement: 4 ambulans di drop-off IGD]", "0"),
        R("persil", "Batas persil timur", o2["persil_x"], "m", "lajur 92,5-98,5 di dalam persil; gedung utilitas x 100-134 tidak tersentuh",
          "[TOR 4.1, tahap3_tapak.LX; GSB timur x 134; cek di Tahap 7]"),
    ]
    return [("A", "Masukan dari data owner dan Tahap 3", a), ("B", "Opsi 0: MRI tetap (80,5; 57,0)", b),
            ("C", "Opsi 1: geser MRI ke barat", c), ("D", "Opsi 2: pindah jalur ambulans ke timur", d)]


def baris_beban(r):
    mi, b = r["mi"], r["beban"]
    a = [
        R("w_mag", "Berat magnet MRI (R-03)", mi["berat_magnet"], "kN", "", "[Alat Medis R-03]", "0.0"),
        R("n_kaki", "Jumlah kaki", mi["n_kaki"], "buah", "", "[Alat Medis R-03]", "0"),
        R("p_kaki", "Beban per kaki", mi["p_kaki"], "kN", "teks data owner: ±12 kN", "[Alat Medis R-03]", "0.0"),
        R("cek_kaki", "Cek 4 x kaki terhadap berat magnet", "={n_kaki}*{p_kaki}/{w_mag}-1", "-", "selisih relatif (data owner membulatkan)", "", "0.0%", b["cek_kaki"]),
        R("a_kaki", "Luas tapak satu kaki (0,25 x 0,25)", f"={mi['kaki_a']}*{mi['kaki_b']}", "m²", "", "[Alat Medis R-03]", "0.0000", b["a_kaki"]),
        R("q_kaki", "Tekanan per kaki magnet", "={p_kaki}/{a_kaki}", "kPa", "beban mati (peralatan layanan tetap)", "SNI 1727:2020 Pasal 3.1.3 (hal PDF 46)", "0.0", b["q_kaki"]),
        R("w_pel", "Berat pelindung baja (R-04)", mi["berat_pelindung"], "kN", "", "[Alat Medis R-04]", "0.0"),
        R("pj", "Panjang dinding berpelindung (timur 7,0 + utara 6,0)", f"={mi['dinding'][0]}+{mi['dinding'][1]}", "m", "", "[Alat Medis R-04]", "0.0", b["pj"]),
        R("q_pel", "Beban garis pelindung", "={w_pel}/{pj}", "kN/m'", "93,2 / 13", "SNI 1727:2020 Pasal 3.1.3", "0.000", b["q_pel"]),
        R("q_pab", "Nilai tertulis di data owner (kolom Keterangan R-04)", mi["garis_pabrik"], "kN/m'", "±7,3", "[Alat Medis R-04]", "0.0"),
        R("sel_pel", "Selisih hitungan terhadap data owner", "={q_pel}/{q_pab}-1", "-", "selisih 1,8 % (data owner membulatkan; dipakai 7,17)", "", "0.0%", b["sel_pel"]),
        R("w_rf", "Berat sangkar RF (R-05)", mi["berat_rf"], "kN", "", "[Alat Medis R-05]", "0.0"),
        R("luas_rf", "Luas sangkar RF (7,0 x 6,0)", f"={mi['rf'][0]}*{mi['rf'][1]}", "m²", "", "[Alat Medis R-05]", "0.0", b["luas_rf"]),
        R("q_rf", "Beban merata sangkar RF", "={w_rf}/{luas_rf}", "kPa", "27,5 / 42", "SNI 1727:2020 Pasal 3.1.3", "0.000", b["q_rf"]),
        R("lo", "Beban hidup ruang MRI (ruang operasi, laboratorium)", b["lo"], "kPa", "60 psf = 2,87 kPa",
          "SNI 1727:2020 Tabel 4.3-1, rumah sakit (hal PDF 52)", "0.00"),
    ]
    c = [
        R("h", "Tebal pelat LT1", H_PELAT * 1000, "mm", "", "[Asumsi, ditetapkan 5.3]", "0"),
        R("sel", "Selimut beton", SELIMUT, "mm", "", "[Asumsi, ditetapkan 5.3]", "0"),
        R("db", "Diameter tulangan", DB_PELAT, "mm", "D13", "[Asumsi, ditetapkan 5.3]", "0"),
        R("d", "Tinggi efektif d", "={h}-{sel}-{db}", "mm", "memakai db penuh (konservatif)", "", "0", b["d"]),
        R("c", "Sisi tapak kaki", mi["kaki_a"] * 1000, "mm", "", "[Alat Medis R-03]", "0"),
        R("b0", "Keliling penampang kritis b0", "=4*({c}+{d})", "mm", "4 (c + d), d/2 dari tepi kaki", "SNI 2847:2019 Pasal 22.6.4.1 (hal PDF 518)", "0", b["b0"]),
        R("vck", "Koefisien vc / (λ √fc'): terkecil dari tiga", "=MIN(0.33,0.17*(1+2/1),0.083*(2+40*{d}/{b0}))", "-",
          "β = 1, αs = 40 (kolom dalam), λ = 1", "SNI 2847:2019 Tabel 22.6.5.2 (hal PDF 521)", "0.000", b["vcko"]),
        R("fc", "Kuat tekan beton fc'", FC, "MPa", "", "[3.6, tahap4_pelat.FC]", "0"),
        R("phivc", "φVc satu kaki", "=0.75*{vck}*SQRT({fc})*{b0}*{d}/1000", "kN", "φ = 0,75 (geser)",
          "SNI 2847:2019 Tabel 21.2.1 (hal PDF 491), 22.6.5.2", "0.0", b["phivc"]),
        R("vu", "Vu satu kaki = 1,2 x 12 kN", "=1.2*{p_kaki}", "kN", "beban mati saja", "SNI 2847:2019 Tabel 5.3.1, Pers. 5.3.1b (hal PDF 106)", "0.0", b["vu"]),
        R("rasio", "Rasio pons Vu / φVc", "={vu}/{phivc}", "-", "< 1,0 cukup untuk penyaring; desain final 5.3", "", "0.000", b["rasio_pons"]),
        R("phit", "φ x 0,85 fc' (tumpu, A2/A1 = 1)", "=0.65*0.85*{fc}*1000", "kPa", "φ = 0,65 (tumpu)",
          "SNI 2847:2019 Pasal 22.8.3.2 (hal PDF 540), Tabel 21.2.1", "#,##0", b["phi_tumpu"]),
        R("tegang", "Tekanan terfaktor kaki 1,2 x 192", "=1.2*{q_kaki}", "kPa", "", "", "0.0", b["tegangan"]),
        R("rasio_t", "Rasio tumpu", "={tegang}/{phit}", "-", "", "", "0.000", b["rasio_tumpu"]),
    ]
    return [("A", "Beban peralatan MRI (semua beban mati) dan beban hidup", a),
            ("B", "Penyaring pons dan tumpu satu kaki magnet (desain final di 5.3)", c)]


def baris_nm(r):
    mi, n = r["mi"], r["nm"]
    a = [
        R("sisi", "Sisi kotak zona tanpa baja (2 x radius)", "=2*{r_nm}", "m", "kotak 2,0 x 2,0 m melingkupi lingkaran r 1,0 m",
          "[Syarat MRI 7]", "0.00", n["sisi"]),
        R("s", "Spasi tulangan pelat", S_PELAT, "mm", "D13-200 atas dan bawah dua arah", "[Asumsi, ditetapkan 5.3]", "0"),
        R("nb", "Batang per lapis per arah", "={sisi}*1000/{s}+1", "buah", "2000/200 + 1", "", "0", n["nb"]),
        R("fy", "fy", FY, "MPa", "", "[3.6, tahap4_pelat.FY]", "0"),
        R("fc2", "fc'", FC, "MPa", "", "[3.6]", "0"),
        R("ld13", "ld D13 = fy ψt ψe / (2,1 λ √fc') db", "={fy}*1*1/(2.1*1*SQRT({fc2}))*13", "mm",
          "ψt = ψe = λ = 1; spasi ≥ 2db dan selimut ≥ db", "SNI 2847:2019 Tabel 25.4.2.2 (hal PDF 588)", "0.0", n["ld13"]),
        R("lap13", "Lewatan kelas B D13 = 1,3 ld", "=1.3*{ld13}", "mm", "", "SNI 2847:2019 Tabel 25.5.2.1 (hal PDF 608)", "0.0", n["lap13"]),
        R("pk13", "Panjang lewatan D13 dipakai (dibulatkan ke atas 10 mm)", "=CEILING({lap13},10)", "mm", "", "", "0", n["pakai13"]),
        R("pj13", "Panjang satu batang tahan karat (zona + 2 lewatan)", "={sisi}+2*{pk13}/1000", "m", "2,0 + 2 x 0,62", "", "0.00", n["pj13"]),
        R("ms13", "Massa D13", MASSA_BAJA["D13"], "kg/m", "", "SNI 2052:2017 (hal PDF 8; terbaca 1,U2 = 1,04)", "0.000"),
        R("bp", "Berat tulangan tahan karat pelat (4 lapis)", "=4*{nb}*{pj13}*{ms13}", "kg", "4 lapis x 11 batang x 3,24 m x 1,04", "", "0.0", n["berat_pelat"]),
    ]
    b = [
        R("sl_b", "Sloof as 9, lebar", SLOOF["b"], "mm", "", "[Asumsi, konsep 5.0; ditetapkan 5.4]", "0"),
        R("sl_h", "Sloof as 9, tinggi", SLOOF["h"], "mm", "", "[Asumsi]", "0"),
        R("sl_n", "Jumlah batang longitudinal (4 atas + 4 bawah) D22", n["n_bar"], "buah", "", "[Asumsi, ditetapkan 5.4]", "0"),
        R("ld22", "ld D22 = fy ψt ψe / (1,7 λ √fc') db", "={fy}/(1.7*SQRT({fc2}))*22", "mm", "", "SNI 2847:2019 Tabel 25.4.2.2 (hal PDF 588)", "0.0", n["ld22"]),
        R("lap22", "Lewatan kelas B D22 = 1,3 ld", "=1.3*{ld22}", "mm", "", "SNI 2847:2019 Tabel 25.5.2.1 (hal PDF 608)", "0.0", n["lap22"]),
        R("pk22", "Panjang lewatan D22 dipakai (dibulatkan ke atas 10 mm)", "=CEILING({lap22},10)", "mm", "", "", "0", n["pakai22"]),
        R("pj22", "Panjang satu batang D22", "={sisi}+2*{pk22}/1000", "m", "2,0 + 2 x 1,30", "", "0.00", n["pj22"]),
        R("ms22", "Massa D22", MASSA_BAJA["D22"], "kg/m", "", "SNI 2052:2017 (hal PDF 7)", "0.000"),
        R("bb", "Berat batang longitudinal D22", "={sl_n}*{pj22}*{ms22}", "kg", "", "", "0.0", n["berat_bar"]),
        R("nsk", "Jumlah sengkang D10-150 di segmen 2,0 m", "=ROUNDUP({sisi}*1000/150,0)+1", "buah", "", "[Asumsi]", "0", n["n_sk"]),
        R("kel", "Panjang satu sengkang", f"=2*(({{sl_b}}-2*{SLOOF['selimut']:.0f})+({{sl_h}}-2*{SLOOF['selimut']:.0f}))+2*{SLOOF['kait']:.0f}",
          "mm", "keliling inti (selimut 40) + 2 kait 75 mm", "[Asumsi: kait 135°; pasal kait belum dikutip]", "0", n["kel"]),
        R("ms10", "Massa D10", MASSA_BAJA["D10"], "kg/m", "", "SNI 2052:2017 (hal PDF 7)", "0.000"),
        R("bsk", "Berat sengkang", "={nsk}*{kel}/1000*{ms10}", "kg", "", "", "0.0", n["berat_sk"]),
        R("bsl", "Berat tahan karat sloof (segmen 2,0 m)", "={bb}+{bsk}", "kg", "", "", "0.0", n["berat_sloof"]),
        R("bt1", "Berat tahan karat total opsi 1 (pelat + sloof)", "={bp}+{bsl}", "kg", "", "", "0.0", n["berat_opsi1"]),
    ]
    return [("A", "Zona tanpa baja magnetik dan tulangan pelat LT1 (opsi 0 dan 2)", a),
            ("B", "Tambahan opsi 1: sloof as 9 melewati isocenter", b)]


def baris_getar(r):
    mi, g = r["mi"], r["getar"]
    s = g["sumber"]
    a = [
        R("g", "Percepatan gravitasi", G, "m/s²", "", "", "0.00"),
        R("abt", "Batas percepatan 0,5 x 10⁻³ g", f"={mi['a_batas_mg']}*{{g}}", "10⁻³ m/s²", "0-50 Hz", "[Syarat MRI 5]", "0.000", mi["a_batas_mg"] * G),
        R("fcg", "fc'", FC, "MPa", "", "[3.6]", "0"),
        R("ec", "Ec = 4700 √fc'", "=4700*SQRT({fcg})", "MPa", "", "SNI 2847:2019 Pasal 19.2.2.1 (hal PDF 456)", "#,##0.0", g["ec"]),
        R("nu", "Angka Poisson ν", NU, "-", "", "[Asumsi]", "0.00"),
        R("hp", "Tebal pelat panel 9-10/D-E", H_PELAT, "m", "", "[Asumsi, ditetapkan 5.3]", "0.000"),
        R("a", "Panjang sisi panel (persegi, tumpuan sederhana)", 8.0, "m", "", "[Asumsi: panel isolasi 8 x 8; diputuskan 5.3]", "0.0"),
        R("D", "Kekakuan lentur D = Ec h³ / (12 (1 - ν²))", "={ec}*1000000*{hp}^3/(12*(1-{nu}^2))", "N·m", "", "teori pelat; belum ada di acuan", "#,##0", g["D"]),
        R("rho", "Massa jenis beton", RHO_BETON, "kg/m³", "", "[Asumsi]", "0"),
        R("m_s", "Massa berat sendiri", "={rho}*{hp}", "kg/m²", "tanpa finishing = konservatif", "", "0.0", g["m_sendiri"]),
        R("w_rf2", "Berat sangkar RF", mi["berat_rf"], "kN", "", "[Alat Medis R-05]", "0.0"),
        R("l_rf2", "Luas sangkar RF", f"={mi['rf'][0]}*{mi['rf'][1]}", "m²", "", "[Alat Medis R-05]", "0.0", mi["rf"][0] * mi["rf"][1]),
        R("m_rf", "Massa sangkar RF terbagi rata", "={w_rf2}*1000/{l_rf2}/{g}", "kg/m²", "", "", "0.0", g["m_rf"]),
        R("m", "Massa total per luas", "={m_s}+{m_rf}", "kg/m²", "", "", "0.0", g["m"]),
        R("fn", "Frekuensi alami fn = (π/2)(1/a² + 1/b²) √(D/m)", "=PI()/2*(1/{a}^2+1/{a}^2)*SQRT({D}/{m})", "Hz", "pelat persegi tumpuan sederhana, ragam pertama",
          "[Asumsi: buku dinamika belum ada di acuan]", "0.00", g["fn"]),
        R("mm", "Massa modal = m a b / 4", "={m}*{a}*{a}/4", "kg", "", "", "#,##0", g["M_modal"]),
        R("zeta", "Redaman pelat ζ", ZETA, "-", "", "[Asumsi]", "0.00"),
    ]
    def sumber(kode, f, ket, kunci, keterangan):
        return [
            R(f"f_{kunci}", f"{kode}: frekuensi gaya", f, "Hz", ket, keterangan, "0.0"),
            R(f"r_{kunci}", f"{kode}: rasio frekuensi r = f / fn", f"={{f_{kunci}}}/{{fn}}", "-", "", "", "0.000", s[kode]["r"]),
            R(f"H_{kunci}", f"{kode}: faktor respons percepatan H", f"={{r_{kunci}}}^2/SQRT((1-{{r_{kunci}}}^2)^2+(2*{{zeta}}*{{r_{kunci}}})^2)",
              "-", "H = r² / √((1 - r²)² + (2 ζ r)²)", "", "0.000", s[kode]["H"]),
            R(f"F_{kunci}", f"{kode}: gaya dinamis izin di pelat", f"={{abt}}/1000*{{mm}}/{{H_{kunci}}}", "N", "F = a_batas M_modal / H", "", "0.0", s[kode]["F"]),
        ]
    b = (sumber("M-04", mi["f_m04"], "pompa 1.450 rpm", "m04", "[Daftar Alat M-04]")
         + sumber("R-06", mi["f_r06"], "kompresor 50 Hz", "r06", "[Alat Medis R-06]")
         + [R("f_m01", "M-01 (catatan): frekuensi kipas", mi["f_m01_kipas"], "Hz", "chiller kipas 870 rpm; dibahas Tahap 7, tidak didesain di sini", "[Daftar Alat M-01]", "0.0"),
            R("H_m01", "M-01 (catatan): faktor respons H di dekat fn", "=({f_m01}/{fn})^2/SQRT((1-({f_m01}/{fn})^2)^2+(2*{zeta}*({f_m01}/{fn}))^2)", "-",
              "r mendekati 1,3 sehingga H > 2", "", "0.000", s["M-01"]["H"])])
    c = [
        R("dl", "Defleksi statik pegas", mi["delta_pegas_mm"], "mm", "", "[Data Pabrikan lembar 9, chiller; juga R-06 diusulkan]", "0"),
        R("fi", "Frekuensi alami isolator fi = √(g/δ)/(2π)", "=SQRT({g}/({dl}/1000))/(2*PI())", "Hz", "", "", "0.000", g["fi"]),
        R("zi", "Redaman isolator ζi", ZETA_I, "-", "", "[Asumsi]", "0.00"),
        R("T_m04", "M-04: transmisibilitas T", "=SQRT(1+(2*{zi}*({f_m04}/{fi}))^2)/SQRT((1-({f_m04}/{fi})^2)^2+(2*{zi}*({f_m04}/{fi}))^2)", "-",
          "T < 1 bila r > √2", "", "0.0000", g["T_m04"]),
        R("Fs_m04", "M-04: gaya dinamis sumber izin (4 unit sefase)", "={F_m04}/{T_m04}", "N", "tanpa redaman jalur atap-kolom-sloof = konservatif", "", "#,##0", g["F_m04_sumber"]),
        R("T_r06", "R-06 pegas 25 mm: transmisibilitas T", "=SQRT(1+(2*{zi}*({f_r06}/{fi}))^2)/SQRT((1-({f_r06}/{fi})^2)^2+(2*{zi}*({f_r06}/{fi}))^2)", "-", "", "", "0.0000", g["T_r06"]),
        R("Fs_r06", "R-06 pegas: gaya dinamis sumber izin", "={F_r06}/{T_r06}", "N", "", "", "#,##0", g["F_r06_pegas"]),
        R("Fk_r06", "R-06 kaku (T = 1): gaya dinamis sumber izin", "={F_r06}", "N", "", "", "0.0", s["R-06"]["F"]),
    ]
    return [("A", "Pelat panel 9-10/D-E: frekuensi alami dan massa modal", a),
            ("B", "Faktor respons dan gaya dinamis izin di pelat", b),
            ("C", "Peredam pegas dan gaya sumber yang diizinkan", c)]


def baris_bukaan(r):
    mi, k = r["mi"], r["bukaan"]
    a = [
        R("lt1", "Elevasi lantai LT1", k["lt1"], "m", "", "[3.3 Peil dan Urugan; tahap4_beban.LEVEL]"),
        R("tb", "Tinggi bukaan dinding", mi["bukaan"][1], "m", "bukaan DINDING 2,6 x 2,6 m", "[Syarat MRI 8]", "0.00"),
        R("atas", "Atas bukaan", "={lt1}+{tb}", "m", "", "", "0.00", k["atas"]),
        R("lt2", "Elevasi lantai LT2", k["lt2"], "m", "", "[tahap4_beban.LEVEL]"),
        R("hb", f"Tinggi balok as 10 LT2 ({k['kel_balok']}, {idn(k['b_balok'], 2)} x {idn(k['h_balok'], 2)})", k["h_balok"], "m",
          "kelompok balok pelat tepi LT2", "[4.6, tahap4_balok.rancang]", "0.00"),
        R("bawah", "Sisi bawah balok as 10", "={lt2}-{hb}", "m", "", "", "0.00", k["bawah_balok"]),
        R("sisa_b", "Jarak atas bukaan ke sisi bawah balok", "={bawah}-{atas}", "m", "> 0 = tidak bentrok", "", "0.00", k["sisa"]),
        R("hal", "Elevasi halaman", k["halaman"], "m", "", "[3.3]"),
        R("beda", "Beda lantai LT1 dan halaman", "={lt1}-{hal}", "m", "platform luar bongkar-pasang (catatan Tahap 7)", "", "0.00", k["beda"]),
        R("y0", "Bukaan: y selatan", f"={mi['iso'][1]}-{mi['bukaan'][0]}/2", "m", "terpusat pada y isocenter", "", "0.00", k["y0"]),
        R("y1", "Bukaan: y utara", f"={mi['iso'][1]}+{mi['bukaan'][0]}/2", "m", "", "", "0.00", k["y1"]),
        R("ke_e", "Jarak tepi utara bukaan ke as E (y 59)", f"={GRID_E}-{{y1}}", "m", "lebar kolom 10/E belum dicek (5.3)", "", "0.00", k["ke_as_E"]),
        R("kor", "Opsi 1: panjang koridor dari ruang baru ke dinding luar", f"={{kor_p}}", "m", "lebar koridor 2,6 m", "", "0.00", k["koridor"]),
    ]
    return [("A", "Bukaan dinding 2,6 x 2,6 m di as 10 (opsi 0 dan 2)", a)]


# ------------------------------------------------------------------ teks
def teks_banding(r):
    mi, o1, o2 = r["mi"], r["o1"], r["o2"]
    n = r["nm"]
    return [
        ["Opsi 0: MRI tetap, lajur tetap",
         f"{idn(r['j0'])} m < {idn(mi['d_logam'])} m: tidak memenuhi (kurang {idn(mi['d_logam'] - r['j0'])} m).",
         "Tidak ada perubahan. Tulangan non-magnetik pelat panel 9-10/D-E saja.",
         "Tidak ada perubahan; tidak boleh dipakai bila syarat 12,0 m berlaku tanpa pelindung.",
         "Apakah pabrikan mengizinkan 7,5 m dengan pelindung tambahan (lihat opsi 3).",
         "Tidak dipilih bila syarat 12,0 m berlaku."],
        ["Opsi 1: geser MRI ke barat",
         f"{idn(o1['j_lajur'])} m: tepat batas (margin 0,0 m, tanpa cadangan). Lift: {idn(o1['j_lift']['L-1..4'])} / {idn(o1['j_lift']['L-5..6'])} / "
         f"{idn(o1['j_lift']['L-7'])} m (syarat 8,0 m) memenuhi. P4: {idn(o1['j_p4'])} m.",
         f"Isocenter x {idn(o1['iso_x'])} tepat di as 9: sloof as 9 melewati isocenter (jarak 0), segmen y 56-58 tulangan non-magnetik "
         f"(tambahan sekitar {idn(n['berat_sloof'], 0)} kg, total opsi 1 sekitar {idn(n['berat_opsi1'], 0)} kg). Kolom 9/E (76; 59) "
         f"berada di dalam ruang baru, {idn(o1['d_kolom'])} m dari isocenter.",
         f"Ruang baru x {idn(o1['ruang'][0])}-{idn(o1['ruang'][1])} menumpuk R-09 dinding timbal (sekitar {idn(o1['ov_r09'])} m²), ruang X-ray "
         f"R-07/R-08 (sekitar {idn(o1['ov_r07'])} m²), R-06 bersinggungan di y 60 (dipindah). Dinding timur ruang tidak lagi di tepi gedung: "
         f"koridor masuk magnet 2,6 m x {idn(o1['koridor_p'])} m. Zonasi radiologi 3.4 berubah.",
         "Kolom baja karbon di dalam ruang MRI: tidak diatur data pabrikan (permintaan data). Tata letak radiologi baru.",
         "Memenuhi hanya tepat batas; paling banyak perubahan."],
        ["Opsi 2: pindah lajur ambulans ke timur",
         f"{idn(o2['j_lajur'])} m: memenuhi (tepi barat lajur x {idn(o2['tepi'])}, lajur {idn(o2['lajur'][0])}-{idn(o2['lajur'][1])}).",
         f"MRI, sloof, kolom tidak berubah; bukaan tetap di dinding luar as 10. Tulangan non-magnetik hanya pelat panel 9-10/D-E "
         f"(sekitar {idn(n['berat_pelat'], 0)} kg).",
         f"P4 (x 94-100, {idn(o2['luas_p4'], 0)} m²): sisa {idn(o2['sisa_p4'])} m < {idn(LEBAR_PARKIR_MOTOR)} m, seluruh P4 hilang, "
         f"{o2['motor_hilang']} motor. Motor {o2['motor_sisa']} < {o2['motor_butuh']} (kurang {o2['motor_kurang']}). Ambulans 4 di drop-off IGD "
         "tidak terpengaruh. Gedung utilitas x 100-134 tidak tersentuh.",
         "Tempat parkir motor pengganti (Tahap 7); batas persil timur x 140 [Asumsi: cek Tahap 7].",
         "Lebih sederhana untuk struktur (MRI, sloof, kolom tetap; bukaan tetap di dinding luar) tetapi menghilangkan P4. "
         "Keputusan di tangan Defsa."],
        ["Opsi 3: pelindung tambahan di sisi lajur",
         "Tidak dapat dinilai: data pabrikan belum ada (permintaan data 5.0 butir 2 belum dijawab).",
         "Tidak ada perubahan struktur bila diizinkan; berat pelindung tambahan belum diketahui.",
         "Tidak ada perubahan tata letak.",
         "Jarak minimum dengan pelindung. Catatan: R-04 sudah berupa pelindung pelat baja pada dinding timur dan utara; apakah syarat 12 m "
         "sudah memperhitungkannya ditanyakan ke pabrikan.",
         "Tanyakan ke pabrikan sebelum memutuskan."],
    ]


def teks_jenis(r):
    n = r["nm"]
    return [
        ["(a) Beton tanpa tulangan dalam lingkaran r 1,0 m", "tidak sesuai",
         "SNI 2847:2019 Pasal 14.1.3 (hal PDF 291): beton polos hanya boleh bila ditopang menerus oleh tanah atau komponen yang memberi tumpuan "
         "vertikal menerus, busur, dinding, atau pedestal. Pasal 14.1.4 (hal PDF 291-292): pada KDS D (KDS situs = D) hanya fondasi telapak "
         "tertentu. Pelat LT1 ditumpu sloof, bukan menerus oleh tanah. Pasal 8.5.4.1 (hal PDF 166): bukaan pada sistem pelat diizinkan bila "
         "analisis kekuatan dan layan dipenuhi, tetapi bukan izin menghapus tulangan. Simpulan: tidak dipakai kecuali 5.3 menunjukkan pelat "
         "ditumpu menerus.",
         "Data kurang: apakah pabrikan menerima beton polos di tengah pelat bertulang."],
        ["(b) Baja tahan karat ASTM A955M", "diizinkan",
         "SNI 2847:2019 Pasal 20.2.1.3 (hal PDF 467) dan Tabel 20.2.2.4(a) (hal PDF 472). Catatan: teks butir d pada 20.2.1.3 menulis A966M "
         "baja nirkarat, kemungkinan salah ketik A955M; Tabel 20.2.2.4(a) menulis A955M. Disebut pabrikan (Syarat MRI 7: tulangan baja tahan karat). "
         "Standar ASTM A955 sendiri: belum ada di acuan. Batas permeabilitas magnetik: belum ada di acuan. Harga: belum ada di acuan "
         "(3.8 tidak memuat baja tahan karat).",
         "Data kurang: permeabilitas magnetik maksimum dari pabrikan; harga dan pemasok."],
        ["(c) GFRP", "tidak tercantum",
         "Tidak tercantum di SNI 2847:2019 Pasal 20.2 (hal PDF 466-467: tulangan FRP tidak dibahas; ACI 440.1R dirujuk). ACI 440.11-22 dan "
         "ACI 440.1R: belum ada di acuan. Tidak disebut pabrikan. Perlu persetujuan pabrikan dan tim ahli bangunan gedung (TABG). Tanpa angka "
         "sifat bahan.",
         "Data kurang: persetujuan pabrikan dan TABG; sifat bahan."],
        ["Usulan AI", "(b)",
         "Pilihan (b) dipakai sebagai dasar hitungan; panjang dan berat di tabel atas.",
         "Keputusan di tangan Defsa."],
    ]


# ------------------------------------------------------------------ workbook
NAMA = ["Petunjuk", "Ringkasan", "Jarak dan Opsi", "Banding Opsi", "Beban MRI", "Non-magnetik", "Getaran", "Bukaan",
        "Cek Silang T-91", "Acuan"]


def _lembar_hitung(wb, nama, nomor, judul, catatan, baris, tambahan=None):
    from format_dokumen import Lembar
    lb = Lembar(wb[nama], nomor, judul, LEBAR)
    lb.catatan(catatan)
    pertama = True
    for huruf, ket, rows in baris:
        lb.kosong()
        lb.bagian(huruf, ket)
        tabel_hitung(lb, rows, beku=pertama)
        pertama = False
    if tambahan:
        tambahan(lb)
    return lb


def _teks_tabel(lb, kepala, isi, rata, beku=False, ai=True):
    from format_dokumen import AI
    return lb.tabel(kepala, [[i + 1, *row] for i, row in enumerate(isi)], rata=rata, beku=beku, fill=AI if ai else None)


def buat_excel(keluar=BERKAS):
    from format_dokumen import Lembar, set_font_bawaan

    r = hitung()
    mi, o1, o2, b, n, g, k, t91 = r["mi"], r["o1"], r["o2"], r["beban"], r["nm"], r["getar"], r["bukaan"], r["t91"]
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    for s in NAMA:
        wb.create_sheet(s)
    REF.clear()
    LABEL_PAKAI.clear()
    ket_ai = LABEL + " " + LABEL_AI

    _lembar_hitung(wb, "Jarak dan Opsi", 3, "Jarak isocenter MRI ke jalur ambulans dan opsi", ket_ai +
                   " Syarat 12,0 m [Syarat MRI 2] dari isocenter ke benda logam bergerak besar. Jalur ambulans x 88-94 / y 44-76 [Asumsi, 5.0]. "
                   "Sel hijau = masukan; sel putih = rumus Excel.", baris_jarak(r))

    lb = Lembar(wb["Banding Opsi"], 4, "Perbandingan opsi MRI", [5, 22, 34, 46, 46, 38, 36])
    lb.catatan(ket_ai + " Opsi 3 tidak dapat dinilai karena data pabrikan belum ada.")
    lb.kosong()
    lb.bagian("A", "Opsi 0 sampai 3: syarat jarak, akibat struktur, akibat arsitektur dan tapak, data kurang, usulan AI")
    _teks_tabel(lb, ["No", "Opsi", "Syarat jarak 12,0 m", "Akibat struktur", "Akibat arsitektur dan tapak", "Data yang masih kurang", "Usulan AI"],
                teks_banding(r), list("clllllll")[:7], beku=True)

    _lembar_hitung(wb, "Beban MRI", 5, "Beban peralatan MRI dan penyaring pons satu kaki", ket_ai +
                   " Semua beban peralatan = beban mati (berat peralatan layanan tetap, SNI 1727:2020 Pasal 3.1.3). Desain pelat final di 5.3. "
                   "Beban transit magnet 48,1 kN di jalur dari bukaan ke isocenter = kasus beban 5.3.", baris_beban(r))

    def tambah_nm(lb):
        lb.kosong()
        lb.bagian("C", "Jenis tulangan non-magnetik: (a) beton tanpa tulangan, (b) baja tahan karat, (c) GFRP")
        _teks_tabel(lb, ["No", "Jenis", "Status", "", "Dasar pasal dan catatan", "Data kurang"],
                    [[x[0], x[1], "", x[2], x[3]] for x in teks_jenis(r)], list("clcclll")[:6])
    _lembar_hitung(wb, "Non-magnetik", 6, "Tulangan non-magnetik dalam radius 1,0 m dari isocenter", ket_ai +
                   " Kotak 2,0 x 2,0 m: x 79,5-81,5 / y 56-58 (opsi 0 dan 2), x 75-77 / y 56-58 (opsi 1).", baris_nm(r), tambah_nm)

    _lembar_hitung(wb, "Getaran", 7, "Getaran lantai di bawah magnet (batas 0,5 x 10⁻³ g, 0-50 Hz)", ket_ai +
                   " Pedoman getaran lantai (AISC DG11, CCIP-016, SCI P354): belum ada di acuan. SNI 1727:2020 Lampiran C.2.3 (hal PDF 294) hanya umum: "
                   "peralatan mekanis yang menimbulkan vibrasi tidak nyaman harus diisolasi. Metode penyaring [Asumsi: SDOF dan pelat persegi tumpuan "
                   "sederhana]. Syarat: gaya dinamis sumber (data pabrikan, belum ada) harus ≤ nilai izin; R-06 di atas pegas δ ≥ 25 mm dan dudukan sendiri; "
                   "panel MRI dipisah sambungan isolasi dari pelat sekitar (diputuskan 5.3); ukur setelah konstruksi (Syarat MRI 5).", baris_getar(r))

    def tambah_bukaan(lb):
        lb.kosong()
        lb.bagian("B", "Koreksi dan temuan bukaan")
        _teks_tabel(lb, ["No", "Hal", "", "", "Temuan", "Sumber"], [
            ["Koreksi rencana 5.0", "", "", "Rencana 5.0 menulis bukaan pelat LT1. Data owner (Syarat MRI 8): bukaan DINDING 2,6 x 2,6 m ke luar gedung. "
             "Jadi bukan bukaan pelat; yang terdampak dinding luar as 10, balok LT2 as 10, dan kolom 10/E.", "[Syarat MRI 8]"],
            ["Balok dan dinding geser", "", "", f"Balok as 10 LT2: {idn(k['b_balok'], 2)} x {idn(k['h_balok'], 2)} m, sisi bawah +{idn(k['bawah_balok'], 2)}; atas bukaan "
             f"+{idn(k['atas'], 2)}; jarak {idn(k['sisa'], 2)} m (tidak bentrok). Dinding geser ujung x 84 pada 4.8 ada di y 35-43 "
             f"(alternatif), jauh dari y {idn(k['y0'])}-{idn(k['y1'])}: tidak ada dinding geser di as 10 antara D-E.",
             "[4.6, tahap4_balok; 4.8, tahap4_model.DINDING_UJUNG]"],
            ["Pelindung R-04", "", "", "Pelindung baja R-04 pada dinding timur dan utara: bukaan butuh panel pelindung bongkar-pasang.", "[Alat Medis R-04]"],
            ["Halaman dan lantai", "", "", f"Halaman +{idn(k['halaman'], 2)} vs lantai LT1 +{idn(k['lt1'], 2)}: beda {idn(k['beda'], 2)} m, perlu platform luar "
             "(catatan Tahap 7).", "[3.3]"],
            ["Opsi 1", "", "", f"Dinding timur ruang tidak di tepi gedung: koridor 2,6 m dari x {idn(o1['ruang'][1])} ke 84 ({idn(o1['koridor_p'])} m).", "[Jarak dan Opsi]"],
        ], list("clccll"))
    _lembar_hitung(wb, "Bukaan", 8, "Bukaan jalur masuk magnet 2,6 x 2,6 m", ket_ai, baris_bukaan(r), tambah_bukaan)

    # ---- Cek silang T-91
    lb = Lembar(wb["Cek Silang T-91"], 9, "Cek silang T-91", [5, 50, 14, 14, 12, 12, 10, 48])
    lb.catatan(ket_ai + " Toleransi ditetapkan sebelum membandingkan. Cara 1 dan cara 2 berbeda metode.")
    lb.kosong()
    lb.bagian("A", "Tiga cek silang")
    ws = lb.ws
    kep = ["No", "Cek", "Cara 1", "Cara 2", "Selisih (%)", "Toleransi (%)", "Status", "Cara 1 / cara 2"]
    isi = [
        [1, "(a) Jarak isocenter ke tepi barat lajur (m)", None, None, None, 0.5, None,
         "1: tangan 88 - 80,5. 2: jarak_titik_ke_kotak (5.0) = lembar Jarak dan Opsi"],
        [2, "(b) fn pelat panel (Hz)", None, None, None, 15.0, None,
         "1: rumus pelat tumpuan sederhana (π/2)(2/a²)√(D/m). 2: Rayleigh 0,18 √(g/δ), δ tengah PyNite pelat 8 x 8, mesh 0,5 m"],
        [3, "(c) Berat tulangan tahan karat pelat (kg)", None, None, None, 0.5, None,
         "1: tangan 44 x 3,24 x 1,04. 2: lembar Non-magnetik"],
    ]
    r0, a0, a1 = lb.tabel(kep, isi, rata=list("clcccccl"), fmt=[None, None, "0.000", "0.000", "0.00", "0.0", None, None])
    from format_dokumen import AI
    ws[f"{lb.kol(2)}{a0}"] = f"=88-80.5"
    ws[f"{lb.kol(3)}{a0}"] = "=" + _sub("{j0}", ws.title)
    ws[f"{lb.kol(2)}{a0 + 1}"] = "=" + _sub("{fn}", ws.title)
    ws[f"{lb.kol(2)}{a0 + 2}"] = "=44*3.24*1.04"
    ws[f"{lb.kol(3)}{a0 + 2}"] = "=" + _sub("{bp}", ws.title)
    for i in range(3):
        rr = a0 + i
        ws[f"{lb.kol(4)}{rr}"] = f"=ABS({lb.kol(3)}{rr}-{lb.kol(2)}{rr})/{lb.kol(2)}{rr}*100"
        ws[f"{lb.kol(6)}{rr}"] = f'=IF({lb.kol(4)}{rr}<={lb.kol(5)}{rr},"Lolos","Tidak lolos")'
        ws[f"{lb.kol(5)}{rr}"].fill = PatternFill("solid", fgColor=AI)
    ws[f"{lb.kol(3)}{a0 + 1}"].fill = PatternFill("solid", fgColor=AI)
    lb.kosong()
    lb.bagian("B", "Data pembanding (diisi AI)")
    r0, b0, b1 = lb.tabel(["No", "Besaran", "Nilai", "Satuan", "", "", "", "Keterangan"], [
        [1, "δ tengah, PyNite 3.2.1 (elemen pelat, mesh 0,5 m)", g["d_pynite"] * 1000, "mm", "", "", "",
         f"pelat 8 x 8 m h 0,25 tumpuan sederhana semua tepi, q = m g = {idn(g['q'], 3)} kPa"],
        [2, "δ tengah, deret Navier (hitung sendiri)", g["d_navier"] * 1000, "mm", "", "", "", "pembanding kedua; selisih PyNite terhadap deret Navier ±1 %"],
        [3, "Selisih PyNite terhadap Navier", None, "%", "", "", "", ""],
    ], rata=list("clcccccl"), fmt=[None, None, "0.000", None, None, None, None, None], beku=False)
    ws[f"{lb.kol(2)}{b0 + 2}"] = f"=({lb.kol(2)}{b0}/{lb.kol(2)}{b0 + 1}-1)*100"
    for rr in (b0, b0 + 1):
        ws[f"{lb.kol(2)}{rr}"].fill = PatternFill("solid", fgColor=AI)
    ws[f"{lb.kol(2)}{b0 + 2}"].number_format = "0.00"
    # nilai PyNite masuk rumus (b) cara 2 lewat sel (bukan angka mati)
    ws[f"{lb.kol(3)}{a0 + 1}"] = f"=0.18*SQRT({G}/({lb.kol(2)}{b0}/1000))"

    # ---- Ringkasan
    lb = Lembar(wb["Ringkasan"], 2, "Ringkasan temuan dan keputusan yang diminta dari Defsa", [5, 38, 58, 46, 40])
    lb.catatan(f"STATUS: {STATUS}. " + ket_ai)
    lb.kosong()
    lb.bagian("A", "Temuan")
    _teks_tabel(lb, ["No", "Temuan", "Hasil kunci", "Keputusan Defsa", "Usulan AI"], [
        ["Jarak MRI ke jalur ambulans (5.0 no. 1)",
         f"Opsi 0: {idn(r['j0'])} m < 12,0 m. Opsi 1: isocenter x {idn(o1['iso_x'])} (tepat as 9), jarak {idn(o1['j_lajur'])} m, sloof as 9 melewati isocenter. "
         f"Opsi 2: tepi lajur x {idn(o2['tepi'])}, P4 hilang ({o2['motor_hilang']} motor; sisa {o2['motor_sisa']} < {o2['motor_butuh']}). Opsi 3 tidak dapat dinilai.",
         "Pilih opsi 0 / 1 / 2 / 3.",
         "Opsi 2 lebih sederhana untuk struktur tetapi menghilangkan P4; keputusan di tangan Defsa."],
        ["Beban MRI (5.0 no. 9)",
         f"Kaki {idn(b['q_kaki'], 0)} kPa; pelindung {idn(b['q_pel'], 2)} kN/m'; sangkar RF {idn(b['q_rf'], 3)} kPa; beban hidup 2,87 kPa. "
         f"Pons satu kaki: φVc {idn(b['phivc'], 0)} kN, rasio {idn(b['rasio_pons'], 3)}.",
         "Menyetujui sebagai masukan 5.3.", "Setuju; desain final di 5.3."],
        ["Tulangan non-magnetik (5.0 no. 3)",
         f"Pelat {idn(n['berat_pelat'], 0)} kg; opsi 1 total {idn(n['berat_opsi1'], 0)} kg. (a) beton polos tidak sesuai Pasal 14.1.3; (b) baja tahan "
         "karat A955M diizinkan; (c) GFRP tidak tercantum.",
         "Pilih a / b / c.", "(b) baja tahan karat."],
        ["Getaran (5.0 no. 4)",
         f"fn pelat {idn(g['fn'])} Hz, M_modal {idn(g['M_modal'], 0)} kg. Gaya izin di pelat: M-04 {idn(g['sumber']['M-04']['F'], 0)} N, "
         f"R-06 {idn(g['sumber']['R-06']['F'], 0)} N. Dengan pegas 25 mm: sumber M-04 {idn(g['F_m04_sumber'] / 1000, 1)} kN, R-06 {idn(g['F_r06_pegas'] / 1000, 1)} kN.",
         "Menerima syarat gaya sumber dan pegas R-06.", "R-06 di atas pegas δ ≥ 25 mm dan dudukan sendiri."],
        ["Bukaan (Syarat MRI 8)",
         f"Bukaan dinding, bukan pelat. Atas +{idn(k['atas'], 2)}; sisi bawah balok as 10 +{idn(k['bawah_balok'], 2)} (sisa {idn(k['sisa'], 2)} m); "
         "tidak ada dinding geser di as 10 antara D-E.", "Menerima koreksi.", "Setuju."],
        ["Permintaan data ke pabrikan",
         "(1) pelindung tambahan dan jarak minimum; (2) kolom baja karbon di dalam ruang MRI (opsi 1); (3) permeabilitas magnetik baja tahan karat; "
         "(4) gaya dinamis M-04 dan R-06; (5) peredam R-06.", "Menyetujui daftar.", "Kirim bersama surat teknis."],
    ], list("clllll")[:5])

    # ---- Acuan
    lb = Lembar(wb["Acuan"], 10, "Acuan yang dipakai dan statusnya", [5, 26, 20, 56, 14, 36])
    lb.catatan(ket_ai + " Halaman = nomor halaman PDF di acuan/privat (diverifikasi dengan pypdf, 21 Nov 2026).")
    lb.kosong()
    lb.bagian("A", "Pasal yang diverifikasi di PDF")
    _teks_tabel(lb, ["No", "Acuan", "Pasal", "Isi yang dipakai", "Hal. PDF", "Status"], [
        ["SNI 1727:2020", "3.1.3", "Berat peralatan layanan tetap, termasuk isi maksimum, masuk beban mati.", "46", "Terverifikasi"],
        ["SNI 1727:2020", "Tabel 4.3-1", "Rumah sakit, ruang operasi dan laboratorium: 60 psf = 2,87 kPa.", "52", "Terverifikasi"],
        ["SNI 1727:2020", "C.2.3", "Peralatan mekanis yang menimbulkan vibrasi harus diisolasi (umum).", "294", "Terverifikasi"],
        ["SNI 2847:2019", "Tabel 5.3.1", "1,2D + 1,6L (Pers. 5.3.1b).", "106", "Terverifikasi"],
        ["SNI 2847:2019", "8.5.4.1", "Bukaan pelat diizinkan bila analisis kekuatan dan layan dipenuhi.", "166", "Terverifikasi"],
        ["SNI 2847:2019", "14.1.3, 14.1.4", "Beton polos hanya bila ditumpu menerus; KDS D-F dibatasi.", "291-292", "Terverifikasi"],
        ["SNI 2847:2019", "19.2.2.1", "Ec = 4700 √fc' (beton normal).", "456", "Terverifikasi"],
        ["SNI 2847:2019", "20.2.1.3, Tabel 20.2.2.4(a)", "Tulangan ulir A615M, A706M, A955M (tahan karat), dan lain-lain. Butir d menulis A966M.", "467, 472", "Terverifikasi; kemungkinan salah ketik A966M"],
        ["SNI 2847:2019", "Tabel 21.2.1", "φ geser 0,75; tumpu 0,65.", "491", "Terverifikasi"],
        ["SNI 2847:2019", "22.6.4.1", "Penampang kritis geser dua arah: bo minimum, tidak lebih dekat dari d/2 dari beban terpusat.", "518", "Terverifikasi"],
        ["SNI 2847:2019", "22.6.5.2", "vc geser dua arah = terkecil dari tiga persamaan (Tabel 22.6.5.2).", "521", "Terverifikasi"],
        ["SNI 2847:2019", "22.8.3.2", "Bn tumpu = 0,85 fc' A1 (bila A2/A1 = 1).", "540", "Terverifikasi"],
        ["SNI 2847:2019", "Tabel 25.4.2.2, 25.4.2.3", "ld = fy ψt ψe / (2,1 λ √fc') db (≤ D19) atau / (1,7 λ √fc') db (≥ D22).", "588", "Terverifikasi"],
        ["SNI 2847:2019", "Tabel 25.5.2.1", "Lewatan kelas B = terbesar dari 1,3 ld dan 300 mm.", "608", "Terverifikasi"],
        ["SNI 2052:2017", "Tabel massa nominal", "D10 0,617; D13 1,04 (OCR 1,U2; dari luas 133 mm²); D22 2,984 kg/m.", "7-8", "Terverifikasi (OCR kasar)"],
    ], list("clllcl"))
    lb.kosong()
    lb.bagian("B", "Tidak ada di acuan")
    _teks_tabel(lb, ["No", "Acuan", "Pasal", "Keterangan", "Hal. PDF", "Status"], [
        ["AISC DG11, CCIP-016, SCI P354", "-", "Pedoman getaran lantai.", "-", "belum ada di acuan"],
        ["ASTM A955", "-", "Standar baja tulangan tahan karat.", "-", "belum ada di acuan"],
        ["ACI 440.11-22 / 440.1R", "-", "Tulangan GFRP.", "-", "belum ada di acuan"],
        ["Batas permeabilitas magnetik baja tahan karat", "-", "Angka pabrikan MRI.", "-", "belum ada di acuan"],
        ["Pedoman parkir motor", "-", "Lebar deretan parkir motor.", "-", "belum ada di acuan"],
        ["Buku dinamika struktur", "-", "Respons SDOF dan pelat; metode penyaring.", "-", "belum ada di acuan"],
    ], list("clllcl"))

    # ---- Petunjuk
    lb = Lembar(wb["Petunjuk"], 1, "Petunjuk kajian MRI (langkah 5.2)", [6, 120])
    lb.catatan(f"STATUS: {STATUS}. " + ket_ai)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        "Data dibaca langsung dari 04 Struktur Atas/Data Owner/Data Beban MEP Rinci.xlsx (lembar Syarat MRI, Alat Medis, Daftar Alat, Lift, Data Pabrikan). "
        "Jalur ambulans x 88-94 / y 44-76 adalah [Asumsi 5.0].",
        "Dua opsi untuk syarat jarak 12,0 m: geser MRI ke barat (opsi 1) atau pindah lajur ke timur (opsi 2); opsi 0 tidak memenuhi; opsi 3 "
        "(pelindung tambahan) tidak dapat dinilai tanpa data pabrikan.",
        "Beban MRI dibagi dari data owner; semua beban peralatan = beban mati (SNI 1727:2020 Pasal 3.1.3); desain pelat final di 5.3.",
        "Tulangan non-magnetik: kotak 2,0 x 2,0 m; panjang lewatan dari SNI 2847:2019 Pasal 25.4.2 dan 25.5.2; massa dari SNI 2052:2017.",
        "Getaran: metode penyaring SDOF dan pelat persegi tumpuan sederhana [Asumsi]; pedoman getaran lantai belum ada di acuan.",
        "Sel hijau diisi AI atas permintaan Defsa. Sel putih berisi rumus Excel (dihitung ulang dan dicocokkan dengan Python di cocokkan()).",
        "Lembar: Ringkasan; Jarak dan Opsi; Banding Opsi; Beban MRI; Non-magnetik; Getaran; Bukaan; Cek Silang T-91; Acuan.",
    ])], rata=list("cl"))

    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


def semua_baris(r):
    out = {}
    for nama, fn in (("Jarak dan Opsi", baris_jarak), ("Beban MRI", baris_beban), ("Non-magnetik", baris_nm),
                     ("Getaran", baris_getar), ("Bukaan", baris_bukaan)):
        out[nama] = [rw for _, _, rows in fn(r) for rw in rows]
    return out


def cocokkan(berkas=BERKAS):
    """Hitung ulang di Excel, lalu bandingkan rumus dengan Python. Kembalikan (ok, pesan)."""
    from format_dokumen import hitung_ulang_excel
    ok, err = hitung_ulang_excel(berkas)
    if not ok:
        return False, f"Excel tidak bisa menghitung ulang: {err[:120]}"
    r = hitung()
    wb = openpyxl.load_workbook(berkas, data_only=True)
    pesan = []
    n_cek = 0
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
            tol = max(1e-9, abs(rw["py"]) * 1e-6)
            if x is None or abs(x - rw["py"]) > tol:
                pesan.append(f"{nama}/{rw['label']}: Excel {x} vs Python {rw['py']}")
    ws = wb["Cek Silang T-91"]
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.startswith("(") and c.value[1] in "abc" and c.value[2] == ")":
                st = ws.cell(c.row, c.column + 5).value
                if st != "Lolos":
                    pesan.append(f"T-91 {c.value}: status {st}")
                n_cek += 1
    return not pesan, "; ".join(pesan) or f"semua {n_cek} rumus/cek Excel cocok dengan Python"


# ------------------------------------------------------------------ ringkasan .md
def buat_md(keluar=KELUAR / "5.2 Kajian MRI.md"):
    r = hitung()
    mi, o1, o2, b, n, g, k = r["mi"], r["o1"], r["o2"], r["beban"], r["nm"], r["getar"], r["bukaan"]
    s = g["sumber"]
    judul = f"5.2 Kajian MRI ({'disetujui Defsa ' + KEPUTUSAN.split(':')[0] if KEPUTUSAN else STATUS})"
    teks = f"""# {judul}

Disusun AI 21 Nov 2026. Data simulasi. Rincian angka di `5.2 Kajian MRI.xlsx` (`skrip/tahap5_mri.py`, uji `tests/test_tahap5_mri.py`).
Data dari `04 Struktur Atas/Data Owner/Data Beban MEP Rinci.xlsx`. Jalur ambulans x 88-94 / y 44-76 adalah [Asumsi 5.0].

## Opsi MRI (temuan 5.0 no. 1)

Isocenter ({idn(mi['iso'][0])}; {idn(mi['iso'][1])}), syarat benda logam bergerak besar ≥ {idn(mi['d_logam'])} m [Syarat MRI 2], lift ≥ {idn(mi['d_lift'])} m [Syarat MRI 3].

| Opsi | Jarak ke tepi lajur | Akibat struktur | Akibat arsitektur dan tapak | Data kurang |
|---|---|---|---|---|
| 0 tetap | {idn(r['j0'])} m < 12,0 m: tidak memenuhi | tidak ada | tidak ada | pelindung (opsi 3) |
| 1 geser MRI ke barat | {idn(o1['j_lajur'])} m, tepat batas (margin 0,0 m); P4 {idn(o1['j_p4'])} m; lift {idn(o1['j_lift']['L-1..4'])} / {idn(o1['j_lift']['L-5..6'])} / {idn(o1['j_lift']['L-7'])} m | isocenter x {idn(o1['iso_x'])} tepat di as 9: sloof as 9 melewati isocenter (jarak 0), segmen y 56-58 non-magnetik; kolom 9/E (76; 59) di dalam ruang ({idn(o1['d_kolom'])} m dari isocenter) | ruang x {idn(o1['ruang'][0])}-{idn(o1['ruang'][1])} menumpuk R-09 (sekitar {idn(o1['ov_r09'])} m²) dan R-07/R-08 (sekitar {idn(o1['ov_r07'])} m²); R-06 bersinggungan di y 60 (pindah); koridor 2,6 × {idn(o1['koridor_p'])} m | kolom baja karbon dalam ruang MRI |
| 2 pindah lajur | {idn(o2['j_lajur'])} m; lajur x {idn(o2['lajur'][0])}-{idn(o2['lajur'][1])} | MRI, sloof, kolom tetap; non-magnetik hanya pelat panel 9-10/D-E | P4 {idn(o2['luas_p4'], 0)} m² hilang seluruhnya (sisa {idn(o2['sisa_p4'])} m < {idn(LEBAR_PARKIR_MOTOR)} m): {o2['motor_hilang']} motor, sisa {o2['motor_sisa']} < {o2['motor_butuh']} (kurang {o2['motor_kurang']}); ambulans 4 di drop-off IGD tidak terpengaruh | motor pengganti; batas persil timur x {idn(o2['persil_x'], 0)} [Asumsi: cek Tahap 7] |
| 3 pelindung tambahan | tidak dapat dinilai | belum diketahui | tidak ada | data pabrikan belum ada (permintaan data 5.0 butir 2); R-04 sudah pelat baja di dinding timur dan utara, apakah syarat 12 m memperhitungkannya? |

Usulan AI: opsi 2 lebih sederhana untuk struktur (MRI, sloof, kolom tetap; bukaan tetap di dinding luar) tetapi menghilangkan P4; keputusan di tangan Defsa.

## Beban MRI (temuan 5.0 no. 9)

Semua beban peralatan = beban mati (SNI 1727:2020 Pasal 3.1.3, hal PDF 46). Beban hidup ruang MRI {idn(b['lo'], 2)} kPa (Tabel 4.3-1, rumah sakit ruang operasi dan laboratorium, hal PDF 52).

| Beban | Hitungan | Hasil |
|---|---|---|
| Kaki magnet R-03 | {idn(mi['p_kaki'], 0)} kN / (0,25 × 0,25 m) | {idn(b['q_kaki'], 0)} kPa |
| Pelindung R-04 | {idn(mi['berat_pelindung'], 1)} kN / ({idn(mi['dinding'][0])} + {idn(mi['dinding'][1])}) m | {idn(b['q_pel'], 2)} kN/m' (data owner ±7,3: selisih {idn(b['sel_pel'] * 100, 1)} %) |
| Sangkar RF R-05 | {idn(mi['berat_rf'], 1)} kN / 42 m² | {idn(b['q_rf'], 3)} kPa |
| Pons satu kaki (pelat 250, d {idn(b['d'], 0)} mm) | Vu {idn(b['vu'], 1)} kN; φVc {idn(b['phivc'], 0)} kN (Pasal 22.6.5.2) | rasio {idn(b['rasio_pons'], 3)} |
| Tumpu satu kaki | 1,2 × {idn(b['q_kaki'], 0)} = {idn(b['tegangan'], 1)} kPa; φ 0,85 fc' = {idn(b['phi_tumpu'], 0)} kPa (Pasal 22.8.3.2) | rasio {idn(b['rasio_tumpu'], 3)} |

Beban transit magnet 48,1 kN di jalur dari bukaan ke isocenter = kasus beban 5.3.

## Tulangan non-magnetik (temuan 5.0 no. 3)

Kotak {idn(n['sisi'])} × {idn(n['sisi'])} m. Pelat LT1 D13-200 [Asumsi 5.3]: {idn(n['nb'], 0)} batang per lapis per arah, ld {idn(n['ld13'], 0)} mm (Tabel 25.4.2.2), lewatan 1,3 ld = {idn(n['lap13'], 0)} → {idn(n['pakai13'], 0)} mm (Tabel 25.5.2.1), batang {idn(n['pj13'], 2)} m, **{idn(n['berat_pelat'], 1)} kg**. Opsi 1 tambah sloof as 9 400 × 800 (4D22 + 4D22): ld {idn(n['ld22'], 0)}, lewatan {idn(n['pakai22'], 0)} mm, **{idn(n['berat_sloof'], 1)} kg**; total opsi 1 **{idn(n['berat_opsi1'], 1)} kg**.

| Jenis | Status | Catatan |
|---|---|---|
| (a) beton tanpa tulangan | tidak sesuai bila pelat ditumpu sloof | SNI 2847:2019 Pasal 14.1.3 dan 14.1.4 (hal PDF 291-292); bukaan pelat Pasal 8.5.4.1 bukan izin menghapus tulangan |
| (b) baja tahan karat A955M | diizinkan | Pasal 20.2.1.3 dan Tabel 20.2.2.4(a); teks butir d menulis A966M (kemungkinan salah ketik); disebut pabrikan; ASTM A955, batas permeabilitas magnetik, dan harga: belum ada di acuan |
| (c) GFRP | tidak tercantum | Pasal 20.2 tidak memuatnya; ACI 440.11-22 / 440.1R: belum ada di acuan; perlu persetujuan pabrikan dan TABG |

Usulan AI: (b).

## Getaran (temuan 5.0 no. 4)

Batas {idn(mi['a_batas_mg'], 1)} × 10⁻³ g = {idn(g['a_batas'] * 1000, 3)} × 10⁻³ m/s² pada 0-{idn(mi['f_maks'], 0)} Hz [Syarat MRI 5]. Pedoman getaran lantai (AISC DG11, CCIP-016, SCI P354): belum ada di acuan. Metode penyaring [Asumsi: SDOF, pelat persegi tumpuan sederhana].

| Besaran | Hasil |
|---|---|
| Panel 9-10/D-E 8 × 8 m, h 0,25; Ec | {idn(g['ec'], 0)} MPa; D = {idn(g['D'] / 1e6, 2)} × 10⁶ N·m |
| m (berat sendiri + sangkar RF) | {idn(g['m_sendiri'], 0)} + {idn(g['m_rf'], 1)} = {idn(g['m'], 1)} kg/m² |
| fn; massa modal | {idn(g['fn'], 2)} Hz; {idn(g['M_modal'], 0)} kg |
| M-04 {idn(mi['f_m04'])} Hz: H; F izin di pelat | {idn(s['M-04']['H'], 2)}; {idn(s['M-04']['F'], 1)} N |
| R-06 {idn(mi['f_r06'], 0)} Hz: H; F izin di pelat | {idn(s['R-06']['H'], 2)}; {idn(s['R-06']['F'], 1)} N |
| M-01 kipas {idn(mi['f_m01_kipas'])} Hz (catatan Tahap 7) | H {idn(s['M-01']['H'], 2)} |
| Isolator pegas 25 mm: fi; T M-04; T R-06 | {idn(g['fi'], 2)} Hz; {idn(g['T_m04'], 4)}; {idn(g['T_r06'], 4)} |
| Gaya sumber izin: M-04 (4 unit sefase); R-06 pegas; R-06 kaku | {idn(g['F_m04_sumber'] / 1000, 2)} kN; {idn(g['F_r06_pegas'] / 1000, 2)} kN; {idn(s['R-06']['F'], 1)} N |

Syarat yang diangkakan: gaya dinamis sumber (data pabrikan, belum ada) ≤ nilai izin di atas; R-06 di atas pegas δ ≥ 25 mm dan dudukan sendiri; panel MRI dipisah sambungan isolasi dari pelat sekitar (diputuskan 5.3); ukur setelah konstruksi (Syarat MRI 5).

## Bukaan (Syarat MRI 8)

Data owner menulis bukaan **dinding** 2,6 × 2,6 m ke luar gedung, bukan bukaan pelat LT1 seperti tertulis di rencana 5.0 (koreksi). Opsi 0 dan 2: dinding timur di as 10 (x 84), y {idn(k['y0'])}-{idn(k['y1'])}; atas bukaan +{idn(k['atas'], 2)}; sisi bawah balok as 10 ({idn(k['b_balok'], 2)} × {idn(k['h_balok'], 2)}, kelompok {k['kel_balok']}, 4.6) +{idn(k['bawah_balok'], 2)}: jarak {idn(k['sisa'], 2)} m, tidak bentrok. Dinding geser 4.8 di as 10: hanya dinding ujung x 84 pada y 35-43 (alternatif), tidak di D-E: tidak ada konflik. Pelindung R-04 di dinding timur: panel bongkar-pasang. Halaman +{idn(k['halaman'], 2)} vs lantai +{idn(k['lt1'], 2)} (beda {idn(k['beda'], 2)} m): platform luar (catatan Tahap 7). Opsi 1: koridor 2,6 m dari x {idn(o1['ruang'][1])} ke 84.

## Cek silang T-91

| Cek | Cara 1 | Cara 2 | Selisih | Toleransi |
|---|---|---|---|---|
| (a) jarak isocenter ke tepi lajur | tangan 88 - 80,5 = {idn(r['t91']['a_tangan'], 3)} m | jarak_titik_ke_kotak (5.0) {idn(r['t91']['a_skrip'], 3)} m | {idn(abs(r['t91']['a_tangan'] / r['t91']['a_skrip'] - 1) * 100, 2)} % | 0,5 % |
| (b) fn pelat | rumus pelat {idn(g['fn'], 2)} Hz | Rayleigh 0,18 √(g/δ), δ PyNite {idn(g['d_pynite'] * 1000, 3)} mm: {idn(g['fn_rayleigh'], 2)} Hz | {idn(g['sel_rayleigh'] * 100, 1)} % | 15 % (metode beda) |
| (c) berat tahan karat pelat | tangan 44 × 3,24 × 1,04 = {idn(r['t91']['c_tangan'], 2)} kg | skrip {idn(n['berat_pelat'], 2)} kg | {idn(abs(r['t91']['c_tangan'] / n['berat_pelat'] - 1) * 100, 2)} % | 0,5 % |

Pembanding kedua untuk (b): deret Navier δ = {idn(g['d_navier'] * 1000, 3)} mm (PyNite {idn(g['sel_pyn_nav'] * 100, 1)} %).

## Data yang masih kurang (permintaan ke pabrikan)

1. Pelindung tambahan dan jarak minimum dengan pelindung (opsi 3).
2. Kolom baja karbon di dalam ruang MRI (opsi 1).
3. Permeabilitas magnetik maksimum baja tahan karat; harga dan pemasok.
4. Gaya dinamis M-04 dan R-06 pada frekuensi kerja.
5. Peredam R-06 (pegas δ ≥ 25 mm).

## Yang perlu diputuskan Defsa

1. **Opsi MRI 0 / 1 / 2 / 3** (usulan AI: opsi 2 lebih sederhana untuk struktur tetapi menghilangkan P4; keputusan di tangan Defsa).
2. **Jenis tulangan non-magnetik a / b / c** (usulan AI: b).
3. **Permintaan data ke pabrikan** (daftar di atas).
"""
    if KEPUTUSAN:
        teks += f"\n## Keputusan Defsa\n\n{KEPUTUSAN}\n"
    keluar.write_text(teks, encoding="utf-8")
    return keluar


def ke_pdf(berkas=BERKAS, pdf=None):
    """Cetak semua lembar xlsx ke PDF lewat Microsoft Excel (ExportAsFixedFormat); kembalikan (ok, pesan)."""
    import subprocess
    pdf = pdf or Path(berkas).with_suffix(".pdf")
    perintah = ("$x = New-Object -ComObject Excel.Application; $x.Visible = $false; $x.DisplayAlerts = $false; "
                f"$b = $x.Workbooks.Open('{Path(berkas).resolve()}'); $b.ExportAsFixedFormat(0, '{Path(pdf).resolve()}'); "
                "$b.Close($false); $x.Quit()")
    h = subprocess.run(["powershell", "-NoProfile", "-Command", perintah], capture_output=True, text=True)
    return h.returncode == 0, h.stderr.strip()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    r = hitung()
    print("j0", round(r["j0"], 3), "iso1", r["o1"]["iso_x"], "tepi2", r["o2"]["tepi"], "motor", r["o2"]["motor_hilang"], r["o2"]["motor_sisa"])
    print({k: round(v, 3) for k, v in r["beban"].items()})
    print({k: round(v, 2) for k, v in r["nm"].items()})
    print({k: v for k, v in r["getar"].items() if k != "sumber"})
    print(buat_excel())
    print(cocokkan())
    print(buat_md())
