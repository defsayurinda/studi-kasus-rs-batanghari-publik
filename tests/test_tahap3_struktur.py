import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap3_program as pr  # noqa: E402
import tahap3_struktur as st  # noqa: E402


def test_fa_fv_interpolasi_tangan():
    # Tabel 6 SE: Ss 0,25 -> 2,4; 0,5 -> 1,7. Tabel 7 SE: S1 0,2 -> 3,3; 0,3 -> 2,8
    fa = 2.4 + (0.334 - 0.25) / 0.25 * (1.7 - 2.4)
    fv = 3.3 + (0.264 - 0.2) / 0.1 * (2.8 - 3.3)
    sp = st.spektrum()
    assert math.isclose(sp["Fa"], fa) and math.isclose(sp["Fv"], fv)
    assert math.isclose(sp["SDS"], 2 / 3 * fa * 0.334) and sp["KDS"] == "D"


def test_tebal_pelat_tabel_8_3_1_2():
    assert math.isclose(st.tebal_pelat(), 7600 * (0.8 + 420 / 1400) / 45)
    assert all(st.PRA[s]["pelat"] >= st.tebal_pelat() for s in st.PRA)


def test_balok_lebih_tinggi_dari_minimum():
    assert all(st.PRA[s]["balok"][1] >= st.tinggi_balok_min()["satu_sisi"] for s in st.PRA)


def test_pynite_cocok_tributari():
    for s in st.SISTEM:
        assert abs(st.pynite_portal(s) / st.aksial_kolom(s) - 1) < 0.05


def test_kolom_aksial_batas():
    for s in st.SISTEM:
        k = st.cek_kolom(s)
        assert k["rasio"] < 1 and k["aksial_fc"] <= 0.35


def test_menara_di_grid():
    m = pr.MASSA["MENARA"]
    assert m["x"][0] in st.GRID_X and m["x"][1] in st.GRID_X
    assert m["y"][0] in st.GRID_Y and m["y"][1] in st.GRID_Y


def test_helikopter_aw139():
    h = st.beban_helikopter()
    assert math.isclose(h["terpusat"], 0.75 * 6800 * 9.81 / 1000)
