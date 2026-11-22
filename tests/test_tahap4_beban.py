import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap4_beban as b  # noqa: E402


def test_luas_lantai_dengan_v1_dan_void():
    k2 = {t["lv"]: t for t in b.berat_tingkat("K2")}
    assert abs(k2["LT2"]["luas"] - (3456 - 624)) < 1e-6        # void LT2
    assert abs(k2["LT3"]["luas"] - 3456) < 1e-6                # LT3 2.304 + atap V1 1.152
    assert abs(k2["LT4"]["luas"] - (1536 + 768)) < 1e-6        # menara + atap LT3 barat
    assert abs(k2["ATAP"]["luas"] - 1536) < 1e-6


def test_jumlah_kolom_grid():
    assert len(b.titik_kolom(b.PODIUM)) == 70
    assert len(b.titik_kolom(b.MENARA)) == 36
    assert len(b.titik_kolom(b.LT3)) == 70 - 18          # x 44-84, y 59-75 hilang (V1); as x 36 tetap tepi LT3 barat


def test_helipad_pasal_4_11():
    a = b.atap_khusus()
    assert abs(a["heli_terpusat"] - 0.75 * 6800 * 9.81 / 1000) < 1e-9
    assert a["heli_jarak"] == 2.44 and a["heli_merata"] == 2.87


def test_elf_manual():
    e = b.elf("K2")
    assert abs(e["Ta"] - 0.0488 * 25.8 ** 0.75) < 1e-9
    assert abs(e["Cs"] - 0.386 / (7 / 1.5)) < 1e-9             # Pers. (31) menentukan
    assert abs(sum(e["Fx"]) - e["V"]) < 1e-6
    assert 10.0 < e["W"] / sum(t["luas"] for t in e["tingkat"]) < 14.0   # cek wajar kPa rata-rata


def test_angin_tidak_menentukan():
    assert b.v_angin_setara_gempa() > 60.0


def test_kombinasi_ev():
    assert "1,277D" in b.KOMBINASI[5][1] and abs(1.2 + 0.2 * b.SDS - 1.2772) < 1e-4
