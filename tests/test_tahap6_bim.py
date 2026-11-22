"""Uji 6.9 model BIM pondasi: memakai IFC yang sudah dibangun (`skrip/tahap6_bim.py --bangun`), tidak membangun ulang."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap6_bim as t  # noqa: E402


@pytest.fixture(scope="module")
def v():
    if not t.IFC.exists():
        pytest.skip("IFC belum dibangun")
    return t.validasi()


def test_jumlah_sama_rencana(v):
    assert (v["n_tiang"], v["n_cap"]) == (319, 83)
    assert v["d_n_tiang"] == 0 and v["d_n_cap"] == 0
    assert v["rencana"]["n_utama"] == 251 and v["rencana"]["n_util"] == 68


def test_volume_dalam_toleransi(v):
    assert abs(v["d_v_tiang"]) <= t.TOL["volume"] and abs(v["d_v_cap"]) <= t.TOL["volume"]


def test_jarak_tiang_minimum(v):
    assert v["jarak_min"] >= t.JARAK_MIN - t.TOL["jarak"]


def test_validasi_ifc_lolos(v):
    assert v["lolos"], [c for c in v["cek"] if not c["lolos"]]


def test_tebal_cap_dan_kepala_tiang():
    cs = {c["id"]: c for c in t.caps()}
    assert cs["Cap E"]["h"] == 2.0 and cs["Cap A"]["h"] == 1.2
    e = [x for x in t.tiang() if x["cap"] == "Cap E"]
    assert len(e) == 54 and "Cap C" not in {x["cap"] for x in t.tiang()} and abs(e[0]["z1"] - 10.20) < 1e-9 and e[0]["z0"] == -27.60


def test_clash_tiang_dan_sambungan():
    cl = t.clash()
    assert cl["cap_cap"] == [] and cl["tiang_cap_lain"] == [] and cl["tiang_tiang"] == [] and cl["cap_sloof"] == [] and cl["cap_stek"] == []
