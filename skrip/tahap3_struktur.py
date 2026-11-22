"""Langkah 3.6: grid kolom, pemilihan sistem struktur, spektrum sementara, pra-dimensi, dan perbandingan volume.

Acuan (halaman PDF berkas di acuan/privat/):
  SNI 1726:2019 hal. 37 Tabel 4 (Ie 1,50 kategori IV); hal. 46-47 Tabel 6 dan 7 (Fa, Fv; kelas SF = "SS", wajib
  analisis respons spesifik-situs); hal. 49 Tabel 8 dan 9 (KDS); hal. 62 Tabel 12 (R, Ω0, Cd; SRPMK beton 8/3/5,5;
  sistem ganda dinding geser khusus + SRPMK 7/2,5/5,5; TB); hal. 84 Tabel 17 (Cu) dan Tabel 18 (Ct, x); hal. 100
  Tabel 20 (simpangan izin 0,010 hsx kategori IV).
  SNI 2847:2019 hal. 157 Tabel 8.3.1.2 (tebal pelat dua arah dengan balok); hal. 202 Tabel 9.3.1.1 (tinggi balok).
  SNI 1727:2020 hal. 52 Tabel 4.3-1 (rumah sakit: ruang operasi/lab 2,87; ruang pasien 1,92; koridor 3,83 kPa;
  helipad > 13,35 kN 2,87 kPa); hal. 61 Pasal 4.11.2 (dua beban terpusat @ 0,75 × berat lepas landas maksimum).
Ss, S1 dari Desain Spektra PUPR (langkah 2.6). Kelas situs SF: Fa dan Fv kelas SE dipakai SEMENTARA untuk
pra-dimensi saja [Asumsi]; spektrum desain dari analisis respons spesifik-situs di Tahap 4.
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 19 Nov 2026 (sistem ganda).
"""
import math
from pathlib import Path

import numpy as np

import tahap3_program as pr
import tahap3_template_bim as tpl

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "03 Desain Konsep"
BERKAS = KELUAR / "3.6 Grid dan Pra-dimensi.xlsx"
PDF = KELUAR / "3.6 Gambar Rencana Struktur.pdf"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = "DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026 (sistem ganda)."

# ------------------------------------------------------------------ grid (m lokal)
GRID_X = [12.0 + 8.0 * i for i in range(10)]  # as 1-10
GRID_Y = [27.0 + 8.0 * j for j in range(7)]  # as A-G
NAMA_Y = "ABCDEFG"
BENTANG = 8.0

# ------------------------------------------------------------------ gempa sementara
SS, S1 = 0.334, 0.264  # Desain Spektra PUPR, Kota Jambi (langkah 2.6)
FA_SE = [(0.25, 2.4), (0.5, 1.7), (0.75, 1.3), (1.0, 1.1), (1.25, 0.9), (1.5, 0.8)]  # Tabel 6 kelas SE
FV_SE = [(0.1, 4.2), (0.2, 3.3), (0.3, 2.8), (0.4, 2.4), (0.5, 2.2), (0.6, 2.0)]  # Tabel 7 kelas SE
IE = 1.50  # Tabel 4, kategori IV
SISTEM = {
    "SRPMK": {"nama": "Sistem rangka pemikul momen khusus beton (SRPMK)", "R": 8.0, "Om": 3.0, "Cd": 5.5,
              "Ct": 0.0466, "x": 0.9},
    "GANDA": {"nama": "Sistem ganda: dinding geser beton khusus + SRPMK", "R": 7.0, "Om": 2.5, "Cd": 5.5,
              "Ct": 0.0488, "x": 0.75},
}


def koef(tabel, nilai):
    xs, ys = zip(*tabel)
    return float(np.interp(nilai, xs, ys))


def spektrum():
    fa, fv = koef(FA_SE, SS), koef(FV_SE, S1)
    sms, sm1 = fa * SS, fv * S1
    sds, sd1 = 2 / 3 * sms, 2 / 3 * sm1
    kds_s = "D" if sds >= 0.33 else ("C" if sds >= 0.167 else "A")  # Tabel 8 kolom IV
    kds_1 = "D" if sd1 >= 0.133 else ("C" if sd1 >= 0.067 else "A")  # Tabel 9 kolom IV
    return {"Fa": fa, "Fv": fv, "SMS": sms, "SM1": sm1, "SDS": sds, "SD1": sd1, "KDS": max(kds_s, kds_1)}


# ------------------------------------------------------------------ beban
LL = {"operasi/lab": 2.87, "pasien": 1.92, "koridor": 3.83, "helipad": 2.87}  # SNI 1727 Tabel 4.3-1
SDL = {"finishing": 1.2, "plafon dan MEP": 1.5, "partisi": 1.0}  # kPa [Asumsi; rinci di Tahap 4]
AW139_KG = 6800.0  # surat Kantor SAR (data owner); helikopter rencana yang menentukan
GAMMA_C = 24.0


