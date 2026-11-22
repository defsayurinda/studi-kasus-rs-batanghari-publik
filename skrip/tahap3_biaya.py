"""Langkah 3.8: perkiraan biaya konstruksi fisik per komponen terhadap pagu Rp 168 M dan opsi pengurangan lingkup.

Acuan (halaman PDF): Permen PUPR 22/2018 (acuan/publik) hal. 21 Pasal 21 ayat (3)-(7) (biaya standar = luas ×
koefisien jumlah lantai × harga satuan tertinggi; biaya nonstandar menurut kebutuhan nyata, paling banyak 150 % biaya
standar); hal. 28 Pasal 27 ayat (6) (persentase komponen standar: fondasi 5-10 %, struktur 25-35 %, lantai 5-10 %,
dinding 7-10 %, plafon 6-8 %, atap 8-10 %, utilitas 5-8 %, perampungan 10-15 %), hal. 29 Pasal 27 ayat (8) (biaya
standar sudah termasuk overhead, asuransi, K3, inflasi, pajak); hal. 29-30 Pasal 28 (jenis pekerjaan nonstandar);
hal. 30-32 Pasal 29 ayat (1) (persentase nonstandar terhadap biaya standar); hal. 34-36 Pasal 30 ayat (6)-(7) dan
Pasal 31 ayat (2) (koefisien fungsi ruang). Permen PUPR 8/2023 hal. 9 Pasal 11 ayat (3) (biaya tidak langsung 10-15 %
dari biaya langsung). Volume dari langkah 3.3 (urugan), 3.4 (luas), 3.6 (struktur sistem ganda), 3.7 (tiang opsi A).

Belum ada di acuan, jadi berlabel [Asumsi]: harga satuan tertinggi (HSBGN) Kota Jambi 2026 (ditetapkan wali kota,
Pasal 30 ayat (7)), koefisien jumlah lantai (Keputusan Menteri, Pasal 21 ayat (5)), tarif PPN, harga satuan
pekerjaan (survei harga SE 47/2026 Lampiran I belum dilakukan). Indeks IKK BPS 2025 Kota Jambi 95,03 (Surabaya 100)
dipakai untuk kalibrasi setelah HSBGN kota acuan didapat. Owner berupa yayasan (bukan bangunan gedung negara), jadi
Permen 22/2018 dipakai sebagai pedoman cara hitung, bukan batas yang mengikat.
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 19 Nov 2026.
"""
import math
from pathlib import Path

import tahap3_peil as pl
import tahap3_pondasi as fd
import tahap3_program as pr
import tahap3_struktur as st

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "03 Desain Konsep"
BERKAS = KELUAR / "3.8 Perkiraan Biaya.xlsx"
PDF = KELUAR / "3.8 Gambar Opsi Pengurangan Lingkup.pdf"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = "DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026."

# ------------------------------------------------------------------ parameter (juta Rp)
PAGU = 168_000.0  # TOR butir 6, termasuk PPN
PAGU_LUAS, PAGU_HARGA = 12_000.0, 14.0  # dasar pagu owner (TOR butir 6)
HSBGN = 7.0  # juta Rp/m² bangunan tidak sederhana [Asumsi: SK wali kota Jambi 2026 belum ada di acuan]
KL = {"UTAMA": 1.197, "GU": 1.135}  # koefisien jumlah lantai 6 dan 4 lantai [Asumsi: Keputusan Menteri belum ada]
KOEF_PARKIR = 0.7  # dek parkir tanpa dinding/plafon [Asumsi: Pasal 31 tidak mengatur; antara teras 0,5 dan 1,0]
BTL = 0.12  # biaya tidak langsung (Permen PUPR 8/2023 Pasal 11 ayat (3): 10-15 %)
PPN = 0.11  # [Asumsi: tarif efektif; UU HPP belum ada di acuan]
KONTINJENSI = 0.05  # [Asumsi: cadangan tahap konsep; tidak diatur Permen 22/2018]
LUAS_PER_MOBIL = 30.0  # m² per mobil di gedung parkir (langkah 3.5)

# Persentase komponen standar (Pasal 27 ayat (6), nilai tengah dipakai untuk pembanding kebutuhan nyata)
STANDAR_KOMPONEN = {"fondasi": (0.05, 0.10), "struktur": (0.25, 0.35), "lantai": (0.05, 0.10),
                    "dinding": (0.07, 0.10), "plafon": (0.06, 0.08), "atap": (0.08, 0.10),
                    "utilitas": (0.05, 0.08), "perampungan": (0.10, 0.15)}

# Harga satuan biaya langsung [Asumsi sampai survei harga]; struktur memakai indeks langkah 3.6
HARGA = {
    "beton_m3": st.HARGA["beton_m3"], "bekisting_m3": st.HARGA["bekisting_m3"], "besi_ton": st.HARGA["besi_ton"],
    "urugan_m3": 0.22,  # tanah urug pilihan didatangkan, dihampar, dipadatkan per m³ padat
    "pvd_m": 0.012,  # PVD terpasang per m
    "pasir_m3": 0.30,  # hamparan pasir drainase
    "pemantauan": 600.0,  # pelat penurunan, piezometer, inklinometer (lumpsum)
    "dermaga": 3_500.0,  # dermaga ponton ambulans air + jembatan gerak + teras pandang (lumpsum)
    "kaca_lebih_m2": 2.5,  # selisih dinding tirai kaca terhadap dinding + jendela standar per m² bukaan
}
PVD_JARAK, PVD_PANJANG = 1.2, 10.5  # segitiga 1,2 m (2.8); dasar U4 9,46 m + 1 m di urugan
PASIR_TEBAL = 0.5
PILECAP_PER_TIANG = 4.5  # m³ beton pile cap per tiang Ø800 (jarak 3D) [Asumsi]
PELAT_LT1 = 0.30  # m³/m² pelat lantai dasar struktural + balok sloof (lantai dasar di atas tiang) [Asumsi]
BESI_KG = {"pelat_lt1": 110.0, "pilecap": 100.0}  # kg/m³ [Asumsi]
WWR = 0.60  # rasio bukaan kaca fasad keinginan owner ("banyak kaca") [Asumsi]
WWR_VE = 0.35

# Koefisien fungsi ruang (Permen PUPR 22/2018 Pasal 31 ayat (2)); kata kunci di nama ruang, urutan menentukan
KOEF = [
    (("drop-off",), 0.5, "m (teras beratap)"),
    (("kamar operasi", "persiapan dan pemulihan", "koridor steril"), 2.0, "c (ruang operasi)"),
    (("cssd", "ruang ganti petugas"), 1.5, "b (CMU) [tafsiran]"),
    (("icu", "hcu", "nicu", "isolasi tekanan"), 1.5, "b (ICU/NICU)"),
    (("radiologi",), 1.25, "d (radiologi)"),
    (("laboratorium", "bank darah"), 1.1, "f (laboratorium)"),
    (("bersalin", "kebidanan"), 1.2, "g (kebidanan)"),
    (("dapur", "laundry"), 1.1, "k (dapur, laundri)"),
    (("genset", "trafo", "pompa"), 1.25, "i (power house)"),
    (("bengkel", "ipsrs"), 1.0, "l (bengkel)"),
    (("ahu", "shaft"), 1.0, "- (ruang mesin) [Asumsi]"),
    (("ruang tunggu keluarga",), 1.0, "- (ruang tunggu)"),
]
KOEF_KELOMPOK = {"Gawat Darurat": (1.5, "b (IGD)"), "Rawat Inap": (1.1, "e (rawat inap)"),
                 "Rawat Jalan": (1.1, "j (rawat jalan)"), "Penunjang Medik": (1.0, "- (penunjang)"),
                 "Penunjang Umum": (1.0, "- (umum)"), "Administrasi": (1.0, "- (kantor)"),
                 "Utilitas (gedung utilitas)": (1.0, "- (gudang)")}
