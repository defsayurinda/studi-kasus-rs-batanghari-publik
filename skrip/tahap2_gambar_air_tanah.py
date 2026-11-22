"""Tahap 2 langkah 2.3: gambar A3 berkop (hidrograf, uji pemompaan, batas dasar galian blow-in).

Keluaran: '02 Olah Data Tanah/Gambar/GT-06..08 ....png' dan '02 Olah Data Tanah/2.3 Gambar Air Tanah.pdf'.
Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap2_gambar_air_tanah.py
"""
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import numpy as np
from gambar_teknik import BukuPDF as PdfPages

import tahap2_air_tanah as at
from gambar_teknik import Kertas
from tahap2_gambar_geoteknik import kotak_catatan

AKAR = Path(__file__).resolve().parents[1]
FOLDER = AKAR / "02 Olah Data Tanah" / "Gambar"
PDF = AKAR / "02 Olah Data Tanah" / "2.3 Gambar Air Tanah.pdf"
WARNA = {"Sungai": "#1f5f99", "PZ-2B": "#c0392b", "PZ-3B": "#e67e22", "PZ-4B": "#8e44ad", "PZ-2A": "#c0392b",
         "PZ-3A": "#e67e22", "PZ-4A": "#8e44ad", "PZ-1": "#2e7d32", "SP-1": "#7f8c8d"}
TOTAL = 3


def gaya_sumbu(ax, judul=None):
    ax.tick_params(labelsize=6, length=2)
    ax.grid(color="#bbbbbb", lw=0.3, ls=":")
    for s in ax.spines.values():
        s.set_linewidth(0.6)
    if judul:
        ax.set_title(judul, fontsize=7.5, fontweight="bold", loc="left")


def fmt(v, d=2):
    return f"{v:.{d}f}".replace(".", ",")