def beban_helikopter():
    w = AW139_KG * 9.81 / 1000
    return {"berat": w, "terpusat": 0.75 * w, "jarak_m": 2.44, "bidang_mm": 200}


# ------------------------------------------------------------------ pra-dimensi
def tebal_pelat(ln_mm=BENTANG * 1000 - 400, fy=420.0, beta=1.0):
    """Tabel 8.3.1.2 (d): αfm > 2,0: h = ℓn (0,8 + fy/1400) / (36 + 9β) ≥ 90 mm."""
    h = ln_mm * (0.8 + fy / 1400) / (36 + 9 * beta)
    return max(h, 90.0)


def tinggi_balok_min(l_mm=BENTANG * 1000):
    """Tabel 9.3.1.1: menerus satu sisi ℓ/18,5; menerus dua sisi ℓ/21."""
    return {"satu_sisi": l_mm / 18.5, "dua_sisi": l_mm / 21}


PRA = {  # ukuran usulan (mm) [Asumsi rekayasa, dicek di bawah]
    "SRPMK": {"pelat": 200, "balok": (400, 650), "kolom_podium": 800, "kolom_menara": 700, "dinding": 0},
    "GANDA": {"pelat": 200, "balok": (350, 600), "kolom_podium": 750, "kolom_menara": 650, "dinding": 350},
}


def beban_mati(sistem):
    p = PRA[sistem]
    b, h = p["balok"]
    balok = GAMMA_C * b / 1000 * (h - p["pelat"]) / 1000 * (2 * BENTANG) / (BENTANG ** 2)
    return GAMMA_C * p["pelat"] / 1000 + sum(SDL.values()) + balok


def aksial_kolom(sistem):
    """Kolom dalam bawah menara (as D-5): 6 pelat (LT2-ATAP) di atasnya, tributari 8 × 8 m; LT1 pelat lantai di
    atas sloof/tiang (tidak dipikul kolom). Pu = 1,2D + 1,6L (SNI 1727 Pasal 2.3)."""
    trib = BENTANG ** 2
    d = beban_mati(sistem)
    pu_lantai = (1.2 * d + 1.6 * LL["operasi/lab"]) * trib
    p = PRA[sistem]
    tinggi = [4.5, 4.5, 4.2, 4.2, 4.2, 4.2]
    berat_kolom = sum(GAMMA_C * (p["kolom_podium"] / 1000) ** 2 * h for h in tinggi[:3]) + \
        sum(GAMMA_C * (p["kolom_menara"] / 1000) ** 2 * h for h in tinggi[3:])
    return 6 * pu_lantai + 1.2 * berat_kolom


def cek_kolom(sistem, fc=35.0, fy=420.0, rho=0.015):
    pu = aksial_kolom(sistem)
    b = PRA[sistem]["kolom_podium"]
    ag = b * b
    phipn = 0.65 * 0.80 * (0.85 * fc * ag * (1 - rho) + fy * rho * ag) / 1000  # SNI 2847 22.4.2 (kolom bersengkang)
    return {"Pu": pu, "phiPn": phipn, "rasio": pu / phipn, "aksial_fc": pu * 1000 / (ag * fc)}


def gaya_geser_dasar(sistem):
    sp = spektrum()
    s = SISTEM[sistem]
    hn = (dict(tpl.LEVEL)["ATAP"] - dict(tpl.LEVEL)["LT1"]) / 1000
    ta = s["Ct"] * hn ** s["x"]
    cs = min(sp["SDS"] / (s["R"] / IE), sp["SD1"] / (ta * s["R"] / IE))
    cs = max(cs, 0.044 * sp["SDS"] * IE, 0.01)
    w = berat_seismik(sistem)
    return {"hn": hn, "Ta": ta, "Cs": cs, "W": w, "V": cs * w}


def berat_seismik(sistem):
    """Berat seismik kasar: beban mati + SDL tiap pelat di atas LT1 (podium LT2-LT4, menara LT5-ATAP) + kolom."""
    d = beban_mati(sistem)
    pod = pr.poligon("PODIUM").area
    men = pr.poligon("MENARA").area
    return d * (3 * pod + 3 * men)


# ------------------------------------------------------------------ volume dan perbandingan
BESI = {"kolom": 200.0, "balok": 180.0, "pelat": 100.0, "dinding": 140.0}  # kg/m³ [Asumsi rasio tulangan]
INTI = [(22, 39), (46, 39), (70, 39), (22, 63), (46, 63), (70, 63)]


