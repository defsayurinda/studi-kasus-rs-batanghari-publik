"""Tahap 2 langkah 2.7: Excel '2.7 Kimia Tebing Gudang.xlsx' dan gambar GT-13 (tebing), GT-14 (gudang).

Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap2_lembar_kimia_tebing_gudang.py
"""
from datetime import datetime

import numpy as np
import openpyxl
from gambar_teknik import BukuPDF as PdfPages
from matplotlib.patches import Rectangle

import tahap2_stratigrafi as st
from format_dokumen import AI, Lembar, set_font_bawaan
from gambar_teknik import Kertas
from tahap2_gambar_air_tanah import gaya_sumbu
from tahap2_gambar_geoteknik import kotak_catatan
from tahap2_kimia_tebing_gudang import (BERKAS, KELUAR, LABEL, LABEL_AI, PDF, bor_tebing, kategori_ciria,
                                        kemiringan_lantai, kimia, lantai, patok, penampang, ringkas_tebing)

PETUNJUK = [
    "Langkah 2.7 menafsirkan paket penyelidikan 9-11: kimia tanah dan air (agresivitas terhadap beton dan baja), "
    "survei tebing (penampang, batimetri, bor tebing), dan survei kondisi gudang timur sebelum konstruksi.",
    "Sulfat: SNI 2847:2019 Tabel 19.3.1.1 hal. 437 (kelas S0-S3) dan Tabel 19.3.2.1 hal. 442 (persyaratan beton). "
    "SNI 2847 tidak mencakup paparan asam (Penjelasan R19.3.1 hal. 436).",
    "Agresivitas terhadap baja/beton tertanam: pH < 4,5 atau resistivitas < 2.000 Ω·cm (FHWA GEC 10 hal. 5-23); laju "
    "korosi baja konservatif 0,003 in/th = 0,076 mm/th (idem, mengutip Hannigan dkk. 2016).",
    "Gambut: kadar organik > 30 % = tanah sangat organik/gambut (FHWA GEC 5 Tabel 4-9 hal. 4-19).",
    "Bangunan sekitar: kategori risiko kerusakan dari kemiringan dan penurunan, SNI 8460:2017 Tabel 33 hal. 159.",
    "Gambar: '2.7 Gambar Tebing dan Gudang.pdf' (GT-13 penampang tebing, GT-14 gudang timur).",
]

