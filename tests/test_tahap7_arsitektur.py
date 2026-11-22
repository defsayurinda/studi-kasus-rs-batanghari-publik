"""Uji ringan 7.1 (tanpa BIMCraft): tata letak ruang, P4 76 motor, luas program, jumlah TT, level dan inti."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap7_arsitektur as a  # noqa: E402
import tahap4_beban as tb  # noqa: E402


@pytest.fixture(scope="module")
def susunan():
    prog = a.baca_program()
    return {lt: a.susun_lantai(lt, prog) for lt in a.LANTAI}


def test_semua_ruang_muat_tanpa_tumpang_tindih(susunan):
    """Tidak ada ruang tersisa, di luar denah, tumpang tindih, atau menabrak inti pada tiap lantai."""
    for lt, S in susunan.items():
        assert S.gagal == [], (lt, S.gagal)
        assert a.cek_geometri(S) == [], (lt, a.cek_geometri(S)[:3])


def test_luas_program_per_lantai_dalam_5_persen(susunan):
    """T-109: luas bersih ruang program tiap lantai dalam 5 % Rekap Lantai, total LT1-LT6 dalam 2 %."""
    rekap = a.baca_rekap()
    tot_i = tot_t = 0.0
    for lt, S in susunan.items():
        luas = sum(a._luas_bersih(r.poli) for r in S.ruang if r.program)
        assert abs(luas / rekap[lt][0] - 1) <= 0.05, (lt, luas, rekap[lt][0])
        tot_i, tot_t = tot_i + luas, tot_t + rekap[lt][0]
    assert abs(tot_i / tot_t - 1) <= 0.02


def test_tempat_tidur_rawat_inap_128(susunan):
    """VIP 8 + kamar 2 TT 10 ruang + kamar 4 TT 25 ruang = 8 + 20 + 100 = 128 TT di LT4-LT6."""
    kode = [r.kode for lt in ("LT4", "LT5", "LT6") for r in susunan[lt].ruang]
    assert (kode.count("P26"), kode.count("P27"), kode.count("P28")) == (8, 10, 25)
    assert kode.count("P26") + 2 * kode.count("P27") + 4 * kode.count("P28") == 128


def test_p4_76_motor_di_barat():
    """P4: 76 motor dalam x 1-7, y 35-63,5; dua baris 38 motor, pitch 0,75 m, tidak bertabrakan."""
    p = a.posisi_p4()
    assert len(p) == 76
    x0, y0, x1, y1 = a.P4_BAWAH
    assert (x0, y0, x1, y1) == (1.0, 35.0, 7.0, 63.5)
    assert all(x0 <= x <= x1 and y0 <= y <= y1 for x, y in p)
    for xs in {x for x, _ in p}:
        ys = sorted(y for x, y in p if x == xs)
        assert len(ys) == 38 and all(abs((q - r) - 0.75) < 1e-9 for r, q in zip(ys, ys[1:]))
    # pohon V4 di x = 4 dipindah ke x = 9,5 dan tidak masuk P4
    assert all(x != 4.0 for x, _ in a.posisi_pohon())


def test_level_dan_inti():
    """Level LT1-ATAP dari tahap4_beban; tinggi tingkat 4,5 / 4,5 / 4,2 ...; inti 7 di LT1, 6 di LT4 (lift + 3 tangga menembus)."""
    assert [round(a.TINGGI_LT[lt]) for lt in a.LANTAI] == [4500, 4500, 4200, 4200, 4200, 4200]
    assert tb.LEVEL["LT1"] == 12.85 and tb.LEVEL["ATAP"] == 38.65
    assert len(a.inti_lantai("LT1")) == 7
    assert len(a.inti_lantai("LT4")) == 4
    for _, _, luar, dalam in a.inti_lantai("LT1"):
        assert luar.contains(dalam)
