import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap3_bim as bm  # noqa: E402
import tahap3_model_konsep as mk  # noqa: E402

pytest.importorskip("ifcopenshell")


def test_bukaan_tengah_bentang():
    assert mk.bukaan_per_sisi(72000) == [4000 + 8000 * i for i in range(9)]


def test_model_gabungan_lengkap():
    if not mk.IFC.exists():
        pytest.skip("model belum dibangun")
    v = bm.validasi(mk.IFC, wajib_lod=False)
    assert v["lolos"]
    k = v["kelas"]
    assert k["IfcPile"] == len(bm.posisi_tiang()) and k["IfcWindow"] > 100 and k["IfcWall"] > 28
    assert len(v["file"].by_type("IfcSpace")) >= 31
    assert mk.GAMBAR_3D.exists()
