"""Tahap 2 langkah 2.6: Excel '2.6 Likuifaksi.xlsx' dan gambar GT-12.

Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap2_lembar_likuifaksi.py
"""
from pathlib import Path

import numpy as np
import openpyxl
from gambar_teknik import BukuPDF as PdfPages

import tahap2_likuifaksi as lq
from format_dokumen import AI, Lembar, set_font_bawaan
from gambar_teknik import Kertas
from tahap2_gambar_air_tanah import gaya_sumbu
from tahap2_gambar_geoteknik import kotak_catatan

AKAR = Path(__file__).resolve().parents[1]
BERKAS = AKAR / "02 Olah Data Tanah" / "2.6 Likuifaksi.xlsx"
PDF = AKAR / "02 Olah Data Tanah" / "2.6 Gambar Likuifaksi.pdf"
PNG = AKAR / "02 Olah Data Tanah" / "Gambar" / "GT-12 Likuifaksi Pasir U5.png"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = ("DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026. "
            "Kunci jawaban tidak dibuka.")
IB = "Boulanger dan Idriss (2014) UCD/CGM-14/01"

PETUNJUK = [
    "Langkah 2.6 memeriksa pemicu likuifaksi pasir U5 (9-19 m) dengan prosedur SPT dan CPT " + IB + ", yang sejalan "
    "dengan SNI 8460:2017 Pasal 12.2.4.2 hal. 276 (Seed-Idriss / Idriss-Boulanger).",
    "Beban: PGAM = FPGA · PGA (SNI 1726:2019 Pasal 6.7.3 butir 2, Pers. 15, Tabel 10 hal. 39). PGA batuan dasar dari "
    "aplikasi Desain Spektra Indonesia PUPR (2021) di Kota Jambi (-1,582; 103,616) [lokasi wakil, lahan fiktif]. "
    "Magnitudo Mw 7,0 dari peta deagregasi PuSGeN Gambar 4.28 hal. 166 (dibaca dari peta, 6,6-7,2).",
    "Tinggi tekan pasir U5 saat gempa +9,5 [Asumsi: muka sungai maksimum tahunan rata-rata, TOR Lampiran A]; "
    "kepekaan +7,7 (normal, 2.3) dan +11,2 (banjir). Lapisan di atas pasir: MAT 0,7 m.",
    "Persamaan: CSR Pers. 2.2 hal. 5; rd 2.14 hal. 8; CN 2.15 hal. 10; Kσ 2.16 hal. 11; MSF 2.19-2.21 hal. 14; "
    "koreksi butir halus 2.22-2.23 hal. 15; CRR 2.24-2.25 hal. 17; Ic dan FC 2.26-2.30 hal. 19-21 (CFC = 0).",
    "SPT: N60 dari langkah 2.1 (ER per bor). Panjang batang > 10 m di U5 sehingga koreksi panjang batang = 1; "
    "diameter lubang 100 mm dan tabung tanpa lapisan dianggap 1 [Asumsi]. Uji penolakan dan uji tidak dipakai "
    "(langkah 2.1) tidak dihitung. FC dari saringan bila ada, selain itu median 8,7 %.",
    "CPT: qt dari langkah 2.1 tiap 0,05 m di U5; titik dengan Ic ≥ 2,6 dianggap bukan pasir (tidak dinilai).",
]

