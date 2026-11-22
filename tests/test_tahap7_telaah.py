import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap7_telaah as t7  # noqa: E402


def test_nomor_lembar_unik_dan_berurutan():
    semua = [g[0] for g in t7.GA] + [g[0] for g in t7.GS_LAMA] + [g[0] for g in t7.GS_BARU] + [g[0] for g in t7.GM]
    assert len(semua) == len(set(semua))
    gs = [int(n[3:]) for n, *_ in t7.GS_LAMA + t7.GS_BARU]
    assert gs == list(range(1, len(gs) + 1))


def test_rks_punya_status_acuan():
    assert all(r[3] for r in t7.RKS)
    assert any(t7.B in r[3] for r in t7.RKS)   # acuan yang belum ada ditulis, tidak ditebak
