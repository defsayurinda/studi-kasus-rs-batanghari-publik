import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap4_gambar_ded as gd  # noqa: E402


def test_daftar_gambar_berurutan():
    no = [d[0] for d in gd.DAFTAR]
    assert no == [f"GS-{i:02d}" for i in range(1, 21)]
    assert set(gd.LEMBAR) == set(no[2:])


def test_panjang_penyaluran():
    t = {db: (r, lw) for db, r, lw in gd.ld_tabel()}
    # D25 fc' 30 bawah: 420 / (1,7 √30) × 25 = 1.127,7 -> 1.150; lewatan B 1,3 ld -> 1.500
    assert t[25][0][0] == 1150 and t[25][1][0] == 1500
    # D13 fc' 30 atas (ψt 1,3): 420 × 1,3 / (2,1 √30) × 13 = 616 -> 650
    assert t[13][0][1] == 650


def test_kelompok_dan_kode():
    assert gd.kelompok_balok({"lv": "LT3", "p": (68.0, 67.0, 68.0, 75.0)}) == "B-T induk tangki x 68"
    assert gd.kode_balok(gd.kelompok_balok({"lv": "LT2", "p": (12.0, 27.0, 20.0, 27.0)})) == "B2"   # tepi
    assert gd.kode_balok(gd.kelompok_balok({"lv": "LT5", "p": (28.0, 35.0, 36.0, 35.0)})) == "B3"   # menara dalam
    assert gd.kode_kolom("K-T68 LT3") == "K4" and gd.kode_inti("Inti lif x50-58 y35-43") == "DG1"


def test_bersihkan_dxf(tmp_path):
    ezdxf = pytest.importorskip("ezdxf")
    doc = ezdxf.new()
    ms = doc.modelspace()
    ms.add_line((0, 0), (50, 0), dxfattribs={"layer": "wall"})                  # goresan huruf: dibuang
    ms.add_line((0, 0), (5000, 0), dxfattribs={"layer": "wall"})                # dinding: tetap
    ms.add_lwpolyline([(0, 0), (200, 0), (200, 200)], dxfattribs={"layer": "structuralcolumn"})   # tetap
    ms.add_line((0, 0), (9000, 0), dxfattribs={"layer": "grid"})                # anotasi BIM: dibuang
    p = tmp_path / "uji.dxf"
    doc.saveas(p)
    assert gd.bersihkan_dxf(p) == 2
    assert len(ezdxf.readfile(p).modelspace()) == 2
