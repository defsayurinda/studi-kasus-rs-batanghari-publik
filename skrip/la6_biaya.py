"""Laporan antara LA.6: rincian kenaikan luas, biaya basement (informasi), biaya rev B, dan paket tahap 1 ±Rp 230 M.

Tindak lanjut rapat konsep (Tabel 1.2 no. 4, 8; R3-1) dan keputusan rapat: pembiayaan bertahap, target akhir 150 TT,
tahap 1 dibatasi ±Rp 230 M. Dasar: 3.8 (Permen PUPR 22/2018 Pasal 21, 27, 29, 31 sebagai pedoman), LA.1 (tiang per
zona, opsi a), LA.4 (helipad hanya disiapkan, TOR 5.7), LA.5 (uji tiang), LA.3 (perkuatan tebing, PR #21, draf),
Program Ruang owner (lembar Rekap). Permenkes 6/2026 Pasal 10 (1): RS minimal 50 TT.
Harga basement, perkuatan tebing, penyiapan atap helipad, dan parkir permukaan [Asumsi].
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 19 Nov 2026 (LA.6).
"""
import math
from pathlib import Path

import la1_zona as l1
import la5_lapangan as l5
import tahap3_basement as bs
import tahap3_biaya as bi
import tahap3_pondasi as fd
import tahap3_program as pr

AKAR = Path(__file__).resolve().parents[1]
BERKAS = AKAR / "03 Desain Konsep" / "LA.6 Biaya dan Pentahapan.xlsx"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = "DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026 (LA.6)."
PAGU_TAHAP1 = 230_000.0  # juta Rp, keputusan rapat konsep (pagu 168 M + pinjaman tambahan ±60 M, belum pasti)
OWNER = {"bersih": 8586.0, "di_atas_tanah": 9200.0, "basement": 2800.0, "total": 12000.0, "tt": 138}  # Program Ruang
TT_PER_LANTAI_INAP = 50  # 150 TT di LT4-LT6 (3.4)
# biaya langsung [Asumsi]
HARGA = {"dinding_potong_m2": 5.5, "galian_m3": 0.15, "pelat_basement_m3": 4.4, "dewatering": 2500.0,
         "kedap_m2": 0.4, "ramp_basement": 1500.0,
         "bronjong_m3": 0.75, "turap_m": 4.6, "pompa_outlet": 500.0, "atap_helipad": 1000.0, "parkir_m2": 0.35}
TEBING = {"panjang": 40.0, "bronjong_m3_per_m": 6.6, "tiang_jarak": 1.5, "tiang_panjang": 15.0}  # LA.3 konsep


# ------------------------------------------------------------------ rincian kenaikan luas
def rincian_luas():
    lf = bi.luas_fungsi()
    bruto_program = sum(b["bruto"] for b in lf if b["kelompok"] not in ("Parkir", "Sisa massa"))
    bersih = bruto_program / pr.FAKTOR_BRUTO
    f_owner = OWNER["di_atas_tanah"] / OWNER["bersih"]
    parkir = next(b["bruto"] for b in lf if b["kelompok"] == "Parkir")
    sisa = next(b["bruto"] for b in lf if b["kelompok"] == "Sisa massa")
    langkah = [
        ("Luas di atas tanah program owner v2 (138 TT)", OWNER["di_atas_tanah"]),
        ("Tambahan program bersih konsultan (150 TT, ruang wajib)", (bersih - OWNER["bersih"]) * f_owner),
        (f"Faktor bruto {fmt(f_owner)} → {fmt(pr.FAKTOR_BRUTO)} (koridor 2,40 m, inti, shaft)",
         bruto_program - bersih * f_owner),
        ("Basement owner (parkir + utilitas)", OWNER["basement"]),
        ("Basement diganti dek parkir gedung utilitas (3.5 opsi C)", parkir - OWNER["basement"]),
        ("Sisa massa belum terprogram (3.4; dikurangi V1 ±1.152 m²)", sisa),
    ]
    return langkah, sum(v for _, v in langkah)


