"""Tahap 8b: RAB (volume 8a × harga satuan), MEP RS, persiapan, SMKK, PPN, rekapitulasi, value engineering, T-121.

Volume dan harga satuan dipakai ulang dari `tahap8_volume` (tidak dihitung ulang); MEP, lahan, pagu dari `tahap3_biaya`.
Keputusan K8-8..K8-11: `08 RAB/00 Rencana Tahap 8.md`. Data simulasi studi kasus.
"""
import functools
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import tahap3_biaya as t3  # noqa: E402
import tahap8_volume as t8  # noqa: E402

AKAR = pathlib.Path(__file__).resolve().parents[1]
KELUAR = AKAR / "08 RAB" / "8b RAB SMKK VE.xlsx"
STATUS = t8.STATUS
LABEL = t8.LABEL
PPN = t3.PPN                                  # K8-11
TOL = {"T-121a": (-30.0, 50.0), "T-121b": (-30.0, 50.0), "T-121c": 0.01, "T-121d": 1.0}   # ditetapkan sebelum membandingkan
LUAS = t3.luas_massa()["total"]               # m² luas lantai kotor (3.5/3.8)
PAGU = t3.PAGU * 1e6                          # Rp, termasuk PPN (TOR butir 6)
UTILITAS_DASAR = 0.065                        # komponen utilitas 5-8 % biaya standar (3.8 STANDAR_KOMPONEN), nilai tengah
MEP_KODE = ("AC", "LIF", "SUARA", "PABX", "TI", "LISTRIK", "KEBAKARAN", "PETIR", "IPAL", "GAS", "GASMEDIS", "SAMBUNG")
PONDASI = ("Tiang bor Ø800", "Pile cap", "Sloof dan balok pondasi", "Pelat lantai 1", "Pit lift")
TAPAK = ("R-RT", "R-AS", "R-PV", "R-PB", "R-PG", "R-NM", "R-BK")

# Persiapan [Asumsi: Jambi 2026, harga termasuk BTL 12 %]
PERSIAPAN = [
    ("P1", "Pengukuran, uitzet, dan bouwplank", "ls", 1, 85_000_000),
    ("P2", "Direksi keet, gudang, los kerja (sewa + bongkar)", "m²", 300, 1_650_000),
    ("P3", "Pagar sementara seng h 2,4 m (keliling lahan ±420 m)", "m'", 420, 650_000),
    ("P4", "Mobilisasi dan demobilisasi (2 rig bor, crawler crane, tower crane)", "ls", 1, 1_250_000_000),
    ("P5", "Sewa tower crane + operator (2 unit × 18 bulan)", "unit-bln", 36, 135_000_000),
    ("P6", "Listrik dan air kerja", "bulan", 24, 45_000_000),
    ("P7", "Gambar kerja, dokumentasi, laporan, gambar as-built", "ls", 1, 350_000_000),
    ("P8", "Pembersihan akhir dan serah terima", "m²", LUAS, 8_000),
]
# Tapak di luar model [Asumsi: volume dari 3.8 (kolam retensi 650 m³), harga Jambi 2026]
TAPAK_LUAR = [
    ("R-DR", "Saluran drainase tapak U-ditch 40 + tutup", "m'", 600, 850_000),
    ("R-KR", "Kolam retensi 650 m³ beton bertulang (3.8)", "m³", 650, 2_400_000),
]
# SMKK 9 komponen, SE 47/2026 Lampiran III bagian B; volume risiko besar, 24 bulan; harga tanpa BTL (K8-9) [Asumsi]
SMKK = [
    (1, "Penyiapan dokumen SMKK (RKK, RMPK, RKPPL, RMLLP)", "set", 1, 25_000_000),
    (2, "Sosialisasi, promosi, pelatihan (induksi, safety talk, spanduk)", "bulan", 24, 6_000_000),
    (3, "APD pekerja (helm, rompi, sepatu, sarung tangan, sabuk tubuh penuh)", "orang", 250, 1_200_000),
    (3, "APK: jaring pengaman dan railing sementara tepi pelat", "m'", 1_600, 150_000),
    (4, "Asuransi CAR (minimal 0,1 % nilai pekerjaan, hal. 260)", "ls", 1, None),
    (5, "Ahli K3 Konstruksi", "org-bln", 24, 25_000_000),
    (5, "Petugas Keselamatan Konstruksi (2 orang)", "org-bln", 48, 8_000_000),
    (6, "Fasilitas kesehatan (P3K, ruang klinik, tenaga medis)", "bulan", 24, 9_000_000),
    (7, "Rambu dan perlengkapan lalu lintas", "ls", 1, 45_000_000),
    (7, "Petugas pengatur lalu lintas (flagman, 2 orang)", "org-bln", 48, 4_500_000),
    (8, "Konsultasi ahli keselamatan (galian, dewatering, tower crane)", "ls", 1, 60_000_000),
    (9, "APAR 6 kg", "buah", 40, 1_100_000),
    (9, "Pemeriksaan dan sertifikasi alat angkat", "kali", 6, 25_000_000),
    (9, "CCTV area kerja", "buah", 8, 6_000_000),
    (9, "Audit internal SMKK", "kali", 2, 15_000_000),
]
SMKK_NAMA = {1: "Penyiapan dokumen", 2: "Sosialisasi, promosi, pelatihan", 3: "APK dan APD", 4: "Asuransi",
             5: "Personel keselamatan", 6: "Fasilitas kesehatan", 7: "Rambu dan lalu lintas", 8: "Konsultasi ahli",
             9: "Kegiatan pengendalian risiko"}
