import re
import sys
from pathlib import Path

from docx import Document

AKAR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AKAR / "skrip"))

import laporan_akhir as la  # noqa: E402


def _teks():
    doc = Document(la.KELUAR)
    sel = [c.text for t in doc.tables for r in t.rows for c in r.cells]
    return "\n".join([p.text for p in doc.paragraphs] + sel)


def test_bab_wajib_dan_pdf():
    assert la.KELUAR.exists() and la.PDF.exists()
    teks = _teks().upper()
    for kata in ("RINGKASAN EKSEKUTIF", "DATA DAN GEOTEKNIK", "STRUKTUR BAWAH", "RAB DAN REKAYASA NILAI",
                 "JADWAL PELAKSANAAN", "BUTIR TERBUKA", "VE-6"):
        assert kata in teks


def test_t126_angka_sama_dengan_ringkasan_tahap():
    r8 = (AKAR / "08 RAB" / "Ringkasan Tahap 8.md").read_text(encoding="utf-8")
    r9 = (AKAR / "09 Jadwal" / "Ringkasan Tahap 9.md").read_text(encoding="utf-8")
    assert f"**{la.RAB_TOTAL}**" in r8 and la.RAB_SEBELUM_PPN in r8
    for div, nilai, porsi in la.RAB:
        assert f"| {nilai} | {porsi} |" in r8, div
    assert f"durasi {la.DURASI_MINGGU} minggu" in r9
    assert f"{la.TIANG} tiang" in r8
    # Σ divisi = jumlah sebelum PPN
    jumlah = sum(float(n.replace(",", ".")) for _, n, _ in la.RAB)
    assert abs(jumlah - float(la.RAB_SEBELUM_PPN.replace(",", "."))) < 0.015


def test_t127_ringkasan_sama_dengan_isi():
    teks = _teks()
    assert len(re.findall(rf"Rp {la.RAB_TOTAL} miliar", teks)) >= 1 and la.RAB_TOTAL in teks
    assert len(re.findall(rf"{la.DURASI_MINGGU} minggu", teks)) >= 2
