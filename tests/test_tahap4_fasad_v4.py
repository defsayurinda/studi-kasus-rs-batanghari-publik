import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap4_fasad_v4 as v4  # noqa: E402


def test_huruf_blok():
    kotak, lebar = v4.kotak_huruf("H")
    assert lebar == 1000
    # H: dua tiang 1 × 7 sel (deret per baris) + palang 3 sel di baris tengah
    luas = sum((x1 - x0) * (z1 - z0) for x0, z0, x1, z1 in kotak)
    assert luas == (7 * 2 + 3) * v4.SEL_HURUF ** 2
    assert set(v4.NAMA_RS) <= set(v4.FONT)


def test_zona_sisi_selatan_menara():
    z = v4.zona_sisi((19.4, 26.4), (84.6, 26.4))
    jenis = [j for _, _, j in z]
    assert "tirai" in jenis and jenis.count("strip") == 2
    panjang = sum(abs(q1[0] - q0[0]) for q0, q1, _ in z)
    assert abs(panjang - 65.2) < 1e-9


def test_zona_sisi_podium_abu():
    z = v4.zona_sisi((11.4, 75.6), (11.4, 26.4))   # sisi barat podium
    assert {j for _, _, j in z} == {"pita_abu"}
