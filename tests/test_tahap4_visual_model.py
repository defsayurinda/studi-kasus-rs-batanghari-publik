import sys
from pathlib import Path

import openpyxl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap4_visual_model as tv  # noqa: E402
import tahap4_model as tm  # noqa: E402

NAMA = ["01_model_3d", "02_ragam_1", "03_ragam_2", "04_ragam_3", "05a_deformasi_gempa_X",
        "05b_deformasi_gempa_Y", "06a_momen_portal", "06b_geser_portal"]


@pytest.fixture(scope="module")
def hasil():
    return tv.buat_semua()


def test_berkas_dibuat_dan_resolusi(hasil):
    from PIL import Image
    for n in NAMA:
        f = tv.KELUAR / f"{n}.png"
        assert f.exists()
        assert Image.open(f).width >= 2400


def test_periode_cocok_ragam(hasil):
    rg = tm.ragam("K2", n=3)
    assert hasil["T"] == pytest.approx(rg["T"][:3], rel=1e-9)


def test_periode_cocok_excel(hasil):
    ws = openpyxl.load_workbook(tm.KELUAR / "4.3 Analisis Struktur.xlsx", data_only=True)
    nilai = [c.value for s in ws for r in s.iter_rows() for c in r if isinstance(c.value, (int, float))]
    for t in hasil["T"]:
        assert any(abs(v - t) < 5e-4 for v in nilai), t
