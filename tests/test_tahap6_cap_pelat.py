import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap6_cap_pelat as cp  # noqa: E402
import tahap6_struktur as ts  # noqa: E402
import tahap6_tata_letak as tl  # noqa: E402


@pytest.fixture(scope="module")
def cap():
    c = next(x for x in tl.rancang("a")[1] if x["kode"] == "E")
    ts.muatan_tiang_cap(c)
    return c


@pytest.fixture(scope="module")
def a(cap):
    return cp.analisis(cap, ts.H_E)


def test_keseimbangan_reaksi(a):
    """Σ reaksi pegas = Σ P beban (Pu maks, tanpa berat sendiri) dalam 0,5 %; pembanding cap kaku 6.3 maksimum dalam 25 %."""
    b = a["banding"]
    assert b["d_sum"] <= 0.5 and b["d_max"] <= 25.0 and b["lolos"]


def test_simetri_beban_simetris():
    """Cap 3 x 3 tiang dengan satu kolom di tengah: reaksi simetris terhadap kedua sumbu dan Σ = P."""
    pos = [(x, y) for x in (0.0, 2.4, 4.8) for y in (0.0, 2.4, 4.8)]
    titik = [dict(nama="K", x=2.4, y=2.4, Pu=9000.0, Pumin=9000.0, Mux=0.0, Muy=0.0)]
    c = dict(pos=pos, titik=titik, ukuran=(6.4, 6.4), r=dict(n=9, A=6.4 * 6.4, W=0.0))
    ts.muatan_tiang_cap(c)
    r = cp._solve(c, 1000.0, "maks", 0.0, 43000.0)["R"].reshape(3, 3)
    assert r.sum() == pytest.approx(9000.0, rel=1e-6)
    assert r == pytest.approx(r[::-1, :], rel=1e-6) and r == pytest.approx(r[:, ::-1], rel=1e-6)
    assert r[1, 1] > r[0, 0]            # pelat melendut: tiang tengah paling terbebani


def test_wood_armer_tangan():
    """mx 100, my 50, mxy 30 -> bawah (130; 80). mx -100, my 100, mxy 60 -> bawah x 0, y = 100 + 60²/100 = 136."""
    bx, by = cp.wood_armer(np.array([100.0]), np.array([50.0]), np.array([30.0]))
    assert (bx[0], by[0]) == pytest.approx((130.0, 80.0))
    bx, by = cp.wood_armer(np.array([-100.0]), np.array([100.0]), np.array([60.0]))
    assert (bx[0], by[0]) == pytest.approx((0.0, 136.0))


def test_rasio_desain(a, cap):
    """h Cap E (6.7, 2.000) lolos dengan pons inti penentu < 1; 1.900 dan 1.500 gagal; φVc per meter = 0,75 · 0,17 √35 · 1000 d."""
    assert a["lolos"] and a["penentu"] == "pons_inti" and 0.9 < a["rasio"]["pons_inti"] < 1.0
    assert a["geser"]["phiVc"] == pytest.approx(0.75 * 0.17 * 35 ** 0.5 * a["d"], rel=1e-6)
    assert not cp.analisis(cap, 1900.0)["lolos"] and not cp.analisis(cap, 1500.0)["lolos"]


def test_png_ada(a, cap, tmp_path):
    f = cp.gambar(a, cap, tmp_path / "pelat.png")
    assert Path(f).exists() and Path(f).stat().st_size > 10000
