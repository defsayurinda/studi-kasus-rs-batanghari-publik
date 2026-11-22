"""Langkah 3.4 (lanjutan): zonasi per lantai, model massa BIMCraft, dan gambar GK-03 (rencana tapak dan massa) serta
GK-04 (zonasi lantai) di CADCraft.

Zona mengikuti PMK 40/2022 Lampiran hal. 9 butir F (zona merah: gawat darurat/PIE; kuning: pelayanan pasien; hijau:
penunjang dan manajemen; dicabut Permenkes 6/2026, dipakai dengan catatan). Tangga darurat berjarak maks 25 m
(hal. 12 butir G.3.e.3.c). Ukuran zona skematik (desain konsep); denah rinci di Tahap 7.
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 19 Nov 2026.
"""
import os
import subprocess
import tempfile
import json
from pathlib import Path

import tahap3_program as pr
import tahap3_tapak as tp
import tahap3_template_bim as tpl

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "03 Desain Konsep"
PDF_TAPAK = KELUAR / "3.4 Gambar Rencana Tapak dan Massa.pdf"
PDF_ZONA = KELUAR / "3.4 Gambar Zonasi Lantai.pdf"
BIMC = AKAR / "model" / "RSTB-ARS-T3-Massa.bimc"
IFC = BIMC.with_suffix(".ifc")
POLA = {"merah": ("ANSI31", 0.9), "kuning": ("DOTS", 0.7), "hijau": ("ANSI37", 1.4), "inti": ("SOLID", 1.0)}

TANGGA = [(22, 39), (46, 39), (70, 39), (22, 63), (46, 63), (70, 63)]  # pusat tangga darurat (4 × 6 m)
LIF = (50.0, 58.0, 35.0, 43.0)  # inti lif brankar (4 unit, Data MEP T-01)

# (nama, x0, x1, y0, y1, zona)
ZONA = {
    "LT1": [
        ("GAWAT DARURAT", 62, 84, 27, 51, "merah"), ("RADIOLOGI", 62, 84, 51, 63, "kuning"),
        ("FARMASI, REKAM MEDIS", 62, 84, 63, 75, "kuning"), ("LOBI DAN PENDAFTARAN", 36, 62, 63, 75, "kuning"),
        ("POLIKLINIK", 12, 36, 27, 75, "kuning"), ("PENUNJANG, LOKER, JENAZAH", 36, 62, 27, 35, "hijau"),
    ],
    "LT2": [
        ("BEDAH SENTRAL, CSSD", 62, 84, 27, 63, "kuning"), ("ICU, HCU, NICU, ISOLASI", 36, 62, 27, 51, "kuning"),
        ("KEBIDANAN", 12, 36, 27, 43, "kuning"), ("LABORATORIUM, BANK DARAH", 12, 36, 43, 55, "kuning"),
        ("HEMODIALISIS", 12, 36, 55, 75, "kuning"),
        ("REHAB MEDIK, TUNGGU KELUARGA", 62, 84, 63, 75, "kuning"),
    ],
    "LT3": [
        ("ADMINISTRASI, AULA, DIKLAT", 12, 46, 27, 75, "hijau"), ("GIZI DAN LAUNDRY", 62, 84, 51, 75, "hijau"),
        ("AHU DAN CADANGAN", 62, 84, 27, 51, "hijau"),
    ],
    "LT4-LT6": [
        ("RAWAT INAP UNIT A", 20, 48, 27, 51, "kuning"), ("RAWAT INAP UNIT B", 58, 84, 27, 51, "kuning"),
    ],
}
UTILITAS = ("GEDUNG UTILITAS DAN PARKIR", 100, 134, 44, 76)


def luas_zona():
    return {lt: [(n, (x1 - x0) * (y1 - y0), z) for n, x0, x1, y0, y1, z in zs] for lt, zs in ZONA.items()}


def cek_tangga():
    """Jarak antarpusat tangga bertetangga (maks 25 m, PMK 40/2022 hal. 12)."""
    jarak = []
    for i, a in enumerate(TANGGA):
        for b in TANGGA[i + 1:]:
            d = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
            if d < 30:
                jarak.append(d)
    return max(jarak)