CAR = 0.001


@functools.lru_cache(maxsize=1)
def data_8a():
    item, tab = t8.daftar_pekerjaan()
    return {r["kode"]: r for r in item}, tab, t8.volume_struktur()


def _hsp(kode):
    return data_8a()[0][kode]["hsp"]


def _r(kode, ur, sat, vol, hsp=None, sumber="8a"):
    hsp = _hsp(kode) if hsp is None else hsp
    return {"kode": kode, "uraian": ur, "satuan": sat, "volume": vol, "hsp": hsp, "jumlah": vol * hsp, "sumber": sumber}


def _struktur(kelompok):
    """Item beton/besi/bekisting per kelompok struktur, harga satuan AHSP 8a (volume 8a, tidak dihitung ulang)."""
    s = data_8a()[2]
    g = {k: s[k] for k in kelompok}
    tot = lambda a: sum(x.get(a, 0.0) for x in g.values())  # noqa: E731
    out = []
    if "Tiang bor Ø800" in g:
        t = g["Tiang bor Ø800"]
        out += [_r("A1", "Tiang bor Ø800 fc' 35 (bor, cor tremie)", "m'", t["panjang"]),
                _r("A4", "Pembesian tiang (16 D25 + spiral D13 40/80, 6.7)", "kg", t["besi"])]
        g = {k: x for k, x in g.items() if k != "Tiang bor Ø800"}
        if "Pile cap" in g:
            cap = g["Pile cap"]
            vg = cap["galian"]
            out += [_r("R-GL", "Galian tanah cap (ruang kerja 1 m)", "m³", vg),
                    _r("A11", "Dewatering galian cap dan pit", "pompa-hari", 3 * 150),
                    _r("R-LK", "Lantai kerja beton fc' 10 tebal 100 mm", "m³", cap["lantai_kerja"]),
                    _r("R-UR", "Urugan kembali dipadatkan", "m³", max(vg - cap["bersih"] - cap["lantai_kerja"], 0.0))]
    nama = ", ".join(k.lower() for k in g)
    for kode, a, ur, sat in (("A2", "fc35", "Beton fc' 35", "m³"), ("A3", "fc30", "Beton fc' 30", "m³"),
                             ("A4", "besi", "Pembesian BjTS 420B", "kg"), ("A5", "bek_v", "Bekisting vertikal", "m²"),
                             ("A6", "bek_h", "Bekisting horizontal + perancah", "m²"), ("R-BJ", "baja", "Kolom baja HEB 200", "kg")):
        if tot(a) > 0:
            out.append(_r(kode, f"{ur} ({nama})" if kode in ("A2", "A3", "A4") else ur, sat, tot(a)))
    return out


