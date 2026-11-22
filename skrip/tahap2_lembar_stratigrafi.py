"""Tahap 2 langkah 2.2: Excel '02 Olah Data Tanah/2.2 Stratigrafi.xlsx' (format wajib).

Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap2_lembar_stratigrafi.py
"""
from pathlib import Path

import numpy as np
import openpyxl

import tahap2_stratigrafi as st
from format_dokumen import AI, Lembar, set_font_bawaan

AKAR = Path(__file__).resolve().parents[1]
BERKAS = AKAR / "02 Olah Data Tanah" / "2.2 Stratigrafi.xlsx"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = ("DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026. "
            "Kunci jawaban tidak dibuka.")
PASANGAN = [("CPTu-2", "BH-2"), ("CPTu-5", "BH-3")]

URAIAN = {
    "U1": "Lanau kepasiran coklat, sisa akar; di BH-8 urugan berpuing (pecahan beton).",
    "U2": "Lempung kelanauan coklat kemerahan berbintik abu-abu, teguh (kerak kering).",
    "U3": "Gambut coklat tua kehitaman berserat (organik 76-86 %) di atas lempung organik (organik 21-38 %).",
    "U4": "Lempung kelanauan abu-abu kehijauan sampai abu-abu, sangat lunak-lunak, sisipan lanau dan sisa kayu.",
    "U5": "Pasir halus kelanauan abu-abu, jenuh; U5a lepas-agak padat (atas), U5b halus-sedang agak padat (bawah).",
    "U6": "Lempung kelanauan abu-abu kebiruan, kaku-sangat kaku, sisipan pasir halus.",
    "U7": "Pasir halus-sedang abu-abu terang, padat-sangat padat, sementasi lemah.",
    "U8": "Lempung keras (hanya BH-5, 54,8-60,45 m).",
}

PETUNJUK = [
    "Langkah 2.2 menyusun model lapisan (stratigrafi) dari log bor BH-1 s.d. BH-8, CPTu-1 s.d. CPTu-8 (qt dari "
    "langkah 2.1), dan bor tangan HA-1 s.d. HA-10.",
    "Lembar Unit Tanah: definisi unit dan rentang elevasi, tebal, N60, dan qt. Lembar Batas Lapisan: kedalaman "
    "atas tiap unit per titik. Lembar Cek Silang: batas dari CPTu dibandingkan dengan bor di dekatnya.",
    "Gambar pendukung: '2.2 Gambar Geoteknik.pdf' (GT-01 denah, GT-02 s.d. GT-04 penampang A-A', B-B', C-C', "
    "GT-05 peta tebal lapisan organik).",
    "Batas unit di CPTu: U3 = rentang Rf > 5 % di 0,9-5,5 m; U5 = qt rata-rata 0,5 m > 2 MPa; U6 = qt rata-rata "
    "1 m < 2,5 MPa; U7 = qt rata-rata 0,5 m > 10 MPa (di bawah 25 m). Batas U1/U2 tidak dibaca dari CPTu.",
    "Skrip: skrip/tahap2_stratigrafi.py, tahap2_lembar_stratigrafi.py, tahap2_gambar_geoteknik.py.",
]

