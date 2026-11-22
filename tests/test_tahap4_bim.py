import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap4_bim as bm  # noqa: E402

ifcopenshell = pytest.importorskip("ifcopenshell")

# ukuran final tahap4_balok.rancang()["ukuran_model"] (4.6, disetujui Defsa 20 Nov 2026); rancang() butuh ±80 s
UK = {("LT3", 60.0, 67.0, 68.0, 67.0): (0.4, 0.7), ("LT3", 60.0, 67.0, 60.0, 75.0): (0.45, 0.8),
      ("LT3", 68.0, 67.0, 76.0, 67.0): (0.4, 0.7), ("LT3", 68.0, 67.0, 68.0, 75.0): (0.6, 1.2),
      ("LT3", 76.0, 67.0, 76.0, 75.0): (0.45, 0.8)}


def test_jumlah_dan_paket():
    u = bm.unsur(UK)
    kolom = [x for x in u if x["k"] == "kolom"]
    assert len(kolom) == 300
    assert sum(x["b"] == 0.95 for x in kolom) == 4 and sum(x["b"] == 0.80 for x in kolom) == 8
    assert all(x["paket"] == "menyusul" for x in u if x["lv"] in ("LT6", "ATAP") and x["k"] != "tangga")
    assert not [x for x in u if x["k"] == "balok" and x["lv"] == "LT5" and x["paket"] == "tahap 1"]


def test_rel_chiller_bebas_shaft():
    for y in bm.REL_Y:
        assert y - bm.REL[0] / 2 > 53.2 or y + bm.REL[0] / 2 < 52.2


@pytest.fixture(scope="module")
def hasil():
    if not bm.IFC.exists():
        pytest.skip("model IFC belum dibangun")
    return bm.validasi(uk_balok=UK)


def test_validasi_ifc(hasil):
    assert hasil["lolos"], [c for c in hasil["cek"] if not c["lolos"]]


def test_volume_dalam_toleransi(hasil):
    for b in hasil["volume"]:
        assert abs(b["selisih"]) <= bm.TOLERANSI_VOLUME, b


def test_tanpa_clash_shaft(hasil):
    assert bm.clash_shaft(hasil["file"]) == []
