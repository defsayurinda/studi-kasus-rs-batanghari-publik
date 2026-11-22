"""Tahap 6 langkah 6.1: daya dukung tiang bor tunggal Ø800 (tekan, tarik, panjang per zona), tiga metode.

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (21 Nov 2026); disetujui Defsa 21 Nov
2026. Kunci jawaban tidak dibuka. Profil tanah dan sigma'v diimpor dari `tahap3_pondasi` (tidak disalin).

Acuan (halaman = nomor halaman PDF di acuan/; nomor cetak dalam kurung):
- Metode A, FHWA-NHI-18-024 GEC10 Drilled Shafts (acuan/pustaka): hal. 289 (10-9) Pers. 10-3, 10-4 (RSN = pi B dz fSN;
  RBN = pi/4 B2 qBN); hal. 290 (10-10) Pers. 10-5..10-7 (fSN = beta sigma'v); hal. 291 (10-11) Pers. 10-9
  (Ko = (1 - sin phi') OCR^sin phi' <= Kp), Pers. 10-11 (sigma'p = 0,47 pa N60^m, m = 0,6 pasir bersih), Pers. 10-13
  (beta; beta dibatasi pada kedalaman 7,5 ft, sigma'v +-900 psf = 43 kPa); hal. 293 (10-13) phi' = 27,5 + 9,2 log N60;
  hal. 294 (10-14) Pers. 10-14 (qBN = 0,60 N60 tsf <= 30 tsf, N60 <= 50); hal. 295 (10-15) Pers. 10-15 (alpha);
  hal. 296 (10-16) Pers. 10-18 (alpha = 0,30 + 0,17 / (su/pa)); hal. 297 (10-17) selimut 5 ft teratas diabaikan, casing
  permanen mereduksi 50-75 %; hal. 222 (8-14) Tabel 8-4 faktor tahanan: selimut pasir 0,55 / 0,45 (tekan / tarik),
  selimut lempung 0,45 / 0,35, ujung pasir 0,50; hal. 319 (10-39) Pers. 10-32 tarik: berat tiang sebagai beban, tanpa
  tahanan ujung, faktor 0,80 untuk gempa; hal. 332 (10-52) gempa: su = 80 % nilai CIUC, faktor tahanan tekan 1,0
  (Extreme Event I), downdrag likuifaksi 50 % selimut beta.
- Metode B, SNI 8460:2017 (acuan/privat; hal. = PDF, nomor cetak = hal. - 18): hal. 204 (186 dari 303) Pasal 9.7.2.1
  Pers. (1) Q = Qs + Qb, f dan q tidak dirumuskan SNI; hal. 194 (176) Pasal 9.2.3.1 (analitik baku "Reese", FK >= 2,5
  fondasi dalam); hal. 197 (179) Pasal 9.3.3 b (uplift >= 1,5 untuk sistem); hal. 295 FK likuifaksi > 1,1 [seperti
  Tahap 3]. Rumus f dan q mengikuti Reese dan O'Neill lewat FHWA-NHI-06-089 Vol II (acuan/pustaka) hal. 239 (9-129)
  Pers. 9-36..9-38 (alpha 0,55), hal. 242-243 (9-132/133) Pers. 9-42, 9-43 (beta = 1,5 - 0,135 sqrt(z ft), 0,25-1,2,
  fs <= 191 kPa), Pers. 9-45a (qt = 1,2 N60 ksf = 57,5 N60 kPa, maks 4.309 kPa); sama dengan Tahap 3 (3.7).
- Metode C, korelasi SPT: phi' = min(phi' desain, 27,5 + 9,2 log N60) [GEC10 hal. 293], K = Ko dengan OCR = 1
  [GEC10 Pers. 10-9 tanpa OCR; Asumsi], ujung NHI-06-089 Pers. 9-45a. Sondir: data S-01..S-06 hanya sampai 20 m (U6
  baru mulai 32-33 m), tidak mencapai U6/U7: dilewati. Metode sondir [Literatur, belum ada di acuan/].
Kasus gempa: U5 pasir dinolkan (likuifaksi FS 0,22-0,75, langkah 2.6); gesekan negatif ada di 6.2, tidak masuk di sini.
Label status: "DIISI AI ATAS PERMINTAAN DEFSA (21 Nov 2026), sel hijau; disetujui Defsa 21 Nov 2026."
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import tahap3_pondasi as t3  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "06 Struktur Bawah dan Basement"
BERKAS = KELUAR / "6.1 Daya Dukung Tiang.xlsx"
MD = KELUAR / "6.1 Daya Dukung Tiang.md"
VERIFIKASI = AKAR / "VERIFIKASI.md"

LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
STATUS = "disetujui Defsa 21 Nov 2026"
LABEL_AI = f"DIISI AI ATAS PERMINTAAN DEFSA (21 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."

D = 0.8                      # m, tiang bor BOR-800
KEPALA = 10.85               # m, kepala tiang (6.0)
PA = 101.325                 # kPa
TSF = 95.76                  # kPa per tsf
FK, FK_GM, FK_TARIK, FK_TARIK_GM = 2.5, 1.1, 2.5, 1.1   # SNI 8460 hal. 194, 295; tarik gempa [Asumsi]
GAMMA_C, GAMMA_W = 24.0, 9.81
PHI = {"U5": 33.0, "U7": 38.0}   # phi' desain (2.4): U7 dibatasi 38
TARGET = 911.0               # kN, izin Tahap 3
ZONA = ["SELATAN", "UTARA", "TENGAH"]
NAMA_METODE = {"A": "A. FHWA GEC10 (2018)", "B": "B. SNI 8460:2017 + Reese dan O'Neill",
               "C": "C. Korelasi SPT (phi' dari N60)"}
KODE = "BOR-800"
TOL = {"excel": 0.5, "t3": 0.5, "sebaran": 30.0}   # persen; ditetapkan sebelum membandingkan


def idn(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def u7_atas(zona):
    return next(lp for lp in t3.PROFIL[zona]["lapisan"] if lp[0] == "U6")[1]


def irisan(zona, ujung=None, langkah=0.25):
    """Irisan 0,25 m seperti t3.kapasitas (titik tengah, z < ujung)."""
    ujung = ujung or t3.PROFIL[zona]["ujung"]
    out, z = [], langkah / 2
    while z < ujung:
        unit, _, _, jenis, su, n60 = t3.lapisan_di(z, zona)
        out.append({"z": z, "dz": langkah, "unit": unit, "jenis": jenis, "su": su, "n60": n60,
                    "sv": t3.sigma_v(z, zona), "phi": PHI.get(unit)})
        z += langkah
    return out


def ikut(unit, kasus, u5_statis=True):
    """1 bila lapisan menyumbang tahanan: U1-U4 tidak; U5 hanya statis; U6, U7 selalu."""
    if unit in ("U1", "U2", "U3", "U4"):
        return 0
    if unit == "U5":
        return 1 if (kasus == "statis" and u5_statis) else 0
    return 1


def fs_unit(metode, s, kasus):
    """Gesekan selimut satuan (kPa) irisan s; 0 untuk lapisan yang tidak menyumbang."""
    if s["unit"] in ("U1", "U2", "U3", "U4"):
        return 0.0
    if s["jenis"] == "lempung":
        if metode == "A":
            su = s["su"] * (0.8 if kasus == "gempa" else 1.0)          # GEC10 hal. 332
            return (0.30 + 0.17 / (su / PA)) * su                        # Pers. 10-18
        return 0.55 * s["su"]                                            # NHI-06-089 Pers. 9-37a
    sv, n = s["sv"], s["n60"]
    if metode == "A":
        r = math.radians(s["phi"])
        sp = 0.47 * PA * n ** 0.6                                        # Pers. 10-11
        ko = (1 - math.sin(r)) * (sp / max(sv, 43.1)) ** math.sin(r)     # Pers. 10-9, beta dibatasi pada 43 kPa
        kp = math.tan(math.radians(45 + s["phi"] / 2)) ** 2
        return min(ko, kp) * math.tan(r) * sv
    if metode == "B":
        beta = min(1.2, max(0.25, 1.5 - 0.135 * math.sqrt(s["z"] / 0.3048)))
        return min(beta * sv, 191.0)
    phi = min(s["phi"], 27.5 + 9.2 * math.log10(n))
    r = math.radians(phi)
    return (1 - math.sin(r)) * math.tan(r) * sv


def qb_unit(metode, n60):
    if metode == "A":
        return 0.6 * min(n60, 50) * TSF
    return min(57.5 * n60, 4309.0)


def berat_tiang(zona, ujung):
    elev = t3.PROFIL[zona]["elev"]
    atas = max(0.0, KEPALA - (elev - t3.MAT))
    bawah = ujung - t3.MAT
    return math.pi * D ** 2 / 4 * (GAMMA_C * atas + (GAMMA_C - GAMMA_W) * bawah)


def hitung(metode, zona, ujung=None, u5_statis=True):
    """Qs per unit, Qb, Qult statis/gempa, Tult, izin untuk satu metode dan zona. ujung = kedalaman dari tanah asli."""
    ujung = ujung or t3.PROFIL[zona]["ujung"]
    kel = math.pi * D
    per = {}
    for s in irisan(zona, ujung):
        u = per.setdefault(s["unit"], {"tebal": 0.0, "Qs_st": 0.0, "Qs_gm": 0.0})
        u["tebal"] += s["dz"]
        for kasus, k in (("statis", "Qs_st"), ("gempa", "Qs_gm")):
            u[k] += fs_unit(metode, s, kasus) * ikut(s["unit"], kasus, u5_statis) * kel * s["dz"]
    for u in per.values():
        u["fs_rata"] = u["Qs_st"] / (kel * u["tebal"]) if u["tebal"] else 0.0
    qs_st = sum(u["Qs_st"] for u in per.values())
    qs_gm = sum(u["Qs_gm"] for u in per.values())
    n60 = t3.lapisan_di(ujung, zona)[5] or 30
    qb = qb_unit(metode, n60) * math.pi * D ** 2 / 4
    w = berat_tiang(zona, ujung)
    r = {"metode": metode, "zona": zona, "ujung": ujung, "n60_ujung": n60, "per": per, "Qs_st": qs_st, "Qs_gm": qs_gm,
         "Qb": qb, "Qult_st": qs_st + qb, "Qult_gm": qs_gm + qb, "W": w,
         "panjang": KEPALA - t3.PROFIL[zona]["elev"] + ujung}
    r["Tult_st"], r["Tult_gm"] = qs_st + w, qs_gm + w
    r["izin_st"], r["izin_gm"] = r["Qult_st"] / FK, r["Qult_gm"] / FK_GM
    r["izin"] = min(r["izin_st"], r["izin_gm"])
    nsf = t3.kapasitas(KODE, ujung=ujung, profil=zona)
    r["NSF_st"], r["NSF_lik"] = nsf["NSF_statis"], nsf["NSF_lik"]
    r["izin_t3"] = min(r["Qult_st"] / FK - r["NSF_st"], r["Qult_gm"] / FK_GM - r["NSF_lik"])
    r["izin_tarik"] = min(r["Tult_st"] / FK_TARIK, r["Tult_gm"] / FK_TARIK_GM)
    return r


def lrfd_A(r):
    """Tahanan terfaktor GEC10 (Tabel 8-4, hal. 222): statis dan gempa (Extreme Event I, phi 1,0 tekan; tarik 0,80)."""
    s = r["per"]
    sel_pasir = sum(s.get(u, {}).get("Qs_st", 0) for u in ("U5", "U7"))
    sel_lempung = s.get("U6", {}).get("Qs_st", 0)
    return {"tekan_st": 0.55 * sel_pasir + 0.45 * sel_lempung + 0.50 * r["Qb"],
            "tekan_gm": r["Qs_gm"] + r["Qb"],
            "tarik_st": 0.45 * sel_pasir + 0.35 * sel_lempung,
            "tarik_gm": 0.80 * r["Qs_gm"]}


def semua():
    return {(m, z): hitung(m, z) for m in "ABC" for z in ZONA}


def cari_benam(metode, zona, target=TARGET, setara_t3=False):
    """Benam minimum ke U7 (langkah 0,5 m) agar izin >= target. Setara T3: izin dikurangi NSF Tahap 3."""
    top = u7_atas(zona)
    e = 0.5
    while e <= 14.0:
        r = hitung(metode, zona, ujung=top + e)
        if (r["izin_t3"] if setara_t3 else r["izin"]) >= target:
            return e, r
        e += 0.5
    return None, None


def panjang_usulan(zona, benam):
    return math.ceil((KEPALA - t3.PROFIL[zona]["elev"] + u7_atas(zona) + benam) * 2 - 1e-9) / 2


def panjang_zona():
    out = {}
    for z in ZONA:
        e1, r1 = cari_benam("A", z)
        e2, r2 = cari_benam("A", z, setara_t3=True)
        out[z] = {"benam_t3": 4.0, "L_t3": hitung("A", z)["panjang"],
                  "benam": e1, "izin": r1["izin"] if r1 else None, "L": panjang_usulan(z, e1) if e1 else None,
                  "benam_nsf": e2, "izin_nsf": r2["izin_t3"] if r2 else None,
                  "L_nsf": panjang_usulan(z, e2) if e2 else None}
    return out


def sebaran(hasil=None):
    """Sebaran Qult statis dan gempa A/B/C per zona: simpangan terbesar dari rata-rata tiga metode (%)."""
    hasil = hasil or semua()
    out = {}
    for z in ZONA:
        for k in ("Qult_st", "Qult_gm"):
            v = [hasil[(m, z)][k] for m in "ABC"]
            mean = sum(v) / 3
            out[(z, k)] = {"v": v, "mean": mean, "dev": max(abs(x - mean) / mean for x in v) * 100}
    return out


def reproduksi_t3():
    """Setelan Tahap 3 (metode B, U5 tidak dihitung) terhadap t3.kapasitas / t3.beban_izin: selisih % per zona."""
    out = {}
    for z in ZONA:
        a = hitung("B", z, u5_statis=False)
        b = t3.beban_izin(KODE, profil=z)
        izin_a = min(a["Qult_st"] / FK - a["NSF_st"], a["Qult_gm"] / FK_GM - a["NSF_lik"])
        out[z] = {"Qult": a["Qult_st"], "Qult_t3": b["Qult"], "izin": izin_a, "izin_t3": b["izin"],
                  "dQ": (a["Qult_st"] - b["Qult"]) / b["Qult"] * 100, "dI": (izin_a - b["izin"]) / b["izin"] * 100}
    return out




# ------------------------------------------------------------------ Excel
ACUAN = [
    ("FHWA-NHI-18-024 GEC10, bab 10 (selimut beta dan alpha, ujung SPT, tarik, gempa) dan Tabel 8-4",
     "ada", "acuan/pustaka/FHWA-NHI-18-024-GEC10-Drilled-Shafts.pdf; hal. 222, 289-297, 319, 332 (PDF)"),
    ("FHWA-NHI-06-089 Vol II, Pers. 9-36..9-45 (alpha 0,55, beta, ujung SPT)", "ada",
     "acuan/pustaka/FHWA-NHI-06-089-Soils-and-Foundations-Vol-II.pdf; hal. 239, 242-243 (PDF)"),
    ("SNI 8460:2017 Pasal 9.2.3.1 (FK >= 2,5), 9.3.3 b (uplift 1,5), 9.7.2.1 Pers. (1), FK likuifaksi 1,1", "ada",
     "acuan/privat/SNI-8460-2017-...pdf; hal. 194, 197, 204, 295 (PDF). Rumus f dan q tidak ada di SNI."),
    ("Rumus gesekan dan ujung di SNI 8460 (selain Pers. 1)", "belum ada",
     "Tidak dirumuskan SNI; dirujuk ke Reese lewat NHI-06-089 dan GEC10."),
    ("Reese dan O'Neill (1988/1989) asli, FHWA-IF-99-025", "belum ada",
     "Hanya lewat ringkasan GEC10 dan NHI-06-089; halaman asli tidak ditebak."),
    ("Metode sondir untuk tiang bor (mis. Schmertmann, Aoki-De Alencar)", "belum ada",
     "[Literatur, belum ada di acuan/]; data sondir S-01..S-06 hanya sampai 20 m, tidak mencapai U6/U7."),
]

KEPUTUSAN = [
    ("Metode utama", "Metode A (GEC10) sebagai metode utama; B (SNI + Reese dan O'Neill) dan C (korelasi SPT) sebagai "
     "pembanding. Izin tekan = min(Qult statis / 2,5; Qult gempa / 1,1) tanpa gesekan negatif."),
    ("Lapisan yang menyumbang", "U1-U4 nol (zona urugan dan penurunan, gesekan negatif di 6.2). U5 hanya statis, nol saat "
     "gempa (likuifaksi FS 0,22-0,75). U6 dan U7 selalu."),
    ("su U6 gempa", "Metode A memakai 0,8 su U6 saat gempa (GEC10 hal. 332). Metode B dan C tidak (tanpa dasar di NHI-06-089)."),
    ("su U6 tidak dikonversi UU ke CIUC", "su 85 kPa dipakai langsung [Asumsi]. Konversi Pers. 10-17 akan menaikkan su "
     "(konservatif bila diabaikan); jenis uji su di 2.4 perlu dikonfirmasi."),
    ("N60 dan phi' U7", "N60 U7 = 30 (penolakan dibatasi), phi' 38 dibatasi, N60 U5 = 12, phi' U5 = 33 (2.4, 2.6)."),
    ("FK tarik", "Selimut + berat efektif tiang dibagi 2,5 (statis, Pasal 9.2.3.1) dan 1,1 (gempa) [Asumsi: 1,1 sejajar "
     "tekan]. SNI Pasal 9.3.3 b memberi 1,5 untuk ketahanan angkat sistem; belum ada FK tarik tiang tunggal sendiri."),
    ("Panjang tiang", "Usulan sementara = panjang setara Tahap 3 (izin 911 kN setelah dikurangi NSF Tahap 3): "
     "Selatan 37,5; Utara 36,5; Tengah 36,5 m (Tahap 3: 38,45; 38,24; 38,21). Keputusan Defsa 21 Nov 2026: tetap 38,45 m "
     "sampai gesekan negatif 6.2 dan uji beban awal."),
    ("Sondir", "Tidak dipakai karena hanya sampai 20 m; metode sondir belum ada di acuan/."),
    ("LRFD", "Tahanan terfaktor GEC10 hanya dicatat; dibandingkan dengan Pu 5.6 di langkah lanjut, bukan di 6.1."),
]


def _fmt3(r):
    return round(r, 3)


def _nama(m, z):
    return f"Metode {m} {z.capitalize()}"


def _lembar_irisan(wb, metode, zona, h):
    """Satu lembar irisan 0,25 m dengan rumus Excel hidup. Kembalikan alamat sel hasil."""
    from format_dokumen import AI, Lembar

    nama = _nama(metode, zona)
    lb = Lembar(wb.create_sheet(nama), f"{ 'ABC'.index(metode) * 2 + (1 if zona == 'SELATAN' else 2) + 2}",
                f"{NAMA_METODE[metode]}: tiang tunggal Ø800, zona {zona.lower()}",
                [8, 9, 9, 9, 10, 10, 9, 8, 8, 8, 8, 11, 11, 13, 13])
    sl = irisan(zona)
    ket = {"A": "Pers. 10-18 (alpha), 10-9/10-11/10-13 (beta, sigma'p), 10-14 (ujung); gempa su U6 x 0,8.",
           "B": "NHI-06-089 Pers. 9-37a (alpha 0,55), 9-42/9-43 (beta, fs <= 191), 9-45a (ujung); SNI 8460 Pers. (1).",
           "C": "phi' = min(phi' desain, 27,5 + 9,2 log N60) [GEC10 hal. 293], K = 1 - sin phi' (OCR 1) [Asumsi], "
                "ujung NHI-06-089 Pers. 9-45a."}[metode]
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.catatan(f"Irisan 0,25 m dari muka tanah asli (z = titik tengah); sigma'v dari tahap3_pondasi.sigma_v (urugan "
               f"terkonsolidasi, MAT 0,7 m). {ket} Kolom 'Ikut' = 1 bila lapisan menyumbang (U1-U4 nol; U5 statis saja).")
    lb.kosong()
    lb.bagian("A", "Parameter")
    r0, p1, _ = lb.tabel(["D (m)", "pa (kPa)", "N60 ujung", "qb (kPa)", "FK statis", "FK gempa", "Ujung z (m)"],
                         [[D, PA, h["n60_ujung"], None, FK, FK_GM, round(h["ujung"], 2)]],
                         rata=list("ccccccc"), fmt=["0.00", "0.000", "0", "#,##0.0", "0.0", "0.0", "0.00"],
                         fill=AI, beku=False)
    Dc, pac = f"$C${p1}", f"$D${p1}"
    qb = (f"=0.6*MIN(E{p1},50)*{TSF}" if metode == "A" else f"=MIN(57.5*E{p1},4309)")
    lb.ws[f"F{p1}"].value = qb
    lb.kosong()
    lb.bagian("B", "Hasil per lapisan dan total")
    s0 = lb.baris
    sl1 = s0 + 11
    sl2 = sl1 + len(sl) - 1
    rng = lambda c: f"${c}${sl1}:${c}${sl2}"   # noqa: E731
    rows = []
    for k, u in enumerate(("U5", "U6", "U7")):
        r = s0 + 1 + k
        rows.append([u, f"=SUMIFS({rng('E')},{rng('F')},C{r})",
                     f"=SUMIFS({rng('P')},{rng('F')},C{r})", f"=SUMIFS({rng('Q')},{rng('F')},C{r})",
                     f"=IF(D{r}>0,E{r}/(PI()*{Dc}*D{r}),0)"])
    t = s0 + 4
    rows.append(["Selimut Qs", f"=SUM(D{s0 + 1}:D{s0 + 3})", f"=SUM(E{s0 + 1}:E{s0 + 3})",
                 f"=SUM(F{s0 + 1}:F{s0 + 3})", None])
    rows.append(["Ujung Qb", None, f"=F{p1}*PI()*{Dc}^2/4", f"=F{p1}*PI()*{Dc}^2/4", None])
    rows.append(["Qult", None, f"=E{t}+E{t + 1}", f"=F{t}+F{t + 1}", None])
    rows.append(["Izin tekan = Qult / FK", None, f"=E{t + 2}/G{p1}", f"=F{t + 2}/H{p1}", f"=MIN(E{t + 3},F{t + 3})"])
    lb.tabel(["Lapisan", "Tebal (m)", "Statis (kN)", "Gempa (kN)", "fs rata statis (kPa); izin: min"], rows,
             rata=list("lcccc"), fmt=[None, "0.00", "#,##0.0", "#,##0.0", "#,##0.0"], fill=AI, beku=False)
    lb.kosong()
    lb.bagian("C", "Irisan 0,25 m")
    assert lb.baris == sl1 - 1, (lb.baris, sl1)
    rows = []
    for i, s in enumerate(sl):
        r = sl1 + i
        u = s["unit"]
        ikt, ikg = ikut(u, "statis"), ikut(u, "gempa")
        if u in ("U1", "U2", "U3", "U4"):
            fst = fgm = 0
        elif s["jenis"] == "lempung":
            if metode == "A":
                fst = f"=(0.3+0.17/(I{r}/{pac}))*I{r}"
                fgm = f"=(0.3+0.17/(0.8*I{r}/{pac}))*0.8*I{r}"
            else:
                fst, fgm = f"=0.55*I{r}", f"=N{r}"
        else:
            if metode == "A":
                fst = (f"=MIN((1-SIN(RADIANS(J{r})))*(0.47*{pac}*K{r}^0.6/MAX(H{r},43.1))^SIN(RADIANS(J{r})),"
                       f"TAN(RADIANS(45+J{r}/2))^2)*TAN(RADIANS(J{r}))*H{r}")
            elif metode == "B":
                fst = f"=MIN(MIN(1.2,MAX(0.25,1.5-0.135*SQRT(D{r}/0.3048)))*H{r},191)"
            else:
                ph = f"MIN(J{r},27.5+9.2*LOG10(K{r}))"
                fst = f"=(1-SIN(RADIANS({ph})))*TAN(RADIANS({ph}))*H{r}"
            fgm = f"=N{r}"
        rows.append([i + 1, round(s["z"], 3), s["dz"], u, s["jenis"], round(s["sv"], 4), s["su"], s["phi"] if u in PHI else None,
                     s["n60"], ikt, ikg, fst, fgm, f"=N{r}*L{r}*PI()*{Dc}*E{r}", f"=O{r}*M{r}*PI()*{Dc}*E{r}"])
    lb.tabel(["No", "z (m)", "dz (m)", "Unit", "Jenis", "sigma'v (kPa)", "su (kPa)", "phi' (°)", "N60", "Ikut statis",
              "Ikut gempa", "fs statis (kPa)", "fs gempa (kPa)", "Qs statis (kN)", "Qs gempa (kN)"], rows,
             rata=list("cccccccccccccc") + ["c"], fmt=[None, "0.000", "0.00", None, None, "0.0", "0.0", "0", "0", "0", "0",
                                                         "0.00", "0.00", "#,##0.00", "#,##0.00"], beku=False,
             fill_kolom={11: AI, 12: AI, 13: AI, 14: AI})
    q = f"'{nama}'!"
    return {"qs_st": f"{q}E{t}", "qs_gm": f"{q}F{t}", "qb": f"{q}E{t + 1}", "qult_st": f"{q}E{t + 2}",
            "qult_gm": f"{q}F{t + 2}", "izin_st": f"{q}E{t + 3}", "izin_gm": f"{q}F{t + 3}", "izin": f"{q}G{t + 3}"}


def buat_excel(keluar=BERKAS):
    import openpyxl
    from format_dokumen import AI, Lembar, set_font_bawaan

    h = semua()
    pz = panjang_zona()
    sb = sebaran(h)
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    ket_ai = LABEL + " " + LABEL_AI

    lr = Lembar(wb.create_sheet("Ringkasan"), 1, "Daya dukung tiang bor tunggal Ø800: tiga metode",
                [26, 10, 11, 11, 10, 11, 11, 11, 11, 11, 10, 10, 12])
    lp = Lembar(wb.create_sheet("Profil Tanah"), 2, "Profil tanah dan parameter hitungan", [6, 9, 9, 9, 10, 10, 9, 8, 9, 14, 14, 12])
    addr = {}
    for m in "ABC":
        for z in ("SELATAN", "UTARA"):
            addr[(m, z)] = _lembar_irisan(wb, m, z, h[(m, z)])

    # ---- Ringkasan
    lr.catatan(f"STATUS: {STATUS}. " + ket_ai)
    lr.catatan("Selatan dan Utara: rumus Excel hidup yang menunjuk ke lembar irisan. Tengah (BH-7): informasi saja, nilai "
               "dari skrip (tidak punya lembar irisan). Izin tekan tanpa gesekan negatif (6.2). Izin setara T3 = izin yang "
               "dikurangi gesekan negatif Tahap 3 (3.7), pembanding 911 kN.")
    lr.kosong()
    lr.bagian("A", "Hasil per metode dan zona (kN)")
    rows, ring = [], {}
    r0 = lr.baris
    for m in "ABC":
        for z in ZONA:
            r = r0 + 1 + len(rows)
            ring[(m, z)] = r
            x = h[(m, z)]
            if z == "TENGAH":
                row = [NAMA_METODE[m], z.capitalize(), x["Qs_st"], x["Qs_gm"], x["Qb"], x["Qult_st"], x["Qult_gm"],
                       x["izin_st"], x["izin_gm"], x["izin"]]
            else:
                a = addr[(m, z)]
                row = [NAMA_METODE[m], z.capitalize(), f"={a['qs_st']}", f"={a['qs_gm']}", f"={a['qb']}",
                       f"={a['qult_st']}", f"={a['qult_gm']}", f"=H{r}/{FK}", f"=I{r}/{FK_GM}", f"=MIN(J{r},K{r})"]
            row += [round(x["NSF_st"], 3), round(x["NSF_lik"], 3), f"=MIN(H{r}/{FK}-M{r},I{r}/{FK_GM}-N{r})"]
            rows.append(row)
    lr.tabel(["Metode", "Zona", "Qs statis", "Qs gempa", "Qb", "Qult statis", "Qult gempa", "Izin statis (FK 2,5)",
              "Izin gempa (FK 1,1)", "Izin tekan", "NSF statis T3", "NSF likuifaksi T3", "Izin setara T3"], rows,
             rata=list("lc") + ["c"] * 11, fmt=[None, None] + ["#,##0.0"] * 11, fill_kolom={i: AI for i in range(2, 13)},
             beku=True)
    lr.kosong()
    lr.bagian("B", "Temuan utama")
    a_s, a_u = h[("A", "SELATAN")], h[("A", "UTARA")]
    tem = [
        ["T1", f"Metode A selatan: Qult statis {idn(a_s['Qult_st'], 0)} kN, gempa {idn(a_s['Qult_gm'], 0)} kN, izin tekan "
               f"{idn(a_s['izin'], 0)} kN; utara {idn(a_u['Qult_st'], 0)} / {idn(a_u['Qult_gm'], 0)} / "
               f"{idn(a_u['izin'], 0)} kN."],
        ["T2", f"Sebaran Qult A/B/C paling lebar {idn(max(v['dev'] for v in sb.values()), 1)} % dari rata-rata tiga metode "
               "(batas 30 % [Asumsi]); metode B tertinggi (alpha dan beta Reese), C terendah pada selimut pasir U5."],
        ["T3", "Dengan setelan Tahap 3 (U5 tidak dihitung) metode B mereproduksi Qult dan izin Tahap 3 (T-99 b); izin 911 kN "
               "T3 sebagian besar diambil gesekan negatif (selatan 452 kN statis, 1.712 kN saat likuifaksi)."],
        ["T4", f"Panjang setara T3 (izin >= 911 kN setelah NSF T3): selatan {idn(pz['SELATAN']['L_nsf'], 1)} m, utara "
               f"{idn(pz['UTARA']['L_nsf'], 1)} m, tengah {idn(pz['TENGAH']['L_nsf'], 1)} m (Tahap 3: 38,45; 38,24; 38,21). "
               "Final menunggu NSF 6.2 dan uji beban."],
    ]
    for tm in tem:
        lr.catatan(f"{tm[0]}. {tm[1]}")

    # ---- Profil tanah
    lp.catatan(ket_ai + " Sumber: tahap3_pondasi.PROFIL (2.2, 2.4, 3.7). Kedalaman dari muka tanah asli tiap zona.")
    for z in ZONA:
        pr = t3.PROFIL[z]
        lp.kosong()
        lp.bagian({"SELATAN": "S", "UTARA": "U", "TENGAH": "T"}[z],
                  f"Zona {z.lower()} ({pr['titik']}, muka tanah +{idn(pr['elev'])}, ujung T3 {idn(pr['ujung'])} m)")
        rows, atas = [], 0.0
        for unit, bawah, g, jenis, su, n60 in pr["lapisan"]:
            zt = (atas + min(bawah, pr["ujung"])) / 2
            rows.append([unit, round(atas, 2), round(bawah, 2), g, jenis, su, n60, PHI.get(unit),
                         round(t3.sigma_v(min(zt, pr["ujung"]), z), 1),
                         "ya" if unit in ("U5", "U6", "U7") else "tidak", "tidak" if unit not in ("U6", "U7") else "ya",
                         "kasus statis" if unit == "U5" else ("selalu" if unit in ("U6", "U7") else "gesekan negatif 6.2")])
            atas = bawah
            if atas > pr["ujung"]:
                break
        lp.tabel(["Unit", "Atas (m)", "Bawah (m)", "γ (kN/m³)", "Jenis", "su (kPa)", "N60", "φ' (°)", "σ'v tengah (kPa)",
                  "Hitung statis", "Hitung gempa", "Catatan"], rows, rata=list("cccccccccccl"),
                 fmt=[None, "0.00", "0.00", "0.0", None, "0", "0", "0", "0.0", None, None, None], beku=False,
                 fill_kolom={8: AI})
    lp.kosong()
    lp.bagian("P", "Parameter umum")
    lp.catatan("D = 0,80 m (BOR-800, 3.7); kepala tiang +10,85 m (6.0); FK statis 2,5 dan gempa 1,1 (SNI 8460 hal. 194, 295); "
               "beton 24 kN/m³ dan air 9,81 kN/m³ [Asumsi: beton 24]; pa = 101,325 kPa (GEC10, 2.116 psf).")

    # ---- Tarik
    lt = Lembar(wb.create_sheet("Tarik"), 9, "Tahanan tarik (uplift) tiang tunggal",
                [26, 10, 11, 11, 10, 10, 11, 11, 11, 11])
    lt.catatan(ket_ai + " Tult = Qs (selimut yang sama per kasus) + berat efektif tiang (24 kN/m³ di atas MAT, apung di bawah "
               "MAT). Tanpa tahanan ujung (GEC10 hal. 318). FK tarik 2,5 statis, 1,1 gempa [Asumsi, SNI 9.2.3.1].")
    lt.kosong()
    lt.bagian("A", "Tult dan izin tarik (kN)")
    rows = []
    t0 = lt.baris
    for m in "ABC":
        for z in ZONA:
            r = t0 + 1 + len(rows)
            x = h[(m, z)]
            elev = t3.PROFIL[z]["elev"]
            atas = max(0.0, KEPALA - (elev - t3.MAT))
            bawah = x["ujung"] - t3.MAT
            if z == "TENGAH":
                qs1, qs2 = x["Qs_st"], x["Qs_gm"]
            else:
                qs1, qs2 = f"='Ringkasan'!E{ring[(m, z)]}", f"='Ringkasan'!F{ring[(m, z)]}"
            rows.append([NAMA_METODE[m], z.capitalize(), qs1, qs2, round(atas, 3), round(bawah, 3),
                         f"=PI()*{D}^2/4*({GAMMA_C}*G{r}+({GAMMA_C}-{GAMMA_W})*H{r})", f"=E{r}+I{r}", f"=F{r}+I{r}",
                         f"=MIN(J{r}/{FK_TARIK},K{r}/{FK_TARIK_GM})"])
    lt.tabel(["Metode", "Zona", "Qs statis", "Qs gempa", "Tiang atas MAT (m)", "Tiang bawah MAT (m)", "Berat efektif W'",
              "Tult statis", "Tult gempa", "Izin tarik"], rows, rata=list("lc") + ["c"] * 8,
             fmt=[None, None, "#,##0.0", "#,##0.0", "0.00", "0.00"] + ["#,##0.0"] * 4,
             fill_kolom={i: AI for i in range(2, 10)}, beku=False)
    lt.kosong()
    lt.bagian("B", "Tahanan terfaktor LRFD, metode A (GEC10 Tabel 8-4 hal. 222; Pers. 10-2, 10-32)")
    rows = []
    for z in ZONA:
        L = lrfd_A(h[("A", z)])
        rows.append([z.capitalize(), L["tekan_st"], L["tekan_gm"], L["tarik_st"], L["tarik_gm"],
                     h[("A", z)]["Qult_st"] / L["tekan_st"]])
    lt.tabel(["Zona", "Tekan statis", "Tekan gempa (phi 1,0)", "Tarik statis", "Tarik gempa (phi 0,80)", "Qult / terfaktor"],
             rows, rata=["l"] + ["c"] * 5, fmt=[None] + ["#,##0.0"] * 4 + ["0.00"], fill_kolom={i: AI for i in range(1, 6)},
             beku=False)
    lt.catatan("Faktor: selimut pasir 0,55 (tekan) / 0,45 (tarik), selimut lempung 0,45 / 0,35, ujung pasir 0,50; gempa: tekan "
               "1,0, tarik 0,80 (hal. 332). Berat tiang pada tarik adalah beban, bukan tahanan (hal. 319). Perbandingan "
               "ke Pu 5.6 di langkah lanjut.")

    # ---- Panjang per zona
    lz = Lembar(wb.create_sheet("Panjang per Zona"), 10, "Panjang tiang per zona (metode A)",
                [10, 10, 10, 10, 10, 12, 12, 12, 12, 12, 12])
    lz.catatan(ket_ai + " Panjang dari kepala tiang +10,85 m. Benam = kedalaman masuk U7 (langkah 0,5 m), izin metode A. "
               "'Tanpa NSF' hanya daya dukung murni; 'Setara T3' menambahkan gesekan negatif Tahap 3 (3.7), pembanding 911 kN. "
               "Usulan sementara = setara T3, dibulatkan 0,5 m.")
    lz.kosong()
    rows = []
    for z in ZONA:
        p = pz[z]
        rows.append([z.capitalize(), round(u7_atas(z), 2), p["benam_t3"], round(p["L_t3"], 2), p["benam"], round(p["izin"], 0),
                     p["L"], p["benam_nsf"], round(p["izin_nsf"], 0), p["L_nsf"],
                     round(p["L_t3"] - p["L_nsf"], 2)])
    lz.tabel(["Zona", "U7 mulai z (m)", "Benam T3 (m)", "Panjang T3 (m)", "Benam min tanpa NSF (m)", "Izin (kN)",
              "Panjang tanpa NSF (m)", "Benam min setara T3 (m)", "Izin setara T3 (kN)", "Usulan panjang (m)",
              "Hemat vs T3 (m)"], rows, rata=list("lcccccccccc"),
             fmt=[None, "0.00", "0.0", "0.00", "0.0", "#,##0", "0.0", "0.0", "#,##0", "0.0", "0.00"],
             fill_kolom={i: AI for i in range(1, 11)}, beku=False)
    lz.catatan("Benam 0,5 m tanpa NSF tidak bermakna praktis (ujung masih di antarmuka U6/U7); gunakan kolom setara T3 dan uji "
               "beban awal sebelum memendekkan tiang.")

    # ---- Banding 911
    lbn = Lembar(wb.create_sheet("Banding 911 kN"), 11, "Perbandingan dengan izin Tahap 3 (911 kN)",
                 [26, 10, 12, 12, 12, 12, 12, 12])
    lbn.catatan(ket_ai + " Izin Tahap 3 per zona dari tahap3_pondasi.beban_izin (Qult/2,5 - NSF statis; Qult/1,1 - NSF likuifaksi).")
    lbn.kosong()
    rows = []
    b0 = lbn.baris
    for m in "ABC":
        for z in ZONA:
            r = b0 + 1 + len(rows)
            rr = ring[(m, z)]
            rows.append([NAMA_METODE[m], z.capitalize(), f"='Ringkasan'!L{rr}", f"=E{r}/{TARGET}",
                         f"='Ringkasan'!O{rr}", f"=G{r}/{TARGET}", round(t3.beban_izin(KODE, profil=z)["izin"], 1),
                         f"=G{r}-I{r}"])
    lbn.tabel(["Metode", "Zona", "Izin tanpa NSF (kN)", "Rasio ke 911", "Izin setara T3 (kN)", "Rasio ke 911",
               "Izin T3 zona (kN)", "Selisih setara T3 - T3"], rows, rata=list("lc") + ["c"] * 6,
              fmt=[None, None, "#,##0.0", "0.00", "#,##0.0", "0.00", "#,##0.0", "#,##0.0"],
              fill_kolom={i: AI for i in range(2, 8)}, beku=True)
    lbn.catatan("Izin setara T3 lebih tinggi dari 911 kN karena U5 dihitung pada kasus statis (Tahap 3 tidak menghitungnya); tanpa U5 "
                "metode B persis 911 kN (T-99 b).")

    # ---- Acuan dan keputusan
    la = Lembar(wb.create_sheet("Acuan"), 12, "Acuan 6.1 di folder acuan/", [5, 70, 12, 80])
    la.catatan(LABEL + " " + LABEL_AI)
    la.tabel(["No", "Acuan", "Status", "Berkas dan halaman (PDF)"], [[i + 1, *a] for i, a in enumerate(ACUAN)],
             rata=list("clcl"), fill_kolom={2: AI, 3: AI})
    lk = Lembar(wb.create_sheet("Keputusan Defsa"), 13, "Keputusan yang diminta dari Defsa", [5, 40, 100, 20])
    lk.catatan(ket_ai)
    lk.tabel(["No", "Keputusan", "Dasar dan usulan AI", "Status"],
             [[i + 1, k[0], k[1], STATUS] for i, k in enumerate(KEPUTUSAN)], rata=list("clll"), fill_kolom={2: AI})

    keluar = Path(keluar)
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar, ring


def baca_excel(berkas=BERKAS, ring=None):
    """Baca nilai Qult dan izin Selatan/Utara dari Excel yang sudah dihitung ulang."""
    import openpyxl
    ws = openpyxl.load_workbook(berkas, data_only=True)["Ringkasan"]
    if ring is None:
        ring = {}
        for r in range(1, ws.max_row + 1):
            if ws.cell(r, 4).value in ("Selatan", "Utara", "Tengah") and str(ws.cell(r, 3).value or "")[:2] in ("A.", "B.", "C."):
                ring[(str(ws.cell(r, 3).value)[0], ws.cell(r, 4).value.upper())] = r
    out = {}
    for (m, z), r in ring.items():
        if z == "TENGAH":
            continue
        out[(m, z)] = {"Qult_st": ws.cell(r, 8).value, "Qult_gm": ws.cell(r, 9).value, "izin": ws.cell(r, 12).value,
                       "izin_t3": ws.cell(r, 15).value}
    return out


# ------------------------------------------------------------------ T-99
def t99(berkas=BERKAS, ring=None):
    h = semua()
    ex = baca_excel(berkas, ring)
    selisih, nilai = 0.0, []
    for (m, z), e in ex.items():
        x = h[(m, z)]
        for k in ("Qult_st", "Qult_gm", "izin", "izin_t3"):
            d = abs(e[k] - x[k]) / abs(x[k]) * 100
            selisih = max(selisih, d)
        nilai.append(((m, z), e["Qult_st"], x["Qult_st"]))
    rp = reproduksi_t3()
    dt3 = max(max(abs(v["dQ"]), abs(v["dI"])) for v in rp.values())
    sb = sebaran(h)
    dev = max(v["dev"] for v in sb.values())
    lolos = selisih <= TOL["excel"] and dt3 <= TOL["t3"]
    return {"selisih_excel": selisih, "dt3": dt3, "rp": rp, "sb": sb, "dev": dev, "lolos": lolos, "ok_sebaran": dev <= TOL["sebaran"]}


def catat_t99(hasil=None, berkas=VERIFIKASI):
    """Tulis baris T-99 setelah baris T-98 (sekali; mengganti baris T-99 lama bila ada)."""
    r = hasil or t99()
    sb = r["sb"]
    rp = r["rp"]
    sel = "; ".join(f"{z.capitalize()} A {idn(sb[(z, 'Qult_st')]['v'][0], 0)} / B {idn(sb[(z, 'Qult_st')]['v'][1], 0)} / "
                    f"C {idn(sb[(z, 'Qult_st')]['v'][2], 0)} kN (simpangan {idn(sb[(z, 'Qult_st')]['dev'], 1)} %)"
                    for z in ZONA)
    c1 = (f"(a) rumus Excel hidup 6.1 (lembar irisan, dihitung ulang di Excel) vs skrip `tahap6_tiang_tunggal.py`: "
          f"selisih terbesar Qult statis, gempa, izin, izin setara T3 (3 metode, selatan dan utara) {idn(r['selisih_excel'], 4)} %")
    c2 = (f"(b) setelan Tahap 3 (metode B, U5 tidak dihitung) vs `tahap3_pondasi.beban_izin`: Qult selatan "
          f"{idn(rp['SELATAN']['Qult'], 1)} vs {idn(rp['SELATAN']['Qult_t3'], 1)} kN, izin {idn(rp['SELATAN']['izin'], 1)} vs "
          f"{idn(rp['SELATAN']['izin_t3'], 1)} kN, utara {idn(rp['UTARA']['izin'], 1)} vs {idn(rp['UTARA']['izin_t3'], 1)} kN, "
          f"selisih terbesar {idn(r['dt3'], 4)} %; (c) sebaran Qult statis {sel}")
    status = "Lolos (a, b); (c) dalam batas" if r["lolos"] and r["ok_sebaran"] else (
        "Lolos (a, b); (c) di luar batas, dijelaskan" if r["lolos"] else "Gagal")
    baris = ("| T-99 | Cek silang 6.1 daya dukung tiang bor tunggal Ø800 (Qult statis dan gempa, izin tekan, izin setara T3) "
             f"| {c1} | {c2} | (a) {idn(r['selisih_excel'], 4)} %; (b) {idn(r['dt3'], 4)} %; (c) maks {idn(r['dev'], 1)} % "
             f"| (a) ≤ 0,5 %; (b) ≤ 0,5 %; (c) ±30 % dari rata-rata A/B/C [Asumsi] | {status}, disetujui Defsa 21 Nov 2026 "
             "| `skrip/tahap6_tiang_tunggal.py`, `tests/test_tahap6_tiang_tunggal.py` | Ditetapkan sebelum membandingkan. "
             "Data simulasi. Sondir tidak dipakai (hanya 20 m). |")
    teks = Path(berkas).read_text(encoding="utf-8").split("\n")
    teks = [ln for ln in teks if not ln.startswith("| T-99 |")]
    i = next(k for k, ln in enumerate(teks) if ln.startswith("| T-98 |"))
    teks.insert(i + 1, baris)
    Path(berkas).write_text("\n".join(teks), encoding="utf-8")
    return baris


# ------------------------------------------------------------------ Markdown
def tulis_md(keluar=MD, hasil=None):
    h = semua()
    pz = panjang_zona()
    r = hasil or t99()
    sb = r["sb"]
    L = [f"# 6.1 Daya dukung tiang bor tunggal Ø800 ({STATUS}, 21 Nov 2026)\n",
         "DATA SIMULASI. Disusun AI atas permintaan Defsa; kunci jawaban tidak dibuka. Rincian di "
         "`6.1 Daya Dukung Tiang.xlsx` (`skrip/tahap6_tiang_tunggal.py`, uji `tests/test_tahap6_tiang_tunggal.py`).\n",
         "## Tujuan\n",
         "Daya dukung tekan dan tarik satu tiang bor Ø800 (kepala +10,85 m) di zona selatan (BH-5) dan utara (BH-3), tengah "
         "(BH-7) hanya informasi; membandingkan tiga metode dengan izin Tahap 3 (911 kN); usulan panjang per zona.\n",
         "## Keputusan metode (disetujui Defsa 21 Nov 2026)\n",
         "- U1-U4 tidak menyumbang (zona urugan dan penurunan; gesekan negatif di 6.2). U5 pasir dihitung pada kasus statis, "
         "nol saat gempa (likuifaksi FS 0,22-0,75). U6 dan U7 selalu. Integrasi per 0,25 m seperti Tahap 3.",
         "- **A, FHWA GEC10 (2018)**: selimut lempung alpha = 0,30 + 0,17 / (su/pa) (Pers. 10-18, hal. 296), selimut pasir "
         "beta = (1 - sin φ') (σ'p/σ'v)^sin φ' tan φ' dengan σ'p = 0,47 pa N60^0,6 (Pers. 10-9, 10-11, 10-13, hal. 291), ujung "
         "qb = 0,60 N60 tsf ≤ 30 tsf (Pers. 10-14, hal. 294); gempa: su U6 × 0,8 (hal. 332).",
         "- **B, SNI 8460:2017**: Q = Qs + Qb (Pasal 9.7.2.1 Pers. 1, hal. 204), FK ≥ 2,5 (Pasal 9.2.3.1, hal. 194); SNI tidak "
         "memberi rumus f dan q, dipakai Reese dan O'Neill lewat NHI-06-089: alpha 0,55 (Pers. 9-37a, hal. 239), beta = 1,5 - "
         "0,135 √z[ft] (0,25-1,2), fs ≤ 191 kPa (Pers. 9-42, 9-43, hal. 242-243), ujung 57,5 N60 kPa (Pers. 9-45a). Sama dengan "
         "Tahap 3 tetapi U5 dihitung pada kasus statis.",
         "- **C, korelasi SPT**: φ' = min(φ' desain; 27,5 + 9,2 log N60) (GEC10 hal. 293), K = 1 - sin φ' (OCR 1) [Asumsi], ujung "
         "NHI-06-089 Pers. 9-45a. Sondir tidak dipakai: data hanya sampai 20 m (U6 mulai 32-33 m); metode sondir "
         "[Literatur, belum ada di acuan/].",
         "- Izin tekan = min(Qult statis / 2,5; Qult gempa / 1,1) tanpa gesekan negatif. Izin setara T3 = dikurangi gesekan negatif "
         "Tahap 3 (3.7) supaya sebanding dengan 911 kN. Tarik: Tult = Qs + berat efektif tiang, FK 2,5 statis, 1,1 gempa [Asumsi].\n",
         "## Hasil (kN per tiang)\n",
         "| Metode | Zona | Qs statis | Qs gempa | Qb | Qult statis | Qult gempa | Izin tekan | Izin setara T3 | Tult statis | Izin tarik |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in "ABC":
        for z in ZONA:
            x = h[(m, z)]
            L.append(f"| {m} | {z.capitalize()} | {idn(x['Qs_st'], 0)} | {idn(x['Qs_gm'], 0)} | {idn(x['Qb'], 0)} | "
                     f"{idn(x['Qult_st'], 0)} | {idn(x['Qult_gm'], 0)} | {idn(x['izin'], 0)} | {idn(x['izin_t3'], 0)} | "
                     f"{idn(x['Tult_st'], 0)} | {idn(x['izin_tarik'], 0)} |")
    L.append("\nGesekan selimut rata-rata statis per lapisan (kPa), selatan: " + "; ".join(
        f"{m}: U5 {idn(h[(m, 'SELATAN')]['per']['U5']['fs_rata'], 1)}, U6 {idn(h[(m, 'SELATAN')]['per']['U6']['fs_rata'], 1)}, "
        f"U7 {idn(h[(m, 'SELATAN')]['per']['U7']['fs_rata'], 1)}" for m in "ABC") + ".\n")
    LA = {z: lrfd_A(h[("A", z)]) for z in ZONA}
    L.append("Tahanan terfaktor LRFD metode A (GEC10 Tabel 8-4): tekan statis " + ", ".join(
        f"{z.capitalize()} {idn(LA[z]['tekan_st'], 0)}" for z in ZONA) + " kN; tarik statis " + ", ".join(
        f"{z.capitalize()} {idn(LA[z]['tarik_st'], 0)}" for z in ZONA) + " kN (dibandingkan dengan Pu 5.6 di langkah lanjut).\n")
    L.append("## Banding dengan izin Tahap 3 (911 kN)\n")
    L.append("| Metode | Zona | Izin tanpa NSF | Izin setara T3 | Izin T3 zona | Rasio setara T3 / T3 |\n|---|---|---|---|---|---|")
    for m in "ABC":
        for z in ZONA:
            x = h[(m, z)]
            i3 = t3.beban_izin(KODE, profil=z)["izin"]
            L.append(f"| {m} | {z.capitalize()} | {idn(x['izin'], 0)} | {idn(x['izin_t3'], 0)} | {idn(i3, 0)} | "
                     f"{idn(x['izin_t3'] / i3)} |")
    L.append("\nIzin 911 kN Tahap 3 dibentuk oleh gesekan negatif besar; tanpa gesekan negatif daya dukung murni (1.700-2.200 kN) "
             "jauh di atas 911 kN. Yang menentukan panjang adalah 6.2 (gesekan negatif), bukan 6.1.\n")
    L.append("## Panjang tiang per zona (metode A, dari kepala +10,85 m)\n")
    L.append("| Zona | Panjang T3 | Benam T3 | Benam min tanpa NSF | Benam min setara T3 | Usulan sementara | Hemat |\n|---|---|---|---|---|---|---|")
    for z in ZONA:
        p = pz[z]
        L.append(f"| {z.capitalize()} | {idn(p['L_t3'])} m | 4,0 m | {idn(p['benam'], 1)} m ({idn(p['L'], 1)} m) | "
                 f"{idn(p['benam_nsf'], 1)} m | {idn(p['L_nsf'], 1)} m | {idn(p['L_t3'] - p['L_nsf'])} m |")
    L.append("\nTengah hanya informasi. Usulan sementara tidak mengubah 38,45 m sampai 6.2 (gesekan negatif) dan uji beban awal "
             "selesai; benam 0,5 m tanpa NSF tidak bermakna praktis.\n")
    L.append("## Verifikasi T-99\n")
    L.append(f"Toleransi ditetapkan dulu: (a) Python vs rumus Excel ≤ 0,5 %; (b) setelan Tahap 3 vs `tahap3_pondasi` ≤ 0,5 %; "
             f"(c) sebaran A/B/C ±30 % [Asumsi]. Hasil: (a) {idn(r['selisih_excel'], 4)} %; (b) {idn(r['dt3'], 4)} %; "
             f"(c) simpangan terbesar {idn(r['dev'], 1)} % (statis) di antara tiga metode. Lolos: {'ya' if r['lolos'] else 'TIDAK'}.\n")
    L.append("## Acuan yang belum ada di acuan/\n")
    for a in ACUAN:
        if a[1] == "belum ada":
            L.append(f"- {a[0]}: {a[2]}")
    L.append("\n## Hal yang perlu diputuskan Defsa\n")
    for i, k in enumerate(KEPUTUSAN, 1):
        L.append(f"{i}. **{k[0]}**: {k[1]}")
    L.append(f"\nStatus: {STATUS}.\n")
    Path(keluar).write_text("\n".join(L), encoding="utf-8")
    return keluar


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from format_dokumen import hitung_ulang_excel
    berkas, ring = buat_excel()
    print(berkas, hitung_ulang_excel(berkas))
    r = t99(berkas, ring)
    print({k: v for k, v in r.items() if k not in ("rp", "sb")})
    print(catat_t99(r))
    print(tulis_md(hasil=r))
    print(panjang_zona())


if __name__ == "__main__":
    main()
