import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap4_balok as bl  # noqa: E402


def test_as_perlu_kebalikan_mn():
    for mu in (100.0, 400.0, 600.0):
        a = bl.as_perlu(mu, 0.35, 0.54)
        assert abs(0.9 * bl.mn(a, 0.35, 0.54) - mu) < 1e-6


def test_mn_contoh_tangan():
    # 4D25 (1963 mm²), b 350, d 540: a = 1963 × 420 / (0,85 × 30 × 350) = 92,4 mm; Mn = 1963 × 420 × (540 - 46,2) N mm
    as_ = 4 * math.pi * 25 ** 2 / 4
    a = as_ * 420 / (0.85 * 30 * 350)
    assert abs(bl.mn(as_, 0.35, 0.54) - as_ * 420 * (540 - a / 2) / 1e6) < 1e-6


def test_susunan_lapis():
    assert bl.susunan(4, 29, 0.35, 10)[:2] == (4, 1)      # 250 mm bersih: 4D29 satu lapis
    n1, lapis, yc = bl.susunan(6, 25, 0.35, 10)
    assert (n1, lapis) == (5, 2) and yc > 0.040 + 0.010 + 0.0125


def test_kaki_sengkang_batang_selang_seling():
    assert [bl.kaki_sengkang(n) for n in (2, 3, 4, 5, 6)] == [2, 2, 3, 3, 4]


def test_ambang_torsi_350x600():
    # φTth = 0,75 × 0,083 √30 × (0,21² / 1,9) × 1000 = 7,91 kNm
    d = bl.desain_penampang(0.35, 0.60, 300, 150, 150, 150, 200, tu=0.0, hc=0.75)
    assert abs(d["phiTth"] - 0.75 * 0.083 * math.sqrt(30) * 0.21 ** 2 / 1.9 * 1000) < 1e-9


def test_desain_penampang_memenuhi_syarat_srpmk():
    d = bl.desain_penampang(0.35, 0.60, 450, 100, 220, 270, 300, tu=20.0, hc=0.65)
    assert d["ok"]
    assert d["phiMn_neg"] >= 450 and d["phiMn_pos"] >= 220
    assert d["bawah"]["As"] >= 0.5 * d["atas"]["As"] - 1e-6                    # 18.6.3.2
    assert d["s_sendi"] <= min(d["d"] / 4, 0.150) + 1e-9                       # 18.6.4.4
    assert d["Ve"] == pytest.approx((d["Mpr_neg"] + d["Mpr_pos"]) / d["ln"] + 270)
    assert d["torsi"] and d["Al"] > 0


def test_reaksi_dek_helipad_statika():
    h = bl.dek_helipad()
    q, s, lc = 1.0, bl.DEK_JARAK, bl.DEK_KANTILEVER
    assert h["PA_D"] + h["PB_D"] == pytest.approx(q * s * lc)
    p = h["roda"]
    assert p[0] + p[1] == pytest.approx(bl.tb.atap_khusus()["heli_terpusat"])


def test_balok_anak_tangki_statika_dan_kekuatan():
    t = bl.balok_anak_tangki()
    qt = t["qt"]
    berat = (bl.tb.GAMMA_C * bl.tp.H_TANGKI + bl.tp.SIDL_ATAP) * 4 * 16 + qt * 4 * 12 + \
        bl.tb.GAMMA_C * t["b"] * (t["h"] - bl.tp.H_TANGKI) * 16
    assert sum(t["R_D"]) == pytest.approx(berat, rel=1e-6)
    assert t["ok"] and t["phiMn_neg"] >= t["Mneg"] and t["phiMn_pos"] >= t["Mpos"]
    assert abs(t["M_koef"] / t["M_pynite_penuh"] - 1) <= 0.15                  # T-75


def test_semua_kelompok_memenuhi_dan_t74():
    r = bl.ringkasan()
    assert all(x["ok"] for x in r["kelompok"])
    assert all(x["rho"] <= 0.025 for x in r["kelompok"])
    cp = r["cp"]
    assert abs(cp["phiMn_neg"] / cp["phiMn_neg_cp"] - 1) <= 0.05             # T-74
    assert abs(cp["phiMn_pos"] / cp["phiMn_pos_cp"] - 1) <= 0.05
    assert r["massa"]["rasio"] < 0.005
