"""Laporan antara LA.5: tanggapan teknis klaim gudang timur, timbunan sementara dan uji mutu tanah merah, uji tiang
awal, dan paket awal urugan + PVD.

Tindak lanjut evaluasi kunci Tahap 3 no. 8 dan rapat konsep (Tabel 1.2 no. 2, 10, 11, 12).
Sumber:
- Survei Gudang Timur (2.7): patok, pengukur retak, inventaris retak, galian uji.
- Uji pompa PW-1 (2.3): Thiem dari OW-1/OW-2, lama pemompaan.
- Parameter U4 (2.4, `tahap2_penurunan_urugan.PAR`); urugan bertahap dan PVD (2.8, 3.3).
- SNI 8460:2017 Pasal 9.8 hal. 188-190 (acuan/privat): jumlah dan beban uji tiang, PDA, CSL.
- Biaya lahan 3.8.

Berlabel [Asumsi]: harga uji tiang, frekuensi dan kriteria uji mutu urugan (acuan uji tanah belum ada di acuan).
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 19 Nov 2026 (LA.5).
"""
import math
from pathlib import Path

import tahap2_air_tanah as at
import tahap2_kimia_tebing_gudang as kg
import tahap2_penurunan_urugan as pu
import tahap3_biaya as bi
import tahap3_peil as pl
import tahap3_pondasi as fd

AKAR = Path(__file__).resolve().parents[1]
BERKAS = AKAR / "03 Desain Konsep" / "LA.5 Gudang Urugan Uji Tiang.xlsx"
MEMO = AKAR / "10 Laporan" / "Tanggapan Teknis Klaim Gudang Timur.docx"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = "DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026 (LA.5)."
GW = 9.81
PW1 = (65.0, 40.0)  # lokasi sumur uji (2.3, lembar Instrumen)
DINDING_GUDANG_X = 144.0
BATAS_MA_GUDANG = 8.6  # m, muka air minimum sisi gudang selama konstruksi (2.8); kepala cerucuk +8,62 (galian uji)
TANAH_GRATIS = 22000.0  # m³ (surat owner butir 3)
UJI_MUTU_PER = 1000.0  # m³ per set uji mutu urugan [Asumsi]
HARGA_UJI = {"statik_instrumen": 350.0, "statik": 250.0, "lateral": 120.0, "pda": 15.0, "csl": 6.0}  # juta Rp [Asumsi]


# ------------------------------------------------------------------ klaim gudang
def tarikan_di_gudang():
    """Penurunan tinggi tekan U5 di dinding barat gudang selama uji pompa (Thiem, garis lurus s-ln r dari OW-1/OW-2)."""
    u = at.ringkas_uji_pompa()
    r1, r2 = 10.0, 30.0
    kem = (u["s1"] - u["s2"]) / math.log(r2 / r1)
    r = DINDING_GUDANG_X - PW1[0]
    s_thiem = max(0.0, u["s2"] - kem * math.log(r / r2))
    # cara kedua (T-63): sumur bayangan batas isian sungai (2.3), s = Q/(2πT) ln(r_bayangan / r)
    bayangan = (PW1[0], PW1[1] - 2 * u["a_pw"])
    r_bay = math.hypot(DINDING_GUDANG_X - bayangan[0], PW1[1] - bayangan[1])
    s_bay = u["q_rata"] / (2 * math.pi * u["T_thiem"]) * math.log(r_bay / r)
    lama_hari = max(b["Waktu sejak mulai (menit)"] for b in at.uji_debit_tetap()) / 1440
    return {"r": r, "s": max(s_thiem, s_bay), "s_thiem": s_thiem, "s_bayangan": s_bay, "lama_hari": lama_hari,
            "kemiringan": kem}


def penurunan_akibat_pompa():
    """Batas atas penurunan U4 di atas akuifer selama pemompaan: lapisan terpengaruh δ = 2√(cv t), Δσ' = γw s (NC)."""
    t = tarikan_di_gudang()
    gam, e0, cc, _, _ = pu.PAR["U4"]
    tahun = t["lama_hari"] / 365.0
    delta = 2 * math.sqrt(pu.CV * tahun)
    z = 9.3  # m, dasar U4 di sisi timur (BH-8/BH-6, 2.2)
    sv = 17.0 * 0.7 + (17.0 - GW) * 0.6 + (gam - GW) * (z - 1.3)  # kasar: U1-U2 di atas, U4 terendam
    dsv = GW * t["s"]
    eps = cc / (1 + e0) * math.log10((sv + dsv) / sv)
    return {"delta": delta, "sv": sv, "dsv": dsv, "eps": eps, "penurunan_mm": eps * delta / 2 * 1000}


