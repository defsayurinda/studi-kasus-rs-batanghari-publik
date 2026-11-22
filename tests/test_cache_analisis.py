import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import cache_analisis as ca  # noqa: E402
import tahap4_model as tm  # noqa: E402


def test_cache_disk_kena_dan_kunci_ukuran(tmp_path, monkeypatch):
    monkeypatch.setattr(ca, "FOLDER", tmp_path)
    monkeypatch.delenv("TANPA_CACHE", raising=False)
    panggil = []

    @ca.disk
    def hitung(konfig="K2"):
        panggil.append(konfig)
        return {"konfig": konfig, "balok": dict(tm.UKURAN_BALOK)}

    assert hitung("K2") == hitung("K2") and panggil == ["K2"]          # kedua kali dari disk
    hitung("K1")
    assert panggil == ["K2", "K1"]                                       # argumen beda: hitung
    monkeypatch.setattr(tm, "UKURAN_BALOK", {("LT2", 0): (0.4, 0.8)})
    assert hitung("K2")["balok"] == {("LT2", 0): (0.4, 0.8)} and len(panggil) == 3   # ukuran model beda: hitung
    monkeypatch.setenv("TANPA_CACHE", "1")
    hitung("K2")
    assert len(panggil) == 4                                             # cache dimatikan
    assert len(list(tmp_path.glob("*.pkl"))) == 3 and not list(tmp_path.glob("*.tmp"))
