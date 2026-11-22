import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap6_telaah as t  # noqa: E402


def test_jumlah_tiang_dan_gedung():
    tg = t.tiang()
    assert len(tg) == 373
    assert sum(1 for x in tg if x["gedung"] == "utama") == 305
    assert sum(1 for x in tg if x["gedung"] != "utama") == 68
    assert len(t.kelompok()) == 102


def test_pasangan_dekat():
    ps = t.pasangan()
    assert len(ps) == 39
    assert sum(1 for p in ps if p["kurang20"]) == 30
    assert abs(min(p["d"] for p in ps) - 0.828) < 0.001
    assert len(t.zona_gabung(ps)) == 14 and not any(p["sama"] for p in ps)


def test_reaksi_77_titik():
    rk = t.reaksi()
    assert len(rk) == 77
    cm = t.cek_murah()
    assert cm["n_kol"] == 70 and cm["n_inti"] == 7
    cr, tanpa = t.cocok_reaksi()
    assert all(r["selisih"] < 0.01 for r in cr) and tanpa == []
    assert abs(cm["sum_tambah"] - 58040.1) < 0.2          # T-95
    assert abs(cm["sel_pmax_DL"]) < 0.5


def test_elevasi_kepala_tiang():
    assert abs(t.KEPALA_TIANG - 10.85) < 1e-9
    el = t.elevasi()
    assert abs(el[0]["terendam"] - 0.35) < 1e-9 and abs(el[2]["terhadap_muka"] - 0.26) < 1e-9


def test_acuan_belum_ada():
    h = dict(t.cek_acuan())
    assert h["SNI 8460:2017 (pasal tiang, jarak, uji; pasal 10 pengangkuran)"]
    assert h["Fellenius (bidang netral, gesekan negatif)"] is None


def test_berkas_keluaran_ada():
    for f in (t.BERKAS, t.MD, t.DWG, t.PNG, t.PDF):
        assert f.exists(), f


def test_t98():
    r = t.t98()
    assert r["lolos"] and r["dwg"]["n"] == 373 and r["ifc"]["p24"] == 39
    assert "| T-98 |" in t.VERIFIKASI.read_text(encoding="utf-8")
