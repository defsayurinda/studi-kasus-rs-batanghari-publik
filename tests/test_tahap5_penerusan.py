import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap5_pit_lift as pit  # noqa: E402
import tahap5_sloof as sl  # noqa: E402
import tahap5_penerusan as t  # noqa: E402


@pytest.fixture(scope="module")
def h():
    return t.hitung()


def test_koefisien_kombinasi():
    ev = 0.2 * 0.386
    ult, lay = t.kombinasi_daftar("ult"), t.kombinasi_daftar("lay")
    assert len(ult) == 2 + 32 * 2 and len(lay) == 2 + 32 * 3
    assert ult[0][1:4] == (1.4, 0.0, 0.0) and ult[1][1:4] == (1.2, 1.6, 0.0)
    assert ult[2][1] == pytest.approx(1.2 + ev) and ult[2][2] == 1.0 and ult[2][3] == pytest.approx(1.3)
    assert ult[3][1] == pytest.approx(0.9 - ev) and ult[3][2] == 0.0
    assert lay[2][1] == pytest.approx(1 + 0.14 * 0.386) and lay[2][3] == pytest.approx(0.7 * 1.3)
    assert lay[3][1] == pytest.approx(1 + 0.105 * 0.386) and lay[3][2] == 0.75 and lay[3][3] == pytest.approx(0.525 * 1.3)
    assert lay[4][1] == pytest.approx(0.6 - 0.14 * 0.386) and lay[4][2] == 0.0
    assert {k[4][2:] for k in ult if k[4]} == {(1, 1), (1, -1), (-1, 1), (-1, -1)}      # 100 % + 30 % dengan tanda ±


def test_kasus_r_tidak_dipakai(h):
    m = h["mentah"]
    assert set(t.KASUS) == {"D", "L", "EX+", "EX-", "EY+", "EY-"}
    for kf in ("K1", "K2"):
        assert all(set(v) == set(t.KASUS) for v in m["kolom"][kf].values()) and len(m["kolom"][kf]) == 70
        assert len(m["inti"][kf]) == 7


def test_kombinasi_gravitasi_dihitung_tangan(h):
    r = [x for x in h["titik"] if x["id"] == "4/B"][0]
    kf = max(r["Fu"], key=lambda k: r["Fu"][k][1, 0])
    assert r["Fu"][kf][0, 0] == pytest.approx(1.4 * (r["raw"][kf]["D"][0] + r["D_tam"]), rel=1e-9)
    assert r["Fu"][kf][1, 0] == pytest.approx(1.2 * (r["raw"][kf]["D"][0] + r["D_tam"]) + 1.6 * (r["raw"][kf]["L"][0] + r["L_tam"]), rel=1e-9)
    assert r["Fl"][kf][1, 0] == pytest.approx(r["raw"][kf]["D"][0] + r["D_tam"] + r["raw"][kf]["L"][0] + r["L_tam"], rel=1e-9)


def test_tambahan_keseimbangan(h):
    c = h["t95"]["c"]
    assert sum(e["D"] + e["L"] for e in h["tam"].values()) == pytest.approx(c["total1"], rel=1e-9)
    assert c["total1"] == pytest.approx(c["total2"], rel=t.TOL["c"] / 100)
    for k, v in c["kat1"].items():
        assert v == pytest.approx(c["kat2"][k], rel=t.TOL["c"] / 100), k
    assert len(h["titik"]) == 70 and len(h["inti"]) == 7


def test_t95_lolos_semua(h):
    x = h["t95"]
    for kf in ("K1", "K2"):
        a = x["a"][kf]
        assert a["kolom"] == pytest.approx(a["rangka2"], rel=t.TOL["a"] / 100)
        assert a["dinding48"] == pytest.approx(a["dinding42"], rel=t.TOL["a"] / 100)
        assert a["kolom"] == pytest.approx(a["statika_total"], rel=1e-9)
        for cs in ("EX+", "EX-", "EY+", "EY-"):
            assert x["b"][(kf, cs)]["jumlah"] == pytest.approx(x["b"][(kf, cs)]["V"], rel=t.TOL["b"] / 100)


def test_delta_p_sloof_jumlah_nol(h):
    for kf in ("K1", "K2"):
        for j in ("ult", "lay"):
            s = sum(np.array(r["dP"][kf][j]) for r in h["titik"])
            assert float(np.abs(s).max()) < 1e-8
    assert max(r["amp"]["ult"]["dP_maks"] for r in h["titik"]) > 0
    assert all(r["amp"]["ult"]["Mx"] == 0.0 for r in h["titik"]) and all(r["amp"]["ult"]["Mx"] > 0 for r in h["inti"])