# ------------------------------------------------------------------ basement penuh (informasi, R3-1)
def basement_penuh():
    a = bs.opsi()[0]
    h = HARGA
    pd = pr.MASSA["PODIUM"]
    luas = (pd["x"][1] - pd["x"][0]) * (pd["y"][1] - pd["y"][0])
    item = [
        ("Dinding potong menembus U5 (±22 m)", a["dinding"] * 22.0 * h["dinding_potong_m2"]),
        ("Galian", a["galian"] * h["galian_m3"]),
        ("Pelat basement 0,6 m pemberat uplift", luas * 0.6 * h["pelat_basement_m3"]),
        ("Dewatering dan sumur pelepas", h["dewatering"]),
        ("Kedap air", luas * h["kedap_m2"]),
        ("Ramp masuk di atas banjir", h["ramp_basement"]),
    ]
    total = sum(v for _, v in item) * bi.FAKTOR_NYATA * (1 + bi.KONTINJENSI)
    hemat_dek = l1.parkir()["biaya_gedung_parkir"]
    return {"item": item, "total": total, "mobil": a["mobil"], "hemat_dek_parkir": hemat_dek,
            "selisih_bersih": total - hemat_dek, "fk_blowin": a["fk"]}


# ------------------------------------------------------------------ biaya rev B
def tambahan_rev_b():
    k = bi.FAKTOR_NYATA * (1 + bi.KONTINJENSI)
    fa, fz = fd.opsi("A"), fd.opsi("A", per_zona=True)
    t = TEBING
    tebing = (t["panjang"] * t["bronjong_m3_per_m"] * HARGA["bronjong_m3"]
              + math.ceil(t["panjang"] / t["tiang_jarak"]) * t["tiang_panjang"] * HARGA["turap_m"] + HARGA["pompa_outlet"])
    return [
        ("Tiang per zona gambut (LA.1, 381 tiang)", (fz["biaya"] - fa["biaya"]) * k),
        ("Program uji tiang SNI 8460 Pasal 9.8 (LA.5)", l5.uji_tiang()["biaya"] * (1 + bi.KONTINJENSI)),
        ("Perkuatan tebing dan pompa outlet (LA.3) [Asumsi harga]", tebing * k),
        ("Penyiapan struktur atap untuk helipad, dek menyusul (LA.4, TOR 5.7) [Asumsi]", HARGA["atap_helipad"] * k),
    ]


def ve_disetujui():
    """Rekayasa nilai yang disetujui rapat konsep: V3, V4, V6, V7; V1 (LT3 utara bukan fungsi kritis, syarat terpenuhi);
    V5 dengan parkir permukaan sementara (layak, LA.1). V2 menunggu uji tiang: potensi, tidak dikurangkan."""
    ve = {o["kode"]: o for o in bi.rekayasa_nilai()}
    pakai = [ve[k] for k in ("V1", "V3", "V4", "V5", "V6", "V7")]
    tambah_parkir = l1.parkir()["biaya_permukaan_v5"] * (1 + bi.KONTINJENSI)
    return pakai, tambah_parkir, ve["V2"]


def rev_b():
    r = bi.rekap()
    tb = tambahan_rev_b()
    total = r["total"] + sum(v for _, v in tb)
    pakai, parkir, v2 = ve_disetujui()
    setelah = total - sum(o["hemat"] for o in pakai) + parkir
    return {"total_38": r["total"], "tambahan": tb, "total_rev_b": total, "ve": pakai, "parkir_v5": parkir,
            "setelah_ve": setelah, "potensi_v2": v2["hemat"], "setelah_v2": setelah - v2["hemat"]}