def patok_per_periode():
    tgl, data = kg.patok()
    hasil = []
    for p in data:
        d = p["d_kor"]
        hasil.append({"patok": p["patok"], "uji_pompa": d[1] - d[0], "jan_feb": d[2] - d[1], "feb_mar": d[3] - d[2],
                      "mar": d[4] - d[3], "total": d[4], "catatan": p["catatan"]})
    return [t.date() for t in tgl], hasil


def ringkas_gudang():
    _, pk = patok_per_periode()
    return {"tarikan": tarikan_di_gudang(), "penurunan": penurunan_akibat_pompa(),
            "maks_periode_pompa": max(abs(p["uji_pompa"]) for p in pk),
            "rata_periode_pompa": sum(p["uji_pompa"] for p in pk) / len(pk),
            "rata_feb_mar": sum(p["feb_mar"] for p in pk if "bengkok" not in p["catatan"]) / (len(pk) - 1),
            "ketelitian_patok": 0.5, "retak_lama": ["R-2", "R-4"]}


# ------------------------------------------------------------------ timbunan sementara dan urugan bertahap
def timbunan():
    tu = pl.tahap_urugan()
    vu = pl.volume_urugan(pl.peil_usulan()["halaman"])
    kap1 = vu["luas"] * tu["h1_min"]
    return {"h1": tu["h1_min"], "luas": vu["luas"], "kapasitas_tahap1": kap1,
            "sisa_ditolak": max(0.0, TANAH_GRATIS - kap1), "set_uji": math.ceil(min(TANAH_GRATIS, kap1) / UJI_MUTU_PER),
            "tebal_rata": vu["tebal_rata"], "tebal_maks": vu["tebal_maks"], "v_padat": vu["v_padat"]}


def paket_urugan():
    tu = pl.tahap_urugan()
    t = timbunan()
    n_rata = math.ceil(t["tebal_rata"] / t["h1"])
    n_maks = math.ceil(t["tebal_maks"] / t["h1"])
    ln = bi.lahan_nyata()
    return {"tahap_rata": n_rata, "tahap_maks": n_maks, "bulan_per_tahap": tu["t_pvd_bulan"],
            "durasi_rata": n_rata * tu["t_pvd_bulan"], "durasi_maks": n_maks * tu["t_pvd_bulan"],
            "biaya": ln["total"], "pvd_m": ln["item"][1][1]}


# ------------------------------------------------------------------ uji tiang (SNI 8460:2017 Pasal 9.8)
def uji_tiang():
    o = fd.opsi("A", per_zona=True)
    n = o["n_utama"] + o["n_gu"]
    statik = max(1, math.ceil(n / 75))  # 9.8.1 a) tiang bor: 1 per 75 tiang
    statik = max(statik, math.ceil(0.01 * n))  # tambahan N ≤ 1000: 1 %
    pra = math.ceil(0.6 * statik)  # 60 % boleh sebelum konstruksi
    izin = max(fd.beban_izin("BOR-800", z)["izin"] for z in fd.PROFIL)
    csl = math.ceil(n / 20)  # 9.8.5: 1 per 20 tiang
    biaya = (pra * HARGA_UJI["statik_instrumen"] + (statik - pra) * HARGA_UJI["statik"] + HARGA_UJI["lateral"]
             + csl * HARGA_UJI["csl"])
    trial_v2 = 3  # tiang spun percobaan di zona barat untuk V2 + PDA [Asumsi], dikorelasikan dengan 1 uji statik
    biaya_v2 = trial_v2 * HARGA_UJI["pda"] + HARGA_UJI["statik"] + \
        trial_v2 * fd.kapasitas("SPUN-600")["panjang"] * fd.TIANG["SPUN-600"]["harga_m"]
    return {"n_tiang": n, "statik": statik, "pra": pra, "konstruksi": statik - pra, "lateral": 1, "csl": csl,
            "beban_uji": 2.0 * izin, "batas_deformasi_mm": 25.0, "biaya": biaya * bi.FAKTOR_NYATA,
            "trial_v2": trial_v2, "biaya_v2": biaya_v2 * bi.FAKTOR_NYATA}


def ringkasan():
    return {"gudang": ringkas_gudang(), "timbunan": timbunan(), "urugan": paket_urugan(), "uji": uji_tiang()}


