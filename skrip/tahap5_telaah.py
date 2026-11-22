"""Tahap 5 langkah 5.0: telaah data owner di atas grid dan tapak (plot koordinat, syarat MRI, elevasi dan air pit lift,
konsistensi satuan, pernyataan ditolak, acuan, permintaan data).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (20 Nov 2026); draf, menunggu persetujuan
Defsa. Kunci jawaban tidak dibuka. Angka dibaca LANGSUNG dari `04 Struktur Atas/Data Owner/Data Beban MEP Rinci.xlsx`.

Konstanta proyek (sumber di lembar Excel): grid [Data Beban MEP Rinci, Umum]; peil LT1 +12,85 dan halaman +12,05
[3.3 Peil dan Urugan]; Q50 +11,85 dan Q100 +12,31 [3.3]; tinggi tekan akuifer desain +11,20 [2.4/Tahap 2]; jalur ambulans
x 88-94 [Asumsi lebar, tahap3_basement.py]; zona parkir P4 x 94-100, y 44-76 [3.5]; tebal pelat dasar pit 0,40 m
[Asumsi, dicek 5.5]; γw 9,81 kN/m³.
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).parent))

AKAR = Path(__file__).resolve().parents[1]
MEP = AKAR / "04 Struktur Atas" / "Data Owner" / "Data Beban MEP Rinci.xlsx"
KELUAR = AKAR / "05 Struktur Tengah"
BERKAS = KELUAR / "5.0 Telaah Data Tahap 5.xlsx"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
STATUS = "Disetujui Defsa 20 Nov 2026"
LABEL_AI = f"DIISI AI ATAS PERMINTAAN DEFSA (20 Nov 2026), sel hijau; {STATUS.lower()}. Kunci jawaban tidak dibuka."

# ------------------------------------------------------------------ konstanta proyek
GRID_X = [12.0 + 8.0 * i for i in range(10)]   # as 1-10 [Data Beban MEP Rinci, Umum]
NAMA_X = [str(i + 1) for i in range(10)]
GRID_Y = [27.0 + 8.0 * j for j in range(7)]    # as A-G
NAMA_Y = list("ABCDEFG")
TOL_AS = 0.05                                   # m, tepi dianggap tepat di as
GAMMA_W = 9.81                                  # kN/m3
LT1 = 12.85                                     # [3.3 Peil dan Urugan]
HALAMAN = 12.05                                 # [3.3]
Q50, Q100 = 11.85, 12.31                        # [3.3]
TEKAN_DESAIN = 11.20                            # tinggi tekan akuifer desain [2.4/Tahap 2]
TEBAL_DASAR_PIT = 0.40                          # m [Asumsi, dicek 5.5]
JALUR_X = (88.0, 94.0)                          # jalur ambulans, sumbu 91 [Asumsi lebar, tahap3_basement.py]
JALUR_Y = (44.0, 76.0)                          # [Asumsi: jalur menerus di sisi timur setinggi zona P4]
P4 = (94.0, 100.0, 44.0, 76.0)                  # zona parkir P4 x0, x1, y0, y1 [3.5]
UTILITAS = (100.0, 134.0, 44.0, 76.0)           # gedung utilitas [3.5]
RADIUS_NONMAGNET = 1.0                          # m, rekomendasi pabrikan (Syarat MRI butir 7)
KG_KE_KN = 9.81 / 1000
# angka lama Data MEP Awal (5 Mar 2027) yang masih dipakai lembar Ringkasan Atap
CHILLER_KG_AWAL, TANGKI_T_AWAL, ELEV_UTILITAS_AWAL = 3900.0, 158.0, 11.30


# ------------------------------------------------------------------ fungsi hitung murni
def parse_rentang(s):
    """'66,0-77,0' -> (66.0, 77.0); angka tunggal -> (v, v)."""
    if isinstance(s, (int, float)):
        return float(s), float(s)
    t = str(s).replace(" ", "").replace("–", "-")
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)(?:-(\d+(?:[.,]\d+)?))?", t)
    if not m:
        raise ValueError(f"rentang tidak terbaca: {s!r}")
    a = float(m.group(1).replace(",", "."))
    return a, float(m.group(2).replace(",", ".")) if m.group(2) else a


def jarak_titik_ke_kotak(px, py, x0, x1, y0, y1):
    """Jarak terdekat titik ke kotak (0 bila di dalam)."""
    return math.hypot(max(x0 - px, 0.0, px - x1), max(y0 - py, 0.0, py - y1))


def as_terdekat(v, grid, nama):
    """(nama-nama as terdekat, jarak); as kembar bila jarak sama (mis. di tengah bentang)."""
    d = [abs(v - g) for g in grid]
    dm = min(d)
    return [n for n, di in zip(nama, d) if abs(di - dm) < 1e-9], dm


def analisis_tepi(a, b, grid, nama):
    """Dua tepi (a, b) terhadap as: [(nilai tepi, [as terdekat], jarak)]."""
    return [(v, *as_terdekat(v, grid, nama)) for v in (a, b)]


def status_plot(x0, x1, y0, y1):
    """'di atas as' bila keempat tepi di as; selain itu rincian tepi yang di tengah bentang."""
    bagian = []
    for sb, (a, b), grid, nama in (("x", (x0, x1), GRID_X, NAMA_X), ("y", (y0, y1), GRID_Y, NAMA_Y)):
        for v, n, d in analisis_tepi(a, b, grid, nama):
            if d > TOL_AS:
                bagian.append(f"tepi {sb} {idn(v)} di tengah bentang ({idn(d)} m dari as {' dan '.join(n)})")
    return "; ".join(bagian) if bagian else "di atas as"


def tekanan_angkat(tinggi_tekan, sisi_bawah_pelat):
    """u = γw·h (kPa), h = tinggi tekan di atas sisi bawah pelat (tidak negatif)."""
    return GAMMA_W * max(0.0, tinggi_tekan - sisi_bawah_pelat)


def idn(v, d=1):
    """Angka berkoma desimal, titik ribuan (untuk teks di sel)."""
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------------------------------------------ baca data owner
def baca_baris(wb, nama, kolom_kode="Kode"):
    """Baris data lembar `nama` sebagai dict {kepala: nilai}; kepala = baris yang memuat `kolom_kode`."""
    rows = list(wb[nama].iter_rows(values_only=True))
    for i, r in enumerate(rows):
        if kolom_kode in r:
            idx = [(j, h) for j, h in enumerate(r) if h is not None]
            return [{h: rr[j] for j, h in idx} for rr in rows[i + 1:] if rr[r.index(kolom_kode)] is not None]
    raise ValueError(f"kepala {kolom_kode!r} tidak ditemukan di {nama}")


def baca_item(berkas=MEP):
    """Semua alat, alat medis, lift, dan shaft/lubang dengan koordinat kotak [dict]."""
    wb = openpyxl.load_workbook(berkas, data_only=True)
    out = []
    spesifik = (("Daftar Alat", "Uraian", "Lantai / bidang", "x (m)", "y (m)"),
                ("Alat Medis", "Alat", "Lantai", "x (m)", "y (m)"),
                ("Lift", "Jenis", "Lantai layanan", "x shaft (m)", "y shaft (m)"),
                ("Shaft dan Lubang", "Fungsi", "Lantai tembus", "x (m)", "y (m)"))
    for lembar, ku, kl, kx, ky in spesifik:
        for r in baca_baris(wb, lembar):
            x0, x1 = parse_rentang(r[kx])
            y0, y1 = parse_rentang(r[ky])
            out.append({"lembar": lembar, "kode": r["Kode"], "uraian": str(r[ku]), "lantai": str(r[kl]),
                        "x": (x0, x1), "y": (y0, y1), "raw": r})
    return out


def _num(s):
    return float(str(s).replace(",", "."))


def syarat_mri(berkas=MEP):
    """Isocenter, syarat jarak (m), dan koordinat alat terkait dari lembar Syarat MRI dan Shaft/Alat/Lift."""
    wb = openpyxl.load_workbook(berkas, data_only=True)
    sy = {r["Butir"]: r["Syarat"] for r in baca_baris(wb, "Syarat MRI", "Butir")}
    iso = tuple(_num(v) for v in re.findall(r"[xy] (\d+(?:,\d+)?)", sy["Pusat magnet (isocenter) rencana"]))
    d_logam = _num(re.search(r"(\d+(?:,\d+)?) m", sy["Benda logam bergerak besar (mobil, ambulans, truk)"]).group(1))
    d_lift = _num(re.search(r"(\d+(?:,\d+)?) m", sy["Lift dan bobot imbang"]).group(1))
    item = {i["kode"]: i for i in baca_item(berkas)}
    return {"iso": iso, "d_logam": d_logam, "d_lift": d_lift, "item": item}


def jarak_mri(m):
    """Jarak isocenter ke tiap unsur (m) dan statusnya."""
    px, py = m["iso"]
    it = m["item"]

    def kotak(k):
        return it[k]["x"] + it[k]["y"]

    j = {
        "sumbu_jalur": jarak_titik_ke_kotak(px, py, 91.0, 91.0, *JALUR_Y),
        "tepi_barat_lajur": jarak_titik_ke_kotak(px, py, JALUR_X[0], JALUR_X[0], *JALUR_Y),
        "tepi_p4": jarak_titik_ke_kotak(px, py, P4[0], P4[0], P4[2], P4[3]),
        "L-1..4": jarak_titik_ke_kotak(px, py, *kotak("L-1..4")),
        "L-5..6": jarak_titik_ke_kotak(px, py, *kotak("L-5..6")),
        "L-7": jarak_titik_ke_kotak(px, py, *kotak("L-7")),
        "SH-6": jarak_titik_ke_kotak(px, py, *kotak("SH-6")),
        "R-06": jarak_titik_ke_kotak(px, py, *kotak("R-06")),
        "M-04": jarak_titik_ke_kotak(px, py, *kotak("M-04")),
    }
    return j


def as_ke_isocenter(m):
    """As grid terdekat ke isocenter: [(nama, posisi, jarak)] urut jarak."""
    px, py = m["iso"]
    h = [(f"as {n}", g, abs(px - g)) for n, g in zip(NAMA_X, GRID_X)] + \
        [(f"as {n}", g, abs(py - g)) for n, g in zip(NAMA_Y, GRID_Y)]
    return sorted(h, key=lambda t: t[2])


def akibat_mri(m):
    """Dua akibat jarak ke jalur: geser isocenter ke barat, atau geser lajur ke timur."""
    px, py = m["iso"]
    x_maks = JALUR_X[0] - m["d_logam"]            # isocenter paling timur bila lajur tetap
    tepi_min = px + m["d_logam"]                  # tepi barat lajur paling barat bila isocenter tetap
    lebar = JALUR_X[1] - JALUR_X[0]
    lajur = (tepi_min, tepi_min + lebar)
    makan_p4 = max(0.0, min(lajur[1], P4[1]) - max(lajur[0], P4[0]))
    return {"x_iso_maks": x_maks, "jarak_as9": abs(x_maks - 76.0), "geser_barat": px - x_maks,
            "tepi_min": tepi_min, "sumbu_min": tepi_min + lebar / 2, "lajur": lajur, "makan_p4": makan_p4,
            "lebar_p4": P4[1] - P4[0], "geser_timur": tepi_min - JALUR_X[0]}


def pit_lift(berkas=MEP):
    """Pit lift dari lembar Lift: dasar, kedalaman, sisi bawah pelat, tinggi air dan tekanan angkat."""
    wb = openpyxl.load_workbook(berkas, data_only=True)
    out = []
    for r in baca_baris(wb, "Lift"):
        dasar, dalam = float(r["Elevasi dasar pit (m)"]), float(r["Kedalaman pit (m)"])
        bawah = dasar - TEBAL_DASAR_PIT
        out.append({"kode": r["Kode"], "dasar": dasar, "dalam": dalam, "jumlah_cek": dasar + dalam, "bawah": bawah,
                    "selisih": {k: dasar - v for k, v in (("tekan", TEKAN_DESAIN), ("q50", Q50), ("q100", Q100),
                                                           ("halaman", HALAMAN))},
                    "h": {k: max(0.0, v - bawah) for k, v in (("tekan", TEKAN_DESAIN), ("q50", Q50), ("q100", Q100))},
                    "u": {k: tekanan_angkat(v, bawah) for k, v in (("tekan", TEKAN_DESAIN), ("q50", Q50),
                                                                   ("q100", Q100))}})
    return out


def beban_atap(berkas=MEP):
    """Beban atap podium utara dari Daftar Alat dan angka Ringkasan Atap (kN)."""
    wb = openpyxl.load_workbook(berkas, data_only=True)
    d = {r["Kode"]: r for r in baca_baris(wb, "Daftar Alat")}
    chiller = d["M-01"]["Jumlah"] * d["M-01"]["Berat operasi per unit (kN)"]
    tangki = d["M-02"]["Jumlah"] * d["M-02"]["Berat operasi per unit (kN)"]
    pompa = sum(d[k]["Jumlah"] * d[k]["Berat operasi per unit (kN)"] for k in ("M-03", "M-04"))
    rs = {r["Kelompok alat"]: r["Beban operasi (kN)"] for r in baca_baris(wb, "Ringkasan Atap", "Kelompok alat")}
    luas = 48.0 * 24.0
    benar = chiller + tangki + pompa
    return {"chiller": chiller, "tangki": tangki, "pompa": pompa, "jumlah": benar, "luas": luas,
            "q": benar / luas, "ring_chiller": rs["Chiller 4 unit"], "ring_tangki": rs["Tangki air atap"],
            "ring_pompa": rs["Pompa booster dan sirkulasi"], "ring_jumlah": rs["Jumlah beban alat atap podium utara"],
            "q_ring": rs["Jumlah beban alat atap podium utara"] / luas, "d": d}


def konsistensi(berkas=MEP):
    """Daftar cek satuan: (butir, nilai di data, nilai hitung ulang, satuan, formula Excel, status, keterangan)."""
    a = beban_atap(berkas)
    wb = openpyxl.load_workbook(berkas, data_only=True)
    medis = {r["Kode"]: r for r in baca_baris(wb, "Alat Medis")}
    p1, p2 = (parse_rentang(x) for x in ("7,0-7,0", "6,0-6,0"))
    panjang_dinding = p1[0] + p2[0]
    mag = medis["R-03"]["Berat per unit (kN)"]
    ring_pel = medis["R-04"]["Berat per unit (kN)"]
    t = a["d"]["M-02"]["Berat kosong per unit (kN)"]
    return [
        ("Chiller di Ringkasan Atap: 4 × 3.900 kg", a["ring_chiller"], 4 * CHILLER_KG_AWAL * KG_KE_KN, "kN",
         "=4*3900*9.81/1000", "Konversi cocok, angka dasar lama",
         "Konversi kg→kN benar (153,0 ≈ 153,2) tetapi memakai berat Data MEP Awal."),
        ("Chiller di Daftar Alat: 4 × 115,8", a["chiller"], 4 * a["d"]["M-01"]["Berat operasi per unit (kN)"], "kN",
         "=4*115.8", "Beda dari Ringkasan; sudah ditangani",
         "463,2 kN dipakai. Tahap 4: M-1 (Ringkasan Atap) dan M-8 (115,8 kN per unit, data baru dipakai)."),
        ("Tangki di Ringkasan Atap: 158 t", a["ring_tangki"], TANGKI_T_AWAL * 1000 * 9.81 / 1000, "kN",
         "=158*9.81", "Konversi cocok, angka dasar lama",
         "158 t × 9,81 = 1.550 kN; letak dan ukuran baru, volume menjadi 210 m³."),
        ("Tangki di Daftar Alat: 210 m³ × 9,81 + 107,9", a["tangki"], 210 * GAMMA_W + t, "kN",
         "=210*9.81+107.9", "OK", "Isi penuh 2.060,1 + berat kosong 107,9 = 2.168,0 kN."),
        ("Pompa M-03 dan M-04: 3 × 3,9 + 4 × 8,3", a["ring_pompa"], a["pompa"], "kN",
         "=3*3.9+4*8.3", "OK", "Sama dengan Ringkasan Atap (44,9 kN)."),
        ("Jumlah atap podium utara", a["ring_jumlah"], a["jumlah"], "kN",
         "=463.2+2168+44.9", "Beda; sudah ditangani",
         f"Jumlah benar {idn(a['jumlah'])} kN, bukan {idn(a['ring_jumlah'])} kN "
         f"(+{idn((a['jumlah'] / a['ring_jumlah'] - 1) * 100, 0)} %). Tahap 4: M-1."),
        ("Luas atap podium utara: 48 × 24", 1152.0, a["luas"], "m²", "=48*24", "OK",
         "x 36-84 (48 m) dan y 51-75 (24 m); Ringkasan Atap memakai 1.152 m²."),
        ("Beban rata-rata atap", a["q_ring"], a["q"], "kPa", "=(463.2+2168+44.9)/1152", "Beda; sudah ditangani",
         f"{idn(a['q'], 2)} kPa rata-rata (bukan {idn(a['q_ring'], 1)}); tangki lokal 30,1 kPa pada 72 m² (Tahap 4: M-1)."),
        ("Pelindung MRI R-04: 93,2 kN / 13 m", 7.3, ring_pel / panjang_dinding, "kN/m'", "=93.2/13", "OK",
         f"Dinding 7,0 + 6,0 = {idn(panjang_dinding)} m; {idn(ring_pel / panjang_dinding, 2)} ≈ ±7,3 (selisih "
         f"{idn(abs(ring_pel / panjang_dinding - 7.3) / 7.3 * 100)} %)."),
        ("Magnet MRI: 4 kaki × 12 kN", mag, 4 * 12.0, "kN", "=4*12", "OK", "48 ≈ 48,1 kN (pembulatan)."),
        ("Tekanan per kaki magnet: 12 kN / (0,25 × 0,25)", 192.0, 12.0 / (0.25 * 0.25), "kPa", "=12/(0.25*0.25)",
         "OK", "Tekanan kontak lokal 192 kPa pada tapak 0,25 × 0,25 m; dicek terhadap pelat di 5.2/5.3."),
        ("Elevasi gedung utilitas: Data MEP Awal +11,30", ELEV_UTILITAS_AWAL, LT1, "m", "=12.85",
         "Beda; digantikan", "Diganti +12,85 (3.3 Peil dan Urugan); lembar Gedung Utilitas memakai +12,85."),
    ]


# ------------------------------------------------------------------ acuan
ACUAN = [
    ("SNI 2847:2019 (beton struktural)", r"2847"),
    ("SNI 1726:2019 (ketahanan gempa)", r"1726"),
    ("SNI 1727:2020 (beban desain minimum)", r"1727"),
    ("SNI 8460:2017 (perancangan geoteknik)", r"8460"),
    ("AISC Design Guide 11 / CCIP-016 / SCI P354 (getaran lantai)", r"design.?guide.?11|dg.?11|ccip|p354"),
    ("ACI 440.11-22 / ACI 440.1R (tulangan GFRP)", r"440"),
    ("ASTM A955 (tulangan baja tahan karat)", r"a955"),
    ("Pedoman tapak MRI pabrikan", r"mri|magnet"),
    ("Permen PUPR 28/2015 (garis sempadan sungai dan danau)", r"permen.?pupr.?28|pupr.?28.?2015"),
]


def daftar_acuan(folder=AKAR / "acuan"):
    """Nama berkas di acuan/ (termasuk privat, pustaka, jurnal, publik) dengan subfolder-nya."""
    nama = []
    for sub in ("privat", "pustaka", "jurnal", "publik"):
        d = folder / sub
        if d.is_dir():
            nama += [f"{sub}/{p.name}" for p in sorted(d.iterdir()) if p.is_file()]
    return nama


def cek_acuan(nama_berkas):
    """[(acuan, nama berkas yang cocok atau None)]."""
    hasil = []
    for ket, pola in ACUAN:
        cocok = [n for n in nama_berkas if re.search(pola, n, re.I)]
        hasil.append((ket, "; ".join(cocok) if cocok else None))
    return hasil


# ------------------------------------------------------------------ ringkasan temuan
def ringkas(berkas=MEP):
    m = syarat_mri(berkas)
    return {"mri": m, "jarak": jarak_mri(m), "as_iso": as_ke_isocenter(m), "akibat": akibat_mri(m),
            "pit": pit_lift(berkas), "atap": beban_atap(berkas), "item": baca_item(berkas)}


def temuan(r):
    j, ak, a = r["jarak"], r["akibat"], r["atap"]
    pit = {p["kode"]: p for p in r["pit"]}
    p14, p56, p7 = pit["L-1..4"], pit["L-5..6"], pit["L-7"]
    tangki = next(i for i in r["item"] if i["kode"] == "M-02")
    d_x72 = analisis_tepi(*tangki["x"], GRID_X, NAMA_X)[1]
    d_y73 = analisis_tepi(*tangki["y"], GRID_Y, NAMA_Y)[1]
    return [
        ["T-1", f"Jarak isocenter MRI (80,5; 57,0) ke sumbu jalur ambulans x 91 hanya {idn(j['sumbu_jalur'])} m dan ke "
                f"tepi barat lajur x 88 {idn(j['tepi_barat_lajur'])} m; syarat ≥ 12,0 m TIDAK terpenuhi (kurang "
                f"{idn(12 - j['tepi_barat_lajur'])} m dari tepi lajur). Tepi zona parkir P4 x 94: {idn(j['tepi_p4'])} m OK.",
         "Syarat MRI", "Tidak memenuhi"],
        ["T-2", f"Akibat T-1: isocenter harus x ≤ {idn(ak['x_iso_maks'])} (tepat di as 9, balok dan sloof as 9 masuk "
                f"radius 1,0 m), atau tepi barat lajur ≥ x {idn(ak['tepi_min'])} (lajur {idn(ak['lajur'][0])}-"
                f"{idn(ak['lajur'][1])}) yang memakan {idn(ak['makan_p4'])} dari {idn(ak['lebar_p4'], 0)} m zona P4.",
         "Syarat MRI", "Perlu keputusan"],
        ["T-3", f"Lift dan bobot imbang ≥ 8,0 m dari isocenter: L-1..4 {idn(j['L-1..4'])} m, L-5..6 "
                f"{idn(j['L-5..6'])} m, L-7 {idn(j['L-7'])} m; memenuhi.", "Syarat MRI", "OK"],
        ["T-4", f"Pompa M-04 (atap podium +21,85, getaran 24,2 Hz) tepat di atas ruang MRI; kompresor R-06 "
                f"{idn(j['R-06'])} m dari isocenter (getaran 50 Hz); SH-6 (lubang helium) {idn(j['SH-6'])} m.",
         "Syarat MRI, 5.2-5.3", "Catatan"],
        ["T-5", f"As terdekat ke isocenter: as E y 59 = {idn(r['as_iso'][0][2])} m, as 10 x 84 = "
                f"{idn(r['as_iso'][1][2])} m, as 9 x 76 = {idn(r['as_iso'][2][2])} m; tidak ada balok atau sloof dalam "
                "radius 1,0 m. Tulangan non-magnetik hanya di pelat panel 9-10/D-E (x 79,5-81,5; y 56-58).",
         "Syarat MRI", "OK"],
        ["T-6", f"Tangki M-02: tepi x {idn(d_x72[0], 0)} berada {idn(d_x72[2])} m dari as {' dan '.join(d_x72[1])}; "
                f"tepi y {idn(d_y73[0], 0)} berada {idn(d_y73[2])} m dari as {' dan '.join(d_y73[1])}; tepi x 60 dan "
                "y 67 tepat di as 7 dan as F. Tepi timur dan utara di tengah bentang (dasar 5.1).",
         "Plot Koordinat", "Perlu 5.1"],
        ["T-7", f"Pit lift tekanan angkat (tinggi tekan +11,20 / Q50 / Q100): L-1..4 {idn(p14['u']['tekan'])} / "
                f"{idn(p14['u']['q50'])} / {idn(p14['u']['q100'])} kPa; L-5..6 {idn(p56['u']['tekan'])} / "
                f"{idn(p56['u']['q50'])} / {idn(p56['u']['q100'])}; L-7 {idn(p7['u']['tekan'])} / "
                f"{idn(p7['u']['q50'])} / {idn(p7['u']['q100'])}. Ruang MRI/CT LT1 +12,85 hanya {idn(LT1 - Q100, 2)} m "
                "di atas Q100.", "Elevasi dan Air", "Perlu 5.5"],
        ["T-8", f"Beban atap podium utara: Daftar Alat {idn(a['jumlah'])} kN ({idn(a['q'], 2)} kPa pada 1.152 m²), "
                f"bukan {idn(a['ring_jumlah'])} kN ({idn(a['q_ring'], 1)} kPa) di Ringkasan Atap.",
         "Konsistensi", "Sudah ditangani (Tahap 4 M-1)"],
        ["T-9", "Pernyataan lembar Lift 'dasar pit di atas muka air, tidak perlu kedap' ditolak.",
         "Pernyataan Ditolak", "Ditolak"],
        ["T-10", "Acuan yang belum ada di acuan/: getaran lantai (AISC DG11/CCIP-016/SCI P354), GFRP (ACI 440), "
                 "A955, pedoman MRI pabrikan, Permen PUPR 28/2015.", "Acuan", "Belum ada"],
    ]


# ------------------------------------------------------------------ Excel
def buat_excel(keluar=BERKAS):
    from format_dokumen import AI, Lembar, set_font_bawaan

    r = ringkas()
    j, ak, a = r["jarak"], r["akibat"], r["atap"]
    m = r["mri"]
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    ket_ai = LABEL + " " + LABEL_AI

    # ---- 1 Ringkasan
    lb = Lembar(wb.create_sheet("Ringkasan"), 1, "Ringkasan telaah data Tahap 5", [6, 100, 24, 28])
    lb.catatan(f"STATUS: {STATUS}. " + ket_ai)
    lb.kosong()
    lb.bagian("A", "Daftar lembar")
    lb.tabel(["No", "Isi lembar", "Lembar", "Status"], [
        [1, "Temuan utama, satu baris per temuan", "Ringkasan", STATUS],
        [2, "Letak tiap alat, shaft, lift, dan lubang di atas as grid", "Plot Koordinat", STATUS],
        [3, "Jarak isocenter MRI ke jalur ambulans, lift, shaft, as grid; akibat", "Syarat MRI", STATUS],
        [4, "Dasar pit lift terhadap muka air, Q50, Q100; tekanan angkat", "Elevasi dan Air", STATUS],
        [5, "Cek satuan kg ke kN, rentang, dan elevasi lama", "Konsistensi dan Satuan", STATUS],
        [6, "Tiga pernyataan data owner yang ditolak", "Pernyataan Ditolak", STATUS],
        [7, "Acuan yang ada dan belum ada di acuan/", "Acuan", STATUS],
        [8, "Permintaan data ke owner dan pemasok (belum dikirim)", "Permintaan Data", STATUS],
    ], rata=list("clll"), beku=False)
    lb.kosong()
    lb.bagian("B", "Temuan utama")
    lb.tabel(["Kode", "Temuan", "Lembar", "Status"], [[t[0], t[1], t[2], t[3]] for t in temuan(r)],
             rata=list("clll"), fill_kolom={1: AI, 3: AI})

    # ---- 2 Plot Koordinat
    lb = Lembar(wb.create_sheet("Plot Koordinat"), 2, "Plot koordinat data owner di atas grid",
                [5, 9, 40, 20, 11, 11, 22, 22, 22, 22, 52])
    lb.catatan(ket_ai + " Grid: as 1-10 pada x = 12 + 8(i-1), as A-G pada y = 27 + 8j [Data Beban MEP Rinci, Umum]. "
               "Tiap tepi kotak dicari as terdekatnya: '(0,0 m)' berarti tepat di as; selain itu tepi berada di tengah "
               "bentang. Tepi dianggap di as bila jarak ≤ 0,05 m.")
    baris = []
    for n, it in enumerate(r["item"], 1):
        cel = []
        for sb, (p, q), grid, nama in (("x", it["x"], GRID_X, NAMA_X), ("y", it["y"], GRID_Y, NAMA_Y)):
            for v, nm, d in analisis_tepi(p, q, grid, nama):
                cel.append(f"{sb} {idn(v)} → as {'/'.join(nm)} ({idn(d)} m)")
        baris.append([n, it["kode"], it["uraian"], it["lantai"], f"{idn(it['x'][0])}-{idn(it['x'][1])}",
                      f"{idn(it['y'][0])}-{idn(it['y'][1])}", *cel, status_plot(*it["x"], *it["y"])])
    lb.tabel(["No", "Kode", "Uraian", "Lantai / bidang", "x (m)", "y (m)", "Tepi x barat", "Tepi x timur",
              "Tepi y selatan", "Tepi y utara", "Status"], baris, rata=list("cclccccccll"), fill_kolom={10: AI})

    # ---- 3 Syarat MRI
    lb = Lembar(wb.create_sheet("Syarat MRI"), 3, "Syarat penempatan MRI terhadap tapak dan struktur",
                [6, 46, 14, 20, 26, 60, 9, 9, 9, 9])
    lb.catatan(ket_ai + " Isocenter dan syarat dari lembar Syarat MRI [Data owner / pabrikan], bukan SNI. Jarak = jarak "
               "terdekat titik ke kotak (rumus Excel). Jalur ambulans x 88-94 sumbu 91 [Asumsi lebar, tahap3_basement.py]; "
               "kotak jalur y 44-76 mengikuti zona P4 [Asumsi], isocenter y 57 berada dalam rentang itu.")
    ka = lambda k: m["item"][k]["x"] + m["item"][k]["y"]  # noqa: E731
    d12, d8 = f"≥ {idn(m['d_logam'])} m", f"≥ {idn(m['d_lift'])} m"

    def st(d, syarat):
        return "OK" if d >= syarat else f"TIDAK (kurang {idn(syarat - d)} m)"

    unsur = [
        ("Sumbu jalur ambulans x 91", (91.0, 91.0) + JALUR_Y, d12, st(j["sumbu_jalur"], m["d_logam"]),
         "Benda logam bergerak besar ≥ 12,0 m [pabrikan]."),
        ("Tepi barat lajur x 88", (88.0, 88.0) + JALUR_Y, d12, st(j["tepi_barat_lajur"], m["d_logam"]),
         "Tepi lajur yang paling dekat ke MRI; kendaraan dapat berada di tepi ini."),
        ("Tepi zona parkir P4 x 94", (94.0, 94.0, P4[2], P4[3]), d12, st(j["tepi_p4"], m["d_logam"]),
         "Tepi barat zona parkir P4 (motor dan ambulans) [3.5]."),
        ("Shaft L-1..4 (titik terdekat)", ka("L-1..4"), d8, st(j["L-1..4"], m["d_lift"]),
         "Lift dan bobot imbang ≥ 8,0 m."),
        ("Shaft L-5..6 (titik terdekat)", ka("L-5..6"), d8, st(j["L-5..6"], m["d_lift"]), "Idem."),
        ("Shaft L-7 (titik terdekat)", ka("L-7"), d8, st(j["L-7"], m["d_lift"]), "Idem; > 40 m."),
        ("SH-6 pipa ventilasi helium Ø 300 mm", ka("SH-6"), "-", "Catatan",
         "Lubang pelat berada di dalam ruang MRI (x 77-84, y 54-60) dan memutus tulangan pelat; "
         "dicek di 5.2/5.3."),
        ("Kompresor kriogenik R-06", ka("R-06"), "-", "Catatan",
         "Getaran 50 Hz; syarat getaran lantai ≤ 0,5 × 10⁻³ g pada 0-50 Hz. Titik tumpu 4, peredam dicek di 5.3."),
        ("Pompa M-04 di atap podium +21,85", ka("M-04"), "-", "Catatan",
         "TEPAT di atas ruang MRI (x 78,5-82,5 beririsan x 77-84; y 58-66 beririsan y 54-60); frekuensi 24,2 Hz; "
         "dukungan pelat atap dan balok dicek di 5.2."),
    ]
    r0, a0, a1 = lb.tabel(["No", "Unsur", "Jarak ke isocenter (m)", "Syarat", "Status", "Keterangan", "x0", "x1", "y0",
                            "y1"],
                           [[i + 1, u, None, sy, s, ke, *k] for i, (u, k, sy, s, ke) in enumerate(unsur)],
                           rata=list("clccllcccc"), fmt=[None, None, "0.00", None, None, None, "0.0", "0.0", "0.0",
                                                                "0.0"], fill_kolom={4: AI})
    ws = lb.ws
    lb.catatan("x0, x1, y0, y1: kotak unsur dalam meter (koordinat grid lokal).")
    lb.kosong()
    lb.bagian("B", "As grid terdekat ke isocenter dan radius tulangan non-magnetik")
    pilih = r["as_iso"][:3]
    b_r0, b_a0, b_a1 = lb.tabel(["No", "As", "Jarak ke isocenter (m)", "Radius 1,0 m", "Status", "Keterangan", "Posisi"],
                                [[i + 1, n, None, None, "OK" if d > RADIUS_NONMAGNET else "TIDAK",
                                  "Tidak ada balok atau sloof di dalam radius 1,0 m dari isocenter." if i == 0 else "", g]
                                 for i, (n, g, d) in enumerate(pilih)],
                                rata=list("clcccl") + ["c"], fmt=[None, None, "0.00", None, None, None, "0.0"],
                                fill_kolom={4: AI}, beku=False)
    lb.catatan("Tulangan baja di dalam radius 1,0 m dari isocenter dilarang (atau baja tahan karat) [Syarat MRI butir 7]. "
               "Karena tidak ada as dalam radius itu, tulangan non-magnetik hanya perlu di pelat panel 9-10/D-E, "
               "kotak x 79,5-81,5 dan y 56-58.")
    lb.kosong()
    lb.bagian("C", "Akibat jarak ke jalur ambulans (dua pilihan)")
    lb.tabel(["No", "Pilihan", "Nilai batas (m)", "Dasar", "Status", "Akibat"], [
        [1, "Geser isocenter ke barat; lajur tetap x 88-94", ak["x_iso_maks"], "x isocenter ≤ 88 - 12", "Perlu keputusan",
         f"Isocenter harus x ≤ {idn(ak['x_iso_maks'])} (geser {idn(ak['geser_barat'])} m ke barat). Itu tepat di as 9: "
         "balok dan sloof as 9 masuk radius 1,0 m (jarak 0,0 m), sehingga tulangan non-magnetik menjadi sepanjang as 9 "
         "dan ruang MRI x 77-84 perlu bergeser."],
        [2, "Geser lajur ke timur; isocenter tetap (80,5; 57,0)", ak["tepi_min"], "tepi barat lajur ≥ 80,5 + 12",
         "Perlu keputusan",
         f"Tepi barat lajur ≥ x {idn(ak['tepi_min'])} (sumbu ≥ {idn(ak['sumbu_min'])}, lajur {idn(ak['lajur'][0])}-"
         f"{idn(ak['lajur'][1])}) memakan {idn(ak['makan_p4'])} m dari {idn(ak['lebar_p4'], 0)} m zona parkir P4 "
         "(x 94-100); parkir dan ambulans dipindah."],
    ], rata=list("clcclll"), fmt=[None, None, "0.0", None, None, None], fill_kolom={4: AI, 5: AI}, beku=False)
    lb.kosong()
    lb.bagian("D", "Konstanta")
    c_r0, c_a0, c_a1 = lb.tabel(["No", "Besaran", "Nilai", "Satuan", "Sumber", "Keterangan"], [
        [1, "x isocenter", m["iso"][0], "m", "Syarat MRI butir 1", ""],
        [2, "y isocenter", m["iso"][1], "m", "Syarat MRI butir 1", ""],
        [3, "Radius non-magnetik", RADIUS_NONMAGNET, "m", "Syarat MRI butir 7", ""],
    ], rata=list("clccll"), fmt=[None, None, "0.0", None, None, None], beku=False)
    px, py, rad = (f"${lb.kol(2)}${c_a0 + i}" for i in range(3))
    for i in range(a0, a1 + 1):
        x0c, x1c, y0c, y1c = (f"{lb.kol(k)}{i}" for k in (6, 7, 8, 9))
        ws[f"{lb.kol(2)}{i}"] = f"=SQRT(MAX({x0c}-{px},0,{px}-{x1c})^2+MAX({y0c}-{py},0,{py}-{y1c})^2)"
    for i in range(b_a0, b_a1 + 1):
        titik = px if ws[f"{lb.kol(1)}{i}"].value.split()[1].isdigit() else py
        ws[f"{lb.kol(2)}{i}"] = f"=ABS({titik}-{lb.kol(6)}{i})"
        ws[f"{lb.kol(3)}{i}"] = f'=IF({lb.kol(2)}{i}>{rad},"di luar radius","di dalam radius")'

    # ---- 4 Elevasi dan Air
    lb = Lembar(wb.create_sheet("Elevasi dan Air"), 4, "Elevasi pit lift dan tekanan angkat", [
        13, 9, 9, 10, 12, 12, 12, 12, 12, 12, 10, 10, 10, 11, 11, 11])
    lb.catatan(ket_ai + " Dasar dan kedalaman pit dari lembar Lift. Tinggi air h = tinggi tekan - sisi bawah pelat dasar "
               "(dasar - 0,40 m [Asumsi, dicek 5.5]); u = γw·h dengan γw = 9,81 kN/m³. Selisih negatif = dasar pit "
               "di bawah muka tersebut. Kolom hitung adalah rumus Excel; konstanta di bawah tabel.")
    kep = ["Pit", "Dasar (+m)", "Dalam (m)", "Dasar + dalam", "Cek vs LT1 +12,85", "Dasar - tekan +11,20", "Dasar - Q50",
           "Dasar - Q100", "Dasar - halaman", "Sisi bawah pelat (+m)", "h tekan (m)", "h Q50 (m)", "h Q100 (m)",
           "u tekan (kPa)", "u Q50 (kPa)", "u Q100 (kPa)"]
    p = r["pit"]
    e0, e_a0, e_a1 = lb.tabel(kep, [[x["kode"], x["dasar"], x["dalam"]] + [None] * 13 for x in p],
                               rata=["c"] * 16, fmt=[None, "0.00", "0.00", "0.00", None] + ["0.00"] * 5 + ["0.00"] * 3 +
                               ["0.0"] * 3, fill_kolom={k: AI for k in range(3, 16)}, beku_kolom=1)
    ws = lb.ws
    lb.kosong()
    lb.bagian("B", "Sisa LT1 +12,85 di atas muka (ruang MRI/CT)")
    f0, f_a0, f_a1 = lb.tabel(["Muka", "Elevasi (+m)", "Sisa (m)"], [
        ["Q100", Q100, None], ["Q50", Q50, None], ["Tinggi tekan desain", TEKAN_DESAIN, None],
        ["Halaman", HALAMAN, None]], rata=["c"] * 16, fmt=[None, "0.00", "0.00"], beku=False)
    for i in range(f_a0, f_a1 + 1):
        ws[f"{lb.kol(2)}{i}"] = f"={LT1}-{lb.kol(1)}{i}"
    lb.kosong()
    lb.bagian("C", "Konstanta dan sumber")
    k0, k_a0, k_a1 = lb.tabel(["Besaran", "Nilai", "Satuan"], [
        ["Tinggi tekan akuifer desain", TEKAN_DESAIN, "+m"], ["Q50", Q50, "+m"], ["Q100", Q100, "+m"],
        ["Halaman", HALAMAN, "+m"], ["Peil LT1", LT1, "+m"], ["Tebal pelat dasar pit", TEBAL_DASAR_PIT, "m"],
        ["γw", GAMMA_W, "kN/m³"]], rata=["c"] * 16, fmt=[None, "0.00", None], beku=False)
    lb.catatan("Sumber: tinggi tekan desain +11,20 [2.4 / Tahap 2]; Q50 +11,85, Q100 +12,31, halaman +12,05, peil LT1 "
               "+12,85 [3.3 Peil dan Urugan]; tebal pelat dasar pit 0,40 m [Asumsi, dicek 5.5]; γw 9,81 kN/m³.")
    kc = {nm: f"${lb.kol(1)}${k_a0 + i}" for i, nm in enumerate(("tekan", "q50", "q100", "halaman", "lt1", "tebal", "gw"))}
    for i in range(e_a0, e_a1 + 1):
        c = lambda k: f"{lb.kol(k)}{i}"  # noqa: E731
        ws[c(3)] = f"={c(1)}+{c(2)}"
        ws[c(4)] = f'=IF(ABS({c(3)}-{kc["lt1"]})<0.001,"OK","beda")'
        ws[c(5)] = f"={c(1)}-{kc['tekan']}"
        ws[c(6)] = f"={c(1)}-{kc['q50']}"
        ws[c(7)] = f"={c(1)}-{kc['q100']}"
        ws[c(8)] = f"={c(1)}-{kc['halaman']}"
        ws[c(9)] = f"={c(1)}-{kc['tebal']}"
        for k, nm in ((10, "tekan"), (11, "q50"), (12, "q100")):
            ws[c(k)] = f"=MAX(0,{kc[nm]}-{c(9)})"
            ws[c(k + 3)] = f"={kc['gw']}*{c(k)}"

    # ---- 5 Konsistensi dan Satuan
    lb = Lembar(wb.create_sheet("Konsistensi dan Satuan"), 5, "Konsistensi satuan dan rentang", [
        5, 52, 14, 14, 9, 30, 62])
    lb.catatan(ket_ai + " 'Dalam data' diambil dari lembar sumber; 'dihitung ulang' adalah rumus Excel. Tahap 4: M-1 dan M-8 "
               "ada di '4.0 Telaah Data Tahap 4.xlsx' (lembar Telaah MEP).")
    kons = konsistensi()
    k0, k_a0, k_a1 = lb.tabel(["No", "Butir", "Dalam data", "Dihitung ulang", "Satuan", "Status", "Keterangan"],
                               [[i + 1, b, v, None, s, st_, ket] for i, (b, v, h, s, f, st_, ket) in enumerate(kons)],
                               rata=list("clccclll"), fmt=[None, None, "#,##0.00", "#,##0.00", None, None, None],
                               fill_kolom={5: AI, 6: AI})
    for i, (b, v, h, s, f, st_, ket) in zip(range(k_a0, k_a1 + 1), kons):
        lb.ws[f"{lb.kol(3)}{i}"] = f

    # ---- 6 Pernyataan Ditolak
    lb = Lembar(wb.create_sheet("Pernyataan Ditolak"), 6, "Pernyataan data owner yang ditolak", [5, 34, 50, 62, 30])
    lb.catatan(ket_ai)
    p14, p7 = r["pit"][0], r["pit"][2]
    lb.tabel(["No", "Sumber", "Pernyataan", "Alasan penolakan dan angka", "Ditangani di"], [
        [1, "Data Beban MEP Rinci, lembar Lift",
         "'Dasar pit +11,25 sampai +11,45 berada di atas muka air tanah (±1,0 m di bawah muka tanah asli), sehingga pit "
         "tidak memerlukan lapisan kedap air.'",
         f"Ditolak. Sisi bawah pelat pit L-1..4 +{idn(p14['bawah'], 2)} berada di bawah tinggi tekan desain +11,20, di "
         f"bawah Q50 +11,85 dan Q100 +12,31. Tekanan angkat u = {idn(p14['u']['tekan'])} / {idn(p14['u']['q50'])} / "
         f"{idn(p14['u']['q100'])} kPa (L-7 sampai {idn(p7['u']['q100'])} kPa). Pit harus kedap air dan dicek angkat.",
         "5.5 Desain Pit Lift (Tahap 4: M-3)"],
        [2, "Data Beban MEP Rinci, lembar Ringkasan Atap",
         "Chiller 4 × 3.900 kg = 153,2 kN dan tangki 158 t = 1.550 kN; jumlah 1.748,1 kN (±1,5 kPa).",
         f"Ditolak. Berat itu dari Data MEP Awal. Daftar Alat memberi chiller {idn(r['atap']['chiller'])} kN dan tangki "
         f"{idn(r['atap']['tangki'], 0)} kN; jumlah {idn(r['atap']['jumlah'])} kN ({idn(r['atap']['q'], 2)} kPa). "
         "Dipakai Daftar Alat.", "5.1 dan Tahap 4 (M-1, M-8)"],
        [3, "Data MEP Awal (5 Maret 2027)", "Elevasi gedung utilitas +11,30.",
         "Ditolak. Digantikan +12,85 (3.3 Peil dan Urugan; lembar Umum dan Gedung Utilitas Data Beban MEP Rinci). "
         "Pada +11,30 lantai berada di bawah Q50 +11,85 dan Q100 +12,31.", "3.3 dan 5.6"],
    ], rata=list("cllll"), fill_kolom={3: AI})

    # ---- 7 Acuan
    lb = Lembar(wb.create_sheet("Acuan"), 7, "Acuan di folder acuan/", [5, 56, 14, 70])
    lb.catatan(LABEL + " Dicek pada folder acuan/privat, pustaka, jurnal, dan publik (nama berkas). "
               + LABEL_AI)
    nama = daftar_acuan()
    hasil = cek_acuan(nama)
    lb.tabel(["No", "Acuan yang dibutuhkan", "Status", "Berkas di acuan/ atau penanganan"], [
        [i + 1, ket, "ada" if b else "belum ada",
         b if b else "Belum ada di acuan/; ditulis [Literatur, belum ada di acuan/], pasal tidak ditebak."]
        for i, (ket, b) in enumerate(hasil)], rata=list("clcl"), fill_kolom={2: AI, 3: AI})

    # ---- 8 Permintaan Data
    lb = Lembar(wb.create_sheet("Permintaan Data"), 8, "Permintaan data (draf, belum dikirim)", [5, 56, 24, 62, 22])
    lb.catatan("DRAF, belum dikirim. " + ket_ai)
    lb.tabel(["No", "Permintaan", "Kepada", "Alasan", "Status"], [
        [1, "Lebar dan sumbu jalur ambulans tetap serta letak drop-off IGD", "Owner / arsitek",
         f"Jarak isocenter ke tepi lajur x 88 hanya {idn(j['tepi_barat_lajur'])} m (syarat ≥ 12,0 m); lebar lajur 6 m "
         "dan sumbu 91 masih [Asumsi].", "Draf, belum dikirim"],
        [2, "Apakah pabrikan MRI mengizinkan pelindung aktif atau pasif tambahan untuk jarak < 12 m", "Pemasok MRI",
         "Bila diizinkan, isocenter atau jalur tidak perlu digeser (pilihan 3 di luar dua akibat T-2).",
         "Draf, belum dikirim"],
        [3, "Jalur masuk magnet: bukaan 2,6 × 2,6 m ke sisi mana (timur, utara, atau lain)", "Pemasok MRI / arsitek",
         "Menentukan bukaan di dinding dan pelat LT1 serta jalur alat berat ke ruang MRI.", "Draf, belum dikirim"],
        [4, "Tanggapan owner atas surat teknis Tahap 4", "Owner", "Butir M-4 sampai M-7 Tahap 4 masih menunggu "
         "keputusan.", "Draf, belum dikirim"],
        [5, "Data owner Tahap 5 bila ada: detail pit lift dari pemasok, sump dan pompa pit", "Pemasok lift / MEP",
         "Dasar pit +11,25 sampai +11,45 dan tebal pelat dasar 0,40 m [Asumsi]; drainase pit (sump, pompa) belum ada.",
         "Draf, belum dikirim"],
    ], rata=list("cllll"), fill_kolom={3: AI})

    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


def cocokkan(berkas=BERKAS):
    """Hitung ulang di Excel (bila terpasang), lalu bandingkan rumus dengan Python. Kembalikan (ok, pesan)."""
    from format_dokumen import hitung_ulang_excel

    ok, err = hitung_ulang_excel(berkas)
    if not ok:
        return False, f"Excel tidak bisa menghitung ulang: {err[:120]}"
    wb = openpyxl.load_workbook(berkas, data_only=True)
    r = ringkas()
    pesan, bad = [], 0
    ws = wb["Konsistensi dan Satuan"]
    kons = konsistensi()
    hdr = next(c.row for c in ws["C"] if c.value == "No")
    for i, (b, v, h, s, f, st_, ket) in enumerate(kons):
        x = ws.cell(hdr + 1 + i, 6).value
        if x is None or abs(x - h) > 0.01:
            bad += 1
            pesan.append(f"konsistensi {i + 1}: Excel {x} vs Python {h}")
    ws = wb["Elevasi dan Air"]
    hdr = next(c.row for c in ws["C"] if c.value == "Pit")
    for i, p in enumerate(r["pit"]):
        for k, kk in ((13, "tekan"), (14, "q50"), (15, "q100")):
            x = ws.cell(hdr + 1 + i, 3 + k).value
            if x is None or abs(x - p["u"][kk]) > 0.01:
                bad += 1
                pesan.append(f"pit {p['kode']} u {kk}: Excel {x} vs Python {p['u'][kk]}")
    ws = wb["Syarat MRI"]
    hdr = next(c.row for c in ws["C"] if c.value == "No")
    j = r["jarak"]
    for i, kk in enumerate(("sumbu_jalur", "tepi_barat_lajur", "tepi_p4", "L-1..4", "L-5..6", "L-7", "SH-6", "R-06",
                            "M-04")):
        x = ws.cell(hdr + 1 + i, 5).value
        if x is None or abs(x - j[kk]) > 0.01:
            bad += 1
            pesan.append(f"jarak {kk}: Excel {x} vs Python {j[kk]}")
    return bad == 0, "; ".join(pesan) or "semua rumus Excel cocok dengan Python"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    r = ringkas()
    print({k: round(v, 2) for k, v in r["jarak"].items()})
    print({k: round(v, 2) if isinstance(v, float) else v for k, v in r["akibat"].items()})
    print([(p["kode"], {k: round(v, 1) for k, v in p["u"].items()}) for p in r["pit"]])
    print(round(r["atap"]["jumlah"], 1), round(r["atap"]["q"], 2))
    print(buat_excel())
    print(cocokkan())
