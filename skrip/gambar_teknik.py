"""Alat bantu gambar Tahap 2: lembar A3 (`Kertas`) dan penggabung PDF (`BukuPDF`).

`Kertas` sekarang adalah cad_grafik.LembarCAD: isi lembar digambar langsung di CADCraft sebagai entitas CAD asli
(model space berkoordinat nyata untuk peta dan penampang, grafik CAD di layout) dengan kop KOP_A3. Lihat
cad_grafik.py. Satuan tata letak dalam milimeter kertas.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pypdf import PdfReader, PdfWriter

from cad_grafik import LembarCAD as Kertas  # noqa: F401  gambar digambar langsung di CADCraft

STATUS = "DISETUJUI 19 NOV 2026"  # status gambar Tahap 2 setelah disetujui Defsa

plt.rcParams.update({"font.family": "Arial", "font.size": 7, "axes.linewidth": 0.6, "hatch.linewidth": 0.4,
                     "pdf.fonttype": 42})


class BukuPDF:
    """Pengganti PdfPages: mengumpulkan halaman PDF hasil cetak CADCraft menjadi satu berkas."""

    def __init__(self, path):
        self.path = Path(path)
        self.halaman = []
        self._info = {}

    def tambah(self, halaman):
        self.halaman.append(Path(halaman))

    def infodict(self):
        return self._info

    def __enter__(self):
        return self

    def __exit__(self, *a):
        if a[0] is not None:
            return False
        tulis = PdfWriter()
        for h in self.halaman:
            for hal in PdfReader(str(h)).pages:
                tulis.add_page(hal)
            h.unlink()
        tulis.add_metadata({f"/{k}": str(v) for k, v in self._info.items()} | {"/Creator": "CADCraft 0.20.1"})
        with open(self.path, "wb") as f:
            tulis.write(f)