def fmt(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


# ------------------------------------------------------------------ Excel
def buat_excel(keluar=BERKAS):
    import openpyxl

    from format_dokumen import AI, Lembar, set_font_bawaan

    r = ringkasan()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk gudang, urugan, uji tiang (LA.5)", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        "Tindak lanjut evaluasi kunci Tahap 3 no. 8 dan rapat konsep no. 2, 10, 11, 12.",
        "Klaim gudang: data survei kondisi awal 2.7 (patok sejak 3 Des 2026, pengukur retak sejak 3 Des 2026, inventaris "
        "retak) dibanding uji pompa PW-1 mulai 8 Des 2026 selama 3 hari (2.3).",
        "Uji tiang: SNI 8460:2017 Pasal 9.8, 9.8.1 (hal. 188-189), 9.8.3, 9.8.4, 9.8.5 (hal. 189-190).",
        "Urugan bertahap: tebal per tahap h1 dan waktu per tahap dengan PVD dari 2.8/3.3.",
        "Harga uji tiang dan frekuensi uji mutu urugan [Asumsi]; acuan metode uji tanah belum ada di acuan.",
        "Tanggapan tertulis kepada yayasan: '10 Laporan/Tanggapan Teknis Klaim Gudang Timur.docx'.",
    ])], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Gudang"), 2, "Patok penurunan gudang per periode (mm)", [10, 16, 14, 14, 14, 12, 50])
    lb.catatan(LABEL + " Ketelitian sipat datar ±0,5 mm (Survei Gudang Timur lembar 4). Uji pompa 8-11 Des 2026.")
    tgl, pk = patok_per_periode()
    lb.tabel(["Patok", "3 Des-6 Jan (uji pompa)", "6 Jan-3 Feb", "3 Feb-3 Mar", "3-31 Mar", "Total", "Catatan"],
             [[p["patok"], round(p["uji_pompa"], 1), round(p["jan_feb"], 1), round(p["feb_mar"], 1), round(p["mar"], 1),
               round(p["total"], 1), p["catatan"][:80]] for p in pk], rata=list("ccccccl"),
             fmt=[None, "0.0", "0.0", "0.0", "0.0", "0.0", None], fill_kolom={1: AI})
    lb.kosong()
    g = r["gudang"]
    lb.tabel(["Butir", "Nilai", "", "", "", "", "Keterangan"], [
        ["Jarak PW-1 ke dinding barat gudang (m)", round(g["tarikan"]["r"]), "", "", "", "", "PW-1 (65, 40)"],
        ["Penurunan tinggi tekan U5 di gudang (m)", round(g["tarikan"]["s"], 2), "", "", "", "",
         "maks(Thiem OW-1/OW-2, sumur bayangan sungai) (T-63)"],
        ["Lama pemompaan (hari)", round(g["tarikan"]["lama_hari"], 1), "", "", "", "", "lalu pulih dalam ±4 jam"],
        ["Batas atas penurunan U4 akibat pompa (mm)", round(g["penurunan"]["penurunan_mm"], 2), "", "", "", "",
         "δ = 2√(cv t), Δσ' = γw s, NC; setara ketelitian patok ±0,5 mm"],
        ["Perubahan patok periode uji pompa, maks (mm)", round(g["maks_periode_pompa"], 1), "", "", "", "",
         "setara derau ukur ±0,5-2 mm; naik-turun tidak searah"],
        ["Rata-rata perubahan 3 Feb-3 Mar (mm)", round(g["rata_feb_mar"], 1), "", "", "", "",
         "penurunan merata seluruh gudang setelah surut banjir, bukan terpusat di sisi PW-1"],
        ["Retak lama", ", ".join(g["retak_lama"]), "", "", "", "", "ditambal 2018, terbuka kembali (inventaris 2.7)"],
        ["Pengukur retak 3 Des 2026-31 Mar 2027", "±0,05 mm", "", "", "", "", "dalam ketelitian ±0,1 mm: tidak bergerak"],
        ["Batas muka air sisi gudang selama konstruksi", "+8,60", "", "", "", "", "kepala cerucuk +8,62 (galian uji)"],
    ], rata=list("lc") + ["c"] * 4 + ["l"], fill_kolom={1: AI}, beku=False)

    lb = Lembar(wb.create_sheet("Urugan"), 3, "Timbunan sementara dan paket awal urugan + PVD", [56, 18, 56])
    lb.catatan(LABEL)
    t, u = r["timbunan"], r["urugan"]
    lb.tabel(["Butir", "Nilai", "Keterangan"], [
        ["Tebal urugan per tahap h1 (m)", round(t["h1"], 2), "2.8: stabilitas lempung lunak (FHWA Pers. 7-11)"],
        ["Luas urugan (m²)", round(t["luas"]), "3.3, di luar sempadan; penyangga ≤ 1,0 m"],
        ["Kapasitas tahap 1 (m³)", round(t["kapasitas_tahap1"]), "setelah PVD terpasang"],
        ["Tanah gratis yang dapat diterima (m³)", round(min(TANAH_GRATIS, t["kapasitas_tahap1"])), "sebagai urugan tahap 1"],
        ["Sisa yang tidak dapat ditimbun di lokasi (m³)", round(t["sisa_ditolak"]), "timbunan di luar lokasi atau ditolak"],
        ["Set uji mutu tanah merah", t["set_uji"], "1 set per 1.000 m³: gradasi, batas Atterberg, kadar air, pemadatan [Asumsi]"],
        ["Tebal urugan rata-rata / maksimum (m)", f"{fmt(t['tebal_rata'])} / {fmt(t['tebal_maks'])}", "3.3, termasuk kompensasi"],
        ["Jumlah tahap rata-rata / maksimum", f"{u['tahap_rata']} / {u['tahap_maks']}", "tebal / h1"],
        ["Waktu per tahap dengan PVD (bulan)", round(u["bulan_per_tahap"], 1), "2.8"],
        ["Durasi urugan rata-rata / maksimum (bulan)", f"{fmt(u['durasi_rata'], 0)} / {fmt(u['durasi_maks'], 0)}",
         "gedung bertiang dapat dibangun paralel di atas platform tahap 1"],
        ["Panjang PVD (m)", round(u["pvd_m"]), "3.8"],
        ["Biaya paket awal urugan + PVD (juta Rp)", round(u["biaya"]), "3.8 dengan BTL dan PPN"],
    ], rata=list("lcl"), fill_kolom={1: AI})

    lb = Lembar(wb.create_sheet("Uji Tiang"), 4, "Program uji tiang (SNI 8460:2017 Pasal 9.8)", [56, 18, 56])
    lb.catatan(LABEL)
    j = r["uji"]
    lb.tabel(["Butir", "Nilai", "Keterangan"], [
        ["Jumlah tiang bor Ø800 (LA.1)", j["n_tiang"], "opsi A per zona"],
        ["Uji tekan statik", j["statik"], "1 per 75 tiang bor (9.8.1 a), ≥ 1 % (hal. 188)"],
        ["- sebelum konstruksi (≤ 60 %)", j["pra"], "terinstrumentasi: tiang bor > 30 m dianjurkan (hal. 189)"],
        ["- saat konstruksi (≥ 40 %)", j["konstruksi"], "lokasi pelaksanaan terburuk"],
        ["Beban uji (kN)", round(j["beban_uji"]), "≥ 200 % beban rencana (9.8 e)"],
        ["Batas deformasi pada 200 % (mm)", j["batas_deformasi_mm"], "D ≤ 80 cm (hal. 189)"],
        ["Uji lateral", j["lateral"], "bangunan tanpa basement (9.8.3 a)"],
        ["Uji integritas CSL", j["csl"], "1 per 20 tiang bor (9.8.5)"],
        ["Biaya program uji tiang bor (juta Rp)", round(j["biaya"]), "[Asumsi harga]"],
        ["V2: tiang spun percobaan + PDA", j["trial_v2"], "PDA hanya pembanding; 1 uji statik untuk korelasi (9.8.4)"],
        ["Biaya uji V2 (juta Rp)", round(j["biaya_v2"]), "[Asumsi]; dana yayasan (rapat konsep)"],
    ], rata=list("lcl"), fill_kolom={1: AI})
    wb.save(keluar)
    return keluar


