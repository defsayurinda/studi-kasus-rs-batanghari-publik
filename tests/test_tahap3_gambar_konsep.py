import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap3_gambar_konsep as gk  # noqa: E402


def test_dxf_dari_bimcraft_tersimpan():
    assert gk.DXF_DENAH.exists() and gk.DXF_POTONGAN.exists()
    assert "LWPOLYLINE" in gk.DXF_DENAH.read_text(errors="ignore")


def test_lembar_pdf_dan_dwg_ada():
    for nama in ("GK-09 Denah Konsep LT1", "GK-10 Potongan Konsep A-A"):
        assert (gk.KELUAR / "Gambar" / "DWG" / f"{nama}.dwg").exists()
    assert gk.PDF_DENAH.exists() and gk.PDF_POTONGAN.exists()
