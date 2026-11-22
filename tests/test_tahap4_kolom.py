import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap4_kolom as kl  # noqa: E402


def test_diagram_titik_ujung():
    # 12D25 di kolom 650: Po = 0,85 fc' (Ag - Ast) + fy Ast; tarik murni -fy Ast
    dg = kl.diagram(0.65, 4, 25)
    ast = 12 * math.pi * 25 ** 2 / 4
    assert dg["Ast"] == pytest.approx(ast)
    assert dg["Po"] == pytest.approx((0.85 * 35 * (650 ** 2 - ast) + 420 * ast) / 1e3)
    assert dg["Pn"][0] == pytest.approx(-420 * ast / 1e3)
    assert dg["phiPmax"] == pytest.approx(0.65 * 0.8 * dg["Po"])


def test_titik_seimbang_tangan():
    # c seimbang: εs baris terjauh = εty 0,002 → c = 0,003 dt / 0,005, φ = 0,65
    b, m, db = 0.75, 5, 25
    ys, as_ = kl.baris_batang(b, m, db)
    dt = ys.max()
    c = 0.003 * dt / 0.005
    pn, mn, et, phi = kl.titik_pm(c, b, ys, as_)
    assert et[0] == pytest.approx(0.002) and phi[0] == pytest.approx(0.65)
    # hitung tangan per baris
    a = 0.8 * c
    p = 0.85 * 35 * a * 750
    m_ = p * (375 - a / 2)
    for y, s in zip(ys, as_):
        fs = max(-420.0, min(420.0, 200000 * 0.003 * (c - y) / c)) - (0.85 * 35 if y < a else 0.0)
        p += fs * s
        m_ += fs * s * (375 - y)
    assert pn[0] == pytest.approx(p / 1e3) and mn[0] == pytest.approx(m_ / 1e6)


def test_mn_pada_dan_batas():
    dg = kl.diagram(0.75, 5, 25)
    assert np.isnan(kl.mn_pada(dg, dg["phiPmax"] + 1, desain=True))
    assert kl.mn_pada(dg, 0.0) > 0
    assert kl.mn_pada(dg, 0.0, desain=True) <= kl.mn_pada(dg, 0.0)


def test_pilihan_tulangan_sah():
    for b in (0.65, 0.75):
        for ast, m, db in kl.pilihan_tulangan(b):
            assert 0.01 <= ast / (b * 1000) ** 2 <= kl.RHO_PAKAI
            assert (b * 1000 - 2 * kl.SEL - 2 * kl.DS - db) / (m - 1) - db >= max(40, 1.5 * db)


def test_beban_segitiga_total():
    # 16 beban titik × q = q L²/4 per sisi
    assert kl.BOBOT_SEGITIGA.sum() == pytest.approx(kl.L_GRID ** 2 / 4)


def test_sayap_tabel_6321():
    assert kl.sayap(0.35, 0.75, False) == pytest.approx(min(1.6, 3.825, 7.25 / 8))
    assert kl.sayap(0.35, 0.75, True) == pytest.approx(min(1.2, 3.825, 7.25 / 12))


def test_rancang_memenuhi_dan_statika():
    r = kl.rancang()
    for konfig, st in r["statika"].items():
        total, dasar = st["D"]
        assert dasar == pytest.approx(total, rel=1e-3)                     # T-78
    for x in r["kelompok"]:
        assert 0.01 <= x["rho"] <= 0.06
        assert x["pm"]["rasio"] <= 1.0
        g = x["geser"]
        assert g["s_lo"] <= min(x["b"] * 1000 / 4, 6 * x["db"], 150)
        assert g["lo"] >= max(x["b"] * 1000, 450)
