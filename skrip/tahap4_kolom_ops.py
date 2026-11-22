"""Tahap 4 langkah 4.1, cara 2: kolom tanah 1D nonlinier tegangan total di openseespy (cek silang pystrata).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (20 Nov 2026); draf, menunggu persetujuan
Defsa.

Model: elemen quad 2D satu kolom (lebar 1 m), sisi kiri-kanan diikat equalDOF (geser murni); material
PressureIndependMultiYield (tegangan total, kurva hiperbolik, 20 permukaan leleh); dasar Lysmer-Kuhlemeyer
(peredam c = ρ·Vs batuan) dengan gaya F = c × kecepatan singkapan batuan (Joyner-Chen); redaman Rayleigh 2 %
pada 1 dan 5 Hz [Asumsi]. Kuat geser: lempung su (2.4) [Uji sendiri]; pasir τmax = σ'm sin φ' [Asumsi];
urugan 30 kPa, U8 300 kPa, U9 400 kPa [Asumsi].
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_respons_situs as rs  # noqa: E402
import tahap4_rekaman as rk  # noqa: E402

PHI = {"U5": 33.0, "U7": 38.0}
SU = {"U0": 30.0, "U1": 20.0, "U2": 35.0, "U3": 8.0, "U6": 85.0, "U8": 300.0, "U9": 400.0}


def su_u4(z_asli):
    return 5.2 + 1.09 * z_asli  # kPa, 2.4 (z dari muka tanah asli)


def kuat_geser(unit, s_m, z_asli):
    if unit == "U4":
        return su_u4(z_asli)
    if unit in PHI:
        return max(5.0, s_m * math.sin(math.radians(PHI[unit])))
    return SU[unit]


def jalankan(rekaman=1, zona="SELATAN", faktor_u5=1.0, maks=0.5):
    import openseespy.opensees as ops

    lap = rs.lapisan_zona(zona, faktor_u5=faktor_u5, maks=maks)
    sm = rs.tegangan_rata(lap)
    acc = np.loadtxt(rk.FOLDER / f"SIN-{rekaman:02d}.csv", delimiter=",", skiprows=2)[:, 1] * 9.81
    dt_in = rk.DT
    vel = np.cumsum(acc) * dt_in
    vel = vel - np.linspace(0, vel[-1], len(vel))   # kecepatan akhir nol

    ops.wipe()
    ops.model("basic", "-ndm", 2, "-ndf", 2)
    n = len(lap)
    tinggi = [h for _, h, *_ in lap][::-1]        # dari bawah ke atas
    y = np.concatenate([[0.0], np.cumsum(tinggi)])
    for i, yi in enumerate(y):
        ops.node(2 * i + 1, 0.0, yi)
        ops.node(2 * i + 2, 1.0, yi)
    ops.fix(1, 0, 1)
    ops.fix(2, 0, 1)
    for i in range(1, len(y)):
        ops.equalDOF(2 * i + 1, 2 * i + 2, 1, 2)
    ops.equalDOF(1, 2, 1)
    for k, ((unit, h, vs, g, *_rest), s) in enumerate(zip(lap[::-1], sm[::-1])):
        rho = g / 9.81
        gmax = rho * vs ** 2
        bulk = 2 * gmax * (1 + 0.3) / (3 * (1 - 2 * 0.3))
        z_asli = _rest[-1]
        tau = kuat_geser(unit, s, z_asli)
        ops.nDMaterial("PressureIndependMultiYield", k + 1, 2, rho, gmax, bulk, tau, 0.1, 0.0, 100.0, 0.0, 20)
        ops.element("quad", k + 1, 2 * k + 1, 2 * k + 2, 2 * k + 4, 2 * k + 3, 1.0, "PlaneStrain", k + 1)
    for k in range(n):
        ops.updateMaterialStage("-material", k + 1, "-stage", 1)
    # peredam dasar
    c_dasar = 22.0 / 9.81 * rs.VS_BATUAN * 1.0
    ops.node(9001, 0.0, 0.0)
    ops.node(9002, 0.0, 0.0)
    ops.fix(9001, 1, 1)
    ops.fix(9002, 0, 1)
    ops.equalDOF(1, 9002, 1)
    ops.uniaxialMaterial("Viscous", 9000, c_dasar, 1.0)
    ops.element("zeroLength", 9000, 9001, 9002, "-mat", 9000, "-dir", 1)
    ops.timeSeries("Path", 1, "-dt", dt_in, "-values", *(vel * c_dasar))
    ops.pattern("Plain", 1, 1)
    ops.load(1, 1.0, 0.0)
    w1, w2, zeta = 2 * np.pi * 1.0, 2 * np.pi * 5.0, 0.02
    a0 = 2 * zeta * w1 * w2 / (w1 + w2)
    a1 = 2 * zeta / (w1 + w2)
    ops.rayleigh(a0, 0.0, a1, 0.0)
    ops.constraints("Transformation")
    ops.numberer("RCM")
    ops.system("BandGeneral")
    ops.test("NormDispIncr", 1e-6, 30)
    ops.algorithm("Newton")
    ops.integrator("Newmark", 0.5, 0.25)
    ops.analysis("Transient")
    dt = dt_in / 2
    langkah = int(len(acc) * dt_in / dt)
    atas = 2 * n + 1
    a_perm = np.zeros(langkah)
    for i in range(langkah):
        if ops.analyze(1, dt) != 0:
            ops.algorithm("ModifiedNewton", "-initial")
            ok = ops.analyze(1, dt)
            ops.algorithm("Newton")
            if ok != 0:
                raise RuntimeError(f"tidak konvergen di t = {i * dt:.2f} s")
        a_perm[i] = ops.nodeAccel(atas, 1)
    ops.wipe()
    # percepatan total permukaan = relatif terhadap... model memakai gaya dasar, jadi nodeAccel sudah absolut
    a_perm = a_perm[::2] / 9.81
    return a_perm


def rasio(rekaman=1, zona="SELATAN", faktor_u5=1.0):
    a = jalankan(rekaman, zona, faktor_u5)
    acc_in = np.loadtxt(rk.FOLDER / f"SIN-{rekaman:02d}.csv", delimiter=",", skiprows=2)[:, 1]
    per = rs.PER
    sp = rk.spektrum_nj(a, rk.DT, per)
    sb = rk.spektrum_nj(acc_in, rk.DT, per)
    return sp / sb, float(np.max(np.abs(a)))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    import time
    for r in (1, 4):
        t0 = time.time()
        q, pga = rasio(r)
        print(f"SIN-{r:02d}: {time.time() - t0:.0f} s, PGA permukaan {pga:.3f} g, rasio maks {q.max():.2f} di "
              f"T {rs.PER[np.argmax(q)]:.2f} s")
