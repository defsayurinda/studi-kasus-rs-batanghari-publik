"""Laporan antara LA.1: pondasi per zona tanah, opsi letak massa, dan parkir permukaan vs gedung parkir.

Tindak lanjut evaluasi kunci Tahap 3 no. 1-3. Profil per zona dari log bor 2.2 (BH-5 selatan, BH-7 tengah, BH-3 utara),
tebal gambut U3 diinterpolasi linear dari titik penyelidikan 2.2 (data sendiri). Rumus tiang tetap 3.7 (FHWA
NHI-06-089 Vol II hal. 239-243; SNI 8460:2017 hal. 194, 204, 295). Zona baik = amplop 6 lantai di luar zona labil (3.2)
dengan gambut < 1 m. Luas per mobil permukaan 25 m² dan harga perkerasan [Asumsi].
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 19 Nov 2026: opsi (a) massa tetap, tiang per zona.
"""
import math
from pathlib import Path

import tahap3_basement as bs
import tahap3_biaya as bi
import tahap3_pondasi as fd
import tahap3_program as pr
import tahap3_tapak as tp

AKAR = Path(__file__).resolve().parents[1]
BERKAS = AKAR / "03 Desain Konsep" / "LA.1 Pondasi per Zona.xlsx"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = "DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026: opsi (a) massa tetap di tempat, tiang per zona."
BATAS_BAIK = 1.0  # m gambut: kriteria zona baik (evaluasi kunci Tahap 3, pelajaran 1)
M2_MOBIL_PERMUKAAN = 25.0  # m² per mobil termasuk jalur [Asumsi]
M2_MOTOR = 2.0  # m² per motor (3.5)
HARGA_PERKERASAN = 0.35  # juta Rp/m²: paving blok + geotekstil + lapis pondasi (biaya langsung) [Asumsi]
OPSI_B = {"podium": (46.0, 134.0, 26.0, 66.0), "gu": (6.0, 38.0, 8.0, 42.0)}  # hasil pencarian letak (fungsi cari_letak)


def _kotak(x0, x1, y0, y1):
    from shapely.geometry import box
    return box(x0, y0, x1, y1)


_BAIK = None


def zona_baik():
    """Amplop 6 lantai (tanpa zona labil) dengan gambut < 1 m; sel 1 m, dihitung sekali (vektor)."""
    global _BAIK
    if _BAIK is None:
        import numpy as np
        from shapely.geometry import box
        from shapely.ops import unary_union
        fd.tebal_gambut(0, 0)  # siapkan interpolator
        gx, gy = np.meshgrid(np.arange(0.5, 140, 1.0), np.arange(0.5, 90, 1.0))
        v = fd._GAMBUT[0](gx, gy)
        v = np.where(np.isnan(v), fd._GAMBUT[1](gx, gy), v)
        sel = [box(x - 0.5, y - 0.5, x + 0.5, y + 0.5) for x, y, t in zip(gx.ravel(), gy.ravel(), v.ravel())
               if t < BATAS_BAIK]
        _BAIK = tp.amplop().intersection(unary_union(sel))
    return _BAIK


def porsi_baik(baik=None):
    """Porsi tapak tiap massa yang berada di zona baik, opsi (a) letak 3.4 dan opsi (b)."""
    baik = baik or zona_baik()
    pd, gu = pr.MASSA["PODIUM"], bs.GEDUNG_UP
    hasil = {}
    for nama, kotak in (("a podium", (*pd["x"], *pd["y"])), ("a gedung utilitas", (*gu["x"], *gu["y"])),
                        ("b podium", OPSI_B["podium"]), ("b gedung utilitas", OPSI_B["gu"])):
        k = _kotak(*kotak)
        hasil[nama] = {"luas": k.area, "baik": k.intersection(baik).area,
                       "gambut_maks": max(fd.tebal_gambut(x, y) for x in range(int(kotak[0]), int(kotak[1]) + 1, 2)
                                          for y in range(int(kotak[2]), int(kotak[3]) + 1, 2))}
    return hasil


def daya_dukung_zona(kode="BOR-800"):
    return {z: {**fd.beban_izin(kode, z), "urugan": fd.urugan(z)[0], "titik": fd.PROFIL[z]["titik"]} for z in fd.PROFIL}


