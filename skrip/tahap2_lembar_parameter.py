"""Tahap 2 langkah 2.4: Excel '02 Olah Data Tanah/2.4 Parameter Tanah.xlsx' (format wajib).

Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap2_lembar_parameter.py
"""
from pathlib import Path

import numpy as np
import openpyxl
from openpyxl.worksheet.formula import ArrayFormula

import tahap2_parameter as tp
from format_dokumen import AI, Lembar, set_font_bawaan

AKAR = Path(__file__).resolve().parents[1]
BERKAS = AKAR / "02 Olah Data Tanah" / "2.4 Parameter Tanah.xlsx"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = ("DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026. "
            "Kunci jawaban tidak dibuka.")
KAR = ("Nilai karakteristik = rata-rata ∓ 0,5 simpangan baku (arah yang merugikan) [Literatur: Schneider 1999, "
       "pendekatan 'cautious estimate' EN 1997-1; belum ada di acuan/]. SNI 8460:2017 Pasal 5.7.3-5.7.4 hal. 63-64 "
       "hanya mensyaratkan zona lemah dibahas dan korelasi didokumentasikan.")

PETUNJUK = [
    "Langkah 2.4 menurunkan parameter tanah per unit (U1-U8, langkah 2.2) dari data lab, CPTu (qt langkah 2.1), "
    "SPT (N60 langkah 2.1), dan air tanah (langkah 2.3). Lembar Ringkasan berisi usulan nilai desain.",
    "Contoh yang tidak dipakai: BH-2 UD-2 (rusak) dan BH-7 UD-3 (mutu buruk) - langkah 2.1. Berat isi BH-3 di lab "
    "lama tidak dipakai (tertulis < γw, Tahap 1 no. 11).",
    "Rumus dan sumber: su = (qt - σv0)/Nkt GEC 5 Pers. 7.13 hal. 7-36; σ'p = 0,33 (qt - σv0) GEC 5 Gambar 6-23 "
    "hal. 6-29; ch = T* a² √Ir / t50 dengan T*50 = 0,245 (u2) GEC 5 Pers. 6.19 hal. 6-36 dan Tabel 6-7 hal. 6-37; "
    "Cα/Cc GEC 5 hal. 6-46; φ' = √(15,4 (N1)60) + 20 GEC 5 Pers. 7.23 hal. 7-55; CN = 0,77 log(20/po) FHWA "
    "NHI-06-088 Pers. 3-3 hal. 3-56.",
    KAR,
    "σ'v0 kondisi sekarang memakai MAT 0,7 m di bawah muka tanah (median SP-1, langkah 2.3) dan tekanan pori "
    "hidrostatik [Asumsi].",
    "Gambar pendukung: '2.4 Gambar Parameter.pdf' (GT-09 profil lempung, GT-10 pasir dan kuat geser efektif).",
]