def volume(sistem):
    p = PRA[sistem]
    pod_x, pod_y = pr.MASSA["PODIUM"]["x"], pr.MASSA["PODIUM"]["y"]
    men = pr.MASSA["MENARA"]
    n_pod = len(GRID_X) * len(GRID_Y)
    n_men = sum(1 for x in GRID_X if men["x"][0] <= x <= men["x"][1]) * \
        sum(1 for y in GRID_Y if men["y"][0] <= y <= men["y"][1])
    kolom = n_pod * (p["kolom_podium"] / 1000) ** 2 * (4.5 + 4.5 + 4.2) + \
        n_men * (p["kolom_menara"] / 1000) ** 2 * (4.2 * 3)
    pj_pod = len(GRID_X) * (pod_y[1] - pod_y[0]) + len(GRID_Y) * (pod_x[1] - pod_x[0])
    nx = sum(1 for x in GRID_X if men["x"][0] <= x <= men["x"][1])
    ny = sum(1 for y in GRID_Y if men["y"][0] <= y <= men["y"][1])
    pj_men = nx * (men["y"][1] - men["y"][0]) + ny * (men["x"][1] - men["x"][0])
    b, h = p["balok"]
    balok = (3 * pj_pod + 3 * pj_men) * b / 1000 * (h - p["pelat"]) / 1000
    pelat = (3 * pr.poligon("PODIUM").area + 3 * pr.poligon("MENARA").area) * p["pelat"] / 1000
    dinding = 0.0
    if p["dinding"]:
        keliling = 6 * 2 * (4 + 6) + 2 * (8 + 8)  # 6 inti tangga 4 × 6 m + inti lif 8 × 8 m
        tinggi = (dict(tpl.LEVEL)["ATAP"] - dict(tpl.LEVEL)["LT1"]) / 1000
        dinding = keliling * tinggi * p["dinding"] / 1000 * 0.75  # 3 inti selatan setinggi atap, 3 utara sampai LT4
    v = {"kolom": kolom, "balok": balok, "pelat": pelat, "dinding": dinding}
    besi = sum(v[k] * BESI[k] for k in v) / 1000  # ton
    return {**v, "beton": sum(v.values()), "besi_ton": besi}


HARGA = {"beton_m3": 1.35, "besi_ton": 18.0, "bekisting_m3": 0.9}  # juta Rp [Asumsi indeks; harga survei di 3.8]


def biaya_relatif(sistem):
    v = volume(sistem)
    return v["beton"] * (HARGA["beton_m3"] + HARGA["bekisting_m3"]) + v["besi_ton"] * HARGA["besi_ton"]


def ringkasan():
    sp = spektrum()
    hasil = {"spektrum": sp, "pelat_min": tebal_pelat(), "balok_min": tinggi_balok_min()}
    for s in SISTEM:
        hasil[s] = {"kolom": cek_kolom(s), "V": gaya_geser_dasar(s), "volume": volume(s), "biaya": biaya_relatif(s)}
    hasil["selisih_biaya"] = hasil["GANDA"]["biaya"] / hasil["SRPMK"]["biaya"] - 1
    return hasil