def nsf_tangan(profil="UTARA", kode="BOR-800"):
    """Cek silang NSF statis: satu nilai σ'v di tengah tiap lapisan U1-U4 × tebal × β × keliling (T-56)."""
    lap = fd.PROFIL[profil]["lapisan"]
    keliling = math.pi * fd.TIANG[kode]["D"]
    atas, total = 0.0, 0.0
    for unit, bawah, _, jenis, _, _ in lap:
        if unit in ("U1", "U2", "U3", "U4"):
            total += fd.BETA_NSF[jenis] * fd.sigma_v((atas + bawah) / 2, profil) * keliling * (bawah - atas)
        atas = bawah
    return total


def tiang(per_zona):
    o = fd.opsi("A", per_zona)
    return {"n": o["n_utama"] + o["n_gu"], "biaya": o["biaya"], "rincian": o}


def parkir():
    """Kebutuhan lahan bila semua mobil di permukaan dibanding lahan sisa (LLP - tapak - KDH - jalan - kolam - IPAL)."""
    t = tp.ringkasan()
    k = bs.cek_kdh()
    oc = bs.opsi()[2]
    utilitas = pr.rekap_lantai()["GU"]["bruto"]
    lahan_sisa_tanpa_gp = (t["lahan_perencanaan"] - pr.MASSA["PODIUM"]["luas"] if "luas" in pr.MASSA["PODIUM"] else
                           t["lahan_perencanaan"] - 72 * 48) - utilitas - t["kdh_min"] - k["jalan"] - k["kolam"] - k["ipal"]
    perlu_semua = oc["mobil"] * M2_MOBIL_PERMUKAAN + oc["motor"] * M2_MOTOR
    lahan_sisa_c = t["lahan_perencanaan"] - pr.cek_massa()["tapak"] - t["kdh_min"] - k["jalan"] - k["kolam"] - k["ipal"] \
        - k["parkir"]
    mobil_v5 = int(bs.GEDUNG_UP["x"][1] - bs.GEDUNG_UP["x"][0]) * int(bs.GEDUNG_UP["y"][1] - bs.GEDUNG_UP["y"][0]) // 30
    perlu_v5 = (120 - (oc["mobil"] - mobil_v5)) * M2_MOBIL_PERMUKAAN
    r = bi.rekap()
    biaya_gp = (r["standar"]["PARKIR"] + dict((b[0], b[1]) for b in r["baris"])[
        "Nonstandar dek parkir (elektrikal, kebakaran)"]) * (1 + bi.KONTINJENSI)
    return {"mobil": oc["mobil"], "motor": oc["motor"], "perlu_semua_permukaan": perlu_semua,
            "lahan_tanpa_gedung_parkir": lahan_sisa_tanpa_gp, "kurang": perlu_semua - lahan_sisa_tanpa_gp,
            "lahan_sisa_opsi_c": lahan_sisa_c, "mobil_kurang_v5": 120 - (oc["mobil"] - mobil_v5),
            "perlu_v5": perlu_v5, "v5_layak": perlu_v5 <= lahan_sisa_c,
            "biaya_gedung_parkir": biaya_gp,
            "biaya_permukaan_v5": perlu_v5 * HARGA_PERKERASAN * bi.FAKTOR_NYATA}


def ringkasan():
    a, b = tiang(False), tiang(True)
    return {"zona": daya_dukung_zona(), "tiang_37": a, "tiang_zona": b, "selisih_tiang": b["n"] - a["n"],
            "selisih_biaya": (b["biaya"] - a["biaya"]) * bi.FAKTOR_NYATA * (1 + bi.KONTINJENSI),
            "porsi": porsi_baik(), "parkir": parkir(), "nsf_tangan": nsf_tangan(),
            "nsf_skrip": fd.beban_izin("BOR-800", "UTARA")["NSF_statis"]}


def fmt(v, d=0):
    s = f"{v:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