def gambar_hidrograf(pdf):
    k = Kertas()
    H = at.bersihkan_harian()
    W = at.mingguan()
    tg = [d["Tanggal"] for d in H]
    ax = k.sumbu(35, 150, 260, 112)
    ax.axhspan(8.82, 10.55, color="#f3ead8", zorder=0)
    ax.text(datetime(2026, 9, 3), 10.62, "rentang muka tanah titik penyelidikan (+8,82 s.d. +10,55)", fontsize=5.5,
            color="#7b5a2b")
    ax.axhline(11.20, color=WARNA["Sungai"], lw=0.7, ls=(0, (8, 3)))
    ax.text(datetime(2026, 9, 3), 11.27, "muka banjir maksimum tercatat +11,20 (TOR Lampiran A)", fontsize=5.5,
            color=WARNA["Sungai"])
    ax.axvspan(datetime(2026, 12, 7), datetime(2026, 12, 13), color="#dddddd", zorder=0)
    ax.text(datetime(2026, 12, 7, 12), 4.15, "uji\npompa", fontsize=5, ha="left")
    tw = [w["Tanggal"] for w in W]
    ax.plot(tw, [w["Muka air sungai (m)"] for w in W], color=WARNA["Sungai"], lw=0.6, ls="--", marker=".", ms=2)
    ax.plot(tg, [d["Sungai (m)"] for d in H], color=WARNA["Sungai"], lw=1.4, label="Sungai (PS-1 harian; mingguan putus)")
    ax.plot(tw, [w.get("PZ-1 elevasi (m)") for w in W], color=WARNA["PZ-1"], lw=1.0, marker="o", ms=2,
            label="PZ-1 pasir 14 m (BH-1, mingguan)")
    ax.plot(tw, [w.get("SP-1 elevasi (m)") for w in W], color=WARNA["SP-1"], lw=1.0, marker="s", ms=2,
            label="SP-1 pipa tegak 1,5-3,0 m (BH-1, mingguan)")
    for s in at.SENSOR_B:
        n = s[:5]
        ax.plot(tg, [d[s] if isinstance(d[s], (int, float)) else np.nan for d in H], color=WARNA[n], lw=1.0,
                label=f"{n} pasir 14 m")
    for s in at.SENSOR_A:
        n = s[:5]
        ax.plot(tg, [d[s] if isinstance(d[s], (int, float)) else np.nan for d in H], color=WARNA[n], lw=0.7,
                ls=(0, (3, 1.5)), label=f"{n} lempung 5 m")
    ax.set_ylim(4, 11.8)
    ax.set_xlim(datetime(2026, 9, 1), datetime(2027, 4, 2))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_ylabel("Elevasi muka air / tinggi tekan (m)", fontsize=6.5)
    ax.legend(fontsize=5.5, loc="lower right", ncol=2, frameon=True, framealpha=0.95)
    gaya_sumbu(ax, "A. Hidrograf sungai, piezometer, dan pipa tegak (Sep 2026 - Mar 2027)")
    # regresi jeda
    ax2 = k.sumbu(35, 38, 120, 88)
    riv = np.array([d["Sungai (m)"] for d in H])
    for s in at.SENSOR_B:
        g = at.regresi_jeda(s)
        L = g["L"]
        h = np.array([d[s] if isinstance(d[s], (int, float)) else np.nan for d in H])
        x, y = (riv[:len(riv) - L], h[L:]) if L else (riv, h)
        ax2.plot(x, y, ".", ms=2.2, color=WARNA[s[:5]], alpha=0.7)
        xx = np.array([7.4, 11.2])
        ax2.plot(xx, g["a"] + g["b"] * xx, color=WARNA[s[:5]], lw=0.9,
                 label=f"{s[:5]}: h = {fmt(g['a'])} + {fmt(g['b'], 3)} H(t-{L} hari), r = {fmt(g['r'], 3)}")
    ax2.plot([7.4, 11.2], [7.4, 11.2], color="#555", lw=0.5, ls=":", label="garis h = H")
    ax2.set_xlabel("Muka sungai H, digeser sebesar jeda L (m)", fontsize=6.5)
    ax2.set_ylabel("Tinggi tekan pasir h (m)", fontsize=6.5)
    ax2.legend(fontsize=5.2, loc="upper left")
    gaya_sumbu(ax2, "B. Regresi tinggi tekan pasir terhadap sungai")
    ax3 = k.sumbu(180, 38, 115, 88)
    g = at.regresi_pz1()
    ax3.plot(g["x"], g["y"], "o", ms=2.5, color=WARNA["PZ-1"])
    xx = np.array([3.8, 11.2])
    ax3.plot(xx, g["a"] + g["b"] * xx, color=WARNA["PZ-1"], lw=0.9,
             label=f"PZ-1: h = {fmt(g['a'])} + {fmt(g['b'], 3)} H, r = {fmt(g['r'], 3)} (n = {g['n']})")
    ax3.plot(xx, xx, color="#555", lw=0.5, ls=":", label="garis h = H")
    ax3.set_xlabel("Muka sungai H (m)", fontsize=6.5)
    ax3.set_ylabel("Tinggi tekan PZ-1 (m)", fontsize=6.5)
    ax3.legend(fontsize=5.5, loc="upper left")
    gaya_sumbu(ax3, "C. PZ-1 (BH-1) mingguan, termasuk musim surut")
    k.teks(35, 275, "HIDROGRAF AIR TANAH DAN SUNGAI", fontsize=11, fontweight="bold")
    k.teks(35, 270, "Elevasi terhadap BM-1 = +10,000; data harian rata-rata empat bacaan logger", fontsize=6.5)
    kotak_catatan(k, 287, "CATATAN", [
        "Sensor B (pasir) tidak ditampilkan 7-13 Des 2026 (terpengaruh uji pompa PW-1); PZ-3A 14 Feb 2027 "
        "dibuang (lonjakan setelah petir); PZ-4B kosong 24 Jan - 2 Feb 2027 (logger mati).",
        "Tinggi tekan pasir mengikuti sungai dengan jeda 3 hari (PZ-2B, dekat tebing), 6 hari (PZ-3B), 7 hari "
        "(PZ-4B). Saat surut, tinggi tekan pasir di atas sungai: akuifer mengalir ke sungai.",
        "Sensor A (lempung) dan SP-1 lebih tinggi dari sensor B saat normal (aliran ke bawah); saat lahan "
        "tergenang mengikuti muka genangan.",
        "Puncak sungai 10,83 (15 Jan 2027); puncak PZ-2B 10,41 (19 Jan), PZ-3B 9,92 (21 Jan), PZ-4B 9,72 (22 Jan).",
        "Usulan tinggi tekan desain akuifer: +11,20 (lihat 2.3 Air Tanah.xlsx lembar MAT Desain).",
    ], 92)
    k.etiket("Hidrograf air tanah dan sungai", "GT-06", "Tanpa skala", f"1 / {TOTAL}")
    k.simpan(pdf, FOLDER / "GT-06 Hidrograf Air Tanah.png")


