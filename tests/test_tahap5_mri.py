import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap5_mri as t  # noqa: E402


@pytest.fixture(scope="module")
def r():
    return t.hitung()


def test_jarak_opsi_0_dan_isocenter_opsi_1(r):
    assert r["j0"] == pytest.approx(7.5) and r["j0"] < r["mi"]["d_logam"]
    o1 = r["o1"]
    assert o1["iso_x"] == pytest.approx(76.0) and o1["j_lajur"] == pytest.approx(12.0)
    assert o1["d_as9"] == pytest.approx(0.0) and o1["d_as9"] <= r["mi"]["radius"]   # sloof as 9 dalam radius 1,0 m
    assert o1["d_kolom"] == pytest.approx(2.0)
    assert o1["ruang"] == pytest.approx((72.5, 79.5, 54.0, 60.0))
    assert o1["ov_r09"] == pytest.approx(9.0) and o1["ov_r07"] == pytest.approx(1.5) and o1["ov_r06"] == 0.0
    assert o1["j_lift"]["L-1..4"] == pytest.approx(22.8, abs=0.05) and min(o1["j_lift"].values()) > r["mi"]["d_lift"]


def test_opsi_2_lajur_dan_p4(r):
    o2 = r["o2"]
    assert o2["tepi"] == pytest.approx(92.5) and o2["lajur"][1] == pytest.approx(98.5)
    assert o2["sisa_p4"] == pytest.approx(1.5) and o2["sisa_p4"] < t.LEBAR_PARKIR_MOTOR
    assert o2["hilang_luas"] == pytest.approx(192.0) and o2["motor_hilang"] == 76
    assert o2["motor_sisa"] == o2["motor_total"] - 76 and o2["motor_sisa"] < o2["motor_butuh"]


def test_beban_mri(r):
    b = r["beban"]
    assert b["q_kaki"] == pytest.approx(192.0)
    assert b["q_pel"] == pytest.approx(93.2 / 13, abs=1e-9) and round(b["q_pel"], 2) == 7.17
    assert b["q_rf"] == pytest.approx(27.5 / 42)
    assert b["phivc"] == pytest.approx(443.1, rel=0.01) and b["rasio_pons"] == pytest.approx(0.0325, abs=0.001)
    assert b["rasio_tumpu"] < 0.05


def test_non_magnetik_berat(r):
    n = r["nm"]
    assert n["nb"] == 11 and n["pakai13"] == 620 and n["pj13"] == pytest.approx(3.24)
    assert n["berat_pelat"] == pytest.approx(44 * 3.24 * 1.04, rel=0.005)
    assert n["ld13"] == pytest.approx(475, rel=0.01) and n["ld22"] == pytest.approx(992, rel=0.01)
    assert 270 <= n["berat_opsi1"] <= 285


def test_fn_pelat_dekat_rayleigh_pynite(r):
    g = r["getar"]
    assert g["fn"] == pytest.approx(11.2, rel=0.01) and g["M_modal"] == pytest.approx(10670, rel=0.01)
    assert abs(g["fn_rayleigh"] / g["fn"] - 1) <= 0.15
    assert abs(g["d_pynite"] / g["d_navier"] - 1) <= 0.03   # PyNite mesh 0,5 m vs deret Navier


def test_gaya_izin_dan_isolator(r):
    g, s = r["getar"], r["getar"]["sumber"]
    assert s["M-04"]["F"] == pytest.approx(41, rel=0.02) and s["R-06"]["F"] == pytest.approx(50, rel=0.02)
    assert s["M-04"]["H"] == pytest.approx(1.27, abs=0.02) and s["R-06"]["H"] == pytest.approx(1.05, abs=0.02)
    assert g["T_m04"] < 1 and g["T_r06"] < 1 and g["fi"] == pytest.approx(3.15, abs=0.01)
    assert g["F_m04_sumber"] == pytest.approx(1900, rel=0.02) and g["F_r06_pegas"] == pytest.approx(6600, rel=0.02)


def test_transmisibilitas_kurang_dari_satu_di_atas_akar_dua():
    fi = 3.15
    for rr in (1.5, 2, 5, 15):
        assert t.transmisibilitas(rr * fi, fi, 0.05) < 1.0
    assert t.transmisibilitas(0.5 * fi, fi, 0.05) > 1.0


def test_bukaan_tidak_bentrok_balok(r):
    k = r["bukaan"]
    assert k["atas"] == pytest.approx(15.45) and k["sisa"] > 0 and k["beda"] == pytest.approx(0.80)
    assert not [d for d in k["dinding_ujung"] if 51.0 <= d[3] + 4.0 and d[3] - 4.0 <= 59.0]   # tidak ada dinding geser di D-E


def test_excel_cocok_dengan_python(tmp_path):
    f = t.buat_excel(tmp_path / "5.2.xlsx")
    ok, pesan = t.cocokkan(f)
    assert ok, pesan


def test_md_berlabel_status(tmp_path):
    f = t.buat_md(tmp_path / "5.2.md")
    teks = f.read_text(encoding="utf-8")
    assert ("disetujui Defsa" if t.KEPUTUSAN else "draf, menunggu persetujuan Defsa") in teks.splitlines()[0]
    assert "belum ada di acuan" in teks
    assert ("## Keputusan Defsa" in teks) == bool(t.KEPUTUSAN)
