import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap4_fasad as fs  # noqa: E402


def test_fp_dan_batas():
    n = fs.hitung()
    # 0,4 ap SDS Ip/Rp (1 + 2 z/h) = 0,4 × 1,25 × 0,386 × 1,5 × 3 = 0,8685, di antara 0,3 dan 1,6 SDS Ip
    assert math.isclose(n["fp"], 0.4 * 1.25 * 0.386 * 1.5 * 3, rel_tol=1e-9)
    assert 0.3 * 0.386 * 1.5 <= n["fp"] <= 1.6 * 0.386 * 1.5
    assert n["Dpl"] >= 13.0


def test_angkur_memenuhi():
    n = fs.hitung()
    for s in ("ns", "tk"):
        assert n[f"{s}_rNV"] <= 1.2
        assert n[f"{s}_rN"] <= 1.0 and n[f"{s}_rV"] <= 1.0
    # tangan: tarik baris atas 1,4D B-T = 1,4 × M / z
    assert math.isclose(n["tk_K1_N"], 1.4 * n["tk_DM"] / 0.15, rel_tol=1e-9)


def test_rumus_excel_sama():
    alamat = {"a": "$E$5", "b": "$E$6"}
    assert fs._ke_excel("max(a,b**1.5)/sqrt(a)", alamat) == "=MAX($E$5,$E$6^1.5)/SQRT($E$5)"


def test_berat_fasad_lebih_ringan_dari_42():
    b = fs.berat_fasad()
    assert b["wv3"] < b["w42"]
    # keliling as: podium 2 × (72 + 48) × 9 m + LT3 + menara 2 × (64 + 24) × 12,6 m
    tot_as = sum(s["L_as"] * s["h"] for s in b["rinci"])
    assert math.isclose(tot_as, 240 * 9.0 + sum(s["L_as"] for s in b["rinci"] if s["pita"] == "LT3-LT4") * 4.2
                        + 176 * 12.6, rel_tol=1e-9)
    assert all(s["L_fs"] > s["L_as"] - 1e-9 for s in b["rinci"] if s["orientasi"] == "U-S")
