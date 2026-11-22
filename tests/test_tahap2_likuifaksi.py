import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap2_likuifaksi as lq  # noqa: E402


def test_fpga_dan_amax():
    assert abs(lq.fpga_se(0.1644) - 2.078) < 1e-3  # SNI 1726 Tabel 10 interpolasi
    assert abs(lq.AMAX - 0.1644 * 2.078) < 1e-3


def test_crr_titik_acuan_ib2014():
    # hitungan tangan Pers. 2.25, (N1)60cs = 30: exp(2,128 + 0,057 - 2,054 + 1,946 - 2,8) = exp(-0,723) = 0,485
    assert abs(lq.crr_spt(30) - 0.485) < 0.002
    # Pers. 2.24, qc1Ncs = 150: exp(1,327 + 0,0225 - 1,230 + 1,436 - 2,80) = exp(-1,244) = 0,288
    assert abs(lq.crr_cpt(150) - 0.288) < 0.002


def test_rd_dan_msf():
    assert 0.9 < lq.rd(3.0, 7.5) < 1.0
    assert math.isclose(lq.msf(7.5, 1.8), 1.0, abs_tol=0.01)  # MSF = 1 di M 7,5


def test_u5_likuifaksi():
    fs = [x["fs"] for x in lq.analisis_spt()]
    assert len(fs) == 38 and max(fs) < 1
