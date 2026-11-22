"""Tahap 2 langkah 2.2: gambar geoteknik A3 (denah, penampang, peta tebal lapisan organik).

Keluaran: '02 Olah Data Tanah/Gambar/GT-0n ....png' dan '02 Olah Data Tanah/2.2 Gambar Geoteknik.pdf'.
Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap2_gambar_geoteknik.py
"""
import textwrap
from pathlib import Path

import numpy as np
from gambar_teknik import BukuPDF as PdfPages
from matplotlib.patches import Rectangle
from scipy.interpolate import griddata

import tahap2_koreksi_data as kd
import tahap2_stratigrafi as st
from gambar_teknik import Kertas

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "02 Olah Data Tanah"
FOLDER_GAMBAR = KELUAR / "Gambar"
PDF = KELUAR / "2.2 Gambar Geoteknik.pdf"

LAHAN = (0, 0, 140, 90)
TEBING = [(-5, -14.5), (0, -14), (40, -12), (60, -10), (80, -7), (90, -6.5), (100, -6), (125, -8.8),
          (140, -11), (175, -13)]
GUDANG = (144, 18, 24, 40)
BANJIR = 11.20
POTONGAN = {  # nama: (titik awal, titik akhir, toleransi proyeksi m, label arah)
    "A": ((10, 35), (140, 35), 7, ("BARAT", "TIMUR")),
    "B": ((10, 72), (140, 72), 10, ("BARAT", "TIMUR")),
    "C": ((55, 0), (55, 90), 15, ("SELATAN", "UTARA")),
}
ER = {"BH-4": 86, "BH-5": 85, "BH-6": 81, "BH-7": 53, "BH-8": 53, "BH-1": 53, "BH-2": 53, "BH-3": 53}
TOTAL_LEMBAR = 5


def fmt(v, d=2):
    return f"{v:.{d}f}".replace(".", ",")


# ---------------------------------------------------------------- legenda dan catatan
def legenda_unit(k, y_atas, tinggi=78, unit=None):
    unit = unit or st.URUT[:7]
    if hasattr(k, "legenda_unit"):  # LembarCAD: arsir standar di kotak KETERANGAN
        k.legenda_unit(unit)
        return y_atas
    x, y, w, h = k.judul_kolom(y_atas, "LEGENDA UNIT TANAH", tinggi)
    yy = y + h - 4
    for u in unit:
        nama, uscs, warna, arsir = st.UNIT[u]
        k.kertas.add_patch(Rectangle((x + 3, yy - 2.2), 9, 5, fc=warna, ec="#333", lw=0.4, hatch=arsir))
        k.teks(x + 14, yy + 0.3, f"{u}  {nama}", fontsize=6.3, va="center")
        k.teks(x + w - 3, yy + 0.3, uscs, fontsize=6.3, va="center", ha="right")
        yy -= 8
    return y


def kotak_catatan(k, y_atas, judul, butir, tinggi):
    if hasattr(k, "catatan"):  # LembarCAD: catatan di kotak KETERANGAN
        k.catatan(butir)
        return y_atas
    x, y, w, h = k.judul_kolom(y_atas, judul, tinggi)
    yy = y + h - 4
    for i, b in enumerate(butir, start=1):
        baris = textwrap.wrap(b, 74)
        k.teks(x + 2.5, yy, f"{i}.", fontsize=5.8, va="top")
        k.teks(x + 6, yy, "\n".join(baris), fontsize=5.8, va="top", linespacing=1.25)
        yy -= 2.55 * len(baris) + 1.4
    return y