# ------------------------------------------------------------------ paket tahap 1
def biaya_per_bagian():
    """Biaya (juta Rp, sudah dengan nonstandar ikutan dan kontinjensi) per bagian bangunan setelah rekayasa nilai.
    Standar per lantai dari baris 3.8; M/E nonstandar ikut porsi standarnya; fasad dibagi menurut luas lantai."""
    lf = bi.luas_fungsi()
    k = 1 + bi.KONTINJENSI
    f_me = 1 + bi.persen_nonstandar()
    r = bi.rekap()
    baris = dict((b[0], b[1]) for b in r["baris"])
    surplus = {"LT1": 0.0, "LT2": 652.0, "LT3": 1162.0, "LT4": 274.0, "LT5": 274.0, "LT6": 274.0}  # 3.4 massa - program
    std = {k_: 0.0 for k_ in ("LT1", "LT2", "LT3", "LT4", "LT5", "LT6", "GU", "PARKIR")}
    for b in lf:
        if b["kelompok"] == "Parkir":
            std["PARKIR"] += b["biaya"]
        elif b["massa"] == "GU":
            std["GU"] += b["biaya"]
        elif b["kelompok"] == "Sisa massa":
            tot = sum(surplus.values())
            for lt, v in surplus.items():
                std[lt] += b["biaya"] * v / tot
        elif b["lantai"] in std:
            std[b["lantai"]] += b["biaya"]
        elif b["lantai"] == "LT4-LT6":
            for lt in ("LT4", "LT5", "LT6"):
                std[lt] += b["biaya"] / 3
        elif b["lantai"] == "LT1-LT6":
            for lt in ("LT1", "LT2", "LT3", "LT4", "LT5", "LT6"):
                std[lt] += b["biaya"] / 6
    fasad = baris["Peningkatan arsitektur: fasad kaca"]
    luas_lt = {"LT1": 3456, "LT2": 3456, "LT3": 3456, "LT4": 1536, "LT5": 1536, "LT6": 1536}
    bagian = {lt: (std[lt] * f_me + fasad * luas_lt[lt] / sum(luas_lt.values())) * k for lt in luas_lt}
    bagian["GU utilitas"] = std["GU"] * f_me * k
    bagian["Dek parkir"] = (std["PARKIR"] + baris["Nonstandar dek parkir (elektrikal, kebakaran)"]) * k
    rb = rev_b()
    bersama = (baris["Fondasi dalam: kebutuhan nyata dikurangi porsi fondasi standar"]
               + baris["Peningkatan struktur (kategori IV, KDS D)"]
               + baris["Penyiapan dan pematangan lahan: urugan, PVD"]) * k + sum(v for _, v in rb["tambahan"])
    bagian["Fondasi, lahan, tebing, uji tiang (bersama)"] = bersama
    bagian["Dermaga"] = baris["Dermaga ambulans air dan teras pandang"] * k
    return bagian


def paket():
    """Susunan tahap: tahap 1 tidak boleh kurang dari 50 TT (Permenkes 6/2026 Pasal 10 (1))."""
    b = biaya_per_bagian()
    ve = {o["kode"]: o["hemat"] for o in bi.rekayasa_nilai()}
    lengkap = sum(b.values())
    # Paket A: semua kecuali V-tunda (LT6 fit-out, LT4 dek parkir, dermaga) = setelah VE disetujui
    a = rev_b()["setelah_ve"]
    # Paket B: + menara LT5-LT6 seluruhnya ditunda (struktur menara di atas LT4 menyusul), 50 TT di LT4
    menara_tunda = b["LT5"] + b["LT6"] - ve["V6"]
    pb = a - menara_tunda
    # Paket C: + dek parkir LT2-LT4 ditunda (parkir permukaan sementara di utara, kurang dari 120 mobil)
    pc = pb - (b["Dek parkir"] - ve["V5"])
    # Paket D: + LT3 podium hanya cangkang (administrasi, gizi, laundri sementara di LT1-LT2/ruang sewa)
    lt3_fitout = b["LT3"] * 0.45  # porsi lantai, plafon, utilitas, perampungan + M/E fit-out ±45 % [Asumsi]
    pd_ = pc - lt3_fitout
    hasil = [
        {"kode": "A", "uraian": "Seluruh lingkup setelah rekayasa nilai disetujui (V1, V3-V7)", "biaya": a, "tt": 100},
        {"kode": "B", "uraian": "A, menara LT5-LT6 ditunda (struktur dan isi); 50 TT di LT4", "biaya": pb,
         "tt": TT_PER_LANTAI_INAP},
        {"kode": "C", "uraian": "B, dek parkir LT2-LT4 ditunda; parkir permukaan sementara", "biaya": pc,
         "tt": TT_PER_LANTAI_INAP},
        {"kode": "D", "uraian": "C, LT3 podium hanya cangkang", "biaya": pd_, "tt": TT_PER_LANTAI_INAP},
        {"kode": "E", "uraian": "D, ditambah V2 tiang hibrida bila uji tiang berhasil", "biaya": pd_ - ve["V2"],
         "tt": TT_PER_LANTAI_INAP},
    ]
    for h in hasil:
        h["selisih"] = h["biaya"] - PAGU_TAHAP1
        h["tahap2"] = rev_b()["total_rev_b"] - h["biaya"]
    return hasil, b, lengkap