def gambar_uji_pompa(pdf):
    k = Kertas()
    up = at.ringkas_uji_pompa()
    t, s = up["t"], up["s"]
    m = up["q"] > 0
    ax = k.sumbu(35, 100, 150, 160)
    for ow, w in (("PW-1", "#555"), ("OW-1", "#c0392b"), ("OW-2", "#1f5f99")):
        ax.semilogx(t[m & (t < 1860)], s[ow][m & (t < 1860)], "o", ms=2.6, color=w, label=f"{ow} (sebelum pompa mati)")
        ax.semilogx(t[m & (t > 1878)], s[ow][m & (t > 1878)], "x", ms=2.6, color=w, label=f"{ow} (sesudah)")
    for ow, w in (("OW-1", "#c0392b"), ("OW-2", "#1f5f99")):
        cj = up["cj"][ow]
        tt = np.logspace(-0.3, 2)
        ax.semilogx(tt, cj["ds"] * np.log10(tt * 60 / cj["t0"]), color=w, lw=0.8, ls="--")
        ax.axhline(up["s1"] if ow == "OW-1" else up["s2"], color=w, lw=0.6, ls=":")
    ax.text(300, up["s1"] - 0.12, f"tunak OW-1 = {fmt(up['s1'], 3)} m", fontsize=5.5, color="#c0392b", ha="center")
    ax.text(300, up["s2"] - 0.12, f"tunak OW-2 = {fmt(up['s2'], 3)} m", fontsize=5.5, color="#1f5f99", ha="center")
    ax.invert_yaxis()
    ax.set_xlabel("Waktu sejak pompa mulai (menit, skala log)", fontsize=6.5)
    ax.set_ylabel("Penurunan muka air s (m)", fontsize=6.5)
    ax.legend(fontsize=5.2, loc="lower left", ncol=3)
    gaya_sumbu(ax, "A. Penurunan muka air uji debit tetap 72 jam (Q ±3,98 L/s)")
    ax2 = k.sumbu(205, 190, 90, 70)
    ax2.semilogx(up["tt"] / up["tp"], up["sr"], "o", ms=2.5, color="#c0392b")
    mm = (up["tp"] >= 1) & (up["tp"] <= 20)
    kem = np.polyfit(np.log10(up["tt"][mm] / up["tp"][mm]), up["sr"][mm], 1)
    xx = np.logspace(2.2, 4)
    ax2.semilogx(xx, np.polyval(kem, np.log10(xx)), color="#c0392b", lw=0.8, ls="--", label="garis lurus t' = 1-20 menit")
    ax2.set_ylim(-0.2, 1.7)
    ax2.legend(fontsize=5.5, loc="upper left")
    ax2.set_xlabel("t / t' (-)", fontsize=6.5)
    ax2.set_ylabel("Penurunan sisa OW-1 (m)", fontsize=6.5)
    gaya_sumbu(ax2, "B. Pemulihan (Theis-Jacob)")
    ax3 = k.sumbu(205, 100, 90, 70)
    bt = at.uji_bertahap_jacob()
    ax3.plot(bt["q"] * 1000, bt["sw"] / bt["q"], "s", ms=3.5, color="#555")
    qq = np.linspace(0, 5, 20) / 1000
    ax3.plot(qq * 1000, bt["B"] + bt["C"] * qq, color="#555", lw=0.8, ls="--",
             label=f"s/Q = {bt['B']:.0f} + {bt['C']:.0f} Q")
    ax3.set_xlabel("Debit Q (L/s)", fontsize=6.5)
    ax3.set_ylabel("s_w / Q (s/m²)", fontsize=6.5)
    ax3.set_ylim(0, 2000)
    ax3.legend(fontsize=5.5, loc="lower right")
    gaya_sumbu(ax3, "C. Uji bertahap (Jacob)")
    # tabel hasil
    y = 82
    k.teks(35, y, "D. RINGKASAN HASIL", fontsize=7.5, fontweight="bold")
    baris = [("Metode", "T (m²/s)", "k (m/s)", "S"),
             ("Thiem (GEC 5 Pers. 10.24)", f"{up['T_thiem']:.2e}", f"{up['k_thiem']:.2e}", "-"),
             ("Sumur bayangan OW-1 / OW-2", f"{up['T_bayangan']['OW-1']:.2e} / {up['T_bayangan']['OW-2']:.2e}", "-", "-"),
             ("Cooper-Jacob OW-1 / OW-2", f"{up['cj']['OW-1']['T']:.2e} / {up['cj']['OW-2']['T']:.2e}", "-",
              f"{up['cj']['OW-1']['S']:.1e}"),
             ("Pemulihan Theis-Jacob OW-1", f"{up['T_pulih']:.2e}", "-", "-")]
    xs = [35, 105, 175, 215]
    for i, r in enumerate(baris):
        for x, v in zip(xs, r):
            v = v if i == 0 or x == xs[0] else v.replace(".", ",")
            k.teks(x, y - 6 - i * 4.5, v, fontsize=6.2, fontweight="bold" if i == 0 else None)
    kotak_catatan(k, 287, "CATATAN", [
        "PW-1 (65; 40) saringan 10-18,6 m di pasir U5; OW-1 dan OW-2 pada 10 m dan 30 m. Tebal akuifer 9,3 m.",
        "Penurunan tunak setelah ±4 jam: batas isian (sungai, tebing ±49 m dari PW-1).",
        "Katup disetel pada menit 30 (Q 4,13 → ±3,98 L/s); pompa mati 18 menit pada menit 1.860 (genset). "
        "Jendela tunak: menit 960-1.800 dan 2.160-4.320.",
        "Sungai naik 0,18 m selama uji; Thiem memakai selisih dua sumur pantau sehingga tidak terpengaruh.",
        "Cooper-Jacob, Theis-Jacob, Jacob uji bertahap, dan sumur bayangan dari literatur (belum ada di acuan/); "
        "dipakai sebagai cek silang.",
        "Bacaan PW-1 menit 400 uji bertahap dianggap salah baca dan tidak dipakai.",
    ], 92)
    k.teks(35, 275, "ANALISIS UJI PEMOMPAAN PW-1", fontsize=11, fontweight="bold")
    k.teks(35, 270, "Uji bertahap 7 Des 2026; uji debit tetap 8-11 Des 2026; pemulihan 11-12 Des 2026", fontsize=6.5)
    k.etiket("Analisis uji pemompaan PW-1", "GT-07", "Tanpa skala", f"2 / {TOTAL}")
    k.simpan(pdf, FOLDER / "GT-07 Uji Pemompaan.png")