# ---------------------------------------------------------------- denah
def gambar_denah(titik, pdf):
    k = Kertas()
    skala = 750
    x0m, x1m, y0m, y1m = -12, 176, -42, 96
    w, h = (x1m - x0m) / skala * 1000, (y1m - y0m) / skala * 1000
    ax = k.sumbu(32, 52, w, h)
    ax._cad = {"skala": skala, "jenis": "peta"}
    ax.set_xlim(x0m, x1m)
    ax.set_ylim(y0m, y1m)
    ax.set_aspect("equal")
    ax.set_facecolor("white")
    # sungai
    xs = [p[0] for p in TEBING]
    ys = [p[1] for p in TEBING]
    ax.fill_between(xs, ys, y0m, color="#d6e9f5", zorder=0)
    ax.plot(xs, ys, color="#7b4a22", lw=1.2)
    ax.text(70, -30, "S U N G A I   B A T A N G H A R I", ha="center", fontsize=9, color="#3c6e8f",
            style="italic")
    ax.text(15, -11.2, "puncak tebing", fontsize=5.5, color="#7b4a22", rotation=3)
    # lahan dan gudang
    ax.add_patch(Rectangle(LAHAN[:2], LAHAN[2], LAHAN[3], fill=False, lw=1.2, ls=(0, (8, 2, 2, 2)), ec="k"))
    ax.text(2, 91.5, "BATAS LAHAN", fontsize=5.5)
    ax.add_patch(Rectangle(GUDANG[:2], GUDANG[2], GUDANG[3], fc="#eeeeee", ec="#555", hatch="////", lw=0.6))
    ax.text(GUDANG[0] + GUDANG[2] / 2, GUDANG[1] + GUDANG[3] + 2, "GUDANG TETANGGA\n(pondasi cerucuk kayu)",
            ha="center", fontsize=5.5)
    # potongan
    for nama, (p0, p1, tol, _) in POTONGAN.items():
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color="#c0392b", lw=0.9, ls=(0, (10, 3, 2, 3)))
        for p, lab in ((p0, nama), (p1, nama + "'")):
            ax.add_patch(plt_lingkaran(p, 2.2))
            ax.text(p[0], p[1], lab, ha="center", va="center", fontsize=6.5, fontweight="bold", color="#c0392b", zorder=6)
    # titik lama non-bor
    lama_sondir = {"S-01": (15, 10), "S-02": (70, 25), "S-03": (95, 45), "S-04": (40, 60), "S-05": (110, 75),
                   "S-06": (125, 20)}
    for n, (x, y) in lama_sondir.items():
        ax.plot(x, y, marker="^", mfc="white", mec="#555", ms=4.5, mew=0.7, ls="")
        ax.text(x + 1.5, y - 2.8, n, fontsize=4.8, color="#555")
    gaya = {"Bor": dict(marker="o", ms=5.5, mfc="#c0392b", mec="k"),
            "CPTu": dict(marker="^", ms=5.5, mfc="#1f5f99", mec="k"),
            "Bor tangan": dict(marker="s", ms=4, mfc="#2e7d32", mec="k")}
    for t in titik:
        g = dict(gaya[t["jenis"]])
        if t["nama"] in ("BH-1", "BH-2", "BH-3"):
            g["mfc"] = "white"
        ax.plot(t["x"], t["y"], ls="", mew=0.6, **g)
        kiri = sisi_kiri(t, titik)
        dx, ha = (-1.6, "right") if kiri else (1.6, "left")
        ax.text(t["x"] + dx, t["y"] + 1.2, t["nama"], fontsize=5.2, fontweight="bold", ha=ha)
        ax.text(t["x"] + dx, t["y"] - 2.6, f"+{fmt(t['elev'])}", fontsize=4.5, color="#444", ha=ha)
    lain = [("PW-1", 65, 40, "P"), ("OW-1", 75, 40, "P"), ("OW-2", 95, 40, "P"), ("PZ-2", 60, 5, "D"),
            ("PZ-3", 40, 45, "D"), ("PZ-4", 53, 81.5, "D"), ("BT-1", 40, -10, "B"), ("BT-1K", 40, -22, "B"),
            ("BT-2", 90, -4.5, "B"), ("BT-2K", 90, -15, "B"), ("BT-3", 125, -7, "B"), ("PS-1", 60, -14, "R")]
    sim = {"P": dict(marker="P", mfc="k", mec="k", ms=5), "D": dict(marker="D", mfc="#7b3fa0", mec="k", ms=4),
           "B": dict(marker="o", mfc="#8d5a2b", mec="k", ms=4), "R": dict(marker="|", mfc="#1f5f99",
                                                                        mec="#1f5f99", ms=7)}
    for n, x, y, s_ in lain:
        ax.plot(x, y, ls="", mew=0.6, **sim[s_])
        if n == "PZ-4":
            ax.text(x - 1.6, y + 1.0, n, fontsize=4.6, color="#333", ha="right")
        else:
            ax.text(x + 1.6, y - 2.8, n, fontsize=4.6, color="#333")
    ax.set_xticks(range(0, 180, 20))
    ax.set_yticks(range(-40, 100, 20))
    ax.tick_params(labelsize=5.5, length=2)
    ax.grid(color="#bbbbbb", lw=0.3, ls=":")
    ax.set_xlabel("x lokal (m)", fontsize=6)
    ax.set_ylabel("y lokal (m)", fontsize=6)
    k.teks(32, 52 + h + 8, "DENAH TITIK PENYELIDIKAN DAN GARIS POTONGAN", fontsize=11, fontweight="bold")
    k.teks(32, 52 + h + 3.5, f"Skala 1:{skala}  -  koordinat lokal proyek, titik nol di sudut barat daya lahan",
           fontsize=6.5)
    k.skala_grafis(32, 30, 50, skala, judul=f"Skala grafis 1:{skala}")
    k.panah_utara(32 + w - 8, 52 + h - 18)
    # legenda simbol (kotak KETERANGAN)
    for m, isi, lab in (("o", True, "Bor mesin + SPT tambahan (BH-4 s.d. BH-8)"),
                        ("o", False, "Bor mesin + SPT awal (BH-1 s.d. BH-3)"),
                        ("^", True, "CPTu (CPTu-1 s.d. CPTu-8)"),
                        ("^", False, "Sondir mekanis awal (S-01 s.d. S-06)"),
                        ("s", True, "Bor tangan gambut (HA-1 s.d. HA-10)"),
                        ("D", True, "Piezometer (A lempung, B pasir)"),
                        ("P", True, "Sumur uji / sumur pantau"),
                        ("o", True, "Bor tebing (BT)"),
                        ("|", True, "Papan duga sungai PS-1")):
        k.legenda("simbol", lab, simbol=m, isi=isi, ukuran=1.6)
    k.legenda("garis", "Garis potongan penampang geoteknik", garis="DASHDOT", tebal=0.35)
    kotak_catatan(k, 195, "CATATAN", [
        "Koordinat dan elevasi dari laporan faktual GBL/LF/2027/021 dan TRG/LP/2026/117 (data simulasi).",
        "Elevasi muka tanah titik tertulis di bawah nama titik (m, datum BM-1 = +10,000).",
        "Potongan A-A' dan B-B' arah barat-timur; C-C' arah selatan-utara. Titik diproyeksikan ke garis "
        "potongan bila jaraknya tidak lebih dari 7 m (A), 10 m (B), atau 15 m (C).",
        "Garis puncak tebing diinterpolasi dari potongan P-1 s.d. P-3; lihat Survei Tebing.xlsx.",
    ], 60)
    k.etiket("Denah titik penyelidikan tanah dan garis potongan", "GT-01", f"1:{skala}", f"1 / {TOTAL_LEMBAR}")
    k.simpan(pdf, FOLDER_GAMBAR / "GT-01 Denah Titik dan Potongan.png")


