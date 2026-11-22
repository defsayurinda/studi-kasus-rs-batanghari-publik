"""Tahap 2 penyelesaian: penurunan akibat urugan, PVD, bahaya amblas, cek fase contoh, artesis, muka air gudang,
koreksi tren latar uji pompa, dan catatan data sisa.

Keluaran: '02 Olah Data Tanah/2.8 Penurunan dan Pelengkap.xlsx', gambar GT-15.
Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap2_pelengkap.py
"""
import math
from datetime import datetime
from pathlib import Path

import numpy as np
from gambar_teknik import BukuPDF as PdfPages
from matplotlib.patches import Rectangle
from scipy.interpolate import griddata

import tahap2_air_tanah as at
import tahap2_parameter as tp
import tahap2_penurunan_urugan as pu
import tahap2_stratigrafi as st
from format_dokumen import AI, Lembar, set_font_bawaan
from gambar_teknik import Kertas
from tahap2_gambar_air_tanah import gaya_sumbu
from tahap2_gambar_geoteknik import LAHAN, kotak_catatan, sisi_kiri

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "02 Olah Data Tanah"
BERKAS = KELUAR / "2.8 Penurunan dan Pelengkap.xlsx"
PDF = KELUAR / "2.8 Gambar Penurunan Urugan.pdf"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = ("DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026. Disusun "
            "setelah kunci Tahap 2 dibuka (tindak lanjut evaluasi).")
ELEV_GUDANG = 9.79  # muka tanah galian uji gudang
KEPALA_CERUCUK = 8.62


# ------------------------------------------------------------------ analisis tambahan
def cek_fase():
    """S = w Gs / e0 (contoh konsolidasi) dan S dari γ, w, Gs (contoh indeks UD)."""
    ring, idx = {}, {}
    for path in (tp.LAMA / "Laboratorium.xlsx", tp.BARU / "Laboratorium Tambahan.xlsx"):
        for b in tp._baris(path, "Ringkasan Konsolidasi"):
            ring[(b["Titik"], b["Contoh"])] = b
        for b in tp._baris(path, "Indeks"):
            idx[(b["Titik"], b["Contoh"])] = b
    kons = []
    for k, b in ring.items():
        g = idx.get(k, {}).get("Gs")
        if g:
            s = b["w (%)"] / 100 * g / b["e0"]
            kons.append(dict(titik=k[0], contoh=k[1], w=b["w (%)"], gs=g, e0=b["e0"], s=s,
                             e0_kor=b["w (%)"] / 100 * g if abs(s - 1) > 0.05 else None))
    gam = []
    for k, i in idx.items():
        w, g, G = i.get("Kadar air w (%)"), i.get("Berat isi (kN/m³)"), i.get("Gs")
        if all(isinstance(v, (int, float)) for v in (w, g, G)) and str(k[1]).startswith("UD"):
            e = G * 9.81 * (1 + w / 100) / g - 1
            s = w / 100 * G / e
            if abs(s - 1) > 0.05:
                gam.append(dict(titik=k[0], contoh=k[1], w=w, gs=G, gamma=g, s=s, gamma_kor=g * (1 + w / 100)))
    return kons, gam


def artesis():
    H = at.bersihkan_harian()
    muka = {"PZ-2B (m)": 10.47, "PZ-3B (m)": 9.82, "PZ-4B (m)": 9.19}
    hasil = []
    for k, e in muka.items():
        hari = [d for d in H if isinstance(d[k], (int, float)) and d[k] > e]
        kering = [d for d in hari if "tergenang" not in (d.get("Keterangan") or "")]
        mx = max((d[k] for d in H if isinstance(d[k], (int, float))), default=None)
        hasil.append(dict(sensor=k[:5], muka=e, maks=mx, hari=len(hari), hari_kering=len(kering),
                          maks_kering=max((d[k] for d in kering), default=None),
                          tgl_kering=f"{kering[0]['Tanggal']:%d %b}-{kering[-1]['Tanggal']:%d %b %Y}" if kering else "-"))
    return hasil


def muka_air_gudang():
    W = [w for w in at.mingguan() if isinstance(w.get("SP-1 kedalaman (m)"), (int, float))]
    sep = [w for w in W if w["Tanggal"].month == 9]
    dalam = max(w["SP-1 kedalaman (m)"] for w in sep)
    return dict(sp1_dalam_kemarau=dalam, elev_kemarau=ELEV_GUDANG - dalam, kepala=KEPALA_CERUCUK,
                batas=round(KEPALA_CERUCUK, 1))


