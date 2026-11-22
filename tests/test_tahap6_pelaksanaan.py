import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap6_pelaksanaan as t  # noqa: E402


@pytest.fixture(scope="module")
def h():
    return t.semua()


def test_davisson_tangan(h):
    """TP-1, L 37,01 m, f'c 30: s_D = P L / (A E) + 4 + D/120 pada 1.822 kN; kurva tiang jauh di bawah garis."""
    ae = 4700 * math.sqrt(30) * 1e3 * math.pi * 0.8 ** 2 / 4          # kN
    sd = 1822 * 37.01 / ae * 1e3 + 4 + 800 / 120
    assert t.davisson(1822.0, 37.01) == pytest.approx(sd, rel=0.02)
    assert sd == pytest.approx(15.9, abs=0.3)                          # 6.2: 15,4-15,5 dengan L dan Ec sedikit berbeda
    for v in h["statik"]["tp"].values():
        assert not v["davisson_tercapai"] and v["lolos_25"] and v["lolos_12"]


def test_kekakuan_6_6(h):
    assert h["statik"]["k_rata"] == pytest.approx(489.0, rel=0.01)
    for tp, v in h["statik"]["tp"].items():
        assert v["Pmaks"] == pytest.approx(1822.0, rel=0.01)
        assert v["sisa"] == pytest.approx(t.SISA_RINGKASAN[tp], abs=0.02)      # lembar Ringkasan: 1,96; 2,42; 1,78; 1,81


def test_chin_tangan(h):
    env = h["statik"]["tp"]["TP-3"]["env"]
    pts = [(p, s) for p, s in env if p >= 0.45 * 911]
    n = len(pts)
    sx = sum(s for p, s in pts); sy = sum(s / p for p, s in pts)
    sxx = sum(s * s for p, s in pts); sxy = sum(s * s / p for p, s in pts)
    c1 = (n * sxy - sx * sy) / (n * sxx - sx ** 2)
    assert h["statik"]["tp"]["TP-3"]["chin"]["Qult"] == pytest.approx(1 / c1, rel=0.02)
    assert 1 / c1 > 1822.0


def test_jumlah_uji(h):
    j = h["jumlah"]
    assert j["total"]["statik"] == 5 and j["utama"]["statik"] == 4    # 319 / 251 tiang setelah Cap C digabung ke Cap E dan berat cap masuk 6.3
    assert (j["total"]["csl"], j["total"]["pit"]) == (16, 64) and (j["utama"]["csl"], j["utama"]["pit"]) == (13, 51)
    tb = h["tambahan"]
    assert tb["pit"] == 24 and tb["pit_utama"] == 11 and tb["csl"] == 0
    assert tb["statik"] == 2          # 4 ada semua sebelum konstruksi; 40 % x 4 = 1,6 -> 2 harus saat konstruksi
    assert h["beban"]["statik"]["SELATAN"] == 3166.0 and h["beban"]["statik"]["UTARA"] == 2886.0


def test_dewatering_dupuit_tangan(h):
    k, base, dasar = 1e-5, 9.95, t.DASAR_E          # Cap E pelat h t.H_E
    pj, lb = t.E_UK
    a, b = pj + 2, lb + 2
    re = math.sqrt(a * b / math.pi)
    s = 11.20 - (dasar - 0.5)
    R = re + 3000 * s * math.sqrt(k)
    H, hh = 11.20 - base, max(0.02, dasar - 0.5 - base)      # h dikunci 0,02 m bila muka air turun di bawah dasar urugan
    q = math.pi * k * (H ** 2 - hh ** 2) / math.log(R / re)
    r = next(x for x in h["dew"] if x["nama"].startswith("Cap E") and x["zona"] == "SELATAN" and x["k"] == 1e-5)
    assert r["Q"] == pytest.approx(q, rel=0.02)
    # muka air di gudang (>= 8 m dari galian) tidak turun di bawah dasar urugan, jadi di atas batas +8,6
    assert min(t.muka_air_x(x, x["k"], x["base"], 8) for x in h["dew"]) > t.BATAS_GUDANG


def test_heave_tangan(h):
    """Utara, Cap E (dasar t.DASAR_E), target = dasar - 0,5: σ total = 19 (target - 9,23) + U1 .. U4 sampai puncak U5; u = 9,81 (11,20 - puncak U5)."""
    sig = 19 * (t.DASAR_E - 0.5 - 9.23) + 17.0 * 0.41 + 17.8 * 0.72 + 10.7 * 2.84 + 15.2 * (9.73 - 3.97)
    u = 9.81 * (11.20 - (9.23 - 9.73))
    v = h["heave"][("UTARA", f"Cap E h {t.HE_LABEL}")]
    assert v["FS"] == pytest.approx(sig / u, rel=0.02)
    assert min(x["FS"] for x in h["heave"].values()) >= 1.1


def test_excel_sama_python(h, tmp_path):
    from format_dokumen import hitung_ulang_excel
    berkas, adr = t.buat_excel(tmp_path / "6.8.xlsx", h)
    ok, _ = hitung_ulang_excel(berkas)
    assert ok
    assert t.t106(h, berkas, adr)["dxl"] <= t.TOL["excel"]


def test_md_label_draf(h, tmp_path):
    md = t.tulis_md(h=h, r=t.t106(h), keluar=tmp_path / "6.8.md")
    teks = Path(md).read_text(encoding="utf-8")
    assert f"STATUS: {t.STATUS}" in teks
    assert "Keputusan yang dibutuhkan dari Defsa" in teks and "DATA SIMULASI" in teks and "T-107" in teks
