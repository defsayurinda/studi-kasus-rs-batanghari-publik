"""Uji 7.6 (tanpa CADCraft): shaft IFC = rencana, bukaan inti, beban alat, DWG GM-01..06 cad_cek 0, set PDF 6 halaman."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap7_gambar_mep as gm  # noqa: E402


def test_shaft_ifc_sama_rencana():
    sh = gm.shaft_ifc()
    assert len(sh) == 9 and all(r[6] is None or r[5] == r[6] for r in sh)


def test_bukaan_inti():
    b = gm.bukaan_inti()
    assert len(b) == 7 and len(b["Inti lif x50-58 y35-43"]) == 2


def test_beban_alat():
    baris, total = gm.beban_lantai()
    assert abs(sum(q for *_, q in baris) - sum(total.values())) < 1e-6 and total["LT3"] > 2676


def test_dwg_cek_pdf():
    from pypdf import PdfReader
    assert gm.cek() == {k: 0 for k in gm.LEMBAR}
    assert len(PdfReader(str(gm.PDF)).pages) == 6
