"""Tahap 2 langkah 2.1 tugas D: mutu contoh tak terganggu (Lunne dkk. 1997; Terzaghi dkk. 1996).

Fungsi di sini dipakai tahap2_koreksi_data.py untuk mengisi lembar Mutu Contoh.
Sumber kriteria: FHWA GEC 5 (NHI-16-072) Tabel 6-1 dan 6-2, hal. 6-7.
σ'v0 memakai profil berat isi SEMENTARA (lapisan dari log bor, γ dari lab) dan MAT di muka tanah
(keputusan Tahap 1). Parameter tanah desain ditetapkan di langkah 2.4.
"""
import math
from pathlib import Path

import openpyxl

AKAR = Path(__file__).resolve().parents[1]
LAMA = AKAR / "01 Penyelidikan Tanah"
BARU = LAMA / "Penyelidikan Tambahan"
GAMMA_W = 9.81

# Berat isi sementara (kN/m³) per jenis lapisan, dengan label sumber.
GAMMA = {
    "Urug": (17.0, "[Asumsi: tidak ada contoh UD urugan]"),
    "Kerak": (17.8, "[Uji sendiri: rata-rata BH-1 UD-1, BH-2 UD-1]"),
    "Gambut": (10.7, "[Uji sendiri: BH-7 UD-2]"),
    "Lempung lunak": (15.2, "[Uji sendiri: rata-rata 21 contoh CH 2-9,5 m]"),
    "Pasir": (19.0, "[Asumsi: tidak ada contoh UD pasir; dicek di 2.4]"),
    "Lempung kaku": (19.1, "[Uji sendiri: rata-rata 5 contoh CH 20-29,5 m]"),
}


def _jenis(teks, atas, bawah, pertama_ch):
    t = teks.lower().strip()
    if "urug" in t or t == "ml":
        return "Urug"
    if t.startswith(("lempung organik", "pt")):
        return "Gambut"
    if t.startswith(("pasir", "sp")):
        return "Pasir"
    if atas > 17:
        return "Lempung kaku"
    if pertama_ch and bawah <= 2.5:
        return "Kerak"
    return "Lempung lunak"


def baca_lapisan():
    """{bor: [(atas, bawah, jenis)]} dari lembar Log tiap bor."""
    hasil = {}
    for path, bor_list in [(LAMA / "Bor dan SPT.xlsx", ["BH-1", "BH-2", "BH-3"]),
                           (BARU / "Bor Tambahan dan SPT.xlsx", ["BH-4", "BH-5", "BH-6", "BH-7", "BH-8"])]:
        wb = openpyxl.load_workbook(path, data_only=True)
        for bor in bor_list:
            lap, pertama = [], True
            for r in wb["Log " + bor].iter_rows(values_only=True):
                isi = [c for c in r if c is not None]
                if len(isi) >= 3 and isinstance(isi[0], (int, float)) and isinstance(isi[1], (int, float)):
                    teks = next(x for x in isi if isinstance(x, str))
                    j = _jenis(teks, isi[0], isi[1], pertama)
                    if j not in ("Urug",):
                        pertama = False
                    lap.append((isi[0], isi[1], j))
            if lap[0][0] > 0:  # log lama mulai di bawah 0: bagian atas dianggap urugan
                lap.insert(0, (0.0, lap[0][0], "Urug"))
            hasil[bor] = lap
    return hasil


def sigma_v0(lapisan, z):
    """Tegangan vertikal total (kPa) di kedalaman z."""
    s = 0.0
    for atas, bawah, j in lapisan:
        if z <= atas:
            break
        s += GAMMA[j][0] * (min(z, bawah) - atas)
    return s


def baca_konsolidasi():
    """Daftar contoh: titik, contoh, dari, sampai, e0, σ'p, kurva [(σ, e)] tahap beban."""
    contoh = {}
    for path in [LAMA / "Laboratorium.xlsx", BARU / "Laboratorium Tambahan.xlsx"]:
        wb = openpyxl.load_workbook(path, data_only=True)
        for r in wb["Ringkasan Konsolidasi"].iter_rows(values_only=True):
            isi = [c for c in r if c is not None]
            if len(isi) >= 9 and str(isi[0]).startswith("BH") and isinstance(isi[5], (int, float)):
                contoh[(isi[0], isi[1])] = dict(titik=isi[0], contoh=isi[1], dari=isi[2], sampai=isi[3],
                                                e0=isi[5], sp=isi[8], kurva=[])
        for r in wb["Konsolidasi"].iter_rows(values_only=True):
            isi = [c for c in r if c is not None]
            if len(isi) >= 7 and (isi[0], isi[1]) in contoh and isi[4] == "Beban":
                contoh[(isi[0], isi[1])]["kurva"].append((isi[5], isi[6]))
    return list(contoh.values())


def e_pada(kurva, s):
    """Interpolasi e terhadap log σ' di antara dua tahap beban; kembalikan (e, σ1, e1, σ2, e2)."""
    for (s1, e1), (s2, e2) in zip(kurva, kurva[1:]):
        if s1 <= s <= s2:
            return e1 + (e2 - e1) * math.log10(s / s1) / math.log10(s2 / s1), s1, e1, s2, e2
    raise ValueError(f"σ'v0 = {s:.1f} kPa di luar rentang kurva")


def peringkat_lunne(de, ocr):
    if ocr > 4:
        return "Di luar tabel (OCR > 4)"
    b = (0.04, 0.07, 0.14) if ocr <= 2 else (0.03, 0.05, 0.10)
    for batas, nama in zip(b, ["Sangat baik-istimewa", "Baik-cukup", "Buruk"]):
        if de < batas:
            return nama
    return "Sangat buruk"


def peringkat_sqd(ev):
    for batas, nama in [(1, "A"), (2, "B"), (4, "C"), (8, "D")]:
        if ev < batas:
            return nama
    return "E"


def hitung(mat=0.0):
    """Hitung mutu tiap contoh. mat = kedalaman muka air tanah (m)."""
    lap = baca_lapisan()
    hasil = []
    for c in baca_konsolidasi():
        z = (c["dari"] + c["sampai"]) / 2
        sv = sigma_v0(lap[c["titik"]], z)
        u0 = GAMMA_W * max(0.0, z - mat)
        sv0 = sv - u0
        ev0, s1, e1, s2, e2 = e_pada(c["kurva"], sv0)
        de = (c["e0"] - ev0) / c["e0"]
        ev = (c["e0"] - ev0) / (1 + c["e0"]) * 100
        ocr = c["sp"] / sv0
        hasil.append(dict(c, z=z, sv=sv, u0=u0, sv0=sv0, ev0=ev0, s1=s1, e1=e1, s2=s2, e2=e2, de=de, ev=ev,
                          ocr=ocr, lunne=peringkat_lunne(de, ocr), sqd=peringkat_sqd(ev)))
    return hasil


if __name__ == "__main__":
    for mat in (0.0, 1.0):
        print(f"--- MAT {mat} m")
        for h in hitung(mat):
            print(f"{h['titik']} {h['contoh']} z={h['z']:.2f} σv={h['sv']:.1f} σ'v0={h['sv0']:.1f} e0={h['e0']} "
                  f"ev0={h['ev0']:.3f} Δe/e0={h['de']:.3f} εv={h['ev']:.1f}% OCR={h['ocr']:.2f} "
                  f"{h['lunne']} SQD {h['sqd']}")
