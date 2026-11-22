import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap4_telaah as t  # noqa: E402


def test_koreksi_lintasan():
    # d = 4 m, sumber 3 m: lintasan miring 5 m -> waktu tegak = t × 4/5
    assert abs(t.koreksi_lintasan(np.array([4.0]), np.array([0.05]))[0] - 0.04) < 1e-12


def test_loncatan_pemicu_dan_vs():
    r = t.ringkas()
    assert 3.5e-3 < r["off"] < 4.5e-3            # loncatan sakelar pemicu ±4 ms
    assert abs(r["vs_a"] - r["vs_b"]) / r["vs_a"] < 0.02
    i = t.RUAS.index((46, 47))
    assert r["vs_penyedia"][i] < 200 and r["vs_koreksi"][i] > 400   # lapisan lunak palsu hilang
    assert abs(r["vs30"] - 156) < 2


def test_frekuensi_seperempat():
    r = t.ringkas()
    assert 2.3 < r["f95"] < 2.6 and 1.1 < r["f33"] < 1.35 and 0.75 < r["f80"] < 0.9


def test_beban_atap_dari_daftar_alat():
    r = t.ringkas()["atap"]
    assert abs(r["jumlah"] - 2676.1) < 0.5       # bukan 1.748,1 kN di Ringkasan Atap
    assert abs(r["q_tangki"] - 30.1) < 0.1
