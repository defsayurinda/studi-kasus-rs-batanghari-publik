"""Template kop gambar A3 tunggal untuk semua gambar proyek, dibuat di CADCraft.

Gaya mengikuti contoh gambar Defsa (Menggambar Struktur Bangunan 2, 2026): bingkai garis tunggal, kolom kanan
berisi kotak KETERANGAN besar (legenda dan catatan), blok proyek rata tengah, pihak-pihak, JUDUL GAMBAR / SKALA,
dan kisi NO GAMBAR / LEMBAR / TANGGAL / REV. Huruf Times New Roman tebal kapital, hitam-putih.
NIM dan nama orang lain tidak dicantumkan (aturan privasi repo).

Hasil: 'templat/KOP A3.dwg' (seperti WBLOCK; disisipkan sebagai block KOP_A3) beratribut
STATUS, JUDUL, NO_GAMBAR, SKALA, REV, LEMBAR, TANGGAL, DIGAMBAR, DIPERIKSA, DISETUJUI.
Semua gambar menyisipkan block ini; mengubah kop cukup di sini lalu bangun ulang gambar.
Jalankan:  .venv\\Scripts\\python.exe skrip\\cad_kop.py
"""
from pathlib import Path

from cadcraft import Sesi

AKAR = Path(__file__).resolve().parents[1]
TEMPLAT = AKAR / "templat" / "KOP A3.dwg"
NAMA = "KOP_A3"

A3 = (420, 297)
KIRI, KANAN, ATAS, BAWAH = 20, 10, 10, 10
LEBAR_KOLOM = 75
XK = A3[0] - KANAN - LEBAR_KOLOM  # 335, tepi kiri kolom kanan
PROYEK = ["PEMBANGUNAN GEDUNG", "RUMAH SAKIT TEPIAN BATANGHARI", "6 LANTAI + 1 BASEMENT", "KOTA JAMBI"]
PEMBERI = "YAYASAN KESEHATAN TEPIAN BATANGHARI"
PERENCANA = "DEFSA YURINDA"
CATATAN = "SATUAN METER; ELEVASI TERHADAP BM-1 = +10,000 (DATUM LOKAL)"
# baris kolom kanan dari atas ke bawah (tinggi mm); jumlah = 277
BARIS = [(18, "keterangan_judul"), (107, "keterangan"), (44, "proyek"), (16, "pemberi"), (34, "pihak"),
         (14, "status"), (22, "judul"), (10, "nomor"), (12, "tanggal")]
TINGGI_KOLOM = sum(h for h, _ in BARIS)
assert TINGGI_KOLOM == A3[1] - ATAS - BAWAH
TINGGI_ETIKET = TINGGI_KOLOM - 18 - 107  # bagian kop di bawah kotak keterangan (152 mm)
KETERANGAN = (XK, BAWAH + TINGGI_ETIKET, XK + LEBAR_KOLOM, BAWAH + TINGGI_ETIKET + 107)  # x0, y0, x1, y1


def tinggi(pt):
    """Tinggi huruf CAD (tinggi huruf kapital, mm) dari ukuran huruf dalam poin."""
    return round(pt * 25.4 / 72 * 0.716, 2)


def siapkan_gaya(cad):
    cad.cmd("style", {"name": "ARIAL", "font": "arial.ttf"})
    cad.cmd("style", {"name": "ARIAL_TEBAL", "font": "arialbd.ttf"})
    cad.cmd("style", {"name": "TNR", "font": "times.ttf"})
    cad.cmd("style", {"name": "TNR_TEBAL", "font": "timesbd.ttf"})
    cad.cmd("style.current", {"name": "TNR"})


