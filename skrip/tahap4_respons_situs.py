"""Tahap 4 langkah 4.1: analisis respons spesifik-situs kelas SF dan spektrum desain.

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (20 Nov 2026); draf, menunggu persetujuan
Defsa; disetujui Defsa 20 Nov 2026 dengan opsi (a). Kunci jawaban tidak dibuka.

Acuan SNI 1726:2019 (halaman cetak):
- Pasal 5.3.1 hal. 30: SF bila tanah mudah likuifaksi -> analisis respons spesifik-situs.
- Tabel 5 hal. 29: SB batuan v̄s 750-1.500 m/s. Tabel 6-7 hal. 34-35: Fa, Fv.
- Pasal 6.10.1.1 hal. 40: MCER batuan kelas situs SB, minimal 5 rekaman/simulasi.
- Pasal 6.10.1.2 hal. 41: Vs diukur langsung (downhole); kurva nonlinier dari korelasi terpublikasi; ketidakpastian.
- Pasal 6.10.1.3 hal. 41: MCER permukaan >= MCER batuan × rata-rata rasio spektrum permukaan/batuan; kepekaan sifat
  tanah, kedalaman model, dan gerak masukan.
- Pasal 6.10.3 hal. 43: Sa = 2/3 SaM; SF: tidak kurang dari 80 % Sa kelas SE (Pasal 6.4); struktur juga didesain
  untuk anggapan tidak terjadi likuifaksi.
- Pasal 6.10.4 hal. 43: SDS = 90 % Sa maks pada 0,2-5 s; SD1 = maks T·Sa pada 1-5 s (Vs30 <= 360 m/s); SMS, SM1
  = 1,5 × SDS, SD1; tidak kurang dari 80 % nilai Pasal 6.2-6.3.

Data: Vs downhole BH-9 terkoreksi (4.0, tahap4_telaah), profil per zona gambut (LA.1, tahap3_pondasi), parameter 2.4
(γ, PI), rekaman sintetis (tahap4_rekaman). Kurva G/Gmax dan redaman Darendeli (2001) [Literatur].
Cara 1: pystrata ekivalen-linear. Cara 2 (cek silang): openseespy 1D nonlinier tegangan total (tahap4_kolom_ops).
"""
from __future__ import annotations

import csv
import functools
import sys
from pathlib import Path

import numpy as np
import pystrata

sys.path.insert(0, str(Path(__file__).parent))
import tahap3_pondasi as pd3  # noqa: E402
import tahap4_rekaman as rk  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "04 Struktur Atas"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
STATUS = "disetujui Defsa 20 Nov 2026 (opsi a)"

HALAMAN = 12.05                 # elevasi halaman akhir (3.3)
MAT = 0.7                       # m di bawah muka tanah asli (2.3)
K0 = 0.5                        # [Asumsi] untuk tegangan rata-rata
GW = 9.81

# Vs per unit [m/s]: downhole BH-9 terkoreksi (lembar Olah Downhole), kecuali yang diberi label
VS_U4 = [(3.0, 73.0), (6.0, 91.0), (99.0, 106.0)]       # kedalaman dari muka tanah asli: <3, 3-6, >6 m
VS_U5 = [(14.0, 206.0), (99.0, 225.0)]
VS_U6 = [(24.0, 235.0), (30.0, 262.0), (99.0, 294.0)]
SIFAT = {  # unit: (γ kN/m³, PI %, OCR, Vs atau None bila menurut kedalaman, sumber Vs)
    "U0": (18.0, 15, 1.0, 150.0, "[Asumsi] urugan dipadatkan"),
    "U1": (17.0, 20, 1.0, 120.0, "MASW 2.5 lapisan teratas 130"),
    "U2": (17.8, 38, 3.0, 120.0, "MASW 2.5; PI 2.4"),
    "U3": (10.7, 150, 1.0, 70.0, "MASW 2.5 (75); PI 150 sebagai pengganti kurva gambut [Asumsi]"),
    "U4": (15.2, 50, 1.2, None, "downhole BH-9 1-10 m; PI 2.4"),
    "U5": (19.0, 0, 1.0, None, "downhole BH-9 10-19 m"),
    "U6": (19.1, 31, 2.5, None, "downhole BH-9 19-34 m; PI dan OCR 2.4"),
    "U7": (20.0, 0, 1.0, 405.0, "downhole BH-9 34-56 m (terkoreksi)"),
    "U8": (21.0, 20, 1.0, 493.0, "downhole BH-9 56-70 m"),
    "U9": (21.5, 15, 1.0, 599.0, "downhole BH-9 70-80 m, diperpanjang"),
}
BATAS_U7_U8 = 54.86             # log BH-9
BATAS_U8_U9 = 71.36
DALAM_KERAS = 85.0              # m, rata-rata sumur dataran banjir SB-1..SB-3 (telaah V-6)
VS_BATUAN = 750.0               # m/s, batas bawah SB (Tabel 5) [Asumsi]
REDAMAN_BATUAN = 0.01
FAKTOR_LIK = 0.4                # Vs U5 terdegradasi = 0,4 Vs (G 16 %) [Asumsi]
ZONA = ("SELATAN", "TENGAH", "UTARA")
FREK = np.logspace(np.log10(0.1), np.log10(50.0), 160)
PER = 1.0 / FREK

