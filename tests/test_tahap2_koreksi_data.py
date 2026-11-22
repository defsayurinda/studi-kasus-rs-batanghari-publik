import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap2_koreksi_data as t2  # noqa: E402


def test_baca_energi_lengkap():
    data = t2.baca_energi()
    assert len(data) == 25
    assert {d[0] for d in data} == set(t2.RIG)
    assert all(40 <= d[3] <= 100 for d in data)


def test_lembar_terbentuk(tmp_path):
    keluar = t2.buat(tmp_path / "uji.xlsx")
    wb = openpyxl.load_workbook(keluar)
    assert wb.sheetnames == ["Petunjuk", "Energi Palu", "ER Desain", "N60", "Ringkasan N60", "Ringkasan qt"] + [f"qt CPTu-{i}" for i in range(1, 9)] + ["Mutu Contoh"]
    ws = wb["Energi Palu"]
    assert ws.freeze_panes is not None
    assert not ws.sheet_view.showGridLines
    assert wb["ER Desain"].freeze_panes is not None
    nilai = [c.value for row in wb["ER Desain"].iter_rows() for c in row]
    assert "BH-6" in nilai and "Lama" in nilai


def test_baca_spt_dan_status():
    spt = t2.baca_spt()
    assert len(spt) == 204
    assert all(isinstance(u["n"], (int, float)) for u in spt)
    tidak = [(u["bor"], u["dari"]) for u in spt if t2.status_spt(u)[0] == "Tidak"]
    assert sorted(tidak) == [("BH-2", 12), ("BH-2", 14), ("BH-2", 16), ("BH-2", 18), ("BH-8", 1.5)]
    assert sum(u["jenis"] == "Penolakan" for u in spt) == 32


def test_baca_cptu():
    cptu = t2.baca_cptu()
    assert list(cptu) == [f"CPTu-{i}" for i in range(1, 9)]
    assert all(len(v) == 599 for k, v in cptu.items() if k != "CPTu-8")
    assert len(cptu["CPTu-8"]) == 680
    assert t2.catatan_cptu("CPTu-4", 3.0, 0.2, 10).startswith("u2 tidak andal")


def test_mutu_contoh():
    import tahap2_mutu_contoh as mc
    assert mc.peringkat_lunne(0.035, 1.5) == "Sangat baik-istimewa"
    assert mc.peringkat_lunne(0.035, 3.0) == "Baik-cukup"
    assert mc.peringkat_lunne(0.2, 5.0).startswith("Di luar")
    assert mc.peringkat_sqd(1.5) == "B"
    h = {(x["titik"], x["contoh"]): x for x in mc.hitung(0.0)}
    assert len(h) == 15
    assert h[("BH-2", "UD-2")]["lunne"] == "Buruk"
    assert h[("BH-5", "UD-5")]["lunne"] == "Sangat baik-istimewa"
    # sigma'v0 lempung lunak 3,25 m: kira-kira (17 x 0,5 + 17,8 x 1,3 + 15,2 x 1,5) - 9,81 x 3,25
    assert 18 < h[("BH-1", "UD-2")]["sv0"] < 25