def buat(keluar=BERKAS):
    lab = tp.contoh_lab()
    kon = tp.konsolidasi()
    rk = tp.rangkak()
    nkt = tp.kalibrasi_nkt()
    dis = tp.disipasi_ch()
    cu = tp.triaksial_cu()
    spt = tp.spt_pasir()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    ref = {}

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk langkah 2.4 parameter tanah", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i, t] for i, t in enumerate(PETUNJUK, start=1)], rata=list("cl"))

    # ---------------- Indeks
    lb = Lembar(wb.create_sheet("Indeks"), 3, "Sifat indeks dan kuat geser UU contoh UD (bor gedung)",
                [5, 8, 8, 8, 8, 9, 9, 8, 8, 9, 9, 9, 40])
    lb.catatan(LABEL + " Sumber: lembar Indeks dan Triaksial UU di 'Laboratorium.xlsx' dan "
               "'Laboratorium Tambahan.xlsx'. Unit dari kedalaman tengah contoh dan log bor (2.2). " + LABEL_AI)
    lb.kosong()
    data = sorted(lab.values(), key=lambda d: (d["unit"], d["titik"], d["z"]))
    r0 = lb.baris + 1
    baris = []
    for i, d in enumerate(data):
        cat = d["alasan"] or d.get("gamma_catatan", "")
        baris.append([i + 1, d["titik"], d["contoh"], d["unit"], d["z"], d["w"], d["gamma"], d["LL"], d["PI"],
                      d["org"], d.get("su_uu"), "Ya" if d["dipakai"] else "Tidak", cat])
    lb.tabel(["No", "Titik", "Contoh", "Unit", "z (m)", "w (%)", "γ (kN/m³)", "LL (%)", "PI (%)", "Organik (%)",
              "su UU (kPa)", "Dipakai?", "Catatan"], baris, rata=list("ccccccccccccl"),
             fmt=[None, None, None, None, "0.00", "0.0", "0.00", "0", "0", "0.0", "0.0", None, None],
             fill_kolom={11: AI, 12: AI}, beku_kolom=3)
    r1 = r0 + len(baris) - 1
    rng = lambda k: f"Indeks!${k}${r0}:${k}${r1}"  # noqa: E731
    ref["idx"] = dict(unit=rng("F"), w=rng("H"), g=rng("I"), LL=rng("J"), PI=rng("K"), su=rng("M"), pakai=rng("N"))

    # ---------------- Kuat geser lempung lunak
    lb = Lembar(wb.create_sheet("Su Lempung"), 4, "Kuat geser tak terdrainase lempung lunak U4",
                [5, 10, 14, 14, 14, 14, 14, 40])
    lb.catatan(LABEL + " su UU (contoh dipakai) terhadap kedalaman; kalibrasi Nkt dengan CPTu di kedalaman yang sama "
               "(median qt - σv0 tiap CPTu dalam ±0,25 m lalu median antar-CPTu, unit U4; CPTu-4 di atas 4,5 m tidak dipakai). " + LABEL_AI)
    lb.kosong()
    lb.bagian("A", "Kalibrasi Nkt (GEC 5 Pers. 7.13 hal. 7-36: Nkt lazim 10-20)")
    r0 = lb.baris + 1
    baris = []
    for i, x in enumerate(sorted(nkt, key=lambda x: x["z"])):
        r = r0 + i
        baris.append([i + 1, x["titik"] + " " + x["contoh"], x["z"], x["su"], round(x["qnet"], 1), f"=G{r}/F{r}",
                      "", "su UU rendah: Nkt tinggi" if x["Nkt"] > 19 else ""])
    lb.tabel(["No", "Contoh", "z (m)", "su UU (kPa)", "qt - σv0 CPTu (kPa)", "Nkt", "", "Catatan"], baris,
             rata=list("clccccc") + ["l"], fmt=[None, None, "0.00", "0.0", "0.0", "0.0", None, None],
             fill_kolom={5: AI, 7: AI}, beku=False)
    r1 = r0 + len(baris) - 1
    lb.catatan(f"Nkt median {np.median([x['Nkt'] for x in nkt]):.1f}; dipakai Nkt = 12 [usulan] (sesuai acuan kompresi "
               "triaksial ±10, GEC 5 hal. 7-36; contoh berpenunjuk 'Nkt tinggi' memiliki su UU rendah).".replace(
                   "12.2", "12,2"), fill=AI)
    lb.kosong()
    lb.bagian("B", "Garis su terhadap kedalaman (regresi su UU contoh dipakai)")
    d4 = [x for x in lab.values() if x["unit"] == "U4" and x["dipakai"] and x.get("su_uu")]
    z = np.array([x["z"] for x in d4])
    s = np.array([x["su_uu"] for x in d4])
    b, a = np.polyfit(z, s, 1)
    sd = float(np.std(s - (a + b * z), ddof=2))
    lb.tabel(["No", "Besaran", "Nilai", "Satuan", "", "", "", "Keterangan"],
             [[1, "su = a + b z : a", round(a, 2), "kPa", "", "", "", f"n = {len(d4)} contoh (U4)"],
              [2, "b", round(b, 3), "kPa/m", "", "", "", "z dari muka tanah setempat"],
              [3, "simpangan baku residu", round(sd, 2), "kPa", "", "", "", ""],
              [4, "Garis karakteristik: a - 0,5 sd", round(a - 0.5 * sd, 2), "kPa", "", "", "",
               "su,k = a_k + b z [usulan]"]],
             rata=list("clcccccl"), fmt=[None, None, "0.00", None, None, None, None, None],
             fill_kolom={2: AI, 7: AI}, beku=False)
    lb.ws._print_rows = None
    ref["su"] = (a, b, sd)

    # ---------------- Konsolidasi
    lb = Lembar(wb.create_sheet("Konsolidasi"), 5, "Parameter pemampatan dan konsolidasi (oedometer)",
                [5, 8, 7, 6, 7, 7, 7, 7, 8, 9, 9, 9, 9, 9, 12, 30])
    lb.catatan(LABEL + " σ'p lab = Casagrande (laboratorium); σ'p bilinear = perpotongan dua garis lurus e-log σ' "
               "(dihitung ulang, cek silang). cv NC = median cv tahap ≥ 1,5 σ'p. σ'v0 dengan MAT 0,7 m. " + LABEL_AI)
    lb.kosong()
    r0 = lb.baris + 1
    baris = []
    sv0 = _sv0_mat07()
    for i, k in enumerate(sorted(kon, key=lambda k: (k["unit"], k["z"]))):
        r = r0 + i
        baris.append([i + 1, k["titik"], k["contoh"], k["unit"], k["z"], k["e0"], k["Cc"], k["Cr"],
                      f"=I{r}/(1+H{r})", k["sp_lab"], round(k["sp_bil"], 1), round(sv0[(k["titik"], k["contoh"])], 1),
                      f"=M{r}/N{r}", k["cv_nc"], k["lunne"], k["alasan"] or (
                          "σ'p lab tidak cocok dengan kurva; pakai bilinear" if (k["titik"], k["contoh"]) ==
                          ("BH-5", "UD-1") else "")])
    lb.tabel(["No", "Titik", "Contoh", "Unit", "z (m)", "e0", "Cc", "Cr", "CR = Cc/(1+e0)", "σ'p lab (kPa)",
              "σ'p bilinear (kPa)", "σ'v0 (kPa)", "OCR (bilinear)", "cv NC (m²/th)", "Mutu (2.1)", "Catatan"], baris,
             rata=list("ccccccccccccccc") + ["l"],
             fmt=[None, None, None, None, "0.00", "0.000", "0.000", "0.000", "0.000", "0", "0.0", "0.0", "0.00", "0.00",
                  None, None], fill_kolom={i: AI for i in (8, 10, 11, 12, 15)}, beku_kolom=3)
    lb.kosong()
    lb.bagian("A", "Pemampatan sekunder (tahap beban 7 hari)")
    r0 = lb.baris + 1
    baris = []
    for i, x in enumerate(rk):
        r = r0 + i
        batas = "0,06 ± 0,01 (gambut)" if x["titik"] == "BH-7" else "0,04 ± 0,01 (anorganik)"
        baris.append([i + 1, x["titik"], x["contoh"], "", "", x["tegangan"], round(x["Ca"], 4), x["Cc"],
                      f"=I{r}/J{r}", batas, "", "", "", "", "", "Cα dari dekade 2.880-10.080 menit"])
    lb.tabel(["No", "Titik", "Contoh", "", "", "σ' tahap (kPa)", "Cα", "Cc", "Cα/Cc", "GEC 5 hal. 6-46", "", "", "",
              "", "", "Catatan"], baris, rata=list("ccccccccccccccc") + ["l"],
             fmt=[None, None, None, None, None, "0", "0.0000", "0.000", "0.000", None] + [None] * 6,
             fill_kolom={6: AI, 8: AI}, beku=False)
    lb.ws._print_rows = None

    # ---------------- Disipasi
    lb = Lembar(wb.create_sheet("Disipasi CPTu"), 6, "Uji disipasi CPTu: t50 dan ch dihitung ulang",
                [5, 9, 7, 9, 9, 9, 9, 9, 10, 10, 10, 38])
    lb.catatan(LABEL + f" Un = (u - u0)/(ui - u0), GEC 5 Pers. 6.20 hal. 6-37; u0 hidrostatik MAT 0,7 m. "
               f"ch = T* a² √Ir / t50, T*50 = 0,245, a = 1,784 cm, Ir = {tp.IR} [Asumsi: rentang 50-150; ch berubah "
               "±40 %]. t50 penyedia memakai u akhir sebagai patokan (salah bila uji belum setimbang). " + LABEL_AI)
    lb.kosong()
    baris = []
    for i, d in enumerate(dis):
        cat = ""
        if d["t50"] is None and d["un_akhir"] > 0.5:
            cat = "Belum mencapai 50 % disipasi: t50 tidak bisa ditentukan; t50 penyedia keliru"
        elif d["t50"] is None:
            cat = "Pasir: disipasi seketika (u ≈ u0)"
        elif d["t50_penyedia"] and abs(d["t50"] - float(str(d["t50_penyedia"]).replace(",", "."))) > 10:
            cat = "t50 penyedia keliru (patokan u akhir, bukan u0)"
        elif d["un_akhir"] < 0:
            cat = "u akhir < u0 hidrostatik: muka air di titik ini lebih dalam"
        baris.append([i + 1, d["cptu"], d["z"], round(d["u0"], 1), d["ui"], d["u_akhir"], d["durasi"],
                      round(d["un_akhir"], 2), round(d["t50"], 1) if d["t50"] else "-", d["t50_penyedia"],
                      round(d["ch"], 1) if d["ch"] else "-", cat])
    lb.tabel(["No", "CPTu", "z (m)", "u0 (kPa)", "ui (kPa)", "u akhir (kPa)", "Durasi (menit)", "Un akhir",
              "t50 hitung ulang (menit)", "t50 penyedia (menit)", "ch (m²/th)", "Catatan"], baris,
             rata=list("ccccccccccc") + ["l"], fmt=[None, None, "0.0", "0.0", "0.0", "0.0", "0", "0.00", "0.0", None,
                                                    "0.0", None], fill_kolom={7: AI, 8: AI, 10: AI, 11: AI})

    # ---------------- CU
    lb = Lembar(wb.create_sheet("Triaksial CU"), 7, "Kuat geser efektif dari triaksial CU",
                [5, 9, 7, 6, 9, 9, 9, 9, 10, 10, 10, 34])
    lb.catatan(LABEL + " σ'3f = σ'3c - Δu; σ'1f = σ'3f + (σ1 - σ3); p' = (σ'1 + σ'3)/2, q = (σ1 - σ3)/2; "
               "q = p' sin φ' + c' cos φ'. Dua cara: lewat titik nol (c' = 0) dan regresi bebas. " + LABEL_AI)
    lb.kosong()
    baris = []
    for i, c in enumerate(cu):
        cat = {"U3": "Gambut berserat: φ' tinggi lazim, tidak dipakai langsung untuk stabilitas",
               "U6": "Lempung kaku terkonsolidasi lebih: c' > 0"}.get(c["unit"], "")
        pq = "; ".join(f"({p:.0f}; {q:.0f})" for p, q in c["pq"])
        baris.append([i + 1, c["titik"], c["contoh"], c["unit"], c["z"], pq, "", "", round(c["phi_c0"], 1),
                      round(c["phi"], 1), round(c["c"], 1), cat])
    lb.tabel(["No", "Titik", "Contoh", "Unit", "z (m)", "(p'; q) runtuh (kPa)", "", "", "φ' (c' = 0) (°)",
              "φ' regresi (°)", "c' regresi (kPa)", "Catatan"], baris, rata=list("cccccl") + ["c"] * 5 + ["l"],
             fmt=[None, None, None, None, "0.00", None, None, None, "0.0", "0.0", "0.0", None],
             fill_kolom={8: AI, 9: AI, 10: AI, 11: AI})
    for rr in range(lb.baris - len(baris) - 1, lb.baris):
        lb.ws.merge_cells(start_row=rr, start_column=8, end_row=rr, end_column=10)

    # ---------------- Pasir
    lb = Lembar(wb.create_sheet("Pasir SPT"), 8, "Pasir U5 dan U7: (N1)60 dan φ' dari SPT",
                [5, 8, 8, 6, 9, 9, 9, 9, 9, 30])
    lb.catatan(LABEL + " N60 dari langkah 2.1; σ'v0 dengan MAT 0,7 m, γ pasir 19 [Asumsi]; CN = 0,77 log10(20/po), "
               "po dalam tsf (1 tsf = 95,76 kPa), CN ≤ 2 (FHWA NHI-06-088 Pers. 3-3); φ' = √(15,4 (N1)60) + 20 (GEC 5 "
               "Pers. 7.23). Uji penolakan tidak dipakai untuk statistik. " + LABEL_AI)
    lb.kosong()
    r0 = lb.baris + 1
    baris = []
    for i, x in enumerate(sorted(spt, key=lambda x: (x["unit"], x["bor"], x["z"]))):
        r = r0 + i
        baris.append([i + 1, x["bor"], x["unit"], x["z"], round(x["n60"], 1), round(x["sv_eff"], 1),
                      f"=MIN(2,0.77*LOG10(20/(H{r}/95.76)))", f"=I{r}*G{r}", f"=SQRT(15.4*J{r})+20",
                      "Penolakan (batas bawah), tidak dihitung statistik" if x["tolak"] else ""])
    lb.tabel(["No", "Bor", "Unit", "z (m)", "N60", "σ'v0 (kPa)", "CN", "(N1)60", "φ' (°)", "Catatan"], baris,
             rata=list("ccccccccc") + ["l"], fmt=[None, None, None, "0.00", "0.0", "0.0", "0.00", "0.0", "0.0", None],
             fill_kolom={6: AI, 7: AI, 8: AI, 9: AI}, beku_kolom=2)
    r1 = r0 + len(baris) - 1
    ref["spt"] = dict(unit=f"'Pasir SPT'!$E${r0}:$E${r1}", n160=f"'Pasir SPT'!$J${r0}:$J${r1}",
                      phi=f"'Pasir SPT'!$K${r0}:$K${r1}", cat=f"'Pasir SPT'!$L${r0}:$L${r1}")

    # ---------------- Ringkasan (dibuat terakhir, ditaruh di depan)
    lb = Lembar(wb.create_sheet("Ringkasan", 1), 2, "Usulan parameter tanah desain per unit",
                [5, 7, 26, 9, 9, 9, 9, 11, 50])
    lb.catatan(LABEL + " USULAN untuk diputuskan Defsa. " + KAR + " " + LABEL_AI)
    lb.kosong()
    a, b, sd = ref["su"]
    k4 = [k for k in kon if k["unit"] == "U4" and k["dipakai"]]
    st_ = {n: (float(np.mean([k[n] for k in k4])), float(np.std([k[n] for k in k4], ddof=1))) for n in ("Cc", "Cr", "e0")}
    phi4 = [c["phi_c0"] for c in cu if c["unit"] == "U4"]
    st_["phi"] = (float(np.mean(phi4)), float(np.std(phi4, ddof=1)))
    I, S = ref["idx"], ref["spt"]

    def stat_idx(kol, unit, fungsi):
        return f'={fungsi}(IF(({I["unit"]}="{unit}")*({I["pakai"]}="Ya")*ISNUMBER({I[kol]}),{I[kol]}))'

    baris = [
        ["U1", "Urugan: γ", 17.0, "", "", 17.0, "kN/m³", "[Asumsi] tidak diuji; dikupas/diganti saat pekerjaan tanah"],
        ["U2", "Kerak: γ", stat_idx("g", "U2", "AVERAGE"), "", "", 17.8, "kN/m³", "[Uji sendiri] n = 2"],
        ["U2", "Kerak: su", stat_idx("su", "U2", "AVERAGE"), "", "", 35, "kPa", "[Uji sendiri] UU n = 2; σ'p ±96-99 kPa"],
        ["U3", "Gambut: γ", 10.7, "", "", 10.7, "kN/m³",
         "[Uji sendiri] BH-7 UD-2; bor tangan: gambut 10,7-11,6, lempung organik 11,9-13,1"],
        ["U3", "Gambut: Cc / e0", "3,55 / 6,01", "", "", "3,5 / 6,0", "-",
         "[Uji sendiri] BH-7 UD-2 (BH-3 UD-2: 2,74, kurva tidak wajar - Tahap 1 no. 12)"],
        ["U3", "Gambut: Cα", 0.212, "", "", 0.21, "-", "[Uji sendiri] Cα/Cc = 0,060 (GEC 5: 0,06 ± 0,01)"],
        ["U3", "Gambut: su", 9.5, "", "", 8, "kPa", "[Uji sendiri] UU n = 3, regangan runtuh > 20 %"],
        ["U3", "Gambut: cv", 8.3, "", "", 8, "m²/th", "[Uji sendiri] BH-7 UD-2 NC"],
        ["U4", "Lempung lunak: γ", stat_idx("g", "U4", "AVERAGE"), stat_idx("g", "U4", "STDEV"), "", 15.2, "kN/m³",
         "[Uji sendiri]"],
        ["U4", "Lempung lunak: w", stat_idx("w", "U4", "AVERAGE"), stat_idx("w", "U4", "STDEV"), "", "-", "%",
         "[Uji sendiri]"],
        ["U4", "Lempung lunak: PI", stat_idx("PI", "U4", "AVERAGE"), stat_idx("PI", "U4", "STDEV"), "", "-", "%",
         "[Uji sendiri] CH plastisitas tinggi"],
        ["U4", "Lempung lunak: su (z)", f"{a:.2f} + {b:.2f} z".replace(".", ","), round(sd, 2), "",
         f"{a - 0.5 * sd:.1f} + {b:.2f} z".replace(".", ","), "kPa",
         "[Uji sendiri] UU n = 23; CPTu Nkt = 12 memberi profil serupa (GT-09)"],
        ["U4", "Lempung lunak: Cc", st_["Cc"][0], st_["Cc"][1], "", 0.75, "-",
         f"[Uji sendiri] {len(k4)} contoh dipakai; desain = rata + 0,5 sd (merugikan)"],
        ["U4", "Lempung lunak: Cr", st_["Cr"][0], st_["Cr"][1], "", 0.075, "-", "[Uji sendiri] rata + 0,5 sd"],
        ["U4", "Lempung lunak: e0", st_["e0"][0], st_["e0"][1], "", round(st_["e0"][0], 2), "-", "[Uji sendiri]"],
        ["U4", "Lempung lunak: σ'p (z)", "lihat Konsolidasi", "", "", "σ'v0 + POP; POP 18 kPa di z = 3 m, linear ke 0 di z = 8,5 m",
         "kPa", "[Uji sendiri] bilinear; CPTu 0,33 qnet sedikit lebih tinggi (GT-09)"],
        ["U4", "Lempung lunak: cv / ch", "1,8 / 4,7-6,6", "", "", "1,8 / 4,5", "m²/th",
         "[Uji sendiri] cv lab NC; ch CPTu Ir = 75 [Asumsi]"],
        ["U4", "Lempung lunak: Cα", 0.028, "", "", 0.03, "-", "[Uji sendiri] Cα/Cc 0,036-0,041 (GEC 5: 0,04 ± 0,01)"],
        ["U4", "Lempung lunak: φ' (c' = 0)", st_["phi"][0], st_["phi"][1], "", 22, "°", "[Uji sendiri] CU n = 3"],
        ["U5", "Pasir: γ", 19.0, "", "", 19.0, "kN/m³", "[Asumsi] tidak ada contoh UD pasir"],
        ["U5", "Pasir: (N1)60", f'=AVERAGE(IF(({S["unit"]}="U5")*({S["cat"]}=""),{S["n160"]}))',
         f'=STDEV(IF(({S["unit"]}="U5")*({S["cat"]}=""),{S["n160"]}))', "", 12, "-", "[Uji sendiri] n = 38"],
        ["U5", "Pasir: φ'", f'=AVERAGE(IF(({S["unit"]}="U5")*({S["cat"]}=""),{S["phi"]}))',
         f'=STDEV(IF(({S["unit"]}="U5")*({S["cat"]}=""),{S["phi"]}))', "", 33, "°",
         "[Korelasi GEC 5 Pers. 7.23] pasir kelanauan (butir halus median 9 %); geser langsung dibentuk ulang 28-29°"],
        ["U5", "Pasir: k", "8,3 × 10⁻⁵", "", "", "8 × 10⁻⁵", "m/s", "[Uji sendiri] uji pompa (2.3)"],
        ["U6", "Lempung kaku: γ", stat_idx("g", "U6", "AVERAGE"), stat_idx("g", "U6", "STDEV"), "", 19.1, "kN/m³",
         "[Uji sendiri]"],
        ["U6", "Lempung kaku: su", stat_idx("su", "U6", "AVERAGE"), stat_idx("su", "U6", "STDEV"), "", 85, "kPa",
         "[Uji sendiri] UU tabung Pitcher n = 5"],
        ["U6", "Lempung kaku: Cc / Cr / σ'p", "0,34 / 0,044 / 408-447", "", "", "0,37 / 0,05 / 400", "- / kPa",
         "[Uji sendiri] OCR ±2,5"],
        ["U6", "Lempung kaku: c' / φ'", "17,8 / 21,7", "", "", "10 / 22", "kPa / °", "[Uji sendiri] CU n = 1"],
        ["U7", "Pasir padat: γ", 20.0, "", "", 20.0, "kN/m³", "[Asumsi]"],
        ["U7", "Pasir padat: (N1)60 / φ'", "≥ 29 / ≥ 41", "", "", "30 / 38", "- / °",
         "[Korelasi GEC 5 Pers. 7.23] sebagian besar uji penolakan; φ' dibatasi 38° [Asumsi]"],
        ["U8", "Lempung keras", "N60 50-65", "", "", "-", "-", "Hanya BH-5 di bawah 54,8 m; tidak diperlukan "
         "kecuali tiang sangat panjang"],
    ]
    r0 = lb.baris + 1
    isi = []
    for i, r_ in enumerate(baris):
        r = r0 + i
        rata_, sd_ = r_[2], r_[3]
        if isinstance(rata_, str) and rata_.startswith("=") and isinstance(sd_, str) and sd_.startswith("="):
            r_[4] = f"=F{r}-0.5*G{r}" if any(x in r_[1] for x in ("su", "φ'", "N1", "γ")) else ""
        elif isinstance(rata_, float) and isinstance(sd_, float):
            arah = "+" if any(x in r_[1] for x in ("Cc", "Cr")) else "-"
            r_[4] = f"=F{r}{arah}0.5*G{r}" if "e0" not in r_[1] else ""
        isi.append([i + 1, r_[0], r_[1], rata_, sd_, r_[4], r_[5], r_[6], r_[7]])
    lb.tabel(["No", "Unit", "Parameter", "Rata-rata", "Simpangan baku", "Rata - 0,5 sd", "Nilai desain [usulan]",
              "Satuan", "Sumber / keterangan"], isi, rata=list("cclccccc") + ["l"],
             fmt=[None, None, None, "0.000", "0.000", "0.000", None, None, None],
             fill_kolom={i: AI for i in range(3, 9)}, beku_kolom=3)
    for rr in range(r0, r0 + len(isi)):
        for kol in ("F", "G"):
            c = lb.ws[f"{kol}{rr}"]
            if isinstance(c.value, str) and c.value.startswith("=") and "IF(" in c.value:
                c.value = ArrayFormula(f"{kol}{rr}", c.value)

    # ---------------- Catatan
    lb = Lembar(wb.create_sheet("Catatan"), 9, "Catatan dan temuan langkah 2.4", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Catatan"], [[i, t] for i, t in enumerate(CATATAN, start=1)], rata=list("cl"),
             fill_kolom={1: AI})
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