CATATAN = [
    "Kimia: gambut T-1 S1 dan T-2 S2 (sulfat T-2 dilaporkan dalam % SO₃, berbeda satuan dari contoh lain; setelah "
    "dikonversi 0,24 % SO₄). Air pori gambut A-2 S1, air akuifer A-1 S0. Urugan berpuing T-4 S2.",
    "Gambut dan air porinya asam (pH 3,7-4,0) dengan CO₂ agresif 45 mg/L dan amonium 6 mg/L; resistivitas 900-1.300 "
    "Ω·cm dan redoks negatif (anaerob). Agresif menurut GEC 10. Paparan asam berada di luar SNI 2847.",
    "Usulan [untuk RKS Tahap 7]: beton yang menyentuh U3/U4 dan tiang melewati gambut minimal kelas S2 (w/cm ≤ 0,45, "
    "f'c ≥ 31 MPa, semen Tipe V atau IP(HS)/IS(HS)); dinding basement W1 dan C1; perlindungan tambahan terhadap asam "
    "(lapis pelindung, selimut tambahan) memakai acuan lain [belum ada di acuan/]. Tiang baja: tambahan tebal korosi "
    "±0,076 mm/th per muka.",
    "Tebing: tinggi dari puncak ke dasar sungai terdalam 15-16 m; lereng atas 30° (P-1), 48° (P-2), 32° (P-3); dasar "
    "sungai terdalam -4,9 s.d. -5,9 berarti sungai memotong pasir U5 (atas U5 di tebing +0,5 s.d. +1,4): muka bebas "
    "untuk penyebaran lateral pasir yang mudah likuifaksi (langkah 2.6).",
    "P-2 adalah longsoran lama: BT-2 menemukan bidang licin mengkilap di 4,6-5,1 m (elevasi +5,2 s.d. +5,7), BT-2K "
    "menemukan massa longsoran 2,35 m di kaki tebing, dan contoh BT-2 UD-2 dari bidang itu su 4,4 kPa (setengah "
    "contoh lain). Puncak tebing P-2 hanya 6,5 m dari batas lahan; GSB 5 m usulan owner berarti gedung 1,5 m dari "
    "puncak longsoran.",
    "Batimetri P-3 diukur 3 Des 2026 (muka air +7,64) tetapi dikonversi dengan muka air 14 Des (+8,05): elevasi dasar "
    "sungai P-3 di laporan 0,41 m terlalu tinggi. Sudah dikoreksi di lembar Tebing dan GT-13.",
    "Garis sempadan sungai (Permen PUPR 28/2015) belum ada di acuan/; jarak bangunan dari tebing ditetapkan di Tahap 3 "
    "berdasarkan stabilitas lereng, penyebaran lateral, dan aturan sempadan.",
    "Gudang timur (1984, pondasi batu kali di atas cerucuk gelam ±4 m): sudah turun 0,8-1,9 mm/bulan selama Des 2026 - "
    "Mar 2027 sebelum ada pekerjaan; sisi utara (GT-4, GT-5, GT-6) paling cepat. Bacaan GT-7 3 Mar dikoreksi karena "
    "patok bengkok diluruskan (loncatan -11,5 mm bukan penurunan).",
    "Lantai gudang: sudut timur laut (D6-E6) miring 1/54 dan celah lantai R-12 11,1 mm - kategori risiko 3 (SNI 8460 "
    "Tabel 33) SEBELUM proyek. Lantai utara ditinggikan 10 cm pada 2009; luas peninggian tidak tercatat, sehingga "
    "kemiringan ditampilkan dua cara (apa adanya dan baris 5-6 dikurangi 10 cm). Tanyakan ke pemilik.",
    "Kepala cerucuk +8,62 dan 10-15 cm teratas lapuk; air merembes di +8,94. Saat kemarau muka air dangkal turun di "
    "bawah kepala cerucuk. Dewatering basement akan menurunkan muka air di dekat gudang dan mempercepat pelapukan serta "
    "penurunan - harus dikendalikan (Tahap 6). Data ini catatan kondisi awal untuk menghadapi klaim (TOR butir 10).",
    "Pengukur retak R-2, R-4, R-5, R-12: perubahan ≤ 0,3 mm dan kembali, tanpa tren; retak tidak aktif selama pemantauan.",
]


