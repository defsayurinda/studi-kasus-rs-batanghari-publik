import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap4_pelat as tp  # noqa: E402
import tahap5_pelat_lt1 as t  # noqa: E402


@pytest.fixture(scope="module")
def r():
    return t.hitung()


def test_beban_qu_dan_mo_pl1(r):
    p = r["pl1"]
    assert p["D"] == pytest.approx(23.6 * 0.25 + 1.10 + 1.00)
    assert p["qu"] == pytest.approx(1.2 * 8.0 + 1.6 * 4.79, rel=1e-9)
    assert p["Mo"] == pytest.approx(p["qu"] * 8 * 7.25 ** 2 / 8, rel=1e-9)


def test_hmin_dan_geser_satu_arah(r):
    p = r["pl1"]
    assert p["af"] > 2.0 and p["hmin"] == pytest.approx(7.25 * (0.8 + 420 / 1400) / 45, rel=1e-6)
    assert p["hmin"] < t.H and p["Vu"] < p["phiVc"]


def test_tulangan_pl1_cukup_dan_memenuhi_syarat(r):
    for b in r["pl1"]["baris"]:
        assert b["db13"] == 13 and b["s13"] <= 450
        assert b["phimn13"] >= b["Mu"] and b["as13"] >= b["as_min13"] == pytest.approx(450.0)


def test_modul_lama_tetap_berperilaku_sama():
    a = tp.desain_panel(*tp.PANEL[0])
    b = tp.desain_panel(*tp.PANEL[0], selimut=tp.SELIMUT, fc=tp.FC, bw=tp.tb.BALOK_B, hb=tp.tb.BALOK_H)
    assert a["qu"] == b["qu"] and a["hmin"] == b["hmin"] and [x["Mu"] for x in a["baris"]] == [x["Mu"] for x in b["baris"]]
    assert [x["As"] for x in a["baris"]] == [x["As"] for x in b["baris"]]


def test_panel_mri_kombinasi_dan_tulangan(r):
    q = r["pl2"]
    assert q["pos_gov"] == "operasi" and q["tr_pos"] < q["op_pos"]
    assert q["mu_pos"] < q["bawah"]["phimn"] and q["mu_neg"] < q["atas"]["phimn"]
    assert q["bawah"]["db"] == 13 and q["bawah"]["s"] <= 200


def test_transit_posisi_dan_perbandingan_pynite(r):
    tr = r["transit"]
    assert 80.5 <= tr["xc_w"] <= 83.4 and tr["m_pos"] == max(tr["m_nav"], tr["m_pyn"])
    assert tr["m_pyn"] <= tr["m_nav"] * 1.05          # tapak elemen PyNite lebih lebar: tidak lebih besar dari Navier persegi 0,15
    assert tr["neg_pyn"] > 0 and r["penyebar"][-1]["M"] < r["penyebar"][0]["M"]


def test_pons_dan_tumpu(r):
    assert r["pons_kaki"]["rasio"] == pytest.approx(0.0301, abs=0.0005) and r["pons_roda"]["rasio"] == pytest.approx(0.0521, abs=0.0005)
    assert r["pons_roda"]["phivc"] == pytest.approx(369.1, rel=0.002) and r["tumpu"]["rasio"] < 0.02


def test_sh6_menembus_lt1_di_luar_zona(r):
    s6 = [x for x in r["lubang"] if x["kode"] == "SH-6"][0]
    assert "LT1" in s6["tembus"] and s6["di_zona"] == 0.0 and s6["jarak_iso"] > 1.0
    assert r["sh6_di_bukaan"] == 1 and s6["n_x"] >= 2


def test_baja_tahan_karat(r):
    k = r["tk"]
    assert k["ld"] == pytest.approx(439.5, abs=0.5) and k["pakai"] == 580 and k["pj"] == pytest.approx(3.16)
    assert k["jml"] == 44 and k["massa"] == pytest.approx(44 * 3.16 * 1.04, rel=0.005) and k["massa"] < 148.26


def test_getaran_opsi(r):
    g = r["getar"]
    assert g["A"]["fn"] == pytest.approx(11.67, abs=0.05) and g["A"]["fn_jepit"] > g["A"]["fn"]
    assert abs(g["B30"]["fn"] - 14.5) < 1.0 and g["B30"]["M-01"]["H"] > 10          # resonansi dengan kipas M-01
    assert g["B35"]["fn"] > g["B30"]["fn"] > g["A"]["fn"] and g["C"]["fn"] > g["A"]["fn"]
    assert r["isolasi"]["vol"] == pytest.approx(20 * 0.4 * 0.55)


def test_selimut_75_menambah_kebutuhan_tulangan(r):
    a = r["alt_sel"]
    assert a[0.075]["as"] > a[0.05]["as"] and a[0.075]["pl2_rasio"] > a[0.05]["pl2_rasio"]


def test_t92_cek_silang(r):
    x = r["t92"]
    assert x["a"]["qu_skrip"] == pytest.approx(x["a"]["qu_tangan"], rel=0.005) and x["a"]["mo_skrip"] == pytest.approx(x["a"]["mo_tangan"], rel=0.005)
    assert x["b"]["pynite"] == pytest.approx(x["b"]["navier"], rel=0.05)
    assert x["c"]["skrip"] == pytest.approx(x["c"]["tangan"], rel=0.005) and x["d"]["skrip"] == pytest.approx(x["d"]["tangan"], rel=0.005)


def test_excel_cocok_dengan_python(tmp_path):
    f = t.buat_excel(tmp_path / "5.3.xlsx")
    ok, pesan = t.cocokkan(f)
    assert ok, pesan


def test_md_berlabel_status(tmp_path):
    f = t.buat_md(tmp_path / "5.3.md")
    teks = f.read_text(encoding="utf-8")
    assert ("disetujui Defsa" if t.KEPUTUSAN else "draf, menunggu persetujuan Defsa") in teks.splitlines()[0]
    assert "belum ada di acuan" in teks and "## Yang perlu diputuskan Defsa" in teks
    assert ("## Keputusan Defsa" in teks) == bool(t.KEPUTUSAN)