def buat_templat(path=TEMPLAT):
    path.parent.mkdir(parents=True, exist_ok=True)
    with Sesi() as cad:
        cad.baru(metric=True)
        siapkan_gaya(cad)
        cad.cmd("layer.new", {"name": "KOP", "color": 7, "lineweight": 0.35, "current": True})

        def garis(pts, lw=0.35, tutup=False):
            cad.cmd("lweight", {"lineweight": lw})
            return cad.cmd("pline", {"vertices": pts, "closed": tutup})["handle"]

        def kotak(x, y, w, t, lw=0.35):
            return garis([[x, y], [x + w, y], [x + w, y + t], [x, y + t]], lw, True)

        def teks(x, y, s, pt, tebal=True, j="L"):
            cad.cmd("style.current", {"name": "TNR_TEBAL" if tebal else "TNR"})
            cad.cmd("text", {"at": [x, y], "text": s, "height": tinggi(pt), "justify": j})

        def atribut(tag, x, y, pt, bawaan="", j="L"):
            cad.cmd("style.current", {"name": "TNR_TEBAL"})
            cad.cmd("attdef", {"tag": tag, "prompt": tag.replace("_", " ").title(), "default": bawaan,
                               "at": [x, y], "height": tinggi(pt), "justify": j})

        kotak(0, 0, A3[0], A3[1], 0.09)  # batas potong kertas
        kotak(KIRI, BAWAH, A3[0] - KIRI - KANAN, A3[1] - ATAS - BAWAH, 0.6)
        garis([[XK, BAWAH], [XK, A3[1] - ATAS]], 0.6)
        x, w = XK, LEBAR_KOLOM
        yy = A3[1] - ATAS
        for t, nama in BARIS:
            yy -= t
            garis([[x, yy], [x + w, yy]], 0.35)
            if nama == "keterangan_judul":
                teks(x + w / 2, yy + t / 2, "KETERANGAN", 24, j="MC")
            elif nama == "proyek":
                for i, s in enumerate(PROYEK):
                    teks(x + w / 2, yy + t - 9 - i * 7.5, s, 9.5 if i == 1 else 9.5, j="MC")
            elif nama == "pemberi":
                teks(x + 3, yy + t - 5.5, "PEMBERI TUGAS :", 9)
                teks(x + 3, yy + 4, PEMBERI, 7.6)
            elif nama == "pihak":
                teks(x + 3, yy + t - 5.5, "PERENCANA :", 9)
                teks(x + 3, yy + t - 11, PERENCANA, 9.5)
                for i, (lab, tag, bw) in enumerate((("DIGAMBAR", "DIGAMBAR", "D. YURINDA"),
                                                    ("DIPERIKSA", "DIPERIKSA", "D. YURINDA"),
                                                    ("DISETUJUI", "DISETUJUI", "-"))):
                    yb = yy + t - 18 - i * 5.5
                    teks(x + 3, yb, lab, 8)
                    teks(x + 24, yb, ":", 8)
                    atribut(tag, x + 27, yb, 8, bw)
            elif nama == "status":
                teks(x + 3, yy + t - 5, "STATUS :", 8)
                atribut("STATUS", x + 18, yy + t - 5, 8, "DRAF")
                teks(x + 3, yy + 2.8, "DATA SIMULASI - TIDAK UNTUK KONSTRUKSI", 7.5)
            elif nama == "judul":
                teks(x + 3, yy + t - 6, "JUDUL GAMBAR", 9)
                teks(x + 31.5, yy + t - 6, ":", 9)
                atribut("JUDUL", x + 34, yy + t - 6, 8.5, "JUDUL")
                teks(x + 3, yy + 5, "SKALA", 9)
                teks(x + 31.5, yy + 5, ":", 9)
                atribut("SKALA", x + 34, yy + 5, 8.5, "-")
            elif nama == "nomor":
                garis([[x + w / 2, yy], [x + w / 2, yy + t]], 0.35)
                teks(x + 3, yy + t / 2 - 1, "NO GAMBAR :", 7.5)
                atribut("NO_GAMBAR", x + 22.5, yy + t / 2 - 1, 8, "-")
                teks(x + w / 2 + 3, yy + t / 2 - 1, "LEMBAR :", 7.5)
                atribut("LEMBAR", x + w / 2 + 18, yy + t / 2 - 1, 8, "-")
            elif nama == "tanggal":
                garis([[x + w / 2, yy], [x + w / 2, yy + t]], 0.35)
                teks(x + 3, yy + t - 4.5, "TANGGAL :", 7)
                atribut("TANGGAL", x + 3, yy + 2.5, 8, "-")
                teks(x + w / 2 + 3, yy + t - 4.5, "REV :", 7)
                atribut("REV", x + w / 2 + 3, yy + 2.5, 8, "A")
        teks(KIRI + 1.5, BAWAH - 4, CATATAN, 6.5, tebal=False)
        cad.cmd("style.current", {"name": "TNR"})
        cad.simpan(path)  # seperti WBLOCK: model space = isi block KOP_A3, titik sisip (0, 0)
    path.with_suffix(".bak").unlink(missing_ok=True)
    with Sesi() as cad:  # contoh kop terisi untuk diperiksa
        cad.baru(metric=True)
        siapkan_gaya(cad)
        cad.cmd("insert", {"name": NAMA, "file": str(path), "at": [0, 0],
                           "attribs": {"STATUS": "CONTOH", "JUDUL": "CONTOH JUDUL", "NO_GAMBAR": "XX-00",
                                       "SKALA": "1:100", "REV": "A", "LEMBAR": "1 / 1", "TANGGAL": "APRIL 2027"}})
        cad.cmd("plot", {"path": str(path.with_name("KOP A3 contoh.pdf")), "layout": "Model",
                         "device": "CADCraft PDF", "paper": "ISO A3 (297.00 x 420.00 MM)", "landscape": True,
                         "scale": "1:1", "plotArea": "window", "window": [[0, 0], list(A3)], "lineweights": True})
    return path


if __name__ == "__main__":
    print(buat_templat())
