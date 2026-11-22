import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap4_kolom as kl  # noqa: E402
import tahap5_sloof as t  # noqa: E402


@pytest.fixture(scope="module")
def r():
    return t.hitung()


def test_beban_pelat_dan_dinding():
    assert t.D_PL == pytest.approx(23.6 * 0.25 + 1.10 + 1.00) and t.QU_PL == pytest.approx(1.2 * 8.0 + 1.6 * 4.79)
    assert t.W_FASAD == pytest.approx(t.Q_DL * 4.2) and 11.0 < t.W_FASAD < 12.0
    assert t.pl_w() == pytest.approx(93.2 / 13.0, rel=1e-6) and t.W_R09 == pytest.approx(0.45 * 4.5)


def test_gaya_ikat_10_persen_sds(r):
    g = r["gi"]
    assert g["ftie_maks"] == pytest.approx(0.10 * 0.386 * g["pu_maks"], rel=1e-9)
    assert {b["kel"] for b in g["kelompok"]} == {"K-P", "K-T B"}
    d = r["desain"][("SL-2", 0.40, 0.80)]
    assert g["ftie_maks"] < 0.9 * (d["atas"]["As"] + d["bawah"]["As"]) * 420 / 1000 / 3     # jauh di bawah φTn


def test_kolom_tangki_memakai_opsi_b():
    dk = t.data_kolom()
    tangki = [e for e in dk.values() if "Pu_B" in e]
    assert len(tangki) == 6 and all(e["b"] == 0.80 for e in tangki)
    assert all(t.pu_gravitasi(e) == pytest.approx(e["Pu_B"]) for e in tangki)


def test_momen_kolom_dibagi_ke_sloof(r):
    mk = r["mk"]
    assert mk["M_maks"] >= max(max(b["Mx"], b["My"]) for b in mk["kelompok"]) - 1e-9
    assert all(b["M_dalam"] == pytest.approx(b["M_tepi"] / 2) for b in mk["kelompok"])
    assert all(0 < mk["me"][x] <= mk["M_maks"] for x in t.TIPE) and mk["me"]["SL-1"] >= mk["me"]["SL-2"]


def test_gravitasi_pynite_keseimbangan():
    g = t.gaya_garis("SL-2", 0.40, 0.80)
    total = (t.W_FASAD + g["w_diri"]) * 40.0 + t.D_PL * 5 * sum(float(w) for w in kl.BOBOT_SEGITIGA)
    assert sum(abs(x) for x in g["reaksi"]["D"]) == pytest.approx(total, rel=0.005)
    assert g["neg_g"] > 0 and g["pos_g"] > 0 and g["v_g"] > 0


def test_penurunan_beda_rumus():
    ig = 0.40 * 0.80 ** 3 / 12
    m16 = t.momen_penurunan(0.40, 0.80, t.DELTA_16)
    assert t.DELTA_16 == pytest.approx(0.016) and m16 == pytest.approx(6 * 4700 * math.sqrt(35) * 1000 * 0.35 * ig * 0.016 / 64, rel=1e-9)
    assert t.momen_penurunan(0.40, 0.80, t.DELTA_8) == pytest.approx(m16 / 2) and t.momen_penurunan(0.40, 0.80, t.DELTA_16, ie=1.0) == pytest.approx(m16 / 0.35)


def test_desain_400_800_dan_kandidat(r):
    assert r["desain"][("SL-2", 0.40, 0.80)]["ok"] and r["desain"][("SL-3", 0.40, 0.80)]["ok"]
    d1 = r["desain"][("SL-1", 0.40, 0.80)]
    assert not d1["ok"] and not d1["cek"]["rho"] and d1["atas"]["rho"] > 0.025
    assert r["desain"][("SL-1", 0.40, 0.90)]["ok"] and r["desain"][("SL-1", 0.50, 0.80)]["ok"]


