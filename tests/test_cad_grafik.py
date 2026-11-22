"""Uji aturan gambar CAD (cad_grafik): jenis garis, teks, arsir unit tanah, pola .pat."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import cad_grafik as cg  # noqa: E402
import tahap2_stratigrafi as st  # noqa: E402
from cad_lembar import POLA_GT, prm_hatch  # noqa: E402


def test_jenis_garis():
    assert cg._jenis_garis(None) == "Continuous"
    assert cg._jenis_garis([1.0, 1.65]) == "DOT"
    assert cg._jenis_garis([3.7, 1.6]) == "HIDDEN"
    assert cg._jenis_garis([8, 3]) == "DASHED"
    assert cg._jenis_garis([6, 2, 2, 2]) == "DASHDOT"


def test_teks_desimal_koma_dan_mathtext():
    assert cg._teks("2.5") == "2,5"
    assert cg._teks("$\\mathdefault{10^{2}}$") == "10²"
    assert cg._teks("−5") == "-5"
    assert cg._teks("Sep 2026") == "Sep 2026"


def test_arsir_unit_tanah_lengkap_dan_ada_di_pat():
    pola = cg._warna_unit()
    teks = POLA_GT.read_text(encoding="utf-8")
    nama_pat = set(re.findall(r"^\*([^,]+)", teks, re.M))
    for u, v in st.UNIT.items():
        unit, p = pola[v[2].lower()]
        assert unit == u and p in nama_pat
    assert {"GT-AIR", "GT-LONGSOR"} <= nama_pat
    assert "patternText" in prm_hatch("GT-GAMBUT") and "patternText" not in prm_hatch("ANSI31")


def test_judul_kop_muat():
    assert len(cg.JUDUL_KOP) == 15
    assert all(len(v) <= 20 for v in cg.JUDUL_KOP.values())
