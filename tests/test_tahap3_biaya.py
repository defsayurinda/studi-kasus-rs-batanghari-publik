import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap3_biaya as bi  # noqa: E402
import tahap3_program as pr  # noqa: E402


def test_luas_fungsi_sama_dengan_luas_massa():
    lf = bi.luas_fungsi()
    assert math.isclose(sum(b["bruto"] for b in lf), pr.cek_massa()["luas_lantai"])


def test_koefisien_pasal_31():
    assert bi.koef_ruang("Kamar operasi", "Bedah Sentral")[0] == 2.0
    assert bi.koef_ruang("ICU", "Intensif")[0] == 1.5
    assert bi.koef_ruang("Radiologi: CT scan", "Penunjang Medik")[0] == 1.25
    assert bi.koef_ruang("Kamar 2 TT", "Rawat Inap")[0] == 1.1
    assert bi.koef_ruang("Drop-off ambulans (beratap)", "Gawat Darurat")[0] == 0.5


def test_biaya_standar_tangan():
    # baris pertama: lobi 260 m² × 1,45 × 1,1 × 1,197 × HSBGN
    b = bi.luas_fungsi()[0]
    assert math.isclose(b["biaya"], 260 * pr.FAKTOR_BRUTO * 1.1 * bi.KL["UTAMA"] * bi.HSBGN)


def test_nonstandar_dalam_rentang_pasal_29():
    for kode, _, _, mn, mx, pakai, _ in bi.NONSTANDAR:
        assert mn <= pakai <= mx, kode


def test_rekap_jumlah_dan_kontinjensi():
    r = bi.rekap()
    assert math.isclose(r["subtotal"], sum(b[1] for b in r["baris"]))
    assert math.isclose(r["total"], r["subtotal"] * (1 + bi.KONTINJENSI))
    assert r["total"] > bi.PAGU  # pagu tidak cukup: temuan utama 3.8


def test_struktur_di_dalam_porsi_standar():
    r = bi.rekap()
    s = r["standar"]["total"]
    assert 0.25 * s <= r["struktur_nyata"] <= 0.35 * s


def test_rentang_mengapit_nilai_pakai():
    lo, hi = bi.ringkasan()["rentang"]
    assert lo < bi.rekap()["total"] < hi


def test_rekayasa_nilai_kumulatif():
    ve = bi.rekayasa_nilai()
    assert all(o["hemat"] > 0 for o in ve)
    assert math.isclose(ve[-1]["sisa"], bi.rekap()["total"] - sum(o["hemat"] for o in ve))