def gambar_blowin(pdf):
    k = Kertas()
    ax = k.sumbu(35, 75, 260, 180)
    h = np.linspace(4.0, 11.2, 145)
    warna = ["#2e7d32", "#5b3a1c", "#1f5f99"]
    for (p, (elev0, lap)), w in zip(at.PROFIL.items(), warna):
        e = [at.elev_dasar_min(p, x) for x in h]
        e = np.array([np.nan if v is None else v for v in e])
        ax.plot(h, e, color=w, lw=1.4, label=f"{p}: muka tanah +{fmt(elev0)}, atas pasir {fmt(elev0 - lap[-1][0])}")
        ax.axhline(elev0, color=w, lw=0.5, ls=":")
        ax.text(11.35, elev0 + 0.06, f"muka tanah {p.split(' (')[1][:-1]} +{fmt(elev0)}", fontsize=5.3, color=w,
                ha="right")
    ax.axhline(6.0, color="#b00020", lw=0.9, ls=(0, (6, 2)))
    ax.text(4.1, 6.12, "contoh dasar galian basement ±+6,0 [Asumsi; ditetapkan di Tahap 3]", fontsize=6,
            color="#b00020")
    for bln, rata, maks in at.SUNGAI_BULANAN:
        hb = max(maks, rata + at.SELISIH_SURUT)
        ax.plot([hb, hb], [1.0, 1.6], color="#333", lw=0.7)
        ax.text(hb, 1.75, bln, fontsize=5.3, ha="center", rotation=90, va="bottom")
    ax.text(4.1, 2.75, "tinggi tekan akuifer konstruksi per bulan:", fontsize=5.5)
    ax.fill_between(h, 10.6, 11.0, color="white", alpha=0)
    ax.set_xlim(4, 11.4)
    ax.set_ylim(1, 11)
    ax.set_xlabel("Tinggi tekan akuifer pasir U5, h (m)", fontsize=6.5)
    ax.set_ylabel("Elevasi dasar galian terendah yang aman, FK blow-in = 1,25 (m)", fontsize=6.5)
    ax.legend(fontsize=6, loc="upper left")
    ax.text(10.9, 4.0, "AMAN\n(dasar galian di atas garis)", fontsize=7, ha="right", color="#2e7d32",
            fontweight="bold")
    gaya_sumbu(ax, "Batas dasar galian terhadap blow-in (galian kering, tanpa sumur pelepas tekanan)")
    k.teks(35, 275, "BATAS DASAR GALIAN TERHADAP BLOW-IN", fontsize=11, fontweight="bold")
    k.teks(35, 270, "SNI 8460:2017 Pasal 10.3.6.7.2 hal. 211: FK blow-in ≥ 1,25", fontsize=6.5)
    kotak_catatan(k, 287, "CATATAN", [
        "FK = σv total lempung antara dasar galian dan atas pasir U5 / u di atas pasir, u = γw (h - elevasi atas "
        "pasir). γ: urugan 17,0 [Asumsi], kerak 17,8, gambut 10,7, lempung lunak 15,2 kN/m³ (lab).",
        "Tinggi tekan konstruksi per bulan = maks(H maks bulanan; H rata-rata + 0,9) dari TOR Lampiran A "
        "[Asumsi: selisih PZ-1 dan sungai saat surut Sep 2026].",
        "Dengan dasar galian ±+6,0, FK ≥ 1,25 hanya tercapai bila h ≤ ±+6,4-7,1: praktis Juni-Oktober, atau "
        "dengan sumur pelepas tekanan (dewatering akuifer) sepanjang tahun.",
        "Zona gambut (BH-3) paling kritis karena gambut ringan; pada h = +11,20 tanpa genangan FK tanpa galian 1,20.",
        "Tidak memperhitungkan beban urugan +11,50, hambatan dinding galian, atau genangan; rancangan galian dan "
        "dewatering di Tahap 6.",
    ], 92)
    k.etiket("Batas dasar galian terhadap blow-in", "GT-08", "Tanpa skala", f"3 / {TOTAL}")
    k.simpan(pdf, FOLDER / "GT-08 Batas Dasar Galian Blow-in.png")


def buat():
    FOLDER.mkdir(parents=True, exist_ok=True)
    with PdfPages(PDF) as pdf:
        gambar_hidrograf(pdf)
        gambar_uji_pompa(pdf)
        gambar_blowin(pdf)
        pdf.infodict()["Title"] = "2.3 Gambar Air Tanah - RS Tepian Batanghari (data simulasi)"
    return PDF


if __name__ == "__main__":
    print(buat())
