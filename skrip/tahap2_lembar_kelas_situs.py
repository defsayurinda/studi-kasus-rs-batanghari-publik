"""Tahap 2 langkah 2.5: Excel '2.5 Kelas Situs.xlsx' dan gambar GT-11 (profil Vs dan kelas situs).

Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap2_lembar_kelas_situs.py
"""
from pathlib import Path

import numpy as np
import openpyxl
from gambar_teknik import BukuPDF as PdfPages

import tahap2_kelas_situs as ks
from format_dokumen import AI, Lembar, set_font_bawaan
from gambar_teknik import Kertas
from tahap2_gambar_air_tanah import gaya_sumbu
from tahap2_gambar_geoteknik import kotak_catatan

AKAR = Path(__file__).resolve().parents[1]
BERKAS = AKAR / "02 Olah Data Tanah" / "2.5 Kelas Situs.xlsx"
PDF = AKAR / "02 Olah Data Tanah" / "2.5 Gambar Kelas Situs.pdf"
PNG = AKAR / "02 Olah Data Tanah" / "Gambar" / "GT-11 Profil Vs dan Kelas Situs.png"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = ("DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026. "
            "Kunci jawaban tidak dibuka.")

PETUNJUK = [
    "Langkah 2.5 menetapkan kelas situs menurut SNI 1726:2019 Pasal 5.1-5.4 dan Tabel 5 (hal. 29-32), berdasarkan "
    "30 m teratas. Pasal 5.1: minimal dua dari tiga parameter (v̄s, N̄, s̄u) diukur mandiri; kelas yang lebih buruk "
    "berlaku.",
    "v̄s Pers. (1) hal. 31; N̄ Pers. (2) dan N̄ch Pers. (3) hal. 32 (Ni ≤ 300 pukulan/m); s̄u Pers. (4)-(6) hal. 32 "
    "(sui ≤ 250 kPa). Batas kelas: SE v̄s < 175 m/s, N̄ < 15, s̄u < 50 kPa; SD 175-350, 15-50, 50-100.",
    "Pasal 5.3.2: situs bukan SF yang mengandung lempung lunak > 3 m (su < 25 kPa, w ≥ 40 %, PI > 20) adalah SE.",
    "Pasal 5.3.1: SF bila (1) tanah rawan likuifaksi (pengecualian hanya untuk T ≤ 0,5 detik), (2) lempung organik "
    "tinggi/gambut H > 3 m, (3) PI ≥ 75 dan H > 7,5 m, (4) H > 35 m dengan su < 50 kPa.",
    "Data: 'Geofisika Vs.xlsx' (MASW 6 stasiun, downhole BH-5), SPT langkah 2.1, su desain langkah 2.4, tebal "
    "gambut langkah 2.2. Gambar: '2.5 Gambar Kelas Situs.pdf' (GT-11).",
]