# ------------------------------------------------------------------ model massa BIMCraft (LOD 100-200)
def baris_bim():
    lv = dict(tpl.LEVEL)
    b = []

    def kotak(x0, x1, y0, y1):
        return [[x0 * 1000, y0 * 1000], [x1 * 1000, y0 * 1000], [x1 * 1000, y1 * 1000], [x0 * 1000, y1 * 1000]]

    pd, mn = pr.MASSA["PODIUM"], pr.MASSA["MENARA"]
    for lt in ("LT1", "LT2", "LT3", "LT4"):
        b.append("floor " + json.dumps({"boundary": kotak(*pd["x"], *pd["y"]), "level": lt, "type": "PL-200-fc30",
                                        "structural": True}))
    for lt in ("LT1", "LT2", "LT3"):
        b.append("wall " + json.dumps({"points": kotak(*pd["x"], *pd["y"]), "closed": True, "type": "DD-150-Bata",
                                       "level": lt, "top_level": {"LT1": "LT2", "LT2": "LT3", "LT3": "LT4"}[lt]}))
    for lt in ("LT5", "LT6", "ATAP"):
        b.append("floor " + json.dumps({"boundary": kotak(*mn["x"], *mn["y"]), "level": lt, "type": "PL-200-fc30",
                                        "structural": True}))
    for lt, atas in (("LT4", "LT5"), ("LT5", "LT6"), ("LT6", "ATAP")):
        b.append("wall " + json.dumps({"points": kotak(*mn["x"], *mn["y"]), "closed": True, "type": "DD-150-Bata",
                                       "level": lt, "top_level": atas}))
    _, x0, x1, y0, y1 = UTILITAS
    for lt in ("LT1", "LT2", "LT3"):
        b.append("floor " + json.dumps({"boundary": kotak(x0, x1, y0, y1), "level": lt, "type": "PL-200-fc30",
                                        "structural": True}))
    for lt, atas in (("LT1", "LT2"), ("LT2", "LT3")):
        b.append("wall " + json.dumps({"points": kotak(x0, x1, y0, y1), "closed": True, "type": "DD-150-Bata",
                                       "level": lt, "top_level": atas}))
    for cx, cy in TANGGA:  # inti tangga beton (dinding geser) sampai atap
        atas = "ATAP" if cy < 51 else "LT4"
        b.append("wall " + json.dumps({"points": kotak(cx - 2, cx + 2, cy - 3, cy + 3), "closed": True,
                                       "type": "DG-300-fc35", "level": "LT1", "top_level": atas}))
    b.append("wall " + json.dumps({"points": kotak(*LIF), "closed": True, "type": "DG-300-fc35", "level": "LT1",
                                   "top_level": "ATAP"}))
    return b