# spektrum SE sementara (3.6) untuk batas bawah 80 %
SDS_SE, SD1_SE = 0.482, 0.524
TL = 20.0                       # [Asumsi; tidak berpengaruh sampai 5 s]


def vs_menurut(tabel, z):
    for bawah, v in tabel:
        if z < bawah:
            return v
    return tabel[-1][1]


def lapisan_zona(zona="SELATAN", dalam_keras=DALAM_KERAS, faktor_u5=1.0, maks=2.0):
    """Daftar sublapisan (unit, tebal, Vs, γ, PI, OCR, z tengah dari halaman, z dari muka tanah asli)."""
    prof = pd3.PROFIL[zona]
    tebal_urug = HALAMAN - prof["elev"]
    batas = [("U0", -tebal_urug, 0.0)]
    atas = 0.0
    for unit, bawah, *_ in prof["lapisan"]:
        if unit == "U7":
            batas.append(("U7", atas, BATAS_U7_U8))
            break
        batas.append((unit, atas, bawah))
        atas = bawah
    batas += [("U8", BATAS_U7_U8, BATAS_U8_U9), ("U9", BATAS_U8_U9, dalam_keras)]
    hasil = []
    for unit, a, b in batas:
        n = max(1, int(np.ceil((b - a) / maks)))
        for i in range(n):
            z0, z1 = a + (b - a) * i / n, a + (b - a) * (i + 1) / n
            zt = 0.5 * (z0 + z1)
            g, pi, ocr, vs, _ = SIFAT[unit]
            if vs is None:
                vs = vs_menurut({"U4": VS_U4, "U5": VS_U5, "U6": VS_U6}[unit], zt)
            if unit == "U5":
                vs *= faktor_u5
            hasil.append((unit, z1 - z0, vs, g, pi, ocr, zt + tebal_urug, zt))
    return hasil


def tegangan_rata(lap):
    """σ'm (kPa) di tengah tiap sublapisan; MAT 0,7 m di bawah muka tanah asli."""
    out, sv, u_atas = [], 0.0, 0.0
    for unit, h, vs, g, *_ , zasli in lap:
        sv_t = sv + g * h / 2
        u = max(0.0, (zasli - MAT)) * GW
        out.append(max(5.0, (sv_t - u) * (1 + 2 * K0) / 3))
        sv += g * h
    return out


def profil(zona="SELATAN", dalam_keras=DALAM_KERAS, vs_batuan=VS_BATUAN, faktor_u5=1.0):
    lap = lapisan_zona(zona, dalam_keras, faktor_u5)
    sm = tegangan_rata(lap)
    layers = []
    for (unit, h, vs, g, pi, ocr, *_), s in zip(lap, sm):
        st = pystrata.site.DarendeliSoilType(unit_wt=g, plas_index=pi, ocr=ocr, stress_mean=s)
        layers.append(pystrata.site.Layer(st, h, vs))
    batuan = pystrata.site.SoilType("batuan SB", 22.0, None, REDAMAN_BATUAN)
    layers.append(pystrata.site.Layer(batuan, 0, vs_batuan))
    return pystrata.site.Profile(layers)


@functools.lru_cache(maxsize=None)
def gerak():
    out = []
    for i in range(1, rk.JUMLAH + 1):
        a = np.loadtxt(rk.FOLDER / f"SIN-{i:02d}.csv", delimiter=",", skiprows=2)[:, 1]
        out.append(pystrata.motion.TimeSeriesMotion(f"SIN-{i:02d}", "sintetis", rk.DT, a))
    return out


def jalankan(zona="SELATAN", dalam_keras=DALAM_KERAS, vs_batuan=VS_BATUAN, faktor_u5=1.0, motions=None):
    """Rasio spektrum permukaan/batuan singkapan per rekaman, regangan maks, PGA permukaan."""
    p = profil(zona, dalam_keras, vs_batuan, faktor_u5)
    calc = pystrata.propagation.EquivalentLinearCalculator(strain_ratio=0.65)
    loc_in = p.location("outcrop", index=-1)
    outs = pystrata.output.OutputCollection([
        pystrata.output.ResponseSpectrumOutput(FREK, pystrata.output.OutputLocation("outcrop", index=-1), 0.05),
        pystrata.output.ResponseSpectrumOutput(FREK, pystrata.output.OutputLocation("outcrop", index=0), 0.05),
    ])
    rasio, regangan, pga, sa_perm = [], [], [], []
    for m in motions or gerak():
        calc(m, p, loc_in)
        outs(calc)
        sb, sp = np.ravel(outs[0].values), np.ravel(outs[1].values)
        rasio.append(sp / sb)
        sa_perm.append(sp)
        regangan.append(max(float(np.max(l.strain)) if np.ndim(l.strain) else float(l.strain) for l in p[:-1]))
        pga.append(float(sp[np.argmax(FREK)]))
        outs.reset()
    return {"rasio": np.array(rasio), "sa": np.array(sa_perm), "regangan": regangan, "pga": pga}