def buat_excel(keluar=BERKAS):
    tanah, air = kimia()
    tb = ringkas_tebing()
    tg, pk = patok()
    km = kemiringan_lantai(lantai())
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk langkah 2.7 kimia, tebing, gudang", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i, t] for i, t in enumerate(PETUNJUK, start=1)], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Kimia"), 2, "Agresivitas tanah dan air terhadap beton dan baja",
                [5, 7, 24, 7, 10, 9, 11, 10, 10, 40])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.bagian("A", "Contoh tanah")
    r0 = lb.baris + 1
    baris = []
    for i, x in enumerate(tanah):
        r = r0 + i
        baris.append([i + 1, x["Kode"], f"{x['Jenis']} ({x['Asal']})", x["pH"], round(x["so4"], 3),
                      f'=IF(G{r}<0.1,"S0",IF(G{r}<0.2,"S1",IF(G{r}<=2,"S2","S3")))', x["Resistivitas (Ω·cm)"],
                      x["Kadar organik (%)"], f'=IF(OR(F{r}<4.5,I{r}<2000),"Agresif","Tidak")', x["catatan"]])
    lb.tabel(["No", "Kode", "Jenis (asal)", "pH", "SO₄ (% massa)", "Kelas S", "Resistivitas (Ω·cm)",
              "Organik (%)", "GEC 10", "Catatan"], baris, rata=list("cclcccccc") + ["l"],
             fmt=[None, None, None, "0.0", "0.000", None, "0", "0.0", None, None],
             fill_kolom={4: AI, 5: AI, 8: AI, 9: AI}, beku=False)
    lb.kosong()
    lb.bagian("B", "Contoh air")
    r0 = lb.baris + 1
    baris = []
    for i, x in enumerate(air):
        r = r0 + i
        baris.append([i + 1, x["Kode"], f"{x['Jenis']} ({x['Asal']})", x["pH"], x["Sulfat SO₄ (mg/L)"],
                      f'=IF(G{r}<150,"S0",IF(G{r}<1500,"S1",IF(G{r}<=10000,"S2","S3")))', x["Klorida (mg/L)"],
                      x["CO₂ agresif (mg/L)"], x["Amonium (mg/L)"], "Asam, CO₂ agresif" if x["pH"] < 4.5 else ""])
    lb.tabel(["No", "Kode", "Jenis (asal)", "pH", "SO₄ (mg/L)", "Kelas S", "Klorida (mg/L)", "CO₂ agresif (mg/L)",
              "Amonium (mg/L)", "Catatan"], baris, rata=list("cclcccccc") + ["l"],
             fmt=[None, None, None, "0.0", "0", None, "0", "0", "0.0", None], fill_kolom={5: AI, 9: AI}, beku=False)
    lb.ws._print_rows = None

    lb = Lembar(wb.create_sheet("Tebing"), 3, "Geometri tebing per potongan", [5, 8, 7, 11, 10, 10, 9, 9, 9, 10, 30])
    lb.catatan(LABEL + " Sudut atas = puncak ke tepi air (+7,64); sudut total = puncak ke dasar terdalam. P-3: "
               "batimetri dikoreksi -0,41 m. " + LABEL_AI)
    lb.kosong()
    baris = [[i + 1, t["potongan"], t["x"], t["jarak_puncak"], t["elev_puncak"], round(t["thal_elev"], 2),
              round(t["tinggi"], 2), round(t["sudut_atas"], 1), round(t["sudut_total"], 1), t["koreksi"],
              "Longsoran lama (BT-2, BT-2K)" if t["potongan"] == "P-2" else ""] for i, t in enumerate(tb)]
    lb.tabel(["No", "Potongan", "x (m)", "Puncak dari batas lahan (m)", "Elevasi puncak (m)", "Dasar terdalam (m)",
              "Tinggi (m)", "Sudut atas (°)", "Sudut total (°)", "Koreksi batimetri (m)", "Catatan"], baris,
             rata=list("cccccccccc") + ["l"],
             fmt=[None, None, "0", "0.0", "0.00", "0.00", "0.00", "0.0", "0.0", "0.00", None],
             fill_kolom={i: AI for i in range(5, 11)})

    lb = Lembar(wb.create_sheet("Gudang"), 4, "Gudang timur: patok penurunan dan kemiringan lantai",
                [5, 9, 6, 6, 10, 10, 10, 10, 10, 10, 40])
    lb.catatan(LABEL + " Penurunan relatif terhadap bacaan 3 Des 2026 (mm, negatif = turun). " + LABEL_AI)
    lb.kosong()
    lb.bagian("A", "Patok penurunan")
    baris = [[i + 1, p["patok"], p["x"], p["y"]] + [round(v, 1) for v in p["d_kor"]] + [round(p["laju"], 2),
                                                                                        p["catatan"]]
             for i, p in enumerate(pk)]
    lb.tabel(["No", "Patok", "x (m)", "y (m)", "3 Des (mm)", "6 Jan (mm)", "3 Feb (mm)", "3 Mar (mm)", "31 Mar (mm)",
              "Laju (mm/bln)", "Catatan"], baris, rata=list("cccccccccc") + ["l"],
             fmt=[None, None, "0", "0"] + ["0.0"] * 6 + [None], fill_kolom={9: AI, 10: AI}, beku=False)
    lb.kosong()
    lb.bagian("B", "Kemiringan lantai antar kolom bersebelahan (delapan terbesar)")
    baris = []
    for i, h in enumerate(km[:8]):
        baris.append([i + 1, f"{h['a']}-{h['b']}", h["L"], "", f"1/{1 / max(h['beta_asli'], 1e-9):.0f}",
                      f"1/{1 / h['beta']:.0f}", kategori_ciria(h["beta_asli"]), kategori_ciria(h["beta"]), "", "",
                      "Kategori SNI 8460 Tabel 33; terkoreksi = baris 5-6 dikurangi 10 cm [Asumsi]"])
    lb.tabel(["No", "Kolom", "L (m)", "", "Kemiringan apa adanya", "Kemiringan terkoreksi", "Kategori (apa adanya)",
              "Kategori (terkoreksi)", "", "", "Catatan"], baris, rata=list("cccccccccc") + ["l"],
             fill_kolom={4: AI, 5: AI, 6: AI, 7: AI}, beku=False)
    lb.ws._print_rows = None

    lb = Lembar(wb.create_sheet("Catatan"), 5, "Catatan dan temuan langkah 2.7", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Catatan"], [[i, t] for i, t in enumerate(CATATAN, start=1)], rata=list("cl"),
             fill_kolom={1: AI})
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