def tren_latar():
    """Kenaikan latar akuifer selama uji debit tetap dari kenaikan sungai (8-11 Des) × rasio respons PZ (2.3)."""
    s = at.sungai_selama_uji()
    a = [(t, v) for t, v in s if datetime(2026, 12, 8) <= t <= datetime(2026, 12, 11, 8)]
    hari = [(t - a[0][0]).total_seconds() / 86400 for t, _ in a]
    laju_sungai = float(np.polyfit(hari, [v for _, v in a], 1)[0])
    rasio = at.regresi_jeda("PZ-3B (m)")["b"]
    laju = laju_sungai * rasio
    up = at.ringkas_uji_pompa()
    t_rata = np.mean([(960 + 1800) / 2, (2160 + 4320) / 2]) / 1440
    s1, s2 = up["s1"] + laju * t_rata, up["s2"] + laju * t_rata
    k = at.thiem_tertekan(up["q_rata"], 30, 10, s2, s1, at.TEBAL_AKUIFER)
    bay = (65.0, 40.0 - 2 * up["a_pw"])
    rb = math.hypot(75 - bay[0], 40 - bay[1])
    t_bay = up["q_rata"] / (2 * math.pi * s1) * math.log(rb / 10)
    return dict(laju_sungai=laju_sungai, rasio=rasio, laju=laju, koreksi=laju * t_rata, s1=s1, s2=s2, k=k,
                k_asal=up["k_thiem"], t_bay=t_bay, t_bay_asal=up["T_bayangan"]["OW-1"])


def kurva_waktu(s_akhir, tebal_u4=8.0, s_pvd=None, tahun=np.linspace(0, 15, 301)):
    """U(t): Terzaghi (Tv) tanpa PVD; dengan PVD gabungan radial (GEC 13 Pers. 2-1) dan vertikal."""
    hdr = tebal_u4 / 2
    tv = pu.CV * tahun / hdr ** 2
    uv = np.where(tv < 0.2827, np.sqrt(4 * tv / np.pi), 1 - 8 / np.pi ** 2 * np.exp(-np.pi ** 2 * tv / 4))
    if s_pvd is None:
        return tahun, s_akhir * uv
    dc = 1.05 * s_pvd
    fn = math.log(dc / pu.DW) - 0.75 + pu.FS_GANGGUAN
    uh = 1 - np.exp(-8 * pu.CH * tahun / (dc ** 2 * fn))
    return tahun, s_akhir * (1 - (1 - uv) * (1 - uh))