def _sv0_mat07():
    """{(titik, contoh): σ'v0} contoh konsolidasi dengan MAT 0,7 m (profil γ dari tahap2_mutu_contoh)."""
    import tahap2_mutu_contoh as mc
    lap = mc.baca_lapisan()
    hasil = {}
    for c in mc.baca_konsolidasi():
        z = (c["dari"] + c["sampai"]) / 2
        hasil[(c["titik"], c["contoh"])] = mc.sigma_v0(lap[c["titik"]], z) - tp.GW * max(0, z - tp.MAT)
    return hasil

CATATAN = [
    "Lempung lunak U4 cukup seragam: γ 15,3 ± 0,3 kN/m³, w ±75 %, PI ±48 % (CH), e0 ±2,1, Cc ±0,72, CR ±0,23. "
    "Pemampatannya besar; penurunan akibat urugan +11,50 (±1,5-2,3 m) akan besar dan lama (Tahap 6).",
    "su U4 naik terhadap kedalaman (su UU = 6,3 + 1,09 z kPa). CPTu dengan Nkt = 12 (median kalibrasi 12,2) memberi profil yang sama "
    "(GT-09). Nkt per contoh 10,5-21,2; nilai > 19 berasal dari contoh dengan su UU rendah (BH-3, BH-4 UD-1, BH-7).",
    "Contoh BH-3 (bor lama) konsisten lebih lemah (su 6,9-12,2 kPa) dari bor baru pada kedalaman yang sama; "
    "kemungkinan gangguan contoh atau zona di bawah gambut. Tidak dibuang, tetapi menurunkan nilai karakteristik.",
    "σ'p bilinear cocok dengan σ'p lab (selisih ≤ 13 %) kecuali BH-1 UD-2 (+36 %) dan BH-5 UD-1 (lab 100, bilinear "
    "44 kPa). σ'p lab BH-5 UD-1 tidak dipakai. Lapisan atas U4 (2-5 m) sedikit terkonsolidasi lebih (OCR 1,3-1,7; POP ±11-18 kPa), "
    "lapisan bawah (7-9 m) hampir NC (OCR ±1,0).",
    "σ'p dari CPTu (0,33 qnet) 20-35 % lebih tinggi dari lab di 5-9 m; faktor setempat ±0,25-0,27. Nilai lab dipakai "
    "(lebih konservatif untuk penurunan).",
    "cv lab NC 1,7-2,2 m²/th; ch CPTu 4,7-6,6 m²/th (Ir 75). ch/cv ±2,5-3,5, wajar untuk aliran horizontal dan "
    "sisipan lanau. Untuk desain PVD (bila dipakai) ch dari CPTu; untuk konsolidasi vertikal cv lab.",
    "t50 penyedia keliru di dua uji: CPTu-5 9 m (45 menit; hitung ulang ±76 menit) dan CPTu-8 24 m (28,8 menit; "
    "uji baru 46 % disipasi sehingga t50 > 60 menit, tidak bisa ditentukan). Di CPTu-2 5 m u akhir di bawah u0 "
    "hidrostatik: muka air setempat ±1,1 m.",
    "Cα/Cc U4 0,036-0,041 dan gambut 0,060, sesuai rentang GEC 5 hal. 6-46 (cek silang lolos).",
    "Pasir U5: (N1)60 13,9 ± 3,0; φ' Hatanaka-Uchida 34,5 ± 1,6°. Korelasi itu untuk pasir bersih; U5 kelanauan "
    "(butir halus 2,5-29 %, median 9 %), sehingga nilai desain dibulatkan ke bawah menjadi 33°. Geser langsung "
    "contoh dibentuk ulang (laporan lama) 27,6-29,1° adalah batas bawah (kepadatan tidak terjaga).",
    "Gambut U3: e0 6,0, Cc 3,5, Cα 0,21, su ±9 kPa. Tidak boleh menjadi tumpuan apa pun; bila tidak dikupas, "
    "penurunan primer dan sekunder sangat besar (Tahap 3 dan 6).",
    "Contoh bor tebing (BT) tidak dimasukkan ke statistik gedung; BT-2 UD-2 su 4,4 kPa jauh lebih rendah dari "
    "contoh lain di kedalaman yang sama - dibahas di langkah 2.7 (tebing).",
]


if __name__ == "__main__":
    print(buat())