def fmt(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


# ------------------------------------------------------------------ Excel
def buat_excel(keluar=BERKAS):
    import openpyxl

    from format_dokumen import AI, Lembar, set_font_bawaan

    r = ringkasan()
    sp = r["spektrum"]
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk grid, sistem struktur, dan pra-dimensi (langkah 3.6)",
                [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        "Acuan: SNI 1726:2019 hal. 37 Tabel 4, hal. 46-47 Tabel 6-7, hal. 49 Tabel 8-9, hal. 62 Tabel 12, hal. 84 "
        "Tabel 17-18, hal. 100 Tabel 20; SNI 2847:2019 hal. 157 Tabel 8.3.1.2, hal. 202 Tabel 9.3.1.1, 22.4.2; SNI "
        "1727:2020 hal. 52 Tabel 4.3-1, hal. 61 Pasal 4.11.2 (halaman = nomor halaman PDF di acuan/privat).",
        "Kelas situs SF (langkah 2.5-2.6): Fa dan Fv kelas SE dipakai SEMENTARA untuk pra-dimensi [Asumsi]. Spektrum "
        "desain dari analisis respons spesifik-situs di Tahap 4; ukuran di sini diperiksa ulang di sana.",
        "Grid modul 8 m: as 1-10 (x 12-84), as A-G (y 27-75). Menara digeser ke x 20-84, y 27-51 (64 × 24 m) agar "
        "kolom menerus tanpa balok transfer.",
        "Beban mati tambahan, rasio tulangan, dan indeks harga berlabel [Asumsi]; harga survei di langkah 3.8.",
        "Gambar: GK-06 '3.6 Gambar Rencana Struktur.pdf'; model BIMCraft 'model/RSTB-STR-T3-Pradimensi.bimc'.",
    ])], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Spektrum"), 2, "Parameter gempa sementara dan KDS", [26, 14, 14, 46])
    lb.catatan(LABEL + " Sel hijau rumus Excel.")
    r0, r1, r2 = lb.tabel(["Parameter", "Nilai", "Satuan", "Dasar"], [
        ["Ss", SS, "g", "Desain Spektra PUPR, Kota Jambi (2.6)"],
        ["S1", S1, "g", "idem"],
        ["Fa (kelas SE, interpolasi)", round(sp["Fa"], 4), "-", "SNI 1726 Tabel 6 hal. 46 [Asumsi: SE untuk SF]"],
        ["Fv (kelas SE, interpolasi)", round(sp["Fv"], 4), "-", "SNI 1726 Tabel 7 hal. 47 [Asumsi: SE untuk SF]"],
        ["SMS = Fa Ss", None, "g", "Pers. (7)"],
        ["SM1 = Fv S1", None, "g", "Pers. (8)"],
        ["SDS = 2/3 SMS", None, "g", "Pers. (9)"],
        ["SD1 = 2/3 SM1", None, "g", "Pers. (10)"],
        ["Kategori desain seismik", sp["KDS"], "-", "Tabel 8 dan 9 hal. 49, kategori risiko IV"],
        ["Ie", IE, "-", "Tabel 4 hal. 37"],
    ], rata=list("lccl"), fmt=[None, "0.000", None, None], fill_kolom={1: AI})
    w = lb.ws
    w[f"D{r1 + 4}"] = f"=D{r1 + 2}*D{r1}"
    w[f"D{r1 + 5}"] = f"=D{r1 + 3}*D{r1 + 1}"
    w[f"D{r1 + 6}"] = f"=2/3*D{r1 + 4}"
    w[f"D{r1 + 7}"] = f"=2/3*D{r1 + 5}"

    lb = Lembar(wb.create_sheet("Sistem"), 3, "Dua alternatif sistem struktur", [32, 22, 22, 40])
    lb.catatan(LABEL + " Berat seismik kasar (beban mati + SDL pelat di atas LT1).")
    a, g = r["SRPMK"], r["GANDA"]
    lb.tabel(["Butir", "Alternatif 1: SRPMK", "Alternatif 2: sistem ganda", "Dasar"], [
        ["R / Ω0 / Cd", "8 / 3 / 5,5", "7 / 2,5 / 5,5", "SNI 1726 Tabel 12 hal. 62; batas tinggi TB untuk KDS D"],
        ["Ct / x", "0,0466 / 0,9", "0,0488 / 0,75", "Tabel 18 hal. 84"],
        ["hn (m)", fmt(a["V"]["hn"]), fmt(g["V"]["hn"]), "ATAP +38,65 - LT1 +12,85"],
        ["Ta (detik)", fmt(a["V"]["Ta"], 3), fmt(g["V"]["Ta"], 3), "Pers. (36)"],
        ["Cs", fmt(a["V"]["Cs"], 4), fmt(g["V"]["Cs"], 4), "Pers. (31)-(33), dibatasi SD1/(T R/Ie)"],
        ["W (kN)", fmt(a["V"]["W"], 0), fmt(g["V"]["W"], 0), "kasar [Asumsi]"],
        ["V = Cs W (kN)", fmt(a["V"]["V"], 0), fmt(g["V"]["V"], 0), "sementara; Tahap 4 respons spesifik-situs"],
        ["Simpangan izin", "0,010 hsx", "0,010 hsx", "Tabel 20 hal. 100, kategori IV"],
        ["Kekakuan lateral", "rangka saja, simpangan menentukan", "inti dinding mengendalikan simpangan dan torsi",
         "penilaian kualitatif; dihitung di Tahap 4"],
    ], rata=list("lccl"), fill_kolom={1: AI, 2: AI})

    lb = Lembar(wb.create_sheet("Pra-dimensi"), 4, "Pra-dimensi elemen", [30, 20, 20, 44])
    lb.catatan(LABEL + " Pu kolom dalam (as D-6): 6 pelat × tributari 8 × 8 m, 1,2D + 1,6L, LL 2,87 kPa (ruang "
               "operasi/lab, konservatif). Cek silang PyNite portal 2D (T-44).")
    lb.tabel(["Elemen", "Alternatif 1: SRPMK", "Alternatif 2: sistem ganda", "Dasar"], [
        ["Pelat (mm), h min Tabel 8.3.1.2(d)", f"{PRA['SRPMK']['pelat']} (min {fmt(r['pelat_min'], 0)})",
         f"{PRA['GANDA']['pelat']} (min {fmt(r['pelat_min'], 0)})", "ℓn 7.600, fy 420, β 1 (hal. 157)"],
        ["Balok b × h (mm)", "{} × {}".format(*PRA["SRPMK"]["balok"]), "{} × {}".format(*PRA["GANDA"]["balok"]),
         f"h min ℓ/18,5 = {fmt(r['balok_min']['satu_sisi'], 0)} (Tabel 9.3.1.1 hal. 202); seismik ±ℓ/12 [Asumsi]"],
        ["Kolom podium/bawah menara (mm)", f"{PRA['SRPMK']['kolom_podium']} × {PRA['SRPMK']['kolom_podium']}",
         f"{PRA['GANDA']['kolom_podium']} × {PRA['GANDA']['kolom_podium']}", "fc' 35 MPa"],
        ["Kolom menara LT4-LT6 (mm)", f"{PRA['SRPMK']['kolom_menara']} × {PRA['SRPMK']['kolom_menara']}",
         f"{PRA['GANDA']['kolom_menara']} × {PRA['GANDA']['kolom_menara']}", "-"],
        ["Pu kolom dalam (kN)", fmt(a["kolom"]["Pu"], 0), fmt(g["kolom"]["Pu"], 0), "tributari"],
        ["φPn,maks (kN), ρ 1,5 %", fmt(a["kolom"]["phiPn"], 0), fmt(g["kolom"]["phiPn"], 0),
         "SNI 2847 Pasal 22.4.2: 0,65 × 0,80 [0,85 fc'(Ag - Ast) + fy Ast]"],
        ["Pu / (fc' Ag)", fmt(a["kolom"]["aksial_fc"], 3), fmt(g["kolom"]["aksial_fc"], 3),
         "batas daktilitas ±0,35 [Asumsi praktik]"],
        ["Dinding geser inti (mm)", "-", f"{PRA['GANDA']['dinding']}", "6 inti tangga + inti lif [Asumsi tebal]"],
        ["Beban helikopter AW139", "2 × 50,0 kN @ 2,44 m", "2 × 50,0 kN @ 2,44 m",
         "SNI 1727 Pasal 4.11.2 hal. 61: 0,75 × 66,7 kN; LL helipad 2,87 kPa"],
    ], rata=list("lccl"), fill_kolom={1: AI, 2: AI})

    lb = Lembar(wb.create_sheet("Volume"), 5, "Volume struktur atas dan biaya relatif", [26, 18, 18, 40])
    lb.catatan(LABEL + f" Rasio tulangan {BESI} kg/m³ dan indeks harga {HARGA} juta Rp [Asumsi]. Hanya gedung utama "
               "di atas LT1; pondasi dan gedung utilitas + parkir tidak termasuk.")
    va, vg = a["volume"], g["volume"]
    lb.tabel(["Butir", "SRPMK", "Sistem ganda", "Keterangan"], [
        ["Beton kolom (m³)", round(va["kolom"], 1), round(vg["kolom"], 1), ""],
        ["Beton balok (m³)", round(va["balok"], 1), round(vg["balok"], 1), "di bawah pelat"],
        ["Beton pelat (m³)", round(va["pelat"], 1), round(vg["pelat"], 1), ""],
        ["Beton dinding geser (m³)", round(va["dinding"], 1), round(vg["dinding"], 1), ""],
        ["Beton total (m³)", round(va["beton"], 1), round(vg["beton"], 1), ""],
        ["Tulangan (ton)", round(va["besi_ton"], 1), round(vg["besi_ton"], 1), ""],
        ["Biaya relatif (juta Rp, indeks)", round(a["biaya"]), round(g["biaya"]), "bukan RAB"],
        ["Selisih biaya sistem ganda", "-", f"+{fmt(100 * r['selisih_biaya'], 1)} %", "terhadap SRPMK"],
    ], rata=list("lccl"), fmt=[None, "#,##0.0", "#,##0.0", None], fill_kolom={1: AI, 2: AI})
    lb.kosong()
    lb.bagian("B", "Usulan untuk keputusan Defsa")
    lb.tabel(["Butir", "", "", "Uraian"], [
        ["Keputusan Defsa 19 Nov 2026", "", "", "Alternatif 2 sistem ganda: inti dinding mengendalikan simpangan 0,010 hsx (kategori IV), "
         "torsi menara yang tidak simetris terhadap podium, dan redundansi di situs SF; selisih biaya struktur rangka "
         f"±{fmt(100 * r['selisih_biaya'], 0)} % (indeks)."],
        ["Bila memilih SRPMK", "", "", "kolom 800 mm dan balok 650 mm; simpangan harus dibuktikan di Tahap 4."],
    ], rata=list("llll"), fill_kolom={3: AI}, beku=False)
    wb.save(keluar)
    return keluar