def sisi_kiri(t, titik, jarak=6.0):
    """Label ditaruh di kiri bila ada titik lain dekat di sebelah kanannya."""
    for u in titik:
        if u is t:
            continue
        dx, dy = u["x"] - t["x"], u["y"] - t["y"]
        if 0 <= dx < jarak and abs(dy) < 4 and (dx > 0 or u["nama"] < t["nama"]):
            return True
    return False


def plt_lingkaran(p, r):
    from matplotlib.patches import Circle
    return Circle(p, r, fc="white", ec="#c0392b", lw=0.8, zorder=5)


# ---------------------------------------------------------------- penampang
def proyeksi(titik, p0, p1, tol):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    arah = (p1 - p0) / np.linalg.norm(p1 - p0)
    hasil = []
    for t in titik:
        v = np.array([t["x"], t["y"]]) - p0
        s = float(v @ arah)
        d = float(abs(v[0] * arah[1] - v[1] * arah[0]))
        if d <= tol and -2 <= s <= np.linalg.norm(p1 - p0) + 2:
            hasil.append(dict(t, s=s, jarak=d))
    return sorted(hasil, key=lambda t: t["s"]), float(np.linalg.norm(p1 - p0))


def gambar_penampang(nama, titik, pdf, lembar):
    p0, p1, tol, arah = POTONGAN[nama]
    proj, L = proyeksi(titik, p0, p1, tol)
    sk_h, sk_v = 500, 250
    zmin, zmax = -32, 17
    w, h = L / sk_h * 1000, (zmax - zmin) / sk_v * 1000
    k = Kertas()
    x_ax, y_ax = 40, 62
    ax = k.sumbu(x_ax, y_ax, w, h)
    ax._cad = {"skala": sk_h, "vertikal": sk_v, "jenis": "penampang"}
    ax.set_xlim(0, L)
    ax.set_ylim(zmin, zmax)
    s_grid = np.linspace(0, L, 400)
    pos = [0.0] + [t["s"] for t in proj] + [L]
    celah = max(range(len(pos) - 1), key=lambda i: pos[i + 1] - pos[i])
    s_label = (pos[celah] + pos[celah + 1]) / 2

    def garis(nilai):
        pts = sorted((s, z) for s, z in nilai)
        return np.interp(s_grid, [a for a, _ in pts], [b for _, b in pts])

    muka = garis([(t["s"], t["elev"]) for t in proj])
    batas = [muka]
    for u in st.URUT[1:7]:
        nilai = []
        for t in proj:
            if t["jenis"] == "CPTu" and u == "U2":
                continue
            d = st.atas_unit(t, u)
            if d is not None and d <= t["akhir"] + 0.01:
                nilai.append((t["s"], t["elev"] - d))
        g = garis(nilai) if nilai else np.full_like(s_grid, zmin)
        batas.append(np.minimum(g, batas[-1]))
    batas.append(np.full_like(s_grid, zmin))
    for i, u in enumerate(st.URUT[:7]):
        _, _, warna, arsir = st.UNIT[u]
        ax.fill_between(s_grid, batas[i], batas[i + 1], facecolor=warna, edgecolor="#00000030", hatch=arsir,
                        linewidth=0, zorder=1)
        if i > 0:
            ax.plot(s_grid, batas[i], color="#222", lw=0.45, ls=(0, (6, 2)), zorder=2)
        tengah = (batas[i] + batas[i + 1]) / 2
        tebal = batas[i] - batas[i + 1]
        j = int(np.argmin(abs(s_grid - s_label)))
        if tebal[j] > 1.2:
            ax.text(s_grid[j], tengah[j], u, fontsize=7.5, fontweight="bold", ha="center", va="center",
                    color="white" if u in ("U3", "U6") else "#222", zorder=6)
    ax.plot(s_grid, muka, color="k", lw=1.0, zorder=3)
    ax.fill_between(s_grid, muka, zmax, color="white", zorder=2)
    # air
    ax.axhline(BANJIR, color="#1f5f99", lw=0.7, ls=(0, (8, 3)), zorder=3)
    ax.text(L - 1, BANJIR + 0.3, f"Muka banjir rencana +{fmt(BANJIR)} (Tahap 1)", fontsize=5.5,
            color="#1f5f99", ha="right")
    ax.plot(s_grid, muka - 0.02, color="#1f5f99", lw=0.6, ls=":", zorder=4)
    # kolom titik; label bertingkat bila titik berdekatan
    tingkat, s_sebelum = 0, -99.0
    for t in proj:
        tingkat = (tingkat + 1) % 3 if t["s"] - s_sebelum < 8 else 0
        s_sebelum = t["s"]
        t["tingkat"] = tingkat
        t["tetangga_kanan"] = any(0 < u["s"] - t["s"] < 6 for u in proj)
    for t in proj:
        s = t["s"]
        lebar = 1.4 if t["jenis"] == "Bor tangan" else 2.0
        if t["jenis"] in ("Bor", "Bor tangan"):
            for lp in t["lapisan"]:
                _, _, warna, arsir = st.UNIT[lp["unit"]]
                bawah = max(t["elev"] - lp["bawah"], zmin)
                ax.add_patch(Rectangle((s - lebar / 2, bawah), lebar, (t["elev"] - lp["atas"]) - bawah,
                                       fc=warna, ec="k", lw=0.5, hatch=arsir, zorder=7))
        if t["jenis"] == "Bor":
            for u in kd.baca_spt():
                if u["bor"] != t["nama"]:
                    continue
                z = t["elev"] - u["dari"] - 0.225
                if z < zmin:
                    continue
                n60 = u["n"] * ER[u["bor"]] / 60
                tanda = "≥" if u["jenis"] == "Penolakan" else ""
                warna = "#999" if kd.status_spt(u)[0] == "Tidak" else "k"
                if t["tetangga_kanan"]:
                    ax.text(s - lebar / 2 - 0.4, z, f"{tanda}{n60:.0f}", fontsize=4.2, va="center", ha="right",
                            color=warna, zorder=8)
                else:
                    ax.text(s + lebar / 2 + 0.4, z, f"{tanda}{n60:.0f}", fontsize=4.2, va="center",
                            color=warna, zorder=8)
        if t["jenis"] == "CPTu":
            qt = np.clip(t["qt"], 0, 12)
            ax.plot([s, s], [t["elev"], t["elev"] - t["akhir"]], color="#1f5f99", lw=0.4, zorder=7)
            ax.plot(s + qt * 0.9, t["elev"] - t["z"], color="#1f5f99", lw=0.55, zorder=8)
            ax.plot([s, s + 9], [t["elev"] + 0.6] * 2, color="#1f5f99", lw=0.4, zorder=8)
            for q in (0, 5, 10):
                ax.text(s + q * 0.9, t["elev"] + 0.9, f"{q}", fontsize=3.8, ha="center", color="#1f5f99", zorder=8)
            ax.text(s + 10, t["elev"] + 0.9, "qt MPa", fontsize=3.8, color="#1f5f99", zorder=8)
        tinggi_label = 12.4 + 1.5 * t["tingkat"]
        ax.plot([s, s], [t["elev"] + (1.4 if t["jenis"] == "CPTu" else 0.1), tinggi_label - 0.1], color="#888",
                lw=0.3, zorder=8)
        ax.text(s, tinggi_label + 0.75, t["nama"], fontsize=5.8, fontweight="bold", ha="center", zorder=9,
                bbox=dict(fc="white", ec="none", pad=0.2))
        ax.text(s, tinggi_label + 0.05, f"+{fmt(t['elev'])} | {t['jarak']:.0f} m", fontsize=4.2, ha="center",
                color="#444", zorder=9)
        if t["elev"] - t["akhir"] > zmin:
            ax.text(s, t["elev"] - t["akhir"] - 0.5, f"Akhir {fmt(t['akhir'])} m", fontsize=4.2, ha="center",
                    va="top", zorder=9)
    ax.set_xticks(np.arange(0, L + 0.1, 10))
    ax.set_yticks(np.arange(-30, 11, 5))
    ax.tick_params(labelsize=5.5, length=2)
    ax.grid(color="#999", lw=0.25, ls=":", zorder=0)
    ax.set_xlabel(f"Jarak sepanjang potongan dari {nama} (m)", fontsize=6)
    ax.set_ylabel("Elevasi (m)", fontsize=6)
    ax.set_axisbelow(True)
    for s_, lab, ha in ((0, f"{nama}\n{arah[0]}", "left"), (L, f"{nama}'\n{arah[1]}", "right")):
        k.teks(x_ax + s_ / sk_h * 1000, y_ax + h + 4, lab, ha=ha, fontsize=8, fontweight="bold", color="#c0392b")
    k.teks(x_ax + 40, y_ax + h + 9, f"PENAMPANG GEOTEKNIK {nama}-{nama}'", fontsize=11, fontweight="bold")
    k.teks(x_ax + 40, y_ax + h + 4.5, f"Skala horizontal 1:{sk_h}, vertikal 1:{sk_v} (dilebihkan 2x)", fontsize=6.5)
    k.skala_grafis(x_ax, 36, 50, sk_h, judul=f"Skala horizontal 1:{sk_h}")
    k.skala_grafis(x_ax + 125, 36, 20, sk_v, bagi=4, judul=f"Skala vertikal 1:{sk_v}")
    legenda_unit(k, 287, tinggi=66)
    kotak_catatan(k, 219, "CATATAN", [
        "Batas antartitik diinterpolasi lurus (garis putus); kondisi di antara titik dapat berbeda.",
        "Angka di kanan kolom bor = N60 (langkah 2.1; ER per bor). '≥' = penolakan, abu-abu = tidak dipakai.",
        "Garis biru tipis di kanan CPTu = qt (0-12 MPa). Batas unit di CPTu dari qt dan Rf (lihat 2.2 Stratigrafi.xlsx).",
        "Label titik: elevasi muka tanah | jarak proyeksi ke garis potongan.",
        "MAT desain sementara di muka tanah (garis titik biru); MAT desain final ditetapkan di langkah 2.3.",
        "Unit U8 (lempung keras) hanya di BH-5 di bawah 54,8 m; di luar batas gambar.",
    ], 78)
    k.etiket(f"Penampang geoteknik {nama}-{nama}'", f"GT-0{lembar}", f"H 1:{sk_h} V 1:{sk_v}",
             f"{lembar} / {TOTAL_LEMBAR}")
    k.simpan(pdf, FOLDER_GAMBAR / f"GT-0{lembar} Penampang {nama}-{nama}'.png")
    return proj


