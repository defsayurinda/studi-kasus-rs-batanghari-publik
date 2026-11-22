import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap4_pelat as pl  # noqa: E402


def test_ddm_jumlah_momen_sama_mo():
    m = pl.ddm(10.0, 7.25, ujung=False)
    assert abs(m["neg_int"]["M"] + m["pos"]["M"] - m["Mo"]) < 1e-9
    e = pl.ddm(10.0, 7.25, ujung=True)
    assert abs((e["neg_int"]["M"] + e["neg_eks"]["M"]) / 2 + e["pos"]["M"] - e["Mo"]) < 0.01 * e["Mo"]


def test_tebal_minimum_tabel_8312():
    assert abs(pl.tebal_minimum(7.25, 2.5) - 7.25 * 1.1 / 45) < 1e-9
    assert pl.tebal_minimum(7.25, 1.96) > pl.tebal_minimum(7.25, 2.5)


def test_tulangan_contoh_tangan():
    # Mu 30 kNm/m, d 0,1605: As ≈ Mu/(φ fy 0,95 d) ± 3 %
    t = pl.tulangan(30.0)
    perkiraan = 30.0 / (0.9 * 420e3 * 0.95 * t["d"]) * 1e6
    assert abs(t["As"] / perkiraan - 1) < 0.03
    assert abs(t["As_min"] - 360) < 1e-6


def test_semua_panel_memenuhi():
    for p in pl.ringkasan()["panel"]:
        assert p["h"] >= p["hmin"] and p["Vu"] <= p["phiVc"]
        for b in p["baris"]:
            assert b["As_ada"] >= b["As_pakai"] - 1e-6 and b["s"] <= 400


def test_pons_helipad():
    h = pl.helipad_pons()
    assert h["Pu"] < h["phiVn"] and abs(h["Pu"] - 1.6 * 0.75 * 6800 * 9.81 / 1000) < 1e-6
