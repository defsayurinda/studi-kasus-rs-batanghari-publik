"""Tahap 1: denah titik penyelidikan dan lembar kerja telaah, format sesuai FORMAT LAPORAN DAN EXCEL.md.

Tanpa argumen: lembar kosong (sel kuning muda untuk diisi Defsa).
Dipanggil dari tahap1_isi_telaah_ai.py: lembar berisi draf AI (sel hijau).
Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap1_lembar_telaah.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import openpyxl
from openpyxl.worksheet.datavalidation import DataValidation

from format_dokumen import AI, ISIAN, Lembar, set_font_bawaan

AKAR = Path(__file__).resolve().parents[1]
FOLDER = AKAR / "01 Penyelidikan Tanah"
BERKAS = FOLDER / "Telaah Penyelidikan Tanah.xlsx"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata."
N_TEMUAN, N_USULAN = 30, 15


def baca_titik():
    """Koordinat dan kedalaman dari lembar 'Titik' kedua berkas lapangan."""
    titik = []
    for berkas, jenis in [("Sondir.xlsx", "Sondir"), ("Bor dan SPT.xlsx", "Bor")]:
        ws = openpyxl.load_workbook(FOLDER / berkas, data_only=True)["Titik"]
        for r in ws.iter_rows(values_only=True):
            if r[0] and str(r[0]).startswith(("S-", "BH-")):
                titik.append(dict(nama=r[0], jenis=jenis, x=r[2], y=r[3], elev=r[4], dalam=r[5]))
    return titik


def gambar_denah(titik, keluar):
    plt.rcParams["font.family"] = "Times New Roman"
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.add_patch(plt.Rectangle((0, 0), 140, 90, fill=False, lw=1.5, ec="black"))
    ax.fill_between([0, 140], -12, 0, color="#cfe3f3")
    ax.text(70, -7, "Sungai Batanghari (selatan) - tebing", ha="center", fontsize=10)
    ax.add_patch(plt.Rectangle((144, 20), 14, 50, fill=True, fc="#e0e0e0", ec="gray"))
    ax.text(151, 45, "Gudang lama\n2 lantai\n(pihak lain)", ha="center", va="center", fontsize=9)
    ax.text(70, 95, "Jalan kolektor 12 m (utara)", ha="center", fontsize=10)
    ax.text(-6, 45, "Jalan lingkungan 6 m (barat)", rotation=90, va="center", fontsize=10)
    ax.plot([0, 140], [80, 80], ls="--", c="gray", lw=0.8)
    ax.text(139, 81, "GSB utara 10 m", ha="right", fontsize=8, c="gray")
    ax.plot([5, 5], [0, 90], ls="--", c="gray", lw=0.8)
    ax.text(6, 30, "GSB barat 5 m", fontsize=8, c="gray", rotation=90)
    ax.plot(0, 0, marker="s", c="k")
    ax.text(1.5, 1.5, "BM-1 +10,000", fontsize=8)
    for t in titik:
        gaya = dict(marker="^", c="tab:blue", ms=9) if t["jenis"] == "Sondir" else dict(marker="o", c="tab:red", ms=10)
        ax.plot(t["x"], t["y"], ls="", **gaya)
        ax.annotate(f'{t["nama"]}\n+{t["elev"]:.2f}, {t["dalam"]:g} m'.replace(".", ","),
                    (t["x"], t["y"]), xytext=(5, 5), textcoords="offset points", fontsize=9)
    ax.plot([], [], "^", c="tab:blue", label="Sondir mekanis")
    ax.plot([], [], "o", c="tab:red", label="Bor + SPT")
    ax.legend(loc="upper right", fontsize=9, bbox_to_anchor=(1.0, 0.93))
    ax.set_xlim(-12, 162)
    ax.set_ylim(-14, 100)
    ax.set_aspect("equal")
    ax.set_xlabel("x lokal (m), ke timur")
    ax.set_ylabel("y lokal (m), ke utara")
    ax.grid(alpha=0.3)
    fig.text(0.5, 0.01, LABEL + " Label titik: elevasi muka tanah, kedalaman akhir. Batas lahan dan GSB dari KAK 4.1-4.2; "
             "gudang digambar skematis.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(keluar, dpi=200)
    plt.close(fig)


PETUNJUK = [
    "Sel kuning muda diisi Defsa; sel hijau berisi draf AI. AI memeriksa setelah Defsa selesai (CLAUDE.md).",
    "Berkas yang ditelaah: Ringkasan Laporan Penyelidikan Tanah.md, Sondir.xlsx, Bor dan SPT.xlsx, Laboratorium.xlsx.",
    "Konteks dari KAK: lahan 140 × 90 m, 6 lantai + 1 basement, urugan sampai +11,50, muka air sungai +4,0 (kemarau) "
    "sampai +11,20 (banjir), tebing sungai di selatan, gudang lama di timur.",
    "Kelompok 1 Cukup: jumlah, jarak, kedalaman titik (SNI 8460:2017 Tabel 2 hal. 25, Gambar 1 hal. 27, Pasal 5.2.4.1.3; "
    "SNI 1726:2019 Pasal 5.1).",
    "Kelompok 2 Dipercaya: prosedur, kualitas contoh, pengukuran air tanah (SNI 8460:2017 Pasal 5.3.2, 5.3.4.1, Tabel 3, 5.4.2-5.4.3).",
    "Kelompok 3 Konsisten: sondir vs bor vs lab, antartitik, ringkasan vs data mentah (SNI 8460:2017 Pasal 5.7.3).",
    "Kelompok 4 Kebutuhan desain: kelas situs, likuifaksi, galian dan dewatering, tiang, tebing, keawetan "
    "(SNI 1726:2019 Tabel 5, Pasal 6.7).",
    "Hasil akhir: lembar Temuan Telaah dan Usulan Penyelidikan (wajib, SNI 8460:2017 Pasal 5.7.1 hal. 62).",
    "Keparahan: Tinggi = mengubah keputusan desain atau keselamatan; Sedang = mengubah angka desain; Rendah = kelengkapan.",
    "Denah titik ada di 'Denah Titik Penyelidikan.png'. Lembar ini dibuat ulang dengan skrip/tahap1_lembar_telaah.py.",
]

CEK = [  # (butir, keterangan) ; nilai diisi / rumus
    ("Luas tapak bangunan yang diselidiki, A (m²)", "Isi dan sebutkan asumsinya"),
    ("Luas per titik menurut Tabel 2 (m²/titik)", "Pilih baris Tabel 2 yang berlaku"),
    ("Jumlah titik minimum", "Dibulatkan ke atas"),
    ("Jumlah titik bor yang ada", ""),
    ("Jumlah titik sondir yang ada", ""),
    ("d = kedalaman dasar bangunan dari muka tanah (m)", "Gambar 1(d)"),
    ("L = panjang tiang rencana (m)", ""),
    ("b = lebar terpendek tapak bangunan (m)", ""),
    ("Zi kriteria 1 = d + L + b (m)", ""),
    ("Zi kriteria 2 = d + 2/3 L + 1,5 b (m)", ""),
    ("Zi kriteria 3 = d + L + 5 (m)", ""),
    ("Zi perlu, terdalam (m)", ""),
    ("Kedalaman bor yang ada (m)", ""),
    ("h = dalam galian basement (m)", "Gambar 1(f)"),
    ("Zi galian = maks(1,4 h ; h + 2) (m)", ""),
    ("Kesimpulan", ""),
]


def buat_lembar(titik, ai=None, keluar=BERKAS):
    """ai: dict opsional dengan kunci temuan, usulan, cek, cek_ket, inventaris, kesimpulan."""
    ai = ai or {}
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)

    # 1 Petunjuk
    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk telaah penyelidikan tanah", [6, 120])
    lb.catatan(LABEL + (" DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026. "
                        "Kunci jawaban tidak dibuka." if ai else ""))
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i, t] for i, t in enumerate(PETUNJUK, start=1)], rata=list("cl"))

    # 2 Inventaris
    lb = Lembar(wb.create_sheet("Inventaris Data"), 2, "Inventaris data penyelidikan", [14, 14, 9, 9, 13, 13, 13, 50])
    lb.bagian("A", "Titik penyelidikan (disalin dari lembar Titik berkas data)")
    catatan = ai.get("inventaris", {})
    baris = []
    for t in titik:
        baris.append([t["nama"], t["jenis"], t["x"], t["y"], t["elev"], t["dalam"], None, catatan.get(t["nama"], "")])
    r0, r1, r2 = lb.tabel(["Titik", "Jenis", "x (m)", "y (m)", "Elevasi tanah (m)", "Kedalaman akhir (m)",
                           "Elevasi dasar (m)", "Catatan"], baris, rata=list("cccccccl"),
                          fmt=[None, None, "#,##0", "#,##0", "0.00", "0.0", "0.00", None],
                          fill_kolom={7: AI if ai else ISIAN})
    for r in range(r1, r2 + 1):
        lb.ws[f"I{r}"] = f"=G{r}-H{r}"
        if ai and not lb.ws[f"J{r}"].value:
            lb.ws[f"J{r}"].fill = openpyxl.styles.PatternFill(fill_type=None)
    lb.kosong()
    lb.bagian("B", "Uji laboratorium (jumlah baris data per lembar Laboratorium.xlsx)")
    wb_lab = openpyxl.load_workbook(FOLDER / "Laboratorium.xlsx", data_only=True)
    lab = [[nama, sum(1 for r in wb_lab[nama].iter_rows(values_only=True) if r[0] and str(r[0]).startswith("BH-"))]
           for nama in wb_lab.sheetnames]
    lb.tabel(["Lembar laboratorium", "Jumlah data"], lab, rata=list("lc"), beku=False)
    lb.ws.freeze_panes = f"A{r1}"

    # 3 Temuan
    lb = Lembar(wb.create_sheet("Temuan Telaah"), 3, "Temuan telaah laporan dan data penyelidikan tanah",
                [5, 16, 24, 55, 32, 40, 12, 32])
    temuan = ai.get("temuan") or [[""] * 7 for _ in range(N_TEMUAN)]
    r0, r1, r2 = lb.tabel(["No", "Kelompok", "Berkas / lembar / titik", "Temuan (apa yang dilihat)",
                           "Acuan (SNI pasal dan halaman)", "Dampak ke desain", "Keparahan", "Tindak lanjut"],
                          [[i] + list(t) for i, t in enumerate(temuan, start=1)], rata=list("clllllcl"),
                          fill=AI if ai else ISIAN, fill_kolom={0: None}, beku_kolom=2)
    for rentang, pilihan in [(f"D{r1}:D{r2}", "1 Cukup,2 Dipercaya,3 Konsisten,4 Kebutuhan desain"),
                             (f"I{r1}:I{r2}", "Tinggi,Sedang,Rendah")]:
        dv = DataValidation(type="list", formula1=f'"{pilihan}"', allow_blank=True)
        lb.ws.add_data_validation(dv)
        dv.add(rentang)

    # 4 Cek kecukupan
    lb = Lembar(wb.create_sheet("Cek Kecukupan"), 4, "Cek jumlah dan kedalaman titik (SNI 8460:2017 Tabel 2, Gambar 1)",
                [5, 50, 14, 70])
    nilai = ai.get("cek", {})
    ket = ai.get("cek_ket", {})
    r0 = lb.baris
    rr = {i: r0 + i for i in range(1, len(CEK) + 1)}  # nomor butir -> baris
    rumus = {3: f'=IF(AND(E{rr[1]}>0,E{rr[2]}>0),ROUNDUP(E{rr[1]}/E{rr[2]},0),"")',
             9: f'=IF(COUNT(E{rr[6]}:E{rr[8]})=3,E{rr[6]}+E{rr[7]}+E{rr[8]},"")',
             10: f'=IF(COUNT(E{rr[6]}:E{rr[8]})=3,E{rr[6]}+2/3*E{rr[7]}+1.5*E{rr[8]},"")',
             11: f'=IF(COUNT(E{rr[6]}:E{rr[7]})=2,E{rr[6]}+E{rr[7]}+5,"")',
             12: f'=IF(COUNT(E{rr[9]}:E{rr[11]})=3,MAX(E{rr[9]}:E{rr[11]}),"")',
             15: f'=IF(E{rr[14]}>0,MAX(1.4*E{rr[14]},E{rr[14]}+2),"")'}
    baris = []
    for i, (butir, k) in enumerate(CEK, start=1):
        baris.append([i, butir, rumus.get(i, nilai.get(i)), ket.get(i, k)])
    lb.tabel(["No", "Butir", "Nilai", "Keterangan"], baris, rata=list("clcl"), fmt=[None, None, "#,##0.0", None])
    for i in range(1, len(CEK) + 1):
        if i not in rumus:
            lb.ws[f"E{rr[i]}"].fill = openpyxl.styles.PatternFill("solid", fgColor=AI if i in nilai else ISIAN)
        if i in ket and ai:
            lb.ws[f"F{rr[i]}"].fill = openpyxl.styles.PatternFill("solid", fgColor=AI)

    # 5 Usulan
    lb = Lembar(wb.create_sheet("Usulan Penyelidikan"), 5,
                "Usulan penyelidikan tambahan (SNI 8460:2017 Pasal 5.7.1)", [5, 34, 28, 12, 10, 40, 28, 20, 28])
    usulan = ai.get("usulan") or [[""] * 8 for _ in range(N_USULAN)]
    r0, r1, r2 = lb.tabel(["No", "Jenis uji", "Lokasi (x, y) / zona", "Kedalaman (m)", "Jumlah",
                           "Alasan (rujuk No temuan)", "Acuan", "Prioritas", "Catatan biaya / waktu"],
                          [[i] + list(u) for i, u in enumerate(usulan, start=1)], rata=list("clllcllcl"),
                          fill=AI if ai else ISIAN, fill_kolom={0: None}, beku_kolom=2)
    dv = DataValidation(type="list", formula1='"Wajib sebelum desain,Sebelum DED,Saat konstruksi"', allow_blank=True)
    lb.ws.add_data_validation(dv)
    dv.add(f"J{r1}:J{r2}")

    wb.save(keluar)


if __name__ == "__main__":
    t = baca_titik()
    gambar_denah(t, FOLDER / "Denah Titik Penyelidikan.png")
    buat_lembar(t)
    print(f"{len(t)} titik; denah dan lembar kosong dibuat di {FOLDER}")