WARNA_U = {u: v[2] for u, v in st.UNIT.items()}
WARNA_U.update({"Longsoran": "#b03a2e", "Bidang licin": "#ff0000"})


def gambar_tebing(pdf):
    k = Kertas()
    bor = bor_tebing()
    pos = {"P-1": ("BT-1", "BT-1K"), "P-2": ("BT-2", "BT-2K"), "P-3": ("BT-3", None)}
    ring = {t["potongan"]: t for t in ringkas_tebing()}
    tinggi = 74
    for i, n in enumerate(("P-1", "P-2", "P-3")):
        y0 = 192 - i * (tinggi + 13)
        ax = k.sumbu(35, y0, 265, tinggi)
        ax._cad = {"skala": 400, "jenis": "penampang", "grid_elevasi": False}
        p = penampang(n)
        j = [t["jarak"] for t in p]
        e = [t["elev_kor"] for t in p]
        ax.fill_between(j, e, -12, color="#ecd98a", alpha=0.35)
        ax.fill_between(j, e, 7.64, where=np.array(e) < 7.64, color="#d6e9f5")
        ax.plot(j, e, color="k", lw=1.0)
        if n == "P-3":
            ax.plot(j, [t["elev"] for t in p], color="#888", lw=0.6, ls="--", label="batimetri laporan (belum dikoreksi)")
        for lv, lab, ls in ((11.20, "banjir +11,20", "--"), (7.64, "muka air 3 Des 2026 +7,64", ":"),
                            (4.0, "surut +4,0", "-.")):
            ax.axhline(lv, color="#1f5f99", lw=0.6, ls=ls)
            ax.text(j[-1] - 1, lv + 0.25, lab, fontsize=4.8, color="#1f5f99", ha="right")
        ax.axvline(0, color="k", lw=0.6, ls=(0, (6, 2, 2, 2)))
        ax.text(0.3, 11.8, "batas lahan", fontsize=4.8)
        ax.axvline(-5, color="#b00020", lw=0.7, ls=":")
        ax.text(-4.7, -10.8, "GSB 5 m (usulan owner)", fontsize=4.8, color="#b00020")
        for nb in pos[n]:
            if not nb:
                continue
            b = bor[nb]
            xb = -b["y lokal (m)"]
            for lp in b["lapisan"]:
                ax.add_patch(Rectangle((xb - 0.9, lp["eb"]), 1.8, lp["ea"] - lp["eb"],
                                       fc=WARNA_U.get(lp["unit"], "#ccc"), ec="k", lw=0.4, zorder=5))
            ax.text(xb, b["lapisan"][0]["ea"] + 0.6, nb, fontsize=5.5, ha="center", fontweight="bold", zorder=6)
            for z, nv in b["spt"]:
                ez = b["lapisan"][0]["ea"] - z - 0.2
                if ez > -11.5:
                    ax.text(xb + 1.1, ez, str(nv), fontsize=3.8, zorder=6)
        ax.set_xlim(-12, 90)
        ax.set_ylim(-12, 13)
        ax.set_ylabel("Elevasi (m)", fontsize=6)
        if i == 2:
            ax.set_xlabel("Jarak dari batas lahan selatan, positif ke arah sungai (m)", fontsize=6)
        r = ring[n]
        judul = (f"POTONGAN {n} (x = {r['x']} m): puncak {r['jarak_puncak']:g} m dari batas lahan, lereng atas "
                 f"{r['sudut_atas']:.0f}°, dasar terdalam {r['thal_elev']:.1f} m").replace(".", ",")
        gaya_sumbu(ax, judul)
        if n == "P-2":
            ax.annotate("bidang licin (BT-2, 4,6-5,1 m)", (4.5, 5.4), (16, 9.5), fontsize=5, color="#b00020",
                        arrowprops=dict(arrowstyle="->", lw=0.5))
            ax.annotate("massa longsoran (BT-2K)", (15, 5), (25, 1), fontsize=5, color="#b03a2e",
                        arrowprops=dict(arrowstyle="->", lw=0.5))
        if n == "P-3":
            ax.legend(fontsize=5, loc="lower left")
    k.teks(35, 283, "PENAMPANG TEBING SUNGAI P-1, P-2, P-3", fontsize=11, fontweight="bold")
    k.teks(35, 278.5, "Topografi total station dan batimetri echosounder; kolom bor tebing dengan N-SPT; skala "
           "horizontal = vertikal 1:400", fontsize=6.5)
    kotak_catatan(k, 287, "CATATAN", [
        "Sungai memotong pasir U5 (dasar terdalam -4,9 s.d. -5,9; atas U5 di tebing +0,5 s.d. +1,4): muka bebas "
        "untuk penyebaran lateral pasir yang mudah likuifaksi (2.6).",
        "P-2 longsoran lama: bidang licin BT-2 4,6-5,1 m dan massa longsoran 2,35 m di kaki (BT-2K). Puncak P-2 hanya "
        "6,5 m dari batas lahan.",
        "Batimetri P-3 dikoreksi -0,41 m (diukur 3 Des pada muka air +7,64, laporan memakai +8,05).",
        "Kolom bor: warna unit sesuai legenda GT-02; merah = bidang licin dan massa longsoran. Angka = N-SPT lapangan.",
        "Stabilitas lereng dan sempadan ditetapkan di Tahap 3 dan 6.",
    ], 75)
    k.etiket("Penampang tebing sungai P-1, P-2, P-3", "GT-13", "1:400", "1 / 2")
    k.simpan(pdf, KELUAR / "Gambar" / "GT-13 Penampang Tebing.png")