# ---------------------------------------------------------------- peta organik
def gambar_peta_organik(titik, pdf):
    k = Kertas()
    skala = 750
    x0m, x1m, y0m, y1m = -8, 148, -8, 98
    w, h = (x1m - x0m) / skala * 1000, (y1m - y0m) / skala * 1000
    ax = k.sumbu(40, 70, w, h)
    ax._cad = {"skala": skala, "jenis": "peta"}
    ax.set_xlim(x0m, x1m)
    ax.set_ylim(y0m, y1m)
    ax.set_aspect("equal")
    pts = np.array([[t["x"], t["y"]] for t in titik])
    nil = np.array([st.tebal_organik(t) for t in titik])
    gx, gy = np.meshgrid(np.linspace(0, 140, 281), np.linspace(0, 90, 181))
    gz = griddata(pts, nil, (gx, gy), method="linear")
    tingkat = [-0.01, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4]
    warna = ["#fbf3e4", "#f1dfbf", "#e3c597", "#d1a670", "#b9864e", "#9a6a38", "#7a5028", "#5b3a1c"]
    cf = ax.contourf(gx, gy, gz, levels=tingkat, colors=warna, extend="neither")
    cs = ax.contour(gx, gy, gz, levels=tingkat[1:], colors="#3b2a1a", linewidths=0.4)
    ax.clabel(cs, fmt=lambda v: fmt(v, 1), fontsize=5)
    c3 = ax.contour(gx, gy, gz, levels=[3.0], colors="#b00020", linewidths=1.3)
    ax.contourf(gx, gy, gz, levels=[3.0, 10], colors="none", hatches=["////"])
    del c3
    ax.add_patch(Rectangle(LAHAN[:2], LAHAN[2], LAHAN[3], fill=False, lw=1.0, ls=(0, (8, 2, 2, 2))))
    for t, v in zip(titik, nil):
        m = {"Bor": "o", "CPTu": "^", "Bor tangan": "s"}[t["jenis"]]
        ax.plot(t["x"], t["y"], marker=m, mfc="white", mec="k", ms=4, mew=0.6, ls="")
        lab = ("≥" if t.get("org_terbuka") else "") + fmt(v)
        kiri = sisi_kiri(t, titik)
        ax.text(t["x"] + (-1.5 if kiri else 1.5), t["y"] + 1.3, f"{t['nama']}\n{lab}", fontsize=4.6,
                fontweight="bold", ha="right" if kiri else "left",
                bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.3))
    ax.set_xticks(range(0, 150, 20))
    ax.set_yticks(range(0, 100, 20))
    ax.tick_params(labelsize=5.5, length=2)
    ax.set_xlabel("x lokal (m)", fontsize=6)
    ax.set_ylabel("y lokal (m)", fontsize=6)
    k.teks(40, 70 + h + 13, "PETA TEBAL LAPISAN ORGANIK (UNIT U3: GAMBUT DAN LEMPUNG ORGANIK)", fontsize=11,
           fontweight="bold")
    k.teks(40, 70 + h + 8.5, f"Skala 1:{skala}  -  kontur tebal (m), interpolasi linear antartitik", fontsize=6.5)
    k.skala_grafis(40, 45, 50, skala, judul=f"Skala grafis 1:{skala}")
    k.panah_utara(40 + w - 8, 70 + h - 18)
    k.legenda("garis", "Kontur tebal lapisan organik U3 (interval 0,5 m)", tebal=0.18)
    k.legenda("garis", "Kontur tebal 3,0 m", tebal=0.5)
    k.legenda("arsir", "Tebal ≥ 3,0 m (perlu dicek kelas situs SF)", pola="ANSI31", skala_pola=0.45)
    k.legenda("garis", "Batas lahan", garis="DASHDOT", tebal=0.35)
    kotak_catatan(k, 205, "CATATAN", [
        "Tebal U3 = jumlah gambut dan lempung organik. Bor tangan: dari lembar Titik bor tangan; bor mesin: "
        "dari log; CPTu: rentang Rf > 5 % di 0,9-5,5 m.",
        "HA-9 berhenti di 4,0 m masih di gambut: tebal ≥ 2,97 m (batas bawah), lapisan sebenarnya lebih tebal.",
        "Bagian selatan (y < ±42 m) tidak mengandung lapisan organik (BH-1, BH-2, BH-4, BH-5, BH-6, CPTu-2, "
        "CPTu-6, CPTu-7). Lapisan menebal ke utara sampai ±3,3-3,7 m.",
        "Batas tebal 3 m: kriteria kelas situs SF untuk gambut/lempung organik di SNI 1726:2019 Tabel 5; "
        "penetapan kelas situs di langkah 2.5.",
        "Di luar jangkauan titik (tepi lahan) tidak diinterpolasi (putih).",
    ], 88)
    k.etiket("Peta tebal lapisan organik U3", "GT-05", f"1:{skala}", f"5 / {TOTAL_LEMBAR}")
    k.simpan(pdf, FOLDER_GAMBAR / "GT-05 Peta Tebal Lapisan Organik.png")
    return cf


def buat():
    FOLDER_GAMBAR.mkdir(parents=True, exist_ok=True)
    titik = st.semua_titik()
    with PdfPages(PDF) as pdf:
        gambar_denah(titik, pdf)
        for i, nama in enumerate("ABC", start=2):
            gambar_penampang(nama, titik, pdf, i)
        gambar_peta_organik(titik, pdf)
        info = pdf.infodict()
        info["Title"] = "2.2 Gambar Geoteknik - RS Tepian Batanghari (data simulasi)"
        info["Author"] = "Defsa Yurinda (draf AI)"
    return PDF


if __name__ == "__main__":
    print(buat())