CATATAN = [
    "Pasir U5 MUDAH LIKUIFAKSI di seluruh tapak: FS SPT 0,25-0,72 (38 uji, semua < 1) dan FS CPT 0,22-0,75 "
    "(tebal FS < 1: 7-10 m di tiap CPTu). Hasil SPT dan CPT konsisten (VERIFIKASI T-25).",
    "Penyebab: amax 0,34 g (PGA 0,164 × FPGA 2,08 untuk SE), pasir lepas-agak padat ((N1)60cs 9-24; qc1Ncs persentil 5-95 % 97-128), "
    "dan tegangan efektif rendah di bawah lempung lunak (σv/σ'v ±2,0-3,3 sehingga CSR 0,35-0,63).",
    "Kepekaan: Mw 6,5-7,5, tinggi tekan +7,7 s.d. +11,2, amax dikurangi menjadi 80 % (batas bawah PGAM spesifik-situs, "
    "SNI 1726 Pasal 6.10.5.3): FS SPT maksimum 0,61-0,94, tetap < 1. Pengaruh urugan +11,50 belum dihitung; "
    "diperiksa ulang di Tahap 6 bersama elevasi dasar basement. Kesimpulan tidak peka asumsi.",
    "Akibat untuk kelas situs (SNI 1726:2019 Pasal 5.3.1 butir 1): situs SF. Pengecualian T ≤ 0,5 detik tidak berlaku "
    "karena Ta gedung ±0,53-0,82 detik (Pers. 36, Tabel 18 hal. 72; hn ±24 m [Asumsi]). Wajib analisis respons "
    "spesifik-situs (Pasal 6.10) untuk spektrum desain - masuk lingkup Tahap 4.",
    "Akibat untuk fondasi (SNI 8460 Pasal 12.2.4.3 hal. 276): fondasi dangkal tidak direkomendasikan; gesekan tiang di "
    "U5 diabaikan saat gempa; penurunan pascalikuifaksi dan downdrag diperiksa (FK > 1,1, hal. 277). Tiang harus "
    "menembus U5 dan bertumpu di U7 atau dalam U6 (Tahap 6).",
    "Tebing sungai berjarak 6-12 m dari batas lahan dengan pasir U5 yang naik ke ±+1,6 di sisi tebing (2.2): potensi "
    "penyebaran lateral (lateral spreading) ke arah sungai; diperiksa di langkah 2.7 dan Tahap 6.",
    "Lempung U4 dan U6 (PI 25-68) dan gambut U3 tidak dinilai dengan prosedur pasir; perilaku siklik lempung lunak "
    "(pelunakan) dibahas bersama analisis respons situs.",
]