def test_syarat_18_6_dan_18_13(r):
    for k, d in r["desain"].items():
        if not d["ok"]:
            continue
        assert d["bawah"]["As"] >= 0.5 * d["atas"]["As"] - 1e-9 and max(d["atas"]["rho"], d["bawah"]["rho"]) <= 0.025
        assert d["s_ujung"] <= min(d["d"] / 4, 0.150, d["b"] / 2, 0.300) + 1e-9 and d["s_tengah"] <= min(d["d"] / 2, d["b"] / 2, 0.300) + 1e-9
        assert d["b"] >= (8.0 - 0.75) / 20 and d["Vc"] == 0.0 and d["Ve"] >= d["Vg"]
        for v in d["kasus"].values():
            assert v["r_neg"] <= 1.0 + 1e-9 and v["r_pos"] <= 1.0 + 1e-9


def test_gempa_menentukan_dan_sensitivitas(r):
    d = r["desain"][("SL-2", 0.40, 0.80)]
    assert d["kasus"]["E"]["neg"] > d["kasus"]["G+T"]["neg"] > d["kasus"]["G"]["neg"]
    a16 = r["sensitivitas"][(0.40, 0.80, t.DELTA_16, True)]["SL-2"]
    a8 = r["sensitivitas"][(0.40, 0.80, t.DELTA_8, True)]["SL-2"]
    assert a16["T"] == pytest.approx(2 * a8["T"]) and a16["atas"]["As"] >= a8["atas"]["As"] >= d["atas"]["As"]
    assert r["jepit"][("SL-1", 0.40, 0.80)]["ok"] and r["jepit"][("SL-1", 0.40, 0.80)]["atas"]["As"] < r["desain"][("SL-1", 0.40, 0.80)]["atas"]["As"]


def test_ujung_sloof():
    assert t.ldh(25) == pytest.approx(420 * 25 / (5.4 * math.sqrt(35)), rel=1e-9) and t.ldh(10) == 150.0
    assert t.ld_lurus(29, True) == pytest.approx(1.3 * t.ld_lurus(29, False))
    u = {x["jenis"]: x for x in t.ujung_tabel(29)}
    kolom = [x for k, x in u.items() if k.startswith("kolom tepi")]
    assert all(x["perlu"] <= x["ada"] for x in kolom)
    inti = u["inti: kait 90° ke dinding inti 350"]
    assert inti["perlu"] > inti["ada"]


def test_jarak_mri_lebih_dari_satu_meter(r):
    assert len(r["mri"]) == 4 and all(m["jarak"] > 1.0 for m in r["mri"])
    j = {m["nama"]: m["jarak"] for m in r["mri"]}
    assert j["as 10 (x 84)"] == pytest.approx(3.3) and j["as 9 (x 76)"] == pytest.approx(4.3)
    assert j["as E (y 59)"] == pytest.approx(1.8)


def test_t93_cek_silang(r):
    x = r["t93"]
    assert x["a"]["skrip"] == pytest.approx(x["a"]["tangan"], rel=t.TOL["a"] / 100)
    assert x["b"]["pynite"] == pytest.approx(x["b"]["tangan"], rel=t.TOL["b"] / 100)
    assert x["c"]["pynite"] == pytest.approx(x["c"]["tangan"], rel=t.TOL["c"] / 100)
    assert x["d"]["cp_neg"] == pytest.approx(x["d"]["sendiri_neg"], rel=t.TOL["d"] / 100)
    assert x["d"]["cp_pos"] == pytest.approx(x["d"]["sendiri_pos"], rel=t.TOL["d"] / 100)
    assert x["d"]["cp_tarik"] < x["d"]["cp_neg_penuh"]       # tarik ikat menurunkan kapasitas lentur


def test_excel_cocok_dengan_python(tmp_path):
    f = t.buat_excel(tmp_path / "5.4.xlsx")
    ok, pesan = t.cocokkan(f)
    assert ok, pesan


def test_md_berlabel_status(tmp_path):
    f = t.buat_md(tmp_path / "5.4.md")
    teks = f.read_text(encoding="utf-8")
    assert ("disetujui Defsa" if t.KEPUTUSAN else "draf, menunggu persetujuan Defsa") in teks.splitlines()[0]
    assert "belum ada di acuan" in teks and "## Yang perlu diputuskan Defsa" in teks and "## Keputusan Defsa" in teks
