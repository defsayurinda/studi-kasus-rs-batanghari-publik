import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap2_kimia_tebing_gudang as k  # noqa: E402


def test_kelas_sulfat_sni2847():
    assert k.kelas_s_tanah(0.09) == "S0" and k.kelas_s_tanah(0.17) == "S1" and k.kelas_s_tanah(0.24) == "S2"
    assert k.kelas_s_air(310) == "S1" and k.kelas_s_air(38) == "S0"


def test_konversi_so3_t2():
    t = {x["Kode"]: x for x in k.kimia()[0]}
    assert abs(t["T-2"]["so4"] - 0.2 * 96.06 / 80.06) < 1e-9
    assert t["T-1"]["agresif"] and not t["T-4"]["agresif"]


def test_koreksi_batimetri_p3():
    p = [t for t in k.penampang("P-3") if t["kedalaman"]]
    assert all(abs((t["elev"] - t["elev_kor"]) - 0.41) < 0.011 for t in p)


def test_patok_gt7_dikoreksi():
    _, pk = k.patok()
    g7 = next(p for p in pk if p["patok"] == "GT-7")
    assert g7["d_kor"][-1] > -3 and g7["d"][-1] < -10


def test_kategori_ciria():
    assert k.kategori_ciria(1 / 600) == 1 and k.kategori_ciria(1 / 54) == 3 and k.kategori_ciria(1 / 40) == 4
