import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap2_stratigrafi as st  # noqa: E402


def test_golongan_unit():
    assert st.unit_dari_teks("Tanah urug: lanau kepasiran coklat") == ("U1", "")
    assert st.unit_dari_teks("Gambut/lempung organik coklat tua")[0] == "U3"
    assert st.unit_dari_teks("Pasir halus-sedang kelanauan abu-abu, agak padat") == ("U5", "b")
    assert st.unit_dari_teks("Pasir halus-sedang abu-abu terang, padat")[0] == "U7"
    assert st.unit_dari_teks("Lempung kelanauan abu-abu kebiruan, kaku")[0] == "U6"


def test_titik_dan_tebal_organik():
    t = {x["nama"]: x for x in st.semua_titik()}
    assert len(t) == 26
    assert abs(st.tebal_organik(t["BH-3"]) - 2.84) < 0.01
    assert st.tebal_organik(t["BH-5"]) == 0
    assert t["HA-9"]["org_terbuka"]
    # batas CPTu dan bor berdekatan cocok dalam 0,5 m (elevasi)
    for c, b in [("CPTu-2", "BH-2"), ("CPTu-5", "BH-3")]:
        for u in ("U4", "U5", "U6"):
            ec = t[c]["elev"] - st.atas_unit(t[c], u)
            eb = t[b]["elev"] - st.atas_unit(t[b], u)
            assert abs(ec - eb) <= 0.5