def bangun_bim(status="disetujui Defsa 19 Nov 2026"):
    """Model massa LOD 200 di BIMCraft lewat klien skrip/bimcraft.py (sesi sendiri, lalu tampil di jendela bila ada):
    grid modul 8 m, pelat, dinding keliling, inti beton, pemisah ruang, ruang bernama per zona, tag, Pset_RSTB_Umum."""
    from bimcraft import Sesi, tampilkan

    def mm(x, y):
        return [round(x * 1000), round(y * 1000)]

    def kotak(x0, x1, y0, y1):
        return [mm(x0, y0), mm(x1, y0), mm(x1, y1), mm(x0, y1)]

    pd, mn = pr.MASSA["PODIUM"], pr.MASSA["MENARA"]
    _, ux0, ux1, uy0, uy1 = UTILITAS
    id_elemen = []

    def catat(r):
        for k in ("id", "ids"):
            v = r.get(k)
            if isinstance(v, int):
                id_elemen.append(v)
            elif isinstance(v, list):
                id_elemen.extend(i for i in v if isinstance(i, int))
        return r

    with Sesi(tpl.BIMC) as b:
        b.cmd("project_info", {"status": "Desain Konsep LOD 200 - massa dan zonasi (langkah 3.4)"})
        # grid modul 8 m: as 1-10 arah utara-selatan, A-G arah barat-timur
        xs = [pd["x"][0] + 8 * i for i in range(10)]
        ys = [pd["y"][0] + 8 * j for j in range(7)]
        for i, x in enumerate(xs):
            b.cmd("grid", {"start": mm(x, pd["y"][0] - 6), "end": mm(x, pd["y"][1] + 6), "name": str(i + 1)})
        for j, y in enumerate(ys):
            b.cmd("grid", {"start": mm(pd["x"][0] - 6, y), "end": mm(pd["x"][1] + 6, y), "name": "ABCDEFG"[j]})
        # pelat dan dinding keliling
        for lt in ("LT1", "LT2", "LT3", "LT4"):
            catat(b.cmd("floor", {"boundary": kotak(*pd["x"], *pd["y"]), "level": lt, "type": "PL-200-fc30",
                                  "structural": True}))
        for lt, atas in (("LT1", "LT2"), ("LT2", "LT3"), ("LT3", "LT4")):
            catat(b.cmd("wall", {"points": kotak(*pd["x"], *pd["y"]), "closed": True, "type": "DD-150-Bata",
                                 "level": lt, "top_level": atas}))
        for lt in ("LT5", "LT6", "ATAP"):
            catat(b.cmd("floor", {"boundary": kotak(*mn["x"], *mn["y"]), "level": lt, "type": "PL-200-fc30",
                                  "structural": True}))
        for lt, atas in (("LT4", "LT5"), ("LT5", "LT6"), ("LT6", "ATAP")):
            catat(b.cmd("wall", {"points": kotak(*mn["x"], *mn["y"]), "closed": True, "type": "DD-150-Bata",
                                 "level": lt, "top_level": atas}))
        for lt in ("LT1", "LT2", "LT3", "LT4", "LT5"):
            catat(b.cmd("floor", {"boundary": kotak(ux0, ux1, uy0, uy1), "level": lt, "type": "PL-200-fc30",
                                  "structural": True}))
        for lt, atas in (("LT1", "LT2"), ("LT2", "LT3"), ("LT3", "LT4"), ("LT4", "LT5")):
            catat(b.cmd("wall", {"points": kotak(ux0, ux1, uy0, uy1), "closed": True, "type": "DD-150-Bata",
                                 "level": lt, "top_level": atas}))
        # inti tangga dan lif (beton, dinding geser)
        for cx, cy in TANGGA:
            catat(b.cmd("wall", {"points": kotak(cx - 2, cx + 2, cy - 3, cy + 3), "closed": True,
                                 "type": "DG-300-fc35", "level": "LT1", "top_level": "ATAP" if cy < 51 else "LT4"}))
        catat(b.cmd("wall", {"points": kotak(*LIF), "closed": True, "type": "DG-300-fc35", "level": "LT1",
                             "top_level": "ATAP"}))
        # ruang per zona: pemisah ruang + room bernama di titik label (bebas inti)
        ruang = []
        rencana = [(lt, lt) for lt in ("LT1", "LT2", "LT3")] + [("LT4-LT6", lt) for lt in ("LT4", "LT5", "LT6")]
        for kunci, lt in rencana:
            inti = [(cx - 2.6, cy - 3.6, cx + 2.6, cy + 3.6) for cx, cy in TANGGA
                    if not (kunci == "LT4-LT6" and cy > 51)] + [(LIF[0] - .8, LIF[2] - .8, LIF[1] + .8, LIF[3] + .8)]
            for nama, x0, x1, y0, y1, zona in ZONA[kunci] + KOSONG.get(kunci, []):
                b.cmd("room_separator", {"points": kotak(x0, x1, y0, y1), "level": lt, "closed": True})
                cx, cy, _, _ = tempat_label(nama, x0, x1, y0, y1, 1, inti)
                r = b.cmd("room", {"point": mm(cx, cy), "level": lt, "name": nama.replace(",", ""),
                                   "number": f"{lt}-{len(ruang) + 1:02d}"})
                ruang.append(r.get("id"))
        for i, lt in enumerate(("LT1", "LT2", "LT3", "LT4")):
            r = b.cmd("room", {"point": mm((ux0 + ux1) / 2, (uy0 + uy1) / 2), "level": lt,
                               "name": "UTILITAS MEP" if lt == "LT1" else "PARKIR MOBIL", "number": f"GU-{i + 1:02d}"})
            ruang.append(r.get("id"))
        ruang = [i for i in ruang if isinstance(i, int)]
        if ruang:
            b.cmd("tag", {"ids": ruang})
        nilai = {"RSTB_Tahap": "3", "RSTB_LOD": "200", "RSTB_Status": status,
                 "RSTB_Sumber": "langkah 3.4 (tahap3_zonasi.py); dimensi [Asumsi] sampai 3.6"}
        b.cmd("modify", {"ids": id_elemen + ruang, "params": nilai})
        b.simpan(BIMC)
        b.simpan(IFC)
    tampilkan(BIMC)
    return BIMC, IFC


