"""Uji 7.5 (tanpa CADCraft): DWG GS-33..35, cad_cek 0, set PDF, tabel tiang GS-32 = 321."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap6_gambar as g6  # noqa: E402
import tahap7_gambar_str as gs  # noqa: E402


def test_dwg_ada():
    assert all((gs.DWG / f"{n}.dwg").exists() for n in gs.NAMA.values())


def test_cad_cek_nol():
    import cad_cek
    assert all(len(cad_cek.cek(str(gs.DWG / f"{n}.dwg"))) == 0 for n in gs.NAMA.values())


def test_set_pdf():
    from pypdf import PdfReader
    hal, hilang = gs.daftar_halaman()
    assert len(PdfReader(str(gs.PDF)).pages) >= len(hal) == 35 and hilang == []


def test_tabel_tiang_321():
    cs = g6.caps73()
    assert sum(r[4] for r in g6.rekap_cap(cs)) == 321