# ------------------------------------------------------------------ gambar GK-06 (rencana struktur tipikal)
def gambar_cad(status=None, sistem="GANDA"):
    from cad_lembar import STATUS_SETUJU, Gambar

    p = PRA[sistem]
    men = pr.MASSA["MENARA"]
    dwg = KELUAR / "Gambar" / "DWG" / "GK-06 Rencana Struktur.dwg"
    png = KELUAR / "Gambar" / "GK-06 Rencana Struktur.png"

    def k(x0, x1, y0, y1):
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    with Gambar(300) as g:
        x0, x1, y0, y1 = GRID_X[0], GRID_X[-1], GRID_Y[0], GRID_Y[-1]
        for i, x in enumerate(GRID_X):
            g.as_grid(str(i + 1), (x, y0 - 4), (x, y1 + 4))
        for j, y in enumerate(GRID_Y):
            g.as_grid(NAMA_Y[j], (x0 - 4, y), (x1 + 4, y))
        # balok
        g.layer("S-BALOK", 7, 0.35, "HIDDEN")
        b = p["balok"][0] / 1000 / 2
        for x in GRID_X:
            for ya, yb in zip(GRID_Y[:-1], GRID_Y[1:]):
                g.pline([(x - b, ya), (x - b, yb)], "S-BALOK")
                g.pline([(x + b, ya), (x + b, yb)], "S-BALOK")
        for y in GRID_Y:
            for xa, xb in zip(GRID_X[:-1], GRID_X[1:]):
                g.pline([(xa, y - b), (xb, y - b)], "S-BALOK")
                g.pline([(xa, y + b), (xb, y + b)], "S-BALOK")
        g.legenda_tambah("garis", "Balok B1 {} × {} (garis tersembunyi)".format(*p["balok"]), garis="HIDDEN",
                         tebal=0.35)
        # kolom
        g.layer("S-KOLOM", 7, 0.5)
        for x in GRID_X:
            for y in GRID_Y:
                s = (p["kolom_podium"]) / 1000 / 2
                g.arsir(k(x - s, x + s, y - s, y + s), "S-KOLOM", pola="SOLID")
        g.legenda_tambah("arsir", f"Kolom K1 {p['kolom_podium']} × {p['kolom_podium']} (LT1-LT3)", pola="SOLID")
        # dinding inti
        if p["dinding"]:
            g.layer("S-DINDING", 7, 0.5)
            t = p["dinding"] / 1000
            for cx, cy in INTI:
                luar, dalam = k(cx - 2 - t / 2, cx + 2 + t / 2, cy - 3 - t / 2, cy + 3 + t / 2), \
                    k(cx - 2 + t / 2, cx + 2 - t / 2, cy - 3 + t / 2, cy + 3 - t / 2)
                g.arsir_lubang(luar, [dalam], "S-DINDING", pola="ANSI31", skala_pola=0.4)
            lx0, lx1, ly0, ly1 = 50.0, 58.0, 35.0, 43.0
            g.arsir_lubang(k(lx0 - t / 2, lx1 + t / 2, ly0 - t / 2, ly1 + t / 2),
                           [k(lx0 + t / 2, lx1 - t / 2, ly0 + t / 2, ly1 - t / 2)], "S-DINDING", pola="ANSI31",
                           skala_pola=0.4)
            g.legenda_tambah("arsir", f"Dinding geser inti DG {p['dinding']} (tangga dan lif)", pola="ANSI31",
                             skala_pola=0.4)
        g.layer("A-MENARA", 7, 0.35, "DASHED")
        g.pline(k(*men["x"], *men["y"]), "A-MENARA", tutup=True)
        g.legenda_tambah("garis", "Batas menara LT4-LT6 di atas podium", garis="DASHED", tebal=0.35)
        g.layer("S-TEKS", 7, 0.25)
        g.teks((40, 47), f"PL {p['pelat']}", "S-TEKS", 2.0, j="MC", tebal=True)
        # ukuran berantai
        for xa, xb in zip(GRID_X[:-1], GRID_X[1:]):
            g.ukur((xa, y1 + 4), (xb, y1 + 4), ((xa + xb) / 2, y1 + 9))
        g.ukur((x0, y1 + 4), (x1, y1 + 4), ((x0 + x1) / 2, y1 + 12))
        for ya, yb in zip(GRID_Y[:-1], GRID_Y[1:]):
            g.ukur((x0 - 4, ya), (x0 - 4, yb), (x0 - 9, (ya + yb) / 2))
        g.ukur((x0 - 4, y0), (x0 - 4, y1), (x0 - 12, (y0 + y1) / 2))
        sp = spektrum()
        g.lembar("GK-06", "Rencana struktur LT2", "1:300", pusat=(48, 51),
                 subjudul=f"Alternatif usulan: {SISTEM[sistem]['nama'].lower()}; pra-dimensi langkah 3.6",
                 status=status or STATUS_SETUJU,
                 catatan=[
                     f"Gempa sementara: SDS {fmt(sp['SDS'], 3)}, SD1 {fmt(sp['SD1'], 3)} (kelas SE untuk SF), KDS "
                     f"{sp['KDS']}, Ie 1,5; spektrum spesifik-situs di Tahap 4.",
                     f"Sistem ganda R 7, Ω0 2,5, Cd 5,5 (SNI 1726 Tabel 12); simpangan izin 0,010 hsx.",
                     f"Beton fc' 35 (kolom, dinding), 30 (balok, pelat); BJTS 420.",
                     f"Kolom menara LT4-LT6 {p['kolom_menara']} × {p['kolom_menara']}; helipad AW139 2 × 50 kN.",
                 ])
        g.skala_grafis(205, 22, 20, bagi=4)
        g.panah_utara(318, 262, 10)
        g.simpan(dwg, PDF, png)
    return dwg


