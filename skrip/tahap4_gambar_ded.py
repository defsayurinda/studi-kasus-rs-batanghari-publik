"""Langkah 4.10: gambar struktur atas setara DED (GS-03 s.d. GS-19) di CADCraft, ber-kop KOP_A3.

Alur BIM (sama dengan 3.11; arahan Defsa: gambar diambil dari model BIM, alur BIM 1D-7D):
  model BIMCraft LOD 300 `model/RSTB-STR-T4-LOD300.bimc` (4.9, ukuran dari skrip desain 4.5-4.8)
  -> tampak denah tiap lantai dan potongan disimpan di model lalu diekspor ke DXF (`04 Struktur Atas/Gambar/BIM/`)
  -> garis-teks BIMCraft (teks yang diekspor sebagai garis pendek < 100 mm) dibuang dari DXF (`bersihkan_dxf`)
  -> DXF diimpor ke model space CADCraft (1 unit = 1 mm, koordinat proyek)
  -> anotasi asli CADCraft: as grid, kode unsur, ukuran asosiatif, titik tinggi, legenda, catatan.
Detail penulangan (tabel dan penampang 1:20-1:50) digambar di CADCraft dari hasil skrip desain 4.6-4.8 karena
tulangan tidak dimodelkan di LOD 300 (baru LOD 350/400). Angka diambil dari skrip, bukan diketik ulang.
DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (20 Nov 2026); disetujui
Defsa 20 Nov 2026. Kunci jawaban tidak dibuka.
Jalankan: .venv\\Scripts\\python.exe skrip\\tahap4_gambar_ded.py [--ekspor] [GS-04 GS-11 ...]
"""
from __future__ import annotations

import functools
import math
import sys
from pathlib import Path

from shapely.geometry import Point, box
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_beban as tb  # noqa: E402
import tahap4_bim as bim  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "04 Struktur Atas"
GAMBAR = KELUAR / "Gambar"
DWG = GAMBAR / "DWG"
BIM = GAMBAR / "BIM"
PDF = KELUAR / "4.10 Gambar Struktur Atas DED.pdf"
TANGGAL = "NOVEMBER 2026"
STATUS = "DISETUJUI 20 NOV 2026"   # label kop (persetujuan Defsa atas 4.10)
LANTAI = ["LT1", "LT2", "LT3", "LT4", "LT5", "LT6", "ATAP"]
NAMA_X = [str(i + 1) for i in range(len(tb.GRID_X))]
NAMA_Y = bim.NAMA_Y
SKALA_DENAH = 300
Y_POT_A = 35.0          # as B: memotong menara, podium, dan inti tangga y 39 di belakang bidang
X_POT_B = 68.0          # as 8: memotong balok transfer tangki x 68 dan kolom 950
TANGGA = "Tangga x22 y39"
TEKS_BIM = {"grid", "level", "section", "tag", "room", "door"}   # layer anotasi BIMCraft yang diganti anotasi CADCraft
GARIS_TEKS = 100.0      # mm, garis lebih pendek dari ini = goresan huruf hasil ekspor teks BIMCraft

# kode unsur di gambar -> kelompok desain 4.6-4.8
KODE_BALOK = {"B-P dalam": "B1", "B-P tepi": "B2", "B-M dalam": "B3", "B-M tepi": "B4",
              "B-T induk tangki x 68": "BT1", "B-T induk tangki x 60/76": "BT2", "B-T induk tangki y 67": "BT3",
              "balok anak tangki": "BA", "rel chiller": "BR"}
KODE_KOLOM = {"K-P": "K1", "K-M": "K2", "K-T": "K3", "K-T68": "K4"}
KODE_DINDING = {"W-L": "DG1", "W-TM": "DG2", "W-TP": "DG3"}


def nomor(lv):
    return f"GS-{4 + LANTAI.index(lv):02d}"


def id_(v, n=2):
    return f"{v:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def elev(lv):
    return f"+{id_(tb.LEVEL[lv])}"


# ------------------------------------------------------------------ data desain (sekali per proses)
@functools.lru_cache(maxsize=1)
def data():
    import tahap4_balok as bk
    import tahap4_dinding as td
    import tahap4_fasad as fs
    import tahap4_kolom as kl
    rb = bk.ringkasan()
    return {"balok": rb, "kolom": kl.rancang(), "dinding": td.rancang(), "fasad": fs.ringkas(),
            "tepi": {x["kelompok"]: x for x in fs.cek_balok_tepi()}, "unsur": bim.unsur(rb["ukuran_model"])}


@functools.lru_cache(maxsize=1)
def wilayah():
    """Wilayah lantai + atap per tingkat (K2) dan wilayah kolom di bawahnya."""
    out = {}
    for t in tb.tingkat("K2"):
        out[t["lv"]] = {"pelat": unary_union([g for g in (t.get("lantai"), t.get("atap")) if g is not None]),
                        "kolom": t["kolom_bawah"][0]}
    return out


def kelompok_balok(e):
    """Nama kelompok desain 4.6 untuk unsur balok dari `bim.unsur()` (aturan sama dengan tahap4_balok.kelompok)."""
    import tahap4_balok as bk
    if e.get("khusus"):
        return e["khusus"]
    x1, y1, x2, y2 = e["p"]
    arah = "X" if abs(y1 - y2) < 1e-6 else "Y"
    wil = wilayah()[e["lv"]]["pelat"]
    xm, ym = (x1 + x2) / 2, (y1 + y2) / 2
    nx, ny = (0.0, 2.0) if arah == "X" else (2.0, 0.0)
    sisi = sum(wil.buffer(0.01).contains(Point(xm + s * nx, ym + s * ny)) for s in (1, -1))
    return bk.kelompok({"lv": e["lv"], "x1": x1, "y1": y1, "x2": x2, "y2": y2, "arah": arah}, sisi)


def kode_balok(nama):
    for k, v in KODE_BALOK.items():
        if nama.startswith(k):
            return v
    raise KeyError(nama)


def kode_kolom(nama):
    return KODE_KOLOM[nama.split()[0]]


def kelompok_kolom(e):
    import tahap4_kolom as kl
    return kl.kelompok_kolom(e["lv"], e["x"], e["y"], e["b"])


# ------------------------------------------------------------------ ekspor dari model BIM dan pembersihan DXF
def dxf(nama):
    return BIM / f"RSTB-STR-T4 {nama}.dxf"


# potongan detail besi dari model LOD 350: (nama, awal, akhir) mm; sumbu mendatar DXF = jarak dari awal
# bidang potong tepat di satu sengkang (BIMCraft hanya menggambar besi yang terpotong): sengkang model mulai x 28,045
DETAIL = [("DET B1 TUMPUAN", [28945, 41000], [28945, 45000]), ("DET B1 LAPANGAN", [32000, 41000], [32000, 45000]),
          ("DET B4 TUMPUAN", [28945, 25000], [28945, 29000]), ("DET BT1 TUMPUAN", [66000, 68145], [70000, 68145]),
          ("MEMANJANG B1", [26000, 43000], [38000, 43000])]
DENAH_DETAIL = ("LT1", "LT2", "LT4")    # denah yang juga diekspor dengan besi untuk penampang kolom
KOLOM_DETAIL = {"LT1": [(36.0, 35.0)], "LT2": [(60.0, 67.0), (68.0, 67.0)], "LT4": [(36.0, 35.0)]}
# daerah yang disimpan dari DXF detail (mm, koordinat DXF): bidang potong BIMCraft tak berujung
KOTAK = {"Det B1 Tumpuan": [(0, 19000, 4000, 23500)], "Det B1 Lapangan": [(0, 19000, 4000, 23500)],
         "Det B4 Tumpuan": [(0, 24000, 4000, 27500)], "Det Bt1 Tumpuan": [(0, 19500, 4000, 23000)],
         "Memanjang B1": [(0, 16000, 12000, 23000)], "Potongan Tangga": [(-500, 12000, 12000, 23000)],
         **{f"Detail Denah {lv}": [(x * 1000 - 600, y * 1000 - 600, x * 1000 + 600, y * 1000 + 600)
                                   for x, y in k] for lv, k in KOLOM_DETAIL.items()}}
DALAM = {f"Detail Denah {lv}" for lv in KOLOM_DETAIL}   # simpan hanya entitas yang utuh di dalam kotak (tanpa besi balok lewat)


def ekspor_bim():
    """Ekspor tampak dari model pembesian LOD 350 (tahap4_besi; dibangun bila belum ada) ke DXF: denah LT1-ATAP,
    potongan A-A (as B), B-B (as 8), tangga, dan potongan detail besi balok/kolom. Tampak disimpan di model."""
    import shutil

    import tahap4_besi as besi
    from bimcraft import GalatBIM, Sesi
    BIM.mkdir(parents=True, exist_ok=True)
    besi.bangun()   # model LOD 350 selalu dibangun ulang dari LOD 300 + desain terbaru (tanpa tampak lama)
    d = bim.dalam_inti(TANGGA)
    import tahap4_dinding as td
    x_t = d.bounds[0] + td.tangga(4.5)["lebar"] / 2   # tengah lengan pertama (naik ke utara)
    pot = [("POTONGAN A-A", [0, round(Y_POT_A * 1000)], [100000, round(Y_POT_A * 1000)], 4000),
           ("POTONGAN B-B", [round(X_POT_B * 1000), 85000], [round(X_POT_B * 1000), 15000], 4000),
           ("POTONGAN TANGGA", [round(x_t * 1000), round((d.bounds[1] - 1.5) * 1000)],
            [round(x_t * 1000), round((d.bounds[3] + 1.5) * 1000)], 300)] +         [(n, a, b_, 250) for n, a, b_ in DETAIL]   # 250 mm: paling sedikit satu sengkang terlihat
    hasil = []
    with Sesi(besi.BIMC) as b:
        for lv in LANTAI:
            b.cmd("export", {"format": "dxf", "view": lv, "path": str(dxf(f"Denah {lv}")), "overwrite": True})
            hasil.append(dxf(f"Denah {lv}"))
            if lv in DENAH_DETAIL:
                shutil.copy(dxf(f"Denah {lv}"), dxf(f"Detail Denah {lv}"))
                hasil.append(dxf(f"Detail Denah {lv}"))
        for nama, p1, p2, dalam in pot:
            try:
                b.cmd("section", {"start": p1, "end": p2, "depth": dalam, "name": nama})
            except GalatBIM as e:   # tampak sudah tersimpan di model dari ekspor sebelumnya
                if "already named" not in str(e):
                    raise
            b.cmd("export", {"format": "dxf", "view": nama, "path": str(dxf(nama.title())), "overwrite": True})
            hasil.append(dxf(nama.title()))
        b.simpan(besi.BIMC)
    for p in hasil:
        detail = p.stem.split(" ", 1)[1].startswith(("Detail", "Det ", "Memanjang", "Potongan Tangga"))
        nama = p.stem.split(" ", 1)[1]
        bersihkan_dxf(p, tanpa_besi=not detail, kotak=KOTAK.get(nama), dalam=nama in DALAM)
    return hasil