def periode_situs(zona="SELATAN", dalam_keras=DALAM_KERAS, vs_batuan=VS_BATUAN, faktor_u5=1.0):
    """(a) 4 Σh/Vs; (b) puncak pertama fungsi transfer linear (regangan kecil) permukaan/singkapan batuan."""
    lap = lapisan_zona(zona, dalam_keras, faktor_u5)
    t4 = 4 * sum(h / vs for _, h, vs, *_ in lap)
    p = profil(zona, dalam_keras, vs_batuan, faktor_u5)
    calc = pystrata.propagation.LinearElasticCalculator()
    m = gerak()[0]
    calc(m, p, p.location("outcrop", index=-1))
    f = m.freqs
    tf = np.abs(calc.calc_accel_tf(p.location("outcrop", index=-1), p.location("outcrop", index=0)))
    sel = (f > 0.2) & (f < 5.0)
    fs, ts = f[sel], tf[sel]
    # puncak lokal pertama
    for i in range(1, len(ts) - 1):
        if ts[i] > ts[i - 1] and ts[i] >= ts[i + 1] and ts[i] > 1.5:
            return t4, 1.0 / fs[i], fs, ts
    return t4, 1.0 / fs[np.argmax(ts)], fs, ts


# ------------------------------------------------------------------ spektrum
def sa_se(t):
    """Spektrum desain kelas SE (3.6, Pasal 6.4)."""
    t = np.asarray(t, dtype=float)
    t0, ts = 0.2 * SD1_SE / SDS_SE, SD1_SE / SDS_SE
    sa = np.where(t < t0, SDS_SE * (0.4 + 0.6 * t / t0), SDS_SE)
    sa = np.where(t > ts, SD1_SE / np.maximum(t, 1e-9), sa)
    return np.where(t > TL, SD1_SE * TL / np.maximum(t, 1e-9) ** 2, sa)


def parameter_desain(per, sa):
    """Pasal 6.10.4: SDS = 0,9 max Sa (0,2-5 s); SD1 = max T·Sa (1-5 s, Vs30 <= 360)."""
    m1 = (per >= 0.2) & (per <= 5.0)
    m2 = (per >= 1.0) & (per <= 5.0)
    sds = 0.9 * float(np.max(sa[m1]))
    sd1 = float(np.max(per[m2] * sa[m2]))
    return sds, sd1


@functools.lru_cache(maxsize=None)
def semua_kasus():
    kasus = {}
    for z in ZONA:
        for nama, fu in (("utuh", 1.0), ("terdegradasi", FAKTOR_LIK)):
            kasus[(z, nama, DALAM_KERAS, VS_BATUAN)] = jalankan(z, faktor_u5=fu)
    for dk in (79.0, 93.0):
        for nama, fu in (("utuh", 1.0), ("terdegradasi", FAKTOR_LIK)):
            kasus[("SELATAN", nama, dk, VS_BATUAN)] = jalankan("SELATAN", dk, faktor_u5=fu)
    for nama, fu in (("utuh", 1.0), ("terdegradasi", FAKTOR_LIK)):
        kasus[("SELATAN", nama, DALAM_KERAS, 1000.0)] = jalankan("SELATAN", vs_batuan=1000.0, faktor_u5=fu)
    return kasus


def spektrum_desain():
    """Selubung rata-rata rasio semua kasus × MCER batuan -> SaM; Sa = 2/3 SaM; batas 80 % SE.

    Dua selubung: (A) semua kasus (U5 utuh dan terdegradasi), (B) anggapan tidak terjadi likuifaksi (U5 utuh saja,
    Pasal 6.10.3 alinea terakhir). Spektrum desain = selubung A dan B (A sudah mencakup B).
    """
    kasus = semua_kasus()
    rata = {k: v["rasio"].mean(axis=0) for k, v in kasus.items()}
    sel_semua = np.max(np.array(list(rata.values())), axis=0)
    sel_utuh = np.max(np.array([v for k, v in rata.items() if k[1] == "utuh"]), axis=0)
    sam = rk.sa_target(PER) * sel_semua
    sa_situs = 2.0 / 3.0 * sam
    batas = 0.8 * sa_se(PER)
    sa = np.maximum(sa_situs, batas)
    sds, sd1 = parameter_desain(PER, sa)
    sds = max(sds, 0.8 * SDS_SE)
    sd1 = max(sd1, 0.8 * SD1_SE)
    return {"per": PER, "rata": rata, "sel_semua": sel_semua, "sel_utuh": sel_utuh, "sam": sam,
            "sa_situs": sa_situs, "batas": batas, "sa": sa, "SDS": sds, "SD1": sd1,
            "SMS": 1.5 * sds, "SM1": 1.5 * sd1}


