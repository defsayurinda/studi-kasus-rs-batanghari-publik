"""Uji 7.7 RKS: angka dari dokumen sumber (T-116), pasal berstatus (T-115), docx terbentuk."""
import sys
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap7_rks as r  # noqa: E402


def test_angka_ada_di_sumber():
    for kunci, (teks, berkas) in r.ANGKA.items():
        isi = (r.AKAR / berkas).read_text(encoding="utf-8")
        assert teks in isi, f"{kunci}: '{teks}' tidak ada di {berkas}"


def test_pasal_berstatus():
    for bab, acuan, pasal, hal, status in r.PASAL:
        if status == r.DICEK:
            assert hal != "-", f"{acuan} {pasal}: dicek tanpa halaman"
        assert status in (r.DICEK, r.BELUM) or "acuan/publik" in status


def test_docx_terbentuk(tmp_path, monkeypatch):
    monkeypatch.setattr(r, "KELUAR", tmp_path / "rks.docx")
    d = Document(r.main(pdf=False))
    teks = "\n".join(p.text for p in d.paragraphs)
    for judul in ("Tiang Bor dan Uji Tiang", "Dewatering Galian Cap", "Kedap Air", "Fasad", "MEP Dasar"):
        assert judul.upper() in teks.upper()
    assert r.a("uji_s") in teks and "belum ada di acuan" in teks