def bersihkan_dxf(path, tanpa_besi=False, kotak=None, dalam=False):
    """Siapkan DXF BIMCraft untuk gambar: buang goresan teks (LINE < 100 mm, polyline/arsir < 300 mm di layer
    dinding/pelat), layer anotasi, dan arsir pejal beton (poché; arahan Defsa: potongan tidak hitam pejal) sehingga
    beton tampil sebagai garis tepi dan besi terlihat. tanpa_besi: buang juga layer besi (denah/potongan 1:300);
    kotak: daftar (x0, y0, x1, y1) mm, entitas di luar semua kotak dibuang (DXF detail tetap kecil).
    Kembalikan jumlah entitas yang dibuang."""
    import ezdxf
    doc = ezdxf.readfile(str(path))
    ms = doc.modelspace()
    from ezdxf import bbox

    def kecil(e):
        if e.dxf.layer not in ("wall", "floor"):   # goresan teks BIMCraft hanya ada di layer dinding/pelat
            return False
        if e.dxftype() == "LINE":
            return math.hypot(e.dxf.start.x - e.dxf.end.x, e.dxf.start.y - e.dxf.end.y) < GARIS_TEKS
        if e.dxftype() in ("LWPOLYLINE", "HATCH"):   # goresan huruf/kepala panah: sampai 300 mm
            b = bbox.extents([e])
            return max(b.size.x, b.size.y) < 3 * GARIS_TEKS
        return False

    def luar(e):
        if not kotak:
            return False
        b = bbox.extents([e])
        if not b.has_data:
            return True
        if dalam:
            return not any(b.extmin.x >= k[0] and b.extmax.x <= k[2] and b.extmin.y >= k[1] and b.extmax.y <= k[3]
                           for k in kotak)
        return not any(b.extmax.x >= k[0] and b.extmin.x <= k[2] and b.extmax.y >= k[1] and b.extmin.y <= k[3]
                       for k in kotak)

    def buang_(e):
        if e.dxf.layer in TEKS_BIM or kecil(e) or luar(e):
            return True
        if e.dxf.layer == "rebar":
            return tanpa_besi
        return e.dxftype() == "HATCH"     # poché beton
    buang = [e for e in ms if buang_(e)]
    for e in buang:
        ms.delete_entity(e)
    doc.saveas(str(path))
    return len(buang)


def batas_dxf(path):
    """Kotak batas isi DXF (m): x0, y0, x1, y1."""
    import ezdxf
    from ezdxf import bbox
    b = bbox.extents(ezdxf.readfile(str(path)).modelspace())
    return b.extmin.x / 1000, b.extmin.y / 1000, b.extmax.x / 1000, b.extmax.y / 1000


def impor(g, path):
    r = g.cmd("import", {"path": str(path), "at": [0, 0]})
    return r["imported"]


# ------------------------------------------------------------------ lembar denah (GS-04 s.d. GS-10)
def _batas_lantai(lv):
    w = wilayah()["LT2" if lv == "LT1" else lv]
    return (w["kolom"] if lv == "LT1" else w["pelat"]).bounds


def _atas(lv):
    """Tingkat di atas lv (kolom yang terpotong bidang denah lv berujung di tingkat ini)."""
    return LANTAI[LANTAI.index(lv) + 1] if lv != "ATAP" else None


def _penghalang(lv):
    """Inti (dinding menerus di atas lv) dan shaft yang menembus lv, untuk menghindari label pelat."""
    kotak = []
    for nama, _, puncak in tb.INTI:
        if tb.LEVEL[puncak] > tb.LEVEL[lv] + 1e-6:
            kotak.append(bim.dalam_inti(nama).buffer(0.6, join_style=2))
    for kode, x0, x1, y0, y1, a, c in bim.SHAFT:
        if tb.LEVEL[a] <= tb.LEVEL[lv] <= tb.LEVEL[c]:
            kotak.append(box(x0, y0, x1, y1).buffer(0.8, join_style=2))
    if lv == "LT3":   # rel chiller dan balok anak tangki
        kotak.append(box(60.0, 52.0, 76.0, 72.0))
    return unary_union(kotak)


def kode_inti(nama):
    if nama.startswith("Inti"):
        return "DG1"
    return "DG2" if tb.MENARA.contains(Point(bim.PUSAT[nama])) else "DG3"


def denah(lv, status=None):
    from cad_lembar import Gambar
    no = nomor(lv)
    judul = f"Denah struktur {lv} ({elev(lv)})" if lv != "LT1" else f"Denah kolom dan inti {lv} ({elev(lv)})"
    dwg = DWG / f"{no} Denah Struktur {lv}.dwg"
    d = data()
    x0, y0, x1, y1 = _batas_lantai(lv)
    atas = _atas(lv)
    with Gambar(SKALA_DENAH) as g:
        impor(g, dxf(f"Denah {lv}"))
        g.legenda_tambah("arsir", "Kolom terpotong (model BIM)", pola="SOLID")
        g.legenda_tambah("garis", "Dinding inti, balok, tepi pelat (model BIM)", tebal=0.35)
        g.legenda_tambah("garis", "As grid", garis="CENTER", tebal=0.18)
        # as grid: potongan pendek di luar bangunan, gelembung di atas-bawah dan kiri
        for i, x in enumerate(tb.GRID_X):
            if x0 - 0.01 <= x <= x1 + 0.01:
                g.as_grid(NAMA_X[i], (x, y1 + 1.5), (x, y1 + 5.0), r_kertas=3.0, dua_ujung=False)
                g.as_grid(NAMA_X[i], (x, y0 - 1.5), (x, y0 - 5.0), r_kertas=3.0, dua_ujung=False)
        for j, y in enumerate(tb.GRID_Y):
            if y0 - 0.01 <= y <= y1 + 0.01:
                g.as_grid(NAMA_Y[j], (x0 - 1.5, y), (x0 - 5.0, y), r_kertas=3.0, dua_ujung=False)
        # ukuran berantai (asosiatif) antar as dan total
        xs = [x for x in tb.GRID_X if x0 - 0.01 <= x <= x1 + 0.01]
        ys = [y for y in tb.GRID_Y if y0 - 0.01 <= y <= y1 + 0.01]
        for a, b in zip(xs[:-1], xs[1:]):
            g.ukur((a, y1 + 8.5), (b, y1 + 8.5), ((a + b) / 2, y1 + 8.5))
        g.ukur((xs[0], y1 + 11.5), (xs[-1], y1 + 11.5), ((xs[0] + xs[-1]) / 2, y1 + 11.5))
        for a, b in zip(ys[:-1], ys[1:]):
            g.ukur((x0 - 8.5, a), (x0 - 8.5, b), (x0 - 8.5, (a + b) / 2), rot=90)
        g.ukur((x0 - 11.5, ys[0]), (x0 - 11.5, ys[-1]), (x0 - 11.5, (ys[0] + ys[-1]) / 2), rot=90)
        # kode balok di tengah bentang (khusus: seperempat bentang supaya tidak menimpa balok induk)
        g.layer("S-TEKS-BALOK", 7, 0.18)
        kode_dipakai = set()
        for e in d["unsur"]:
            if e["k"] != "balok" or e["lv"] != lv:
                continue
            kode = kode_balok(kelompok_balok(e))
            kode_dipakai.add(kode)
            bx1, by1, bx2, by2 = e["p"]
            if abs(by1 - by2) < 1e-6:
                xm = bx1 + (bx2 - bx1) * (0.25 if e.get("khusus") else 0.5)
                g.teks((xm, by1 + e["b"] / 2 + 0.25), kode, "S-TEKS-BALOK", 1.6, j="BC")
            else:
                g.teks((bx1 - e["b"] / 2 - 0.25, (by1 + by2) / 2), kode, "S-TEKS-BALOK", 1.6, j="BC", rot=90)
        # kode kolom yang terpotong bidang denah (segmen lv -> tingkat di atasnya)
        g.layer("S-TEKS-KOLOM", 7, 0.18)
        for e in d["unsur"]:
            if e["k"] == "kolom" and e["lv"] == atas:
                g.teks((e["x"] + e["b"] / 2 + 0.15, e["y"] + e["b"] / 2 + 0.15), kode_kolom(kelompok_kolom(e)),
                       "S-TEKS-KOLOM", 1.6, j="L")
        # kode dinding inti di bordes bawah
        g.layer("S-TEKS-DINDING", 7, 0.18)
        for nama, _, puncak in tb.INTI:
            if tb.LEVEL[puncak] > tb.LEVEL[lv] + 1e-6:
                bx0, by0, bx1, by1 = bim.dalam_inti(nama).bounds
                yk = by1 - 0.5 if nama.startswith("Inti") else by0 + 0.5   # lif: di atas, jauh dari label kolom
                g.teks(((bx0 + bx1) / 2, yk), kode_inti(nama), "S-TEKS-DINDING", 1.8, j="MC", tebal=True)
        # shaft
        g.layer("S-TEKS-SHAFT", 7, 0.18)
        for kode, sx0, sx1, sy0, sy1, a, c in bim.SHAFT:
            if tb.LEVEL[a] <= tb.LEVEL[lv] <= tb.LEVEL[c] and x0 <= sx0 <= x1 and y0 <= sy0 <= y1:
                if sx1 > x1 - 3.0:   # dekat tepi timur: label di kiri shaft
                    g.teks((sx0 - 0.25, (sy0 + sy1) / 2), kode, "S-TEKS-SHAFT", 1.6, j="MR")
                else:
                    g.teks((sx1 + 0.25, (sy0 + sy1) / 2), kode, "S-TEKS-SHAFT", 1.6, j="ML")
        if lv in ("LT2", "LT3"):   # SH-4 hasil clash 4.9: ukuran asosiatif dari as 7
            g.ukur((60.6, 46.0), (63.0, 46.0), (61.8, 47.6))
            g.tunjuk((62.4, 44.2), (65.6, 48.6), "SH-4 DIGESER (4.9)", layer="S-TEKS-SHAFT")
        # pelat: kode di tengah panel yang bebas inti/shaft
        if lv != "LT1":
            g.layer("S-TEKS-PELAT", 7, 0.18)
            hal = _penghalang(lv)
            pelat = wilayah()[lv]["pelat"]
            for xa in tb.GRID_X[:-1]:
                for ya in tb.GRID_Y[:-1]:
                    c = Point(xa + 4, ya + 4)
                    if pelat.contains(c) and not hal.intersects(c.buffer(2.2)):
                        tangki = lv == "LT3" and 60 < c.x < 72 and 67 < c.y < 73
                        g.teks((c.x, c.y), "S2" if tangki else "S1", "S-TEKS-PELAT", 1.8, j="MC")
        # titik tinggi lantai dan garis potong
        g.titik_tinggi((x0 + 0.9, y0 + 2.2), f"{elev(lv)} {lv}", "S-ELEVASI")
        g.layer("S-POTONG", 7, 0.5)
        if y0 <= Y_POT_A <= y1:
            for xa, xb in ((x0 - 3.6, x0 - 2.0), (x1 + 2.0, x1 + 3.6)):
                g.pline([(xa, Y_POT_A), (xb, Y_POT_A)], "S-POTONG")
                g.teks(((xa + xb) / 2, Y_POT_A + 0.5), "A", "S-POTONG", 2.2, j="BC", tebal=True)
        if x0 <= X_POT_B <= x1:
            for ya, yb in ((y0 - 3.6, y0 - 2.0), (y1 + 2.0, y1 + 3.6)):
                g.pline([(X_POT_B, ya), (X_POT_B, yb)], "S-POTONG")
                g.teks((X_POT_B + 0.5, (ya + yb) / 2), "B", "S-POTONG", 2.2, j="ML", tebal=True)
        g.legenda_tambah("garis", "Garis potong A-A (GS-11), B-B (GS-12)", tebal=0.5)
        rujuk = (("Balok " + ", ".join(sorted(kode_dipakai)) + ": GS-13; ") if kode_dipakai else "") + \
            "kolom K1-K4: GS-14; dinding DG1-DG3: GS-15."
        catatan = [f"Geometri dari model BIM RSTB-STR-T4-LOD300 (4.9), tampak denah {lv} diekspor DXF; anotasi "
                   "CADCraft.", rujuk,
                   "Pelat S1 t 200, S2 t 250 (bawah tangki), fc' 30; kolom/dinding fc' 35; BjTS 420B (4.5-4.8).",
                   f"Kolom tergambar: segmen {lv}-{atas}." if atas else "Tumpuan dek helipad HEB 200 [Asumsi].",
                   "Ukuran dalam meter; elevasi terhadap BM-1 = +10,000."]
        if lv in ("LT2", "LT3"):
            catatan.insert(3, "SH-4 digeser ke x 60,6-63,0, y 43,6-46,0 (clash 4.9, keputusan Defsa 20 Nov 2026).")
        if lv == "LT3":
            catatan.insert(3, "Atap V1 utara +21,85: rel chiller BR, tangki 210 m³ (S2, BA, BT1-BT3): GS-17.")
        xc, yc = (x0 - 12 + x1 + 7) / 2, (y0 - 7 + y1 + 12.5) / 2
        g.lembar(no, judul, f"1:{SKALA_DENAH}", pusat=(xc, yc), status=status or STATUS, tanggal=TANGGAL,
                 subjudul="Langkah 4.10: denah dari model BIMCraft LOD 300 (4.9); kode unsur dari desain 4.5-4.8",
                 catatan=catatan, judul_kop=f"DENAH STRUKTUR {lv}")
        g.skala_grafis(205, 22, 20, bagi=4)
        g.panah_utara(318, 262, 10)
        _simpan(g, dwg)
    return dwg


