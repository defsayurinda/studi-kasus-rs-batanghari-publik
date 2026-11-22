import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap2_air_tanah as at  # noqa: E402


def test_thiem_contoh_tangan():
    # Q = 0,004 m3/s, r1 = 30, r2 = 10, s2 - s1 = 0,9 m, B = 9,3 m
    k = at.thiem_tertekan(0.004, 30, 10, 1.1, 2.0, 9.3)
    assert math.isclose(k, 0.004 * math.log(3) / (2 * math.pi * 9.3 * 0.9), rel_tol=1e-12)


def test_uji_pompa_dan_regresi():
    up = at.ringkas_uji_pompa()
    assert 5e-5 < up["k_thiem"] < 1.5e-4
    assert abs(up["T_bayangan"]["OW-1"] / up["T_thiem"] - 1) < 0.15
    g = at.regresi_jeda("PZ-2B (m)")
    assert g["L"] == 3 and g["r"] > 0.99


def test_fk_blowin():
    p = "Tengah tapak (BH-5)"
    assert at.fk_blowin(p, 6.0, 7.0) > at.fk_blowin(p, 5.0, 7.0)
    assert at.fk_blowin(p, 6.0, 6.0) > at.fk_blowin(p, 6.0, 9.0)
    e = at.elev_dasar_min(p, 7.0)
    assert abs(at.fk_blowin(p, e, 7.0) - 1.25) < 1e-6
    # hitungan tangan: dasar +6,0, h +7,0: (15,2 x (6,0 - 0,49)) / (9,81 x (7,0 - 0,49))
    assert math.isclose(at.fk_blowin(p, 6.0, 7.0), 15.2 * 5.51 / (9.81 * 6.51), rel_tol=1e-9)
