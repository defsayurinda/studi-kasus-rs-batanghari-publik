import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import audit_akhir as au  # noqa: E402


def test_blok_tabel_dan_daftar():
    md = "## I. Uji\n\n**Tabel: Contoh**\n\n| A | B |\n|---|---|\n| `x` | 2 |\n\nSumber: s.\n\n- satu\n- dua\n"
    bl = au.blok(md)
    assert ("h2", "I. Uji") in bl
    assert ("t", [["A", "B"], ["x", "2"]]) in bl
    assert ("l", ("huruf", ["satu", "dua"])) in bl
    assert ("p", "Sumber: s.") in bl


def test_docx_terbentuk_dan_memuat_angka_kunci(tmp_path, monkeypatch):
    monkeypatch.setattr(au, "KELUAR", tmp_path / "a.docx")
    au.bangun()
    from docx import Document
    d = Document(tmp_path / "a.docx")
    teks = " ".join(c.text for t in d.tables for r in t.rows for c in r.cells)
    assert "25 / 11" in teks and "321" in teks and "AU-16" in teks