KOEF_RUANG_KHUSUS = {"Hemodialisis (10 kursi)": (1.1, "j (rawat jalan) [tafsiran]"),
                     "Rehabilitasi medik": (1.1, "j (rawat jalan) [tafsiran]")}

# Nonstandar Pasal 29 ayat (1): (kode, uraian, huruf, min, maks, nilai pakai, alasan nilai pakai)
NONSTANDAR = [
    ("AC", "Alat pengondisian udara", "a", 0.07, 0.15, 0.15, "RS: ruang bersih OK, tekanan negatif, AHU per lantai"),
    ("LIF", "Lift", "b", 0.08, 0.14, 0.12, "lift brankar, lift penumpang, lift barang; 6 lantai"),
    ("SUARA", "Tata suara (paging, nurse call)", "c", 0.02, 0.04, 0.03, "nurse call di rawat inap"),
    ("PABX", "Telepon dan PABX", "d", 0.01, 0.03, 0.02, "-"),
    ("TI", "Instalasi informasi dan teknologi", "e", 0.06, 0.11, 0.08, "jaringan SIMRS, ruang server"),
    ("LISTRIK", "Elektrikal termasuk genset", "f", 0.07, 0.12, 0.12, "genset cadangan penuh, UPS ruang kritis"),
    ("KEBAKARAN", "Sistem proteksi kebakaran", "g", 0.07, 0.12, 0.10, "sprinkler, hidran, alarm, ruang aman"),
    ("PETIR", "Penangkal petir khusus", "h", 0.01, 0.02, 0.015, "-"),
    ("IPAL", "Instalasi pengolahan air limbah", "i", 0.01, 0.02, 0.02, "limbah medis cair"),
    ("INTERIOR", "Interior termasuk furnitur", "j", 0.15, 0.25, 0.15, "nilai bawah; furnitur medis di anggaran alkes"),
    ("GAS", "Gas pembakaran", "k", 0.01, 0.02, 0.01, "dapur gizi"),
    ("GASMEDIS", "Gas medis", "l", 0.02, 0.04, 0.04, "O2, vakum, udara tekan ke OK, ICU, rawat inap"),
    ("RAYAP", "Pencegahan bahaya rayap", "m", 0.01, 0.03, 0.01, "-"),
    ("DIFABEL", "Fasilitas penyandang disabilitas", "o", 0.03, 0.05, 0.03, "-"),
    ("LINGKUNGAN", "Sarana dan prasarana lingkungan", "p", 0.03, 0.08, 0.05,
     "jalan, drainase, kolam retensi 650 m³, lansekap, pagar"),
    ("IZIN", "Perizinan selain IMB (dokumen SLF)", "r", 0.0, 0.01, 0.01, "-"),
    ("SAMBUNG", "Penyambungan utilitas", "u", 0.0, 0.02, 0.02, "PLN tegangan menengah, PDAM, saluran kota"),
]
NONSTANDAR_PARKIR = [("LISTRIK", 0.07), ("KEBAKARAN", 0.07)]  # dek parkir: nilai bawah huruf f dan g


def _bulat(x):
    return round(x, 6)


# ------------------------------------------------------------------ luas dan biaya standar
def luas_massa():
    m = {r["massa"]: r for r in pr.cek_massa()["massa"]}
    utama = m["PODIUM"]["luas"] * m["PODIUM"]["lantai"] + m["MENARA"]["luas"] * m["MENARA"]["lantai"]
    gu = m["GEDUNG UTILITAS"]["luas"] * m["GEDUNG UTILITAS"]["lantai"]
    return {"UTAMA": utama, "GU": gu, "total": utama + gu, "gu_lantai": m["GEDUNG UTILITAS"]["luas"]}


def koef_ruang(ruang, kelompok):
    if ruang in KOEF_RUANG_KHUSUS:
        return KOEF_RUANG_KHUSUS[ruang]
    r = ruang.lower()
    for kunci, k, dasar in KOEF:
        if any(s in r for s in kunci):
            return k, dasar
    return KOEF_KELOMPOK[kelompok]


def luas_fungsi():
    """Baris luas bruto per ruang (luas bersih × faktor bruto 3.4) dengan koefisien fungsi, ditambah sisa massa."""
    baris = []
    for r in pr.program_konsultan():
        if r["lantai"] == "HALAMAN":
            continue  # IPAL di halaman: masuk nonstandar huruf i
        k, dasar = koef_ruang(r["ruang"], r["kelompok"])
        massa = "GU" if r["lantai"] == "GU" else "UTAMA"
        baris.append({"lantai": r["lantai"], "ruang": r["ruang"], "kelompok": r["kelompok"], "massa": massa,
                      "bersih": r["bersih"], "bruto": r["bersih"] * pr.FAKTOR_BRUTO, "k": k, "dasar": dasar})
    lm = luas_massa()
    sisa_utama = lm["UTAMA"] - sum(b["bruto"] for b in baris if b["massa"] == "UTAMA")
    sisa_gu = lm["GU"] - sum(b["bruto"] for b in baris if b["massa"] == "GU")
    baris.append({"lantai": "LT1-LT6", "ruang": "Ruang belum terprogram (selisih massa 3.4 terhadap program)",
                  "kelompok": "Sisa massa", "massa": "UTAMA", "bersih": 0.0, "bruto": sisa_utama, "k": 1.0,
                  "dasar": "- (umum)"})
    baris.append({"lantai": "GU LT1-LT4", "ruang": "Dek parkir gedung utilitas + parkir", "kelompok": "Parkir",
                  "massa": "GU", "bersih": 0.0, "bruto": sisa_gu, "k": KOEF_PARKIR, "dasar": "- [Asumsi]"})
    for b in baris:
        b["biaya"] = b["bruto"] * b["k"] * KL[b["massa"]] * HSBGN
    return baris


def standar(hsbgn=HSBGN):
    f = hsbgn / HSBGN
    bs = luas_fungsi()
    utama = sum(b["biaya"] for b in bs if b["massa"] == "UTAMA") * f
    parkir = sum(b["biaya"] for b in bs if b["kelompok"] == "Parkir") * f
    gu = sum(b["biaya"] for b in bs if b["massa"] == "GU" and b["kelompok"] != "Parkir") * f
    return {"UTAMA": utama, "GU": gu, "PARKIR": parkir, "bangunan": utama + gu, "total": utama + gu + parkir,
            "luas_parkir": sum(b["bruto"] for b in bs if b["kelompok"] == "Parkir")}


