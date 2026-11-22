import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import la6_biaya as l6  # noqa: E402
import tahap3_program as pr  # noqa: E402


def test_rincian_luas_sama_dengan_konsep():
    _, total = l6.rincian_luas()
    assert math.isclose(total, pr.cek_massa()["luas_lantai"])


def test_biaya_per_bagian_sama_dengan_rev_b():
    a, b = l6.cek_bagian()
    assert math.isclose(a, b, rel_tol=1e-6)


def test_rev_b_lebih_besar_dari_3_8_dan_ve_mengurangi():
    r = l6.rev_b()
    assert r["total_rev_b"] > r["total_38"] > r["setelah_ve"] > r["setelah_v2"]


def test_paket_menurun_dan_minimal_50_tt():
    p = l6.paket()[0]
    biaya = [x["biaya"] for x in p]
    assert biaya == sorted(biaya, reverse=True)
    assert all(x["tt"] >= 50 for x in p)