CATATAN = [
    "Ketiga parameter memberi SE di semua titik: v̄s30 139-171 m/s (MASW) dan 162 m/s (downhole BH-5); N̄ 3,5-6,6 "
    "(N lapangan) atau 3,6-6,4 (N60); s̄u 21,7-24,5 kPa. Lempung lunak U4 ±8 m dengan su 7-16 kPa, w ±74 %, PI ±50 % "
    "juga memenuhi Pasal 5.3.2 (SE).",
    "v̄s30 terbesar (L-1/90, 170,6 m/s) hanya 2,5 % di bawah batas 175 m/s, tetapi N̄, s̄u, dan Pasal 5.3.2 tetap "
    "memberi SE, sehingga kelas SE tidak peka terhadap ketidakpastian v̄s.",
    "Downhole BH-5 (v̄s30 161,8 m/s) cocok dengan MASW L-1/57 di dekatnya (161,9 m/s) - VERIFIKASI T-22.",
    "Bacaan downhole 23 m (153,39 ms) lebih kecil dari 22 m (154,98 ms): mustahil (waktu tempuh harus bertambah); "
    "dibuang dan diinterpolasi. Bacaan P 34 m juga turun. Tidak mengubah v̄s30.",
    "MASW L-2/75 (utara) memberi Vs 45-46 m/s di 1-3,5 m: lapisan gambut. L-2/50 juga rendah (60-69 m/s).",
    "SF butir 2 (gambut H > 3 m): gambut saja HA-8 3,47 m, HA-10 3,05 m, HA-9 ≥ 2,99 m (lubang runtuh di gambut); "
    "termasuk lempung organik HA-8 3,72 m, HA-10 3,30 m. Zona ini di tepi utara (y ≳ 80 m, GT-05), yaitu lahan yang "
    "dicadangkan untuk gedung tahap 2 (TOR butir 9).",
    "SF butir 1 (likuifaksi pasir U5) diperiksa di langkah 2.6. Gedung 6 lantai diperkirakan T > 0,5 detik, jadi "
    "pengecualian Pasal 5.3.1 tidak berlaku: bila U5 mudah likuifaksi, situs SF dan wajib analisis respons spesifik-situs.",
    "SF butir 3 dan 4 tidak terpenuhi: PI terbesar 68 (< 75); tebal lempung lunak ±9,5 m (< 35 m).",
    "Kesimpulan (diperbarui setelah langkah 2.6): pasir U5 mudah likuifaksi di seluruh tapak, sehingga kelas situs SF "
    "dan spektrum desain wajib dari analisis respons spesifik-situs. Nilai SE (v̄s, N̄, s̄u) tetap dicatat sebagai "
    "pembanding.",
]