CATATAN = [
    "Model lapisan seragam di seluruh tapak, kecuali U3: lapisan organik tidak ada di bagian selatan (y < ±42 m) "
    "dan menebal ke utara sampai 3,3-3,7 m (HA-8, HA-10; HA-9 ≥ 2,97 m karena lubang runtuh).",
    "Tebal organik ≥ 3 m di sudut utara (GT-05). Ini menyentuh kriteria kelas situs SF untuk gambut/lempung organik "
    "(SNI 1726:2019 Tabel 5); dibahas di langkah 2.5.",
    "BH-1 dan BH-2 (laporan lama) tidak mencatat lapisan organik; letaknya di selatan (y = 15 dan 40 m), sesuai "
    "dengan CPTu-2, CPTu-6, CPTu-7 yang juga tanpa lapisan organik. Jadi bukan kesalahan log.",
    "Atas pasir U5 pada elevasi +1,6 sampai -0,8 (kedalaman 9,0-10,1 m); paling tinggi di sisi tebing (CPTu-6 +1,55, "
    "CPTu-7 +1,28), jadi pasir lebih dekat ke permukaan di dekat sungai (penting untuk tebing dan rembesan, "
    "langkah 2.3 dan 2.7). Atas U6 pada elevasi -8,1 sampai -9,2 (kedalaman 17,2-19,7 m); atas U7 -23,1 sampai -24,0.",
    "U5 dibagi dua di bor baru (U5a sampai ±13,5-13,7 m, U5b di bawahnya). Bor lama dan CPTu tidak membedakan.",
    "CPTu-1 (dekat S-03): lonjakan qc tipis di 8,3 m tidak dihitung sebagai atas U5 (kriteria rata-rata 0,5 m); "
    "ini kayu terkubur (langkah 2.1, catatan C.6).",
    "U8 lempung keras di 54,8 m hanya diketahui dari BH-5; luas dan tebalnya belum diketahui.",
    "Urugan U1 di BH-8 (dekat gudang timur) setebal 1,34 m dan berpuing, lebih tebal dari titik lain (0,3-0,65 m).",
    "Data bor tangan: batas antarlapisan di log bor tangan tumpang tindih 0,02-0,1 m dan berbeda sedikit dengan "
    "lembar Titik; batas U3 diambil dari lembar Titik, batas U1/U2 dari titik tengah tumpang tindih.",
]


def _stat(nilai, d=1):
    if not nilai:
        return "-"
    a, b = (f"{v:.{d}f}".replace(".", ",") for v in (min(nilai), max(nilai)))
    return a if a == b else f"{a} s.d. {b}"


