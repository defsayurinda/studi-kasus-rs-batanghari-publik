import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap3_pondasi as t3  # noqa: E402
import tahap6_tiang_tunggal as t  # noqa: E402


def test_reproduksi_tahap3_911():
    rp = t.reproduksi_t3()
    assert abs(rp["SELATAN"]["izin"] - 911) < 1.0
    for v in rp.values():
        assert abs(v["dQ"]) < 0.5 and abs(v["dI"]) < 0.5


def test_panjang_selatan_38_45():
    assert abs(t.hitung("A", "SELATAN")["panjang"] - 38.45) < 0.01
    assert abs((t.KEPALA - (9.95 - 37.55)) - 38.45) < 1e-9


def test_u1_u4_nol_dan_u5_hanya_statis():
    for m in "ABC":
        for z in ("SELATAN", "UTARA"):
            r = t.hitung(m, z)
            assert all(r["per"][u]["Qs_st"] == 0 and r["per"][u]["Qs_gm"] == 0 for u in r["per"] if u in ("U1", "U2", "U3", "U4"))
            assert r["per"]["U5"]["Qs_gm"] == 0 and r["per"]["U5"]["Qs_st"] > 0


def test_gempa_lebih_kecil_dari_statis_dan_tarik_lebih_kecil_dari_tekan():
    for (m, z), r in t.semua().items():
        assert r["Qult_gm"] < r["Qult_st"]
        assert r["Tult_st"] < r["Qult_st"] and r["Tult_gm"] < r["Qult_gm"]


def test_metode_a_rumus_tangan():
    # U6 selatan: alpha = 0,30 + 0,17 / (85 / 101,325) = 0,5027; fs = 42,7 kPa
    r = t.hitung("A", "SELATAN")
    assert abs(r["per"]["U6"]["fs_rata"] - (0.30 + 0.17 / (85 / t.PA)) * 85) < 0.05
    # ujung: 0,6 N60 tsf, N60 30 -> 17,28 ... 1.723,7 kPa x luas Ø800
    assert abs(r["Qb"] - 0.6 * 30 * t.TSF * 3.141592653589793 * 0.8 ** 2 / 4) < 0.1


def test_sebaran_abc_dalam_30_persen():
    assert max(v["dev"] for v in t.sebaran().values()) < t.TOL["sebaran"]


def test_panjang_setara_t3_menurut_zona():
    pz = t.panjang_zona()
    assert pz["SELATAN"]["L_nsf"] == 37.5 and pz["UTARA"]["L_nsf"] == 36.5 and pz["TENGAH"]["L_nsf"] == 36.5
    assert all(pz[z]["izin_nsf"] >= 911 for z in pz)


def test_excel_sama_dengan_python():
    import openpyxl
    assert t.BERKAS.exists()
    ex = t.baca_excel()
    h = t.semua()
    assert len(ex) == 6
    for (m, z), e in ex.items():
        for k in ("Qult_st", "Qult_gm", "izin", "izin_t3"):
            assert abs(e[k] - h[(m, z)][k]) / h[(m, z)][k] < 0.005, (m, z, k)
    wb = openpyxl.load_workbook(t.BERKAS)
    assert wb["Ringkasan"].freeze_panes is not None