def buat(keluar=BERKAS):
    M = ks.masw()
    lok = ks.lokasi()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk langkah 2.5 kelas situs", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i, t] for i, t in enumerate(PETUNJUK, start=1)], rata=list("cl"))

    # ---- MASW
    lb = Lembar(wb.create_sheet("MASW"), 3, "MASW: v̄s30 tiap stasiun (Pers. (1) SNI 1726:2019)",
                [5, 10, 8, 9, 9, 10, 10, 11, 30])
    lb.catatan(LABEL + " Lapisan terbawah (setengah ruang) diperpanjang sampai 30 m. di/vsi dijumlahkan per stasiun. "
               + LABEL_AI)
    lb.kosong()
    r0 = lb.baris + 1
    baris, ringkas = [], {}
    i = 0
    for s_, lap in M.items():
        awal = r0 + i
        for a, b, v in lap:
            b = min(b, 30.0)
            r = r0 + i
            baris.append([i + 1, s_, len([x for x in baris if x[1] == s_]) + 1, a, b, v, f"=G{r}-F{r}",
                          f"=I{r}/H{r}", ""])
            i += 1
        ringkas[s_] = (awal, r0 + i - 1)
    lb.tabel(["No", "Stasiun", "Lapisan", "Dari (m)", "Sampai (m)", "Vs (m/s)", "di (m)", "di/vsi (s)", "Catatan"],
             baris, rata=list("cccccccc") + ["l"], fmt=[None, None, "0", "0.0", "0.0", "0", "0.0", "0.0000", None],
             fill_kolom={6: AI, 7: AI})
    ref_masw = {s_: f"=SUM(MASW!$I${a}:$I${b})/SUM(MASW!$J${a}:$J${b})" for s_, (a, b) in ringkas.items()}

    # ---- Downhole
    lb = Lembar(wb.create_sheet("Downhole"), 4, "Downhole BH-5: koreksi kemiringan dan v̄s30",
                [6, 10, 11, 11, 12, 12, 34])
    lb.catatan(LABEL + f" tc = t · z / √(z² + x²), x = {ks.OFFSET_DH:g} m (offset sumber); Vs interval = Δz / Δtc. "
               "v̄s30 = 30 / tc(30 m), setara Pers. (1). " + LABEL_AI)
    lb.kosong()
    r0 = lb.baris + 1
    baris = []
    for i, h in enumerate(ks.downhole()):
        r = r0 + i
        vs_int = f"=IF(G{r}>G{r - 1},(D{r}-D{r - 1})/((G{r}-G{r - 1})/1000),\"-\")" if i else f"=D{r}/(G{r}/1000)"
        cat = "Waktu tempuh turun: bacaan salah, dibuang" if h.get("vs_int") is None and i else (
            "Kecepatan interval semu karena bacaan 23 m" if h["z"] == 22.0 or h["z"] == 24.0 else "")
        baris.append([i + 1, h["z"], h["tp"], h["ts"], f"=F{r}*D{r}/SQRT(D{r}^2+{ks.OFFSET_DH}^2)", vs_int, cat])
    lb.tabel(["No", "z (m)", "t P (ms)", "t S (ms)", "tc S (ms)", "Vs interval (m/s)", "Catatan"], baris,
             rata=list("cccccc") + ["l"], fmt=[None, "0", "0.00", "0.00", "0.00", "0", None],
             fill_kolom={4: AI, 5: AI, 6: AI})
    r30 = r0 + [h["z"] for h in ks.downhole()].index(30.0)
    ref_dh = f"=30/(Downhole!$G${r30}/1000)"

    # ---- Ringkasan kelas
    lb = Lembar(wb.create_sheet("Kelas Situs", 1), 2, "Parameter kelas situs per titik dan kelas akhir",
                [5, 16, 10, 10, 10, 10, 10, 10, 30])
    lb.catatan(LABEL + " SE bila v̄s < 175 m/s, N̄ < 15, s̄u < 50 kPa (SNI 1726:2019 Tabel 5). " + LABEL_AI)
    lb.kosong()
    lb.bagian("A", "v̄s30 dari pengukuran geofisika")
    r0 = lb.baris + 1
    baris = []
    for i, (s_, f) in enumerate(list(ref_masw.items()) + [("BH-5 downhole", ref_dh)]):
        r = r0 + i
        L = lok[s_]
        baris.append([i + 1, s_, L["x"], L["y"], f, f'=IF(G{r}>350,"SC",IF(G{r}>=175,"SD","SE"))', "", "",
                      "MASW" if s_.startswith("L") else "Downhole, koreksi kemiringan"])
    lb.tabel(["No", "Stasiun", "x (m)", "y (m)", "v̄s30 (m/s)", "Kelas", "", "", "Keterangan"], baris,
             rata=list("clccccccl"), fmt=[None, None, "0", "0", "0.0", None, None, None, None],
             fill_kolom={4: AI, 5: AI}, beku=False)
    lb.kosong()
    lb.bagian("B", "N̄, N̄ch, dan s̄u per bor (30 m teratas)")
    r0 = lb.baris + 1
    baris = []
    for i, b in enumerate(ks.ER):
        r = r0 + i
        baris.append([i + 1, b, round(ks.n_rata(b), 1), round(ks.n_rata(b, True), 1),
                      round(ks.n_rata(b, nonkohesif_saja=True), 1), round(ks.su_rata(b), 1),
                      f'=IF(MAX(E{r}:F{r})>50,"SC",IF(MAX(E{r}:F{r})>=15,"SD","SE"))',
                      f'=IF(H{r}>=100,"SC",IF(H{r}>=50,"SD","SE"))', "WOH dianggap N = 1 [Asumsi]"])
    lb.tabel(["No", "Bor", "N̄ (N lapangan)", "N̄ (N60)", "N̄ch pasir", "s̄u (kPa)", "Kelas N̄", "Kelas s̄u",
              "Keterangan"], baris, rata=list("clccccccl"),
             fmt=[None, None, "0.0", "0.0", "0.0", "0.0", None, None, None], fill_kolom={i: AI for i in range(2, 9)},
             beku=False)
    lb.kosong()
    lb.bagian("C", "Pemeriksaan kelas situs SF (Pasal 5.3.1) dan SE (Pasal 5.3.2)")
    cek = [
        [1, "SF-1 rawan likuifaksi", "Pasir U5: FS 0,22-0,75 (langkah 2.6)", "Seluruh tapak", "Ya",
         "Ta gedung 0,53-0,82 detik > 0,5: pengecualian tidak berlaku"],
        [2, "SF-2 gambut/lempung organik H > 3 m", "Gambut HA-8 3,47; HA-10 3,05; HA-9 ≥ 2,99 m", "Tepi utara",
         "Ya, di zona utara", "Tergantung denah Tahap 3 (lahan tahap 2)"],
        [3, "SF-3 PI ≥ 75 dan H > 7,5 m", "PI terbesar 68 (U4)", "-", "Tidak", ""],
        [4, "SF-4 H > 35 m dan su < 50 kPa", "Lempung lunak ±9,5 m", "-", "Tidak", ""],
        [5, "SE Pasal 5.3.2", "U4 ±8 m: su 7-16 kPa, w ±74 %, PI ±50 %", "Seluruh tapak", "Ya", "Minimal SE"],
    ]
    lb.tabel(["No", "Kriteria", "Data", "", "Lokasi", "", "Terpenuhi?", "", "Catatan"],
             [[c[0], c[1], c[2], "", c[3], "", c[4], "", c[5]] for c in cek], rata=list("cllclccc") + ["l"],
             fill_kolom={i: AI for i in range(2, 9)}, beku=False)
    for rr in range(lb.baris - len(cek) - 1, lb.baris):
        lb.ws.merge_cells(start_row=rr, start_column=5, end_row=rr, end_column=6)
        lb.ws.merge_cells(start_row=rr, start_column=7, end_row=rr, end_column=8)
        lb.ws.merge_cells(start_row=rr, start_column=9, end_row=rr, end_column=10)
    lb.ws._print_rows = None
    lb.kosong()
    lb.catatan("KESIMPULAN [usulan, diperbarui setelah langkah 2.6]: parameter v̄s, N̄, s̄u memberi SE, tetapi pasir U5 "
               "mudah likuifaksi di seluruh tapak sehingga kelas situs SF (Pasal 5.3.1 butir 1). Spektrum desain dari "
               "analisis respons spesifik-situs (Pasal 6.10); SE dipakai hanya sebagai pembanding/batas bawah.", fill=AI)

    lb = Lembar(wb.create_sheet("Catatan"), 5, "Catatan dan temuan langkah 2.5", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Catatan"], [[i, t] for i, t in enumerate(CATATAN, start=1)], rata=list("cl"),
             fill_kolom={1: AI})
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