def mep():
    """K8-8: persentase Pasal 29 Permen PUPR 22/2018 (kolom 'pakai' 3.8) × biaya standar 3.8, dibagi (1 + PPN)."""
    s = t3.standar()
    out = []
    for kode, ur, huruf, _, _, pakai, ket in t3.NONSTANDAR:
        if kode in MEP_KODE:
            out.append(_r("M-" + kode, f"{ur} (Ps. 29 huruf {huruf}, {pakai * 100:g} %)", "ls", 1,
                          pakai * s["bangunan"] * 1e6 / (1 + PPN), "3.8"))
    for kode, p in t3.NONSTANDAR_PARKIR:
        out.append(_r("M-P" + kode[:3], f"{'Elektrikal' if kode == 'LISTRIK' else 'Proteksi kebakaran'} dek parkir ({p * 100:g} %)",
                      "ls", 1, p * s["PARKIR"] * 1e6 / (1 + PPN), "3.8"))
    out.append(_r("M-UD", f"Utilitas dasar: plambing, sanitair, penerangan, stop kontak ({UTILITAS_DASAR * 100:g} % biaya standar)",
                  "ls", 1, UTILITAS_DASAR * s["total"] * 1e6 / (1 + PPN), "3.8"))
    return out


def rab():
    """Daftar divisi: (nomor, nama, [item])."""
    it = data_8a()[0]
    s = t3.standar()
    ars = [_r(k, it[k]["uraian"], it[k]["satuan"], it[k]["volume"]) for k in it
           if (k.startswith("A") and k[1:2] in "7891" and k not in ("A1", "A11")) or (k.startswith("R-") and k not in TAPAK
                                                                                     and k not in ("R-GL", "R-LK", "R-UR", "R-BJ"))]
    for kode in ("RAYAP", "DIFABEL"):
        n = next(x for x in t3.NONSTANDAR if x[0] == kode)
        ars.append(_r("N-" + kode, f"{n[1]} (Ps. 29 huruf {n[2]}, {n[5] * 100:g} %)", "ls", 1,
                      n[5] * s["bangunan"] * 1e6 / (1 + PPN), "3.8"))
    lahan = [_r("L%d" % (i + 1), ur, sat, vol, rp * 1e6 / vol * t3.FAKTOR_NYATA / (1 + PPN), "3.8")
             for i, (ur, vol, sat, rp) in enumerate(t3.lahan_nyata()["item"])]
    tapak = lahan + [_r(k, it[k]["uraian"], it[k]["satuan"], it[k]["volume"]) for k in TAPAK]
    tapak += [_r(*x, sumber="8b") for x in TAPAK_LUAR]
    return [
        ("I", "Pekerjaan persiapan", [_r(*x, sumber="8b") for x in PERSIAPAN]),
        ("II", "Pekerjaan tanah dan pondasi", _struktur(PONDASI)),
        ("III", "Pekerjaan struktur atas", _struktur([k for k in data_8a()[2] if k not in PONDASI])),
        ("IV", "Pekerjaan arsitektur", ars),
        ("V", "Pekerjaan tapak dan pematangan lahan", tapak),
        ("VI", "Pekerjaan MEP rumah sakit (K8-8)", mep()),
    ]


def smkk(nilai_pekerjaan):
    out = []
    for no, ur, sat, vol, hs in SMKK:
        hs = CAR * nilai_pekerjaan if hs is None else hs
        out.append({"komponen": no, "uraian": ur, "satuan": sat, "volume": vol, "hsp": hs, "jumlah": vol * hs})
    return out


def rekap():
    div = rab()
    sub = [(no, nama, sum(r["jumlah"] for r in isi)) for no, nama, isi in div]
    fisik = sum(x[2] for x in sub)
    sm = smkk(fisik)
    jsm = sum(r["jumlah"] for r in sm)
    jumlah = fisik + jsm
    ppn = PPN * jumlah
    total = jumlah + ppn
    bulat = round(total, -6)
    return {"divisi": div, "sub": sub, "fisik": fisik, "smkk": sm, "j_smkk": jsm, "jumlah": jumlah, "ppn": ppn,
            "total": total, "bulat": bulat, "per_m2": bulat / LUAS, "pagu": PAGU, "selisih_pagu": bulat - PAGU,
            "luas_pagu": PAGU / (bulat / LUAS)}


