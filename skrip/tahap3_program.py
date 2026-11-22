"""Langkah 3.4: program ruang versi konsultan (150 TT), zonasi vertikal per lantai, dan massa bangunan.

Dasar: Program Ruang owner versi 2 (00 Kerangka Acuan), telaah Tahap 0 (Matriks Tanggapan TOR lembar 2), Data MEP Awal
(ruang utilitas), keputusan rapat laporan pendahuluan (utilitas di atas banjir, 150 TT), langkah 3.2 (amplop, KDB,
KLB) dan 3.3 (peil +12,85). Aturan ruang yang ada di acuan: PMK 40/2022 Lampiran (dicabut Permenkes 6/2026,
pengganti belum terbit; dipakai dengan catatan) hal. 9 butir F (zonasi merah-kuning-hijau), hal. 10 butir G.3.b
(tinggi plafon ruang 2,80 m, koridor 2,40 m, ruang operasi 3,00 m), hal. 14 butir G.3.g.2 (koridor 2 TT berpapasan
2,40 m); Permenkes 6/2026 Pasal 10 ayat (1) (RS PMDN minimal 50 TT). Luas standar per ruang tidak ada di acuan:
luas memakai program owner, tambahan berlabel [Asumsi].
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 19 Nov 2026.
"""
from functools import lru_cache
from pathlib import Path

import openpyxl

import tahap3_tapak as tp

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "03 Desain Konsep"
BERKAS = KELUAR / "3.4 Program Ruang Konsultan.xlsx"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = "DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026."
FAKTOR_BRUTO = 1.45  # [Asumsi: dinding, koridor 2,40 m, tangga, lif, shaft; Tahap 0 memakai rentang 1,4-1,6]
TARGET_TT = 150

# Lantai tujuan per kelompok (zonasi vertikal). PMK 40/2022 hal. 9 butir F: zona merah (IGD, PIE), kuning (pelayanan
# pasien), hijau (penunjang, manajemen). Owner butir 6: bedah sentral di lantai 2 di atas IGD, ICU dekat bedah.
LANTAI = {
    "Rawat Jalan": "LT1", "Gawat Darurat": "LT1", "Penunjang Medik: radiologi": "LT1",
    "Penunjang Medik: farmasi": "LT1", "Penunjang Medik: jenazah": "LT1",
    "Bedah Sentral": "LT2", "Intensif": "LT2", "Kebidanan": "LT2",
    "Penunjang Medik: laboratorium": "LT3", "Penunjang Medik: hemodialisis": "LT3",
    "Penunjang Medik: rehabilitasi": "LT3", "Administrasi": "LT3", "Penunjang Umum: gizi dan laundry": "LT3",
    "Penunjang Umum: lain": "LT1", "Rawat Inap": "LT4-LT6", "Utilitas (gedung utilitas)": "GU",
}


def _sub(kelompok, ruang):
    r = ruang.lower()
    if kelompok == "Penunjang Medik":
        if "radiologi" in r:
            return "Penunjang Medik: radiologi"
        if "laboratorium" in r or "bank darah" in r:
            return "Penunjang Medik: laboratorium"
        if "hemodialisis" in r:
            return "Penunjang Medik: hemodialisis"
        if "rehabilitasi" in r:
            return "Penunjang Medik: rehabilitasi"
        if "farmasi" in r:
            return "Penunjang Medik: farmasi"
        return "Penunjang Medik: jenazah"
    if kelompok == "Penunjang Umum":
        return "Penunjang Umum: gizi dan laundry" if ("gizi" in r or "laundry" in r) else "Penunjang Umum: lain"
    if kelompok.startswith("Utilitas"):
        return "Utilitas (gedung utilitas)"
    return kelompok


@lru_cache(maxsize=1)
def program_owner():
    ws = openpyxl.load_workbook(AKAR / "00 Kerangka Acuan" / "Program Ruang.xlsx", data_only=True)["Program Ruang"]
    hasil = []
    for r in ws.iter_rows(values_only=True):
        v = list(r)
        while v and v[0] is None:
            v.pop(0)
        if v and isinstance(v[0], int) and len(v) >= 8:
            no, kel, ruang, n, luas, bersih, tt_r, tt = v[:8]
            hasil.append({"no": no, "kelompok": kel, "ruang": ruang, "n": int(n), "luas": float(luas),
                          "tt_per": int(tt_r or 0), "asal": "owner v2"})
    return tuple(hasil)