def test_kolom_tangki_opsi_b(h):
    tg = [r for r in h["titik"] if r["kel"] == "K-T B"]
    assert len(tg) == 6 and all(r["b"] == 0.80 for r in tg)
    assert all(r["dD_tangki"] == pytest.approx(h["mentah"]["tangki"][(r["x"], r["y"])]["dD"]) for r in tg)
    assert all(r["D_tam"] >= r["dD_tangki"] for r in tg)


def test_l7_ke_empat_kolom_sloof(h):
    p = pit.data_lift()["L-7"]
    w = pit.angkat(p, 0.40, pit.Q100)["W"]
    pb = p["jumlah"] * (p["p_kereta"] + p["p_imbang"])
    wb = 2 * t.GC * 0.4 * 0.8 * 8.0
    tam = h["tam"]
    ke4 = sum(tam[k]["kat"].get("pit", 0.0) for k in ((36.0, 27.0), (36.0, 35.0), (44.0, 27.0), (44.0, 35.0)))
    assert ke4 == pytest.approx(w + pb + wb, rel=1e-9)
    assert tam[(36.0, 35.0)]["kat"]["pit"] == pytest.approx(tam[(44.0, 35.0)]["kat"]["pit"])
    assert tam[(36.0, 35.0)]["L"] > 0 and tam[(36.0, 27.0)]["L"] > 0


def test_l1_4_ke_inti_dengan_t_045(h):
    p = pit.data_lift()["L-1..4"]
    w45, w40 = pit.angkat(p, 0.45, pit.Q100)["W"], pit.angkat(p, 0.40, pit.Q100)["W"]
    assert w45 > w40 and t.T_PIT["L-1..4"] == 0.45
    lif = [r for r in h["inti"] if r["id"] == "INTI-LIF"][0]
    assert lif["kat"]["pit"] == pytest.approx(w45 + p["jumlah"] * (p["p_kereta"] + p["p_imbang"]), rel=1e-9)
    kolom_pit = sum(h["tam"][(r["x"], r["y"])]["kat"].get("pit", 0.0) for r in h["titik"] if (r["x"], r["y"]) in {(52.0, 43.0), (60.0, 43.0)})
    p56 = pit.data_lift()["L-5..6"]
    assert kolom_pit == pytest.approx(pit.angkat(p56, 0.40, pit.Q100)["W"] + p56["jumlah"] * (p56["p_kereta"] + p56["p_imbang"]), rel=1e-9)


def test_ldh_dan_penyaluran():
    assert sl.ldh(29) == pytest.approx(381.3, abs=0.1)
    assert t.ldh_2543(29) == pytest.approx(0.24 * 420 * 29 / math.sqrt(35), rel=1e-9) and t.ldh_2543(6) == 150.0
    assert t.ld_tarik(29) == pytest.approx(420 * 29 / (1.7 * math.sqrt(35)), rel=1e-9) and t.ld_tarik(6) == 300.0
    assert t.ldc(29) == pytest.approx(0.043 * 420 * 29, rel=1e-9) and t.tersedia() == (pytest.approx(1093.0), pytest.approx(1125.0))


def test_stek_dan_angkur(h):
    for x in t.stek_kolom(h):
        assert x["ok_ldh"] and x["pu_max"] < x["phiBn"] and x["Ast"] >= x["as_min"] and not x["tarik"]
    an = t.angkur_sloof(h)
    d29 = [x for x in an["baris"] if x["db"] == 29]
    assert d29 and all(x["ldh"] == pytest.approx(sl.ldh(29)) and not x["ok"] and x["h_cap_kait"] < t.T_CAP * 1000 < x["h_cap_lurus"] for x in d29)
    assert an["ftie"] == pytest.approx(0.10 * 0.386 * sl.gaya_ikat(sl.data_kolom())["pu_maks"], rel=1e-9)
    assert sum(1 for s in an["di_inti"] if s["di_dalam"]) == 1


def test_pmin_pmax_dan_tarik(h):
    for r in h["semua"]:
        for j in ("lay", "ult"):
            a = r["amp"][j]
            assert a["Pmin"] <= a["Pmax"] and a["Pmin_dP"] <= a["Pmax_dP"] and a["Vmax"] >= 0
    assert min(r["amp"]["ult"]["Pmin_dP"] for r in h["semua"]) > 0       # tidak ada tarik


def test_excel_cocok_dengan_python(tmp_path):
    f = t.buat_excel(tmp_path / "5.6.xlsx")
    ok, pesan = t.cocokkan(f)
    assert ok, pesan


def test_md_berlabel_status(tmp_path):
    f = t.buat_md(tmp_path / "5.6.md")
    teks = f.read_text(encoding="utf-8")
    assert "disetujui Defsa" in teks.splitlines()[0]
    assert "belum ada di acuan" in teks and "## Yang perlu diputuskan Defsa" in teks and "## Keputusan Defsa" in teks
