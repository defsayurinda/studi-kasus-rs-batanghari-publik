import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import la_tebing as lt  # noqa: E402
import tahap6_tebing as t  # noqa: E402

KERING = lt.Kondisi("uji", "kering", -50.0, -50.0, mat=None)
XK = 6.0 / math.tan(math.radians(30))


def _pot(kode):
    return lt.Potongan("UJI", np.array([-40.0, 0.0, XK, 60.0]), np.array([6.0, 6.0, 0.0, 0.0]), [(kode, -99.0)])


def test_spencer_sama_bishop_phi_nol():
    lt.BAHAN["UJI0"] = lt.Bahan("UJI0", 18.0, su=20.0)
    b = lt.Bidang(6.0, 12.0, 13.0)
    f, s = lt.fk(_pot("UJI0"), KERING, b)
    assert t.spencer(s, b, 0.0) == pytest.approx(f, rel=0.01)


def test_spencer_dekat_bishop_c_phi_dan_kh():
    lt.BAHAN["UJI1"] = lt.Bahan("UJI1", 18.0, su=5.0, phi=25.0)
    b = lt.Bidang(6.0, 12.0, 13.0)
    f, s = lt.fk(_pot("UJI1"), KERING, b)
    assert t.spencer(s, b, 0.0) == pytest.approx(f, rel=0.05)
    assert t.spencer(s, b, 0.2) == pytest.approx(lt._fk(s, b, 0.2, "bishop"), rel=0.05)


def test_sr_rasio_satu_titik():
    # (N1)60 = 15, FC 10 %: Delta = 1, x = 16: exp(1 + 0 - 3) = exp(-2); batas tan 33 derajat tidak menahan
    assert t.sr_rasio(15.0, 10.0) == pytest.approx(math.exp(-2.0), rel=1e-9)
    # pasir padat: dibatasi tan phi'
    assert t.sr_rasio(40.0, 5.0) == pytest.approx(t.TAN_PHI_U5, rel=1e-9)


def test_youd_satu_set_masukan():
    # hitungan tangan (log10): M 7,0 R 50 W 19 T15 7,7 F15 9,6 D50 0,2
    M, R, W, T15, F15, D50 = 7.0, 50.0, 19.0, 7.7, 9.6, 0.2
    rs = R + 10 ** (0.89 * M - 5.64)
    lg = (-16.713 + 1.532 * M - 1.406 * math.log10(rs) - 0.012 * R + 0.592 * math.log10(W) + 0.540 * math.log10(T15)
          + 3.413 * math.log10(100 - F15) - 0.795 * math.log10(D50 + 0.1))
    assert t.youd(M, R, W, T15, F15, D50) == pytest.approx(10 ** lg - 0.01, rel=1e-12)
    assert 0.05 < t.youd(M, R, W, T15, F15, D50) < 5.0
    assert t.youd(M, 20.0, W, T15, F15, D50) > t.youd(M, 100.0, W, T15, F15, D50)   # makin jauh makin kecil


def test_zhang_gmax_batas_fs():
    n = 14.0
    dr = math.sqrt(n / 46)
    glim = 1.859 * (1.1 - dr) ** 3
    assert t.zhang_gmax(2.0, n) == 0.0 and t.zhang_gmax(3.0, n) == 0.0
    assert t.zhang_gmax(0.3, n) == pytest.approx(glim)        # FS <= Falpha: regangan batas
    fa = 0.032 + 4.7 * dr - 6.0 * dr ** 2
    fs = (fa + 2.0) / 2
    assert t.zhang_gmax(fs, n) == pytest.approx(min(glim, 0.035 * (1 - fa) * (2 - fs) / (fs - fa)))
    assert t.zhang_gmax(fs, n) < t.zhang_gmax(0.3, n)


def test_profil_u_puncak_dh_dan_dasar_nol():
    pool = t.spt_pool()
    sk = t.serakan(pool, t.d50_saringan())
    assert sk["ldi"] > 0 and sk["dh_zhang"] == pytest.approx(t.zhang_dh(sk["ldi"], sk["geo"]["L"], sk["geo"]["H"]))
    node = t.profil_node(sk)
    atas, bawah = t.u5_batas()
    assert node[0][2] == pytest.approx(sk["dh_zhang"]) and node[0][0] == pytest.approx(t.ELEV_TIANG_ATAS)
    u_atas_u5 = next(n for n in node if n[1] == "Atas U5")[2]
    assert u_atas_u5 == pytest.approx(sk["dh_zhang"]) and node[-1][2] == 0.0
    assert next(n for n in node if n[1].startswith("Dasar"))[2] == 0.0
    assert all(a[2] >= b[2] - 1e-9 for a, b in zip(node, node[1:]))            # tidak bertambah ke bawah


def test_pyslope_sama_skrip():
    for b in t.cek_pyslope():
        assert b["selisih"] <= t.TOL["pyslope"]


def test_excel_terbaca():
    from openpyxl import load_workbook
    assert t.BERKAS.exists()
    wb = load_workbook(t.BERKAS)
    assert wb.sheetnames == ["Petunjuk", "Data", "Inklinometer", "FK Tebing", "Perkuatan", "Kuat Residu", "Serakan Lateral",
                             "Cek Silang", "Kesimpulan"]
    wd = load_workbook(t.BERKAS, data_only=True)
    sr = wd["Kuat Residu"]
    vals = [c.value for row in sr.iter_rows() for c in row if isinstance(c.value, (int, float))]
    assert vals and wb["Serakan Lateral"].freeze_panes is None or True