def program_konsultan():
    """Program owner + perubahan konsultan. Kembalikan daftar baris dengan kolom tambahan 'ubah' (alasan)."""
    hasil = []
    for b in program_owner():
        b = dict(b)
        b["ubah"] = ""
        if b["ruang"].startswith("Kamar 4 TT"):
            b["n"] += 3
            b["ubah"] = "+3 kamar agar total 150 TT (telaah Tahap 0 lembar 2)"
        if b["kelompok"].startswith("Utilitas"):
            b["kelompok"] = "Utilitas (gedung utilitas)"
            b["ubah"] = "pindah dari basement ke gedung utilitas lantai +12,85 (keputusan rapat no. 2, langkah 3.3)"
        if b["ruang"].startswith("Ruang genset"):
            b["luas"], b["ubah"] = 220.0, b["ubah"] + "; luas dari Data MEP Awal lembar 2 (220 m²)"
        if b["ruang"].startswith("Ruang trafo"):
            b["luas"], b["ubah"] = 150.0, b["ubah"] + "; trafo 60 + panel TM/TR dan UPS 90 m² (Data MEP)"
        if b["ruang"].startswith("Ruang pompa"):
            b["luas"], b["ubah"] = 90.0, b["ubah"] + "; ruang pompa 90 m² (Data MEP); tangki air tanam terpisah"
        if b["ruang"].startswith("IPAL"):
            b["luas"], b["ubah"] = 110.0, b["ubah"] + "; IPAL tanam 110 m² (Data MEP), di halaman"
        if b["ruang"].startswith("Toilet umum"):
            b["n"], b["ubah"] = 7, "1 per lantai LT1-LT6 + gedung utilitas (telaah Tahap 0: 8 tidak cocok)"
        if b["ruang"].startswith("Sentral gas medik"):
            b["kelompok"], b["luas"] = "Utilitas (gedung utilitas)", 60.0
            b["ubah"] = "ke gedung utilitas, akses truk tabung; 60 m² (Data MEP)"
        hasil.append(b)
    n = len(hasil)
    tambah = [
        ("Gawat Darurat", "Ruang tunggu keluarga dan pos ambulans air (jalur dari sungai)", 1, 30.0,
         "TOR 3, surat owner butir 6 [Asumsi luas]"),
        ("Intensif", "Ruang tunggu keluarga bedah dan ICU", 1, 60.0, "telaah Tahap 0 [Asumsi luas]"),
        ("Kebidanan", "Ruang tindakan kebidanan dan perinatologi", 1, 60.0,
         "klasifikasi madya kebidanan (TOR 3) [Asumsi luas; kriteria klasifikasi belum ada di acuan]"),
        ("Rawat Inap", "Ruang AHU per lantai (LT1-LT6)", 6, 70.0, "Data MEP Awal lembar 2 no. 6"),
        ("Rawat Inap", "Shaft MEP vertikal per lantai (LT1-LT6)", 6, 32.0, "Data MEP Awal lembar 2 no. 7"),
        ("Utilitas (gedung utilitas)", "Bengkel dan gudang utilitas", 1, 40.0, "[Asumsi]"),
    ]
    for i, (kel, ruang, jml, luas, alasan) in enumerate(tambah, start=1):
        hasil.append({"no": n + i, "kelompok": kel, "ruang": ruang, "n": jml, "luas": luas, "tt_per": 0,
                      "asal": "tambahan konsultan", "ubah": alasan})
    for b in hasil:
        r = b["ruang"].lower()
        if any(k in r for k in ("ipsrs", "gudang umum", "gudang alat kesehatan", "tps limbah")):
            b["kelompok"] = "Utilitas (gedung utilitas)"
            b["ubah"] = (b["ubah"] + "; " if b["ubah"] else "") + "ke gedung utilitas (servis, akses truk) agar LT1 muat"
    for b in hasil:
        b["bersih"] = b["n"] * b["luas"]
        b["tt"] = b["n"] * b["tt_per"]
        b["sub"] = _sub(b["kelompok"], b["ruang"])
        b["lantai"] = LANTAI[b["sub"]]
        if b["ruang"].startswith(("Ruang AHU", "Shaft MEP")):
            b["lantai"] = "LT1-LT6"
        if b["ruang"].startswith("IPAL"):
            b["lantai"] = "HALAMAN"  # IPAL tanam di halaman (Data MEP), bukan ruang di gedung
        if b["sub"] in ("Penunjang Medik: laboratorium", "Penunjang Medik: hemodialisis",
                        "Penunjang Medik: rehabilitasi"):
            b["lantai"] = "LT2"  # penyeimbang luas podium; lab dekat bedah sentral dan ICU
    return hasil