# ------------------------------------------------------------------ Excel
CATATAN = [
    "Penurunan primer akibat urugan ke +11,50 (tebal 0,95-2,68 m, Δσ 18-51 kPa): 0,15-0,39 m di selatan (tanpa "
    "gambut) sampai 1,05-1,18 m di utara (gambut 2,3-3,7 m); ditambah pemampatan sekunder 0,06-0,23 m dalam 50 tahun. "
    "Beda penurunan sampai ±1 m antara selatan dan utara, dan antara halaman dan gedung bertiang.",
    "Tanpa drainase vertikal, konsolidasi 90 % lempung lunak (tebal ±8 m, drainase dua arah, cv 1,8 m²/th) butuh "
    "±7,5 tahun. Dengan PVD pola segitiga 1,2 m: ±5 bulan; 1,5 m: ±8 bulan (GEC 13 Pers. 2-1, ch 4,5 m²/th, Fs 2).",
    "Bahaya amblas/desakan lateral (FHWA NHI-06-088 Pers. 7-11): beban urugan > 3 su di semua titik kecuali CPTu-6 "
    "(paling parah di utara). Urugan harus bertahap dengan pemantauan (piezometer, inklinometer, patok penurunan) atau diperkuat "
    "geotekstil dasar; tinggi tahap dan jeda ditetapkan di Tahap 3 dan 6.",
    "Mitigasi untuk Tahap 3: PVD + prapembebanan sejak awal jadwal; urugan ringan (geofoam/agregat ringan) atau "
    "galian-ganti gambut di utara; peil halaman utara diturunkan bila memungkinkan; tiang gedung dirancang dengan "
    "gesekan negatif (NSF); sambungan utilitas dan ramp fleksibel terhadap beda penurunan.",
    "Cek fase: semua contoh konsolidasi S = 1,00 ± 0,003, kecuali BH-8 UD-2 S = 0,89; e0 lab 2,343 tidak sesuai "
    "w·Gs = 2,088. Dipakai e0 = 2,09 dan Cc/(1+e0) naik ±8 %; tidak mengubah parameter desain U4.",
    "Berat isi BH-3 (laporan lama) memberi S 0,21-0,48: angka itu berat isi kering. Dikoreksi γ = γd (1 + w): gambut "
    "10,8, lempung 14,9-15,4 kN/m³, sama dengan contoh lain.",
    "Artesis: PZ-4B (utara) di atas muka tanah selama 24 hari, 11 di antaranya saat lahan tidak tergenang (akhir Feb-"
    "awal Mar 2027, maks. +9,29 vs muka tanah +9,19). Pelat dasar basement dan dasar galian di utara harus memakai "
    "tinggi tekan ini (sudah tercakup tinggi tekan desain +11,20).",
    "Gudang timur: muka air dangkal saat kemarau di gudang ±+8,30 (SP-1 Sep 2026 1,49 m di bawah muka tanah), di "
    "bawah kepala cerucuk +8,62, sehingga kepala cerucuk sudah terekspos tiap kemarau (cocok dengan 10-15 cm lapuk). "
    "Usulan syarat RKS: pekerjaan proyek tidak boleh menurunkan muka air di sisi gudang di bawah +8,6 di luar "
    "kemarau alami; dinding kedap + sumur imbuhan + sumur pantau di batas timur.",
    "Uji pompa: kenaikan latar akuifer selama uji ±0,03 m/hari (sungai +0,04 m/hari × rasio respons PZ-3B 0,71). "
    "Koreksi menambah penurunan kedua sumur pantau ±0,05 m; k Thiem tidak berubah (selisih dua sumur), T sumur "
    "bayangan turun ±2 %. Kesimpulan 2.3 tetap.",
    "Catatan data sisa: BH-7 UD-1 (gambut) perolehan 48 % dan tidak diuji - parameter gambut dari BH-7 UD-2; SP-1 "
    "terendam dan tidak dibaca saat banjir Januari, pipa PZ-1 diperpanjang 1,0 m - bacaan sesudahnya tetap dipakai "
    "tanpa interpolasi.",
]


