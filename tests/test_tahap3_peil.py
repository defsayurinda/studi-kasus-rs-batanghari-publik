import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap3_peil as pl  # noqa: E402


def test_yn_sn_sama_tabel_penyedia():
    # penyedia (lembar Analisis Frekuensi): n 37, Yn 0,5417, Sn 1,1339
    yn, sn = pl.yn_sn(37)
    assert abs(yn - 0.5417) < 5e-5 and abs(sn - 1.1339) < 5e-5


def test_reproduksi_q50_penyedia():
    x = [e for _, e in pl.deret(koreksi_nol=False, buang_tidak_lengkap=False)]
    assert len(x) == 37
    assert abs(pl.gumbel_yn_sn(x, 50) - 11.73) < 0.01  # penyedia 11,73 m lokal


def test_koreksi_nol_papan_dan_1999():
    d = dict(pl.deret())
    assert 1999 not in d and len(d) == 36
    # 2003: bacaan 9,99 + nol 3,500 - 1,840 = 11,65
    assert math.isclose(d[2003], 9.99 + 3.5 - 1.84, abs_tol=1e-9)
    assert math.isclose(d[2017], 11.20, abs_tol=1e-6)  # AWLR tidak berubah


def test_q50_terkoreksi_sama_balai():
    assert abs(pl.muka_air(50) - (pl.Q50_BALAI_DPL + pl.DPL_KE_LOKAL)) < 0.02


def test_momen_rumus_tangan():
    x = [1.0, 2.0, 3.0, 4.0]
    k = -math.sqrt(6) / math.pi * (0.5772156649 + math.log(math.log(100 / 99)))
    sd = (sum((v - 2.5) ** 2 for v in x) / 3) ** 0.5
    assert math.isclose(pl.gumbel_momen(x, 100), 2.5 + k * sd, rel_tol=1e-9)


def test_peil_usulan_di_atas_q100():
    p = pl.peil_usulan()
    assert p["lantai"] >= p["q100"] + 0.5 - 1e-9
    assert p["halaman"] >= p["q50"]


def test_topografi_tor():
    xs, ys, z = pl.topografi()
    assert z.shape == (7, 8) and z[0, 0] == 10.45 and z[-1, -1] == 8.81  # y 0 x 0; y 90 x 140


# ------------------------------------------------------------------ LA.2: Log-Pearson III dan uji kecocokan
def test_k_lp3_skew_nol_sama_normal():
    # Cs = 0: K = z (sebaran normal); T = 100 → z = 2,3263
    assert math.isclose(pl.k_lp3(0.0, 100), 2.326348, abs_tol=1e-6)


def test_k_lp3_tabel_cs_positif():
    # tabel K Pearson III (Chow dkk. 1988 Tabel 12.3.1): Cs 0,6, T 100 → 2,755; T 50 → 2,359
    assert abs(pl.k_lp3(0.6, 100) - 2.755) < 0.005 and abs(pl.k_lp3(0.6, 50) - 2.359) < 0.005


def test_lp3_dua_cara_cocok_1_persen():  # T-52
    x = [e for _, e in pl.deret()]
    for T in pl.T_LP3:
        assert abs(pl.lp3_k(x, T) / pl.lp3_scipy(x, T) - 1) < 0.01


def test_statistik_log_hitung_tangan():
    x = [10.0, 100.0, 1000.0, 10000.0]  # log10 = 1, 2, 3, 4: simetris
    st = pl.statistik_log(x)
    assert math.isclose(st["rata"], 2.5) and math.isclose(st["sd"], (5 / 3) ** 0.5) and abs(st["cs"]) < 1e-12


def test_uji_kecocokan_semua_diterima():
    u = pl.uji_kecocokan()
    for d, v in u.items():
        assert sum(v["chi2"]["O"]) == 36
        assert v["chi2"]["lolos"] and v["ks"]["lolos"], d
    assert u["lp3"]["chi2"]["dk"] == 2 and u["gumbel_yn"]["chi2"]["dk"] == 3
    assert abs(u["lp3"]["ks"]["kritis"] - 1.36 / 6) < 0.01  # eksak ≈ asimtotik untuk n = 36


def test_ks_cdf_gumbel_konsisten_dengan_kuantil():
    x = [e for _, e in pl.deret()]
    f = pl._cdf("gumbel_yn", x)
    assert math.isclose(float(f(pl.gumbel_yn_sn(x, 100))), 0.99, abs_tol=1e-9)
    g = pl._cdf("lp3", x)
    assert math.isclose(float(g(pl.lp3_scipy(x, 100))), 0.99, abs_tol=1e-9)


def test_peil_disetujui_aman_semua_metode():
    for c in pl.cek_peil():
        assert c["lantai_ok"] and c["halaman_ok"] and c["halaman_jagaan_ok"], c["metode"]
    assert pl.distribusi_terpilih()["terbaik"] == "gumbel_yn"


def test_excel_lp3_sama_python():
    import openpyxl
    from format_dokumen import baca_tabel

    ws = openpyxl.load_workbook(pl.BERKAS, data_only=True)["LP3 dan Uji"]
    a = [r for r in baca_tabel(ws, "Besaran")[1] if isinstance(r[2], (int, float))]  # tanpa baris catatan
    b = [r for r in baca_tabel(ws, "T (tahun)")[1] if isinstance(r[0], int)]
    assert len(a) == 4 and len(b) == len(pl.T_LP3)
    if a[1][1] in ("", None):
        import pytest

        pytest.skip("nilai Excel belum dihitung ulang (jalankan tahap3_peil.py --excel)")
    for besaran, excel, python, _ in a:
        assert abs(excel - python) < 1e-5, besaran
    x = [e for _, e in pl.deret()]
    for r in b:
        assert abs(r[3] - pl.lp3_k(x, r[0])) < 1e-6 and abs(r[4] - pl.lp3_scipy(x, r[0])) < 1e-6
