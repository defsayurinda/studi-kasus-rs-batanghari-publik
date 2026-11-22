import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap3_bim as bm  # noqa: E402
import tahap3_pondasi as fd  # noqa: E402

ifcopenshell = pytest.importorskip("ifcopenshell")


def test_jumlah_tiang_sama_dengan_3_7():
    o = fd.opsi("A")
    assert len(bm.posisi_tiang()) == o["n_utama"] + o["n_gu"]


def test_ukuran_cap_dua_tiang():
    _, (w, d) = bm.pola(2)
    assert math.isclose(w, 2.4 + 1.6) and math.isclose(d, 1.6)


@pytest.fixture(scope="module")
def model():
    if not bm.IFC.exists():
        pytest.skip("model IFC belum dibangun")
    return ifcopenshell.open(str(bm.IFC))


def test_validasi_lolos(model):
    v = bm.validasi(bm.IFC)
    assert v["lolos"], [c for c in v["cek"] if not c["lolos"]]
    assert v["kelas"]["IfcPile"] == len(bm.posisi_tiang())
    assert v["kelas"]["IfcFooting"] == len(bm.kelompok_tiang())


def test_volume_struktur_atas_dalam_toleransi(model):
    rows, _, _ = bm.pembanding(model)
    for r in rows:
        assert abs(r["selisih"]) <= bm.TOLERANSI_VOLUME, r