def kds(sds, sd1):
    """Tabel 8 dan 9 SNI 1726:2019 hal. 37, kolom kategori risiko IV: A / C / D / D."""
    a = "A" if sds < 0.167 else "C" if sds < 0.33 else "D"
    b = "A" if sd1 < 0.067 else "C" if sd1 < 0.133 else "D"
    return max(a, b)


def simpan_csv(hasil, berkas=KELUAR / "4.1 Spektrum Desain Spesifik Situs.csv"):
    with open(berkas, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([f"# {LABEL} Disusun AI atas permintaan Defsa; {STATUS}. Redaman 5 %."])
        w.writerow(["T (s)", "Sa MCER batuan SB (g)", "Rasio selubung", "SaM situs (g)", "2/3 SaM (g)",
                    "80 % SE (g)", "Sa desain (g)", "Sa SE sementara (g)"])
        for i in np.argsort(hasil["per"]):
            t = hasil["per"][i]
            w.writerow([f"{t:.4f}", f"{rk.sa_target(t):.4f}", f"{hasil['sel_semua'][i]:.3f}", f"{hasil['sam'][i]:.4f}",
                        f"{hasil['sa_situs'][i]:.4f}", f"{hasil['batas'][i]:.4f}", f"{hasil['sa'][i]:.4f}",
                        f"{sa_se(t):.4f}"])
    return berkas


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    import time
    t0 = time.time()
    h = spektrum_desain()
    print(f"waktu {time.time() - t0:.0f} s")
    for k, v in semua_kasus().items():
        r = h["rata"][k]
        i = np.argmax(r)
        print(k, f"rasio maks {r[i]:.2f} di T {PER[i]:.2f} s; PGA perm {np.mean(v['pga']):.3f} g; "
                 f"regangan maks {max(v['regangan']) * 100:.2f} %")
    print(f"SDS {h['SDS']:.3f} SD1 {h['SD1']:.3f} SMS {h['SMS']:.3f} SM1 {h['SM1']:.3f} KDS {kds(h['SDS'], h['SD1'])}")
    for z in ZONA:
        t4, tf, *_ = periode_situs(z)
        print(z, f"4Σh/Vs {t4:.2f} s; fungsi transfer puncak pertama {tf:.2f} s")
    print(simpan_csv(h))
    if "--lengkap" in sys.argv:
        print(buat_excel(ops=cek_silang_ops()))
        print(gambar())


# ------------------------------------------------------------------ HVSR (cek silang periode situs)
HVSR_DIPAKAI = ("H-1", "H-2", "H-3", "H-5")   # H-4 dikeluarkan (telaah V-4)
BERKAS_VS = AKAR / "01 Penyelidikan Tanah" / "Penyelidikan Tambahan" / "Geofisika Vs Dalam.xlsx"


def hvsr_puncak_pertama(berkas=BERKAS_VS):
    """Puncak lokal pertama (> 1 Hz, H/V > 2) tiap kurva HVSR bila lebih rendah dari puncak tertinggi; None bila
    kurva hanya punya bahu (puncak tertinggi = lapisan U4)."""
    import openpyxl
    ws = openpyxl.load_workbook(berkas, data_only=True)["HVSR Kurva"]
    rows = [[x for x in r if x is not None] for r in ws.iter_rows(values_only=True)]
    a = np.array([r for r in rows if len(r) == 11 and all(isinstance(x, (int, float)) for x in r)], dtype=float)
    f = a[:, 0]
    hasil = {}
    for k, n in enumerate(("H-1", "H-2", "H-3", "H-4", "H-5")):
        h = a[:, 1 + 2 * k]
        pk = [f[i] for i in range(1, len(f) - 1) if h[i] > h[i - 1] and h[i] >= h[i + 1] and h[i] > 2 and f[i] > 1]
        tertinggi = f[np.argmax(h)]
        hasil[n] = pk[0] if pk and pk[0] < 0.8 * tertinggi else None
    return hasil


# ------------------------------------------------------------------ cek silang openseespy (T-66)
REKAMAN_OPS = (1, 4)
RENTANG_OPS = (0.5, 2.0)


def cek_silang_ops():
    """Rasio rata-rata 2 rekaman pada T 0,5-2,0 s: pystrata EL vs openseespy nonlinier (SELATAN, U5 utuh)."""
    import tahap4_kolom_ops as ko
    m = (PER >= RENTANG_OPS[0]) & (PER <= RENTANG_OPS[1])
    mot = [gerak()[i - 1] for i in REKAMAN_OPS]
    el = jalankan("SELATAN", motions=mot)["rasio"].mean(axis=0)
    nl = np.mean([ko.rasio(i)[0] for i in REKAMAN_OPS], axis=0)
    a, b = float(np.mean(el[m])), float(np.mean(nl[m]))
    return {"el": a, "nl": b, "selisih": (b - a) / a, "el_kurva": el, "nl_kurva": nl}


# ------------------------------------------------------------------ Excel
def buat_excel(keluar=KELUAR / "4.1 Respons Spesifik Situs.xlsx", ops=None):
    import openpyxl
    from format_dokumen import AI, Lembar, set_font_bawaan

    h = spektrum_desain()
    kasus = semua_kasus()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    label_ai = f"DIISI AI ATAS PERMINTAAN DEFSA (20 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk analisis respons spesifik-situs (4.1)", [6, 120])
    lb.catatan(LABEL + " " + label_ai)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, x] for i, x in enumerate([
        "Dasar: SNI 1726:2019 Pasal 5.3.1 hal. 30 (SF karena pasir U5 mudah likuifaksi), Pasal 6.10.1 hal. 40-41 "
        "(gerak batuan SB, model situs, rasio spektrum), Pasal 6.10.3 hal. 43 (Sa = 2/3 SaM, tidak kurang dari 80 % "
        "Sa kelas SE; desain juga untuk anggapan tanpa likuifaksi), Pasal 6.10.4 hal. 43 (SDS, SD1).",
        "Gerak masukan: 7 rekaman sintetis SIN-01..07 dicocokkan ke MCER batuan SB (SMS 0,301 g, SM1 0,211 g; T-65), "
        "sebagai singkapan batuan pada dasar model.",
        "Model tanah: urugan sampai halaman +12,05, profil per zona gambut (LA.1), Vs downhole BH-9 terkoreksi (4.0, "
        "telaah V-1), lapisan keras 85 m (V-6), setengah ruang Vs 750 m/s [Asumsi, batas bawah SB Tabel 5 hal. 29], "
        "kurva Darendeli (2001) [Literatur] dengan PI dan OCR dari 2.4.",
        "Kasus: 3 zona × U5 utuh / terdegradasi (Vs × 0,4 [Asumsi]); kepekaan kedalaman keras 79/93 m dan Vs batuan "
        "1.000 m/s (zona selatan). Spektrum desain memakai selubung rata-rata rasio semua kasus.",
        "Cara 1: pystrata ekivalen-linear (skrip/tahap4_respons_situs.py). Cara 2: openseespy 1D nonlinier tegangan "
        "total (skrip/tahap4_kolom_ops.py), cek silang T-66; periode situs dicek ke HVSR (T-67).",
        "Lembar Spektrum Desain dan Parameter Desain memakai rumus Excel (2/3 SaM, batas 80 % SE, Pasal 6.10.4) yang "
        "dicocokkan dengan Python. Rasio selubung adalah keluaran pystrata (nilai tetap).",
        "Status: " + STATUS + ".",
    ])], rata=list("cl"))

    # 2 Profil
    lb = Lembar(wb.create_sheet("Profil"), 2, "Profil Vs per zona (dari halaman +12,05)",
                [12, 8, 11, 11, 11, 10, 8, 8, 52])
    lb.catatan(LABEL + " Kedalaman dari halaman +12,05. Sublapisan ≤ 2 m digabung per unit dan Vs.")
    baris = []
    for z in ZONA:
        gab = []
        for unit, hh, vs, g, pi, ocr, zt, _ in lapisan_zona(z):
            if gab and gab[-1][1] == unit and abs(gab[-1][4] - vs) < 1e-9:
                gab[-1][3] += hh
            else:
                atas = (gab[-1][2] + gab[-1][3]) if gab else 0.0
                gab.append([z, unit, atas, hh, vs, g, pi, ocr])
        for zz, unit, atas, hh, vs, g, pi, ocr in gab:
            baris.append([zz, unit, round(atas, 2), round(atas + hh, 2), round(vs), g, pi, ocr, SIFAT[unit][4]])
        baris.append([z, "batuan", round(gab[-1][2] + gab[-1][3], 2), "-", VS_BATUAN, 22.0, "-", "-",
                      "setengah ruang, redaman 1 % [Asumsi]"])
    lb.tabel(["Zona", "Unit", "Dari (m)", "Sampai (m)", "Vs (m/s)", "γ (kN/m³)", "PI (%)", "OCR", "Sumber"],
             baris, rata=list("cccccccc") + ["l"], fmt=[None, None, "0.00", "0.00", "0", "0.0", None, None, None],
             fill=AI)

    # 3 Kasus
    lb = Lembar(wb.create_sheet("Kasus"), 3, "Kasus analisis dan hasil (rata-rata 7 rekaman)",
                [14, 15, 12, 12, 12, 12, 13, 13, 14])
    lb.catatan(LABEL + " Rasio = Sa permukaan / Sa singkapan batuan (redaman 5 %), rata-rata 7 rekaman per periode.")
    baris = []
    for kk, v in kasus.items():
        r = h["rata"][kk]
        i = int(np.argmax(r))
        baris.append([kk[0], kk[1], kk[2], kk[3], round(float(r[i]), 2), round(float(PER[i]), 2),
                      round(float(np.mean(v["pga"])), 3), round(max(v["regangan"]) * 100, 2),
                      "dasar" if (kk[2], kk[3]) == (DALAM_KERAS, VS_BATUAN) else "kepekaan"])
    lb.tabel(["Zona", "U5", "Lapisan keras (m)", "Vs batuan (m/s)", "Rasio maks", "T rasio maks (s)",
              "PGA permukaan (g)", "Regangan maks (%)", "Jenis"], baris, rata=list("ccccccccc"),
             fmt=[None, None, "0", "0", "0.00", "0.00", "0.000", "0.00", None], fill=AI)
    lb.kosong()
    pt = hvsr_puncak_pertama()
    baris = []
    for z in ZONA:
        t4, tf, *_ = periode_situs(z)
        baris.append([z, round(t4, 2), round(tf, 2), round(1 / tf, 2), "fungsi transfer linear pystrata", "", "", "",
                      ""])
    for n in HVSR_DIPAKAI:
        f0 = pt[n]
        baris.append([n, "-", round(1 / f0, 2) if f0 else "-", round(f0, 2) if f0 else "-",
                      "HVSR puncak lokal pertama" if f0 else "HVSR hanya bahu (tidak dihitung)", "", "", "", ""])
    lb.tabel(["Zona / titik", "4Σh/Vs (s)", "Periode situs (s)", "Frekuensi (Hz)", "Cara", "", "", "", ""], baris,
             rata=list("ccccl") + ["l"] * 4, fmt=[None, "0.00", "0.00", "0.00", None, None, None, None, None],
             fill=AI, beku=False)
    if ops:
        lb.kosong()
        lb.tabel(["Cek silang T-66", "Rasio rata-rata T 0,5-2,0 s", "", "", "", "", "", "", ""], [
            ["pystrata EL", round(ops["el"], 3), "SELATAN, U5 utuh, SIN-01 dan SIN-04", "", "", "", "", "", ""],
            ["openseespy NL", round(ops["nl"], 3), "PressureIndependMultiYield, tegangan total", "", "", "", "", "", ""],
            ["Selisih", f"{ops['selisih'] * 100:.1f} %", "batas geoteknik 30 %", "", "", "", "", "", ""],
        ], rata=list("lcl") + ["l"] * 6, fill=AI, beku=False)

    # 4 Spektrum desain (rumus)
    lb = Lembar(wb.create_sheet("Spektrum Desain"), 4, "Spektrum desain spesifik-situs (Pasal 6.10.1.3, 6.10.3)",
                [10, 13, 12, 13, 13, 13, 13, 13, 12])
    lb.catatan(LABEL + " SaM = Sa batuan × rasio selubung (Pasal 6.10.1.3); Sa = MAX(2/3 SaM; 0,8 Sa SE) (Pasal "
               "6.10.3 alinea SF). Kolom rumus hijau dihitung Excel.")
    urut = np.argsort(PER)
    baris = [[round(float(PER[i]), 4), round(float(rk.sa_target(PER[i])), 5), round(float(h["sel_semua"][i]), 4),
              None, None, round(float(sa_se(PER[i])), 5), None, None, None] for i in urut]
    _, a, b = lb.tabel(["T (s)", "Sa batuan SB (g)", "Rasio selubung", "SaM situs (g)", "2/3 SaM (g)",
                        "Sa SE sementara (g)", "80 % SE (g)", "Sa desain (g)", "T × Sa (g·s)"], baris,
                       rata=list("ccccccccc"), fmt=["0.000", "0.0000", "0.000", "0.0000", "0.0000", "0.0000",
                                                    "0.0000", "0.0000", "0.0000"],
                       fill_kolom={3: AI, 4: AI, 6: AI, 7: AI, 8: AI})
    k = lb.kol
    for r in range(a, b + 1):
        lb.ws[f"{k(3)}{r}"] = f"={k(1)}{r}*{k(2)}{r}"
        lb.ws[f"{k(4)}{r}"] = f"=2/3*{k(3)}{r}"
        lb.ws[f"{k(6)}{r}"] = f"=0.8*{k(5)}{r}"
        lb.ws[f"{k(7)}{r}"] = f"=MAX({k(4)}{r},{k(6)}{r})"
        lb.ws[f"{k(8)}{r}"] = f"={k(0)}{r}*{k(7)}{r}"

    def rng(c):
        return f"'Spektrum Desain'!${k(c)}${a}:${k(c)}${b}"

    # 5 Parameter desain
    lb = Lembar(wb.create_sheet("Parameter Desain"), 5, "Parameter percepatan desain (Pasal 6.10.4) dan KDS",
                [34, 16, 16, 16, 56])
    lb.catatan(LABEL + " SDS = 0,9 × Sa maks pada 0,2-5 s; SD1 = maks T·Sa pada 1-5 s (Vs30 156 ≤ 360 m/s); tidak "
               "kurang dari 80 % nilai Pasal 6.3 kelas SE (0,482; 0,524). KDS dari Tabel 8-9 hal. 37 (kategori IV).")
    _, a2, _ = lb.tabel(["Parameter", "Spesifik-situs", "SE sementara (3.6)", "Perubahan", "Dasar"], [
        ["SDS (g)", f"=MAX(0.9*_xlfn.MAXIFS({rng(7)},{rng(0)},\">=0.2\",{rng(0)},\"<=5\"),0.8*{SDS_SE})", SDS_SE, None,
         "Pasal 6.10.4; batas 80 % SE menentukan"],
        ["SD1 (g)", f"=MAX(_xlfn.MAXIFS({rng(8)},{rng(0)},\">=1\",{rng(0)},\"<=5\"),0.8*{SD1_SE})", SD1_SE, None,
         "Pasal 6.10.4; spesifik-situs menentukan di T ±1,5-1,8 s"],
        ["SMS = 1,5 SDS (g)", None, round(1.5 * SDS_SE, 3), None, "Pasal 6.10.4"],
        ["SM1 = 1,5 SD1 (g)", None, round(1.5 * SD1_SE, 3), None, "Pasal 6.10.4"],
        ["Kategori desain seismik", kds(h["SDS"], h["SD1"]), "D", "tetap", "Tabel 8-9 hal. 37, kategori IV"],
    ], rata=list("lcccl"), fmt=[None, "0.000", "0.000", "0.0%", None], fill_kolom={1: AI, 3: AI}, beku=False)
    ws = lb.ws
    ws[f"{k(1)}{a2 + 2}"] = f"=1.5*{k(1)}{a2}"
    ws[f"{k(1)}{a2 + 3}"] = f"=1.5*{k(1)}{a2 + 1}"
    for r in range(a2, a2 + 4):
        ws[f"{k(3)}{r}"] = f"={k(1)}{r}/{k(2)}{r}-1"
    lb.kosong()
    lb.tabel(["No", "Catatan dan rekomendasi", "", "", ""], [[i + 1, x, "", "", ""] for i, x in enumerate([
        "Akibat: plateau spektrum desain turun dari 0,482 menjadi 0,386 g (-20 %), sehingga geser dasar gedung "
        "(T ±0,5-0,8 s, di plateau) turun ±20 % dibanding pra-dimensi 3.6; SD1 turun ±12 %.",
        "2/3 SaM berada di bawah batas 80 % SE pada hampir semua periode, kecuali T ±1,5-1,8 s (dekat resonansi "
        "kolom tanah). Batas bawah SNI yang menentukan, bukan amplifikasi situs.",
        "Keterbatasan: regangan geser ekivalen-linear 1,4-2,8 % (di atas ±1 %, batas wajar metode EL); rekaman sintetis "
        "(T-65); kurva gambut memakai pengganti PI 150; Vs U5 terdegradasi 0,4 Vs [Asumsi].",
        "Keputusan Defsa 20 Nov 2026: opsi (a), spektrum lembar 4 sesuai SNI (SDS 0,386, SD1 0,459). Pilihan lain yang "
        "tidak dipakai: (b) tetap spektrum SE 100 %. Saran AI tetap: simpangan kategori IV juga dicek dengan SE di 4.3.",
    ])], rata=list("cllll"), fill_kolom={1: AI}, beku=False)
    for r in range(lb.baris - 4, lb.baris):
        ws.merge_cells(f"{k(1)}{r}:{k(4)}{r}")
        lb._tinggi(r, ["", ws[f"{k(1)}{r}"].value], [lb.lebar[0], sum(lb.lebar[1:])], 12)
    r0 = lb.baris - 5
    ws.merge_cells(f"{k(1)}{r0}:{k(4)}{r0}")

    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


