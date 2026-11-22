import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap5_telaah as t  # noqa: E402


def test_parse_rentang():
    assert t.parse_rentang("66,0-77,0") == (66.0, 77.0)
    assert t.parse_rentang("38-40,8") == (38.0, 40.8)
    assert t.parse_rentang(5) == (5.0, 5.0)


def test_jarak_mri_ke_jalur():
    j = t.ringkas()["jarak"]
    assert abs(j["sumbu_jalur"] - 10.5) < 1e-9
    assert abs(j["tepi_barat_lajur"] - 7.5) < 1e-9
    assert abs(j["tepi_p4"] - 13.5) < 1e-9
    assert j["sumbu_jalur"] < 12 and j["tepi_p4"] >= 12


def test_jarak_lift_dan_shaft():
    j = t.ringkas()["jarak"]
    assert abs(j["L-1..4"] - 26.5) < 0.05 and abs(j["L-5..6"] - 25.3) < 0.05 and j["L-7"] > 40
    assert abs(j["SH-6"] - 2.3) < 0.05 and abs(j["R-06"] - 5.4) < 0.05


def test_as_terdekat_isocenter_dan_akibat():
    r = t.ringkas()
    a = r["as_iso"]
    assert a[0][0] == "as E" and abs(a[0][2] - 2.0) < 1e-9
    assert abs(a[1][2] - 3.5) < 1e-9 and abs(a[2][2] - 4.5) < 1e-9
    assert all(d > t.RADIUS_NONMAGNET for _, _, d in a)
    ak = r["akibat"]
    assert ak["x_iso_maks"] == 76.0 and ak["tepi_min"] == 92.5 and abs(ak["makan_p4"] - 4.5) < 1e-9


def test_tepi_tangki_di_tengah_bentang():
    tangki = next(i for i in t.baca_item() if i["kode"] == "M-02")
    assert tangki["x"] == (60.0, 72.0) and tangki["y"] == (67.0, 73.0)
    (v0, n0, d0), (v1, n1, d1) = t.analisis_tepi(*tangki["x"], t.GRID_X, t.NAMA_X)
    assert d0 == 0 and n0 == ["7"] and v1 == 72.0 and n1 == ["8", "9"] and abs(d1 - 4.0) < 1e-9
    (_, n2, d2), (_, n3, d3) = t.analisis_tepi(*tangki["y"], t.GRID_Y, t.NAMA_Y)
    assert d2 == 0 and n2 == ["F"] and n3 == ["G"] and abs(d3 - 2.0) < 1e-9
    assert "di tengah bentang" in t.status_plot(60, 72, 67, 73)
    assert t.status_plot(68, 76, 51, 59) == "di atas as"


def test_tekanan_angkat_pit():
    u = {p["kode"]: p["u"] for p in t.ringkas()["pit"]}
    assert [round(u["L-1..4"][k], 1) for k in ("tekan", "q50", "q100")] == [3.4, 9.8, 14.3]
    assert [round(u["L-5..6"][k], 1) for k in ("tekan", "q50", "q100")] == [1.5, 7.8, 12.4]
    assert [round(u["L-7"][k], 1) for k in ("tekan", "q50", "q100")] == [2.5, 8.8, 13.3]
    assert all(abs(p["jumlah_cek"] - t.LT1) < 1e-9 for p in t.ringkas()["pit"])
    assert t.tekanan_angkat(10.0, 11.0) == 0.0


def test_beban_atap_dari_daftar_alat():
    a = t.ringkas()["atap"]
    assert abs(a["chiller"] - 463.2) < 0.01 and abs(a["tangki"] - 2168.0) < 0.01
    assert abs(a["jumlah"] - 2676.1) < 0.01 and abs(a["q"] - 2.32) < 0.01
    assert abs(a["ring_jumlah"] - 1748.1) < 0.01


def test_konsistensi_satuan():
    for butir, v, h, *_ in t.konsistensi():
        if "Luas" in butir or "Magnet" in butir or "Tangki di Daftar" in butir or "Tekanan per kaki" in butir:
            assert abs(v - h) <= 0.12, butir
    pel = next(h for b, v, h, *_ in t.konsistensi() if "Pelindung MRI" in b)
    assert abs(pel - 7.17) < 0.01


def test_cek_acuan():
    hasil = dict(t.cek_acuan(["privat/SNI-2847-2019-Beton-Struktural.pdf"]))
    assert hasil["SNI 2847:2019 (beton struktural)"]
    assert hasil["ASTM A955 (tulangan baja tahan karat)"] is None