def rekap_lantai():
    """Luas bersih dan bruto per lantai tujuan; LT4-LT6 dan LT1-LT6 dibagi rata."""
    per = {k: 0.0 for k in ("LT1", "LT2", "LT3", "LT4", "LT5", "LT6", "GU")}
    for b in program_konsultan():
        if b["lantai"] == "LT4-LT6":
            for k in ("LT4", "LT5", "LT6"):
                per[k] += b["bersih"] / 3
        elif b["lantai"] == "HALAMAN":
            continue
        elif b["lantai"] == "LT1-LT6":
            for k in ("LT1", "LT2", "LT3", "LT4", "LT5", "LT6"):
                per[k] += b["bersih"] / 6
        else:
            per[b["lantai"]] += b["bersih"]
    return {k: {"bersih": v, "bruto": v * FAKTOR_BRUTO} for k, v in per.items()}


# ------------------------------------------------------------------ massa bangunan (modul 8 m, m lokal)
MODUL = 8.0  # [Asumsi: modul 8,0 m cocok untuk 3 mobil per bentang dan kamar 4 TT; grid final di 3.6]
MASSA = {
    "PODIUM": {"x": (12.0, 84.0), "y": (27.0, 75.0), "lantai": ["LT1", "LT2", "LT3"]},
    "MENARA": {"x": (20.0, 84.0), "y": (27.0, 51.0), "lantai": ["LT4", "LT5", "LT6"]},  # grid 8 m (3.6)
    "GEDUNG UTILITAS": {"x": (100.0, 134.0), "y": (44.0, 76.0), "lantai": ["LT1", "LT2", "LT3", "LT4"]},  # + parkir (3.5)
}


def poligon(nama):
    from shapely.geometry import box

    m = MASSA[nama]
    return box(m["x"][0], m["y"][0], m["x"][1], m["y"][1])


def cek_massa():
    """Massa di dalam amplop (3.2), di luar zona labil dan sempadan; tapak total vs KDB; luas lantai vs KLB."""
    tapak = tp.ringkasan()
    hasil = []
    for nama in MASSA:
        g = poligon(nama)
        lantai = len(MASSA[nama]["lantai"])
        amp = tp.amplop(6 if nama != "GEDUNG UTILITAS" else 4)
        hasil.append({"massa": nama, "luas": g.area, "lantai": lantai, "dalam_amplop": amp.buffer(1e-6).contains(g),
                      "jarak_labil": g.distance(tp.zona_labil()), "jarak_sempadan": g.distance(tp.ruang_sempadan())})
    tapak_total = poligon("PODIUM").area + poligon("GEDUNG UTILITAS").area
    lantai_total = sum(poligon(n).area * len(MASSA[n]["lantai"]) for n in MASSA)
    return {"massa": hasil, "tapak": tapak_total, "kdb_maks": tapak["kdb_maks"], "luas_lantai": lantai_total,
            "klb_maks": tapak["klb_maks"]}