def buat_excel(keluar=BERKAS):
    hasil = pu.semua()
    kons, gam = cek_fase()
    ar = artesis()
    gd = muka_air_gudang()
    tl = tren_latar()
    wb = openpyxl_wb()
    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk penurunan urugan dan pelengkap Tahap 2", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, t] for i, t in enumerate([
        "Lembar ini menutup tindak lanjut evaluasi kunci Tahap 2: penurunan akibat urugan ke +11,50 (TOR butir 4), "
        "waktu konsolidasi dan PVD, bahaya amblas, cek fase contoh, artesis, batas muka air gudang, koreksi tren latar "
        "uji pompa, dan catatan data sisa.",
        "Rumus: FHWA NHI-06-088 Bab 7.5 Pers. 7-2 hal. 7-24, Pers. 7-8 dan Tabel 7-4 hal. 7-31/7-32, sekunder Bab 7.5.4 "
        "hal. 7-38, Pers. 7-11 hal. 7-41; FHWA GEC 13 Vol. I Pers. 2-1 s.d. 2-3 hal. 2-32 s.d. 2-35.",
        "Parameter: 2.4 (disetujui Defsa). U3: σ'p = σ'v0 + 7 kPa (lab); U4: POP 18 kPa di 3 m → 0 di 8,5 m; γ urugan 19 "
        "kN/m³ [Asumsi]; MAT 0,7 m; urugan luas (Δσ tetap). Pasir U5/U7 dianggap tidak mampat. Bor tangan: atas U5 "
        "-0,3 [Asumsi].",
        "Gambar: '2.8 Gambar Penurunan Urugan.pdf' (GT-15).",
    ])], rata=list("cl"))

    # ---- penurunan per titik
    lb = Lembar(wb.create_sheet("Penurunan"), 2, "Penurunan akibat urugan ke +11,50 per titik",
                [5, 9, 10, 6, 6, 8, 8, 8, 8, 8, 8, 8, 9, 9, 22])
    lb.catatan(LABEL + " Penurunan per unit dari hitungan sublapisan 0,1 m (skrip tahap2_penurunan_urugan.py); contoh "
               "hitungan penuh dengan rumus Excel di lembar Contoh BH-3. " + LABEL_AI)
    lb.kosong()
    r0 = lb.baris + 1
    baris = []
    for i, r in enumerate(hasil):
        q, tiga, bahaya = pu.amblas(st.semua_titik()[i])
        rr = r0 + i
        baris.append([i + 1, r["nama"], r["jenis"], r["x"], r["y"], r["elev"], f"=11.5-H{rr}", f"=19*I{rr}",
                      round(r["per_unit"].get("U3", 0), 3), round(r["per_unit"].get("U4", 0), 3),
                      round(sum(v for k, v in r["per_unit"].items() if k not in ("U3", "U4")), 3),
                      f"=K{rr}+L{rr}+M{rr}", round(r["sekunder"], 3), f"=N{rr}+O{rr}",
                      f"Amblas: {q:.0f} > 3su = {tiga:.0f} kPa" if bahaya else ""])
    lb.tabel(["No", "Titik", "Jenis", "x (m)", "y (m)", "Elevasi tanah (m)", "Tebal urugan (m)", "Δσ (kPa)",
              "U3 (m)", "U4 (m)", "U2+U6 (m)", "Primer (m)", "Sekunder 50 th (m)", "Total (m)", "Catatan"], baris,
             rata=list("cclcccccccccccl"), fmt=[None, None, None, "0", "0", "0.00", "0.00", "0.0", "0.000", "0.000",
                                                 "0.000", "0.000", "0.000", "0.000", None],
             fill_kolom={i: AI for i in range(8, 15)}, beku_kolom=2)

    # ---- contoh BH-3 dengan rumus
    lb = Lembar(wb.create_sheet("Contoh BH-3"), 3, "Contoh hitungan sublapisan BH-3 (rumus Excel)",
                [5, 7, 8, 8, 8, 8, 8, 8, 8, 8, 9, 9, 10, 22])
    lb.catatan(LABEL + " Sublapisan 0,5 m. σv0 kumulatif; u0 = 9,81 (z - 0,7); Δσ = 19 × 2,27 = 43,1 kPa. "
               "S = H[Cr/(1+e0) log(σ'p/σ'0) + Cc/(1+e0) log(σ'f/σ'p)] bila σ'f > σ'p (FHWA NHI-06-088 Pers. 7-2). "
               + LABEL_AI)
    lb.kosong()
    t3 = next(t for t in st.semua_titik() if t["nama"] == "BH-3")
    lap = pu.lapisan_lengkap(t3)
    r0 = lb.baris + 1
    baris, i = [], 0
    sv = 0.0
    for lp in lap:
        u = lp["unit"]
        g, e0, cc, cr, _ = pu.PAR[u]
        a, b = lp["atas"], min(lp["bawah"], 40.0)
        n = max(1, int(round((b - a) / 0.5)))
        h = (b - a) / n
        for j in range(n):
            if e0 is None:
                break
            z = a + (j + 0.5) * h
            rr = r0 + i
            s_tengah = sv + g * (j + 0.5) * h
            pop = {"U2": None, "U3": "7", "U4": f"MIN(18,MAX(0,18*(8.5-E{rr})/5.5))", "U6": None}[u]
            sp = (f"=MAX(96,H{rr})" if u == "U2" else f"=MAX(400,H{rr})" if u == "U6" else f"=H{rr}+{pop}")
            baris.append([i + 1, u, round(z, 3), round(h, 3), round(s_tengah, 2), f"=G{rr}-9.81*MAX(0,E{rr}-0.7)",
                          sp, e0, cc, cr, f"=J{rr}+43.13",
                          f"=IF(N{rr}<=K{rr},G{rr}*M{rr}/(1+L{rr})*LOG10(N{rr}/J{rr}),"
                          f"G{rr}*(M{rr}/(1+L{rr})*LOG10(K{rr}/J{rr})+M{rr}/(1+L{rr})*0+"
                          f"{cc}/(1+L{rr})*LOG10(N{rr}/K{rr})))", ""])
            i += 1
        sv += g * (b - a)
    lb.tabel(["No", "Unit", "z (m)", "H (m)", "σv0 (kPa)", "σ'v0 (kPa)", "σ'p (kPa)", "e0", "Cc", "Cr",
              "σ'f (kPa)", "ΔS (m)", "Catatan"], baris, rata=list("ccccccccccccl"),
             fmt=[None, None, "0.00", "0.00", "0.0", "0.0", "0.0", "0.00", "0.000", "0.000", "0.0", "0.0000", None],
             fill_kolom={i: AI for i in (5, 6, 10, 11)})
    r1 = r0 + len(baris) - 1
    lb.catatan(f"Jumlah ΔS sampai dasar bor (Excel, sublapisan ±0,5 m) di kolom ΔS; Python (sublapisan 0,1 m): "
               f"{next(r for r in hasil if r['nama'] == 'BH-3')['primer']:.3f} m.".replace(".", ","), fill=AI)
    c = lb.ws.cell(lb.baris, 14)
    c.value = f"=SUM(N{r0}:N{r1})"
    c.number_format = "0.000"
    # catatan: rumus ΔS memakai Cr di kolom J untuk bagian terkonsolidasi lebih dan Cc untuk bagian NC
    for rr in range(r0, r1 + 1):
        lb.ws[f"N{rr}"] = (f"=IF(M{rr}<=I{rr},F{rr}*L{rr}/(1+J{rr})*LOG10(M{rr}/H{rr}),"
                           f"F{rr}*(L{rr}/(1+J{rr})*LOG10(I{rr}/H{rr})+K{rr}/(1+J{rr})*LOG10(M{rr}/I{rr})))")
        lb.ws[f"M{rr}"] = f"=H{rr}+43.13"

    # ---- PVD dan waktu
    lb = Lembar(wb.create_sheet("Waktu dan PVD"), 4, "Waktu konsolidasi tanpa dan dengan PVD",
                [5, 30, 12, 12, 12, 40])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    r0 = lb.baris + 1
    lb.tabel(["No", "Besaran", "Nilai", "Satuan", "", "Sumber"], [
        [1, "Tebal U4 (drainase dua arah)", 8.0, "m", "", "2.2 (±7,5-8,5 m)"],
        [2, "cv lempung U4", pu.CV, "m²/th", "", "2.4"],
        [3, "t90 tanpa PVD = 0,848 Hdr²/cv", f"=0.848*(E{r0}/2)^2/E{r0 + 1}", "tahun", "",
         "FHWA NHI-06-088 Pers. 7-8, Tabel 7-4"],
        [4, "ch lempung U4", pu.CH, "m²/th", "", "2.4 (CPTu)"],
        [5, "dw PVD 100 × 4 mm = 2(a+b)/π", round(pu.DW, 4), "m", "", "GEC 13 Pers. 2-3 hal. 2-35"],
        [6, "Fs faktor gangguan", pu.FS_GANGGUAN, "-", "", "GEC 13 hal. 2-35 (plastisitas tinggi)"],
    ], rata=list("clccll"), fmt=[None, None, "0.000", None, None, None], fill_kolom={2: AI}, beku=False)
    lb.kosong()
    r1 = lb.baris + 1
    baris = []
    for i, s in enumerate((1.0, 1.2, 1.5, 2.0)):
        rr = r1 + i
        baris.append([i + 1, f"Pola segitiga, jarak {s:g} m".replace(".", ","), s, f"=1.05*E{rr}",
                      f"=F{rr}^2/(8*$E${r0 + 3})*(LN(F{rr}/$E${r0 + 4})-0.75+$E${r0 + 5})*LN(1/(1-0.9))*12",
                      "GEC 13 Pers. 2-1, 2-2; dc = 1,05 s"])
    lb.tabel(["No", "Pola PVD", "Jarak s (m)", "dc (m)", "t90 radial (bulan)", "Sumber"], baris,
             rata=list("clccll"), fmt=[None, None, "0.00", "0.000", "0.0", None], fill_kolom={4: AI}, beku=False)
    lb.ws._print_rows = None

    # ---- cek fase
    lb = Lembar(wb.create_sheet("Cek Fase"), 5, "Cek hubungan fase contoh (S = w Gs / e)",
                [5, 8, 8, 9, 8, 9, 9, 10, 40])
    lb.catatan(LABEL + " Contoh di bawah muka air harus jenuh (S ≈ 1). " + LABEL_AI)
    lb.kosong()
    lb.bagian("A", "Contoh konsolidasi: S dari e0 laboratorium")
    r0 = lb.baris + 1
    baris = []
    for i, x in enumerate(kons):
        rr = r0 + i
        baris.append([i + 1, x["titik"], x["contoh"], x["w"], x["gs"], x["e0"], f"=F{rr}/100*G{rr}/H{rr}",
                      f'=IF(ABS(I{rr}-1)>0.05,F{rr}/100*G{rr},"-")',
                      "e0 lab tidak konsisten; pakai w·Gs" if x["e0_kor"] else ""])
    lb.tabel(["No", "Titik", "Contoh", "w (%)", "Gs", "e0 lab", "S", "e0 terkoreksi", "Catatan"], baris,
             rata=list("ccccccccl"), fmt=[None, None, None, "0.0", "0.00", "0.000", "0.000", "0.000", None],
             fill_kolom={6: AI, 7: AI, 8: AI}, beku=False)
    lb.kosong()
    lb.bagian("B", "Contoh indeks dengan S tidak wajar: berat isi BH-3 (laporan lama)")
    r0 = lb.baris + 1
    baris = []
    for i, x in enumerate(gam):
        rr = r0 + i
        baris.append([i + 1, x["titik"], x["contoh"], x["w"], x["gs"], x["gamma"],
                      f"=F{rr}/100*G{rr}/(G{rr}*9.81*(1+F{rr}/100)/H{rr}-1)", f"=H{rr}*(1+F{rr}/100)",
                      "Tertulis γ kering; γ = γd (1 + w)"])
    lb.tabel(["No", "Titik", "Contoh", "w (%)", "Gs", "γ tertulis (kN/m³)", "S", "γ terkoreksi (kN/m³)", "Catatan"],
             baris, rata=list("ccccccccl"), fmt=[None, None, None, "0.0", "0.00", "0.00", "0.00", "0.00", None],
             fill_kolom={6: AI, 7: AI, 8: AI}, beku=False)
    lb.ws._print_rows = None

    # ---- artesis, gudang, pompa
    lb = Lembar(wb.create_sheet("Air Tanah Pelengkap"), 6, "Artesis, muka air gudang, tren latar uji pompa",
                [5, 30, 12, 12, 12, 12, 40])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.bagian("A", "Tinggi tekan pasir di atas muka tanah (artesis)")
    baris = [[i + 1, a["sensor"], a["muka"], a["maks"], a["hari"], a["hari_kering"],
              f"saat tidak tergenang: {a['tgl_kering']}, maks {a['maks_kering']:.2f}".replace(".", ",")
              if a["hari_kering"] else "hanya saat lahan tergenang" if a["hari"] else "tidak pernah"]
             for i, a in enumerate(ar)]
    lb.tabel(["No", "Sensor", "Muka tanah (m)", "Tinggi tekan maks (m)", "Hari > muka tanah",
              "Hari > muka tanah, tidak tergenang", "Catatan"], baris, rata=list("ccccccl"),
             fmt=[None, None, "0.00", "0.00", "0", "0", None], fill_kolom={4: AI, 5: AI, 6: AI}, beku=False)
    lb.kosong()
    lb.bagian("B", "Muka air dangkal di gudang timur dan batas usulan")
    lb.tabel(["No", "Besaran", "Nilai", "Satuan", "", "", "Sumber / keterangan"], [
        [1, "SP-1 terdalam Sep 2026 (kemarau)", gd["sp1_dalam_kemarau"], "m", "", "", "Muka Air BH-1 (laporan lama)"],
        [2, "Muka tanah galian uji gudang", ELEV_GUDANG, "m", "", "", "Survei Gudang Timur, Galian Uji"],
        [3, "Muka air kemarau di gudang", round(gd["elev_kemarau"], 2), "m", "", "",
         "[Asumsi: kedalaman sama dengan SP-1]"],
        [4, "Kepala cerucuk gelam", KEPALA_CERUCUK, "m", "", "", "Galian Uji; 10-15 cm teratas lapuk"],
        [5, "Batas muka air di sisi gudang selama konstruksi [usulan]", gd["batas"], "m", "", "",
         "Tidak turun di bawah kepala cerucuk akibat proyek; syarat RKS Tahap 7"],
    ], rata=list("clccccl"), fmt=[None, None, "0.00", None, None, None, None], fill_kolom={2: AI}, beku=False)
    lb.kosong()
    lb.bagian("C", "Koreksi tren latar uji debit tetap")
    lb.tabel(["No", "Besaran", "Nilai", "Satuan", "", "", "Keterangan"], [
        [1, "Laju naik sungai 8-11 Des 2026", round(tl["laju_sungai"], 4), "m/hari", "", "", "PS-1"],
        [2, "Rasio respons pasir (PZ-3B)", round(tl["rasio"], 3), "-", "", "", "2.3 regresi berjeda"],
        [3, "Laju naik latar akuifer", round(tl["laju"], 4), "m/hari", "", "", "baris 1 × baris 2"],
        [4, "Koreksi penurunan rata-rata jendela tunak", round(tl["koreksi"], 3), "m", "", "", "ditambahkan ke s1, s2"],
        [5, "k Thiem setelah koreksi", tl["k"], "m/s", "", "", f"sebelum {tl['k_asal']:.2e} (tidak berubah)"],
        [6, "T sumur bayangan OW-1 setelah koreksi", tl["t_bay"], "m²/s", "", "", f"sebelum {tl['t_bay_asal']:.2e}"],
    ], rata=list("clccccl"), fmt=[None, None, "0.0000", None, None, None, None], fill_kolom={2: AI}, beku=False)
    lb.ws._print_rows = None

    lb = Lembar(wb.create_sheet("Catatan"), 7, "Catatan penyelesaian Tahap 2", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Catatan"], [[i + 1, t] for i, t in enumerate(CATATAN)], rata=list("cl"), fill_kolom={1: AI})
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


def openpyxl_wb():
    import openpyxl
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    return wb


# ------------------------------------------------------------------ gambar
def gambar(pdf):
    hasil = pu.semua()
    titik = st.semua_titik()
    k = Kertas()
    skala = 1000
    x0m, x1m, y0m, y1m = -8, 148, -8, 98
    w, h = (x1m - x0m) / skala * 1000, (y1m - y0m) / skala * 1000
    ax = k.sumbu(35, 120, w, h)
    ax._cad = {"skala": skala, "jenis": "peta"}
    ax.set_xlim(x0m, x1m)
    ax.set_ylim(y0m, y1m)
    ax.set_aspect("equal")
    pts = np.array([[r["x"], r["y"]] for r in hasil])
    nil = np.array([r["total"] for r in hasil])
    gx, gy = np.meshgrid(np.linspace(0, 140, 281), np.linspace(0, 90, 181))
    gz = griddata(pts, nil, (gx, gy), method="linear")
    lv = [0, 0.3, 0.45, 0.6, 0.75, 0.9, 1.05, 1.2, 1.5]
    warna = ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#084594"]
    ax.contourf(gx, gy, gz, levels=lv, colors=warna)
    cs = ax.contour(gx, gy, gz, levels=lv[1:], colors="#08306b", linewidths=0.4)
    ax.clabel(cs, fmt=lambda v: f"{v:.2f}".replace(".", ","), fontsize=5)
    ax.add_patch(Rectangle(LAHAN[:2], LAHAN[2], LAHAN[3], fill=False, lw=1.0, ls=(0, (8, 2, 2, 2))))
    for t, r in zip(titik, hasil):
        m = {"Bor": "o", "CPTu": "^", "Bor tangan": "s"}[t["jenis"]]
        ax.plot(r["x"], r["y"], marker=m, mfc="white", mec="k", ms=3.5, mew=0.5, ls="")
        kiri = sisi_kiri(t, titik)
        ax.text(r["x"] + (-1.4 if kiri else 1.4), r["y"] + 1.2, f"{r['nama']}\n{r['total']:.2f}".replace(".", ","),
                fontsize=4.4, fontweight="bold", ha="right" if kiri else "left",
                bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.2))
    ax.set_xticks(range(0, 150, 20))
    ax.set_yticks(range(0, 100, 20))
    ax.tick_params(labelsize=5.5, length=2)
    ax.set_xlabel("x lokal (m)", fontsize=6)
    ax.set_ylabel("y lokal (m)", fontsize=6)
    gaya_sumbu(ax, f"A. Penurunan total (primer + sekunder 50 th) akibat urugan ke +11,50 (m), skala 1:{skala}")
    k.skala_grafis(35, 100, 50, skala, judul=f"Skala grafis 1:{skala}")
    ax2 = k.sumbu(35, 30, 260, 55)
    nama = [r["nama"] for r in hasil]
    x = np.arange(len(nama))
    u3 = [r["per_unit"].get("U3", 0) for r in hasil]
    u4 = [r["per_unit"].get("U4", 0) for r in hasil]
    lain = [r["primer"] - a - b for r, a, b in zip(hasil, u3, u4)]
    sek = [r["sekunder"] for r in hasil]
    ax2.bar(x, u4, color="#9fb8a3", label="primer U4")
    ax2.bar(x, u3, bottom=u4, color="#4a3b2f", label="primer U3 (gambut)")
    ax2.bar(x, lain, bottom=np.add(u4, u3), color="#c99a6b", label="primer U2 + U6")
    ax2.bar(x, sek, bottom=np.add(np.add(u4, u3), lain), color="#7f9cb5", hatch="///", label="sekunder 50 th")
    ax2.set_xticks(x)
    ax2.set_xticklabels(nama, fontsize=4.8, rotation=60)
    ax2.set_ylabel("Penurunan (m)", fontsize=6)
    ax2.legend(fontsize=5, ncol=4, loc="upper left")
    gaya_sumbu(ax2, "B. Komponen penurunan per titik")
    ax3 = k.sumbu(212, 125, 85, 80)
    for nm, warna_ in (("BH-1", "#2e7d32"), ("BH-3", "#5b3a1c"), ("HA-8", "#b00020")):
        r = next(x for x in hasil if x["nama"] == nm)
        t_, s_ = kurva_waktu(r["primer"])
        ax3.plot(t_, s_, color=warna_, lw=1.0, label=f"{nm} tanpa PVD")
        t_, s_ = kurva_waktu(r["primer"], s_pvd=1.2)
        ax3.plot(t_, s_, color=warna_, lw=1.0, ls="--", label=f"{nm} PVD 1,2 m")
    ax3.invert_yaxis()
    ax3.set_xlim(0, 10)
    ax3.set_xlabel("Waktu sejak urugan (tahun)", fontsize=6)
    ax3.set_ylabel("Penurunan primer (m)", fontsize=6)
    ax3.legend(fontsize=4.6, loc="lower right", ncol=2)
    gaya_sumbu(ax3, "C. Penurunan terhadap waktu")
    k.teks(35, 275, "PENURUNAN AKIBAT URUGAN HALAMAN KE +11,50", fontsize=11, fontweight="bold")
    k.teks(35, 270, "FHWA NHI-06-088 Bab 7.5; PVD FHWA GEC 13 Pers. 2-1; parameter 2.4; γ urugan 19 kN/m³ [Asumsi]",
           fontsize=6.5)
    kotak_catatan(k, 287, "CATATAN", [
        "Primer 0,15-0,39 m di selatan sampai 1,05-1,18 m di utara (gambut); sekunder 0,06-0,23 m dalam 50 tahun.",
        "Tanpa PVD t90 ±7,5 tahun; PVD segitiga 1,2 m ±5 bulan, 1,5 m ±8 bulan.",
        "Beban urugan > 3 su di semua titik kecuali CPTu-6 (FHWA Pers. 7-11): urugan bertahap atau geotekstil dasar, dipantau.",
        "Mitigasi untuk Tahap 3: PVD + prapembebanan, urugan ringan atau galian-ganti gambut, peil utara, NSF tiang.",
        "Kontur diinterpolasi linear antartitik; bor tangan memakai atas U5 -0,3 [Asumsi].",
    ], 75)
    k.etiket("Penurunan akibat urugan halaman", "GT-15", f"1:{skala} (peta)", "1 / 1")
    k.simpan(pdf, KELUAR / "Gambar" / "GT-15 Penurunan Akibat Urugan.png")


def buat():
    buat_excel()
    with PdfPages(PDF) as pdf:
        gambar(pdf)
        pdf.infodict()["Title"] = "2.8 Gambar Penurunan Urugan - RS Tepian Batanghari (data simulasi)"
    return BERKAS, PDF


if __name__ == "__main__":
    print(buat())
