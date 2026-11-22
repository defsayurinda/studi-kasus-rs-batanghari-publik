import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap5_gambar_ded as gd  # noqa: E402


def md(nama):
    return (gd.KELUAR / nama).read_text(encoding="utf-8")


def test_lembar_gs22_sampai_gs26():
    assert list(gd.LEMBAR) == [f"GS-{i}" for i in range(22, 27)]


def test_angka_pit_sama_dengan_md():
    t = md("5.5 Desain Pit Lift.md")
    for k, (atas, bawah) in gd.PIT_TUL.items():
        baris = [b for b in t.splitlines() if b.startswith(f"| {k} |") and "D13-" in b and "Pons" not in b]
        assert any(atas in b and bawah in b for b in baris), k
    assert "D13-250 luar; D13-275 dalam" in t
    for _, z in gd.AIR:
        assert gd.idn(z, 2) in t


def test_angka_mri_dan_stek_sama_dengan_md():
    t3, t6 = md("5.3 Desain Pelat LT1.md"), md("5.6a Kolom Tangki Opsi B.md")
    assert "144,60 kg" in t3 and "580 mm" in t3 and "3,16 m" in t3 and "11 batang per lapis" in t3
    assert f"{gd.STEK['ldh']} / {gd.STEK['ld']} / {gd.STEK['ldc']}" in t6
    assert "1.093 / 1.125" in t6
    for lv, v in gd.KOLOM_TB.items():
        assert any(f"({v['rho']} %)" in b and f"{v['pm']} (" in b and f"| {v['ve']} |" in b
                   for b in t6.splitlines() if b.startswith(f"| K-TB {lv} (800)")), lv


def test_sloof_sama_dengan_md():
    t = md("5.4 Desain Sloof.md")
    d = gd.sloof_data()
    assert (d["SL-1"]["atas"]["n"], d["SL-1"]["atas"]["db"], d["SL-1"]["bawah"]["n"], d["SL-1"]["bawah"]["db"]) == (10, 29, 8, 25)
    assert "| SL-1 | 400 × 900 | 10 D29 / 8 D25 |" in t
    assert "| SL-2 | 400 × 800 | 6 D29 / 4 D29 |" in t and "| SL-3 | 400 × 800 | 11 D22 / 5 D29 |" in t
    assert "D13-150 / 200" in t and "D13-125 / 200" in t
    assert (d["SL-2"]["s_ujung"], d["SL-2"]["s_tengah"], d["SL-3"]["s_ujung"]) == pytest.approx((0.15, 0.2, 0.125))
    assert d["SL-3"]["kaki"] == 4


@pytest.mark.parametrize("no", ["GS-22", "GS-23", "GS-24", "GS-25", "GS-26"])
def test_dwg_tanpa_teks_bertumpuk(no):
    import cad_cek
    dwg = list(gd.DWG.glob(f"{no} *.dwg"))
    if not dwg:
        pytest.skip("DWG belum dibangun (jalankan skrip/tahap5_gambar_ded.py)")
    assert cad_cek.cek(dwg[0]) == []
