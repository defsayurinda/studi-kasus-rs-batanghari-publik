import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap2_pelengkap as pl  # noqa: E402
import tahap2_penurunan_urugan as pu  # noqa: E402


def test_t90_tanpa_pvd_tangan():
    # 0,848 × 4² / 1,8 = 7,54 tahun (FHWA NHI-06-088 Pers. 7-8)
    assert math.isclose(pu.t90_tanpa_pvd(8.0), 0.848 * 16 / 1.8)
    assert 7.5 < pu.t90_tanpa_pvd(8.0) < 7.6


def test_pvd_tangan_jarak_1_2():
    # dc 1,26; dw 0,0662; F(n) = ln(19,03) - 0,75 = 2,196; t = 1,26²/36 × 4,196 × ln10 = 0,426 th
    dc, dw = 1.26, 2 * 0.104 / math.pi
    t = dc ** 2 / 36 * (math.log(dc / dw) - 0.75 + 2) * math.log(10)
    assert math.isclose(pu.t_pvd(1.2), t, rel_tol=1e-9)
    assert 5.0 < pu.t_pvd(1.2) * 12 < 5.2


def test_lapisan_nc_satu_sublapisan():
    # lapisan U4 tipis NC: S = H Cc/(1+e0) log(σf/σp) bagian NC + Cr bagian OC
    s0, sp, sf, h = 30.0, 30.0, 70.0, 1.0
    s = h * 0.75 / 3.05 * math.log10(sf / sp)
    assert math.isclose(s, 0.0905, abs_tol=5e-4)


def test_penurunan_selatan_kecil_utara_besar():
    h = {r["nama"]: r for r in pu.semua()}
    assert h["BH-1"]["primer"] < 0.3 and h["CPTu-6"]["primer"] < 0.2
    assert h["HA-8"]["primer"] > 1.0 and h["BH-3"]["primer"] > 1.0
    assert h["BH-1"]["per_unit"].get("U3", 0) == 0  # tanpa gambut di selatan


def test_cek_fase_bh8_dan_bh3():
    kons, gam = pl.cek_fase()
    bh8 = next(x for x in kons if x["titik"] == "BH-8" and x["contoh"] == "UD-2")
    assert math.isclose(bh8["s"], 0.891, abs_tol=0.002)
    assert math.isclose(bh8["e0_kor"], 2.088, abs_tol=0.002)
    assert all(abs(x["s"] - 1) < 0.01 for x in kons if x is not bh8)
    assert {x["titik"] for x in gam} == {"BH-3"}
    assert all(10.5 < x["gamma_kor"] < 15.5 for x in gam)


def test_artesis_pz4b():
    a = {x["sensor"]: x for x in pl.artesis()}
    assert math.isclose(a["PZ-4B"]["maks"] - 9.19, 0.53, abs_tol=0.01)
    assert a["PZ-4B"]["hari_kering"] > 0 and a["PZ-2B"]["hari"] == 0


def test_teks_cad_dari_mathtext():
    from cad_render import teks_biasa
    s = teks_biasa(r"$\sigma'_v$ (kPa)")
    assert s.startswith("σ'") and "$" not in s and "\\" not in s
    assert teks_biasa("m$^2$") == "m²"
    assert teks_biasa("biasa 1,2 m") == "biasa 1,2 m"


def test_templat_kop_ada():
    import cad_kop
    assert cad_kop.TEMPLAT.exists()
    # kop gaya contoh Defsa: kolom kanan 75 mm, kotak KETERANGAN 107 mm di atas bagian kop 152 mm
    assert cad_kop.LEBAR_KOLOM == 75 and cad_kop.TINGGI_ETIKET == 152
    assert cad_kop.TINGGI_KOLOM == 297 - cad_kop.ATAS - cad_kop.BAWAH
