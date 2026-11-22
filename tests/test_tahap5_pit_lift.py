import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap5_pit_lift as t  # noqa: E402


@pytest.fixture(scope="module")
def r():
    return t.hitung()


def test_data_lift_dan_geometri(r):
    d = r["lift"]
    assert (d["L-1..4"]["a"], d["L-1..4"]["b"]) == pytest.approx((5.2, 6.2))
    assert (d["L-5..6"]["a"], d["L-5..6"]["b"]) == pytest.approx((4.6, 2.3))
    assert (d["L-7"]["a"], d["L-7"]["b"]) == pytest.approx((2.8, 3.4))
    assert d["L-1..4"]["dasar"] == pytest.approx(11.25) and d["L-7"]["p_kereta"] == 168


def test_angkat_hitungan_tangan_l14(r):
    a = r["angkat"]["L-1..4"]["t"]["q100"]
    ao = 5.8 * 6.8
    assert a["U"] == pytest.approx(9.81 * (12.31 - 10.85) * ao, rel=1e-9)
    w = 23.6 * (0.4 * ao + (ao - 5.2 * 6.2) * (12.60 - 11.25))
    assert a["W"] == pytest.approx(w, rel=1e-9) and a["FK_utuh"] == pytest.approx(w / a["U"])
    assert 1.0 < a["FK_utuh"] < 1.1 and a["FK_lepas"] == pytest.approx(0.659, abs=0.005)


def test_fk_tiga_pit_dan_muka_air(r):
    q = {k: r["angkat"][k]["t"] for k in t.KODE}
    assert q["L-1..4"]["q100"]["FK_utuh"] < t.FK_M <= q["L-5..6"]["q100"]["FK_utuh"] < t.FK_A
    assert q["L-7"]["q100"]["FK_utuh"] > t.FK_M
    for k in t.KODE:        # Q100 menentukan: FK makin kecil bila muka air naik
        assert q[k]["tekan"]["FK_utuh"] > q[k]["q50"]["FK_utuh"] > q[k]["q100"]["FK_utuh"]
        assert r["angkat"][k]["tahap_konstruksi"]["FK"] > 1.1


def test_opsi_a_tebal_pelat(r):
    a = r["angkat"]["L-1..4"]
    assert a["tmin"] == pytest.approx(t.t_min_bisection(r["lift"]["L-1..4"]), rel=1e-6)
    assert 0.40 < a["tmin"] < 0.45 and a["tmin_bulat"] == pytest.approx(0.45)
    assert a["A"]["FK_utuh"] >= t.FK_M - 1e-9 and a["tlepas"] == pytest.approx(0.893, abs=0.005)
    assert r["angkat"]["L-5..6"]["tmin"] < 0.40 and r["angkat"]["L-7"]["tmin"] < 0.40


def test_opsi_b_ikat(r):
    a = r["angkat"]["L-1..4"]
    q = a["t"]["q100"]
    assert a["R"] == pytest.approx(1.5 * q["U"] - q["W"]) and a["R"] > 0
    assert a["as_stek"] == pytest.approx(1.6 * a["R"] * 1000 / (0.9 * 420))
    assert (1.5 * q["U"] - q["W"]) + q["W"] == pytest.approx(1.5 * q["U"])      # FK 1,5 tercapai dengan angkur


def test_navier_dan_pynite_pelat():
    mx, my = t.navier_tengah(5.5, 6.5, 14.0)
    assert mx > my > 0
    mp = t.navier_pelat(5.5, 6.5, [(14.0 * 5.5 * 6.5, 5.5, 6.5, 2.75, 3.25)])
    assert mp[0] == pytest.approx(mx, rel=0.02)          # deret patch penuh pelat = beban merata
    px, py = t.pynite_pelat(5.5, 6.5, 0.40, 14.0)
    assert px == pytest.approx(mx, rel=0.05) and py == pytest.approx(my, rel=0.05)