def ve():
    """Value engineering tanpa analisis struktur ulang; penghematan termasuk PPN."""
    it, _, s = data_8a()
    t = s["Tiang bor Ø800"]
    L = t["panjang"] / t["n"]
    l_tul = L - (27.60 - 17.76) + 0.9                      # sama `tahap8_volume.besi_tiang` (6.7)
    keliling = math.pi * (0.800 - 2 * 0.075 - 0.013)
    dkg = t["n"] * keliling * t8.MASSA["D13"] * (l_tul - 6.0) * (1 / 0.080 - 1 / 0.150)
    hp = {"stick": 2_350_000, "acian": 68_000, "ht": 400_000}   # [Asumsi: Jambi 2026, termasuk BTL]
    lv = 0.5                                                    # porsi vinil di rawat inap [Asumsi]
    opsi = [
        ("VE-1", "Spiral tiang di bawah 6 m atas: D13-80 → D13-150", f"{t8.idn(dkg / 1000, 1)} t besi", dkg * _hsp("A4"),
         "Perencana memeriksa syarat tulangan transversal tiang KDS D di luar zona sendi (SNI 2847:2019, acuan/privat) "
         "dan geser tiang Tahap 6.7; tidak dihitung ulang di sini."),
        ("VE-2", "Fasad kaca: curtain wall unitized → sistem stick (rangka dipasang di tempat)", f"{t8.idn(it['A9']['volume'], 0)} m²",
         it["A9"]["volume"] * (_hsp("A9") - hp["stick"]),
         "Tampak sama; waktu pasang lebih lama ±2 bulan dan mutu kedap air bergantung pengawasan lapangan."),
        ("VE-3", "Dinding bata ringan: acian langsung 3-5 mm (mortar instan) ganti plester 15 mm + acian",
         f"{t8.idn(it['A8']['volume'], 0)} m²", it["A8"]["volume"] * (_hsp("A8") - hp["acian"]),
         "Syarat pasangan bata ringan rata (toleransi 3 mm); dinding basah tetap plester."),
        ("VE-4", "Dek helipad ditunda ke tahap 2 (struktur atap sudah disiapkan, K7)", f"{t8.idn(it['R-HP']['volume'], 0)} m²",
         it["R-HP"]["jumlah"], "Sejalan keputusan helipad tahap 2 (Tahap 7); atap dilapis kedap air sementara."),
        ("VE-5", "Lantai rawat inap: vinil homogen → homogeneous tile 60 × 60 nat epoksi", f"{t8.idn(lv * it['R-LV']['volume'], 0)} m²",
         lv * it["R-LV"]["volume"] * (it["R-LV"]["hsp"] - hp["ht"]),
         "OK, ICU, isolasi tetap vinil (sambungan las, pengendalian infeksi)."),
    ]
    r = rekap()
    sisa = r["bulat"]
    out = []
    for kode, ur, vol, hemat, akibat in opsi:
        h = hemat * (1 + PPN)
        sisa -= h
        out.append({"kode": kode, "uraian": ur, "volume": vol, "hemat": h, "porsi": h / r["bulat"] * 100,
                    "sisa": sisa, "akibat": akibat})
    return out


def cek_silang():
    r = rekap()
    a = t3.rekap()["total"] * 1e6
    sub = {no: j for no, _, j in r["sub"]}
    b1 = sub["II"] + sub["III"]
    b2 = (t3.fondasi_nyata("A")["total"] + t3.struktur_nyata()["total"]) * 1e6 / (1 + PPN)
    kode_8a = set(data_8a()[0])
    d1 = sum(x["jumlah"] for _, _, isi in r["divisi"] for x in isi if x["sumber"] == "8a")
    d2 = sum(x["jumlah"] for x in data_8a()[0].values())
    n_8a = sum(1 for _, _, isi in r["divisi"] for x in isi if x["sumber"] == "8a")
    baris = []
    for kode, nama, x1, x2 in (("T-121a", "Total RAB termasuk PPN vs perkiraan 3.8", r["bulat"], a),
                               ("T-121b", "Pondasi + struktur tanpa PPN vs 3.8 (fondasi A + struktur)", b1, b2)):
        d = (x1 / x2 - 1) * 100
        lo, hi = TOL[kode]
        baris.append({"kode": kode, "besaran": nama, "x1": x1, "x2": x2, "selisih": d, "lolos": lo <= d <= hi})
    baris.append({"kode": "T-121d", "besaran": f"Item 8a di divisi II-V ({n_8a} baris, {len(kode_8a)} kode)", "x1": d1, "x2": d2,
                  "selisih": d1 - d2, "lolos": abs(d1 - d2) <= TOL["T-121d"]})
    return baris


# ------------------------------------------------------------------ keluaran
idn = t8.idn


