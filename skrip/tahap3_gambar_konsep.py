"""Langkah 3.11: gambar konsep dari model BIMCraft (denah LT1 dan potongan A-A) di lembar CADCraft ber-kop KOP_A3.

Alur: model BIMCraft (massa arsitektur 3.4 dan struktur LOD 200 3.9) → tampak denah/potongan diekspor BIMCraft ke DXF
(`03 Desain Konsep/Gambar/BIM/`) → diimpor ke model space CADCraft (1 unit = 1 mm, koordinat proyek) → lapisan teks
BIMCraft (teks sudah menjadi garis) dihapus dan diganti teks, as grid, garis ukur asosiatif, dan titik tinggi asli
CADCraft (skrip/cad_lembar.py) supaya dapat diedit seperti gambar drafter. Disusun AI atas permintaan Defsa
(19 Nov 2026); disetujui Defsa 19 Nov 2026.
"""
from pathlib import Path

import tahap3_bim as bm
import tahap3_peil as pl
import tahap3_pondasi as fd
import tahap3_program as pr
import tahap3_struktur as st
import tahap3_zonasi as zn

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "03 Desain Konsep"
BIM = KELUAR / "Gambar" / "BIM"
DXF_DENAH = BIM / "RSTB-ARS-T3 Denah LT1.dxf"
DXF_POTONGAN = BIM / "RSTB-STR-T3 Potongan A-A.dxf"
PDF_DENAH = KELUAR / "3.11 Gambar Denah Konsep LT1.pdf"
PDF_POTONGAN = KELUAR / "3.11 Gambar Potongan Konsep A-A.pdf"
Y_POTONGAN = 43.0  # m, as D (kolom terpotong)
SKALA = 500


def ekspor_bim():
    """Ekspor tampak dari BIMCraft: denah LT1 model massa, potongan A-A model struktur (view disimpan di model)."""
    from bimcraft import Sesi

    BIM.mkdir(parents=True, exist_ok=True)
    with Sesi(zn.BIMC) as b:
        b.cmd("export", {"format": "dxf", "view": "LT1", "path": str(DXF_DENAH), "overwrite": True})
    with Sesi(bm.BIMC) as b:
        b.cmd("section", {"start": [0, round(Y_POTONGAN * 1000)], "end": [140000, round(Y_POTONGAN * 1000)],
                          "depth": 10000, "name": "POTONGAN A-A"})
        b.cmd("export", {"format": "dxf", "view": "POTONGAN A-A", "path": str(DXF_POTONGAN), "overwrite": True})
        b.simpan(bm.BIMC)
    return DXF_DENAH, DXF_POTONGAN


def _impor(g, path, hapus):
    """Impor DXF BIMCraft ke model space dan hapus lapisan yang berisi teks-garis atau anotasi BIMCraft."""
    r = g.cmd("import", {"path": str(path), "at": [0, 0]})
    ada = {l_["name"] for l_ in g.cmd("layer", {})["layers"] if l_["used"]}
    buang = [n for n in hapus if n in ada]
    if buang:
        g.cmd("laydel", {"names": buang})
    return r["imported"], sorted(ada - set(buang))


