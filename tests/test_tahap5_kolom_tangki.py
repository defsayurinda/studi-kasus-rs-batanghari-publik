"""Uji 5.6a (kolom tangki opsi B). Cepat bila KOLOM_TANGKI_CACHE dan PENERUSAN_CACHE menunjuk berkas pickle (lihat data_mentah)."""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap4_beban as tb  # noqa: E402
import tahap4_kolom as kl  # noqa: E402
import tahap5_kolom_tangki as t  # noqa: E402


@pytest.fixture(scope="module")
def r7():
    return t.hitung(0.75)             # pembanding 750


@pytest.fixture(scope="module")
def r8():
    return t.hitung()                 # keputusan Defsa 21 Nov 2026: 800 seragam (b_B 5.1)


@pytest.fixture(scope="module")
def st7(r7):
    return t.stek_dan_dampak(r7)


@pytest.fixture(scope="module")
def st8(r8):
    return t.stek_dan_dampak(r8)


def test_koreksi_dd_dihitung_tangan(r8):
    r7 = r8
    ev = 0.2 * tb.SDS
    for q in t.KOLOM:
        dd = float(r7["m"]["w_b"][q] - r7["m"]["w_a"][q])
        assert r7["dd"][q] == pytest.approx(dd)
        for lv in t.SEG:
            k = (lv, *q)
            for awal in (0, 130):                      # K2 lalu K1 (130 baris per konfigurasi): baris 1,4 D; 1,2 D + 1,6 L; (1,2 + 0,2 SDS) D + ...; (0,9 - 0,2 SDS) D + E
                for baris, cd in ((0, 1.4), (1, 1.2), (2, 1.2 + ev), (3, 0.9 - ev)):
                    sel = r7["gk"][k]["F"][awal + baris, :, 0] - r7["gk0"][k]["F"][awal + baris, :, 0]
                    assert sel == pytest.approx([cd * dd, cd * dd], rel=1e-9, abs=1e-6)


def test_ukuran_dan_kelompok(r7, r8):
    assert {round(v["b_B"], 2) for v in r8["m"]["kolom_b"].values()} == {0.80}     # 5.1: 800 seragam
    assert [x["kelompok"] for x in r8["grup"]] == ["K-TB LT2", "K-TB LT3"] and all(x["n"] == 6 for x in r8["grup"])
    assert all(x["b"] == 0.75 for x in r7["grup"]) and all(x["b"] == 0.80 for x in r8["grup"])


def test_pm_tulangan_terkecil(r7, r8):
    for r in (r7, r8):
        for x in r["grup"]:
            pil = kl.pilihan_tulangan(x["b"])
            i = pil.index(x["awal_pm"])
            rasio = lambda opsi: max(kl.rasio_pm(r["gk"][k], kl.diagram(x["b"], *opsi[1:])).max() for k in x["kolom"])   # noqa: E731
            if rasio(pil[-1]) <= 1.0:
                assert rasio(pil[i]) <= 1.0 and (i == 0 or rasio(pil[i - 1]) > 1.0)
            assert x["pm"]["rasio"] == pytest.approx(max(d["rasio"] for d in x["per_kolom"].values()))


def test_pm_memenuhi_kecuali_lt3_750(r7, r8):
    lt2, lt3 = r7["grup"]
    assert lt2["pm"]["rasio"] <= 1.0 and lt2["ok"]
    assert lt3["pm"]["rasio"] > 1.0 and not lt3["ok"] and lt3["usulan"]["b"] == 0.80     # momen model A konservatif; usulan 800
    assert all(x["pm"]["rasio"] <= 1.0 and x["ok"] for x in r8["grup"])
    assert max(t.peka_momen(r7).values()) < 1.0                                          # indikatif: momen model B lebih kecil