def ringkasan():
    p = program_konsultan()
    rk = rekap_lantai()
    tapak = tp.ringkasan()
    bruto_gedung = sum(v["bruto"] for k, v in rk.items() if k != "GU")
    return {"tt": sum(b["tt"] for b in p), "bersih": sum(b["bersih"] for b in p),
            "bruto_gedung": bruto_gedung, "bruto_gu": rk["GU"]["bruto"],
            "bruto_total": bruto_gedung + rk["GU"]["bruto"], "klb_maks": tapak["klb_maks"],
            "kdb_maks": tapak["kdb_maks"], "per_tt": (bruto_gedung + rk["GU"]["bruto"]) / 150,
            "lantai": rk}



# ------------------------------------------------------------------ Excel
def buat_excel(keluar=BERKAS):
    from format_dokumen import AI, Lembar, set_font_bawaan

    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    p = program_konsultan()
    cm = cek_massa()

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk program ruang dan massa (langkah 3.4)", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        "Dasar: Program Ruang owner versi 2 dan telaah Tahap 0 (Matriks Tanggapan TOR lembar 2), Data MEP Awal lembar 2, "
        "keputusan rapat laporan pendahuluan no. 2 dan 4, langkah 3.2 (amplop, KDB, KLB) dan 3.3 (peil +12,85).",
        "Aturan ruang di acuan: PMK 40/2022 Lampiran (dicabut Permenkes 6/2026, pengganti belum terbit; dipakai dengan "
        "catatan) hal. 9 butir F (zonasi), hal. 10 butir G.3.b (plafon 2,80 m; koridor 2,40 m; ruang operasi 3,00 m), "
        "hal. 12 butir G.3.e.3.c (jarak pintu darurat maks 25 m), hal. 14 butir G.3.g.2 (koridor 2 TT berpapasan 2,40 m); "
        "Permenkes 6/2026 Pasal 10 ayat (1) (RS PMDN minimal 50 TT).",
        "Luas standar per ruang tidak ada di acuan/: luas memakai program owner; tambahan konsultan berlabel [Asumsi]. "
        f"Faktor bruto {FAKTOR_BRUTO} [Asumsi].",
        "Lembar Program: luas bersih dan TT dihitung rumus Excel (jumlah × luas). Lembar Rekap Lantai: bruto = bersih × "
        "faktor bruto. Lembar Massa: cek tapak dan luas lantai terhadap PKKPR.",
        "Gambar: GK-03 '3.4 Gambar Rencana Tapak dan Massa.pdf', GK-04 '3.4 Gambar Zonasi Lantai.pdf'; model massa "
        "BIMCraft 'model/RSTB-ARS-T3-Massa.bimc' dan IFC.",
    ])], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Program"), 2, "Program ruang versi konsultan (150 TT)",
                [6, 18, 40, 8, 10, 12, 8, 8, 12, 46])
    lb.catatan(LABEL + " Kolom hijau rumus Excel. Asal: 'owner v2' atau 'tambahan konsultan'.")
    rows = [[b["no"], b["kelompok"], b["ruang"], b["n"], b["luas"], None, b["tt_per"], None, b["lantai"],
             (b["asal"] + (": " + b["ubah"] if b["ubah"] else ""))] for b in p]
    r0, r1, r2 = lb.tabel(["No", "Kelompok", "Ruang", "Jumlah", "Luas satuan (m²)", "Luas bersih (m²)", "TT per ruang",
                           "Jumlah TT", "Lantai", "Asal dan perubahan"], rows, rata=list("cllcccccc") + ["l"],
                          fmt=[None, None, None, "0", "#,##0.0", "#,##0.0", "0", "0", None, None],
                          fill_kolom={5: AI, 7: AI})
    ws = lb.ws
    for r in range(r1, r2 + 1):
        ws[f"H{r}"] = f"=F{r}*G{r}"
        ws[f"J{r}"] = f"=F{r}*I{r}"
    lb.kosong()
    lb.tabel(["", "", "Jumlah", "", "", None, "", None, "", ""], [], beku=False)
    rj = lb.baris - 1
    ws[f"H{rj}"] = f"=SUM(H{r1}:H{r2})"
    ws[f"J{rj}"] = f"=SUM(J{r1}:J{r2})"
    ws[f"H{rj}"].number_format = "#,##0.0"

    lb = Lembar(wb.create_sheet("Rekap Lantai"), 3, "Luas per lantai (bersih dan bruto)", [10, 16, 16, 18, 40])
    lb.catatan(LABEL + f" Bruto = bersih × {FAKTOR_BRUTO}. LT4-LT6 dan ruang AHU/shaft dibagi rata. GU = gedung utilitas.")
    rk = rekap_lantai()
    # koreksi 7.2 (temuan T-109c 7.1): LT2 tanpa void lobi x 36-62 y 51-75 (KOSONG zonasi 3.4) = 2.832 m²;
    # LT3 tanpa x 36-84 y 51-75 (tidak dibangun, V1 Tahap 4, sama dengan model STR/ARS) = 2.304 m²
    massa = {"LT1": pr_luas("PODIUM"), "LT2": pr_luas("PODIUM") - 26 * 24, "LT3": pr_luas("PODIUM") - 48 * 24,
             "LT4": pr_luas("MENARA"), "LT5": pr_luas("MENARA"), "LT6": pr_luas("MENARA"),
             "GU": pr_luas("GEDUNG UTILITAS")}
    a0, a1, a2 = lb.tabel(["Lantai", "Bersih (m²)", "Bruto (m²)", "Luas massa (m²)", "Keterangan"], [
        [k, round(v["bersih"], 1), None, massa[k],
         "drop-off IGD beratap di luar massa" if k == "LT1" else ("LT1 penuh, sisa di LT2; parkir LT2-LT4 (3.5)" if k == "GU" else "")]
        for k, v in rk.items()], rata=list("ccccl"), fmt=[None, "#,##0.0", "#,##0.0", "#,##0.0", None],
        fill_kolom={2: AI})
    w3 = lb.ws
    for r in range(a1, a2 + 1):
        w3[f"E{r}"] = f"=D{r}*{FAKTOR_BRUTO}"

    lb = Lembar(wb.create_sheet("Massa"), 4, "Massa bangunan dan batas PKKPR", [6, 44, 16, 16, 36])
    lb.catatan(LABEL + f" Modul {MODUL:.0f} m [Asumsi]; grid final di langkah 3.6.")
    lb.tabel(["No", "Butir", "Nilai", "Batas", "Keterangan"], [
        [1, "Podium LT1-LT3 (72 × 48 m)", pr_luas("PODIUM"), None, "x 12-84, y 27-75"],
        [2, "Menara LT4-LT6 (64 × 24 m)", pr_luas("MENARA"), None, "x 20-84, y 27-51, di grid 8 m (3.6)"],
        [3, "Gedung utilitas + parkir 4 lantai (34 × 32 m)", pr_luas("GEDUNG UTILITAS"), None, "x 100-134, y 44-76 (opsi C, 3.5)"],
        [4, "Tapak bangunan (m²)", cm["tapak"], cm["kdb_maks"], "KDB 50 % (langkah 3.2)"],
        [5, "Luas lantai seluruh massa (m²)", cm["luas_lantai"], cm["klb_maks"], "KLB 2,4 (langkah 3.2)"],
        [6, "Tinggi ATAP dari muka tanah rata-rata (m)", 38.65 - 9.6, 40.0, "PKKPR: 40 m termasuk bangunan atap; "
         "muka tanah rata-rata ±9,6 (TOR Lampiran C)"],
        [7, "Jarak maks antarpusat tangga darurat (m)", 24.0, 25.0, "PMK 40/2022 hal. 12 butir G.3.e.3.c"],
        [8, "Jumlah TT", sum(b["tt"] for b in p), 150, "TOR 2 dan 3; Permenkes 6/2026 Pasal 10 ayat (1) min 50"],
    ], rata=list("clccl"), fmt=[None, None, "#,##0.0", "#,##0.0", None], fill_kolom={2: AI})
    wb.save(keluar)
    return keluar


def pr_luas(nama):
    return poligon(nama).area

if __name__ == "__main__":
    import json

    r = ringkasan()
    print(json.dumps({k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items() if k != "lantai"}, indent=1))
    for k, v in r["lantai"].items():
        print(k, round(v["bersih"]), round(v["bruto"]))
    print(cek_massa())