# ------------------------------------------------------------------ model BIM struktur
BIMC = AKAR / "model" / "RSTB-STR-T3-Pradimensi.bimc"
IFC = BIMC.with_suffix(".ifc")


def bangun_bim(sistem="GANDA", status="disetujui Defsa 19 Nov 2026"):
    from bimcraft import Sesi, tampilkan

    p = PRA[sistem]
    men = pr.MASSA["MENARA"]

    def mm(x, y):
        return [round(x * 1000), round(y * 1000)]

    kp, km = f"KL-{p['kolom_podium']}x{p['kolom_podium']}-fc35", f"KL-{p['kolom_menara']}x{p['kolom_menara']}-fc35"
    bl = "BL-{}x{}-fc30".format(*p["balok"])
    pl = f"PL-{p['pelat']}-fc30"
    ids = []
    with Sesi(tpl.BIMC) as b:
        b.cmd("project_info", {"status": "Desain Konsep - pra-dimensi struktur (langkah 3.6)"})
        for nama, ukuran in ((kp, p["kolom_podium"]), (km, p["kolom_menara"])):
            b.cmd("type", {"category": "structuralcolumn", "name": nama, "width": ukuran, "depth": ukuran,
                           "material": "Beton fc 35 S2"})
        b.cmd("type", {"category": "beam", "name": bl, "width": p["balok"][0], "depth": p["balok"][1],
                       "material": "Beton fc 30 S2"})
        b.cmd("type", {"category": "floor", "name": pl,
                       "layers": [{"function": "structure", "material": "Beton fc 30 S2", "thickness": p["pelat"]}]})
        if p["dinding"]:
            b.cmd("type", {"category": "wall", "name": f"DG-{p['dinding']}-fc35",
                           "layers": [{"function": "structure", "material": "Beton fc 35 S2",
                                       "thickness": p["dinding"]}]})
        for i, x in enumerate(GRID_X):
            b.cmd("grid", {"start": mm(x, GRID_Y[0] - 6), "end": mm(x, GRID_Y[-1] + 6), "name": str(i + 1)})
        for j, y in enumerate(GRID_Y):
            b.cmd("grid", {"start": mm(GRID_X[0] - 6, y), "end": mm(GRID_X[-1] + 6, y), "name": NAMA_Y[j]})
        tingkat = ["LT1", "LT2", "LT3", "LT4", "LT5", "LT6", "ATAP"]
        for x in GRID_X:
            for y in GRID_Y:
                dlm = men["x"][0] <= x <= men["x"][1] and men["y"][0] <= y <= men["y"][1]
                for a, c in zip(tingkat[:-1], tingkat[1:]):
                    if a in ("LT4", "LT5", "LT6") and not dlm:
                        continue
                    if a == "LT4" and not dlm:
                        continue
                    r = b.cmd("structural_column", {"at": mm(x, y), "type": kp if a in ("LT1", "LT2", "LT3") else km,
                                                     "level": a, "top_level": c})
                    ids.append(r.get("id"))
        for lv in tingkat[1:]:
            dlm_lv = lv in ("LT5", "LT6", "ATAP")
            xs = [x for x in GRID_X if not dlm_lv or men["x"][0] <= x <= men["x"][1]]
            ys = [y for y in GRID_Y if not dlm_lv or men["y"][0] <= y <= men["y"][1]]
            for y in ys:
                r = b.cmd("beam", {"points": [mm(xs[0], y), mm(xs[-1], y)], "type": bl, "level": lv})
                ids += r.get("ids", [])
            for x in xs:
                r = b.cmd("beam", {"points": [mm(x, ys[0]), mm(x, ys[-1])], "type": bl, "level": lv})
                ids += r.get("ids", [])
            bx = (xs[0] - 0.5, xs[-1] + 0.5)
            by = (ys[0] - 0.5, ys[-1] + 0.5)
            r = b.cmd("floor", {"boundary": [mm(bx[0], by[0]), mm(bx[1], by[0]), mm(bx[1], by[1]), mm(bx[0], by[1])],
                                "level": lv, "type": pl, "structural": True})
            ids.append(r.get("id"))
        if p["dinding"]:
            for cx, cy in INTI:
                r = b.cmd("wall", {"points": [mm(cx - 2, cy - 3), mm(cx + 2, cy - 3), mm(cx + 2, cy + 3),
                                              mm(cx - 2, cy + 3)], "closed": True, "type": f"DG-{p['dinding']}-fc35",
                                   "level": "LT1", "top_level": "ATAP" if cy < 51 else "LT4"})
                ids += r.get("ids", []) or [r.get("id")]
            r = b.cmd("wall", {"points": [mm(50, 35), mm(58, 35), mm(58, 43), mm(50, 43)], "closed": True,
                               "type": f"DG-{p['dinding']}-fc35", "level": "LT1", "top_level": "ATAP"})
            ids += r.get("ids", []) or [r.get("id")]
        ids = [i for i in ids if isinstance(i, int)]
        b.cmd("modify", {"ids": ids, "params": {"RSTB_Tahap": "3", "RSTB_LOD": "200", "RSTB_Status": status,
                                                "RSTB_KelasPaparan": "-",
                                                "RSTB_Sumber": f"pra-dimensi 3.6 ({sistem}); diganti Tahap 4"}})
        b.simpan(BIMC)
        b.simpan(IFC)
    tampilkan(BIMC)
    return BIMC, IFC