def test_scwb_semua_joint(r7, r8):
    for x in r8["grup"] + r7["grup"][:1]:
        assert x["scwb_gagal"] == 0 and min(c["rasio"] for c in x["scwb_semua"]) >= 1.2
    gagal = [c for c in r7["grup"][1]["scwb_semua"] if c["rasio"] < 1.2]
    assert len(gagal) == 1 and gagal[0]["joint"] == ("LT3", 68.0, 67.0)
    c = [c for c in r8["grup"][1]["scwb_semua"] if c["joint"] == ("LT3", 68.0, 67.0) and c["arah"] == "Y"][0]
    assert c["rasio"] == pytest.approx((c["Mnc_bawah"] + c["Mnc_atas"]) / (c["Mnb_kiri"] + c["Mnb_kanan"]), rel=1e-9)
    assert c["Mnc_atas"] == 0.0                                    # joint atap podium: tidak ada kolom di atas


def test_pelat_tangki_di_mnb(r7):
    pp = t.peka_pelat(r7)
    assert pp["As_B"][0] > 3 * pp["As_std"][0]
    assert pp["scwb_min"]["K-TB LT3"] > min(c["rasio"] for c in r7["grup"][1]["scwb_semua"])     # tanpa pelat tangki: tidak konservatif
    assert t.pelat_balok_b("x 68")[0] == pytest.approx((pp["As_B"][0] + pp["As_std"][0]) / 2)


def test_geser_dan_pengekang(r7, r8):
    for x in r8["grup"] + r7["grup"][:1]:
        g = x["geser"]
        assert g["ok"] and 75 <= g["s_lo"] <= g["s_maks"] and g["s_lo"] <= 150 and g["hx"] <= 350      # 18.7.5.3: s <= b/4, 6 db, so <= 150
        assert g["lo"] >= max(x["b"] * 1000, 450.0) and g["Ve"] >= g["Vu"]
    assert r7["grup"][1]["hbk"]["rasio"] > 1.0                    # geser joint LT3 750 gagal; 800 memenuhi
    assert all(c["rasio"] <= 1.0 for x in r8["grup"] for c in x["hbk_semua"])


def test_stek_ke_pile_cap(st7, st8):
    ldh22 = max(0.24 * 420 * 22 / math.sqrt(35), 8 * 22, 150.0)
    assert st7["baru"]["ldh"] == pytest.approx(ldh22) and st7["lama"]["ldh"] == pytest.approx(ldh22)
    for x in (st7["lama"], st7["baru"], st8["baru"]):
        assert x["ok_ldh"] and x["ok_ld"] and x["ok_tumpu"] and x["ok_asmin"] and x["ok_tarik"] and x["ok_geser"]


def test_dampak_ke_56(st7, st8):
    assert all(abs(x["dW"]) < 1e-9 and x["Pu_baru"] == pytest.approx(x["Pu_56"]) for x in st8["baris"])       # 5.6 sudah memakai b_B 800
    for x in st7["baris"]:                                                                                   # pembanding 750
        assert x["dW"] == pytest.approx(23.6 * (0.75 ** 2 - 0.8 ** 2) * (9.0 + 0.55), rel=1e-6)
        assert x["Pu_baru"] - x["Pu_56"] == pytest.approx(1.4 * x["dW"]) and (x["Pu_baru"] / x["Pu_56"] - 1) > -0.015


def test_t96(r8):
    r7 = r8
    c = t.t96(r8)
    assert t.selisih(c["a"]["sendiri"], c["a"]["cp"]) <= t.TOL["a"]
    assert t.selisih(*c["b"]["neg"]) <= t.TOL["b"] and t.selisih(*c["b"]["pos"]) <= t.TOL["b"]
    assert t.selisih(c["c"]["Pu_B"], c["c"]["Pu_5.6a"]) <= t.TOL["c"]
    assert c["c"]["Pu_5.6a"] == pytest.approx(float(r7["gk"][("LT2", 68.0, 67.0)]["F"][:, :, 0].max()))


def test_excel_sama_python(tmp_path):
    berkas = tmp_path / "kt.xlsx"
    t.buat_excel(berkas)
    sel, stat = t.cek_excel(berkas)
    assert sel <= t.TOL["d"] and stat == ["Lolos"] * 4
    import openpyxl
    wb = openpyxl.load_workbook(berkas)
    assert wb.sheetnames == t.NAMA and all(wb[n].freeze_panes for n in t.NAMA)