def cek_ifc():
    import ifcopenshell
    import ifcopenshell.util.element as ue

    f = ifcopenshell.open(str(IFC))
    n = {}
    for e in f.by_type("IfcElement"):
        c = ue.get_container(e)
        n[(e.is_a(), c.Name if c else None)] = n.get((e.is_a(), c.Name if c else None), 0) + 1
    return n



# ------------------------------------------------------------------ gambar CAD
KOSONG = {  # bidang tanpa arsir: selasar, void, inti
    "LT1": [("SELASAR UTAMA DAN RUANG TUNGGU", 36, 62, 35, 63, "kosong")],
    "LT2": [("VOID DAN TAMAN DALAM", 36, 62, 51, 75, "kosong")],
    "LT3": [("VOID DAN TAMAN DALAM", 46, 62, 27, 75, "kosong")],
    "LT4-LT6": [("INTI", 48, 58, 27, 51, "kosong")],
}
RETENSI = (112.0, 134.0, 22.0, 40.0)  # kolam retensi 396 m², dalam 1,8 m ≈ 713 m³ (≥ 650 m³ Q10, 3.3) [Asumsi dalam]
IPAL = (96.0, 108.0, 30.0, 38.0)  # IPAL tanam 12 × 8 m (Data MEP), dipindah dari zona GSB utara
PINTU = {"utama": (50.0, 58.0), "ambulans": (88.0, 94.0)}  # bukaan di jalan kolektor (x, ≥ 50 m dari simpang)


