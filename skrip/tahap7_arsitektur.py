"""Langkah 7.1: model arsitektur LOD 300 di BIMCraft (hanya unsur arsitektur; struktur ada di RSTB-STR-T6-LOD300).

DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi.
Status: draf, keputusan usulan AI disetujui atas delegasi Defsa 22 Nov 2026. Disusun AI (Sonnet 5.5).

Isi: fasad V4 (dikunci, pola `tahap4_fasad_v4`), tata letak ruang tiap lantai sesuai program 3.4 di dalam zona
`tahap3_zonasi`, dinding partisi, ruang (IfcSpace) dengan Pset finishing, pintu bertipe, plafon dan lapis lantai 50 mm,
inti lift/tangga (ruang + pintu lift + railing), tapak (rumput, jalan, parkir, P4 76 motor di barat, pagar, gerbang,
lampu), taman atap, dek helipad, gedung utilitas, tangki opsi B, tepi sungai dan tebing.
Level dan grid sama dengan model struktur (tidak digeser). Bagian geometri murni (tanpa BIMCraft) diuji di
`tests/test_tahap7_arsitektur.py`.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

from shapely.geometry import LineString, MultiLineString, Point, Polygon, box
from shapely.ops import linemerge, unary_union

sys.path.insert(0, str(Path(__file__).parent))
from bimcraft import GalatBIM  # noqa: E402
import tahap3_tapak as tp  # noqa: E402
import tahap3_zonasi as zn  # noqa: E402
import tahap4_beban as tb  # noqa: E402
import tahap4_bim as bim  # noqa: E402
import tahap4_dinding as td  # noqa: E402
import tahap4_fasad_v4 as v4  # noqa: E402
import tahap5_tangki as t5t  # noqa: E402
import tahap5_telaah as te  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
TEMPLAT = AKAR / "model" / "RSTB-TPL-Template.bimc"
BIMC = AKAR / "model" / "RSTB-ARS-T7-LOD300.bimc"
IFC = BIMC.with_suffix(".ifc")
STR_IFC = AKAR / "model" / "RSTB-STR-T6-LOD300.ifc"
PROGRAM = AKAR / "03 Desain Konsep" / "3.4 Program Ruang Konsultan.xlsx"
GAMBAR = AKAR / "07 DED dan RKS" / "Gambar"
MD = AKAR / "07 DED dan RKS" / "7.1 Model Arsitektur.md"
STATUS = "Model ARS LOD 300 Tahap 7 (draf, disetujui atas delegasi Defsa 22 Nov 2026)"

KOR = 2.4            # m, lebar koridor ganda untuk brankar [Asumsi: pedoman koridor RS belum ada di acuan/]
T_EFF = 0.10         # m, tebal partisi efektif untuk luas bersih ruang (partisi 100 mm, [Asumsi])
OFFSET_LANTAI = 50   # mm, lapis finishing lantai [Asumsi]
OVERSTEK = (3600, 3900)   # mm di atas LT1: konsol overstek podium [Asumsi: GS-19 tidak ada nilainya di skrip]
LANTAI = ["LT1", "LT2", "LT3", "LT4", "LT5", "LT6"]
TINGGI_LT = {lv: (tb.LEVEL[hi] - tb.LEVEL[lv]) * 1000 for lv, hi in zip(tb.URUT[:-1], tb.URUT[1:])}
H_PARTISI = 800      # mm, partisi berhenti 800 mm di bawah level atas (bawah balok) [Asumsi]

# ------------------------------------------------------------------ inti (lift dan tangga darurat)
_TOP = {n: p for n, _, p in tb.INTI}


def inti_lantai(lt):
    """[(nama, jenis, kotak luar muka dinding STR, kotak dalam)] inti yang ada di lantai `lt`."""
    out = []
    for nama, pusat in bim.PUSAT.items():
        if tb.URUT.index(lt) >= tb.URUT.index(_TOP[nama]):
            continue
        cx, cy = pusat
        lift = nama.startswith("Inti")
        dx, dy = td.DIM["L" if lift else "T"]
        out.append((nama, "lift" if lift else "tangga",
                    box(cx - (dx + td.T) / 2, cy - (dy + td.T) / 2, cx + (dx + td.T) / 2, cy + (dy + td.T) / 2),
                    box(cx - (dx - td.T) / 2, cy - (dy - td.T) / 2, cx + (dx - td.T) / 2, cy + (dy - td.T) / 2)))
    return out


def shaft_lantai(lt):
    """[(kode, 'shaft', kotak luar selubung bata 100, kotak shaft)] shaft STR (`tahap4_bim.SHAFT`) yang menembus lantai
    `lt` di dalam denah (koreksi 7.2: partisi tidak memotong shaft, ruang shaft tanpa lapis lantai)."""
    out = []
    for kode, x0, x1, y0, y1, a, c in bim.SHAFT:
        g = box(x0, y0, x1, y1)
        if tb.URUT.index(a) <= tb.URUT.index(lt) <= tb.URUT.index(c) and wilayah_lantai(lt).contains(g):
            out.append((kode, "shaft", g.buffer(0.1, join_style=2), g))
    return out


def lubang_atap(level, poli):
    """Lubang shaft STR yang berakhir di `level` dan berada di dalam lapis atap `poli` (koreksi 7.2)."""
    return [_poli(box(x0, y0, x1, y1)) for _k, x0, x1, y0, y1, _a, c in bim.SHAFT
            if c == level and poli.contains(box(x0, y0, x1, y1))]


def _lub(o):
    return {"openings": o} if o else {}


def wilayah_lantai(lt):
    """Poligon denah lantai (m): LT1 podium, LT2 podium tanpa void, LT3 bentuk L, LT4-6 menara."""
    if lt == "LT1":
        return tb.PODIUM
    if lt == "LT2":
        return tb.PODIUM.difference(tb.VOID_LT2)
    if lt == "LT3":
        return tb.LT3
    return tb.MENARA


# ------------------------------------------------------------------ program ruang
def baca_program():
    """{No: (kelompok, ruang, jumlah, luas satuan)} dari 3.4 Program Ruang Konsultan.xlsx (lembar Program)."""
    import openpyxl
    ws = openpyxl.load_workbook(PROGRAM, data_only=True)["Program"]
    out = {}
    for r in ws.iter_rows(min_row=7, values_only=True):
        if isinstance(r[2], int):
            out[r[2]] = (r[3], r[4], int(r[5]), float(r[6]))
    return out


def baca_rekap():
    """{lantai: (bersih, bruto, massa)} dari lembar Rekap Lantai."""
    import openpyxl
    ws = openpyxl.load_workbook(PROGRAM, data_only=True)["Rekap Lantai"]
    return {r[2]: (r[3], r[4], r[5]) for r in ws.iter_rows(min_row=1, values_only=True)
            if r[2] in LANTAI + ["GU"]}


# finishing per kunci: (lantai, dinding, plafon, tinggi plafon mm, kunci material)  [Asumsi semua]
FINISH = {
    "OK": ("vinil konduktif 2 mm", "HPL antibakteri atau cat epoksi", "plafon laminar-flow modul MEP (tanpa gypsum)", None),
    "INTENSIF": ("vinil homogen 2 mm", "cat epoksi", "gypsum anti-jamur", 2800),
    "RAWAT": ("vinil homogen 2 mm", "cat emulsi anti-bakteri", "gypsum", 2800),
    "KLINIK": ("vinil homogen 2 mm", "cat emulsi anti-bakteri", "gypsum", 2800),
    "LOBI": ("granit 60 x 60 poles", "cat emulsi + panel wall", "gypsum drop ceiling", 3000),
    "SERVIS": ("epoksi self-leveling", "cat epoksi setinggi 2,1 m", "gypsum anti-jamur", 2800),
    "TOILET": ("keramik anti-slip 30 x 30", "keramik 30 x 60 sampai plafon", "gypsum anti-jamur", 2800),
    "ADM": ("homogeneous tile 60 x 60", "cat emulsi", "gypsum", 3000),
    "SIRK": ("vinil homogen 2 mm", "cat emulsi + bumper rail", "gypsum", 2800),
    "UTIL": ("epoksi self-leveling", "cat epoksi", None, None),
    "INTI": ("beton ekspos", "beton ekspos", None, None),
    "PARKIR": ("beton trowel", "beton ekspos", None, None),
}
# jenis pintu: P1 900 tunggal, P2 1.200 ganda brankar, P3 1.500 ganda IGD/OK
PINTU_UKURAN = {"P1": (900, 2100), "P2": (1200, 2100), "P3": (1500, 2100), "PL": (1400, 2400)}


@dataclass
class Ruang:
    nama: str
    kode: str
    kel: str
    poli: Polygon
    fin: str = "KLINIK"
    pintu: str = "P1"
    lt: str = ""
    zona: str = ""
    program: bool = True       # ikut hitungan luas bersih program (T-109)
    nomor: str = ""            # nomor baris program 3.4 (bila ada)


@dataclass
class Susunan:
    lt: str
    ruang: list = field(default_factory=list)
    sirk: list = field(default_factory=list)     # poligon sirkulasi (sisa)
    inti: list = field(default_factory=list)
    wilayah: Polygon = None


def _celah(a0, a1, b0, b1, blok):
    """Interval bebas dalam [a0, a1] setelah dikurangi daftar interval terblokir `blok` (hanya yang beririsan [b0, b1])."""
    pot = [(max(a0, p), min(a1, q)) for p, q in blok if q > a0 and p < a1]
    pot.sort()
    out, cur = [], a0
    for p, q in pot:
        if p > cur + 1e-9:
            out.append([cur, p])
        cur = max(cur, q)
    if cur < a1 - 1e-9:
        out.append([cur, a1])
    return out


def _luas_bersih(poli):
    """Luas bersih (muka dinding): partisi T_EFF mengurangi tiap sisi setengah tebalnya."""
    return poli.buffer(-T_EFF / 2, join_style=2).area


def solusi(f, lo, hi, target, n=60):
    """Cari x di [lo, hi] dengan f(x) = target (f monoton)."""
    naik = f(hi) > f(lo)
    for _ in range(n):
        m = (lo + hi) / 2
        if (f(m) < target) == naik:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


def isi_zona(zona, daftar, hambatan, d_maks=8.0, sisi_koridor="min", penuh=False, hulu=0.0, tumpuk=None,
             koridor=None, kor_luar=False):
    """Susun ruang `daftar` [(nama, kode, kel, luas, fin, pintu, nomor)] dalam persegi `zona` (x0, y0, x1, y1) dengan
    rak (shelf) di kedua sisi koridor (zona tebal) atau satu sisi (zona tipis). Rak menempel koridor. Lebar ruang dihitung
    supaya luas bersih (muka partisi) sama dengan program; ruang yang menabrak inti diberi takik (poligon L) dan
    dilebarkan sampai luas bersihnya tetap. `tumpuk`: luas maks (m2) ruang kecil yang ditumpuk berpasangan dalam satu
    kolom (ruang belakang lewat pintu ke ruang depan). `koridor`: ruang yang memakai koridor itu sendiri (mis. koridor
    steril); koridor dilebarkan sampai luasnya sama. `kor_luar`: koridor di luar persegi zona.
    Kembalikan (daftar Ruang, sisa yang tidak muat)."""
    x0, y0, x1, y1 = zona
    sumbu_x = (x1 - x0) >= (y1 - y0)
    u0, u1, v0, v1 = (x0, x1, y0, y1) if sumbu_x else (y0, y1, x0, x1)
    D = v1 - v0
    kotak = (lambda ua, ub, va, vb: box(ua, va, ub, vb)) if sumbu_x else (lambda ua, ub, va, vb: box(va, ua, vb, ub))
    obs = unary_union(hambatan).buffer(0.12, join_style=2) if hambatan else Polygon()
    hasil = []
    lebar_k = KOR
    ganda = D >= 16
    vc = v0 + D / 2
    if koridor:
        nama, kode, kel, luas, fin, pintu, nomor = koridor
        lebar_k = solusi(lambda w: kotak(u0, u1, vc - w / 2, vc + w / 2).difference(obs).area, KOR, 6.0, luas)
        pk = kotak(u0, u1, vc - lebar_k / 2, vc + lebar_k / 2).difference(obs)
        hasil.append(Ruang(nama, kode, kel, pk, fin, pintu, nomor=str(nomor)))
    if ganda:
        d = min(d_maks, (D - lebar_k) / 2)
        rak = [(vc - lebar_k / 2, -1, d), (vc + lebar_k / 2, +1, d)]
    elif kor_luar:
        d = min(d_maks, D)
        rak = [(v0, +1, d)] if sisi_koridor == "min" else [(v1, -1, d)]
    else:
        d = min(d_maks, D - lebar_k)
        rak = [(v0 + lebar_k, +1, d)] if sisi_koridor == "min" else [(v1 - lebar_k, -1, d)]
    kursor = [u0 + hulu for _ in rak]
    sisa = []

    def coba(i, luas, dru, pasang=0.0):
        """Tempatkan satu ruang di rak i: (poligon, tepi u akhir) atau None."""
        ve, arah, dr = rak[i]
        va, vb = sorted((ve, ve + arah * dru))
        u = kursor[i]
        w = (luas + pasang) / (dru - (2 if pasang else 1) * T_EFF) + T_EFF
        while True:
            if u + w > u1 + 1e-9:
                return None
            p = kotak(u, u + w, va, vb)
            if not obs.is_empty and p.intersects(obs):
                if pasang:
                    return None
                inter = p.intersection(obs).area
                ob = p.intersection(obs).bounds
                p = p.difference(obs)
                if p.geom_type != "Polygon" or inter > 0.2 * (p.area + inter):
                    # inti memotong rak: lompat melewati inti (tepi akhir irisan di sumbu u)
                    u = ob[2] if sumbu_x else ob[3]
                    kursor[i] = u
                    w = (luas + pasang) / (dru - T_EFF) + T_EFF
                    continue
                if _luas_bersih(p) < luas - 0.05:
                    w += 0.05
                    continue
            return p, u + w

    antri = list(daftar)
    while antri:
        ru = antri.pop(0)
        nama, kode, kel, luas, fin, pintu, nomor = ru
        pasangan = None
        if tumpuk and luas <= tumpuk and ganda is not None:
            for k, c in enumerate(antri):
                if c[3] <= tumpuk:
                    pasangan = antri.pop(k)
                    break
        urutan = sorted(range(len(rak)), key=lambda i: kursor[i])
        ok = None
        for i in urutan:
            ve, arah, dr = rak[i]
            if pasangan:
                r = coba(i, luas, dr, pasangan[3])
                if r:
                    ok = (i, r, True)
                    break
            dru = dr if (penuh or fin == "RAWAT") else min(dr, max(3.6, 1.2 * math.sqrt(luas)))
            r = coba(i, luas, dru)
            if r:
                ok = (i, r, False)
                if pasangan:
                    antri.insert(0, pasangan)
                    pasangan = None
                break
        if not ok:
            sisa.append(ru)
            if pasangan:
                sisa.append(pasangan)
            continue
        i, (p, ujung), dua = ok
        ve, arah, dr = rak[i]
        if dua:
            w = ujung - kursor[i]
            d1 = luas / (w - T_EFF) + T_EFF
            va, vb = sorted((ve, ve + arah * d1))
            va2, vb2 = sorted((ve + arah * d1, ve + arah * dr))
            hasil.append(Ruang(nama, kode, kel, kotak(kursor[i], ujung, va, vb), fin, pintu, nomor=str(nomor)))
            hasil.append(Ruang(pasangan[0], pasangan[1], pasangan[2], kotak(kursor[i], ujung, va2, vb2), pasangan[4],
                               pasangan[5], nomor=str(pasangan[6])))
        else:
            hasil.append(Ruang(nama, kode, kel, p, fin, pintu, nomor=str(nomor)))
        kursor[i] = ujung
    return hasil, sisa


def ruang_dari(nomor, prog, jumlah=None, fin="KLINIK", pintu="P1", nama=None):
    """Baris program -> daftar tuple isi_zona sebanyak `jumlah`."""
    kel, r, n, a = prog[nomor]
    n = n if jumlah is None else jumlah
    out = []
    for k in range(n):
        label = nama or r
        out.append((f"{label} {k + 1}" if n > 1 else label, f"P{nomor:02d}", kel, a, fin, pintu, nomor))
    return out


def _rawat(prog, lt):
    """Rawat inap LT4-LT6: jumlah ruang per lantai (VIP 3,3,2; 2 TT 3,3,4; 4 TT 8,8,9) menjaga 8/10/25 ruang dan 150 TT."""
    k = LANTAI.index(lt) - 3
    jml = {26: (3, 3, 2)[k], 27: (3, 3, 4)[k], 28: (8, 8, 9)[k], 29: 2, 30: 2, 31: 2, 32: 2, 33: 2, 34: 1,
           35: (1, 1, 0)[k]}
    return jml


# ------------------------------------------------------------------ susunan lantai
def lajur(rect, daftar, arah="x"):
    """Ruang berderet memenuhi seluruh kedalaman persegi `rect` (tanpa koridor): lebar = luas / (kedalaman - T_EFF) + T_EFF."""
    x0, y0, x1, y1 = rect
    out, c = [], x0 if arah == "x" else y0
    dalam = (y1 - y0) if arah == "x" else (x1 - x0)
    for nama, kode, kel, luas, fin, pintu, nomor in daftar:
        w = luas / (dalam - T_EFF) + T_EFF
        p = box(c, y0, c + w, y1) if arah == "x" else box(x0, c, x1, c + w)
        out.append(Ruang(nama, kode, kel, p, fin, pintu, nomor=str(nomor)))
        c += w
    return out


def _urut(daftar):
    return sorted(daftar, key=lambda r: -r[3])


def zona_lantai(lt, prog):
    """Daftar zona lantai: (nama zona, kerja(hambatan) -> (ruang, sisa)). Lihat 7.1 Model Arsitektur.md untuk alasan alokasi."""
    def rd(no, **k):
        return ruang_dari(no, prog, **k)

    def mek():
        return rd(71, jumlah=1, fin="UTIL", nama=f"Ruang AHU {lt}") + rd(72, jumlah=1, fin="UTIL", nama=f"Shaft MEP {lt}")

    def Z(rect, rooms, **kw):
        f = lambda h: isi_zona(rect, _urut(rooms), h, **kw)  # noqa: E731
        f.rect = rect
        return f

    def M(fn):
        return lambda h: (fn(), [])

    z = []
    if lt == "LT1":
        z += [("Poliklinik", Z((12, 27, 36, 75), rd(2, fin="KLINIK") + rd(3, pintu="P2", nama="Sub-ruang tunggu poliklinik")
                               + rd(4) + rd(5, pintu="P2") + rd(6, pintu="P2") + rd(56, jumlah=3, fin="TOILET"),
                               d_maks=10.8, tumpuk=30)),
              ("Gawat darurat", Z((62, 27, 84, 51), rd(9, pintu="P3") + rd(10, pintu="P3", fin="INTENSIF")
                                  + rd(11, pintu="P3") + rd(12, pintu="P3", fin="OK") + rd(13, pintu="P2", fin="SERVIS")
                                  + rd(14, pintu="P2", fin="INTENSIF") + rd(15, pintu="P2", fin="LOBI")
                                  + rd(68, pintu="P2"), d_maks=9.8, tumpuk=30)),
              ("Radiologi", Z((62, 51, 84, 63), rd(37, pintu="P2") + rd(38, pintu="P2") + rd(40),
                              d_maks=9.6, sisi_koridor="max")),
              ("Farmasi dan rekam medis", Z((62, 63, 84, 75), rd(7, fin="SERVIS") + rd(8, fin="ADM"), d_maks=9.6)),
              ("Penunjang tengah", Z((36, 27, 62, 63), rd(46, pintu="P2", fin="SERVIS") + rd(55, fin="ADM")
                                     + rd(45, pintu="P2", fin="SERVIS") + rd(56, jumlah=4, fin="TOILET") + rd(51, fin="UTIL") + rd(39) + mek(),
                                     d_maks=10.8, tumpuk=30))]
    elif lt == "LT2":
        z += [("Bedah sentral", Z((62, 27, 84, 63), rd(17, pintu="P3", fin="OK") + rd(18, pintu="P3", fin="INTENSIF")
                                   + rd(20, fin="SERVIS") + rd(21, pintu="P2", fin="SERVIS") + rd(69, nama="Ruang tunggu keluarga bedah dan ICU", fin="LOBI"),
                                   d_maks=9.8, penuh=True, koridor=("Koridor steril dan scrub",) + tuple(
                                       [f"P{19:02d}", prog[19][0], prog[19][3], "OK", "P3", 19]))),
              ("Kebidanan", Z((12, 27, 36, 43), rd(36, pintu="P2", fin="INTENSIF") + rd(70, pintu="P2", fin="INTENSIF")
                              + mek(), d_maks=6.8, tumpuk=30)),
              ("Laboratorium", Z((12, 43, 36, 55), rd(41, pintu="P2", fin="SERVIS") + rd(42, fin="SERVIS"),
                                  d_maks=9.6, penuh=True)),
              ("Hemodialisis", Z((12, 55, 36, 75), rd(43, pintu="P2", fin="INTENSIF") + rd(25, fin="INTENSIF", pintu="P2"),
                                  d_maks=8.8, tumpuk=40)),
              ("Rehabilitasi medik", Z((62, 66.2, 84, 75), rd(44, pintu="P2"), d_maks=8.8, kor_luar=True))]
    elif lt == "LT3":
        z += [("Administrasi", Z((12, 27, 36, 75), rd(57, fin="ADM") + rd(59, pintu="P2", fin="ADM", nama="Aula")
                                 + rd(60, fin="ADM") + rd(58, fin="ADM") + rd(62, fin="ADM"),
                                 d_maks=10.8, tumpuk=30)),
              ("Tengah", Z((36, 27, 62, 51), rd(61, fin="ADM") + rd(63, pintu="P2", fin="SERVIS") + mek(),
                           d_maks=10.8, tumpuk=40)),
              ("Gizi dan laundry", Z((62, 27, 84, 51), rd(47, pintu="P2", fin="SERVIS") + rd(48, pintu="P2", fin="SERVIS"),
                                     d_maks=9.8))]
    else:
        j = _rawat(prog, lt)
        wr = (rd(26, jumlah=j[26], pintu="P2", fin="RAWAT") + rd(27, jumlah=j[27], pintu="P2", fin="RAWAT")
              + rd(28, jumlah=j[28], pintu="P2", fin="RAWAT"))
        lain = (rd(29, jumlah=j[29], fin="KLINIK") + rd(30, jumlah=j[30], fin="KLINIK") + rd(31, jumlah=j[31], fin="SERVIS")
                + rd(32, jumlah=j[32], fin="SERVIS") + rd(33, jumlah=j[33], fin="LOBI") + rd(34, jumlah=j[34], fin="SERVIS")
                + (rd(35, jumlah=j[35], fin="KLINIK") if j[35] else []))
        urut = ([x for x in wr] + [x for x in lain])
        f = lambda h: isi_zona((20, 27, 84, 51), mek() + urut, h, d_maks=10.8)  # noqa: E731
        f.rect = (20, 27, 84, 51)
        z += [("Rawat inap " + lt, f)]
    return z


def lobi_lt1(prog):
    """Lobi, pendaftaran, ruang tunggu 260 m2: persegi x 36-62 dari y0 sampai 75 dikurangi inti tangga (46, 63)."""
    inti = [c[2] for c in inti_lantai("LT1") if c[0].endswith("y63") and "x46" in c[0]][0]
    kel, nama, _, a = prog[1]

    def bentuk(y0):
        return box(36, y0, 62, 75).difference(inti.buffer(0.1))
    y0 = solusi(lambda y: _luas_bersih(bentuk(y)), 60.0, 74.0, a)
    return Ruang(nama, "P01", kel, bentuk(y0), "LOBI", "P3", nomor="1")


def dropoff_lt1(prog):
    kel, nama, _, a = prog[16]
    return Ruang(nama, "P16", kel, box(DROPOFF[0], DROPOFF[1], DROPOFF[2], DROPOFF[1] + a / 7.4), "PARKIR", "P1", nomor="16")


def sisipkan(W, ruang, hamb, tup, rect):
    """Cari tempat bebas (persegi di sisa denah) untuk ruang yang tidak muat di rak zonanya; terdekat ke pusat zona."""
    nama, kode, kel, luas, fin, pintu, nomor = tup
    pakai = unary_union([r.poli.buffer(0.12, join_style=2) for r in ruang] + [h.buffer(0.12, join_style=2) for h in hamb])
    bebas = W.difference(pakai)
    cx, cy = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
    from shapely.prepared import prep
    pb = prep(bebas.buffer(1e-6))
    minx, miny, maxx, maxy = W.bounds
    for d in (5.0, 6.0, 4.0, 7.0, 8.0, 3.6):
        w = luas / (d - T_EFF) + T_EFF
        cand = []
        for a, b in ((w, d), (d, w)):
            for xi in range(int((maxx - minx) / 1.0)):
                x = minx + xi
                for yi in range(int((maxy - miny) / 1.0)):
                    y = miny + yi
                    cand.append((math.hypot(x + a / 2 - cx, y + b / 2 - cy), x, y, a, b))
        for _, x, y, a, b in sorted(cand):
            p = box(x, y, x + a, y + b)
            if pb.contains(p):
                return Ruang(nama, kode, kel, p, fin, pintu, nomor=str(nomor))
    return None


def susun_lantai(lt, prog=None):
    """Tata letak ruang satu lantai: ruang program, ruang inti, sisa sirkulasi. Kembalikan Susunan (+ .gagal)."""
    prog = prog or baca_program()
    W = wilayah_lantai(lt)
    inti = inti_lantai(lt) + shaft_lantai(lt)
    hamb = [c[2] for c in inti]
    S = Susunan(lt=lt, wilayah=W, inti=inti)
    S.gagal = []
    ruang = []
    # ruang manual lebih dulu (lobi, drop-off, ICU/HCU/NICU); poligonnya jadi hambatan bagi rak zona
    if lt == "LT1":
        for x in (lobi_lt1(prog), dropoff_lt1(prog)):
            x.zona = "Lobi" if x.kode == "P01" else "Drop-off IGD"
            ruang.append(x)
    if lt == "LT2":
        # ICU, HCU, NICU: dua lajur di utara dan selatan inti lift (inti memotong koridor tengah zona)
        kt = [Ruang(prog[22][1], "P22", prog[22][0], box(36, 27, 62, 34.7), "INTENSIF", "P3", nomor="22")]  # 198 m2 (-1 %)
        ks = lajur((36, 43.3, 62, 51), [(prog[23][1], "P23", prog[23][0], prog[23][3], "INTENSIF", "P3", 23),
                                       (prog[24][1], "P24", prog[24][0], prog[24][3], "INTENSIF", "P3", 24)])
        for x in kt + ks:
            x.zona = "ICU, HCU, NICU"
        ruang += kt + ks
    sh = unary_union([c[2] for c in inti if c[1] == "shaft"])
    for x in ruang:   # ruang manual diberi takik di shaft STR (koreksi 7.2)
        x.poli = x.poli.difference(sh).buffer(0) if not sh.is_empty else x.poli
    hamb_z = hamb + [r.poli for r in ruang if r.kode != "P16"]
    pusat_zona = {}
    for nama_zona, kerja in zona_lantai(lt, prog):
        r, sisa = kerja(hamb_z)
        for x in r:
            x.zona = nama_zona
        ruang += r
        pusat_zona[nama_zona] = kerja.rect
        S.gagal += [(nama_zona, s) for s in sisa]
    sisa_semua, S.gagal = S.gagal, []
    for nama_zona, s in sorted(sisa_semua, key=lambda t: -t[1][3]):
        r = sisipkan(W, ruang, hamb, s, pusat_zona[nama_zona])
        if r:
            r.zona = nama_zona + " (sisipan)"
            ruang.append(r)
        else:
            S.gagal.append((nama_zona, s[0]))
    for x in ruang:
        x.lt = lt
    for nama, jenis, luar, dalam in inti:
        if jenis == "shaft":
            ruang.append(Ruang(f"Shaft MEP {nama} (lubang pelat STR)", "INTI", "Inti", dalam, "VOID", "P1", lt, "Inti", False))
            continue
        nm = "Lift brankar dan pasien (inti lift)" if jenis == "lift" else "Tangga darurat " + nama.split()[1]
        # ruang luncur lift tanpa lapis lantai (koreksi 7.2: lapis LT-INTI menutup lubang lift pelat STR)
        ruang.append(Ruang(nm, "INTI", "Inti", dalam, "VOID" if jenis == "lift" else "INTI",
                           "PL" if jenis == "lift" else "P2", lt, "Inti", False))
    S.ruang = ruang
    kosong = W.difference(unary_union([r.poli for r in ruang] + [c[2] for c in inti]))
    geo = [g for g in (kosong.geoms if hasattr(kosong, "geoms") else [kosong])]
    S.sirk = [g.buffer(0) for g in geo if g.area > 1.0 and not g.buffer(-0.2, join_style=2).is_empty]
    return S


def pratinjau(png=None, lantai=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    prog = baca_program()
    lantai = lantai or LANTAI
    fig, axs = plt.subplots(2, 3, figsize=(24, 14))
    for ax, lt in zip(axs.flat, lantai):
        S = susun_lantai(lt, prog)
        for g in [S.wilayah]:
            ax.plot(*g.exterior.xy, "k-", lw=1)
        for r in S.ruang:
            fc = {"INTI": "#bbbbbb", "SERVIS": "#e8c9a0", "OK": "#a0c8e8", "TOILET": "#a0e8d0"}.get(r.fin, "#dfe8c0")
            xs, ys = r.poli.exterior.xy
            ax.fill(xs, ys, fc=fc, ec="k", lw=0.5)
            c = r.poli.representative_point()
            ax.text(c.x, c.y, r.nama[:14], fontsize=5, ha="center")
        for g in S.sirk:
            ax.fill(*g.exterior.xy, fc="#ffffe0", ec="r", lw=0.3, alpha=0.6)
        ax.set_title(f"{lt}  gagal={len(S.gagal)}")
        ax.set_aspect("equal")
    if png:
        fig.savefig(png, dpi=70)
    return fig


# ------------------------------------------------------------------ garis dinding dari susunan lantai
def _garis(g):
    if g.is_empty:
        return []
    if g.geom_type == "LineString":
        return [g]
    out = []
    for h in getattr(g, "geoms", []):
        out += _garis(h)
    return out


def garis_susunan(S):
    """Pisahkan batas poligon ruang dan sirkulasi menjadi: dinding 100 (antarruang), dinding 150 (batas koridor),
    pemisah ruang (tepi denah, tepi void, ruang di luar denah) dan tepi void (untuk railing). Semua dalam meter.
    Garis dinodakan dulu (unary_union) lalu tiap ruas diklasifikasi dari titik tengahnya, supaya ujung dinding tepat
    bertemu dan ruang tertutup rapat."""
    polys = [r.poli for r in S.ruang if r.kel != "Inti" and r.kode != "P16"] + list(S.sirk)
    semua = unary_union([p.boundary for p in polys])
    luar = S.wilayah.boundary
    sirk_b = unary_union([p.boundary for p in S.sirk]) if S.sirk else Polygon()
    kls = {"d100": [], "d150": [], "sep": []}
    for ln in _garis(semua):
        m = ln.interpolate(0.5, normalized=True)
        if luar.distance(m) < 0.01:
            kls["sep"].append(ln)
        elif not sirk_b.is_empty and sirk_b.distance(m) < 0.01:
            kls["d150"].append(ln)
        else:
            kls["d100"].append(ln)

    def gabung(ls):
        return [l for l in (_garis(linemerge(ls)) if ls else []) if l.length > 0.05]

    void = []
    if S.lt == "LT2":
        vb = tb.VOID_LT2.boundary
        void = [l for l in kls["sep"] if vb.distance(l.interpolate(0.5, normalized=True)) < 0.01
                and tb.PODIUM.boundary.distance(l.interpolate(0.5, normalized=True)) > 0.01]
    return {"d100": gabung(kls["d100"]), "d150": gabung(kls["d150"]), "sep": gabung(kls["sep"]), "void": gabung(void),
            "inti_luar": [c[2] for c in S.inti]}


def posisi_pintu(r, S):
    """Kandidat titik pintu (x, y, n) pada batas ruang `r`: tepi bersama dengan koridor (n=0) lebih dulu, lalu tepi
    dengan ruang tetangga (n=1); tiap tepi dicoba di beberapa pecahan panjangnya."""
    sirk = unary_union([p.buffer(0.04) for p in S.sirk]) if S.sirk else Polygon()
    lebar = PINTU_UKURAN[r.pintu][0] / 1000
    out = []
    tetangga = [q.poli.buffer(0.04) for q in S.ruang if q is not r and q.kel != "Inti"]
    for lawan, n in ((sirk, 0), (unary_union(tetangga) if tetangga else Polygon(), 1)):
        bersama = r.poli.boundary.intersection(lawan)
        ruas = sorted([l for l in _garis(bersama) if l.length >= lebar + 0.5], key=lambda l: -l.length)
        for l in ruas:
            for f in (0.5, 0.35, 0.65, 0.25, 0.75, 0.15, 0.85):
                m = l.interpolate(f, normalized=True)
                out.append((m.x, m.y, n))
    return out


# ------------------------------------------------------------------ bahan, tipe, parameter
BAHAN = {  # nama: (warna, transparansi)
    "Bata ringan": ("#D9D5CC", 0), "Lapis inti": ("#C8C8C4", 0), "Gypsum": ("#F2F2EF", 0),
    "Vinil homogen": ("#9FB3A8", 0), "Vinil konduktif": ("#7FA0B8", 0), "Granit poles": ("#6D6F73", 0),
    "Epoksi": ("#B7B1A0", 0), "Keramik": ("#C9C2B2", 0), "Homogeneous tile": ("#CFCABB", 0),
    "Beton ekspos": ("#9A9A98", 0), "Paving": ("#B8B2A6", 0), "Tanah taman": ("#5E7F3E", 0),
    "Air sungai": ("#4A7FA5", 40), "Tanah lereng": ("#7A6A4F", 0), "Pagar": ("#4B5257", 0), "Aluminium dek": ("#A9AFB4", 0),
    "Marka putih": ("#FFFFFF", 0), "Marka kuning": ("#E6B800", 0), "Kanopi": ("#7C848A", 0), "Tiang lampu": ("#3A3F44", 0),
    "Cahaya": ("#F7E9A6", 0), "Motor": ("#2B2F33", 0), "Motor bodi": ("#8B2E2E", 0),
}
FIN_LANTAI = {"OK": "Vinil konduktif", "INTENSIF": "Vinil homogen", "RAWAT": "Vinil homogen", "KLINIK": "Vinil homogen",
              "LOBI": "Granit poles", "SERVIS": "Epoksi", "TOILET": "Keramik", "ADM": "Homogeneous tile",
              "SIRK": "Vinil homogen", "UTIL": "Epoksi", "INTI": "Beton ekspos", "PARKIR": "Beton ekspos"}
KAT_PARAM = ["wall", "floor", "ceiling", "roof", "door", "window", "room", "column", "component", "stair", "ramp", "railing"]
H_PL = lambda lt, fin: FINISH[fin][3]  # noqa: E731


def siapkan(b):
    for nama, (warna, tr) in {**v4.WARNA, **BAHAN}.items():
        b.cmd("material", {"name": nama, "color": warna, "transparency": tr})
    lap = lambda f, m, t: [{"function": f, "material": m, "thickness": t}]  # noqa: E731
    for nama, bahan, t in (("FS-PanelPutih", "Panel putih", 50), ("FS-PanelAbu", "Panel abu", 50),
                           ("FS-PanelAbuTua", "Panel abu tua", 50), ("FS-KacaBiru", "Kaca biru", 30),
                           ("FS-KacaPita", "Kaca pita", 30), ("DP-Bata100", "Bata ringan", 100),
                           ("DP-Bata150", "Bata ringan", 150), ("DL-LapisInti50", "Lapis inti", 50),
                           ("PG-Pagar150", "Pagar", 150), ("PG-Tiang400", "Pagar", 400), ("PG-Papan", "Panel abu tua", 200),
                           ("TK-Panel100", "Panel abu", 100), ("BT-Bak200", "Beton ekspos", 200)):
        b.cmd("type", {"category": "wall", "name": nama, "layers": lap("finish" if nama.startswith("FS") else "structure", bahan, t)})
    for nama, bahan, t in (("TP-Rumput", "Rumput", 100), ("TP-Aspal", "Aspal", 100), ("TP-Paving", "Paving", 100),
                           ("TP-TamanAtap", "Tanah taman", 150), ("TP-Lereng", "Tanah lereng", 300),
                           ("TP-Air", "Air sungai", 100), ("TP-Kanopi", "Kanopi", 200), ("TP-DekHelipad", "Aluminium dek", 100),
                           ("TP-MarkaPutih", "Marka putih", 10), ("TP-MarkaKuning", "Marka kuning", 10),
                           ("TP-Overstek", "Panel abu", 300), ("TP-AtapTangki", "Panel abu", 150),
                           ("TP-Beton", "Beton ekspos", 150)):
        b.cmd("type", {"category": "floor", "name": nama, "layers": lap("finish", bahan, t)})
    for fin, mat in FIN_LANTAI.items():
        b.cmd("type", {"category": "floor", "name": f"LT-{fin}", "layers": lap("finish", mat, OFFSET_LANTAI)})
    b.cmd("type", {"category": "ceiling", "name": "PL-Gypsum", "thickness": 12})
    for fin, (lantai, dinding, plafon, tinggi) in FINISH.items():
        p = {"category": "room", "name": f"R-{fin}", "floor": f"LT-{fin}", "floor_offset": OFFSET_LANTAI}
        if tinggi:
            p.update({"ceiling": "PL-Gypsum", "ceiling_offset": tinggi})
        b.cmd("type", p)
    b.cmd("type", {"category": "room", "name": "R-VOID"})   # shaft dan ruang luncur lift: tanpa lapis lantai dan plafon
    for k, (lb, h) in PINTU_UKURAN.items():
        if k == "PL":
            b.cmd("type", {"category": "door", "name": f"PL-{lb}x{h}", "width": lb, "height": h})
    umum = {k: "Pset_RSTB_Umum" for k in KAT_PARAM}
    for nama, ket in (("RSTB_Tahap", "Tahap pekerjaan"), ("RSTB_LOD", "Level of development"), ("RSTB_Status", "Status model"),
                      ("RSTB_Sumber", "Asal unsur dan asumsi")):
        b.cmd("parameter", {"name": nama, "kind": "text", "categories": KAT_PARAM, "sets": umum, "description": ket})
    for nama, ket in (("RSTB_Zona", "Zona fungsi (zona merah, kuning, hijau, utilitas)"),
                      ("RSTB_KodeProgram", "Nomor baris program 3.4"), ("RSTB_Kelompok", "Kelompok program 3.4"),
                      ("RSTB_FinLantai", "Finishing lantai"), ("RSTB_FinDinding", "Finishing dinding"),
                      ("RSTB_FinPlafon", "Finishing plafon")):
        b.cmd("parameter", {"name": nama, "kind": "text", "categories": ["room"], "sets": {"room": "Pset_RSTB_Finishing"},
                            "description": ket})
    for i, x in enumerate(tb.GRID_X):
        b.cmd("grid", {"start": bim.mm(x, tb.GRID_Y[0] - 6), "end": bim.mm(x, tb.GRID_Y[-1] + 6), "name": str(i + 1)})
    for j, y in enumerate(tb.GRID_Y):
        b.cmd("grid", {"start": bim.mm(tb.GRID_X[0] - 6, y), "end": bim.mm(tb.GRID_X[-1] + 6, y), "name": bim.NAMA_Y[j]})


class Catat:
    """Kumpulkan id elemen per kelompok untuk pengisian Pset_RSTB_Umum di akhir."""
    def __init__(self):
        self.ids = {}
        self.hitung = {}

    def __call__(self, grup, r, n=1):
        if isinstance(r, dict):
            ids = [i for i in (r.get("ids") or [r.get("id")]) if isinstance(i, int)]
            self.ids.setdefault(grup, []).extend(ids)
        self.hitung[grup] = self.hitung.get(grup, 0) + n
        return r


def mm(p):
    return [round(p[0] * 1000), round(p[1] * 1000)]


def mm_garis(coords):
    """Titik garis (m) -> mm tanpa titik kembar berurutan; kosong bila kurang dari 2 titik."""
    out = []
    for p in coords:
        q = mm(p)
        if not out or q != out[-1]:
            out.append(q)
    return out if len(out) >= 2 else []


def _poli(g):
    return [mm(p) for p in list(g.exterior.coords)[:-1]]


def _pintu(b, x, y, jenis, lt, rec, grup="pintu"):
    lb, h = PINTU_UKURAN[jenis]
    if jenis == "P1":
        p = {"family": "Single Door", "type": "900 x 2100"}
    elif jenis == "P2":
        p = {"family": "Double Door", "type": "1200 x 2100"}
    elif jenis == "P3":
        p = {"family": "Double Door", "type": "1500 x 2100"}
    else:
        p = {"type": f"PL-{lb}x{h}"}
    return rec(grup, b.cmd("door", {"at": mm((x, y)), "level": lt, **p}))


# ------------------------------------------------------------------ interior satu lantai
def interior(b, lt, S, rec, lap_ruang):
    """Dinding, pemisah, pintu, ruang (IfcSpace), railing void dan lapisan inti satu lantai. `lap_ruang` menampung
    (id ruang, Ruang, nomor) untuk pengisian Pset finishing."""
    gs = garis_susunan(S)
    h = round(TINGGI_LT[lt] - H_PARTISI)
    for tipe, kunci in (("DP-Bata100", "d100"), ("DP-Bata150", "d150")):
        for ln in gs[kunci]:
            pts = mm_garis(ln.coords)
            if pts:
                rec("dinding partisi", b.cmd("wall", {"points": pts, "type": tipe, "level": lt, "height": h}), len(pts) - 1)
    for ln in gs["sep"] + gs["void"]:
        pts = mm_garis(ln.coords)
        if pts:
            b.cmd("room_separator", {"points": pts, "level": lt})
    for ln in gs["void"]:
        pts = mm_garis(ln.coords)
        if pts:
            rec("railing", b.cmd("railing", {"path": pts, "level": lt}))
    # ruang di luar denah (drop-off IGD): pemisah di sekeliling
    for r in S.ruang:
        if r.kode == "P16":
            b.cmd("room_separator", {"points": _poli(r.poli), "level": lt, "closed": True})
    # lapisan inti 50 mm di muka luar dinding inti + pintu lift/tangga; ruang inti dibatasi pemisah muka dalam
    for nama, jenis, luar, dalam in S.inti:
        if jenis == "shaft":   # selubung bata 100 di luar muka shaft, tanpa pintu (panel akses MEP)
            rec("selubung shaft", b.cmd("wall", {"points": _poli(dalam.buffer(0.05, join_style=2)), "closed": True,
                                                 "type": "DP-Bata100", "level": lt, "height": h}), 4)
            b.cmd("room_separator", {"points": _poli(dalam), "level": lt, "closed": True})
            continue
        x0, y0, x1, y1 = luar.bounds
        loop = box(x0 - 0.025, y0 - 0.025, x1 + 0.025, y1 + 0.025)
        rec("lapisan inti", b.cmd("wall", {"points": _poli(loop), "closed": True, "type": "DL-LapisInti50", "level": lt,
                                           "height": h}), 4)
        b.cmd("room_separator", {"points": _poli(dalam), "level": lt, "closed": True})
        cx, cy = bim.PUSAT[nama]
        dx, dy = td.DIM["L" if jenis == "lift" else "T"]
        ys = cy - (dy + td.T) / 2 - 0.025
        for xp, lb in td.PINTU["L" if jenis == "lift" else "T"]:
            _pintu(b, cx + xp, ys, "PL" if jenis == "lift" else "P2", lt, rec, "pintu inti")
        if jenis == "lift":
            rec("railing", b.cmd("railing", {"path": [mm((cx - 4.0, ys - 0.3)), mm((cx + 4.0, ys - 0.3))], "level": lt}))
    # pintu ruang
    tanpa = []
    for r in S.ruang:
        if r.kel == "Inti" or r.kode == "P16":
            continue
        for x, y, n in posisi_pintu(r, S):
            try:
                _pintu(b, x, y, r.pintu, lt, rec)
                break
            except GalatBIM:
                continue
        else:
            tanpa.append(r.nama)
    # ruang
    for k, r in enumerate(S.ruang, 1):
        c = r.poli.representative_point() if r.poli.geom_type == "Polygon" else r.poli.centroid
        if r.kel == "Inti":
            c = r.poli.centroid
        fin = r.fin
        res = b.cmd("room", {"point": mm((c.x, c.y)), "level": lt, "type": f"R-{fin}", "name": r.nama,
                             "number": f"{lt}-{k:03d}"})
        lap_ruang.append((res["id"], r, f"{lt}-{k:03d}", res.get("area_m2")))
    for k, g in enumerate(S.sirk, 1):
        c = g.representative_point()
        nm = getattr(S, "nama_sirk", "Sirkulasi (koridor dan selasar)")
        fn = getattr(S, "fin_sirk", "SIRK")
        res = b.cmd("room", {"point": mm((c.x, c.y)), "level": lt, "type": f"R-{fn}", "name": nm,
                             "number": f"{lt}-S{k:02d}"})
        sr = Ruang(nm, "SIRK", "Sirkulasi", g, fn, "P1", lt, getattr(S, "zona_sirk", "Sirkulasi"), False)
        lap_ruang.append((res["id"], sr, f"{lt}-S{k:02d}", res.get("area_m2")))
    return tanpa


# ------------------------------------------------------------------ gedung utilitas dan parkir
GU = (100.0, 44.0, 134.0, 76.0)
GU_LANTAI = ["LT1", "LT2", "LT3", "LT4"]      # LT5 = atap (tahap3_bim.GU_TINGKAT)


def susun_gu(lt, prog=None):
    """Gedung utilitas: LT1 ruang utilitas, LT2 dua gudang + parkir, LT3-LT4 parkir."""
    prog = prog or baca_program()
    W = box(*GU)
    S = Susunan(lt=lt, wilayah=W)
    S.gagal = []
    rd = lambda no, **k: ruang_dari(no, prog, **k)  # noqa: E731
    if lt == "LT1":
        daftar = (rd(64, pintu="P3", fin="UTIL") + rd(65, pintu="P3", fin="UTIL") + rd(49, pintu="P3", fin="UTIL")
                  + rd(66, pintu="P2", fin="UTIL") + rd(52, pintu="P2", fin="UTIL") + rd(54, pintu="P2", fin="UTIL")
                  + rd(73, pintu="P2", fin="UTIL"))
        S.ruang, sisa = isi_zona(GU, _urut(daftar), [], d_maks=10.8, penuh=True)
        for t in sisa:
            r = sisipkan(W, S.ruang, [], t, GU)
            if r:
                S.ruang.append(r)
            else:
                S.gagal.append(t[0])
        S.nama_sirk, S.fin_sirk = "Sirkulasi (koridor utilitas)", "UTIL"
    elif lt == "LT2":
        S.ruang, sisa = isi_zona((100, 44, 134, 56), _urut(rd(50, pintu="P3", fin="UTIL") + rd(53, pintu="P3", fin="UTIL")), [],
                                 d_maks=10.8, penuh=True, kor_luar=True, sisi_koridor="max")
        S.gagal = [t[0] for t in sisa]
        S.nama_sirk, S.fin_sirk = "Area parkir GU LT2", "PARKIR"
    else:
        S.ruang = []
        S.nama_sirk, S.fin_sirk = f"Area parkir GU {lt}", "PARKIR"
    for r in S.ruang:
        r.lt = lt
        r.zona = "Gedung utilitas"
    kosong = W.difference(unary_union([r.poli for r in S.ruang]))
    S.sirk = [g.buffer(0) for g in _poligon(kosong) if g.area > 1.0 and not g.buffer(-0.2, join_style=2).is_empty]
    S.zona_sirk = "Gedung utilitas"
    return S


def _poligon(g):
    if g.is_empty:
        return []
    return [g] if g.geom_type == "Polygon" else [p for h in g.geoms for p in _poligon(h)]


def selubung_gu(b, rec):
    """Selubung panel abu GU: LT1 tertutup, LT2-LT4 parapet + pita atas (bukaan parkir 1,9 m), LT5 parapet 1,2 m."""
    loop = _poli(box(*GU).buffer(bim.FASAD_JARAK, join_style=2))
    for lt in GU_LANTAI:
        h = TINGGI_LT[lt]
        if lt == "LT1":
            rec("selubung GU", b.cmd("wall", {"points": loop, "closed": True, "type": "FS-PanelAbu", "level": lt, "height": round(h)}), 4)
        else:
            rec("selubung GU", b.cmd("wall", {"points": loop, "closed": True, "type": "FS-PanelAbu", "level": lt, "height": 1100}), 4)
            rec("selubung GU", b.cmd("wall", {"points": loop, "closed": True, "type": "FS-PanelAbuTua", "level": lt,
                                                "base_offset": round(h - 1000), "height": 1000}), 4)
    rec("selubung GU", b.cmd("wall", {"points": loop, "closed": True, "type": "FS-PanelAbu", "level": "LT5", "height": 1200}), 4)


# ------------------------------------------------------------------ fasad V4 (dikunci) dan overstek podium
def fasad_v4(b, rec):
    """Pola `tahap4_fasad_v4.bangun` apa adanya (panel putih menara berjendela pita, pita kaca biru, dinding tirai tengah,
    podium panel abu, mahkota menara, logo H dan huruf RUMAH SAKIT TEPIAN BATANGHARI)."""
    mmv = bim.mm

    def dinding(q0, q1, tipe, lv, base, h):
        rec("fasad V4", b.cmd("wall", {"points": [mmv(*q0), mmv(*q1)], "type": tipe, "level": lv, "base_offset": round(base),
                                       "height": round(h)}))

    for poli, a, c in bim._pita():
        tingkat = tb.URUT[tb.URUT.index(a):tb.URUT.index(c) + 1]
        for p0, p1 in bim._sisi(poli):
            for q0, q1, jenis in v4.zona_sisi(p0, p1):
                for lo, hi in zip(tingkat[:-1], tingkat[1:]):
                    h = (tb.LEVEL[hi] - tb.LEVEL[lo]) * 1000
                    if jenis in ("tirai", "strip"):
                        dinding(q0, q1, "FS-KacaBiru", lo, 0, h)
                    else:
                        panel = "FS-PanelPutih" if jenis == "pita_putih" else "FS-PanelAbu"
                        dinding(q0, q1, panel, lo, 0, 1100)
                        dinding(q0, q1, "FS-KacaPita", lo, 1100, 1800)
                        dinding(q0, q1, panel, lo, 2900, h - 2900)
    for p0, p1 in bim._sisi(tb.MENARA):
        dinding(p0, p1, "FS-PanelPutih", "ATAP", 0, 1800)
    kot = v4._kotak
    h_kotak = [(-1500, 0, -900, 3000), (900, 0, 1500, 3000), (-900, 1200, 900, 1800)]
    b.cmd("family", {"name": "RSTB Logo H", "category": "generic", "forms": [
        {"plane": "xz", "profile": kot(-1600, -100, 1600, 3100), "from": -150, "to": 150, "material": "Logo biru"}] +
        [{"plane": "xz", "profile": kot(x0, z0, x1, z1), "from": f, "to": t, "material": "Huruf putih"}
         for f, t in ((-250, -150), (150, 250)) for x0, z0, x1, z1 in h_kotak], "types": {"Standar": {}}})
    y_muka = (tb.MENARA.bounds[1] - bim.FASAD_JARAK) * 1000
    lebar = len(v4.NAMA_RS) * v4.MAJU - (v4.MAJU - 5 * v4.SEL_HURUF)
    for c in sorted(set(v4.NAMA_RS) - {" "}):
        kotak, _ = v4.kotak_huruf(c)
        b.cmd("family", {"name": f"RSTB Huruf {c}", "category": "generic", "forms": [
            {"plane": "xz", "profile": kot(x0, z0, x1, z1), "from": -150, "to": 150, "material": "Logo biru"}
            for x0, z0, x1, z1 in kotak], "types": {"Standar": {}}})
    for i, c in enumerate(v4.NAMA_RS):
        if c != " ":
            x = 55000 - lebar / 2 + i * v4.MAJU + 2.5 * v4.SEL_HURUF
            rec("papan nama", b.cmd("component", {"family": f"RSTB Huruf {c}", "at": [round(x), round(y_muka - 200)],
                                                  "level": "LT6", "offset": 2400}))  # 7.8: di bawah dek helipad (dek menjorok 3,9 m), puncak = puncak logo H
    rec("papan nama", b.cmd("component", {"family": "RSTB Logo H", "at": [24500, round(y_muka - 300)], "level": "LT6", "offset": 700}))
    x_timur = (v4.MENARA_X[1] + bim.FASAD_JARAK) * 1000
    rec("papan nama", b.cmd("component", {"family": "RSTB Logo H", "at": [round(x_timur + 300), 39000], "level": "LT6",
                                          "offset": 700, "angle": 90}))
    # overstek/teritis podium (konsol +3,60 s.d. +3,90 di atas LT1, B-6) di sisi utara dan selatan, lebar 0,9 m (V3)
    a, c, d, e = tb.PODIUM.bounds
    j, lo = bim.FASAD_JARAK, 0.9
    for (y0, y1) in ((c - j - lo, c - j), (e + j, e + j + lo)):
        rec("overstek podium", b.cmd("floor", {"boundary": [mm(p) for p in ((a - j, y0), (d + j, y0), (d + j, y1), (a - j, y1))],
                                               "level": "LT1", "offset": OVERSTEK[1], "type": "TP-Overstek"}))


# ------------------------------------------------------------------ tapak
def _kotak4(x0, y0, x1, y1):
    return [mm(p) for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]


def definisi_keluarga(b):
    b.cmd("family", {"name": "RSTB Pohon", "category": "generic", "forms": [
        {"circle": {"centre": [0, 0], "radius": 160}, "from": 0, "to": 2600, "material": "Batang"},
        {"circle": {"centre": [0, 0], "radius": 1500}, "from": 2400, "to": 3600, "material": "Daun"},
        {"circle": {"centre": [0, 0], "radius": 2000}, "from": 3600, "to": 4800, "material": "Daun"},
        {"circle": {"centre": [0, 0], "radius": 1300}, "from": 4800, "to": 5800, "material": "Daun"}], "types": {"Standar": {}}})
    b.cmd("family", {"name": "RSTB Mobil", "category": "generic",
                     "parameters": [{"name": "Warna", "kind": "material", "value": "Mobil putih"}],
                     "forms": [{"profile": v4._kotak(-2250, -900, 2250, 900), "from": 250, "to": 1050, "material": "Warna"},
                               {"profile": v4._kotak(-1300, -800, 1100, 800), "from": 1050, "to": 1550, "material": "Kaca pita"}],
                     "types": {w.split()[-1].title(): {"Warna": w} for w in v4.WARNA if w.startswith("Mobil")}})
    b.cmd("family", {"name": "RSTB Motor", "category": "generic", "forms": [
        {"profile": v4._kotak(-850, -220, 850, 220), "from": 350, "to": 700, "material": "Motor bodi"},
        {"profile": v4._kotak(-1000, -90, -600, 90), "from": 0, "to": 650, "material": "Motor"},
        {"profile": v4._kotak(600, -90, 1000, 90), "from": 0, "to": 650, "material": "Motor"},
        {"profile": v4._kotak(-300, -200, 400, 200), "from": 700, "to": 850, "material": "Motor"}], "types": {"Standar": {}}})
    b.cmd("family", {"name": "RSTB Lampu Jalan", "category": "generic", "forms": [
        {"circle": {"centre": [0, 0], "radius": 70}, "from": 0, "to": 6000, "material": "Tiang lampu"},
        {"profile": v4._kotak(-100, -150, 900, 150), "from": 5900, "to": 6000, "material": "Tiang lampu"},
        {"profile": v4._kotak(500, -200, 1000, 200), "from": 5800, "to": 5900, "material": "Cahaya"}], "types": {"Standar": {}}})


P4_BAWAH = (1.0, 35.0, 7.0, 63.5)       # P4 76 motor dipindah ke barat tapak [keputusan 7.1]
P4_BARIS, P4_JUMLAH, P4_PITCH = 2, 38, 0.75
# koreksi 7.2 (clash C-MRI): jalan IGD mengikuti lajur ambulans 5.2 opsi 2 (x 92,5-98,5) dan drop-off digeser ke
# selatan supaya semua jalur kendaraan ≥ 12,0 m dari isocenter MRI (80,5; 57,0) [Syarat MRI butir 2]
JALAN = [(92.5, 55.0, 98.5, 90.0)]       # lajur ambulans dari gerbang utara sampai kaki ramp IGD
JALAN_LOBI = (50.0, 75.6, 58.0, 90.0)    # jalan masuk lobi dari gerbang utama (zn.PINTU utama)
DROPOFF = (84.6, 34.6, 92.0, 45.4)       # 80 m², tetap di muka zona IGD (x 62-84, y 27-51)
APRON = (92.0, 34.6, 98.5, 45.4)         # pelataran putar ambulans setinggi drop-off, antara ramp dan drop-off
RAMP_IGD = (92.5, 45.4, 98.5, 55.0)      # 9,6 m, naik 0,8 m (8,33 %)
KANOPI_LOBI = (42.0, 75.6, 64.0, 81.0)
GERBANG = {"utama": zn.PINTU["utama"], "jalan": (92.5, 98.5)}   # lebar bukaan pagar sisi utara y = 90


def posisi_p4():
    """76 motor: dua baris tegak lurus lorong, 38 motor tiap baris, pitch 0,75 m, kedalaman 2,0 m, lorong 2,0 m."""
    x0, y0, x1, y1 = P4_BAWAH
    xs = (x0 + 1.0, x1 - 1.0)
    return [(x, y0 + P4_PITCH * (i + 0.5)) for x in xs for i in range(P4_JUMLAH)]


def posisi_pohon():
    pohon = [(x, 14.0) for x in range(6, 86, 8)] + [(x, 86.0) for x in range(6, 84, 9)] + \
            [(9.5, y) for y in range(24, 84, 8)] + [(x, 23.0) for x in range(94, 136, 8)] + \
            [(88.2, y) for y in range(44, 88, 8)]
    keras = [P4_BAWAH, DROPOFF, APRON, RAMP_IGD] + JALAN
    return [p for p in pohon if not any(k[0] - 1 <= p[0] <= k[2] + 1 and k[1] - 2 <= p[1] <= k[3] + 2 for k in keras)]


def muka_air_rata():
    import tahap2_air_tanah as at
    return sum(r[1] for r in at.SUNGAI_BULANAN) / len(at.SUNGAI_BULANAN)


def tapak(b, rec):
    z0 = round(v4.HALAMAN * 1000)
    bang = [mm(p) for p in list(tb.PODIUM.buffer(bim.FASAD_JARAK, join_style=2).exterior.coords)[:-1]]
    gu = [mm(p) for p in list(box(*GU).buffer(bim.FASAD_JARAK, join_style=2).exterior.coords)[:-1]]
    rec("tapak", b.cmd("floor", {"boundary": _kotak4(*v4.PERSIL), "openings": [bang, gu], "level": "LT1",
                                  "offset": z0 - 100, "type": "TP-Rumput"}))
    for k in [v4.PARKIR] + JALAN + [JALAN_LOBI, P4_BAWAH]:
        rec("tapak", b.cmd("floor", {"boundary": _kotak4(*k), "level": "LT1", "offset": z0 - 60, "type": "TP-Aspal"}))
    rec("tapak", b.cmd("floor", {"boundary": _kotak4(*KANOPI_LOBI), "level": "LT1", "offset": z0 - 50, "type": "TP-Paving"}))
    # ramp IGD (lantai miring naik 0,8 m) dan drop-off beratap
    xm = (RAMP_IGD[0] + RAMP_IGD[2]) / 2
    rec("tapak", b.cmd("floor", {"boundary": _kotak4(*RAMP_IGD), "level": "LT1", "offset": -800, "type": "TP-Beton",
                                  "slope": 4.764, "arrow": [mm((xm, RAMP_IGD[3])), mm((xm, RAMP_IGD[1]))]}))
    rec("tapak", b.cmd("floor", {"boundary": _kotak4(*APRON), "level": "LT1", "offset": 0, "type": "TP-Beton"}))
    # kanopi: lobi, drop-off + pelataran, ramp IGD (pelat 200, tiang 300)
    for rect in (KANOPI_LOBI, (DROPOFF[0], DROPOFF[1], APRON[2], APRON[3]), RAMP_IGD):
        rec("kanopi", b.cmd("floor", {"boundary": _kotak4(*rect), "level": "LT1", "offset": 4400, "type": "TP-Kanopi"}))
    for (x, y) in [(42.3, 75.9), (53.0, 75.9), (63.7, 75.9), (42.3, 80.7), (53.0, 80.7), (63.7, 80.7),
                   (84.9, 34.9), (84.9, 45.1), (98.2, 34.9), (98.2, 45.1), (92.8, 54.7), (98.2, 54.7)]:
        # tiang kanopi 300 x 300 dibuat sebagai dinding kotak (bukan IfcColumn: model ARS tanpa kolom)
        rec("kanopi", b.cmd("wall", {"points": _kotak4(x - 0.15, y - 0.15, x + 0.15, y + 0.15), "closed": True,
                                     "type": "PG-Tiang400", "level": "LT1", "base_offset": z0, "height": 4200 - z0}), 4)
    for x, y in posisi_p4():
        rec("kendaraan", b.cmd("component", {"family": "RSTB Motor", "at": mm((x, y)), "level": "LT1", "offset": z0 - 60}))
    for x, y in posisi_pohon():
        rec("lanskap", b.cmd("component", {"family": "RSTB Pohon", "at": mm((x, y)), "level": "LT1", "offset": z0}))
    warna = [w.split()[-1].title() for w in v4.WARNA if w.startswith("Mobil")]
    n = 0
    for baris, (y, sudut) in enumerate(((9.5, 90), (18.5, 90), (28.5, 90), (37.0, 90))):
        for i, x in enumerate(range(93, 135, 3)):
            if (i * 7 + baris * 3) % 5 == 0 or (APRON[0] - 1.5 <= x <= APRON[2] + 1.5 and y >= APRON[1] - 2.5):
                continue
            rec("kendaraan", b.cmd("component", {"family": "RSTB Mobil", "type": warna[n % len(warna)], "at": mm((x, y)),
                                                 "level": "LT1", "offset": z0 - 60, "angle": sudut}))
            n += 1
    # pagar keliling persil dengan bukaan gerbang (utara: gerbang utama dan jalan IGD), tiang dan papan nama
    x0, y0, x1, y1 = v4.PERSIL
    ga, gb = GERBANG["utama"]
    ja, jb = GERBANG["jalan"]
    ruas = [[(x0, y0), (x1, y0)], [(x1, y0), (x1, y1)], [(x1, y1), (jb, y1)], [(ja, y1), (gb, y1)], [(ga, y1), (x0, y1)],
            [(x0, y1), (x0, y0)]]
    for r in ruas:
        rec("pagar", b.cmd("wall", {"points": [mm(p) for p in r], "type": "PG-Pagar150", "level": "LT1",
                                    "base_offset": z0, "height": 2200}))
    for x in (ga, gb, ja, jb):
        rec("pagar", b.cmd("wall", {"points": [mm(p) for p in ((x - 0.2, y1 - 0.2), (x + 0.2, y1 - 0.2), (x + 0.2, y1 + 0.2),
                                                               (x - 0.2, y1 + 0.2))], "closed": True, "type": "PG-Tiang400",
                                    "level": "LT1", "base_offset": z0, "height": 3000}))
    rec("pagar", b.cmd("wall", {"points": [mm((ga - 0.2, y1)), mm((gb + 0.2, y1))], "type": "PG-Papan", "level": "LT1",
                                "base_offset": z0 + 3000, "height": 1200}))
    rec("papan nama", b.cmd("component", {"family": "RSTB Logo H", "at": mm(((ga + gb) / 2, y1 - 0.25)), "level": "LT1",
                                          "offset": z0 + 3000}))
    lampu = [(x, 88.0) for x in (46.0, 62.0, 80.0, 96.0)] + [(88.3, y) for y in (64.0, 76.0)] + \
            [(x, 42.0) for x in (96.0, 112.0, 128.0)] + [(x, 30.0) for x in (96.0, 112.0, 128.0)] + [(4.0, 33.0), (4.0, 65.0)] + \
            [(46.0, 77.0), (62.0, 77.0)]
    for x, y in lampu:
        rec("lampu jalan", b.cmd("component", {"family": "RSTB Lampu Jalan", "at": mm((x, y)), "level": "LT1", "offset": z0}))
    # tepi sungai: lereng per segmen TEBING_2026 dan bidang air (muka air rata-rata bulanan)
    air = muka_air_rata()
    xs = sorted(tp.TEBING_2026)
    for xa, xb in zip(xs[:-1], xs[1:]):
        # lebar lereng membesar dengan tinggi puncak tebing TEBING_2026 (8 + puncak, m); puncak lereng = halaman +12,05
        lebar_lereng = 8.0 + (tp.TEBING_2026[xa] + tp.TEBING_2026[xb]) / 2
        sudut = math.degrees(math.atan2(12.05 - air, lebar_lereng))
        rec("tebing", b.cmd("floor", {"boundary": _kotak4(xa, -lebar_lereng, xb, 0.0), "level": "LT1",
                                      "offset": round((12.05 - tb.LEVEL["LT1"]) * 1000), "type": "TP-Lereng",
                                      "slope": -round(sudut, 3), "arrow": [mm(((xa + xb) / 2, 0.0)), mm(((xa + xb) / 2, -lebar_lereng))]}))
    rec("tebing", b.cmd("floor", {"boundary": _kotak4(-10.0, -40.0, 150.0, -6.0), "level": "LT1",
                                  "offset": round((air - tb.LEVEL["LT1"]) * 1000), "type": "TP-Air"}))


# ------------------------------------------------------------------ atap: taman, helipad, tangki opsi B
HELI_PUSAT = (52.0, 39.0)      # pusat HELIDEK (35,35-68,65 x 22,35-55,65)


def bidang_helipad():
    """(lingkar luar, lingkar dalam, tiga kotak huruf H) dalam meter untuk marka helipad."""
    cx, cy = HELI_PUSAT
    luar, dalam = Point(cx, cy).buffer(11.0, 48), Point(cx, cy).buffer(10.6, 48)
    h = [box(cx - 2.2, cy - 3.0, cx - 1.6, cy + 3.0), box(cx + 1.6, cy - 3.0, cx + 2.2, cy + 3.0),
         box(cx - 1.6, cy - 0.3, cx + 1.6, cy + 0.3)]
    return luar, dalam, h


def atap(b, rec):
    # taman atap V1: lapisan taman di atap LT3 di luar menara (tampak di LT4), bak tanaman, pohon, railing tepi
    rec("taman atap", b.cmd("floor", {"boundary": _poli(tb.ATAP_LT3_BARAT), **_lub(lubang_atap("LT4", tb.ATAP_LT3_BARAT)),
                                       "level": "LT4", "offset": 150, "type": "TP-TamanAtap"}))
    bak = [(14.0, 54.0, 18.0, 58.0), (14.0, 62.0, 18.0, 66.0), (14.0, 70.0, 18.0, 73.5), (24.0, 70.0, 30.0, 73.5),
           (24.0, 54.0, 30.0, 57.0)]
    for r in bak:
        rec("taman atap", b.cmd("wall", {"points": _kotak4(*r), "closed": True, "type": "BT-Bak200", "level": "LT4",
                                          "base_offset": 150, "height": 450}), 4)
    for x, y in ((16.0, 56.0), (16.0, 64.0), (27.0, 55.5)):
        rec("taman atap", b.cmd("component", {"family": "RSTB Pohon", "at": mm((x, y)), "level": "LT4", "offset": 150}))
    sisi = [[(12, 27), (12, 75), (36, 75), (36, 51)], [(12, 27), (20, 27)]]
    for p in sisi:
        rec("railing", b.cmd("railing", {"path": [mm(q) for q in p], "level": "LT4", "base_offset": 150}))
    # penutup atap (lapis kedap air 150): menara di ATAP, atap podium di LT3 (di luar bentuk L LT3), atap GU di LT5
    rec("atap", b.cmd("floor", {"boundary": _poli(tb.MENARA), **_lub(lubang_atap("ATAP", tb.MENARA)), "level": "ATAP",
                                "offset": 150, "type": "TP-AtapTangki"}))
    for g in _poligon(tb.PODIUM.difference(tb.LT3)):
        rec("atap", b.cmd("floor", {"boundary": _poli(g), **_lub(lubang_atap("LT3", g)), "level": "LT3", "offset": 150,
                                    "type": "TP-AtapTangki"}))
    rec("atap", b.cmd("floor", {"boundary": _poli(box(*GU)), "level": "LT5", "offset": 150, "type": "TP-AtapTangki"}))
    # dek helipad: pelat aluminium 100 di atas tiang HEB 600 mm (struktur dek tetap di STR), marka, railing pengaman
    rec("helipad", b.cmd("floor", {"boundary": _poli(tb.HELIDEK), "level": "ATAP", "offset": bim.DEK_TINGGI + 100,
                                    "type": "TP-DekHelipad"}))
    luar, dalam, h = bidang_helipad()
    rec("helipad", b.cmd("floor", {"boundary": _poli(luar), "openings": [_poli(dalam)], "level": "ATAP",
                                    "offset": bim.DEK_TINGGI + 110, "type": "TP-MarkaKuning"}))
    for p in h:
        rec("helipad", b.cmd("floor", {"boundary": _poli(p), "level": "ATAP", "offset": bim.DEK_TINGGI + 110,
                                        "type": "TP-MarkaPutih"}))
    pts = [mm(p) for p in list(tb.HELIDEK.exterior.coords)]
    rec("helipad", b.cmd("railing", {"path": pts, "level": "ATAP", "base_offset": bim.DEK_TINGGI + 100}))
    # tangki air opsi B di atap LT3 (x 60-68, y 67-75, tinggi 3,5 m): selubung panel dan penutup
    tk = t5t.TANGKI_B
    rect = (tk["x"][0], tk["y"][0], tk["x"][1], tk["y"][1])
    rec("tangki B", b.cmd("wall", {"points": _kotak4(*rect), "closed": True, "type": "TK-Panel100", "level": "LT3",
                                    "base_offset": 150, "height": round(tk["tinggi"] * 1000)}), 4)
    rec("tangki B", b.cmd("floor", {"boundary": _kotak4(*rect), "level": "LT3", "offset": round(tk["tinggi"] * 1000) + 300,
                                     "type": "TP-AtapTangki"}))


# ------------------------------------------------------------------ rakit seluruh model
def bangun(render=True, bimc=BIMC):
    from bimcraft import Sesi
    prog = baca_program()
    rec = Catat()
    lap_ruang = []
    tanpa_pintu = {}
    susunan = {lt: susun_lantai(lt, prog) for lt in LANTAI}
    susunan_gu = {lt: susun_gu(lt, prog) for lt in GU_LANTAI}
    with Sesi(TEMPLAT) as b:
        siapkan(b)
        definisi_keluarga(b)
        b.cmd("project_info", {"status": STATUS})
        for lt in LANTAI:
            tanpa_pintu[lt] = interior(b, lt, susunan[lt], rec, lap_ruang)
        for lt in GU_LANTAI[:2]:
            tanpa_pintu["GU " + lt] = interior(b, lt, susunan_gu[lt], rec, lap_ruang)
        for lt in GU_LANTAI[2:]:
            # lantai parkir terbuka: satu ruang parkir dibatasi pemisah di tepi denah
            S = susunan_gu[lt]
            b.cmd("room_separator", {"points": _poli(S.wilayah), "level": lt, "closed": True})
            res = b.cmd("room", {"point": mm(S.wilayah.centroid.coords[0]), "level": lt, "type": "R-PARKIR",
                                 "name": S.nama_sirk, "number": f"GU-{lt}-01"})
            lap_ruang.append((res["id"], Ruang(S.nama_sirk, "SIRK", "Sirkulasi", S.wilayah, "PARKIR", "P1", lt, "Gedung utilitas", False),
                              f"GU-{lt}-01", res.get("area_m2")))
        selubung_gu(b, rec)
        fasad_v4(b, rec)
        tapak(b, rec)
        atap(b, rec)
        # mobil di lantai parkir GU
        warna = [w.split()[-1].title() for w in v4.WARNA if w.startswith("Mobil")]
        n = 0
        for lt in GU_LANTAI[1:]:
            for i in range(6):
                rec("kendaraan", b.cmd("component", {"family": "RSTB Mobil", "type": warna[n % len(warna)],
                                                     "at": mm((105.0 + i * 4.5, 66.0 if lt != "LT2" else 62.0)), "level": lt,
                                                     "offset": 50, "angle": 0}))
                n += 1
        # Pset_RSTB_Umum dan finishing
        for grup, ids in rec.ids.items():
            if ids:
                b.cmd("modify", {"ids": ids, "params": {"RSTB_Tahap": "7", "RSTB_LOD": "300", "RSTB_Status": STATUS,
                                                          "RSTB_Sumber": f"[{grup}] 7.1 arsitektur (usulan AI, atas delegasi Defsa 22 Nov 2026)"}})
        for idr, r, nomor, _ in lap_ruang:
            fl, dn, pl, _t = FINISH.get(r.fin, ("tanpa lapis lantai (shaft / ruang luncur)", "-", "-", None))
            b.cmd("modify", {"id": idr, "params": {
                "RSTB_Tahap": "7", "RSTB_LOD": "300", "RSTB_Status": STATUS, "RSTB_Sumber": "[ruang] 7.1 tata letak skematik [Asumsi]",
                "RSTB_Zona": r.zona, "RSTB_KodeProgram": r.kode, "RSTB_Kelompok": r.kel,
                "RSTB_FinLantai": f"{fl} [Asumsi]", "RSTB_FinDinding": f"{dn} [Asumsi]", "RSTB_FinPlafon": f"{pl} [Asumsi]"}})
        b.simpan(bimc)
        b.simpan(Path(bimc).with_suffix(".ifc"))
        if render:
            GAMBAR.mkdir(parents=True, exist_ok=True)
            b.cmd("graphics", {"view": "{3D}", "hide": ["levels", "grids"]})
            for nama, az, el in (("Depan", -55, 10), ("Udara", -40, 32)):
                b.alat("render", {"view": "{3D}", "path": str(GAMBAR / f"7.1 Model ARS 3D {nama}.png"), "width": 1800,
                                  "height": 1100, "azimuth": az, "elevation": el})
    return {"hitung": rec.hitung, "ruang": len(lap_ruang), "tanpa_pintu": tanpa_pintu, "susunan": susunan,
            "susunan_gu": susunan_gu, "lap_ruang": lap_ruang}


if __name__ == "__main__" and "--bangun" in sys.argv and "--laporan" not in sys.argv:
    r = bangun(render="--tanpa-render" not in sys.argv)
    print(r["hitung"], r["ruang"], {k: v for k, v in r["tanpa_pintu"].items() if v})
if __name__ == "__main__" and "--pratinjau" in sys.argv:
    prog = baca_program()
    for lt in LANTAI:
        S = susun_lantai(lt, prog)
        prog_luas = sum(_luas_bersih(r.poli) for r in S.ruang if r.program)
        print(lt, "ruang", len(S.ruang), "program", round(prog_luas, 1), "sirk", len(S.sirk), "gagal", S.gagal)


def cek_geometri(S):
    """Daftar masalah geometri satu lantai: ruang di luar denah, tumpang tindih antar ruang, menabrak inti."""
    out = []
    inti = unary_union([c[2] for c in S.inti]) if S.inti else Polygon()
    rs = S.ruang
    for r in rs:
        if r.kel != "Inti" and r.poli.difference(S.wilayah.buffer(0.01)).area > 0.05 and r.kode != "P16":
            out.append(f"{r.nama}: {r.poli.difference(S.wilayah).area:.2f} m2 di luar denah")
        if r.kel != "Inti" and r.poli.intersection(inti).area > 0.05:
            out.append(f"{r.nama}: menabrak inti {r.poli.intersection(inti).area:.2f} m2")
    for i, a in enumerate(rs):
        for b in rs[i + 1:]:
            if a.poli.intersection(b.poli).area > 0.05:
                out.append(f"tumpang tindih {a.nama} x {b.nama}: {a.poli.intersection(b.poli).area:.2f} m2")
    return out


if __name__ == "__main__" and "--cek" in sys.argv:
    prog = baca_program()
    for lt in LANTAI:
        S = susun_lantai(lt, prog)
        print(lt, "gagal", S.gagal)
        for m in cek_geometri(S)[:12]:
            print("   ", m)


def pratinjau_satu(lt, png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    S = susun_lantai(lt, baca_program())
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.plot(*S.wilayah.exterior.xy, "k-", lw=1.5)
    for r in S.ruang:
        fc = {"INTI": "#bbbbbb", "SERVIS": "#e8c9a0", "OK": "#a0c8e8", "TOILET": "#a0e8d0"}.get(r.fin, "#dfe8c0")
        polys = [r.poli] if r.poli.geom_type == "Polygon" else list(r.poli.geoms)
        for p in polys:
            ax.fill(*p.exterior.xy, fc=fc, ec="k", lw=0.6)
        c = r.poli.representative_point()
        ax.text(c.x, c.y, r.nama[:22], fontsize=6, ha="center")
    for g in S.sirk:
        ax.fill(*g.exterior.xy, fc="#ffffe0", ec="r", lw=0.4, alpha=0.6)
    ax.set_aspect("equal")
    fig.savefig(png, dpi=65)


# ------------------------------------------------------------------ validasi IFC
def idn(x, n=1):
    return f"{x:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _grid_dunia(f):
    """{tag: ((x1, y1), (x2, y2))} mm di koordinat dunia untuk tiap sumbu grid IfcGrid."""
    import ifcopenshell.util.placement as up
    out = {}
    for g in f.by_type("IfcGrid"):
        m = up.get_local_placement(g.ObjectPlacement) if g.ObjectPlacement else None
        for ax in list(g.UAxes) + list(g.VAxes):
            pts = []
            for p in ax.AxisCurve.Points:
                c = list(p.Coordinates) + [0.0]
                v = (m @ [c[0], c[1], c[2], 1.0])[:2] if m is not None else c[:2]
                pts.append((float(v[0]), float(v[1])))
            out[ax.AxisTag] = tuple(pts[:2])
    return out


def ukur(path=IFC):
    """Baca IFC ARS: ruang per lantai (luas bersih/kotor, kode program), kelas elemen, dan data T-110."""
    import ifcopenshell
    import ifcopenshell.util.element as ue
    from collections import Counter
    f = ifcopenshell.open(str(path))
    ruang = []
    for s in f.by_type("IfcSpace"):
        ps = ue.get_psets(s)
        q, fin = ps.get("Qto_SpaceBaseQuantities", {}), ps.get("Pset_RSTB_Finishing", {})
        ag = ue.get_aggregate(s)
        ruang.append({"lt": ag.Name if ag else None, "nama": s.LongName, "no": s.Name, "net": q.get("NetFloorArea"),
                      "gross": q.get("GrossFloorArea"), "kode": fin.get("RSTB_KodeProgram"), "kel": fin.get("RSTB_Kelompok"),
                      "zona": fin.get("RSTB_Zona")})
    slab = Counter((e.ObjectType or "").split("-")[0] for e in f.by_type("IfcSlab"))
    return {"f": f, "ruang": ruang, "kelas": Counter(e.is_a() for e in f.by_type("IfcElement")), "slab": slab,
            "storey": {s.Name: s.Elevation for s in f.by_type("IfcBuildingStorey")}, "grid": _grid_dunia(f),
            "mb": Path(path).stat().st_size / 1e6}


def validasi(path=IFC, str_path=STR_IFC):
    """Validasi 7.1: hierarki, kelas struktur, T-110 (elevasi dan grid vs STR), T-109 (luas program vs Rekap Lantai)."""
    import ifcopenshell
    import tahap3_bim as t3
    from collections import defaultdict
    v = t3.validasi(path, wajib_lod=False)
    cek = list(v["cek"])
    m = ukur(path)
    ruang = m["ruang"]
    cek.append({"butir": "Ruang (IfcSpace) bernama, semua bernomor dan punya luas", "lolos": all(r["nama"] and r["net"] for r in ruang),
                "ket": f"{len(ruang)} ruang; tanpa luas: {sum(1 for r in ruang if not r['net'])}"})
    cek.append({"butir": "Tidak ada IfcColumn, IfcBeam, IfcMember, IfcFooting; IfcSlab hanya lapis arsitektur (LT-, TP-)",
                "lolos": not any(m["kelas"].get(k) for k in ("IfcColumn", "IfcBeam", "IfcMember", "IfcFooting", "IfcPile"))
                and set(m["slab"]) <= {"LT", "TP"},
                "ket": f"kelas: {dict(m['kelas'])}; slab: {dict(m['slab'])}"})
    # T-110
    fs = ifcopenshell.open(str(str_path))
    st_s = {s.Name: s.Elevation for s in fs.by_type("IfcBuildingStorey")}
    d_el = max(abs(m["storey"][k] - st_s[k]) for k in m["storey"] if k in st_s)
    gs = _grid_dunia(fs)
    d_gr = max(max(abs(a[0] - b[0]), abs(a[1] - b[1])) for k in m["grid"] if k in gs
               for p, q in zip(m["grid"][k], gs[k]) for a, b in [(p, q)])
    t110 = {"elevasi_mm": d_el, "grid_mm": d_gr, "n_storey": len(st_s), "n_grid": len(gs), "lolos": d_el <= 1.0 and d_gr <= 1.0}
    cek.append({"butir": "T-110: elevasi storey dan posisi grid ARS = STR (toleransi 1 mm)", "lolos": t110["lolos"],
                "ket": f"selisih maks elevasi {idn(d_el, 3)} mm ({t110['n_storey']} storey), grid {idn(d_gr, 3)} mm ({t110['n_grid']} sumbu)"})
    # T-109
    rekap = baca_rekap()
    prog = baca_program()
    gu = lambda r: r["zona"] == "Gedung utilitas"  # noqa: E731
    per = defaultdict(float)
    per_gross = defaultdict(float)
    per_kel = defaultdict(float)
    for r in ruang:
        if (r["kode"] or "").startswith("P") and not gu(r):
            per[r["lt"]] += r["net"]
            per_kel[r["kel"]] += r["net"]
        if gu(r) and (r["kode"] or "").startswith("P"):
            per["GU"] += r["net"]
            per_kel[r["kel"]] += r["net"]
        if not gu(r) and r["kode"] != "P16":
            per_gross[r["lt"]] += r["gross"] or 0
    for lt in LANTAI:      # tebal dinding inti struktur (350) bagian dari denah, bukan ruang
        per_gross[lt] += sum(c[2].area - c[3].area for c in inti_lantai(lt))
    t109 = {"lantai": [], "kel": [], "massa": []}
    for lt in LANTAI + ["GU"]:
        tgt = rekap[lt][0]
        t109["lantai"].append((lt, tgt, per[lt], per[lt] / tgt - 1))
    tot_t, tot_i = sum(x[1] for x in t109["lantai"]), sum(x[2] for x in t109["lantai"])
    t109["total"] = (tot_t, tot_i, tot_i / tot_t - 1)
    ktgt = defaultdict(float)
    for no, (kel, nm, n, a) in prog.items():
        if no == 67:      # IPAL tanam: di luar model arsitektur (MEP, bawah tanah)
            continue
        ktgt[kel] += n * a
    for kel, tgt in ktgt.items():
        t109["kel"].append((kel, tgt, per_kel[kel], per_kel[kel] / tgt - 1))
    for lt in LANTAI:
        luas_plan = wilayah_lantai(lt).area
        t109["massa"].append((lt, rekap[lt][2], luas_plan, per_gross[lt], per_gross[lt] / rekap[lt][2] - 1,
                              per_gross[lt] / luas_plan - 1))
    ok_l = all(abs(x[3]) <= 0.05 for x in t109["lantai"]) and abs(t109["total"][2]) <= 0.02
    ok_k = all(abs(x[3]) <= 0.05 for x in t109["kel"])
    cek.append({"butir": "T-109a: luas ruang program per lantai vs Rekap Lantai (5 % per lantai, 2 % total)", "lolos": ok_l,
                "ket": "; ".join(f"{x[0]} {idn(x[3] * 100, 1)} %" for x in t109["lantai"]) + f"; total {idn(t109['total'][2] * 100, 2)} %"})
    cek.append({"butir": "T-109b: luas ruang program per kelompok (zona fungsi) vs program 3.4 (5 %)", "lolos": ok_k,
                "ket": "; ".join(f"{x[0]} {idn(x[3] * 100, 1)} %" for x in t109["kel"])})
    ok_m = all(abs(x[5]) <= 0.02 for x in t109["massa"])
    cek.append({"butir": "T-109c: seluruh ruang + sirkulasi + inti (luas kotor) vs luas denah lantai (2 %)", "lolos": ok_m,
                "ket": "; ".join(f"{x[0]} {idn(x[5] * 100, 2)} %" for x in t109["massa"])})
    return {"cek": cek, "lolos": all(c["lolos"] for c in cek), "ukur": m, "t110": t110, "t109": t109, "file": v["file"]}


def info_cli(path=BIMC):
    import json
    import subprocess
    from bimcraft import CLI
    r = subprocess.run([str(CLI), "info", str(path)], capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout)


# ------------------------------------------------------------------ catatan md dan jalankan
def tulis_md(v, hasil, info):
    from collections import Counter, defaultdict
    m = v["ukur"]
    ruang = m["ruang"]
    t109, t110 = v["t109"], v["t110"]
    hit = hasil["hitung"] if hasil else {}
    kelas = m["kelas"]
    pintu = Counter((e.ObjectType or "?") for e in m["f"].by_type("IfcDoor"))
    per_lt = defaultdict(lambda: [0, 0.0, 0, 0.0, 0, 0.0])
    for r in ruang:
        if r["zona"] == "Gedung utilitas":
            continue
        k = 0 if (r["kode"] or "").startswith("P") else (4 if r["kode"] == "INTI" else 2)
        per_lt[r["lt"]][k] += 1
        per_lt[r["lt"]][k + 1] += r["net"] or 0
    kode = Counter(r["kode"] for r in ruang)
    tt = kode["P26"] * 1 + kode["P27"] * 2 + kode["P28"] * 4
    tt_int = 8 + 4 + 4 + 6
    mb = m["mb"]
    o = ["# 7.1 Model Arsitektur LOD 300", "",
         f"Status: **draf, keputusan usulan AI disetujui atas delegasi Defsa 22 Nov 2026** (belum disetujui Defsa langsung). "
         "DATA SIMULASI, bukan data proyek nyata, tidak untuk konstruksi.", "",
         "Disusun AI 22 Nov 2026 (`skrip/tahap7_arsitektur.py`, uji `tests/test_tahap7_arsitektur.py`). Model: "
         "`model/RSTB-ARS-T7-LOD300.bimc` dan `.ifc`; untuk jendela BIMCraft 0.11.0 pakai `model/RSTB-ARS-T7-LOD300-v0.11.bimc` "
         "(impor dari IFC). Render: `07 DED dan RKS/Gambar/7.1 Model ARS 3D Depan.png` dan `... Udara.png`.", "",
         "## Isi model", "",
         "Hanya unsur arsitektur: kolom, balok, pelat, dinding inti, tangga, dan pondasi struktur ada di "
         "`model/RSTB-STR-T6-LOD300.ifc` dan digabung di 7.2. Level dan grid sama dengan model struktur (tidak digeser): "
         "LT1 12,85; LT2 17,35; LT3 21,85; LT4 26,05; LT5 30,25; LT6 34,45; ATAP 38,65 m; grid 1-10 dan A-G modul 8 m; halaman +12,05.", "",
         "| Kategori (`bimcraft-cli info`) | Jumlah |", "|---|---|"]
    o += [f"| {k} | {idn(n, 0)} |" for k, n in sorted(info["counts"].items())]
    o += ["", "Kelas IFC: " + ", ".join(f"{k} {idn(n, 0)}" for k, n in sorted(kelas.items()))
          + f". Ukuran berkas IFC {idn(mb, 1)} MB. Jumlah ruang (IfcSpace) bernama: **{idn(len(ruang), 0)}**.", "",
          "Unsur per kelompok yang dibuat (hitungan perintah): " + ", ".join(f"{k} {idn(n, 0)}" for k, n in sorted(hit.items())) + ".", "",
          "Pintu bertipe: " + ", ".join(f"{k} {n}" for k, n in sorted(pintu.items())) + ". "
          "P1 900 tunggal, P2 1.200 ganda (brankar), P3 1.500 ganda (IGD, OK, utilitas), PL pintu lift 1.400 × 2.400 (posisi dari `tahap4_dinding.PINTU`).", "",
          "### Ruang per lantai (luas bersih, m²)", "",
          "| Lantai | Ruang program | Luas program | Sirkulasi | Luas sirkulasi | Inti | Luas inti |", "|---|---|---|---|---|---|---|"]
    for lt in LANTAI:
        p = per_lt[lt]
        o.append(f"| {lt} | {p[0]} | {idn(p[1])} | {p[2]} | {idn(p[3])} | {p[4]} | {idn(p[5])} |")
    gu = [r for r in ruang if r["zona"] == "Gedung utilitas"]
    o += ["", f"Gedung utilitas: {len(gu)} ruang (LT1 ruang utilitas, LT2 dua gudang dan parkir, LT3-LT4 parkir; LT5 atap).", "",
          "### Isi per bagian", "",
          "- **Fasad V4 (dikunci)**: pola `tahap4_fasad_v4` apa adanya (panel putih menara berjendela pita, pita kaca biru, dinding tirai tengah, "
          "podium panel abu, mahkota menara, logo H, huruf RUMAH SAKIT TEPIAN BATANGHARI). Tambahan overstek/teritis podium sisi utara dan selatan "
          f"pelat 300 mm lebar 0,9 m pada konsol +3,60 s.d. +3,90 di atas LT1 (B-6).",
          "- **Dalam gedung**: dinding partisi bata ringan 100 (antarruang) dan 150 (batas koridor), koridor ganda 2,4 m, ruang tiap baris program 3.4 "
          "dalam zona `tahap3_zonasi`, pintu tiap ruang, plafon gypsum dan lapis lantai 50 mm otomatis dari tipe ruang, Pset finishing per ruang "
          "(`Pset_RSTB_Finishing`: zona, kode program, kelompok, finishing lantai/dinding/plafon) dan `Pset_RSTB_Umum` (tahap, LOD 300, status, sumber).",
          "- **Inti**: ruang \"Lift brankar dan pasien\" dan \"Tangga darurat\" (dibatasi pemisah di muka dalam dinding inti STR), lapisan inti 50 mm "
          "di muka luar dinding inti, pintu lift tiap lantai, railing di depan pintu lift, railing di tepi void lobi LT2.",
          "- **Tapak**: halaman rumput +12,05, jalan masuk lobi berkanopi, drop-off IGD beratap dengan ramp 0,8 m (8,33 %), parkir mobil V4, "
          "**P4 76 motor di sisi barat (x 1-7, y 35-63,5; 2 baris × 38 @ 0,75 m, kedalaman 2,0 m, lorong 2,0 m)**, pohon V4 baris x = 4 dipindah ke x = 9,5, "
          "pagar keliling dengan gerbang utama bernama papan nama (logo H) dan gerbang jalan IGD, 16 lampu jalan.",
          "- **Atap**: taman atap V1 (lapisan taman 150, 5 bak tanaman, pohon, railing tepi) di atap LT3 sisi barat (tampak di LT4), dek helipad "
          "(pelat aluminium di atas tiang STR 600 mm, marka H dan lingkar, railing keliling), lapis kedap air menara, podium, dan GU, selubung tangki opsi B "
          "di tepi utara atap LT3 (x 60-68, y 67-75, tinggi 3,5 m).",
          "- **Gedung utilitas dan parkir**: selubung panel abu (LT1 tertutup; LT2-LT4 parapet 1,1 m dan pita atas 1,0 m dengan bukaan parkir; LT5 parapet 1,2 m), "
          "partisi LT1-LT2, parkir LT2-LT4 dengan mobil.",
          "- **Tepi sungai**: tujuh lereng per segmen `TEBING_2026` (puncak lereng +12,05, dasar di muka air rata-rata bulanan "
          f"{idn(muka_air_rata(), 2)} m dari `SUNGAI_BULANAN`; lebar lereng 8 m + puncak tebing) dan bidang \"Air sungai\" biru.", "",
          "## Validasi (ifcopenshell pada IFC hasil)", ""]
    o += [f"- {'Lolos' if c['lolos'] else '**GAGAL**'}: {c['butir']} ({c['ket']})" for c in v["cek"]]
    o += ["", "### T-110: kesesuaian level dan grid dengan model struktur (toleransi ≤ 1 mm)", "",
          f"Selisih maksimum elevasi {t110['n_storey']} storey: **{idn(t110['elevasi_mm'], 3)} mm**; posisi {t110['n_grid']} sumbu grid "
          f"(1-10, A-G): **{idn(t110['grid_mm'], 3)} mm**. Hasil: **{'lolos' if t110['lolos'] else 'gagal'}** "
          "(level dan grid dibuat dari `tahap4_beban.LEVEL`, `GRID_X`, `GRID_Y` dengan template yang sama dengan model struktur).", "",
          "### T-109: luas ruang terhadap program 3.4 dan massa", "",
          "Toleransi ditetapkan sebelum dihitung: ≤ 5 % per lantai atau zona, ≤ 2 % total. Luas ruang = `NetFloorArea` IfcSpace (muka dalam dinding).", "",
          "| Lantai | Luas bersih Rekap Lantai (m²) | Σ ruang program IFC (m²) | Selisih |", "|---|---|---|---|"]
    o += [f"| {x[0]} | {idn(x[1])} | {idn(x[2])} | {idn(x[3] * 100, 2)} % |" for x in t109["lantai"]]
    o += [f"| **Total** (LT1-LT6 + GU) | {idn(t109['total'][0])} | {idn(t109['total'][1])} | **{idn(t109['total'][2] * 100, 2)} %** |", "",
          "Per kelompok program (zona fungsi):", "", "| Kelompok | Program 3.4 (m²) | IFC (m²) | Selisih |", "|---|---|---|---|"]
    o += [f"| {x[0]} | {idn(x[1])} | {idn(x[2])} | {idn(x[3] * 100, 2)} % |" for x in t109["kel"]]
    o += ["", "Seluruh ruang + sirkulasi + inti (luas kotor sampai garis as dinding, ditambah tebal dinding inti 350 mm) terhadap denah lantai:", "",
          "| Lantai | Luas massa Rekap (m²) | Luas denah lantai sebenarnya (m²) | Σ ruang + sirkulasi + inti (m²) | Selisih ke Rekap | Selisih ke denah |",
          "|---|---|---|---|---|---|"]
    o += [f"| {x[0]} | {idn(x[1])} | {idn(x[2])} | {idn(x[3])} | {idn(x[4] * 100, 2)} % | {idn(x[5] * 100, 2)} % |" for x in t109["massa"]]
    o += ["", "**Catatan T-109 (massa):** di 7.1 kolom \"Luas massa\" lembar Rekap Lantai memakai 3.456 m² untuk LT2 dan LT3, padahal denah LT2 "
          "tanpa void lobi (36-62 × 51-75) = 2.832 m² dan denah LT3 berbentuk L = 2.304 m² (sisanya atap podium di level LT3). Sumbernya "
          "`tahap3_program.buat_excel` (luas podium penuh untuk ketiga lantai); dikoreksi di 7.2 dan 3.4 Program Ruang Konsultan.xlsx dibuat ulang, "
          "jadi kolom Rekap = denah sebenarnya. Sirkulasi di model = sisa denah setelah ruang program, jadi luas bruto per lantai ikut denah, bukan 1,45 × bersih "
          "(rasio denah/luas program di model: " + "; ".join(f"{x[0]} {idn(x[2] / dict((y[0], y[1]) for y in t109['lantai'])[x[0]], 2)}" for x in t109["massa"]) + "; Rekap memakai 1,45).", "",
          "### Cek kewajaran", "",
          f"- Denah: podium 72 × 48 = {idn(tb.PODIUM.area, 0)} m², menara 64 × 24 = {idn(tb.MENARA.area, 0)} m² (diambil dari `tahap4_beban`).",
          f"- Tempat tidur rawat inap: VIP {kode['P26']} + kamar 2 TT {kode['P27']} + kamar 4 TT {kode['P28']} ruang = **{tt} TT** (LT4-LT6, target 128) "
          f"+ intensif {tt_int} (ICU 8, HCU 4, NICU 4, isolasi 6) = **{tt + tt_int} TT** (target 150).",
          f"- Ukuran IFC {idn(mb, 1)} MB (orde 3-15 MB); model fasad V4 lama 451 dinding, 37 pintu, 111 floor, 111 komponen (itu termasuk unsur "
          f"struktur inti): ARS baru {info['counts'].get('wall')} dinding, {info['counts'].get('door')} pintu, {info['counts'].get('room')} ruang, "
          f"{info['counts'].get('floor')} floor, {info['counts'].get('component')} komponen.",
          f"- Pintu: tiap ruang non-inti punya pintu; ruang tanpa pintu: {sum(len(x) for x in hasil['tanpa_pintu'].values()) if hasil else 'tidak dicek'}.", "",
          "## Asumsi", "",
          "- [Asumsi: koridor ganda 2,4 m untuk brankar; pedoman koridor RS belum ada di `acuan/`]. Pembukaan pintu ganda brankar 1.200 dan 1.500.",
          "- [Asumsi: partisi bata ringan 100 antarruang dan 150 di batas koridor; luas bersih memakai tebal efektif 100; partisi berhenti 800 mm di bawah level atas (bawah balok), bagian di atas plafon belum dimodelkan].",
          "- [Asumsi: plafon gypsum 2.800 mm di atas lantai (3.000 mm untuk lobi, administrasi, aula), ruang OK tanpa plafon gypsum (plafon laminar-flow oleh MEP), "
          "ruang utilitas dan parkir tanpa plafon; lapis lantai 50 mm].",
          "- [Asumsi: finishing OK vinil konduktif; ICU, rawat inap, klinik vinil homogen; lobi granit; servis dan utilitas epoksi; toilet keramik; administrasi homogeneous tile] "
          "(Pset ruang).",
          "- [Asumsi: konsol overstek +3,60 s.d. +3,90 di atas LT1; angka GS-19 tidak ada di skrip tahap 4, dipakai nilai rencana Tahap 7 B-6; pelat 300 lebar 0,9 m seperti V3].",
          "- [Asumsi: tata letak ruang skematik] ruang disusun berjajar menempel koridor dalam tiap zona (rak ganda atau tunggal), ruang kecil (≤ 30-40 m²) "
          "ditumpuk berpasangan dan ruang belakang diakses lewat ruang depan, ruang yang menabrak inti diberi takik. Sisa denah menjadi "
          "\"Sirkulasi (koridor dan selasar)\". Denah rinci dan alur steril/kotor disetel Defsa atau dibahas di 7.2-7.4.",
          "- [Asumsi: alokasi] program yang tidak persis di zona 3.4: kamar isolasi tekanan negatif (6) di zona hemodialisis LT2 (zona ICU ditempati lift dan tangga); "
          "ICU/HCU/NICU memakai lajur utara dan selatan inti lift; LT3 tidak punya denah di y 51-75 (itu atap podium), jadi gizi dan laundry di x 62-84 y 27-51 "
          "dan musala/kantin/jaga dokter di tengah; toilet umum 7 ruang semua di LT1 (mengikuti lembar Rekap); USG di zona tengah LT1; "
          "server dan loker di zona tengah; 6 ruang AHU dan 6 shaft MEP (1 per lantai, 70 dan 32 m²); "
          "rawat inap: VIP 3-3-2, 2 TT 3-3-4, 4 TT 8-8-9, laktasi 1-1-0 per lantai LT4-LT6 supaya total 8/10/25 ruang.",
          "- [Asumsi: koridor steril dan scrub bedah] dibuat sebagai koridor itu sendiri (dilebarkan sampai luas 110 m²).",
          "- [Asumsi: drop-off IGD 80 m²] x 84,6-92 y 34,6-45,4 beratap (kanopi pelat 200 di +4,4 m, tiang kotak 300), pelataran putar x 92-98,5 "
          "dan ramp lantai miring 9,6 m di lajur ambulans x 92,5-98,5 (y 45,4-55); semua jalur kendaraan ≥ 12,0 m dari isocenter MRI "
          "(koreksi 7.2, sebelumnya jalan x 84,6-92 hanya 5,3 m).",
          "- [Literatur: zona merah, kuning, hijau] PMK 40/2022 Lampiran hal. 9 butir F (dicabut Permenkes 6/2026, dipakai dengan catatan seperti 3.4).",
          "- [Asumsi: P4 76 motor di barat] 2 baris × 38 @ 0,75 m (keputusan rencana 7.1); pohon x = 4 dipindah ke x = 9,5.",
          "- [Asumsi: lebar lereng tepi sungai] 8 m + puncak tebing; bentuk lereng skematik (tanpa kontur survei).", "",
          "## Disederhanakan atau tidak dimodelkan", "",
          "- Lift (kereta, rel), anak tangga (di model STR), jendela interior, furnitur, fixture toilet, MEP, IPAL (110 m², tanam, MEP), "
          "ramp parkir GU dan jalur kendaraan di dalam GU tidak dimodelkan; lubang shaft MEP di pelat STR tidak diteruskan ke lapis lantai ARS "
          "(lapis lantai menutup lubang; diselesaikan di 7.2 saat model digabung).",
          "- Tiang kanopi dibuat sebagai dinding kotak 300 (model ARS tanpa IfcColumn). Tiang dan balok kanopi struktur menyusul di 7.2 bila perlu.",
          "- Ruang tidak dipasangi Pset per dinding; Pset ada di tiap kelompok unsur (`RSTB_Sumber` menyebut kelompoknya).",
          "- Titik hitung luas ruang bersih mengikuti partisi 100: ruang bertepi denah (pemisah ruang, bukan dinding) memiliki luas bersih sedikit lebih besar.", "",
          "## Cara membuka dan melanjutkan manual", "",
          "1. Jendela BIMCraft 0.11.0: `BUKA BIMCRAFT.cmd`, lalu buka `model/RSTB-ARS-T7-LOD300-v0.11.bimc`. Ruang, dinding, pintu, plafon bisa diedit; "
          "hindari memindah dinding partisi tanpa memindah ruang di sebelahnya (ruang terikat pada dinding).",
          "2. Pemeriksa IFC: `model/RSTB-ARS-T7-LOD300.ifc` dapat dibuka di Blender Bonsai (`BUKA MODEL DI BLENDER.cmd`) atau FreeCAD.",
          "3. Membangun ulang: `.venv\\Scripts\\python.exe skrip\\tahap7_arsitektur.py --bangun` (15 detik; tambah `--tanpa-render` untuk melewatkan PNG), "
          "lalu `--laporan` untuk validasi dan berkas ini.",
          "4. Uji: `.venv\\Scripts\\python.exe -m pytest -q tests/test_tahap7_arsitektur.py`.", "",
          "## Langkah berikutnya", "",
          "7.2 gabung model ARS (berkas ini) dengan STR 6.9 dan MEP, cek clash dan duplikasi (lapis lantai vs lubang shaft, dinding lapis inti vs dinding STR).", ""]
    MD.write_text("\n".join(o), encoding="utf-8")
    return MD


def laporan(bangun_dulu=False):
    from bimcraft import ke_v011, tampilkan
    hasil = bangun(render=bangun_dulu) if bangun_dulu else None
    v = validasi()
    info = info_cli()
    if hasil is None:
        hasil = {"hitung": {}, "tanpa_pintu": {}}
    v011 = ke_v011(IFC)
    tampil = tampilkan(BIMC)
    tulis_md(v, hasil, info)
    return v, info, v011, tampil


if __name__ == "__main__" and "--laporan" in sys.argv:
    v, info, v011, tampil = laporan("--bangun" in sys.argv)
    for c in v["cek"]:
        print(("OK  " if c["lolos"] else "GAL ") + c["butir"], "|", c["ket"][:300])
    print(info["counts"], v011, "tampil di jendela:", tampil)