def cek(dwg):
    import cad_cek
    return cad_cek.cek(dwg)


PLOT = GAMBAR / "_plot"   # PDF per lembar sementara; digabung menjadi PDF 4.10 lalu dihapus


def _simpan(g, dwg):
    PLOT.mkdir(parents=True, exist_ok=True)
    g.simpan(dwg, PLOT / f"{dwg.stem}.pdf", GAMBAR / f"{dwg.stem}.png")


# ------------------------------------------------------------------ pembantu gambar detail (model space, meter)
def tabel(g, x, y, lebar, kepala, baris, h=1.6, layer="S-TABEL", kiri=(1,)):
    """Tabel bergaris di model space. lebar: mm kertas per kolom; sel boleh berisi beberapa baris ('\\n').
    Lebar huruf dicek dengan faktor cad_cek (0,90 h per huruf) supaya teks tidak keluar sel. Kembalikan y bawah."""
    s = g.skala / 1000
    g.layer(layer, 7, 0.25)
    W = sum(lebar) * s
    xs = [x]
    for w in lebar:
        xs.append(xs[-1] + w * s)
    semua = [list(kepala)] + [[str(c) for c in b] for b in baris]
    for r in semua:
        for c, w in zip(r, lebar):
            for bar in str(c).split("\n"):
                if 0.9 * h * len(bar) > w - 1.2:
                    raise ValueError(f"teks '{bar}' tidak muat di kolom {w} mm")
    yy = y
    g.pline([(x, y), (x + W, y)], layer)
    for i, r in enumerate(semua):
        n = max(len(str(c).split("\n")) for c in r)
        tinggi_b = (n * (h + 1.4) + 1.6) * s
        for j, c in enumerate(r):
            for k, bar in enumerate(str(c).split("\n")):
                yb = yy - (0.8 + h + 0.5 + k * (h + 1.4)) * s
                if i and j in kiri:
                    g.teks((xs[j] + 1.0 * s, yb), bar, layer, h, j="L")
                else:
                    g.teks(((xs[j] + xs[j + 1]) / 2, yb), bar, layer, h, j="BC", tebal=(i == 0))
        yy -= tinggi_b
        g.pline([(x, yy), (x + W, yy)], layer, tebal=0.35 if i == 0 else None)
    for xv in xs:
        g.pline([(xv, y), (xv, yy)], layer)
    return yy


def _bulat(g, c, d, layer):
    """Batang tulangan (lingkaran terisi) diameter d (m) sebagai poligon 12 sisi + arsir SOLID."""
    r = max(d / 2, 0.006)
    pts = [(c[0] + r * math.cos(t * math.pi / 6), c[1] + r * math.sin(t * math.pi / 6)) for t in range(12)]
    g.arsir(pts, layer, "SOLID")


def _baris_batang(g, x0, x1, y, n, d, layer):
    if n == 1:
        _bulat(g, ((x0 + x1) / 2, y), d, layer)
        return
    for i in range(n):
        _bulat(g, (x0 + (x1 - x0) * i / (n - 1), y), d, layer)


def _lembar_detail(g, no, judul, skala_teks, subjudul, catatan, status, pusat, judul_kop=None, viewports=None,
                   vp=None):
    g.lembar(no, judul, skala_teks, pusat=pusat, status=status or STATUS, tanggal=TANGGAL, subjudul=subjudul,
             catatan=catatan, judul_kop=judul_kop, viewports=viewports, vp=vp)


def tul(t):
    return f"{t['n']}D{t['db']}" + (f" ({t['lapis']} lapis)" if t.get("lapis", 1) > 1 else "")


# ------------------------------------------------------------------ GS-03 catatan umum dan daftar gambar
def ld_tabel():
    """Panjang penyaluran tarik dan lewatan kelas B (mm), SNI 2847 Tabel 25.4.2.2 hal. 566 (spasi bersih >= db,
    selimut >= db, sengkang minimum) dan Tabel 25.5.2.1 hal. 586; ψe 1,0, λ 1,0; ψt 1,3 tulangan atas."""
    out = []
    for db in (10, 13, 16, 19, 22, 25, 29, 32):
        k = 2.1 if db <= 19 else 1.7
        r = []
        for fc in (30.0, 35.0):
            for psit in (1.0, 1.3):
                ld = max(420 * psit / (k * math.sqrt(fc)) * db, 300)
                r.append(math.ceil(ld / 50) * 50)
        out.append((db, r, [math.ceil(max(1.3 * v, 300) / 50) * 50 for v in r]))
    return out


DAFTAR = [("GS-01", "Respons spesifik situs", "TANPA SKALA"), ("GS-02", "Zona beban", "1:500"),
          ("GS-03", "Catatan umum dan daftar gambar", "TANPA SKALA")] + \
    [(f"GS-{4 + i:02d}", f"Denah struktur {lv}", "1:300") for i, lv in enumerate(LANTAI)] + \
    [("GS-11", "Potongan A-A (as B)", "1:300"), ("GS-12", "Potongan B-B (as 8)", "1:300"),
     ("GS-13", "Tabel dan penampang balok", "1:20"), ("GS-14", "Tabel kolom dan HBK", "1:25"),
     ("GS-15", "Dinding inti dan balok kopel", "1:50"), ("GS-16", "Tangga", "1:50"),
     ("GS-17", "Transfer tangki atap V1", "1:100"), ("GS-18", "Shaft dan lubang pelat", "1:50"),
     ("GS-19", "Angkur fasad V3", "1:20"), ("GS-20", "Potongan memanjang balok dan kolom", "1:50")]


def catatan_umum(status=None):
    from cad_lembar import Gambar
    dwg = DWG / "GS-03 Catatan Umum.dwg"
    sp = "SDS 0,386; SD1 0,459 (spesifik situs 4.1)"
    butir = [
        "Standar: SNI 2847:2019 (beton), SNI 1726:2019 (gempa),\nSNI 1727:2020 (beban), SNI 2052:2017 (baja tulangan).",
        "Mutu beton: kolom dan dinding inti fc' 35 MPa; balok, pelat,\ntangga fc' 30 MPa (4.5-4.8).",
        "Baja tulangan BjTS 420B (fy 420 MPa) untuk semua diameter.",
        "Selimut bersih: balok dan kolom 40 mm; pelat, dinding,\ntangga 20 mm (SNI 2847 Tabel 20.6.1.3.1).",
        f"Sistem ganda SRPMK + dinding struktural khusus: R 7, Ω0 2,5,\nCd 5,5; KDS D; Ie 1,5; {sp}.",
        "Kait gempa 135° dengan perpanjangan 6 db >= 75 mm pada\nsengkang dan ikat silang (SNI 2847 25.3.4, 18.6.4, 18.7.5).",
        "Sambungan lewatan balok di luar 2h dari muka kolom (18.6.3.3);\nkolom hanya di tengah tinggi bersih (18.7.4.3).",
        "Panjang penyaluran dan lewatan: tabel di kanan (bila syarat\nspasi/selimut tidak terpenuhi, hitung ulang 25.4.2.3).",
        "Sengkang di daerah lo kolom diteruskan melewati joint (HBK)\n(18.8.3.1); ukuran dan jarak lihat GS-14.",
        "Tahap 1 (K1): podium + menara s.d. kolom/inti LT5 di bawah\natap sementara; LT5-ATAP dan dek helipad menyusul.",
        "Kode unsur: B balok, BT transfer, BA anak tangki, BR rel chiller,\nK kolom, DG dinding geser, S pelat, SH shaft.",
        "Penampang dan potongan besi dari model BIM berbesi LOD 350\n(tahap4_besi); angka dari skrip desain 4.5-4.10.",
    ]
    with Gambar(100) as g:
        y = tabel(g, 0, 0, [8, 112], ["NO", "CATATAN UMUM STRUKTUR"], [[i + 1, t] for i, t in enumerate(butir)],
                  kiri=(1,))
        lds = ld_tabel()
        g.teks((0, y - 0.55), "PANJANG PENYALURAN TARIK ld DAN LEWATAN KELAS B (mm)", "S-TEKS", 1.8, tebal=True)
        tabel(g, 0, y - 0.8, [12, 18, 18, 18, 18, 18, 18], ["D", "ld f30", "ld f30\natas", "ld f35", "ld f35\natas",
                                                             "lew. B\nf30", "lew. B\nf35"],
              [[f"D{db}", r[0], r[1], r[2], r[3], lw[0], lw[2]] for db, r, lw in lds], kiri=())
        tabel(g, 13.0, 0, [16, 62, 22], ["NO", "JUDUL GAMBAR", "SKALA"], [list(r) for r in DAFTAR], kiri=(1,))
        _lembar_detail(g, "GS-03", "Catatan umum dan daftar gambar", "TANPA SKALA",
                       "Langkah 4.10: catatan umum set gambar struktur atas (setara DED)",
                       ["ld dan lewatan (mm) dari SNI 2847 Tabel 25.4.2.2 hal. 566 dan Tabel 25.5.2.1 hal. 586 "
                        "(ψe 1,0; λ 1,0; atas ψt 1,3; min 300 mm), dibulatkan ke atas 50 mm.",
                        "Set gambar Tahap 4; DED lengkap seluruh disiplin dirakit di Tahap 7."],
                       status, pusat=(11.0, -9.0), judul_kop="CATATAN UMUM")
        _simpan(g, dwg)
    return dwg


