"""Langkah 7.5: DED struktur. GS-33 (LB-1 + pelat turun), GS-34 (rel chiller), GS-35 (catatan umum) di CADCraft (KOP_A3),
dan satu set PDF GS-01..GS-35 dari PDF tahap 4, 5, 6 yang sudah ada. Data: 7.3 (lb1(), rel_baru()). DATA SIMULASI.
Jalankan (satu lembar per proses, timeout di pemanggil):
  .venv\\Scripts\\python.exe skrip\\tahap7_gambar_str.py GS-33 | GS-34 | GS-35 | --pdf | --cek
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_gambar_ded as t4g  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "07 DED dan RKS"
DWG = KELUAR / "Gambar" / "DWG"
PLOT = KELUAR / "Gambar" / "_plot_str"
PNG = KELUAR / "Gambar"
PDF = KELUAR / "7.5 Gambar Struktur DED.pdf"
STATUS = "DISETUJUI 22 NOV 2026"
TANGGAL = "NOVEMBER 2026"
H = 1.6
NAMA = {"GS-33": "GS-33 LB-1 dan Pelat Turun", "GS-34": "GS-34 Rel Chiller", "GS-35": "GS-35 Catatan Umum Struktur"}

# PDF sumber (berkas, halaman pertama, jumlah halaman, nomor lembar pertama); urut GS
SUMBER = [("04 Struktur Atas/4.1 Gambar Respons Spesifik Situs.pdf", 1, "GS-01"),
          ("04 Struktur Atas/4.2 Gambar Zona Beban.pdf", 1, "GS-02"),
          ("04 Struktur Atas/4.10 Gambar Struktur Atas DED.pdf", 18, "GS-03"),
          ("05 Struktur Tengah/5.0 Gambar Plot Data Owner.pdf", 1, "GS-21"),
          ("05 Struktur Tengah/5.8 Gambar Struktur Tengah.pdf", 5, "GS-22"),
          ("06 Struktur Bawah dan Basement/6.0 Gambar Telaah Data.pdf", 1, "GS-27"),
          ("06 Struktur Bawah dan Basement/Gambar/GS-28..32 dan GT-16 Pondasi.pdf", 5, "GS-28")]


def idn(v, d=2):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def simpan(g, no):
    PLOT.mkdir(parents=True, exist_ok=True)
    dwg = DWG / f"{NAMA[no]}.dwg"
    g.simpan(dwg, PLOT / f"{dwg.stem}.pdf", PNG / f"{dwg.stem}.png")
    return dwg


def lingkar(g, cx, cz, db):
    g.cmd("circle", {"center": g.mm((cx, cz)), "radius": db / 2})


def penampang_balok(g, cx, b, h, atas, bawah, ds, tutup=0.040):
    """Penampang balok b x h (m) di (cx, 0..h), sengkang + tulangan (n, db mm); n > 4 dibagi dua lapis."""
    g.pline([(cx - b / 2, 0), (cx + b / 2, 0), (cx + b / 2, h), (cx - b / 2, h)], "S-BALOK", tutup=True)
    s = tutup
    g.pline([(cx - b / 2 + s, s), (cx + b / 2 - s, s), (cx + b / 2 - s, h - s), (cx - b / 2 + s, h - s)], "S-TUL", tutup=True)
    for (n, db), arah in ((atas, -1), (bawah, 1)):
        z0 = h - s - ds / 1000 - db / 2000 if arah < 0 else s + ds / 1000 + db / 2000
        baris = [n] if n <= 4 else [4, n - 4]
        for k, m in enumerate(baris):
            z = z0 + arah * k * (db / 1000 + 0.025)
            x0 = cx - b / 2 + s + ds / 1000 + db / 2000
            x1 = cx + b / 2 - s - ds / 1000 - db / 2000
            for i in range(m):
                lingkar(g, x0 + (x1 - x0) * (i / (m - 1) if m > 1 else 0.5), z, db)


def kertas_label(g, vp, pusat, skala, titik, s, dy=0.0, j="MC", h=2.2):
    """Teks di kertas pada titik model (x, z) dalam viewport vp=((x1,y1),(x2,y2)) berskala 1:skala."""
    (x1, y1), (x2, y2) = vp
    px = (x1 + x2) / 2 + (titik[0] - pusat[0]) * 1000 / skala
    py = (y1 + y2) / 2 + (titik[1] - pusat[1]) * 1000 / skala + dy
    g.kertas_teks((px, py), s, h, j)


def atasbawah(d):
    return (d["atas"]["n"], d["atas"]["db"]), (d["bawah"]["n"], d["bawah"]["db"])


# ------------------------------------------------------------------ GS-33
def gs33():
    from cad_lembar import Gambar
    import tahap7_cek_struktur as cs
    lb = cs.lb1()["balok"]
    SK = 100
    with Gambar(SK) as g:
        for ly, w, gy in (("S-BALOK", 0.35, "Continuous"), ("S-INDUK", 0.35, "DASHDOT"), ("S-PELAT", 0.25, "DASHED"),
                          ("S-TUL", 0.25, "Continuous"), ("S-POTONG", 0.5, "DASHDOT"), ("S-TEKS", 0.18, "Continuous"),
                          ("S-BETON", 0.35, "Continuous")):
            g.layer(ly, 7, w, gy)
        rect = lambda x0, y0, x1, y1, ly: g.pline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], ly, tutup=True)  # noqa: E731
        # --- denah (x, y model = koordinat gedung)
        rect(69.825, 51.0, 70.175, 59.0, "S-BALOK")
        rect(70.175, 51.85, 76.0, 52.15, "S-BALOK")
        rect(70.175, 55.85, 76.0, 56.15, "S-BALOK")
        rect(75.85, 51.0, 76.15, 59.0, "S-INDUK")
        rect(70.0, 52.0, 76.0, 56.0, "S-PELAT")
        g.teks((73.0, 54.7), "PELAT TURUN -300 (CSSD LT2)", "S-TEKS", H, j="MC", tebal=True)
        g.teks((73.0, 54.3), "t 200 TETAP; ISIAN SCREED 250", "S-TEKS", H, j="MC")
        g.teks((73.0, 50.5), f"LB-1 y 52: 300 × 600, {lb['y 52']['atas']['n']}D{lb['y 52']['atas']['db']} / {lb['y 52']['bawah']['n']}D{lb['y 52']['bawah']['db']}",
               "S-TEKS", H, j="MC")
        g.teks((73.0, 57.0), f"LB-1 y 56: 300 × 600, {lb['y 56']['atas']['n']}D{lb['y 56']['atas']['db']} / {lb['y 56']['bawah']['n']}D{lb['y 56']['bawah']['db']}",
               "S-TEKS", H, j="MC")
        g.teks((69.25, 57.0), f"LB-1 x 70: 350 × 600, {lb['x 70']['atas']['n']}D{lb['x 70']['atas']['db']} / {lb['x 70']['bawah']['n']}D{lb['x 70']['bawah']['db']}",
               "S-TEKS", H, j="MC", rot=90)
        g.teks((76.75, 57.0), "BALOK INDUK x 76 (EKSISTING)", "S-TEKS", H, j="MC", rot=90)
        g.ukur((70, 59.0), (76, 59.0), (73, 59.9))
        for a, b in ((51, 52), (52, 56), (56, 59)):
            g.ukur((69.825, a), (69.825, b), (67.9, (a + b) / 2), rot=90)
        g.ukur((69.825, 51), (69.825, 59), (66.8, 55.0), rot=90)
        g.pline([(67.6, 53.0), (77.9, 53.0)], "S-POTONG")
        g.teks((67.45, 52.9), "A", "S-TEKS", H, j="R", tebal=True)
        g.teks((78.05, 52.9), "A", "S-TEKS", H, j="L", tebal=True)
        # --- potongan A-A (x, z)
        from shapely.geometry import box
        from shapely.ops import unary_union
        u = unary_union([box(69, -0.2, 70, 0), box(69.825, -0.75, 70.175, -0.15), box(70, -0.75, 76, -0.55),
                         box(75.825, -0.75, 76.175, -0.15), box(76, -0.2, 77, 0)])
        g.arsir(list(u.exterior.coords)[:-1], "S-BETON", "ANSI31", 0.5)
        g.arsir([(70.175, -0.55), (75.825, -0.55), (75.825, -0.30), (70.175, -0.30)], "S-BETON", "ANSI37", 0.5)
        g.ukur((70, -1.0), (76, -1.0), (73, -1.5))
        g.tunjuk((69.9, -0.5), (68.0, -1.3), "LB-1 x 70", "S-TEKS")
        g.tunjuk((76.0, -0.5), (76.8, -1.3), "BALOK INDUK x 76 [ASUMSI]", "S-TEKS")
        g.tunjuk((73.0, -0.65), (71.5, -2.0), "PELAT TURUN t 200", "S-TEKS")
        g.tunjuk((73.0, -0.42), (74.2, 0.55), "ISIAN SCREED 250 [ASUMSI]", "S-TEKS")
        g.tunjuk((69.4, -0.1), (68.0, 0.55), "PELAT LT2 t 200", "S-TEKS")
        g.titik_tinggi((77.5, 0.0), "±0,00 (LT2)", "S-TEKS", teks_at=(77.7, 0.1))
        g.titik_tinggi((77.5, -0.30), "-0,30 (PELAT TURUN)", "S-TEKS", teks_at=(77.7, -0.6))
        # --- penampang 1:20 (x 100..104)
        for cx, k, b in ((100.0, "x 70", 0.35), (102.0, "y 52", 0.30), (104.0, "y 56", 0.30)):
            penampang_balok(g, cx, b, 0.60, (lb[k]["atas"]["n"], lb[k]["atas"]["db"]), (lb[k]["bawah"]["n"], lb[k]["bawah"]["db"]), lb[k]["ds"])
        g.legenda_tambah("garis", "Balok LB-1 (tepi pelat turun)", tebal=0.35)
        g.legenda_tambah("garis", "Balok induk x 76 (eksisting), titik-garis", garis="DASHDOT", tebal=0.35)
        g.legenda_tambah("garis", "Tepi pelat turun x 70-76, y 52-56 (putus)", garis="DASHED", tebal=0.25)
        g.legenda_tambah("garis", "Garis potong A-A", garis="DASHDOT", tebal=0.5)
        catatan = [
            "LB-1 (7.3, K7.3-5): balok tepi tiga sisi pelat turun -300 (x 70; y 52; y 56); sisi x 76 balok induk. Pelat tetap 200 mm; isian screed 250 mm [Asumsi].",
            "Beban 7.3: pelat 200 + SIDL 7,49 kPa; di pelat turun + isian 12,49 kPa; Lo 2,87 kPa. Desain SNI 2847:2019 Pasal 9 (pola 4.6); semua lolos.",
            "f'c 30 MPa, BjTS 420B, selimut 40 mm. Tulangan atas/bawah dari tabel 7.3: x 70 2D22/8D25 (dua lapis bawah), y 52 2D22/2D29, y 56 2D22/4D22.",
            "Letak vertikal balok (bawah = bawah pelat turun) dan balok induk x 76 350 × 600: [Asumsi gambar], bukan hasil hitungan."]
        g.lembar("GS-33", "Denah dan penampang balok LB-1, pelat turun", f"1:{SK}; PENAMPANG 1:20", pusat=None, status=STATUS, tanggal=TANGGAL,
                 subjudul="Langkah 7.5: dari 7.3 (balok LB-1, K7.3-5)", catatan=catatan, judul_kop="LB-1 DAN PELAT TURUN LT2")
        g.viewport_tambahan((26, 160), (160, 283), (73.0, 55.0), SK, "Denah pelat turun dan balok LB-1", f"SKALA 1:{SK}")
        vp = ((164, 160), (331, 283))
        g.viewport_tambahan(vp[0], vp[1], (73.8, -0.4), SK, "Potongan A-A", f"SKALA 1:{SK}")
        vd = ((26, 70), (331, 146))
        g.viewport_tambahan(vd[0], vd[1], (102.0, 0.3), 20, "Penampang balok LB-1 (x 70 | y 52 | y 56)", "SKALA 1:20")
        for cx, k in ((100.0, "x 70"), (102.0, "y 52"), (104.0, "y 56")):
            b = 350 if k == "x 70" else 300
            a, w = lb[k]["atas"], lb[k]["bawah"]
            kertas_label(g, vd, (102.0, 0.3), 20, (cx, 0.0), f"LB-1 {k}: {b} × 600", dy=-6, h=2.6)
            kertas_label(g, vd, (102.0, 0.3), 20, (cx, 0.0), f"ATAS {a['n']}D{a['db']}; BAWAH {w['n']}D{w['db']}", dy=-10.5, h=2.2)
            kertas_label(g, vd, (102.0, 0.3), 20, (cx, 0.0), f"SENGKANG D{lb[k]['ds']} (JARAK: 7.3)", dy=-14.5, h=2.2)
        g.skala_grafis(205, 22, 5, bagi=5)
        return simpan(g, "GS-33")


# ------------------------------------------------------------------ GS-34
REL_X = [69.0, 70.1, 72.5, 73.6, 77.1, 79.5, 80.6]
UNIT_X0 = [68.4, 71.9, 75.4, 78.9]


def gs34():
    from cad_lembar import Gambar
    import tahap7_cek_struktur as cs
    r = cs.rel_baru()
    SK = 150
    with Gambar(SK) as g:
        for ly, w, gy in (("S-REL", 0.35, "Continuous"), ("S-INDUK", 0.35, "DASHDOT"), ("M-CHILLER", 0.25, "DASHED"),
                          ("S-TUL", 0.25, "Continuous"), ("S-TEKS", 0.18, "Continuous"), ("S-BALOK", 0.35, "Continuous")):
            g.layer(ly, 7, w, gy)
        rect = lambda x0, y0, x1, y1, ly: g.pline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], ly, tutup=True)  # noqa: E731
        for x in REL_X:
            rect(x - 0.15, 59.0, x + 0.15, 75.0, "S-REL")
        rect(75.85, 59.0, 76.15, 75.0, "S-INDUK")
        for y in (59.0, 67.0, 75.0):
            g.pline([(67.0, y), (83.0, y)], "S-INDUK")
        for k, x0 in enumerate(UNIT_X0):
            rect(x0, 63.5, x0 + 2.4, 74.5, "M-CHILLER")
            g.teks((x0 + 1.2, 75.6), f"M-01.{k + 1}", "S-TEKS", H, j="MC")
        rect(60.0, 62.0, 68.0, 66.0, "M-CHILLER")
        g.teks((64.0, 64.0), "POMPA M-04 [ASUMSI]", "S-TEKS", H, j="MC")
        g.teks((75.0, 76.5), "UNIT CHILLER M-01 (4 UNIT, 11,0 × 2,4 m) DI ATAS PEGAS δ 25 mm", "S-TEKS", H, j="MC", tebal=True)
        g.teks((83.2, 59.3), "INDUK y 59", "S-TEKS", H, j="L")
        g.teks((83.2, 67.3), "INDUK y 67", "S-TEKS", H, j="L")
        g.teks((83.2, 75.3), "INDUK y 75", "S-TEKS", H, j="L")
        xs = sorted(REL_X + [76.0])
        for a, b in zip(xs, xs[1:]):
            g.ukur((a, 59.0), (b, 59.0), ((a + b) / 2, 57.6))
        g.ukur((69.0, 59.0), (80.6, 59.0), (74.8, 56.4))
        g.teks((72.6, 55.8), "REL: 7 BUAH ARAH y, 300 × 500; SATU REL BERIMPIT BALOK INDUK x 76", "S-TEKS", H, j="MC")
        g.teks((72.6, 79.0), "DENAH ATAP PODIUM: REL CHILLER M-01 (LT2-ATAP)", "S-TEKS", 2.2, j="MC", tebal=True)
        # --- penampang rel 1:20
        cx = 200.0
        a, w = r["atas"], r["bawah"]
        penampang_balok(g, cx, 0.30, 0.50, (a["n"], a["db"]), (w["n"], w["db"]), r["ds"])
        g.legenda_tambah("garis", "Rel chiller baru 300 × 500 (arah y)", tebal=0.35)
        g.legenda_tambah("garis", "Balok induk atap, titik-garis", garis="DASHDOT", tebal=0.35)
        g.legenda_tambah("garis", "Unit chiller M-01 dan pompa M-04 (putus)", garis="DASHED", tebal=0.25)
        catatan = [
            "Rel baru arah y bentang 2 × 8 m (y 59-67-75), 300 × 500, pola 4.6 balok_chiller (7.3): Mu- 182 kNm, Mu+ 117 kNm, Vu 129 kN; lolos.",
            f"Tulangan rel: atas {a['n']}D{a['db']}, bawah {w['n']}D{w['db']}, sengkang D{r['ds']} {r['kaki']} kaki, jarak sendi {int(r['s_sendi'] * 1000)} mm; f'c 30 MPa, BjTS 420B, selimut 40 mm.",
            "Chiller dipindah ke y ≥ 63 (frekuensi lantai atap 4,2-5,6 Hz < 20,3 Hz: cabang pegas-saja tidak berlaku); unit diputar 11 m arah y; pegas δ 25 mm (RKS 7.7).",
            "Rel lama 8 × x 60-76 dihapus dari model STR. Pompa M-04 x 60-68, y 62-66 [Asumsi]. Panjang balok induk di gambar skematik."]
        g.lembar("GS-34", "Rel dan dudukan chiller M-01 di pelat atap", f"1:{SK}; PENAMPANG 1:20", pusat=None, status=STATUS, tanggal=TANGGAL,
                 subjudul="Langkah 7.5: dari 7.3 (K7.3-2)", catatan=catatan, judul_kop="REL CHILLER ATAP")
        g.viewport_tambahan((26, 40), (205, 283), (72.6, 67.5), SK, None, None)
        vd = ((209, 150), (331, 283))
        g.viewport_tambahan(vd[0], vd[1], (cx, 0.25), 20, "Penampang rel 300 × 500", "SKALA 1:20")
        kertas_label(g, vd, (cx, 0.25), 20, (cx, 0.0), "REL 300 × 500", dy=-6, h=2.6)
        kertas_label(g, vd, (cx, 0.25), 20, (cx, 0.0), f"ATAS {a['n']}D{a['db']}; BAWAH {w['n']}D{w['db']}", dy=-10.5, h=2.2)
        kertas_label(g, vd, (cx, 0.25), 20, (cx, 0.0), f"SENGKANG D{r['ds']}-{int(r['s_sendi'] * 1000)}", dy=-14.5, h=2.2)
        g.skala_grafis(205, 22, 5, bagi=5)
        return simpan(g, "GS-34")


# ------------------------------------------------------------------ GS-35
def gs35():
    from cad_lembar import Gambar
    SK = 100
    with Gambar(SK) as g:
        g.layer("S-TEKS", 7, 0.18)
        g.teks((1.0, 23.8), "TABEL 1: MUTU BAHAN DAN SELIMUT PER UNSUR", "S-TEKS", 2.0, j="L", tebal=True)
        mutu = [["Tiang bor Ø800", "35", "420", "75 (ke spiral)", "6.7, 6.9"],
                ["Pile cap (E, A, PC, PU)", "35", "420", "75", "6.7"],
                ["Sloof, pelat LT1, pit", "35", "420", "50 (bawah)", "5.3 (B-5)"],
                ["Zona MRI pelat panel 9-10/D-E", "35", "A955M", "50 (bawah)", "5.2 (B-10)"],
                ["Kolom", "35", "420", "40", "4.5-4.8"],
                ["Dinding inti, balok kopel", "35", "420", "20 (dinding)", "4.10"],
                ["Balok, rel chiller, LB-1", "30", "420", "40", "4.6, 7.3"],
                ["Pelat lantai, atap, tangga", "30", "420", "20", "4.5, 4.9"]]
        yb = t4g.tabel(g, 1.0, 23.3, [64, 16, 20, 28, 28], ["UNSUR", "f'c (MPa)", "fy (MPa)", "SELIMUT (mm)", "ACUAN"], mutu)
        g.teks((1.0, yb - 0.8), "TABEL 2: ACUAN DAN SATUAN", "S-TEKS", 2.0, j="L", tebal=True)
        acu = [["Beton struktural", "SNI 2847:2019"], ["Gempa", "SNI 1726:2019"], ["Geoteknik, lereng, pondasi", "SNI 8460:2017"],
               ["Baja tulangan", "BjTS 420B (SNI 2052); A955M di zona MRI"], ["Satuan", "kN, m, kPa, MPa; gambar dalam mm, elevasi dalam m"],
               ["Datum", "BM-1 = +10,000 (datum lokal)"]]
        yb2 = t4g.tabel(g, 1.0, yb - 1.3, [64, 92], ["BESARAN", "KETERANGAN"], acu)
        g.teks((1.0, yb2 - 0.8), "TABEL 3: BETON DAN PAPARAN", "S-TEKS", 2.0, j="L", tebal=True)
        pap = [["Kelas paparan S2", "tiang, cap, sloof, pelat LT1, pit: w/cm ≤ 0,45, f'c ≥ 35 MPa"],
               ["Perlindungan asam", "tiang dan cap (B-5), rincian di RKS 7.7"],
               ["Selimut bawah", "50 mm (pelat LT1, sloof); 75 mm tiang dan cap"],
               ["Struktur atas", "sesuai GS-03 (Tahap 4) dan GS-13/14 (tabel penampang)"]]
        t4g.tabel(g, 1.0, yb2 - 1.3, [64, 92], ["BESARAN", "KETERANGAN"], pap)
        x2 = 17.6
        g.teks((x2, 23.8), "TABEL 4: PERKUATAN TEBING B-2 (SKEMA)", "S-TEKS", 2.0, j="L", tebal=True)
        teb = [["Status", "diputuskan 7.0 (K7-1); dimensi akhir\nBELUM dihitung, gambar rinci BELUM dibuat"],
               ["Pelandaian", "1V:2H [6.4, LA.3]"], ["Berm bronjong", "puncak +6,50, lebar 8 m [6.4]"],
               ["Tiang bor Ø600", "satu baris di batas lahan, as ±0,96 m,\npanjang ±9,6 m (kasus gempa kh 0,171, 6.4)"],
               ["Perbaikan tanah U5", "jalur tebing sampai di belakang baris tiang y 26,3 m"],
               ["Sumber", "6.4 Stabilitas Tebing, GT-16 (berm + pelandaian)"]]
        yt = t4g.tabel(g, x2, 23.3, [30, 94], ["BUTIR", "KETERANGAN"], teb)
        g.teks((x2, yt - 0.8), "CATATAN UMUM", "S-TEKS", 2.0, j="L", tebal=True)
        cat = ["1. Semua dimensi dan tulangan mengikuti gambar yang lebih rinci; bila berbeda, tanyakan perencana.",
               "2. Sengkang dan ikat silang berkait gempa 135 derajat; sambungan lewatan sesuai SNI 2847:2019 Pasal 25.",
               "3. Tulangan zona MRI baja tahan karat ASTM A955M, 2,0 × 2,0 m (5.2).",
               "4. Pelat turun LB-1 dan rel chiller baru: GS-33, GS-34. Cap E + 2 tiang (321 tiang): GS-28, 29, 32.",
               "5. Data studi kasus SIMULASI, tidak untuk konstruksi."]
        for i, s in enumerate(cat):
            g.teks((x2, yt - 1.5 - i * 0.4), s, "S-TEKS", H, j="L")
        catatan = ["Catatan umum struktur rev. Tahap 7: mutu per unsur, selimut, acuan, satuan; perkuatan tebing B-2 hanya skema (belum dihitung).",
                   "Mutu tiang, cap, sloof, pelat LT1 dan pit dari 2.7, 5.3, 6.7 (B-5). Struktur atas dari Tahap 4.",
                   "Data studi kasus simulasi."]
        g.lembar("GS-35", "Catatan umum struktur", "TANPA SKALA", pusat=None, status=STATUS, tanggal=TANGGAL,
                 subjudul="Langkah 7.5: rev. Tahap 7", catatan=catatan, judul_kop="CATATAN UMUM STRUKTUR")
        g.viewport_tambahan((26, 40), (331, 283), (14.5, 12.0), SK, None, None)
        return simpan(g, "GS-35")


LEMBAR = {"GS-33": gs33, "GS-34": gs34, "GS-35": gs35}


# ------------------------------------------------------------------ set PDF
def daftar_halaman():
    """[(nomor GS, berkas, indeks halaman)] untuk GS-01..GS-35 yang ditemukan, dan nomor yang hilang."""
    from pypdf import PdfReader
    out = []
    for f, n, awal in SUMBER:
        p = AKAR / f
        if not p.exists():
            continue
        m = int(awal[3:])
        jml = len(PdfReader(str(p)).pages)
        for i in range(min(n, jml)):
            out.append((f"GS-{m + i:02d}", p, i))
    for no in LEMBAR:
        f = PLOT / f"{NAMA[no]}.pdf"
        f = f if f.exists() else KELUAR / "Gambar" / f"{NAMA[no]}.pdf"
        if f.exists():
            out.append((no, f, 0))
    ada = {x[0] for x in out}
    hilang = [f"GS-{i:02d}" for i in range(1, 36) if f"GS-{i:02d}" not in ada]
    return sorted(out, key=lambda x: x[0]), hilang


def gabung_pdf(keluar=PDF):
    from pypdf import PdfReader, PdfWriter
    hal, hilang = daftar_halaman()
    w = PdfWriter()
    for no, p, i in hal:
        w.add_page(PdfReader(str(p)).pages[i])
        w.add_outline_item(no, len(w.pages) - 1)
    w.write(str(keluar))
    return len(hal), hilang


def cek():
    import cad_cek
    return {no: len(cad_cek.cek(str(DWG / f"{NAMA[no]}.dwg"))) for no in LEMBAR if (DWG / f"{NAMA[no]}.dwg").exists()}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    if "--pdf" in a:
        print(gabung_pdf())
    elif "--cek" in a:
        print(cek())
    else:
        for no in a:
            if no in LEMBAR:
                d = LEMBAR[no]()
                import cad_cek
                print(no, d.name, len(cad_cek.cek(str(d))), "pasangan", flush=True)
