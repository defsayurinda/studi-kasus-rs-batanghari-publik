import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap4_besi as bs  # noqa: E402

# kelompok B-P dalam LT3 (4.6): atas 6D25 dua lapis (5 + 1), bawah 3D25, 3 kaki D10-100/100
B1 = {"b": 0.35, "h": 0.6, "ds": 10, "s_sendi": 0.1, "s_lap": 0.1, "samping": 0, "kaki": 3,
      "atas": {"n": 6, "n1": 5, "db": 25, "lapis": 2}, "bawah": {"n": 3, "n1": 3, "db": 25, "lapis": 1}}


def test_param_balok_baris_kedua():
    prm, atas2, bawah2 = bs.param_balok(B1)
    assert prm["top"] == {"count": 5, "diameter": 25} and prm["bottom"] == {"count": 3, "diameter": 25}
    assert atas2 == (1, 25) and bawah2 == (0, 25)
    assert prm["stirrup"]["ends"] == {"length": 1200, "spacing": 100} and prm["cover"] == 40
    assert "skin" not in prm


def test_param_balok_tepi_dan_samping():
    x = {**B1, "samping": 2}
    prm, _, _ = bs.param_balok(x, s_sendi=0.075, s_lap=0.075)
    assert prm["stirrup"]["spacing"] == 75 and prm["stirrup"]["ends"]["spacing"] == 75
    assert prm["skin"] == {"diameter": 13, "spacing": round((600 - 80) / 3)}


def test_kelompok_balok_khusus():
    assert bs.kelompok_balok("LT3", (60000, 71000, 76000, 71000)) == "anak tangki"
    assert bs.kelompok_balok("LT3", (60000, 53500, 76000, 53500)) == "rel chiller"
    assert bs.kelompok_balok("LT3", (68000, 67000, 68000, 75000)) == "B-T induk tangki x 68"