# ------------------------------------------------------------------ GS-11, GS-12 potongan dari model BIM
def potongan(no, nama, judul, grid, tunjuk, catatan, status=None):
    from cad_lembar import Gambar
    dwg = DWG / f"{no} {nama}.dwg"
    x0, z0, x1, z1 = batas_dxf(dxf(nama))
    with Gambar(SKALA_DENAH) as g:
        impor(g, dxf(nama))
        g.legenda_tambah("garis", "Unsur terpotong dan terlihat (model BIM)", tebal=0.5)
        g.legenda_tambah("garis", "Level lantai", garis="DASHED", tebal=0.18)
        for n_, xd in grid:
            g.as_grid(n_, (xd, z1 + 1.0), (xd, z1 + 3.5), r_kertas=3.0, dua_ujung=False)
        g.layer("S-LEVEL", 7, 0.18, "DASHED")
        lv_ada = [lv for lv in LANTAI if tb.LEVEL[lv] <= z1 + 0.01]
        for lv in lv_ada:
            z = tb.LEVEL[lv]
            g.pline([(x1 + 1.0, z), (x1 + 3.0, z)], "S-LEVEL")
            g.titik_tinggi((x1 + 3.4, z), f"{lv} {elev(lv)}", "S-ELEVASI")
        for a, b in zip(lv_ada[:-1], lv_ada[1:]):
            g.ukur((x1 + 9.0, tb.LEVEL[a]), (x1 + 9.0, tb.LEVEL[b]), (x1 + 9.0, (tb.LEVEL[a] + tb.LEVEL[b]) / 2),
                   rot=90)
        for panah, letak, s_ in tunjuk:
            g.tunjuk(panah, letak, s_, layer="S-TEKS")
        _lembar_detail(g, no, judul, f"1:{SKALA_DENAH}",
                       "Langkah 4.10: potongan dari model BIMCraft LOD 300 (4.9) diekspor DXF; anotasi CADCraft",
                       catatan, status, pusat=((x0 - 13 + x1 + 13) / 2, (z0 + z1 + 4) / 2),
                       judul_kop=judul.split(" (")[0].upper())
        g.skala_grafis(205, 22, 20, bagi=4)
        _simpan(g, dwg)
    return dwg


def potongan_a(status=None):
    return potongan("GS-11", "Potongan A-A", "Potongan A-A (as B, y 35)",
                    [(NAMA_X[i], x) for i, x in enumerate(tb.GRID_X)],
                    [((12.0, 15.0), (7.5, 15.6), "K1 750"), ((16.0, 17.1), (7.5, 19.6), "B2 350×600"),
                     ((20.0, 32.0), (7.5, 33.0), "K2 650"), ((36.0, 38.95), (7.5, 41.0), "DEK HEB 200")],
                    ["Bidang potong y 35 (as B) menghadap utara; dinding selatan inti lif x 50-58 terpotong.",
                     "Kode dan tulangan: balok GS-13, kolom GS-14, dinding inti GS-15; denah GS-04 s.d. GS-10.",
                     "Dek helipad baja di atas pelat atap: tumpuan HEB 200 [Asumsi], desain dek menyusul.",
                     "Elevasi terhadap BM-1 = +10,000; LT1 +12,85 (peil 3.3)."], status)


def potongan_b(status=None):
    return potongan("GS-12", "Potongan B-B", "Potongan B-B (as 8, x 68)",
                    [(NAMA_Y[j], 85.0 - y) for j, y in enumerate(tb.GRID_Y)],
                    [((14.0, 21.35), (0.5, 25.5), "BT1 600 × 1200"), ((10.0, 16.0), (0.5, 17.0), "K4 950 × 950"),
                     ((34.0, 32.0), (0.5, 35.5), "K2 650 × 650")],
                    ["Bidang potong x 68 (as 8) menghadap barat; sumbu mendatar = 85 - y (utara di kiri).",
                     "BT1 600 × 1200 memikul balok anak tangki BA (4.6); kolom K4 950 menerus LT1-LT3 (keputusan "
                     "Defsa 4.7).",
                     "Tangki 210 m³ di atap V1 +21,85 (pelat S2 t 250): GS-17. Kode lain: GS-13, GS-14.",
                     "Elevasi terhadap BM-1 = +10,000."], status)


# ------------------------------------------------------------------ GS-13 balok (penampang dari model LOD 350)
def _impor_di(g, nama, ox):
    """Impor DXF detail digeser ox m ke timur supaya beberapa potongan tidak saling menimpa di model space."""
    return g.cmd("import", {"path": str(dxf(nama)), "at": [ox * 1000, 0]})["imported"]


def _vp_baris(n, i, y0=40.0, y1=166.0, x0=28.0, x1=327.0):
    w = (x1 - x0) / n
    return (x0 + i * w + 1.5, y0), (x0 + (i + 1) * w - 1.5, y1)


def balok(status=None):
    from cad_lembar import Gambar
    d = data()
    rb, tepi, fn = d["balok"], d["tepi"], d["fasad"]["n"]
    dwg = DWG / "GS-13 Tabel Penampang Balok.dwg"
    baris, pilih = [], {}

    def sengk(x, s_):
        return f"{x['kaki']} kaki D{x['ds']}-{s_ * 1000:.0f}"

    def samping(x):
        return f"{x['samping']}D13/sisi" if x["samping"] else "-"

    def s_pakai(nama, x):
        t = tepi.get(nama)
        return t["s_baru"] if t and t["berubah"] else (x["s_sendi"], x["s_lap"])

    for x in rb["kelompok"]:
        nama = x["kelompok"]
        s1, s2 = s_pakai(nama, x)
        tanda = "*" if (s1, s2) != (x["s_sendi"], x["s_lap"]) else ""
        pilih[nama] = x
        baris.append([kode_balok(nama), nama, f"{x['b'] * 1000:.0f} × {x['h'] * 1000:.0f}", tul(x["atas"]),
                      tul(x["bawah"]), f"{x['atas_lap']}D{x['atas']['db']}", tul(x["bawah"]), sengk(x, s1) + tanda,
                      sengk(x, s2) + tanda, samping(x)])
    for kode, nama, x in (("BA", "anak tangki y 71", rb["tangki"]), ("BR", "rel chiller (8)", rb["chiller"])):
        baris.append([kode, nama, f"{x['b'] * 1000:.0f} × {x['h'] * 1000:.0f}", tul(x["atas"]), tul(x["bawah"]),
                      f"{x['atas_lap']}D{x['atas']['db']}", tul(x["bawah"]), sengk(x, x["s_sendi"]),
                      sengk(x, x["s_lap"]), samping(x)])
    bp, bm, bt = pilih["B-P dalam LT3"], pilih["B-M tepi LT4"], pilih["B-T induk tangki x 68"]
    lap = {"n": bp["atas_lap"], "db": bp["atas"]["db"], "lapis": 1}
    det = [("Det B1 Tumpuan", "B1 LT3 TUMPUAN", "B-P dalam LT3", bp["atas"], 0, "LT3"),
           ("Det B1 Lapangan", "B1 LT3 LAPANGAN", "B-P dalam LT3", lap, 1, "LT3"),
           ("Det B4 Tumpuan", "B4 LT4 TUMPUAN", "B-M tepi LT4", bm["atas"], 0, "LT4"),
           ("Det Bt1 Tumpuan", "BT1 TUMPUAN", "B-T induk tangki x 68", bt["atas"], 0, "LT3")]
    with Gambar(20) as g:
        yt = tabel(g, 0, 0, [12, 40, 22, 30, 30, 20, 30, 30, 30, 18],
                   ["KODE", "KELOMPOK", "b × h", "ATAS\nTUMPUAN", "BAWAH\nTUMPUAN", "ATAS\nLAP.", "BAWAH\nLAP.",
                    "SENGKANG\nSENDI (2h)", "SENGKANG\nLAPANGAN", "SAMPING"], baris, kiri=(1,))
        vps = []
        for i, (nama_dxf, jd, kel, atas, lapangan, lv) in enumerate(det):
            x = pilih[kel]
            ox = 100.0 * (i + 1)
            _impor_di(g, nama_dxf, ox)
            cx, zt, b, h = ox + 2.0, tb.LEVEL[lv], x["b"], x["h"]
            s1, s2 = s_pakai(kel, x)
            g.teks((cx, zt + 0.30), jd, "S-TEKS", 2.0, j="BC", tebal=True)
            g.ukur((cx - b / 2, zt - h - 0.08), (cx + b / 2, zt - h - 0.08), (cx, zt - h - 0.08), layer="S-UKURAN")
            g.ukur((cx - b / 2 - 0.12, zt), (cx - b / 2 - 0.12, zt - h), (cx - b / 2 - 0.12, zt - h / 2),
                   layer="S-UKURAN", rot=90)
            for k, s_ in enumerate((f"ATAS {tul(atas)}", f"BAWAH {tul(x['bawah'])}",
                                    f"SENGKANG {x['kaki']} KAKI D{x['ds']}-{(s2 if lapangan else s1) * 1000:.0f}")):
                g.teks((cx, zt - h - 0.25 - 0.08 * k), s_, "S-TEKS", 1.6, j="TC")
            p1, p2 = _vp_baris(len(det), i)
            vps.append((p1, p2, (cx * 1000, (zt - 0.62) * 1000), 20))
        g.legenda_tambah("garis", "Beton terpotong (garis tepi, model BIM LOD 350)", tebal=0.35)
        g.legenda_tambah("garis", "Besi dari model BIM (batang, sengkang)", tebal=0.25)
        lebar = sum([12, 40, 22, 30, 30, 20, 30, 30, 30, 18]) * 0.02
        _lembar_detail(g, "GS-13", "Tabel dan penampang balok", "1:20",
                       "Langkah 4.10: tabel dari desain balok 4.6; penampang = potongan model BIMCraft berbesi (LOD 350)",
                       ["SRPMK; fc' 30, BjTS 420B, selimut 40 mm. Lantai pada nama kelompok = tingkat balok.",
                        "Daerah sendi 2h dari muka kolom (18.6.4.1), sengkang pertama <= 50 mm dari muka (18.6.4.4); "
                        "lewatan di luar daerah sendi (18.6.3.3).",
                        f"* Balok tepi dirapatkan: torsi keseimbangan fasad V3 {id_(fn['t_tk'], 1)} kNm (keputusan Defsa 4.10).",
                        "Model BIM: kaki sengkang dalam tidak dimodelkan; atas baris 2 sepanjang L/3; balok as ke as "
                        "sehingga sengkang model menerus di joint. Jumlah kaki menurut tabel.",
                        "Atas lapangan menerus >= 1/4 As tumpuan (18.6.3.2). BT, BA, BR: GS-17; memanjang: GS-20."],
                       status, pusat=(lebar / 2, yt / 2), judul_kop="TABEL BALOK", vp=((28, 170), (327, 283)),
                       viewports=vps)
        _simpan(g, dwg)
    return dwg


