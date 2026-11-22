import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap6_struktur as t  # noqa: E402


@pytest.fixture(scope="module")
def h():
    return t.semua()


def test_cap_4_tiang_tangan(h):
    """Cap 4 tiang (4/B), h 1.000, f'c 35: hitung tangan geser satu arah (tiang di ±1,2 m, kolom 0,8, Dt 0,8, lebar 4,0 m)."""
    e = h["cap_kolom"][4]["h1000"]
    ru = h["cap_kolom"][4]["cap"]["r"]["sumPu"] / 4
    d = (1000 - 75 - 1.5 * 32) / 1e3                     # 0,877 m
    frak = (1.2 - (0.4 + d) + 0.4) / 0.8                 # 13.4.2.5: (jarak + Dt/2) / Dt
    vu = 2 * frak * ru
    pvc = 0.75 * 0.17 * math.sqrt(35) * 4.0 * 1e3 * d
    assert e["geser"]["Vu"] == pytest.approx(vu, rel=0.02)
    assert e["geser"]["phiVc"] == pytest.approx(pvc, rel=0.02)
    bo = 4 * (0.8 + d)
    assert e["pons_kolom"]["bo"] == pytest.approx(bo, rel=0.02)
    vc = min(0.33, 0.17 * 3, 0.083 * (2 + 40 * d / bo)) * math.sqrt(35)
    assert e["pons_kolom"]["phiVc"] == pytest.approx(0.75 * vc * bo * d * 1e3, rel=0.02)
    mu = 2 * ru * (1.2 - 0.4)
    assert e["lentur"]["x"]["Mu"] == pytest.approx(mu, rel=0.02)


def test_tiang_pm():
    """φPn,maks hitung tangan dan φMn 16 D25 pada 1.560 kN terhadap 1.122 kNm (6.5)."""
    kv = t.pm_kurva(30.0, 16)
    ast = 16 * math.pi * 25 ** 2 / 4
    po = 0.85 * 30 * (t.AG - ast) + 420 * ast
    assert kv["phiPn_maks"] == pytest.approx(0.75 * 0.85 * po / 1e3, rel=0.001)
    assert kv["phiTn"] == pytest.approx(0.9 * ast * 420 / 1e3, rel=0.001)
    assert t.phi_mn(kv, 1560.0) == pytest.approx(1122.0, rel=0.05)
    assert t.phi_mn(kv, 0.0) < t.phi_mn(kv, 1560.0)          # tarik/tekan rendah: φMn naik terhadap P sampai titik seimbang


def test_tiang_n_min_dan_spiral(h):
    for fc in (30.0, 35.0):
        tt = h["tiang"][fc]
        assert 11 <= tt["n_min"] <= 16
        assert tt["cek16"]["lolos"]
        sp = tt["spiral"]
        assert 25 <= sp["bersih_rapat"] <= 75 and 25 <= sp["bersih_luar"] <= 75
        assert sp["rs_pasang_rapat"] >= max(sp["rs_d"], sp["rs_e"]) - 1e-9
    assert h["tiang"][35.0]["panjang"]["ld"] == pytest.approx(420 * 25 / (1.7 * math.sqrt(35)), rel=0.001)


def test_stm_cap_e(h):
    S = h["stm_E"]
    ce = h["cap_E"]
    assert sum(r["R"] for r in S["rows"]) == pytest.approx(sum(x["Pu"] for x in ce["titik"]), rel=0.001)   # kesetimbangan vertikal
    assert S["n_stm"] >= 1 and all(r["theta"] >= 25.0 for r in S["rows"] if r["stm"])
    assert S["dev_stm_beam"] <= t.TOL["stm"]
    assert S["Tx"] == pytest.approx(S["Mx"] / S["z"])


def test_pit(h):
    p = h["pit"]
    assert p[0.45]["FK"] == pytest.approx(1.11, abs=0.005) and p[0.45]["ok_a"]
    assert p[0.40]["FK"] == pytest.approx(1.065, abs=0.005) and not p[0.40]["ok_a"]
    assert p[0.40]["R"] == pytest.approx(245.6, rel=0.005)
    assert p[0.40]["As"] == pytest.approx(1040.0, rel=0.005)
    assert p["geom"]["menjorok"] == 0.0 and p["geom"]["frak_dalam"] == 1.0    # Cap E gabungan (x 41,2-57,2) memuat tapak pit x 51,1-56,9


def test_sloof_sl2(h):
    s = h["sloof"]["SL-2"]
    assert s["rasio"] == pytest.approx((363.1 + 383.0) / 978.1, rel=0.001)
    assert h["sloof"]["SL-3"]["rasio"] < 1.0 and s["rasio"] < 1.0


def test_excel_sama_python(h, tmp_path):
    from format_dokumen import hitung_ulang_excel
    berkas, adr = t.buat_excel(tmp_path / "6.7.xlsx", h)
    ok, _ = hitung_ulang_excel(berkas)
    assert ok
    r = t.t105(h, berkas, adr)
    assert r["dxl"] <= t.TOL["excel"]


def test_md_label_draf(h, tmp_path):
    md = t.tulis_md(h=h, r=t.t105(h), keluar=tmp_path / "6.7.md")
    teks = Path(md).read_text(encoding="utf-8")
    assert f"STATUS: {t.STATUS}" in teks
    assert "Keputusan yang dibutuhkan dari Defsa" in teks
    assert "DATA SIMULASI" in teks
