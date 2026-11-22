import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap2_parameter as tp  # noqa: E402


def test_sigma_p_bilinear_garis_ideal():
    # kurva buatan: datar 0,05/log sampai 50 kPa, lalu 0,8/log
    import numpy as np
    s = [6.25, 12.5, 25, 50, 100, 200, 400, 800]
    e = [2.0 - 0.05 * math.log10(x / 6.25) if x <= 50 else 2.0 - 0.05 * math.log10(8) - 0.8 * math.log10(x / 50)
         for x in s]
    assert abs(tp.sigma_p_bilinear(list(zip(s, e))) - 50) < 1.0
    assert np.isclose(e[0], 2.0)


def test_konsolidasi_dan_bh5():
    k = {(x["titik"], x["contoh"]): x for x in tp.konsolidasi()}
    assert k[("BH-5", "UD-1")]["sp_lab"] == 100 and k[("BH-5", "UD-1")]["sp_bil"] < 60
    assert not k[("BH-2", "UD-2")]["dipakai"]


def test_rangkak_sesuai_gec5():
    for r in tp.rangkak():
        batas = (0.05, 0.07) if r["titik"] == "BH-7" else (0.03, 0.05)
        assert batas[0] <= r["rasio"] <= batas[1]


def test_spt_phi_rumus():
    x = tp.spt_pasir()[0]
    assert math.isclose(x["phi"], math.sqrt(15.4 * x["n160"]) + 20)
    assert x["cn"] <= 2


def test_disipasi_t50_cptu5():
    d = {(x["cptu"], x["z"]): x for x in tp.disipasi_ch()}
    assert d[("CPTu-5", 9)]["t50"] > 60  # penyedia menulis 45 menit
    assert d[("CPTu-8", 24)]["t50"] is None
