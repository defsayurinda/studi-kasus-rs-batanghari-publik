import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap5_bim as bm  # noqa: E402

ifcopenshell = pytest.importorskip("ifcopenshell")


@pytest.fixture(scope="module")
def u():
    return bm.unsur()


def test_kolom_tangki_800_tanpa_950(u):
    kol = [x for x in u if x["k"] == "kolom"]
    assert len(kol) == 300 and not [x for x in kol if x["b"] == 0.95]
    tk = [x for x in kol if x.get("tangki")]
    assert len(tk) == 12 and {(x["x"], x["y"]) for x in tk} == bm.KOLOM_B and all(x["b"] == 0.80 for x in tk)
    assert {x["lv"] for x in tk} == {"LT2", "LT3"}


def test_pelat_tangki_350_di_bay_b(u):
    pt = [x for x in u if x["k"] == "pelat" and "tangki" in x["nama"]]
    assert len(pt) == 1 and pt[0]["t"] == 0.35 and pt[0]["poli"].bounds == (60.0, 67.0, 68.0, 75.0)
    assert not [x for x in u if x.get("nama") == "PL-250-tangki"]
    assert not [x for x in u if x["k"] == "balok" and x.get("khusus") == "balok anak tangki"]


def test_pit_dasar(u):
    p = {x["kode"]: x for x in u if x["k"] == "pit" and x["jenis"] == "pelat"}
    assert p["L-1..4"]["t"] == 0.45 and p["L-5..6"]["t"] == 0.40 and p["L-7"]["t"] == 0.40
    assert len([x for x in u if x["k"] == "pit" and x["jenis"] == "dinding"]) == 3


def test_tanpa_sloof_di_inti_lift(u):
    sl = {x["p"] for x in u if x["k"] == "sloof" and x["tipe"] != "BP-L7"}
    assert (52.0, 35.0, 52.0, 43.0) not in sl
    assert len([x for x in u if x["k"] == "sloof" and x["tipe"] == "BP-L7"]) == 2
    assert {x["b"] for x in u if x["k"] == "sloof" and x["tipe"] == "SL-1"} == {0.40}


def test_pelat_lt1_dan_stek(u):
    p = [x for x in u if x.get("lt1")][0]
    assert p["t"] == 0.25 and p["fc"] == 35 and len(p["lubang"]) == 13  # 5 SH + 5 inti tangga + 3 pit
    assert len([x for x in u if x["k"] == "stek" and x["jenis"] == "kolom"]) == 70


def test_clash_geometri(u):
    c = bm.clash(u)
    assert not [v for k, v in c.items() if k != "shaft_lt1_dicek" and v], c


@pytest.fixture(scope="module")
def hasil():
    if not bm.IFC.exists():
        pytest.skip("model IFC belum dibangun")
    return bm.validasi()


def test_validasi_ifc(hasil):
    assert hasil["lolos"], [c for c in hasil["cek"] if not c["lolos"]]


def test_volume_dalam_toleransi(hasil):
    assert {b["unsur"] for b in hasil["volume"]} == set(bm.KELOMPOK)
    for b in hasil["volume"]:
        assert abs(b["selisih"]) <= bm.TOLERANSI_VOLUME, b


def test_tanpa_clash_shaft(hasil):
    assert bm.t4.clash_shaft(hasil["file"]) == []
