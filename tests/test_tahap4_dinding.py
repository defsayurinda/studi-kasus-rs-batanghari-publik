import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap4_dinding as dd  # noqa: E402


def test_luas_kotak_dengan_pintu():
    for tipe in "LT":
        dx, dy = dd.DIM[tipe]
        t = dd.T
        a_tangan = (dx + t) * (dy + t) - (dx - t) * (dy - t) - t * sum(w for _, w in dd.PINTU[tipe])
        a, _, _ = dd.sifat(dd.persegi_u(tipe, "Y", 100.0))   # hw besar: seluruh sayap efektif
        assert a == pytest.approx(a_tangan)


def test_sayap_efektif_18_10_5_2():
    # sayap dinding 6 m (arah X inti tangga), hw 9 m: 0,25 hw = 2,25 dari muka dalam badan
    f = 6.0 / 2 - dd.T / 2
    assert dd.panjang_efektif(-f, f, 6.0, 2.25) == pytest.approx(2 * 2.25)
    assert dd.panjang_efektif(-f, f, 6.0, 10.0) == pytest.approx(2 * f)


def test_titik_pm_persegi_tangan():
    # satu persegi 0,35 × 2,0 m, dua batang ujung 1.000 mm² di u = ±0,95; c = 0,5 m
    rects = np.array([[-1.0, 1.0, 0.35]])
    bars = np.array([[0.95, 1000.0], [-0.95, 1000.0]])
    c = 0.5
    pn, mn, et, phi = dd.titik_pm(c, rects, bars)
    a = dd.BETA1 * c
    cc = 0.85 * 35 * a * 350 * 1000 / 1000            # kN (a m × 0,35 m)
    fs_t = max(-420.0, min(420.0, 200000 * 0.003 * (c - 1.95) / c))
    fs_c = min(420.0, 200000 * 0.003 * (c - 0.05) / c) - 0.85 * 35
    p = cc + (fs_t + fs_c) * 1000 / 1000
    m = cc * (1.0 - a / 2) + fs_c * 0.95 - fs_t * 0.95
    assert pn[0] == pytest.approx(p) and mn[0] == pytest.approx(m)
    assert et[0] == pytest.approx(0.003 * (1.95 - c) / c)


def test_mn_desain_ambil_terkecil():
    dg = dd.diagram("L", "X", 25.8, 1, (13, 300, 8, 22))
    p = np.array([0.0, 5000.0])
    assert np.all(dd.mn_pada(dg, p, True) <= dd.mn_pada(dg, p) + 1e-6)
    assert np.isnan(dd.mn_pada(dg, np.array([dg["phiPmax"] + 1.0]), True)[0])


def test_alpha_c():
    assert dd.alpha_c(1.0) == 0.25 and dd.alpha_c(3.0) == 0.17
    assert dd.alpha_c(1.75) == pytest.approx(0.21)


def test_aliran_torsi():
    for tipe in "LT":
        dx, dy = dd.DIM[tipe]
        assert dd.koef_aliran(tipe)[0]["qt"] == pytest.approx(1 / (2 * dx * dy))


def test_tangga_pynite_dan_tebal():
    for h in (4.2, 4.5):
        s = dd.tangga(h)
        assert s["t"] >= s["ell"] / 24 - 1e-9                      # Tabel 7.3.1.1
        assert s["r"] <= 0.175 + 1e-9
        assert dd.tangga_pynite(s) == pytest.approx(s["Mpos"], rel=0.01)   # T-81
        assert s["Vu"] <= s["phiVc"]


def test_atap_angkur():
    a = dd.atap_sementara()
    assert a["Nb"] == pytest.approx(10 * math.sqrt(35) * 150 ** 1.5 / 1000)
    assert a["ok"] and a["ed_ok"]


def test_rancang_memenuhi():
    r = dd.rancang()
    for x in r["kelompok"]:
        assert x["rasio_pm"] <= 1.0
        for s in x["geser"].values():
            assert s["rasio"] <= 1.0 and s["rho_t"] >= 0.0025 and s["s"] <= 450
        assert x["rho_l"] >= 0.0025
    assert r["cp"]["Mn_cp"] == pytest.approx(r["cp"]["Mn_sendiri"], rel=0.05)   # T-80