# ------------------------------------------------------------------ kebutuhan nyata (biaya langsung → dengan BTL dan PPN)
FAKTOR_NYATA = (1 + BTL) * (1 + PPN)


def _beton(vol, besi_ton):
    return vol * (HARGA["beton_m3"] + HARGA["bekisting_m3"]) + besi_ton * HARGA["besi_ton"]


def struktur_nyata():
    """Struktur atas gedung utama (sistem ganda 3.6), gedung utilitas + parkir (rasio SRPMK 3.6), pelat lantai dasar."""
    g = st.volume("GANDA")
    s = st.volume("SRPMK")
    luas_str = 3 * pr.poligon("PODIUM").area + 3 * pr.poligon("MENARA").area
    lm = luas_massa()
    v_gu = s["beton"] / luas_str * lm["GU"]
    besi_gu = s["besi_ton"] / s["beton"] * v_gu
    luas_lt1 = pr.poligon("PODIUM").area + lm["gu_lantai"]
    v_lt1 = PELAT_LT1 * luas_lt1
    item = [
        ("Struktur atas gedung utama, sistem ganda (3.6)", g["beton"], g["besi_ton"], _beton(g["beton"], g["besi_ton"])),
        ("Struktur gedung utilitas + parkir (rasio SRPMK 3.6)", v_gu, besi_gu, _beton(v_gu, besi_gu)),
        ("Pelat lantai dasar struktural + sloof", v_lt1, v_lt1 * BESI_KG["pelat_lt1"] / 1000,
         _beton(v_lt1, v_lt1 * BESI_KG["pelat_lt1"] / 1000)),
    ]
    langsung = sum(i[3] for i in item)
    return {"item": item, "langsung": langsung, "total": langsung * FAKTOR_NYATA}


def fondasi_nyata(kunci="A"):
    o = fd.opsi(kunci)
    n = o["n_utama"] + o["n_gu"]
    v = n * PILECAP_PER_TIANG
    besi = v * BESI_KG["pilecap"] / 1000
    item = [(f"Tiang opsi {kunci}: {o['nama']} ({n} tiang, 3.7)", n, None, o["biaya"]),
            ("Pile cap", v, besi, _beton(v, besi))]
    langsung = sum(i[3] for i in item)
    return {"item": item, "langsung": langsung, "total": langsung * FAKTOR_NYATA, "n": n}


def lahan_nyata(halaman=12.05):
    vu = pl.volume_urugan(halaman)
    luas = vu["luas"]
    pvd_m = luas / (math.sqrt(3) / 2 * PVD_JARAK ** 2) * PVD_PANJANG
    pasir = PASIR_TEBAL * luas
    item = [("Urugan dipadatkan (3.3)", vu["v_padat"], "m³ padat", vu["v_padat"] * HARGA["urugan_m3"]),
            ("PVD segitiga 1,2 m sampai dasar U4", pvd_m, "m", pvd_m * HARGA["pvd_m"]),
            ("Hamparan pasir drainase 0,5 m", pasir, "m³", pasir * HARGA["pasir_m3"]),
            ("Pemantauan penurunan dan tekanan air pori", 1, "ls", HARGA["pemantauan"])]
    langsung = sum(i[3] for i in item)
    return {"item": item, "langsung": langsung, "total": langsung * FAKTOR_NYATA, "luas": luas}


def luas_fasad():
    pd, mn = pr.MASSA["PODIUM"], pr.MASSA["MENARA"]
    kel_pod = 2 * ((pd["x"][1] - pd["x"][0]) + (pd["y"][1] - pd["y"][0]))
    kel_men = 2 * ((mn["x"][1] - mn["x"][0]) + (mn["y"][1] - mn["y"][0]))
    return kel_pod * (4.5 + 4.5 + 4.2) + kel_men * (4.2 * 3)


def fasad_nyata(wwr=WWR):
    return luas_fasad() * wwr * HARGA["kaca_lebih_m2"] * FAKTOR_NYATA


def dermaga_nyata():
    return HARGA["dermaga"] * FAKTOR_NYATA


# ------------------------------------------------------------------ rekap
def persen_nonstandar(kolom="pakai"):
    i = {"min": 3, "maks": 4, "pakai": 5}[kolom]
    return sum(n[i] for n in NONSTANDAR)


def rekap(kolom="pakai", hsbgn=HSBGN, fondasi="A"):
    s = standar(hsbgn)
    ns_bangunan = persen_nonstandar(kolom) * s["bangunan"]
    ns_parkir = sum(p for _, p in NONSTANDAR_PARKIR) * s["PARKIR"]
    fnd, strk, lhn = fondasi_nyata(fondasi), struktur_nyata(), lahan_nyata()
    fnd_std = sum(STANDAR_KOMPONEN["fondasi"]) / 2 * s["total"]
    str_std = sum(STANDAR_KOMPONEN["struktur"]) / 2 * s["total"]
    fondasi_dalam = max(0.0, fnd["total"] - fnd_std)
    peningkatan_str = max(0.0, strk["total"] - str_std)
    baris = [
        ("Biaya standar gedung utama", s["UTAMA"], "Pasal 21 (4), 31"),
        ("Biaya standar gedung utilitas", s["GU"], "Pasal 21 (4), 31"),
        ("Biaya standar dek parkir", s["PARKIR"], "Pasal 21 (4) [Asumsi koef 0,7]"),
        ("Nonstandar M/E dan kelengkapan (Pasal 29 a-u)", ns_bangunan, "Pasal 29 (1)"),
        ("Nonstandar dek parkir (elektrikal, kebakaran)", ns_parkir, "Pasal 29 (1) f, g"),
        ("Fondasi dalam: kebutuhan nyata dikurangi porsi fondasi standar", fondasi_dalam, "Pasal 28 (3) n, 21 (6)"),
        ("Peningkatan struktur (kategori IV, KDS D)", peningkatan_str, "Pasal 28 (2) c"),
        ("Penyiapan dan pematangan lahan: urugan, PVD", lhn["total"], "Pasal 28 (3) s, 21 (6)"),
        ("Peningkatan arsitektur: fasad kaca", fasad_nyata(), "Pasal 28 (2) b"),
        ("Dermaga ambulans air dan teras pandang", dermaga_nyata(), "Pasal 33 (2) [Asumsi]"),
    ]
    subtotal = sum(b[1] for b in baris)
    kont = KONTINJENSI * subtotal
    total = subtotal + kont
    nonstandar = subtotal - s["total"]
    lm = luas_massa()
    return {"baris": baris, "standar": s, "subtotal": subtotal, "kontinjensi": kont, "total": total,
            "nonstandar": nonstandar, "rasio_nonstandar": nonstandar / s["total"],
            "fondasi_std": fnd_std, "fondasi_nyata": fnd["total"], "struktur_std": str_std,
            "struktur_nyata": strk["total"], "lahan": lhn["total"], "lahan_batas": 0.035 * s["total"],
            "selisih": total - PAGU, "rasio_pagu": total / PAGU, "per_m2": total / lm["total"],
            "metode_owner": PAGU_HARGA * lm["total"], "luas": lm["total"]}


