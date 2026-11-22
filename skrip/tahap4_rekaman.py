"""Tahap 4 langkah 4.1: rekaman gempa sintetis batuan dasar yang dicocokkan spektrum MCER kelas situs SB.

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (20 Nov 2026): Defsa memilih rekaman
sintetis karena PEER NGA-West2 hanya menerima email kampus/perusahaan dan akun lama dinonaktifkan 2 Juli 2026.

Dasar:
- SNI 1726:2019 Pasal 6.10.1.1 (hal. 40): MCER batuan dasar dengan anggapan kelas situs SB; minimal 5 (lima)
  "rekaman atau simulasi riwayat waktu" yang diskalakan sehingga rata-rata spektrumnya mendekati MCER batuan
  pada rentang periode penting.
- Tabel 6 dan 7 (hal. 34-35): SB Fa 0,9 dan Fv 0,8. Bentuk spektrum Pasal 6.4 (hal. 35) pada taraf MCER.
- Ss 0,334 dan S1 0,264 (Desain Spektra PUPR, langkah 2.6); Mw 7,0 (deagregasi PuSGeN 2017, langkah 2.6).

Cara: derau putih Gauss x selubung Saragoni-Hart [Asumsi: durasi kuat ±20 s untuk Mw 7,0 jarak menengah],
lalu pencocokan spektrum di domain frekuensi (rasio target/hitung, iteratif) dan koreksi garis dasar.
Spektrum respons dihitung dua cara: Nigam-Jennings (eksak untuk percepatan linear per langkah) dan Newmark
percepatan rata-rata (cek silang).
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

AKAR = Path(__file__).resolve().parents[1]
FOLDER = AKAR / "04 Struktur Atas" / "Rekaman Gempa" / "sintetis"

SS, S1 = 0.334, 0.264          # g, langkah 2.6 (Desain Spektra PUPR)
FA_SB, FV_SB = 0.9, 0.8        # SNI 1726:2019 Tabel 6 dan 7, kelas SB
SMS, SM1 = FA_SB * SS, FV_SB * S1
TS = SM1 / SMS
T0 = 0.2 * TS
TL = 20.0                      # [Asumsi] tidak berpengaruh sampai 10 s

DT = 0.01                      # s
DURASI = 40.0                  # s
REDAMAN = 0.05
JUMLAH = 7
BENIH = [11, 23, 37, 41, 53, 67, 79]
T_COCOK = (0.1, 3.0)           # rentang periode pencocokan (s)
BATAS = (0.9, 1.3)             # rasio rekaman/target yang diterima per rekaman di T_COCOK [Asumsi]


def sa_target(t):
    """Spektrum MCER batuan SB (g), bentuk Pasal 6.4 tanpa faktor 2/3."""
    t = np.asarray(t, dtype=float)
    sa = np.where(t < T0, SMS * (0.4 + 0.6 * t / T0), SMS)
    sa = np.where(t > TS, SM1 / np.maximum(t, 1e-9), sa)
    sa = np.where(t > TL, SM1 * TL / np.maximum(t, 1e-9) ** 2, sa)
    return sa


def periode(n=60):
    return np.logspace(np.log10(0.05), np.log10(5.0), n)


def selubung(t, tr=3.0, tp=8.0, td=DURASI):
    """Selubung Saragoni-Hart dinormalkan puncak 1: naik sampai tr, datar ±tp, meluruh sampai td."""
    e = np.ones_like(t)
    e = np.where(t < tr, (t / tr) ** 2, e)
    turun = t > tr + tp
    e = np.where(turun, np.exp(-3.0 * (t - tr - tp) / (td - tr - tp)), e)
    return e


def spektrum_nj(acc, dt, per, zeta=REDAMAN):
    """Sa pseudo (g) dengan metode Nigam-Jennings (percepatan linear per langkah, eksak)."""
    sa = np.empty(len(per))
    for k, tn in enumerate(per):
        w = 2 * np.pi / tn
        wd = w * np.sqrt(1 - zeta ** 2)
        e = np.exp(-zeta * w * dt)
        s, c = np.sin(wd * dt), np.cos(wd * dt)
        a11 = e * (zeta / np.sqrt(1 - zeta ** 2) * s + c)
        a12 = e / wd * s
        a21 = -w / np.sqrt(1 - zeta ** 2) * e * s
        a22 = e * (c - zeta / np.sqrt(1 - zeta ** 2) * s)
        t1 = (2 * zeta ** 2 - 1) / (w ** 2 * dt)
        t2 = 2 * zeta / (w ** 3 * dt)
        b11 = e * ((t1 + zeta / w) * s / wd + (t2 + 1 / w ** 2) * c) - t2
        b12 = -e * (t1 * s / wd + t2 * c) - 1 / w ** 2 + t2
        b21 = e * ((t1 + zeta / w) * (c - zeta / np.sqrt(1 - zeta ** 2) * s)
                   - (t2 + 1 / w ** 2) * (wd * s + zeta * w * c)) + 1 / (w ** 2 * dt)
        b22 = -e * (t1 * (c - zeta / np.sqrt(1 - zeta ** 2) * s) - t2 * (wd * s + zeta * w * c)) - 1 / (w ** 2 * dt)
        u = v = 0.0
        umax = 0.0
        for i in range(len(acc) - 1):
            p0, p1 = -acc[i], -acc[i + 1]
            u, v = a11 * u + a12 * v + b11 * p0 + b12 * p1, a21 * u + a22 * v + b21 * p0 + b22 * p1
            umax = max(umax, abs(u))
        sa[k] = umax * w ** 2
    return sa


def spektrum_newmark(acc, dt, per, zeta=REDAMAN, sub=5):
    """Sa pseudo (g) dengan Newmark percepatan rata-rata (gamma 1/2, beta 1/4), cek silang.

    Langkah dibagi `sub` (percepatan diinterpolasi linear) karena Newmark dengan dt 0,01 s kurang teliti di T < 0,2 s.
    """
    if sub > 1:
        t = np.arange(len(acc)) * dt
        dt = dt / sub
        acc = np.interp(np.arange(0, t[-1] + 1e-12, dt), t, acc)
    sa = np.empty(len(per))
    for k, tn in enumerate(per):
        w = 2 * np.pi / tn
        m, c, kk = 1.0, 2 * zeta * w, w ** 2
        g, b = 0.5, 0.25
        khat = kk + g / (b * dt) * c + m / (b * dt ** 2)
        a1 = m / (b * dt) + g / b * c
        a2 = m / (2 * b) + dt * (g / (2 * b) - 1) * c
        u = v = 0.0
        a = -acc[0]
        umax = 0.0
        for i in range(len(acc) - 1):
            dp = -(acc[i + 1] - acc[i]) + a1 * v + a2 * a
            du = dp / khat
            dv = g / (b * dt) * du - g / b * v + dt * (1 - g / (2 * b)) * a
            da = du / (b * dt ** 2) - v / (b * dt) - a / (2 * b)
            u, v, a = u + du, v + dv, a + da
            umax = max(umax, abs(u))
        sa[k] = umax * w ** 2
    return sa


F_POTONG = (0.08, 0.16)        # Hz, saringan lolos-tinggi kosinus [Asumsi]; di bawah 1/3 s = 0,33 Hz


def koreksi_garis_dasar(acc, dt):
    """Saringan lolos-tinggi kosinus lalu buang tren kubik perpindahan (tanpa suku konstanta dan linear).

    Tujuannya kecepatan dan perpindahan akhir mendekati nol (rekaman dapat dipakai di analisis 1D/3D).
    """
    t = np.arange(len(acc)) * dt
    acc = acc * selubung_tepi(t)
    F = np.fft.rfft(acc)
    f = np.fft.rfftfreq(len(acc), dt)
    lo, hi = F_POTONG
    h = np.where(f <= lo, 0.0, np.where(f >= hi, 1.0, 0.5 * (1 - np.cos(np.pi * (f - lo) / (hi - lo)))))
    acc = np.fft.irfft(F * h, n=len(acc))
    for _ in range(3):
        # tren perpindahan d = c2 t^2 + c3 t^3 (d dan v awal nol), dibuang lewat percepatan 2 c2 + 6 c3 t
        d = np.cumsum(np.cumsum(acc) * dt) * dt
        c2, c3 = np.linalg.lstsq(np.column_stack([t ** 2, t ** 3]), d, rcond=None)[0]
        acc = acc - (2 * c2 + 6 * c3 * t)
    return acc


def selubung_tepi(t, lebar=1.0):
    """Taper kosinus 1 s di awal dan akhir agar rekaman mulai dan berakhir di nol."""
    e = np.ones_like(t)
    e = np.where(t < lebar, 0.5 * (1 - np.cos(np.pi * t / lebar)), e)
    e = np.where(t > t[-1] - lebar, 0.5 * (1 - np.cos(np.pi * (t[-1] - t) / lebar)), e)
    return e


def cocokkan(acc, dt, iterasi=20):
    """Pencocokan spektrum domain frekuensi: kalikan amplitudo Fourier dengan rasio target/hitung."""
    per = periode(60)
    frek = 1 / per
    for _ in range(iterasi):
        rasio = sa_target(per) / spektrum_nj(acc, dt, per)
        F = np.fft.rfft(acc)
        f = np.fft.rfftfreq(len(acc), dt)
        r = np.interp(f, frek[::-1], rasio[::-1], left=rasio[-1], right=rasio[0])
        acc = np.fft.irfft(F * r, n=len(acc))
        acc = koreksi_garis_dasar(acc, dt)
    return acc


def bangkitkan(benih, dt=DT):
    rng = np.random.default_rng(benih)
    t = np.arange(0, DURASI, dt)
    acc = rng.standard_normal(len(t)) * selubung(t)
    acc = acc / np.max(np.abs(acc)) * 0.12
    return t, cocokkan(acc, dt)


def ringkas(acc, dt):
    per = periode()
    sa = spektrum_nj(acc, dt, per)
    m = (per >= T_COCOK[0]) & (per <= T_COCOK[1])
    r = sa[m] / sa_target(per[m])
    v = np.cumsum(acc) * dt * 9.81
    d = np.cumsum(v) * dt
    ia = np.cumsum(acc ** 2) * dt
    i5, i95 = np.searchsorted(ia, 0.05 * ia[-1]), np.searchsorted(ia, 0.95 * ia[-1])
    return dict(pga=float(np.max(np.abs(acc))), pgv=float(np.max(np.abs(v))), dakhir=float(d[-1]),
                d595=(i95 - i5) * dt, rmin=float(r.min()), rmax=float(r.max()), sa=sa, per=per)


def buat(folder=FOLDER):
    folder.mkdir(parents=True, exist_ok=True)
    hasil = []
    for n, b in enumerate(BENIH[:JUMLAH], start=1):
        t, acc = bangkitkan(b)
        nama = f"SIN-{n:02d}"
        with open(folder / f"{nama}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["# DATA SIMULASI - rekaman sintetis [Asumsi], dicocokkan MCER batuan SB "
                        f"SMS {SMS:.4f} g SM1 {SM1:.4f} g; benih {b}; dt {DT} s; disusun AI atas permintaan Defsa"])
            w.writerow(["t (s)", "a (g)"])
            for ti, ai in zip(t, acc):
                w.writerow([f"{ti:.2f}", f"{ai:.6f}"])
        r = ringkas(acc, DT)
        r.update(nama=nama, benih=b)
        hasil.append(r)
    per = hasil[0]["per"]
    rata = np.mean([h["sa"] for h in hasil], axis=0)
    with open(folder / "Ringkasan Rekaman Sintetis.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Rekaman", "Benih", "PGA (g)", "PGV (m/s)", "D5-95 (s)", "Perpindahan akhir (m)",
                    f"Sa/target min {T_COCOK}", f"Sa/target maks {T_COCOK}"])
        for h in hasil:
            w.writerow([h["nama"], h["benih"], f"{h['pga']:.4f}", f"{h['pgv']:.4f}", f"{h['d595']:.1f}",
                        f"{h['dakhir']:.4f}", f"{h['rmin']:.3f}", f"{h['rmax']:.3f}"])
        w.writerow([])
        w.writerow(["T (s)", "Sa target (g)", "Sa rata-rata 7 rekaman (g)", "Rasio"])
        for tt, st, sr in zip(per, sa_target(per), rata):
            w.writerow([f"{tt:.3f}", f"{st:.4f}", f"{sr:.4f}", f"{sr / st:.3f}"])
    return hasil, per, rata


def grafik(hasil, per, rata, berkas=FOLDER / "Spektrum Rekaman Sintetis.png"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Times New Roman"
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for h in hasil:
        ax.plot(per, h["sa"], color="0.7", lw=0.7)
    ax.plot(per, sa_target(per), "k-", lw=1.8, label="Target MCER batuan SB")
    ax.plot(per, rata, "k--", lw=1.4, label="Rata-rata 7 rekaman sintetis")
    ax.plot(per, 0.9 * sa_target(per), "k:", lw=0.9, label="0,9 dan 1,3 × target")
    ax.plot(per, 1.3 * sa_target(per), "k:", lw=0.9)
    ax.axvspan(*T_COCOK, color="0.93", zorder=0)
    ax.set_xscale("log")
    ax.set_xlabel("Periode T (detik)")
    ax.set_ylabel("Sa (g), redaman 5 %")
    ax.set_title("Rekaman sintetis batuan dasar (DATA SIMULASI, draf menunggu persetujuan Defsa)", fontsize=9)
    ax.grid(True, which="both", lw=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(berkas, dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    hasil, per, rata = buat()
    grafik(hasil, per, rata)
    for h in hasil:
        print(f"{h['nama']} PGA {h['pga']:.3f} g D5-95 {h['d595']:.1f} s rasio {h['rmin']:.2f}-{h['rmax']:.2f}"
              f" d_akhir {h['dakhir']:.4f} m")
    m = (per >= T_COCOK[0]) & (per <= T_COCOK[1])
    r = rata[m] / sa_target(per[m])
    print(f"Rata-rata/target di {T_COCOK}: {r.min():.3f}-{r.max():.3f}")
