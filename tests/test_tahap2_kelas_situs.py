import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap2_kelas_situs as ks  # noqa: E402


def test_vs30_rumus_tangan():
    # 10 m @ 100 + 20 m @ 300: 30 / (0,1 + 0,0667) = 180 m/s
    assert abs(ks.vs30([(0, 10, 100), (10, 30, 300)]) - 180) < 1e-9


def test_kelas():
    assert ks.kelas(vs=174.9) == "SE" and ks.kelas(vs=175) == "SD" and ks.kelas(vs=351) == "SC"
    assert ks.kelas(n=14.9) == "SE" and ks.kelas(su=50) == "SD"


def test_situs_se_dan_downhole_cocok_masw():
    m = ks.masw()
    assert all(ks.vs30(l) < 175 for l in m.values())
    assert abs(ks.downhole_vs30() - ks.vs30(m["L-1/57"])) / ks.vs30(m["L-1/57"]) < 0.05
    assert all(ks.n_rata(b) < 15 and ks.su_rata(b) < 50 for b in ks.ER)


def test_gambut_lebih_3m_di_utara():
    g = ks.tebal_gambut_ha()
    assert g["HA-8"] > 3 and g["HA-10"] > 3 and g["HA-3"] < 1
