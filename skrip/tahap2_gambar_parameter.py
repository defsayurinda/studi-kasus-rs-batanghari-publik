"""Tahap 2 langkah 2.4: gambar A3 berkop (profil parameter lempung; pasir dan kuat geser efektif).

Keluaran: '02 Olah Data Tanah/Gambar/GT-09, GT-10 ....png' dan '02 Olah Data Tanah/2.4 Gambar Parameter.pdf'.
Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap2_gambar_parameter.py
"""
import math
from pathlib import Path

import numpy as np
import openpyxl
from gambar_teknik import BukuPDF as PdfPages

import tahap2_mutu_contoh as mc
import tahap2_parameter as tp
from gambar_teknik import Kertas
from tahap2_gambar_air_tanah import gaya_sumbu
from tahap2_gambar_geoteknik import kotak_catatan

AKAR = Path(__file__).resolve().parents[1]
FOLDER = AKAR / "02 Olah Data Tanah" / "Gambar"
PDF = AKAR / "02 Olah Data Tanah" / "2.4 Gambar Parameter.pdf"
NKT = 12
TOTAL = 2


def _sv0_profil(z):
    """σ'v0 rata-rata profil tipikal (BH-5) dengan MAT 0,7 m."""
    lap = mc.baca_lapisan()["BH-5"]
    return np.array([mc.sigma_v0(lap, zi) - tp.GW * max(0, zi - tp.MAT) for zi in z])