def gambar_gudang(pdf):
    k = Kertas()
    tg, pk = patok()
    lt = lantai()
    ax = k.sumbu(35, 120, 130, 140)
    ax._cad = {"skala": 300, "jenis": "peta"}
    ax.add_patch(Rectangle((144, 18), 24, 40, fill=False, lw=1.2))
    for t in lt:
        ax.plot(t["x"], t["y"], "s", ms=3, color="#555")
        ax.text(t["x"] + 0.4, t["y"] + 0.8, f"{t['elev']:.3f}".replace(".", ","), fontsize=4.6)
    for p in pk:
        ax.plot(p["x"], p["y"], "o", ms=6, mfc="#c0392b" if p["laju"] < -1.5 else "#e67e22", mec="k", mew=0.5)
        ax.text(p["x"] - 0.5, p["y"] - 2.6, f"{p['patok']}\n{p['laju']:.1f} mm/bl".replace(".", ","), fontsize=4.6,
                ha="right")
    retak = {"R-2": (144, 34), "R-4": (144, 58), "R-5": (156, 58), "R-12": (162, 58), "R-9": (153, 46)}
    for n, (x, y) in retak.items():
        ax.plot(x, y, "x", color="#7b3fa0", ms=6, mew=1)
        ax.text(x + 0.6, y - 1.6, n, fontsize=5, color="#7b3fa0")
    ax.axvline(140, color="k", lw=0.8, ls=(0, (6, 2, 2, 2)))
    ax.text(139.5, 60, "batas lahan RS", rotation=90, fontsize=5, ha="right")
    ax.set_xlim(134, 172)
    ax.set_ylim(12, 64)
    ax.set_aspect("equal")
    ax.set_xlabel("x lokal (m)", fontsize=6)
    ax.set_ylabel("y lokal (m)", fontsize=6)
    gaya_sumbu(ax, "A. Denah: elevasi lantai, patok, retak")
    ax2 = k.sumbu(185, 160, 110, 100)
    for p in pk:
        ax2.plot(tg, p["d_kor"], marker="o", ms=2.5, lw=0.8, label=p["patok"])
    ax2.axvspan(datetime(2027, 1, 8), datetime(2027, 1, 26), color="#d6e9f5")
    ax2.text(datetime(2027, 1, 9), -7.6, "tergenang", fontsize=5)
    ax2.set_ylabel("Penurunan sejak 3 Des 2026 (mm)", fontsize=6)
    ax2.legend(fontsize=4.6, ncol=2, loc="lower left")
    ax2.tick_params(axis="x", labelsize=5, rotation=20)
    gaya_sumbu(ax2, "B. Penurunan patok (GT-7 dikoreksi)")
    ax3 = k.sumbu(185, 70, 110, 70)
    km = kemiringan_lantai(lt)[:8]
    ax3.barh(range(len(km)), [1 / max(h["beta_asli"], 1e-9) for h in km], color="#c0392b", height=0.4,
             label="apa adanya")
    ax3.barh([i + 0.4 for i in range(len(km))], [1 / h["beta"] for h in km], color="#7f9cb5", height=0.4,
             label="baris 5-6 dikurangi 10 cm")
    ax3.set_yticks([i + 0.2 for i in range(len(km))])
    ax3.set_yticklabels([f"{h['a']}-{h['b']}" for h in km], fontsize=5)
    for b_, lab in ((50, "1/50"), (200, "1/200"), (500, "1/500")):
        ax3.axvline(b_, color="k", lw=0.5, ls=":")
        ax3.text(b_, len(km) - 0.3, lab, fontsize=5)
    ax3.set_xscale("log")
    ax3.set_xlabel("Penyebut kemiringan 1/β (batas kategori SNI 8460 Tabel 33)", fontsize=6)
    ax3.legend(fontsize=5, loc="lower right")
    gaya_sumbu(ax3, "C. Kemiringan lantai terbesar")
    k.teks(35, 275, "KONDISI AWAL GUDANG TIMUR (SEBELUM KONSTRUKSI)", fontsize=11, fontweight="bold")
    k.teks(35, 270, "Survei 3 Des 2026; patok dibaca sampai 31 Mar 2027; elevasi terhadap BM-1", fontsize=6.5)
    kotak_catatan(k, 287, "CATATAN", [
        "Gudang sudah turun 0,8-1,9 mm/bulan tanpa pekerjaan di lahan RS; sisi utara paling cepat.",
        "Sudut timur laut miring 1/54 (kategori risiko 3, SNI 8460 Tabel 33) dan celah lantai R-12 11,1 mm sebelum "
        "proyek. Luas peninggian lantai utara 10 cm (2009) belum jelas.",
        "GT-7: loncatan -11,5 mm pada 3 Mar karena patok bengkok diluruskan 20 Feb, bukan penurunan.",
        "Retak R-2, R-4, R-5, R-12 tidak aktif (perubahan ≤ 0,3 mm tanpa tren).",
        "Cerucuk gelam: kepala +8,62, 10-15 cm teratas lapuk. Dewatering basement harus dikendalikan (Tahap 6).",
        "Dokumen ini catatan kondisi awal untuk menanggapi klaim tetangga (TOR butir 10).",
    ], 85)
    k.etiket("Kondisi awal gudang timur", "GT-14", "1:300 (denah)", "2 / 2")
    k.simpan(pdf, KELUAR / "Gambar" / "GT-14 Kondisi Awal Gudang Timur.png")


def buat():
    buat_excel()
    with PdfPages(PDF) as pdf:
        gambar_tebing(pdf)
        gambar_gudang(pdf)
        pdf.infodict()["Title"] = "2.7 Gambar Tebing dan Gudang - RS Tepian Batanghari (data simulasi)"
    return BERKAS, PDF


if __name__ == "__main__":
    print(buat())