def buat_excel(keluar=BERKAS):
    import openpyxl

    from format_dokumen import AI, Lembar, set_font_bawaan

    r = ringkasan()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk pondasi per zona tanah (LA.1)", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        "Tindak lanjut evaluasi kunci Tahap 3 no. 1-3: 3.7 menghitung gesekan negatif (NSF) dengan satu profil BH-5 tanpa "
        "gambut, padahal sebagian podium dan gedung utilitas di atas gambut.",
        "Profil per zona dari log bor 2.2: selatan BH-5 (gambut < 0,5 m), tengah BH-7 (0,5-2,0 m), utara BH-3 (≥ 2,0 m). "
        "Tebal gambut tiap kolom diinterpolasi linear dari titik penyelidikan 2.2. Batas zona [Asumsi].",
        "Rumus tiang tetap 3.7: FHWA NHI-06-089 Vol II hal. 239-243; NSF sebagai beban SNI 8460:2017 hal. 204; FK 2,5 "
        "hal. 194; likuifaksi FK 1,1 hal. 295. NSF statis kini termasuk U3 gambut (β 0,25 [Asumsi]).",
        "Zona baik = amplop 6 lantai (3.2) di luar zona labil, dengan gambut < 1 m. Opsi (b) dicari dengan pencarian "
        "letak persegi (grid 8 m) yang memaksimalkan porsi tapak di zona baik.",
        "Parkir: luas per mobil permukaan 25 m², motor 2 m², harga perkerasan [Asumsi].",
    ])], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Daya Dukung Zona"), 2, "Daya dukung tiang bor Ø800 per zona", [24, 16, 16, 16, 40])
    lb.catatan(LABEL)
    zz = r["zona"]
    kol = list(zz)
    lb.tabel(["Butir"] + kol + ["Keterangan"], [
        ["Titik acuan"] + [zz[z]["titik"] for z in kol] + ["log bor 2.2"],
        ["Tebal urugan ke +12,05 (m)"] + [round(zz[z]["urugan"], 2) for z in kol] + ["halaman 3.3"],
        ["Panjang tiang (m)"] + [round(zz[z]["panjang"], 1) for z in kol] + ["dari bawah pile cap"],
        ["Qult (kN)"] + [round(zz[z]["Qult"]) for z in kol] + ["U6 α su, U7 β σ'v + ujung"],
        ["NSF statis U1-U4 (kN)"] + [round(zz[z]["NSF_statis"]) for z in kol] + ["termasuk U3 gambut"],
        ["NSF likuifaksi U1-U5 (kN)"] + [round(zz[z]["NSF_lik"]) for z in kol] + [""],
        ["Beban izin (kN)"] + [round(zz[z]["izin"]) for z in kol] + ["min(statis, likuifaksi)"],
    ], rata=["l"] + ["c"] * len(kol) + ["l"], fill_kolom={i + 1: AI for i in range(len(kol))})
    lb.kosong()
    lb.tabel(["Cek silang NSF utara (T-56)", "Skrip (kN)", "Tangan (kN)", "Selisih", "Keterangan"], [
        ["NSF statis BH-3", round(r["nsf_skrip"]), round(r["nsf_tangan"]),
         f"{(r['nsf_tangan'] / r['nsf_skrip'] - 1) * 100:.1f} %".replace(".", ","),
         "tangan: σ'v di tengah lapisan; toleransi 10 %"],
    ], rata=list("lcccl"), fill_kolom={1: AI, 2: AI}, beku=False)

    lb = Lembar(wb.create_sheet("Tiang per Kolom"), 3, "Jumlah tiang per kolom dengan profil zona", [10, 10, 12, 12, 14, 10, 10])
    lb.catatan(LABEL + " Opsi A (bor Ø800) seluruhnya.")
    o = r["tiang_zona"]["rincian"]
    rows = [[c["x"], c["y"], round(fd.tebal_gambut(c["x"], c["y"]), 2), c["zona"], round(c["P"]) if "P" in c else "-", c["n"],
             "GU" if c in o["gu"] else ("inti" if c in o["inti"] else "utama")] for c in o["utama"] + o["inti"] + o["gu"]]
    lb.tabel(["x (m)", "y (m)", "Gambut (m)", "Zona", "P (kN)", "Tiang", "Massa"], rows, rata=list("ccccccc"),
             fmt=[None, None, "0.00", None, "#,##0", "0", None], fill_kolom={5: AI})

    lb = Lembar(wb.create_sheet("Opsi Massa"), 4, "Opsi letak massa terhadap zona baik", [30, 16, 16, 16, 60])
    lb.catatan(LABEL + f" Zona baik {fmt(zona_baik().area)} m² (gambut < 1 m, dalam amplop, di luar zona labil).")
    p = r["porsi"]
    lb.tabel(["Massa", "Tapak (m²)", "Di zona baik (m²)", "Gambut maks (m)", "Keterangan"], [
        [k, round(v["luas"]), round(v["baik"]), round(v["gambut_maks"], 2),
         {"a podium": "letak 3.4: x 12-84, y 27-75", "a gedung utilitas": "letak 3.5: x 100-134, y 44-76",
          "b podium": "x 46-134, y 26-66 (88 × 40 m, grid 8 m)",
          "b gedung utilitas": "x 6-38, y 8-42 (32 × 34 m), barat daya"}[k]] for k, v in p.items()],
        rata=list("lcccl"), fmt=[None, "#,##0", "#,##0", "0.00", None], fill_kolom={2: AI, 3: AI})
    lb.kosong()
    a_ = sum(v["baik"] for k, v in p.items() if k.startswith("a")) / sum(v["luas"] for k, v in p.items() if k.startswith("a"))
    b_ = sum(v["baik"] for k, v in p.items() if k.startswith("b")) / sum(v["luas"] for k, v in p.items() if k.startswith("b"))
    lb.tabel(["Opsi", "Porsi di zona baik", "Tiang (A)", "Biaya tiang + (juta Rp)", "Akibat"], [
        ["(a) tetap, tiang per zona", f"{a_:.0%}", r["tiang_zona"]["n"], round(r["selisih_biaya"]),
         "Tiang tetap ke U7: NSF naik ±4 %, +8 tiang. Halaman di atas gambut turun lebih (urug lebih/PVD sudah "
         "dihitung 3.3); sambungan fleksibel gedung-halaman; GU di atas gambut tetap bertiang."],
        ["(b) massa dipindah ke zona baik", f"{b_:.0%}", "dihitung ulang", "dihitung ulang",
         "Zonasi 3.4, grid 3.6, parkir 3.5, model 3.9, biaya 3.8 diulang; podium 3.520 m² (88 × 40) ≥ 3.456 "
         "m² perlu; GU pindah ke barat daya dekat jalan barat; menara di atas podium baru; jarak ke gudang 10 m."],
    ], rata=list("lcccl"), fill_kolom={1: AI, 2: AI, 3: AI}, beku=False)

    lb = Lembar(wb.create_sheet("Parkir"), 5, "Parkir permukaan dibanding gedung parkir", [52, 18, 60])
    lb.catatan(LABEL)
    k = r["parkir"]
    lb.tabel(["Butir", "Nilai", "Keterangan"], [
        ["Mobil / motor rencana (opsi C)", f"{k['mobil']} / {k['motor']}", "3.5"],
        ["Lahan perlu bila semua di permukaan (m²)", round(k["perlu_semua_permukaan"]), "25 m²/mobil, 2 m²/motor [Asumsi]"],
        ["Lahan tersedia tanpa gedung parkir (m²)", round(k["lahan_tanpa_gedung_parkir"]),
         "LLP - podium - utilitas 1 lantai - KDH - jalan - kolam - IPAL"],
        ["Kekurangan lahan (m²)", round(k["kurang"]), "semua di permukaan tidak muat tanpa mengurangi KDH"],
        ["V5: mobil kurang dari 120 bila LT4 parkir ditunda", k["mobil_kurang_v5"], ""],
        ["V5: lahan permukaan sementara perlu (m²)", round(k["perlu_v5"]), ""],
        ["Lahan sisa opsi C (m²)", round(k["lahan_sisa_opsi_c"]), "setelah parkir permukaan 3.5"],
        ["V5 layak dengan parkir permukaan sementara", "ya" if k["v5_layak"] else "tidak", "perkerasan fleksibel di utara"],
        ["Biaya dek parkir gedung (juta Rp)", round(k["biaya_gedung_parkir"]), "standar + nonstandar + kontinjensi (3.8)"],
        ["Biaya parkir permukaan sementara V5 (juta Rp)", round(k["biaya_permukaan_v5"]), "perkerasan [Asumsi]"],
    ], rata=list("lcl"), fill_kolom={1: AI})
    wb.save(keluar)
    return keluar


if __name__ == "__main__":
    r = ringkasan()
    for z, v in r["zona"].items():
        print(z, round(v["izin"]), round(v["NSF_statis"]))
    print("tiang", r["tiang_37"]["n"], "->", r["tiang_zona"]["n"], "biaya +", round(r["selisih_biaya"]))
    print({k: (round(v["baik"]), round(v["luas"])) for k, v in r["porsi"].items()})
    print({k: (round(v) if isinstance(v, float) else v) for k, v in r["parkir"].items()})
    print("NSF tangan", round(r["nsf_tangan"]), "skrip", round(r["nsf_skrip"]))