def gambar_lempung(pdf):
    k = Kertas()
    lab = [d for d in tp.contoh_lab().values() if d["unit"] in ("U2", "U3", "U4")]
    kon = tp.konsolidasi()
    P = tp.profil_cptu()
    b, a = np.polyfit([d["z"] for d in lab if d["unit"] == "U4" and d["dipakai"] and d.get("su_uu")],
                      [d["su_uu"] for d in lab if d["unit"] == "U4" and d["dipakai"] and d.get("su_uu")], 1)
    w, h, y0 = 47, 185, 72
    xs = [35, 89, 143, 197, 251]
    ax = [k.sumbu(x, y0, w, h) for x in xs]
    for A in ax:
        A.set_ylim(10, 0)
        A.axhspan(9.5, 10, color="#ecd98a", alpha=0.5, zorder=0)
        gaya_sumbu(A)
    ax[0].text(0.5, 9.8, "pasir U5", fontsize=5, transform=ax[0].get_yaxis_transform())
    # 1 batas Atterberg
    for d in lab:
        if not isinstance(d.get("LL"), (int, float)):
            if isinstance(d.get("w"), (int, float)) and d["w"] > 150:
                ax[0].plot(150, d["z"], ">", color="#5b3a1c", ms=4)
                ax[0].text(147, d["z"] - 0.2, f"w {d['w']:.0f}", fontsize=4.5, ha="right", color="#5b3a1c")
            continue
        pl = d["LL"] - d["PI"]
        ax[0].plot([pl, d["LL"]], [d["z"], d["z"]], color="#888", lw=0.6)
        ax[0].plot(pl, d["z"], "|", color="#333", ms=4)
        ax[0].plot(d["LL"], d["z"], "|", color="#333", ms=4)
        ax[0].plot(d["w"], d["z"], "o", ms=3, mfc="#1f5f99" if d["dipakai"] else "white", mec="#1f5f99")
    ax[0].set_xlim(0, 150)
    ax[0].set_xlabel("PL - LL (garis), w (bulat) (%)", fontsize=6)
    ax[0].set_ylabel("Kedalaman dari muka tanah (m)", fontsize=6.5)
    gaya_sumbu(ax[0], "A. Kadar air dan batas Atterberg")
    # 2 berat isi
    for d in lab:
        if isinstance(d.get("gamma"), (int, float)):
            ax[1].plot(d["gamma"], d["z"], "s", ms=3, mfc="#2e7d32" if d["unit"] == "U4" else "#5b3a1c",
                       mec="k", mew=0.3)
    ax[1].axvline(15.2, color="#2e7d32", lw=0.8, ls="--")
    ax[1].text(15.25, 0.6, "desain U4\n15,2", fontsize=5, color="#2e7d32")
    ax[1].set_xlim(10, 19)
    ax[1].set_xlabel("γ (kN/m³)", fontsize=6)
    gaya_sumbu(ax[1], "B. Berat isi")
    # 3 su
    for n, p in P.items():
        m = (p["unit"] == "U4") & ~((n == "CPTu-4") & (p["z"] <= 4.5))
        su = np.where(m, p["qnet"] / NKT, np.nan)
        ax[2].plot(su, p["z"], color="#bbbbbb", lw=0.4)
    for d in lab:
        if d.get("su_uu"):
            ax[2].plot(d["su_uu"], d["z"], "o", ms=3.2, mfc="#c0392b" if d["dipakai"] else "white", mec="#c0392b",
                       zorder=5)
    zz = np.linspace(1.6, 9.5, 20)
    sd = tp_su_sd()
    ax[2].plot(a + b * zz, zz, color="#c0392b", lw=1.0, label=f"regresi UU: {a:.1f} + {b:.2f} z".replace(".", ","))
    ax[2].plot(a - 0.5 * sd + b * zz, zz, color="#c0392b", lw=1.2, ls="--",
               label=f"desain: {a - 0.5 * sd:.1f} + {b:.2f} z".replace(".", ","))
    ax[2].plot([], [], color="#bbbbbb", lw=0.8, label=f"CPTu-1 s.d. 8: (qt - σv0)/{NKT}")
    ax[2].set_xlim(0, 45)
    ax[2].set_xlabel("su (kPa)", fontsize=6)
    ax[2].legend(fontsize=4.8, loc="lower left")
    gaya_sumbu(ax[2], "C. Kuat geser tak terdrainase")
    # 4 sigma'p
    zz = np.linspace(0.2, 9.5, 60)
    sv0 = _sv0_profil(zz)
    ax[3].plot(sv0, zz, color="k", lw=0.9, label="σ'v0 (BH-5, MAT 0,7 m)")
    pop = np.clip(18 * (8.5 - zz) / 5.5, 0, 18)
    ax[3].plot(sv0 + pop, zz, color="#7b3fa0", lw=1.2, ls="--", label="σ'p desain = σ'v0 + POP")
    for n, p in P.items():
        m = (p["unit"] == "U4") & ~((n == "CPTu-4") & (p["z"] <= 4.5))
        ax[3].plot(np.where(m, 0.33 * p["qnet"], np.nan), p["z"], color="#cccccc", lw=0.4)
    ax[3].plot([], [], color="#cccccc", lw=0.8, label="CPTu: 0,33 (qt - σv0)")
    for c in kon:
        if c["unit"] not in ("U2", "U3", "U4"):
            continue
        ax[3].plot(c["sp_lab"], c["z"], "^", ms=3.5, mfc="white", mec="#7b3fa0", zorder=5)
        ax[3].plot(c["sp_bil"], c["z"], "o", ms=3.5, mfc="#7b3fa0" if c["dipakai"] else "white", mec="#7b3fa0",
                   zorder=5)
    ax[3].plot([], [], "^", mfc="white", mec="#7b3fa0", label="lab (Casagrande)")
    ax[3].plot([], [], "o", color="#7b3fa0", label="bilinear (hitung ulang)")
    ax[3].annotate("BH-5 UD-1\nlab 100", (100, 2.75), (70, 1.3), fontsize=5, arrowprops=dict(arrowstyle="->", lw=0.5))
    ax[3].set_xlim(0, 120)
    ax[3].set_xlabel("Tegangan (kPa)", fontsize=6)
    ax[3].legend(fontsize=4.8, loc="lower left")
    gaya_sumbu(ax[3], "D. Tegangan prakonsolidasi")
    # 5 Cc dan CR
    for c in kon:
        if c["unit"] not in ("U2", "U3", "U4"):
            continue
        cr = c["Cc"] / (1 + c["e0"])
        ax[4].plot(cr, c["z"], "D", ms=3.5, mfc="#e67e22" if c["dipakai"] else "white", mec="#e67e22")
        ax[4].text(cr + 0.01, c["z"] + 0.1, f"Cc {c['Cc']:.2f}".replace(".", ","), fontsize=4.6)
    ax[4].axvline(0.75 / (1 + 2.05), color="#e67e22", lw=0.8, ls="--")
    ax[4].text(0.25, 9.2, "desain U4\nCc 0,75; e0 2,05", fontsize=5, color="#e67e22")
    ax[4].set_xlim(0, 0.6)
    ax[4].set_xlabel("CR = Cc / (1 + e0)", fontsize=6)
    gaya_sumbu(ax[4], "E. Rasio pemampatan")
    k.teks(35, 275, "PROFIL PARAMETER LEMPUNG LUNAK (U2-U4)", fontsize=11, fontweight="bold")
    k.teks(35, 270, "Semua bor gedung BH-1 s.d. BH-8; simbol kosong = contoh tidak dipakai (BH-2 UD-2, BH-7 UD-3)",
           fontsize=6.5)
    kotak_catatan(k, 287, "CATATAN", [
        f"su CPTu = (qt - σv0)/Nkt, Nkt = {NKT} dari kalibrasi terhadap UU (median 12,2; GEC 5 Pers. 7.13 hal. 7-36).",
        "Garis desain su = regresi UU dikurangi 0,5 simpangan baku residu [Literatur: Schneider 1999].",
        "σ'p bilinear = perpotongan dua garis e-log σ' (dihitung ulang); σ'p lab BH-5 UD-1 (100 kPa) tidak dipakai.",
        "σ'p CPTu = 0,33 (qt - σv0) (GEC 5 Gambar 6-23 hal. 6-29) 25-35 % di atas lab di 5-9 m; lab dipakai.",
        "Lapisan atas U4 sedikit terkonsolidasi lebih (POP ±18 kPa di 3 m), bagian bawah hampir NC.",
        "γ BH-3 di laporan lama tidak dipakai (tertulis < γw); kadar air gambut 230-424 % ditunjukkan dengan panah.",
    ], 80)
    k.etiket("Profil parameter lempung lunak", "GT-09", "Tanpa skala", f"1 / {TOTAL}")
    k.simpan(pdf, FOLDER / "GT-09 Profil Parameter Lempung.png")