def test_tulangan_pelat_dan_kedap(r):
    assert t.smaks_retak(50) == pytest.approx(255.0) and t.smaks_retak(40) == pytest.approx(280.0)
    for k in t.KODE:
        p = r["pelat"][k]
        for x in (p["atas"], p["bawah"]):
            assert x["ok"] and x["phimn"] >= x["mu"] and x["as_ada"] >= x["as_min"] - 1e-9
        assert p["atas"]["s"] <= 280 and p["bawah"]["s"] <= 255 and p["ok_geser"]
        assert max(p["Mx_d"], p["My_d"]) > 2 * max(p["Mx_n"], p["My_n"])        # turun (buffer) menentukan bawah


def test_pons_buffer(r):
    for k in t.KODE:
        p = r["pelat"][k]
        assert p["r_pons"] < 1.0 and p["r_tumpu"] < 1.0
    p = r["pelat"]["L-7"]
    d = p["bawah"]["d"]
    b0 = 4 * (0.30 + d)
    assert p["b0"] == pytest.approx(b0) and p["Vu_pons"] == pytest.approx(1.6 * 294)


def test_dinding_jepit_sendi(r):
    for k in t.KODE:
        d = r["dinding"][k]
        assert d["M_cek"] == pytest.approx(-d["M_jepit"], rel=1e-3)          # statika konsisten dengan Green
        assert 0 < d["M_lapangan"] < d["M_jepit"] < d["M_kantilever"]
        assert d["luar"]["ok"] and d["dalam"]["ok"] and d["ok_geser"] and d["hor"]["as_ada"] >= d["hor"]["as_perlu"]
    # tekanan di dasar L-1..4: K0 (18 x 0,29 + 9,19 x 1,06) + 9,81 x 1,06
    assert t.tekanan(11.25) == pytest.approx(0.5 * (18 * 0.29 + (19 - 9.81) * 1.06) + 9.81 * 1.06)
    assert t.tekanan(12.60) == 0.0


def test_l7_balok_vs_tiang(r):
    g = r["grav"]["L-7"]
    assert g["layan"] == pytest.approx(g["W"] + 294) and g["Pu"] == pytest.approx(1.2 * g["W"] + 1.6 * 294)
    b = r["l7_balok"]["pilih"]
    assert b["ok"] and b["phiMn"] >= b["Mu"] and b["rho"] <= 0.025
    tg = r["l7_tiang"]
    assert tg["n"] == 2 and tg["rasio"] < 1.0 and tg["izin"] == 911.0


def test_jarak_sloof_dan_bukaan(r):
    j = r["jarak"]["L-5..6"]
    assert j["sisi"]["barat"][0] == 52.0 and j["sisi"]["barat"][1] == pytest.approx(0.7)
    assert j["turun_sloof"]["SL-1"] == pytest.approx(11.95 - 11.05)
    assert r["jarak"]["L-1..4"]["di_inti"] and not r["jarak"]["L-7"]["di_inti"]
    b = r["bukaan"]["L-7"]
    assert b["n_per_sisi"] == 2 and b["panjang_a"] > b["a"]


def test_t94_cek_silang(r):
    x = r["t94"]
    assert x["a"]["grid"] == pytest.approx(x["a"]["rumus"], rel=t.TOL["a"] / 100)
    assert x["b"]["pynite"] == pytest.approx(x["b"]["navier"], rel=t.TOL["b"] / 100)
    assert x["c"]["pynite"] == pytest.approx(x["c"]["rumus"], rel=t.TOL["c"] / 100)
    assert x["d"]["bisection"] == pytest.approx(x["d"]["tertutup"], rel=t.TOL["d"] / 100)


def test_excel_cocok_dengan_python(tmp_path):
    f = t.buat_excel(tmp_path / "5.5.xlsx")
    ok, pesan = t.cocokkan(f)
    assert ok, pesan


def test_md_berlabel_status(tmp_path):
    f = t.buat_md(tmp_path / "5.5.md")
    teks = f.read_text(encoding="utf-8")
    assert ("disetujui Defsa" if t.KEPUTUSAN else "draf, menunggu persetujuan Defsa") in teks.splitlines()[0]
    assert "belum ada di acuan" in teks and "## Pilihan untuk Defsa" in teks and "## Keputusan Defsa\n\n" + (t.KEPUTUSAN or "Belum ada.") in teks