def faktor_bangunan():
    """Pengali biaya standar per m² untuk bagian yang ikut menanggung nonstandar M/E, plus kontinjensi."""
    return (1 + persen_nonstandar()) * (1 + KONTINJENSI)


def rekayasa_nilai():
    r = rekap()
    k = 1 + KONTINJENSI
    m2_utama = KL["UTAMA"] * HSBGN
    lm = luas_massa()
    fa, fc = fondasi_nyata("A"), fondasi_nyata("C")
    luas_v1 = 48.0 * 24.0  # LT3 podium utara di luar menara: x 36-84, y 51-75 (lihat GK-08)
    lt6 = pr.poligon("MENARA").area
    ditunda_std = sum(STANDAR_KOMPONEN[c][0] + STANDAR_KOMPONEN[c][1] for c in ("lantai", "plafon", "perampungan")) / 2
    ditunda_ns = sum(n[5] for n in NONSTANDAR if n[0] in ("AC", "INTERIOR", "GASMEDIS", "SUARA", "TI"))
    v_hijau = (pl.volume_urugan(12.05)["v_padat"] - pl.volume_urugan(11.50)["v_padat"])
    import tahap3_basement as bs
    hijau = bs.cek_kdh()["hijau"] / lahan_nyata()["luas"]
    mobil_lt4 = int(lm["gu_lantai"] / LUAS_PER_MOBIL)
    mobil = bs.opsi()[2]["mobil"]
    opsi = [
        {"kode": "V1", "uraian": "Rampingkan podium LT3: bagian utara di luar menara (±1.152 m²) tidak dibangun",
         "hemat": luas_v1 * 1.0 * m2_utama * faktor_bangunan(),
         "akibat": "Sisa LT3 2.304 m² ≥ program LT3 2.294 m²; zonasi LT3 disusun ulang (3.4 rev)."},
        {"kode": "V2", "uraian": "Fondasi opsi C hibrida (spun Ø600 di gedung utama) setelah uji tiang",
         "hemat": (fa["total"] - fc["total"]) * k,
         "akibat": "Syarat: uji pancang + PDA menembus U6, pemantauan getaran; pancang ≥ 60 m dari gudang."},
        {"kode": "V3", "uraian": "Dermaga ambulans air dan teras pandang ditunda ke tahap 2",
         "hemat": dermaga_nyata() * k,
         "akibat": "Jalur dari sungai tetap disiapkan; izin sempadan dan kajian tebing dulu (zona labil 3.2)."},
        {"kode": "V4", "uraian": f"Bukaan kaca fasad {WWR_VE:.0%} (dari {WWR:.0%}) dengan sirip peneduh",
         "hemat": (fasad_nyata(WWR) - fasad_nyata(WWR_VE)) * k,
         "akibat": "Tampak tetap 'tepian sungai'; beban AC turun; perlu persetujuan owner (keinginan 8)."},
        {"kode": "V5", "uraian": "Lantai 4 gedung parkir ditunda (dek parkir 3 lantai)",
         "hemat": lm["gu_lantai"] * KOEF_PARKIR * KL["GU"] * HSBGN * (1 + sum(p for _, p in NONSTANDAR_PARKIR)) * k,
         "akibat": f"Mobil berkurang ±{mobil_lt4} ({mobil} → {mobil - mobil_lt4}) < 120 yang diminta; kolom disiapkan."},
        {"kode": "V6", "uraian": "LT6 rawat inap dibangun cangkang dan inti; fit-out tahap 2",
         "hemat": lt6 * 1.1 * m2_utama * (ditunda_std + ditunda_ns) * k,
         "akibat": "Saat dibuka 100 TT (≥ 50 TT Permenkes 6/2026 Pasal 10 (1)); bertentangan keinginan owner 1."},
        {"kode": "V7", "uraian": "Halaman hijau non-akses diurug ke +11,50 (bukan +12,05)",
         "hemat": v_hijau * hijau * HARGA["urugan_m3"] * FAKTOR_NYATA * k,
         "akibat": "Taman tergenang saat banjir > +11,50 (antara Q25 dan Q50, 3.3); jalan, drop-off IGD tetap +12,05."},
    ]
    sisa = r["total"]
    for o in opsi:
        sisa -= o["hemat"]
        o["sisa"] = sisa
        o["selisih_pagu"] = sisa - PAGU
    return opsi


def ringkasan():
    r = rekap()
    ve = rekayasa_nilai()
    return {"total": r["total"], "pagu": PAGU, "selisih": r["selisih"], "rasio": r["rasio_pagu"],
            "per_m2": r["per_m2"], "metode_owner": r["metode_owner"], "rasio_nonstandar": r["rasio_nonstandar"],
            "rentang": (rekap("min", HSBGN * 0.85)["total"], rekap("maks", HSBGN * 1.15)["total"]),
            "setelah_ve": ve[-1]["sisa"], "hemat_ve": sum(o["hemat"] for o in ve),
            "luas_pagu_cukup": PAGU / (r["total"] / r["luas"])}