def buat(keluar=BERKAS):
    sp = lq.analisis_spt()
    cp = lq.analisis_cpt()
    rk = lq.ringkas_cpt(cp)
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk langkah 2.6 likuifaksi", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i, t] for i, t in enumerate(PETUNJUK, start=1)], rata=list("cl"))

    # ---- beban gempa
    lb = Lembar(wb.create_sheet("Beban Gempa"), 2, "Beban gempa untuk analisis likuifaksi", [6, 34, 12, 10, 56])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    r0 = lb.baris + 1
    beban = [
        ("PGA batuan dasar (MCEG)", lq.PGA, "g", "Desain Spektra Indonesia PUPR 2021, -1,582; 103,616"),
        ("Ss / S1 (MCER batuan dasar)", f"{lq.SS} / {lq.S1}".replace(".", ","), "g", "Idem; dipakai di Tahap 4"),
        ("FPGA kelas SE", f"=IF(E{r0}<=0.1,2.4,IF(E{r0}<=0.2,2.4-(E{r0}-0.1)/0.1*0.5,1.9-(E{r0}-0.2)/0.1*0.3))", "-",
         "SNI 1726:2019 Tabel 10 hal. 39, interpolasi linear"),
        ("PGAM = FPGA · PGA = amax", f"=E{r0}*E{r0 + 2}", "g", "SNI 1726:2019 Pers. 15 hal. 39"),
        ("Magnitudo momen Mw", lq.MW, "-", "PuSGeN 2017 deagregasi Gambar 4.28 hal. 166 (6,6-7,2) [dibaca dari peta]"),
        ("Tinggi tekan U5 saat gempa", lq.H_AKUIFER, "m", "[Asumsi] maks. tahunan rata-rata sungai (TOR Lampiran A)"),
        ("Ta gedung, rangka beton pemikul momen", "=0.0466*24^0.9", "detik", "SNI 1726 Pers. 36, Tabel 18 hal. 72; hn 24 m [Asumsi]"),
        ("Ta gedung, sistem lain", "=0.0488*24^0.75", "detik", "Idem"),
    ]
    lb.tabel(["No", "Besaran", "Nilai", "Satuan", "Sumber"], [[i + 1, a, b, c, d] for i, (a, b, c, d) in
                                                               enumerate(beban)],
             rata=list("clccl"), fmt=[None, None, "0.000", None, None], fill_kolom={2: AI})
    amax_sel = f"'Beban Gempa'!$E${r0 + 3}"
    m_sel = f"'Beban Gempa'!$E${r0 + 4}"

    # ---- SPT
    lb = Lembar(wb.create_sheet("SPT"), 3, "Likuifaksi pasir U5 dari SPT (" + IB + ")",
                [5, 7, 7, 6, 7, 7, 8, 8, 9, 7, 8, 8, 7, 8, 8, 24])
    lb.catatan(LABEL + " (N1)60cs hasil iterasi CN (Pers. 2.15) dengan Δ(N1)60 (Pers. 2.23). rd, CSR, CRR, MSF, Kσ, "
               "dan FS ditulis sebagai rumus Excel. " + LABEL_AI)
    lb.kosong()
    r0 = lb.baris + 1
    baris = []
    for i, x in enumerate(sorted(sp, key=lambda x: (x["bor"], x["z"]))):
        r = r0 + i
        z, sv, sve, n = f"E{r}", f"I{r}", f"J{r}", f"K{r}"
        rd_ = (f"=EXP((-1.012-1.126*SIN({z}/11.73+5.133))+(0.106+0.118*SIN({z}/11.28+5.142))*{m_sel})")
        baris.append([i + 1, x["bor"], round(x["z"], 3), x["n"], round(x["n60"], 2), x["fc"],
                      round(x["sv"], 1), round(x["sve"], 1), round(x["n160cs"], 2), rd_,
                      f"=0.65*{sv}/{sve}*{amax_sel}*L{r}",
                      f"=EXP({n}/14.1+({n}/126)^2-({n}/23.6)^3+({n}/25.4)^4-2.8)"
                      f"*(1+(MIN(2.2,1.09+({n}/31.5)^2)-1)*(8.64*EXP(-{m_sel}/4)-1.325))"
                      f"*MIN(1.1,1-MIN(0.3,1/(18.9-2.55*SQRT(MIN({n},37))))*LN({sve}/101.325))",
                      f"=N{r}/M{r}", f'=IF(O{r}<1,"Likuifaksi","Aman")', x["sumber_fc"]])
    lb.tabel(["No", "Bor", "z (m)", "N", "N60", "FC (%)", "σv (kPa)", "σ'v (kPa)", "(N1)60cs", "rd", "CSR",
              "CRR (M, σ'v)", "FS", "Status", "FC dari"], baris, rata=list("ccccccccccccccc")[:15],
             fmt=[None, None, "0.00", "0", "0.0", "0.0", "0.0", "0.0", "0.0", "0.000", "0.000", "0.000", "0.00", None,
                  None], fill_kolom={i: AI for i in (8, 9, 10, 11, 12, 13)}, beku_kolom=2)

    # ---- CPT
    lb = Lembar(wb.create_sheet("CPT"), 4, "Likuifaksi pasir U5 dari CPTu (rata-rata tiap 0,5 m)",
                [5, 8, 8, 9, 8, 8, 8, 9, 8, 8, 9, 22])
    lb.catatan(LABEL + " Nilai per 0,05 m dirata-ratakan tiap 0,5 m; FS minimum dalam rentang juga ditampilkan. "
               "Hanya Ic < 2,6. " + LABEL_AI)
    lb.kosong()
    baris, i = [], 0
    for n, b in cp.items():
        for a in np.arange(9.0, 20.0, 0.5):
            g = [x for x in b if a <= x["z"] < a + 0.5 and x["fs_liq"] is not None]
            if not g:
                continue
            i += 1
            fsr = float(np.mean([x["fs_liq"] for x in g]))
            baris.append([i, n, f"{a:.1f}-{a + 0.5:.1f}".replace(".", ","), round(np.mean([x["qt"] for x in g]) / 1000, 2),
                          round(np.mean([x["ic"] for x in g]), 2), round(np.mean([x["fc"] for x in g]), 1),
                          round(np.mean([x["qc1ncs"] for x in g]), 1), round(np.mean([x["csr"] for x in g]), 3),
                          round(np.mean([x["crr"] for x in g]), 3), round(fsr, 2),
                          round(min(x["fs_liq"] for x in g), 2), "Likuifaksi" if fsr < 1 else "Aman"])
    lb.tabel(["No", "CPTu", "z (m)", "qt (MPa)", "Ic", "FC (%)", "qc1Ncs", "CSR", "CRR", "FS rata-rata",
              "FS min", "Status"], baris, rata=list("cccccccccccc"),
             fmt=[None, None, None, "0.00", "0.00", "0.0", "0.0", "0.000", "0.000", "0.00", "0.00", None],
             fill_kolom={i: AI for i in range(4, 12)}, beku_kolom=2)

    # ---- kepekaan
    lb = Lembar(wb.create_sheet("Kepekaan"), 5, "Kepekaan FS terhadap asumsi", [6, 44, 12, 12, 12, 12, 40])
    lb.catatan(LABEL + " FS SPT (38 uji) dan CPTu (semua titik Ic < 2,6). " + LABEL_AI)
    lb.kosong()
    kas = [("Dasar: Mw 7,0; h +9,5; amax 0,342", {}),
           ("Mw 6,5", dict(m=6.5)), ("Mw 7,5", dict(m=7.5)),
           ("Tinggi tekan +7,7 (normal)", dict(h=7.7)), ("Tinggi tekan +11,2 (banjir)", dict(h=11.2)),
           ("amax 80 % (batas bawah spesifik-situs)", dict(amax=0.8 * lq.AMAX)),
           ("amax 80 % dan h +7,7 (paling menguntungkan)", dict(amax=0.8 * lq.AMAX, h=7.7))]
    baris = []
    for i, (nama, kw) in enumerate(kas):
        s = [x["fs"] for x in lq.analisis_spt(**kw)]
        c = lq.analisis_cpt(**kw)
        cf = [x["fs_liq"] for b in c.values() for x in b if x["fs_liq"] is not None]
        baris.append([i + 1, nama, round(float(np.median(s)), 2), round(max(s), 2), round(float(np.median(cf)), 2),
                      round(float(np.percentile(cf, 95)), 2), "Likuifaksi" if max(s) < 1 else "Sebagian"])
    lb.tabel(["No", "Kasus", "FS SPT median", "FS SPT maks", "FS CPT median", "FS CPT persentil 95",
              "Kesimpulan"], baris, rata=list("clccccl"), fmt=[None, None, "0.00", "0.00", "0.00", "0.00", None],
             fill_kolom={i: AI for i in range(2, 7)})
    lb.catatan("Urugan +11,50 (±1,5-2,3 m) menaikkan σ'v dan menurunkan σv/σ'v sehingga FS naik; belum dihitung. Karena "
               "kasus paling menguntungkan di atas masih memberi FS maks 0,94, pengaruhnya diperiksa di Tahap 6.", fill=AI)

    lb = Lembar(wb.create_sheet("Kesimpulan"), 6, "Kesimpulan dan catatan langkah 2.6", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Catatan"], [[i, t] for i, t in enumerate(CATATAN, start=1)], rata=list("cl"),
             fill_kolom={1: AI})
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar, rk