def buat_excel(keluar=KELUAR):
    import openpyxl
    from format_dokumen import Lembar, set_font_bawaan
    r = rekap()
    v = ve()
    cs = cek_silang()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    rp = "#,##0"
    # 2 RAB (dibuat dulu supaya alamat subtotal diketahui; urutan lembar diatur di akhir)
    s = Lembar(wb.create_sheet("RAB"), 2, "Rencana anggaran biaya per divisi", [9, 62, 10, 15, 16, 19, 6])
    s.catatan("Jumlah = volume × harga satuan (rumus). Harga satuan termasuk biaya umum + keuntungan 12 %. Sumber: 8a = "
              "volume Qto IFC + AHSP 8a; 3.8 = Tahap 3.8 (persentase Permen PUPR 22/2018 Ps. 29 atau lahan_nyata), dibagi "
              "(1 + PPN); 8b = lumsum/volume [Asumsi: Jambi 2026].")
    alamat = {}
    for no, nama, isi in r["divisi"]:
        s.bagian(no, nama)
        r0 = s.baris + 1
        D, E, F = s.kol(3), s.kol(4), s.kol(5)
        rows = [[x["kode"], x["uraian"], x["satuan"], round(x["volume"], 2), round(x["hsp"], 2), f"={D}{r0 + i}*{E}{r0 + i}",
                 x["sumber"]] for i, x in enumerate(isi)]
        rs = r0 + len(isi)
        rows.append(["", f"Subtotal divisi {no}", "", "", "", f"=SUM({F}{r0}:{F}{rs - 1})", ""])
        s.tabel(["Kode", "Uraian pekerjaan", "Sat.", "Volume", "Harga satuan (Rp)", "Jumlah (Rp)", "Sbr."], rows,
                rata=list("clcrrrc"), fmt=[None, None, None, "#,##0.00", rp, rp, None], beku=(no == "I"))
        alamat[no] = f"RAB!{F}{rs}"
        s.kosong()
    # 3 SMKK
    s = Lembar(wb.create_sheet("SMKK"), 3, "Biaya penerapan SMKK (9 komponen)", [7, 64, 10, 12, 16, 19])
    s.catatan("SE Dirjen Binkon 47/2026 Lampiran III bagian B (komponen 1-9, hal. 236-243 dan 245-276); Permen PUPR 8/2023 "
              "Ps. 22 ayat (1) dan (3) hal. 12: SMKK pokok pekerjaan tersendiri, bukan Biaya Umum (tanpa BTL). Volume risiko "
              "besar, durasi 24 bulan, harga [Asumsi: Jambi 2026]. Asuransi CAR = 0,1 % × jumlah divisi I-VI (rumus).")
    r0 = s.baris + 1
    D, E, F = s.kol(3), s.kol(4), s.kol(5)
    fisik = "+".join(alamat.values())
    rows = []
    for i, x in enumerate(r["smkk"]):
        hs = f"={CAR}*({fisik})" if x["uraian"].startswith("Asuransi") else round(x["hsp"])
        rows.append([x["komponen"], f"{SMKK_NAMA[x['komponen']]}: {x['uraian']}", x["satuan"], x["volume"], hs,
                     f"={D}{r0 + i}*{E}{r0 + i}"])
    rs = r0 + len(rows)
    rows.append(["", "Jumlah biaya penerapan SMKK", "", "", "", f"=SUM({F}{r0}:{F}{rs - 1})"])
    s.tabel(["Komp.", "Rincian", "Sat.", "Volume", "Harga satuan (Rp)", "Jumlah (Rp)"], rows,
            rata=list("clcrrr"), fmt=[None, None, None, "#,##0", rp, rp])
    alamat["VII"] = f"SMKK!{F}{rs}"
    # 4 VE
    s = Lembar(wb.create_sheet("Value Engineering"), 4, "Value engineering dan pagu owner", [8, 50, 14, 17, 9, 19, 46])
    s.ws.page_setup.paperSize = s.ws.PAPERSIZE_A3  # 7 kolom lebar: A3 agar huruf cetak terbaca (AU-09)
    s.catatan(f"Penghematan termasuk PPN, tanpa analisis struktur ulang. Pagu owner Rp {idn(PAGU / 1e9, 1)} miliar = "
              f"{idn(t3.PAGU_LUAS, 0)} m² × Rp {idn(t3.PAGU_HARGA, 0)} juta/m² (TOR butir 6).")
    s.tabel(["Kode", "Usulan", "Volume", "Hemat (Rp)", "Porsi (%)", "Sisa biaya (Rp)", "Akibat dan syarat"],
            [[o["kode"], o["uraian"], o["volume"], round(o["hemat"]), round(o["porsi"], 2), round(o["sisa"]), o["akibat"]]
             for o in v], rata=list("clrrrrl"), fmt=[None, None, None, rp, "0.00", rp, None])
    hv = sum(o["hemat"] for o in v)
    s.catatan(f"Total VE Rp {idn(hv / 1e9, 2)} miliar ({idn(hv / r['bulat'] * 100, 1)} %). Setelah VE Rp "
              f"{idn(v[-1]['sisa'] / 1e9, 1)} miliar, masih {idn((v[-1]['sisa'] - PAGU) / 1e9, 1)} miliar di atas pagu. "
              f"Penyebab utama: luas kotor {idn(LUAS, 0)} m² vs {idn(t3.PAGU_LUAS, 0)} m² dasar pagu; biaya per m² "
              f"Rp {idn(r['per_m2'] / 1e6, 2)} juta sudah dekat asumsi owner Rp {idn(t3.PAGU_HARGA, 0)} juta. Pagu cukup untuk "
              f"±{idn(r['luas_pagu'], 0)} m²: owner menaikkan pagu atau memakai opsi lingkup 3.8 (V1, V5, V6).")
    # 5 Verifikasi dan acuan
    s = Lembar(wb.create_sheet("Verifikasi dan Acuan"), 5, "Cek silang T-121 dan acuan", [9, 50, 19, 19, 12, 14, 10])
    rows = [[b["kode"], b["besaran"], round(b["x1"]), round(b["x2"]), round(b["selisih"], 2),
             f"{TOL[b['kode']][0]:g} s.d. +{TOL[b['kode']][1]:g} %" if isinstance(TOL[b["kode"]], tuple) else f"≤ Rp {TOL[b['kode']]:g}",
             "lolos" if b["lolos"] else "gagal"] for b in cs]
    rows.append(["T-121c", "Total RAB: rumus Excel (dihitung Excel) vs Python", "lihat Ringkasan", round(r["total"]), "", "≤ 0,01 %",
                 "lihat md"])
    s.tabel(["Kode", "Besaran", "Cara 1", "Cara 2", "Selisih (% / Rp)", "Batas", "Hasil"], rows,
            rata=list("clrrrcc"), fmt=[None, None, rp, rp, "#,##0.00", None, None])
    s.kosong()
    s.bagian("B", "Acuan")
    s.tabel(["No", "Acuan", "Dipakai untuk", "", "", "", "Status"], [
        [1, "Permen PUPR 8/2023 Ps. 11 ayat (3) hal. 9", "BTL 12 % (dalam harga satuan 8a)", "", "", "", "publik"],
        [2, "Permen PUPR 8/2023 Ps. 22 hal. 12", "SMKK biaya tersendiri", "", "", "", "publik"],
        [3, "SE Dirjen Binkon 47/2026 Lampiran III", "9 komponen SMKK, CAR 0,1 %", "", "", "", "publik"],
        [4, "Permen PUPR 22/2018 Ps. 29 (Tahap 3.8)", "persentase MEP RS", "", "", "", "publik"],
        [5, "TOR owner butir 6", "pagu Rp 168 miliar", "", "", "", "proyek"],
        [6, "Harga dasar dan lumsum", "persiapan, tapak, SMKK, VE", "", "", "", "[Asumsi: Jambi 2026]"],
    ], rata=list("clllllc"), beku=False)
    # 1 Ringkasan (rekapitulasi rumus)
    s = Lembar(wb.create_sheet("Ringkasan", 0), 1, "Rekapitulasi RAB Tahap 8b", [8, 60, 21, 12])
    s.catatan(f"STATUS: {STATUS}. {LABEL}")
    s.catatan("Petunjuk: lembar 2 RAB per divisi (rumus volume × harga), lembar 3 SMKK, lembar 4 value engineering, lembar 5 "
              "cek silang dan acuan. Rekap di bawah merujuk subtotal lembar 2-3. Hitung ulang: "
              ".venv\\Scripts\\python.exe skrip\\tahap8_rab.py")
    s.kosong()
    s.bagian("A", "Rekapitulasi")
    r0 = s.baris + 1
    C = s.kol(2)
    rows = [[no, nama, f"={alamat[no]}", ""] for no, nama, _ in r["sub"]]
    rows.append(["VII", "Biaya penerapan SMKK (tanpa BTL)", f"={alamat['VII']}", ""])
    rj = r0 + len(rows)
    rows += [["", "Jumlah I-VII", f"=SUM({C}{r0}:{C}{rj - 1})", ""],
             ["", f"PPN {PPN * 100:g} % [Asumsi: tarif efektif, 3.8]", f"={PPN}*{C}{rj}", ""],
             ["", "Total termasuk PPN", f"={C}{rj}+{C}{rj + 1}", ""],
             ["", "Total dibulatkan (juta)", f"=ROUND({C}{rj + 2},-6)", ""],
             ["", f"Biaya per m² luas kotor {idn(LUAS, 0)} m²", f"={C}{rj + 3}/{LUAS}", ""],
             ["", "Pagu owner (TOR butir 6)", PAGU, ""],
             ["", "Selisih terhadap pagu", f"={C}{rj + 3}-{C}{rj + 5}", ""]]
    for i in range(len(r["sub"]) + 1):
        rows[i][3] = f"={C}{r0 + i}/{C}{rj}"
    s.tabel(["No", "Uraian", "Jumlah (Rp)", "Porsi"], rows, rata=list("clrr"), fmt=[None, None, rp, "0.0%"])
    s.catatan(f"Nilai Python: total Rp {idn(r['total'], 0)}; dibulatkan Rp {idn(r['bulat'] / 1e9, 2)} miliar "
              f"(Rp {idn(r['per_m2'] / 1e6, 2)} juta/m²).")
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar, f"{C}{rj + 2}"