def fmt(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


def miliar(v):
    return fmt(v / 1000, 1)


# ------------------------------------------------------------------ Excel
def buat_excel(keluar=BERKAS):
    import openpyxl

    from format_dokumen import AI, Lembar, set_font_bawaan

    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    r = rekap()
    rg = ringkasan()

    # 1 Petunjuk
    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk perkiraan biaya (langkah 3.8)", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        "Metode Permen PUPR 22/2018: biaya standar = luas bruto × koefisien fungsi (Pasal 31 ayat (2), hal. 35-36) × "
        "koefisien jumlah lantai (Pasal 21 ayat (4)-(5), hal. 21) × harga satuan tertinggi (Pasal 30, hal. 34). Biaya "
        "standar sudah termasuk overhead, asuransi, K3, inflasi, dan pajak (Pasal 27 ayat (8), hal. 29).",
        "Nonstandar M/E: persentase Pasal 29 ayat (1) hal. 30-32 terhadap biaya standar; nilai pakai dan alasannya di "
        "lembar Nonstandar. Jumlah nonstandar ≤ 150 % biaya standar (Pasal 21 ayat (7)). Owner yayasan, bukan "
        "bangunan gedung negara: Permen 22/2018 dipakai sebagai pedoman cara hitung.",
        "Fondasi dalam, struktur, dan pematangan lahan dihitung dari volume nyata (3.3, 3.6, 3.7) × harga satuan "
        "[Asumsi] × (1 + biaya tidak langsung 12 %, Permen PUPR 8/2023 Pasal 11 ayat (3) hal. 9) × (1 + PPN). Yang "
        "sudah tercakup porsi standar (Pasal 27 ayat (6) hal. 28, nilai tengah) dikurangkan.",
        "Ubah sel hijau di lembar Parameter (HSBGN, koefisien lantai, harga satuan); semua lembar memakai rumus Excel.",
        "HSBGN Kota Jambi 2026, koefisien lantai, PPN, dan harga satuan belum ada di acuan: berlabel [Asumsi] sampai "
        "SK wali kota dan survei harga (SE 47/2026 Lampiran I). Kalibrasi IKK BPS 2025: Kota Jambi 95,03.",
        "Rekayasa nilai V1-V7 di lembar Rekayasa Nilai; letaknya di gambar GK-08.",
    ])], rata=list("cl"))

    # 2 Parameter
    lb = Lembar(wb.create_sheet("Parameter"), 2, "Parameter biaya", [6, 54, 14, 14, 50])
    lb.catatan(LABEL + " Satuan uang juta Rp.")
    par = [
        ("HSBGN", "Harga satuan tertinggi bangunan tidak sederhana", HSBGN, "juta/m²", "[Asumsi] Pasal 30 (7)"),
        ("KL_UTAMA", "Koefisien jumlah lantai, 6 lantai", KL["UTAMA"], "-", "[Asumsi] Pasal 21 (5)"),
        ("KL_GU", "Koefisien jumlah lantai, 4 lantai", KL["GU"], "-", "[Asumsi] Pasal 21 (5)"),
        ("FB", "Faktor bruto (3.4)", pr.FAKTOR_BRUTO, "-", "langkah 3.4 [Asumsi]"),
        ("BTL", "Biaya tidak langsung", BTL, "-", "Permen PUPR 8/2023 Pasal 11 (3): 0,10-0,15"),
        ("PPN", "PPN", PPN, "-", "[Asumsi]"),
        ("KONT", "Kontinjensi tahap konsep", KONTINJENSI, "-", "[Asumsi]"),
        ("BETON", "Beton per m³", HARGA["beton_m3"], "juta/m³", "langkah 3.6 [Asumsi]"),
        ("BEKISTING", "Bekisting per m³ beton", HARGA["bekisting_m3"], "juta/m³", "langkah 3.6 [Asumsi]"),
        ("BESI", "Baja tulangan terpasang", HARGA["besi_ton"], "juta/ton", "langkah 3.6 [Asumsi]"),
        ("URUG", "Urugan dipadatkan", HARGA["urugan_m3"], "juta/m³", "[Asumsi]"),
        ("PVD", "PVD terpasang", HARGA["pvd_m"], "juta/m", "[Asumsi]"),
        ("PASIR", "Hamparan pasir", HARGA["pasir_m3"], "juta/m³", "[Asumsi]"),
        ("KACA", "Selisih dinding tirai kaca per m² bukaan", HARGA["kaca_lebih_m2"], "juta/m²", "[Asumsi]"),
        ("PAGU", "Pagu konstruksi fisik (termasuk PPN)", PAGU, "juta", "TOR butir 6"),
    ]
    h, r1, _ = lb.tabel(["No", "Parameter", "Nilai", "Satuan", "Sumber"],
                        [[i + 1, p[1], p[2], p[3], p[4]] for i, p in enumerate(par)],
                        rata=list("clccl"), fmt=[None, None, "0.000", None, None], fill_kolom={2: AI})
    P = {p[0]: f"Parameter!${lb.kol(2)}${r1 + i}" for i, p in enumerate(par)}
    FN = f"(1+{P['BTL']})*(1+{P['PPN']})"

    # 3 Luas dan standar
    lf = luas_fungsi()
    lb = Lembar(wb.create_sheet("Biaya Standar"), 3, "Luas bruto, koefisien fungsi, dan biaya standar",
                [6, 12, 46, 10, 12, 10, 12, 24, 16])
    lb.catatan(LABEL + " Biaya = bruto × koef fungsi × koef lantai × HSBGN. Bruto = bersih × faktor bruto; dua baris "
               "terakhir sisa luas massa (3.4).")
    rows = [[i + 1, b["lantai"], b["ruang"], b["massa"], b["bersih"], b["k"], b["bruto"], b["dasar"], b["biaya"]]
            for i, b in enumerate(lf)]
    h, a, z = lb.tabel(["No", "Lantai", "Ruang", "Massa", "Bersih (m²)", "Koef fungsi", "Bruto (m²)",
                        "Pasal 31 (2) huruf", "Biaya (juta Rp)"], rows, rata=list("cclcccclc"),
                       fmt=[None, None, None, None, "#,##0", "0.00", "#,##0", None, "#,##0"], fill_kolom={5: AI, 8: AI},
                       beku_kolom=3)
    cE, cF, cG, cD, cI = lb.kol(4), lb.kol(5), lb.kol(6), lb.kol(3), lb.kol(8)
    for i, rr in enumerate(range(a, z + 1)):
        ws = lb.ws
        if lf[i]["bersih"] > 0:
            ws[f"{cG}{rr}"] = f"={cE}{rr}*{P['FB']}"
        ws[f"{cI}{rr}"] = f"={cG}{rr}*{cF}{rr}*IF({cD}{rr}=\"GU\",{P['KL_GU']},{P['KL_UTAMA']})*{P['HSBGN']}"
    rng = f"{cI}{a}:{cI}{z}"
    rngD, rngB = f"{cD}{a}:{cD}{z}", f"{lb.kol(2)}{a}:{lb.kol(2)}{z}"
    lb.kosong()
    tot = [
        ["", "", "Jumlah gedung utama", "UTAMA", "", "", "", "", f"=SUMIF({rngD},\"UTAMA\",{rng})"],
        ["", "", "Jumlah gedung utilitas (tanpa dek parkir)", "GU", "", "", "", "",
         f"=SUMIF({rngD},\"GU\",{rng})-{cI}{z}"],
        ["", "", "Jumlah dek parkir", "GU", "", "", "", "", f"={cI}{z}"],
        ["", "", "Jumlah biaya standar", "", "", "", f"=SUM({cG}{a}:{cG}{z})", "", f"=SUM({rng})"],
    ]
    _, t1, _ = lb.tabel(["", "", "Rekap", "", "", "", "Bruto (m²)", "", "Biaya (juta Rp)"], tot, rata=list("cclcccclc"),
                        fmt=[None] * 6 + ["#,##0", None, "#,##0"], beku=False)
    S = {"UTAMA": f"'Biaya Standar'!${cI}${t1}", "GU": f"'Biaya Standar'!${cI}${t1 + 1}",
         "PARKIR": f"'Biaya Standar'!${cI}${t1 + 2}", "TOTAL": f"'Biaya Standar'!${cI}${t1 + 3}",
         "LUAS": f"'Biaya Standar'!${cG}${t1 + 3}"}
    _ = rngB

    # 4 Nonstandar
    lb = Lembar(wb.create_sheet("Nonstandar"), 4, "Biaya nonstandar M/E dan kelengkapan (Pasal 29 ayat (1))",
                [6, 40, 8, 9, 9, 10, 16, 46])
    lb.catatan(LABEL + " Persen terhadap biaya standar gedung utama + gedung utilitas; dek parkir hanya f dan g "
               "(nilai bawah).")
    rows = [[i + 1, n[1], n[2], n[3], n[4], n[5], n[5] * r["standar"]["bangunan"], n[6]] for i, n in enumerate(NONSTANDAR)]
    rows += [[len(NONSTANDAR) + j + 1, f"Dek parkir: {k.lower()}", "f" if k == "LISTRIK" else "g", p, p, p,
              p * r["standar"]["PARKIR"], "nilai bawah"] for j, (k, p) in enumerate(NONSTANDAR_PARKIR)]
    h, a, z = lb.tabel(["No", "Pekerjaan", "Huruf", "Min", "Maks", "Pakai", "Biaya (juta Rp)", "Alasan nilai pakai"],
                       rows, rata=list("clcccccl"),
                       fmt=[None, None, None, "0.0%", "0.0%", "0.0%", "#,##0", None], fill_kolom={5: AI, 6: AI})
    cF, cG = lb.kol(5), lb.kol(6)
    for i, rr in enumerate(range(a, z + 1)):
        basis = S["PARKIR"] if i >= len(NONSTANDAR) else f"({S['UTAMA']}+{S['GU']})"
        lb.ws[f"{cG}{rr}"] = f"={cF}{rr}*{basis}"
    zb = a + len(NONSTANDAR) - 1
    lb.kosong()
    _, t2, _ = lb.tabel(["", "Rekap", "", "", "", "Persen", "Biaya (juta Rp)", ""], [
        ["", "Nonstandar gedung utama + utilitas", "", "", "", f"=SUM({cF}{a}:{cF}{zb})", f"=SUM({cG}{a}:{cG}{zb})", ""],
        ["", "Nonstandar dek parkir", "", "", "", "", f"=SUM({cG}{zb + 1}:{cG}{z})", ""],
    ], rata=list("clcccccl"), fmt=[None] * 5 + ["0.0%", "#,##0", None], beku=False)
    NS = {"BANGUNAN": f"Nonstandar!${cG}${t2}", "PARKIR": f"Nonstandar!${cG}${t2 + 1}"}

    # 5 Kebutuhan nyata
    lb = Lembar(wb.create_sheet("Kebutuhan Nyata"), 5, "Fondasi, struktur, pematangan lahan: kebutuhan nyata",
                [6, 56, 14, 12, 14, 16, 40])
    lb.catatan(LABEL + " Biaya langsung = volume × harga; total = langsung × (1 + BTL) × (1 + PPN).")
    fa, sn, ln = fondasi_nyata("A"), struktur_nyata(), lahan_nyata()
    rows, rumus = [], []
    for nama, v, besi, biaya in fa["item"]:
        if besi is None:
            rows.append([len(rows) + 1, nama, v, "tiang", None, biaya, "panjang × harga per m (3.7) [Asumsi]"])
            rumus.append(None)
        else:
            rows.append([len(rows) + 1, nama, v, "m³", besi, biaya, f"{PILECAP_PER_TIANG} m³/tiang [Asumsi]"])
            rumus.append("beton")
    n_fondasi = len(rows)
    for nama, v, besi, biaya in sn["item"]:
        rows.append([len(rows) + 1, nama, v, "m³", besi, biaya, "volume 3.6; besi per jenis unsur"])
        rumus.append("beton")
    n_struktur = len(rows)
    kode_lahan = {"m³ padat": "URUG", "m": "PVD", "m³": "PASIR"}
    for nama, v, sat, biaya in ln["item"]:
        rows.append([len(rows) + 1, nama, v, sat, None, biaya, "lumpsum [Asumsi]" if sat == "ls" else "[Asumsi]"])
        rumus.append(kode_lahan.get(sat))
    h, a, z = lb.tabel(["No", "Pekerjaan", "Volume", "Satuan", "Besi (ton)", "Biaya langsung (juta Rp)", "Dasar"],
                       rows, rata=list("clccccl"),
                       fmt=[None, None, "#,##0", None, "#,##0.0", "#,##0", None], fill_kolom={2: AI, 5: AI})
    cC, cE, cF = lb.kol(2), lb.kol(4), lb.kol(5)
    for i, rr in enumerate(range(a, z + 1)):
        if rumus[i] == "beton":
            lb.ws[f"{cF}{rr}"] = f"={cC}{rr}*({P['BETON']}+{P['BEKISTING']})+{cE}{rr}*{P['BESI']}"
        elif rumus[i]:
            lb.ws[f"{cF}{rr}"] = f"={cC}{rr}*{P[rumus[i]]}"
    lb.kosong()
    _, t3, _ = lb.tabel(["", "Rekap (dengan BTL dan PPN)", "", "", "", "Total (juta Rp)", ""], [
        ["", "Fondasi (tiang + pile cap)", "", "", "", f"=SUM({cF}{a}:{cF}{a + n_fondasi - 1})*{FN}", ""],
        ["", "Struktur atas + pelat lantai dasar", "", "", "", f"=SUM({cF}{a + n_fondasi}:{cF}{a + n_struktur - 1})*{FN}",
         ""],
        ["", "Penyiapan dan pematangan lahan", "", "", "", f"=SUM({cF}{a + n_struktur}:{cF}{z})*{FN}", ""],
    ], rata=list("clccccl"), fmt=[None] * 5 + ["#,##0", None], beku=False)
    KN = {"FONDASI": f"'Kebutuhan Nyata'!${cF}${t3}", "STRUKTUR": f"'Kebutuhan Nyata'!${cF}${t3 + 1}",
          "LAHAN": f"'Kebutuhan Nyata'!${cF}${t3 + 2}"}

    # 6 Rekap
    lb = Lembar(wb.create_sheet("Rekap"), 6, "Rekap perkiraan biaya terhadap pagu", [6, 60, 18, 34])
    lb.catatan(LABEL + " Perkiraan kelas konsep (luas × harga satuan), bukan RAB.")
    f_fnd = f"MAX(0,{KN['FONDASI']}-0.075*{S['TOTAL']})"
    f_str = f"MAX(0,{KN['STRUKTUR']}-0.30*{S['TOTAL']})"
    luas_fas = luas_fasad()
    rumus_rekap = [S["UTAMA"], S["GU"], S["PARKIR"], NS["BANGUNAN"], NS["PARKIR"], f_fnd, f_str, KN["LAHAN"],
                   f"{luas_fas:.1f}*{WWR}*{P['KACA']}*{FN}", f"{HARGA['dermaga']}*{FN}"]
    rows = [[i + 1, b[0], b[1], b[2]] for i, b in enumerate(r["baris"])]
    h, a, z = lb.tabel(["No", "Komponen", "Biaya (juta Rp)", "Dasar"], rows, rata=list("clcl"),
                       fmt=[None, None, "#,##0", None], fill_kolom={2: AI})
    cC = lb.kol(2)
    for rr, f_ in zip(range(a, z + 1), rumus_rekap):
        lb.ws[f"{cC}{rr}"] = f"={f_}"
    lb.kosong()
    _, t4, _ = lb.tabel(["", "Jumlah", "Nilai", "Keterangan"], [
        ["", "Subtotal", f"=SUM({cC}{a}:{cC}{z})", ""],
        ["", "Kontinjensi", f"={P['KONT']}*{cC}{z + 3}", "[Asumsi]"],
        ["", "Perkiraan biaya konstruksi fisik", f"={cC}{z + 3}+{cC}{z + 4}", "termasuk PPN"],
        ["", "Pagu", f"={P['PAGU']}", "TOR butir 6"],
        ["", "Selisih terhadap pagu", f"={cC}{z + 5}-{cC}{z + 6}", "positif = kurang"],
        ["", "Rasio perkiraan / pagu", f"={cC}{z + 5}/{cC}{z + 6}", ""],
        ["", "Biaya per m² luas lantai", f"={cC}{z + 5}/{S['LUAS']}", f"luas {fmt(r['luas'], 0)} m² (3.4)"],
        ["", "Rasio nonstandar / standar", f"=({cC}{z + 3}-{S['TOTAL']})/{S['TOTAL']}", "Pasal 21 (7): ≤ 150 % untuk gedung negara"],
        ["", "Metode owner: 14 juta/m² × luas konsultan", f"=14*{S['LUAS']}", "pembanding"],
    ], rata=list("clcl"), fmt=[None, None, "#,##0", None], beku=False)
    for rr in (t4 + 5, t4 + 7):
        lb.ws[f"{cC}{rr}"].number_format = "0.0%"
    lb.ws[f"{cC}{t4 + 6}"].number_format = "#,##0.00"
    lb.kosong()
    lb.bagian("B", "Pembanding dan rentang")
    rmin, rmaks = rg["rentang"]
    lb.tabel(["No", "Butir", "Nilai (juta Rp)", "Keterangan"], [
        [1, "Fondasi kebutuhan nyata vs porsi standar 5-10 %", r["fondasi_nyata"],
         f"porsi standar tengah {fmt(r['fondasi_std'], 0)}"],
        [2, "Struktur kebutuhan nyata vs porsi standar 25-35 %", r["struktur_nyata"],
         f"porsi standar tengah {fmt(r['struktur_std'], 0)}"],
        [3, "Pematangan lahan vs batas 3,5 % (Pasal 29 (1) s)", r["lahan"], f"batas {fmt(r['lahan_batas'], 0)}"],
        [4, "Rentang bawah: persen Pasal 29 minimum, HSBGN -15 %", rmin, "kepekaan"],
        [5, "Rentang atas: persen Pasal 29 maksimum, HSBGN +15 %", rmaks, "kepekaan"],
        [6, "Luas yang cukup dibiayai pagu pada biaya per m² ini (m²)", rg["luas_pagu_cukup"], "pembanding"],
    ], rata=list("clcl"), fmt=[None, None, "#,##0", None], fill_kolom={2: AI}, beku=False)

    # 7 Rekayasa nilai
    lb = Lembar(wb.create_sheet("Rekayasa Nilai"), 7, "Opsi pengurangan lingkup dan rekayasa nilai",
                [6, 56, 14, 14, 14, 58])
    lb.catatan(LABEL + " Penghematan kumulatif berurutan V1 → V7; termasuk nonstandar ikutan dan kontinjensi.")
    ve = rekayasa_nilai()
    lb.tabel(["Kode", "Opsi", "Hemat (juta Rp)", "Sisa biaya (juta Rp)", "Selisih pagu (juta Rp)", "Akibat dan syarat"],
             [[o["kode"], o["uraian"], o["hemat"], o["sisa"], o["selisih_pagu"], o["akibat"]] for o in ve],
             rata=list("clcccl"), fmt=[None, None, "#,##0", "#,##0", "#,##0", None], fill=AI)
    lb.kosong()
    lb.bagian("B", "Kesimpulan (disetujui Defsa 19 Nov 2026)")
    lb.tabel(["No", "Butir", "", "", "", "Uraian"], [
        [1, "Pagu", "", "", "", f"Perkiraan Rp {miliar(r['total'])} M = {fmt(r['rasio_pagu'], 2)} × pagu Rp 168 M. "
         f"Pagu disusun untuk 12.000 m²; program 150 TT menurut konsultan {fmt(r['luas'], 0)} m² termasuk dek parkir."],
        [2, "Rekayasa nilai", "", "", "", f"V1-V7 bersama menghemat ±Rp {miliar(rg['hemat_ve'])} M; sisa "
         f"Rp {miliar(rg['setelah_ve'])} M, masih di atas pagu."],
        [3, "Pilihan owner", "", "", "", "(a) tambah pagu/pinjaman; (b) bertahap: 150 TT tetap tetapi fit-out dan "
         "fasilitas penunjang menyusul; (c) kurangi TT (≥ 50 TT). Dibawa ke rapat konsep (3.10)."],
    ], rata=list("cl") + ["l"] * 4, fill_kolom={5: AI}, beku=False)
    wb.save(keluar)
    return keluar