def gambar_denah(status=None):
    from cad_lembar import STATUS_SETUJU, Gambar

    pd = pr.MASSA["PODIUM"]
    gx, gy = fd.GU_GRID_X, fd.GU_GRID_Y
    dwg = KELUAR / "Gambar" / "DWG" / "GK-09 Denah Konsep LT1.dwg"
    png = KELUAR / "Gambar" / "GK-09 Denah Konsep LT1.png"
    with Gambar(SKALA) as g:
        n, sisa = _impor(g, DXF_DENAH, ["room", "tag", "section", "grid"])
        g.legenda_tambah("garis", "Dinding inti dan batas massa (model BIMCraft)", tebal=0.5)
        g.legenda_tambah("garis", "Pemisah zona (model BIMCraft)")
        # as grid: hanya potongan di luar bangunan (label zona di dalam tidak tertimpa garis)
        for i, x in enumerate(st.GRID_X):
            g.as_grid(str(i + 1), (x, pd["y"][1] + 5.5), (x, pd["y"][1] + 7), r_kertas=3.0, dua_ujung=False)
            g.as_grid(str(i + 1), (x, pd["y"][0]), (x, pd["y"][0] - 7), r_kertas=3.0, dua_ujung=False)
        for j, y in enumerate(st.GRID_Y):
            g.as_grid(st.NAMA_Y[j], (pd["x"][0], y), (pd["x"][0] - 7, y), r_kertas=3.0, dua_ujung=False)
        for i, x in enumerate(gx):
            g.as_grid(f"U{i + 1}", (x, gy[-1]), (x, gy[-1] + 7), r_kertas=3.0, dua_ujung=False)
        # label zona LT1 (nama + luas) menghindari inti tangga dan lif, teks asli CADCraft
        inti = [(cx - 2.6, cy - 3.6, cx + 2.6, cy + 3.6) for cx, cy in zn.TANGGA] +             [(zn.LIF[0] - .8, zn.LIF[2] - .8, zn.LIF[1] + .8, zn.LIF[3] + .8)]
        for nama, x0, x1, y0, y1, _ in zn.ZONA["LT1"] + zn.KOSONG.get("LT1", []):
            cx, cy, baris, _ = zn.tempat_label(nama, x0, x1, y0, y1, (x1 - x0) * (y1 - y0), inti)
            zn._tulis_label(g, cx, cy, baris)
        g.teks(((gx[0] + gx[-1]) / 2, 64), "GEDUNG UTILITAS + PARKIR", "C-ZONA-TEKS", 1.8, j="MC", tebal=True)
        g.teks(((gx[0] + gx[-1]) / 2, 61), "LT1: GENSET, TRAFO, POMPA, IPSRS", "C-ZONA-TEKS", 1.6, j="MC")
        # titik tinggi dan ramp beratap (keputusan rapat konsep 3.10)
        pe = pl.peil_usulan()
        g.titik_tinggi((14, 72), f"+{pe['lantai']:.2f} LANTAI".replace(".", ","), "A-ELEVASI")
        g.titik_tinggi((106, 47.5), f"+{pe['lantai']:.2f}".replace(".", ","), "A-ELEVASI")
        g.titik_tinggi((-3, 21), f"+{pe['halaman']:.2f} HALAMAN".replace(".", ","), "A-ELEVASI")
        g.layer("A-RAMP", 7, 0.35, "DASHED")
        g.pline([(40, 75), (40, 80), (56, 80), (56, 75)], "A-RAMP")
        g.pline([(84, 31), (90, 31), (90, 47), (84, 47)], "A-RAMP")
        g.legenda_tambah("garis", "Ramp beratap (rapat konsep 3.10)", garis="DASHED")
        g.teks((48, 77.5), "RAMP BERATAP", "A-RAMP-TEKS", 1.6, j="MC")
        g.tunjuk((89, 39), (94, 22), "RAMP BERATAP IGD", layer="A-RAMP-TEKS")
        # ukuran utama (asosiatif)
        yu = pd["y"][1] + 14
        g.ukur((pd["x"][0], yu), (pd["x"][1], yu), (sum(pd["x"]) / 2, yu + 3))
        for a, b in zip(st.GRID_X[:-1], st.GRID_X[1:]):
            g.ukur((a, yu - 1), (b, yu - 1), ((a + b) / 2, yu - 1))
        xu = pd["x"][0] - 13
        g.ukur((xu, pd["y"][0]), (xu, pd["y"][1]), (xu - 3, sum(pd["y"]) / 2))
        g.ukur((gx[0], gy[0] - 9), (gx[-1], gy[0] - 9), ((gx[0] + gx[-1]) / 2, gy[0] - 12))
        g.lembar("GK-09", "Denah konsep LT1", f"1:{SKALA}", pusat=(70, 52),
                 subjudul="Langkah 3.11: geometri dari model BIMCraft (RSTB-ARS-T3-Massa, tampak LT1); anotasi CADCraft",
                 status=status or STATUS_SETUJU,
                 catatan=[
                     "Zona dan luas: program ruang dan zonasi 3.4; luas = luas zona kotor.",
                     f"Peil lantai +{pe['lantai']:.2f}, halaman +{pe['halaman']:.2f} (3.3); beda tinggi ".replace(".", ",")
                     + "ditempuh ramp beratap; kemiringan dicek ke aturan aksesibilitas.",
                     "Inti tangga dan lif: dinding geser sistem ganda (3.6).",
                     "Tidak untuk konstruksi; denah rinci di Tahap 7.",
                 ])
        g.skala_grafis(205, 22, 50)
        g.panah_utara(318, 262, 10)
        g.simpan(dwg, PDF_DENAH, png)
    return dwg, n, sisa


