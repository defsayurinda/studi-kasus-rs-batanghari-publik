import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap3_basement as bs  # noqa: E402


def test_fk_blowin_bh5_tangan():
    # BH-5: muka tanah +9,95; U2 sampai 1,62 m (+8,33); U4 sampai 9,46 m (+0,49); dasar galian +8,35
    sig = 17.8 * (8.35 - 8.33) + 15.2 * (8.33 - 0.49)
    u = 9.81 * (11.20 - 0.49)
    r = next(x for x in bs.blowin() if x["profil"].startswith("Tengah") and x["h"] == 11.20)
    assert math.isclose(r["fk"], sig / u, rel_tol=1e-6)
    assert r["fk"] < 1.25  # SNI 8460:2017 Pasal 10.3.6.7.2


def test_semua_profil_basement_tidak_aman():
    assert all(r["fk"] < 1.25 for r in bs.blowin())


def test_uplift_q100():
    up = bs.uplift()
    assert math.isclose(up["u"], 9.81 * (bs.tinggi_tekan()["3.3 Q100"] - bs.ELEV_DASAR_GALIAN))
    assert up["selisih"] > 0


def test_opsi_c_penuhi_kebutuhan_dan_pkkpr():
    c = next(o for o in bs.opsi() if o["opsi"] == "C")
    assert c["mobil"] >= bs.KEBUTUHAN["mobil"] and c["motor"] >= bs.KEBUTUHAN["motor"]
    k = bs.cek_opsi_c()
    assert k["tapak"] <= k["kdb"] and k["lantai"] <= k["klb"] and k["dalam_amplop"]
    assert bs.cek_kdh()["hijau"] >= bs.cek_kdh()["kdh_min"]


def test_opsi_d_kurang():
    d = next(o for o in bs.opsi() if o["opsi"] == "D")
    assert d["mobil"] < bs.KEBUTUHAN["mobil"]
