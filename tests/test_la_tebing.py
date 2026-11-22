import math
import sys
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import Point, Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import la_tebing as lt  # noqa: E402


def _lereng_homogen(kode, h=6.0, sudut=30.0):
    """Lereng sederhana: puncak +h di x ≤ 0, kaki +0 di x = h / tan(sudut), satu bahan sampai -40."""
    xk = h / math.tan(math.radians(sudut))
    xs = np.array([-40.0, 0.0, xk, 60.0])
    zs = np.array([h, h, 0.0, 0.0])
    return lt.Potongan("UJI", xs, zs, [(kode, -99.0)])


KERING = lt.Kondisi("uji", "kering", -50.0, -50.0, mat=None)


def test_lingkaran_phi_nol_sama_hitungan_tangan():
    """φ = 0: FK = c L R / (γ A d), A dan titik berat dari poligon shapely (cara independen)."""
    lt.BAHAN["UJI0"] = lt.Bahan("UJI0", 18.0, su=20.0)
    pot = _lereng_homogen("UJI0")
    b = lt.Bidang(6.0, 12.0, 13.0)
    f, s = lt.fk(pot, KERING, b, "bishop")
    f_fel, _ = lt.fk(pot, KERING, b, "fellenius")
    tanah = Polygon([(-40, -40), (-40, 6), (0, 6), (6 / math.tan(math.radians(30)), 0), (60, 0), (60, -40)])
    massa = tanah.intersection(Point(b.xo, b.yo).buffer(b.r, 4096))
    # titik potong lingkaran dengan permukaan: dari batas poligon massa (bukan dari skrip)
    xs_m = [x for x, y in massa.exterior.coords]
    x1, x2 = min(xs_m), max(xs_m)
    L = b.r * (math.asin((x2 - b.xo) / b.r) - math.asin((x1 - b.xo) / b.r))
    tangan = 20.0 * L * b.r / (18.0 * massa.area * (b.xo - massa.centroid.x))
    assert f == pytest.approx(tangan, rel=0.01)
    assert f_fel == pytest.approx(f, rel=1e-4)  # φ = 0 dan lingkaran: Bishop = Fellenius


def test_pyslope_lereng_c_phi():
    """Cek silang pencarian dengan pyslope (Bishop): c 5 kPa, φ 25°, γ 18, H 6 m, 30°: pyslope 1,452."""
    lt.BAHAN["UJI1"] = lt.Bahan("UJI1", 18.0, su=5.0, phi=25.0)  # su dipakai sebagai c' bila φ' > 0
    pot = _lereng_homogen("UJI1")
    f, b, s = lt.cari(pot, KERING)
    assert f == pytest.approx(1.452, rel=0.05)


def test_kh_dan_muka_air():
    assert lt.KH == pytest.approx(0.5 * 0.3416, abs=1e-3)  # SNI 8460 Pasal 12.2.7: 0,5 PGAM
    assert lt.MA_NORMAL == pytest.approx(6.367, abs=0.01)  # rata-rata 12 bulan TOR Lampiran A
    assert lt.MA_Q50 == pytest.approx(11.85, abs=0.01)
    assert lt.FK_IZIN["statis"][0] == 1.5 and lt.FK_IZIN["gempa"][0] == 1.1


def test_beban_jalur_penyangga_p2():
    """Zona labil x 70-110: P-2 (x 90) jalur penyangga y 15,5-25,5 urugan 1 m; di luar zona labil tanpa jalur."""
    pot = lt.potongan("P-2")
    assert lt.tp.kedalaman_sempadan(90) == pytest.approx(15.5)
    assert pot.q(-20.0) == pytest.approx(19.0 * 1.0 + 10.0)
    assert pot.q(-10.0) == 0.0  # ruang sempadan tidak diurug
    assert pot.q(-30.0) > pot.q(-20.0)  # halaman +12,05 di utara jalur
    assert len(lt.potongan("P-1").beban) == 1 and len(lt.potongan("P-3").beban) == 1


def test_bahan_bidang_licin_dan_longsoran():
    pot = lt.potongan("P-2")
    assert pot.bahan(2.5, 5.43) == "LICIN"  # BT-2 jarak 4,5 digeser -2 m (puncak Feb 2027)
    assert pot.bahan(13.0, 5.0) == "LONGSOR"  # BT-2K (jarak 15 → 13)
    assert pot.bahan(-20.0, 3.0) == "U4"
    assert pot.bahan(-20.0, 0.0) == "U5"
    assert lt.potongan("P-1").bahan(10.0, 5.43) == "U4"


def test_berm_menaikkan_fk_lingkaran_kaki():
    pot0, pot1 = lt.potongan("P-2", k_su=1.5), lt.potongan("P-2", k_su=1.5, berm=True)
    kon = lt.kondisi()[0]
    b = lt.Bidang(14.0, 20.0, 18.0)
    assert lt.fk(pot1, kon, b)[0] > lt.fk(pot0, kon, b)[0]
    assert lt.luas_berm(pot1) > 0


def test_saluran_pembuang():
    s = lt.saluran()
    assert s["volume"] == pytest.approx(649.5, abs=1.0)  # retensi Q10 langkah 3.3
    assert s["q_pompa"] >= s["volume"] / (6 * 3600)
    assert s["q_pipa"] > s["q_pra"]  # pipa gravitasi Ø400 mampu mengalirkan laju izin
    assert s["jarak_labil"] >= 15.0 and s["jarak_longsor"] >= 25.0
    assert s["invert"] == pytest.approx(9.70)