def gambar():
    sp = lq.analisis_spt()
    cp = lq.analisis_cpt()
    k = Kertas()
    ax = k.sumbu(35, 70, 110, 190)
    for n, b in cp.items():
        ax.plot([x["fs_liq"] if x["fs_liq"] is not None else np.nan for x in b], [x["z"] for x in b], lw=0.5,
                alpha=0.8, label=n)
    ax.plot([x["fs"] for x in sp], [x["z"] for x in sp], "ko", ms=3, label="SPT (38 uji)")
    ax.axvline(1.0, color="#b00020", lw=1.0)
    ax.text(1.02, 19.6, "FS = 1", color="#b00020", fontsize=6)
    ax.set_xlim(0, 2)
    ax.set_ylim(20, 8)
    ax.set_xlabel("FS likuifaksi = CRR / CSR", fontsize=6.5)
    ax.set_ylabel("Kedalaman (m)", fontsize=6.5)
    ax.legend(fontsize=5, loc="lower right", ncol=2)
    gaya_sumbu(ax, "A. Faktor keamanan terhadap likuifaksi, pasir U5")
    ax2 = k.sumbu(165, 155, 130, 105)
    for n, b in cp.items():
        ax2.plot([x["qc1ncs"] for x in b if x["fs_liq"]], [x["csr"] / x["msf"] / x["ks"] for x in b if x["fs_liq"]],
                 ".", ms=1.2, alpha=0.5)
    q = np.linspace(20, 200, 100)
    ax2.plot(q, [lq.crr_cpt(v) for v in q], "k", lw=1.2, label="CRR M7,5 σ'1 (IB2014 Pers. 2.24)")
    ax2.set_xlim(0, 200)
    ax2.set_ylim(0, 0.8)
    ax2.set_xlabel("qc1Ncs", fontsize=6.5)
    ax2.set_ylabel("CSR M7,5 σ'1 = CSR / (MSF Kσ)", fontsize=6.5)
    ax2.legend(fontsize=5.2, loc="upper left")
    ax2.text(150, 0.65, "LIKUIFAKSI", fontsize=8, color="#b00020", fontweight="bold")
    gaya_sumbu(ax2, "B. Data CPTu terhadap kurva pemicu likuifaksi")
    ax3 = k.sumbu(165, 70, 130, 60)
    n160 = np.linspace(2, 40, 100)
    ax3.plot(n160, [lq.crr_spt(v) for v in n160], "k", lw=1.2, label="CRR M7,5 σ'1 (IB2014 Pers. 2.25)")
    ax3.plot([x["n160cs"] for x in sp], [x["csr"] / x["msf"] / x["ks"] for x in sp], "o", ms=3, color="#c9a227",
             label="SPT pasir U5")
    ax3.set_xlim(0, 40)
    ax3.set_ylim(0, 0.8)
    ax3.set_xlabel("(N1)60cs", fontsize=6.5)
    ax3.set_ylabel("CSR M7,5 σ'1", fontsize=6.5)
    ax3.legend(fontsize=5.2, loc="upper left")
    gaya_sumbu(ax3, "C. Data SPT terhadap kurva pemicu likuifaksi")
    k.teks(35, 275, "EVALUASI PEMICU LIKUIFAKSI PASIR U5", fontsize=11, fontweight="bold")
    k.teks(35, 270, f"{IB}; amax = PGAM = {lq.AMAX:.3f} g (SNI 1726 Pers. 15), Mw {lq.MW:.1f}, tinggi tekan +9,5"
           .replace(".", ","), fontsize=6.5)
    kotak_catatan(k, 287, "CATATAN", [
        "Semua uji SPT (38) dan hampir semua data CPTu di pasir U5 memberi FS < 1: pasir U5 mudah likuifaksi.",
        "Kesimpulan tetap untuk Mw 6,5-7,5, tinggi tekan +7,7 s.d. +11,2, dan amax 80 %.",
        "Situs menjadi kelas SF (SNI 1726:2019 Pasal 5.3.1 butir 1); Ta gedung ±0,53-0,82 detik > 0,5 detik sehingga "
        "pengecualian tidak berlaku. Analisis respons spesifik-situs diperlukan (Tahap 4).",
        "Fondasi: tiang menembus U5; gesekan di U5 diabaikan saat gempa; periksa penurunan pascalikuifaksi dan downdrag "
        "(SNI 8460 Pasal 12.2.4.3). Potensi penyebaran lateral ke arah sungai diperiksa di langkah 2.7.",
        "PGA batuan dasar dari Desain Spektra Indonesia PUPR (2021); Mw dari peta deagregasi PuSGeN Gambar 4.28.",
    ], 85)
    k.etiket("Evaluasi pemicu likuifaksi pasir U5", "GT-12", "Tanpa skala", "1 / 1")
    with PdfPages(PDF) as pdf:
        k.simpan(pdf, PNG)
    return PDF


if __name__ == "__main__":
    print(buat()[0])
    print(gambar())
