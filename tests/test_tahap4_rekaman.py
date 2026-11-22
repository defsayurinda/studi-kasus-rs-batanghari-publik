import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap4_rekaman as r  # noqa: E402


def test_spektrum_target_sb():
    # SNI 1726:2019 Tabel 6/7: SB Fa 0,9, Fv 0,8; Ss 0,334, S1 0,264
    assert abs(r.SMS - 0.3006) < 1e-4
    assert abs(r.SM1 - 0.2112) < 1e-4
    assert abs(r.sa_target(0.0) - 0.4 * r.SMS) < 1e-9
    assert abs(r.sa_target(0.5) - r.SMS) < 1e-9
    assert abs(r.sa_target(2.0) - r.SM1 / 2.0) < 1e-9


def test_sdof_harmonik_analitik():
    # beban harmonik resonansi, redaman 5 %: amplitudo tunak u = a0 / (2 zeta w^2) -> Sa = a0 / (2 zeta)
    dt, tn = 0.005, 0.5
    t = np.arange(0, 60, dt)
    a0 = 0.1
    acc = a0 * np.sin(2 * np.pi / tn * t)
    sa_nj = r.spektrum_nj(acc, dt, np.array([tn]))[0]
    assert abs(sa_nj - a0 / (2 * 0.05)) / (a0 / 0.1) < 0.02


def test_dua_cara_spektrum_sama():
    # cek silang Nigam-Jennings vs Newmark percepatan rata-rata
    t, acc = r.bangkitkan(r.BENIH[0])
    per = np.array([0.2, 0.7, 1.5])
    a = r.spektrum_nj(acc, r.DT, per)
    b = r.spektrum_newmark(acc, r.DT, per)
    assert np.all(np.abs(a - b) / a < 0.03)


def test_rekaman_cocok_target():
    t, acc = r.bangkitkan(r.BENIH[1])
    h = r.ringkas(acc, r.DT)
    assert h["rmin"] >= r.BATAS[0] and h["rmax"] <= r.BATAS[1]
    assert abs(h["dakhir"]) < 0.15
    assert 15 <= h["d595"] <= 30