def cek_excel(keluar=KELUAR, sel=None):
    """T-121c: total rumus Excel (setelah dihitung Excel) vs Python."""
    import openpyxl
    from format_dokumen import hitung_ulang_excel
    ok, err = hitung_ulang_excel(keluar)
    if not ok:
        return None, err
    x = openpyxl.load_workbook(keluar, data_only=True)["Ringkasan"][sel].value
    py = rekap()["total"]
    return (x / py - 1) * 100 if x else None, ""


def tulis_md(t121c, keluar=KELUAR.with_suffix(".md")):
    r = rekap()
    v = ve()
    cs = cek_silang()
    jt = lambda x: idn(x / 1e6, 1)  # noqa: E731
    L = ["# 8b RAB, SMKK, Value Engineering", "",
         f"Status: {STATUS}. {LABEL}", "",
         "Skrip `skrip/tahap8_rab.py`, Excel `08 RAB/8b RAB SMKK VE.xlsx` (5 lembar, rekap dan jumlah dengan rumus). "
         "Keputusan K8-8..K8-11: `08 RAB/00 Rencana Tahap 8.md`.", "",
         "## 1. Rekapitulasi", "", "| No | Uraian | Jumlah (Rp juta) | Porsi (%) |", "|---|---|---:|---:|"]
    for no, nama, j in r["sub"]:
        L.append(f"| {no} | {nama} | {jt(j)} | {idn(j / r['jumlah'] * 100, 1)} |")
    L += [f"| VII | Biaya penerapan SMKK | {jt(r['j_smkk'])} | {idn(r['j_smkk'] / r['jumlah'] * 100, 1)} |",
          f"| | **Jumlah I-VII** | **{jt(r['jumlah'])}** | 100,0 |",
          f"| | PPN {PPN * 100:g} % | {jt(r['ppn'])} | |",
          f"| | **Total dibulatkan** | **{jt(r['bulat'])}** | |",
          f"| | Biaya per m² ({idn(LUAS, 0)} m² kotor) | {idn(r['per_m2'] / 1e6, 2)} juta/m² | |", "",
          "## 2. Rincian di luar model BIM", "",
          "- MEP RS (K8-8): " + "; ".join(f"{x['uraian'].split(' (')[0]} {jt(x['jumlah'])}" for x in mep()) + " (Rp juta).",
          f"- SMKK 9 komponen SE 47/2026 Lampiran III, {len(r['smkk'])} rincian, Rp {jt(r['j_smkk'])} juta "
          f"({idn(r['j_smkk'] / r['fisik'] * 100, 2)} % biaya fisik); CAR 0,1 % (hal. 260).",
          "- Persiapan, drainase, kolam retensi: lumsum/volume [Asumsi: Jambi 2026]; pematangan lahan dari 3.8 `lahan_nyata()`.",
          "", "## 3. Value engineering", "", "| Kode | Usulan | Volume | Hemat (Rp juta) | Porsi (%) | Akibat dan syarat |",
          "|---|---|---:|---:|---:|---|"]
    for o in v:
        L.append(f"| {o['kode']} | {o['uraian']} | {o['volume']} | {jt(o['hemat'])} | {idn(o['porsi'], 2)} | {o['akibat']} |")
    hv = sum(o["hemat"] for o in v)
    L += ["", f"Total VE Rp {idn(hv / 1e9, 2)} miliar ({idn(hv / r['bulat'] * 100, 1)} %); setelah VE Rp {idn(v[-1]['sisa'] / 1e9, 1)} "
          f"miliar terhadap pagu Rp {idn(PAGU / 1e9, 1)} miliar (selisih {idn((v[-1]['sisa'] - PAGU) / 1e9, 1)} miliar).", "",
          f"Kesimpulan (atas delegasi Defsa): biaya per m² Rp {idn(r['per_m2'] / 1e6, 2)} juta sudah sekitar asumsi owner "
          f"Rp {idn(t3.PAGU_HARGA, 0)} juta/m², tetapi luas kotor {idn(LUAS, 0)} m² jauh di atas {idn(t3.PAGU_LUAS, 0)} m² dasar pagu. "
          f"VE saja tidak menutup selisih; pagu cukup untuk ±{idn(r['luas_pagu'], 0)} m². Rekomendasi: owner menaikkan pagu ke "
          f"±Rp {idn(v[-1]['sisa'] / 1e9, 0)} miliar (dengan VE-1..VE-5) atau pembangunan bertahap memakai opsi lingkup 3.8 "
          "(V1 rampingkan podium LT3, V5 tunda LT4 parkir, V6 LT6 cangkang).", "",
          "## 4. Cek silang (T-121)", "", "| Kode | Besaran | Cara 1 (Rp juta) | Cara 2 (Rp juta) | Selisih | Batas | Hasil |",
          "|---|---|---:|---:|---:|---|---|"]
    for b in cs:
        tol = TOL[b["kode"]]
        bt = f"{tol[0]:g} s.d. +{tol[1]:g} %" if isinstance(tol, tuple) else f"≤ Rp {tol:g}"
        sl = f"{idn(b['selisih'], 1)} %" if isinstance(tol, tuple) else f"Rp {idn(b['selisih'], 2)}"
        L.append(f"| {b['kode']} | {b['besaran']} | {jt(b['x1'])} | {jt(b['x2'])} | {sl} | {bt} | {'lolos' if b['lolos'] else 'gagal'} |")
    L.append(f"| T-121c | Total RAB rumus Excel vs Python | | | {'-' if t121c is None else idn(t121c, 4) + ' %'} | ≤ 0,01 % | "
             f"{'belum' if t121c is None else ('lolos' if abs(t121c) <= TOL['T-121c'] else 'gagal')} |")
    L += ["", "## 5. Catatan", "",
          "- T-121a/b membandingkan RAB rinci dengan perkiraan konsep 3.8. Perkiraan 3.8 menambahkan nonstandar dan fondasi dalam "
          "di atas biaya standar HSBGN (Permen PUPR 22/2018), sedangkan RAB menghitung volume nyata dari model; selisih di luar "
          "batas dijelaskan di Ringkasan Tahap 8.",
          "- MEP memakai persentase 3.8, bukan volume dari model MEP (model MEP 7.2 hanya koordinasi); MEP rinci menunggu konsultan MEP.",
          "- Harga [Asumsi: Jambi 2026], belum survei harga SE 47/2026 Lampiran I.", ""]
    keluar.write_text("\n".join(L), encoding="utf-8")
    return keluar


if __name__ == "__main__":
    x, sel = buat_excel()
    t121c, err = cek_excel(x, sel)
    print("Excel:", x, "T-121c:", t121c, err)
    print("md:", tulis_md(t121c))
    r = rekap()
    for no, nama, j in r["sub"]:
        print(no, nama, round(j / 1e9, 2))
    print("SMKK", round(r["j_smkk"] / 1e9, 3), "total", round(r["bulat"] / 1e9, 2), "per m2", round(r["per_m2"] / 1e6, 2))
    for b in cek_silang():
        print(b["kode"], round(b["selisih"], 2), b["lolos"])
    for o in ve():
        print(o["kode"], round(o["hemat"] / 1e9, 2))