# ------------------------------------------------------------------ GS-14 kolom dan HBK (penampang dari model LOD 350)
def kolom(status=None):
    from cad_lembar import Gambar
    d = data()
    dwg = DWG / "GS-14 Tabel Kolom HBK.dwg"
    baris, pilih = [], {}
    for x in d["kolom"]["kelompok"]:
        gs = x["geser"]
        pilih[x["kelompok"]] = x
        baris.append([kode_kolom(x["kelompok"]), x["kelompok"], f"{x['b'] * 1000:.0f}", f"{x['n_batang']}D{x['db']}",
                      f"{id_(x['rho'] * 100)} %", f"{gs['lo']:.0f}", f"D13-{gs['s_lo']}", f"{gs['kaki']} kaki",
                      f"D13-{gs['s_luar']}", id_(x["hbk"]["rasio"]) if x["hbk"] else "-",
                      id_(x["scwb_min"]["rasio"]) if x["scwb_min"] else "-"])
    lebar = [12, 26, 16, 20, 18, 14, 22, 16, 22, 16, 18]
    det = [("LT1", (36.0, 35.0), "K-P LT2", "K1 LT2"), ("LT4", (36.0, 35.0), "K-M LT5", "K2 LT5"),
           ("LT2", (60.0, 67.0), "K-T LT3", "K3 LT3"), ("LT2", (68.0, 67.0), "K-T68 LT3", "K4 LT3")]
    geser = {"LT1": 0.0, "LT2": 200.0, "LT4": 400.0}
    with Gambar(25) as g:
        yt = tabel(g, 0, 0, lebar, ["KODE", "KELOMPOK", "b (mm)", "TULANGAN", "ρ", "lo (mm)", "SENGKANG\ndaerah lo",
                                    "IKAT\n/ARAH", "SENGKANG\nluar lo", "GESER\nHBK", "ΣMnc/\nΣMnb"], baris, kiri=(1,))
        for lv in geser:
            _impor_di(g, f"Detail Denah {lv}", geser[lv])
        vps = []
        for i, (lv, (x0, y0), kel, jd) in enumerate(det):
            x = pilih[kel]
            cx, cy, b = x0 + geser[lv], y0, x["b"]
            g.teks((cx, cy + b / 2 + 0.30), jd, "S-TEKS", 2.0, j="BC", tebal=True)
            g.ukur((cx - b / 2, cy - b / 2 - 0.10), (cx + b / 2, cy - b / 2 - 0.10), (cx, cy - b / 2 - 0.10),
                   layer="S-UKURAN")
            for k, s_ in enumerate((f"{x['n_batang']}D{x['db']}", f"D13-{x['geser']['s_lo']} (lo) / -"
                                    f"{x['geser']['s_luar']}")):
                g.teks((cx, cy - b / 2 - 0.30 - 0.10 * k), s_, "S-TEKS", 1.6, j="TC")
            p1, p2 = _vp_baris(len(det), i, y1=170.0)
            vps.append((p1, p2, (cx * 1000, (cy - 0.25) * 1000), 25))
        g.legenda_tambah("garis", "Kolom terpotong (garis tepi, model BIM LOD 350)", tebal=0.35)
        g.legenda_tambah("garis", "Besi kolom dari model BIM", tebal=0.25)
        _lembar_detail(g, "GS-14", "Tabel kolom dan HBK", "1:25",
                       "Langkah 4.10: tabel dari desain kolom 4.7; penampang = denah model BIMCraft berbesi (LOD 350)",
                       ["fc' 35, BjTS 420B, selimut 40 mm; sengkang dan ikat silang D13 berkait gempa 135°.",
                        "lo dari muka joint (18.7.5.1); sengkang daerah lo diteruskan melewati HBK (18.8.3.1).",
                        "Lewatan hanya di tengah tinggi bersih kolom (18.7.4.3); panjang lihat GS-03.",
                        "Geser HBK dan ΣMnc/ΣMnb: rasio terburuk tiap kelompok (4.7; syarat <= 1,0 dan >= 1,2).",
                        "Model BIM memasang ikat silang di semua batang tengah (jumlah perlu menurut tabel). K3/K4 "
                        "transfer tangki menerus LT1-LT3 (keputusan Defsa 4.7)."],
                       status, pusat=(sum(lebar) * 0.025 / 2, yt / 2), judul_kop="TABEL KOLOM DAN HBK",
                       vp=((28, 176), (327, 283)), viewports=vps)
        _simpan(g, dwg)
    return dwg


# ------------------------------------------------------------------ GS-20 potongan memanjang balok dan kolom
def memanjang(status=None):
    from cad_lembar import Gambar
    d = data()
    bal = {x["kelompok"]: x for x in d["balok"]["kelompok"]}
    kol = {x["kelompok"]: x for x in d["kolom"]["kelompok"]}
    x, k = bal["B-P dalam LT3"], kol["K-P LT3"]
    dwg = DWG / "GS-20 Potongan Memanjang Balok Kolom.dwg"
    z3, z2 = tb.LEVEL["LT3"], tb.LEVEL["LT2"]
    a0, a1 = 28.0 - 26.0, 36.0 - 26.0          # as 3 dan 4 pada sumbu potongan (x - 26)
    hk = tb.KOLOM_POD / 2
    with Gambar(50) as g:
        impor(g, dxf("Memanjang B1"))
        for nama, xa in (("3", a0), ("4", a1)):
            g.as_grid(nama, (xa, z3 + 0.9), (xa, z3 + 1.5), r_kertas=3.0, dua_ujung=False)
        for lv, z in (("LT2", z2), ("LT3", z3)):
            g.titik_tinggi((a1 + 1.4, z + 0.05), f"{lv} {elev(lv)}", "S-ELEVASI", teks_at=(a1 + 1.6, z + 0.15))
        zs = z3 + 0.55
        l2h = 2 * x["h"]
        g.ukur((a0 + hk, zs), (a0 + hk + l2h, zs), (a0 + hk + l2h / 2, zs))
        g.ukur((a0 + hk + l2h, zs), (a1 - hk - l2h, zs), ((a0 + a1) / 2, zs))
        g.ukur((a1 - hk - l2h, zs), (a1 - hk, zs), (a1 - hk - l2h / 2, zs))
        lo = k["geser"]["lo"] / 1000
        zb = z3 - x["h"]
        g.ukur((a0 - hk - 0.35, zb), (a0 - hk - 0.35, zb - lo), (a0 - hk - 0.35, zb - lo / 2), rot=90)
        g.ukur((a0 - hk - 0.35, z2), (a0 - hk - 0.35, z2 + lo), (a0 - hk - 0.35, z2 + lo / 2), rot=90)
        xl = a0 + 3.0
        s1, s2 = x["s_sendi"] * 1000, x["s_lap"] * 1000
        for panah, z, s_ in (((a0 + hk + 0.5, z3 - 0.06), z3 - 1.1, f"ATAS TUMPUAN {tul(x['atas'])}"),
                             ((4.4, z3 - 0.06), z3 - 1.5, f"ATAS LAPANGAN {x['atas_lap']}D{x['atas']['db']} MENERUS"),
                             ((4.0, zb + 0.06), z3 - 1.9, f"BAWAH {tul(x['bawah'])} MENERUS"),
                             ((a0 + hk + 0.8, zb + 0.3), z3 - 2.3,
                              f"SENGKANG {x['kaki']} KAKI D{x['ds']}-{s1:.0f} (2h) / -{s2:.0f}"),
                             ((a0, z2 + 1.8), z3 - 2.7, f"KOLOM K1 LT3 {k['n_batang']}D{k['db']}, D13-"
                                                       f"{k['geser']['s_lo']} (lo) / -{k['geser']['s_luar']}")):
            g.tunjuk(panah, (xl, z), s_, "S-TEKS")
        g.legenda_tambah("garis", "Beton terpotong (garis tepi, model BIM LOD 350)", tebal=0.35)
        g.legenda_tambah("garis", "Besi dari model BIM", tebal=0.25)
        _lembar_detail(g, "GS-20", "Potongan memanjang balok B1 dan kolom K1", "1:50",
                       "Langkah 4.10: potongan model BIMCraft berbesi (LOD 350) pada as C (y 43), as 3-4, LT2-LT3",
                       ["Balok B1 LT3 (B-P dalam LT3) dan kolom K1 LT3 (K-P LT3); angka dari 4.6-4.7.",
                        "Daerah sendi 2h dari muka kolom; lo kolom dari muka balok dan lantai (18.7.5.1); sengkang lo "
                        "menerus melewati joint (18.8.3.1).",
                        "Model: tulangan atas baris 2 sepanjang L/3 dari ujung [Asumsi detail; putus >= ld + d, "
                        "dicek di BBS Tahap 7]. Lewatan di luar sendi.",
                        "Bidang potong y 43 menghadap utara; sumbu mendatar = x - 26."],
                       status, pusat=((a0 + a1) / 2 + 0.6, (z2 + z3) / 2 + 0.2), judul_kop="POTONGAN MEMANJANG B1")
        _simpan(g, dwg)
    return dwg


