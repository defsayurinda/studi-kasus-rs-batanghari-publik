"""Uji ringan 7.4 (tanpa CADCraft): daftar lembar, nama berkas, muat A3."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap7_gambar_ars as ga  # noqa: E402
import tahap7_telaah as tt  # noqa: E402


def test_daftar_lengkap():
    assert list(ga.LEMBAR) == [f"GA-{i:02d}" for i in range(1, 24)]
    assert {n for n, *_ in tt.GA} == set(ga.LEMBAR)


def test_nama_berkas():
    assert ga.nberkas("GA-04").name == "GA-04 Denah LT1 Barat.dwg"
    assert all(len(ga.LEMBAR[n][0]) < 30 for n in ga.LEMBAR)


def test_denah_muat_a3():
    # viewport tinggi penuh 307 x 249 mm; denah setengah 1:250: lebar 58 m, tinggi 62 m
    skala = 250
    assert 58 * 1000 / skala <= 307 and 62 * 1000 / skala <= 249
    assert set(ga.GA_DENAH) == {"GA-04", "GA-05", "GA-06", "GA-07", "GA-08", "GA-09"}


def test_kode_pintu_dan_tata():
    assert ga.kode_pintu(900, 2100) == "P1" and ga.kode_pintu(1400, 2400) == "PL"
    assert ga.idn(1234.56, 1) == "1.234,6"
