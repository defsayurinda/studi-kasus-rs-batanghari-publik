import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap3_pondasi as fd  # noqa: E402


def test_gesekan_u6_tangan():
    # Ø800 di U6 (19,30-33,55 m): 0,55 × 85 × π × 0,8 × 14,25
    k = fd.kapasitas("BOR-800")
    qs_u6 = 0.55 * 85 * math.pi * 0.8 * (33.55 - 19.30)
    assert qs_u6 < k["Qs"] < qs_u6 * 1.6  # sisanya gesekan 4 m di U7


def test_ujung_u7():
    k = fd.kapasitas("BOR-800")
    assert math.isclose(k["Qb"], 57.5 * 30 * math.pi * 0.8 ** 2 / 4)


def test_sigma_v_dengan_urugan():
    h, du = fd.urugan()
    assert math.isclose(du, 19 * h) and fd.sigma_v(0.0) == du
    assert fd.sigma_v(9.46) > fd.sigma_v(1.62) > du


def test_beban_izin_fk_dan_nsf():
    b = fd.beban_izin("BOR-800")
    assert math.isclose(b["statis"], b["Qult"] / 2.5 - b["NSF_statis"])
    assert math.isclose(b["likuifaksi"], b["Qult"] / 1.1 - b["NSF_lik"])
    assert b["izin"] == min(b["statis"], b["likuifaksi"]) > 0


def test_opsi_a_tanpa_pancang_dan_c_jauh_dari_gudang():
    assert fd.opsi("A")["jarak_pancang_gudang"] is None
    assert fd.opsi("C")["jarak_pancang_gudang"] >= 50
    assert fd.opsi("B")["biaya"] < fd.opsi("C")["biaya"] < fd.opsi("A")["biaya"] < fd.opsi("D")["biaya"]


def test_tiang_cukup_untuk_kolom_terberat():
    pa = fd.beban_izin("BOR-800")["izin"]
    for c in fd.n_tiang("BOR-800", fd.beban_kolom()):
        assert c["n"] * pa >= c["P"]
