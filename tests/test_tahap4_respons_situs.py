import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap4_respons_situs as rs  # noqa: E402


def test_profil_per_zona():
    for z in rs.ZONA:
        lap = rs.lapisan_zona(z)
        tebal = sum(h for _, h, *_ in lap)
        urug = rs.HALAMAN - rs.pd3.PROFIL[z]["elev"]
        assert abs(tebal - (urug + rs.DALAM_KERAS)) < 1e-6
        assert all(h <= 2.0 + 1e-9 for _, h, *_ in lap)
    unit = [u for u, *_ in rs.lapisan_zona("UTARA")]
    assert "U3" in unit and "U3" not in [u for u, *_ in rs.lapisan_zona("SELATAN")]


def test_degradasi_u5():
    a = {u: v for u, _, v, *_ in rs.lapisan_zona("SELATAN")}
    b = {u: v for u, _, v, *_ in rs.lapisan_zona("SELATAN", faktor_u5=rs.FAKTOR_LIK)}
    assert abs(b["U5"] / a["U5"] - rs.FAKTOR_LIK) < 1e-9 and a["U6"] == b["U6"]


def test_spektrum_se_sementara():
    # 3.6: SDS 0,482, SD1 0,524 (Pasal 6.4)
    assert abs(rs.sa_se(0.5) - 0.482) < 1e-9
    assert abs(rs.sa_se(2.0) - 0.262) < 1e-9


def test_parameter_desain_pasal_6_10_4():
    per = np.array([0.1, 0.2, 0.5, 1.0, 2.0, 5.0])
    sa = np.array([0.30, 0.50, 0.60, 0.40, 0.25, 0.08])
    sds, sd1 = rs.parameter_desain(per, sa)
    assert abs(sds - 0.54) < 1e-9          # 0,9 × 0,60
    assert abs(sd1 - 0.50) < 1e-9          # maks T·Sa di 1-5 s = 2,0 × 0,25


def test_kds_kategori_iv():
    # Tabel 8-9 hal. 37, kategori IV
    assert rs.kds(0.386, 0.459) == "D"
    assert rs.kds(0.30, 0.15) == "D"
    assert rs.kds(0.20, 0.10) == "C"
    assert rs.kds(0.10, 0.05) == "A"
