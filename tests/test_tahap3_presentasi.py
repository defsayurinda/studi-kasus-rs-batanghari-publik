import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import rapat_desain_konsep as rk  # noqa: E402
import tahap3_biaya as bi  # noqa: E402
import tahap3_presentasi as tp  # noqa: E402


def test_slide_memakai_angka_skrip():
    isi = tp.isi()
    biaya = next(x for x in isi if x[0].startswith("Perkiraan biaya"))
    baris = biaya[2]["tabel"][1]
    assert ["Perkiraan (termasuk PPN)", tp.m(bi.rekap()["total"])] in baris
    assert len(next(x for x in isi if x[0].startswith("Rekayasa"))[2]["tabel"][1]) == len(bi.rekayasa_nilai())


def test_gambar_slide_ada():
    for _, _, lampiran in tp.isi():
        if lampiran and "gambar" in lampiran:
            assert (tp.GAMBAR / lampiran["gambar"]).exists(), lampiran["gambar"]


def test_notulen_lengkap():
    ag = rk.agenda()
    assert len(ag) == 10 and all(len(a) == 4 and all(a) for a in ag)
    assert len(rk.KEPUTUSAN) == 13
