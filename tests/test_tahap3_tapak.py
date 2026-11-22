import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap3_tapak as tp  # noqa: E402


def test_sta_dari_tenggara_cocok_tor():
    # STA 0+000 di sudut tenggara: x = 140 - STA. Puncak di x 0 dan x 120 sama dengan TOR Lampiran B.
    s = {r[3]: r for r in tp.sempadan()}
    assert s[0.0][0] == 140 and s[0.0][1] == tp.TEBING_2026[0]
    assert s[120.0][1] == tp.TEBING_2026[120]


def test_garis_sempadan_20_m_dari_puncak():
    for d in tp.cek_sempadan():
        assert math.isclose(d["garis"], d["garis_hitung"], abs_tol=1e-9)


def test_luas_sempadan_tangan():
    # trapesium tabel: sum((x2-x1)*(s1+s2)/2), langkah 10 m
    s = [r[2] for r in tp.sempadan()]
    tangan = sum(10 * (a + b) / 2 for a, b in zip(s[:-1], s[1:]))
    assert math.isclose(tp.ruang_sempadan().area, tangan, rel_tol=1e-9)


def test_lahan_perencanaan_dan_kdb():
    r = tp.ringkasan()
    # 12.600 - sempadan - rumija utara 280 - rumija barat 1 × (88 - 6)
    assert math.isclose(r["lahan_perencanaan"], 12600 - r["sempadan"] - 280 - 82, abs_tol=0.05)  # jalur barat di atas garis sempadan yang miring
    assert math.isclose(r["kdb_maks"], 0.5 * r["lahan_perencanaan"])
    assert r["kdb_maks"] < r["owner_tapak"]  # arahan owner 6.300 m² melampaui KDB


def test_amplop_dua_cara():
    for lantai, labil in ((6, True), (6, False), (4, True)):
        a = tp.amplop(lantai, labil).area
        assert abs(a - tp.luas_amplop_strip(lantai, labil)) / a < 0.001


def test_zona_labil_40_x_10():
    assert math.isclose(tp.zona_labil().area, 400, rel_tol=1e-6)