def buat(keluar=BERKAS):
    titik = st.semua_titik()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk langkah 2.2 stratigrafi", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i, t] for i, t in enumerate(PETUNJUK, start=1)], rata=list("cl"))

    # ---- Unit tanah
    n60 = st.n60_per_unit()
    qt_unit = {}
    for t in titik:
        if t["jenis"] != "CPTu":
            continue
        for lp in t["lapisan"]:
            m = (t["z"] >= lp["atas"]) & (t["z"] < lp["bawah"])
            if t["nama"] == "CPTu-4":
                m &= t["z"] > 4.5
            qt_unit.setdefault(lp["unit"], []).append(float(np.median(t["qt"][m])) if m.any() else None)
    baris = []
    for i, u in enumerate(st.URUT, start=1):
        nama, uscs, _, _ = st.UNIT[u]
        elev, tebal = [], []
        for t in titik:
            ada = [lp for lp in t["lapisan"] if lp["unit"] == u]
            if not ada or (t["jenis"] == "CPTu" and u in ("U1", "U2")):
                continue
            elev.append(t["elev"] - ada[0]["atas"])  # atas unit = lapisan pertama unit itu
            tembus = any(st.URUT.index(lp["unit"]) > st.URUT.index(u) for lp in t["lapisan"])
            if tembus:
                tebal.append(ada[-1]["bawah"] - ada[0]["atas"])
        nv = n60.get(u, [])
        n60_teks = (f"{min(nv):.0f}-{max(nv):.0f} (median {np.median(nv):.0f}; n = {len(nv)})" if nv else "-")
        qv = [q for q in qt_unit.get(u, []) if q is not None]
        baris.append([i, u, nama, uscs, URAIAN[u], _stat(elev, 2), _stat(tebal, 2), n60_teks,
                      _stat(qv, 2) if qv else "-"])
    lb = Lembar(wb.create_sheet("Unit Tanah"), 2, "Unit tanah (model lapisan sementara)",
                [5, 7, 22, 9, 46, 17, 13, 20, 14])
    lb.catatan(LABEL + " Elevasi atas dan tebal dari semua titik; N60 dari langkah 2.1 (uji yang dipakai, "
               "penolakan = batas bawah); qt = median per titik dalam unit. " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Kode", "Nama unit", "USCS", "Uraian khas", "Elevasi atas (m)", "Tebal (m)", "N60",
              "qt median per titik (MPa)"], baris, rata=list("cclclcccc"), fill_kolom={i: AI for i in range(5, 9)})

    # ---- Batas lapisan
    kepala = ["No", "Titik", "Jenis", "x (m)", "y (m)", "Elevasi tanah (m)", "Akhir (m)"] + \
             [f"Atas {u} (m)" for u in st.URUT[1:]] + ["Tebal U3 (m)", "Catatan"]
    baris = []
    for i, t in enumerate(titik, start=1):
        atas = []
        for u in st.URUT[1:]:
            if t["jenis"] == "CPTu" and u == "U2":
                atas.append("-")
                continue
            d = st.atas_unit(t, u)
            ada = any(lp["unit"] == u for lp in t["lapisan"])
            atas.append(round(d, 2) if d is not None and (ada or d <= t["akhir"]) else "-")
        cat = ""
        if t.get("org_terbuka"):
            cat = "Berhenti di 4,0 m masih di gambut: tebal U3 ≥ nilai tertulis."
        if t["nama"] == "CPTu-4":
            cat = "Lubang awal 0-1 m; u2 0-4,5 m tidak andal (2.1)."
        if t["nama"] == "BH-8":
            cat = "Urugan berpuing 1,34 m."
        baris.append([i, t["nama"], t["jenis"], t["x"], t["y"], t["elev"], t["akhir"]] + atas +
                     [round(st.tebal_organik(t), 2), cat])
    lb = Lembar(wb.create_sheet("Batas Lapisan"), 3, "Kedalaman atas unit per titik (dari muka tanah setempat)",
                [5, 9, 11, 6, 6, 9, 8] + [8] * 7 + [8, 29])
    lb.catatan(LABEL + " '-' = tidak tercapai atau tidak dibaca. Bila unit tidak ada, kedalaman atasnya sama "
               "dengan atas unit di bawahnya (tebal nol). " + LABEL_AI)
    lb.kosong()
    lb.tabel(kepala, baris, rata=list("cclcccc") + ["c"] * 8 + ["l"],
             fmt=[None, None, None, "0", "0", "0.00", "0.00"] + ["0.00"] * 8 + [None],
             fill_kolom={i: AI for i in range(7, 16)}, beku_kolom=2)

    # ---- Cek silang
    ref = {t["nama"]: t for t in titik}
    baris = []
    no = 0
    for c, b in PASANGAN:
        tc, tb = ref[c], ref[b]
        jarak = float(np.hypot(tc["x"] - tb["x"], tc["y"] - tb["y"]))
        for u in ("U3", "U4", "U5", "U6"):
            dc, db = st.atas_unit(tc, u), st.atas_unit(tb, u)
            ada = any(lp["unit"] == u for lp in tc["lapisan"] + tb["lapisan"])
            if dc is None or db is None or not ada:
                continue
            no += 1
            ec, eb = tc["elev"] - dc, tb["elev"] - db
            sel = ec - eb
            baris.append([no, f"{c} - {b}", round(jarak, 1), f"Atas {u}", round(ec, 2), round(eb, 2), round(sel, 2),
                          0.5, "Lolos" if abs(sel) <= 0.5 else "Tidak lolos"])
    tc, tb = ref["CPTu-5"], ref["BH-3"]
    lb = Lembar(wb.create_sheet("Cek Silang"), 4, "Cek silang batas lapisan CPTu terhadap bor terdekat",
                [5, 17, 10, 11, 14, 14, 12, 10, 12])
    lb.catatan(LABEL + " Dibandingkan dalam elevasi (muka tanah kedua titik berbeda). Batas toleransi 0,5 m "
               "ditetapkan sebelum menghitung (ketelitian batas log ±0,1 m, jarak titik 2-3 m). " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Pasangan", "Jarak (m)", "Batas", "Elevasi CPTu (m)", "Elevasi bor (m)", "Selisih (m)",
              "Batas (m)", "Status"], baris, rata=list("cclcccccc"),
             fmt=[None, None, "0.0", None, "0.00", "0.00", "0.00", "0.0", None], fill_kolom={6: AI, 8: AI})
    lb.ws._print_rows = None
    lb.kosong()
    lb.catatan(f"Tebal U3: CPTu-5 {st.tebal_organik(tc):.2f} m, BH-3 {st.tebal_organik(tb):.2f} m "
               f"(selisih {st.tebal_organik(tc) - st.tebal_organik(tb):+.2f} m).".replace(".", ","), fill=AI)

    # ---- Catatan
    lb = Lembar(wb.create_sheet("Catatan"), 5, "Catatan dan temuan langkah 2.2", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Catatan"], [[i, t] for i, t in enumerate(CATATAN, start=1)], rata=list("cl"),
             fill_kolom={1: AI})

    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar, baris


if __name__ == "__main__":
    k, b = buat()
    print(k)
    for r in b:
        print(r)
