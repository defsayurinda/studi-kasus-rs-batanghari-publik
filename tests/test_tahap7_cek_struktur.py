"""Uji cepat 7.3 (tanpa OpenSees dan BIMCraft): tata letak chiller, kantilever pit, perlebaran Cap E, rumus Rayleigh."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap7_cek_struktur as cs  # noqa: E402


def test_y63_muat_hanya_diputar():
    y = cs.muat_y63()
    assert not y["muat_x"] and y["muat_y"] and y["tumpang_tangki"] == 0.0


def test_rel_baru_tidak_menabrak_balok_induk():
    t = cs.tata_chiller("baru")
    rel = [g[1] for g in t["garis"] if g[6] == "rel"]
    induk = [(g[1], g[4]) for g in t["garis"] if g[0] == "y" and g[6] == "induk"]
    assert len(rel) == 7
    for x in rel:
        for xi, b in induk:
            assert abs(x - xi) >= (0.30 + b) / 2 - 1e-6


def test_rayleigh_balok_sendi_merata():
    # f = 0,18 √(g/Δ) dengan Δ = 5wL⁴/384EI mendekati π/(2L²) √(EI/m) dalam 1 %
    ei, w, L = 80_000.0, 15.0, 8.0
    d = 5 * w * L ** 4 / (384 * ei)
    eksak = math.pi / (2 * L ** 2) * math.sqrt(ei / (w / 9.81))
    assert abs(0.18 * math.sqrt(9.81 / d) - eksak) / eksak < 0.01


def test_pit_l7_tertutup_dan_tiang_berjarak():
    p = cs.pit_k04b()
    assert p["pit_tertutup"] and p["jarak_min"] >= 2.4 - 1e-9
    assert p["opsi_a"]["P_layan"] > p["izin"] >= p["dasar"]["P_layan"]   # tanpa tiang gagal, dasar lolos
    assert p["rasio_lokal"] < 1.0 and p["kant"]["lolos"]
