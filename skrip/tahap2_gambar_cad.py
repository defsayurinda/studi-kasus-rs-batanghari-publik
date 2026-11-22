"""Bangun ulang seluruh gambar Tahap 2 (GT-01 s.d. GT-15) di jendela CADCraft dengan kop tunggal KOP_A3.

Setiap lembar digambar sebagai gambar CAD asli (cad_grafik.LembarCAD): denah, peta, dan penampang di model space
berkoordinat nyata (1 unit = 1 mm) lewat viewport berskala; grafik data di layout dengan bingkai, garis skala,
kurva per layer, dan legenda; arsir unit tanah dari templat/geoteknik.pat; cetak hitam-putih (monochrome.ctb).
Keluaran per gambar: '02 Olah Data Tanah/Gambar/DWG/<nama>.dwg' (bisa dibuka dan diedit di CADCraft), PNG di
'Gambar/', dan PDF gabungan per langkah (dicetak CADCraft, A3 skala 1:1). Excel tidak disentuh.
Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap2_gambar_cad.py          (di jendela CADCraft yang terbuka)
           set CADCRAFT_JENDELA=0 lalu jalankan untuk menggambar tanpa jendela.
"""
import os

os.environ.setdefault("CADCRAFT_JENDELA", "1")

import tahap2_gambar_air_tanah as g23  # noqa: E402
import tahap2_gambar_geoteknik as g22  # noqa: E402
import tahap2_gambar_parameter as g24  # noqa: E402
import tahap2_lembar_kelas_situs as g25  # noqa: E402
import tahap2_lembar_kimia_tebing_gudang as g27  # noqa: E402
import tahap2_lembar_likuifaksi as g26  # noqa: E402
import tahap2_pelengkap as g28  # noqa: E402
from gambar_teknik import BukuPDF  # noqa: E402


def buat():
    hasil = [g22.buat(), g23.buat(), g24.buat(), g25.gambar(), g26.gambar()]
    with BukuPDF(g27.PDF) as pdf:
        g27.gambar_tebing(pdf)
        g27.gambar_gudang(pdf)
        pdf.infodict()["Title"] = "2.7 Gambar Tebing dan Gudang - RS Tepian Batanghari (data simulasi)"
    hasil.append(g27.PDF)
    with BukuPDF(g28.PDF) as pdf:
        g28.gambar(pdf)
        pdf.infodict()["Title"] = "2.8 Gambar Penurunan Urugan - RS Tepian Batanghari (data simulasi)"
    hasil.append(g28.PDF)
    return hasil


if __name__ == "__main__":
    for p in buat():
        print(p)
