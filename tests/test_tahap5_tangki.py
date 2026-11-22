import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap5_tangki as t  # noqa: E402


@pytest.fixture(scope="module")
def r():
    return t.hitung()


def test_keseimbangan_tangki_ke_kolom(r):
    assert abs(sum(r["t_a"].values()) / t.P_TANGKI - 1) <= 0.005
    assert abs(sum(r["t_bk"].values()) / t.P_TANGKI - 1) <= 0.005
    assert abs(r["info_b"]["W_balok"] - t.P_TANGKI / 4) < 1e-6   # tiap balok W/4


def test_volume_tangki_b_dan_tepi_di_as():
    b = t.TANGKI_B
    assert b["x"][1] - b["x"][0] == 8.0 and b["y"][1] - b["y"][0] == 8.0
    assert 8.0 * 8.0 * 3.3 >= 210.0
    for tepi, grid in ((b["x"][0], t.GRID_X["7"]), (b["x"][1], t.GRID_X["8"]), (b["y"][0], t.GRID_Y["F"]), (b["y"][1], t.GRID_Y["G"])):
        assert abs(tepi - grid) < 1e-9
    assert abs(t.P_TANGKI / 64 - 33.875) < 1e-9
    assert t.baca_tangki()["berat_operasi"] == t.P_TANGKI


def test_biaya_sama_dengan_volume_kali_harga(r):
    h, bi, sa, sb = r["harga"], r["biaya"], r["sa"], r["sb"]
    dv = sb["vol"] - sa["vol"]
    assert abs(bi["beton"] - dv * h["beton"]) < 1e-9 and abs(bi["bekisting"] - dv * h["bekisting"]) < 1e-9
    assert abs(bi["besi"] - (sb["besi"] - sa["besi"]) / 1000 * h["besi"]) < 1e-9
    assert abs(bi["tiang"] - bi["d_tiang"] * h["biaya_tiang"]) < 1e-9
    assert abs(bi["langsung"] - (bi["beton"] + bi["bekisting"] + bi["besi"] + bi["tiang"] + bi["cap"])) < 1e-9
    assert abs(bi["total"] - bi["langsung"] * (1 + h["btl"]) * (1 + h["ppn"])) < 1e-9
    assert abs(h["biaya_cap_m3"] - 4.05) < 1e-6 and abs(h["biaya_tiang"] - 65972.51 / 373) < 1e-6


def test_tiang_ceil_reaksi_per_izin(r):
    for k in t.KOLOM:
        assert r["n_a"][k] == max(2, math.ceil(r["r_a"][k] / 911.0 - 1e-9))
        assert r["n_b"][k] == max(2, math.ceil(r["r_b"][k] / 911.0 - 1e-9))
    assert t.n_tiang(911.0) == 2 and t.n_tiang(2 * 911.0 + 1) == 3


def test_reaksi_b_menjaga_keseimbangan_beban(r):
    # selisih total reaksi B - A = selisih berat unsur (tangki sama)
    sa = sum(r["w_b"].values()) - sum(r["w_a"].values())
    assert abs(sum(r["r_b"].values()) - sum(r["r_a"].values()) - sa) < 1e-6


def test_t90_dalam_toleransi(r):
    x = r["t90"]
    assert abs(x["a_A"] / x["P"] - 1) <= 0.005 and abs(x["a_B"] / x["P"] - 1) <= 0.005
    assert x["b_ukuran_51"] == x["b_ukuran_46"] == (0.60, 1.20)
    assert abs(x["b_Mneg_51"] / x["b_Mneg_46"] - 1) <= 0.15
    assert abs(x["b_Mpos_51"] / x["b_Mpos_46"] - 1) <= 0.15
    assert abs(x["c_tangan_total"] / x["c_pynite_RD"] - 1) <= 0.10
    assert abs(x["c_tangan_tangki"] / x["c_pynite_tangki"] - 1) <= 0.10


def test_pelat_b_tebal_terkecil_yang_cukup(r):
    assert r["t_b"] == 0.35
    assert not r["pelat"][0.25]["ok"] and not r["pelat"][0.30]["ok"] and r["pelat"][0.35]["ok"]
    assert r["pelat"][0.25]["rasio_geser"] > 1.0


def test_tinggi_bersih_lt2(r):
    ru = r["ruang"]
    assert abs(ru["bersih_A"] - (4.5 - 1.2)) < 1e-9
    assert ru["bersih_B"] > ru["bersih_A"]
    assert ru["jarak_lb2_A"] == pytest.approx(ru["jarak_lb2_B"]) and ru["hadap_A"] == 6.0 and ru["hadap_B"] == 2.0


def test_excel_cocok_dengan_python(tmp_path):
    f = t.buat_excel(tmp_path / "5.1.xlsx")
    ok, pesan = t.cocokkan(f)
    assert ok, pesan