def _kotak(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _baris_label(nama, luas, lebar_maks):
    """Pecah nama zona menjadi baris yang muat di lebar zona (m, skala 1:750, huruf 1,5 mm)."""
    kata, baris, cur = nama.replace(",", "").split(), [], ""
    per_huruf = 0.95 * 1.5 * 0.75
    for k in kata:
        uji = (cur + " " + k).strip()
        if len(uji) * per_huruf > lebar_maks and cur:
            baris.append(cur)
            cur = k
        else:
            cur = uji
    baris.append(cur)
    if luas:
        baris.append(f"± {luas:,.0f} M²".replace(",", "."))
    return baris


def tempat_label(nama, x0, x1, y0, y1, luas, hindari):
    """Titik label terdekat ke pusat zona yang kotaknya di dalam zona dan tidak menimpa inti tangga/lif."""
    cx0, cy0 = (x0 + x1) / 2, (y0 + y1) / 2
    for lebar in (x1 - x0 - 3.0, (x1 - x0) * 0.6, (x1 - x0) * 0.4, 6.0):  # pecah lebih sempit bila belum muat
        baris = _baris_label(nama, luas, lebar)
        w = max(len(b) for b in baris) * 0.95 * 1.5 * 0.75
        h = len(baris) * 2.0
        if w > x1 - x0 - 1 or h > y1 - y0 - 1:
            continue
        nx = int(max(0.0, x1 - x0 - 1 - w) / 0.25) + 1
        ny = int(max(0.0, y1 - y0 - 1 - h) / 0.25) + 1
        calon = sorted(((x0 + .5 + w / 2 + i * .25, y0 + .5 + h / 2 + j * .25) for i in range(nx) for j in range(ny)),
                       key=lambda p: (p[0] - cx0) ** 2 + (p[1] - cy0) ** 2)
        for cx, cy in calon:
            k = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
            if not any(k[0] < a[2] and a[0] < k[2] and k[1] < a[3] and a[1] < k[3] for a in hindari):
                return cx, cy, baris, k
    raise ValueError(f"label '{nama}' tidak mendapat tempat kosong; ubah zona atau inti")


def _tulis_label(g, cx, cy, baris, layer="C-ZONA-TEKS"):
    n = len(baris)
    for k, s in enumerate(baris):
        tebal = not s.startswith("±")
        g.teks((cx, cy + (n / 2 - k - 0.5) * 2.0), s, layer, 1.5 if tebal else 1.4, j="MC", tebal=tebal)

def gambar_tapak(status=None):
    from cad_lembar import STATUS_SETUJU, Gambar

    tapak = tp.ringkasan()
    cm = pr.cek_massa()
    dwg = KELUAR / "Gambar" / "DWG" / "GK-03 Rencana Tapak dan Massa.dwg"
    png = KELUAR / "Gambar" / "GK-03 Rencana Tapak dan Massa.png"
    with Gambar(750) as g:
        g.layer("C-SEMPADAN", 3, 0.25)
        g.arsir(list(tp.ruang_sempadan().exterior.coords)[:-1], "C-SEMPADAN", pola="DOTS", skala_pola=0.6)
        g.legenda_tambah("arsir", "Ruang sempadan sungai (taman, jalan inspeksi lolos air)", pola="DOTS", skala_pola=0.6)
        g.layer("C-LABIL", 1, 0.25)
        g.arsir(list(tp.zona_labil().exterior.coords)[:-1], "C-LABIL", pola="ANSI31", skala_pola=1.2)
        g.legenda_tambah("arsir", "Zona labil tebing (tanpa bangunan)", pola="ANSI31", skala_pola=1.2)
        g.layer("C-RUMIJA", 8, 0.25)
        rj = tp.rumija()
        for geom in getattr(rj, "geoms", [rj]):
            g.arsir(list(geom.exterior.coords)[:-1], "C-RUMIJA", pola="ANSI37", skala_pola=0.8)
        g.legenda_tambah("arsir", "Rencana rumija", pola="ANSI37", skala_pola=0.8)
        # massa
        pd, mn = pr.MASSA["PODIUM"], pr.MASSA["MENARA"]
        g.layer("A-MASSA-PODIUM", 7, 0.7)
        g.pline(_kotak(*pd["x"], *pd["y"]), "A-MASSA-PODIUM", tutup=True)
        g.legenda_tambah("garis", "Podium LT1-LT3; gedung utilitas + parkir 4 lantai", tebal=0.7)
        g.layer("A-MASSA-MENARA", 7, 0.5, "DASHED")
        g.pline(_kotak(*mn["x"], *mn["y"]), "A-MASSA-MENARA", tutup=True)
        g.legenda_tambah("garis", "Menara rawat inap LT4-LT6 di atas podium", garis="DASHED", tebal=0.5)
        nama, x0, x1, y0, y1 = UTILITAS
        g.layer("A-MASSA-UTILITAS", 7, 0.7)
        g.pline(_kotak(x0, x1, y0, y1), "A-MASSA-UTILITAS", tutup=True)
        g.layer("A-TEKS-MASSA", 7, 0.25)
        g.teks((48, 57), "PODIUM 3 LANTAI", "A-TEKS-MASSA", 2.6, j="MC", tebal=True)
        g.teks((48, 53), f"± {pr.poligon('PODIUM').area:,.0f} M² PER LANTAI".replace(",", "."), "A-TEKS-MASSA", 1.8, j="MC")
        g.teks((48, 40), "MENARA RAWAT INAP LT4-LT6", "A-TEKS-MASSA", 2.2, j="MC", tebal=True)
        g.teks((48, 32.5), "PEIL LANTAI DASAR +12,85", "A-TEKS-MASSA", 1.8, j="MC")
        g.teks(((x0 + x1) / 2, (y0 + y1) / 2 + 1.2), "GEDUNG UTILITAS + PARKIR", "A-TEKS-MASSA", 1.6, j="MC", tebal=True)
        g.teks(((x0 + x1) / 2, (y0 + y1) / 2 - 2.0), "LT1 UTILITAS, LT2-LT4 PARKIR", "A-TEKS-MASSA", 1.4, j="MC")
        # sarana tapak
        g.layer("C-KOLAM", 7, 0.35)
        g.arsir(_kotak(*RETENSI), "C-KOLAM", pola="ANSI38", skala_pola=1.6)
        g.teks(((RETENSI[0] + RETENSI[1]) / 2, RETENSI[3] + 1.6), "KOLAM RETENSI ± 710 M³", "C-KOLAM", 1.6, j="MC")
        g.legenda_tambah("arsir", "Kolam retensi (langkah 3.3)", pola="ANSI38", skala_pola=1.6)
        g.layer("C-IPAL", 7, 0.35, "HIDDEN")
        g.pline(_kotak(*IPAL), "C-IPAL", tutup=True)
        g.teks(((IPAL[0] + IPAL[1]) / 2, IPAL[3] + 1.4), "IPAL TANAM", "C-IPAL", 1.5, j="MC")
        # jalur dan pintu
        g.layer("C-JALUR", 7, 0.35, "DASHDOT")
        g.pline([(91, 88), (91, 30), (86, 30)], "C-JALUR")  # ambulans dari kolektor ke IGD
        g.pline([(54, 88), (54, 77)], "C-JALUR")  # drop-off utama
        g.pline([(58, 1.0), (58, 20), (66, 27)], "C-JALUR")  # jalur ambulans air dari tepi sungai
        g.legenda_tambah("garis", "Jalur kendaraan dan ambulans", garis="DASHDOT", tebal=0.35)
        g.teks((90.2, 55), "JALUR AMBULANS KE IGD", "C-JALUR", 1.5, rot=90)
        g.teks((56.8, 2.0), "JALAN INSPEKSI", "C-JALUR", 1.5, rot=90)
        g.layer("C-PINTU", 7, 0.7)
        for k, (a, b) in PINTU.items():
            g.pline([(a, 90), (b, 90)], "C-PINTU")
        g.teks((54, 92), "PINTU UTAMA", "C-PINTU", 1.5, j="MC")
        g.teks((91, 92), "PINTU AMBULANS", "C-PINTU", 1.5, j="MC")
        g.layer("A-KANOPI", 7, 0.25, "HIDDEN")
        g.pline(_kotak(84, 90, 30, 46), "A-KANOPI", tutup=True)
        g.pline(_kotak(46, 62, 75, 81), "A-KANOPI", tutup=True)
        g.teks((86.2, 32), "DROP-OFF IGD", "A-KANOPI", 1.4, rot=90)
        g.teks((54, 82.3), "DROP-OFF LOBI", "A-KANOPI", 1.4, j="MC")
        g.teks((14, 80), "PARKIR PERMUKAAN P1 (GK-05)", "C-TEKS", 1.5)
        # persil, gudang, BM
        g.layer("C-PERSIL", 7, 0.7, "PHANTOM")
        g.pline([(0, 0), (140, 0), (140, 90), (0, 90)], "C-PERSIL", tutup=True)
        g.legenda_tambah("garis", "Batas persil 140 × 90 M", garis="PHANTOM", tebal=0.7)
        g.layer("C-GUDANG", 8, 0.35)
        gx, gy, gw, gh = tp.GUDANG
        g.arsir(_kotak(gx, gx + gw, gy, gy + gh), "C-GUDANG", pola="ANSI31", skala_pola=1.5)
        g.teks((gx + gw / 2, gy - 3), "GUDANG TETANGGA", "C-GUDANG", 1.8, j="MC", tebal=True)
        g.teks((70, 96.5), "JALAN KOLEKTOR", "C-TEKS", 2.2, j="MC", tebal=True)
        g.teks((70, -14), "SUNGAI BATANGHARI", "C-TEKS", 2.6, j="MC", tebal=True)
        g.titik_tinggi((0, 0), "BM-1 +10,000", teks_at=(-21, -10.5))
        g.pline([(-0.7, -0.7), (-5.2, -0.7), (-8, -9.3), (-11.5, -9.3)], "C-TEKS")
        # ukuran massa
        g.ukur((pd["x"][0], pd["y"][1]), (pd["x"][1], pd["y"][1]), (30, 86.0))
        g.ukur((pd["x"][0], pd["y"][0]), (pd["x"][0], pd["y"][1]), (6.5, 51))
        g.ukur((0, 60), (pd["x"][0], 60), (6, 63.5))
        g.ukur((x0, y1), (x1, y1), ((x0 + x1) / 2, y1 + 4.5))
        g.ukur((x1, y0), (x1, y1), (x1 + 4.5, (y0 + y1) / 2))
        g.lembar("GK-03", "Rencana tapak dan massa", "1:750", pusat=(76, 40), revisi="C",
                 subjudul="Langkah 3.2 (amplop, PKKPR), 3.3 (peil, retensi), 3.4 (program ruang 150 TT); rev C: opsi C (3.5), menara di grid 8 m (3.6)",
                 status=status or STATUS_SETUJU,
                 catatan=[
                     f"Tapak bangunan {cm['tapak']:,.0f} m² ≤ KDB {cm['kdb_maks']:,.0f} m²; luas lantai {cm['luas_lantai']:,.0f} m²"
                     f" ≤ KLB {cm['klb_maks']:,.0f} m².".replace(",", "."),
                     "Lantai dasar dan utilitas +12,85; halaman +12,05; tanpa basement (3.5).",
                     "Massa di luar zona labil dan sempadan; menara menghadap sungai.",
                     "Parkir: gedung parkir LT2-LT4 dan permukaan (GK-05).",
                 ])
        g.skala_grafis(205, 22, 50)
        g.panah_utara(318, 262, 10)
        g.simpan(dwg, PDF_TAPAK, png)
    return dwg


def gambar_zonasi(status=None):
    from cad_lembar import STATUS_SETUJU, Gambar

    dwg = KELUAR / "Gambar" / "DWG" / "GK-04 Zonasi Lantai.dwg"
    png = KELUAR / "Gambar" / "GK-04 Zonasi Lantai.png"
    geser = {"LT1": (0, 0), "LT2": (90, 0), "LT3": (0, -66), "LT4-LT6": (90, -66)}
    judul = {"LT1": "DENAH ZONASI LANTAI 1 (+12,85)", "LT2": "DENAH ZONASI LANTAI 2 (+17,35)",
             "LT3": "DENAH ZONASI LANTAI 3 (+21,85)", "LT4-LT6": "DENAH ZONASI LANTAI 4-6 (TIPIKAL)"}
    with Gambar(750) as g:
        g.legenda_tambah("arsir", "Zona merah: gawat darurat (PMK 40/2022 hal. 9)", pola="ANSI31", skala_pola=0.9)
        g.legenda_tambah("arsir", "Zona kuning: pelayanan pasien", pola="DOTS", skala_pola=0.7)
        g.legenda_tambah("arsir", "Zona hijau: penunjang dan manajemen", pola="ANSI37", skala_pola=1.4)
        g.legenda_tambah("arsir", "Inti tangga darurat dan lif (beton)", pola="SOLID")
        g.legenda_tambah("garis", "Batas massa bangunan", tebal=0.7)
        pd, mn = pr.MASSA["PODIUM"], pr.MASSA["MENARA"]
        for lt, (dx, dy) in geser.items():
            def k(x0, x1, y0, y1):
                return _kotak(x0 + dx, x1 + dx, y0 + dy, y1 + dy)
            batas = mn if lt == "LT4-LT6" else pd
            inti = [(cx - 2.6, cy - 3.6, cx + 2.6, cy + 3.6) for cx, cy in TANGGA
                    if not (lt == "LT4-LT6" and cy > 51)] + [(LIF[0] - .8, LIF[2] - .8, LIF[1] + .8, LIF[3] + .8)]
            if lt != "LT4-LT6":  # garis batas menara (putus-putus) juga dihindari label
                inti += [(19, 50.2, 85, 51.8), (19.2, 26, 20.8, 52)]
            for nama, x0, x1, y0, y1, zona in ZONA[lt] + KOSONG.get(lt, []):
                luas = (x1 - x0) * (y1 - y0) if zona != "kosong" else 0
                cx, cy, baris, kt = tempat_label(nama, x0, x1, y0, y1, luas, inti)
                if zona != "kosong":
                    pola, sk = POLA[zona]
                    lap = f"A-ZONA-{zona.upper()}"
                    g.layer(lap, 7, 0.18)
                    m = 0.6
                    lub = [(kt[0] - m + dx, kt[1] - m + dy), (kt[2] + m + dx, kt[1] - m + dy),
                           (kt[2] + m + dx, kt[3] + m + dy), (kt[0] - m + dx, kt[3] + m + dy)]
                    g.arsir_lubang(k(x0, x1, y0, y1), [lub], lap, pola=pola, skala_pola=sk)
                    g.pline(k(x0, x1, y0, y1), lap, tutup=True)
                _tulis_label(g, cx + dx, cy + dy, baris)
            g.layer("A-INTI", 7, 0.35)
            for cx, cy in TANGGA:
                if lt == "LT4-LT6" and cy > 51:
                    continue
                g.arsir(k(cx - 2, cx + 2, cy - 3, cy + 3), "A-INTI", pola="SOLID")
            g.arsir(k(*LIF), "A-INTI", pola="SOLID")
            g.layer("A-MASSA", 7, 0.7)
            g.pline(k(*batas["x"], *batas["y"]), "A-MASSA", tutup=True)
            if lt != "LT4-LT6":
                g.layer("A-MASSA-MENARA", 7, 0.25, "DASHED")
                g.pline(k(*mn["x"], *mn["y"]), "A-MASSA-MENARA", tutup=True)
            g.layer("A-JUDUL-DENAH", 7, 0.35)
            g.teks((12 + dx, 21 + dy), judul[lt], "A-JUDUL-DENAH", 2.2, tebal=True)
            g.pline([(12 + dx, 20.2 + dy), (62 + dx, 20.2 + dy)], "A-JUDUL-DENAH", tebal=0.5)
        g.lembar("GK-04", "Zonasi lantai", "1:750", pusat=(91, 18), revisi="B",
                 subjudul="Program ruang versi konsultan (langkah 3.4); tangga darurat berjarak maks 25 m (PMK 40/2022 hal. 12)",
                 status=status or STATUS_SETUJU,
                 catatan=[
                     "Podium 72 × 48 m dan menara 64 × 24 m di grid 8 m (3.6).",
                     "Bedah sentral di atas IGD; ICU di samping bedah sentral (arahan owner butir 6).",
                     "Rawat inap 150 TT di LT4-LT6, 2 unit per lantai; ICU/HCU/NICU di LT2.",
                     "Luas zona skematik; denah rinci di Tahap 7.",
                 ])
        g.skala_grafis(205, 22, 50)
        g.simpan(dwg, PDF_ZONA, png)
    return dwg

if __name__ == "__main__":
    for lt, zs in luas_zona().items():
        print(lt, [(n, a) for n, a, _ in zs], sum(a for _, a, _ in zs))
    print("tangga maks", cek_tangga())
    print(bangun_bim())
    print(cek_ifc())
