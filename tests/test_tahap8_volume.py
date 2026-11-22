import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "skrip"))
import tahap8_volume as tv  # noqa: E402


def test_koef_bor_sama_contoh_se47():
    # SE 47/2026 Lampiran II hal. 188: p 25,4 m, Ts 225 menit -> 0,1779 jam/m'
    assert tv.koef_bor(25.4) == pytest.approx(0.1779, abs=1e-4)


def test_kelompok_dan_besi_tiang():
    assert tv.kelompok_str("IfcSlab", "PL-250-fc35") == "Pelat lantai 1"
    assert tv.kelompok_str("IfcSlab", "PIT-400-fc35") == "Pit lift"
    assert tv.kelompok_str("IfcBeam", "SL-400x900-fc35") == "Sloof dan balok pondasi"
    assert tv.kelompok_str("IfcReinforcingBar", "Bar 13") is None
    # tangan: L 38,8 -> l_tul 29,86; 16 D25 1.839,4 kg + spiral 2,0 m × 1,04 × (150 + 298,3) = 932,4 kg
    assert tv.besi_tiang(38.8) == pytest.approx(2771.8, rel=0.005)


def test_ahsp_besi_tangan():
    h = tv.harga_satuan("A4", tv.ahsp(38.8))
    tangan = 1.05 * 13_500 + 0.015 * 25_000 + 0.007 * 130_000 + 0.007 * 160_000 + 0.0007 * 175_000 + 0.0004 * 190_000
    assert h["langsung"] == pytest.approx(tangan)
    assert h["hsp"] == pytest.approx(tangan * 1.12)


def test_t119_t120_lolos():
    cs = tv.cek_silang()
    assert all(b["lolos"] for b in cs["baris"]), [b for b in cs["baris"] if not b["lolos"]]
    assert cs["pareto"]["lolos"]
    s = tv.volume_struktur()
    assert s["Tiang bor Ø800"]["n"] == 321 and s["Pile cap"]["n"] == 84