def tp_su_sd():
    lab = tp.contoh_lab()
    d4 = [x for x in lab.values() if x["unit"] == "U4" and x["dipakai"] and x.get("su_uu")]
    z = np.array([x["z"] for x in d4])
    s = np.array([x["su_uu"] for x in d4])
    b, a = np.polyfit(z, s, 1)
    return float(np.std(s - (a + b * z), ddof=2))


def gambar_pasir(pdf):
    k = Kertas()
    spt = tp.spt_pasir()
    ax1 = k.sumbu(35, 125, 70, 135)
    ax2 = k.sumbu(115, 125, 70, 135)
    warna = {"U5": "#c9a227", "U7": "#8d5a2b"}
    for x in spt:
        mk = "^" if x["tolak"] else "o"
        ax1.plot(x["n160"], x["z"], mk, ms=3, mfc=warna[x["unit"]] if not x["tolak"] else "white",
                 mec=warna[x["unit"]])
        ax2.plot(x["phi"], x["z"], mk, ms=3, mfc=warna[x["unit"]] if not x["tolak"] else "white",
                 mec=warna[x["unit"]])
    for A in (ax1, ax2):
        A.set_ylim(42, 8)
        A.axhspan(18.5, 33.3, color="#7f9cb5", alpha=0.15)
        A.text(0.02, 26, "lempung kaku U6", fontsize=5.5, transform=A.get_yaxis_transform())
        gaya_sumbu(A)
    ax1.axvline(12, color=warna["U5"], lw=0.8, ls="--")
    ax2.axvline(33, color=warna["U5"], lw=0.8, ls="--")
    ax2.axvline(38, color=warna["U7"], lw=0.8, ls="--")
    ax2.text(33.2, 9.5, "desain U5 33°", fontsize=5.5, color=warna["U5"])
    ax2.text(38.2, 36, "desain U7 38°", fontsize=5.5, color=warna["U7"])
    for bor, z, phi, c in tp.geser_langsung_lama():
        ax2.plot(phi, z + 0.225, "x", color="k", ms=4)
    ax2.plot([], [], "x", color="k", label="geser langsung lama (dibentuk ulang)")
    ax2.plot([], [], "o", color=warna["U5"], label="U5 SPT")
    ax2.plot([], [], "o", color=warna["U7"], label="U7 SPT")
    ax2.plot([], [], "^", mfc="white", mec="k", label="penolakan (batas bawah)")
    ax2.legend(fontsize=5, loc="lower left")
    ax1.set_xlabel("(N1)60", fontsize=6)
    ax1.set_ylabel("Kedalaman (m)", fontsize=6.5)
    ax2.set_xlabel("φ' Hatanaka-Uchida (°)", fontsize=6)
    ax1.set_xlim(0, 60)
    ax2.set_xlim(25, 50)
    gaya_sumbu(ax1, "A. (N1)60 pasir U5 dan U7")
    gaya_sumbu(ax2, "B. Sudut geser efektif dari SPT")
    # CU
    ax3 = k.sumbu(205, 160, 90, 100)
    wcu = {"U3": "#5b3a1c", "U4": "#2e7d32", "U6": "#1f5f99"}
    for c in tp.triaksial_cu():
        p = np.array([x[0] for x in c["pq"]])
        q = np.array([x[1] for x in c["pq"]])
        ax3.plot(p, q, "o", ms=3.5, color=wcu[c["unit"]])
        pp = np.linspace(0, p.max() * 1.1, 10)
        if c["unit"] == "U6":
            s_ = math.sin(math.radians(c["phi"]))
            lab = f"{c['titik']} {c['contoh']} ({c['unit']}): c' {c['c']:.0f} kPa, φ' {c['phi']:.0f}°"
            ax3.plot(pp, c["c"] * math.cos(math.radians(c["phi"])) + s_ * pp, color=wcu[c["unit"]], lw=0.8,
                     label=lab)
        else:
            lab = f"{c['titik']} {c['contoh']} ({c['unit']}): φ' {c['phi_c0']:.0f}° (c' = 0)"
            ax3.plot(pp, math.sin(math.radians(c["phi_c0"])) * pp, color=wcu[c["unit"]], lw=0.8,
                     ls=["-", "--", ":"][hash(c["contoh"]) % 3] if c["unit"] == "U4" else "-", label=lab)
    ax3.set_xlim(0, 420)
    ax3.legend(fontsize=5, loc="upper left")
    ax3.set_xlabel("p' = (σ'1 + σ'3)/2 (kPa)", fontsize=6)
    ax3.set_ylabel("q = (σ1 - σ3)/2 (kPa)", fontsize=6)
    gaya_sumbu(ax3, "C. Triaksial CU: lintasan runtuh")
    # Disipasi
    ax4 = k.sumbu(205, 45, 90, 90)
    ws = openpyxl.load_workbook(tp.BARU / "CPTu.xlsx", data_only=True)["Disipasi Data"]
    data = {}
    for r in ws.iter_rows(values_only=True):
        isi = [x for x in r if x is not None]
        if len(isi) == 4 and str(isi[0]).startswith("CPTu"):
            data.setdefault((isi[0], isi[1]), []).append((isi[2], isi[3]))
    for (n, z), v in data.items():
        u0 = tp.GW * (z - tp.MAT)
        v = sorted(v)
        ui = v[0][1]
        if abs(ui - u0) < 20:
            continue
        ax4.semilogx([t for t, _ in v if t > 0], [(u - u0) / (ui - u0) for t, u in v if t > 0], lw=0.9,
                     label=f"{n} {z:g} m".replace(".", ","))
    ax4.axhline(0.5, color="k", lw=0.5, ls=":")
    ax4.set_ylim(-0.4, 1.1)
    ax4.set_xlabel("Waktu (menit)", fontsize=6)
    ax4.set_ylabel("Un = (u - u0)/(ui - u0)", fontsize=6)
    ax4.legend(fontsize=4.8, loc="lower left")
    gaya_sumbu(ax4, "D. Uji disipasi CPTu (u0 hidrostatik)")
    k.teks(35, 275, "PARAMETER PASIR DAN KUAT GESER EFEKTIF", fontsize=11, fontweight="bold")
    k.teks(35, 270, "(N1)60 = CN N60; CN = 0,77 log(20/po) (FHWA NHI-06-088 Pers. 3-3); φ' = √(15,4 (N1)60) + 20 "
           "(GEC 5 Pers. 7.23)", fontsize=6.5)
    kotak_catatan(k, 287, "CATATAN", [
        "U5: (N1)60 13,9 ± 3,0 dan φ' 34,5 ± 1,6° (korelasi pasir bersih); butir halus median 9 %, desain 33°.",
        "U7: sebagian besar uji penolakan; nilai yang tergambar batas bawah. φ' desain dibatasi 38° [Asumsi].",
        "Geser langsung laporan lama (contoh dibentuk ulang, kepadatan tidak terjaga) 27,6-29,1° = batas bawah.",
        "CU: lempung lunak U4 φ' 22-27° (c' = 0); lempung kaku U6 c' 18 kPa, φ' 22°; gambut U3 φ' 39° (serat).",
        "Disipasi: CPTu-5 9 m berhenti di Un 0,34 (t50 ±76 menit, bukan 45); CPTu-8 24 m berhenti di Un 0,54 "
        "(t50 tidak bisa ditentukan). CPTu-2 5 m berakhir di bawah u0 hidrostatik.",
    ], 80)
    k.etiket("Parameter pasir dan kuat geser efektif", "GT-10", "Tanpa skala", f"2 / {TOTAL}")
    k.simpan(pdf, FOLDER / "GT-10 Parameter Pasir dan CU.png")


def buat():
    FOLDER.mkdir(parents=True, exist_ok=True)
    with PdfPages(PDF) as pdf:
        gambar_lempung(pdf)
        gambar_pasir(pdf)
        pdf.infodict()["Title"] = "2.4 Gambar Parameter - RS Tepian Batanghari (data simulasi)"
    return PDF


if __name__ == "__main__":
    print(buat())