def buat():
    buat_excel()
    gambar_cad()
    bangun_bim()
    return BERKAS, PDF, BIMC

if __name__ == "__main__":
    import json

    r = ringkasan()
    print(json.dumps(r, indent=1, default=lambda o: round(o, 3) if isinstance(o, float) else o))
    print(beban_helikopter())


def pynite_portal(sistem):
    """Cek silang aksial kolom dalam (as 6, x = 52) dengan portal 2D PyNite as C/D: balok menerus dibebani tributari
    8 m, kolom jepit di dasar, berat kolom sebagai beban titik. Kembalikan aksial dasar kolom (kN, positif tekan)."""
    from Pynite import FEModel3D

    p = PRA[sistem]
    trib = BENTANG
    qu = (1.2 * beban_mati(sistem) + 1.6 * LL["operasi/lab"]) * trib  # kN/m
    z = {"LT1": 0.0, "LT2": 4.5, "LT3": 9.0, "LT4": 13.2, "LT5": 17.4, "LT6": 21.6, "ATAP": 25.8}
    men = pr.MASSA["MENARA"]["x"]
    m = FEModel3D()
    ec = 4700 * math.sqrt(35) * 1000  # kN/m² (SNI 2847 19.2.2.1)
    m.add_material("beton", ec, ec / 2.4, 0.2, 24.0)
    b, h = p["balok"][0] / 1000, p["balok"][1] / 1000
    m.add_section("balok", b * h, h * b ** 3 / 12, b * h ** 3 / 12, 0.0)
    for nama, s in (("kp", p["kolom_podium"] / 1000), ("km", p["kolom_menara"] / 1000)):
        m.add_section(nama, s * s, s ** 4 / 12, s ** 4 / 12, 0.14 * s ** 4)
    tingkat = list(z)
    for x in GRID_X:
        for lv in tingkat:
            if lv in ("LT5", "LT6", "ATAP") and not (men[0] <= x <= men[1]):
                continue
            m.add_node(f"{x:g}-{lv}", x, z[lv], 0.0)
            m.def_support(f"{x:g}-{lv}", lv == "LT1", lv == "LT1", True, True, True, lv == "LT1")
    for x in GRID_X:
        for a, b_ in zip(tingkat[:-1], tingkat[1:]):
            if f"{x:g}-{b_}" in m.nodes:
                sek = "kp" if b_ in ("LT2", "LT3", "LT4") else "km"
                m.add_member(f"K{x:g}-{b_}", f"{x:g}-{a}", f"{x:g}-{b_}", "beton", sek)
                s = (p["kolom_podium"] if sek == "kp" else p["kolom_menara"]) / 1000
                m.add_node_load(f"{x:g}-{b_}", "FY", -1.2 * GAMMA_C * s * s * (z[b_] - z[a]))
    for lv in tingkat[1:]:
        xs = [x for x in GRID_X if f"{x:g}-{lv}" in m.nodes]
        for a, b_ in zip(xs[:-1], xs[1:]):
            nm = f"B{lv}-{a:g}"
            m.add_member(nm, f"{a:g}-{lv}", f"{b_:g}-{lv}", "beton", "balok")
            m.add_member_dist_load(nm, "FY", -qu, -qu)
    m.analyze_linear(check_statics=False)
    return m.nodes["52-LT1"].RxnFY["Combo 1"]