# ------------------------------------------------------------------ memo Word
def buat_memo(keluar=MEMO):
    from format_dokumen import Laporan, perbarui_word

    g = ringkas_gudang()
    _, pk = patok_per_periode()
    lap = Laporan()
    lap.bab("", "Tanggapan Teknis atas Klaim Pemilik Gudang Timur", mulai_arab=True)
    lap.bab_aktif = "1"
    lap.paragraf("*DOKUMEN SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa sebagai bahan bagi "
                 "yayasan (rapat konsep 5 April 2027, tindak lanjut no. 12). Disetujui Defsa 19 Nov 2026. Surat resmi "
                 "kepada pemilik gudang dikirim yayasan.*", inden=False)
    lap.subbab("1.1", "Klaim")
    lap.paragraf("Kuasa pemilik gudang menyatakan gudang retak sejak uji pompa Desember 2026, meminta ganti rugi sebelum "
                 "proyek dimulai, dan meminta tidak ada galian di sisi timur.")
    lap.subbab("1.2", "Data yang Tersedia")
    lap.daftar([
        "Survei kondisi awal gudang dengan izin pemilik (2.7): inventaris retak, elevasi lantai, patok penurunan pada 3 Des "
        "2026, 6 Jan, 3 Feb, 3 Mar, dan 31 Mar 2027, pengukur retak sejak 3 Des 2026, galian uji pondasi.",
        "Uji pompa PW-1 di (65, 40) mulai 8 Des 2026, debit ±4,0 L/s selama 3 hari, dengan sumur pantau OW-1 dan OW-2 (2.3).",
    ])
    lap.subbab("1.3", "Penilaian")
    lap.daftar([
        f"Penurunan tinggi tekan akuifer pasir di dinding barat gudang ({fmt(g['tarikan']['r'], 0)} m dari PW-1) paling "
        f"besar ±{fmt(g['tarikan']['s'])} m selama {fmt(g['tarikan']['lama_hari'], 0)} hari, lalu pulih dalam ±4 jam. Akuifer "
        "berada 10-19 m di bawah muka tanah, dipisahkan dari cerucuk (kepala +8,62) oleh lempung lunak ±8 m.",
        f"Batas atas penurunan lempung akibat pemompaan itu ±{fmt(g['penurunan']['penurunan_mm'])} mm (lempung dianggap "
        "terkonsolidasi normal), setara ketelitian sipat datar ±0,5 mm dan terlalu kecil untuk menimbulkan retak dinding.",
        f"Perubahan patok pada periode yang mencakup uji pompa (3 Des-6 Jan) paling besar {fmt(g['maks_periode_pompa'], 1)} mm "
        "dengan arah naik dan turun bergantian, setara derau pengukuran.",
        f"Penurunan baru terukur pada 3 Feb-3 Mar 2027 (rata-rata {fmt(g['rata_feb_mar'], 1)} mm), merata di seluruh gudang "
        "setelah surut banjir Januari, bukan terpusat di sisi terdekat PW-1. Laju Des 2026-Mar 2027 0,3-1,9 mm/bulan (2.7), "
        "terbesar sesudah surut banjir.",
        "Retak R-2 dan R-4 tercatat sudah ditambal pada 2018 lalu terbuka kembali. Pengukur retak yang dipasang 3 Des 2026, "
        "sebelum uji pompa, tidak bergerak (±0,05 mm, ketelitian ±0,1 mm).",
    ])
    lap.subbab("1.4", "Kesimpulan dan Usulan")
    lap.daftar([
        "Data kondisi awal tidak menunjukkan retak atau penurunan yang disebabkan uji pompa Desember 2026.",
        "Desain konsep tidak memakai galian dalam: basement ditolak (3.5) dan tiang di dekat gudang adalah tiang bor tanpa "
        "getaran (3.7).",
        "Selama konstruksi: muka air di sisi gudang dijaga tidak lebih rendah dari +8,60 (kepala cerucuk +8,62), dipantau "
        "dengan piezometer dan patok yang sama.",
        "Yayasan mengundang pemilik gudang ke survei kondisi awal bersama yang ditandatangani kedua pihak, sebagai dasar "
        "setiap klaim berikutnya.",
    ])
    lap.subbab("1.5", "Data Patok")
    lap.tabel("Perubahan Elevasi Patok Gudang per Periode (mm)", ["Patok", "3 Des-6 Jan", "6 Jan-3 Feb", "3 Feb-3 Mar",
                                                                  "3-31 Mar", "Total"],
              [[p["patok"], fmt(p["uji_pompa"], 1), fmt(p["jan_feb"], 1), fmt(p["feb_mar"], 1), fmt(p["mar"], 1),
                fmt(p["total"], 1)] for p in pk], [2.0, 2.4, 2.4, 2.4, 2.4, 2.0], rata=list("cccccc"),
              sumber="Survei Gudang Timur (2.7); GT-7 dikoreksi karena kepala patok bengkok.")
    lap.simpan(keluar)
    ok, pesan = perbarui_word(keluar)
    return keluar, ok


def buat():
    buat_excel()
    return buat_memo()


if __name__ == "__main__":
    r = ringkasan()
    for k, v in r.items():
        print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items() if not isinstance(b, dict)})
    print(r["gudang"]["tarikan"], r["gudang"]["penurunan"])