# ------------------------------------------------------------------ GS-15 dinding inti dan balok kopel
def _kotak(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def dinding(status=None):
    from cad_lembar import Gambar
    import tahap4_dinding as td
    d = data()["dinding"]
    dwg = DWG / "GS-15 Dinding Inti Balok Kopel.dwg"
    baris = []
    for x in d["kelompok"]:
        t, hz, tr = x["tul"], x["horiz"], x["batas"].get("trans", {})
        pk = f"D{tr['db']}-{tr['s']:.0f}/{tr['s_luar']:.0f}" if tr.get("s") else "-"
        baris.append([KODE_DINDING[x["kelompok"]], x["lv"], f"D{t[0]}-{t[1]}", f"D{hz[1]}-{hz[2]}", f"{t[2]}D{t[3]}",
                      pk, id_(x["batas"]["sigma"])])
    kop = []
    for g_, k in d["kopel"].items():
        tulk = (f"diagonal {k['diag'][0]}D{k['diag'][1]}/kelompok" if k["diagonal"]
                else f"{k['batang'][0]}D{k['batang'][1]} + D{k['db_s']}-{k['s']} ({k['kaki']} kaki)")
        kop.append([KODE_DINDING[g_], f"{k['ln'] * 1000:.0f} × {k['h'] * 1000:.0f}", f"{k['Vu']:,.0f}".replace(",", "."),
                    tulk])
    wtm = next(x for x in d["kelompok"] if x["kelompok"] == "W-TM" and x["lv"] == "LT2")
    kl = d["kopel"]["W-L"]
    with Gambar(50) as g:
        tabel(g, 0, 0, [12, 14, 24, 24, 22, 30, 18],
              ["KODE", "LANTAI", "VERTIKAL\n(2 lapis)", "HORIZONTAL\n(2 lapis)", "ZONA BATAS\ntiap lokasi",
               "PENGEKANG\nsendi/luar", "σ maks\n(MPa)"], baris, kiri=())
        tabel(g, 7.8, 0, [12, 26, 16, 54], ["KODE", "ln × h (mm)", "Vu (kN)", "TULANGAN BALOK KOPEL"], kop, kiri=(3,))
        # denah inti tangga DG2 (LT2) dengan zona batas dan tulangan badan
        T = td.T
        dx, dy = td.DIM["T"]
        cx, cy = 10.7, -6.0
        xo0, xo1, yo0, yo1 = cx - dx / 2 - T / 2, cx + dx / 2 + T / 2, cy - dy / 2 - T / 2, cy + dy / 2 + T / 2
        xi0, xi1, yi0, yi1 = xo0 + T, xo1 - T, yo0 + T, yo1 - T
        pintu = td.PINTU["T"][0][1]
        g.layer("S-DINDING", 7, 0.5)
        for k in (_kotak(xo0, yi1, xo1, yo1), _kotak(xo0, yi0, xi0, yi1), _kotak(xi1, yi0, xo1, yi1),
                  _kotak(xo0, yo0, cx - pintu / 2, yi0), _kotak(cx + pintu / 2, yo0, xo1, yi0)):
            g.arsir(k, "S-DINDING", "ANSI31", skala_pola=0.5)
        g.layer("S-ZONA-BATAS", 7, 0.5)
        n_b, db_b = wtm["tul"][2], wtm["tul"][3] / 1000
        zona = [(xo0, yo1 - T, xo0 + 0.6, yo1), (xo1 - 0.6, yo1 - T, xo1, yo1), (xo0, yo0, xo0 + 0.6, yi0),
                (xo1 - 0.6, yo0, xo1, yi0), (cx - pintu / 2 - 0.6, yo0, cx - pintu / 2, yi0),
                (cx + pintu / 2, yo0, cx + pintu / 2 + 0.6, yi0)]
        for z0x, z0y, z1x, z1y in zona:
            g.pline(_kotak(z0x, z0y, z1x, z1y), "S-ZONA-BATAS", tutup=True)
            per = math.ceil(n_b / 2)
            for yy in (z0y + 0.07, z1y - 0.07):
                _baris_batang(g, z0x + 0.07, z1x - 0.07, yy, per, db_b, "S-TULANGAN")
        g.layer("S-TUL-BADAN", 7, 0.25, "HIDDEN")
        for o in (0.05, T - 0.05):
            g.pline(_kotak(xo0 + o, yo0 + o, xo1 - o, yo1 - o), "S-TUL-BADAN", tutup=True)
        g.ukur((xo0, yo1 + 0.4), (xo1, yo1 + 0.4), (cx, yo1 + 0.4))
        g.ukur((xo0 - 0.4, yo0), (xo0 - 0.4, yo1), (xo0 - 0.4, cy), rot=90)
        g.ukur((cx - pintu / 2, yo0 - 0.4), (cx + pintu / 2, yo0 - 0.4), (cx, yo0 - 0.4))
        g.teks((cx, yo1 + 1.1), "DENAH DG2 INTI TANGGA MENARA (LT2)", "S-TEKS", 2.0, j="BC", tebal=True)
        g.tunjuk((xo0 + 0.3, yo0 + 0.17), (7.9, -10.0), f"ZONA BATAS {n_b}D{wtm['tul'][3]} TIAP LOKASI", "S-TEKS")
        g.tunjuk((xo1 - 0.05, cy), (11.6, -10.6), f"BADAN D{wtm['tul'][0]}-{wtm['tul'][1]} V, "
                 f"D{wtm['horiz'][1]}-{wtm['horiz'][2]} H, 2 LAPIS", "S-TEKS")
        g.tunjuk((cx, yo0 - 0.1), (9.0, -11.2), f"PINTU {pintu:.1f} × {td.H_PINTU:.1f} m [ASUMSI 4.8]".replace(".", ","),
                 "S-TEKS")
        # tampak balok kopel DG1 (inti lif) dengan tulangan diagonal
        w, hk, hp = kl["w"], kl["h"], td.H_PINTU
        f0, xa = -10.6, 1.4
        xb = xa + w
        g.layer("S-BETON", 7, 0.5)
        g.pline([(xa - 0.9, f0), (xa, f0), (xa, f0 + hp), (xb, f0 + hp), (xb, f0), (xb + 0.9, f0)], "S-BETON")
        g.pline([(xa - 0.9, f0 + hp + hk), (xb + 0.9, f0 + hp + hk)], "S-BETON")
        g.layer("S-PUTUS", 7, 0.18, "PHANTOM")
        for xv in (xa - 0.9, xb + 0.9):
            g.pline([(xv, f0), (xv, f0 + hp + hk)], "S-PUTUS")
        g.layer("S-TULANGAN", 7, 0.5)
        la = 0.7
        for (p, q) in (((xa, f0 + hp + 0.3), (xb, f0 + hp + hk - 0.3)), ((xa, f0 + hp + hk - 0.3), (xb, f0 + hp + 0.3))):
            ux, uy = q[0] - p[0], q[1] - p[1]
            n_ = math.hypot(ux, uy)
            ux, uy = ux / n_, uy / n_
            for o in (-0.1, 0.1):
                g.pline([(p[0] - ux * la - uy * o, p[1] - uy * la + ux * o), (q[0] + ux * la - uy * o,
                                                                               q[1] + uy * la + ux * o)], "S-TULANGAN")
        g.ukur((xa, f0 - 0.4), (xb, f0 - 0.4), ((xa + xb) / 2, f0 - 0.4))
        g.ukur((xb + 1.3, f0 + hp), (xb + 1.3, f0 + hp + hk), (xb + 1.3, f0 + hp + hk / 2), rot=90)
        g.ukur((xb + 1.3, f0), (xb + 1.3, f0 + hp), (xb + 1.3, f0 + hp / 2), rot=90)
        g.teks(((xa + xb) / 2, f0 + hp + hk + 0.35), "TAMPAK BALOK KOPEL DG1 (INTI LIF)", "S-TEKS", 2.0, j="BC",
               tebal=True)
        g.tunjuk(((xa + xb) / 2, f0 + hp + hk / 2), (xb + 1.9, f0 + hp + hk + 0.15),
                 f"{kl['diag'][0]}D{kl['diag'][1]} TIAP KELOMPOK DIAGONAL", "S-TEKS")
        g.legenda_tambah("arsir", "Dinding beton terpotong", pola="ANSI31", skala_pola=0.5)
        g.legenda_tambah("garis", "Zona batas (18.10.6.5)", tebal=0.5)
        g.legenda_tambah("garis", "Tulangan badan dua lapis", garis="HIDDEN", tebal=0.25)
        _lembar_detail(g, "GS-15", "Dinding inti dan balok kopel", "1:50",
                       "Langkah 4.10: tulangan dari desain dinding geser dan balok kopel 4.8 (tahap4_dinding.rancang)",
                       ["fc' 35, BjTS 420B, t 350 mm, selimut 20 mm; DG1 inti lif 8 × 8 m, DG2 tangga menara, DG3 "
                        "tangga podium (4 × 6 m).",
                        "Zona batas di tiap sudut dan kedua sisi tiap pintu, panjang 600 mm; elemen batas khusus tidak "
                        "perlu (σ < 0,2 fc' = 7,0 MPa; keputusan Defsa 4.8).",
                        "Pengekang zona batas 18.10.6.5(a) bila ρ > 2,8/fy; '-' = tidak perlu. Horizontal dikait di "
                        "tepi (18.10.6.5(b)).",
                        "Kopel diagonal: pengekang tiap kelompok 18.10.7.4, penjangkaran 1,25 ld ke dinding (rinci "
                        "Tahap 7). Pintu inti [Asumsi 4.8]."],
                       status, pusat=(7.55, -5.5), judul_kop="DINDING INTI DAN KOPEL")
        _simpan(g, dwg)
    return dwg


# ------------------------------------------------------------------ GS-16 tangga (potongan dari model BIM)
def tangga_lembar(status=None):
    from cad_lembar import Gambar
    import tahap4_dinding as td
    d = data()["dinding"]["tangga"]
    dwg = DWG / "GS-16 Tangga.dwg"
    din = bim.dalam_inti(TANGGA)
    y_awal = din.bounds[1] - 1.5          # awal garis potong (sumbu mendatar DXF = y - y_awal)
    yi0, yi1 = din.bounds[1] - y_awal, din.bounds[3] - y_awal
    with Gambar(50) as g:
        impor(g, dxf("Potongan Tangga"))
        c = td.SEL / 1000 + 0.0065
        s = td.tangga(4.5)
        z0 = tb.LEVEL["LT1"]
        ya, yb = yi0 + s["bordes"], yi0 + s["bordes"] + s["lf"]
        g.ukur((yi0, z0 - 0.9), (ya, z0 - 0.9), ((yi0 + ya) / 2, z0 - 0.9))
        g.ukur((ya, z0 - 0.9), (yb, z0 - 0.9), ((ya + yb) / 2, z0 - 0.9))
        g.ukur((yb, z0 - 0.9), (yi1, z0 - 0.9), ((yb + yi1) / 2, z0 - 0.9))
        for lv in ("LT1", "LT2", "LT3"):
            g.titik_tinggi((yi1 + 0.9, tb.LEVEL[lv] + 0.12), f"{lv} {elev(lv)}", "S-ELEVASI",
                           teks_at=(yi1 + 1.1, tb.LEVEL[lv] + 0.22))
        zt = z0 + 2.25
        g.tunjuk(((ya + yb) / 2, z0 + 1.0), (yi1 + 0.9, z0 + 3.4), f"PELAT TANGGA t {s['t'] * 1000:.0f}", "S-TEKS")
        g.tunjuk((ya + 0.6, z0 - s["t"] + c + 0.6 * math.tan(math.atan(2.25 / s["lf"]))), (yi1 + 0.9, z0 + 0.9),
                 f"BAWAH D{s['db']}-{s['s_pos']}", "S-TEKS")
        g.tunjuk((yb, zt - c), (yi1 + 0.9, zt + 0.6), f"ATAS D{s['db']}-{s['s_neg']}", "S-TEKS")
        rows = []
        for kunci, nama, f in (("n_r", "Jumlah tanjakan per lengan", "{:.0f}"), ("r", "Tanjakan (mm)", "r"),
                               ("going", "Injakan (mm)", "r"), ("theta", "Sudut lengan (°)", "{:.1f}"),
                               ("t", "Tebal pelat (mm)", "r"), ("lebar", "Lebar lengan (mm)", "r"),
                               ("Mpos", "Mu+ (kNm/m)", "{:.1f}"), ("s_pos", "Bawah D13 jarak (mm)", "{:.0f}"),
                               ("s_neg", "Atas D13 jarak (mm)", "{:.0f}"), ("Vu", "Vu (kN/m)", "{:.1f}"),
                               ("phiVc", "φVc (kN/m)", "{:.1f}")):
            v = [d[4.2][kunci], d[4.5][kunci]]
            rows.append([nama] + [f"{x * 1000:.0f}" if f == "r" else f.format(x).replace(".", ",") for x in v])
        tabel(g, 60.0, 30.0, [42, 18, 18], ["URAIAN", "h 4,2 m", "h 4,5 m"], rows, kiri=(0,))
        g.legenda_tambah("garis", "Pelat tangga dan bordes terpotong (garis tepi, model BIM LOD 350)", tebal=0.35)
        g.legenda_tambah("garis", "Besi tangga dari model BIM", tebal=0.25)
        vp_utama = ((28, 38), (232, 283))
        _lembar_detail(g, "GS-16", "Tangga", "1:50",
                       f"Langkah 4.10: potongan inti {TANGGA.lower()} dari model BIMCraft (4.9); tulangan 4.8",
                       ["Potongan pada lengan pertama (x tengah lengan), menghadap timur; sumbu mendatar = y - "
                        f"{id_(y_awal)}.",
                        "Pelat tangga satu arah antar-dinding inti (ℓ 6,0 m), fc' 30, selimut 20, ℓ/24 (Tabel "
                        "7.3.1.1); tulangan dari 4.8 `tangga(h)`.",
                        "Tulangan pembagi As min 0,0018 Ag (7.6.1.1); atas dijangkarkan ke dinding inti (ldh).",
                        "Besi dari model BIM (pelat miring: tulangan mengikuti kemiringan); bengkok di BBS Tahap 7."],
                       status, pusat=((yi0 + yi1) / 2 + 1.9, (tb.LEVEL["LT1"] + tb.LEVEL["LT3"]) / 2 - 0.2),
                       judul_kop="TANGGA", vp=vp_utama,
                       viewports=[((238, 150), (327, 283), (62000.0 - 260.0, 30000.0 - 2400.0), 50)])
        _simpan(g, dwg)
    return dwg


# ------------------------------------------------------------------ GS-17 transfer tangki atap V1
def transfer(status=None):
    from cad_lembar import Gambar
    import tahap4_balok as bk
    import tahap4_pelat as tp
    d = data()
    rb = d["balok"]
    dwg = DWG / "GS-17 Transfer Tangki.dwg"
    uk = {k: (b * 1000, h * 1000) for k, (b, h) in rb["ukuran"].items()}
    with Gambar(100) as g:
        impor(g, dxf("Denah LT3"))
        g.layer("A-ALAT", 7, 0.25, "HIDDEN")
        tk = tp.TANGKI
        g.pline(_kotak(tk["x"][0], tk["y"][0], tk["x"][1], tk["y"][1]), "A-ALAT", tutup=True)
        for y0 in bim.CHILLER_Y0:
            g.pline(_kotak(bk.CHILLER_X[0], y0, bk.CHILLER_X[-1], y0 + 2.3), "A-ALAT", tutup=True)
        g.legenda_tambah("garis", "Tangki 210 m³ dan chiller (alat, Data MEP)", garis="HIDDEN", tebal=0.25)
        g.legenda_tambah("garis", "Balok, kolom, pelat (model BIM)", tebal=0.35)
        g.layer("S-TEKS", 7, 0.18)
        bt1, bt2, bt3 = (uk["B-T induk tangki x 68"], uk["B-T induk tangki x 60/76"], uk["B-T induk tangki y 67"])
        g.teks((67.4, 70.0), "BT1 %.0f × %.0f" % bt1, "S-TEKS", 1.8, j="BC", rot=90)
        g.teks((59.5, 70.0), "BT2 %.0f × %.0f" % bt2, "S-TEKS", 1.8, j="BC", rot=90)
        g.teks((75.5, 70.0), "BT2 %.0f × %.0f" % bt2, "S-TEKS", 1.8, j="BC", rot=90)
        g.teks((64.0, 66.55), "BT3 %.0f × %.0f" % bt3, "S-TEKS", 1.8, j="TC")
        g.teks((72.0, 66.55), "BT3 %.0f × %.0f" % bt3, "S-TEKS", 1.8, j="TC")
        ba, br = rb["tangki"], rb["chiller"]
        g.teks((64.0, 71.35), "BA %.0f × %.0f" % (ba["b"] * 1000, ba["h"] * 1000), "S-TEKS", 1.8, j="BC")
        g.teks((64.0, 68.3), f"TANGKI 210 m³ ({id_(rb['tangki']['qt'], 1)} kPa), PELAT S2 t 250", "S-TEKS", 1.8, j="BC")
        g.tunjuk((75.0, bim.REL_Y[-1]), (79.0, 64.6), "BR %.0f × %.0f (8 REL)" % (br["b"] * 1000, br["h"] * 1000),
                 "S-TEKS")
        g.tunjuk((bk.CHILLER_X[-1] - 0.5, bim.CHILLER_Y0[2] + 1.0), (79.0, 60.4), "CHILLER 4 UNIT", "S-TEKS")
        for x, y, kd in ((60, 67, "K3 800"), (60, 75, "K3 800"), (76, 67, "K3 800"), (76, 75, "K3 800"),
                         (68, 67, "K4 950"), (68, 75, "K4 950")):
            g.teks((x + 0.6, y - 0.6), kd, "S-TEKS", 1.8, j="L")
        for i, x in ((6, 60.0), (7, 68.0), (8, 76.0), (9, 84.0)):
            g.as_grid(NAMA_X[i], (x, 75.6), (x, 76.6), r_kertas=3.0, dua_ujung=False)
        for j, y in ((4, 59.0), (5, 67.0), (6, 75.0)):
            g.as_grid(NAMA_Y[j], (84.6, y), (85.3, y), r_kertas=3.0, dua_ujung=False)
        g.ukur((60.0, 78.6), (68.0, 78.6), (64.0, 78.6))
        g.ukur((68.0, 78.6), (76.0, 78.6), (72.0, 78.6))
        g.ukur((57.0, 67.0), (57.0, 75.0), (57.0, 71.0), rot=90)
        g.titik_tinggi((57.6, 76.4), "+21,85 ATAP V1", "S-ELEVASI")
        rd = max(ba["R_D"])
        _lembar_detail(g, "GS-17", "Transfer tangki atap V1", "1:100",
                       "Langkah 4.10: denah atap V1 dari model BIMCraft (4.9); ukuran balok dan kolom 4.6-4.7",
                       [f"Tangki 210 m³ (x 60-72, y 67-73) di atas pelat S2 t 250 dan balok anak BA y 71; reaksi BA "
                        f"ke BT1 ±{rd:,.0f} kN (D, 4.6).".replace(",", "."),
                        "BT1 x 68 600 × 1200 tanpa kolom tambahan (keputusan Defsa 4.6); BT2 x 60/76, BT3 y 67.",
                        "Kolom K4 950 (x 68) dan K3 800 (x 60/76) menerus LT1-LT3 (keputusan Defsa 4.7).",
                        "Rel chiller BR 8 batang [Asumsi tata letak 4.6]; tulangan: GS-13 dan GS-14.",
                        "Ukuran dalam meter."],
                       status, pusat=(71.0, 70.0), judul_kop="TRANSFER TANGKI")
        g.skala_grafis(205, 22, 5, bagi=5)
        g.panah_utara(318, 262, 10)
        _simpan(g, dwg)
    return dwg


# ------------------------------------------------------------------ GS-18 shaft dan lubang pelat
def shaft(status=None):
    from cad_lembar import Gambar
    import tahap4_pelat as tp
    dwg = DWG / "GS-18 Shaft Lubang Pelat.dwg"
    tambah = {b["kode"]: b for b in tp.tulangan_bukaan()}
    with Gambar(50) as g:
        impor(g, dxf("Denah LT2"))
        g.layer("S-SHAFT-LAMA", 7, 0.25, "HIDDEN")
        g.pline(_kotak(59.0, 41.8, 61.4, 44.2), "S-SHAFT-LAMA", tutup=True)
        g.legenda_tambah("garis", "Posisi SH-4 lama (data owner, clash 4.9)", garis="HIDDEN", tebal=0.25)
        g.layer("S-TULANGAN", 7, 0.35)
        x0, x1, y0, y1 = 60.6, 63.0, 43.6, 46.0
        for p, q in (((x0 - 0.6, y0 - 0.1), (x1 + 0.6, y0 - 0.1)), ((x0 - 0.6, y1 + 0.1), (x1 + 0.6, y1 + 0.1)),
                     ((x0 - 0.1, y0 - 0.6), (x0 - 0.1, y1 + 0.6)), ((x1 + 0.1, y0 - 0.6), (x1 + 0.1, y1 + 0.6))):
            g.pline([p, q], "S-TULANGAN")
        g.legenda_tambah("garis", "Tulangan tambahan tepi bukaan D13", tebal=0.35)
        g.ukur((60.0, 47.3), (x0, 47.3), ((60.0 + x0) / 2, 47.3))
        g.ukur((x0, 47.3), (x1, 47.3), ((x0 + x1) / 2, 47.3))
        g.ukur((64.4, 43.0), (64.4, y0), (64.4, (43.0 + y0) / 2), rot=90)
        g.ukur((64.4, y0), (64.4, y1), (64.4, (y0 + y1) / 2), rot=90)
        g.as_grid(NAMA_X[6], (60.0, 48.4), (60.0, 49.2), r_kertas=3.0, dua_ujung=False)
        g.as_grid(NAMA_Y[2], (57.4, 43.0), (56.9, 43.0), r_kertas=3.0, dua_ujung=False)
        g.tunjuk((61.0, 45.5), (61.6, 49.7), "SH-4 2,40 × 2,40 (LT2-LT3)", "S-TEKS")
        g.tunjuk((59.6, 42.4), (57.3, 40.2), "POSISI LAMA", "S-TEKS")
        g.tunjuk((x1 + 0.1, y0 + 0.5), (63.6, 40.2), f"TAMBAHAN {tambah['SH-4']['tambah_sisi_a']}D13 TIAP SISI",
                 "S-TEKS")
        g.teks((60.5, 42.55), "K1 750", "S-TEKS", 1.8, j="L")
        rows = []
        for kode, sx0, sx1, sy0, sy1, a, c in bim.SHAFT:
            t_ = tambah[kode]
            rows.append([kode, f"{id_(sx0, 1)}-{id_(sx1, 1)}", f"{id_(sy0, 1)}-{id_(sy1, 1)}", f"{a}-{c}",
                         f"{t_['tambah_sisi_a']} / {t_['tambah_sisi_b']} D13"])
        tabel(g, 100.0, 50.0, [12, 22, 22, 20, 24], ["KODE", "x (m)", "y (m)", "TINGKAT", "TAMBAHAN\nsisi a/b"],
              rows, kiri=())
        _lembar_detail(g, "GS-18", "Shaft dan lubang pelat", "1:50",
                       "Langkah 4.10: denah LT2 di sekitar SH-4 dari model BIMCraft (4.9); tabel shaft Data MEP",
                       ["SH-4 digeser dari x 59,0-61,4, y 41,8-44,2 (menabrak kolom 7/C, T-85) ke x 60,6-63,0, "
                        "y 43,6-46,0 (keputusan Defsa 20 Nov 2026); kabarkan ke owner/MEP.",
                        "Tulangan tambahan tepi bukaan = tulangan terpotong, minimum 2D13 tiap sisi, diteruskan ld "
                        "melewati sudut (4.5, praktik Pasal 8.5.4.2 [Asumsi]).",
                        "Lubang pelat lain mengikuti koordinat tabel; posisi dicek clash 4.9 (0 clash)."],
                       status, pusat=(61.0, 44.6), judul_kop="SHAFT DAN LUBANG PELAT", vp=((28, 38), (220, 283)),
                       viewports=[((226, 160), (327, 283), (100000.0 + 2550.0, 50000.0 - 1500.0), 50)])
        _simpan(g, dwg)
    return dwg


# ------------------------------------------------------------------ GS-19 angkur fasad V3
def fasad(status=None):
    from cad_lembar import Gambar
    n = data()["fasad"]["n"]
    dwg = DWG / "GS-19 Angkur Fasad V3.dwg"
    e_t, d_fs, L_ov = n["e_tepi"], n["d_fs"], n["L_ov"]
    with Gambar(20) as g:
        for X, judul, bt in ((0.0, "POTONGAN KONSOL U-S (KACA + OVERSTEK)", False),
                             (3.0, "POTONGAN KONSOL B-T (TERAKOTA)", True)):
            g.layer("S-BETON", 7, 0.5)
            g.arsir([(X - 0.8, 0), (X + e_t, 0), (X + e_t, -0.6), (X - e_t, -0.6), (X - e_t, -0.2), (X - 0.8, -0.2)],
                    "S-BETON", "ANSI31", skala_pola=0.4)
            g.layer("S-KOLOM-BLK", 7, 0.18, "HIDDEN")
            g.pline([(X + 0.375, 0.5), (X + 0.375, -1.3)], "S-KOLOM-BLK")
            g.layer("S-BAJA", 7, 0.5)
            g.pline(_kotak(X + e_t, -0.42, X + e_t + 0.02, -0.18), "S-BAJA", tutup=True)
            for za in (-0.225, -0.375):
                g.pline([(X + e_t + 0.02, za), (X + e_t - 0.15, za)], "S-BAJA")
                g.pline([(X + e_t - 0.15, za - 0.02), (X + e_t - 0.15, za + 0.02)], "S-BAJA")
            ujung = d_fs + (0.1 if bt else L_ov)
            g.pline(_kotak(X + e_t + 0.02, -0.35, X + ujung, -0.25), "S-BAJA", tutup=True)
            g.layer("A-FASAD", 7, 0.35)
            if bt:
                g.arsir(_kotak(X + d_fs - 0.1, -0.25, X + d_fs + 0.1, 0.5), "A-FASAD", "ANSI37", skala_pola=0.4)
                g.pline([(X + d_fs - 0.1, -1.3), (X + d_fs - 0.1, -0.35)], "A-FASAD")
                g.pline([(X + d_fs + 0.1, -1.3), (X + d_fs + 0.1, -0.35)], "A-FASAD")
            else:
                g.pline(_kotak(X + d_fs + 0.02, -0.25, X + d_fs + L_ov, -0.15), "A-FASAD", tutup=True)
                g.pline([(X + d_fs - 0.015, -1.3), (X + d_fs - 0.015, -0.35)], "A-FASAD")
                g.pline([(X + d_fs + 0.015, -1.3), (X + d_fs + 0.015, -0.35)], "A-FASAD")
            g.ukur((X, 0.35), (X + e_t, 0.35), (X + e_t / 2, 0.35))
            g.ukur((X + e_t, 0.35), (X + d_fs, 0.35), (X + (e_t + d_fs) / 2, 0.35))
            if not bt:
                g.ukur((X + d_fs, 0.35), (X + d_fs + L_ov, 0.35), (X + d_fs + L_ov / 2, 0.35))
            g.ukur((X - 0.05, -0.225), (X - 0.05, -0.375), (X - 0.05, -0.3), rot=90)
            g.teks((X + 0.25, 0.75), judul, "S-TEKS", 2.0, j="BC", tebal=True)
            g.tunjuk((X + e_t - 0.08, -0.225), (X - 0.95, -0.85), "4 M16 hef 150", "S-TEKS")
            g.tunjuk((X, -0.5), (X - 0.95, -1.05), "BALOK TEPI 350 × 600", "S-TEKS")
            if bt:
                g.tunjuk((X + d_fs, 0.2), (X + 0.9, 0.45), "BLOK TERAKOTA 200", "S-TEKS")
                g.tunjuk((X + 0.5, -0.3), (X + 0.9, -0.7), f"SIKU PENUMPU @ {id_(n['s_tk'], 1)} m [ASUMSI]", "S-TEKS")
            else:
                g.tunjuk((X + d_fs + 0.5, -0.2), (X + 1.0, 0.1), "OVERSTEK HOLLOW + ACP", "S-TEKS")
                g.tunjuk((X + d_fs, -0.9), (X + 0.9, -1.15), "KACA + KUSEN", "S-TEKS")
                g.tunjuk((X + 1.0, -0.3), (X + 1.2, -0.65), f"KONSOL BAJA @ {id_(n['s_ov'], 1)} m [ASUMSI]", "S-TEKS")
        rows = [
            ["D per konsol: V (kN) / M (kNm)", f"{id_(n['ns_DV'])} / {id_(n['ns_DM'])}",
             f"{id_(n['tk_DV'])} / {id_(n['tk_DM'])}"],
            ["Nu baris atas maks non-gempa (kN)", id_(n["ns_Nu"]), id_(n["tk_Nu"])],
            ["Nu baris atas maks gempa (kN)", id_(n["ns_NuE"]), id_(n["tk_NuE"])],
            ["Vu maks (kN)", id_(n["ns_Vu"]), id_(n["tk_Vu"])],
            ["φNsa 2 angkur / φNcbg (kN)", f"{id_(n['phiNsa'], 1)} / {id_(n['phiNcbg'], 1)}",
             f"{id_(n['phiNsa'], 1)} / {id_(n['phiNcbg'], 1)}"],
            ["φVsa 4 angkur (kN)", id_(n["phiVsa"], 1), id_(n["phiVsa"], 1)],
            ["Interaksi tarik + geser (<= 1,2)", id_(n["ns_rNV"]), id_(n["tk_rNV"])],
            ["Beban garis balok tepi (kN/m); 4.2: " + id_(n["gar42"]), id_(n["gar_ns"]), id_(n["gar_tk"])],
            ["Torsi keseimbangan 1,2-1,4D (kNm)", id_(n["t_ns"], 1), id_(n["t_tk"], 1)],
        ]
        tabel(g, -1.0, -1.75, [74, 34, 34], ["URAIAN (4.10 Rincian Fasad V3.xlsx)", "U-S", "B-T"], rows, kiri=(0,))
        g.legenda_tambah("arsir", "Beton balok tepi dan pelat", pola="ANSI31", skala_pola=0.4)
        g.legenda_tambah("garis", "Konsol, pelat dasar, angkur baja", tebal=0.5)
        g.legenda_tambah("arsir", "Blok terakota", pola="ANSI37", skala_pola=0.4)
        _lembar_detail(g, "GS-19", "Angkur fasad V3", "1:20",
                       "Langkah 4.10: rincian fasad V3 (keputusan Defsa 4.9); hitungan tahap4_fasad.py",
                       [f"Fp pengencang {id_(n['fp'], 3)} Wp (ap 1,25, Rp 1,0, Ip 1,5; SNI 1726 Pasal 9 dan Tabel 25); "
                        "Ev 0,2 SDS Wp; angin V 30 m/s [Asumsi 4.2].",
                        f"Sambungan panel menampung Dpl = {id_(n['Dpl'], 0)} mm (Pers. 90, simpangan 4.3): lubang slot "
                        "±35 mm.",
                        "Kapasitas angkur SNI 2847 Pasal 17 (gempa 0,75 φNcbg); geser jebol beton dan cabut dicek "
                        "bersama pemasok di Tahap 7.",
                        "Elevasi overstek di bawah balok tepi; model 4.9 +3,00 dari lantai disesuaikan di Tahap 7.",
                        "Berat V3 lebih ringan dari asumsi 4.2 (lihat 4.10 Rincian Fasad V3.xlsx)."],
                       status, pusat=(1.7, -1.05), judul_kop="ANGKUR FASAD V3")
        _simpan(g, dwg)
    return dwg


# ------------------------------------------------------------------ semua lembar
LEMBAR = {"GS-03": catatan_umum, **{nomor(lv): functools.partial(denah, lv) for lv in LANTAI},
          "GS-11": potongan_a, "GS-12": potongan_b, "GS-13": balok, "GS-14": kolom, "GS-15": dinding,
          "GS-16": tangga_lembar, "GS-17": transfer, "GS-18": shaft, "GS-19": fasad,
          "GS-20": memanjang}


def gabung_pdf(keluar=PDF):
    """PDF 4.10: GS-03 s.d. GS-19 hasil plot layout digabung berurutan; PDF sementara dihapus."""
    import shutil

    import pypdfium2 as pdfium
    hasil = pdfium.PdfDocument.new()
    for p in sorted(PLOT.glob("GS-*.pdf")):
        src = pdfium.PdfDocument(str(p))
        hasil.import_pages(src)
        src.close()
    hasil.save(str(keluar))
    hasil.close()
    shutil.rmtree(PLOT, ignore_errors=True)
    return keluar


def buat(nomor_=None, ekspor=False):
    """Bangun lembar (semua bila nomor_ kosong), periksa cad_cek tiap DWG, gabung PDF bila semua dibangun."""
    if ekspor:
        ekspor_bim()
    hasil = {}
    for no, f in LEMBAR.items():
        if nomor_ and no not in nomor_:
            continue
        dwg = f()
        hasil[no] = {"dwg": dwg, "tumpuk": cek(dwg)}
        print(no, dwg.name, len(hasil[no]["tumpuk"]), "pasangan", flush=True)
    if not nomor_:
        gabung_pdf()
    return hasil


if __name__ == "__main__":
    arg = [a for a in sys.argv[1:] if a.startswith("GS-")]
    buat(arg or None, ekspor="--ekspor" in sys.argv)