def gambar_potongan(status=None):
    from cad_lembar import STATUS_SETUJU, Gambar

    pe = pl.peil_usulan()
    x0, x1 = 2.0, 138.0
    dwg = KELUAR / "Gambar" / "DWG" / "GK-10 Potongan Konsep A-A.dwg"
    png = KELUAR / "Gambar" / "GK-10 Potongan Konsep A-A.png"
    with Gambar(SKALA) as g:
        n, sisa = _impor(g, DXF_POTONGAN, ["grid", "level", "section", "tag"])
        g.legenda_tambah("garis", "Struktur terpotong dan terlihat (model BIMCraft LOD 200)", tebal=0.5)
        # grid
        for i, x in enumerate(st.GRID_X):
            g.as_grid(str(i + 1), (x, 41.5), (x, 45.5), r_kertas=3.0, dua_ujung=False)
        # level lantai
        g.layer("A-LEVEL", 8, 0.13, "DASHED")
        for nama, el in [(k, v / 1000) for k, v in bm.st.tpl.LEVEL if k != "B1"]:
            g.pline([(86, el), (x1 - 8, el)], "A-LEVEL")
            g.titik_tinggi((x1 - 6, el), f"{nama} +{el:.2f}".replace(".", ","), "A-ELEVASI")
        # muka tanah, halaman, banjir
        g.layer("C-TANAH", 7, 0.5)
        g.pline([(x0, fd.ELEV_TANAH), (x1, fd.ELEV_TANAH)], "C-TANAH")
        g.layer("C-HALAMAN", 7, 0.35)
        g.pline([(86, pe["halaman"]), (98, pe["halaman"])], "C-HALAMAN")
        g.layer("C-BANJIR", 7, 0.25, "HIDDEN")
        g.pline([(x0, pe["q50"]), (9.5, pe["q50"])], "C-BANJIR")
        g.pline([(x0, pe["q100"]), (9.5, pe["q100"])], "C-BANJIR")
        g.teks((x0, pe["q100"] + 0.6), f"Q100 +{pe['q100']:.2f}".replace(".", ","), "C-BANJIR", 1.6)
        g.teks((x0, pe["q50"] - 1.6), f"Q50 +{pe['q50']:.2f}".replace(".", ","), "C-BANJIR", 1.6)
        g.teks((100, fd.ELEV_TANAH + 0.3), f"MUKA TANAH ASLI ±+{fd.ELEV_TANAH:.2f}".replace(".", ","), "C-TANAH", 1.6)
        g.teks((86.5, pe["halaman"] - 1.6), f"HALAMAN +{pe['halaman']:.2f}".replace(".", ","), "C-HALAMAN", 1.6)
        # lapisan tanah desain (3.7)
        g.layer("G-LAPISAN", 8, 0.13, "DASHED")
        atas = fd.ELEV_TANAH
        for unit, bawah, _, jenis, _, _ in fd.LAPISAN:
            el = fd.ELEV_TANAH - bawah
            if el > -32:
                g.pline([(x0, el), (x1, el)], "G-LAPISAN")
            mid = (atas + max(el, -32)) / 2
            if atas - max(el, -32) > 3:
                g.teks((x1 - 1, mid), f"{unit} {jenis.upper()}", "G-LAPISAN", 1.6, j="MR")
            atas = el
        ujung = bm.DASAR_CAP / 1000 - bm.PANJANG_TIANG / 1000
        g.tunjuk((13.2, ujung + 1), (28, ujung - 3), f"UJUNG TIANG ±{ujung:.2f}".replace(".", ","), layer="S-TEKS")
        g.tunjuk((13.2, 4.0), (30, 3.2), "TIANG BOR Ø800 KE U7 (3.7)", layer="S-TEKS")
        g.lembar("GK-10", "Potongan konsep A-A", f"1:{SKALA}", pusat=(70, 5.0),
                 subjudul="Langkah 3.11: potongan pada as D dari model BIMCraft (RSTB-STR-T3-LOD200); anotasi CADCraft",
                 status=status or STATUS_SETUJU,
                 catatan=[
                     "Potongan menghadap utara pada as D; kolom, balok, pelat, pile cap, tiang dari model 3.9.",
                     "Banjir Q50/Q100: langkah 3.3; lapisan tanah desain: langkah 3.7 (BH-1, BH-5).",
                     "Menara LT4-LT6 di x 20-84; gedung utilitas + parkir di x 100-134 (di belakang bidang potong).",
                 ])
        g.skala_grafis(205, 22, 50)
        g.simpan(dwg, PDF_POTONGAN, png)
    return dwg, n, sisa


def buat():
    ekspor_bim()
    return gambar_denah(), gambar_potongan()


if __name__ == "__main__":
    print(buat())
