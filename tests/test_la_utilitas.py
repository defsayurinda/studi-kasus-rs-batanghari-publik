import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import la_utilitas as lu  # noqa: E402


def test_ramp_dermaga_tidak_muat_di_sempadan():
    d = lu.dermaga()
    assert math.isclose(d["beda_tinggi"], 12.85 - 4.00)
    assert d["ramp_1_12"] > 80  # sempadan hanya 6-8 m di x 0-40


def test_fato_lebih_lebar_dari_menara():
    h = lu.helipad()
    assert math.isclose(h["fato"], 1.5 * 16.66) and h["area_aman"] > h["lebar_menara"]
    assert h["atap_podium"] >= h["perlu_mep"]


def test_tangki_solar_mengapung_tanpa_pemberat():
    t = lu.tangki_solar()
    assert math.isclose(t["angkat"], 9.81 * math.pi * 1.2 ** 2 * 3.6)
    assert t["fk_tanpa_pemberat"] < 1
    assert math.isclose((t["berat_kosong"] + t["pemberat_beton"] * (24 - 9.81)) / t["angkat"], 1.25)


def test_jarak_o2_ke_solar():
    assert lu.jarak_o2_solar() >= 10