def cek_bagian():
    """Cek silang T-64: jumlah biaya per bagian (sebelum rekayasa nilai) = perkiraan rev B."""
    return sum(biaya_per_bagian().values()), rev_b()["total_rev_b"]


def ringkasan():
    luas, total_luas = rincian_luas()
    return {"luas": luas, "total_luas": total_luas, "basement": basement_penuh(), "rev_b": rev_b(), "paket": paket()[0]}


def fmt(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


def m(v):
    return fmt(v / 1000, 1)


# ------------------------------------------------------------------ Excel
def buat_excel(keluar=BERKAS):
    import openpyxl

    from format_dokumen import AI, Lembar, set_font_bawaan

    r = ringkasan()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk biaya dan pentahapan (LA.6)", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        "Tindak lanjut rapat konsep no. 4 (rincian luas), no. 8 (paket tahap 1 ±Rp 230 M), R3-1 (biaya basement penuh).",
        "Biaya rev B = 3.8 + tiang per zona (LA.1) + uji tiang (LA.5) + perkuatan tebing (LA.3) + penyiapan atap helipad "
        "(LA.4). Rekayasa nilai yang disetujui rapat: V1, V3, V4, V5 (dengan parkir permukaan sementara), V6, V7; V2 "
        "menunggu uji tiang (potensi).",
        "Paket tahap 1 disusun bertingkat (A-D) dan dicek terhadap batas ±Rp 230 M dan minimal 50 TT (Permenkes 6/2026 "
        "Pasal 10 (1)).",
        "Semua harga [Asumsi] sampai SK HSBGN Kota Jambi dan survei harga (SE 47/2026 Lampiran I); rentang ±20 % (3.8).",
    ])], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Kenaikan Luas"), 2, "Rincian kenaikan luas 12.000 → 19.328 m²", [6, 70, 18])
    lb.catatan(LABEL + " Program Ruang owner (lembar Rekap) dibanding 3.4 dan 3.5.")
    rows = [[i + 1, n, v] for i, (n, v) in enumerate(r["luas"])]
    h, a, z = lb.tabel(["No", "Langkah", "Luas (m²)"], rows, rata=list("clc"), fmt=[None, None, "#,##0"],
                       fill_kolom={2: AI})
    lb.ws[f"{lb.kol(2)}{z + 1}"] = f"=SUM({lb.kol(2)}{a}:{lb.kol(2)}{z})"
    lb.ws[f"{lb.kol(1)}{z + 1}"] = "Jumlah (= luas lantai konsep 19.328 m²)"
    lb.ws[f"{lb.kol(2)}{z + 1}"].number_format = "#,##0"

    lb = Lembar(wb.create_sheet("Basement"), 3, "Basement penuh (informasi, bukan opsi)", [60, 18, 50])
    lb.catatan(LABEL + " Biaya langsung [Asumsi] × (1 + BTL) × (1 + PPN) × (1 + kontinjensi).")
    bm = r["basement"]
    lb.tabel(["Komponen", "Biaya langsung (juta Rp)", "Keterangan"],
             [[n, round(v), ""] for n, v in bm["item"]] + [
                 ["Jumlah dengan BTL, PPN, kontinjensi", round(bm["total"]), f"{bm['mobil']} mobil"],
                 ["Dek parkir gedung utilitas yang tidak perlu", -round(bm["hemat_dek_parkir"]), "LA.1"],
                 ["Selisih bersih basement penuh", round(bm["selisih_bersih"]),
                  f"FK blow-in {fmt(bm['fk_blowin'][0])}-{fmt(bm['fk_blowin'][1])} < 1,25 (3.5)"]],
             rata=list("lcl"), fmt=[None, "#,##0", None], fill_kolom={1: AI})

    lb = Lembar(wb.create_sheet("Biaya Rev B"), 4, "Perkiraan biaya rev B dan rekayasa nilai disetujui", [70, 20, 40])
    lb.catatan(LABEL)
    rb = r["rev_b"]
    rows = [["Perkiraan 3.8 (disetujui)", round(rb["total_38"]), "Permen PUPR 22/2018"]]
    rows += [[n, round(v), "tambahan rev B"] for n, v in rb["tambahan"]]
    rows += [["Perkiraan rev B", round(rb["total_rev_b"]), f"{fmt(rb['total_rev_b'] / bi.PAGU)} × pagu"]]
    rows += [[f"{o['kode']}: {o['uraian']}", -round(o["hemat"]), "disetujui rapat"] for o in rb["ve"]]
    rows += [["Parkir permukaan sementara (V5)", round(rb["parkir_v5"]), "LA.1"],
             ["Setelah rekayasa nilai disetujui", round(rb["setelah_ve"]), "dibangun bila tanpa pentahapan lain"],
             ["Potensi V2 setelah uji tiang", -round(rb["potensi_v2"]), "belum dikurangkan"]]
    lb.tabel(["Butir", "Biaya (juta Rp)", "Keterangan"], rows, rata=list("lcl"), fmt=[None, "#,##0", None],
             fill_kolom={1: AI})

    lb = Lembar(wb.create_sheet("Paket Tahap 1"), 5, "Paket tahap 1 terhadap batas ±Rp 230 M", [6, 64, 16, 10, 16, 16])
    lb.catatan(LABEL + " Tahap 2 = rev B - tahap 1. Minimal 50 TT (Permenkes 6/2026 Pasal 10 (1)).")
    lb.tabel(["Kode", "Paket", "Tahap 1 (juta Rp)", "TT", "Selisih batas (juta Rp)", "Tahap 2 (juta Rp)"],
             [[p["kode"], p["uraian"], round(p["biaya"]), p["tt"], round(p["selisih"]), round(p["tahap2"])]
              for p in r["paket"]], rata=list("clcccc"), fmt=[None, None, "#,##0", "0", "#,##0", "#,##0"], fill=AI)
    lb.kosong()
    jb, rv = cek_bagian()
    lb.tabel(["", "Cek silang (T-64)", "Nilai", "", "", "Keterangan"], [
        ["", "Jumlah biaya per bagian (juta Rp)", round(jb), "", "", "standar per lantai + M/E + fasad + bersama"],
        ["", "Perkiraan rev B (juta Rp)", round(rv), "", "", "lembar Biaya Rev B"],
    ], rata=list("clcccl"), fmt=[None, None, "#,##0", None, None, None], beku=False)
    lb.kosong()
    lb.bagian("B", "Kesimpulan (disetujui Defsa 19 Nov 2026)")
    d = next(p for p in r["paket"] if p["kode"] == "D")
    e = next(p for p in r["paket"] if p["kode"] == "E")
    lb.tabel(["No", "Uraian", "", "", "", ""], [
        [1, f"Batas tahap 1: paket terkecil yang masih 50 TT (D) ±Rp {m(d['biaya'])} M, dengan V2 (E) ±Rp {m(e['biaya'])} M; "
         f"masih di atas ±Rp 230 M sebesar ±Rp {m(e['selisih'])}-{m(d['selisih'])} M.", "", "", "", ""],
        [2, "Penyebab: biaya bersama fondasi tiang, urugan + PVD, tebing, dan uji tiang ±Rp 106 M harus dibangun di tahap 1 "
         "berapa pun TT-nya; penyebabnya tapak lunak dan banjir, bukan luas gedung.", "", "", "", ""],
        [3, "Pilihan owner: (a) pembiayaan tahap 1 ±Rp 300-325 M; (b) konsep tahap 1 diperkecil (gedung 50 TT tersendiri, "
         "podium dan menara menyusul), desain konsep diulang; (c) menunda proyek sampai pembiayaan cukup.", "", "", "", ""],
    ], rata=list("cl") + ["l"] * 4, fill_kolom={1: AI}, beku=False)
    wb.save(keluar)
    return keluar


if __name__ == "__main__":
    r = ringkasan()
    for n, v in r["luas"]:
        print(f"{n:70s} {v:8.0f}")
    print("total luas", round(r["total_luas"]))
    print("basement", round(r["basement"]["total"]), "bersih", round(r["basement"]["selisih_bersih"]))
    rb = r["rev_b"]
    print("3.8", round(rb["total_38"]), "rev B", round(rb["total_rev_b"]), "setelah VE", round(rb["setelah_ve"]),
          "setelah V2", round(rb["setelah_v2"]))
    for n, v in rb["tambahan"]:
        print("  +", n, round(v))
    for p in r["paket"]:
        print(p["kode"], round(p["biaya"]), p["tt"], "selisih", round(p["selisih"]))
    print({k: round(v) for k, v in paket()[1].items()})