# ------------------------------------------------------------------ gambar GS-01 (CADCraft, KOP_A3)
PNG_GS01 = KELUAR / "Gambar" / "GS-01 Respons Spesifik Situs.png"
PDF_GS01 = KELUAR / "4.1 Gambar Respons Spesifik Situs.pdf"


def gambar():
    from cad_lembar import STATUS_DRAF
    from gambar_teknik import BukuPDF as PdfPages
    from gambar_teknik import Kertas
    from tahap2_gambar_air_tanah import gaya_sumbu
    from tahap2_gambar_geoteknik import kotak_catatan

    h = spektrum_desain()
    k = Kertas()
    # A. profil Vs per zona
    ax = k.sumbu(35, 70, 70, 190)
    gaya = {"SELATAN": ("k", "-"), "TENGAH": ("k", "--"), "UTARA": ("k", ":")}
    for z in ZONA:
        zz, vv, d = [], [], 0.0
        for _, hh, vs, *_ in lapisan_zona(z):
            zz += [d, d + hh]
            vv += [vs, vs]
            d += hh
        zz += [d, d + 8]
        vv += [VS_BATUAN, VS_BATUAN]
        ax.plot(vv, zz, color=gaya[z][0], ls=gaya[z][1], lw=0.9, label=f"Zona {z.lower()}")
    ax.axhline(DALAM_KERAS + 2.2, color="k", lw=0.5)
    ax.set_ylim(DALAM_KERAS + 10, 0)
    ax.set_xlim(0, 800)
    ax.set_xlabel("Vs (m/s)", fontsize=6.5)
    ax.set_ylabel("Kedalaman dari halaman +12,05 (m)", fontsize=6.5)
    ax.legend(fontsize=5.2, loc="lower left")
    gaya_sumbu(ax, "A. Profil Vs model (BH-9 terkoreksi)")
    # B. rasio spektrum
    ax2 = k.sumbu(125, 175, 175, 85)
    for kk, r in h["rata"].items():
        if (kk[2], kk[3]) != (DALAM_KERAS, VS_BATUAN):
            continue
        ax2.plot(PER, r, color="0.55", lw=0.6, ls="-" if kk[1] == "utuh" else "--")
    ax2.plot(PER, h["sel_semua"], color="k", lw=1.3, label="Selubung rata-rata semua kasus")
    ax2.plot([], [], color="0.55", lw=0.6, label="Rata-rata per zona, U5 utuh")
    ax2.plot([], [], color="0.55", lw=0.6, ls="--", label="Rata-rata per zona, U5 terdegradasi")
    ax2.axhline(1.0, color="k", lw=0.4, ls=":")
    ax2.set_xscale("log")
    ax2.set_xlim(0.05, 5)
    ax2.set_ylim(0, 3.6)
    ax2.set_xlabel("Periode T (detik)", fontsize=6.5)
    ax2.set_ylabel("Rasio Sa permukaan / batuan", fontsize=6.5)
    ax2.legend(fontsize=5.2, loc="upper left")
    gaya_sumbu(ax2, "B. Rasio spektrum respons (redaman 5 %)")
    # C. spektrum desain
    ax3 = k.sumbu(125, 70, 175, 85)
    o = np.argsort(PER)
    t = PER[o]
    ax3.plot(t, rk.sa_target(t), color="k", lw=0.6, ls=":", label="MCER batuan SB")
    ax3.plot(t, h["sa_situs"][o], color="0.45", lw=0.8, ls="--", label="2/3 SaM spesifik-situs")
    ax3.plot(t, sa_se(t), color="0.45", lw=0.8, ls="-.", label="SE sementara (3.6)")
    ax3.plot(t, h["batas"][o], color="0.45", lw=0.6, ls=":", label="80 % SE (batas bawah)")
    ax3.plot(t, h["sa"][o], color="k", lw=1.4, label="Spektrum desain usulan")
    ax3.set_xlim(0, 4)
    ax3.set_ylim(0, 0.6)
    ax3.set_xlabel("Periode T (detik)", fontsize=6.5)
    ax3.set_ylabel("Sa (g)", fontsize=6.5)
    ax3.legend(fontsize=5.2, loc="upper right")
    gaya_sumbu(ax3, "C. Spektrum respons desain")
    k.teks(35, 275, "ANALISIS RESPONS SPESIFIK-SITUS KELAS SF", fontsize=11, fontweight="bold")
    k.teks(35, 270, "SNI 1726:2019 Pasal 6.10.1-6.10.4; 7 rekaman sintetis, pystrata ekivalen-linear", fontsize=6.5)
    f = lambda v: f"{v:.3f}".replace(".", ",")  # noqa: E731
    kotak_catatan(k, 287, "CATATAN", [
        f"Usulan: SDS {f(h['SDS'])} g, SD1 {f(h['SD1'])} g, SMS {f(h['SMS'])} g, SM1 {f(h['SM1'])} g; KDS "
        f"{kds(h['SDS'], h['SD1'])} (Tabel 8-9, kategori IV).",
        "Spektrum SE sementara (3.6): SDS 0,482 g, SD1 0,524 g. Plateau turun ±20 %.",
        "2/3 SaM di bawah 80 % SE kecuali T ±1,5-1,8 s; batas bawah Pasal 6.10.3 yang menentukan.",
        "Lapisan keras 85 m, setengah ruang Vs 750 m/s [Asumsi]; kepekaan 79/93 m dan 1.000 m/s.",
        "Periode situs 0,74-0,77 s (fungsi transfer) cocok dengan HVSR 1,26-1,47 Hz (T-67).",
        "Regangan ekivalen-linear 1,4-2,8 %: keterbatasan metode; cek nonlinier openseespy (T-66).",
    ], 80)
    k.etiket("Respons spesifik-situs", "GS-01", "Tanpa skala", "1 / 1", tanggal="JULI 2027",
              status="DISETUJUI 20 NOV 2026")
    PNG_GS01.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(PDF_GS01) as pdf:
        k.simpan(pdf, PNG_GS01)
    return PDF_GS01
