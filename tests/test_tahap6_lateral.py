import math
import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap6_lateral as t  # noqa: E402


@pytest.fixture(scope="module")
def h():
    os.environ["TAHAP6_LATERAL_CACHE"] = "1"      # hasil berat di cache (%TEMP%\tahap6_lateral_hasil.pkl)
    return t.semua()


def test_sifat_tiang():
    assert t.EC == pytest.approx(25742.96, rel=1e-4)
    assert t.I_TIANG == pytest.approx(0.020106, rel=1e-4)
    assert t.EI_BRUTO == pytest.approx(517.6, rel=1e-3)
    assert t.H_TIANG["X"] == pytest.approx(52.45, rel=1e-3) and t.H_TIANG["Y"] == pytest.approx(35.73, rel=1e-3)


def test_keseimbangan_geser_dan_kepala():
    """Sendi: M kepala 0; jepit: rotasi 0; jumlah reaksi tanah = beban kepala (kasus inersia)."""
    for kep in ("sendi", "jepit"):
        s = t.solusi("SELATAN", kep, 53.95, varian="m0.1", n_el=200)
        L = t.PANJANG / 200
        assert abs(np.sum(s["p"]) * L - 53.95) < 0.005 * 53.95
        assert abs(s["V"][0]) == pytest.approx(53.95, rel=1e-3)
    s = t.solusi("SELATAN", "sendi", 53.95, n_el=200)
    assert abs(s["M"][0]) < 1e-3
    s = t.solusi("SELATAN", "jepit", 53.95, n_el=200)
    assert abs(s["th"][0]) < 1e-12 and abs(s["M"][0]) > 50


def test_fe_linier_sama_rumus_reese_matlock():
    pm = t.pembanding_elastis("SELATAN")
    assert pm["dfe"] <= 2.0            # FE dengan pegas linier nh = rumus tertutup


def test_batas_rankine_menurunkan_pu():
    z, e = t.mesh(200)
    _, P1 = t.parameter_tanah("SELATAN", e, "m0.1", rankine=True)
    _, P0 = t.parameter_tanah("SELATAN", e, "m0.1", rankine=False)
    assert np.all(P1["pu"] <= P0["pu"] + 1e-9) and np.any(P1["pu"] < P0["pu"] - 1.0)


def test_urutan_tuntutan_dan_kepala(h):
    r = h["ringkas"]
    assert r["I-S-X-m0.1-sendi"]["mmaks"] < r["K-Youd-m0.1-sendi"]["mmaks"] < r["K-Zhang-m0.1-sendi"]["mmaks"]
    assert r["I-S-X-m0.1-jepit"]["y0"] < r["I-S-X-m0.1-sendi"]["y0"]
    assert abs(r["I-S-X-m0.1-jepit"]["mkepala"]) == pytest.approx(r["I-S-X-m0.1-jepit"]["mmaks"], rel=0.05)
    assert r["I-S-X-m0.1-sendi-EIbruto"]["y0"] < r["I-S-X-m0.1-sendi"]["y0"]      # EI bruto lebih kaku


def test_kapasitas_lentur_dalam_rentang():
    k = t.kapasitas_lentur()
    assert 0.75 * k["Mn"] <= k["phiMn"] <= 0.9 * k["Mn"] + 1e-9 and 0.75 <= k["phi"] <= 0.9
    assert k["phi"] * k["Pn"] == pytest.approx(t.P_MAKS, rel=1e-3)        # c memenuhi φPn = P
    assert 900 < k["phiMn"] < 1400
    assert t.kapasitas_lentur(P_u=0.0)["phiMn"] < k["phiMn"]


def test_t103_a_openpile_dan_batas_serakan(h):
    for k in ("sendi", "jepit", "utara", "m0.1"):
        o = h["op"][k]
        assert o is not None, "openpile tidak jalan (pydantic 1 di folder temp)"
        assert o["dy"] <= t.TOL["openpile"] and o["dm"] <= t.TOL["openpile"]
    assert h["pemb"]["sebaran"] <= t.TOL["sebaran"] and h["pemb"]["sebaran_het"] <= t.TOL["sebaran"]
    for kep in ("sendi", "jepit"):
        b = h["batas"][kep]
        assert b is None or 0 < b < 1


def test_profil_serakan_dan_skala():
    e = np.array([5.0, 1.01, -2.0, -6.0, -9.18, -20.0])
    assert list(np.round(t.u_tanah(e), 2)) == [4.58, 4.58, 3.02, 1.2, 0.0, 0.0]
    assert t.u_tanah(np.array([-0.5]))[0] == pytest.approx(4.58 + (3.02 - 4.58) * (1.01 + 0.5) / 3.01)
    assert t.u_tanah(np.array([5.0]), t.DH_YOUD / t.DH_ZHANG)[0] == pytest.approx(0.19)