def gambar():
    k = Kertas()
    M = ks.masw()
    ax = k.sumbu(35, 70, 120, 190)
    warna = ["#1f5f99", "#2e7d32", "#c0392b", "#e67e22", "#8e44ad", "#5b3a1c"]
    for (s_, lap), w in zip(M.items(), warna):
        z, v = [], []
        for a, b, vs in lap:
            z += [a, min(b, 30)]
            v += [vs, vs]
        ax.plot(v, z, color=w, lw=1.0, label=f"MASW {s_}: v̄s30 = {ks.vs30(lap):.0f} m/s".replace(".", ","))
    dh = [h for h in ks.downhole() if h["z"] <= 34 and h["z"] != 23.0]  # bacaan 23 m dibuang
    zz, vv = [], []
    for h0, h1 in zip([dict(z=0.0, tsc=0.0)] + dh, dh):
        if h1["z"] == 23.0 or h1["tsc"] <= h0["tsc"]:
            continue
        v = (h1["z"] - h0["z"]) / ((h1["tsc"] - h0["tsc"]) / 1000)
        zz += [h0["z"], h1["z"]]
        vv += [v, v]
    ax.plot(vv, zz, color="k", lw=0.8, ls="--", label=f"Downhole BH-5: v̄s30 = {ks.downhole_vs30():.0f} m/s")
    ax.axvline(175, color="#b00020", lw=0.8, ls=":")
    ax.text(178, 29.3, "175 m/s\n(batas SE/SD)", fontsize=5.5, color="#b00020")
    ax.set_ylim(30, 0)
    ax.set_xlim(0, 400)
    ax.set_xlabel("Vs (m/s)", fontsize=6.5)
    ax.set_ylabel("Kedalaman (m)", fontsize=6.5)
    ax.legend(fontsize=5.2, loc="lower right")
    gaya_sumbu(ax, "A. Profil kecepatan gelombang geser")
    ax2 = k.sumbu(175, 175, 125, 85)
    nama = list(M) + ["BH-5 DH"]
    nilai = [ks.vs30(l) for l in M.values()] + [ks.downhole_vs30()]
    ax2.bar(range(len(nama)), nilai, color=warna + ["#555"], width=0.6)
    for i, v in enumerate(nilai):
        ax2.text(i, v + 3, f"{v:.0f}", ha="center", fontsize=5.5)
    ax2.axhline(175, color="#b00020", lw=0.8, ls=":")
    ax2.axhspan(0, 175, color="#f6d5d5", alpha=0.4)
    ax2.text(5.5, 120, "SE", fontsize=12, fontweight="bold", color="#b00020", ha="center")
    ax2.set_xticks(range(len(nama)))
    ax2.set_xticklabels(nama, fontsize=5.5, rotation=20)
    ax2.set_ylim(0, 380)
    ax2.set_ylabel("v̄s30 (m/s)", fontsize=6.5)
    gaya_sumbu(ax2, "B. v̄s30 tiap stasiun")
    ax3 = k.sumbu(175, 70, 125, 80)
    bor = list(ks.ER)
    n = [ks.n_rata(b) for b in bor]
    su = [ks.su_rata(b) for b in bor]
    x = np.arange(len(bor))
    ax3.bar(x - 0.2, n, 0.4, color="#c9a227", label="N̄ (N lapangan); batas SE 15")
    ax3.bar(x + 0.2, su, 0.4, color="#7f9cb5", label="s̄u (kPa); batas SE 50")
    ax3.axhline(15, color="#c9a227", lw=0.8, ls=":")
    ax3.axhline(50, color="#7f9cb5", lw=0.8, ls=":")
    ax3.set_xticks(x)
    ax3.set_xticklabels(bor, fontsize=5.5)
    ax3.set_ylim(0, 60)
    ax3.legend(fontsize=5.2, loc="upper left")
    gaya_sumbu(ax3, "C. N̄ dan s̄u 30 m teratas tiap bor")
    k.teks(35, 275, "PROFIL KECEPATAN GELOMBANG GESER DAN KELAS SITUS", fontsize=11, fontweight="bold")
    k.teks(35, 270, "SNI 1726:2019 Pasal 5 dan Tabel 5; 30 m teratas dari muka tanah setempat", fontsize=6.5)
    kotak_catatan(k, 287, "CATATAN", [
        "Semua parameter memberi SE: v̄s30 139-171 m/s, N̄ 3,5-6,6, s̄u 22-25 kPa; juga Pasal 5.3.2 (lempung lunak "
        "> 3 m dengan su < 25 kPa).",
        "Downhole dikoreksi kemiringan lintasan (offset sumber 3 m); bacaan 23 m dibuang (waktu tempuh turun).",
        "Vs rendah 45-70 m/s di 1-3,5 m pada L-2/50 dan L-2/75 menunjukkan gambut di bagian utara.",
        "SF: gambut > 3 m di tepi utara (HA-8, HA-9, HA-10); likuifaksi pasir U5 diperiksa di langkah 2.6.",
        "Langkah 2.6: pasir U5 mudah likuifaksi (FS 0,22-0,75), jadi kelas situs SF; wajib respons spesifik-situs.",
    ], 80)
    k.etiket("Profil Vs dan kelas situs", "GT-11", "Tanpa skala", "1 / 1")
    with PdfPages(PDF) as pdf:
        k.simpan(pdf, PNG)
    return PDF


if __name__ == "__main__":
    print(buat())
    print(gambar())
