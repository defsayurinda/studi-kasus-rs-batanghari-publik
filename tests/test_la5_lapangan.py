import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import la5_lapangan as l5  # noqa: E402


def test_tarikan_dua_cara_dalam_toleransi():
    t = l5.tarikan_di_gudang()
    assert 0 < t["s_thiem"] < 1 and 0 < t["s_bayangan"] < 1
    assert abs(t["s_bayangan"] / t["s_thiem"] - 1) < 0.30


def test_penurunan_akibat_pompa_kecil():
    assert l5.penurunan_akibat_pompa()["penurunan_mm"] < 2.0


def test_patok_periode_pompa_seperti_derau():
    g = l5.ringkas_gudang()
    assert g["maks_periode_pompa"] < 2.1 and abs(g["rata_feb_mar"]) > abs(g["rata_periode_pompa"])


def test_jumlah_uji_tiang_sni_8460():
    j = l5.uji_tiang()
    assert j["statik"] == max(math.ceil(j["n_tiang"] / 75), math.ceil(0.01 * j["n_tiang"]))
    assert j["pra"] <= math.ceil(0.6 * j["statik"]) and j["csl"] == math.ceil(j["n_tiang"] / 20)


def test_timbunan_tahap1():
    t = l5.timbunan()
    assert math.isclose(t["kapasitas_tahap1"], t["luas"] * t["h1"]) and t["sisa_ditolak"] > 0
