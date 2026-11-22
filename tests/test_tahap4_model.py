import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap4_model as tm  # noqa: E402


def test_kotak_simetris():
    a, ix, iy, j, avx, avy = tm.kotak(8.0, 8.0, 0.35)
    assert abs(a - (8.35 ** 2 - 7.65 ** 2)) < 1e-9 and abs(ix - iy) < 1e-9 and abs(avx - avy) < 1e-9


def test_cqc_satu_ragam_dan_ragam_jauh():
    assert abs(tm.cqc([[3.0]], [10.0])[0] - 3.0) < 1e-12
    # dua ragam berjauhan -> mendekati SRSS
    r = tm.cqc([[3.0], [4.0]], [10.0, 100.0])[0]
    assert abs(r - 5.0) < 0.01


def test_kantilever_inti_rumus_dan_pynite():
    k = tm.kantilever_inti(True)
    assert abs(k["ops"] / k["rumus"] - 1) < 1e-6
    assert abs(tm.kantilever_inti(False)["ops"] / tm.kantilever_pynite() - 1) < 1e-4


def test_ragam_k1_partisipasi_penuh():
    rg = tm.ragam("K1")
    assert abs(sum(rg["mx"]) - 1) < 1e-6 and abs(sum(rg["my"]) - 1) < 1e-6
    assert max(rg["T"]) < 0.6


def test_spektrum_desain_dipakai():
    assert abs(tm.sa(0.5) - 0.386) < 0.002          # plateau 80 % SE (4.1 opsi a)
    assert abs(tm.sa(0.5, "SE") - 0.482) < 1e-6
