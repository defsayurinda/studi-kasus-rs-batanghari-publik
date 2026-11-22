import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import la1_zona as lz  # noqa: E402
import tahap3_pondasi as fd  # noqa: E402


def test_profil_selatan_sama_dengan_3_7():
    assert math.isclose(fd.beban_izin("BOR-800")["izin"], fd.beban_izin("BOR-800", "SELATAN")["izin"])


def test_nsf_utara_lebih_besar_dan_izin_lebih_kecil():
    s, u = fd.beban_izin("BOR-800", "SELATAN"), fd.beban_izin("BOR-800", "UTARA")
    assert u["NSF_statis"] > s["NSF_statis"] and u["izin"] < s["izin"]


def test_nsf_tangan_dalam_toleransi():
    assert abs(lz.nsf_tangan() / fd.beban_izin("BOR-800", "UTARA")["NSF_statis"] - 1) < 0.10


def test_zona_dari_gambut():
    assert fd.zona(55, 78) == "UTARA" and fd.zona(30, 15) == "SELATAN"


def test_tiang_per_zona_tidak_kurang():
    a, b = lz.tiang(False), lz.tiang(True)
    assert b["n"] >= a["n"]
    izin = {z: fd.beban_izin("BOR-800", z)["izin"] for z in fd.PROFIL}
    for c in b["rincian"]["utama"] + b["rincian"]["gu"]:
        assert c["n"] * izin[c["zona"]] >= c["P"]


def test_opsi_b_lebih_banyak_di_zona_baik():
    p = lz.porsi_baik()
    a = (p["a podium"]["baik"] + p["a gedung utilitas"]["baik"]) / (p["a podium"]["luas"] + p["a gedung utilitas"]["luas"])
    b = (p["b podium"]["baik"] + p["b gedung utilitas"]["baik"]) / (p["b podium"]["luas"] + p["b gedung utilitas"]["luas"])
    assert b > a and p["b podium"]["luas"] >= 72 * 48
