import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import laporan_antara as la  # noqa: E402


def test_laporan_ada_dan_berisi_bab_wajib():
    assert la.KELUAR.exists() and la.PDF.exists()
    teks = "\n".join(p.text for p in Document(la.KELUAR).paragraphs).upper()
    for kata in ("PARAMETER TANAH DESAIN", "KONSEP STRUKTUR", "KONSEP PONDASI", "BIAYA DAN PENTAHAPAN",
                 "KEPUTUSAN YANG DIMINTA"):
        assert kata in teks


def test_tindak_lanjut_rapat_lengkap():
    doc = Document(la.KELUAR)
    t = next(t for t in doc.tables if t.rows[0].cells[1].text.strip() == "Tindak lanjut")
    assert len(t.rows) - 1 == 13