# ------------------------------------------------------------------ gambar GK-08
GRAF_X0, GRAF_Y0 = 0.0, -260.0  # letak diagram batang di model space (m), jauh dari tapak
GRAF_SKALA = 0.5  # m model per miliar Rp


def gambar_cad(status=None):
    import tahap3_basement as bs
    import tahap3_tapak as tp
    import tahap3_zonasi as zn
    from cad_lembar import STATUS_SETUJU, Gambar

    def k(x0, x1, y0, y1):
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    r = rekap()
    ve = rekayasa_nilai()
    dwg = KELUAR / "Gambar" / "DWG" / "GK-08 Opsi Pengurangan Lingkup.dwg"
    png = KELUAR / "Gambar" / "GK-08 Opsi Pengurangan Lingkup.png"
    with Gambar(750) as g:
        g.layer("C-SEMPADAN", 3, 0.25)
        g.arsir(list(tp.ruang_sempadan().exterior.coords)[:-1], "C-SEMPADAN", pola="DOTS", skala_pola=0.6)
        g.legenda_tambah("arsir", "Ruang sempadan sungai", pola="DOTS", skala_pola=0.6)
        pd, mn, gu = pr.MASSA["PODIUM"], pr.MASSA["MENARA"], bs.GEDUNG_UP
        g.layer("A-MASSA", 7, 0.7)
        g.pline(k(*pd["x"], *pd["y"]), "A-MASSA", tutup=True)
        g.pline(k(*gu["x"], *gu["y"]), "A-MASSA", tutup=True)
        g.legenda_tambah("garis", "Massa bangunan", tebal=0.7)
        g.layer("A-MASSA-MENARA", 7, 0.35, "DASHED")
        g.pline(k(*mn["x"], *mn["y"]), "A-MASSA-MENARA", tutup=True)
        g.legenda_tambah("garis", "Menara LT4-LT6", garis="DASHED")
        # V1: LT3 podium utara di luar menara
        g.layer("A-VE-KURANG", 7, 0.35)
        g.arsir_lubang(k(36, 84, 51, 75), [k(48, 72, 60.5, 65.5)], "A-VE-KURANG", pola="ANSI31", skala_pola=1.5)
        g.pline(k(36, 84, 51, 75), "A-VE-KURANG", tutup=True)
        g.legenda_tambah("arsir", "Lingkup dikurangi atau ditunda", pola="ANSI31", skala_pola=1.5)
        g.layer("A-TEKS", 7, 0.25)
        g.teks((60, 63), "LT3 TIDAK DIBANGUN", "A-TEKS", 1.8, j="MC", tebal=True)
        g.teks((24, 70), "PODIUM LT1-LT3", "A-TEKS", 2.0, j="MC", tebal=True)
        g.teks((52, 39), "MENARA LT4-LT6", "A-TEKS", 2.0, j="MC", tebal=True)
        ux = sum(gu["x"]) / 2
        g.teks((ux, 62), "GEDUNG UTILITAS", "A-TEKS", 1.8, j="MC", tebal=True)
        g.teks((ux, 58.5), "DAN PARKIR", "A-TEKS", 1.8, j="MC", tebal=True)
        # V3: dermaga dan teras di tepi sungai, dekat IGD
        g.layer("A-VE-DERMAGA", 7, 0.35, "DASHED")
        g.pline(k(66, 80, 1.5, 6.5), "A-VE-DERMAGA", tutup=True)
        g.pline([(73, 6.5), (73, 27)], "A-VE-DERMAGA")
        g.legenda_tambah("garis", "Dermaga dan jalur ditunda", garis="DASHED")
        g.layer("C-KOLAM", 7, 0.35)
        g.pline(k(*zn.RETENSI), "C-KOLAM", tutup=True)
        g.teks(((zn.RETENSI[0] + zn.RETENSI[1]) / 2, (zn.RETENSI[2] + zn.RETENSI[3]) / 2), "KOLAM RETENSI",
               "C-KOLAM", 1.5, j="MC")
        g.layer("C-PERSIL", 7, 0.7, "PHANTOM")
        g.pline(k(0, 140, 0, 90), "C-PERSIL", tutup=True)
        g.teks((70, 93), "JALAN KOLEKTOR", "C-TEKS", 2.2, j="MC", tebal=True)
        g.teks((30, -2.5), "SUNGAI BATANGHARI", "C-TEKS", 2.2, j="MC", tebal=True)
        # label V1-V7 dengan garis tunjuk
        tanda = {"V1": ((78, 72), (90, 84)), "V2": ((16, 34), (-12, 34)), "V3": ((76, 4), (100, -1.5)),
                 "V4": ((12, 60), (-12, 60)), "V5": ((130, 72), (155, 84)), "V6": ((82, 42), (155, 42)),
                 "V7": ((20, 82), (-12, 84))}
        for o in ve:
            panah, letak = tanda[o["kode"]]
            g.tunjuk(panah, letak, o["kode"], layer="A-VE-TANDA")
        # diagram batang biaya (viewport kedua)
        g.layer("D-SUMBU", 7, 0.25)
        g.layer("D-BATANG", 7, 0.35)
        g.layer("D-PAGU", 7, 0.5, "DASHED")
        g.layer("D-TEKS", 7, 0.25)
        x0, y0 = GRAF_X0, GRAF_Y0
        tinggi_b, jarak = 5.0, 8.0
        batang = [("PERKIRAAN AWAL", r["total"])] + [(f"SETELAH {o['kode']}", o["sisa"]) for o in ve]
        for i, (nama, nilai) in enumerate(batang):
            y = y0 - i * jarak
            panjang = nilai / 1000 * GRAF_SKALA
            g.arsir(k(x0, x0 + panjang, y - tinggi_b, y), "D-BATANG", pola="ANSI31" if i else "SOLID",
                    skala_pola=2.0)
            g.pline(k(x0, x0 + panjang, y - tinggi_b, y), "D-BATANG", tutup=True)
            g.teks((x0 - 3, y - tinggi_b / 2), nama, "D-TEKS", 2.6, j="MR")
            g.teks((x0 + panjang + 3, y - tinggi_b / 2), f"Rp {miliar(nilai)} M", "D-TEKS", 2.6, j="ML")
        y_bawah = y0 - (len(batang) - 1) * jarak - tinggi_b - 4
        xp = x0 + PAGU / 1000 * GRAF_SKALA
        g.pline([(xp, y0 + 5), (xp, y_bawah)], "D-PAGU")
        g.teks((xp, y0 + 7), "PAGU RP 168,0 M", "D-PAGU", 2.6, j="MC", tebal=True)
        g.pline([(x0, y0 + 3), (x0, y_bawah)], "D-SUMBU")
        g.pline([(x0, y_bawah), (x0 + 240, y_bawah)], "D-SUMBU")
        for m in range(0, 451, 50):
            xm = x0 + m * GRAF_SKALA
            g.pline([(xm, y_bawah), (xm, y_bawah - 1.5)], "D-SUMBU")
            g.teks((xm, y_bawah - 4), f"{m}", "D-TEKS", 2.2, j="MC")
        g.teks((x0 + 110, y_bawah - 9), "MILIAR RUPIAH (TERMASUK PPN)", "D-TEKS", 2.2, j="MC")
        g.lembar("GK-08", "Opsi pengurangan lingkup", "1:750", pusat=(66, 46), vp=((24, 150), (331, 283)),
                 subjudul="Langkah 3.8: letak rekayasa nilai V1-V7 dan perkiraan biaya terhadap pagu (lembar Rekap)",
                 status=status or STATUS_SETUJU,
                 catatan=[
                     f"Perkiraan Rp {miliar(r['total'])} M = {fmt(r['rasio_pagu'], 2)} × pagu; luas "
                     f"{fmt(r['luas'], 0)} m² (pagu dasar 12.000 m²).",
                     "Metode Permen PUPR 22/2018 Pasal 21, 29, 31; HSBGN, koefisien lantai, harga [Asumsi].",
                     "V1 LT3 dirampingkan; V2 tiang hibrida; V3 dermaga ditunda; V4 kaca 35 %; V5 parkir LT4 "
                     "ditunda; V6 fit-out LT6 tahap 2; V7 taman +11,50.",
                     "V1-V7 kumulatif; syarat dan akibat di lembar Rekayasa Nilai.",
                 ])
        g.viewport_tambahan((24, 52), (331, 140), pusat=(GRAF_X0 + 90, GRAF_Y0 - 36), skala=1000,
                            judul="Perkiraan biaya setelah tiap opsi", teks_skala="DIAGRAM, TANPA SKALA")
        g.skala_grafis(205, 22, 50)
        g.panah_utara(318, 262, 10)
        g.simpan(dwg, PDF, png)
    return dwg


def buat():
    buat_excel()
    gambar_cad()
    return BERKAS, PDF


if __name__ == "__main__":
    r = rekap()
    for b in r["baris"]:
        print(f"{b[0]:60s} {fmt(b[1], 0):>12s}")
    for k_ in ("subtotal", "kontinjensi", "total", "selisih", "rasio_pagu", "per_m2", "rasio_nonstandar",
               "fondasi_nyata", "fondasi_std", "struktur_nyata", "struktur_std", "lahan", "lahan_batas",
               "metode_owner", "luas"):
        print(k_, fmt(r[k_], 3))
    print(ringkasan())
    for o in rekayasa_nilai():
        print(o["kode"], fmt(o["hemat"], 0), fmt(o["sisa"], 0), o["uraian"])
