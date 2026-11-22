"""Tahap 0: rapikan bentuk 'Matriks Tanggapan TOR.xlsx' sesuai FORMAT LAPORAN DAN EXCEL.md.

Isi tidak diubah; hanya tata letak dan format. Aman dijalankan ulang (membaca tabel di mana pun letaknya).
Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap0_rapikan_matriks.py
"""
from pathlib import Path

import openpyxl

from format_dokumen import AI, Lembar, baca_tabel, set_font_bawaan

AKAR = Path(__file__).resolve().parents[1]
BERKAS = AKAR / "00 Kerangka Acuan" / "Matriks Tanggapan TOR.xlsx"
CATATAN = ("DIISI AI (Claude) atas permintaan Defsa, 18 Nov 2026 (sel hijau); "
           "dipahami dan disetujui Defsa 19 Nov 2026. Data skenario simulasi, tidak untuk konstruksi. Pasal dicek ke PDF "
           "di acuan/; dokumen yang belum ada ditandai 'belum ada di acuan/'.")

# nama lembar, kepala pertama, judul, lebar kolom, rata
LEMBAR = [
    ("Matriks Tanggapan", "No", "Matriks tanggapan KAK",
     [5, 9, 18, 34, 55, 14, 34, 34, 45, 9], "cclllclllc"),
    ("Telaah Program Ruang", "No baris", "Telaah program ruang",
     [9, 26, 18, 22, 40, 32, 36], "clllll l".replace(" ", "l")),
    ("Asumsi dan Data Diminta", "No", "Asumsi dan data yang diminta",
     [5, 16, 45, 40, 24, 20, 16], "cclllcc"),
    ("Acuan Normatif", "Dokumen (dari TOR bagian 8)", "Acuan normatif",
     [44, 20, 34, 28, 14, 12], "llllcc"),
]


def main():
    lama = openpyxl.load_workbook(BERKAS, data_only=True)
    isi = {nama: baca_tabel(lama[nama], kp) for nama, kp, *_ in LEMBAR}

    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    for no, (nama, _kp, judul, lebar, rata) in enumerate(LEMBAR, start=1):
        kepala, data = isi[nama]
        ws = wb.create_sheet(nama)
        lb = Lembar(ws, no, judul, lebar[:len(kepala)])
        lb.catatan(CATATAN)
        lb.kosong()
        lb.tabel(kepala, data, rata=list(rata)[:len(kepala)], fill=AI, beku_kolom=2 if nama == "Matriks Tanggapan" else 0)
    wb.save(BERKAS)
    print("dirapikan:", BERKAS, {k: len(v[1]) for k, v in isi.items()})


if __name__ == "__main__":
    main()
